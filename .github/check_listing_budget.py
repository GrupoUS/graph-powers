#!/usr/bin/env python3
"""What this plugin costs a session *before* anyone invokes anything.

`check_context_budget.py` measures the other number — what one command costs once you run it. This
measures the standing one: Claude Code loads a listing of every skill and command name plus its
description into context at session start, and that listing is what the model matches a sentence
against when it decides, unprompted, to reach for `/debug`.

Two things make it worth a gate rather than a comment.

**It has a hard ceiling nobody sees hit.** The listing is budgeted at about 1% of the context
window across *every* installed source — this plugin, the other plugins, the user's own skills, the
bundled ones. On overflow Claude Code does not warn and does not fail: it drops descriptions,
starting with the entries invoked least, and a skill whose description was dropped still appears by
name while matching nothing. Measured on 2026-08-20, three of this plugin's own skills were in that
state — present, listed, unreachable by description.

**This plugin is the largest single contributor on a typical machine.** 10,752 of 23,902 local
characters at the time of writing: 45%, against four other plugins and nine personal skills. What
this repository adds is therefore what pushes somebody else's skill off the listing, which is a
cost paid by a person who never edited this file.

So the ceiling below is not an aspiration. It is the number this plugin measured at its worst, and
the gate refuses to let it grow back. Lowering it further is welcome — rewrite the ceiling when you
do, so the next change is held to what you achieved rather than to what you inherited.

    python3 .github/check_listing_budget.py            # table, and the verdict
    python3 .github/check_listing_budget.py --json     # the numbers, for a script

Exit 0 = within budget. Exit 1 = a description grew past a cap.
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys

# The high-water mark, from the rewrite that introduced this gate. The plugin measured 10,752 before
# it and 9,283 after; the ceiling is the *before*, so the headroom stays visible instead of being
# spent silently by the next person who adds a skill.
TOTAL_CEILING = 10_752

# Claude Code truncates a single entry's combined `description` + `when_to_use` at this many
# characters regardless of the budget. An entry over it is not a style problem — it is text the
# model provably never reads, which is the worst place for a trigger phrase to be.
ENTRY_CAP = 1_536


def frontmatter(path: str) -> str:
    """The YAML block, or an empty string when the file has none.

    Deliberately textual rather than a YAML parse: this file runs in CI on a checkout with no
    dependencies installed, and PyYAML is not in the standard library. What it needs is the length
    of two fields, which does not justify a dependency.
    """
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    block = text[3:end] if end > 0 else ""
    # Full-line YAML comments are dropped by the parser, so they never reach the listing — but the
    # textual field reader below runs to the next top-level key and would otherwise swallow a
    # comment sitting between two fields and charge it as description. That is not a rounding
    # error: it read 595 characters for a 219-character entry the first time this gate ran.
    #
    # Only a line whose first non-space character is `#` is removed. A `#` inside a quoted value is
    # untouched. The residual imprecision is a block scalar containing a line that starts with `#`,
    # which would then be undercounted — and undercounting is the right direction to be wrong in,
    # since the alternative fails CI over text the model never receives.
    return "\n".join(line for line in block.splitlines() if not line.lstrip().startswith("#"))


def field(block: str, key: str) -> str:
    """One frontmatter field's value, including the folded and block-scalar continuations.

    The stop condition is the next top-level key, which is what makes a multi-line `description:`
    count in full — the shape most of this plugin's descriptions are written in.
    """
    match = re.search(
        rf"^{key}:\s*(.*?)(?=^[A-Za-z_][\w-]*:|\Z)",
        block,
        re.DOTALL | re.MULTILINE,
    )
    return match.group(1).strip() if match else ""


def entries() -> list[tuple[str, str, int]]:
    """Every listing entry this plugin publishes, as (kind, name, characters).

    The name counts because the listing carries it too, and a long name is charged like a long
    description. Commands are included for the same reason they are model-invocable at all: since
    the merge of commands into skills they occupy the same listing.
    """
    found: list[tuple[str, str, int]] = []
    for path in sorted(glob.glob("skills/*/SKILL.md")):
        name = os.path.basename(os.path.dirname(path))
        block = frontmatter(path)
        found.append(("skill", name, len(name) + len(field(block, "description"))
                      + len(field(block, "when_to_use"))))
    for path in sorted(glob.glob("commands/*.md")):
        name = os.path.basename(path)[:-3]
        block = frontmatter(path)
        found.append(("command", name, len(name) + len(field(block, "description"))
                      + len(field(block, "when_to_use"))))
    return found


def main() -> int:
    found = entries()
    total = sum(size for _, _, size in found)
    skills = sum(size for kind, _, size in found if kind == "skill")
    commands = total - skills
    problems: list[str] = []

    if "--json" in sys.argv[1:]:
        print(json.dumps({"total": total, "skills": skills, "commands": commands,
                          "ceiling": TOTAL_CEILING,
                          "entries": {name: size for _, name, size in found}},
                         indent=2, sort_keys=True))
        return 0

    print(f"{'entry':<28}{'kind':<10}{'chars':>8}")
    for kind, name, size in sorted(found, key=lambda row: -row[2]):
        flag = "  ← over the per-entry cap" if size > ENTRY_CAP else ""
        print(f"{name:<28}{kind:<10}{size:>8,}{flag}")
        if size > ENTRY_CAP:
            problems.append(f"{kind} {name}: {size:,} chars, capped at {ENTRY_CAP:,} — the "
                            f"overflow is text the model never receives")

    print(f"\n{'skills':<28}{'':<10}{skills:>8,}")
    print(f"{'commands':<28}{'':<10}{commands:>8,}")
    print(f"{'TOTAL':<28}{'':<10}{total:>8,}   ceiling {TOTAL_CEILING:,}")

    if total > TOTAL_CEILING:
        problems.append(f"listing total {total:,} exceeds the ceiling {TOTAL_CEILING:,} by "
                        f"{total - TOTAL_CEILING:,} chars. Every character added here is one that "
                        f"drops somebody else's skill description on a shared machine. Shorten an "
                        f"existing entry rather than raising the ceiling.")

    if problems:
        for p in problems:
            print(f"::error::{p}")
        return 1

    headroom = TOTAL_CEILING - total
    print(f"\nwithin budget — {headroom:,} chars of headroom "
          f"({headroom / TOTAL_CEILING * 100:.1f}% under the ceiling)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
