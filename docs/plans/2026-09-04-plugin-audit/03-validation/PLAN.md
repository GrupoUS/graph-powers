# Close proven validation blind spots — implementation plan

**Date:** 2026-09-04 · **Branch:** main · **Baseline:** 0a59d3a7c1b8d0ecede6d88a64a3a6107d4034a4
**Tier:** L5
**Risk surface:** local installation ownership and CI/contracts; no live deployment
**Design authority:** [shared specification](../spec.md).
**Authorization:** user authorized completing the plans and applying the local corrections with Gauntlet; no commit, publication or global installation changes. Independent plan review precedes implementation.

## Destination

Complete N6, N7; audit F06, F11. Every task's acceptance must be proved by the existing focused
runner and its new negative/positive fixtures where required. Preserve the functionality listed in
the shared specification. Stop at reviewed, unstaged changes.

## Reuse ledger

| Need | Existing asset | Decision |
|---|---|---|
| T1.1: Validate explicit dot-relative live file references | .github/check_file_references.py | EXTEND existing owner and tests; no new subsystem |
| T1.2: Run existing capture regressions in CI and update the local gate index | .github/workflows/ci.yml | EXTEND existing owner and tests; no new subsystem |

## Regression watchlist

| Existing behavior | Proof command | Owner phase |
|---|---|---|
| Historical documents remain exempt while current rules are checked | `python3 .github/test_file_references.py` | final phase |
| Existing skill capture negative fixtures remain isolated from live providers | `python3 skills/skill-improve/scripts/test_capture_trigger_evals.py` | final phase |

## Execution graph

T1.1: none  
T1.2: none

Task order is sequential where files overlap. Independent tasks may share a writer lane in an
explicitly ordered package, but may never have concurrent writers. Ordering between sibling plans
is review focus, not a fabricated data dependency. Rebase this work order on any already accepted
sibling changes before editing common files.

Before this slice starts, capture a working-tree TASK_BASE. Exclude pre-existing and concurrent
hunks in hooks/_config.py, hooks/test_hooks.py and .codex-plugin/plugin.json from attribution;
compare ownership and rollback against the snapshot rather than HEAD alone.

## Dispatch matrix

| Task | Agent | Skill | Owns | Needs |
|---|---|---|---|---|
| T1.1 | graph-powers:debugger | graph-powers:debugger | .github/check_file_references.py, .github/test_file_references.py, hooks/AGENTS.md, skills/AGENTS.md | none |
| T1.2 | graph-powers:debugger | none | .github/workflows/ci.yml, .claude/rules/verify-supplements.md | none |

## Runtime budget and review

Use the configured caps from the schema/config, never a new literal allowance: 8 cumulative
dispatches per workflow, width 3, 12 tasks, 2 re-patches and 8 rounds per role in the resolved runtime (the schema default is 4).
Before each wave reserve the independent wave review, final review and final verify-loop route.
A capped correction stops with evidence; it cannot silently skip a critic or restart the budget.
No child spawns. Model/effort selection comes from registered roles, never a dispatch override.

## Risk

The shared spec owns the risk register and rollback principles. This slice uses temporary homes
for installer tests, preserves existing dirty changes and has no external effects. A positive
same-version/no-change test is as important as the new negative case.

## Phase 1 — Focused boundary corrections [SEQUENTIAL]

- [x] **T1.1** — Validate explicit dot-relative live file references
  Owns: .github/check_file_references.py, .github/test_file_references.py, hooks/AGENTS.md, skills/AGENTS.md
  Needs: none
  Acceptance: Missing ./ and ../ live references are rejected, valid owner-relative paths pass, historical exclusions remain valid, and the known turbo-helper path points at its existing owner.
  Agent: graph-powers:debugger · Skill: graph-powers:debugger · Effort: design
  TDD: required
  CHECK: python3 .github/test_file_references.py
  EXPECT: OK
  EVIDENCE: RED missed explicit prefixes/escape and untracked policy; GREEN parent 12 tests OK, live scan empty; evaluator compliance/quality/integration PASS at363fa84.
  Steps:
    1. Read the regex, candidate resolution order and historical/runtime exclusions; reproduce the missing ../ path from the audit fixture.
    2. Add RED tests for missing dot-relative paths plus valid owner-relative and spaced-directory positives. Preserve the existing hidden-rule and tracked-runtime tests.
    3. Extend the current path matcher rather than adding another scanner. Resolve explicit prefixes at their owner; avoid treating a same-named file at an unrelated level as proof.
    4. Run the scanner and inspect every newly exposed missing path. Correct only the confirmed turbo helper references to skills/debugger/scripts/turbo_dry_json.py at the appropriate relative location.
    5. Observe GREEN in the test module and an empty live-reference scan. Keep historical records intact.
    6. Record newly scanned edges and exact check output; do not expand into arbitrary Markdown URL validation.

- [x] **T1.2** — Run existing capture regressions in CI and update the local gate index
  Owns: .github/workflows/ci.yml, .claude/rules/verify-supplements.md
  Needs: none
  Acceptance: CI invokes test_capture_trigger_evals.py beside the existing eval-runner test, and the verification supplement names the current required standalone gates without inventing build or lint tasks.
  Agent: graph-powers:debugger · Skill: none · Effort: design
  TDD: not-applicable (connects an existing tested suite to CI and corrects its gate inventory; no new runtime logic)
  CHECK: python3 -c "from pathlib import Path; p='skills/skill-improve/scripts/test_capture_trigger_evals.py'; ci=Path('.github/workflows/ci.yml').read_text(); supplement=Path('.claude/rules/verify-supplements.md').read_text(); assert 'python3 '+p in ci; assert p in supplement; print('CAPTURE CI WIRING OK')"
  EXPECT: CAPTURE CI WIRING OK
  EVIDENCE: Configuration-only: parent CAPTURE CI WIRING OK; capture 15 tests OK; YAML parsed; Hermes dot-path doctor0/38 registrations; reviewer VAL01/02 resolved at7e19d76.
  Steps:
    1. Read the existing eval-runner CI step and the verification supplement; confirm the omitted module already runs 15 isolated tests.
    2. Add one adjacent invocation of the existing capture test module. Keep current OS/client jobs and do not add a live provider job.
    3. Correct the supplement's stale count and include the already declared Oxc/Hermes checks where appropriate; use existing scripts as authorities.
    4. Parse the edited YAML locally and compare the exact script path; run the capture module and existing eval-runner module.
    5. Record the local result as local. Do not claim a GitHub Actions run happened, publish a branch or alter global tooling.

### Phase 1 gate

- [x] **G1.4** — File-reference negative and positive cases pass
  CHECK: python3 .github/test_file_references.py
  EXPECT: OK
  EVIDENCE: 12 file-reference tests OK; exit 0.

- [x] **G1.6** — Current live references all resolve
  CHECK: python3 .github/check_file_references.py
  EXPECT: empty stdout and exit 0
  EVIDENCE: Live reference scan empty; exit 0.

- [x] **G1.7** — Capture CI and local gate wiring exists
  CHECK: python3 -c "from pathlib import Path; p='skills/skill-improve/scripts/test_capture_trigger_evals.py'; ci=Path('.github/workflows/ci.yml').read_text(); supplement=Path('.claude/rules/verify-supplements.md').read_text(); assert 'python3 '+p in ci; assert p in supplement; print('CAPTURE CI WIRING OK')"
  EXPECT: CAPTURE CI WIRING OK
  EVIDENCE: CAPTURE CI WIRING OK; exit 0.

- [x] **G1.1** — Focused boundary regression suite passes
  CHECK: python3 skills/skill-improve/scripts/test_capture_trigger_evals.py
  EXPECT: OK
  EVIDENCE: 15 capture tests OK; exit 0.

- [x] **G1.2** — Existing wiring remains resolvable
  CHECK: python3 .github/check_wiring.py
  EXPECT: /0 unresolved/
  EVIDENCE: 462 routing references checked, 0 unresolved; exit 0.

- [x] **G1.3** — Whitespace and conflict-marker diff checks pass
  CHECK: git diff --check
  EXPECT: empty stdout and exit 0
  EVIDENCE: git diff --check empty stdout; exit 0.

The parent additionally compares actual changed paths against this phase's Owns union and records
the independent critic's compliance/quality verdict before advancing. No type-check or lint gate
is invented: this repository declares neither as a CI gate.

## Verification

- [x] **G1.5** — Existing complete hook guarantees hold at the final boundary
  CHECK: python3 hooks/test_hooks.py
  EXPECT: EVERY GUARANTEE HELD
  EVIDENCE: EVERY GUARANTEE HELD; full hook suite exit 0.

Run the applicable gates from root AGENTS.md and the verification supplement, plus the focused
watchlist. Final profile is Gauntlet's `/verify loop` with the documented single fallback when
the workflow is unavailable. Keep the lease until that verdict. Do not claim live trigger,
Desktop or cross-OS evidence from source inspection. Completion updates the task evidence,
reviews and project-local learning; it does not stage, commit or install globally.

## Rollback

Restore only this slice's changed files to the pre-slice snapshot, excluding pre-existing edits
and accepted sibling changes. The temporary fixture homes clean themselves up. Never run a blanket
reset or reinstall against the operator's real settings. Release only the matching SDD lease
after success or an explicitly recorded safe abort.

## Out of scope

Global installation, permission-policy changes, model upgrades, orphan deletion, new dependencies,
new schedulers, publication and git history changes. Reopen only with an explicit owner request.

## Not yet specified

No implementation-blocking fog remains in this bounded slice. Native provider/session behavior
outside the local fixtures remains unmeasured and is reported as such. Any newly discovered
independent defect belongs in the audit notes rather than silently expanding this plan.
