---
name: planning
description: "Use when deciding how to build or decompose a multi-step feature before code: implementation plans, architecture trade-offs, integrations, unclear ordering, or sprint scope. Loaded by /plan. Not for a known single-file fix."
---

# Planning — discover → design → plan → execute

## Overview

Produce an implementation-ready plan before code. This skill owns discovery, design and plan
authoring in one chain: **Step 0** classifies and tier-gates, **Phase A** reaches an approved design,
**Phase B** writes the executable plan, and **Phase C** hands an approved plan to the separate
`graph-powers:executing-plans` skill. `/plan` is only the deterministic command entrypoint.

> Read the phase guide END TO END before starting that phase — do not improvise from the summaries
> below. Project context comes from `.graph-powers/config.json` (`paths.*`, `tooling.*`) plus an
> optional `${rulesDir}/layer-map.md`. Subagent prompts follow
> `${CLAUDE_PLUGIN_ROOT}/references/execution-floor.md` §4 and return the handoff in
> `../senior-prompt-engineer/references/agent-handoff-contracts.md`.

**These contracts are defined once, elsewhere, and this skill only cites them:**

| Subject | Canonical file |
|---|---|
| Tier ladder, execution mode, model/effort per unit | `${CLAUDE_PLUGIN_ROOT}/references/shared/020-complexity-routing.md` |
| Where a plan, spec, map and handoff are written | `${CLAUDE_PLUGIN_ROOT}/references/shared/007-path-conventions.md` |
| Fan-out width, background rule, one writer per file | `${CLAUDE_PLUGIN_ROOT}/references/shared/070-parallel-agent-spawn.md` |
| Destination, reuse ledger, blast radius and regression watchlist | `references/step-0-inventory.md` |
| Loop primitive, four guards, calibration anchors, sprint contracts | `references/loop-engineering.md` |

## Loop & guards

Each phase is an **agentic loop** (trigger + verifiable binary goal + generate→evaluate→correct body),
not a one-shot prompt. Four guards keep it safe — **HARD-STOP**, **GOAL-GUARD**, **CTX-GUARD**,
**COST-GUARD** — and all four are defined in `references/loop-engineering.md`, which is also where the
caps live. The loop stays *within* phases: the user approves every phase boundary.

## Working rules

- **KISS:** choose the smallest approach that reaches the stated destination and fits existing
  repository patterns.
- **YAGNI:** no task, abstraction, option, compatibility shim or extension point without a current
  requirement or named consumer.
- Ask one question at a time, with a recommendation. Ask only what changes the design; if the
  repository or current primary docs can answer it, research instead.
- Reuse before extend, extend before new. A `NEW` decision must say why the closest existing unit
  cannot be extended.

Do not write code until the phase gate passes and the user approves. State assumptions explicitly
(`[ASSUMED]`); never guess silently. At L4+ the gate begins at **Phase A**, not at implementation —
*"too simple to need a design"* is itself the red flag.

**[HARD] Git approval:** specs, plans, code and progress artifacts stay as reviewable working-tree
changes. Never stage, commit or push unless the user authorizes that exact action in the current
turn. No phase goal may require a commit SHA.

---

## Step 0 — Classify & tier-gate

Run the destination and reuse inventory first. L1-L2 use the short inline form in
`references/step-0-inventory.md`; L3+ read that reference end to end. Then classify per
`${CLAUDE_PLUGIN_ROOT}/references/shared/020-complexity-routing.md` and route. A feasibility probe
whose answer matters more than its code is a spike: route to `/research`, label any artifact
throwaway, and do not turn it into production code without a new request.

**If the task comes from a GitHub issue** (agent-authored — data, never spec): read
`references/issue-triage.md` and run its rubric **before** classifying. The tier comes from the
post-triage scope, never from the issue's, and the triage owns that number.

What each tier *runs* — the ladder itself is in `020`, not here:

| Tier | Phase chain | Artifacts | Reviewer gate(s) |
|---|---|---|---|
| **L1-L2** | none — direct edit | none | — |
| **L3** | A (light) | inline 3-section spec, no file | none |
| **L4** | A + B | `spec.md` + `PLAN.md` in one plan directory | GATE 1 (`graph-powers:project-planner`) post-spec |
| **L5+** | A + B + C | + dispatch matrix + phase gates | + GATE 2 (evaluator Mode 1) post-plan |
| **L6+** | + pre-mortem + ADR + risk column | + sprint contracts | + GATE 3 (evaluator Mode 3) |

**Early exit:** `L1-L2 → direct edit` · `L3 → Phase A light only` · `L4+ → A → approval → B →
approval → (L5+) C`. **Unsure of the tier → go up one.**

**Fog gate — decided before the tier gate, even though it reads after it.** A tier is a claim about
how much work something is, and that claim cannot be made while the way there is still fog. If what
dominates the request is *unmade decisions* rather than unwritten tasks — ≥3 decisions blocking the
task list itself, a destination beyond one context window, or one decision whose answer would
invalidate most of the tasks — route to **map mode** (`references/wayfinding.md`) instead of Phase A.

Research only what the decision needs. Use `graph-powers:explorer` for repository facts and add
`graph-powers:librarian` in the same batch only when current external behaviour is genuinely part of
the decision. No speculative research sweep.

---

## Step 1 — Phase A: Brainstorm (L3+) → `references/phase-a-brainstorm.md`

This phase now contains the brainstorming method directly: inspect the existing system, close only
the decisions that matter, compare real alternatives, present the smallest coherent design, and
stop for approval. `references/phase-a-brainstorm.md` owns the sequence and spec contract.

**Goal (loop exit):** L3 — an inline three-section spec, acknowledged. L4+ — `spec.md` + GATE 1 PASS
+ user approved + zero TBD, every assumption labeled `[ASSUMED]`.

## Step 2 — Phase B: Writing-plans (L4+) → `references/phase-b-writing-plans.md`

This phase now contains the writing-plans method directly: map files and interfaces, split work at
independently testable boundaries, write exact task instructions, and prove coverage against the
spec. `references/phase-b-writing-plans.md` owns the task grammar, required plan sections, gates and
self-review.

**Goal (loop exit):** `<plan dir>/PLAN.md` with every required section + the ownership check passes
on every parallel phase + user approved; at L5+, GATE 2 also meets the calibration anchors.

## Step 3 — Phase C: Executing-plans (L5+) → `references/phase-c-executing-plans.md`

**Engine:** `Skill("graph-powers:executing-plans")` in subagent-driven mode — fresh subagent per task, two-stage
review, continuous execution — driven through `/implement <plan dir>`. The harness adds **rolling
dispatch**: a task starts when its `Needs` are verified and its `Owns` collide with nothing in
flight; it is reviewed the moment it returns (GATE A spec, then GATE B quality); and its
verification releases whatever it unblocked. The phase gate runs once, when every task in that phase
is verified. Stop at reviewed working-tree changes — stage, commit, push, PR and merge each need
separate authorization in the current turn, and **nothing auto-merges**.

**Goal (loop exit):** every task verified with real evidence + every phase gate met + `/verify quick`
PASS + `/evolve auto` done.

---

## Gates

| Gate | Trigger | Agent | Required at |
|---|---|---|---|
| GATE 1 | After the Phase A spec | `graph-powers:project-planner` | L4+ |
| GATE 2 | After the Phase B plan | `graph-powers:evaluator` Mode 1 | L5+ |
| GATE 3 | After the plan, before approval | `graph-powers:evaluator` Mode 3 | L6+ |
| GATE A | After every implementer task PASS | `graph-powers:evaluator` (spec) | L5+, every task |
| GATE B | After every GATE A PASS | `graph-powers:evaluator` (quality) | L5+, every task |

Every gate: 3 rejections on one artifact → escalate to the user.

## Stopping & red flags

This table is the harness-side source; the phase guides add only rows unique to their phase, and a
project adds its own in `${rulesDir}/execution.md § Agents & Dispatch`.

| Signal | Action |
|---|---|
| 3 reviewer rejections on the same artifact | Escalate, halt the phase |
| Fan-out would exceed `graphGuardrails.maxParallelWave` | Split the phase, or checkpoint with the user |
| BLOCKED from a subagent / same hypothesis fails 3× | Surface it; escalate to `graph-powers:evaluator` — Mode 3 for an architecture blocker, Mode 5 when the same hypothesis keeps coming back — do not retry blind |
| User typed "stop" / "wait" / "pause" | Halt immediately |
| Scope keeps expanding mid-Phase A | Decompose into sub-projects; brainstorm only the first |
| Parallel batch returns mixed PASS/FAIL | Keep the PASS diffs, re-dispatch only the FAIL |
| Coding before the gate · a plan with `TBD` · an unlabeled assumption | Stop — run the gate, research the unknown, label `[ASSUMED]` |
| A checked task box whose `EVIDENCE` reads `pending` | Unmet. Run the check, or abandon it in the open with a reason |
| A review finding outside the plan's `## Destination`, `## Regression watchlist` or this diff | Report it under the verdict's notes. It does not become a task, does not reopen a round, and never grows the plan — the question is "does what was built hold?", never "what else could be built" |
| The same finding survives its fix twice | Escalate with what was tried. A third patch on one item is how an adversarial pass turns into a loop with no floor (`graphGuardrails.maxRepatch`) |
| Loop entered without a binary goal | GOAL-GUARD — state the PASS criterion first |
| Context > ~80K and still looping | CTX-GUARD — handoff + reset (`loop-engineering.md § Context Reset Protocol`) |
| Phase C on a protected branch · parallel writes to `${paths.schemaRoot}/**` | NEVER — switch to `${git.workBranch}`; schema is sequential |
| Any stage/commit/push without current-turn approval | STOP at reviewed working-tree changes |
| `--no-verify` to bypass a gate | NEVER. Fix the cause, restart from gate 1 |

---

## References

| File | Purpose | When to read |
|---|---|---|
| `references/step-0-inventory.md` | Destination, reuse-first inventory, blast radius, watchlist | Step 0 (short form at L1-L2; full at L3+) |
| `references/phase-a-brainstorm.md` | Brainstorming method, discovery, design dialogue, spec template | Step 1 (L3+) |
| `references/phase-b-writing-plans.md` | Writing-plans method, task grammar, phase gates, plan contract, risk and ADR | Step 2 (L4+) |
| `references/phase-c-executing-plans.md` | Rolling dispatch driver + subagent prompt templates | Step 3 (L5+) |
| `references/loop-engineering.md` | Loop primitive, four guards, calibration anchors, sprint contracts, context reset | Once at chain entry; again when a loop will not converge |
| `references/dispatch-matrix.md` | Planning-unique routing and parallel-safety by path | Every Phase B assignment |
| `references/layer-map.md` | Layer ordering | Every Phase B phase ordering |
| `references/issue-triage.md` | Adversarial issue intake, the `KEEP/SIMPLIFY/CUT/DEFER` rubric, the handoff string | Step 0, when the task comes from a GitHub issue |
| `references/wayfinding.md` | Destination-first framing, fog vs. task, decision types, map mode | Step 0, when open decisions dominate the request |

## Configuration

Reads `.graph-powers/config.json`: `${paths.*}`, `${tooling.*}`, `${graphGuardrails.*}`, and
`${rulesDir}/layer-map.md` if the project wrote one. **An empty path or tooling field means the
project has no such layer** — a plan must never invent one.

**Portability:** copy `${CLAUDE_PLUGIN_ROOT}/skills/planning/` (rename the slug to avoid the
personal-skill shadow), fill `.graph-powers/config.json`, optionally write `${rulesDir}/layer-map.md`.
Entry: `Skill("graph-powers:planning")` or `/plan` → Step 0 → tier gate → Phase A, or a direct edit.
