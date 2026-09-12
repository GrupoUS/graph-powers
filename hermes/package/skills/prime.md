---
description: "Load a project's minimum relevant context. Modes: auto, backend, frontend, fullstack. Use to get up to speed; not to locate one fact (/research)."
workflow_type: augmented-llm
---

> Hermes: first load `skill_view("graph-powers:graph-engineering")` for native calls and host-policy limits. `content/` paths are `file_path` values relative to the common registered-document parent. Source tools/model frontmatter is not host enforcement.

# /prime

**ARGUMENTS:** the user-provided arguments. Read `content/references/shared/000-config-loader.md`, `content/references/shared/005-method-bootstrap.md`, and `content/references/shared/020-complexity-routing.md`, then `.graph-powers/config.json`. Read `.graph-powers/HANDOFF.md` first when present; inspect working-tree/recent history. Load context only.

| Token | Load |
|---|---|
| none / `auto` / `cross` | classify scope, then selected staging section |
| `backend` / `api` / `db` only | read `content/references/shared/045-context-staging.md § 4.5a` |
| `frontend` / `ui` / `react` only | read `content/references/shared/045-context-staging.md § 4.5b` |
| `fullstack` / `multi` only | read `content/references/shared/045-context-staging.md § 4.5c` |

Auto maps UI to frontend, API/service/schema/integration to backend, combined work to fullstack. Documentation follows its named source and rules. Ask only for a fact blocking the load. Match `${rulesDir}` by `paths:`; Tier 3 docs, ADRs and learnings stay on demand. Never eager-load architecture and design together.

Before readiness, verify constraints and action/scope approval provenance. Reuse proof only with matching project/worktree, source/config/consumer digests, dirty state, dependencies and environment; SHA alone is insufficient. Mark missing proof. Read decisive sources and nearest instructions now; trace entrypoint, definitions and callers for a flow question. Reassess every four files; stop when answered.

Only on resume with an identified same-worktree plan, run `python -X utf8 "content/skills/planning/scripts/sdd.py" status <PLAN_FILE> --max-tasks <graphGuardrails.maxTasksPerPlan> --session-id <SESSION_ID>` using the acquisition identity (Gauntlet adds `--profile gauntlet`). Inspect state/next ID; counts prove neither approval nor fresh checks. Invalid/ambiguous binding stops. Other loads never scan plans or query status.

For an unanswered structural question, use the config loader's graph branch with bounded provider discovery/text fallback. Sufficient source or local/document work needs no graph query.

Only for an unanswered concrete L3+ fact, dispatch `graph-powers:explorer` (repository) or `graph-powers:librarian` (external API/advisory): one at L3, both only for independent L4+ needs; `--no-auto-research` skips. Return under 120 words: project/branch/mode/stage, files actually read, supplements, next on-demand file and ready task or missing proof. Planned reads are not completed reads.
