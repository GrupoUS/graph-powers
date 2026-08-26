# Scoped re-review prompt

After a fix round, the re-reviewer verdicts each earlier finding and inspects the fix diff for new
breakage — nothing else. The full review already happened. Same dispatch rules as the task reviewer:
a **read-only** reviewer (`general-purpose` with this prompt, or the harness reviewer `/pr-review`
names), never a write-capable agent; small fix diffs take a light tier. Send it inside the seven
sections of `${CLAUDE_PLUGIN_ROOT}/references/execution-floor.md § 4`.

Placeholders: `[N]` · `[R]` round number · `[BRIEF_FILE]` · `[FINDINGS]` — the Critical and
Important findings and confirmed spec gaps of the previous review, verbatim, one per bullet ·
`[REPORT_FILE]` (fix reports are appended at its end) · `[FIX_BASE_SHA]` — the commit or snapshot
the previous review saw · `[HEAD_SHA]` · `[DIFF_FILE]` (from `sdd.py package PLAN FIX_BASE HEAD`).

```markdown
## TASK
Re-review Task [N], fix round [R]: verdict each finding below and inspect the fix diff.

## EXPECTED OUTCOME
One verdict per finding, ADDRESSED or NOT ADDRESSED with file:line evidence; any breakage the fix
introduced; a round verdict.

## MANDATORY CONTEXT
**Original request:** the brief at [BRIEF_FILE].
**Decisions already made:** the findings under verification —
[FINDINGS]
**Prior findings:** the implementer's report and its appended fix report at [REPORT_FILE] —
unverified claims.
**Current state:** the fix diff is [FIX_BASE_SHA]..[HEAD_SHA], packaged at [DIFF_FILE].
**Do NOT redo:** the full task review; code the fix did not touch.

## REQUIRED SKILLS & TOOLS
Read, Grep, Glob; Bash read-only. Read [DIFF_FILE] once — commits, stat and the fix diff with
context. If it is missing, `git diff --stat [FIX_BASE_SHA] [HEAD_SHA]` and
`git diff [FIX_BASE_SHA] [HEAD_SHA]`.

## MUST DO
- Verdict every finding, in order. "Attempted" is not ADDRESSED: the specific defect must no longer
  exist, and the evidence is a file:line in the fix diff.
- Confirm the fix report names the covering tests and shows their command and output, and check
  those claims against the diff. Run a test only for a specific doubt no existing run answers —
  focused, never a suite.
- Report anything the fix itself broke or introduced, with severity (Critical, Important, Minor)
  and file:line.
- An issue you notice entirely outside the fix diff goes under Out-of-scope observations. It does
  not block this task and does not extend the loop; the controller ledgers it for the final review.

## MUST NOT DO
- Mutate the working tree, the index, HEAD or any branch.
- Dispatch any subagent, for part of the diff or a second opinion.
- Re-review code the fix did not touch, re-run git commands the package answers, or re-run the
  suite to confirm the report.

## RETURN FORMAT
The final message is the report; it begins with the first finding's verdict — no preamble.

### Finding verdicts
- **<finding one-liner>** — ADDRESSED | NOT ADDRESSED, file:line evidence.

### New breakage in the fix diff
Severity and file:line, or "None".

### Out-of-scope observations
Non-blocking, or "None".

### Verdict
**Fix round:** all findings addressed, no new Critical or Important breakage | findings remain open —
list the open ones. Then the Context Handoff status line: COMPLETED or REVISION_REQUIRED.
```
