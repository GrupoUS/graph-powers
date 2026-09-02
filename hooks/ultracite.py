#!/usr/bin/env python3
"""Run the project's local Oxfmt formatter on one changed file, and nothing else.

Branches on `hook_event_name` from the stdin payload:

  • PostToolUse (Write|Edit) → run `tooling.commands.format` on the edited file
**It is opt-in by configuration.** A project that declares no formatter is not formatted.

**The formatter needs a local tool.** `tooling.commands.format` names Oxfmt or a local package
script that invokes it; this hook runs it and nothing more. Network-capable launchers are rejected,
so an edit hook can never fetch code. If the tool is absent, the hook fails open and formats nothing;
the declared gate remains responsible for reporting unavailable tooling.

A harness may enforce the project's formatting command; it may not impose its author's.

Why format only, never lint or fix, on PostToolUse:
  Oxfmt format only touches formatting. Lint auto-fix is intentionally never used here: across
  multi-step edits, code added in one step may not be complete until the next step, so a fixer
  can remove or rewrite code that is about to receive its usage.

  The hook therefore applies only the declared Oxfmt formatting rules to the edited file.

Trigger:
  PostToolUse (Write|Edit) — format mode

Always fails open: any internal error → exit 0 (never wedge a session).
"""

import json
import os
import shlex
import shutil
import subprocess
import sys
import typing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _config as gp
import command_trust

# The payload arrives on stdin as UTF-8, but Python decodes it with the locale code page unless
# told otherwise — cp1252 on a Windows machine. A file path or a branch name outside that page
# then raises `UnicodeDecodeError`, every hook here falls open, and `protect_files` permits a
# write it was meant to refuse. Reconfiguring costs nothing and is guarded because a stdin that
# is already detached has no `reconfigure`.
try:
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
except Exception:
    pass


FORMATTABLE_EXTENSIONS = {
    ".ts",
    ".tsx",
    ".mts",
    ".cts",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".json",
    ".jsonc",
    ".css",
    ".scss",
    ".sass",
    ".less",
}
FORMAT_TIMEOUT_S = 15
NETWORK_LAUNCHERS = {
    "bunx",
    "bunx.exe",
    "bunx.cmd",
    "npx",
    "npx.exe",
    "npx.cmd",
    "pnpx",
    "pnpx.exe",
    "pnpx.cmd",
    "dlx",
    "dlx.exe",
    "dlx.cmd",
}


def read_input() -> dict[str, object]:
    try:
        raw = sys.stdin.read()
        return typing.cast(dict[str, object], json.loads(raw)) if raw.strip() else {}
    except Exception:
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# PostToolUse — run the declared formatter on a single file
# ─────────────────────────────────────────────────────────────────────────────
def run_format(data: dict[str, object]) -> None:
    """Format one edited file with the command the project declared. No declaration, no formatting."""
    cfg = gp.load(payload=data)
    command = ((cfg.get("tooling") or {}).get("commands") or {}).get("format")
    if not isinstance(command, str) or not command.strip():
        return  # the project formats itself, or does not format. Either way, not our call.

    file_path = gp.file_path_from_payload(data)
    if not file_path:
        return
    project = gp.project_dir(data)
    target = Path(file_path)
    if not target.is_absolute():
        target = project / target
    if target.suffix.lower() not in FORMATTABLE_EXTENSIONS:
        return

    try:
        root = project.resolve(strict=True)
        target = target.resolve(strict=False)
        if not target.is_relative_to(root):
            return
    except Exception:
        return

    parts = safe_format_argv(command, project)
    if not parts:
        return

    # A repository config can declare arbitrary shell commands. Require a separate machine-local
    # approval for the exact config before even checking or launching the formatter.
    if not command_trust.is_trusted(project):
        return

    # Declared is not installed. Checking first turns "silently never formats" into a line
    # `session_context.py` already prints at every session start.
    local_runner = _is_local_runner(parts)
    if not local_runner and gp.missing_tool(command):
        return

    try:
        subprocess.run(
            [*parts, str(target)],
            capture_output=True,
            timeout=FORMAT_TIMEOUT_S,
            cwd=str(project),
            check=False,
        )
    except FileNotFoundError:
        return  # the declared formatter is not installed; the session tag says so
    except Exception:
        pass


def argv_for(command: str) -> list[str]:
    """A declared command string, split into argv that starts on every platform.

    Three things go wrong without this, and all three are silent — the caller swallows the
    exception and the formatter simply never runs again:

    - `shlex.split` in POSIX mode treats `\\` as an escape, so a Windows path in
      `tooling.commands.format` (`C:\\tools\\oxfmt.exe --write`) splits into a malformed Windows path.
    - `CreateProcess` only completes `.exe`, and package-manager shims are `.cmd`. `shutil.which`
      resolves them because it honours `PATHEXT`; the resolved path is used for direct Oxfmt calls.
    - A quoted first token survives POSIX splitting but not the Windows one, so it is unwrapped
      here rather than handed to the OS with its quotes on.
    """
    parts = shlex.split(str(command), posix=(os.name != "nt"))
    parts = [p[1:-1] if len(p) > 1 and p[0] == p[-1] == '"' else p for p in parts]
    if parts:
        parts[0] = shutil.which(parts[0]) or parts[0]
    return parts


def _is_local_runner(parts: list[str]) -> bool:
    """Whether the command resolves a project-local formatting script."""
    if not parts:
        return False
    first = Path(parts[0]).name.lower()
    if first not in {"bun", "bun.exe", "npm", "npm.exe", "pnpm", "pnpm.exe", "yarn", "yarn.exe"}:
        return False
    lowered = [part.lower() for part in parts]
    return any(
        part == "run" and index + 1 < len(lowered) and lowered[index + 1] in {"format", "fmt"}
        for index, part in enumerate(lowered[1:], 1)
    )


def _is_network_launcher(parts: list[str]) -> bool:
    """Reject commands whose normal behavior can install a package."""
    if not parts:
        return False
    names = [Path(part).name.lower() for part in parts]
    if names[0] in NETWORK_LAUNCHERS:
        return "--no-install" not in {part.lower() for part in parts}
    return any(name in {"dlx", "x", "exec"} for name in names[1:])


def _package_script_body(root: Path | None, parts: list[str]) -> str | None:
    if root is None or not parts:
        return None
    names = [Path(part).name.lower() for part in parts]
    try:
        run_index = next(index for index, name in enumerate(names) if name == "run")
        script_name = parts[run_index + 1]
    except (StopIteration, IndexError):
        return None
    try:
        package = json.loads((root / "package.json").read_text(encoding="utf-8"))
        scripts = package.get("scripts") if isinstance(package, dict) else None
        value = scripts.get(script_name) if isinstance(scripts, dict) else None
        return value if isinstance(value, str) else None
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None


def _is_oxfmt_format(parts: list[str]) -> bool:
    if not parts:
        return False
    names = [Path(part).name.lower() for part in parts]
    flags = {part.lower() for part in parts}
    if any(part in {"&&", "||", ";", "|", "&", "check", "lint", "fix"} for part in names):
        return False
    if "--write" not in flags or "--fix" in flags:
        return False
    return "oxfmt" in names


def safe_format_argv(command: str, project_root: Path | None = None) -> list[str]:
    """Return one local-only format command, rejecting lint, autofix and network commands."""
    try:
        parts = argv_for(command)
    except Exception:
        return []
    if not parts or _is_network_launcher(parts):
        return []
    if _is_local_runner(parts):
        body = _package_script_body(project_root, parts)
        try:
            body_parts = argv_for(body) if body else []
        except Exception:
            body_parts = []
        return parts if _is_oxfmt_format(body_parts) else []
    return parts if _is_oxfmt_format(parts) else []


# ─────────────────────────────────────────────────────────────────────────────
# Dispatch
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    data: dict[str, object] = read_input()
    event = gp.hook_event(data)

    # Explicit override via CLI arg ("format") for manual testing
    if len(sys.argv) > 1:
        event_override = sys.argv[1].strip().lower()
        if event_override == "format":
            event = "PostToolUse"

    try:
        if event == "PostToolUse":
            run_format(data)
        # Unknown / missing event: silent no-op (fail open)
    except Exception:
        pass


if __name__ == "__main__":
    main()
    sys.exit(0)
