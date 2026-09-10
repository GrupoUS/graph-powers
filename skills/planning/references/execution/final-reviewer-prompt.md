# Final reviewer prompt

Use one fresh, read-only `graph-powers:evaluator` after all tasks and phase gates. This review is
separate from wave reviews and checks the complete change against the approved plan.

```text
## TASK
Review the completed plan [PLAN] against the complete current snapshot in [REVIEW PACKAGE].
[MERGE BASE]..[HEAD] is a comparison input, not the complete review scope.

## EXPECTED OUTCOME
Strengths, severity-ranked issues with file:line evidence, ledger triage and a readiness verdict.

## MANDATORY CONTEXT
**Original request:** [LOSSLESS REQUEST SUMMARY]
**Decisions already made:** [DECISIONS]
**Prior findings:** [PRIOR FINDINGS]
**Current state:** Phase C final review after all phase gates. The package identifies the current
tracked, staged, unstaged and untracked snapshot; comparison range [MERGE BASE]..[HEAD].
**Do NOT redo:** [WAVE REVIEWS AND IMPLEMENTER TEST RUNS]

Plan and requirements: [PLAN]
Task-review outcomes and parked/deferred findings: [LEDGER]
Complete review package: [REVIEW PACKAGE]

## REQUIRED SKILLS & TOOLS
Use Read, Grep, Glob and read-only Bash. Read the complete diff once; do not mutate the tree or
dispatch an agent.

## MUST DO
- Check destination, scope, architecture, interfaces, real behavioural tests, TDD evidence,
  security, error handling, rollback and declared gates against the supplied complete snapshot.
- For Gauntlet, check the requirement-coverage matrix, or an approved legacy plan's equivalent
  task/connection evidence: every applicable database, backend/API and frontend/client need maps to
  a task, owned path, producer → consumer payload/path and acceptance evidence. `N/A` needs
  repository evidence; do not require an absent layer or a new heading on an otherwise green spec.
- Critical and Important findings block readiness; Minor findings are reported and triaged.
- Review the full change once, without mutating the tree or dispatching another agent.

## MUST NOT DO
- Mutate the working tree, index, HEAD or any branch.
- Re-run per-task implementation tests or whole-project gates.
- Stage, commit, push, open a PR, merge, or dispatch another agent.

## RETURN FORMAT
Return the Context Handoff per
`${CLAUDE_PLUGIN_ROOT}/skills/senior-prompt-engineer/references/agent-handoff-contracts.md` after
the role fields below:
Strengths: [evidence-backed list]
Critical: [issues with file:line, or none]
Important: [issues with file:line, or none]
Minor: [issues with file:line, or none]
Ledger triage: [must fix or can wait]
Assessment: READY | WITH FIXES — [reason]
```
