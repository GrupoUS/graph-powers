---
description: "Use only for /gauntlet objective/plan or --dry-run; excludes L1-L2/generic."
workflow_type: prompt-chaining
---

# /gauntlet

**ARGS:** $ARGUMENTS. Accept objective/plan, `--plan <path>`, `--dry-run`, `--review-only`; reject others. Empty asks
for objective. Resolve quoted existing file/directory (directory → `PLAN.md`); `--plan`/`*.md` stays a
path if invalid, other text an objective. Only when a plan path is supplied, read `${CLAUDE_PLUGIN_ROOT}/references/shared/000-config-loader.md` before resolution.

Objective `--dry-run`: describe Step 0 → A's frontier rounds/recommendations → explicit shared-understanding
confirmation → B → evaluator → approval → C → `/verify loop`; stop without live questions, skill,
investigation, validation, checks, lease, writes or spawns. Only for a non-dry objective, invoke `Skill("graph-powers:planning")`: L1-L2 is `NOT ELIGIBLE FOR GAUNTLET`; L3+ runs Step 0 → Phase A Step 2's grill/confirmation → Phase B. Covered scope approval does not replace that confirmation.

Only for a supplied plan, read `${CLAUDE_PLUGIN_ROOT}/skills/planning/references/gauntlet-loop.md` § Entry and dry-run and apply its hole preflight **before validation**. Ready approved plans need no new grill/confirmation; dry-run describes gaps, review-only reports them and stops. Then validate and check the bound review, read-only:

```text
python -X utf8 "${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/sdd.py" validate <PLAN_FILE> --max-tasks <graphGuardrails.maxTasksPerPlan> --profile gauntlet
python -X utf8 "${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/sdd.py" review-check <PLAN_FILE>
```

Invalid → `/plan`; L1-L2 → `NOT ELIGIBLE FOR GAUNTLET` without profile/spawn.

`review-bind` follows the Mode 1 verdict in Phase B Step 7. `--review-only` validates, reviews,
binds and stops before acquire, Phase C, lease or writer. Every dry-run names distinct `builder`
and `inspector` role ids and binds nothing. Execution requires `review-check` exit `0`; exit `4`
(`STALE`, `REVISION_REQUIRED`, `UNREVIEWED`) returns to Phase B without a lease.

Only for a valid L3+ plan `--dry-run`, report tier, tasks, Owns/Needs, waves, reviewers,
caps and `/verify loop <PLAN_FILE>`, then stop; no workspace, lease, write or spawn.

Only for a valid non-dry L3+ plan without `--review-only`, read `${CLAUDE_PLUGIN_ROOT}/skills/planning/references/gauntlet-loop.md` and invoke `Skill("graph-powers:planning")` Phase C with `profile: gauntlet`. End reviewed/unstaged.
