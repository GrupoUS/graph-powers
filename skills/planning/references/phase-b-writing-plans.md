# Phase B — Writing-plans

> Canonical plan-authoring method for the planning chain. It turns an approved design authority
> into a plan a zero-context implementer can execute without inventing paths, interfaces, tests or
> scope.

---

## Entry contract

- Direct route: Phase A complete, with `<plan dir>/spec.md` GATE-1-approved and user-approved.
- `ultra-plan` route: the exact Step 0 handoff blocks and chosen approach are the design authority;
  the generated plan still waits for `/plan`'s human gate.
- Task tier is **L4+** (L3 skips Phase B). Tier ladder: `${CLAUDE_PLUGIN_ROOT}/references/shared/020-complexity-routing.md`.
- Branch is `${git.workBranch}`.

## Exit contract

- Plan at `<plan dir>/PLAN.md`, one directory per plan
  (`${CLAUDE_PLUGIN_ROOT}/references/shared/007-path-conventions.md`).
- Self-review PASS and user approved. At L5+, GATE 2 (evaluator Mode 1) also PASS before Phase C.

## Loop contract

> Model: `references/loop-engineering.md`. Guards, caps and the anchors are defined there, once.

- **trigger:** Phase A complete, tier L4+.
- **goal (binary):** `PLAN.md` exists **AND** it carries every required section from Step 5
  **AND** every task declares `Owns` and `Needs` **AND** Step 6 passes **AND** user approved. At L5+,
  GATE 2 must also meet the calibration anchors (`loop-engineering.md § Calibration anchors`).
- **body:** map files and interfaces → write independently testable tasks → self-review → evaluator
  Mode 1 → correct.
- **terminal:** goal PASS → Phase C. Any guard trips → escalate to user.

---

## Before tasks — scope and file map

If the design authority contains independent subsystems, stop and propose one plan per independently
useful, testable slice. A long input is not automatically several plans; a slice is independent only when a
reviewer could accept it while rejecting its neighbour.

Map every file the work creates or modifies, its single responsibility, and the interfaces between
files. Follow the repository's existing layout. Split a touched file only when the change needs that
seam now; do not reorganize the tree for hypothetical future work.

KISS and YAGNI bind the plan: fold setup, scaffolding, config and docs into the task whose
deliverable needs them. Do not create a task, abstraction, flag or compatibility path without a
current requirement or consumer.

---

## Step 1 — The task grammar

A task is written as a checkbox with indented fields. That is not decoration: `/implement` parses
`- [ ]`, `/verify` reads the evidence, and the same block is both the work order and the ledger that
proves the work happened.

```markdown
- [ ] **T2.1** — <imperative one-line action>
  Owns: <full paths this task is the sole writer of>
  Needs: T1.2 (reads: <the type, file or exported symbol it consumes>) | none
  Agent: <lane> · Skill: <domain skill | none> · Effort: mechanical | design
  CHECK: <command, scoped to this task>
  EXPECT: <string or /regex/ that can only appear on success>
  EVIDENCE: pending
  Steps:
    1. Read <file> to confirm <pre-state>
    2. Write failing test at <test-path> asserting <criterion> — confirm RED
    3. Implement the minimal change at <impl-path> — confirm GREEN
  Risk: low | medium | high      (L6+ only)
```

**`Owns:` is the ownership contract.** Two tasks that run at the same time own disjoint paths, and
ownership is declared here rather than inferred at dispatch time. The rule and its repairs live in
`${CLAUDE_PLUGIN_ROOT}/references/shared/070-parallel-agent-spawn.md § One writer per file`.

**`Needs:` carries its payload.** Name what this task reads from that one. An arrow whose payload you
cannot name is a false edge — delete it, and the two tasks run together. The execution graph in Step
5 visualizes the same contract; this field is what the scheduler reads.

**`CHECK` / `EXPECT` / `EVIDENCE` replace a sentence with a command.**

- `CHECK` is **scoped to this task** — the one test, the one search, the one probe. Repository-wide
  gates belong to the phase gate (Step 2), not to every task.
- `EXPECT` is a substring of the command's output, or a `/regex/`. Match the line that can only
  appear on success (`8/8 passed`), never one that appears either way (`done`).
- `EVIDENCE` starts as `pending` and is replaced by the deciding output lines when the check runs.
  **A checked box whose `EVIDENCE` still reads `pending` is unmet — worse than unchecked, not
  better.** A checkbox is a claim; the evidence is the proof, and the gap between the two is the
  failure this grammar exists to catch.
- A check that turns out impossible is not deleted. It is surrendered in the open, on its own line:
  `ABANDON: T2.1 <reason>` — and every report lists it.

**`Agent:` takes only a routable lane**, written with its namespace exactly as it is spawned:
`graph-powers:frontend-specialist` · `graph-powers:debugger` · `graph-powers:performance-optimizer` ·
`graph-powers:mobile-developer` · `graph-powers:verification`. A lane whose root the project does not
have is not routable — no `mobileRoot`, no mobile lane. `main` means the main thread and is valid
only in the human chain: the workflows have no main-thread lane and silently reroute it, so a plan
headed for `ultra-build` never writes it.

**`Effort:`** picks the model tier per
`${CLAUDE_PLUGIN_ROOT}/references/shared/020-complexity-routing.md § Model and effort per unit of work`.

**`Steps:`** are required when a subagent owns the task — it reads this block and nothing else — and
omitted when the main thread does. Give exact paths, signatures, commands and expected results.
Include code or test snippets when a fragile or novel step would otherwise force the implementer to
make a design decision; do not paste boilerplate the repository already supplies.

### Atomicity, tested from both sides

One deliverable, one owner, one acceptance block. The test is two-sided, and the second half is the
one usually missing:

- **Too big** — it would need two independent commits, or its acceptance needs two unrelated `EXPECT`
  strings → split.
- **Too small** — its `Owns` set overlaps a sibling's, or its `EXPECT` is a sub-assertion of a
  sibling's → merge. Splitting past the natural joint costs more in re-established context than the
  parallelism returns.

Also disqualifying: `TBD`, a placeholder path, "similar to T2.1", "implement X" as a whole task, and
an acceptance nobody can run ("looks right" is not a check).

**Dependency check:** when a `Needs` edge is not obvious from the paths, name the exact payload before
Step 2. If none exists, delete the edge. **Agent ↔ skill lookup:** `dispatch-matrix.md`.

## Step 2 — Phase envelopes, and the gate that closes each one

Phases group tasks in layer-dependency order (`references/layer-map.md`) and carry the marker
`/implement` parses. `[PARALLEL-SAFE]` is the spelling everywhere:

```markdown
## Phase 2 — Components  [PARALLEL-SAFE]

- [ ] **T2.1** — …
- [ ] **T2.2** — …

### Phase 2 gate
- [ ] **G2.1** — every T2.x met its acceptance with evidence
  CHECK: <re-run this phase's task CHECK lines>
  EXPECT: no gate left with EVIDENCE pending
  EVIDENCE: pending
- [ ] **G2.2** — the project still type-checks and lints as a whole
  CHECK: ${tooling.commands.typeCheck} then ${tooling.commands.lint}
  EXPECT: <the success line>
  EVIDENCE: pending
- [ ] **G2.3** — nothing outside this phase's Owns sets changed
- [ ] **G2.4** — the interfaces the next phase Needs exist and match
```

**Why the gate exists at all:** a dozen locally perfect tasks can still be a broken repository, and
nothing in a per-task check would notice. The gate is where integration is proven — and it is also
where the whole-project commands run, **once per phase instead of once per task**. A twelve-task
plan that type-checks twelve times is paying twelve times for one fact.

Order only layers the project declares in `references/layer-map.md` or `${rulesDir}/layer-map.md`.
Preserve dependency direction — data contracts before their consumers, integration after the units
it connects, verification after the changed path exists — and never invent an absent layer.

## Step 3 — Ownership check on every `[PARALLEL-SAFE]` phase

Every task has a non-empty `Owns`; the sets are pairwise disjoint; nothing shared is written twice.
The rule, the exceptions (schema, singletons, global styles) and the repairs are in
`${CLAUDE_PLUGIN_ROOT}/references/shared/070-parallel-agent-spawn.md § One writer per file`. Overlap
found → re-split, or move the phase to `[SEQUENTIAL]`.

## Step 4 — Dispatch matrix at the top of the plan

```markdown
## Dispatch matrix

| Task | Agent | Skill | Owns | Needs |
|---|---|---|---|---|
| T1.1 | graph-powers:debugger | none | <paths> | — |
| T2.1 | graph-powers:frontend-specialist | <domain skill> | <paths> | T1.1 |
```

One table, read before any task block, so the reader sees the graph before the prose.

## Step 5 — Write the plan

**Path:** `${paths.planDir}/YYYY-MM-DD-<slug>/PLAN.md` (today, UTC), one directory per plan.

The sections below are the contract, not a style. `/verify § 3` reads the reuse ledger, regression
watchlist and rollback **verbatim**; without them verification degrades to a generic gate run.

```markdown
# <Feature> — implementation plan

**Date:** YYYY-MM-DD · **Branch:** `${git.workBranch}` · **Baseline:** <short SHA>
**Tier:** L<n> · **Risk surface:** <none | the surfaces from chain.riskSurfaces>
**Design authority:** <approved spec path | ultra-plan: embedded Step 0 handoff + chosen approach>

## Destination
<the observable condition for "arrived" — "done when X is true", never "improve X">

## Reuse ledger
| # | Need | Existing asset (`path:line`) | Verdict | Why extending fails (NEW only) |

## Regression watchlist
| # | Existing behaviour that must still work | How to prove it | Phase |

## Execution graph
<the DAG, then one row per edge naming what the destination reads from the source>

## Dispatch matrix          <Step 4>

## Phase 1 — <Name>  [SEQUENTIAL]
- [ ] **T1.1** — …          <Step 1 grammar>
### Phase 1 gate            <Step 2>

## Verification
- Gates: the commands in `${tooling.commands}` — a gate the project did not declare is reported
  NOT DECLARED, never as passing
- The project's own negative checks, from `${rulesDir}/`
- Staging E2E if UI changed, per `Skill("webapp-testing")`
- Post-success: `/evolve auto`

## Rollback
<how to undo each phase: revert commit, flag off, column left in place>

## Out of scope
<each row with the trigger that would reopen it>

## Not yet specified
<the declared fog — may be empty, but then say "no fog: the path is closed">
```

Nothing is staged or committed. The plan is a working-tree artifact until a person says otherwise.

## Step 6 — Plan self-review

Fix inline once, then run the checklist once more:

- [ ] Every task: non-empty `Owns`, a `Needs` with a named payload or `none`, a runnable `CHECK`
      with an `EXPECT` that cannot match on failure.
- [ ] Every `[PARALLEL-SAFE]` phase passes the ownership check (Step 3).
- [ ] Every phase ends with a gate, and the whole-project commands appear **only** there.
- [ ] Every in-scope design requirement maps to a task; no task serves an out-of-scope row.
- [ ] Names and signatures consumed later exactly match what earlier tasks produce.
- [ ] Every required section is present and non-empty (`## Not yet specified` may say it is empty).
- [ ] Every watchlist row has a proof command and an owner phase.
- [ ] Every execution-graph edge names the payload its destination reads; parallel siblings have
      disjoint `Owns` sets.
- [ ] Every not-yet-specified row is still fog or became an evidence-backed decision, never an
      assumed task.
- [ ] No `TBD`, no placeholder path, no "similar to T…", no mega-task.
- [ ] Phase order matches `references/layer-map.md`.
- [ ] Agent lanes are routable; no `main` in a plan headed for a workflow.
- [ ] Fan-out per phase ≤ `graphGuardrails.maxParallelWave`.
- [ ] L6+: `## Risk` and an ADR present.

## Step 7 — GATE 2 — evaluator Mode 1 (L5+)

Dispatch `graph-powers:evaluator` in Mode 1 with the seven-section prompt from
`${CLAUDE_PLUGIN_ROOT}/references/execution-floor.md § 4`. It reads the design authority and plan,
checks the Step 6 list, scores the calibration anchors, writes nothing, and returns the canonical
Context Handoff.

At L4, skip this gate unless the user asks for a second review. At L5+, **PASS** → Step 8;
**FAIL** → revise inline, scored against `loop-engineering.md § Calibration anchors`;
**BLOCKED** → surface to the user. **L6+:** run GATE 3 (evaluator Mode 3, architecture) between Step
7 and Step 8.

## Step 8 — User approval

> "Plan saved at `<plan dir>/PLAN.md` and its required review passed. Approve execution, or stop at the plan?"

Wait for an explicit yes. On a revision request → revise, re-run Step 6, re-run Step 7.

## Step 9 — Transition

At L4, stop at the approved plan. At L5+, continue only after the Step 8 approval:

```
"Phase B complete. Plan ready at <plan dir>/PLAN.md. Invoking Phase C."
```

---

## Risk — pre-mortem + ADR (L6+)

> Use for L6+ or a real risk surface: breaking contracts, security, irreversible data or more than
> one viable architecture. Skip otherwise.

**Pre-mortem.** "Two days later, the feature broke. What happened?" Sweep the failure surfaces:
build and type-check (schema drift, stale generated types, lockfile) · logic (null, race, off-by-one,
unhandled rejection) · integration (webhook signature, contract mismatch, version skew) · data
(migration path, FK constraint, missing index, rollback data loss) · auth (wrong scope, missing
tenant filter, privilege escalation) · performance (N+1, full scan, bundle bloat) · security (input
gap, secret leak, CSRF/XSS/SSRF) · accessibility and SEO · cross-cutting (telemetry blind spot, log
injection, no rollback) · human (requirement misread, scope creep).

```
Score = Probability (1-3) × Impact (1-3)   →  7-9 BLOCK (mitigate first) · 4-6 MITIGATE · 1-3 ACCEPT
```

```markdown
## Risk
| # | Risk | Score | Mitigation |
|---|------|-------|------------|
```

A score ≥ 7 has a written rollback path or it does not ship. The project's own recurring failure
modes come from `${rulesDir}/`, never from a generic list invented here.

**ADR (≤15 lines, when more than one approach was valid):**

```markdown
### ADR: <title>
**Context:** <problem + why a decision is needed>
**Options:** A) … / B) …
**Decision:** <X> because <reason>
**Consequences:** <consequence>, <trade-off>
```

ADRs go before the first phase. Sprint contracts, when the tier calls for them, are defined once in
`loop-engineering.md § Sprint Contracts`.

## Anti-patterns

| Bad | Good |
|---|---|
| "Implement feature X" as a task | One deliverable, one `EXPECT`, TDD shape |
| `Acceptance: looks correct` | `CHECK` + an `EXPECT` that cannot match on failure |
| `Owns: TBD` | Full paths, or the task is not ready to be written |
| Two parallel tasks writing one shared module | Re-split, or the phase is `[SEQUENTIAL]` |
| `Needs: T1.2` with no payload named | Name what is read, or delete the edge and gain the parallelism |
| Whole-project type-check inside every task | Scoped check per task; the repository-wide one at the phase gate |
| Checked box, `EVIDENCE: pending` | Unmet. Run the check, or abandon it in the open |
| A plan without `## Reuse ledger` / `## Regression watchlist` / `## Rollback` | `/verify` reads those three verbatim; without them it is a generic gate run |
