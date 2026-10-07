---
description: "Implement an objective or approved plan by tier: direct edit, one writer, or the L4+ Gauntlet profile. Only --dry-run; /plan decides, /verify confirms."
workflow_type: prompt-chaining
---

# /implement

**ARGUMENTS:** $ARGUMENTS: a plan path, an objective, or empty.

Read `${CLAUDE_PLUGIN_ROOT}/references/shared/000-config-loader.md`, `${CLAUDE_PLUGIN_ROOT}/references/shared/007-path-conventions.md`, and `.graph-powers/config.json`. Only `--dry-run` is valid; reject other flags, including `--codex`, `--sprint=N` and `--review-only`.

## 1. Select the input

A path argument is the plan (directory → `PLAN.md`); one that does not resolve stops at `/plan` and
never becomes an objective. Other text is the objective, even when plans exist. Only empty input
falls back, in order, to an unambiguous active session/handoff binding to this project and plan, a
unique current or legacy plan under `${paths.planDir}`, then an approved conversation plan (by its
declared tier; L1-L3 runs as an objective); otherwise ask what to implement. Exclude
spec/map/handoff records. Resolve real paths against the current Git worktree; reject escaping
symlinks, external/nested repositories and sibling worktrees. An invalid binding stops without
fallback; multiple candidates need one selection question; never select by mtime or lease.

## 2. Route by tier

A plan's tier comes from the validator (§ 3); an objective's from
`${CLAUDE_PLUGIN_ROOT}/references/shared/020-complexity-routing.md`, the lower tier when unsure.
The table is the contract: run only the row and the phase it names.

| Input | Route | Agents | Closes with |
|---|---|---|---|
| L1-L2 | Main-thread edit; a plan's tasks run in order on their own `CHECK` | none | the focused `CHECK` |
| L3 objective | Implement directly, no plan file; one question only if it changes scope | none, or one writer from `${CLAUDE_PLUGIN_ROOT}/references/shared/030-agent-assignment-matrix.md` | focused `CHECK`; `/verify quick` when a gate is declared |
| L3 plan | Phase C, default profile | its writer lane; Phase C's final evaluator | `/verify quick` |
| L4+ objective | Hand off once to `/plan --plan-only` and stop | none here | the approved plan |
| L4+ plan | Phase C with `profile: gauntlet` | writer lanes; one `graph-powers:evaluator` per wave (+ § 3 bind review) | `/verify loop`, then `/evolve auto` on PASS |

No row calls a second planner, chains A → B → C in one turn, or runs `/evolve` before PASS. L1-L3
never run an evaluator per wave or `/verify loop`.

## 3. Plans

```text
python -X utf8 "${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/sdd.py" validate <PLAN_FILE> --max-tasks <graphGuardrails.maxTasksPerPlan>
```

Exit 2/invalid/legacy or missing approval routes to `/plan`; never infer fields or try another
candidate. A conversation plan is materialized once at the canonical path, only for a non-dry L4+ run.

Only for a non-dry L3 plan, invoke `Skill("graph-powers:planning")` and read `${CLAUDE_PLUGIN_ROOT}/skills/planning/references/phase-c-executing-plans.md` without a profile.

Only for an L4+ plan, read `${CLAUDE_PLUGIN_ROOT}/skills/planning/references/gauntlet-loop.md`, apply its hole check, then:

```text
python -X utf8 "${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/sdd.py" validate <PLAN_FILE> --max-tasks <graphGuardrails.maxTasksPerPlan> --profile gauntlet
python -X utf8 "${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/sdd.py" review-check <PLAN_FILE>
```

Invalid or `REVISION_REQUIRED` routes to `/plan`. `UNREVIEWED` or `STALE` (exit `4`) gets one fresh
`graph-powers:evaluator` Mode 1 review, bound by `review-bind`
(`${CLAUDE_PLUGIN_ROOT}/skills/planning/references/phase-b-writing-plans.md` § Step 7); anything but
`APPROVED` stops at `/plan` without a lease.
Only on exit `0` or `APPROVED`, invoke `Skill("graph-powers:planning")` Phase C with `profile: gauntlet`.

## 4. Dry-run

Report input, tier and route. For a plan, validate read-only (L4+ also with the profile and
`review-check`) and list tasks, `Owns`/`Needs`, waves, distinct `builder` and `inspector` roles,
caps and the closing command. No question, materialization, bind, lease, workspace, write or spawn;
an objective dry-run also runs no investigation or check.

Preserve the tree; return reviewed, unstaged evidence. Git/publication needs separate action/scope authorization.
