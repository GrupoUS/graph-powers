# Implementer prompt

Use this prompt for one fresh, write-capable Graph Powers specialist per lane package. A package may
contain multiple ready, related task blocks owned by the same role with disjoint paths; paste each
block verbatim. The worker does not read the plan or any task outside the package.

```text
## TASK
Implement lane [LANE ID]: [TASK IDS AND TITLES]. Read every file in the combined Owns before editing.

## EXPECTED OUTCOME
Deliver each task's criterion, only within its Owns, with a separate CHECK and evidence per task.

## MANDATORY CONTEXT
**Original request:** [LOSSLESS REQUEST SUMMARY]
**Decisions already made:** [DECISIONS]
**Prior findings:** [PRIOR FINDINGS]
**Current state:** Phase C, lane [LANE ID], tasks [TASK IDS] of [TOTAL TASKS], base [BASE SHA], branch [WORK BRANCH].
**Do NOT redo:** [COMPLETED WORK AND INTERFACES]

Task blocks, verbatim: [TASK BLOCKS]

## REQUIRED SKILLS & TOOLS
Use the project's declared tools and read
`${CLAUDE_PLUGIN_ROOT}/skills/planning/references/execution/tdd-policy.md` when `TDD: required`.
Do not dispatch another agent.

## MUST DO
- Follow the task's TDD status. For required, record RED (expected failure), minimal GREEN, and
  refactoring only while green. Use the real production interface.
- Run every task CHECK and report each deciding output verbatim.
- Format edited files with the configured formatter. Leave the working tree unstaged.
- Return changed paths, test evidence, concerns and the Context Handoff.

## MUST NOT DO
- Write outside the combined Owns or move one task's changes into another task's ownership.
- Invent scope, flags, abstractions or compatibility paths.
- Run whole-project gates; the final phase gate owns them.
- Stage, commit, push, open a PR, merge, or invoke a process skill or reviewer.

## RETURN FORMAT
Return the Context Handoff per
`${CLAUDE_PLUGIN_ROOT}/skills/senior-prompt-engineer/references/agent-handoff-contracts.md`,
including the role fields below before that handoff:
Lane status: PASS | FAIL | BLOCKED
Per task: [TASK ID] — PASS | FAIL | BLOCKED — [CHECK and deciding output]
Changed paths: [paths]
RED: [command and deciding output, or status reason]
GREEN: [command and deciding output, or status reason]
CHECK: [command and output]
Summary: [2-5 sentences]
Next: [empty unless blocked]
```
