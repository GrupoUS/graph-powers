#!/usr/bin/env python3
"""git_branch_gate.py - PreToolUse/Bash gate for landing HEAD on `main`.

Why this exists
---------------
`${CLAUDE_PLUGIN_ROOT}/references/safety-floor.md` §1 and `.claude/CLAUDE.md § Branch protection`
make it a [HARD] rule that all work happens on `dev-test` (or a branch off it)
and that `main` is a read-only mirror of merged work. Until now that rail was
prose only: `git_commit_gate.py` and `git_push_gate.py` guard the *write* end,
but nothing stopped a `git checkout main` from silently moving the whole session
onto the protected branch — after which every later edit lands in the wrong
place and the push gate is the first thing to notice.

Shape
-----
Same contract as its two siblings: deny by default, per-command opt-in written
only by the main thread after the user asks for it in the current turn.

    <PREFIXO>_ALLOW_MAIN_CHECKOUT=1 git switch main

What is *not* blocked, deliberately:

- `git checkout main -- path/to/file` — restores a file, HEAD does not move.
- `git switch -c fix/foo origin/main` — branching off main for PR work is the
  documented flow; only a *resulting branch* named main/master is refused.
- every read-only inspection (`git log main`, `git diff main...HEAD`, ...) —
  this gate only looks at `checkout` / `switch` / destructive `branch` verbs.

Also refused: `git branch -D|-d|-m|-M|-f main`, i.e. deleting, renaming or
force-moving the protected branch.

Scope and honesty about it
--------------------------
A guardrail, not a sandbox: anything that can read this file can read the
opt-in. Remote `main` is protected by `git_push_gate.py` (`<PREFIXO>_ALLOW_PUSH`
plus `<PREFIXO>_ALLOW_PUSH_MAIN`); this gate only keeps the local session honest.

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



OPT_IN = f"{gp.opt_in('MAIN_CHECKOUT')}=1"

PROTECTED = {b for n in gp.protected_branches() for b in (n, f"refs/heads/{n}")}
WORK_BRANCH = gp.work_branch()

# `git` must sit in command position — start of string, or after a separator,
# optionally behind env assignments. Without that anchor a read-only
# `grep -rn "git switch main" docs/` matches the quoted text and gets blocked.
_SEPARATOR = r"(?:^|[;&|(\n])\s*"
_ENV_ASSIGNMENTS = r"(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*"
_GIT_GLOBAL_FLAGS = r"(?:\s+-[^\s]+(?:\s+[^\s]+)?)*"
# Args stop at the next shell separator so `git switch dev-test && git log main`
# is judged on `dev-test` alone.
_ARGS = r"(?P<args>[^;&|\n]*)"

SWITCH_RE = re.compile(
    rf"{_SEPARATOR}{_ENV_ASSIGNMENTS}git\b{_GIT_GLOBAL_FLAGS}\s+(?:checkout|switch)\b{_ARGS}"
)
BRANCH_RE = re.compile(
    rf"{_SEPARATOR}{_ENV_ASSIGNMENTS}git\b{_GIT_GLOBAL_FLAGS}\s+branch\b{_ARGS}"
)

# Flags whose *next* token is the name of the branch being created. A create
# always wins over the start-point that follows it: `git switch -c foo main`
# ends on `foo`, which is fine.
CREATE_FLAGS = {"-b", "-B", "-c", "-C", "--orphan"}
# Destructive `git branch` modes — these act *on* the named branch.
BRANCH_WRITE_FLAGS = {"-d", "-D", "-m", "-M", "-f", "--delete", "--move", "--force"}
# Flags that swallow the following token, so it is never a branch name.
VALUE_FLAGS = {"--conflict", "--pathspec-from-file", "--start-point"}

REASON_SWITCH = (
    "Blocked by the graph-powers git_branch_gate.\n"
    "\n"
    f"safety-floor.md §1 [HARD]: work happens on `{WORK_BRANCH}` (or a branch cut from it).\n"
    "A protected branch is a read-only mirror of what has already been merged, and every\n"
    f"update to it flows `{WORK_BRANCH} → PR → the user approves → the user merges`.\n"
    "\n"
    "What to do instead:\n"
    f"    git switch {WORK_BRANCH}                 # normal work\n"
    "    git switch -c fix/<slug> origin/<protected>   # a PR branch cut from it\n"
    "\n"
    "To inspect a protected branch without moving HEAD: `git log origin/<branch>`,\n"
    "`git diff origin/<branch>...HEAD`, `git checkout <branch> -- <file>`.\n"
    "\n"
    "If — and only if — the user EXPLICITLY asked to move onto it IN THIS TURN, repeat\n"
    "the command with the opt-in:\n"
    f"    {OPT_IN} git switch <protected-branch>\n"
    "  Not in a POSIX shell? The hook matches the key as TEXT, not as syntax, so\n"
    "  `$env:<KEY>=1; <command>` (PowerShell) and `set <KEY>=1 && <command>` (cmd)\n"
    "  release it just as well.\n"
    "\n"
    "If you are a subagent: do NOT use the opt-in. Stop and report to the orchestrator."
)

REASON_BRANCH = (
    "Blocked by the graph-powers git_branch_gate.\n"
    "\n"
    "safety-floor.md §1 [HARD]: a protected branch is not deleted, renamed or force-moved —\n"
    "it is the read-only mirror of what was merged through a PR.\n"
    "\n"
    "If the user asked for this EXPLICITLY in this turn, repeat it with the opt-in:\n"
    f"    {OPT_IN} <command>"
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


def target_branch(args: str, *, create_flags: set[str]) -> str | None:
    """The branch this invocation lands on / acts upon, or None.

    A `--` anywhere means the pathspec form (`git checkout main -- file`): that
    restores files and HEAD never moves, so there is no target to judge. Note
    the branch name sits *before* the separator, which is why this is checked up
    front rather than while walking. Otherwise the tokens are read left to
    right until a branch name falls out.
    """
    tokens = args.split()
    if "--" in tokens:
        return None
    skip_next = False
    for index, token in enumerate(tokens):
        if skip_next:
            skip_next = False
            continue
        if token in create_flags or token in VALUE_FLAGS:
            # The created/targeted name is the next token, if there is one.
            if token in create_flags:
                return tokens[index + 1] if index + 1 < len(tokens) else None
            skip_next = True
            continue
        if token.startswith("-"):
            continue  # `--detach`, `--force`, `-q`, `--conflict=diff3`, ...
        return token
    return None


def main() -> int:
    try:
        # `cast` (not a bare annotation) is what stops the Any from leaking into
        # every downstream `.get()`.
        payload = cast("object", json.load(sys.stdin))
    except (ValueError, OSError, RecursionError):
        # A gate that crashes must not become a gate that blocks everything.
        return 0

    if not isinstance(payload, dict):
        return 0
    tool_input = cast("dict[str, object]", payload).get("tool_input")
    if not isinstance(tool_input, dict):
        return 0
    command = cast("dict[str, object]", tool_input).get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    if gp.opted_in("MAIN_CHECKOUT", command):
        return 0

    for match in SWITCH_RE.finditer(command):
        target = target_branch(match.group("args"), create_flags=CREATE_FLAGS)
        if target in PROTECTED:
            deny(REASON_SWITCH)
            return 0

    for match in BRANCH_RE.finditer(command):
        args = match.group("args")
        if not any(flag in args.split() for flag in BRANCH_WRITE_FLAGS):
            continue  # `git branch`, `git branch -a`, ... are read-only
        target = target_branch(args, create_flags=BRANCH_WRITE_FLAGS)
        if target in PROTECTED:
            deny(REASON_BRANCH)
            return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
