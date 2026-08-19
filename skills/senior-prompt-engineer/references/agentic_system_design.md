# Agentic System Design (Claude Code)

> Subagent vs. agent team, skill preload vs. body-level invocation, isolation modes, model selection.
> Anthropic-anchored. Scoped to a host project's `.claude/agents/` and to this plugin's `skills/`.

References:
- Subagents: https://code.claude.com/docs/en/sub-agents
- Skills: https://code.claude.com/docs/en/skills
- Agent teams: https://code.claude.com/docs/en/agent-teams

---

## 1. Subagent vs. Agent Team

| Construct | When to use | Coordination | Lifetime |
|---|---|---|---|
| **Subagent** (`.claude/agents/*.md`) | Single-session task that floods main context with research/logs you won't reference again. | Parent ↔ child via tool result. | One spawn per Agent() call. |
| **Agent Team** (`TeamCreate` + `TaskCreate`) | Multi-agent coordination across separate sessions, with task dependencies. L6+ work. | Coordinator + workers via `SendMessage` and `TaskUpdate`. | Persists until `TeamDelete`. |

> **Anthropic doc:** "Subagents work within a single session; agent teams coordinate across separate sessions."

**Choosing:**
- L1-L5 → subagents.
- L6+ with parallel sprints + dependencies → agent team.
- Single specialist with no dependencies → always subagent (cheaper).

---

## 2. Subagent file contract

Required per Anthropic spec:

```markdown
---
name: <unique-lowercase-hyphens>
description: <when Claude should delegate — front-load use case>
tools: <allowlist OR omit to inherit all>          # OR disallowedTools
model: opus | sonnet | haiku | inherit             # default: inherit
skills: [<skill-name>, …]                          # optional preload
permissionMode: default | acceptEdits | plan | …   # optional
maxTurns: <int>                                    # optional cap
isolation: worktree                                # optional sandbox
---

# <Agent Name>

[System prompt — 50-300 lines. Sections: Role · Iron Laws · Phases · Handoff · Stopping]
```

**Body conventions in this repo:**

1. **Role** — one paragraph: who the agent is, what it owns.
2. **Iron Laws** — non-negotiable invariants (e.g., "never write outside `src/`", "always finish with quality gate").
3. **Phases** — numbered execution flow.
4. **Handoff Format** — link to `agent-handoff-contracts.md` (do NOT redeclare schema).
5. **Stopping Conditions** — explicit triggers for `BLOCKED` / escalation.

**Forbidden:** repeating context that the `senior-prompt-engineer` skill already preloads.

---

## 3. Skill preload (`skills:` frontmatter) vs. body-level `Skill()`

> **Anthropic doc:** "Subagents don't inherit skills from the parent conversation; you must list them explicitly. The full content of each skill is injected into the subagent's context, not just made available for invocation."

| Pattern | When | Cost | Typical example |
|---|---|---|---|
| **Preload** (`skills: [<name>]` in frontmatter) | The agent **always** needs the skill — every invocation. Process skills (planning methodology, debugging methodology, agent-orchestration). | Skill body injected at startup; counts against subagent context budget once. | Orchestrator preloads `senior-prompt-engineer` + `planning`; debugger preloads its methodology skill. |
| **Body-level `Skill()` call** | The agent **conditionally** needs the skill (depends on routing). Domain skills (framework-specific, design system, brand voice). | Skill body loaded only when invoked; cheaper if skill is unused. | A frontend specialist calling a UI/design-system skill only on UI tasks. |

**Rule of thumb:** if removing the skill would break >50% of the agent's invocations, preload it. Otherwise body-level.

**Precondition for preloading:** target skill must NOT set `disable-model-invocation: true` (Anthropic constraint).

---

## 4. Tool restriction patterns

| Pattern | Frontmatter | Use case |
|---|---|---|
| **Inherit all** | omit `tools` and `disallowedTools` | General-purpose agent |
| **Allowlist** | `tools: Read, Glob, Grep` | Read-only researcher (`explorer`, `librarian`) |
| **Denylist** | `disallowedTools: Write, Edit` | Inherits all minus writes |
| **Restricted Agent spawn** | `tools: Agent(worker, researcher), Read` | Coordinator can only spawn specific agents |

**Typical splits:**
- A codebase researcher allowlists Read/Grep/Glob/Bash; forbids WebFetch/external search MCPs.
- A docs/web researcher allowlists WebFetch + external search/docs MCPs; forbids local filesystem read.
- A read-only consultant allowlists Read/Grep/Glob.
- Write-capable specialists (frontend, debugger fix mode) inherit all tools.

---

## 5. Model selection

| Model | When | Typical agents |
|---|---|---|
| `opus` | Architecture, ambiguous reasoning, multi-lens evaluation | orchestrator, evaluator, oracle, debugger, write-capable specialists, planner, verification |
| `sonnet` | Code review, structured analysis with clear rubric | code reviewer |
| `haiku` | Fast read-only search, low-stakes lookups | codebase explorer, docs/web librarian |
| `inherit` | When agent should match parent's capability tier | rare |

**Cost guidance:** prefer `haiku` for read-only research agents; tokens add up across parallel batches.

---

## 6. Isolation (`isolation: worktree`)

> Use when the subagent might leave the repo in a bad state (parallel experiments, destructive refactors).

```yaml
isolation: worktree
```

Anthropic doc: "Run the subagent in a temporary git worktree, giving it an isolated copy of the repository. The worktree is automatically cleaned up if the subagent makes no changes."

**Typical use case:** a fix-mode command that spawns one optimizer/refactorer per cluster with `isolation: "worktree"` so multiple experiments run in parallel without merge conflicts.

---

## 7. Subagent ↔ Skill bidirectional pattern

| Approach | System prompt | Task | Context source |
|---|---|---|---|
| **Subagent invokes skill in body** | Subagent's markdown body | User-provided | `Skill()` tool call at runtime |
| **Subagent preloads skill (`skills:` field)** | Subagent's markdown body | User-provided | Skill content injected at startup |
| **Skill runs in forked subagent (`context: fork` in skill frontmatter)** | Subagent type's body (e.g., `Explore`) | The skill's own content | The skill drives the agent |

The third pattern is **not the default** here — keep skills as content (loaded by agents) and use built-in `Explore`/`Plan` for ad-hoc forking, unless a host project explicitly opts into `context: fork` skills.

---

## 8. Anti-patterns

| Anti-pattern | Symptom | Fix |
|---|---|---|
| **Vague description** | Skill/agent never auto-triggers | Front-load use case in description; include trigger phrases ("Use when…") |
| **Body bloat** | SKILL.md > 500 lines | Move detail to `references/<topic>.md`; SKILL.md is the index |
| **Re-declared schemas** | Three agents define their own "Context Handoff" block | Single SSOT in this skill; agents link only |
| **Auto-trigger on `disable-model-invocation: true`** | Skill listed in `skills:` preload silently skipped | Remove the flag; or invoke manually only |
| **Subagent spawning subagent** | Doesn't work — Anthropic spec | Use coordinator + agent team for nested orchestration |
| **Spawning eagerly when result not yet needed** | Wasted parallelism — agent finishes idle while parent works on something else | Use `run_in_background: true` for read-only agents per `shared-context.md § 7` |

---

## 9. Cross-references

- Spawn template + Context Handoff schema: `agent-handoff-contracts.md`
- Parallel batch return contract: `parallel-batch-contracts.md`
- Application-level prompt patterns (RAG, few-shot, CoT): `prompt_engineering_patterns.md`
- LLM eval harness: `llm_evaluation_frameworks.md`

Owner: `senior-prompt-engineer` skill.
