# Persistent planning and verifiable resume — implementation plan

**Date:** 2026-09-09 · **Branch:** main · **Baseline:** ba6cd8d
**Tier:** L5 · **Risk surface:** none
**Design authority:** spec.md — approved inline by user; independent plan and wiring reviews PASS.

## Destination
Deliver the approved T1–T4 contract in spec.md: persistent decisions and explicit, read-only plan
status/recovery with actual CLI, behavioral and repository evidence, without changing permissions.

## Reuse ledger
| Need | Existing owner | Verdict |
|---|---|---|
| Plan and findings | PLAN.md/spec.md, Phase A/B, shared 007 | EXTEND |
| Derived status | sdd.py validate_plan, source lines, secure read helpers | EXTEND |
| Recovery | implement/prime, Phase C, loop checkpoint | EXTEND |
| Evidence freshness and budgets | existing Phase C including dirty Cole Medin improvements | REUSE |
| Client projections | codex/native-plugin.mjs | REUSE |

## Regression watchlist
| Existing contract | Proof | Owner |
|---|---|---|
| validate/acquire/dispatch/consult/legacy profiles | python3 skills/planning/scripts/test_sdd.py | T1.1 |
| Simple route and current/stale evidence | tagged planning evals including retained cases | T1.2 |
| Frontmatter, public command descriptions, models and permissions | final wiring/native/policy gates; baseline diff | T1.2 |
| Dirty work from previous plan | compare baseline-files.json and unchanged unrelated paths | controller |

## Execution graph
Approved T1 and T2 form T1.1 (capture plus CLI); approved T3 and T4 form T1.2 (consumers plus
release metadata). Each package executes its original parts sequentially and reports per-part proof.
T1.2 reads T1.1's status JSON and persistence contract. Two writer waves and their reviews, one
behavioral evaluator and a protected slot for a separate final reviewer fit the eight-dispatch cap.

## Local execution exception
The user subsequently instructed “ignore os conflitos e implemente o plano”. Proceed with this
approved plan while docs/plans/2026-09-09-hermes-package/PLAN.md owns the global lease; the previous
wait-for-lease blocker is superseded for this run only. This is no change to the shipped harness.
Do not acquire, release, replace or reset the global lease, call `sdd.py dispatch reserve`, write
shared progress, or touch another execution's files or ledgers. A denied tool/hook is not bypassed.

The controller uses only `.graph-powers/logs/sdd/2026-09-09-persistent-planning-resume/task-reviews.md`
for dispatch accounting and checkpoints. Record stable keys, roles, attempts, outcomes and current
snapshot evidence there before advancing; retain prior history across resumes. Count every child
call in this execution, including this plan confirmation, writers, wave reviews, behavioral
evaluation, corrections and final review, toward eight total. Protect one remaining slot for the
separate final reviewer before the first writer; a resumed or failed attempt never resets the cap.
At exhaustion, report completed/pending work and the remaining evidence gap without another spawn.
Task/gate evidence continues to be recorded in this PLAN.md; snapshots and outputs remain in this
plan's own runtime directory. Never use the saved baseline to remove later concurrent work.

T1/T2 remain sequential within T1.1, with observed real-CLI RED/GREEN and its declared CHECK plus
independent wave acceptance. Only that accepted current status/persistence contract admits T3/T4
in T1.2. All original task, behavioral and final gates below remain required. The real status
command must continue to report the unrelated lease as LEASE_CONFLICT (exit 4, null nextAction);
this execution authority is separate from the command's approved read-only contract.

## Dispatch matrix
| Task | Agent | Skill | Needs |
|---|---|---|---|
| T1.1 | graph-powers:debugger | planning | none |
| T1.2 | graph-powers:debugger | planning | T1.1 status and persistence contract |

## Phase 1 — Implement the approved feature [SEQUENTIAL]

- [x] **T1.1** — Implement approved persistence and read-only status contracts
  Owns: references/shared/007-path-conventions.md, skills/planning/references/phase-a-brainstorm.md, skills/planning/references/phase-b-writing-plans.md, skills/planning/scripts/sdd.py, skills/planning/scripts/test_sdd.py
  Needs: none
  Acceptance: Approved T1 decision capture and T2 status contract satisfy every spec scenario with observed CLI RED/GREEN and no new query state, preserving validator behavior.
  Agent: graph-powers:debugger · Skill: planning · Effort: design
  TDD: required
  CHECK: python3 skills/planning/scripts/test_sdd.py
  EXPECT: OK
  EVIDENCE: CLI RED four methods/23 missing-status failures exit1; GREEN four methods exit0; full SDD 55 tests OK exit0 (t1-tests.txt). Independent wave review CLI/quality/integration PASS, F1 documentary correction confirmed PASS; no code refactor after GREEN. Current fingerprints in review-hashes.json.
  Steps:
    1. Preserve the approved spec contract and existing files; implement original T1 documentation with one canonical owner and unchanged lightweight routes.
    2. Add four named CLI methods in SddCliTests: test_status_frontier, test_status_scope_and_lease, test_status_readonly_deterministic, test_status_validation_compatibility; observe missing-status RED before production code.
    3. Implement original T2 via existing validator/read helpers; confirm minimum GREEN, then refactor only while green.
    4. Cover numeric phases/Needs/gates, invalid evidence, matching/malformed/conflicting lease, nested/foreign/sibling worktrees, symlinks, immutable output/state and embedded commands. Preserve validate/acquire contracts.
    5. Return exact commands and decisive RED/GREEN outputs plus per-original-task evidence. The controller runs wave review and records acceptance.

- [x] **T1.2** — Integrate approved recovery consumers and distribution
  Owns: commands/implement.md, commands/prime.md, skills/planning/references/phase-c-executing-plans.md, skills/planning/references/loop-engineering.md, skills/planning/evals/evals.json, NOTICE, CHANGELOG.md, package.json, .claude-plugin/plugin.json, .cursor-plugin/plugin.json, .grok-plugin/plugin.json, plugin.yaml, .codex-plugin/plugin.json, .codex-plugin/marketplace.json, codex/native-command-skills/debug/SKILL.md, codex/native-command-skills/design/SKILL.md, codex/native-command-skills/evolve/SKILL.md, codex/native-command-skills/gauntlet/SKILL.md, codex/native-command-skills/implement/SKILL.md, codex/native-command-skills/perf/SKILL.md, codex/native-command-skills/plan/SKILL.md, codex/native-command-skills/pr-review/SKILL.md, codex/native-command-skills/prime/SKILL.md, codex/native-command-skills/research/SKILL.md, codex/native-command-skills/setup/SKILL.md, codex/native-command-skills/verify/SKILL.md, codex/native-agents/debugger.toml, codex/native-agents/evaluator.toml, codex/native-agents/explorer.toml, codex/native-agents/frontend-specialist.toml, codex/native-agents/librarian.toml, codex/native-agents/mobile-developer.toml, codex/native-agents/performance-optimizer.toml, codex/native-agents/project-planner.toml, codex/native-agents/security-reviewer.toml, codex/native-agents/skill-improver.toml, codex/native-agents/ui-ux-designer.toml, codex/native-agents/verification.toml
  Needs: T1.1 (reads: status JSON interface and canonical persistence responsibilities)
  Acceptance: Approved T3 recovery scenarios pass real tagged eval responses; original T4 provenance, six versions 1.20.0 and generated projections pass final checks without changing pre-existing behavior, descriptions, models or permissions.
  Agent: graph-powers:debugger · Skill: planning · Effort: design
  TDD: not-applicable (instruction documents, behavioral eval fixtures and generated metadata)
  CHECK: python3 .github/check_context_budget.py
  EXPECT: within budget
  EVIDENCE: T3/T4 compliance and integration PASS in wave review; final independent reviewer confirmed F1 correction and implementation quality PASS. Current 9/9 behavioral cases,25/25 assertions,54positive/negative controls exit0; six versions1.20.0 and25unchanged generated artifacts; context49596/199970 exit0. Full global closure remains G1.2.
  Steps:
    1. Implement explicit path then valid active binding then unique candidate selection; invalid binding stops, no mtime/lease fallback, no writes in dry-run including conversational plans.
    2. Keep prime ordinary loads free of plan scans/status. On identified resume use status and the single loop-engineering recovery protocol; retain existing evidence freshness and budget protections.
    3. Reuse existing trivial/stale/valid-evidence evals; add only missing planning-resume scenarios for ambiguity, invalid binding, partial recovery, new scope after completion and conversational dry-run. Parent captures actual responses per case without installing a capture backend.
    4. Append original T4 provenance/CHANGELOG and update six metadata versions to 1.20.0 without removing 1.19.5 content. Run bun codex/native-plugin.mjs; its 26 exact outputs are in Owns and only plugin version may differ.
    5. Condense owned text until context floor/ceiling fit unchanged caps; preserve public descriptions and all existing assertions. Return per-original-task evidence and exact changed paths.

### Phase gate
- [x] **G1.1** — Verify behavioral recovery cases
  CHECK: python3 skills/skill-improve/scripts/run_evals.py --skill-path skills/planning --evals-path skills/planning/evals/evals.json --response-dir .graph-powers/logs/evals/planning-resume --case-tag planning-resume --threshold 1.0
  EXPECT: PASSED: every case reached the threshold
  EVIDENCE: Official run_evals with --case-tag planning-resume --threshold1.0:9/9cases25/25assertions exit0; behavior-results.txt. Original response hashes unchanged; independent final review confirms behavioral evidence and both F1 corrections.
- [ ] **G1.2** — Verify every declared repository gate
  CHECK: python3 .graph-powers/logs/sdd/2026-09-09-persistent-planning-resume/run-gates.py --all
  EXPECT: ALL 25 GATES PASSED
  EVIDENCE: FAIL:23/25gates passed (26commands in current inventory). Gate17:pre-existing docs/RELATORIO.md broken reference; gate24:concurrent staged Hermes package raises clone to564files/5426KiB, over4MiB. gates.json and ACCEPTANCE.md contain exact commands/exits. Both failures outside approved Owns; final review implementationPASS, globalWITH FIXES.

## Verification
The controller runs all 25 commands from .claude/rules/verify-supplements.md in exact order, storing
commands, exits and decisive output under the plan runtime directory. A portable local runner only
executes that inventory and checks six disk versions exceed HEAD; it changes no gate policy.
Codex fixture-only check_codex remains CI-only. Context baseline: 49,371 floor / 199,795 ceiling.
Use current task snapshots (including pre-existing dirty baseline) for independent wave/final review.
Do not call textual fixture evals proof of clean-session trigger routing. No performance claim.

## Rollback
Revert only feature hunks relative to baseline-files.json, consumers before status. Retain previous
changes, approval evidence and all ledgers. No broad checkout/reset/clean or automatic publication.

## Out of scope
Upstream installation, hooks/Stop loops, new registries/parsers, client model/permission changes,
other-plan completion or ledger edits, staging, commit, push, PR, merge and publishing.

## Not yet specified
None. Existing user approval covers this exact implementation, the completed prior lease release
and the local concurrency exception above; it grants no authority over the current Hermes lease.

## Final review outcome
Implementation compliance/quality and both wave corrections independently PASS. No feature finding
remains. Global acceptance is NEEDS_WORK solely for gates17/24 outside Owns. All eight dispatches
are recorded in the own task-review ledger; no reset. Do not mark G1.2 or the whole plan complete
until current evidence resolves both gates. User work and concurrent staging remain preserved.
