## Section 5: Tool Usage (ACI)

> ACI = Agent-Computer Interface. Per Anthropic "Building Effective Agents": tool documentation often more important than prompts.

| Tool | Purpose | When to use | When NOT to use | Edge cases |
|---|---|---|---|---|
| `Agent()` | Spawn subagent | L3+ tasks needing specialist | L1-L2 (overhead > value) | Background agents cannot Write/Edit |
| `Skill()` | Load domain context | User request or clear documented trigger | No clear match | Multiple skills OK; process skills before implementation skills |
| Agent Team tools | Runtime-native agent teams | L6+ multi-service tasks with true parallelism and team tools available | Below L6, or when tools are unavailable | If unavailable, use a coordinator agent plus explicit phase gates |
| `mcp__tavily__tavily_research` | Deep external research | A concrete unresolved decision needs multiple current sources and the tool is available | Tier alone or one fact; use a focused source lookup | Use the smallest available research capability that answers the gap |
| `mcp__tavily__tavily_search` | Web quick-check (single-shot) | Version checks, CVE audits, one external fact | Broad/ambiguous research (use `tavily_research`) | Add year/version; `search_depth: advanced` for thorough |
| `mcp__tavily__tavily_crawl` / `_map` / `_extract` | Multi-page docs intake | Crawl changelog/docs tree, map site, extract a known URL | Single quick fact | Scope with `select_paths` / `select_domains` |
| `mcp__claude_ai_Context7__*` | Library/framework docs | Any library Q: API, config, migration | General research (Tavily); internal (Grep) | resolve-library-id first → query-docs |
| `mcp__sequential-thinking__sequentialthinking` | Optional structured reasoning | A concrete ambiguity benefits from tracked reasoning and the tool is available | Tier alone, known patterns or unavailable tool | Ordinary reasoning remains sufficient; no mandatory pre-action call |
| `Read / Grep / Glob` | Codebase exploration | Always prefer over bulk reads | Never overly broad Grep patterns | Grep to filter → Read for content |
| `WebFetch` | Fetch web content | Official docs deep-dive, specific page | General research (Tavily) | `graph-powers:librarian` agent context only |

### Bounded results

Ask each tool for the smallest result scope that can support the decision. Keep the deciding
excerpts, counts, paths, commands, errors, numbers, and uncertainty in context; point to the full
artifact or source for everything else. This is selection guidance for context efficiency, not an
enforced hard cap: widen the request when the evidence requires it.
