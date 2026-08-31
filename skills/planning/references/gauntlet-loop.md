# Gauntlet execution profile

> Explicit, bounded delta over `phase-c-executing-plans.md`. Phase C remains the engine and its
> implementer, task-reviewer, correction-reviewer and final-reviewer prompts remain canonical.
> Never copy those contracts here or infer this profile from a request for quality or assurance.

## Activation and goal

Only `/gauntlet <approved-plan-file-or-directory> [--dry-run]` may pass `profile: gauntlet`, and
only after `sdd.py validate --profile gauntlet` returns a normalized eligible tier. The explicit non-dry invocation is
current-turn approval for exactly that canonical plan; it authorizes neither another plan nor a Git
or outward-facing action. Never infer a plan: a missing path, invalid plan or tier routes to `/plan`
before this file is loaded. L1-L2 returns `NOT ELIGIBLE FOR GAUNTLET` and follows the normal route. `/implement`
always keeps Phase C's default profile and `/verify quick` close.

The controller owns the loop. Its stable unit is:

```text
Task ID + Owns + Acceptance + CHECK/EXPECT + open finding IDs
```

A runtime may resume a process, but correction belongs to that logical lane. Re-dispatching the
lane with explicit state is equivalent; persistent subagent identity is never required.

## Entry and dry-run

The normalized plan must provide `tier`, unique task IDs, non-empty `Owns`, payload-bearing `Needs`,
observable acceptance, decisive `CHECK`/`EXPECT`, an `EVIDENCE` field, valid TDD status and a
routable writer and bundled skill (or `none`). `EVIDENCE: pending` is correct for an open task; Phase C replaces it only when the
task closes. Phase C's validator remains the authority for the complete grammar and lease.

For `--dry-run`, derive and display tier, task count, `Owns`, `Needs`, ready waves, writer and
reviewer routes, every applicable cap and the final `/verify loop <PLAN_FILE>`. Do not acquire a lease, create a
workspace, write any file or dispatch any agent. Reject unknown flags rather than ignoring them.

## Scheduler

- L3 uses exactly one sequential builder/critic lane. This is the explicit Gauntlet exception that
  allows an approved structured L3 plan; ordinary L3 still uses Planning's inline path.
- L4+ may fill a wave only with ready tasks whose `Owns` are pairwise disjoint, bounded by
  `${graphGuardrails.maxParallelWave}`. Release a lane's paths only after that task closes.
- One writer per file: parallel lanes never share an `Owns` path. Shared schema, migrations, global
  styles, singletons, lockfiles, generated clients or one browser session force serialization;
  directory boundaries do not prove independence.
- A task in correction does not block independent lanes unless its paths or promised interface are
  their dependency. Mixed results preserve PASS diffs and re-dispatch only the failed lane.
- Builders and critics MUST NOT dispatch children. The controller counts all dispatches against
  `${graphGuardrails.maxSpawnsPerSession}` and specialist rounds against
  `${graphGuardrails.maxRoundsPerAgent}`.

Consultations are a separate parent-owned operation. Tag the critic/reviewer cycle `review` and the
parent-mediated operation `consult`; critic and reviewer passes neither reserve nor consume a
consultation key, and resuming Gauntlet never resets consultation state. Only the controller may
submit the canonical envelope to `sdd.py consult reserve|record`. Builders, critics and evaluators
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

## One lane cycle

```text
builder attempt
  → controller focused CHECK
    → fresh read-only critic
      → PASS: close task
      → FAIL: correction packet to the same logical lane
        → controller focused CHECK
          → fresh correction reviewer
            → PASS: close task
            → FAIL: next bounded attempt
      → BLOCKED: supply missing factual context once, otherwise stop
```

The builder receives only its task block, `Owns`, required dependency payloads, open finding IDs and
failed evidence — never the full plan or another task. Builder `PASS` is a claim. The controller
runs the exact focused `CHECK` first and requires both successful exit and `EXPECT`; a failed check
returns directly to the lane without spending a critic dispatch. A green check produces Phase C's
review package for one fresh read-only critic, which treats the builder report as unverified.

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

The existing task reviewer still decides compliance first and quality/KISS second. Under this
profile both the initial task critic and every correction critic normalize their evidence-backed
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

Correction critics preserve prior finding IDs, mark each one resolved or still open, and assign an
ID plus the same matrix fields to any new regression. The critic is read-only and must not stage,
commit, spawn, widen scope or re-evaluate unrelated
files except a regression directly caused by the diff. Preference, “looks bad”, “not impressive”
or any finding without a criterion and reproducible evidence is non-blocking. Send only actionable
findings and evidence to the builder, never private reasoning.

Close a task only when its focused check and `EXPECT` pass, every changed path is inside `Owns`,
compliance and quality pass, no Critical or Important finding remains, and deciding evidence is
written to the existing plan plus `task-reviews.md`. Failed and blocked attempts remain in that
ledger; no second state machine or ledger is created.

## Caps and non-convergence

Use only configured limits: `${graphGuardrails.maxRepatch}` per failing item,
`${graphGuardrails.maxRoundsPerAgent}` per specialist, `${graphGuardrails.maxSpawnsPerSession}` per
session, `${graphGuardrails.maxParallelWave}` in flight, `${graphGuardrails.maxTasksPerPlan}` at
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

After Phase C's separate final reviewer resolves Critical and Important findings, keep the lease
and run `/verify loop <PLAN_FILE>`. Its documented fallback in `commands/verify.md § 1.6` runs once when the
workflow tool is absent, the name does not resolve or the workflow declines; record the degradation
and never retry resolution. Merge workflow `blocked` and `capped` into the verdict: either prevents
success and is handled before evolve or release.

On complete PASS, run `/evolve auto`, then release only this plan's lease and stop at reviewed,
unstaged changes. On `NEEDS-WORK` or `BLOCKED`, leave the lease and state explicit until the failure
is resolved or the controller declares a safe abort; a safe abort may then use Phase C's matching
release rule. Never stage, commit, push, open a PR, merge, release, publish or deploy without the
separate approval required for that action in the current turn.
