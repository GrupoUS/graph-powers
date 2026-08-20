---
description: "Investigate without changing anything — how this codebase does X, what a library or API actually supports, what a change would touch. Use when the user says to look into it, find out how something works, or explicitly not to edit yet. Explores the codebase and external docs in parallel and returns structured findings only. Do not use to then fix what it found (/debug) or to turn it into a plan (/plan)."
workflow_type: parallelization
---

# /research — Parallel Research Only

**ARGUMENTS**: $ARGUMENTS

> **Read before step 0 — never reconstruct these from memory:** `${CLAUDE_PLUGIN_ROOT}/references/shared/005-superpowers-bootstrap.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/030-agent-assignment-matrix.md`
> Read `${CLAUDE_PLUGIN_ROOT}/references/shared/050-tool-usage.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/070-parallel-agent-spawn.md`

> Research-only mode: findings, no edits, no fixes. This is the discovery half of the planning
> chain, usable on its own when the question is what exists rather than what to build.

---

## Agent routing (mandatory — choose by **where the answer lives**)

> **`graph-powers:explorer` = the plugin's agent, `${CLAUDE_PLUGIN_ROOT}/agents/explorer.md`** — structured findings table with confidence scores (1-5), Knowledge Gaps, Librarian Requests.
> **NOT the built-in `Explore`.** Use `subagent_type: "graph-powers:explorer"` (exact case).

| Question type | Agent | Why |
|---|---|---|
| What exists in our codebase? | `graph-powers:explorer` | Filesystem |
| How does this code pattern work? | `graph-powers:explorer` | Filesystem |
| Which files need to change? | `graph-powers:explorer` | Filesystem |
| How does this library/API work? | `graph-powers:librarian` | External |
| What are best practices for X? | `graph-powers:librarian` | External |
| Is this package behavior documented? | `graph-powers:librarian` | External |

---

## Setup

```typescript
Skill("superpowers:using-superpowers");           // meta — bootstrap (per `${CLAUDE_PLUGIN_ROOT}/references/shared/005-superpowers-bootstrap.md`)
Skill("superpowers:dispatching-parallel-agents"); // explorer + librarian = parallel batch with distinct scope
```

If the research scope is open-ended (user says "should we build X?" / "how should we approach Y?" / no concrete artifact requested), also invoke `Skill("superpowers:brainstorming")` to frame the right questions before research. Skip when the user asked a concrete factual question (`how does library X handle Y?`).

## Execution

1. Fire `graph-powers:explorer` (custom agent, **NOT** built-in `Explore`) in background for codebase analysis.
2. Fire `graph-powers:librarian` in background for external documentation **IF** any library, package, or external API is mentioned.
3. Continue reading immediately — do not wait for agents.
4. Collect background results.
5. Output structured findings table with confidence (1-5), source, impact.
6. **Do NOT implement.** Research only.

---

## Tool selection

| Question | Tool | Rationale |
|---|---|---|
| API syntax, config options, framework patterns | **Context7** | Official docs — version-accurate |
| Best practices, community patterns, broad/multi-subtopic | **`tavily_research`** (`model: auto`) | Agentic multi-source synthesis — default for planning research |
| Single fact / version / quick CVE check | **`tavily_search`** (year + version) | Low-latency single-shot; `search_depth: advanced` when thorough |
| Package CVEs, security advisories, maintenance | **`tavily_search`** or **`tavily_research`** | Realtime ecosystem (GHSA, Snyk, npm) |
| Breaking changes in library vN | **Context7 → `tavily_research`** | Official migration → community pitfalls |
| Comparing 2+ packages | **`tavily_research`** | Multi-source benchmarks, npm stats |
| Multi-page docs / changelog intake | **`tavily_crawl`** / **`tavily_map`** | Crawl/map a docs tree; `tavily_extract` for a known URL |
| Exact hook/function signatures, schemas | **Context7** | Always prefer over training |

**Which tool for which question** is decided by `050-tool-usage.md`, loaded above — it is the one
table, and this command does not carry a second opinion about it. What follows is only how to drive
the ones this command reaches for, which that table does not cover.

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

## Approach

1. Classify: answer in codebase (graph-powers:explorer) or external (graph-powers:librarian)?
2. External: API/docs question (Context7) or ecosystem state (`tavily_research` default)?
3. Run both when question spans documentation + community context
4. Verify key facts across sources — flag contradictions
5. **When sources conflict or ≥3 findings must be reconciled** → invoke `mcp__sequential-thinking__sequentialthinking` to synthesize before reporting (L4+ MUST · L3 SHOULD)
6. Confidence score reflects source quality: 1=speculation · 3=community · 5=official docs

---

## Output

- Research methodology + queries used
- Curated findings with source URLs
- Credibility assessment of sources
- Synthesis highlighting key insights
- Contradictions or gaps identified
- Data tables / structured summaries
- Recommendations for further research

Direct quotes for important claims. Actionable insights only.

---

## Findings format

| # | Finding | Confidence | Source | Impact |
|---|---|---|---|---|
| 1 | … | 4 | codebase: path/file | high |
| 2 | … | 5 | docs: URL | high |

## Knowledge gaps

[List what remains unknown after both agents complete]

## Recommended next step

[One suggested action based on findings]
