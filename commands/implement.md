---
description: "Execute an approved implementation plan through planning Phase C. Supports only --dry-run; use /plan to decide and /verify to confirm."
workflow_type: prompt-chaining
---

# /implement

**ARGUMENTS:** $ARGUMENTS. `graph-powers:planning` Phase C owns execution, TDD, leases, dispatch, review, correction and gates; this command only resolves and validates the plan.

Read `${CLAUDE_PLUGIN_ROOT}/references/shared/000-config-loader.md`, `${CLAUDE_PLUGIN_ROOT}/references/shared/007-path-conventions.md`, and `.graph-powers/config.json`. Accept one plan path or directory (`PLAN.md`); without one, select the active matching `${paths.planDir}/*/PLAN.md`. Conversation-only approved plans are written once to that canonical path without redesign. Missing approval routes to `/plan`. Reject `--codex`, `--sprint=N`, and unknown flags; only `--dry-run` is valid.

```text
python -X utf8 "${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/sdd.py" validate <PLAN_FILE> --max-tasks <graphGuardrails.maxTasksPerPlan>
```

Exit 2/invalid/legacy plan routes to `/plan`; never infer omitted fields. `--dry-run` reports plan, tasks, gates, Owns/Needs, routing and proposed lease, then stops without workspace/write/lease/dispatch.

Only for a valid non-dry run, invoke `Skill("graph-powers:planning")` Phase C and read `${CLAUDE_PLUGIN_ROOT}/skills/planning/references/phase-c-executing-plans.md` with the approved plan and validator JSON. Preserve the working tree; return reviewed unstaged evidence. Stage, commit, push, PR and merge remain separate authorized actions.
