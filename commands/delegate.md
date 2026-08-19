---
description: Delegate a task to a specialist agent using the mandatory 7-section delegation protocol.
workflow_type: routing
---

# /delegate - Explicit Delegation Protocol

**ARGUMENTS**: $ARGUMENTS

> **Read first:** `${CLAUDE_PLUGIN_ROOT}/references/shared-context.md` — config loader, quality
> gates, complexity routing, agent matrix, spawn patterns. Every section this command cites by
> number lives there. Read it before step 0; do not reconstruct it from memory.

<command-instruction>
```typescript
Skill("superpowers:using-superpowers"); // meta — bootstrap (per shared-context.md § 0.5)
```

If the task scope is ambiguous (user did not name the agent, multiple agents could plausibly own the work, or the deliverable is not a concrete file change), invoke `Skill("superpowers:brainstorming")` first to surface alternatives + tradeoffs before locking in the delegation. Skip when the user already named the agent or the routing matrix is unambiguous.

Before delegating, you MUST complete the Pre-Delegation Declaration:

```
Agent selected: [agent name]
Why this agent: [match between agent specialty and task domain]
Skills to load: [list from ${CLAUDE_PLUGIN_ROOT}/skills/]
Skill evaluation:
  - [skill-1]: INCLUDED because [reason]
  - [skill-2]: OMITTED because [reason]
Expected outcome: [concrete deliverable]
```

Then structure the delegation prompt with ALL 7 sections:

1. TASK: [atomic, specific - one action per delegation]
2. EXPECTED OUTCOME: [concrete deliverables with success criteria]
3. REQUIRED SKILLS: [skills to invoke]
4. REQUIRED TOOLS: [explicit whitelist]
5. MUST DO: [exhaustive requirements - nothing implicit]
6. MUST NOT DO: [forbidden actions]
7. CONTEXT: [file paths, patterns, constraints]

After delegation completes, VERIFY:

- Does it work as expected?
- Does it follow existing codebase patterns?
- Did the agent follow MUST DO and MUST NOT DO?

## Research Agent Selection

When delegating research tasks, choose based on **where the answer lives**:

| Need                                        | Agent      |
| ------------------------------------------- | ---------- |
| Find patterns / files / conventions in repo | `explorer` |
| Check docs / packages / best practices      | `librarian` |
| Both needed?                                | Delegate to **both in the same message** (parallel) |
  </command-instruction>
