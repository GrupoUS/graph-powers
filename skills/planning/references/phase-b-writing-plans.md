# Phase B — Writing-plans

> Sequential guide for the second phase of the planning chain.
> **Direct-invokes `superpowers:writing-plans` as the engine** and wraps it with harness deltas.
> Consolidates the former extended-plan-detail + risk references. Sprint Contracts live in `loop-engineering.md § Sprint Contracts`.

---

## Entry contract

- Phase A complete. Spec at `${paths.planDir}/specs/<file>`, GATE-1-approved + user-approved.
- Task tier is **L4+** (L3 skips Phase B).
- Branch is `${git.workBranch}`.

## Exit contract

- Plan file at `${paths.planDir}/YYYY-MM-DD-<feature>.md` in the working tree.
- GATE 2 (evaluator Mode 1) PASS. User approved. Proceed to `phase-c-executing-plans.md`.

---

## Loop contract

> Phase B is a goal-gated loop. Model: `references/loop-engineering.md`.

- **trigger:** Phase A complete (spec GATE-1-approved + user-approved), tier L4+.
- **goal (binary):** plan file exists **AND** GATE 2 `evaluator` Mode 1 meets the calibration anchors (Completeness ≥ 8 · Atomicity ≥ 7 · Risk Coverage ≥ 7 · Dependency Order ≥ 8, `loop-engineering.md § Calibration anchors`) **AND** disjoint-file check passes on every `[PARALLEL-SAFE]` phase **AND** user approved.
- **body:** `superpowers:writing-plans` generates the plan → `evaluator` Mode 1 scores vs anchors (Step 7) → revise inline.
- **guards:** HARD-STOP 3 plan revisions → escalate · COST-GUARD spawn cap 5 per phase · CTX-GUARD on a large plan (`loop-engineering.md § Context Reset Protocol`).
- **terminal:** goal PASS → Phase C. Any guard trips → escalate to user.

---

## Engine — invoke `superpowers:writing-plans`

**Invoke `Skill("superpowers:writing-plans")`** and let it drive the core loop. Do NOT reimplement its rules — the engine owns them:

| The engine owns | the harness wraps (the deltas below) |
|---|---|
| bite-sized 2-5 min TDD task granularity · mandatory plan header · exact file paths · no-placeholders rule · file-structure mapping · plan self-review · save to `${paths.planDir}/` · execution-handoff offer | per-task `Agent:`/`Skill load:` from `dispatch-matrix.md` (Step 1) · `[SEQUENTIAL]`/`[PARALLEL-SAFE]` envelopes by `layer-map.md` order (Step 2) · disjoint-file enforcement (Step 3) · dispatch matrix table at top (Step 4) · GATE 2 `evaluator` Mode 1 (Step 7) · **intercept the engine's execution-handoff** → Phase C via `/implement`, no user re-prompt (Step 9) |

The numbered steps are the **harness deltas in execution order** — interleave with the engine.

---

## Step 1 — Decompose spec into atomic tasks (2-5 min each)

> Engine-owned (granularity, TDD shape, no-placeholders). Harness delta: `Agent:` / `Skill load:` / `Mode:` from `dispatch-matrix.md` so `/implement` knows which agent runs each task.

```markdown
### Task N.M — <one-line action in imperative form>

- **Agent:** <frontend-specialist | debugger | performance-optimizer | mobile-developer | project-planner | evaluator | verification | main>
- **Skill load:** <the domain skill matching this phase, from this plugin or from the project | none>
- **Mode:** [SEQUENTIAL] or [PARALLEL-SAFE]
- **Depends on:** T<N.M> | none
- **Files touched:** <full-path-1>, <full-path-2>
- **Acceptance:** <single-line testable criterion — command, test name, runtime probe>
- **Steps:**
  1. Read <file> to confirm <pre-state>
  2. Write failing test at <test-path> — assert <criterion>
  3. Run `${tooling.commands.test}` scoped to that test → confirm RED
  4. Implement minimal code at <impl-path>
  5. Re-run → confirm GREEN
  6. `${tooling.commands.format}` on every touched file
  7. Record the suggested conventional-commit subject for optional user-authorized use
- **Estimated time:** 2-5 min
- **Risk:** low | medium | high   (L6+ only — high-risk tasks get extra review)
```

**Granularity rules:** each task = one reviewable change unit (would need multiple independent commits → split) · TDD baked in (skip steps 2-3 only for non-testable docs/config/layout-CSS) · no "implement X" mega-tasks · no "similar to Task N" — every task is complete prose · no placeholder paths, no TBD, no "etc." · acceptance must be runnable ("looks right" is not one) · task self-contained (a fresh subagent reading only the block can finish it).

**Dependency check (tier-gated):** if tasks reveal hidden sequencing/shared-state coupling not obvious from paths → `mcp__sequential-thinking__sequentialthinking` to verify parallel-safe groups **before** Step 2 (L5+ MUST · L4 SHOULD). **Skill ↔ Agent lookup:** `dispatch-matrix.md`.

## Step 2 — Group tasks into phase envelopes

`[SEQUENTIAL]` tasks run one at a time; `[PARALLEL-SAFE]` tasks fire as one batched message (≤ 5 concurrent agents).

```markdown
## Phase 1 — Foundation [SEQUENTIAL]
T1.1 → T1.2 → T1.3

## Phase 2 — Components [PARALLEL-SAFE — N subagents]
T2.1 (Agent: frontend-specialist, files: ${paths.componentsRoot}/<family-a>/*)
T2.2 (Agent: frontend-specialist, files: ${paths.componentsRoot}/<family-b>/*)

## Phase 3 — Integration [SEQUENTIAL]
T3.1 → T3.2

## Phase 4 — Verification [SEQUENTIAL]
T4.1 /verify quick → T4.2 staging E2E (if UI) → T4.3 /evolve auto
```

**Phase ordering = layer dependency order** per `references/layer-map.md`:
`Schema → Service → Router → Webhook → Shared types → UI primitives → Components → Pages → Verification`. Never plan presentation before data; never plan integration before components compile.

## Step 3 — Disjoint-file enforcement (PARALLEL phases)

For every `[PARALLEL-SAFE]` phase verify: every task has a non-empty `Files touched` · file-path sets across tasks are **pairwise disjoint** · no two tasks edit the same schema module (`${paths.schemaRoot}/**`), cross-cutting singleton (`${paths.backendRoot}/_core/*` or wherever the project puts them), global stylesheet (`${paths.stylesRoot}/**`), or shared package in parallel (shared modules → SEQUENTIAL). Overlap detected → downgrade to SEQUENTIAL or re-split to disjoint paths.

## Step 4 — Add dispatch matrix table at top of plan

```markdown
## Dispatch matrix (this plan)

| Task | Agent | Skill | Mode | Files |
|---|---|---|---|---|
| T1.1 | main | none | SEQ | <paths> |
| T2.1 | frontend-specialist | <domain skill> | PAR | <paths> |
```

## Step 5 — Write plan doc

> Engine writes the working-tree plan (incl. mandatory header w/ REQUIRED SUB-SKILL line). Harness delta: Spec lineage, Dispatch matrix, layer-ordered phases.

**Path:** `${paths.planDir}/YYYY-MM-DD-<feature>.md` (today, UTC).

```markdown
# <Feature> — Implementation plan

## Spec lineage
- Spec: ${paths.planDir}/specs/<file>   · Spec state: reviewed working tree or approved commit

## Dispatch matrix      <see Step 4>

## Phase 1 — <Name> [SEQUENTIAL or PARALLEL-SAFE]
### Task 1.1 — <action>   <task block per Step 1>

## Verification
- Quality gates: `${tooling.commands.typeCheck}`, `${tooling.commands.lint}`, `${tooling.commands.test}`
- Negative checks: the project's own, from `${rulesDir}/` — the patterns that have broken *this* project before
- Staging E2E if UI: browser flow against `${project.stagingUrl}` per `Skill("webapp-testing")`
- Post-success: `/evolve auto` → progress.md row

## Out of scope        — explicit non-goals (mirror spec + plan-level exclusions)
## Risks               — L6+ only: link to § Risk + ADRs
## Open questions      — anything unresolved at plan time
```

Run the relevant Markdown/config checks. Do not stage or commit the plan without
explicit current-turn user approval.

## Step 6 — Plan self-review

Scan before GATE 2 (fix inline, re-review after each fix):

- [ ] No "TBD"/"TODO"/"similar to Task N"/"implement X" mega-tasks.
- [ ] Every task self-contained (a fresh subagent could execute reading only that block).
- [ ] Every `[PARALLEL-SAFE]` phase passes disjoint-file check.
- [ ] Every task has a runnable acceptance criterion.
- [ ] Phase ordering matches layer dependency (`references/layer-map.md`).
- [ ] Agent assignments match `dispatch-matrix.md`; no skill load forgotten — every task names the domain skill it needs, or says `none` deliberately.
- [ ] Total spawn count per phase ≤ 5.
- [ ] Verification phase included; final task invokes `/evolve`.
- [ ] Findings with Confidence ≤ 2 flagged (§ Confidence scoring); L6+: ADR + Risk present (§ Risk).
- [ ] Research complete (codebase + Context7 + Tavily best-practice).

## Step 7 — GATE 2 — evaluator Mode 1 (Plan Review)

```ts
Agent({
  subagent_type: "evaluator",
  prompt: "Mode 1 Plan Review. Plan at <path>. Critique: ambiguities, missing edge cases, layer-ordering violations, parallel-safety violations, gate placement, agent assignment fitness, atomic-task granularity, acceptance-criterion testability, dispatch matrix correctness. Return: PASS / FAIL+specifics / BLOCKED. < 2000 tokens.",
})
```

**PASS** → Step 8. **FAIL** → revise inline (loop body, scored vs `loop-engineering.md § Calibration anchors`); **HARD-STOP at 3 iterations** → escalate. **BLOCKED** → surface to user. **L6+:** add GATE 3 (evaluator Mode 3 architecture pass) between Step 7 and Step 8.

## Step 8 — User approval

> "Plan saved at `${paths.planDir}/<file>`. evaluator Mode 1 returned PASS. Approve to proceed to Phase C (executing-plans)?"

Wait for explicit "yes". On revision request → revise + re-loop self-review + Step 7.

## Step 9 — Transition

The engine ends by **offering an execution choice** (subagent-driven vs inline). **Intercept it** — do NOT surface that generic prompt. This chain always routes to Phase C via `/implement` (engine "subagent-driven" → Phase C default; engine "inline" → Phase C with `superpowers:executing-plans` as doctrine).

```
"Phase B complete. Plan ready at <path>. Invoking Phase C."
```
Read `phase-c-executing-plans.md` next.

---

## Confidence scoring

| Score | Meaning | Action |
|-------|---------|--------|
| **5** | Verified in codebase / docs | Use directly |
| **4** | Multiple sources agree | Use with confidence |
| **3** | Community consensus | Note uncertainty |
| **2** | Single source / unverified | Flag as assumption |
| **1** | Speculation | Don't rely on it |

**Rule:** findings ≤ 2 MUST be flagged and validated before relying. Surface them in a Research Summary table (`# | Finding | Confidence | Source | Impact`) when the plan needs research lineage.

## Complexity levels (calibrate decomposition + agent count)

| Level | Indicators | Deliverables | Agents (parallel?) |
|---|---|---|---|
| L1-L2 | Bug fix, single function | Atomic tasks | None |
| L3 | Feature, multi-file | Tasks + research | 1 (explorer/specialist), no |
| L4-L5 | Multi-file feature | + parallel + mini-contracts | 2-3 swarm, YES |
| L6-L8 | Architecture, integration | + full sprint contracts + pre-mortem + ADR | 3-5 team, YES |
| L9-L10 | Migrations, multi-service | + dependency graph | 5+, YES |

**Complexity bumps:** +1/+2 for multi-file · DB/schema change · auth/permission · 3rd-party API · breaking change · security-sensitive · multi-service. −1 for reused pattern · similar code exists · isolated module · tests exist · feature flag available.

## Risk — pre-mortem + ADR (L6+)

> Use at L6+, architecture decisions, multi-module/breaking/security work. Skip L1-L5 unless breaking/security/data-loss risk.

**Pre-mortem.** "2 days later, the feature broke. What happened?" Brainstorm failure modes across: build/type-check (schema drift, stale generated types, lockfile) · logic (null, race, off-by-one, unhandled rejection) · integration (webhook signature, contract mismatch, version skew) · data (migration path, FK constraint, missing index, rollback data loss) · auth (wrong scope, missing tenant filter, privilege escalation) · performance (N+1, full scan, bundle bloat) · security (input gap, secret leak, CSRF/XSS/SSRF) · a11y/SEO · cross-cutting (telemetry blind spot, log injection, missing rollback) · human (requirement misread, scope creep, cardinal-rule violation).

```
Score = Probability (1-3) × Impact (1-3)   →  7-9 BLOCK (mitigate first) · 4-6 MITIGATE · 1-3 ACCEPT
```

Embed in plan:

```markdown
## Risk
| # | Risk | Score | Mitigation |
|---|------|-------|------------|
| 1 | [risk] | 6 | [concrete mitigation + owner] |
```

**Stack-specific failure modes** (generic — adapt from `${rulesDir}/layer-map.md` + `${rulesDir}/stability.md`): FK missing index → add in same migration · validator drift → derive from ORM/schema gen · unverified webhook signature → verify secret, fail closed · DB cold-start → pooled/serverless driver · non-idempotent payment handler → idempotency key on provider event ID · stale cache → invalidate on write / short TTL · snapshot drift → regenerate + review · lockfile skew → commit with same PM version · missing env var → document in `.env.example`, fail-fast.

**ADR (≤15 lines, L6+ with multiple valid approaches):**

```markdown
### ADR: [Title]
**Context:** [problem + why decision needed]
**Options:** A) [option] / B) [option]
**Decision:** [X] because [reason]
**Consequences:** [consequence], [trade-off]
```

Place ADRs before the Tasks section in the plan. **Checklist:** 5+ failure modes brainstormed · top 3 risks with mitigations · score ≥ 7 has a rollback path · stack-specific failures checked · cardinal-rule violations checked · ADR for architectural decisions.

## Sprint contracts (L6+)

Full template, mini-variant (L3-L5), and worked example → `loop-engineering.md § Sprint Contracts`. Negotiated between planner and evaluator BEFORE implementation; evaluator approves first.

---

## Stopping conditions

| Condition | Action |
|---|---|
| evaluator FAIL 3× on same plan | Escalate; plan likely has architectural problem |
| Disjoint-file check fails after 2 splits | Downgrade phase to SEQUENTIAL |
| Spawn count per phase > 5 after split | Split phase into two phases |
| User requests scope expansion | Loop back to Phase A — re-brainstorm before re-planning |

## Anti-patterns

| Bad | Good |
|---|---|
| "Implement feature X" as a task | TDD-shaped: write test → fail → minimal code → pass → verified working-tree checkpoint |
| Two PARALLEL tasks edit the same shared module (logger, db handle, global stylesheet) | Downgrade phase to SEQUENTIAL |
| "Files touched: TBD" | Full paths or task is not ready |
| Acceptance: "looks correct" | Acceptance: `${tooling.commands.test}` scoped to `patternName` passes |
| No verification phase | Always include `/verify quick` + `/evolve auto` |
| Skip `[SEQUENTIAL]`/`[PARALLEL-SAFE]` markers | Markers mandatory — `/implement` parses them |
| Agent: <empty> | Default `main`, or pick from `dispatch-matrix.md` |
| Plan invents layers the project doesn't have | Verify against `references/layer-map.md` |
| Full sprint contracts for L3-L5 | Atomic task blocks suffice; sprint contracts L6+ only |
