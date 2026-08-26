# Implementer prompt

Use this prompt for one fresh, write-capable subagent per task. Paste the task block verbatim; the
worker does not read the plan or another task.

```text
## TASK
Implement [TASK ID]: [TASK TITLE]. Read every file in Owns before editing.

## EXPECTED OUTCOME
Deliver the task's criterion, only within Owns, with the task CHECK and evidence.

## MANDATORY CONTEXT
**Original request:** [ORIGINAL REQUEST]
**Decisions already made:** [DECISIONS]
**Prior findings:** [PRIOR FINDINGS]
**Current state:** Phase C, task [TASK ID] of [TOTAL TASKS], base [BASE SHA], branch [WORK BRANCH].
**Do NOT redo:** [COMPLETED WORK AND INTERFACES]

Task block, verbatim: [TASK BLOCK]

## REQUIRED SKILLS & TOOLS
Use the project's declared tools and read
`${CLAUDE_PLUGIN_ROOT}/skills/planning/references/execution/tdd-policy.md` when `TDD: required`.
Do not dispatch another agent.

## MUST DO
- Follow the task's TDD status. For required, record RED (expected failure), minimal GREEN, and
  refactoring only while green. Use the real production interface.
- Run the task CHECK and report its deciding output verbatim.
- Format edited files with the configured formatter. Leave the working tree unstaged.
- Return changed paths, test evidence, concerns and the Context Handoff.

## MUST NOT DO
- Write outside Owns or invent scope, flags, abstractions or compatibility paths.
- Run whole-project gates; the final phase gate owns them.
- Stage, commit, push, open a PR, merge, or invoke a process skill or reviewer.

## RETURN FORMAT
Return the Context Handoff per
`${CLAUDE_PLUGIN_ROOT}/skills/senior-prompt-engineer/references/agent-handoff-contracts.md`,
including the role fields below before that handoff:
Status: PASS | FAIL | BLOCKED
Changed paths: [paths]
RED: [command and deciding output, or status reason]
GREEN: [command and deciding output, or status reason]
CHECK: [command and output]
Summary: [2-5 sentences]
Next: [empty unless blocked]
```
