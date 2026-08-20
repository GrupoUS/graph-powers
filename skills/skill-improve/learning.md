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
