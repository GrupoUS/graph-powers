---
description: "Investigate without changes: how this codebase works, what a library/API supports, or what a change touches. Findings only; not for fixing (/debug) or planning (/plan)."
workflow_type: parallelization
---

# /research

**ARGUMENTS:** $ARGUMENTS. Research-only: no edits or fixes. Load `${CLAUDE_PLUGIN_ROOT}/references/shared/005-method-bootstrap.md`, `${CLAUDE_PLUGIN_ROOT}/references/shared/030-agent-assignment-matrix.md`, `${CLAUDE_PLUGIN_ROOT}/references/shared/050-tool-usage.md`, and `${CLAUDE_PLUGIN_ROOT}/references/shared/070-parallel-agent-spawn.md`.

Route by where the answer lives: dispatch `graph-powers:explorer` in background for codebase/pattern/file questions; dispatch `graph-powers:librarian` in the same batch only for a library, API, documentation, version or advisory question. Continue local reading while they run.

Only for open-ended “should we build” questions, read `${CLAUDE_PLUGIN_ROOT}/skills/planning/references/wayfinding.md`; do not enter planning Phase B.

Use available tools for the concrete gap: Context7 for precise current APIs/docs; Tavily for broad ecosystem/community work. Ask versioned, dated, scoped questions and use authoritative sources for material claims. Reconcile contradictions; sequential thinking is optional only when an evidenced impasse benefits from it and that tool is available, never required by tier or finding count.

Return only: findings table (claim, confidence 1–5, source/path/URL, impact), knowledge gaps/contradictions, and one prioritized next action. Preserve explorer gaps and librarian requests. Do not turn findings into implementation.
