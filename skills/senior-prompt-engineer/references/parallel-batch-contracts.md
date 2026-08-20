# Parallel Batch Contracts

> Shared return contract for parallel-spawn agents (≥2 agents in one message).
> Loaded by the `senior-prompt-engineer` skill and by `references/rubrics/explorer-rubric.md`.
> The spawn pattern it implements is `${CLAUDE_PLUGIN_ROOT}/references/shared/070-parallel-agent-spawn.md`.

---

## 1. When this applies

Whenever a command spawns ≥2 agents in a single message via the parallel pattern in `${CLAUDE_PLUGIN_ROOT}/references/shared/070-parallel-agent-spawn.md`. Examples:

| Command | Parallel batch members |
|---|---|
| `/research` | `graph-powers:explorer` + `graph-powers:librarian` |
| `/debug` (L4-L5) | `graph-powers:explorer` + `regression-hunter` |
| `/implement` (L6+ Phase 2 PARALLEL) | 2-3 `graph-powers:frontend-specialist` instances on independent tasks |
| `/perf fix` | 1 `graph-powers:performance-optimizer` per route cluster |
| `/verify` Phase 8 | parallel codex review + adversarial review |

**Single-agent spawns** use only the schema in `agent-handoff-contracts.md` — no findings table required.

---

## 2. Findings table schema

Every parallel-batch member returns a findings table with these exact columns:

```markdown
| # | Finding | Confidence (1-5) | Source | Impact (Low/Med/High) |
|---|---------|------------------|--------|------------------------|
| 1 | <one-line claim with file:line if applicable> | 4 | code | High |
| 2 | … | 3 | docs | Med |
```

**Column semantics:**

- **`#`** — sequence within this agent's report. Renumbered after consolidation.
- **`Finding`** — one-line claim. Cite `file:line` when grounded in code; cite URL when from external docs. Avoid prose paragraphs — long detail goes in `Context Handoff::Decisions`.
- **`Confidence`** — see scoring table § 3.
- **`Source`** — `code` | `docs` | `tests` | `tooling` | `inferred`. Single token, no commas.
- **`Impact`** — qualitative business/technical impact. Distinct from severity (§ 4).

**No additional columns.** Adding columns breaks mechanical consolidation. If a finding needs more dimensions, file it as multiple rows.

---

## 3. Confidence scoring

| Score | Meaning | Action by parent |
|---|---|---|
| **5** | Verified in codebase or runtime build | Use directly |
| **4** | Multiple sources agree (e.g., docs + grep) | Use with confidence |
| **3** | Community consensus / single authoritative source | Note uncertainty in plan |
| **2** | Single source, indirect evidence | Flag as `[ASSUMED]` in plan |
| **1** | Speculation | Don't rely; spawn follow-up agent |

**Hard rule:** parent must NOT proceed to implementation on findings ≤ 2 unless explicitly flagged `[ASSUMED]` and accepted by user.

---

## 4. Severity scale (review batches only)

For batches that produce reviews (codex review, evaluator, security-review), each finding additionally carries a severity:

| Severity | Meaning | Parent action |
|---|---|---|
| **P0** | Ship-blocker — security, data loss, build break | STOP. Do not merge. |
| **P1** | Must fix this PR | Block merge until resolved or explicitly waived |
| **P2** | Next sprint — quality / minor regression risk | Track in tasks; ship without |
| **P3** | Nice-to-have — style, micro-optimization, doc nit | Optional; ship without |

Add severity as a 6th column for review batches only:

```markdown
| # | Finding | Confidence | Source | Impact | Severity |
|---|---------|------------|--------|--------|----------|
| 1 | XSS in `<src>/<file>:<line>` via raw HTML injection | 5 | code | High | P0 |
```

---

## 5. Consolidation rules (parent agent)

When N parallel agents complete, the parent merges results:

1. **Concatenate** all rows from all members into one combined table.
2. **Dedupe** by `Finding` string. When two members report the same finding:
   - `Confidence` ← max of the two
   - `Impact` ← max (Low < Med < High)
   - `Severity` ← max (P3 < P2 < P1 < P0)
   - `Source` ← merge into "code+docs" if different
3. **Renumber** `#` column after dedupe.
4. **Sort** by Severity (descending), then Confidence (descending).
5. **Aggregate status** per `agent-handoff-contracts.md § 5`: worst status wins.

The consolidated table is what the parent presents to the user — never the raw per-agent tables.

---

## 6. Tool-precedence guidance for batch members

When `/research` spawns `graph-powers:explorer` + `graph-powers:librarian`:

- **`graph-powers:explorer`** uses Grep/Glob/Read first. Tavily/Context7/WebFetch are forbidden by agent definition (`explorer.md`).
- **`graph-powers:librarian`** uses Context7 (`mcp__claude_ai_Context7__resolve-library-id` → `query-docs`) **first** for API signatures, config, version migration. Uses Tavily (`mcp__tavily__tavily_research` for deep passes, `mcp__tavily__tavily_search` for single CVE / version facts) for community-pattern news, ecosystem updates, advisories. WebFetch is the last resort for specific URLs not covered by either.

**Why:** Context7 ships up-to-date library docs; Tavily ships current web. Calling Tavily for "what's the React 19 useEffect signature?" wastes tokens because Context7 has it.

Commands that spawn `graph-powers:librarian` (currently `/research`, `/debug auto`) MUST inject this precedence guidance into the agent prompt — the agent definition does not enforce it.

---

## 7. Non-overlapping scope

Per `${CLAUDE_PLUGIN_ROOT}/references/shared/070-parallel-agent-spawn.md` rule 4 ("Distinct scope"): each agent in a parallel batch must investigate a non-overlapping area. If two agents would cover the same files / questions / docs, merge into one agent.

When in doubt, ask: "Could one agent answer both prompts in one pass?" If yes → one agent.

---

## 8. Maximum batch size

Per `${CLAUDE_PLUGIN_ROOT}/references/shared/070-parallel-agent-spawn.md`: at most `graphGuardrails.maxParallelWave` agents in one
fan-out (default 5). A parallel batch counts each agent toward that width. Plan accordingly:

| Batch size | Remaining spawn budget |
|---|---|
| 2 (e.g., explorer + librarian) | 3 left for follow-ups |
| 3 | 2 left |
| 4 | 1 left — cannot afford another batch |
| 5 | 0 — must checkpoint with user |

If the natural fan-out exceeds 5, **cluster** by root cause (see `/perf` § 2.5 pattern) before spawning.

Owner: `senior-prompt-engineer` skill.
