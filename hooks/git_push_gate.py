#!/usr/bin/env python3
"""git_push_gate.py - PreToolUse/Bash gate for `git push`.

Why this exists
---------------
`${CLAUDE_PLUGIN_ROOT}/references/safety-floor.md` §1 makes it a [HARD] rule that nothing is pushed
without the user asking in the current turn. Until 2026-08-12 that was enforced
by `permissions.deny: Bash(git push *)` in `.claude/settings.json` — a hard deny
that ALSO blocked the user's own approved pushes, because `deny` outranks every
`allow` and has no per-turn opt-in. The user then had to run the push by hand.

This gate replaces that deny with the same opt-in shape already used by
`git_commit_gate.py`: blocked by default, unblocked for one command when the
caller deliberately opts in:

    <PREFIXO>_ALLOW_PUSH=1 git push origin <branch de trabalho>

The main thread adds that prefix only after the user approves in the current
turn. A subagent following a normal "implement X" prompt has no reason to write
it, so the accidental-push path stays closed.

Branch rail
-----------
Pushing `main` is a separate [HARD] rail (safety-floor §1: all main updates flow
`dev-test → PR → user merges`). It needs a second, louder opt-in:

    <PREFIXO>_ALLOW_PUSH=1 <PREFIXO>_ALLOW_PUSH_MAIN=1 git push origin main

so that "user approved a push" can never be silently upgraded into "user
approved a push to main". A push counts as main-touching when the command names
`main`/`master` in a refspec, uses `--all`/`--mirror`, or when HEAD is currently
on `main`/`master`.

Scope and honesty about it
--------------------------
This is a guardrail, not a sandbox: anything that can read this file can also
read the opt-in. Force-push to `main`/`master` is denied separately by the global
`~/.claude/hooks/smart_bash_approver.py`.

Contract: exit 0 allows; a `permissionDecision: "deny"` payload blocks and shows
`permissionDecisionReason` to the model. Never blocks on its own failure.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import cast

# Project parameters (branch, protected branches, opt-in prefix) come from
# the project config via `_config`, never hardcoded — this
# file is byte-for-byte the same in every repository that installs the plugin.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _config as gp  # noqa: E402


OPT_IN = f"{gp.opt_in('PUSH')}=1"
OPT_IN_MAIN = f"{gp.opt_in('PUSH_MAIN')}=1"
WORK_BRANCH = gp.work_branch()

# `git` must sit in command position — start of string, or after a separator,
# optionally behind env assignments. Without that anchor a read-only
# `grep -rn "git push" docs/` matches the quoted text and gets blocked.
_SEPARATOR = r"(?:^|[;&|(\n])\s*"
_ENV_ASSIGNMENTS = r"(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*"
_GIT_GLOBAL_FLAGS = r"(?:\s+-[^\s]+(?:\s+[^\s]+)?)*"
PUSH_RE = re.compile(
    rf"{_SEPARATOR}{_ENV_ASSIGNMENTS}git\b{_GIT_GLOBAL_FLAGS}\s+push\b"
)

# Read-only inspections that merely contain the verb.
SAFE_RE = re.compile(r"\bgit\s+push\s+--dry-run\b")

# `main` / `master` named as a refspec: bare, `HEAD:main`, `refs/heads/main`,
# `+main`, `main:main`. `--all` / `--mirror` push every local branch, main too.
MAIN_REF_RE = re.compile(
    r"(?:^|\s)\+?(?:[\w./-]+:)?(?:refs/heads/)?(?:main|master)(?=\s|$)"
    r"|(?:^|\s)--(?:all|mirror)(?=\s|$)"
)

REASON_BASE = (
    "Blocked by the graph-powers git_push_gate.\n"
    "\n"
    "safety-floor.md §1 [HARD]: nothing is pushed unless the user asked for it in the\n"
    "current turn. This gate exists because a subagent once committed and pushed on its own.\n"
    "\n"
)

REASON = (
    REASON_BASE
    + "If — and only if — the user approved the push IN THIS TURN, repeat the command\n"
    "with the explicit opt-in:\n"
    f"    {OPT_IN} git push origin {WORK_BRANCH}\n"
    "\n"
    "If you are a subagent: do NOT use the opt-in. Stop, leave the commit local, and\n"
    "report to the orchestrator."
)

REASON_MAIN = (
    REASON_BASE
    + "This push also touches a protected branch, which is a separate rail: every update\n"
    f"to it flows `{WORK_BRANCH} → PR → the user approves → the user merges`.\n"
    "\n"
    "Only use the second opt-in if the user EXPLICITLY asked for a push to a protected\n"
    f"branch in this turn (the normal path is a PR from `{WORK_BRANCH}`):\n"
    f"    {OPT_IN} {OPT_IN_MAIN} git push origin <protected-branch>\n"
    "\n"
    "If you are a subagent: do NOT use either opt-in. Stop and report."
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


def current_branch(cwd: str | None) -> str | None:
    """HEAD's branch name, or None when it can't be determined.

    Never raises: a gate that crashes on a missing `git` must not become a gate
    that blocks everything. Returning None means "unknown", and an unknown
    branch only downgrades the check to the ordinary push opt-in — an explicit
    `main` refspec is still caught by MAIN_REF_RE.
    """
    try:
        proc = subprocess.run(  # noqa: S603 - fixed argv, no shell
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],  # noqa: S607 - PATH lookup is intended
            cwd=cwd or None,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def main() -> int:
    try:
        payload = cast("object", json.load(sys.stdin))
    except (ValueError, OSError, RecursionError):
        return 0

    if not isinstance(payload, dict):
        return 0
    payload_dict = cast("dict[str, object]", payload)
    tool_input = payload_dict.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0
    command = cast("dict[str, object]", tool_input).get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    if SAFE_RE.search(command):
        return 0
    if not PUSH_RE.search(command):
        return 0

    if not gp.opted_in("PUSH", command):
        deny(REASON)
        return 0

    raw_cwd = payload_dict.get("cwd")
    cwd = raw_cwd if isinstance(raw_cwd, str) else None
    branch = current_branch(cwd)
    touches_main = bool(MAIN_REF_RE.search(command)) or branch in set(gp.protected_branches())

    if touches_main and not gp.opted_in("PUSH_MAIN", command):
        deny(REASON_MAIN)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
