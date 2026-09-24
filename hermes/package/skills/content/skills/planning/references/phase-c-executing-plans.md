> Hermes auxiliary: `content/` paths are `file_path` values relative to the registered-document parent. Apply the loaded graph-engineering mapping and host policy; this file is served without template expansion.

# Phase C — Execute

> Canonical execution engine for the planning chain. Adapters resolve the plan and invoke this
> phase; no independent execution skill or workflow is required.

## Entry contract

- Phase B is complete: `<plan dir>/PLAN.md` passed its required review and the user approved it.
- Tier is **L5+** for automatic transition. Explicit `/implement` admits an approved L4 plan;
  explicit Gauntlet admits an approved L3+ plan. L1-L2 never enter Phase C.
- Use the authorized current checkout and honor protected-branch hooks; never switch branches or
  infer a protected-branch opt-in from plan approval.
- With the current client's Jev evaluation enabled and the paid batch authorized, link the
  approved PLAN before this phase; Phase C stays the only implementation engine.
- When and only when successful validation passed `profile: gauntlet`, read `content/skills/planning/references/gauntlet-loop.md` and apply its delta; a missing profile is always default.

## Exit contract

Every task has evidence; risk/dependency waves have clean early reviews and the final Evaluator
covers the rest/integration. Gates pass. Default closes with `/verify quick`; Gauntlet with
`/verify loop <PLAN_FILE>`.
After PASS, `/evolve auto` requires its lifecycle trigger. Stop reviewed and unstaged; Git requires
action/scope approval, retaining valid same-scope session approval.

## Step 1 — Validate and lease

For `--dry-run`, validate without creating state:

```bash
python -X utf8 "content/skills/planning/scripts/sdd.py" validate <PLAN_FILE> --max-tasks <graphGuardrails.maxTasksPerPlan>
```

Exit `0` returns `tier`, `tasks`, `gates`, `writeLease`; invalid/legacy plans route to `/plan`,
never inferred. Validation checks IDs/fields/evidence, dependencies/reads/cycles, task cap, phase
gates and ownership. Overlap requires a sequential dependency.

Acquire before writing; use the hook session ID for lifecycle and dispatch:

```bash
python -X utf8 "content/skills/planning/scripts/sdd.py" acquire <PLAN_FILE> --max-tasks <graphGuardrails.maxTasksPerPlan> --session-id <SESSION_ID>
```

Gauntlet adds `--profile gauntlet` to validate/acquire/status and repeats Acceptance/Skill checks.
`STALE`, `REVISION_REQUIRED` or `UNREVIEWED` blocks acquisition (exit `4`): Phase B `review-bind`.
Default omits profile flags.

`.graph-powers/logs/leases/<id>.json`: session/run, plan, literal paths, expiry.
Only check/publication is serialized. Disjoint runs coexist; progress is plan-scoped.

G4 names/denies foreign live claims; other writes/reads stay free. TTL: 45 minutes.
Run `content/skills/planning/scripts/sdd.py heartbeat <PLAN_FILE> --session-id <SESSION_ID>` before waves and every 15 minutes;
after expiry reacquire/recheck inputs. Once verified, replace `heartbeat` with `release`.
Without `--session-id`, CLI uses the hook's chat ID, then the plan ID; legacy claims keep their owner.
`ALLOW_OFF_LEASE` stays. No worktree needed; leases cannot identify children, enforce shell writes
or serialize Git's index.

Dry-run reports validation/routing/dependencies/proposed lease without writes or dispatch;
conversation-only plans remain in the response until an approved non-dry run materializes them.

Before resume and each wave, read `content/skills/planning/references/loop-engineering.md § Context Reset Protocol` and
query the selected plan (read-only; approval and current evidence remain separate):

```bash
python -X utf8 "content/skills/planning/scripts/sdd.py" status <PLAN_FILE> --max-tasks <graphGuardrails.maxTasksPerPlan> --session-id <SESSION_ID>
```

Before skipping checked work, match checks/reviews to current package/tree, relevant staged,
unstaged/untracked files, config, dependencies and environment under
`content/references/shared/015-verification-gate.md`; HEAD alone is insufficient.
Reuse matching PASS without repeating suites/reviews for compaction; then dependencies are verified.
Changed/unknown inputs invalidate only affected evidence/dependents: retain work, record the gap,
obtain bounded proof before advancing. Checked `EVIDENCE: pending` fails validation; boxes are not proof.

## Step 2 — Rolling task loop

Only `state: ACTION_REQUIRED`, `nextAction.kind: TASK` admits a writer wave in `currentPhase`.
A pending GATE goes to Step 3; conflict/dependency blocks stop writers. Require verified `Needs`,
disjoint `Owns` and dependency payload. Group by declared writer role/compatible context into the
fewest useful lanes, up to `graphGuardrails.maxParallelWave`.

Reserve `graph-powers:evaluator` for final review before the first wave. Before every child call:

```bash
python -X utf8 "content/skills/planning/scripts/sdd.py" dispatch reserve <PLAN_FILE> --key <stable-key> --kind <kind> --role graph-powers:<agent> --max-spawns <graphGuardrails.maxSpawnsPerWorkflow> --session-id <SESSION_ID>
```

Kinds are bootstrap, writer, evaluator, correction and confirmation. Only fresh `status: RESERVED`
authorizes exactly one matching child call; `status: ALREADY_RESERVED` returns exit 0 as a resume
fact, never permission to launch. Reservations irrevocably consume attempts, even after a crash
before spawning. Reconcile missing/unknown child evidence; a retry needs a new stable key and slot.
`dispatches.json` and correction history survive resume, compaction and model/context changes under
the lease run ID. At `graphGuardrails.maxSpawnsPerWorkflow`, return `BLOCKED` with completed/deferred
IDs and evidence; never clear reservations. Only a later user-requested run may release/reacquire.

Cluster each package under a write-capable role from
`content/references/shared/030-agent-assignment-matrix.md` and
`content/skills/planning/references/execution/implementer-prompt.md`. Never invent/generalize a role or override its model:
Claude Code uses canonical frontmatter and Codex its semantic policy. Paste every task block; limit
writes to their `Owns` union. Re-dispatch one grouped correction only on changed evidence;
unresolved `BLOCKED` routes to `/debug recover`.

After focused checks, package tasks from `TASK_BASE`. Default: dispatch one fresh
`graph-powers:evaluator` via `content/skills/planning/references/execution/task-reviewer-prompt.md` only when a wave
touches `chain.riskSurfaces` or a dependency whose later consumers a defect would block. Give it
task blocks/packages/reports; retain verdict/snapshot. Other waves close on focused `CHECK` and
changed paths ⊆ `Owns`; final review covers them. Gauntlet's per-wave rule stays in
`content/skills/planning/references/gauntlet-loop.md`. Group corrections by writer role and disjoint `Owns`; at most one fresh
correction re-review covers only material delta via
`content/skills/planning/references/execution/correction-reviewer-prompt.md`. Never review per finding; cap
`${graphGuardrails.maxRepatch}` routes to `/debug recover`.

Close a task only when focused `CHECK` passes, changed paths ⊆ `Owns`, and, when the wave had an
early review, its verdict is clean. The controller replaces `EVIDENCE: pending` in `PLAN_FILE` with output
(and RED/GREEN/refactor proof if TDD), then checks the box. Keep exception reasons/checks;
implementers do not edit the plan. Append `task-reviews.md` rows: timestamp, task ID, snapshot,
early verdict or `final`, correction count, check output, failed/blocked attempts and distinct
hypotheses. Recovery owns findings/contract changes.

### Inline fallback

If the runtime has no Agent tool, review the plan critically and surface blocking concerns before
code, then execute tasks sequentially in the main thread. Keep the same briefs, TDD status, focused
checks, packages, evidence writes and stop conditions; self-review early-risk waves against the
reviewer prompt and note deferred final coverage. Report independent review as unavailable and
acceptance pending that required proof; author checks never count as independent review or full
acceptance. If the Agent tool
exists but a declared write-capable lane does not resolve, stop — do not silently replace it with a
general agent or the main thread.

## Step 3 — Phase gates

After all phase tasks close, run normalized `gates` in plan order: exact `CHECK`, successful exit
and matching `EXPECT`. The controller records deciding `EVIDENCE` and checks each box; every phase
gate must have non-pending proof before phase closure. Phase gates never replace focused task checks.
Then append the phase checkpoint to
`.graph-powers/logs/sdd/<plan-slug>/progress.md`: timestamp, canonical plan, phase, base `HEAD`, working-tree status,
closed gate IDs and the next runnable or blocked task.

Per `content/references/shared/010-quality-gates.md`, repository-wide type-check and
lint run once at each phase gate, never per task; serial full tests run once at the final boundary,
using the project's declared `${tooling.commands}`. A missing command is `NOT DECLARED`, never a
passing result.

## Step 4 — Final review and close

After gates, find the approved target branch/`HEAD` merge base; run
`content/skills/planning/scripts/sdd.py package <PLAN_FILE> <MERGE_BASE> HEAD`. Send package, plan, ledger and early verdicts/snapshots to a separate `graph-powers:evaluator`
using `content/skills/planning/references/execution/final-reviewer-prompt.md`. Reuse valid verdicts for matching scope/inputs;
review only their delta, uncovered tasks and integration. Resolve Critical/Important; report Minor
and deferred findings. Default then runs `/verify quick`,
conditionally `/evolve auto` on PASS when triggered, then `content/skills/planning/scripts/sdd.py release <PLAN_FILE> --session-id <SESSION_ID>`. Gauntlet follows
`content/skills/planning/references/gauntlet-loop.md § Final close` while the lease remains held. A failing final gate leaves the lease
and working-tree state explicit until resolution or a safe abort.

Early and final acceptance differ; reuse valid proof. At most one fresh correction re-review covers
material delta within caps. Stop when reviews, criteria and gates cover the snapshot and pass. Nits
are informational; no cosmetic review loop. Reopen only for changed inputs, material findings or
approved scope; invalidate affected proof.

## Required invariants

- Default: only risk/dependency waves get early review; others close on `CHECK`/`Owns` pending
  final review of uncovered tasks, integration and early-review deltas. Gauntlet keeps per-wave
  review; one fresh correction re-review at most covers material delta.
- Every dispatch names an existing Graph Powers role and counts toward
  `graphGuardrails.maxSpawnsPerWorkflow`; width and total are ceilings, never quotas.
- No task or phase gate is checked while `EVIDENCE` is pending.
- Tests go through the real production interface. Trivial functions need no direct test when their
  consumer-visible behaviour is covered.
- Type-check and lint run once at each phase gate; serial full tests run once at the final boundary.
- Do not stage, commit, push, publish, open a PR or merge.
