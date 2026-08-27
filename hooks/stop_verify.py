#!/usr/bin/env python3
"""Run the configured project linter before a Stop event, fail-open on hook/tool faults."""

from __future__ import annotations

import json
import subprocess
import sys
import typing
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _config as gp
import command_trust
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
SKIP_UNTRUSTED = "SKIP_UNTRUSTED"
INTERNAL_ERROR = "INTERNAL_ERROR"
TIMEOUT = "TIMEOUT"

LINT_TIMEOUT_S = 25


def read_input() -> tuple[dict[str, Any], bool]:
    try:
        raw = sys.stdin.read()
        value = json.loads(raw) if raw.strip() else None
        if not isinstance(value, dict):
            return {}, False
        return typing.cast(dict[str, Any], value), True
    except Exception:
        return {}, False


def _is_cursor_client() -> bool:
    """Cursor is selected only by the marker emitted by its generated adapter."""
    args = sys.argv[1:]
    return any(args[index:index + 2] == ["--graph-powers-client", "cursor"]
               for index in range(len(args) - 1))


def _safe_opt_in(config: dict[str, Any]) -> str:
    """Return a schema-shaped key; malformed config values never reach model-facing output."""
    try:
        key = gp.opt_in("LINT", config)
        if key and key.isascii() and key[0].isalpha() and all(
            char.isalnum() or char == "_" for char in key
        ):
            return key
    except Exception:
        pass
    return "GRAPHPOWERS_ALLOW_LINT"


def _safe_deny_message(message: str) -> str:
    """Keep only the integer exit code and schema-shaped opt-in from a verifier result."""
    marker = "lint failed with exit code "
    if not isinstance(message, str) or not message.startswith(marker):
        return "lint failed"
    remainder = message[len(marker):]
    code_text, separator, key_text = remainder.partition("; set ")
    if not separator or not code_text or not (
        code_text.isdigit() or (code_text.startswith("-") and code_text[1:].isdigit())
    ):
        return "lint failed"
    if not key_text.endswith("=1 to allow"):
        return "lint failed"
    key = key_text[:-len("=1 to allow")]
    if not key or not key.isascii() or not key[0].isalpha() or not all(
        char.isalnum() or char == "_" for char in key
    ):
        return "lint failed"
    return f"lint failed with exit code {code_text}; set {key}=1 to allow"


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
            return _failed_open(INTERNAL_ERROR, "malformed Stop verifier configuration")
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
        if project is None or not command_trust.is_trusted(project):
            return _failed_open(SKIP_UNTRUSTED, "configured command is not approved")
        missing = gp.missing_tool(command)
        if missing:
            return _failed_open(SKIP_UNAVAILABLE, "declared linter is unavailable")

        lint_opt_in = _safe_opt_in(config)
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
        code = result.returncode if isinstance(result.returncode, int) else 1
        return DENY, f"lint failed with exit code {code}; set {lint_opt_in}=1 to allow"
    except subprocess.TimeoutExpired:
        return _failed_open(TIMEOUT, "declared linter timed out")
    except (FileNotFoundError, PermissionError):
        return _failed_open(SKIP_UNAVAILABLE, "declared linter could not be launched")
    except Exception:
        return _failed_open(INTERNAL_ERROR, "Stop verifier failed internally")


def _emit(outcome: str, message: str, payload: dict[str, Any]) -> None:
    if outcome in (ALLOW, SKIP_NOT_DECLARED):
        return
    fixed = {
        SKIP_UNTRUSTED: "configured command is not approved",
        SKIP_UNAVAILABLE: "declared linter is unavailable",
        TIMEOUT: "declared linter timed out",
        INTERNAL_ERROR: "Stop verifier failed internally",
    }
    summary = _safe_deny_message(message) if outcome == DENY else fixed.get(
        outcome, "Stop verifier failed internally"
    )
    text = f"[{outcome}] {summary}"
    if _is_cursor_client():
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
