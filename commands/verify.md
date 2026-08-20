---
description: "Prove the work actually holds before it is handed off — runs the gates the project declared, checks the safety floor, and returns a verdict with the command output behind it. Use when the user asks whether this is done, to run the gates, to check nothing broke, or before claiming any L3+ task complete. Do not use to review a diff for quality (/pr-review) or to chase a gate that is already failing (/debug)."
workflow_type: augmented-llm
---

# /verify — Verification Gate

**ARGUMENTS**: $ARGUMENTS

> **Read before step 0 — never reconstruct these from memory:** `${CLAUDE_PLUGIN_ROOT}/references/shared/000-config-loader.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/005-superpowers-bootstrap.md`
> Read `${CLAUDE_PLUGIN_ROOT}/references/shared/060-skill-domain-matrix.md`

Modes: `/verify` (full) · `/verify quick` (gates only, no review checklist).

The single rule this command exists to enforce: **a gate is passing only if it ran in this session
and exited zero.** A remembered pass is not a pass.

---

## 0. Resolve what this project actually runs

Read the config (`${CLAUDE_PLUGIN_ROOT}/references/shared/000-config-loader.md`). The gates are whatever `tooling.commands` declares —
nothing is assumed:

| Gate | Command | When it is skipped |
|---|---|---|
| Type check | `${tooling.commands.typeCheck}` | field absent |
| Lint | `${tooling.commands.lint}` | field absent |
| Test | `${tooling.commands.test}` | field absent, or `tooling.testRunner` is `null` |
| Build | `${tooling.commands.build}` | field absent |

**A gate with no declared command is reported as `NOT DECLARED`, never as passing.** A missing
script that exits non-zero as "script not found" reads exactly like a real failure, and a gate
nobody declared reads exactly like a gate nobody needed. Say which one it was.

**Then read `${rulesDir}/verify-supplements.md`, if the project has one, and run what it declares
as well.** The four rows above are the shape a typical application has; they are not the shape every
repository has. A project whose real gate set is a manifest validator, a portability scan and a
schema check has nowhere to put any of it — `tooling.commands` accepts seven named keys and those
are not among them — so without this file `/verify` reports one green gate out of thirteen and the
line reads as full coverage.

The file is a table: gate name, exact command, and one line on what a failure means. Run each in
order, capture the exit code, and report them in the same table as the declared gates, marked as
coming from the supplement. A supplement command that fails is a gate failure like any other. When
the project has no such file, say so in one line — for most projects the four rows are the whole
story, and their absence is a fact, not a gap.

Load the domain skill for what changed — `Skill("debugger")` when chasing a failure,
`Skill("performance-optimization")` when performance, security or SEO surfaces moved,
`Skill("astro")` when `project.stack` names Astro.

---

## 1. Run the gates

Run each declared command, in the order above, and capture the exit code and the last meaningful
line of output. Stop at the first failure unless `$ARGUMENTS` says `--all`.

Report as a table: gate, command, exit code, evidence.

---

## 2. Safety floor check

From `${CLAUDE_PLUGIN_ROOT}/references/safety-floor.md`:

- **§1** — nothing was committed, pushed or merged during the work. `git status --short` and
  `git log --oneline -1` prove it.
- **§3** — no migration, destructive SQL or irreversible operation ran without approval.
- **§4** — no secret entered a tracked file. `git diff --cached` and the diff of the touched files
  are the evidence, not a recollection.
- **§5** — the commands that ran are the ones the project declared.
- **§6** — no file outside the task's scope changed. A file the user had dirty before the work
  started is called out, not quietly included.

---

## 3. Review checklist (skipped in `quick` mode)

- Work happened on `${git.workBranch}`, or the deviation is stated.
- No dependency added without approval.
- No file in `protectedFiles` changed.
- Every acceptance criterion of the originating task has a line here saying how it was checked.
- Every blocking finding in the project's root `REVIEW.md` was checked, by its ID. That table is
  the project's own scar tissue; skipping it makes this gate generic.
- Project-specific invariants from `${rulesDir}/` that match the touched paths were honoured. When
  the project declares none, say that — it is a finding about the project, not a pass.

When the work came from a plan file, three of its sections are checked here — they exist for this
moment, and a plan that produces them for nobody to read is wasted work:

- **`## Regression watchlist`** — walk every row. Each one names existing behaviour this change was
  not supposed to touch, and how to prove it still works. Run the proof. A row with no proof
  command is itself the finding.
- **`## Reuse ledger`** — for every `REUSE` and `EXTEND` row, confirm the diff calls the asset the
  ledger named instead of a second implementation of it. A rediscovered "new service" beside a
  ledger row saying to reuse one is the most expensive drift this chain has, and it is invisible in
  a diff read on its own.
- **`## Rollback`** — present and specific enough to execute. This is checked whatever the verdict:
  it matters most exactly when everything else failed.

Then the plan's own ledger, if it carries task checkboxes: **a checked box whose `EVIDENCE:` line
still reads `pending` is unmet.** The box is a claim and the evidence is the proof; checked without
evidence counts as worse than unchecked, not better. An `ABANDON: <id> <reason>` line resolves a
task honestly, and every one of them is listed in the report.

No plan file, or the plan has none of these: say so in one line and continue. Their absence is a
fact about the plan, not a gate failure.

### What a finding may and may not become

Review here is adversarial on purpose, and that is exactly why its mandate is bounded. A finding
becomes **work** only when it is a defect this change introduced, a regression of a
`## Regression watchlist` row, or something that makes the plan's `## Destination` false.

Everything else — a pre-existing issue the diff did not touch, a refactor you would prefer, a
hardening idea, anything matching a `## Out of scope` row — is reported under the verdict's notes
and **does not reopen the work**. It is useful; it is not this change's job.

Two rules follow, and they are what keep an adversarial pass from becoming an unbounded one:

- **Never design past the request.** No new feature, no new file, no new abstraction, no redesign.
  The question is "does what was built hold?", never "what else could be built".
- **The same finding twice is a decision, not a third attempt.** A finding that survives its fix
  goes to the user with what was tried. Re-patching the same item past
  `graphGuardrails.maxRepatch` is how a review turns into a loop with no floor.

---

## 4. Verdict

Return exactly one:

- `VERIFIED` — every declared gate ran and passed; no floor violation; checklist clean.
- `VERIFIED-WITH-NOTES` — gates pass, with non-blocking follow-ups listed.
- `NEEDS-WORK` — a gate failed, an invariant is violated, or something could not be verified.

`NEEDS-WORK` is also the verdict when a gate could not run. "I could not check this" and "this is
fine" are different answers, and collapsing them is the most expensive habit in this harness.

Include the exact commands run and their output summary. A verdict without evidence is an opinion.
