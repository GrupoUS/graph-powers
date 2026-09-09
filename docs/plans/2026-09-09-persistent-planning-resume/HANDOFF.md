# Persistent planning resume — final checkpoint

## Approval and scope
User approved the implementation and explicitly directed proceeding despite foreign lease conflict.
That exception applies only to this run; shipped status still reports conflicts. No global lease,
foreign ledger or shared progress edits were made by this run. Prior Cole Medin lease release was
separately authorized and recorded. No staging/commit/push/publication by this task.

## Implemented and independently accepted
T1/T2: decision capture in draft specs and read-only status over the existing validator.
T3/T4: explicit selection, dry-run and targeted recovery; preserved proof/caps; version1.20.0 and
source-derived Codex projections. T1.1/T1.2 and behavioral gate G1.1 are accepted. Final reviewer
confirmed both wave corrections and full implementation compliance/quality PASS, with no remaining
feature finding. CLI55testsPASS;9actual behavioral responses/25assertionsPASS;54parser controlsPASS.

## Remaining global gate
G1.2 is NOT passed:23/25gates (26commands) currently pass. Gate17 fails on the pre-existing
report docs/RELATORIO.md referencing nonexistent hermes/skills/doctor/SKILL.md. Gate24 fails after
concurrent staging of the Hermes package enlarged the clone to564tracked files/5426KiB, over4MiB.
These paths/decisions are outside this plan Owns. Do not weaken the gate or edit other work to hide it.
The index was modified concurrently (260paths including this feature); this task did not stage or
unstage it. HEAD observed at final review:ba6cd8d. Preserve that concurrent state.

## Evidence and next action
Read .graph-powers/logs/sdd/2026-09-09-persistent-planning-resume/ACCEPTANCE.md and task-reviews.md.
They link exact gate logs, immutable responses, RED/GREEN, scoped review diff and fingerprints.
After responsible work resolves the two external gates, compare source/config/environment and
rerun affected gates; reuse unaffected proof. Only then close G1.2 and global acceptance. Do not
reset reservations:8/8dispatches used, including the distinct final reviewer. No further feature
implementation remains; an additional agent run requires a later user-requested run under policy.

## Limits and rollback
Status is neither approval, actual CHECK execution nor an atomic multi-file snapshot. Captured
fixture behavior is not clean-session routing proof; no performance claim. Context49596/199970bytes,
unchanged caps. Roll back only this feature's hunks in review.diff, consumers before CLI, preserving
all prior/subsequent changes and execution records; never apply the full saved baseline to the tree.
