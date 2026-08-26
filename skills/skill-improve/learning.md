# learning.md — round history for `skill-improve`

One entry per round, in the shape **hypothesis → change → measurement → verdict**. An entry with no
measured number does not count — it is a hunch with markdown around it.

A round that changed nothing still gets an entry saying so. A quiet round is evidence too.

```markdown
## Round N — <YYYY-MM-DD> · <one-line subject>

**Hypothesis:** what you expected to find, before looking.
**Change:** what you actually did.
**Measurement:** command output or the finding, quoted. Numbers, not adjectives.
**Verdict:** kept, refuted, or partial — and what the evidence killed.
```

---

## Inherited failure patterns

Carried from measured rounds in an installed harness, as rules rather than as history. The numbers
that produced them belong to another repository and are deliberately not reproduced here; what
transfers is the rule.

1. **No line of a Gates table enters without having been pasted into a shell and run verbatim, plus
   one run it must fail.** Writing the expected exit code beside a command is not the gate. The weak
   form of this rule — "paste the exit code next to it" — was adopted after the defect appeared
   once, and the same defect then recurred three more times in the same table, in four different
   shapes: a command missing its required arguments, a placeholder the shell read as a redirect, a
   threshold incompatible with the assertion severities, and an assertion that failed the *correct*
   behaviour. Every one was invisible until the line was executed in both directions.
2. **Fixing an internal contradiction displaces it rather than removing it**, whenever a file
   declares the same rule in two places. Two contradictions "fixed" in one round reappeared in the
   next round six lines further down. The real fix is one canonical home per rule, not N homes kept
   consistent with each other.
3. **Consensus between auditors is not evidence.** Two independent auditors agreed that a pair of
   hooks was dead code because neither appeared in `settings.json`; both were imported as modules by
   a hook that *was* declared. Reopen the file on disk before confirming anything dangles.
4. **`memory:` on an agent grants `Read`, `Write` and `Edit` on top of the `tools:` allowlist.** A
   researcher declaring an allowlist without `Read` resolves at runtime with `Write, Edit, Read`
   added. The obvious patch — "add the missing `Read`" — would have masked a P0 instead of fixing
   one. Read the frontmatter for what it grants, not for what it appears to withhold.

Pattern 2 is why this skill exists in its current shape: see Round 1.

---

## Round 1 — 2026-08-20 · merging `skill-creator` and `harness-audit`

**Hypothesis:** the two skills that shared this territory were not merely adjacent but overlapping,
and the cost of keeping them apart was being paid continuously in listing budget, eval cases and
prose — while the border still did not hold.

**Change:** merged `skills/skill-creator/` and `skills/harness-audit/` into `skills/skill-improve/`,
a two-mode router paired with the existing `graph-powers:skill-improver` agent. Detail moved to
`references/authoring.md` (Mode A) and `references/harness-wiring-audit.md` (Mode B).

**Measurement:**

| Metric | Before | After |
|---|---|---|
| SKILL.md non-empty body lines | 235 + 149 = 384 | 107 |
| Listing budget, skills subtotal | 3,625 | 3,177 |
| Listing budget, total | 9,331 / 10,752 | 8,898 / 10,752 |
| Headroom under the ceiling | 1,421 chars (13.2%) | 1,854 chars (17.2%) |
| Entries competing for this territory | 2 (381 + 296 chars) | 1 |
| Functional call sites | 0 | 1 (`commands/evolve.md`) |
| Duplicated or contradictory pairs found | 15 | 0 |
| Eval cases | 3 + 7, two suites in two schemas | 9, one suite, one schema |

**Verdict: kept.** Three results changed the design rather than confirming it.

1. **The repository had already measured the collision and had not acted on it.** The eval case
   `neg-skill-does-not-fire` carried a note recording that "my skill does not fire" was the exact
   prompt where the two skills collided, and that no eval had covered it. The response at the time
   was to add a case defending the border. The border was the defect.
2. **Two of the doomed negative cases were not waste — they had the wrong polarity.** "Create a
   skill for X" and "my skill does not fire" asserted that this skill must *not* fire, because
   firing the wrong one of two skills was the failure then. After the merge the skill fires either
   way and the remaining failure is picking the heavier mode, so both were repointed as Mode A
   positives, one of them with an assertion that Mode B did **not** run. Deleting them would have
   dropped the only cases sited exactly on the surviving internal border.
3. **The merged skill inherited a contradiction in every direction it looked** — pattern 2, in 15
   instances. The description cap was stated as 1024 in three files and 1536 in three others, and
   only the 1536 is enforced by anything. The eval path was documented as nested in one section and
   flat in another *of the same file*, with the file's own evals in the form its own instructions
   forbade. The frontmatter contract said "`name` and `description` only" while the sibling skill
   shipped five fields. A naming rule demanded gerund form, which condemns every skill name the
   plugin ships. None of these was a disagreement between authors: each was one author writing the
   same rule twice, months apart, and believing both.

**Pattern 1 fired during this very round, twice.** Both were invisible until the line was run:

- `quick_validate.py` reported this skill's description as not starting with "Use when" when it
  does. The regex captures the opening quote as part of the value, so a quoted scalar — the form
  the same validator forces, because a folded one is rejected — can never satisfy the prefix rule.
  Fixed with an `unquote` helper applied to both `name` and `description`, which also repairs the
  inverse defect where a quoted `name` failed the hyphen-case check. Verified in both directions:
  the warning now fires on `planning`, whose description really does start with "Layer ordering",
  and no longer on this skill.
- One assertion read `contains: precedence` and failed a correct response, because a real report
  capitalises the word at the start of a sentence and `contains` is case-sensitive. Four prose
  assertions were converted to `regex: (?i)...`; literal filenames, flags and identifiers were left
  alone. Measured before the fix: 8/9 cases exit 0. After: **9/9**, with a deliberately wrong
  response exiting 1 and a positive response scored against a negative case exiting 1.

Honest caveat: those 9 responses are synthetic, written to exercise the assertions. The gate is
proved as a mechanism, not yet as a measure of behaviour in a clean session.

**Refuted:** the premise that `skill-improve` was a live name that would collide. It was not — the
name existed only in `NOTICE` and a local settings grant. What did collide was `skill-creator`'s
description claiming the trigger "improve this skill", and that disappeared with the merge rather
than needing a resolution.

**Also refuted:** the assumption that `allowed-tools` on the audit half bought its report-only
guarantee. It is an additive pre-approval grant, not a restrictive allowlist — the rubric had
already retired that premise. The field was removed and the guarantee stated honestly: a skill
cannot restrict its own tools, and what enforces read-only is the paired agent's `disallowedTools`.

**Next round should measure:** the trigger hit rate across all 9 cases against responses captured in
a clean session — the runner is proved as a mechanism here, not yet as a measure of real behaviour.
And whether Mode A escalates to Mode B when it should, which is the one border the merge created
rather than removed.


---

## Round 2 — 2026-08-20 · dogfood: what invokes it, and when does it read what it wrote

**Hypothesis:** the merged skill was correct, because every gate passed and the 15 duplicated pairs
were resolved. A `PASS` was the expected result.

**Change:** asked two questions of the artefact instead of of the gates — what invokes this
proactively, and when does it open the files it creates. Traced every invocation path and every
producer/reader pair on disk.

**Measurement: 4 defects, none of which any gate could see.**

| # | Defect | How it was found |
|---|---|---|
| 1 | `user-invocable: true` and `argument-hint` were deleted along with `allowed-tools` | Grep for the fields returned **zero hits in the whole repository** — the merge removed the only occurrence. Rubric W4 retired `allowed-tools` only; the other two are live fields that shipping plugins use, and dropping them removed the ability to type the skill as a slash command at all. The reference still documented `--all` and `--phase N`: arguments nothing declared and the skill could no longer receive. |
| 2 | `learning.md` is written at the end of every round and read at the start of none | All ten references to it are write instructions, checklist items, or mid-text pointers. Nothing said "open this before you start". Inherited failure patterns exist to stop a catalogued mistake from recurring, and a pattern nobody loads prevents nothing. |
| 3 | The mandatory `MEMORY.md` paste had no path | Phase 5 ordered "paste the FULL contents of the auditor's MEMORY.md" and never said where it lives. The path existed only in `agents/skill-improver.md`, which the *agent* reads — not the caller who has to do the pasting. Worse, Phase 0's skip-list named `agent-memory/` as skipped, so the skill told itself to skip the directory it must read from. |
| 4 | No automatic trigger existed at all | Invocation was: the description in the session listing, plus one conditional `Skill()` in `/evolve`. No hook, no SessionStart, no agent `skills:` preload, no path-triggered rule. |

**Verdict: NEEDS_WORK, all four patched.** Two results are worth more than the count.

1. **Defect 1 is inherited pattern 2 in its purest form, committed by the round that wrote pattern 2
   down.** Merging deduplicated the frontmatter contract to "`name` and `description` only", and
   applying that rule mechanically deleted two fields the rule was never about. Resolving a
   contradiction by picking one side also deletes whatever the losing side carried that was not part
   of the disagreement. The surviving rule was correct; the deletion it licensed was not.
2. **Defect 4 had an answer sitting unused in the repository.** `.claude/rules/artifacts.md`
   auto-loads on `agents/**`, `skills/**`, `commands/**`, `references/**` and `workflows/**` — the
   exact territory this skill owns — and never named it. That glob is the only trigger here that
   does not depend on a model reading a description and choosing; it now points at the skill. The
   file whose own section is titled "What invokes it" was the missing call site.

**Refuted:** that passing every gate meant the artefact was sound. All four defects are invisible to
`check_wiring`, which resolves `Skill()` calls, `subagent_type` and cited sections — none of which is
"a file written but never read" or "a field deleted everywhere at once, so nothing dangles". A wiring
gate cannot see a missing edge that no file claims exists.

**Next round should measure:** whether the `Before either mode` read actually happens, which needs a
transcript rather than a grep; and the trigger hit rate in a clean session, still unmeasured after
two rounds.


## Round 3 — 2026-08-26 · authoring `designer`, the direction pass in front of `/design`

**Hypothesis:** a model asked for "bolder, no AI slop" would avoid the catalogued defaults on its
own once told what they are, so the skill's value would be the catalogue, and a list of tells plus
a floor would be enough.

**Change:** created `skills/designer/` — SKILL.md (138 non-empty lines, 10,542 B), two
references (`defaults-catalogue.md` 11,912 B, `mirror-test.md` 3,350 B), eight eval cases. Wired
it into `/design § 0` and `§ 1`, the skill-domain matrix, the WISC load and the invocation order;
declared `emil-design-eng` and `apple-design` as optional external skills in `check_wiring.py` and
README; bumped 1.9.5 → 1.10.0 across the five manifests. Research: 16 sources fetched by
`graph-powers:librarian`; the Apple HIG fetch failed, so `apple-design` (WWDC-derived) stood in for it.

**Measurement.** Twelve subagents in one message: eight with the skill (four positives, four
negatives at the real borders), four baselines on the positives without it. One invocation per
case id, `--threshold 1.0`.

| Case | With skill | Baseline (A01 "names the skill" excluded as unfair) |
|---|---|---|
| pos-new-surface-no-design-system | exit 0 | 33% — locked **one** direction, no three, no contract, no exit |
| pos-looks-ai-generated | exit 0 | 80% — good, but no mirror test; the accent chosen as "the opposite of the earth-tone default", by negation |
| pos-bolder-without-slop | exit 0 (after one assertion widened) | 25% — see below |
| pos-brief-pins-the-look | exit 0 | 75% — kept the pinned values, then spent the free axes on eyebrows, numbered principles and paper grain: three catalogue defaults |
| neg-motion-tuning-only | exit 0 → `emil-design-eng` | — |
| neg-conversion-lever | exit 0 → `uxmaster` | — |
| neg-broken-control | exit 0 → `/debug` | — |
| neg-craft-pass-on-locked-direction | exit 0 → `impeccable typeset` | — |

Gate in the failing direction: the motion response graded as `pos-new-surface` → 0/6, exit 1.

Repository gates: `quick_validate` 0 · listing budget headroom 2,172 → 835 chars (designer 637,
`/design` +13, and 687 from a `skills/animate/` that is not this round's — see 4) · context budget
floor **297,104 B (red, over by 2,104, on a clean `main`) → 294,927 B (green, 73 B under)** ·
wiring 241 references, 0 unresolved · hooks "EVERY GUARANTEE HELD" · every other gate 0.

**Verdict: hypothesis refuted; skill kept.** Four results.

1. **Avoiding by list does not escape the mode.** The `pos-bolder` baseline was asked for "bolder
   without AI slop", wrote a "refused on sight" slop list — gradients, glass, glow, equal cards —
   and then delivered **"Concept: Broadsheet"**: warm off-white `#F7F5F0`, Instrument Serif hero
   numbers, international orange, hairline rules. That is catalogue looks #1 and #3 fused, with the
   ban list attached. The `pos-new-surface` baseline derived genuinely from podcasting (timecode,
   tracklist, the recording light) and still landed on cream paper `#F3EEE3` + Fraunces + one red.
   Knowing the tells is not deciding; the skill's value is the method (mine the world, diverge in
   kind, mirror), and the body's rule "read the catalogue at move 5, not before move 2, or it
   becomes a menu" is now measured rather than asserted.
2. **Authoring pattern 2 fired once** — a narrow regex failing correct behaviour. `A02` on
   `pos-bolder` demanded the literal "one signature"; the with-skill response wrote "boldness is
   one lit tile" and a `Signature` contract line. Widened to `\bsignature\b`; the baseline still
   fails it, so the assertion still discriminates.
3. **The context-budget gate reads a different number than the session pays.** `walk()` drops
   fenced blocks by design, and `/design § 0` loads its skills inside one, so the `Skill("designer")`
   line costs the gate nothing while every `/design` run really loads 10,542 B more. The gate went
   red-to-green because the `030-agent-assignment-matrix.md` read was made conditional ("only when
   the scope needs an agent § 2, § 3 and § 5 do not already name") — a true statement about
   `/design`, whose agent set is fixed — not because the skill is free. Both numbers are recorded
   here so the next round does not read the green as cheap.
4. **A file this round did not write appeared mid-measurement.** `skills/animate/` (untracked,
   07:55–07:57, a merge of Emil's four motion skills, description already naming `designer`)
   landed while the eval agents ran — a parallel session, not one of the twelve, none of which had
   a write instruction. Its 687 listing chars spent the headroom this round was measuring against,
   and its description claims `/design` loads it before the `animate` pass, which is the line this
   round wrote for `emil-design-eng`. Left untouched; one writer per file, and the reconciliation
   is the owner's. Measure a shared budget against `git stash` and an untracked-file check, not
   against the last run's memory.

**Honest caveat:** the twelve responses are real subagent behaviour against the real files, but
the trigger half is simulated — the agent was handed a six-entry listing and asked to choose, not
a live session listing with a hundred skills. Negatives all routed away from `designer`; whether the
description also wins against `impeccable`'s much longer one in a real listing is still unmeasured.

**Next round should measure:** the description against the live listing in a clean session, with
`impeccable` and `animate` both present; and whether `/design § 1` actually produces three
directions on a structural run in a host repository with a `DESIGN.md`, where the "authority
settled" branch has never been exercised.


---

## Round 4 — 2026-08-26 · authoring `animate`, four motion skills merged into one

**Hypothesis:** the four Emil Kowalski motion skills (`animate`, `review-animations`,
`improve-animations`, `find-animation-opportunities`) would merge the way `skill-creator` and
`harness-audit` did in Round 1 — one rulebook, several verbs — and the cost would be one listing
entry instead of four.

**Change:** `skills/animate/` — `SKILL.md` as the rulebook plus a four-mode router (build, review,
audit, find), `references/recipes.md`, `references/review.md`, `references/audit.md`, nine eval
cases. Wired from `/design § 3` (conditional, before the `animate` craft pass), the `/pr-review`
3D row in prose (the agent loads the skill in its own context), a skill-domain matrix row, the
invocation order, and one line in the bodies of `graph-powers:frontend-specialist` and `graph-powers:ui-ux-designer`
(Codex native agents regenerated). NOTICE and CHANGELOG credit the MIT source.

**Measurement.**

| Metric | Value |
|---|---|
| Upstream, four `SKILL.md` bodies plus four reference files | 544 + 699 lines |
| Merged `SKILL.md` | 195 non-empty lines, 14,646 B; references 25,885 B |
| Copies of the frequency table, the three curves and the duration budgets | 4 → 1 |
| Listing budget | 9,895 / 10,752, 857 chars headroom (was 1,522 before `designer` and `animate`) |
| Context floor | 295,227 B; ceiling 468,749 B |
| Trigger gate, one invocation per case, `--threshold 1.0` | 9/9 exit 0; 4 must-fail runs exit 1 |
| Every repository gate | exit 0, except `check_wiring` — see below |

**Verdict: kept**, with three results that changed the shape.

1. **The context floor was the binding constraint, not the listing budget.** The floor stood at
   73 B of headroom under `FLOOR_CEILING` when the round opened — Round 3 spent 3,117 of the
   3,190 B the 2026-08-24 lowering left, and did not touch the constant. The first wiring of
   `animate` measured +16,354 B on the floor: the `/design § 3` call was written without a
   condition on its line, so the script priced the whole skill on every invocation. Rewriting
   the sentence as the conditional it is (the pass runs in `improve` mode only) moved 14,948 B
   to the ceiling; what remained was 300 B of routing rows, priced at four command floors for the
   matrix. The constant was raised to 300,000 with the cause in the comment, per the script's own
   contract, rather than shaving a matrix row down to a bare name.
2. **The ceiling counts a skill once per command that names it in `Skill()` syntax.** Two call
   sites would have charged 29,896 B and failed by 15 KB. The `/pr-review` 3D track is a spawned
   agent, and the script's own rule says what a subagent reads is paid from the subagent's
   context — so the row names the mode in prose and `graph-powers:ui-ux-designer`'s body carries the
   `Skill("animate")` call. Honest by the script's definition, and the ceiling closed at 1,251 B
   of headroom.
3. **Pattern 1 fired once.** `A06` on `pos-review-diff` read `\*\*block\*\*` and failed the
   correct response, which writes `**Block.**` with the period inside the bold — assertion rule 2,
   the narrower pattern inverting the error. Fixed to `\*\*block\b`; verified in both directions,
   an *Approve* response against the same case exits 1.

**Not mine, and left in place:** `check_wiring` exits 1 on `skills/designer/SKILL.md:176`, which
cites `references/craft-passes.md § 3` — a file and a line that did not exist when this round
opened. A concurrent session is editing `skills/designer/`; the round did not touch that citation.
Also from Round 3: `learning.md` named `graph-powers:librarian` without its namespace, and the namespace gate
added in the same session caught it — patched here to `graph-powers:librarian`.

Honest caveat, as in Round 1: the nine responses are synthetic, written to exercise the assertions.
The gate is proved as a mechanism; the trigger hit rate in a clean session is still unmeasured,
four rounds in.

**Shadowing to decide:** the machine this was authored on carries the four upstream skills at the
user level (`~/.claude/skills/animate` and siblings), so a bare `Skill("animate")` resolves to the
upstream copy there until it is removed. On a clean install the plugin's copy is the only one.

**Next round should measure:** the trigger hit rate across the nine cases in a clean session, and
whether `/design improve` actually loads `animate` before the `animate` pass — a transcript, not
a grep.

---

## Round 5 — 2026-08-26 · folding `second-opinion` into `graph-powers:evaluator` as Mode 5

**Hypothesis:** the skill was a fifth evaluator mode wearing a skill's clothes — one call site
(recovery Step 4), a description that named a trigger the evaluator's did not, and a headless
invocation whose blindness the subagent boundary already provides. Expected: a mechanical move,
no defect in the moved content.

**Change:** deleted `skills/second-opinion/`; `agents/evaluator.md` gained Mode 5 in its
description, Phase 1 and Stopping Conditions; `references/rubrics/evaluator-rubric.md` gained the
Mode 5 section with the caller's side (question rules, two engines, the dollar ceiling); the six
call sites were repointed — recovery Step 4, `060` matrix row, `/debug` § 0 and § 7, the debugger
and planning escalation tables, the `graph_guardrails.py` docstring, `AGENT_SETUP.md` rows.
`codex/native-agents/evaluator.md` regenerated with `bun codex/native-plugin.mjs`.

**Measurement:**

| Metric | Before | After |
|---|---|---|
| Listing budget, skills subtotal | 4,710 (with `second-opinion` at 344) | −344 from this round; the total still exceeds the ceiling by 37 chars from two skills a concurrent session added |
| `check_wiring.py` | 1 unresolved (a concurrent session's `designer` citation) | 0 unresolved, 12 agents, 0 that would not register |
| `check_codex_native.py` | `evaluator.md is stale` after the agent edit | 12 agents, manifest 1.10.0 |
| Context-budget floor, this round's share | — | debug +481 B, plan +86, implement +345, verify +281 — the trimmed pointers; `/design` +15,348 is the concurrent session's |
| Headless engine, measured on CLI 2.1.245 | `claude -p --model opus … --disallowedTools Write Edit "<q>"` | `claude -p "<q>" --agent graph-powers:evaluator --max-budget-usd 1.50 --permission-mode plan --disallowedTools Write Edit` — `result: OK`, `modelUsage: claude-opus-5`, `$0.11`, one turn |

**Verdict: kept, and the hypothesis was refuted on "no defect in the moved content."** Pattern 1
fired on a line that had shipped for two releases: the skill's invocation put the question *after*
`--disallowedTools Write Edit`, and that flag is variadic. Run verbatim, the CLI printed
`Permission deny rule "Reply" matches no known tool — check for typos` once per word of the
question and exited 0 with no review run — a headless call that reported success and asked
nothing. The published line was never pasted into a shell. The moved form puts the prompt first
and was run in both directions: a nonexistent `--agent graph-powers:does-not-exist` exits 1 naming
the available agents, the real one returns on the agent's declared model without a `--model` flag.

Two smaller results. `--agent <plugin>:<agent>` works in print mode, so the headless engine now
literally runs the same agent file rather than a prompt imitating it — the only behavioural
difference between the two engines is the dollar ceiling. And the coreutils `timeout` wrapper was
a cardinal 8 violation nobody had flagged because `check_portability.py` does not list `timeout`;
it is gone, with the Bash tool's own timeout as the wall-clock cap, and `AGENT_SETUP.md` drops the
row that installed it.

**Not mine, and left in place:** `docs/plans/2026-08-20-intent-routing-plan.md:174` still lists
`second-opinion` as a skill row — a dated plan, not a routing surface, and not scanned by the gate.
The listing and context-budget ceilings are exceeded by a concurrent session's additions
(`landing-page-design`, `intent-layer`, the `/design` load); reported to that session, not patched
here.

**Next round should measure:** whether recovery Step 4 actually spawns Mode 5 with `Prior
findings` and `Do NOT redo` left empty — the one spawn where the contract is the blank — from a
transcript, not from the prose that says so.


## Round 6 — 2026-08-26 · porting `landing-page-design` from an external copy into the plugin

**Hypothesis:** the port would be a move — the upstream file was already routed by `/design`, so
the work would be attribution plus a narrower description, and the gates would stay where they were.

**Change:** created `skills/landing-page-design/` — SKILL.md (193 non-empty lines, 15,854 B), one
reference (`house-canon.md`, 12,784 B), eight eval cases (14,611 B) — as an adapted work under
`NOTICE`. Part A of the upstream file (the page system) kept in substance; Part B (the visual
canon) moved whole to the reference as a fallback behind the project's design authority, the
`designer` contract and the `animate` rulebook, each value tagged craft or house taste with its
reason. Description 655 → 589 chars, "any web UI" narrowed to landing and marketing surfaces.
Reversed the 1.9.2 decision in `docs/ARCHITECTURE.md § 7`, README, `docs/AUDIENCE.md`, `NOTICE`,
`AGENT_SETUP.md § Step 1` (install section replaced by a removal step and a `SHADOWS` preflight
row, both run against a throwaway HOME before being written down), `check_wiring.py`
`EXTERNAL_SKILLS`, the domain matrix, the invocation order, `designer`'s depth list,
`commands/design.md § The design layer`, CHANGELOG 1.10.0.

**Measurement.** Two research agents before writing: a read-only design critique across the
siblings returned **45 collisions** (5 P0 — the "this file wins" precedence claim, the mandatory
gradient headline, `transition-all duration-700`, the fade-up on every element, the mandatory
tagline section — all in Part B) and 18 universal rules; a librarian verified 9 claims against
primary sources: 5 hold, 2 outdated (Google removed FAQ rich results on 2026-05-07; `text-wrap:
pretty` is Chromium-only per caniuse), 1 nuanced (`noindex` controls visibility, not crawl budget),
1 unverifiable (FAQ 6–12 is convention). One upstream rule was inverted rather than adapted: the
"organic" fake numbers (`47.2%`) that made invented proof more plausible.

Evals: twelve subagents in one workflow — eight with the ported skill in an eight-entry listing
(designer, animate, uxmaster, landing-page-design, the global `redesign-existing-projects`,
`/design`, `/debug`, `/perf`), four baselines on the positives with the upstream file and its
upstream description in the same slot. One invocation per case id, `--threshold 1.0`.

| Case | With skill | Baseline (upstream file) |
|---|---|---|
| pos-new-landing-from-ads | exit 0 | exit 1 — no single primary action, no outline before code |
| pos-hero-copy-rewrite | exit 0 (after 3 assertions widened) | exit 0 |
| pos-index-decision-campaign-page | exit 0 | exit 0 |
| pos-project-design-authority-wins | exit 0 (after 2 widened) | exit 0 — kept Inter despite upstream's ban |
| neg-app-screen-layout | exit 0 → `/design` + `designer` | — |
| neg-motion-value-only | exit 0 → `animate` (after 1 list fix) | — |
| neg-broken-signup-form | exit 0 → `/debug` | — |
| neg-activation-lever-in-product | exit 0 → `uxmaster` | — |

Failing direction: all four negative responses graded as `pos-new-landing-from-ads` exit 1; a
synthetic wrong response exits 1 on every positive case and 0 on the negative it belongs to.

Repository gates on the final tree: `quick_validate` 0 · listing budget 10 chars headroom (my entry
608, five other new entries this release) · context budget floor 298,004 / cap 300,000, ceiling
497,170 / cap **500,000 — raised from 470,000 with the cause in the comment** · wiring 259
references, 0 unresolved · portability, machine paths, placeholders, JSON, workflows, hooks, clone,
version bump: 0.

**Verdict: hypothesis refuted; skill kept.** Four results.

1. **The port was not a move; it was a precedence problem.** 45 collisions, and every P0 was a value
   the harness already owned — the palette, the curve, the reveal, the signature. Adapting meant
   writing the ownership table and demoting Part B to a proposal, not copying it closer. The
   authoring reference's "one excellent example beats three" held in the other direction too: one
   precedence table replaced eleven "this file wins" sentences.
2. **Authoring pattern 2 fired six times in one round.** Six of the eight with-skill cases passed on
   the first grade; the two that failed, and one negative, failed on correct behaviour: "Sub:" for
   subheadline, "what the person gets" for "what they get", "fabricated proof" for the realism
   floor, "belong to every product and therefore to none" for "cliché", "DESIGN.md is the
   authority" for "design authority", and "above the fold" as legitimate motion vocabulary inside
   a negative's ban list. Every widening was checked against the synthetic wrong response, which
   still exits 1. The synthetic self-check found a seventh before any real run: an absence check
   that failed a refusal saying "no page outline" — pattern 3, now guarded by a negation lookbehind.
3. **Three of four baselines pass, so three positives do not discriminate.** The upstream file
   already handles hero copy and the index decision, and the model kept a pinned Inter against the
   upstream ban on its own judgement. What the port measurably adds is the first case — one action,
   outline before code — and the four borders, which the upstream description ("any web UI")
   cannot hold by construction. The next round should replace two non-discriminating positives with
   cases sited on the canon: a page with no design authority (does the canon get *proposed* rather
   than applied?) and a request for the tagline reveal on a page whose signature is elsewhere.
4. **The context-budget gate priced a prose line, not the fence.** `Skill("landing-page-design")`
   inside `/design § 0`'s fence costs nothing (round 3, note 3), but the same call in the prose
   paragraph of `§ The design layer` was charged on the floor — 15,920 B, the whole overage — until
   the condition word moved onto that line. The floor then dropped 313,602 → 297,920 with no file
   shrinking. A gate that reads a condition word is a gate that can be satisfied by moving a word;
   the honest number is the ceiling, which is why the ceiling was raised and the floor was not.

**Refuted:** that the external copy was gated by `/design`. A personal-scope skill is listed in every
session regardless of what any command says, and on this machine it shadows the plugin's copy under
the same bare name — `ESCOPO GLOBAL`, outside the repository: `~/.claude/skills/landing-page-design`
and `~/.agents/skills/landing-page-design` still exist here and must be removed by hand with the
Step 1 command before the ported skill is the one that loads.

**Honest caveat:** five sessions were editing this repository during the round; the listing headroom
moved from 835 to 10 chars under me, and the measured numbers are the tree at 08:40, not the tree
this entry is read in. The trigger half is simulated as in rounds 3 and 4 — an eight-entry listing,
not a live session with a hundred skills.

**Next round should measure:** whether `/design` on a real landing surface in a host repository with
a `DESIGN.md` resolves every axis to the authority and *proposes* rather than applies the canon;
and the two replacement positives named in result 3.


## Round 7 — 2026-08-26 · the pre-merge `harness-audit` comes home, and the runner stops lying

**Hypothesis:** the global `~/.agents/skills/harness-audit/` (2026-08-19, zero rounds in its own
`learning.md`) still carried rules the 2026-08-20 merge had lost, and bringing it "into the plugin"
would mean restoring them into Mode B.

**Change:** diffed the global section by section against `references/harness-wiring-audit.md`,
then ran a five-lens review (merge-loss, cardinals, producer/reader, eval-suite, runner) with one
adversarial refuter per P0/P1 — 13 agents, 1.06M tokens, 14 minutes — and dispatched
`graph-powers:skill-improver` for the SELF-AUDIT verdict with the first-round line
`MEMORY.md: absent` in place of the paste. Applied inside `skills/skill-improve/` only:

- Mode B Phase 3 crosses every layer that serves a listing and greps each for the retired names of a
  merged or renamed skill; Phase 0 defines the argument and `--phase N`; Phase 5 says the artefacts
  are on disk; Phase 6 reports `graph.mmd`, the scope limits, and sends a host project's round
  record to the host's `.claude/audit/learning.md`; the settings gate is fail-open; the config
  section names its defaults; rubric codes are back beside the findings.
- `run_evals.py`: `--response-dir` (every case against `resp-<id>.txt`, missing file and zero cases
  are failures), critical assertions fatal at any threshold, unknown ids and invalid checks as red
  rows. `init_skill.py`: a quoted description without colon-space, `evals/` and `learning.md`
  scaffolded, UTF-8 everywhere. `quick_validate.py`: rejects an unquoted description with `: `.
- `evals.json`: three cases added (`pos-escalate-a-to-b`, `pos-ancestor-collision`,
  `pos-periodic-audit`), seven assertions rewritten, one added to `pos-skill-does-not-fire`.
- `NOTICE`: the "unmodified upstream" claim about `scripts/` corrected; `.gitignore`: `.claude/audit/`.

**Measurement:**

| Metric | Value |
|---|---|
| Rules in the global absent from Mode B and not a recorded decision | 0 (every drop was cardinal 8 portability or Round 1) |
| Findings from the five lenses | 62 raw, 62 after dedup, 8 verified (cap), 6 confirmed, 2 refuted, 54 left PLAUSIBLE |
| Applied from the 54 unverified, after checking the cited line by hand | 27 |
| Eval cases | 9 → 12; `--response-dir` 12/12 exit 0; six wrong-direction runs exit 1 |
| Runner fixtures | invalid check values → 3 red rows, no traceback; all-manual case exit 1; zero-case file exit 1; critical miss at 0.5 exit 1; non-critical miss at 0.5 exit 0 |
| Validator | unquoted `: ` description exit 1; this skill exit 0; the new scaffold exit 0 and `yaml.safe_load` parses it |
| Settings gate, three directions | absent 0 · valid 0 · malformed 1 |
| Listing budget | skill-improve 567 → 584 chars (+2 net in the description, +15 in the name column's rounding); total 10,672 / 10,752, 80 chars headroom — four other rounds landed skills the same morning |
| SKILL.md non-empty body lines | 125 → 136 |
| Judge verdict | `NEEDS_WORK`: 0 P0, 3 P1 (one SELF-AUDIT inside the skill, fixed in the same turn; two outside it, reported), 6 P2 |

**Verdict: hypothesis refuted; the round kept for what it found instead.** Four results.

1. **Nothing was lost in the merge; what was missing was the merge's own residue.** Both ancestors
   are still served from the personal layer — `~/.claude/skills/harness-audit` and
   `~/.claude/skills/skill-creator`, symlinks into `~/.agents/skills/` — listed in every session
   beside `graph-powers:skill-improve`, and the global `skill-creator` still routes wiring questions
   to `harness-audit`. Round 1 wrote that the `skill-creator` trigger collision "disappeared with the
   merge". It did not: it moved one layer up, where the repository's gates cannot see it. Both are
   `REMOVAL_CANDIDATE` with double evidence (no call site anywhere in the global config, hooks or
   skills; the successor carries a strict superset). Global scope, outside the repository — the
   unlink is the user's.
2. **Inherited pattern 1 fired again, in the round that fixed three instances of it.** The fail-open
   settings gate was written into the reference's table and described as "measured in three
   directions" while `SKILL.md`, which the same reference names as the one home for command text,
   still shipped the line that raises `FileNotFoundError` in this repository. The judge ran the
   canonical row verbatim. The rule now has a corollary: when a file says the command lives
   elsewhere, patch there first and grep the home before recording the fix as applied.
3. **The validator was the defect, not only the template.** `init_skill.py` scaffolded an unquoted
   description with a colon-space — not YAML — and `quick_validate.py` passed it, because every gate
   in the chain tested for the substring `description:` and none parsed the shape. The same shape
   left four command files unregistered once (CHANGELOG 1.x). The template is fixed and the
   validator now rejects the shape, which is the half that prevents the next one.
4. **Round 1's measurement was wrong on the caps.** "The description cap was stated as 1024 in three
   files and 1536 in three others, and only the 1536 is enforced by anything" — `quick_validate.py`
   enforces 1,024 on `description` alone, `check_listing_budget.py` enforces 1,536 on `description`
   plus `when_to_use`. Two quantities, both live; the table now carries both.

**Refuted:** that `run_evals.py` was upstream code. No commit in anthropics/skills touches that
path; upstream ships `run_eval.py`, a different tool that measures triggers by running `claude -p`
against a temporary command file — which is the clean-session measurement every round here has
deferred. Its `select.select` on a pipe is POSIX-only, so a port rather than a copy.

**Honest caveat:** the 12 responses are synthetic, written to exercise the assertions; the runner and
the assertion set are measured, the skill's live trigger behaviour still is not — four rounds now.

**Next round should measure:** the trigger hit rate in a clean session, by porting upstream's
`run_eval.py` approach to `subprocess` with `encoding="utf-8"` and no `select`; and whether the
judge's four recurring patterns, once in `MEMORY.md`, change a verdict.


## Round 4 — 2026-08-26 · `/design` drops the `impeccable` dependency; `designer` carries the craft passes

**Hypothesis:** the craft passes `/design § 3` delegated to the external plugin could be written
into `designer` as two references — the passes and the floor — and the removal would be a routing
change: swap the call sites, delete the install instructions, done.

**Change:** new `skills/designer/references/craft-passes.md` (the passes, what each asks, reads,
changes, and when it is done) and `craft-floor.md` (the checks on the built result); `/design`
"## The design layer" and `§ 3` rewired to `graph-powers:frontend-specialist` with a fenced handoff
template, `audit` read-only in `graph-powers:ui-ux-designer`, `animate` pass opened by path;
impeccable removed from README, AGENT_SETUP § Step 1 (its runner table survives as "Package
runners"), NOTICE, both docs, both skill matrices, the hook test fixtures, the codex comments; the
eval case for a locked-direction craft pass repointed from `/impeccable typeset` to
`/design fix … only the typeset pass` and re-measured (4/4, exit 0).

**Measurement.** A read-only workflow: 4 finders (dangling/contradiction, coverage + licence
hygiene, cardinals, orchestrator dry-run) → 10 findings after dedup → 3 lenses each (correctness,
materiality, fix-validity), 34 agents, 2.2 M tokens. Confirmed by ≥2 of 3, and fixed:

| Finding | Where | What the lens added |
|---|---|---|
| CHANGELOG said "impeccable still polishes it" three lines above "Removed — the impeccable dependency" | `CHANGELOG.md` 1.10.0 | materiality: P2, not P1 — no agent reads the changelog; a maintainer does |
| Four near-verbatim runs from impeccable in `craft-floor.md` (the inspection paragraph, the heading-spacing rule, "run the real copy", the whole Browser-surfaces paragraph) plus two from Anthropic's `frontend-design` in `SKILL.md`, under a sentence claiming "written for this harness rather than copied" | `craft-floor.md`, `SKILL.md`, `defaults-catalogue.md` | fix-validity: reword every run, not the one clause — or the claim stays false |
| `audit` demanded "the rendered result at desktop and mobile" from an agent whose tools are Read, Grep, Glob, WebFetch | the audit entry of `craft-passes.md` | the render is captured before the delegation by `graph-powers:verification`; the rule's single home is `/design § 2` |
| `Skill("animate")` inside `graph-powers:frontend-specialist`, which carries no `Skill` tool | the animate entry of `craft-passes.md`, and the third section of `/design` | path read of `${CLAUDE_PLUGIN_ROOT}/skills/animate/SKILL.md`; the same gap exists in two agent files another session owns and was handed to it |
| The mode→passes table and the who-runs-what table lived in both `/design § 3` and `craft-passes.md` | `craft-passes.md` | one home: the command routes, the reference is what the executor reads |

Refuted (2): a stale README sentence a parallel session had already fixed; "the context-budget gate
fails" — it did not on the tree at verification time.

Verbatim overlap, measured mechanically as shared 8-word runs against every impeccable reference
file, Anthropic's `frontend-design`, `emil-design-eng` and `apple-design`: **21 before the fix, 0
after.** Gates on the merged tree at the end of the round: wiring 0 unresolved of this round's
references; context budget floor 2,241 B and ceiling 15,228 B of headroom (`/design` floor 16,381 B,
because the two craft references are read by the specialist inside the fenced handoff, not by the
command); `quick_validate` 0; hooks "EVERY GUARANTEE HELD"; portability, placeholders, machine
paths, JSON 0. The listing budget is **red by 221 chars** — five method skills a parallel session is
porting in from superpowers; `designer`'s description was trimmed 625 → 551 chars anyway.

**Verdict: hypothesis refuted; change kept.** The removal was not a routing change. Three of the
five confirmed defects were things impeccable had quietly supplied and the swap silently lost: a
browser for the critic (its own scripts rendered), a way for the specialist to reach the motion
rulebook (its own `/impeccable animate` was a slash command, not a subagent), and the discipline of
not restating the pass table in two places. The fourth — the near-verbatim runs — is the failure
`docs/ARCHITECTURE.md § 7` describes for the first version of this repository, reproduced at
sentence scale by the round that cited it: writing "from scratch" with the source open produces
the source's sentences. The 8-gram check is the gate that catches it, and it did not exist until
this round.

**Also measured, procedurally:** three sessions edited the same files in the same hour. Every edit
here was an exact-match replacement that aborts on drift; it aborted four times, each time on a
file a peer had just changed, and each time the re-read found the peer's version was the one to
keep. A blind overwrite would have lost the `animate` rewiring twice.

**Next round should measure:** whether `graph-powers:verification` actually produces the render
`/design § 2` now orders, in a host project with a staging URL — the wiring resolves, the behaviour
is unexercised; and the listing budget, which no longer holds the plugin as a whole.

**Addendum, same day.** A read-only verification from another session flagged two lines the
`animate` round left in `agents/frontend-specialist.md` and `agents/ui-ux-designer.md`: a
`Skill("animate")` call inside agents whose `tools:` carry no `Skill` — the call cannot resolve in
the subagent, and `check_wiring` cannot see it, because the name resolves and the gate does not
read the caller's allowlist (rubric W2, "dangling when the citing agent lacks the tool to open it").
Replaced by a path read of `${CLAUDE_PLUGIN_ROOT}/skills/animate/SKILL.md`, which also sidesteps
the personal-scope `animate` that shadows the plugin's on this machine; Codex mirrors regenerated.
The gate that would have caught it is the one Mode B runs by hand, not any script here.
