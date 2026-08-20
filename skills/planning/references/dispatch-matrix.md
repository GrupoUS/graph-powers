# Dispatch matrix — planning-specific routing rules

> Lookup for **Phase B writing-plans**: how to fill each task's `Agent:` / `Skill load:` / `Mode:`.
> **Canonical skill↔agent pairing lives in `${CLAUDE_PLUGIN_ROOT}/references/shared/030-agent-assignment-matrix.md` (agent matrix) and `§ 6` (skill-to-domain matrix).** This file keeps only the planning-unique operational rules; it does not restate those tables.

---

## Hard rules (planning-unique)

1. **Disjoint-file rule.** Two write-capable agents NEVER edit overlapping paths in parallel. Phase B self-review enforces it (`phase-b-writing-plans.md § Step 3`). Split by directory, route, or component family.
2. **Read-only agents background.** `graph-powers:explorer`, `graph-powers:librarian` MUST run `run_in_background: true`; `graph-powers:verification` too when alongside write-capable agents.
3. **Caps.** 5-spawn cap per `/implement` invocation (beyond 5 → checkpoint with user); 3-attempt cap per hypothesis (same failure 3× → escalate to `graph-powers:evaluator` Mode 3).
4. **Return budget < 2000 tokens.** Detail to `.claude/agent-memory/<agent>/`, summary index returned to main.
5. **Subagent non-inheritance.** Agents do NOT auto-load project `CLAUDE.md` — embed critical rules in the agent prompt body or task block.

> Full stopping-conditions table: `../SKILL.md § Stopping & red flags`, plus the phase-specific
> rows in `phase-c-executing-plans.md § Stopping conditions`.

---

## Parallel-safety by path (the planning-unique decision)

Pick the agent and skill from `${CLAUDE_PLUGIN_ROOT}/references/shared/030-agent-assignment-matrix.md` and `${CLAUDE_PLUGIN_ROOT}/references/shared/060-skill-domain-matrix.md`; this column is what writing-plans needs that those tables do not carry:

| Path / signal | Parallel-safe? |
|---|---|
| `${paths.frontendRoot}/**`, component/page/dialog/form files | **YES if disjoint files** |
| `${paths.backendRoot}/**` routers, services, webhook handlers | YES if disjoint routers/services/webhooks |
| `${paths.schemaRoot}/**` schema + migrations | **NEVER parallel** (FK + index ordering) |
| `${paths.backendRoot}/_core/**` singletons · `${paths.stylesRoot}/**` global styles · any shared package | **NEVER parallel** (shared module) |
| Mobile app root (if the project has one), `*.{kt,swift,kts}` | YES if disjoint platforms |
| Perf / bundle / Lighthouse / CWV | Generally no |
| Staging E2E / agent-browser | **NEVER parallel** (single browser session) |
| Plan / PRD synthesis · adversarial review · architecture analysis | No |
| Codebase lookup (`graph-powers:explorer`) · external research (`graph-powers:librarian`) | **YES — and always background** |
| Phase A research dispatch (every L4+) | **ALWAYS parallel** (`graph-powers:explorer` + `graph-powers:librarian`, background) |

> **Ambiguous (task touches 2+ domains):** `mcp__sequential-thinking__sequentialthinking` to rank agent fit by primary impact area before filling `Agent:` (L5+ MUST · L4 SHOULD).

---

## Phase decision tree

```
Task → classify signal
  ├─ Read-only (research, lookup) → background agent, parallel OK
  ├─ Write ${paths.frontendRoot}/** → frontend-specialist + the project's design rule
  ├─ Write ${paths.schemaRoot}/**   → main, NEVER parallel
  ├─ Write ${paths.backendRoot}/**  → main / debugger + domain skill
  ├─ Write the mobile app root      → mobile-developer
  ├─ Perf / security           → performance-optimizer
  ├─ Browser E2E               → verification (foreground, single session)
  ├─ Review / audit            → evaluator (Mode 1/3/4)
  └─ Plan synthesis            → project-planner
```

---

## Return contract (every parallel batch)

```
Each parallel subagent returns:
  - Status: PASS | FAIL | BLOCKED
  - Changed paths: [list]
  - Validation evidence: [test output / type-check / lint result]
  - Summary: < 2000 tokens
  - Memory write: .claude/agent-memory/<agent>/<task-id>.md
```

Controller integration: read every summary → verify no overlapping changed paths (disjoint-file check) → `${tooling.commands.typeCheck}` + `${tooling.commands.lint}` on the integrated diff → any FAIL/BLOCKED → halt phase, escalate or re-dispatch the failed task only → all PASS → record a reviewed working-tree checkpoint. Stage/commit/push only when the user explicitly authorizes that Git action in the current turn.

## When NOT to parallelize

Failures are **related** (one root cause — fix one reruns the others) · tasks share state (schema module, cross-cutting singletons, single browser session) · spawn count would exceed 5 · subagent return would exceed 2000 tokens · user typed "one at a time" / "sequential".
