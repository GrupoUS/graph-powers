---
description: "Hand one task to a named specialist agent through the 7-section delegation protocol. Use when the user asks to delegate, to hand it to an agent, or to spawn a specialist for a specific piece. Do not use to decide how many agents a task needs — that is the execution floor, which is already loaded."
workflow_type: routing
---

# /delegate - Explicit Delegation Protocol

**ARGUMENTS**: $ARGUMENTS

> **Read before step 0 — never reconstruct these from memory:** `${CLAUDE_PLUGIN_ROOT}/references/shared/005-superpowers-bootstrap.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/030-agent-assignment-matrix.md`

<command-instruction>
```typescript
Skill("superpowers:using-superpowers"); // meta — bootstrap (per `${CLAUDE_PLUGIN_ROOT}/references/shared/005-superpowers-bootstrap.md`)
```

If the task scope is ambiguous (user did not name the agent, multiple agents could plausibly own the work, or the deliverable is not a concrete file change), invoke `Skill("superpowers:brainstorming")` first to surface alternatives + tradeoffs before locking in the delegation. Skip when the user already named the agent or the routing matrix is unambiguous.

**Which agent, and whether to use one at all**, is the execution floor
(`${CLAUDE_PLUGIN_ROOT}/references/execution-floor.md` §1) — it routes, this command executes. That
floor is always in force, not invoked: when its ladder says a task needs a specialist, the chosen
agent lands here and the contract below is what runs.

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

Then structure the delegation prompt with ALL 7 sections. <!-- mirror of execution-floor.md §4 -->
The floor defines them; this list is the same seven, in the same order, so the parent can consolidate
mechanically. Changing one without the other is the divergence the provenance comment exists to make
visible:

1. TASK: [atomic, specific - one action per delegation]
2. EXPECTED OUTCOME: [concrete deliverables with success criteria]
3. MANDATORY CONTEXT: [original request, locked decisions, prior findings, current state, and an explicit "do NOT redo"]
4. REQUIRED SKILLS & TOOLS: [skills to invoke, plus the explicit tool whitelist]
5. MUST DO: [exhaustive requirements - nothing implicit]
6. MUST NOT DO: [forbidden actions]
7. RETURN FORMAT: [Context Handoff; the finding table for a parallel batch]

After delegation completes, VERIFY:

- Does it work as expected?
- Does it follow existing codebase patterns?
- Did the agent follow MUST DO and MUST NOT DO?

## Research Agent Selection

Choose by **where the answer lives** — the Explorer-vs-Librarian table in
`${CLAUDE_PLUGIN_ROOT}/references/shared/030-agent-assignment-matrix.md`, which this command loads.
When both are needed, delegate to both **in the same message**, so they run in parallel.
  </command-instruction>
