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

Auto classifies UI as frontend, API/service/schema/integration as backend, and combined UI/API/schema as fullstack. Documentation-only scope follows the named document and applicable rules without forcing a code domain. Ask a context question only when the missing fact prevents the requested load; never ask for a domain already resolved by the task. List `${rulesDir}`, match `paths:`, and read only applicable rules; Tier 3 docs, ADRs and learnings are on demand. Never eager-load both architecture and design sets.

Reuse valid handoff evidence after checking project/worktree identity and relevant source/config/consumer digests, including dirty state; unchanged SHA alone is insufficient. Read the named source/document and its nearest applicable instructions now, before claiming readiness. For a flow question, first trace a short source chain through the entrypoint, relevant definitions and callers until it answers the question. Expand to architecture notes or a specialist only if a concrete question remains. Reassess after each four-file stage and stop once the question is answered.

For an unanswered structural question, use the graph branch of the already-read config loader. A local/document task or sufficient current source needs no graph/status query; keep discovery bounded to the selected provider and text fallback.

For an L3+ intent, and only if this context load cannot answer a concrete fact, dispatch `graph-powers:explorer` (repository) or `graph-powers:librarian` (current external API/advisory), at most one for L3 and both only for independent L4+ needs; `--no-auto-research` skips it. Return under 120 words: project/branch/mode/stage, enumerate only files actually read, supplements, next on-demand file, and ready task or the missing evidence preventing readiness. A proposed reading list is not a completed context load. Stop after the minimum sufficient load.
