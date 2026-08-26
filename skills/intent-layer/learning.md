# learning.md — round history for `intent-layer`

One entry per round, in the shape **hypothesis → change → measurement → verdict**. An entry with no
measured number does not count.

## Round 1 — 2026-08-26 · bringing the global skill into the plugin

**Hypothesis:** the personal `~/.claude/skills/intent-layer` could enter the plugin as a copy with
its shell scripts ported, and the adaptation would be mechanical.

**Change:** it entered as adapted material, not as a copy. Three things upstream says are wrong
in this harness, and each was measured before it was rewritten:

1. Upstream's core principle — "only ONE root context file, `CLAUDE.md` and `AGENTS.md` should
   not coexist" — contradicts the root pair `AGENT_SETUP.md § 4a` installs and
   `templates/CLAUDE.md` + `templates/AGENTS.md` ship. Rewritten: `AGENTS.md` is the root node,
   `CLAUDE.md` is behaviour and pointers beside it, and a subdirectory `CLAUDE.md` is reported by
   the gate as a node three of the four harnesses never read.
2. Upstream's three scripts are shell — `find`, `wc`, `grep`, `bc`, `$(…)` — all on the cardinal 8
   ban list, and `NOTICE` records that this repository does not ship shell scripts. Ported to one
   standard-library Python file with three subcommands, plus a subcommand upstream does not have:
   `check`, the gate the playbook runs at `§ 4b` and `§ 10`.
3. Upstream's `## Intent Layer` root section duplicates the `Where things live` table
   `templates/AGENTS.md` already carries. The downlink index has one home: that table.

Also found while wiring it, and worth more than the port: the harness already **read** the nodes
before it could **write** them. `045-context-staging.md` loads `${paths.backendRoot}/AGENTS.md`
and the nearest node under `${paths.frontendRoot}`; `agents/frontend-specialist.md:26` reads
`${paths.frontendRoot}/AGENTS.md`; `agents/explorer.md:26` and `agents/debugger.md:45` load the
nearest `AGENTS.md`. Nothing in the plugin produced those files. That asymmetry is the call site.

**Measurement:**

| Metric | Value | How |
|---|---|---|
| Upstream tree, checked 2026-08-26 | 8 files, 17,573 bytes, MIT | GitHub tree API for crafter-station/skills @ main |
| Local personal copy vs upstream `SKILL.md` | 2,529 vs 2,544 bytes | byte count on both |
| Description | 478 chars (cap 1,536), entry 490 | `python3` on the frontmatter; `check_listing_budget.py` |
| Listing budget | 10,733 / 10,752 with this entry — 19 chars of headroom at the time; later red at 11,065 after four sibling skills landed in the same working tree the same morning | `check_listing_budget.py`; the overage is not this entry's and the ceiling is that session's to settle |
| SKILL.md body | 102 non-empty lines (cap 500) | `quick_validate.py`, exit 0 |
| `/evolve` context cost | floor +717 B, ceiling +10,095 B — the conditional `Skill("graph-powers:intent-layer")` load. The ceiling gate went red on the same run (497,170 / 470,000), of which 17,075 B predated this skill; the constant was raised to 500,000 by the session that owned the rest, with this load named in the comment | `check_context_budget.py` before and after |
| Wiring | 280 routing references checked, 0 unresolved among this skill's 29 inbound and 12 outbound edges; the 3 unresolved on the final run were another session's `graph-powers:executing-plans`, mid-port (later consolidated into `graph-powers:planning`) | `check_wiring.py`; `.claude/audit/graph.json` |
| Portability | 0 problems, for the new bash blocks in `AGENT_SETUP.md` and the script | `check_portability.py` |
| Skill precedence on this machine | `~/.claude/skills/intent-layer` exists with `skillOverrides: "off"` — a bare `Skill("intent-layer")` would return the override error, not run; plugin skills are not affected by the override | `~/.claude/settings.json`; Claude Code docs, Extend Claude with skills § Override skill visibility |
| Eval cases | 9 — 5 positive, 4 negative on the `/prime`, rules-layer, `skill-improve` and single-`/evolve`-capture borders | `evals/evals.json` |
| Routing hit rate, isolated subagents handed the listing | 9/9 chose correctly: 5 positives → `graph-powers:intent-layer`; negatives → `/prime`, no skill (a rules-layer edit), `graph-powers:skill-improve`, `/evolve`. Baseline without the entry: 4/5 positives "no listed skill applies", 1 → `/evolve` | 14-agent workflow, one response file per case |
| Assertion pass rate | first run 5/9 cases; after fixing four assertions 9/9 at `--threshold 1.0`; the five baseline responses fail their positive cases; a positive response graded against a negative case fails | `run_evals.py --response-dir`, then `--test-case` per baseline |
| Script gate | `hooks/test_hooks.py` — 429 checks pass, 44 of them in the intent-layer section; each of the seven `check` failures is made to fire, the clean tree passes, and the approver allows the quoted, single-quoted and bare invocations while `-c` still asks | `python3 hooks/test_hooks.py`, exit 0 |
| Adversarial round 1 on the script | 22 findings across 3 lenses: 4 P0, 7 P2, 11 P3; 44 attacks held | 3-agent workflow, fixtures under the scratchpad |
| This repository, `state . --exclude templates` | `partial`: 7 candidates over 20k tokens with no node, `skills/` first at ~208k; `check` exit 0 | the script itself |

**Verdict: kept, with three corrections the gates could not see.**

1. **The four assertions that failed correct responses were all one defect: the quote.** The
   playbook writes the path as `"$PLUGIN/…/intent_layer.py" state .`, so `intent_layer\.py\s+state`
   never meets the closing quote — pattern 2 of `authoring.md § 5c`, in the direction it warns
   about. The Mode B auditor found the identical defect in `hooks/smart_bash_approver.py`: the
   allow-regex was written from the unquoted test fixture and asked on every real invocation while
   its own test stayed green. Fixed in both, with the quoted spelling now a test case.
2. **The adversarial pass found what the fixtures did not.** The downlink regex read one ASCII-only
   charset, so `módulos/AGENTS.md`, `app/(dashboard)/AGENTS.md` and `packages/@acme/ui/AGENTS.md`
   were truncated and a correct tree failed the gate. The purpose-line rule accepted a YAML
   frontmatter fence, an HTML comment and a table row. A UTF-16 node — what PowerShell 5.1's `>`
   writes — decoded to NUL-interleaved text in which no placeholder was visible, and the gate said
   OK. A BOM turned a heading into a purpose line. All four fixed, each with a test; a second
   adversarial round then ran on the fixes.
3. **Rounding disagreed with the verdict at every threshold.** 19,999 tokens printed as `20.0k`
   beside `—`, and 16,001 bytes floored to exactly the cap. Tokens now round up and the display
   floors, so what is printed never contradicts what was decided.

**Refuted:** that the port was mechanical. Two of the three upstream decisions were wrong for this
harness before a line of shell was read, and the third would have created the second copy of a
table the repository already owns.

**Kept, deliberately:** every call site names the skill `graph-powers:intent-layer`, never the bare
name, because the personal copy shadows the bare name on any machine that installed it — the
collision `docs/ARCHITECTURE.md § 5` describes, met on the day the skill was added.

**Deferred, with the reason:** git and walk sources disagree on a gitignored directory and on a
submodule, by construction — the footer now names the source and whether `.gitignore` was
honoured, and a tree is only compared to itself under one source. A bracket directory in
`--exclude` needs the `[[]slug]` spelling; the help text says so rather than the code guessing.

**Next round should measure:** the trigger hit rate in a clean session (`claude -p`) rather than in
an isolated subagent handed the listing; whether `/evolve § 5` actually loads the skill when a
third learning lands in a node-less subtree, which needs a transcript; and whether this repository
wants the `skills/` and `hooks/` nodes its own `state` now names, or keeps its rules layer as the
answer — a decision for its owner, not for the skill.
