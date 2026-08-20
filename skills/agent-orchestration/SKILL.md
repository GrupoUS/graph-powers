---
name: agent-orchestration
description: "How many agents a task needs and which ones: parallel versus sequential, disjoint file ownership, background read-only research, delegation contracts. Use when the user authorises agents, subagents, parallel work or delegation — including use agentes, subagentes, paralelo, delegue. Not for a trivial single-file fix."

---

# Agent Orchestration

## Purpose

Make Claude Code and Codex use specialist agents consistently without over-delegating. Claude Code may proactively delegate when descriptions and hooks match. Codex subagents require explicit user intent or a skill/command prompt that explicitly asks for spawned agents.

## When to Use

Use this skill for:

- Multi-file or multi-domain implementation plans.
- Research that needs both codebase facts and current external docs.
- Debug audits, regressions, CI failures, or unknown root causes.
- Review batches that benefit from independent perspectives.
- Cloud or background work where one thread per task scope avoids bloated context.

Do not use this skill for:

- L1-L2 edits with one obvious file and a known pattern.
- Tasks where the next step is blocked on a single local file read.
- Parallel write work on the same files.

## Routing Matrix

| Need | Agent | Mode |
|---|---|---|
| Codebase discovery, impact map, existing patterns | `graph-powers:explorer` | read-only, background |
| Current docs, package/API behavior, external best practice | `graph-powers:librarian` | read-only, background |
| Root cause, tests, backend/API/data bug | `graph-powers:debugger` | write-capable only after root cause |
| UI, React components, accessibility, responsive polish | `graph-powers:frontend-specialist` | write-capable, disjoint scope |
| Performance, security, SEO/GEO, bundle, CWV | `graph-powers:performance-optimizer` | measure first |
| Plan synthesis or sprint breakdown | `graph-powers:project-planner` | planning only |
| Adversarial review or architecture tradeoff | `graph-powers:evaluator` | read-only |
| UI/user-flow verification after implementation | `graph-powers:verification` | read-only, after code lands |

## Delegation Contract

Every spawned agent prompt must include these sections:

```markdown
## TASK
<one atomic task>

## EXPECTED OUTCOME
<concrete deliverables and success criteria>

## MANDATORY CONTEXT
**Original request:** <verbatim or concise quote>
**User decisions:** <choices already locked>
**Prior agent findings:** <summaries only>
**Current plan state:** <phase/sprint/task>
**Do NOT redo:** <completed research/work>

## MUST DO
- <requirements>

## MUST NOT DO
- <scope boundaries and forbidden actions>

## RETURN FORMAT
- Context Handoff using `Skill("senior-prompt-engineer")` -> `../senior-prompt-engineer/references/agent-handoff-contracts.md`
- For parallel batches, include `| # | Finding | Confidence (1-5) | Source | Impact (Low/Med/High) |`

## DO NOT REDO
<explicit duplicate work to avoid>
```

For review batches, add `Severity (P0-P3)` as the sixth table column.

## Parallel Patterns

- Spawn `graph-powers:explorer` and `graph-powers:librarian` together when both repo facts and external docs matter.
- Split write-capable agents only by disjoint file ownership or module boundary.
- Keep read-only work in background; wait only when the main task needs the result.
- Cap at 5 spawned agents per user request. If the natural fan-out is larger, cluster the work first.
- In Codex, include explicit prompt text such as: "Spawn one subagent per point, wait for all, and consolidate results."
- In Claude Code, use agent teams only for L6+ work with real dependencies or multi-session coordination.
- Writing a `Workflow({ script })` by hand rather than calling one by name: read
  `${CLAUDE_PLUGIN_ROOT}/references/shared/130-workflow-authoring.md` first, and check the script
  with the command it names before invoking it. A workflow script is mostly agent prompts written as
  template literals, so one backtick inside prose about code ends the literal and the whole call
  fails at parse — after you have written it, and before anything runs.

## Codex Hook Bridge

Codex repo hooks use `UserPromptSubmit` to classify complex or agent-oriented prompts and inject the routing contract before the model acts. This is the supported bridge for Cloud-like proactivity: the hook can add context, log the routing decision, and remind the parent agent to spawn explicit subagents when the user has authorized agents/parallel work.

The hook must not claim it can silently spawn agents. If no explicit agent/parallel/delegation intent is present, the injected context is a routing hint only: keep work local or ask for explicit delegation consent when parallel subagents materially change the workflow.

## Cloud Guidance

- Use one Codex Cloud/Cursor Cloud thread per task scope.
- Avoid concurrent cloud threads editing the same files unless they are isolated worktrees and have a merge plan.
- Setup scripts may use internet for dependencies. Keep agent-phase internet limited unless current docs or package behavior are required.
- Every cloud result must report changed paths, validation commands, and unresolved blockers.

## Parent Consolidation

After agents return:

1. Verify each result follows the contract.
2. Dedupe findings by concrete claim.
3. Sort by severity, then confidence, then impact.
4. Do not implement from findings with confidence <= 2 unless marked `[ASSUMED]` and accepted.
5. Run the smallest meaningful local gate before claiming progress.
