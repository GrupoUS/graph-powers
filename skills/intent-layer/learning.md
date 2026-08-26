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
| Skill precedence on this machine | `~/.claude/skills/intent-layer` existed with `skillOverrides: "off"` when the round started — a bare `Skill("intent-layer")` would have returned the override error, not run; plugin skills are not affected by the override. The personal copy was removed by the end of the round; the `"intent-layer": "off"` entry remains in `~/.claude/settings.json`, now naming nothing | `~/.claude/settings.json`; Claude Code docs, Extend Claude with skills § Override skill visibility |
| Eval cases | 9 — 5 positive, 4 negative on the `/prime`, rules-layer, `skill-improve` and single-`/evolve`-capture borders | `evals/evals.json` |
| Routing hit rate, isolated subagents handed the listing | 9/9 chose correctly: 5 positives → `graph-powers:intent-layer`; negatives → `/prime`, no skill (a rules-layer edit), `graph-powers:skill-improve`, `/evolve`. Baseline without the entry: 4/5 positives "no listed skill applies", 1 → `/evolve` | 14-agent workflow, one response file per case |
| Assertion pass rate | first run 5/9 cases; after fixing four assertions 9/9 at `--threshold 1.0`; the five baseline responses fail their positive cases; a positive response graded against a negative case fails | `run_evals.py --response-dir`, then `--test-case` per baseline |
| Script gate | `hooks/test_hooks.py` — 439 checks pass, 54 of them in the intent-layer section; each of the seven `check` failures is made to fire, the clean tree passes, and the approver allows the quoted, single-quoted and bare invocations while `-c` still asks | `python3 hooks/test_hooks.py`, exit 0 |
| Adversarial round 1 on the script | 22 findings across 3 lenses: 4 P0, 7 P2, 11 P3; 44 attacks held | 3-agent workflow, fixtures under the scratchpad |
| Adversarial round 2, on the round-1 fixes | 27 findings across 2 lenses: 4 P0, 13 P2, 10 P3; all 7 round-1 fixes held on fresh fixtures, 32 attacks held; no traceback in 34 fixtures | 2-agent workflow |
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
4. **The second round broke the first round's fix, in the direction the first round pushed it.**
   Widening the charset so `módulos/` resolved let a markdown link earlier on the same row swallow
   the real path, let the prose between two code spans read as one path, and glued a curly quote
   to the token — four P0s on a table row any word processor produces. The parser is now four
   shapes read in order with each match blanked before the next (angle-bracketed link target,
   plain link target, whitespace-free code span, bare token with balanced `()` and `[]`), a
   prose-only line scanner that skips fenced blocks and HTML comments, and a short list of marks
   (`* ? < > { } $ ://`) that make a token a convention rather than a path. Every case is a test;
   the cost is that a path with a space resolves only inside an angle-bracketed link target, which
   the docstring says.
5. **The review that followed found what neither adversarial round looked for.** Commits
   `b4fa51a`, `f774042` and `00eb254`, from the review flow rather than this session: the bare-token
   regex backtracked from every character on a 16 KiB line with no viable tail (over five seconds),
   so it became a forward scanner behind a fixed-tail pre-check; a symlinked node and a downlink
   that resolves outside the project root are refused rather than read; a differently-cased or
   symlinked spelling of a known node resolves to the discovered one instead of dangling; and the
   approver's `-X` allowance was narrowed so an arbitrary interpreter option does not inherit the
   read-only grant. Six more tests, all in the same section. Neither refuter lens carried
   "performance" or "path containment" — the next audit prompt should.

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
From round 2, left as documented edges rather than code: an `IGNORED` name prunes at any depth
(a package named `vendor` is invisible); a symlinked *source file* alias counts twice in
`measure` (a symlinked *node* is now refused outright); a directory named exactly `AGENTS.md`;
`_path_` italic on a bare path is not a link; U+2028 shifts a line number; a NUL after the first
2 KiB is not sniffed. None produces a wrong verdict on a tree anyone has shown; each would cost
more lines than it protects.

**Next round should measure:** the trigger hit rate in a clean session (`claude -p`) rather than in
an isolated subagent handed the listing; whether `/evolve § 5` actually loads the skill when a
third learning lands in a node-less subtree, which needs a transcript; and whether this repository
wants the `skills/` and `hooks/` nodes its own `state` now names, or keeps its rules layer as the
answer — a decision for its owner, not for the skill.

## Round 2 — 2026-08-26 · the skill on its own repository, and a deferral that can be read

**Hypothesis:** running the skill's procedure on this repository would end at `complete`, and the
five directories the measure flagged but nobody wanted a node for could be waved through in the
changelog.

**Change:** two nodes written by the procedure — `skills/AGENTS.md` and `hooks/AGENTS.md`, sourced
from the rules layer, the gate scripts and the incident records — and linked from the root's
`Where things live`. Then the part the hypothesis got wrong: `state` stayed `partial` at 7, then 3
candidates, because a decision that lives only in a changelog is invisible to the tool that counts.
So the config gained an `intentLayer` block (`schema/config.schema.json`): thresholds, `exclude`,
and `deferred` — a directory the measure flags and the project refuses a node for. `state` stops
counting it; `check` refuses the deferral until the nearest ancestor node names the directory in
backticks with the reason beside it, and warns once the directory grows a node. Flag beats block,
block beats default, `--exclude` adds to the block.

**Measurement:**

| Metric | Value | How |
|---|---|---|
| This repository, before | `partial` — 7 candidates, largest `skills/` ~216k tokens | `state . --exclude templates` |
| After the two nodes | `partial` — 5, then 3 after `docs/`, `skills/debugger`, `skills/intent-layer` crossed the line as the tree grew | same |
| After eight declared deferrals, each named in an ancestor row | `complete`; `check`: 3 nodes, 0 failures, 0 warnings; longest chain ~20 KB | `state .` and `check .` with no flags — the block carries `exclude: ["templates"]` |
| Node sizes | root ~3.6k, `hooks/` ~1.5k, `skills/` ~1.3k tokens | `state` |
| Tests | 467 checks, 11 on the config block: exclude, deferral retired, unexplained deferral fails naming where to write it, stale deferral warns, missing directory warns, threshold from config, flag over config, typo falls to defaults, `--exclude` adds | `hooks/test_hooks.py`, exit 0 |
| The mention rule, first version | `directory in a.text` — passed for `references`, `codex` and `commands` on any root, because those words occur in every root; tightened to the backticked path `` `references/` `` before it shipped | fixture with the row removed |
| Installer | `skills/AGENTS.md` not copied into `~/.agents/skills/` (0 occurrences in the dry-run, 14 skills still listed) | `codex/install.mjs --dry-run` |
| Gates | 17 of 17 exit 0, version 1.10.4 | the gate list in `AGENTS.md` |

**Verdict: kept, with the hypothesis refuted twice.** Waving a decision through in prose left the
tool reporting `partial` forever, which is the same defect as a rule nobody reads — and the first
mention test accepted any root that happened to contain the word, which is the same defect one
level down. Both fixed by making the decision a thing the script can find and a person can read
in the same place.

**Kept, deliberately:** deferrals live in the config *and* in the ancestor row. One copy is the
divergence this repository exists to end; here the two copies say different things — the config
says *what*, the row says *why* — and the gate holds them together.

### Clean-session measurement, same day

The open item from Round 1, run for real: `claude -p --plugin-dir <this tree>` with the
marketplace copy disabled through `--settings`, plan mode, from a scratch bun-monorepo fixture (a
fresh tree, a grown tree with one orphan and one dangling row, and a root-pair tree), one session
per eval case. A probe first: the session returned the working tree's 478-character description
verbatim for `graph-powers:intent-layer` and `NONE` for a retired skill, which is what proves the
plugin under test was the one loaded.

| Run | Prompt shape | Language | Routing (tool stream) | Body loaded | Grader |
|---|---|---|---|---|---|
| 1 | "…do not run any command" suffix, all tools | pt-BR — a host `CLAUDE.md` pins it | 9/9 named the right entry | 4/5 positives called `Skill("graph-powers:intent-layer")` | 5/9 |
| 2 | "load the skill you choose with the Skill tool…" suffix, tools `Skill,Read,Glob,Grep`, `--append-system-prompt "Answer in English."` | English | 9/9 | 5/5 | **9/9** at `--threshold 1.0` |

Three things the numbers say, in order of what they cost to learn:

1. **Routing is not the risk; loading is.** Run 1's one real miss was the audit case: the response
   named the skill on line 1 and the stream had zero tool calls — the model then hand-rolled a
   shell audit (`rg`, `xargs`, `/tmp`) with no `check`, no orphan or dangling gate, no drift
   report. Named is not loaded, and a body that is not loaded protects nothing. The "do not run any
   command" instruction was read as forbidding `Skill()` once in five; run 2's wording removed the
   ambiguity and the same case loaded the body and passed 4/4.
2. **The assertions are English.** Three of run 1's four failures were vocabulary: "no node" is
   "não ganha nó", "responsibility boundary" is "fronteira de responsabilidade", "does not own" is
   "não é dono". The responses followed the skill; the grader could not read them. The eval notes
   now say so, and a clean-session run pins the language — the routing evidence comes from the
   tool stream, which has no language.
3. **The cost of a session that explores is the cost to watch.** An unconstrained first attempt
   spent $7–8 and 600 s per case in plan mode reading the fixture; the constrained runs cost
   $0.69–$1.23 and 36–124 s. The measurement wanted routing plus one procedure description, and
   that is one to three turns. Spent on the day: about $39, of which $26 was the unconstrained
   attempt.

The `/evolve § 5` observation could not be run as `/evolve`: in print mode with the plugin loaded
from a directory, a plugin command is only `/graph-powers:evolve`, and the bare name returns
`Unknown command` in 12 ms with no model turn — on this machine the bare names belong to personal
`~/.claude/skills/graph-powers-*` copies of the commands, which predate § 5. Namespaced and given
room ($2.69, 30 turns, 161 s, tools `Read,Glob,Grep,Bash,Skill`), the flow **did** reach § 5 and
loaded `Skill("graph-powers:intent-layer")` as call 22 of 28, ran `state .` (→ `none`), and
planned the dated entry in `.graph-powers/logs/learnings.md`, the root pair via
`AGENT_SETUP.md § 4a`, then `check`. At a $1.5 cap the same flow ran out reading `000`, `005`, `060` and the fixture before
§ 5 — the budget, not the routing, was the variable: a second run at a $4 cap with tools
`Skill,Read,Glob,Grep` ($2.13, 26 turns, 131 s) loaded the skill as its last call and planned the
same three writes. Two of two runs that reached § 5 loaded it; zero of two that ran out of budget
did. One thing the run surfaced that is not this
skill's: `/evolve § 4` had the session propose writing the learning into the **plugin's** own
`skills/debugger/references/` — a host-project learning aimed at a globally installed plugin
directory. The final PR review closed it in the shared skill-domain matrix: selecting a method no
longer grants write ownership, and `/evolve` skips global/plugin destinations while keeping the
learning in the host project's log and `AGENTS.md`. The same clean-session case then passed at
$2.14 / 23 turns with a clean fixture: it selected `graph-powers:debugger` as method only, reported
`Skills: none (global plugin unchanged)`, and proposed no plugin-file write.

**Next round should measure:** whether a host project's setup actually writes
`intentLayer.deferred` rather than leaving `partial` on the report, and the same nine cases from a
Codex session, where nothing spawns or loads on its own (`execution-floor.md § 5`).
