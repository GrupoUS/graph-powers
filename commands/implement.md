---
description: "Execute an approved implementation plan through planning Phase C. Use when the user says implement, build or execute an existing plan. Supports only --dry-run; use /plan to decide what to build and /verify to confirm the result."
workflow_type: prompt-chaining
---

# /implement

**ARGUMENTS:** $ARGUMENTS

`/implement` is a thin adapter. The execution engine, task grammar, TDD, reviewers, write lease,
correction cap and gates are owned by `graph-powers:planning` Phase C and its references. Do not
restate or replace those rules here.

## 1. Read the project contract

Read, in order:

1. `${CLAUDE_PLUGIN_ROOT}/references/shared/000-config-loader.md`
2. `${CLAUDE_PLUGIN_ROOT}/references/shared/007-path-conventions.md`
3. `.graph-powers/config.json`

Resolve the project's `${git.workBranch}`, `${paths.planDir}` and
`${graphGuardrails.maxTasksPerPlan}`. Preserve the current working tree and do not create or switch
worktrees.

## 2. Resolve the plan

Accept one plan file or plan directory in `$ARGUMENTS`. A directory resolves to `PLAN.md`. Without
an explicit path, select the one active `${paths.planDir}/*/PLAN.md` matching the request. If the
approved plan is only in this conversation, write it once to the canonical path from
`007-path-conventions.md`; do not redesign it. If no approved plan resolves, stop and route to
`/plan`.

Reject `--codex`, `--sprint=N` and every unknown flag as invalid arguments. The only supported flag
is `--dry-run`; it may accompany a plan path.

## 3. Validate and route

Run the canonical validator before execution:

```text
python -X utf8 "${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/sdd.py" validate <PLAN_FILE> --max-tasks <graphGuardrails.maxTasksPerPlan>
```

Invalid or legacy unstructured plans return exit `2` and route back to `/plan`; do not infer missing
fields. A valid result is normalized JSON containing `tasks`, executable phase `gates` and
`writeLease`.

For `--dry-run`, display the plan, task count, phase gates, `Owns`/`Needs`, agent routing and the
proposed lease, then stop. Do not create a workspace, write a lease or dispatch an agent.

## 4. Invoke Phase C

For a valid non-dry run, pass the plan and validator result to
`Skill("graph-powers:planning")` →
`${CLAUDE_PLUGIN_ROOT}/skills/planning/references/phase-c-executing-plans.md`. Phase C owns all
workspace, lease, dispatch, review, correction and final-gate behaviour. Return its evidence and
stop at reviewed working-tree changes; stage, commit, push, PR and merge remain separate user
actions.
