#!/usr/bin/env python3
"""branch_session_notice.py - SessionStart notice about the working branch.

Why this exists
---------------
`git_branch_gate.py` stops a session from *moving* onto a protected branch, but a session
can also *start* there — a leftover checkout from the previous day, a `gh pr
checkout`, a fresh clone (whose default HEAD is the default branch). The gate stays silent
in that case because nothing was switched, and the first signal would be the
push gate, long after the edits landed on the wrong branch.

So: report the branch at session start, and when it is not the declared work branch, say
plainly what to do about it. Advisory by design — it never mutates the repo,
because a stash/switch decision on a dirty tree belongs to the user.

Contract: SessionStart consumes `hookSpecificOutput.additionalContext`. Never
fails loudly — an unreadable git state just produces no notice.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

# Project parameters (branch, protected branches, opt-in prefix) come from
# the project config via `_config`, never hardcoded — this
# file is byte-for-byte the same in every repository that installs the plugin.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _config as gp  # noqa: E402


WORK_BRANCH = gp.work_branch()
PROTECTED = set(gp.protected_branches())


def git(*args: str, cwd: str | None) -> str | None:
    """Stdout of a git command, or None when it cannot be determined."""
    try:
        proc = subprocess.run(  # noqa: S603 - fixed argv, no shell
            ["git", *args],  # noqa: S607 - PATH lookup is intended
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
    return proc.stdout.strip()


def notice(branch: str, *, dirty: bool) -> str | None:
    if branch == WORK_BRANCH:
        return None  # the expected state needs no words
    if branch in PROTECTED:
        tail = (
            "The working tree has uncommitted changes — decide with the user between "
            "`git stash` and moving them; discard nothing."
            if dirty
            else "The working tree is clean, so switching is safe."
        )
        return (
            f"[branch] The session started on `{branch}`, which is protected "
            f"(safety-floor §1 [HARD]: a protected branch is a read-only mirror; work "
            f"lives on `{WORK_BRANCH}` or a branch cut from it).\n"
            f"Run `git switch {WORK_BRANCH}` BEFORE any edit. {tail}"
        )
    return (
        f"[branch] Session on `{branch}` (not `{WORK_BRANCH}`). If this is a work branch "
        f"cut from `{WORK_BRANCH}`, carry on here; otherwise switch back to "
        f"`{WORK_BRANCH}` before editing."
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError, RecursionError):
        payload = {}

    cwd = None
    if isinstance(payload, dict) and isinstance(payload.get("cwd"), str):
        cwd = payload["cwd"]
    cwd = cwd or os.environ.get("CLAUDE_PROJECT_DIR")

    branch = git("rev-parse", "--abbrev-ref", "HEAD", cwd=cwd)
    if not branch or branch == "HEAD":
        return 0  # not a repo, or detached — nothing useful to say

    status = git("status", "--porcelain", cwd=cwd)
    message = notice(branch, dirty=bool(status))
    if not message:
        return 0

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": message,
            }
        },
        sys.stdout,
    )
    print()  # the hook payload must be newline-terminated
    return 0


if __name__ == "__main__":
    sys.exit(main())
