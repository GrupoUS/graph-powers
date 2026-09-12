# Issue 25 — Verification

Baseline: a815af18baa4c1c14658a655b50ccf646ea7ee05. Existing staged issue-24 changes and
external yaml/yaml.ps operations are excluded from this issue's ownership.

## Behavioral evidence

- RED: old CLI disjoint acquisition returned [0,2] instead of [0,0]; G4 allowed four foreign
  writes. A release/dispatch race was reproduced before extending the short transaction lock.
- GREEN: author ran `python3 skills/planning/scripts/test_sdd.py`: 70 tests, OK, exit 0;
  `python3 hooks/test_hooks.py`: EVERY GUARANTEE HELD, exit 0. Final logs are retained under
  `.graph-powers/logs/issue-25/author/`.
- Tests exercise concurrent disjoint/overlapping acquisitions, owner lifecycle, expiry/pruning,
  migration preserving run/dispatch, Gauntlet resume identity, malformed/symlink records,
  process death while holding the transaction lock, literal paths and dispatch/release races.
- Current execution's legacy lease was migrated and renewed, retaining run
  d9c2b7248997c878dcf28cbc and its dispatch ledger.

## Distribution

`bun hermes/install.mjs --package-only` and `bun hermes/install.mjs --check` exited 0,
with 39 registrations. All six version owners are 1.20.8; issue-24 content is retained.

## Final checks

Parent executed all 28 declared gate groups: 27 PASS, one existing checkout-budget failure.
`python3 .github/check_clone.py` exited 1: source 16,148,618 bytes against 4,194,304;
external `yaml.ps` accounts for 12,221,795 bytes. The issue's source plus other existing source
without that file is 3,926,823 bytes, but no filtered check is claimed as passed. The file and
external staged state were preserved. Hermes is 1,832,141 bytes against 2,097,152 and its proofs pass.
Detailed commands/exits: `.graph-powers/logs/issue-25/gates/results.json`.
The final parent rerun passed 71 SDD tests and EVERY GUARANTEE HELD. Wave review found one P2:
a timestamp integer 10**400 raised OverflowError in both readers. The bounded correction and
regressions passed; a fresh independent confirmation marked compliance/quality/integration PASS.
Current affected-gate results: `.graph-powers/logs/issue-25/correction-gates/results.json`;
unaffected initial results remain applicable. Final review accepted runtime but found F25-01: prime/status and Phase C final release omitted
session identity. Both canonical calls now preserve it; Codex/Hermes were regenerated. Affected
documentation/distribution gates pass in `.graph-powers/logs/issue-25/doc-gates/results.json`.
Final bounded confirmation PASS/READY: no outstanding Critical/Important/Minor finding.
Runtime source and its 71-test evidence are unchanged. Local issue acceptance is READY;
repository-wide verification remains NEEDS-WORK solely for the external checkout-size failure.
No commit, push, release publication or installed-client update was performed.
Native installed-client enforcement and Windows execution are UNVERIFIED; portable static checks
and Linux subprocess tests do not establish those runtime properties. Type-check/lint/build are
NOT DECLARED by the repository. The fixture-dependent Codex install assertion remains CI-only.

## Issue closure

Published implementation/validation comment 5648874383; GitHub confirmed issue 25 CLOSED
at 2026-09-12T21:40:51Z. The local run lease was released; status confirms ABSENT.
No commit or push was performed.
