# Phase C — Executing-plans

> Sequential guide for the third phase of the planning chain.
> **Direct-invokes `superpowers:subagent-driven-development` as the engine** (doctrine: fresh subagent per task + two-stage review + continuous execution), executed through this plugin's `/implement` orchestrator. For inline/batch execution, the engine is `superpowers:executing-plans` instead.
> The subagent prompt templates (implementer / spec-reviewer / code-quality) are inlined in the § Subagent prompt templates appendix below.

---

## Entry contract

- Phase B complete. Plan at `${paths.planDir}/<file>`, GATE-2-approved + user-approved.
- Task tier is **L5+** (L4 stops at Phase B with plan ready; user invokes `/implement` manually).
- Branch is `${git.workBranch}`. **NEVER work on a protected branch.**

## Exit contract

- All plan tasks verified in the working tree with PASS from both reviewers.
- `/verify quick` PASS. `/evolve auto` ran. `.graph-powers/logs/progress.md` has a new row.
- Stop at "reviewed working tree ready". Git actions remain separate and require explicit authorization in the current turn. **NEVER auto-merge.**

---

## Loop contract

> Phase C is a goal-gated loop, run per task. Model: `references/loop-engineering.md`.

- **trigger:** Phase B complete (plan GATE-2-approved + user-approved), tier L5+, branch `${git.workBranch}`.
- **goal (binary):** *per task* — implementer PASS **AND** GATE A spec PASS **AND** GATE B quality PASS **AND** working-tree checkpoint recorded; *overall* — all tasks done **AND** `/verify quick` PASS **AND** `/evolve auto` done.
- **body:** implementer (2a) → GATE A spec review (2b) → GATE B quality review (2c) → working-tree checkpoint (2d). `/verify quick` (Step 5) is the closing verifiable check across the whole plan.
- **guards:** HARD-STOP 3 retries per task → escalate · COST-GUARD spawn cap 5 per `/implement` batch · CTX-GUARD reset > ~80K (`loop-engineering.md § Context Reset Protocol`) · seq-think gate before the 3rd retry (Step 4.5).
- **terminal:** overall goal PASS → "reviewed working tree ready", stop. Any guard trips → escalate. Stage, commit, push, PR, and merge require separate user authorization. **Never auto-merge.**

---

## Step 1 — Invoke engine + /implement

**Invoke `Skill("superpowers:subagent-driven-development")`** first (loads the doctrine: read plan once, per-task implementer → spec review → quality review, continuous execution). Then drive it through `/implement`:

```
/implement ${paths.planDir}/<file>
```

`/implement` already parses `[SEQUENTIAL]` / `[PARALLEL-SAFE]` markers and the per-task `Agent:` + `Skill load:` fields written in Phase B. The plan format from `phase-b-writing-plans.md` is exactly its expected input. The engine supplies the *why* (two-stage review order, no inter-task pause); `/implement` + the steps below supply the *how* (which agents, branch policy, `/verify`, `/evolve`). Phase C's role from here is **enforcement**.

## Step 2 — Per-task subagent driver

For every task in plan order (respecting `[SEQUENTIAL]` / `[PARALLEL-SAFE]` markers):

### 2a — Implementer dispatch (fresh subagent, foreground, write-capable)

```ts
Agent({
  subagent_type: <Agent: field from task>,
  prompt: <filled § Subagent prompt templates → Implementer — paste task block + scene context>,
})
```

- Subagent does NOT read the plan file — only its task block.
- Subagent returns PASS / FAIL / BLOCKED per the Implementer return contract.

### 2b — GATE A — spec-compliance reviewer (fresh subagent, foreground). Run ONLY if 2a returned PASS.

```ts
Agent({
  subagent_type: "graph-powers:evaluator",
  prompt: <filled § Subagent prompt templates → Spec reviewer — paste spec excerpt + implementer's diff>,
})
```

- PASS → 2c. FAIL → append "Missing items" to the task block under `## Reviewer feedback`, re-dispatch 2a (max 3 retries per task across both gates). BLOCKED → halt, escalate.

### 2c — GATE B — code-quality reviewer (fresh subagent, foreground). Run ONLY if 2b returned PASS.

```ts
Agent({
  subagent_type: "graph-powers:evaluator",
  prompt: <filled § Subagent prompt templates → Code-quality reviewer — paste implementer's diff>,
})
```

- Nits are FYI only, do NOT re-dispatch. Only rule/anti-pattern citations trigger re-dispatch.
- PASS → 2d. FAIL → append violations, re-dispatch 2a (counter shared with 2b). 3rd FAIL → escalate, do not auto-retry.

### 2d — Working-tree checkpoint

Both reviewers PASS → record changed paths, validation evidence, the current base `HEAD`, and the suggested conventional-commit subject. Confirm no files outside the task scope changed, leave all changes unstaged, and proceed to the next task. Never stage or commit without explicit authorization in the current turn.

## Step 3 — Continuous execution (no inter-task pause)

Per superpowers' subagent-driven rule: *"Do not pause to check in between tasks. Execute all tasks without stopping. Only stop on: BLOCKED you cannot resolve, ambiguity that prevents progress, or all tasks complete."* Surface progress in status updates, not approval requests.

## Step 4 — Parallel batch dispatch (inside `[PARALLEL-SAFE]` phases)

1. **Count tasks.** > 5 → split into two batches.
2. **Single message, multiple Agent calls.** All implementer dispatches fire in one assistant turn.
3. **Wait for all returns** before starting any GATE A/B.
4. **Integration check on merged diffs:** the project's `tooling.commands.typeCheck` then `tooling.commands.lint`, run from the repository root. Cross-task failures → resolve sequentially in a new SEQUENTIAL task, do NOT re-dispatch the batch.
5. **Run GATE A + B per task** (not per batch).
6. **On any task FAIL → re-dispatch only that one task.**

## Step 4.5 — Reasoning gate before escalation (L5+)

When a task fails its **2nd** retry, invoke `mcp__sequential-thinking__sequentialthinking` to decompose the error surface (root cause, why prior fixes missed, candidate paths) **before** the 3rd attempt or `/debug recover`. Prevents a blind 3rd retry burning the spawn cap.

## Step 5 — Post-execution gate

After every plan task PASS, run `/verify quick`. The gate commands are the ones the project
declared in `tooling.commands` — type check, lint, format on the touched files, then tests. A gate
the project did not declare is reported as `NOT DECLARED`, never as passing.

Plus the negative checks the project's rules define (`${rulesDir}/`) — things like "no hardcoded
colour outside tokens", "no stray debug logging", "no CRLF", "no foreign key without an index". If
UI changed and the project has a staging URL → browser E2E per `Skill("webapp-testing")`.

## Step 6 — Auto /evolve

On `/verify quick` PASS, run `/evolve auto`: captures learnings · updates `${CLAUDE_PLUGIN_ROOT}/skills/<relevant>` if patterns crystallized · may append a row to `.graph-powers/logs/progress.md` with the base `HEAD` plus working-tree status. `/evolve auto` must not stage or commit changes without explicit authorization in the current turn.

## Step 7 — Branch finalization message

```
Phase C complete.
- All plan tasks reviewed in the working tree
- /verify quick PASS
- /evolve auto done; progress.md updated
- Base HEAD: <SHA>
- Suggested commit subject: <subject>
- Working tree ready for user review. Stage/commit/push/PR/merge require separate authorization.
```

**STOP.** Do not push, do not open PR, do not merge.

---

## Stopping conditions

| Condition | Action |
|---|---|
| 3 reviewer rejections on same task | Escalate to user, halt plan |
| 5 spawn cap hit mid-phase | Checkpoint with user before 6th |
| BLOCKED from implementer or reviewer | Halt task, escalate, do not retry |
| `/verify quick` FAIL after task PASS | Halt, investigate (likely cross-task interaction); do NOT auto-fix in `/implement` loop |
| Parallel batch returns mixed PASS/FAIL | Integrate PASS diffs, re-dispatch FAIL only |
| Same hypothesis fails 3× | Escalate to `graph-powers:evaluator` Mode 3 |
| User typed "stop" or "wait" | Halt immediately, do not finish current task |

## Parallel dispatch contract (single-message rule)

ALL implementer Agent calls in ONE message → then ALL GATE A reviewers in ONE message (after all implementers return) → then ALL GATE B reviewers in ONE message (after all GATE A PASS). Never interleave dispatch + collection.

## Anti-patterns

| Bad | Good |
|---|---|
| Pause between tasks for user approval | Continuous execution; only stop on BLOCKED |
| Run GATE B before GATE A | Spec compliance FIRST. Code quality on a spec-failing diff wastes tokens. |
| Re-dispatch entire parallel batch on one task FAIL | Re-dispatch only the failed task |
| Any stage/commit/push without current-turn approval | STOP at reviewed working-tree changes. User decides Git actions. |
| `gh pr merge --auto` | NEVER. Branch policy. |
| Skip `/evolve` after success | Mandatory — Cardinal Rule #4 |
| Use `--no-verify` to bypass hooks | NEVER. Fix root cause, restart from gate 1. |

---

## Subagent prompt templates

> Fill `{{...}}` placeholders per dispatch. Shared contract first, then one block per gate. All three return < 2000 tokens; detail to `.claude/agent-memory/<agent>/` if large.

### Shared dispatch contract

- **One task = one fresh subagent.** No context carry-over between tasks.
- **Subagents receive pasted content, not file paths** — paste the task block / spec excerpt / diff inline; do not assume the subagent reads files (except the implementer, which reads its own `Files touched`).
- **Gate order:** implementer (write-capable, foreground) → spec reviewer (read-only) → code-quality reviewer (read-only). Code-quality runs ONLY after spec PASS.
- **Re-dispatch:** FAIL with feedback → append to the task block under `## Reviewer feedback`, re-dispatch implementer. **Max 3 retries per task across both gates.** BLOCKED → halt, escalate.

### Implementer (write-capable)

```
You are an implementer subagent for `${project.name}`.

## Scene context (read once, do not re-derive)

Fill these from the project config before dispatching — a subagent inherits nothing, so anything
left as a placeholder here is a fact the implementer will invent.

- Repo: `${project.name}`. Working branch: `${git.workBranch}` (never a protected branch; never push; never auto-merge).
- Stack: `${project.stack}`. Package manager: `${tooling.packageManager}` — and no other.
- Tests: `${tooling.commands.test}`. Type check: `${tooling.commands.typeCheck}`. Never substitute a different tool.
- Line endings: LF only. Before handoff: `${tooling.commands.format}` on every edited file.
- The project's own invariants from `${rulesDir}/` that match the touched paths.

## Your task
{{task block from plan — verbatim: title, acceptance, Files touched (full paths), numbered Steps, Skill loads, Estimated time}}

## What you MUST do
1. Read each file in "Files touched" before editing.
2. Follow the steps in order; do not skip TDD steps (failing test → RED → implement → GREEN).
3. Run `${tooling.commands.format}` on every file you edit before declaring done.
4. Record the suggested conventional-commit subject from your task block; leave all files unstaged.
5. Return the structured report below.

## What you MUST NOT do
- Read the plan file or other task blocks (your work is self-contained).
- Edit files outside "Files touched" (need to → STOP, return BLOCKED).
- Skip the format/type-check/lint gates. Stage, commit, push, open PRs, or merge.
- Use `--no-verify` or `git commit --amend`. Introduce hardcoded hex, console.log, or `as any`.

## Return contract (< 2000 tokens)
### Status        PASS | FAIL | BLOCKED
### Changed paths  - path/to/file …
### Validation evidence  - type-check: <result> · lint: <result> · test (scoped): <result> · format: <result>
### Git state      base HEAD <short SHA> · suggested subject <conventional-commit subject> · unstaged YES/NO
### Summary        2-5 sentences: what you did + why the acceptance criterion is met.
### Next           (empty if complete; populate only if BLOCKED — what's blocking)
```

### Spec reviewer (read-only — GATE A)

```
You are a spec-compliance reviewer for `${project.name}`. Verify the diff fulfills the spec excerpt — nothing else.
You are NOT reviewing code quality, style, naming, comments, or test design.

## Spec excerpt            {{paste exact spec section + acceptance criterion}}
## Implementer's diff      {{paste full diff}}
## Claimed validation      {{paste implementer's Validation evidence + Git state + Summary}}

## What to check
1. Acceptance criterion met — exactly what it specifies, no more, no less.
2. Files touched match the spec (no surprise files).
3. No scope creep (no "while I was here" refactors / extra features / unscoped fixes).
4. No silent omissions — every sub-item of the criterion appears in the diff.
5. Validation actually proves the criterion (type-check passing alone is not enough — need test/probe/schema evidence).

## Return contract (< 1000 tokens)
### Verdict                 PASS | FAIL | BLOCKED
### Acceptance criterion    Criterion: <restate> · Met? YES/NO/PARTIAL · Evidence: <diff lines / test result>
### Scope-creep check       PASS / FAIL — <name out-of-scope changes if FAIL>
### Missing items (if FAIL) - <gap the spec asked for that the diff doesn't deliver>
### Recommendation          PASS → "Proceed to code-quality reviewer." · FAIL → "Re-dispatch implementer with gaps as `## Reviewer feedback`." · BLOCKED → describe blocker.
```

### Code-quality reviewer (read-only — GATE B)

```
You are a code-quality reviewer for `${project.name}`. The diff already passed spec compliance — do NOT re-check the spec.
Catch maintainability, project conventions, security, testability, anti-patterns.

## Project rules to enforce (each violation = FAIL)
1. No hardcoded hex in UI (semantic tokens only).   2. No `console.log` in production paths.
3. No `as any` in new code (use `unknown` + narrow). 4. No CRLF (LF only).
5. FK index for every new FK column (same migration). 6. Shared logger only (no bare `console.*` in services).
7. Validation schemas at module level, not inside handlers. 8. New routers registered in the entry index.
9. Webhooks idempotent (upsert / idempotency-key).    10. Webhook handlers fire-and-forget external calls (`void dispatchX(...)` after DB writes, never await inline).
11. No `--no-verify`, stage, commit, or push.           12. Suggested conventional-commit scope matches changed paths.

## Implementer's diff      {{paste full diff}}

## Also check
- Anti-patterns from `Skill("debugger") → ../../debugger/references/anti-patterns.md` if relevant to touched files.
- Test design (tests exist + exercise the criterion, not mocked away). Error handling at boundaries. Self-descriptive naming, reasonable function size, no premature abstraction. Comments only for non-obvious WHY. No backwards-compat shims. Security boundaries (no SQLi/XSS/command injection; auth scope correct).

## Return contract (< 1500 tokens)
### Verdict             PASS | FAIL | BLOCKED
### Rule check          - Rule N (<name>): PASS/FAIL — <evidence>   (list only rules the diff touches)
### Anti-pattern check  PASS / FAIL — <name the anti-pattern if FAIL>
### Test design check   PASS / FAIL — <name the gap>
### Nits (FYI only)     - <nit>   (never triggers re-dispatch alone)
### Recommendation      PASS → "Working-tree checkpoint complete." · FAIL → "Re-dispatch implementer with violations as `## Reviewer feedback`." · BLOCKED → describe blocker.
```
