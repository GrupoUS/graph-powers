# Shared context — canonical patterns for every command

Every command in this plugin opens by reading this file:

```
Read ${CLAUDE_PLUGIN_ROOT}/references/shared-context.md
```

That line is deliberate. This file used to live in `commands/`, where two things went wrong: the
runtime registered it as a slash command nobody meant to expose, and the commands only *mentioned*
it in prose — so whether it was ever read depended on the model deciding to go look.

Never duplicate a section from here inside a command. A pattern that lives in two files diverges,
and this whole plugin exists because that is what happened last time.

---

## Section 0: Config Loader

Every command reads `.graph-powers/config.json` at start to resolve project-specific values. Pattern:

```bash
# read config (commands invoke via Bash or Read)
test -f .graph-powers/config.json && cat .graph-powers/config.json
```

Substitution placeholders used in commands (resolve at runtime):

| Placeholder | Source field |
|---|---|
| `${project.name}` | `project.name` |
| `${project.stagingUrl}` | `project.stagingUrl` |
| `${project.locale}` | `project.locale` |
| `${paths.backendRoot}` | `paths.backendRoot` |
| `${paths.frontendRoot}` | `paths.frontendRoot` |
| `${paths.schemaRoot}` | `paths.schemaRoot` |
| `${paths.libRoot}` | `paths.libRoot` |
| `${paths.componentsRoot}` | `paths.componentsRoot` |
| `${tooling.packageManager}` | `tooling.packageManager` |
| `${tooling.buildTool}` | `tooling.buildTool` |
| `${tooling.typeChecker}` | `tooling.typeChecker` |
| `${tooling.linter}` | `tooling.linter` |
| `${tooling.testRunner}` | `tooling.testRunner` |
| `${gates.lighthouse.*}` | `gates.lighthouse.*` |
| `${gates.lcp/cls/inp/initialJsKb}` | `gates.*` |
| `${rulesDir}` | `paths.rulesDir` (defaults to `.claude/rules`) |

**Rule layer.** All project rules + supplements live under `${rulesDir}`. No overlay folder, no overlay-first resolution. Tier 2 rules auto-load via `globs:` frontmatter; supplements load on demand by command/skill:

| File | Purpose |
|---|---|
| `${rulesDir}/routing-supplements.md` | Project-specific routing matrix rows (loaded by `/prime`, `/implement`) |
| `${rulesDir}/verify-supplements.md` | Project-specific smoke tests (loaded by `/verify`) |
| `Skill("debugger")` → `${CLAUDE_PLUGIN_ROOT}/skills/debugger/references/anti-patterns.md` | Project-specific bug patterns + Negative Constraints index |
| `Skill("planning")` → `${CLAUDE_PLUGIN_ROOT}/skills/planning/references/layer-map.md` | Project-specific layer map for sprint phase ordering |
| `Skill("senior-architect")` | Project orientation: architecture map, runtime shape, trade-off analysis |
| `.graph-powers/logs/` | Runtime state: session counters, write lease, progress log, learnings (never versioned) |

Project identity, cardinal rules, and constraints live in **root `AGENTS.md`** (always loaded as Tier 1).

---

## Section 0.5: Superpowers Bootstrap

Every command **MUST** invoke the superpowers meta-router as the first skill load, before any other skill, agent, or Bash call:

```typescript
Skill("superpowers:using-superpowers"); // meta-router — sets discipline + announce pattern
```

This loads the discipline-skill index and the "announce-before-action" rule. Domain skills (`debugger`, `planning`, `performance-optimization`, `senior-architect`, …) load **after** the superpowers method layer, per § 12 (Skill invocation order).

Exceptions:
- `/prime` is a context loader — it only **recommends** the next command run the bootstrap.
- Subagents skip the bootstrap (superpowers `<SUBAGENT-STOP>` directive).

---

## Section 0.7: Path Conventions

Specs, plans, and learnings produced by the superpowers pipeline use these canonical paths:

| Artifact | Path | Producer |
|---|---|---|
| Design spec | `${paths.planDir}/specs/YYYY-MM-DD-<topic>-design.md` | `Skill("superpowers:brainstorming")` |
| Implementation plan | `${paths.planDir}/YYYY-MM-DD-<topic>-plan.md` | `Skill("superpowers:writing-plans")` |
| Session handoff | `.graph-powers/HANDOFF.md` | `/evolve handoff` |
| Audit report | `docs/AUDIT-REPORT-YYYY-MM-DD.md` | `/debug audit` |
| Phase tracker | `.graph-powers/logs/progress.md` | `/implement` (append on phase complete) |

Folders are created on first write. `.graph-powers/logs/progress.md` is the chronological phase tracker; `/implement` appends to it when a phase completes.

---

## Section 1: Quality Gates

| Timing | Gates |
|---|---|
| After each task | type-check |
| After each phase | type-check + lint |
| Final | type-check + lint + tests |

```bash
# Resolve from config
${tooling.packageManager} run ${tooling.typeChecker}    # or `bunx tsgo`, `npx tsc --noEmit`, etc.
${tooling.packageManager} run lint                       # or direct: `bunx biome check`, `eslint .`
${tooling.packageManager} run test                       # only when test runner configured
```

> **Pre-commit:** run formatter+linter on every manually edited file. Most linters (`biome`, `eslint`) treat errors as build-breaking — they fail CI immediately.

---

## Section 1.5: Verification Gate (evidence before completion)

Before any command (or phase inside a command) claims success, invoke:

```typescript
Skill("superpowers:verification-before-completion");
```

The skill enforces: a verification command was actually run, its full stdout + exit code are captured, and the claim of "done / fixed / passing" cites that evidence. No claim without evidence.

Apply at:
- Tail of any command that mutates code (`/implement`, `/debug` fix mode, `/design` Phase 2, `/perf fix`, `/evolve`).
- Inside `/verify` Phase 0 — gates pass condition becomes evidence-bound, not assumption-bound.
- Per-phase tail inside `/implement` Mode B and `/debug` fix mode.

Anti-pattern: marking a task complete after only inspecting code; running `bun run type-check` then forgetting to check exit code; assuming a fix worked because the diff "looks right".

---

## Section 2: Complexity Routing

| Level | Indicators | Mode |
|---|---|---|
| L1-L2 | Single file, known pattern, trivial | Direct — no agents |
| L3 | Multi-file, single domain | 1 background agent |
| L4-L5 | Multi-domain, parallel changes | 2-3 parallel agents |
| L6+ | Architecture, multi-service | Coordinator + specialist agents; use Agent Teams only when the runtime exposes them |

---

## Section 3: Agent Assignment Matrix

| Task type | Agent | Background? |
|---|---|---|
| Backend handler/service/auth/DB | `debugger` | No (write-capable) |
| React/components/UI/styling | `frontend-specialist` | No (write-capable) |
| Schema/migrations/indexes | `debugger` | No |
| Tests/QA | `debugger` | No |
| Performance/security/SEO | `performance-optimizer` | No |
| Codebase patterns/files lookup | `explorer` | **YES — mandatory** |
| External docs/packages | `librarian` | **YES — mandatory** |
| Architecture consultation | `evaluator` (Mode 3) | Caller decides |

Read-only agents (`explorer`, `librarian`) **must** use `run_in_background: true`.

**Explorer vs Librarian:**

| Question | Agent |
|---|---|
| What exists in this codebase? | `explorer` |
| How does this library/API work? | `librarian` |
| Both needed? | Spawn both in same message |

> `explorer` = custom agent (`${CLAUDE_PLUGIN_ROOT}/agents/explorer.md`), NOT the built-in `Explore`. Use `subagent_type: "explorer"`.

---

## Section 4: WISC Context Load

Before any task, load the right tier:

| Domain | Command | Loads |
|---|---|---|
| Frontend | `/prime frontend` | The project's design rule + the nearest `AGENTS.md` under `${paths.frontendRoot}` + only the references they name |
| Backend / API / data | `/prime backend` | The project's backend, data and stability rules from `${rulesDir}/` + targeted references |
| Full-stack / multi-domain | `/prime` (auto) or `/prime fullstack` | Intent-based Tier 2 + exact Tier 3 only when justified |
| Continuing prior session | Read `.graph-powers/HANDOFF.md` first | — |

**Tier 3 (read on demand only):**
- `Skill("senior-architect")` — runtime and environment shape, architecture decisions, trade-off analysis
- `Skill("uxmaster")` — UX judgement: conversion, onboarding, hierarchy, retention
- `${rulesDir}/` — the project's own rules and references, including anything it keeps outside skills

---

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

---

## Section 6: Skill-to-Domain Matrix

Single source of truth — used by `/implement`, `/design`, `/verify`, `/debug audit`.

| Domain / task signal | Primary skill | Supporting skills |
|---|---|---|
| Bug fix / runtime error / regression | `debugger` | `second-opinion` when a fix keeps not sticking |
| Plan / decompose / architecture decision | `planning` (via `/plan`) | `senior-architect`, `senior-prompt-engineer` when the feature is an LLM feature |
| Delegation / who runs what | `agent-orchestration` | — |
| UI / component / page / design system | the project's design rule, plus the external `impeccable` plugin | `uxmaster` for the direction, `debugger` if mid-fix |
| UX direction / conversion / onboarding | `uxmaster` | — |
| Performance / SEO / security baseline / Core Web Vitals / bundle | `performance-optimization` | `librarian` for external tool docs |
| Browser verification / E2E evidence | `webapp-testing` | `verification` agent |
| Astro project surfaces | `astro` (when `project.stack` names Astro) | — |
| Database, provider or deploy specifics | the project's own skill, when it has one | `librarian` for external docs |
| Skill creation / iteration | `skill-creator` | — |
| Harness wiring audit | `harness-audit` | `skill-improver` agent |
| Prompt engineering / LLM apps / RAG | `senior-prompt-engineer` | — |

If domain isn't listed → no skill applies; use rules + tool docs directly.

---

## Section 7: Parallel Agent Spawn pattern

Before any parallel batch, invoke:

```typescript
Skill("superpowers:dispatching-parallel-agents");
```

This skill enforces: distinct scope per agent, shared return contract, single-message dispatch, stopping conditions. The numbered rules below are the local the project quick-reference.

When invoking 2+ agents in parallel:

1. **Single message** — all `Agent()` calls in the same response (concurrent execution).
2. **Background flag** — `run_in_background: true` for read-only agents (`explorer`, `librarian`, audit dimensions, codex:rescue diagnose).
3. **Foreground only** when the agent must write/edit (`frontend-specialist`, `debugger` in fix mode).
4. **Distinct scope** — each agent prompt has non-overlapping investigation area; otherwise merge into one agent.
5. **Same return contract** — all agents in a parallel batch return findings in the same format (table, columns, severity scale) so consolidation is mechanical.
6. **Maximum 5 spawns per user request** (per CLAUDE.md stopping conditions). At 5 → checkpoint with user.

Anti-pattern: spawning agents serially across multiple messages → loses parallelism + multiplies overhead.

---

## Section 8: Sequential Phase Gating pattern

When phases have dependencies (Phase N requires Phase N-1 output):

```
Phase N-1 → produce artifact → checkpoint gate → Phase N → ...
```

Each gate verifies:
- Required artifact present (file written, agent returned, tests passed)
- Quality threshold met (gate output matches contract)
- No regression in prior phase output

If a gate fails → STOP. Don't proceed silently. Either:
- Re-run prior phase with corrected scope
- Escalate to evaluator (Mode 3)
- Switch to `/debug recover`

Never collapse phases when their outputs feed each other (e.g., schema → API → UI).

---

## Section 9: Verdict Matrix template

Used by `/verify` to consolidate signals from gates + agents + reviews into a single ship/no-ship verdict.

```markdown
## Verdict — {feature/task}

| Signal | Source | Status | Notes |
|---|---|---|---|
| Type-check | `${tooling.typeChecker}` | PASS / FAIL | {output tail or error count} |
| Lint | `${tooling.linter}` | PASS / FAIL | {error count} |
| Tests | `${tooling.testRunner}` | PASS / FAIL | {N passed / N failed} |
| Static analysis | `/debug` | PASS / FAIL / N issues | {summary} |
| Performance | `/perf` | PASS / FAIL | {Lighthouse / CWV} |
| E2E | `/debug frontend` | PASS / FAIL | {snapshots captured / regressions} |
| Spec compliance | manual or eval | PASS / FAIL | {requirements satisfied?} |
| Codex review | `codex:rescue` | PASS / FAIL / N findings | {by severity} |
| Codex adversarial | `codex:rescue` adversarial-review | PASS / FAIL / N findings | {by severity} |
| Architecture review | `evaluator` Mode 3 | PASS / WARNINGS | {warnings if any} |

## Decision
- **Ship** if: all PASS + no P0/P1 findings unresolved
- **Hold** if: any FAIL or unresolved P0/P1
- **Ship with follow-up** if: only P2/P3 findings + tracked in tasks

## Open follow-ups
- {list of P2/P3 to schedule}
```

---

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

---

## Section 11: Guardrails Index

> Quick-reference map. Read the canonical source before applying.

| Guardrail | Canonical location | Trigger |
|---|---|---|
| Stability checklist A-L | `${rulesDir}/stability.md` | Any code change |
| DB FK index requirement | `${rulesDir}/database.md` | Schema changes |
| Render mode + polling + mutations | `${rulesDir}/DESIGN.md` | Page/route changes |
| RLS / auth model | `${rulesDir}/database.md` + `${rulesDir}/backend.md` | Auth/data changes |
| Webhook idempotency | `${rulesDir}/integrations.md` | Webhook handlers |
| Design tokens / no hex / mobile scroll owner | `${rulesDir}/DESIGN.md` | Style changes |
| Project-specific anti-patterns | `Skill("debugger")` → `${CLAUDE_PLUGIN_ROOT}/skills/debugger/references/anti-patterns.md` | Per-project bugs |
| Pre-commit formatter/linter | `${tooling.linter}` per AGENTS.md | Every commit |

---

## Section 11.5: Code graph (`code-review-graph`) — canonical contract

> Structural map of the repo (Tree-sitter → SQLite) used to answer "does this already exist?" and
> "what does changing this break?" without a grep sweep. Consumed by `/plan` Step 0 and `/verify`
> Phases 1.5 / 1.6 / 4. Canonical here; those commands reference this section instead of restating it.
>
> Local-first: graph lives in `.code-review-graph/` (gitignored + dockerignored). No cloud calls, no
> telemetry. Never pass `--embedding-provider openai|google|minimax` — those transmit source-derived
> text off-machine.

### Invocation

```bash
CRG="python -m code_review_graph"      # console script is NOT on PATH in Git Bash — use the module form
export PYTHONIOENCODING=utf-8          # REQUIRED on Windows: the Rich panels crash with
                                       # UnicodeEncodeError on the cp1252 console otherwise
$CRG update -q                         # incremental re-parse (seconds). ALWAYS run before querying
$CRG status                            # nodes/edges/files + "Built at commit" — the staleness check
```

Not installed / no `.code-review-graph/graph.db` → the graph steps are **SKIPPED, never blocking**.
Record `SKIPPED (graph unavailable)` and use the grep fallback. Rebuild from scratch with
`$CRG build` (~2 min on this monorepo). Install: `python -m pip install code-review-graph`.

### Query cookbook

| Question | Command |
|---|---|
| Does this capability already exist? | `$CRG search "<terms>" --kind Function\|Class\|File --limit 15` |
| Who calls this function? | `$CRG query callers_of "<symbol>"` |
| Who imports this module? | `$CRG query importers_of "<file>"` |
| What does this file pull in? | `$CRG query imports_of "<file>"` |
| Which tests touch it? | `$CRG query tests_for "<symbol>"` (see limits) |
| Blast radius of a change | `$CRG impact --files <f1> <f2> --depth 2 --max-results 60` |
| Risk-scored diff summary | `$CRG detect-changes --base <base> --brief` |
| Layer overview (L4+ framing) | `$CRG architecture --detail-level minimal` |
| Orphans after a refactor | `$CRG dead-code --kind Function --file-pattern "<path>" --limit 20` |
| Rename impact before doing it | `$CRG refactor rename --old-name <a> --new-name <b> --kind Function` |

Output is JSON and can be large. Always bound it (`--limit` / `--max-results`, pipe through `head`)
and quote only the `file_path:line_start` rows you act on — dumping raw graph JSON into the report
defeats the purpose of using it.

`--base` for `detect-changes` / `impact`: `HEAD~1` for the last commit, `$(git merge-base main HEAD)`
for the whole branch. On a long-lived `dev-test` the merge-base form can span 1000+ files and caps at
500 functions (`CRG_MAX_CHANGED_FUNCS`) — prefer explicit `--files` from the diff when that happens.

### Limits — where the graph is NOT authoritative `[HARD]`

The parser resolves **static** imports and call sites. It does not see anything reached through a
string or assembled at runtime. For these five, **grep is the authority and the graph is the hint**:

1. tRPC client paths (`trpc.<domain>.<proc>.useQuery`) — the procedure↔caller edge does not exist.
2. TanStack Router route ids / `to="/…"` targets.
3. Drizzle column reads (a column is not a node).
4. Anything behind a dynamic `import()`, a registry map, or a string key.
5. **`tests_for` is incomplete** — verified on this repo: `applyMovement` returns 0 tests while
   `stock-service.test.ts` references it 7×. A zero here means "no static edge found", NEVER
   "untested". Confirm with `grep -rln "<symbol>" apps/*/src/**/*.test.ts*` before claiming a test gap.

A graph result therefore **widens** the search and **never narrows** a safety check: it may add
consumers you would have missed, but an empty result never authorizes skipping the grep that a
`[HARD]` rule (tenant filter, PII gate, financial mirror) depends on.

---

## Section 12: Skill invocation order

When a task touches multiple domains, invoke skills in this order:

1. **Meta layer** — `superpowers:using-superpowers` (always first, per § 0.5)
2. **Superpowers method** — `superpowers:brainstorming` / `writing-plans` / `executing-plans` / `subagent-driven-development` / `test-driven-development` / `systematic-debugging` / `verification-before-completion` / `requesting-code-review` / `receiving-code-review` / `dispatching-parallel-agents` / `using-git-worktrees` / `finishing-a-development-branch` / `writing-skills` (HOW: discipline + format)
3. **Harness knowledge** — `planning`, `debugger`, `senior-architect` (WHAT: layer ordering, anti-pattern catalogue, architecture trade-offs)
4. **Domain skills** — the project's own database/provider/deploy skills, `performance-optimization`, `webapp-testing`, `senior-prompt-engineer`
5. **Implementation and design skills last** — `uxmaster`, the external `impeccable` plugin, `skill-creator`

Multiple skills can be loaded in the same response; order matters because earlier skills set context that later ones build on. The pipeline `spec (brainstorming) → plan (writing-plans) → execute (executing-plans / subagent-driven-development) → verify (verification-before-completion) → review (requesting-code-review / receiving-code-review) → finish (finishing-a-development-branch)` is the canonical flow for any L3+ feature work.
