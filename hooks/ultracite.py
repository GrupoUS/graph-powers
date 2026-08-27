#!/usr/bin/env python3
"""ultracite.py - run the project's own formatter, and nothing else.

Branches on `hook_event_name` from the stdin payload:

  • PostToolUse (Write|Edit) → run `tooling.commands.format` on the edited file
**It is opt-in by configuration.** A project that declares no formatter is not formatted.

**The formatter needs the tool itself to be installed.** `tooling.commands.format` names the
command; this hook runs it and nothing more. If the command is `bunx biome check --write` and
`biome` is not on PATH, the run raises `FileNotFoundError`, this hook
fails open as it must, and the session goes on editing files that are never formatted — for hours,
with nothing on screen. So the miss is now detected before the run rather than swallowed after it,
and `session_context.py` names it at the start of every session:

    | NOT INSTALLED: lint needs `oxlint`, format needs `biome` — install globally or these never run

Installing globally is the fix, and global is the point: these run against whatever repository the
session is in, including one that does not carry them as dependencies.

    bun add -g @biomejs/biome oxlint      # or: npm i -g @biomejs/biome oxlint
    biome --version && oxlint --version   # both must answer

A harness may enforce the project's formatting command; it may not impose its author's.

Why format only, never fix, on PostToolUse:
  `biome check --write` runs the linter + assists with auto-fix. Rules like
  `noUnusedImports` (level error, fix safe) DELETE imports they consider
  unused. Across multi-step edits, an import added in step N may not have
  its usage code written until step N+1 — Biome would remove it between
  steps and cascade errors. `biome format --write` only touches whitespace,
  indentation, quotes, semicolons, trailing commas, line width.

  Lint auto-fix is intentionally never used here for the same reason: the formatter only applies
  the declared formatting rules to the edited file.

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

# The payload arrives on stdin as UTF-8, but Python decodes it with the locale code page unless
# told otherwise — cp1252 on a Windows machine. A file path or a branch name outside that page
# then raises `UnicodeDecodeError`, every hook here falls open, and `protect_files` permits a
# write it was meant to refuse. Reconfiguring costs nothing and is guarded because a stdin that
# is already detached has no `reconfigure`.
try:
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
except Exception:
    pass


FORMATTABLE_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".json", ".css", ".scss", ".astro", ".vue", ".svelte", ".py", ".go", ".rs"}
FORMAT_TIMEOUT_S = 30


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
    if not command:
        return  # the project formats itself, or does not format. Either way, not our call.

    file_path = gp.file_path_from_payload(data)
    if not file_path:
        return
    if Path(file_path).suffix.lower() not in FORMATTABLE_EXTENSIONS:
        return

    # Declared is not installed. Checking first turns "silently never formats" into a line
    # `session_context.py` already prints at every session start.
    if gp.missing_tool(str(command)):
        return

    try:
        subprocess.run(
            [*argv_for(command), file_path],
            capture_output=True,
            timeout=FORMAT_TIMEOUT_S,
            cwd=str(gp.project_dir(data)),
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
      `tooling.commands.format` (`C:\\tools\\biome.exe format`) splits into `C:toolsbiome.exe`.
    - `CreateProcess` only completes `.exe`, and the npm/bun/pnpm shims are `.cmd`. `shutil.which`
      resolves them because it honours `PATHEXT`; a bare `"bunx"` raises `FileNotFoundError`.
    - A quoted first token survives POSIX splitting but not the Windows one, so it is unwrapped
      here rather than handed to the OS with its quotes on.
    """
    parts = shlex.split(str(command), posix=(os.name != "nt"))
    parts = [p[1:-1] if len(p) > 1 and p[0] == p[-1] == '"' else p for p in parts]
    if parts:
        parts[0] = shutil.which(parts[0]) or parts[0]
    return parts


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
