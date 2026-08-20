---
name: skill-improve
description: "Use when authoring or iterating one skill, or when auditing how a whole harness is wired. Trigger on make a skill for X, improve this skill, my skill is not triggering, description tuning, the eval loop that proves a change helped — and on are my agents, skills and commands connected, audit my harness, this skill fires at the wrong time, the subagent is not found, what part of .claude no longer earns its place. Designing one agent's prompt is senior-prompt-engineer; choosing which agents to spawn for a task is the always-in-force execution floor."
user-invocable: true
argument-hint: "[skill-path | --all | --phase N] — a skill path picks Mode A, no argument audits .claude/ in Mode B"
---

# Skill Improve

> Derived from `skill-creator` in anthropics/skills (Apache-2.0, see `LICENSE.txt`). Modified by
> GrupoUS: the authoring loop and the harness-wiring audit were merged into one skill, because the
> border between them was measured and never closed. Changes are listed in the NOTICE file at the
> root of the plugin.

Two modes, one territory. Both answer "why is this skill not doing what I meant?" — one by looking
inside a skill, the other by looking at how skills resolve to each other.

| Mode | Question | Writes? | Detail |
|---|---|---|---|
| **A — Author** | What should this one skill say, and does it trigger? | Yes | `references/authoring.md` |
| **B — Audit** | Do the artefacts resolve to each other? | No | `references/harness-wiring-audit.md` |

## Before either mode

Read `learning.md` first, and `.claude/agent-memory/skill-improver/MEMORY.md` when the round will
reach Mode B Phase 5. Both are written at the *end* of a round and are worth nothing if the next
round does not open them — the inherited failure patterns exist to stop a mistake already
catalogued from being made again, and a pattern nobody loads prevents nothing.

`MEMORY.md` is also the one file Phase 5 orders pasted verbatim into the auditor's prompt. The
agent declares no `memory:` field, deliberately, because that would grant it `Write` and `Edit` on
top of its allowlist — so this paste is the only path by which accumulated patterns reach it.

## Which mode

**Mode A** when the subject is one artefact: creating a skill, restructuring a body, tuning a
description so it fires, writing the evals that prove a change helped. One name in the question.

**Mode B** when the subject is the link between artefacts: a subagent that is not found, a skill
that fires in the wrong situation because another one claims the same words, an orphan nobody
dispatches, a hook declared nowhere. Two or more names, or none — a question about the graph.

Ambiguous by design: *"my skill does not fire"* is Mode A when one description is weak, and Mode B
when two descriptions overlap. Start in A, and escalate to B the moment a second skill turns out to
claim the same territory. That border used to be two competing skills; merging them is what removed
the need to guess right on the first turn.

Not this skill: designing an agent's prompt — when the audit lands on an `agents/*.md` file rather
than a skill, hand it to `Skill("senior-prompt-engineer")`, which owns the file contract and the
handoff schema. Nor deciding which agents to run for a task (that is the always-in-force
`references/execution-floor.md`), nor reviewing production code (`/pr-review`,
`graph-powers:evaluator`).

## Hard rules

- **Mode B is report-only.** No patch is applied without the user's explicit approval in the turn.
  Writing is permitted in `.claude/audit/` freely — those are scan artefacts — and in `learning.md`
  and the auditor's memory file **only after approval**, carrying the record of the round and the
  failure pattern, never patch content.
- **A skill cannot restrict its own tools.** `allowed-tools` is an additive pre-approval grant, not
  a restrictive allowlist, so Mode B's report-only promise is behavioural. What *enforces* it is the
  paired agent `graph-powers:skill-improver`, which declares `disallowedTools: Write, Edit`. Say
  this plainly rather than implying a sandbox that does not exist.
- **`[HARD]`** Never `git commit` or `git push` on your own initiative.
- **`[HARD]`** A secret you find is never printed in the clear. Report `path:line` plus the kind,
  masked. A secret in the harness is P0 and ships in its own batch, before any other fix.
- An orphan is never deleted in the round that found it. Classify it `DOCUMENT` /
  `DIRECT_INVOCATION_OK` / `REMOVAL_CANDIDATE`; the last needs double evidence and the user's
  decision.

## Measured constraints

These are enforced by scripts in this repository, not by convention. Ignoring one fails a build or,
worse, passes while measuring nothing.

| Constraint | Value | Enforced by |
|---|---|---|
| `description` plus `when_to_use`, per entry | 1,536 characters | `.github/check_listing_budget.py` |
| Same, summed over every skill and command | a shared ceiling | same file — your entry spends everyone's headroom |
| SKILL.md body | 500 **non-empty** lines | `scripts/quick_validate.py` |
| `name` | must equal the directory name | `scripts/quick_validate.py`, and CI separately |

Three validator behaviours that look like style advice and are not:

- `name` must be **unquoted**. Quotes are captured as part of the value and fail the hyphen-case check.
- `description` must be a **quoted single-line scalar**. Written as a folded block scalar it is
  captured literally and rejected by the angle-bracket check; written as a literal block it passes
  while the length check silently measures only the first line.
- Keep `<`, `>`, `[` and `]` out of the description text. The bracket check is a substring test, so
  a description that legitimately quotes CLI syntax fails.

## Gates

No line enters this table without having been pasted into a shell and run verbatim, **plus one run
it must fail**. Writing the expected exit code beside a command is not the gate; running both
directions is. That rule was adopted once in the weak form and violated three more times in the same
table — see `learning.md`.

| Gate | Command | Expected exit | Mode |
|---|---|---|---|
| Frontmatter and body size | `python3 ${CLAUDE_PLUGIN_ROOT}/skills/skill-improve/scripts/quick_validate.py <skill-path>` | 0 | A, B |
| Listing budget | `python3 ${CLAUDE_PLUGIN_ROOT}/.github/check_listing_budget.py` | 0 | A |
| Trigger, **one invocation per case id** | the runner line below | 0 per case | A, B |
| Settings and config JSON | `python3 -c "import json;json.load(open('.claude/settings.json'))"` | 0 | B |
| Edges resolve | every edge resolves, or is marked `DANGLING` with a cause | — | B |

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/skill-improve/scripts/run_evals.py --skill-path <skill-path> --evals-path <skill-path>/evals/evals.json --response-file <captured-response>.txt --test-case <case-id> --threshold 1.0
```

Four things about that runner, each measured rather than assumed:

1. **Never run it without `--test-case`.** In default mode it flattens the assertions of every case
   against a single response, so `contains: X` on a positive case and `not_contains: X` on a
   negative one cancel out. The mathematical ceiling lands near 81%; a correct set of artefacts
   measured 75% with 4 critical failures. The gate is only honest per case.
2. **`--threshold 1.0` is required.** The exit code is only `pass_rate >= threshold`. An assertion's
   `critical` field does **not** enter the exit code — it is a severity label in the printed report.
   With a handful of assertions per case the 0.95 default already demands 100%; passing `1.0` makes
   that explicit instead of accidental.
3. **A typo in an assertion id fails silently as an empty run.** Unknown ids are filtered out, so a
   case whose ids are all misspelled yields zero assertions, a pass rate of 0.0 and exit 1 with an
   empty table — indistinguishable at a glance from a real failure.
4. **An assertion without a `check` key raises rather than fails.** So does a check written without
   a colon. Both surface as a traceback, not as a red row.

## Trigger calibration

This skill's own cases live in `evals/evals.json` — positives that must fire, negatives that must
route elsewhere. They are the calibration; do not restate them in prose here, or the two copies
drift and the prose wins by being read first.

## References

- `references/authoring.md` — Mode A in full: the seven steps, the description formula, the
  assertion-design rules
- `references/harness-wiring-audit.md` — Mode B in full: phases 0 to 6, the four silent resolvers,
  the independent-judgement dispatch
- `references/testing-skills.md` — RED-GREEN-REFACTOR and pressure scenarios, the source for
  discipline-enforcing skills
- `references/persuasion-principles.md` — when authority language is the mechanism rather than an
  anti-pattern
- `references/anthropic-best-practices-summary.md` — the condensed validation rubric
- `../../references/rubrics/skill-improver-rubric.md` — the D/W/L/E/S/C rubric the paired agent
  scores against
- `../../agents/skill-improver.md` — the judge for Mode B, read-only by declared field
- `learning.md` — round history and the inherited failure patterns
- `scripts/` — `init_skill.py` scaffolds, `package_skill.py` zips for distribution,
  `quick_validate.py` checks structure, `run_evals.py` grades assertions

## Configuration

Mode B reads `.graph-powers/config.json` at the start: `project.locale` for the report language,
`paths.rulesDir`, and any agent alias map. It writes only into `.claude/audit/`.
