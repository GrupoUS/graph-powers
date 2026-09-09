# Persistent planning and verifiable resume — design

## Destination
A session resumes the explicitly selected structured plan, recovers its objective, findings,
recorded work, dependencies and next action without resetting limits or claiming unverified success.

## Authority and approval
The user approved the inline T1–T4 plan with “implemente” and “pode implementar”, then explicitly
authorized releasing only the previous Cole Medin plan's lease with “autorizo”. Its changes and
ledgers remain intact. The starting checkout is main at ba6cd8d with existing 1.19.5 changes.
No installation, publication, staging, commit, push, merge or other-plan ledger change is approved.

The subsequent user instruction “ignore os conflitos e implemente o plano” authorizes this run to
proceed while the Hermes execution holds the global lease. This is a local execution exception,
not a harness or product-contract change. Preserve its lease, files and ledgers; do not acquire,
release, replace or reset the global lease and do not call `sdd.py dispatch reserve`, which requires
the other execution's lease. The controller records dispatches and checkpoints only in this plan's
`.graph-powers/logs/sdd/2026-09-09-persistent-planning-resume/task-reviews.md`, retaining prior
attempts and a maximum of eight dispatches in total, including this confirmation and final review.
Do not write shared progress or another plan's state, and do not bypass a denied tool or hook.
All approved T1–T4 contracts, dependencies, focused checks and independent reviews remain required.
In particular, real `status` with an unrelated lease must still report LEASE_CONFLICT, exit 4 and
null nextAction; the local authority to proceed does not change that result.

## Background research
OthmanAdi/planning-with-files at 3cbb7dcc4b37224ba41e0200e8db1e64edfb7bb2 supplies the separation
of plan/findings/progress, decision-triggered rereading and isolated plan selection. Its subsequent
f67e2bb revision changes the canonical skill's version metadata only. Adapt the principles to
existing Graph Powers owners; no upstream file is redistributed and performance gains are unmeasured.
Current Graph Powers already has spec research, task/gate evidence, current-input revalidation,
atomic leases and persistent dispatch/consultation budgets. Reuse these, including uncommitted
Cole Medin improvements; do not recreate them.

## Approach and responsibilities
Approved T1 adds proportional research capture/consumption in Phase A/B and minimal path-table links.
Approved T2 extends sdd.py through its existing validator; no parallel parser, cache or registry.
Approved T3 integrates selection and targeted recovery into implement, prime, Phase C and the
existing loop checkpoint protocol. Approved T4 records provenance, advances six metadata versions
to 1.20.0 and regenerates existing Codex projections. All descriptions/models/permissions remain.

## Status interface
`python3 skills/planning/scripts/sdd.py status PLAN_FILE --max-tasks N [--profile gauntlet]`.
N is resolved from graphGuardrails.maxTasksPerPlan (default 12); default profile remains default.
Validate explicit file containment and equality of canonical Git worktree roots for cwd and plan.
Reject external/sibling-worktree/nested-repository/escaping-symlink inputs, with no fallback.
Reuse validate_plan and existing read-only directory/lease readers. Preserve validate/acquire APIs.
Validate lease identity and each path locally for status; malformed/dangling symlink is exit 2.
Compare the complete expected acquire path set; another owner or changed set is conflict, exit 4.
Absent/matching lease and valid pending or blocked plans return exit 0.

JSON fields: repositoryRoot, planFile (relative POSIX), tier, profile;
counts.tasks {total, checked, pending, ready}; counts.gates {total, checked, pending};
currentPhase (numeric or null); nextAction ({kind: TASK|GATE, id, line} or null);
state (ACTION_REQUIRED|BLOCKED_DEPENDENCIES|LEASE_CONFLICT|NEEDS_FINAL_VERIFICATION);
lease {state: ABSENT|MATCHING|CONFLICT, planFile}; approval: NOT_VERIFIED; checksExecuted: false.
No task bodies, commands, research, logs, titles, timestamps or task lists are emitted; therefore no
list truncation is hidden. Identical observed inputs produce identical JSON. Counts are recorded
structural state, not fresh verification. Invalid input emits the existing stderr-style error.

Derive phase from numeric T/G IDs. Select the first incomplete phase, then the first eligible
unchecked task in source order whose Needs are checked with evidence and prior gates are closed.
When all phase tasks close, select its first pending gate. No eligible work with unfinished tasks
is BLOCKED_DEPENDENCIES. All recorded tasks/gates closed is NEEDS_FINAL_VERIFICATION, never DONE.
Lease conflict overrides state and clears nextAction. The query creates no files, workspace, Git
objects, index, refs, lease or ledger. It does not execute CHECK. It is not an atomic multi-file
snapshot or approval proof: revalidate/acquire before a writer and assess current evidence separately.

## Selection and persistence
Explicit path > existing unambiguous same-project/session handoff binding > unique candidate.
Invalid explicit/active binding stops selection. Never select by mtime or lease. Include legacy
plan files but exclude spec/map/handoff records from discovery. Prime scans no plans in ordinary
context loads; status applies only to an identified resume. Dry-run writes nothing, including a
conversation-only plan. Keep the single recovery protocol in loop-engineering; consumers link it.
Capture decision-changing findings with source, fact, inference, decision and rationale in a draft
spec only when artifact writes are authorized. Approved specs remain unchanged during execution;
record findings/failures in task-review state and return contract changes to planning. Preserve
rejected research, current proof and restrictions without copying full evidence or repeating reads.
L1–L2 require no plan artifacts and L3 keeps its inline light route.

## Testing and risks
Real CLI RED/GREEN covers frontier, gate/dependency barriers, late phases, all-records closure,
checked pending evidence, malformed input and lease, matching/conflicting lease, cwd isolation,
symlinks, deterministic output, no mutation and inert embedded commands, plus unchanged default
and gauntlet validation/acquire behavior. Capture actual independent model responses per scenario;
run_evals threshold 1.0 is behavioral fixture evidence, not live clean-session routing proof.
Run all 25 declared final gates, with CI-only verification explicitly separate. Compare six disk
versions with HEAD as the version gate alone does not prove an unstaged bump.
Current context budget is floor 49,371 / ceiling 199,795 bytes. Replace/condense within owned files;
do not raise the 50,000/200,000 caps or duplicate protocols. Preserve all pre-existing dirty work.

## Out of scope
New hooks, Stop loops, upstream installation, new planning authorities, approval hashes, tool-count
logging, transcripts, performance claims, model changes and privilege changes.

## Not yet specified
None: observable scope and contracts are approved.

## Rollback
Undo only this delivery's hunks, consumers before status; preserve pre-existing edits and all
execution evidence. Do not reset, clean, broadly check out or remove another plan's state.
