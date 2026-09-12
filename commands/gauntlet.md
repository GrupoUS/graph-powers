---
description: "Use only for /gauntlet objective/plan or --dry-run; excludes L1-L2/generic."
workflow_type: prompt-chaining
---

# /gauntlet

**ARGS:** $ARGUMENTS. Accept objective/plan, `--plan <path>`, `--dry-run`, `--review-only`; reject others. Empty asks
for objective. Resolve quoted existing file/directory (directory → `PLAN.md`); `--plan`/`*.md` stays a
path if invalid, other text an objective. Only when a plan path is supplied, read `${CLAUDE_PLUGIN_ROOT}/references/shared/000-config-loader.md` before resolution.

Objective `--dry-run`: report Step 0 → A → B → evaluator → approval → C → `/verify loop` and stop. No skill,
investigate, validate, check, lease, write or spawn. Only when a non-dry objective is supplied, invoke `Skill("graph-powers:planning")`: L1-L2 is `NOT ELIGIBLE FOR GAUNTLET`; L3+ runs
Step 0 → A → B and evaluator review. Reuse covered approval; pause only for new scope/authority/decision.

Validate the plan and check its bound review, both read-only:

```text
python -X utf8 "${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/sdd.py" validate <PLAN_FILE> --max-tasks <graphGuardrails.maxTasksPerPlan> --profile gauntlet
python -X utf8 "${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/sdd.py" review-check <PLAN_FILE>
```

Invalid → `/plan`; L1-L2 → `NOT ELIGIBLE FOR GAUNTLET` without profile/spawn.

`review-bind` belongs to Phase B Step 7, after the Mode 1 verdict, or to `--review-only`: validate,
run that review, bind its verdict and stop — no acquire, Phase C, lease or writer. Every `--dry-run`
reports `builder` and `inspector` as two distinct role ids and binds nothing. A non-dry run without
`--review-only` enters Phase C only when `review-check` exits `0`; exit `4` (`STALE`,
`REVISION_REQUIRED`, `UNREVIEWED`) returns to Phase B with no lease.

Only for a valid L3+ plan `--dry-run`, report tier, tasks, Owns/Needs, waves, reviewers,
caps and `/verify loop <PLAN_FILE>`, then stop; no workspace, lease, write or spawn.

Only for a valid non-dry L3+ plan, read `${CLAUDE_PLUGIN_ROOT}/skills/planning/references/gauntlet-loop.md` and invoke `Skill("graph-powers:planning")` Phase C with `profile: gauntlet`; the loop owns coverage/review reuse before lease. End reviewed/unstaged.
