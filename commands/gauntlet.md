---
description: "Use only for explicit /gauntlet on an approved structured plan. Not for planning, L1-L2, generic assurance or unbounded perfection."
workflow_type: prompt-chaining
---

# /gauntlet

**ARGUMENTS:** $ARGUMENTS

Require one approved plan path (directory → `PLAN.md`) and optional `--dry-run`. No path → `/plan`
before load, write, lease or spawn; reject other flags.

Only when a path resolves, read `${CLAUDE_PLUGIN_ROOT}/references/shared/000-config-loader.md` and `.graph-powers/config.json`; resolve caps.

```text
python -X utf8 "${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/sdd.py" validate <PLAN_FILE> --max-tasks <graphGuardrails.maxTasksPerPlan> --profile gauntlet
```

Invalid plan/tier → `/plan`. L1-L2 prints `NOT ELIGIBLE FOR GAUNTLET` and stays local without
profile load or spawn.

Only when eligible L3+, read `${CLAUDE_PLUGIN_ROOT}/skills/planning/references/gauntlet-loop.md`.
Dry-run prints tier, tasks, `Owns`, `Needs`, waves, reviewers, caps and `/verify loop <PLAN_FILE>`;
no workspace, lease, write or spawn.

Only non-dry execution approves that plan; pass its JSON plus `profile: gauntlet` to `Skill("graph-powers:planning")` Phase C. End reviewed and unstaged; external actions need separate approval.
