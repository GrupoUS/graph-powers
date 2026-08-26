# Phase C — Execute

> Canonical execution engine for the planning chain. `/implement` resolves the plan and invokes
> this phase; no independent execution skill or workflow is required.

## Entry contract

- Phase B is complete: `<plan dir>/PLAN.md` passed its required review and the user approved it.
- Tier is **L5+** (at L4, the approved plan is the deliverable until the user invokes `/implement`).
- The current branch is `${git.workBranch}` and is not protected.

## Exit contract

Every task has implementation, one task review and evidence; every phase gate is met; the final
declared gates and `/verify quick` pass; `/evolve auto` is run. Stop with reviewed, unstaged
working-tree changes. Stage, commit, push, PR and merge require separate current-turn approval.

## Step 1 — Validate and lease

Before creating a workspace or dispatching a writer, run the moved SDD tool:

```bash
python -X utf8 "${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/sdd.py" validate <PLAN_FILE> --max-tasks <graphGuardrails.maxTasksPerPlan>
```

The command returns exit `0` only for a structured plan and emits normalized JSON with `tasks`,
phase `gates` and `writeLease`; invalid plans return exit `2`. A legacy unstructured plan is rejected
and routed to `/plan`, never inferred. The validator checks unique IDs, task and gate fields,
checked-box evidence, existing dependencies, the `reads` payload, acyclic dependencies, task count,
phase-gate coverage and `Owns` conflicts. File overlap is valid only when a dependency makes the
tasks sequential.

Use the JSON `writeLease` to create `.graph-powers/logs/write-lease.json` scoped to this plan before
the first writer. Add the canonical repository-relative `PLAN_FILE` to `paths`, because the
controller — never an implementer — persists each reviewed task's evidence there. The exact object
is `{ "plan": "<canonical PLAN_FILE>", "paths": [<writeLease plus PLAN_FILE>] }`. If the file
contains a lease for another canonical plan, stop and report the conflict; never merge or overwrite
it. Create the workspace only after validation and lease acquisition. On normal finish or abort,
remove only the lease whose `plan` exactly matches the current canonical plan.

`--dry-run` performs validation and displays routing, dependencies and the lease that would be
created, but does not create a workspace, write a lease or dispatch an agent.

On resume, skip only tasks whose validator object has `checked: true` and non-pending evidence.
Their dependencies count as verified. Validation rejects a checked task that still says
`EVIDENCE: pending`; do not infer completion from a checkbox alone.

## Step 2 — Rolling task loop

Dispatch every task whose `Needs` are verified and whose `Owns` paths collide with nothing in
flight, up to `graphGuardrails.maxParallelWave`. Review each result immediately, then release the
paths and dispatch newly unblocked work. A task with no dependency payload cannot be treated as
independent.

For each task use one fresh implementer from `references/execution/implementer-prompt.md`, with the
task block pasted verbatim. The worker follows the task's TDD status and does not write outside
`Owns`. Handle its status explicitly: `PASS` continues to the focused check and review; `FAIL`
re-dispatches only that task with the report and failed evidence, counting against
`${graphGuardrails.maxRepatch}`; `BLOCKED` receives missing factual context once, otherwise stops and
routes to `/debug recover`. Never retry unchanged.

After a PASS and green focused check, run `sdd.py package <PLAN_FILE> <TASK_BASE> HEAD` and give the
resulting review package, task block and implementer report to one fresh read-only reviewer using
`references/execution/task-reviewer-prompt.md`. It returns two verdicts in one review: compliance
first, then quality/KISS. Preserve the package's printed working-tree snapshot as the next
`TASK_BASE` and, when correction is required, as `FIX_BASE`. Package each correction as
`FIX_BASE..HEAD` for `references/execution/correction-reviewer-prompt.md`. Correction count is
limited only by `${graphGuardrails.maxRepatch}`; exhaustion routes to `/debug recover`.

Close a task only when the focused `CHECK` passes, changed paths are a subset of `Owns`, and the
reviewer is clean. The controller then replaces `EVIDENCE: pending` in `PLAN_FILE` with the deciding
output (plus RED/GREEN/refactor evidence when TDD is required) and checks the task box. For either
explicit exception status, retain its reason and run the applicable focused check. Implementers do
not edit the plan.

### Inline fallback

If the runtime has no Agent tool, review the plan critically and surface blocking concerns before
code, then execute tasks sequentially in the main thread. Keep the same briefs, TDD status, focused
checks, packages, evidence writes and stop conditions; self-review each task against both verdicts
in the task-reviewer prompt and report that independent review was unavailable. If the Agent tool
exists but a declared write-capable lane does not resolve, stop — do not silently replace it with a
general agent or the main thread.

## Step 3 — Phase gates

When all tasks in a phase are closed, execute that phase's normalized `gates` in plan order. For
each gate, run its exact `CHECK`, require both a successful exit and its `EXPECT`, then have the
controller replace `EVIDENCE: pending` with the deciding output and check the gate box. Do not close
the phase until every gate for it is checked with non-pending evidence. Focused task checks run per
task and are not replaced by the phase gate.

Per `${CLAUDE_PLUGIN_ROOT}/references/shared/010-quality-gates.md`, repository-wide type-check and
lint run once at each phase gate, never per task; serial full tests run once at the final boundary,
using the project's declared `${tooling.commands}`. A missing command is `NOT DECLARED`, never a
passing result.

## Step 4 — Final review and close

After all phase gates, resolve the merge base between the approved target branch and `HEAD`, then
run `sdd.py package <PLAN_FILE> <MERGE_BASE> HEAD`. Give that complete review package, the plan and
task-review ledger to the separate read-only reviewer in
`references/execution/final-reviewer-prompt.md`. Resolve Critical and Important findings; report
Minor findings and triage deferred or parked items. Then run `/verify quick`, followed by
`/evolve auto` on PASS. Remove only this plan's lease whether execution finishes successfully or
aborts. If a final gate fails, leave the lease and working-tree state explicit until the failure is
resolved or the plan is safely aborted.

## Required invariants

- One reviewer per task; the final reviewer is a separate role.
- No task or phase gate is checked while `EVIDENCE` is pending.
- Tests go through the real production interface. Trivial functions need no direct test when their
  consumer-visible behaviour is covered.
- Type-check and lint run once at each phase gate; serial full tests run once at the final boundary.
- Do not stage, commit, push, publish, open a PR or merge.
