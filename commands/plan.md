---
description: "Decide how to build a multi-step feature before code: scope, architecture trade-offs, integrations, ordering, issue triage and implementation plans. Routes all planning through the planning skill. Do not use to execute an existing plan or fix a known bug."
workflow_type: prompt-chaining
---

# /plan

`/plan` is the adapter for `Skill("graph-powers:planning")`. Discovery, tiering, design, task
grammar, TDD status and plan review live in that skill and its references; this command does not
duplicate them.

**ARGUMENTS:** $ARGUMENTS

## 1. Load context

Read, in order:

1. `${CLAUDE_PLUGIN_ROOT}/references/shared/000-config-loader.md`
2. `${CLAUDE_PLUGIN_ROOT}/references/shared/005-method-bootstrap.md`
3. `.graph-powers/config.json`
4. `PRODUCT.md` at the repository root, when present

Then invoke `Skill("graph-powers:planning")` with the original arguments and loaded project
config. Empty arguments ask what to plan; a GitHub issue is triaged by the skill when applicable.

## 2. Route the planning chain

Let the skill own Step 0 and the fog/tier route. L1-L2 stay direct, L3 uses the light Phase A
route, and L4+ uses Phase A → Phase B. When `graph-powers:ultra-plan` is available, it may
accelerate L4+ planning; otherwise the skill runs the same phases inline. Do not retry an unresolved
accelerator or invent a second route.

## 3. Human gate

Before execution, show only the destination, chosen approach, plan path and task count, open
decisions or `[ASSUMED]` rows, and the plan-review verdict. Wait for explicit user approval. An
L4 plan or `--plan-only` stops here.

## 4. Continue approved L5+ plans

For L5+, the chain is `ultra-plan → /implement → /verify`; `/implement` invokes the planning
skill's Phase C and owns execution. Stop at reviewed working-tree changes; staging, commit, push,
PR and merge require separate user approval.
