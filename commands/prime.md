---
description: "Load a project's minimum relevant context. Modes: auto, backend, frontend, fullstack. Use to get up to speed; not to locate one fact (/research)."
workflow_type: augmented-llm
---

# /prime

**ARGUMENTS:** $ARGUMENTS. Read `${CLAUDE_PLUGIN_ROOT}/references/shared/000-config-loader.md`, `${CLAUDE_PLUGIN_ROOT}/references/shared/005-method-bootstrap.md`, and `${CLAUDE_PLUGIN_ROOT}/references/shared/020-complexity-routing.md`, then `.graph-powers/config.json`. Read `.graph-powers/HANDOFF.md` first when it exists; inspect working-tree/recent history. This command loads context, not an implementation skill.

| Token | Load |
|---|---|
| none / `auto` / `cross` | classify scope, then selected staging section |
| `backend` / `api` / `db` only | read `${CLAUDE_PLUGIN_ROOT}/references/shared/045-context-staging.md § 4.5a` |
| `frontend` / `ui` / `react` only | read `${CLAUDE_PLUGIN_ROOT}/references/shared/045-context-staging.md § 4.5b` |
| `fullstack` / `multi` only | read `${CLAUDE_PLUGIN_ROOT}/references/shared/045-context-staging.md § 4.5c` |

Auto classifies UI as frontend, API/service/schema/integration as backend, and combined UI/API/schema as fullstack. Vague scope stops after config/history and asks which domain it is. List `${rulesDir}`, match `paths:`, and read only applicable rules; Tier 3 docs, ADRs and learnings are on demand. Never eager-load both architecture and design sets.

For an L3+ intent, and only if this context load cannot answer a concrete fact, dispatch `graph-powers:explorer` (repository) or `graph-powers:librarian` (current external API/advisory), at most one for L3 and both only for independent L4+ needs; `--no-auto-research` skips it. Return under 120 words: project/branch/mode/stage, actual files loaded, supplements, next on-demand file, and ready task. Stop after the minimum sufficient load.
