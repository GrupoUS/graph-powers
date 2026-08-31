# Phase C — Execute

> Canonical execution engine for the planning chain. Adapters resolve the plan and invoke this
> phase; no independent execution skill or workflow is required.

## Entry contract

- Phase B is complete: `<plan dir>/PLAN.md` passed its required review and the user approved it.
- Tier is **L5+** for automatic transition. Explicit `/implement` admits an approved L4 plan;
  explicit Gauntlet admits an approved L3+ plan. L1-L2 never enter Phase C.
- The current branch is `${git.workBranch}` and is not protected.
- When and only when successful validation passed `profile: gauntlet`, read `references/gauntlet-loop.md` and apply its delta; a missing profile is always default.

## Exit contract

Every task has implementation, one task review and evidence, and every phase gate is met. Default
execution closes with `/verify quick`; Gauntlet uses its profile's `/verify loop <PLAN_FILE>` close. Both run
`/evolve auto` only after PASS and stop reviewed and unstaged. Git actions need separate approval.

## Step 1 — Validate and lease

For `--dry-run`, validate without creating state:

```bash
python -X utf8 "${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/sdd.py" validate <PLAN_FILE> --max-tasks <graphGuardrails.maxTasksPerPlan>
```

The command returns exit `0` only for a structured plan and emits normalized JSON with `tier`,
`tasks`, phase `gates` and `writeLease`; invalid plans return exit `2`. A legacy plan is rejected
and routed to `/plan`, never inferred. The validator checks unique IDs, task and gate fields,
checked-box evidence, existing dependencies, the `reads` payload, acyclic dependencies, task count,
phase-gate coverage and `Owns` conflicts. File overlap is valid only when a dependency makes the
tasks sequential.

For a real run, atomically validate and acquire the plan-scoped lease before the first writer:

```bash
python -X utf8 "${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/sdd.py" acquire <PLAN_FILE> --max-tasks <graphGuardrails.maxTasksPerPlan>
```

The default profile omits a profile flag. Gauntlet appends `--profile gauntlet` to both `validate`
and `acquire`, so its Acceptance and bundled-Skill admission checks are repeated before lease.

`acquire` creates `.graph-powers/logs/write-lease.json` with create-if-absent semantics. Its `paths`
are the validated `writeLease`, canonical repository-relative `PLAN_FILE`, the phase progress ledger
and this plan's task-review ledger. A concurrent controller can observe the same empty state, but
only one atomic create wins; an existing lease for another plan is a conflict and is never merged or
overwritten. Create the workspace only after acquisition.

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
not edit the plan. Append one row to the plan workspace's `task-reviews.md`: timestamp, task ID,
package snapshot, reviewer verdict, correction count and deciding check output. Failed and blocked
attempts get rows too, so resumption does not erase why a task was retried or stopped.

### Parent-mediated consultation

The controller is the only consultation requester and owns the stable `taskId`, validated
`decisionKey`, reservation, deduplication, cap and resume state. Before any consultation, tag the
operation `consult` and use the canonical request/result envelope and `sdd.py consult reserve`; tag
ordinary task, correction and final evaluator calls `review`. Review calls are separate from
consultations, do not consume the consultation budget, and must not reset its ledger on resume.
Workers cannot spawn children; evaluators, reviewers and critics are read-only and cannot request a
consultation. A duplicate decision key returns its recorded result, a capped request returns
`USER_REQUIRED`, and unresolved capability or unavailable fallback returns `BLOCKED` without a spawn
or retry; persistent uncertainty is returned to the user.

Capability status is supplied by the parent and is not live-probed. Native Fable/advisor is selected
only after positive `SUPPORTED` metadata. `UNSUPPORTED` or `UNKNOWN` selects the existing read-only
evaluator as an explicit fallback without emitting the native backend. Record a result only through
the same ledger with `sdd.py consult record`; the atomic, symlink-safe state lives in this plan's
existing SDD workspace.

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
task and are not replaced by the phase gate. Then append the phase checkpoint to
`.graph-powers/logs/progress.md`: timestamp, canonical plan, phase, base `HEAD`, working-tree status,
closed gate IDs and the next runnable or blocked task.

Per `${CLAUDE_PLUGIN_ROOT}/references/shared/010-quality-gates.md`, repository-wide type-check and
lint run once at each phase gate, never per task; serial full tests run once at the final boundary,
using the project's declared `${tooling.commands}`. A missing command is `NOT DECLARED`, never a
passing result.

## Step 4 — Final review and close

After all phase gates, resolve the merge base between the approved target branch and `HEAD`, then
run `sdd.py package <PLAN_FILE> <MERGE_BASE> HEAD`. Give that complete review package, the plan and
task-review ledger to the separate read-only reviewer in
`references/execution/final-reviewer-prompt.md`. Resolve Critical and Important findings; report
Minor findings and triage deferred or parked items. The default profile then runs `/verify quick`,
`/evolve auto` on PASS and `sdd.py release <PLAN_FILE>`. The Gauntlet profile instead follows
`gauntlet-loop.md § Final close` while the lease remains held. A failing final gate leaves the lease
and working-tree state explicit until resolution or a safe abort.

## Required invariants

- One reviewer per task; the final reviewer is a separate role.
- No task or phase gate is checked while `EVIDENCE` is pending.
- Tests go through the real production interface. Trivial functions need no direct test when their
  consumer-visible behaviour is covered.
- Type-check and lint run once at each phase gate; serial full tests run once at the final boundary.
- Do not stage, commit, push, publish, open a PR or merge.
