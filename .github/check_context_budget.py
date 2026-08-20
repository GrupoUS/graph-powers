#!/usr/bin/env python3
"""What a command costs before it does anything.

Invoking a command loads the command body plus everything its header orders read. That number is
invisible while you edit — a reference added in one line can cost twenty kilobytes on every future
invocation of that command — so this prints it, and can hold a baseline to compare against.

The measurement is deliberately crude and deliberately honest about being crude: it follows the
`${CLAUDE_PLUGIN_ROOT}/...` paths and the `Skill("...")` calls a command names, one level deep. It
does not follow what those files then load, so the real cost is higher than what is printed here.
What matters is that it is measured the same way before and after a change, so the delta is real.

    python3 .github/check_context_budget.py                 # print the table
    python3 .github/check_context_budget.py --baseline      # save it
    python3 .github/check_context_budget.py --compare       # diff against the saved one
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys

BASELINE = os.path.join(".graph-powers", "logs", "context-budget.json")
PLUGIN_REF = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([A-Za-z0-9_./-]+\.md)")
SKILL_CALL = re.compile(r"""Skill\(\s*["'](?:graph-powers:)?([a-z-]+)["']""")


def size(path: str) -> int:
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def chain_of(command_path: str) -> tuple[int, list[str]]:
    """Bytes loaded by invoking this command, and what makes them up."""
    with open(command_path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    loaded: dict[str, int] = {command_path: size(command_path)}

    # Only references the command tells the reader to LOAD. A path can be cited to identify
    # something — "`explorer` is the agent at <path>" — without anyone opening it, and counting
    # those inflates the figure and, worse, makes a correctness fix look like a regression.
    for line in text.splitlines():
        if not re.search(r"\b(read|load|deep-load|loads|reads|consult)\w*\b", line, re.IGNORECASE):
            continue
        for ref in PLUGIN_REF.findall(line):
            if os.path.exists(ref):
                loaded[ref] = size(ref)

    for skill in set(SKILL_CALL.findall(text)):
        p = os.path.join("skills", skill, "SKILL.md")
        if os.path.exists(p):
            loaded[p] = size(p)

    return sum(loaded.values()), sorted(loaded)


def measure() -> dict[str, int]:
    return {
        os.path.basename(c)[:-3]: chain_of(c)[0]
        for c in sorted(glob.glob("commands/*.md"))
    }


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "--print"
    now = measure()
    total = sum(now.values())

    if mode == "--baseline":
        os.makedirs(os.path.dirname(BASELINE), exist_ok=True)
        with open(BASELINE, "w", encoding="utf-8") as fh:
            json.dump(now, fh, indent=2, sort_keys=True)
        print(f"baseline saved: {len(now)} commands, {total:,} bytes total")
        return 0

    if mode == "--compare":
        if not os.path.exists(BASELINE):
            print(f"no baseline at {BASELINE} — run --baseline first")
            return 1
        with open(BASELINE, encoding="utf-8") as fh:
            before: dict[str, int] = json.load(fh)
        old_total = sum(before.values())
        print(f"{'command':<14}{'before':>10}{'after':>10}{'delta':>10}{'':>3}")
        for name in sorted(now, key=lambda k: before.get(k, 0) - now[k], reverse=True):
            b, a = before.get(name, 0), now[name]
            mark = "" if b == a else ("↓" if a < b else "↑")
            print(f"{name:<14}{b:>10,}{a:>10,}{a - b:>10,}{mark:>3}")
        pct = 0.0 if not old_total else (old_total - total) / old_total * 100
        print(f"\n{'TOTAL':<14}{old_total:>10,}{total:>10,}{total - old_total:>10,}")
        print(f"{pct:.1f}% less loaded per full sweep of the command set")
        return 0

    print(f"{'command':<14}{'bytes':>10}   what it loads")
    for name in sorted(now, key=lambda k: now[k], reverse=True):
        _, parts = chain_of(f"commands/{name}.md")
        # `os.path.dirname`, not `startswith("commands/")`: glob returns the platform separator,
        # so on Windows every path here is `commands\\x.md` and the prefix test silently matches
        # nothing — the command would list itself among its own dependencies and nobody would see
        # why. This whole file exists to produce a number somebody trusts.
        others = [os.path.basename(p) for p in parts if os.path.dirname(p) != "commands"]
        print(f"{name:<14}{now[name]:>10,}   {', '.join(others) or '(itself only)'}")
    print(f"\n{'TOTAL':<14}{total:>10,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
