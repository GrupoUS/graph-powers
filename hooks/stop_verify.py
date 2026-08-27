#!/usr/bin/env python3
"""Run the configured project linter before a Stop event, fail-open on hook/tool faults."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import typing
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _config as gp
from _change_set import ChangeSet, collect_change_set

try:
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
except Exception:
    pass


# These names are part of the verifier's internal decision vocabulary. ASK is reserved for a
# future interactive Stop surface; Stop currently either allows or supplies a follow-up.
ALLOW = "ALLOW"
DENY = "DENY"
ASK = "ASK"
SKIP_NOT_DECLARED = "SKIP_NOT_DECLARED"
SKIP_UNAVAILABLE = "SKIP_UNAVAILABLE"
INTERNAL_ERROR = "INTERNAL_ERROR"
TIMEOUT = "TIMEOUT"

LINT_TIMEOUT_S = 25
MAX_DIAGNOSTIC_CHARS = 3000
MAX_DIAGNOSTIC_LINES = 40

_SECRET_ASSIGNMENT = re.compile(
    r"(?i)(?:[A-Za-z_][A-Za-z0-9_]*(?:token|secret|password|passwd|api[_-]?key|credential|cookie)"
    r"[A-Za-z0-9_]*|token|secret|password|passwd|api[_-]?key|credential|cookie)"
    r"\s*[:=]\s*[^\s,;]+"
)


def read_input() -> tuple[dict[str, Any], bool]:
    try:
        raw = sys.stdin.read()
        value = json.loads(raw) if raw.strip() else None
        if not isinstance(value, dict):
            return {}, False
        return typing.cast(dict[str, Any], value), True
    except Exception:
        return {}, False


def _is_cursor_payload(payload: dict[str, Any]) -> bool:
    return (
        isinstance(payload.get("status"), str)
        and isinstance(payload.get("loop_count"), int)
        and not isinstance(payload.get("loop_count"), bool)
    )


def _diagnostic(stdout: str, stderr: str) -> str:
    """Keep useful tail context while preventing command output from becoming an env dump."""
    combined = "\n".join(part for part in (stdout, stderr) if part)
    safe = _SECRET_ASSIGNMENT.sub("[REDACTED]", combined)
    lines = safe.splitlines()
    if len(lines) > MAX_DIAGNOSTIC_LINES:
        safe = "\n".join(lines[-MAX_DIAGNOSTIC_LINES:])
    return safe[-MAX_DIAGNOSTIC_CHARS:]


def _lint_command(config: dict[str, Any]) -> tuple[str | None, str | None]:
    tooling = config.get("tooling")
    if tooling is None:
        return None, None
    if not isinstance(tooling, dict):
        return None, "tooling configuration is malformed"
    commands = tooling.get("commands")
    if commands is None:
        return None, None
    if not isinstance(commands, dict):
        return None, "tooling.commands configuration is malformed"
    value = commands.get("lint")
    if value is None or (isinstance(value, str) and not value.strip()):
        return None, None
    if not isinstance(value, str):
        return None, "tooling.commands.lint is malformed"
    return value, None


def _failed_open(outcome: str, message: str) -> tuple[str, str]:
    return outcome, message


def verify(payload: dict[str, Any]) -> tuple[str, str]:
    """Return ``(outcome, message)`` without writing a hook response."""
    if not isinstance(payload, dict):
        return _failed_open(INTERNAL_ERROR, "malformed Stop hook payload")
    if payload.get("stop_hook_active") is True:
        return ALLOW, "stop hook already active"

    try:
        config = gp.load(payload=payload)
        command, config_error = _lint_command(config)
        if config_error:
            return _failed_open(INTERNAL_ERROR, config_error)
        if command is None:
            return _failed_open(SKIP_NOT_DECLARED, "no lint command is declared")

        changes: ChangeSet = collect_change_set(payload)
        # Only an assessed empty set is clean. An assessment failure still reaches the declared
        # lint command, which is the safe direction for a verifier fault.
        if changes.assessed and not changes.paths:
            return ALLOW, "clean tree"

        project = changes.project_dir
        if project is None:
            try:
                project = gp.project_dir(payload)
            except Exception:
                project = None
        missing = gp.missing_tool(command)
        if missing:
            return _failed_open(SKIP_UNAVAILABLE, f"declared linter is unavailable: {missing}")

        lint_opt_in = gp.opt_in("LINT", config)
        if gp.opted_in("LINT", "", config):
            return ALLOW, "lint failure released by the project opt-in"

        # The repository config is the executable command authority. shell=True is deliberate so
        # its declared package-script and compound-command semantics remain intact.
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(project) if project is not None else None,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=LINT_TIMEOUT_S,
            check=False,
        )
        # Native shells use 127 for command-not-found; cmd.exe commonly uses 9009. These are
        # tooling availability failures, not lint findings, and therefore fail open.
        if result.returncode in (126, 127, 9009):
            return _failed_open(SKIP_UNAVAILABLE, "declared linter could not be launched")
        if result.returncode == 0:
            return ALLOW, "linter passed"
        detail = _diagnostic(result.stdout or "", result.stderr or "")
        suffix = f"\n\n{detail}" if detail else ""
        return DENY, f"linter exited with code {result.returncode}; set {lint_opt_in}=1 to allow{suffix}"
    except subprocess.TimeoutExpired:
        return _failed_open(TIMEOUT, "declared linter timed out")
    except (FileNotFoundError, PermissionError):
        return _failed_open(SKIP_UNAVAILABLE, "declared linter could not be launched")
    except Exception:
        return _failed_open(INTERNAL_ERROR, "Stop verifier failed internally")


def _emit(outcome: str, message: str, payload: dict[str, Any]) -> None:
    if outcome in (ALLOW, SKIP_NOT_DECLARED):
        return
    text = f"[{outcome}] {message}"
    if _is_cursor_payload(payload):
        if outcome != DENY:
            return
        print(json.dumps({"followup_message": text}))
    elif outcome == DENY:
        print(json.dumps({"decision": "block", "reason": text}))
    else:
        print(json.dumps({"systemMessage": text}))


def main() -> None:
    payload, valid = read_input()
    if not valid:
        _emit(INTERNAL_ERROR, "malformed Stop hook payload", {})
        return
    try:
        outcome, message = verify(payload)
        _emit(outcome, message, payload)
    except Exception:
        _emit(INTERNAL_ERROR, "Stop verifier failed internally", payload)


if __name__ == "__main__":
    main()
    sys.exit(0)
