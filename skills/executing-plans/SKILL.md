---
name: executing-plans
description: "Use when a written implementation plan has to be executed task by task."
---

# Executing plans

A fresh subagent per task, a task review after each (spec compliance, then quality), one broad
review of the whole change at the end. A subagent gets isolated, crafted context — never this
session's history — so it stays on its task, and the controller's context stays for coordination.
Announce per `${CLAUDE_PLUGIN_ROOT}/references/shared/005-method-bootstrap.md`.

Two modes. **Subagent-driven** is the default wherever an `Agent` tool exists — every harness this
plugin ships for. **Inline** is for a session without subagents: the same artefacts and stop
conditions, the tasks executed here with a checkpoint between them. Rolling dispatch, GATE A /
GATE B, phase gates and `/verify quick` are
`${CLAUDE_PLUGIN_ROOT}/skills/planning/references/phase-c-executing-plans.md`, not restated here.

## Continuous execution

Do not pause between tasks; progress is status, never an approval request. **Rulings, not stalls:**
whatever the plan leaves open — conflicts, defects, a cap you would ask to exceed — decide it, spec
over plan, and ledger `Ruling: <decision> — <why> — <cost if wrong>`. A wrong ruling is rework the
user can see and undo; a parked session costs the day.

Only these stop you: an irreversible or destructive operation; a security-sensitive action; anything
that leaves the repository — stage, commit, push, PR, merge, publish, each needing approval in the
current turn (`${CLAUDE_PLUGIN_ROOT}/references/safety-floor.md § 1`); a plan so broken that every
path forward is a guess.

## Setup

Workspace: `.graph-powers/logs/sdd/<plan-slug>/` — ledger `progress.md`, briefs, reports, review
packages. Another plan's directory is never yours. `sdd.py` below is this command with another
subcommand:

```bash
python -X utf8 "${CLAUDE_PLUGIN_ROOT}/skills/executing-plans/scripts/sdd.py" workspace <PLAN_FILE>
```

The ledger is the recovery map: controllers without one have re-dispatched whole completed
sequences. First line: `# SDD ledger — plan: <plan file>`. If it names your plan, resume at the
first task without a `Task <N>: complete` line (a trailing fix-round line resumes that loop); after
compaction trust it, `git status` and `git diff --stat` over recollection. A ledger naming another
plan is not yours: start fresh.

Read the plan once, and the spec it names (none reachable: ledger note, rulings provisional). One
todo per task. Then the pre-flight scan, a table in the ledger: a row per pair of tasks sharing a
file or interface (what one produces against what the other consumes), a row per task (does its own
text agree with itself), and what you found. "Clean" without rows is not a scan. Rule on every row
before Task 1.

## Choosing the worker

The agent comes from `${CLAUDE_PLUGIN_ROOT}/references/shared/030-agent-assignment-matrix.md`; its
frontmatter carries the tier, so the spawn passes no model (rule 8 of
`${CLAUDE_PLUGIN_ROOT}/references/shared/070-parallel-agent-spawn.md`). Cost follows turn count more
than token price: a brief holding the complete code is transcription for the lightest agent that
fits; prose briefs, integration and every review take a specialist. Fix rounds 4–5 escalate to a
more capable agent, or a more capable *model* only where the worker is the runtime's own
`general-purpose`.

## The task loop

**Batch same-shape work:** small independent edits of one kind across files go to ONE implementer
as one brief and one review. Hand artefacts over as files: anything pasted or printed back stays in
your context all session. Wait on children in bounded stretches — local work meanwhile, a status
line between stretches, reconcile live children and chase any that finished silently.

### 1. Dispatch

Record BASE (`git rev-parse HEAD`); `sdd.py brief <PLAN_FILE> <N>` extracts the brief. Build the
prompt from `references/implementer-prompt.md` inside the seven sections of
`${CLAUDE_PLUGIN_ROOT}/references/execution-floor.md § 4`, carrying five things: where the task fits,
in one line; the brief path, "read this first — your requirements, exact values verbatim";
interfaces and decisions from earlier tasks the brief cannot know; your resolution of any ambiguity
in it; the report path (`task-N-report.md` beside the brief) and its contract. Never the plan or
session history; always the no-subagents contract — a worker-spawned reviewer is a duplicate seat.
Record the agent identity; rounds 1–3 resume it. Parallel implementers only on disjoint `Owns`: one
writer per file is `${CLAUDE_PLUGIN_ROOT}/references/shared/070-parallel-agent-spawn.md § 7`.

### 2. Handle the report

**DONE** → package and review. **DONE_WITH_CONCERNS** → correctness or scope concerns are handled
before review, observations ledgered. **NEEDS_CONTEXT** → supply it, re-dispatch. **BLOCKED** → a
context problem gets context; a reasoning problem a more capable worker; an oversized task a split;
a wrong plan a ruling, ledgered and carried in the re-dispatch. Never re-run the same worker
unchanged. Answer its questions fully.

### 3. Review the task

`sdd.py package <PLAN_FILE> <BASE> HEAD` writes commits, stat and `-U10` diff from BASE to the
checkout — a working-tree snapshot when nothing was committed; its printed id is the next round's
FIX_BASE. Never `HEAD~1` as BASE. Dispatch a read-only reviewer (a `general-purpose` agent with
`references/task-reviewer-prompt.md`, or the harness reviewer `/pr-review` names) with the brief,
the report, the package path and the global constraints copied verbatim from the plan or spec. No
pre-judging: "do not flag" or "at most Minor" in your prompt is you sparing yourself a loop. Both
verdicts are required. CANNOT VERIFY items are yours to settle; a confirmed gap is a failed spec
review.

### 4. The fix loop

Triggered by a spec failure, any Critical or Important finding, or a confirmed gap. Two routes leave
first: Minor findings go to the ledger — `Task <N>: minor (deferred): <one-liner>` — for the final
review to triage; a plan-mandated finding gets a ruling, spec as authority — neither dismissed
because the plan said so nor fixed against the plan without one. Read and apply
`${CLAUDE_PLUGIN_ROOT}/commands/pr-review.md § 4.1` first; that is the single receiving-feedback
protocol.

A round is one fix dispatch plus one scoped re-review; five per task. Rounds 1–3 resume the original
implementer with the findings verbatim (or a fresh worker, with the report file as memory). Rounds
4–5 dispatch a fresh, more capable worker that owns the task now and reads the report for what was
tried. Each round the implementer fixes, re-runs the covering tests, appends a fix report (tests,
command, output) and returns the short contract; then package `FIX_BASE..HEAD` for
`references/re-review-prompt.md`. New Critical or Important breakage joins the list; out-of-scope
observations become deferred minors. Ledger: `Task <N>: fix round <R>/5 (<X> addressed, <Y> open —
<one-liners>; <base7>..<head7>)`. Never fix in the controller: it skips review and spends
coordination context.

**The breaker.** Findings still open after round 5: stop dispatching and adjudicate each. Reviewer
wrong or contestable → `Task <N>: parked — <finding> — Ruling: <why the code stands>`. Real, nothing
downstream builds on it → parked, deferred. Real and load-bearing → the smallest unblocking change,
`Task <N>: Ruling: …`, carried into the next dispatch; stop only when every path is a guess. Only at
the cap — earlier is pre-judging.

### 5. Complete the task

`Task <N>: complete (<base7>..<head7>, review clean)` or `(…, <K> parked)`; mark the todo. Never
move on with a Critical or Important finding that is neither fixed nor parked with a ruling.

## Final review

Package `MERGE_BASE..HEAD` (MERGE_BASE: `git merge-base <target> HEAD`, the target being the first
of `${git.protectedBranches}`, or the commit the work started from) and dispatch
`references/final-reviewer-prompt.md` on the most capable read-only reviewer, pointed at the
ledger's deferred and parked lines. Findings → ONE fix dispatch with the whole list, not one per
finding; one scoped re-review of that range; residuals adjudicated as the breaker does. No second
wave: residual load-bearing findings reach the user in the final message.

## Finish

Collect every ledger `Ruling:` line into the final message under **Rulings I made**, in order, each
with its cost if wrong — the only way those decisions reach the user. Stop at reviewed working-tree
changes and run `/verify quick`; claims follow
`${CLAUDE_PLUGIN_ROOT}/references/shared/015-verification-gate.md`. No merge or PR menu: the user
decides the git step and authorises it in that turn. Delete the workspace — this plan's directory
only, `python -X utf8 -c "import shutil; shutil.rmtree(r'<workspace>')"` — only after that step.

## Inline mode

No `Agent` tool: load the plan, review it critically — concerns go to the user before any code —
then one todo per task. Per task: mark it in progress, write the brief anyway, follow its steps
exactly (`Skill("graph-powers:test-driven-development")` where the plan says so), run its own
verification and record the output, write the report, review your diff against the task reviewer's
checklist, ledger it. Stop and ask on a missing dependency, a verification that keeps failing, an
unclear instruction or a gap that prevents starting — never guess through a blocker. A defect under
investigation is `Skill("debugger")`.

## Common rationalizations

| Excuse | Reality |
|---|---|
| "Close enough on spec" | A spec gap is not done. Fix, or hit the cap and adjudicate. |
| "I'll fix it myself" | Controller fixes skip review and spend coordination context. |
| "One more round will converge" | Past the cap the failure is structural. Adjudicate. |
| "The reviewer will find something new anyway" | Re-reviews are scoped; new findings elsewhere go to the ledger. |
| "This finding is obviously wrong" | Adjudicate at the cap only, in the ledger. No silent discards. |
| "The fix was small, skip the re-review" | Unreviewed fixes are how regressions land. |
| "Reviews slow the loop" | Without them it is unverified churn. |
| "Ledger bookkeeping is overhead" | The ledger is what survives compaction. |
| "The implementer's own reviewer is free assurance" | A duplicate seat. The task review is the gate. |

## Example

```text
Using executing-plans on <plan dir>/PLAN.md — workspace resolved, no ledger, fresh start.
Pre-flight: 3 rows, 1 ruling (T1.2 vs T2.1 field name — the spec wins). Todos created.
T1.1 — brief; graph-powers:debugger dispatched; BASE a1b2c3d. DONE, 5/5 passing.
Package a1b2c3d..e4f5a6b (snapshot); reviewer COMPLIANT, Approved. Ledger: Task 1.1: complete.
T1.2 — NOT COMPLIANT (progress reporting missing). Fix round 1: resumed; re-review ADDRESSED.
Final review: one Important → one fix dispatch → clean. Rulings I made: (1) T1.2 field name.
Working tree ready for review; /verify quick next. Stage or commit needs your approval.
```
