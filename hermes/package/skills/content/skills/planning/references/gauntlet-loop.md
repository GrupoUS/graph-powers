> Hermes auxiliary: `content/` paths are `file_path` values relative to the registered-document parent. Apply the loaded graph-engineering mapping and host policy; this file is served without template expansion.

# Gauntlet execution profile

> Explicit, bounded delta over `content/skills/planning/references/phase-c-executing-plans.md`. Phase C remains the engine and its
> implementer, task-reviewer, correction-reviewer and final-reviewer prompts remain canonical.
> Never copy those contracts here or infer this profile from a request for quality or assurance.

## Activation and goal

Only explicit `/gauntlet` may pass `profile: gauntlet`, after validation returns an eligible tier.
Objectives use Step 0 → Phase A Step 2's grill/confirmation → Phase B and its required L3+ plan review.
A direct approved-plan invocation covers Phase C for that plan; objectives cover only stated scope
and approved transitions. New decisions/authority/scope pause. Neither authorizes another plan, Git
or outward actions. A missing, invalid or out-of-worktree supplied path stops at `/plan`, never
becomes an objective. L1-L2 is `NOT ELIGIBLE FOR GAUNTLET`; `/implement` retains its default profile
and `/verify quick`. `--review-only` stops after independent plan review/bind, before execution.

The controller owns the loop. Its stable unit is:

```text
Task ID + Owns + Acceptance + CHECK/EXPECT + open finding IDs
```

A runtime may resume a process, but correction belongs to that logical lane. Re-dispatching the
lane with explicit state is equivalent; persistent subagent identity is never required.

## Entry and dry-run

**Before validating a supplied plan**, inspect unresolved `TBD`, `[ASSUMED]`, and missing or
payload-empty `Needs`. `Needs: none` and open-task `EVIDENCE: pending` are valid, not holes. A ready
approved plan reuses settled decisions with no new grill or confirmation. For holes, reopen only
those decisions and affected dependents through Phase A Step 2; confirm the repaired understanding,
then Phase B repairs the plan and obtains a new Mode 1 verdict/`review-bind` for its changed bytes.
Run `validate` and `review-check` before admission; any further edit, including a validation repair,
invalidates the bind. Dry-run describes holes without live questions or effects; review-only reports
holes and stops before repair. Other invalid grammar still returns to `/plan`.

Phase C's validator owns grammar/lease: eligible `tier`, unique IDs, non-empty `Owns`, payload-bearing
`Needs`, observable acceptance, decisive `CHECK`/`EXPECT`, `EVIDENCE`, valid TDD and routable
writer/skill (or `none`). Before lease/writer, require a current independent evaluator Mode 1 review
under § Review binding. It checks applicable database, API and client coverage from the Gauntlet
matrix or approved legacy task/connection evidence. Missing/invalidated coverage or review returns
to Phase B; reuse matching evidence and do not rewrite a green spec merely to add headings.

For a plan `--dry-run`, validate read-only, then derive and display tier, task count, `Owns`, `Needs`,
ready waves, writer and reviewer routes, every applicable cap and the final `/verify loop <PLAN_FILE>`.
For an objective dry-run, describe Step 0 → Phase A frontier rounds/recommendations → explicit
shared-understanding confirmation → Phase B → evaluator → approval → Phase C → verify, and artifact
boundaries. Both forms name distinct `builder` (plan dispatch matrix, or the objective's task role
from `content/references/shared/030-agent-assignment-matrix.md`) and `inspector`
(default `graph-powers:evaluator`). No live questions, bind, lease, workspace, writes or spawns;
objective dry-run also forbids investigation, plan materialization/validation and checks.
Reject unknown flags.

## Scheduler

- L3 uses exactly one sequential builder lane and one Evaluator review per completed wave. This is the explicit Gauntlet exception that
  allows an approved structured L3 plan; ordinary L3 still uses Planning's inline path.
- L4+ may fill a wave only with ready tasks whose `Owns` are pairwise disjoint. Cluster tasks owned
  by the same existing Graph Powers writer role into the fewest useful lane packages, bounded by
  `${graphGuardrails.maxParallelWave}`. Release paths only after the wave Evaluator closes the task.
- One writer per file: parallel lanes never share an `Owns` path. Shared schema, migrations, global
  styles, singletons, lockfiles, generated clients or one browser session force serialization;
  directory boundaries do not prove independence.
- A task in correction does not block independent lanes unless its paths or promised interface are
  their dependency. Mixed results preserve PASS diffs and re-dispatch only the failed lane.
- Builders and critics MUST NOT dispatch children. The controller counts all dispatches against
  cumulative `${graphGuardrails.maxSpawnsPerWorkflow}`, direct `${graphGuardrails.maxSpawnsPerSession}`
  and specialist `${graphGuardrails.maxRoundsPerAgent}`, reserving the final Evaluator before a wave.
- Every dispatch names a role from the Graph Powers assignment matrix. Native Claude spawns inherit
  that role's frontmatter model; generated Codex roles use the semantic Codex model policy. Never
  invent an agent name, use a generic runtime agent or override the role's model at the call site.

Consultations are a separate parent-owned operation. Tag the critic/reviewer cycle `review` and the
parent-mediated operation `consult`; critic and reviewer passes neither reserve nor consume a
consultation key, and resuming Gauntlet never resets consultation state. Only the controller may
submit the canonical envelope to `content/skills/planning/scripts/sdd.py consult reserve|record`. Builders, critics and evaluators
cannot request or spawn a consultation. A duplicate key reuses its recorded result; a capped key is
`USER_REQUIRED`, and unresolved capability or unavailable fallback is `BLOCKED` without spawn or
retry. Persistent uncertainty returns to the user.

Capability metadata is declared by the parent and never live-probed. Native Fable/advisor is allowed
only on positive `SUPPORTED`; `UNSUPPORTED`/`UNKNOWN` explicitly falls back to the existing
read-only evaluator without emitting the native backend. Keep this state in the existing SDD
workspace ledger and preserve it across critic, correction and resume cycles.

Phase C's inline self-review fallback is disabled for this profile. If an independent critic cannot
be dispatched, stop `BLOCKED`, preserve the lease and report the unavailable review boundary; a
builder may never serve as its own Gauntlet critic.

## Review binding

`content/skills/planning/scripts/sdd.py review-bind` ties the Mode 1 verdict to the SHA-256 of the plan bytes: in the plan's SDD
workspace, `<plan-slug>/plan-review.json` keeps the last round and the append-only
`<plan-slug>/PLAN-REVIEW-LOG.md` takes one line per round, with the requested model beside the
observed one — a fallback is recorded, never silent. Both paths are in
`content/references/shared/007-path-conventions.md`. The `inspector` id defaults to `graph-powers:evaluator`
and is never the `builder` id or `main`; `codex:codex-rescue` inspects only on an explicit host
request in that turn, which the bind records.

`review-check` writes nothing: it reads the raw bytes and gates the first `acquire`, where `0`
authorizes the lease and `4` sends the plan back to Phase B for a new round, with no lease. A resume
of this plan's own lease compares the plan without the structured task and gate `EVIDENCE:` fields
and with their checkboxes normalized, so Phase C's own evidence writes are not drift; any other
change is `STALE`.

## One wave cycle

```text
grouped builder lane attempts (parallel only when Owns are disjoint)
  → controller focused CHECK per task
    → one fresh read-only graph-powers:evaluator for the whole wave
      → PASS per task + integration PASS: close those tasks
      → FAIL: grouped correction packets to the owning logical lanes
        → controller focused CHECK per corrected task
          → one fresh Evaluator for the correction wave
            → PASS: close corrected tasks
            → FAIL: next bounded attempt or stop at cap
      → BLOCKED: supply missing factual context once, otherwise stop
```

Each builder receives only the related task blocks in its lane package, their disjoint `Owns`,
required dependency payloads, open finding IDs and failed evidence — never the full plan or another
lane's task. Builder `PASS` is a claim. The controller
runs the exact focused `CHECK` first and requires both successful exit and `EXPECT`; a failed check
returns directly to the lane without spending an Evaluator dispatch. Green checks produce Phase C's
review packages for one fresh read-only Evaluator, which treats every builder report as unverified.

Every correction packet contains:

```text
Task ID:                 Attempt:
Owns:                    Open finding IDs:
Failed criterion IDs:    Observed evidence:
Expected evidence:       Previous hypothesis:
Required changed hypothesis:
Do not touch:            Focused CHECK:
Remaining attempt budget:
```

An attempt must change the hypothesis, patch or evidence; never retry unchanged. A correction may
touch only the lane's `Owns` and may not reopen unrelated code.

## Critic contract

The existing wave Evaluator still decides compliance first and quality/KISS second per task, then
integration. Under this profile both the initial wave review and the one correction re-review normalize their evidence-backed
return as:

```text
Task:
Overall verdict: PASS | FAIL | BLOCKED
Compliance: PASS | FAIL
Quality: PASS | FAIL
Criterion matrix:
- Criterion ID:          Verdict: PASS | FAIL | BLOCKED
  Evidence:              Confidence: 1-5
Findings:
- Finding ID:            Severity: Critical | Important | Minor
  Criterion ID:          Expected:              Actual:
  Reproduction or inspection:
  Evidence: path:line | command output | screenshot/probe
  Smallest valid correction:                    Confidence: 1-5
Checked clean:
- surface:               evidence:
Recommendation: close task | correct findings | route to debug recover
```

Correction reviews preserve prior finding IDs, mark each one resolved or still open, and assign an
ID plus the same matrix fields to any new regression. The critic is read-only and must not stage,
commit, spawn, widen scope or re-evaluate unrelated
files except a regression directly caused by the diff. Preference, “looks bad”, “not impressive”
or any finding without a criterion and reproducible evidence is non-blocking. Send only actionable
findings and evidence to the builder, never private reasoning.

Close a task only when its focused check and `EXPECT` pass, every changed path is inside `Owns`,
its compliance and quality pass, the wave integration verdict passes, no Critical or Important finding remains, and deciding evidence is
written to the existing plan plus `task-reviews.md`. Failed and blocked attempts remain in that
ledger; no second state machine or ledger is created.

## Caps and non-convergence

Use only configured limits: `${graphGuardrails.maxRepatch}` per failing item,
`${graphGuardrails.maxRoundsPerAgent}` per specialist, `${graphGuardrails.maxSpawnsPerWorkflow}` per
workflow invocation, `${graphGuardrails.maxSpawnsPerSession}` for direct calls,
`${graphGuardrails.maxParallelWave}` in flight, `${graphGuardrails.maxTasksPerPlan}` at
validation and `${chain.maxFixRounds}` for final verification. Never raise, reset or replace one
with a literal.

At any cap: stop the affected loop, persist attempts, hypotheses and evidence, return `NEEDS-WORK`
or `BLOCKED`, and route persistent failure to `/debug recover`. A capped run is unfinished — never
success — and receives no blind extra attempt.

## Optional visual A/B

This branch is available only for a visual task with a real stable permitted reference, declared
viewport and state, and deterministic capture. Otherwise record `NOT AVAILABLE`; never fabricate a
reference, screenshot or result.

When available, use `graph-powers:verification` with `webapp-testing` and `agent-browser`; do not
introduce Playwright. Capture candidate and reference with the same viewport, state, data and
conditions, hide revealing labels, judge both `A/B` and `B/A`, and require consistent results. A
position-dependent result goes to an objective rubric or a human decision, never the convenient
order. A/B is complementary evidence: acceptance, behavior, accessibility, console/network errors,
declared performance and project gates remain authoritative.

## Final close

The final inspection is a fresh evaluator, distinct from every builder of the run; a controller edit
to the plan after it invalidates that inspection and requires a new one.
After Phase C's separate final reviewer resolves Critical and Important findings, keep the lease
and run `/verify loop <PLAN_FILE>`. Its documented fallback in `content/commands/verify.md § 1.6` runs once when the
workflow tool is absent, the name does not resolve or the workflow declines; it still requires a fresh
independent Evaluator and permits correction only through declared `chain.maxFixRounds`. Record the
degradation and never retry resolution. Merge workflow `blocked` and `capped` into the verdict: either
prevents success and is handled before evolve or release.

On complete PASS, run `/evolve auto`, then release only this plan's lease and stop at reviewed,
unstaged changes. On `NEEDS-WORK` or `BLOCKED`, leave the lease and state explicit until the failure
is resolved or the controller declares a safe abort; a safe abort may then use Phase C's matching
release rule. Never stage, commit, push, open a PR, merge, release, publish or deploy without the
separate approval required for that action in the current turn.
