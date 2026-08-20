## Section 10: AutoResearch Loop

Triggered by `/debug auto`, `/implement auto`, or any command-mode that detects unresolved external knowledge gap.

Loop:

1. Identify external question (library API, version diff, current best practice, CVE)
2. **Library API / config / signature** → `mcp__claude_ai_Context7__resolve-library-id` → `query-docs` (authoritative)
3. **Best practice / comparison / migration / broad topic** → `mcp__tavily__tavily_research` (`model: auto`) as the **default deep pass — not a fallback**. Single fact / CVE / version → `mcp__tavily__tavily_search` (year + version)
4. **Sources conflict OR ≥3 distinct findings to reconcile** → invoke `mcp__sequential-thinking__sequentialthinking` to synthesize before acting (L4+ MUST · L3 SHOULD)
5. Still unresolved after Context7 + Tavily → spawn `librarian` agent with full context
6. Cache the answer; if useful long-term → propose memory write via `/evolve`
7. Resume the original task with new info

Hard limit: 3 cycles. After 3 unresolved → flag to user as a research blocker.
