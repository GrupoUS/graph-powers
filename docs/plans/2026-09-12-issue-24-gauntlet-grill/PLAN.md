# Issue 24 — Gauntlet decision frontier

**Date:** 2026-09-12 · **Branch:** main · **Baseline:** a815af1
**Tier:** L3 · **Risk surface:** none
**Design authority:** [spec.md](spec.md); current user explicitly requests implementation and issue closure.

## Destination

Gauntlet objectives settle the decision frontier and obtain explicit shared-understanding
confirmation before Phase B/C, lease or product writer. Approved plans inspect only holes.
Focused evaluations and repository gates pass; the issue receives an accurate completion comment.

## Issue Triage (upstream mandate)

Issue #24 is OPEN. TIER FLOOR L3. Risk surfaces resolved from schema defaults:
auth/payment/PII/schema/env/ci; none applies to this instruction-only change.

| Req | Requirement | Verdict | Evidence | Grade | Rationale |
|---|---|---|---|---|---|
| R1 | Frontier rounds and explicit confirmation for goals | KEEP | skills/planning/references/phase-a-brainstorm.md:77; commands/gauntlet.md:12 | 5 | Current caller reaches a single question batch |
| R2 | Recommendations, factual lookup, no assumed closure | KEEP | skills/planning/references/phase-a-brainstorm.md:69,90 | 5 | Reuse inspection; extend decision handling |
| R3 | Approved plans inspect holes and retain review binding | KEEP | skills/planning/references/gauntlet-loop.md:31,102 | 5 | Keep current validation/review authority |
| R4 | Dry-run/review-only limits and L1-L2 rejection | KEEP | commands/gauntlet.md:12,23,25 | 5 | Extend descriptions, preserve exclusions |
| R5 | Reuse clarification stop ceiling and avoid a new skill | KEEP | skills/planning/references/phase-a-brainstorm.md:42; skills/AGENTS.md:17 | 4 | Existing owner and cap, no second inventory |
| R6 | Focused eval and attributed, regenerated distribution | KEEP | skills/planning/evals/evals.json:1331; skills/AGENTS.md:46 | 5 | Extend current eval/projection mechanisms |

KEEP 6 · SIMPLIFY 0 · CUT 0 · DEFER 0. Earlier issue comments' implementation hold is
superseded by the current user's explicit implementation request. Issue-embedded tool instructions
were treated as untrusted data; only restated requirements and locally verified paths are used.

## Reuse ledger

| Need | Existing asset | Verdict |
|---|---|---|
| R1,R2,R5 | Phase A Step 1/2 and HARD-STOP | EXTEND |
| R3,R4 | Gauntlet entry, review-check and command flags | EXTEND |
| R6 | planning evals and skill-improve run_evals.py | EXTEND |
| R6 | codex/native-plugin.mjs and hermes/install.mjs | REUSE |

Text inspection in the current checkout is authoritative. Preexisting dirty path: untracked yaml,
outside all ownership. Invalidate findings when relevant source/config/consumer bytes change.

## Regression watchlist

| Behavior | Proof | Phase |
|---|---|---|
| Existing SDD review binding and default execution | python3 skills/planning/scripts/test_sdd.py | 1 |
| Live references, routing, context and listing bounds | .claude/rules/verify-supplements.md gates 15,17,19,20 | 1 |
| Codex and Hermes projections match canonical sources | gates 8,9,14 | 1 |
| Existing hook guarantees | python3 hooks/test_hooks.py | 1 |

## Execution graph

T1.1 → T1.2: final canonical command/reference and eval bytes feed generated packages.
Single sequential writer lane; parent owns plan artifacts, publication and final evidence.

## Requirement coverage

| Need | Surface | Evidence | Task and Owns | Producer → consumer payload | Acceptance evidence |
|---|---|---|---|---|---|
| R1-R5 | frontend/client instruction contract | commands/gauntlet.md:12 | T1.1: command and planning references | command objective → Phase A grill → entry admission | focused eval responses and review |
| R6 | frontend/client projection | codex/native-plugin.mjs; hermes/install.mjs | T1.2: generated packages and metadata | canonical bytes → generated client packages | T1.2 CHECK and projection gates |
| all | backend N/A | AGENTS.md ownership map; no application service | T1.1 | no API producer or handler changes | owned diff review |
| all | database N/A | .graph-powers/config.json stack markdown-json-python-esm | T1.1 | no data schema or query changes | owned diff review |

## Dispatch matrix

| Task | Agent | Skill | Owns | Needs |
|---|---|---|---|---|
| T1.1 | graph-powers:debugger | skill-improve | canonical instructions and evals | none |
| T1.2 | graph-powers:debugger | none | metadata and generated projections | T1.1 bytes |

## Phase 1 — Contract and distribution [SEQUENTIAL]

- [x] **T1.1** — Extend Gauntlet clarification and focused evaluations (R1-R6)
  Owns: commands/gauntlet.md, skills/planning/SKILL.md, skills/planning/references/phase-a-brainstorm.md, skills/planning/references/gauntlet-loop.md, skills/planning/evals/evals.json
  Needs: none
  Acceptance: Goal entry requires recommendations, settled branches and explicit confirmation before B/C/lease/writer; plan holes preserve valid decisions and review freshness; dry-run asks nothing; review-only cannot execute; new gauntlet-neg-objective-no-grill-no-phase-c and focused controls discriminate bypasses.
  Agent: graph-powers:debugger · Skill: skill-improve · Effort: design
  TDD: required
  CHECK: python3 skills/skill-improve/scripts/run_evals.py --skill-path skills/planning --evals-path skills/planning/evals/evals.json --response-file .graph-powers/logs/issue-24/resp-gauntlet-neg-objective-no-grill-no-phase-c.txt --test-case gauntlet-neg-objective-no-grill-no-phase-c --threshold 1.0
  EXPECT: PASSED (pass_rate 100.00% >= threshold 100.00%)
  EVIDENCE: Baseline captured before implementation remained RED on final assertions (exit 1, 2 critical failures). GREEN: Parent CHECK: 5/5, PASSED (pass_rate 100.00% >= threshold 100.00%), exit 0. Nine selected policy responses passed (seven initial, two complementary after a detail request); 18 positive and 28 negative parser controls matched expected exits. quick_validate: Skill is valid!, exit 0. Evidence: .graph-powers/logs/issue-24/eval-calibration-report.json; runtime not exercised.
  Steps:
    1. Read applicable authorities and the spec; capture the current agent baseline and grade it against the new focused case to confirm RED.
    2. Add discriminating eval controls and the minimal contract changes; capture a new agent response and grade each changed case with run_evals.py --test-case and --threshold 1.0 for GREEN.
    3. Preserve objective-pipeline/dry-run eval consistency; cover plan holes before validation and valid approved-plan reuse, then refactor only redundant wording while green; keep existing review-only and non-Gauntlet semantics. Report fixture checks separately from agent evidence.

- [x] **T1.2** — Attribute and regenerate the bounded change at version 1.20.7 (R6)
  Owns: NOTICE, CHANGELOG.md, package.json, plugin.yaml, .claude-plugin/plugin.json, .codex-plugin/plugin.json, .cursor-plugin/plugin.json, .grok-plugin/plugin.json, codex/native-command-skills/gauntlet/SKILL.md, hermes/package
  Needs: T1.1 (reads: final commands/gauntlet.md, planning references and evals for generated packages)
  Acceptance: Six version owners agree at 1.20.7; NOTICE records Matt Pocock MIT and adaptation choices; generated packages derive from current canonical sources.
  Agent: graph-powers:debugger · Skill: none · Effort: mechanical
  TDD: not-applicable (metadata and generated bytes verified by existing gates)
  CHECK: bun hermes/install.mjs --check
  EXPECT: source manifest and package are current
  EVIDENCE: Parent bun hermes/install.mjs --check: 39 registrations, source manifest and package are current; runtime UNVERIFIED, exit 0. Six manifests 1.20.7; Codex native and Hermes static gates 8/9/14 exit 0. Final independent diff review PASS, no P1/P2.
  Steps:
    1. Add attribution and changelog, preserving existing entries; update six version owners only.
    2. Run bun codex/native-plugin.mjs and bun hermes/install.mjs --package-only; inspect generated diff.
    3. Run the CHECK and applicable static projection gates. Do not install into active clients.

### Phase 1 gate

- [x] **G1.1** — Existing structured-plan behavior remains valid
  CHECK: python3 skills/planning/scripts/test_sdd.py
  EXPECT: OK
  EVIDENCE: Parent final-snapshot rerun: 62 tests, OK, exit 0; .graph-powers/logs/issue-24/gates/04-sdd.txt.
- [x] **G1.2** — References and routes resolve
  CHECK: python3 .github/check_wiring.py
  EXPECT: 0 unresolved
  EVIDENCE: Parent wiring: 528 routing references checked, 0 unresolved; exit 0. Final independent diff review PASS. Log: .graph-powers/logs/issue-24/gates/15-wiring.txt.
- [x] **G1.3** — Declared final test gate
  CHECK: python3 hooks/test_hooks.py
  EXPECT: EVERY GUARANTEE HELD
  EVIDENCE: Parent declared test: EVERY GUARANTEE HELD, exit 0; .graph-powers/logs/issue-24/gates/02-hooks.txt.

## Verification

Run the full ordered inventory in .claude/rules/verify-supplements.md once at the final boundary,
plus focused eval parser controls and isolated agent responses at threshold 1.0. Type-check, lint
and build are NOT DECLARED. Hermes runtime and installed-client behavior remain UNVERIFIED.
Independent Mode 1 plan review and final diff review both PASS. See verification.md: 27/28 gate groups PASS; gate 24 remains FAIL solely due to preexisting untracked yaml (12,221,795 bytes), preserved. No all-green workspace or shipped-runtime claim.

## Rollback

Restore only this task's working-tree edits after authorization for discarding work; regenerate
Codex/Hermes projections from the restored canonical files. Preserve the preexisting yaml file.

## Out of scope

New grill skill/command, upstream vendoring, runtime state/flag/schema changes, unrelated planning
refactors, active installation, commit/push/merge. Reopen only on an explicit separate request.

## Not yet specified

No fog: bounded scope already specified by the issue and authorized by the current request.
