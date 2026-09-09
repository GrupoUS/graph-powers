---
description: "Execute an approved implementation plan through planning Phase C. Supports only --dry-run; use /plan to decide and /verify to confirm."
workflow_type: prompt-chaining
---

> Hermes: first load `skill_view("graph-powers:graph-engineering")` for native calls and host-policy limits. `content/` paths are `file_path` values relative to the common registered-document parent. Source tools/model frontmatter is not host enforcement.

# /implement

**ARGUMENTS:** the user-provided arguments. Phase C owns execution; this adapter selects and validates the plan.

Read `content/references/shared/000-config-loader.md`, `content/references/shared/007-path-conventions.md`, and `.graph-powers/config.json`. Only `--dry-run` is valid; reject other flags, including `--codex` and `--sprint=N`.

Select in order: explicit file/directory (`PLAN.md`); an unambiguous active session/handoff binding to this project and plan; otherwise a unique current or legacy plan under `${paths.planDir}`. Exclude spec/map/handoff records. Resolve real paths against the current Git worktree; reject escaping symlinks, external/nested repositories and sibling worktrees. Invalid explicit or active bindings stop without fallback. Multiple bindings/candidates require one selection question. Never select by mtime or lease. With none, use an approved conversational plan or `/plan`.

A conversation-only approved plan is materialized once at the canonical path only on a non-dry run. In dry-run, report its proposed route and missing disk validation in the response; write nothing. Missing approval routes to `/plan`.

```text
python -X utf8 "content/skills/planning/scripts/sdd.py" validate <PLAN_FILE> --max-tasks <graphGuardrails.maxTasksPerPlan>
```

For an existing selection, exit 2/invalid/legacy routes to `/plan`; never infer fields or try another candidate. Dry-run reports plan, tasks/gates, Owns/Needs, routing and proposed lease without writes, workspace or dispatch.

Only for a valid non-dry run, invoke `skill_view("graph-powers:planning")` and read `content/skills/planning/references/phase-c-executing-plans.md` with the approved plan and validator JSON. Preserve the tree; return reviewed unstaged evidence. Git/publication needs separate action/scope authorization.
