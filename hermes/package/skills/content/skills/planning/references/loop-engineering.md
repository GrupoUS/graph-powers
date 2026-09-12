> Hermes auxiliary: `content/` paths are `file_path` values relative to the registered-document parent. Apply the loaded graph-engineering mapping and host policy; this file is served without template expansion.

# Loop Engineering — the planning loop primitive + execution harness

> **Canonical source** for the loop model the planning chain follows **and** the harness
> patterns it reuses (GEL, calibration anchors, sprint contracts, context reset). Other files
> (`SKILL.md`, `phase-a/b/c-*.md`) reference this by link — they do not redefine it. Read this
> once; each phase guide then declares its own `## Loop contract` using the primitive below.
>
> Harness sections (§ GEL onward) source: Anthropic Engineering, "Harness Design for Long-Running Apps".

---

## Why loops

A planning phase is not a one-shot prompt — it is an **agentic loop**. 

> **An agentic loop = a trigger + a verifiable goal.** The agent generates, *evaluates whether
> the goal is met*, and loops — generate → evaluate → correct — **until the goal passes**,
> without waiting for a fresh human prompt on each turn.

The same survey work names the **four failure modes** that sink loops in production. Every one
of them maps to a guard this skill already owns:

| Failure mode (why loops die) | Guard that prevents it | Lives in |
|---|---|---|
| **No hard stopping condition** — loops forever | **HARD-STOP**: max iterations per artifact → escalate to user | `SKILL.md § Stopping & red flags` + each phase guide |
| **Underspecified goal** — "looks good" is not checkable | **GOAL-GUARD**: refuse to enter the loop unless the goal is a binary PASS/FAIL criterion | this file (§ Calibration anchors) |
| **Context overflow** — long sessions degrade | **CTX-GUARD**: checkpoint at client context signals or task boundaries; resume from the artifact | this file (§ Context Reset Protocol) |
| **Missing cost controls** — runaway spend | **COST-GUARD**: in-flight width `graphGuardrails.maxParallelWave`, correction cap `${graphGuardrails.maxRepatch}` in Phase C | `SKILL.md § Stopping & red flags` + `${rulesDir}/execution.md § Agents & Dispatch` |

---

## The loop primitive

Every phase is an instance of this shape:

```
LOOP <phase>:
  trigger:  <what enters this loop>
  goal:     <BINARY, checkable exit criterion — PASS/FAIL, never prose>
  body:     generate → evaluate (a SEPARATE agent) → correct      (= the GEL, below)
  guards:
    - HARD-STOP : max N iterations on the same artifact → escalate to user
    - GOAL-GUARD: do not start the loop if `goal` is not binary/observable
    - CTX-GUARD : client context signal or task boundary → checkpoint (§ Context Reset Protocol)
    - COST-GUARD: width `graphGuardrails.maxParallelWave` / cumulative `graphGuardrails.maxSpawnsPerWorkflow` / Phase C correction cap `${graphGuardrails.maxRepatch}`
  terminal: goal PASS → next phase | any guard trips → escalate / halt
```

**The body IS the GEL** (§ Generator-Evaluator Loop). Loop engineering is the GEL plus a named
goal and the four guards wrapped around it.

---

## Generator-Evaluator Loop (GEL) — the body of every phase loop

**The core insight:** Separate production from quality judgment. Never ask the same agent to
generate AND evaluate its own work.

**Why self-review fails:** Agents default to "confidently praising work — even when quality is
obviously mediocre." A generating agent is implicitly motivated to complete the task, which
biases it toward approving its own output.

**The solution:** A separate evaluator with calibrated skepticism — not adversarial, just a
second set of eyes with a different incentive: catch what the generator missed.

```
Generator Agent  →  produces plan/spec/code
                      ↓
Evaluator Agent  →  scores against explicit criteria
                      ↓
     PASS? → proceed     FAIL? → actionable feedback → generator
```

**Evaluator disposition:**

- Score against hard thresholds, not gut feel.
- FAIL with specific, actionable feedback — vague "needs improvement" is useless.
- Do not approve work that misses thresholds even if overall quality seems acceptable.
- Distinguish architectural issues (evaluator Mode 3) from quality issues (Mode 1).

---

## The goal must be verifiable — calibration anchors

A goal stated as "the spec is good" cannot close a loop. The **calibration anchors** below give
binary thresholds — they are the **literal PASS criterion** of each gate, not a soft rubric.
Calibrate evaluator judgment against them before each session to prevent score drift.

| Score | Completeness | Atomicity | Risk Coverage | Dependency Order |
|-------|-------------|-----------|---------------|-----------------|
| **9** | Every requirement maps to ≥1 task; edge cases covered | Each task is one natural, independently verifiable deliverable, no ambiguity | Top 5 risks with mitigations, all BLOCK items addressed | Can execute in order without backtracking |
| **7** | All requirements covered, minor edge cases missing | Most steps atomic, 1-2 slightly large but splittable | Major risks identified, some mitigations vague | Order works, minor dependency question |
| **5** | Core requirements covered, 1-2 missing | Mix of atomic and vague steps | Some risks noted, mitigations missing | Some tasks could conflict, needs clarification |
| **3** | Several requirements missing or vague | Steps like "implement auth" with no decomposition | Risks absent or trivial | Order unclear or has explicit conflict |

**Hard thresholds (binary goal):** Completeness ≥ 8 · Atomicity ≥ 7 · Risk Coverage ≥ 7 · Dependency Order ≥ 8.

At/above threshold → goal PASS → exit. Below → FAIL with actionable feedback → loop body runs again.

> **Loop budget (cost control).** Thresholds give the loop a terminal; the budget keeps it from
> running away. CTX-GUARD = the Context Reset Protocol (§ below) at client signals or task boundaries. COST-GUARD =
> Phase C correction cap `${graphGuardrails.maxRepatch}` + `graphGuardrails.maxParallelWave` in flight
> + cumulative `graphGuardrails.maxSpawnsPerWorkflow`. Together they prevent "context overflow" and
> "runaway spend".

---

## Sprint Contracts

> **Canonical definition** (L6+ mandatory; mini-variant for L3-L5). `content/skills/planning/references/phase-b-writing-plans.md`
> references this section — it is the single home for the template.

**Purpose:** Before any implementation begins, planner and evaluator negotiate explicit
agreements defining WHAT will be built, HOW success is verified, and the SCOPE BOUNDARY.
Bridges user stories → testable implementation.

```markdown
### Sprint Contract: [Sprint N — Name]

**Deliverables:**
- [ ] `exact/path/to/file.ts` — [what it does]
- [ ] `exact/path/to/other.ts` — [what it does]

**Acceptance Criteria:**
- [ ] the focused test from `${tooling.commands.test}` passes for `<path>`
- [ ] `${tooling.commands.typeCheck}` reports 0 errors at the phase gate
- [ ] [agent-browser CLI: user can do X without Y error — see `skill_view("graph-powers:webapp-testing")`]
- [ ] Edge case: [describe at least 1 edge case and expected behavior]

**Done Definition:** run `${tooling.commands.typeCheck}` and the focused `${tooling.commands.test}` invocation as separate commands; both exit 0. JS/TS commands first pass `content/references/shared/130-typescript7-oxc-gates.md`.

**Boundary (NOT in this sprint):**
- [Feature A] — defer to Sprint N+1
- [Edge case B] — out of scope for this milestone
```

### Mini-Contract (L3-L5)

For lower complexity, use a 3-line version:

```markdown
**Sprint N:** [Name] — builds [X], verified by `[command]`, excludes [Y].
```

### Worked Example (Database Schema Sprint — generic)

```markdown
### Sprint Contract: Sprint 1 — Database Schema

**Deliverables:**
- [ ] `${paths.schemaRoot}/<schema-file>` — add `notifications` table with FK to `users`
- [ ] `${paths.schemaRoot}/0005_notifications.sql` — migration file

**Acceptance Criteria:**
- [ ] the project's migration/push command completes without errors
- [ ] `${tooling.commands.typeCheck}` reports 0 errors at the phase gate
- [ ] FK index exists on `notifications.user_id`
- [ ] Edge case: duplicate notification insert rejected by unique constraint

**Done Definition:** type-check + apply migration both pass

**Boundary (NOT in Sprint 1):**
- Notification delivery logic — Sprint 2
- Frontend notification bell — Sprint 3
```

---

## Context Reset Protocol

**When to checkpoint:** a task/phase boundary, a real client context-capacity or compaction signal,
or observed repetition/loss of critical state. Use only signals the client actually exposes;
never infer a token count or impose a universal threshold.

Write the checkpoint before a deliberate session transition. Support the client's automatic
compaction and continue from preserved state; never automatically clear context or impose a blanket
`/compact` prohibition.

### Handoff Artifact Format

When writing/resuming a checkpoint, read `content/commands/evolve.md § 4` for session state.

Save to `<plan dir>/HANDOFF.md`, linking the active plan/sprint and existing snapshots/ledgers instead
of pasting them. `/evolve handoff` maintains the session entry pointing to that plan checkpoint.
On resume, recover six answers from the checkpoint and linked artifacts, marking missing facts:

1. Where are we? Canonical project/worktree, selected plan, phase and recorded frontier.
2. What is the objective? Approved scope/acceptance, restrictions and approval provenance.
3. What remains? Pending tasks, dependency/gate barriers and retained execution budgets.
4. What was learned? Sourced findings, rejected alternatives and distinct failed hypotheses.
5. What is done? Recorded work and checks/reviews with matching current inputs.
6. What is next? One bounded eligible action, or the missing selection/proof needed first.

Use Phase C's read-only status before resume/waves. Load `nextAction` by ID and source line, then
relevant Needs, spec decisions and linked proof; recheck the ID if lines moved. Status is the
recorded frontier, not approval or fresh verification: `approval: NOT_VERIFIED`,
`checksExecuted: false` and counts never prove success. `LEASE_CONFLICT` stops writers;
`BLOCKED_DEPENDENCIES` needs missing dependency proof; `NEEDS_FINAL_VERIFICATION` routes to final
acceptance, never DONE. Status replaces neither CHECK, independent review nor validate/acquire.

Reuse valid research; invalidate only findings whose relevant sources changed. Approved specs stay
unchanged during execution. The controller records decision-changing findings, failed attempts and
distinct hypotheses in existing `task-reviews.md`; changed contracts or newly requested scope after
completion return to planning. Retain dispatch/consultation reservations and correction attempts
across contexts; a new status query never resets caps. Preserve restrictions and scoped approval
provenance, reuse current gates and recheck affected proof before advancing.

Partial-work check: preserve local-edit approval/provenance, a no-publication restriction and the
rejected workaround. A gate PASS for snapshot A becomes stale after a relevant uncommitted config
edit at the same HEAD. Keep unaffected completed work; the one next action is rerunning that gate
against current inputs before accepting its result.

---

## Iterative Simplification

> "Every component in a harness encodes an assumption about what the model can't do on its own —
> and those assumptions are worth stress testing."

As Claude's capabilities improve across model versions:

1. **Stress-test each harness component:** can the model now handle this natively?
2. **Sprint decomposition** may become unnecessary for high-capability models.
3. **Evaluator strictness** may be adjustable — less hand-holding on obvious quality failures.
4. **Context resets** may become less necessary as long-context retrieval improves.

**Principle:** don't calcify harness patterns. Remove components that no longer encode real
limitations. The interesting harness work moves to more sophisticated orchestration, not less.

---

## State / control plane

A loop that may reset (CTX-GUARD) needs durable state to resume from — the loop's *control
plane*. In this chain that state is the artifacts on disk, not the conversation:

- `<plan dir>/spec.md` — Phase A's output, Phase B's input.
- `<plan dir>/PLAN.md` — Phase B's output, Phase C's input. One plan is one directory: `content/references/shared/007-path-conventions.md`.
- `.graph-powers/logs/sdd/<plan-slug>/progress.md` — the plan's cross-session ledger (date + base HEAD and working-tree status per phase).
- `<plan dir>/HANDOFF.md` — the reset checkpoint (§ Context Reset Protocol).

Because goal and state live in files, a fresh context can re-enter any loop mid-flight by reading
the artifact + the active sprint contract — the conversation history is replaceable.

---

## Phase → loop contract map

Each phase guide repeats its own contract at the top; this is the index. Goals are binary —
read them as "all clauses true → exit".

| Phase | Verifiable goal (binary) | Body | Guards |
|---|---|---|---|
| **A — Brainstorm** (`content/skills/planning/references/phase-a-brainstorm.md`) | spec file exists **AND** GATE 1 `graph-powers:project-planner` = PASS **AND** user approved **AND** zero TBD/placeholder tokens **AND** every `[ASSUMED]` labeled | inspect → clarify → compare → design → `graph-powers:project-planner` evaluates → revise | HARD-STOP 3 spec revisions · GOAL-GUARD (no observable destination → do not plan) |
| **B — Writing-plans** (`content/skills/planning/references/phase-b-writing-plans.md`) | plan file exists **AND** self-review passes **AND** disjoint-file check passes on every `[PARALLEL-SAFE]` phase **AND** user approved; at L5+, GATE 2 meets the 4 anchors | map files/interfaces → write tasks → self-review → at L5+ `graph-powers:evaluator` Mode 1 scores vs anchors → revise | HARD-STOP 3 plan revisions · COST-GUARD spawn/retry · CTX-GUARD on a large plan |
| **C — Execute** (`content/skills/planning/references/phase-c-executing-plans.md`) | per task: implementer PASS **AND** its wave Evaluator review PASS **AND** its `EVIDENCE` line carries real output; overall: every phase gate met **AND** `/verify quick` PASS **AND** `/evolve auto` done | rolling dispatch: grouped specialist lanes → one consolidated Evaluator per wave → grouped correction when needed → close verified tasks | correction cap `${graphGuardrails.maxRepatch}` · COST-GUARD width `graphGuardrails.maxParallelWave` and total `graphGuardrails.maxSpawnsPerWorkflow` · CTX-GUARD at client signals/task boundaries · then `/debug recover` |

---

## What loop engineering is NOT here

- **Not an autonomous always-on agent.** The git rails hold: commit/push stay manual, the user
  approves every phase boundary and every merge (`content/references/safety-floor.md § 1`). The loop
  iterates *within* a phase toward its goal; it never auto-advances past a user-approval gate.
- **Not a second method.** Phase A and Phase B own their methods. Loop engineering adds only the
  iteration and stop conditions.
- **Not a license to skip framing.** GOAL-GUARD is upstream of the loop: if Phase A can't state a
  binary goal, the answer is more framing (`content/skills/planning/references/step-0-inventory.md § 0.0`), not a
  looser loop.
