---
description: "Decide how to build a multi-step feature before code: scope, architecture trade-offs, integrations, ordering, GitHub issue triage, and implementation plans. Uses the planning skill as the single method source, prefers ultra-plan at L4+, and falls back to the same phases inline. Do not use to execute an existing plan or fix a known bug."
workflow_type: prompt-chaining
---

# /plan

Deterministic entrypoint for `Skill("graph-powers:planning")`. The skill and its references own Step 0,
brainstorming, plan authoring, task grammar and review. This command does not restate them; it only
passes arguments, selects the workflow accelerator when available, and holds the human gate a
workflow cannot ask for.

**ARGUMENTS:** $ARGUMENTS

Read, in order:

1. `${CLAUDE_PLUGIN_ROOT}/references/shared/000-config-loader.md`
2. `${CLAUDE_PLUGIN_ROOT}/references/shared/005-method-bootstrap.md`
3. `.graph-powers/config.json`
4. the root `PRODUCT.md`, when present, as scope authority

Then invoke:

```text
Skill("graph-powers:planning")
```

Empty arguments → ask what to plan. The arguments are otherwise either a task description or a
resolvable GitHub issue reference; `Skill("graph-powers:planning") § Step 0` owns that distinction and the
ambiguous bare-word case.

## 1. Establish the planning contract

Run `Skill("graph-powers:planning") § Step 0` before choosing a route. Read only the reference that branch names:
`step-0-inventory.md`, `issue-triage.md` or `wayfinding.md`. Its Destination, Reuse ledger,
Regression watchlist, Out of scope and Not yet specified blocks are binding inputs downstream.

KISS and YAGNI are gates, not style notes: reuse before extend before new; no task, abstraction,
option or compatibility path without a current requirement or named consumer. Research only enough
to decide the next branch. No design, code or file write happens inside Step 0.

## 2. Route once

Follow the tier and fog routes in `Skill("graph-powers:planning") § Step 0`:

- fog-dominated → map mode, write only the map, then stop;
- L1-L2 → direct path, no workflow or plan file;
- L3 → Phase A light, inline design and approval, no plan file;
- L4+ → prefer `graph-powers:ultra-plan`; fallback to Phase A + B in the skill.

For L4+, attempt once:

```typescript
Workflow({ name: 'graph-powers:ultra-plan', args: { task: scopeLockedTask, config } })
```

`scopeLockedTask` is the original scope plus the exact Step 0 handoff blocks. Use the template in
`${CLAUDE_PLUGIN_ROOT}/skills/planning/references/issue-triage.md § FF-6`; task mode uses the same
shape with no issue-only rows. Pass the config object already loaded, plus `pluginRoot`.

Three outcomes take the same fallback: no `Workflow` tool, the workflow name does not resolve, or it
returns `skipped: true`. State which occurred, do not retry the name, and run
`Skill("graph-powers:planning")` Phase A + B directly. The route changed; the plan contract did not.

## 3. Verify the returned plan

For a workflow return, require a real `planPath`, open that file, then run
`${CLAUDE_PLUGIN_ROOT}/skills/planning/references/phase-b-writing-plans.md § Step 6` against the
exact Step 0 handoff blocks and the workflow's chosen approach. If the workflow also returns a
`specPath`, use that spec as an additional authority; do not require one from a route that only
writes `PLAN.md`. In issue mode also run
`${CLAUDE_PLUGIN_ROOT}/skills/planning/references/issue-triage.md § FF-8`. Treat
`approved !== true`, a missing file, a failed contract row, a task
serving Out of scope, or an execution-graph edge with no payload as `NEEDS_WORK`; correct the plan
before offering execution.

For the direct Phase A + B fallback, GATE 1, Step 6, and GATE 2 when the tier requires it are the
equivalent evidence. Do not run a second review merely because the accelerator was unavailable.

## 4. Human gate

Print only the decision payload:

- destination;
- chosen approach;
- plan path and task count;
- open decisions and `[ASSUMED]` rows;
- plan review verdict.

Then stop and ask for explicit approval. Silence is not approval. `--plan-only` always ends here.
An L4 plan also ends here; execution starts later through `/implement`.

## 5. Execute only when this chain includes Phase C

At L5+ after explicit approval, follow
`${CLAUDE_PLUGIN_ROOT}/skills/planning/references/phase-c-executing-plans.md`.

- Workflow route: write `.graph-powers/logs/write-lease.json` from the returned `writeLease` or the
  union of task `Owns`, run `graph-powers:ultra-build`, then `graph-powers:ultra-verify`, and remove
  the lease when the chain ends.
- Direct fallback: run `/implement <plan dir>`, then `/verify quick`.

An unresolved `ultra-build` or `ultra-verify` name is the same route decision as Step 2: state it
once, do not retry, and use the command fallback. A capped or non-green verification result is not
completion.

Stop at reviewed working-tree changes. Stage, commit, push, PR and merge remain separate actions and
each needs the user's authorization in the current turn. Never auto-merge.
