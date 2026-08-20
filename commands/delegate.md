---
description: Delegate a task to a specialist agent using the mandatory 7-section delegation protocol.
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

**Which agent, and whether to use one at all**, is `Skill("agent-orchestration")` — it routes; this
command executes. It also fires on its own when a request asks for agents in so many words, in which
case it hands the chosen agent here and the contract below is what runs.

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

Choose by **where the answer lives** — the Explorer-vs-Librarian table in
`${CLAUDE_PLUGIN_ROOT}/references/shared/030-agent-assignment-matrix.md`, which this command loads.
When both are needed, delegate to both **in the same message**, so they run in parallel.
  </command-instruction>
