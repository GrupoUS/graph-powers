---
name: senior-prompt-engineer
description: "Use when writing or revising an agent file, a handoff schema, a spawn template or a batch return contract — anything about how the harness is built rather than how it is run. Also for LLM features inside the product: RAG, structured extraction, eval harnesses. Not for deciding how many agents a task needs, and not for filling in an ordinary delegation prompt."

---

# Senior Prompt Engineer — designing the harness

> **Running the harness is `${CLAUDE_PLUGIN_ROOT}/references/execution-floor.md`**, which is in force
> without being invoked: when to delegate, how wide, who owns which file, and the seven sections
> every spawn prompt carries. This skill is the other half — how an agent file, a handoff schema or
> an LLM feature is *built*. Loading it to write one ordinary spawn prompt is sixteen kilobytes
> spent on something the floor already answered.

Anchored to the Claude Code documentation for [sub-agents](https://code.claude.com/docs/en/sub-agents),
[skills](https://code.claude.com/docs/en/skills) and [agent teams](https://code.claude.com/docs/en/agent-teams).
Project-agnostic: the host project supplies stack rules through `${rulesDir}/`.

## 1. Scope

Three things: the shape of an agent file, the contract between agents, and prompt engineering for a
product feature. Domain knowledge is not here — it lives in the skill that owns that domain.

## 2. The agent file

```markdown
---
name: <unique-lowercase-hyphens>          # identical to the filename
description: <when to delegate — front-load the use case>
tools: <explicit allowlist>               # without it the agent inherits everything, Write included
disallowedTools: Write, Edit              # inline, on anything that judges or researches
model: opus | sonnet | haiku              # never `inherit` in a verifier
---

# <Agent Name>

## Role            — one paragraph: who it is, what it owns
## Iron Laws       — non-negotiable invariants, at most seven
## Phases          — numbered, each producing a checkpoint artefact
## Handoff Format  — one line pointing at references/agent-handoff-contracts.md
## Stopping Conditions — what triggers BLOCKED, including a max-attempts cap
```

Only `name` and `description` are required; everything else has a documented default. The optional
fields worth knowing, because this plugin's twelve agents use them: `skills:` (§ 8), `memory:`,
`effort:`, `color:`, `background:`, `maxTurns:`, `mcpServers:`, `hooks:`, `initialPrompt:`,
`isolation:`, `permissionMode:`.

**The `memory:` trap.** `memory:` auto-enables `Read`, `Write` and `Edit` for managing the memory
file — *on top of* the `tools:` allowlist. An agent declaring `tools: [Read]` plus `memory: project`
resolves write-capable, against its own description. Declare `disallowedTools` alongside it or drop
the field.

**Forbidden in the body:** re-declaring the handoff schema or the spawn template (they live in
`references/agent-handoff-contracts.md`), repeating a preloaded skill, or restating a project rule
the agent could cite.

**One exception, and it is safety-critical.** Subagents do not inherit `CLAUDE.md`, a subdirectory
`AGENTS.md`, or anything the parent loaded. `[HARD]` invariants — git rails, tenant boundaries,
declared tooling — are mirrored into the body on purpose, each with a provenance comment
(`<!-- mirror of safety-floor.md §N -->`) so the source stays findable and a divergence is visible.
`${CLAUDE_PLUGIN_ROOT}/references/safety-floor.md` explains why that duplication is the cheaper
mistake.

## 3. Descriptions, which is where auto-invocation lives

The description is not a summary. It is the only thing the model reads when deciding whether to
delegate, and it is also what a person browses in `/agents`.

- **Front-load the use case.** `description` plus the optional `when_to_use` are truncated at 1,536
  characters in the listing (configurable via `skillListingMaxDescChars`) — what is cut is what is
  last.
- **Name the trigger, not the capability.** Include the words a user would actually type.
- **Say what it is *not* for**, whenever a neighbouring agent could plausibly claim the same work.
  `explorer` (codebase only) and `librarian` (external only) are only distinguishable because both
  descriptions say so.

Bad: `"Powerful research agent."` — generic descriptions do not auto-trigger, and the documentation
says so in as many words.

Good: `"Internal codebase researcher. Use when planning a feature, tracing a dependency, or mapping
existing patterns. Never searches the internet."`

## 4. The spawn prompt

Seven sections, defined once in `${CLAUDE_PLUGIN_ROOT}/references/execution-floor.md` §4 — including
the five mandatory context fields, whose absence is why an agent rediscovers what the parent already
knew. Full semantics and edge cases: `references/agent-handoff-contracts.md § 1`.

Nothing here restates them, and neither should a command.

## 5. What comes back

Every agent returns the canonical Context Handoff. Full schema, status semantics and anti-patterns:
**`references/agent-handoff-contracts.md`**.

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

Four invariants: confidence below 3 on a critical finding forces `BLOCKED`; `BLOCKED` requires a
mitigation, even if the mitigation is `ESCALATE`; `REVISION_REQUIRED` is reviewer-only; and
`Quality gates: []` on a `COMPLETED` is a defect, because no evidence is no claim.

## 6. A batch returns one shape

Two or more agents in one message add a shared findings table to the handoff:

```markdown
| # | Finding | Confidence (1-5) | Source | Impact (Low/Med/High) |
```

Review batches add `Severity (P0-P3)`. Same column order for every member — consolidation has to be
mechanical, and an ad-hoc per-agent shape is how a finding gets lost. Column semantics, the
confidence scale and the consolidation rules: **`references/parallel-batch-contracts.md`**. The
spawn rules themselves belong to the execution floor, not here.

## 7. Coordinator recovery

A coordinator (`${CLAUDE_PLUGIN_ROOT}/commands/implement.md § 6`) that receives `REVISION_REQUIRED`
forwards it to the specialist once, then a second and final time. There is no third: it returns
`BLOCKED: <criterion>` to the main agent, which runs `/debug recover`. Never escalate to the user
mid-loop — recovery triages first. The rule recurses if a coordinator delegates to a coordinator.

Full semantics: `references/agent-handoff-contracts.md § 4`.

## 8. Preloading a skill into an agent

Subagents do not inherit the parent's skills; `skills:` lists them explicitly and the **full body**
is injected at startup, which is what makes the choice cost something.

| Pattern | When | Cost |
|---|---|---|
| `skills: [<name>]` in frontmatter | The agent needs it on essentially every invocation | Injected once, always paid |
| `Skill()` in the body | Needed only on some routes | Loaded when invoked |

Rule of thumb: preload only if removing the skill would break more than half of that agent's
invocations. In this plugin four agents pass that test, and each preloads its own domain skill —
none preloads this one, because designing prompts is not what they do.

A skill carrying `disable-model-invocation: true` cannot be preloaded: it is skipped, with a debug
log nobody is reading.

## 9. LLM features in the product

- Patterns — XML structuring, few-shot, chain-of-thought, structured output through tool use, prompt
  caching: `references/prompt_engineering_patterns.md`.
- Eval harnesses — frozen test sets, graders, RAG metrics: `references/llm_evaluation_frameworks.md`.
- Anthropic SDK code, model ids, pricing, migrations: the bundled `claude-api` skill, which
  auto-triggers on the import.

## 10. References

| File | Scope |
|---|---|
| `references/agent-handoff-contracts.md` | Spawn template, handoff schema, status invariants, coordinator recovery |
| `references/parallel-batch-contracts.md` | Findings table, confidence and severity scales, consolidation |
| `references/agentic_system_design.md` | Subagent versus agent team, isolation, model selection |
| `references/prompt_engineering_patterns.md` | Application-level patterns |
| `references/llm_evaluation_frameworks.md` | Eval harnesses and RAG metrics |

## 11. Anti-patterns

| Anti-pattern | Symptom | Fix |
|---|---|---|
| Description written as a summary | The agent never auto-triggers | Front-load the use case, name the trigger words |
| `SKILL.md` past 500 lines | Context spent before the work starts | Move the detail into `references/` |
| Handoff schema re-declared in an agent body | Twelve copies, drifting | One line pointing at the contract |
| `memory:` beside a read-only `tools:` list | A researcher that can write | Add `disallowedTools`, or drop `memory:` |
| `disable-model-invocation: true` on a preloaded skill | Silently skipped | Remove the flag, or invoke it by hand |
| Coordinator with no iteration cap | `REVISION_REQUIRED` forever | § 7 — two resubmits, then `BLOCKED` |
| Spawning before the answer is needed | The agent finishes and idles | Background it, per the execution floor |
| Confidence 2 or below treated as fact | A plan built on a guess | Flag `[ASSUMED]` and ask, per `${CLAUDE_PLUGIN_ROOT}/skills/planning/SKILL.md § Stopping & red flags` |
