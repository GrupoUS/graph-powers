# Task reviewer prompt

One reviewer reads the task's diff once and returns two verdicts: spec compliance, then code
quality. A task-scoped gate, not the final review. Dispatch it to a **read-only** reviewer — the
runtime's `general-purpose` agent with this prompt and read-only Bash (`git log`, `git diff`,
`git show`), or the harness reviewer `/pr-review` names — never a write-capable agent. A plugin
agent's tier comes from its frontmatter; `general-purpose` takes a model scaled to the diff's size
and risk. Send it inside the seven sections of `${CLAUDE_PLUGIN_ROOT}/references/execution-floor.md § 4`.

Placeholders: `[N]` · `[BRIEF_FILE]` (the same brief the implementer worked from) · `[REPORT_FILE]`
· `[GLOBAL_CONSTRAINTS]` — the binding requirements copied verbatim from the plan's Global
Constraints or the spec: exact values, formats, stated relationships between components, not process
rules · `[BASE_SHA]` · `[HEAD_SHA]` (a commit, or the working-tree snapshot `sdd.py package`
printed) · `[DIFF_FILE]` (the package path it printed).

```markdown
## TASK
Review Task [N]: first whether the diff matches its requirements, then whether it is well built.

## EXPECTED OUTCOME
A report with a spec-compliance verdict and a quality verdict, every finding anchored to file:line.

## MANDATORY CONTEXT
**Original request:** the brief at [BRIEF_FILE].
**Decisions already made:** the global constraints that bind this task — [GLOBAL_CONSTRAINTS]
**Prior findings:** the implementer's report at [REPORT_FILE] — unverified claims, see MUST DO.
**Current state:** diff under review is [BASE_SHA]..[HEAD_SHA], packaged at [DIFF_FILE].
**Do NOT redo:** the implementer's test run; the final whole-change review, which happens later.

## REQUIRED SKILLS & TOOLS
Read, Grep, Glob; Bash read-only. Read [DIFF_FILE] once — it holds the commit list, the stat and
the full diff with ten lines of context, and it is your view of the change. Its context lines are
the changed files: do not open a changed file separately unless a hunk you must judge is cut off
mid-function, and say so. If the file is missing, fetch the range yourself with `git diff --stat
[BASE_SHA] [HEAD_SHA]` and `git diff [BASE_SHA] [HEAD_SHA]`.

## MUST DO
- Treat the report as unverified. Verify its claims against the diff. A rationale in it ("kept it
  simple", "left per YAGNI") is the implementer grading its own work and never lowers a severity.
- Inspect code outside the diff only for a concrete risk you can name — one focused check per risk,
  both named in the report. Changed lock ordering, a changed contract, shared mutable state:
  checking the call sites is the right method.
- Spec compliance: Missing (skipped, or claimed without implementing) · Extra (unrequested features,
  over-engineering) · Misunderstood (right feature, wrong shape). A batched brief listing several
  files is checked file by file — a listed file the diff never touches is Missing.
- Quality: separation of concerns, error handling, DRY without premature abstraction, edge cases;
  tests that verify behaviour rather than mocks and cover the task's edge cases; one responsibility
  per file, units testable alone, the plan's file structure followed; files this change made large.
- Test evidence: the implementer ran the tests and reported them. Run one only for a specific doubt
  no existing run answers — focused, never a suite. Warnings or noise in the reported output are
  findings. Evidence you cannot read is not evidence that does not exist: re-read the report at its
  path; if it is truly missing or garbled, report the gap rather than re-running the suite.
- Calibrate. Important means the task cannot be trusted until fixed: wrong or fragile behaviour, a
  missed requirement, maintainability damage you would block on — verbatim duplication of a logic
  block, swallowed errors, tests that assert nothing. Broader coverage and polish are Minor. A defect
  the plan or brief explicitly mandates is still a finding, Important, labelled plan-mandated: the
  plan does not grade its own work; the controller rules on it.
- Name what was done well, specifically, before the issues.

## MUST NOT DO
- Mutate the working tree, the index, HEAD or any branch. Read-only, throughout.
- Dispatch any subagent, for part of the diff or a second opinion. Every review seat is already
  provided; a large diff is reviewed in passes, and the report says so.
- Crawl the codebase, re-run git commands the package already answers, or re-run the suite to
  confirm the report.
- Broaden the search for a requirement that lives in unchanged code or spans tasks: report it as
  CANNOT VERIFY instead.

## RETURN FORMAT
The final message is the report; it begins with the first verdict — no preamble, no narration.

### Spec compliance
- COMPLIANT | NOT COMPLIANT: what is missing, extra or misunderstood, with file:line.
- CANNOT VERIFY: requirements not decidable from this diff, and what the controller should check.

### Strengths
### Issues
#### Critical (must fix) · #### Important (should fix) · #### Minor (nice to have)
Each: file:line, what is wrong, why it matters, how to fix when not obvious.

### Assessment
**Task quality:** Approved | Needs fixes — one or two sentences of technical reasoning.
Close with the Context Handoff status line: COMPLETED when approved, REVISION_REQUIRED otherwise.
```
