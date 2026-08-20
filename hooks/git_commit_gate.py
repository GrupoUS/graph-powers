#!/usr/bin/env python3
"""git_commit_gate.py - PreToolUse/Bash gate for `git commit`.

Why this exists
---------------
`${CLAUDE_PLUGIN_ROOT}/references/safety-floor.md` §1 makes it a [HARD] rule that nothing is
committed or pushed without the user asking in the current turn. On 2026-08-04 a
delegated subagent ran `git pull`, `git commit` and `git push` anyway, despite a
prompt that said not to. Prompt text is not enforcement.

Why it is shaped this way
-------------------------
A hook cannot tell a subagent apart from the main thread: subagents run
in-process and inherit an identical environment (same CLAUDE_CODE_SESSION_ID,
same CLAUDE_PID) — verified empirically. So instead of asking *who* is calling,
this gate asks whether the caller deliberately opted in for this one command.

The opt-in is an inline env assignment that must appear in the command itself:

    <PREFIXO>_ALLOW_COMMIT=1 git commit -m "..."

The main thread adds that prefix only after the user approves in the current
turn. A subagent following a normal "implement X" prompt has no reason to write
it, so the accidental-commit path is closed.

Scope and honesty about it
--------------------------
This is a guardrail, not a sandbox: anything that can read this file can also
read the opt-in. `git push` is not handled here — it has its own gate with the
same shape, `git_push_gate.py` (opt-in `<PREFIXO>_ALLOW_PUSH=1`, plus a second
key for `main`). It used to sit in `permissions.deny` instead, but a `deny` also
blocked the pushes the user themself approved, with no way to lift it per turn.

Contract: exit 0 allows; a `permissionDecision: "deny"` payload blocks and shows
`permissionDecisionReason` to the model. Never blocks on its own failure.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import cast

# Project parameters (branch, protected branches, opt-in prefix) come from
# the project config via `_config`, never hardcoded — this
# file is byte-for-byte the same in every repository that installs the plugin.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _config as gp

# The payload arrives on stdin as UTF-8, but Python decodes it with the locale code page unless
# told otherwise — cp1252 on a Windows machine. A branch name or path outside that page then
# raises `UnicodeDecodeError`, the hook falls open, and a gate that should have denied releases.
try:
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
except Exception:
    pass



OPT_IN = f"{gp.opt_in('COMMIT')}=1"

# `git` must sit in command position — start of string, or after a separator,
# optionally behind env assignments. Without that anchor a read-only
# `grep -rn "git commit" docs/` matches the quoted text and gets blocked.
# Tolerates `git -C <path> commit` and extra spacing. Word-boundary on the verb
# keeps `git commit-graph` out.
_SEPARATOR = r"(?:^|[;&|(\n])\s*"
_ENV_ASSIGNMENTS = r"(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*"
_GIT_GLOBAL_FLAGS = r"(?:\s+-[^\s]+(?:\s+[^\s]+)?)*"
COMMIT_RE = re.compile(
    rf"{_SEPARATOR}{_ENV_ASSIGNMENTS}git\b{_GIT_GLOBAL_FLAGS}\s+commit\b"
)

# Read-only inspections that merely contain the word.
SAFE_RE = re.compile(r"\bgit\s+commit\s+--dry-run\b|\bgit\s+commit-graph\b")

REASON = (
    "Blocked by the graph-powers git_commit_gate.\n"
    "\n"
    "safety-floor.md §1 [HARD]: nothing is committed unless the user asked for it in the\n"
    "current turn. This gate exists because a subagent once committed and pushed on its own.\n"
    "\n"
    "If — and only if — the user approved the commit IN THIS TURN, repeat the command\n"
    "with the explicit opt-in:\n"
    f"    {OPT_IN} git commit -m \"...\"\n"
    "  Not in a POSIX shell? The hook matches the key as TEXT, not as syntax, so\n"
    "  `$env:<KEY>=1; <command>` (PowerShell) and `set <KEY>=1 && <command>` (cmd)\n"
    "  release it just as well.\n"
    "\n"
    "If you are a subagent: do NOT use the opt-in. Stop, leave the changes in the working\n"
    "tree, and report the changed paths to the orchestrator."
)


def deny(reason: str) -> None:
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        },
        sys.stdout,
    )
    print()  # the hook payload must be newline-terminated


def main() -> int:
    try:
        # `cast` (not a bare annotation) is what stops the Any from leaking into
        # every downstream `.get()`.
        payload = cast("object", json.load(sys.stdin))
    except (ValueError, OSError, RecursionError):
        # A gate that crashes must not become a gate that blocks everything.
        # json.load raises JSONDecodeError/UnicodeDecodeError (both ValueError),
        # OSError if stdin is unreadable, RecursionError on pathological nesting.
        return 0

    # Anything that is not the shape we expect is not our business — allow it.
    # Without these isinstance guards a non-dict payload raised AttributeError
    # and the gate exited 1 with a traceback instead of quietly standing down.
    if not isinstance(payload, dict):
        return 0
    tool_input = cast("dict[str, object]", payload).get("tool_input")
    if not isinstance(tool_input, dict):
        return 0
    command = cast("dict[str, object]", tool_input).get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    if SAFE_RE.search(command):
        return 0
    if not COMMIT_RE.search(command):
        return 0
    # `opted_in` is True either because the key is present in the turn, or because the project
    # declared `autonomy.git.commit: auto`. The gate still ran; it just did not stop anything.
    if gp.opted_in("COMMIT", command):
        return 0

    deny(REASON)
    return 0


if __name__ == "__main__":
    sys.exit(main())
