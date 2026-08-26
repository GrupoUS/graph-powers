# Final reviewer prompt

The one broad review of the whole change, after every task is complete: plan alignment, quality,
architecture, tests, readiness. Dispatch it to the most capable **read-only** reviewer available —
`general-purpose` with this prompt on the strongest model, or the harness reviewer `/pr-review`
names — never a write-capable agent, and never before every task's own review is clean or parked
with a ruling. Send it inside the seven sections of
`${CLAUDE_PLUGIN_ROOT}/references/execution-floor.md § 4`.

Severity, in one line: Critical is P0 (security, data loss, a broken build) or P1; Important is P1 —
must be fixed before this change lands; Minor is P2 or P3, per
`${CLAUDE_PLUGIN_ROOT}/skills/senior-prompt-engineer/references/parallel-batch-contracts.md`.

Placeholders: `[DESCRIPTION]` what was built, briefly · `[PLAN_OR_REQUIREMENTS]` the plan path, or
the requirements · `[MERGE_BASE_SHA]` the commit the work started from · `[HEAD_SHA]` (a commit, or
the working-tree snapshot `sdd.py package` printed) · `[DIFF_FILE]` (the package over that range) ·
`[LEDGER_LINES]` the ledger's deferred-minor and parked lines, verbatim.

```markdown
## TASK
Review the completed change against its plan and against quality standards, before it cascades
into anything else: [DESCRIPTION]

## EXPECTED OUTCOME
Strengths, issues by actual severity with file:line, recommendations, and a clear verdict on whether
the change is ready for the user's git step.

## MANDATORY CONTEXT
**Original request:** [PLAN_OR_REQUIREMENTS]
**Decisions already made:** the rulings and parked findings recorded during execution —
[LEDGER_LINES]
Triage them: which must be fixed before this lands, which can wait.
**Prior findings:** every task passed its own spec and quality review; this is the whole-change pass.
**Current state:** range [MERGE_BASE_SHA]..[HEAD_SHA], packaged at [DIFF_FILE].
**Do NOT redo:** per-task reviews; the implementers' test runs.

## REQUIRED SKILLS & TOOLS
Read, Grep, Glob; Bash read-only (`git log`, `git diff`, `git show`). Read [DIFF_FILE] once — the
commit list, the stat and the full diff with context. If it is missing: `git diff --stat
[MERGE_BASE_SHA] [HEAD_SHA]` and `git diff [MERGE_BASE_SHA] [HEAD_SHA]`. Another revision's contents
come from `git show <sha>:<path>` — never by moving HEAD on this checkout.

## MUST DO
- Plan alignment: does the implementation match the plan; are deviations justified improvements or
  problematic departures; is all planned functionality present. Flag significant deviations
  specifically so the user can confirm whether they were intended. If the defect is in the plan
  rather than the implementation, say so.
- Quality: separation of concerns, error handling, type safety where it applies, DRY without
  premature abstraction, edge cases.
- Architecture: sound decisions, reasonable scale and performance, security, clean integration with
  surrounding code.
- Tests: real behaviour rather than mocks, edge cases, integration tests where they matter, all
  passing per the reported evidence.
- Readiness: a migration strategy if a schema changed, backward compatibility considered,
  documentation complete, no obvious bugs.
- Categorise by actual severity; not everything is Critical. Be specific — file:line, never
  "improve error handling". Explain why each issue matters. Name strengths before issues, accurately.

## MUST NOT DO
- Mutate the working tree, the index, HEAD or any branch. Read-only, throughout.
- Dispatch any subagent, for part of the diff or a second opinion. A large diff is reviewed in
  passes, and the report says so.
- Say "looks good" without checking; mark nitpicks Critical; comment on code you did not read;
  withhold a clear verdict.

## RETURN FORMAT
### Strengths
### Issues
#### Critical (must fix) — bugs, security, data loss, broken functionality
#### Important (should fix) — architecture problems, missing features, poor error handling, test gaps
#### Minor (nice to have) — style, optimisation opportunities, documentation polish
Each: file:line, what is wrong, why it matters, how to fix when not obvious.

### Ledger triage
Each deferred or parked line: must fix before landing | can wait — with one line of reasoning.

### Recommendations
### Assessment
**Ready for the user's git step?** Yes | No | With fixes — one or two sentences of reasoning.
Then the Context Handoff status line: COMPLETED when ready, REVISION_REQUIRED otherwise.
```
