---
description: "Use only for /gauntlet objective/plan or --dry-run; excludes L1-L2/generic."
workflow_type: prompt-chaining
---

> Hermes: first load `skill_view("graph-powers:graph-engineering")` for native calls and host-policy limits. `content/` paths are `file_path` values relative to the common registered-document parent. Source tools/model frontmatter is not host enforcement.

# /gauntlet

**ARGS:** the user-provided arguments. Accept objective/plan, `--plan <path>`, `--dry-run`; reject others. Empty asks
for objective. Resolve quoted existing file/directory (directory → `PLAN.md`); `--plan`/`*.md` stays a
path if invalid, other text an objective. Only when a plan path is supplied, read `content/references/shared/000-config-loader.md` before resolution.

Objective `--dry-run`: report Step 0 → A → B → evaluator → approval → C → `/verify loop` and stop. No skill,
investigate, validate, check, lease, write or spawn. Only when a non-dry objective is supplied, invoke `skill_view("graph-powers:planning")`: L1-L2 is `NOT ELIGIBLE FOR GAUNTLET`; L3+ runs
Step 0 → A → B and evaluator review. Reuse covered approval; pause only for new scope/authority/decision.

Validate plan:

```text
python -X utf8 "content/skills/planning/scripts/sdd.py" validate <PLAN_FILE> --max-tasks <graphGuardrails.maxTasksPerPlan> --profile gauntlet
```

Invalid → `/plan`; L1-L2 → `NOT ELIGIBLE FOR GAUNTLET` without profile/spawn.

Only for a valid L3+ plan `--dry-run`, report tier, tasks, Owns/Needs, waves, reviewers,
caps and `/verify loop <PLAN_FILE>`, then stop; no workspace, lease, write or spawn.

Only for a valid non-dry L3+ plan, read `content/skills/planning/references/gauntlet-loop.md` and invoke `skill_view("graph-powers:planning")` Phase C with `profile: gauntlet`; the loop owns coverage/review reuse before lease. End reviewed/unstaged.
