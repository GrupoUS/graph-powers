#!/usr/bin/env python3
"""Run trusted project verification before agent-issued Git writes.

This is deliberately the one PreToolUse owner for both the new core gates and the legacy
``preCommitAudit`` command. It is a fail-open lifecycle guard: only a command that actually
starts and returns a non-zero status blocks the Git call. Configuration, trust, fingerprint,
cache and environment failures are reported as fixed skip reasons and never wedge a session.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import signal
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _change_set as change_set
import _config as gp
import command_trust

try:
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
except Exception:
    pass


GIT_WRITE_RE = re.compile(r"(^|[\s;|&()])git\s+(commit|push)(\s|$)")
CORE_GATES = ("typeCheck", "lint", "test", "build")
DEFAULT_TIMEOUT = 120
MAX_TIMEOUT = 600
DEFAULT_CACHE_SECONDS = 300


def _action(command: str) -> str:
    match = GIT_WRITE_RE.search(command)
    return match.group(2) if match else ""


def _config_digest(project: Path) -> str | None:
    try:
        path = gp.config_path(project)
        if path is None:
            return None
        return hashlib.sha256(path.read_bytes()).hexdigest()[:12]
    except Exception:
        return None


def _skip(reason: str, gate: str, digest: str | None = None) -> None:
    """Emit only fixed, model-safe information to the hook's stderr."""
    suffix = f" {digest}" if reason == "SKIP_UNTRUSTED" and digest else ""
    print(f"[{reason}] {gate} skipped{suffix}", file=sys.stderr)


def _deny(gate: str, code: int, cfg: dict[str, Any]) -> None:
    action = "VERIFY" if gate != "audit" else "AUDIT"
    candidate = gp.opt_in(action, cfg)
    key = candidate
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", candidate):
        key = f"GRAPHPOWERS_ALLOW_{action}"
    print(f"DENY {gate} {int(code)} {key}", file=sys.stderr)


def _integer(value: Any, default: int, maximum: int) -> int | None:
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
        return None
    return value


def _cache_seconds(value: Any) -> int | None:
    if value is None:
        return DEFAULT_CACHE_SECONDS
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 86400:
        return None
    return value


def _core_plan(cfg: dict[str, Any]) -> tuple[str, list[tuple[str, str]], int, int] | None:
    """Resolve the strict core schema, returning ``None`` for an explicit malformed shape."""
    gates = cfg.get("gates")
    if "gates" in cfg and gates is None:
        return None
    if gates is None:
        gates = {}
    if not isinstance(gates, dict):
        return None
    if "preCommit" in gates and gates["preCommit"] is None:
        return None
    raw = gates.get("preCommit")
    if raw is not None and not isinstance(raw, dict):
        return None
    block = raw if isinstance(raw, dict) else {}
    if any(key not in {"enabled", "commands", "scope", "timeoutTotal", "cacheSeconds"}
           for key in block):
        return None
    enabled = block.get("enabled", True)
    if not isinstance(enabled, bool):
        return None
    timeout = _integer(block.get("timeoutTotal"), DEFAULT_TIMEOUT, MAX_TIMEOUT)
    cache = _cache_seconds(block.get("cacheSeconds"))
    if ("timeoutTotal" in block and block["timeoutTotal"] is None) or (
            "cacheSeconds" in block and block["cacheSeconds"] is None):
        return None
    if timeout is None or cache is None:
        return None

    tooling = cfg.get("tooling", {})
    if "tooling" in cfg and tooling is None:
        return None
    if tooling is None:
        tooling = {}
    if not isinstance(tooling, dict):
        return None
    commands_cfg = tooling.get("commands", {})
    if "commands" in tooling and commands_cfg is None:
        return None
    if commands_cfg is None:
        commands_cfg = {}
    if not isinstance(commands_cfg, dict):
        return None
    declared: dict[str, str] = {}
    for name, command in commands_cfg.items():
        if name in CORE_GATES and isinstance(command, str) and command.strip():
            declared[name] = command
        elif name in CORE_GATES:
            return None

    scope = block.get("scope", "worktree")
    if scope != "worktree":
        return None
    selected = block.get("commands")
    if "commands" in block and selected is None:
        return None
    if selected is None:
        names = [name for name in CORE_GATES if name in declared]
    else:
        if not isinstance(selected, list) or any(
            not isinstance(name, str) or name not in CORE_GATES for name in selected
        ):
            return None
        names = [name for name in CORE_GATES if name in selected and name in declared]
    return ("enabled" if enabled else "disabled", [(name, declared[name]) for name in names],
            timeout, cache)


def _audit_plan(cfg: dict[str, Any]) -> tuple[str, int, bool] | None:
    gates = cfg.get("gates")
    if gates is None:
        return None
    if not isinstance(gates, dict) or "preCommitAudit" not in gates:
        return None
    raw = gates.get("preCommitAudit")
    if isinstance(raw, str):
        command, timeout_value, cache_value = raw, None, False
    elif isinstance(raw, dict):
        command = raw.get("command")
        timeout_value = raw.get("timeout")
        cache_value = raw.get("cache", False)
        if not isinstance(cache_value, bool):
            return None
    else:
        return None
    if not isinstance(command, str) or not command.strip():
        return None
    timeout = _integer(timeout_value, DEFAULT_TIMEOUT, MAX_TIMEOUT)
    if timeout is None:
        return None
    return command, timeout, cache_value


def _missing_executable(command: str) -> bool:
    """Recognize a shell missing-command status without treating explicit exit as absent."""
    try:
        parts = shlex.split(command, posix=sys.platform != "win32")
        if not parts:
            return True
        first = parts[0].strip("\"'")
        if first.lower() in {"cd", "echo", "exit", "false", "printf", "set", "test", "true"}:
            return False
        if "/" in first or "\\" in first:
            return not Path(first).is_file()
        return shutil.which(first) is None
    except Exception:
        return False


def _terminate_process_tree(process: subprocess.Popen) -> None:
    """Stop a timed-out shell and the child it launched on every supported platform."""
    try:
        if sys.platform == "win32":
            # `subprocess.run(..., shell=True)` only terminates cmd.exe on Windows. The child can
            # keep the capture pipes open, so the caller appears to ignore its deadline. taskkill's
            # tree flag is the native equivalent of killing a POSIX process group.
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=1,
                check=False,
            )
        else:
            os.killpg(process.pid, signal.SIGKILL)
    except Exception:
        try:
            process.kill()
        except OSError:
            pass


def _run_shell_command(command: str, project: Path, timeout: float) -> subprocess.CompletedProcess:
    """Run a trusted shell command without allowing a child to outlive its timeout."""
    options: dict[str, Any] = {
        "shell": True,
        "cwd": str(project),
        # Gate output is deliberately never forwarded. DEVNULL also prevents a Windows child
        # from keeping capture pipes open after cmd.exe is terminated on timeout.
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if sys.platform == "win32":
        options["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    else:
        options["start_new_session"] = True
    process = subprocess.Popen(command, **options)
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        _terminate_process_tree(process)
        try:
            process.wait(timeout=0.5)
        except subprocess.TimeoutExpired:
            try:
                process.kill()
            except OSError:
                pass
            try:
                process.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                pass
        raise
    return subprocess.CompletedProcess(command, process.returncode)


def _run_configured(
    *,
    gate: str,
    command: str,
    project: Path,
    cfg: dict[str, Any],
    request_command: str,
    deadline: float,
    cache_seconds: int,
    cache_enabled: bool,
) -> str:
    """Return one internal outcome; only ``deny`` is fail-closed."""
    try:
        action = "AUDIT" if gate == "audit" else "VERIFY"
        if not command_trust.is_trusted(project):
            _skip("SKIP_UNTRUSTED", gate, _config_digest(project))
            return "skipped"
        if gp.opted_in(action, request_command, cfg):
            return "opted-out"
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            _skip("TIMEOUT", gate)
            return "skipped"
        fingerprint = change_set.fingerprint_worktree(
            project, gate, command,
            deadline=min(deadline, time.monotonic() + change_set.FINGERPRINT_BUDGET_S),
        )
        if fingerprint and cache_enabled and cache_seconds > 0 and change_set.cache_lookup(
            project, gate, fingerprint, cache_seconds
        ):
            return "cached"
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            _skip("TIMEOUT", gate)
            return "skipped"
        try:
            result = _run_shell_command(command, project, remaining)
        except subprocess.TimeoutExpired:
            _skip("TIMEOUT", gate)
            return "skipped"
        except (FileNotFoundError, OSError):
            _skip("SKIP_UNAVAILABLE", gate)
            return "skipped"
        except Exception:
            _skip("INTERNAL_ERROR", gate)
            return "skipped"
        missing_status = result.returncode in (127, 9009)
        if sys.platform == "win32" and result.returncode == 1:
            missing_status = True
        if missing_status and _missing_executable(command):
            _skip("SKIP_UNAVAILABLE", gate)
            return "skipped"
        if result.returncode != 0:
            _deny(gate, result.returncode, cfg)
            return "deny"
        if fingerprint and cache_enabled and cache_seconds > 0:
            change_set.cache_store(project, gate, fingerprint)
        return "pass"
    except Exception:
        _skip("INTERNAL_ERROR", gate)
        return "skipped"


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    if not isinstance(payload, dict):
        return 0
    command = gp.bash_command(payload)
    action = _action(command)
    if not action:
        return 0
    try:
        project = gp.project_dir(payload)
        cfg = gp.load(payload=payload)
        digest = _config_digest(project)
        core_plan = _core_plan(cfg)
        blocked = False
        audit_deadline = time.monotonic() + DEFAULT_TIMEOUT
        if action == "commit":
            combined_timeout = core_plan[2] if core_plan is not None else DEFAULT_TIMEOUT
            commit_deadline = time.monotonic() + combined_timeout
            if core_plan is None:
                _skip("SKIP_CONFIG", "preCommit", digest)
            elif core_plan[0] == "enabled":
                for gate, gate_command in core_plan[1]:
                    outcome = _run_configured(
                        gate=gate, command=gate_command, project=project, cfg=cfg,
                        request_command=command,
                        deadline=commit_deadline, cache_seconds=core_plan[3], cache_enabled=True,
                    )
                    if outcome == "deny":
                        blocked = True
                    if time.monotonic() >= commit_deadline:
                        break
            audit_deadline = commit_deadline

        audit_declared = isinstance(cfg.get("gates"), dict) and "preCommitAudit" in cfg["gates"]
        audit = _audit_plan(cfg)
        if audit is None:
            if audit_declared:
                _skip("SKIP_CONFIG", "audit", digest)
            return 2 if blocked else 0
        audit_command, audit_timeout, audit_cache = audit
        if action == "push":
            audit_deadline = time.monotonic() + audit_timeout
        else:
            audit_deadline = min(audit_deadline, time.monotonic() + audit_timeout)
        outcome = _run_configured(
            gate="audit", command=audit_command, project=project, cfg=cfg,
            request_command=command,
            deadline=audit_deadline,
            cache_seconds=(core_plan[3] if core_plan is not None else DEFAULT_CACHE_SECONDS),
            cache_enabled=audit_cache,
        )
        return 2 if blocked or outcome == "deny" else 0
    except Exception:
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
