---
description: "Investigate without changing anything — how this codebase does X, what a library or API actually supports, what a change would touch. Use when the user says to look into it, find out how something works, or explicitly not to edit yet. Explores the codebase and external docs in parallel and returns structured findings only. Do not use to then fix what it found (/debug) or to turn it into a plan (/plan)."
workflow_type: parallelization
---

# /research — Parallel Research Only

**ARGUMENTS**: $ARGUMENTS

> **Read before step 0 — never reconstruct these from memory:** `${CLAUDE_PLUGIN_ROOT}/references/shared/005-method-bootstrap.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/030-agent-assignment-matrix.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/050-tool-usage.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/070-parallel-agent-spawn.md`

> Research-only mode: findings, no edits, no fixes. This is the discovery half of the planning
> chain, usable on its own when the question is what exists rather than what to build.

---

## Agent routing (mandatory — choose by **where the answer lives**)

Follow `030-agent-assignment-matrix.md`: codebase, pattern, or file questions go to
`graph-powers:explorer`; external library/API, best-practice, or package-documentation questions
go to `graph-powers:librarian`. The explorer is the plugin agent at
`${CLAUDE_PLUGIN_ROOT}/agents/explorer.md`, **not** the built-in `Explore`; use the exact
namespaced `subagent_type`.

---

## Setup and execution

The method bootstrap governs skill selection and the parallel-spawn reference governs the batch.
For open-ended wayfinding (for example, “should we build X?”), first use
`${CLAUDE_PLUGIN_ROOT}/skills/planning/references/wayfinding.md`; do not enter Phase B because the
research answer is the deliverable. Skip wayfinding for a concrete factual question.

1. Fire `graph-powers:explorer` in background for codebase analysis (custom agent, **not** built-in `Explore`).
2. If a library, package, or external API is mentioned, fire `graph-powers:librarian` in the same background batch.
3. Continue local reading immediately; do not wait for agents. Collect their results when ready.
4. Keep research-only behavior: findings, no edits or fixes. Reconcile sources, then report the structured output below.

## External research driving rules

Tool choice is canonical in `050-tool-usage.md`. For external questions, use Context7 for API/docs
and `tavily_research` for broad ecosystem research; run both when official documentation and
community context are both needed.

### Tavily — writing the query

- Two or three variations, not one: `"<lib> middleware order 2026"`, `"<lib> v<N> breaking changes"`.
- **Always put the year and the version in the query.** Without them the top results are whichever
  version was popular when the page was written, and they read as current.
- `include_domains`: `github.com`, `npmjs.com`, `github.com/advisories`, `snyk.io`. For a CVE:
  `<package> CVE GHSA`.
- `search_depth: advanced` when thoroughness matters, `fast` when latency does.
- For `tavily_research`, pass a full task description in `input` rather than keywords — it runs an
  agentic multi-source pass, and a keyword string wastes that.
- Scope `tavily_crawl` with `select_paths`; an unscoped crawl of a docs tree returns more than any
  context window wants.

### Context7 — the two calls, in order

1. `mcp__claude_ai_Context7__resolve-library-id` — package name to library ID.
2. `mcp__claude_ai_Context7__query-docs` — with a specific topic (`"useQuery options"`,
   `"insert returning"`), never the library name alone.

Prefer it over recalled knowledge for any library whose API surface is non-trivial. Training data
has a cutoff; the docs do not.

---

## Reconciliation and output

Classify each question by destination using the routing above. Verify important facts across
sources and flag contradictions. When sources conflict or at least three findings need
reconciliation, invoke `mcp__sequential-thinking__sequentialthinking` before reporting (L4+ MUST;
L3 SHOULD). Confidence is 1=speculation, 3=community, 5=official documentation.

Return actionable research only:

- **Findings** — methodology/queries, curated findings, source URLs, credibility, synthesis, and material tables; include direct quotes for important claims.
- **Gaps** — contradictions, missing evidence, and unanswered questions; preserve the explorer's Knowledge Gaps and Librarian Requests.
- **Recommended next step** — give one prioritized action by default; add follow-ups only when material to unresolved evidence or gaps.

---

## Findings format

| # | Finding | Confidence | Source | Impact |
|---|---|---|---|---|
| 1 | … | 4 | codebase: path/file | high |
| 2 | … | 5 | docs: URL | high |

## Knowledge gaps

[List what remains unknown after both agents complete]

## Recommended next step

[One prioritized next step by default; add follow-ups only when material to unresolved evidence or gaps]
