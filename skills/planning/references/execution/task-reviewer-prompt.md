# Task reviewer prompt

Use one fresh, read-only reviewer after each implementer. This is the only per-task review: first
verify compliance, then review KISS and quality. Do not review unrelated files or dispatch another
agent.

```text
## TASK
Review [TASK ID] against its pasted task block and diff.

## EXPECTED OUTCOME
Two verdicts with file:line evidence: compliance first, then quality.

## MANDATORY CONTEXT
**Original request:** [LOSSLESS REQUEST SUMMARY]
**Decisions already made:** [DECISIONS]
**Prior findings:** [PRIOR FINDINGS]
**Current state:** Phase C task [TASK ID] review, package [REVIEW PACKAGE].
**Do NOT redo:** [IMPLEMENTER TEST RUN AND FINAL REVIEW]

Task block: [TASK BLOCK]
Task review package: [REVIEW PACKAGE]
Implementer report and evidence: [REPORT]

## REQUIRED SKILLS & TOOLS
Use Read, Grep, Glob and read-only Bash. Read the supplied diff once; do not mutate the tree or
dispatch an agent.

## MUST DO
1. Confirm every requirement, TDD status, RED/GREEN evidence, CHECK/EXPECT and Owns boundary.
2. Then check the real production seam, test behaviour rather than mocks, KISS/YAGNI, error
   handling and project rules. Nits are informational.
3. A missing requirement, invalid evidence, path outside Owns, or quality/security violation is
   FAIL; otherwise PASS. Do not add scope.

## MUST NOT DO
- Mutate the working tree, index, HEAD or any branch.
- Re-run implementation or whole-project gates; the phase gate owns them.
- Stage, commit, push, open a PR, merge, or dispatch another agent.

## RETURN FORMAT
Return the Context Handoff per
`${CLAUDE_PLUGIN_ROOT}/skills/senior-prompt-engineer/references/agent-handoff-contracts.md` after
the role fields below:
Compliance: PASS | FAIL — [criterion and file:line evidence]
Quality: PASS | FAIL — [KISS/test/security finding, or none]
Missing items: [list or none]
Recommendation: [close task | re-dispatch with corrections]
```
