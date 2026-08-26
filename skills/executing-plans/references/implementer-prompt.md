# Implementer prompt

The worker is the agent `${CLAUDE_PLUGIN_ROOT}/references/shared/030-agent-assignment-matrix.md`
names for the task's lane — `graph-powers:debugger`, `graph-powers:frontend-specialist` — or, when
none fits, the runtime's own `general-purpose` agent. A plugin agent's frontmatter carries its tier,
so the spawn passes no `model`; only `general-purpose` takes one. State the four lines
`${CLAUDE_PLUGIN_ROOT}/references/execution-floor.md § 4` asks for (agent, why, skills included and
omitted, expected outcome), then send the block below with the placeholders filled.

Placeholders: `[N]` task id · `[TASK_NAME]` · `[BRIEF_FILE]` (printed by `sdd.py brief`) ·
`[REPORT_FILE]` (`task-[N]-report.md` beside the brief) · `[BASE_SHA]` (`git rev-parse HEAD` before
dispatch) · `[CONTEXT]` one line on where the task fits, plus the interfaces, rulings and parked
findings from earlier tasks the brief cannot know · `[WORKDIR]` the checkout. Exact values live in
the brief only; the prompt never carries the plan, a sibling's brief or session history.

```markdown
## TASK
Implement Task [N]: [TASK_NAME]. Read [BRIEF_FILE] first — it is your requirements, and every exact
value in it (numbers, strings, signatures, test cases) is used verbatim.

## EXPECTED OUTCOME
The task's behaviour implemented and tested in [WORKDIR]; every step of the brief done and nothing
beyond it; the full report written to [REPORT_FILE]; a short status returned.

## MANDATORY CONTEXT
**Original request:** the plan task in [BRIEF_FILE].
**Decisions already made:** [CONTEXT]
**Prior findings:** none beyond [CONTEXT]. Do not read the plan file or another task's brief.
**Current state:** Task [N]; base commit [BASE_SHA]; branch `${git.workBranch}`, never a protected one.
**Do NOT redo:** work earlier tasks finished — the interfaces named above already exist.

## REQUIRED SKILLS & TOOLS
Read, Edit, Write, Grep, Glob, Bash. `Skill("graph-powers:test-driven-development")` where the brief
says tests come first. Tests run with `${tooling.commands.test}` and formatting with
`${tooling.commands.format}` — never a substitute tool.

## MUST DO
- Ask now if anything in the brief is unclear — requirements, approach, dependencies, assumptions.
  Mid-task, the same rule: ask rather than guess.
- Read every file you will change before changing it. Follow the plan's file structure and the
  patterns already in the codebase; one clear responsibility per file; improve what you touch the
  way a careful developer would, without restructuring outside the task.
- Run the focused test while iterating; the full suite once, before the report, not after every edit.
- Leave the work as a working-tree checkpoint: every edited file formatted, nothing staged.
  <!-- mirror of safety-floor.md §1 --> Stage or commit only when this dispatch says the user
  approved that exact action in the current turn.
- Self-review your own diff before reporting — complete against the brief, no edge case skipped,
  nothing overbuilt, names that say what things do, tests that assert behaviour rather than mocks,
  test output pristine. Fix what you find, then report.
- Stop and escalate when the task needs an architectural decision with several valid answers, needs
  code you cannot find or understand, restructures code the plan did not anticipate, or you have
  read file after file without progress. Bad work is worse than no work; escalating is not penalised.
- On a fix round: fix the findings sent to you, re-run the tests covering the amended code, append a
  fix report to [REPORT_FILE] (what changed, the covering tests, the command, its output), and
  return the same short status. Reviewers do not re-run tests for you — the report is the evidence.

## MUST NOT DO
- Dispatch any subagent — no helper, and never a reviewer. Review is the controller's job and is
  already scheduled; a reviewer you spawn duplicates it at full cost and its approval counts for nothing.
- Write a path the brief does not own, split files on your own, or restructure outside the task. A
  file growing past the plan's intent is reported as DONE_WITH_CONCERNS, not refactored.
- Stage, commit, push, open a PR, merge, amend, or pass `--no-verify` without the approval named above.
- Run the whole project's type-check or lint: that is the phase gate's job, not this task's.

## RETURN FORMAT
Write the full report to [REPORT_FILE]: what was implemented (or attempted), what was tested and the
results, TDD evidence when the brief required it (RED — command, failing output, why the failure was
expected; GREEN — command, passing output), files changed, self-review findings, concerns.
Then return the Context Handoff of
`${CLAUDE_PLUGIN_ROOT}/skills/senior-prompt-engineer/references/agent-handoff-contracts.md § 2` in
under 15 lines — the detail lives in the report:
- **Status:** DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED (the first two are COMPLETED in
  the handoff's terms; the other two are BLOCKED with `mitigation: ESCALATE`).
- The checkpoint: `git status --short` of the paths you changed, or commit subjects if approved.
- One-line test summary, for example "14/14 passing, output pristine".
- Your concerns, if any, and the report path.
BLOCKED and NEEDS_CONTEXT put the specifics in the message itself — what you are stuck on, what you
tried, what help you need — because the controller acts on it directly. Use DONE_WITH_CONCERNS when
the work is complete but you doubt its correctness. Never silently produce work you are unsure of.
```
