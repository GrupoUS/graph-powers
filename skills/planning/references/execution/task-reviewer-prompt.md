# Wave Evaluator prompt

Use one fresh, read-only `graph-powers:evaluator` after each writer wave. It reviews every task
package in that wave in one acceptance boundary: compliance per task, then quality/KISS and
integration. Do not create one reviewer per task, review unrelated files or dispatch another agent.

```text
## TASK
Review wave [WAVE ID] and tasks [TASK IDS] against their pasted blocks and packages.

## EXPECTED OUTCOME
Per-task compliance and quality verdicts plus one integration verdict, all with file:line evidence.

## MANDATORY CONTEXT
**Original request:** [LOSSLESS REQUEST SUMMARY]
**Decisions already made:** [DECISIONS]
**Prior findings:** [PRIOR FINDINGS]
**Current state:** Phase C wave [WAVE ID] review, packages [REVIEW PACKAGES].
**Do NOT redo:** [IMPLEMENTER TEST RUN AND FINAL REVIEW]

Task blocks: [TASK BLOCKS]
Task review packages: [REVIEW PACKAGES]
Lane reports and evidence: [REPORTS]

## REQUIRED SKILLS & TOOLS
Use Read, Grep, Glob and read-only Bash. Read the supplied diff once; do not mutate the tree or
dispatch an agent.

## MUST DO
1. For each task confirm every requirement, TDD status, RED/GREEN evidence, CHECK/EXPECT and Owns boundary.
2. Then check the real production seam, test behaviour rather than mocks, KISS/YAGNI, error
   handling and project rules. Nits are informational.
3. Check integration across the wave without reopening untouched code. A missing requirement,
   invalid evidence, path outside Owns, or quality/security violation fails the affected task;
   cross-task breakage fails integration. Do not add scope.

## MUST NOT DO
- Mutate the working tree, index, HEAD or any branch.
- Re-run implementation or whole-project gates; the phase gate owns them.
- Stage, commit, push, open a PR, merge, or dispatch another agent.

## RETURN FORMAT
Return the Context Handoff per
`${CLAUDE_PLUGIN_ROOT}/skills/senior-prompt-engineer/references/agent-handoff-contracts.md` after
the role fields below:
Tasks:
- [TASK ID] Compliance: PASS | FAIL — [criterion and file:line evidence]
  Quality: PASS | FAIL — [KISS/test/security finding, or none]
Integration: PASS | FAIL — [cross-task evidence or none]
Missing items: [grouped by task, or none]
Recommendation: [close named tasks | grouped correction package]
```
