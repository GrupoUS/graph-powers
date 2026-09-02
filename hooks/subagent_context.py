#!/usr/bin/env python3
"""subagent_context.py - the solution ladder, delivered where SessionStart never reaches.

SessionStart context is parent-thread only. A subagent starts from its own prompt and nothing
else (`references/execution-floor.md`), so the one rule that shapes what it writes — the solution
ladder, `references/shared/025-solution-ladder.md` — reached it only when the spawn prompt happened
to carry it. Ponytail (MIT, see `NOTICE`) found the same gap under its issue #252 and closed it with
one SubagentStart hook. This is that hook: the ladder, mirrored in one paragraph, into every
subagent.

Advisory only: `additionalContext`, never a decision, and nothing project-specific — the ladder is
the same in every repository, so this hook reads no config. Bounded: the paragraph stays under
`LIMIT` bytes, held by `test_hooks.py`, because a subagent's context is the scarcer one.

It does not wait on stdin. The payload carries `agent_type`, which this hook does not need, and a
PowerShell wrapper can swallow the piped JSON so EOF never arrives (Ponytail #443); a hook that
blocks on every spawn is worse than no hook, so the read has a join timeout and the output does not
depend on it.

Trigger: SubagentStart
"""

from __future__ import annotations

import json
import sys
import threading
from pathlib import Path

try:
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
except Exception:
    pass

LIMIT = 900
RELATIVE = "references/shared/025-solution-ladder.md"

# mirror of references/shared/025-solution-ladder.md — the ladder and its floor, not the file
LADDER = (
    "Solution ladder in force ({where}). Understand first — read what the change touches, trace "
    "the real flow — then stop at the first rung that holds: 1 does this need to exist (YAGNI) · "
    "2 already in this codebase, reuse it · 3 stdlib · 4 native platform feature · 5 installed "
    "dependency · 6 one line · 7 only then the minimum that works. Fix the root cause once, where "
    "every caller routes through. Never cut validation at trust boundaries, data-loss handling, "
    "security, accessibility or anything requested; non-trivial logic leaves one runnable check."
)


def drain_stdin() -> None:
    """Consume the payload if it arrives; never block the spawn waiting for it."""
    def read() -> None:
        try:
            sys.stdin.read()
        except Exception:
            pass  # a payload that will not decode is still not a reason to block the spawn

    reader = threading.Thread(target=read, daemon=True)
    reader.start()
    reader.join(0.2)


def ladder() -> str:
    """The paragraph, naming the file by its resolved path when that keeps it under LIMIT."""
    where = RELATIVE
    try:
        candidate = Path(__file__).resolve().parent.parent / "references" / "shared" / "025-solution-ladder.md"
        if candidate.is_file():
            where = candidate.as_posix()
    except Exception:
        pass
    text = LADDER.format(where=where)
    if len(text.encode("utf-8")) > LIMIT:
        text = LADDER.format(where=RELATIVE)
    return text


def main() -> None:
    try:
        drain_stdin()
    except Exception:
        pass
    print(json.dumps({
        "hookSpecificOutput": {"hookEventName": "SubagentStart", "additionalContext": ladder()},
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
