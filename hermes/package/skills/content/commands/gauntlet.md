---
description: "Use only for explicit /gauntlet on an approved structured plan. Supports --dry-run; not for planning, L1-L2, generic assurance or unbounded perfection."
workflow_type: prompt-chaining
---

> Hermes: first load `skill_view("graph-powers:graph-engineering")` for native calls and host-policy limits. `content/` paths are `file_path` values relative to the common registered-document parent. Source tools/model frontmatter is not host enforcement.

# /gauntlet

**ARGUMENTS:** the user-provided arguments. Require one approved plan path (directory resolves to `PLAN.md`) and optional `--dry-run`; reject any other flag. No valid path routes to `/plan` before loading, writing, leasing or spawning.

When a path resolves, read `.graph-powers/config.json` and validate:

```text
python -X utf8 "content/skills/planning/scripts/sdd.py" validate <PLAN_FILE> --max-tasks <graphGuardrails.maxTasksPerPlan> --profile gauntlet
```

Invalid plan/tier routes to `/plan`. L1-L2 reports `NOT ELIGIBLE FOR GAUNTLET` without profile load/spawn.

Only for a validated eligible L3+ plan, read `content/skills/planning/references/gauntlet-loop.md`. `--dry-run` reports tier, tasks, Owns/Needs, waves, reviewers, caps and `/verify loop <PLAN_FILE>`; it never creates a workspace, lease, write or spawn.

Only for a valid non-dry run, invoke `skill_view("graph-powers:planning")` Phase C and read `content/skills/planning/references/phase-c-executing-plans.md` with the approved plan JSON and `profile: gauntlet`; end reviewed and unstaged. External actions need separate approval.
