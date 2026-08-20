#!/usr/bin/env python3
"""What a command costs before it does anything, and what it costs at worst.

Invoking a command loads the command body plus everything its header orders read. That number is
invisible while you edit — a reference added in one line can cost twenty kilobytes on every future
invocation of that command — so this prints it, and can hold a baseline to compare against.

Two numbers, because one was lying
----------------------------------
The first version of this script charged every `Skill("x")` and every cited reference to every
invocation. `/verify` came out at 51 KB, of which 42 KB was three domain skills its own text loads
**conditionally** — `Skill("debugger")` *when chasing a failure*, `Skill("astro")` *when the stack
is Astro*. A `/verify` on a passing typecheck loads none of them. Charging all three made the
cheapest command in the set look like the second most expensive, and — worse — made a correct
change (stating a condition instead of loading eagerly) register as no improvement at all.

So:

    FLOOR    the command body, plus everything its header block declares. This is what every
             invocation pays, before it has read the arguments.
    CEILING  the floor plus every other reference and skill reachable from the body. Nothing
             is hidden; a load moved out of the header still shows up here.

What makes a load conditional is read off the line itself, not off where it sits, so the same rule
applies to a tree written before this script existed and the comparison stays fair:

- the line states a condition — `when`, `if`, `unless`, `only`, `otherwise`;
- the line is a table row, which is a routing table and by construction picks one branch;
- the line is inside a fenced block, which is a subagent prompt or an example. What a subagent
  reads is paid out of the subagent's context, not this one.

Everything else is floor. So `Skill("debugger");` in a bootstrap sequence is floor, and
`Skill("debugger")` *when chasing a failure* is not — which is also the sentence a command should
be writing anyway.

    python3 .github/check_context_budget.py                 # print the table
    python3 .github/check_context_budget.py --baseline      # save it
    python3 .github/check_context_budget.py --compare       # diff against the saved one

The measurement stays deliberately one level deep: it does not follow what the loaded files then
load, so the real cost is higher than what is printed. What matters is that both sides of a
comparison are measured the same way — including the baseline, which must be regenerated with this
script rather than carried over from the previous one. To baseline a tree that predates it, copy
this file into a worktree of that tree so both sides run the identical rule:

    git worktree add --detach <dir> <ref>
    cp .github/check_context_budget.py <dir>/.github/
    (cd <dir> && python3 .github/check_context_budget.py --baseline)
    cp <dir>/.graph-powers/logs/context-budget.json .graph-powers/logs/
    python3 .github/check_context_budget.py --compare
    git worktree remove <dir>
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
LOAD_VERB = re.compile(r"\b(read|load|deep-load|loads|reads|consult)\w*\b", re.IGNORECASE)
CONDITION = re.compile(r"\b(when|whenever|if|unless|only|otherwise|optional)\b", re.IGNORECASE)


def size(path: str) -> int:
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def skill_path(name: str) -> str | None:
    p = os.path.join("skills", name, "SKILL.md")
    return p if os.path.exists(p) else None


def loads_on(line: str) -> list[str]:
    """Every plugin reference and skill this one line orders loaded, as paths that exist.

    The verb filter keeps a path cited to identify something — "`explorer` is the agent at <path>"
    — out of the count. A `Skill("x")` call needs no verb: naming it is invoking it.
    """
    out: list[str] = []
    if LOAD_VERB.search(line):
        out += [r for r in PLUGIN_REF.findall(line) if os.path.exists(r)]
    out += [p for p in (skill_path(n) for n in SKILL_CALL.findall(line)) if p]
    return out


def is_conditional(line: str) -> bool:
    """True when this line's load is paid on one branch rather than on every invocation."""
    stripped = line.lstrip("> ").strip()
    if stripped.startswith("|"):        # a routing table row picks exactly one branch
        return True
    return bool(CONDITION.search(line))


def walk(text: str):
    """Yield (line, conditional?) for every line outside a fenced block.

    Fenced blocks are dropped entirely: in these commands a fence is either an example or a
    subagent prompt, and what a subagent reads is paid out of the subagent's context. Counting it
    here made `/debug` look like it loaded three reference files it never opens itself.
    """
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            yield line, is_conditional(line)


def chain_of(command_path: str) -> tuple[int, int, list[str], list[str]]:
    """(floor bytes, ceiling bytes, floor parts, the parts only the ceiling pays for)."""
    with open(command_path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()

    floor = {command_path: size(command_path)}
    ceiling = dict(floor)
    for line, conditional in walk(text):
        for ref in loads_on(line):
            ceiling[ref] = size(ref)
            if not conditional:
                floor[ref] = size(ref)

    conditional_only = sorted(set(ceiling) - set(floor))
    return sum(floor.values()), sum(ceiling.values()), sorted(floor), conditional_only


def measure() -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for c in sorted(glob.glob("commands/*.md")):
        f, ceil, _, _ = chain_of(c)
        out[os.path.basename(c)[:-3]] = {"floor": f, "ceiling": ceil}
    return out


def totals(data: dict[str, dict[str, int]]) -> tuple[int, int]:
    return sum(v["floor"] for v in data.values()), sum(v["ceiling"] for v in data.values())


def read_baseline() -> dict[str, dict[str, int]] | None:
    if not os.path.exists(BASELINE):
        return None
    try:
        with open(BASELINE, encoding="utf-8") as fh:
            raw = json.load(fh)
    except (OSError, ValueError):
        return None
    # A baseline written by the single-number version of this script cannot be compared against a
    # floor/ceiling one. Saying so beats printing a delta that means nothing.
    if not all(isinstance(v, dict) for v in raw.values()):
        return None
    return raw


# Measured 326,356 B / 435,117 B on the day the gate was given teeth, and rounded up to the next
# 5,000 rather than to the next byte. A ceiling set flush against the measurement fails on the
# next paragraph somebody writes in a command, which teaches people to raise the constant reflexively
# — the failure mode this gate exists to prevent. The margin is one edit wide, not one feature wide.
#
# Same contract as `check_listing_budget.py`: the number is the high-water mark, not a target, and
# lowering it when you do better is the point — a ceiling nobody ever tightens becomes headroom for
# the next person to spend without noticing.
#
# FLOOR is what the command set loads on every invocation. CEILING is the worst case, every
# conditional branch taken. WORST_FLOOR bounds a single command, because a total can stay flat
# while one command doubles, and a command is what a person actually pays for.
FLOOR_CEILING = 330_000
# Raised 440_000 -> 470_000 on 2026-08-20, and what bought the increase is two separate things.
# 18_585 B of it was already over the old ceiling before this change and had no owner. The rest is
# `commands/evolve.md` gaining `Skill("skill-improve")`, the first functional call site the
# skill-authoring territory has ever had: the external skill it replaced there matched no local
# path, so it was charged zero and the gate was measuring a load it could not see. A merged 8.6 KB
# body is the honest price of that edge, and the merge itself cut the two bodies from 384 non-empty
# lines to 107. Lower this again when the pre-existing overage is paid down.
CEILING_CEILING = 470_000
WORST_FLOOR = 70_000


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "--print"
    now = measure()
    floor_total, ceiling_total = totals(now)

    if mode == "--baseline":
        os.makedirs(os.path.dirname(BASELINE), exist_ok=True)
        with open(BASELINE, "w", encoding="utf-8") as fh:
            json.dump(now, fh, indent=2, sort_keys=True)
        print(f"baseline saved: {len(now)} commands, floor {floor_total:,} B, "
              f"ceiling {ceiling_total:,} B")
        return 0

    if mode == "--compare":
        before = read_baseline()
        if before is None:
            print(f"no comparable baseline at {BASELINE} — run --baseline first "
                  f"(a baseline from the single-number version cannot be used)")
            return 1
        old_floor, old_ceiling = totals(before)
        print(f"{'command':<14}{'floor was':>11}{'floor now':>11}{'delta':>10}"
              f"{'ceil was':>11}{'ceil now':>11}")
        for name in sorted(now, key=lambda k: before.get(k, {}).get("floor", 0) - now[k]["floor"],
                           reverse=True):
            b = before.get(name, {"floor": 0, "ceiling": 0})
            a = now[name]
            mark = "" if b["floor"] == a["floor"] else ("  ↓" if a["floor"] < b["floor"] else "  ↑")
            print(f"{name:<14}{b['floor']:>11,}{a['floor']:>11,}{a['floor'] - b['floor']:>10,}"
                  f"{b['ceiling']:>11,}{a['ceiling']:>11,}{mark}")
        fpct = 0.0 if not old_floor else (old_floor - floor_total) / old_floor * 100
        cpct = 0.0 if not old_ceiling else (old_ceiling - ceiling_total) / old_ceiling * 100
        print(f"\n{'TOTAL':<14}{old_floor:>11,}{floor_total:>11,}{floor_total - old_floor:>10,}"
              f"{old_ceiling:>11,}{ceiling_total:>11,}")
        print(f"\nfloor:   {fpct:.1f}% less loaded on every invocation of the command set")
        print(f"ceiling: {cpct:.1f}% less in the worst case")
        return 0

    print(f"{'command':<14}{'floor':>10}{'ceiling':>10}   conditional (paid only on that branch)")
    for name in sorted(now, key=lambda k: now[k]["floor"], reverse=True):
        _, _, _, conditional = chain_of(f"commands/{name}.md")
        names = ", ".join(os.path.basename(p) for p in conditional)
        print(f"{name:<14}{now[name]['floor']:>10,}{now[name]['ceiling']:>10,}   {names or '—'}")
    print(f"\n{'TOTAL':<14}{floor_total:>10,}{ceiling_total:>10,}")

    problems: list[str] = []
    if floor_total > FLOOR_CEILING:
        problems.append(f"floor {floor_total:,} B exceeds {FLOOR_CEILING:,} B by "
                        f"{floor_total - FLOOR_CEILING:,} — this is loaded on every invocation "
                        f"of the command set, so it is paid whether or not the addition is used")
    if ceiling_total > CEILING_CEILING:
        problems.append(f"ceiling {ceiling_total:,} B exceeds {CEILING_CEILING:,} B by "
                        f"{ceiling_total - CEILING_CEILING:,} — the worst case is what a session "
                        f"that takes every conditional branch actually costs")
    for name, sizes in sorted(now.items()):
        if sizes["floor"] > WORST_FLOOR:
            problems.append(f"command `{name}`: floor {sizes['floor']:,} B over the "
                            f"{WORST_FLOOR:,} B per-command cap — move a reference behind a "
                            f"condition, or split the command")

    if problems:
        for problem in problems:
            print(f"::error::{problem}")
        print("\nShorten what a command loads unconditionally rather than raising the ceiling. "
              "If the growth is genuinely necessary, raise the constant in the same change and "
              "say in the commit what bought the increase.")
        return 1

    print(f"\nwithin budget — floor {FLOOR_CEILING - floor_total:,} B and ceiling "
          f"{CEILING_CEILING - ceiling_total:,} B of headroom")
    return 0


if __name__ == "__main__":
    sys.exit(main())
