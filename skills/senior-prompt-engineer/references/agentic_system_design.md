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

## 2. The file contract, and preloading

Both live in `SKILL.md` — the frontmatter shape and body sections in § 2, the preload-versus-`Skill()`
decision in § 8. They are not repeated here; this file starts where those stop, at the four choices
below that the contract leaves open.

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
| `opus` | Architecture, ambiguous reasoning, multi-lens evaluation | `graph-powers:evaluator`, `graph-powers:debugger`, `graph-powers:project-planner`, `graph-powers:verification`, write-capable specialists |
| `sonnet` | Review and structured analysis against a clear rubric | `graph-powers:security-reviewer`, `graph-powers:skill-improver` |
| `haiku` | Fast read-only lookup, low stakes | nothing in this plugin today — the two researchers judge what they find |
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

## 8. One anti-pattern that only exists at this level

Nesting is allowed: a subagent may spawn a subagent, to a default depth of three layers below the
main conversation. That is the trap, not a capability to reach for — a chain that spawns at every
level exhausts `graphGuardrails.maxSpawnsPerSession` without anyone having decided to fan out. Spawn
from the level that owns the decision; below L6, a coordinator plus phase gates costs less than a
third layer. The rest of the anti-patterns are in `SKILL.md` § 11.

---

## 9. Cross-references

- Spawn template + Context Handoff schema: `agent-handoff-contracts.md`
- Parallel batch return contract: `parallel-batch-contracts.md`
- Application-level prompt patterns (RAG, few-shot, CoT): `prompt_engineering_patterns.md`
- LLM eval harness: `llm_evaluation_frameworks.md`

Owner: `senior-prompt-engineer` skill.
