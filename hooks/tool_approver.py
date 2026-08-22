#!/usr/bin/env python3
"""tool_approver.py - the approval prompt for everything that is not a shell command.

Trigger: PermissionRequest (matcher `*`). Reads a JSON payload on stdin, answers with the
PermissionRequest decision shape, and stays silent whenever it has no opinion — silence there
means "use the normal approval flow", which is the fail-open answer for this event.

Why this exists
---------------
`smart_bash_approver` answers one question, `autonomy.bashDefault`, and it answers it only for
`Bash`. Every other tool a session runs — a subagent spawn, an MCP call, a fetch, a workflow —
reached the user as a prompt no matter what the project's `autonomy` block said. The setting whose
description is "the field that decides whether a session feels like work or like clicking Approve"
was therefore true of shell commands and false of everything else, and a repository that had
declared `level: autonomous` still stopped on tool calls that git undoes for free.

`autonomy.toolDefault` is that decision, written once. Under `autonomous` it resolves to `allow`
and this hook answers the prompt; under `guarded` it resolves to `ask` and this hook says nothing,
which leaves the prompt exactly where it was.

What it deliberately does not own
---------------------------------
- **`Bash`.** One owner per decision: `smart_bash_approver` classifies shell commands at
  `PreToolUse` and again here, with the destructive floor and the package-manager rules that only
  make sense for a command line. Answering `Bash` here as well would produce two verdicts for one
  call, and the looser one would be this file's — written by something that never saw the command.
- **The floors.** `PreToolUse` runs first and its `deny` short-circuits the call, so
  `protect_files` still refuses a write to `.env`, `graph_guardrails` still holds the kill switch
  and the spawn ceiling, and the git gates still own commit, push and protected branches. This hook
  is only ever reached by a call that every floor already let through.

Fail-open, like every hook here: an unreadable config, an unparseable payload or a missing
`tool_name` resolves to silence rather than to an approval.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _config as gp

# The one tool with an owner of its own. Kept as a set rather than a literal because the reason is
# "these are classified elsewhere", and a second such tool would be a name in this set, not a
# second branch further down.
OWNED_ELSEWHERE = frozenset({"Bash"})


def read_input() -> dict[str, Any]:
    """The payload, or an empty mapping. Never raises: cardinal 3."""
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


def allow() -> None:
    """The PermissionRequest approval shape. `ask` has no shape here — it is silence."""
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PermissionRequest",
                    "decision": {"behavior": "allow"},
                }
            }
        )
    )


def main() -> None:
    data = read_input()
    tool = str(data.get("tool_name") or "")

    # No tool name is not an approval. A payload this hook cannot read is a payload it cannot
    # judge, and the normal flow is the correct place for a call it did not understand.
    if not tool or tool in OWNED_ELSEWHERE:
        return

    try:
        # Codex passes the project in the payload; Claude Code exports it. `_config` resolves both,
        # and falls back to the git root, so the answer is the project's own posture rather than
        # whatever directory the hook process happened to start in.
        policy = gp.autonomy(gp.load(payload=data))
    except Exception:
        return

    if policy.get("toolDefault") == "allow":
        allow()


if __name__ == "__main__":
    main()
    sys.exit(0)
