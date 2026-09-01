# Correction reviewer prompt

Use one fresh, read-only `graph-powers:evaluator` after a grouped correction wave. It checks whether
all cited findings were fixed and whether the integrated corrections introduced blocking breakage.

```text
## TASK
Re-review correction wave [WAVE ID], round [N], for tasks [TASK IDS].

## EXPECTED OUTCOME
Each prior finding is marked ADDRESSED or NOT ADDRESSED with file:line evidence, plus any new
Critical or Important breakage.

## MANDATORY CONTEXT
**Original request:** [LOSSLESS REQUEST SUMMARY]
**Decisions already made:** [DECISIONS]
**Prior findings:** [PRIOR FINDINGS]
**Current state:** Phase C correction wave [WAVE ID], tasks [TASK IDS], round [N].
**Do NOT redo:** [ORIGINAL TASK REVIEW AND UNTOUCHED CODE]

Prior findings grouped by task: [FINDINGS]
Correction review packages: [REVIEW PACKAGES]
Correction reports and focused checks: [REPORTS]

## REQUIRED SKILLS & TOOLS
Use Read, Grep, Glob and read-only Bash. Read the correction diff once; run a focused check only
for a concrete doubt. Do not mutate the tree or dispatch an agent.

## MUST DO
- Treat every report as unverified; compare every claim with the diff and output.
- Do not re-review untouched code or expand scope. Run a focused check only when the report leaves
  a concrete doubt unresolved.
- A finding remains open when the specific defect still exists, even if an attempted fix is present.

## MUST NOT DO
- Mutate the working tree, index, HEAD or any branch.
- Re-review untouched code or expand scope.
- Stage, commit, push, open a PR, merge or dispatch another agent.

## RETURN FORMAT
Return the Context Handoff per
`${CLAUDE_PLUGIN_ROOT}/skills/senior-prompt-engineer/references/agent-handoff-contracts.md` after
the role fields below:
Findings: [one ADDRESSED or NOT ADDRESSED line per prior finding, grouped by task]
Integration: PASS | FAIL — [cross-correction breakage or none]
New breakage: [severity and file:line, or none]
Out-of-scope observations: [non-blocking, or none]
Verdict: PASS | FAIL — [all addressed or open findings]
```
