# Evaluator Mode Rubrics

Load only the selected mode section. Mode 5 also carries the caller's side, because the
contract of a blind review is written by whoever spawns it.

## Mode 1 — Plan Review

Score product intent, functional completeness, visual/UX requirements, and code
feasibility. Identify ambiguity landmines, at least the material edge cases,
testable rewrites, AI meaningfulness, sprint dependencies, migrations, rollback,
and browser/test contracts. Return APPROVED or REVISION_REQUIRED.

## Mode 2 — Sprint QA

Map every sprint criterion to evidence: implementation path, focused test, gate,
or browser probe. Mark MET/UNMET, report reproducible bugs with file:line, and
return SPRINT_APPROVED only when all blocking criteria pass.

## Mode 3 — Architecture Analysis

Restate the decision and constraints, identify root forces, present at least two
viable options with operational/security/performance/maintenance trade-offs,
recommend one, state second-order effects and rollback, and calibrate confidence.

## Mode 4 — Code Review

Inspect the branch/diff and relevant context for bugs, regressions, tenant/auth
violations, irreversible data risks, OWASP exposure, performance regressions,
missing tests, and maintainability defects. Prioritize P0–P3 and cite tight
file:line ranges. Return REVIEW_APPROVED or CHANGES_REQUESTED.

## Mode 5 — Second Opinion

For a fix that keeps not sticking, or a decision that feels right mainly because the thread has
been staring at it. An advisor that reads the current chat inherits the current chat's
conviction: by the time a second opinion is wanted, the thread has spent twenty turns justifying
one approach, and a reviewer given those twenty turns grades the justification, not the work.
This mode is blind by construction — the agent starts from its prompt and nothing else — and the
blindness is the whole instrument.

Hold it. Do not open `.graph-powers/HANDOFF.md`, `PROGRESS.md`, session logs or any record of
prior attempts. Read the artifact the prompt points at (a plan file, `git diff <base>...HEAD`, a
module) and the repository around it. If the prompt carries the caller's conclusion, who proposed
what, or how much work is already done, judge the artifact anyway and name the leak under Risks:
all three are pressure, not evidence.

Return three things, in the Context Handoff: the verdict as Status (APPROVED as `COMPLETED`,
`REVISION_REQUIRED`, or `BLOCKED`); the strongest argument against that verdict, under Decisions;
and the one check — a command, a test, a grep — that would settle the question, under Quality
gates with its command. A disagreement with something the thread ruled out is a question for the
caller, not a verdict: if the reason is not visible in the artifact, that is a finding about the
artifact.

Refuse the mode when the question has a mechanical answer. Settled by a grep, a type-check or a
test → `BLOCKED`, naming that check. Independence of judgment is worthless where a tool decides.

### The caller's side

The prompt carries the case, never the argument for a side:

- **the artifact, by path** — the agent reads the repository, so `${paths.planDir}/<file>.md` or
  `git diff <base>...HEAD` is enough; do not paste what can be pointed at;
- **the decision, stated neutrally** — "is splitting X into two services right here?", not "we
  decided to split X, confirm that this is right";
- **the constraint that is real** — the branch, the surfaces touched, what is out of scope and why,
  so the agent does not solve a different problem;
- **the answer shape above** — verdict, strongest argument against, the one settling check.

Leave out what the thread concluded, who proposed what, and how much work is already done.

Two engines run the same agent:

- **Spawned** — the default. `subagent_type: "graph-powers:evaluator"`, foreground, the seven
  sections of `${CLAUDE_PLUGIN_ROOT}/references/execution-floor.md` § 4 with `MANDATORY CONTEXT`
  reduced to the original request: `Prior findings` and `Do NOT redo` are `—` on purpose, the one
  spawn where an empty field is the contract rather than a fresh start. Blind because a subagent
  starts from its prompt and nothing else.
- **Headless** — when a dollar ceiling is required:

  ```
  claude -p "<the question>" --agent graph-powers:evaluator --max-budget-usd 1.50 --permission-mode plan --disallowedTools Write Edit
  ```

  `--max-budget-usd` exists in print mode only, and `--max-turns` does not exist at all (measured
  on 2.1.245), which makes this the one spend ceiling in the harness. The agent's own frontmatter
  supplies the model, so no `--model` at the call site. **The question goes first:**
  `--disallowedTools` is variadic and swallows a prompt placed after it — the published form of
  this line once did exactly that, and the CLI reported each word of the question as a permission
  rule matching no tool. Never `--continue`, `--resume` or the current `--session-id`: each restores
  exactly the context the mode withholds. Run it through the Bash tool with its own `timeout` at
  the maximum, or in the background — a headless session that hangs prints nothing until it ends,
  and the coreutils wrapper that used to guard it does not exist on Windows.

Record the outcome in `PROGRESS.md` under `## Verdicts` with the invocation as evidence, so the
next session sees the review happened without paying for it twice. One call is a full session:
reach for it when the decision is expensive to get wrong, not as a habit.

Across modes, filter findings that lack a violated contract or plausible impact.
