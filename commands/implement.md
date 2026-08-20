---
description: Execute implementation plans. Parses plan for phase structure + agent assignments, loads domain skills, spawns specialists, orchestrates parallel/sequential execution with sprint contract gates.
workflow_type: orchestrator-workers
---

# /implement

**ARGUMENTS**: $ARGUMENTS

> **Read before step 0 — never reconstruct these from memory:** `${CLAUDE_PLUGIN_ROOT}/references/shared/000-config-loader.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/005-superpowers-bootstrap.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/007-path-conventions.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/010-quality-gates.md`
> Read `${CLAUDE_PLUGIN_ROOT}/references/shared/015-verification-gate.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/020-complexity-routing.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/030-agent-assignment-matrix.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/060-skill-domain-matrix.md`
> Read `${CLAUDE_PLUGIN_ROOT}/references/shared/070-parallel-agent-spawn.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/080-sequential-phase-gating.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/120-skill-invocation-order.md`

> **Plans come from:** `Skill("superpowers:writing-plans")` (canonical format, written to `${paths.planDir}/`) chained with `Skill("planning")` for this project layer-map — both loaded only when no plan exists and this command has to write one first.
> **Plan files:** `${paths.planDir}/YYYY-MM-DD-<feature>-plan.md` (per `${CLAUDE_PLUGIN_ROOT}/references/shared/007-path-conventions.md`) or active conversation context. Legacy `docs/plans/*.md` accepted for back-compat.

---

## 0. Pre-flight

```typescript
Skill("superpowers:using-superpowers");   // meta — bootstrap (per `${CLAUDE_PLUGIN_ROOT}/references/shared/005-superpowers-bootstrap.md`)
```

Use the file-search tool to locate `${paths.planDir}/*.md` (preferred) and `docs/plans/*.md` (legacy). Do not rely on shell globbing or stderr redirection for this check.

| Source | Action |
|---|---|
| Plan file exists | `Skill("superpowers:executing-plans")` — parse phases + TodoWrite seed |
| Plan in chat context | `Skill("superpowers:executing-plans")` — extract phases + tasks from conversation |
| No plan found | `Skill("superpowers:writing-plans")` → `Skill("planning")` — write plan to `${paths.planDir}/`. Never implement without a plan. |

Parse from plan: **Complexity**, **Layers**, phase markers (`[SEQUENTIAL]` / `[PARALLEL]`), task list (`- [ ]`), verify commands, sprint contracts, `[ASSUMED]` items to validate before starting.

For L4+ work (multi-domain or multi-file changes), invoke `Skill("superpowers:using-git-worktrees")` to isolate the workspace before any agent spawns. Skip for L1-L3 trivial work.

Read `.graph-powers/config.json` for tooling + paths. If `${rulesDir}/routing-supplements.md` exists, also read it for project-specific layer/agent routing.

**Flags:**

| Flag | Effect |
|---|---|
| `--codex` | Delegate L5+ phases to `codex:rescue` skill |
| `--sprint=N` | Execute only sprint N of multi-sprint plan |
| `--dry-run` | Parse + display task/agent assignments without executing |

---

## 1. Skill routing

Per `${CLAUDE_PLUGIN_ROOT}/references/shared/060-skill-domain-matrix.md` (Skill-to-Domain Matrix), load the skill matching the task domain **before spawning any agent for that phase**.

If the plan touches:
- Schema / migrations / data → load `graph-powers:debugger` skill and any host database skill listed in `${rulesDir}/routing-supplements.md`
- API / handlers / services → `graph-powers:debugger`
- Components / styling → the project's design rule, or its own design-system skill when it has one
- Performance / SEO → `performance-optimization`
- Skill creation / iteration → `skill-creator`
- External provider/deployment/product API → host provider skill if configured; otherwise there is no skill for this — spawn the **agent** `graph-powers:librarian`, which is a different namespace from a skill

Multiple skills may load. Process skills (`planning`, `graph-powers:debugger`) before implementation skills.

---

## 2. Agent assignment

If plan doesn't specify `**Agent:**`, assign by file-path detection:

| File-path pattern | Agent |
|---|---|
| `${paths.schemaRoot}/**` | `graph-powers:debugger` |
| `${paths.backendRoot}/**` | `graph-powers:debugger` |
| `${paths.frontendRoot}/**` (UI files) | `graph-powers:frontend-specialist` |
| `${paths.frontendRoot}/**` (logic / hooks / non-UI) | `graph-powers:debugger` |
| Cross-domain (3+ layers) | `graph-powers:project-planner` as coordinator |
| Any failing task | `graph-powers:debugger` |

If `${rulesDir}/routing-supplements.md` extends this table → respect those bindings.

Background read-only agents (always `run_in_background: true`):

| When | Agent |
|---|---|
| Before any phase — grep existing patterns | `graph-powers:explorer` |
| External API docs, package versions | `graph-powers:librarian` |

---

## 3. Execution mode (per `${CLAUDE_PLUGIN_ROOT}/references/shared/020-complexity-routing.md`)

| Complexity | Mode |
|---|---|
| L1-L2 | DIRECT — main agent executes |
| L3-L5 | SUBAGENTS — `Agent()` per task/phase |
| L6+ | COORDINATED — coordinator + specialists; use Agent Team tools only when the runtime exposes them |

---

## 4. Mode A — DIRECT (L1-L2)

1. Load skill for the task domain
2. Execute task directly in main agent
3. Run verify command
4. Gate per `${CLAUDE_PLUGIN_ROOT}/references/shared/010-quality-gates.md` (type-check)

---

## 5. Mode B — SUBAGENTS (L3-L5)

Method-layer skill load (single message at the top of Mode B):

```typescript
Skill("superpowers:subagent-driven-development");  // two-stage review (spec → quality), working-tree checkpoint per task
Skill("superpowers:dispatching-parallel-agents");  // distinct scope + shared return contract
```

### Before any phase

Spawn `graph-powers:explorer` in background to grep existing patterns relevant to this phase:

```typescript
Agent({
  subagent_type: "graph-powers:explorer",
  prompt: "Grep [domain] patterns in [paths]. Report file:line for reuse.",
  run_in_background: true
});
```

If the explorer returns conflicting or ambiguous patterns (two conventions for the same concern, unclear layer ownership), invoke `mcp__sequential-thinking__sequentialthinking` to resolve the convention hierarchy **before** spawning phase agents (L4+ MUST · L3 SHOULD).

### Sequential phase

Per `${CLAUDE_PLUGIN_ROOT}/references/shared/080-sequential-phase-gating.md` (Sequential Phase Gating).

**Hard TDD gate (L3+):** Before each task that writes code, invoke `Skill("superpowers:test-driven-development")`. The skill requires a failing test before the implementation lands. L1-L2 trivial tasks (single-line fix, exact existing pattern) are exempt — note the exemption in the task log.

```
Load domain skill
→ Skill("superpowers:test-driven-development") gate → write failing test → wait → spawn agent for task 1 → wait → run verify command → Skill("superpowers:verification-before-completion") evidence → gate
→ Skill("superpowers:test-driven-development") gate → write failing test → wait → spawn agent for task 2 → wait → run verify command → Skill("superpowers:verification-before-completion") evidence → gate
→ ...
```

### Parallel phase

Per `${CLAUDE_PLUGIN_ROOT}/references/shared/070-parallel-agent-spawn.md` (Parallel Agent Spawn). Spawn all independent tasks in **single message**:

```typescript
// Write-capable → foreground:
Agent({ subagent_type: "graph-powers:frontend-specialist", prompt: "..." })
Agent({ subagent_type: "graph-powers:debugger", prompt: "..." })
// Read-only → background:
Agent({ subagent_type: "graph-powers:explorer", prompt: "...", run_in_background: true })
```

After all complete: parse each agent's `## Context Handoff` block, consolidate changes, run phase gate, then invoke `Skill("superpowers:verification-before-completion")` to capture the gate output as evidence before marking the phase complete.

### Sprint contract gate

If plan includes sprint contracts, after all tasks in a sprint:

1. Run each `verify:` command listed in the contract's Done Definition
2. All must pass — no partial credit
3. Any failure → fix + re-run before next sprint

---

## 6. Mode C — COORDINATED (L6+)

### Coordinator pattern

Create a **coordinator task** assigned to `graph-powers:project-planner` (or use native Agent Team tools when available). The coordinator:
- Holds the full plan + sprint contracts
- Delegates domain tasks via `SendMessage`
- Validates `## Context Handoff` from each specialist against the contract
- Gates sprints before advancing
- Reports progress + blockers

If native team tools exist, create the coordinator and dependent specialist tasks there. Otherwise, spawn the coordinator as a foreground subagent and have the main agent enforce phase gates between specialist calls.

### Coordinator prompt template

```
You are the coordinator for implementing [feature].

Plan: [paste plan content or docs/plans/[slug].md]
Sprint contract: [paste Sprint N contract]
Skill loaded: [skill name for this domain]

Responsibilities:
1. Delegate data/API tasks to debugger agent through the available runtime mechanism
2. Delegate UI tasks to frontend-specialist only after required upstream gates pass
3. Validate each agent's Context Handoff against contract Done Definition
4. Run quality gate after each phase: ${tooling.packageManager} run ${tooling.typeChecker}
5. If any criterion fails → return detailed feedback to the responsible agent, not the user
6. Only report to user: SPRINT N COMPLETE (all criteria met) or BLOCKED: [specific failing criterion]

Do not implement yourself. Coordinate, validate, gate.
```

### Context management

| Model | Strategy |
|---|---|
| Sonnet 4.x | Context reset between sprints — write handoff artifact before each reset |
| Opus 4.6+ | Auto-compaction, continuous session — monitor for context anxiety |

Handoff artifact path: `${paths.planDir}/HANDOFF-[slug]-sprint-N.md` (same structure as `/evolve handoff` § 6).

Handoff contains: completed tasks, verified state, next sprint contract, open issues, key decisions, modified files, resume commands.

Context anxiety symptoms (Sonnet): agent rushing, skipping edge cases, accepting failures. If observed → trigger reset immediately.

---

## 7. `--codex` flag (L5+ delegation)

For implementation phases too large or complex for a standard agent:

Invoke `codex:rescue` skill with:
- Task description from the plan phase
- Sprint contract done criteria
- Relevant file paths + line references
- Verify command

Codex handles implementation. Main agent validates against the sprint contract when done.

---

## 8. Quality gates

Per `${CLAUDE_PLUGIN_ROOT}/references/shared/010-quality-gates.md`.

| When | Command |
|---|---|
| After each task | `${tooling.packageManager} run ${tooling.typeChecker}` |
| After each phase | type-check + lint |
| After sprint (if contracts) | All `verify:` commands in Done Definition |
| Final | type-check + lint + tests |

---

## 9. Failure handling

| Attempt | Action |
|---|---|
| 1st | Read error. Retry with error context added to agent prompt |
| 2nd | Invoke `graph-powers:debugger` skill. Break task into smaller subtasks |
| 3rd | Switch to `/debug recover`. Escalate to user with root-cause analysis |

Never retry blindly. Never skip a gate because a task "looks correct."

---

## Stopping conditions

- STOP if no plan exists → invoke `Skill("planning")` (or `/plan`) first
- STOP after 3rd failure on same task → invoke `/debug recover`
- STOP if agent team runs 10+ task iterations without sprint completion
- ASK if plan has `[ASSUMED]` items not yet validated
- ASK before destructive operations (schema drops, data deletion)

---

## 10. Cleanup (Coordinated Runs)

After all sprints complete, collect final handoffs, close any runtime-native team resources if they were created, and leave no background research task uncollected.

---

## 11. Completion

Final gate: `Skill("superpowers:verification-before-completion")` — capture full stdout + exit code of type-check / lint / tests; do not declare "complete" without that evidence.

When useful, append a row to `.graph-powers/logs/progress.md` with the date, phase, base `HEAD`, and working-tree status. Do not stage or commit it without explicit authorization in the current turn.

Then hand off to `/verify` for the full post-implementation pipeline (which itself invokes `finishing-a-development-branch` in Phase 10 to surface the merge/PR/keep/discard options menu).

```
Implementation complete.

Working tree reviewed and left unstaged. Git actions require separate user authorization.

Gates passed (evidence captured):
  - Type check: ok (exit 0)
  - Lint: ok (exit 0)
  - Tests: ok (N passed / 0 failed)
  - Sprint contracts: ok (if applicable)

Next: /verify   (runs the full 10-phase gate + finishing-a-development-branch menu)
```
