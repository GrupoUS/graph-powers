---
name: senior-prompt-engineer
description: "Designing the harness itself: subagent contracts, handoff schemas, orchestrator spawn templates, parallel-batch return contracts, and coordinator failure recovery. Also covers application-level LLM features (RAG, structured outputs, eval harnesses) and systematic refactor method — extract, deduplicate, simplify, test-gated."

---

# Senior Prompt Engineer — Claude Code Agent Orchestration SSOT

> Single source of truth for **how Claude Code agents talk to each other**.
> Anchored to Anthropic official docs (sub-agents, skills) — see `references/agentic_system_design.md`.
> Project-agnostic: examples use placeholders. Host project supplies stack-specific rules via `.claude/CLAUDE.md` + `${rulesDir}/`.

---

## 1. Purpose & scope

This skill governs three things:

1. **Subagent design** — what every `.claude/agents/*.md` file must look like (frontmatter + body sections).
2. **Inter-agent handoff** — the canonical structured shape every agent returns and the 5 mandatory context fields every spawn injects.
3. **Multi-agent orchestration** — parallel-batch return contracts, coordinator failure-recovery, escalation paths.

Out of this skill's scope: domain knowledge (lives in project-specific skills — framework, design system, brand voice, debugger, performance, etc.). Application-level prompt engineering (RAG / few-shot / CoT / evals) is documented here only as a pointer to references.

---

## 2. Subagent file contract

Every `.claude/agents/<name>.md` must follow this shape:

```markdown
---
name: <unique-lowercase-hyphens>
description: <when Claude should delegate — front-load use case>
tools: <allowlist>                    # OR `disallowedTools` — see references/agentic_system_design.md § 4
model: opus | sonnet | haiku | inherit
skills: [<skill-name>, …]             # optional preload — see § 8 below
permissionMode: default | plan | …    # optional — Anthropic spec
maxTurns: <int>                       # optional cap
isolation: worktree                   # optional sandbox
color: <ui hint>
---

# <Agent Name>

## Role
[One paragraph — who the agent is, what it owns.]

## Iron Laws
[Non-negotiable invariants — bullet list, ≤ 7 items.]

## Phases
[Numbered execution flow. Each phase produces a checkpoint artifact.]

## Handoff Format
[ONE LINE pointer to `references/agent-handoff-contracts.md`. Do not redeclare schema.]

## Stopping Conditions
[Explicit triggers for `BLOCKED` / escalation. Always include max-attempts limit.]
```

**Required fields:** `name`, `description`. Everything else has a default per Anthropic spec.

**Pre-deploy gate** for any agent file: `${rulesDir}/execution.md § Agents & Dispatch → Agent Quality Checklist` (complementary — this § defines the *shape*; that checklist is the *gate*).

**Forbidden in body:**
- Re-declaring the Context Handoff schema (it lives in `references/agent-handoff-contracts.md`).
- Re-declaring the 5-field spawn template (same).
- Repeating content from a preloaded skill (waste of context budget).
- Re-stating generic project rules the agent could cite instead — reference `${rulesDir}/<file>.md` by section, don't copy. **Exception (safety-critical):** `[HARD]` invariants (git rails, tenant, tooling) MUST be hardcoded **defensively** — subagents do NOT inherit `.claude/CLAUDE.md` or subdir `AGENTS.md` (see `${rulesDir}/execution.md § Agents & Dispatch → Subagent non-inheritance`). Mirror them with a provenance comment (`<!-- mirror of safety-floor.md §N -->`), never silently drop them.

---

## 3. Description guidelines (auto-trigger reliability)

Per Anthropic skills doc, descriptions are loaded into context so Claude knows what's available. They power both:

1. **Auto-invocation** — Claude reads descriptions to decide when to delegate.
2. **The `/agents` Library tab** — humans browse by description.

Rules:

- **Front-load the key use case.** Anthropic doc: "Front-load the key use case: the combined `description` and `when_to_use` text is truncated at 1,536 characters."
- **Include trigger phrases** — "Use when…", "Triggers on…", literal user-language tokens.
- **Be specific.** Generic descriptions ("World-class X for Y") don't auto-trigger — Anthropic explicitly warns this in the troubleshooting section.
- **Stay under 1,536 chars** combined with `when_to_use`.
- **Distinguish similar agents** — `explorer` (codebase-only) vs. `librarian` (external-only) must have descriptions that prevent overlap.

Bad: `"Powerful research agent."`
Good: `"Internal codebase researcher. Use proactively when planning any feature, investigating code structure, or needing to understand existing patterns and conventions. Triggers automatically on research, discovery, impact analysis. NEVER searches the internet."`

---

## 4. Spawn template (5 mandatory context fields)

Every `Agent()` / `Task()` invocation MUST inject these fields. Promoted from `orchestrator.md` to canonical SSOT.

```markdown
## MANDATORY CONTEXT
**Original request:** <verbatim user message>
**User decisions:** <approach choices made so far>
**Prior agent findings:** <1-2 sentence summary per completed agent>
**Current plan state:** <phase N, task X of Y>
**Do NOT redo:** <what prior agents already covered>
```

**Why:** agents without context rediscover what the parent already knows — wastes tokens, conflicts with prior decisions, multiplies parallel-spawn overhead.

Full semantics + edge cases: `references/agent-handoff-contracts.md § 1`.

**Commands MUST link to that file** rather than duplicating the field list — single SSOT.

---

## 5. Handoff Contract Schema

Every agent returns the canonical Context Handoff block (markdown) — and a JSON variant for `/verify` consolidator tooling.

Full schema, status semantics, invariants, anti-patterns: **`references/agent-handoff-contracts.md`**.

Quick reference:

```markdown
## Context Handoff
- **Status:** COMPLETED | BLOCKED | REVISION_REQUIRED
- **Confidence:** 1-5
- **Artifacts:** [{ path, lines, action }]
- **Quality gates:** [{ name, status, evidence }]
- **Decisions:** [{ what, why }]
- **Risks:** [{ desc, mitigation }]
- **Next agent:** <name> | NONE
- **Resume hint:** <one sentence>
```

Hard rules:
1. `confidence < 3` on critical finding → status MUST be `BLOCKED`.
2. `BLOCKED` requires `risks[].mitigation` (or `mitigation: "ESCALATE"`).
3. `REVISION_REQUIRED` is reviewer-only.
4. `Quality gates: []` is a defect on `COMPLETED` (no evidence = no claim).

---

## 6. Parallel-batch shared contract

When ≥2 agents spawn in one message (parallel pattern, `${CLAUDE_PLUGIN_ROOT}/references/shared/070-parallel-agent-spawn.md`), every member returns the standard Context Handoff PLUS a shared **findings table** with these exact columns:

```markdown
| # | Finding | Confidence (1-5) | Source | Impact (Low/Med/High) |
```

Review batches add a 6th column: `Severity (P0-P3)`.

Full consolidation rules, severity scale, tool-precedence, max batch size: **`references/parallel-batch-contracts.md`**.

Hard rules:
1. Same column order across all batch members — consolidation must be mechanical.
2. Each agent investigates a non-overlapping area (otherwise merge into one).
3. Max `graphGuardrails.maxParallelWave` agents in one fan-out (default 5) — see
   `${CLAUDE_PLUGIN_ROOT}/references/shared/070-parallel-agent-spawn.md`, which distinguishes the fan-out width from the
   session total.

---

## 7. Coordinator failure recovery

When an agent-team coordinator (`/implement § 6`) receives `REVISION_REQUIRED` from a specialist:

1. **Iteration 1:** forward reviewer failures to specialist; specialist resubmits.
2. **Iteration 2:** if still `REVISION_REQUIRED`, forward once more — last attempt.
3. **Would-be iteration 3:** coordinator does NOT retry. Returns `BLOCKED: <criterion>` to main agent. Main invokes `/debug recover`.

**Never escalate to user mid-loop.** `/debug recover` triages first.

Same rule applies recursively if a coordinator delegates to another coordinator (rare in this repo).

Full recovery semantics: `references/agent-handoff-contracts.md § 4`.

---

## 8. Skill preload pattern (`skills:` frontmatter)

> Anthropic doc: "Subagents don't inherit skills from the parent conversation; you must list them explicitly. The full content of each skill is injected into the subagent's context, not just made available for invocation."

Two ways for an agent to use a skill:

| Pattern | When | Cost |
|---|---|---|
| **Preload** (`skills: [<name>]` in frontmatter) | Skill **always** needed (every invocation). Process skills (planning, debugging methodology, agent-orchestration). | Body injected once at startup |
| **Body-level `Skill()` call** | Skill **conditionally** needed (depends on routing). Domain skills (framework-specific, design system, brand voice). | Body loaded only when invoked |

**Rule of thumb:** if removing the skill would break >50% of the agent's invocations → preload it.

**Precondition for preloading:** target skill must NOT have `disable-model-invocation: true` in its frontmatter (Anthropic constraint — silently skipped otherwise).

**Default assignments (adapt per host project):**

| Agent role | Preloaded skills (typical) |
|---|---|
| Orchestrator (multi-agent coordinator) | `senior-prompt-engineer`, `planning`, plus any session-memory skill |
| Project planner | `senior-prompt-engineer`, `planning` |
| Evaluator / reviewer | `senior-prompt-engineer` |
| Debugger | project's debugging methodology skill, `senior-prompt-engineer` |

Domain / leaf agents (frontend, backend, perf, code-review, verification, oracle, librarian, codebase explorer) typically keep body-level `Skill()` calls — they're routing-dependent and would waste context preloading prompt-engineering content. Audit per-agent: if removing the skill would break >50% of invocations, preload it.

---

## 9. Application-level prompt engineering

When the host project gains an AI feature (copy gen, RAG over docs, structured extraction):

- **Patterns** (XML structuring, few-shot, CoT, structured output via tool-use, prompt caching, eval-driven prompting): `references/prompt_engineering_patterns.md`.
- **Eval harnesses** (frozen test sets, graders, Karpathy autoresearch loop, RAG-specific metrics): `references/llm_evaluation_frameworks.md`.

For Karpathy-style optimize loops over a target prompt / skill, prefer a project-bound autoresearch skill (frozen harness, append-only `experiments.tsv`, crash discipline) over rolling custom scaffolding.

For migrating Claude API code or building new Anthropic SDK apps, prefer the `claude-api` skill (it auto-triggers on `@anthropic-ai/sdk` imports).

---

## 10. References

| File | Scope |
|---|---|
| `references/agent-handoff-contracts.md` | Spawn template + Context Handoff schema + status invariants + coordinator recovery |
| `references/parallel-batch-contracts.md` | Findings table schema + severity scale + consolidation rules + tool precedence |
| `references/agentic_system_design.md` | Subagent vs. agent team · file contract · skill preload vs. body-level · isolation · model selection · anti-patterns |
| `references/prompt_engineering_patterns.md` | Application-level patterns (XML, few-shot, CoT, tool-use schemas, prompt caching, anti-patterns) |
| `references/llm_evaluation_frameworks.md` | Eval harness patterns + RAG metrics + project conventions for `evals/` |

`scripts/` (`prompt_optimizer.py`, `rag_evaluator.py`, `agent_orchestrator.py`) are dormant stubs reserved for future eval harness automation. Do not extend without a concrete use case.

---

## 11. Anti-patterns

| Anti-pattern | Symptom | Fix |
|---|---|---|
| Vague description | Skill/agent never auto-triggers | Front-load use case + trigger phrases |
| SKILL.md > 500 lines | Context budget waste; Anthropic doc warns "Keep SKILL.md under 500 lines" | Move detail to `references/<topic>.md` |
| Re-declared Context Handoff in agent body | Drift between agents | Link to `references/agent-handoff-contracts.md` |
| `disable-model-invocation: true` on a skill listed in `skills:` preload | Silently skipped | Remove the flag (or invoke skill manually only) |
| Subagent spawning subagent | Doesn't work — Anthropic spec | Use coordinator + agent team |
| Coordinator without max-iteration | Infinite REVISION_REQUIRED loops | § 7 rule (max 2 resubmits) |
| `confidence ≤ 2` proceeding without `[ASSUMED]` flag | Plans built on speculation | Per `${CLAUDE_PLUGIN_ROOT}/skills/planning/SKILL.md § Stopping & red flags` — flag and ask user |
| Parallel batch with ad-hoc per-agent table shape | Manual consolidation, missed findings | Single shared findings schema (§ 6) |

---

## 12. Refactor Methodology (17-step reference)

> Absorbed from the retired `/refactor-code` command and its template (both removed 2026-05-18). Loaded when intent classifies as refactor (rename, extract, eliminate duplication, design-pattern application, dead-code removal).

### Principle

Refactoring **preserves external behavior** while improving internal structure. Prioritize safety over speed. Maintain comprehensive test coverage throughout.

### Steps

1. **Pre-refactoring analysis** — identify the code, the reasons, the dependencies, the usage points; review existing tests and documentation.
2. **Test coverage verification** — write missing tests **before** refactoring; establish baseline; document current behavior with additional tests if needed.
3. **Refactoring strategy** — define goals (perf / readability / maintainability); pick technique (extract method, extract class, rename, move method/field, replace conditional with polymorphism, eliminate dead code); plan in small incremental steps.
4. **Environment setup** — create branch (`refactor/<scope>`); ensure tests pass before starting; set up profilers/analyzers if needed.
5. **Incremental refactoring** — small focused changes one at a time; tests after each; commit working changes frequently with descriptive messages; use IDE refactoring tools when available for safety.
6. **Code quality improvements** — naming conventions; DRY; simplify complex conditionals; reduce method/function length and complexity; improve separation of concerns.
7. **Performance optimizations** — eliminate bottlenecks; optimize algorithms/data structures; reduce unnecessary computations; improve memory usage patterns.
8. **Design pattern application** — apply patterns where beneficial; improve abstraction/encapsulation; enhance modularity and reusability; reduce coupling.
9. **Error handling improvement** — standardize approaches; improve messages and logging; add proper exception handling; enhance resilience and fault tolerance.
10. **Documentation updates** — code comments reflecting changes; revise API docs if interfaces changed; update inline documentation; ensure comments are accurate and helpful.
11. **Testing enhancements** — tests for new code paths; improve existing test quality and coverage; remove or update obsolete tests; ensure tests remain meaningful and effective.
12. **Static analysis** — run linters; static analyzers; security scanners; complexity metrics.
13. **Performance verification** — run benchmarks if applicable; compare before/after metrics; ensure refactor did not degrade performance; document improvements.
14. **Integration testing** — full test suite; integration with dependent systems; edge cases and error scenarios; verify all functionality.
15. **Code review preparation** — review changes for quality + consistency; verify goals achieved; prepare clear explanation; document benefits and rationale.
16. **Documentation of changes** — summary of refactor; breaking changes; new patterns; update project documentation; explain benefits and reasoning for future reference.
17. **Deployment considerations** — feature flags for gradual rollout; rollback procedure; monitoring on refactored components.

### Anti-patterns

- "Big bang" rewrite — always incremental
- No tests before refactor → no safety net
- Mixing refactor with feature changes → unclear blame
- Skipping benchmarks on perf-motivated refactor
- Forgetting to update docs / interface contracts

---

Owner: project-scoped (`${CLAUDE_PLUGIN_ROOT}/skills/`).
