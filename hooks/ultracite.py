#!/usr/bin/env python3
"""ultracite.py - run the project's own formatter and linter, and nothing else.

Branches on `hook_event_name` from the stdin payload:

  • PostToolUse (Write|Edit) → run `tooling.commands.format` on the edited file
  • Stop                     → run `tooling.commands.lint` over the modified files and, on
                               errors, block the stop with the tail of the output

**Both are opt-in by configuration.** A project that declares no formatter is not formatted, and a
project that declares no linter is not linted. This used to shell out to `bunx biome format --write`
and `bunx oxlint` unconditionally, which meant installing the plugin silently rewrote every edited
file with one specific formatter's defaults — in repositories that had chosen Prettier, or dprint,
or nothing — and downloaded that formatter from npm to do it. A harness may enforce the project's
rules; it may not impose its author's.

Why format only, never fix, on PostToolUse:
  `biome check --write` runs the linter + assists with auto-fix. Rules like
  `noUnusedImports` (level error, fix safe) DELETE imports they consider
  unused. Across multi-step edits, an import added in step N may not have
  its usage code written until step N+1 — Biome would remove it between
  steps and cascade errors. `biome format --write` only touches whitespace,
  indentation, quotes, semicolons, trailing commas, line width.

  Lint auto-fix is intentionally never used here for the same reason: at Stop the lint is
  read-only, and it reports rather than repairs.

Triggers:
  PostToolUse (Write|Edit) — format mode
  Stop                     — lint check mode

Always fails open: any internal error → exit 0 (never wedge a session).
"""

import json
import os
import re
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
LINT_EXTENSIONS = (".ts", ".tsx", ".js", ".jsx")
MAX_LINT_FILES = 20
LINT_TIMEOUT_S = 30
FORMAT_TIMEOUT_S = 30
GIT_DIFF_TIMEOUT_S = 10


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

    file_path = str(
        data.get("file_path")
        or typing.cast(dict[str, object], data.get("tool_input", {})).get(
            "file_path", ""
        )
    )
    if not file_path:
        return
    if Path(file_path).suffix.lower() not in FORMATTABLE_EXTENSIONS:
        return

    try:
        subprocess.run(
            [*argv_for(command), file_path],
            capture_output=True,
            timeout=FORMAT_TIMEOUT_S,
            cwd=str(gp.project_dir(data)),
            check=False,
        )
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Stop — run the declared linter over git-modified files; block on errors
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
def get_modified_files(cwd: str | None = None) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=GIT_DIFF_TIMEOUT_S,
            cwd=cwd,          # the project, not wherever this hook happens to have been started
            check=False,
        )
        files = result.stdout.strip().splitlines()
        return [f for f in files if f.endswith(LINT_EXTENSIONS)][:MAX_LINT_FILES]
    except Exception:
        return []


def run_check(data: dict[str, object]) -> None:
    # Avoid infinite stop-hook loop
    if data.get("stop_hook_active") is True:
        return

    modified = get_modified_files()
    if not modified:
        return

    cfg = gp.load(payload=data)
    lint_command = ((cfg.get("tooling") or {}).get("commands") or {}).get("lint")
    if not lint_command:
        return  # the project declares no linter; there is nothing to enforce

    try:
        result = subprocess.run(
            [*argv_for(lint_command), *modified],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=LINT_TIMEOUT_S,
            cwd=str(gp.project_dir(data)),
            check=False,
        )
        raw_output = result.stdout + result.stderr
    except Exception:
        return  # a linter that cannot run does not get to block the session

    error_match = re.search(r"(\d+) error", raw_output)
    error_count = int(error_match.group(1)) if error_match else 0
    if error_count <= 0:
        return

    truncated = "\n".join(raw_output.splitlines()[-30:])[:2000]
    print(
        json.dumps(
            {
                "decision": "block",
                "reason": f"The project's linter reported {error_count} error(s). Fix them before stopping:\n\n{truncated}",
            }
        )
    )


# ─────────────────────────────────────────────────────────────────────────────
# Dispatch
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    data: dict[str, object] = read_input()
    event = str(data.get("hook_event_name", "")).strip()

    # Explicit override via CLI arg ("format" | "check") for manual testing
    if len(sys.argv) > 1:
        event_override = sys.argv[1].strip().lower()
        if event_override == "format":
            event = "PostToolUse"
        elif event_override == "check":
            event = "Stop"

    try:
        if event == "PostToolUse":
            run_format(data)
        elif event == "Stop":
            run_check(data)
        # Unknown / missing event: silent no-op (fail open)
    except Exception:
        pass


if __name__ == "__main__":
    main()
    sys.exit(0)
