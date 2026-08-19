---
description: Post-implementation verification gate. Runs the gates the project declared, checks the safety floor, and returns a verdict with the command output that proves it. Use before claiming completion of L3+ work or before handing work to review.
workflow_type: augmented-llm
---

# /verify — Verification Gate

**ARGUMENTS**: $ARGUMENTS

> **Read first:** `${CLAUDE_PLUGIN_ROOT}/references/shared-context.md` — config loader, quality
> gates, complexity routing, agent matrix, spawn patterns. Every section this command cites by
> number lives there. Read it before step 0; do not reconstruct it from memory.

Modes: `/verify` (full) · `/verify quick` (gates only, no review checklist).

The single rule this command exists to enforce: **a gate is passing only if it ran in this session
and exited zero.** A remembered pass is not a pass.

---

## 0. Resolve what this project actually runs

Read the config (`shared-context.md § 0`). The gates are whatever `tooling.commands` declares —
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

---

## 4. Verdict

Return exactly one:

- `VERIFIED` — every declared gate ran and passed; no floor violation; checklist clean.
- `VERIFIED-WITH-NOTES` — gates pass, with non-blocking follow-ups listed.
- `NEEDS-WORK` — a gate failed, an invariant is violated, or something could not be verified.

`NEEDS-WORK` is also the verdict when a gate could not run. "I could not check this" and "this is
fine" are different answers, and collapsing them is the most expensive habit in this harness.

Include the exact commands run and their output summary. A verdict without evidence is an opinion.
