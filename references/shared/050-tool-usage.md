## Section 5: Tool Usage (ACI)

> ACI = Agent-Computer Interface. Per Anthropic "Building Effective Agents": tool documentation often more important than prompts.

| Tool | Purpose | When to use | When NOT to use | Edge cases |
|---|---|---|---|---|
| `Agent()` | Spawn subagent | L3+ tasks needing specialist | L1-L2 (overhead > value) | Background agents cannot Write/Edit |
| `Skill()` | Load domain context | Before any domain action — even 1% match | Never skip | Multiple skills OK; process skills before implementation skills |
| Agent Team tools | Runtime-native agent teams | L6+ multi-service tasks with true parallelism and team tools available | Below L6, or when tools are unavailable | If unavailable, use a coordinator agent plus explicit phase gates |
| `mcp__tavily__tavily_research` | Deep external research (agentic, multi-source) — **planning default** | Best practices, comparisons, migration pitfalls, broad topics | Single known fact (use `tavily_search`) | `model: auto`; `pro` for broad multi-subtopic |
| `mcp__tavily__tavily_search` | Web quick-check (single-shot) | Version checks, CVE audits, one external fact | Broad/ambiguous research (use `tavily_research`) | Add year/version; `search_depth: advanced` for thorough |
| `mcp__tavily__tavily_crawl` / `_map` / `_extract` | Multi-page docs intake | Crawl changelog/docs tree, map site, extract a known URL | Single quick fact | Scope with `select_paths` / `select_domains` |
| `mcp__claude_ai_Context7__*` | Library/framework docs | Any library Q: API, config, migration | General research (Tavily); internal (Grep) | resolve-library-id first → query-docs |
| `mcp__sequential-thinking__sequentialthinking` | Multi-step reasoning | L4+, ambiguous, 3+ file errors, irreversible | L1-L2, known patterns | Invoke BEFORE acting |
| `Read / Grep / Glob` | Codebase exploration | Always prefer over bulk reads | Never overly broad Grep patterns | Grep to filter → Read for content |
| `WebFetch` | Fetch web content | Official docs deep-dive, specific page | General research (Tavily) | `librarian` agent context only |
