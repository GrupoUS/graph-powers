# Gauntlet command — implementation plan

**Date:** 2026-08-31 · **Branch:** `main` · **Baseline:** `215b36d`
**Tier:** L5 · **Risk surface:** public command routing, bounded multi-agent execution and client projection
**Design authority:** the user-approved Stage 1 architecture in the task that created this plan

## Destination

An explicit `/gauntlet <approved-plan-file-or-directory> [--dry-run]` command executes only an
approved structured plan through the existing Planning Phase C engine, adding bounded per-task
builder/critic/correction behavior and finishing through `/verify loop`. The default `/implement`
route remains unchanged.

## Reuse ledger

| # | Need | Existing asset | Verdict | Why extending fails (NEW only) |
|---|---|---|---|---|
| 1 | Validation, write lease, scheduler, packages and evidence | `skills/planning/references/phase-c-executing-plans.md` and `skills/planning/scripts/sdd.py` | EXTEND | — |
| 2 | Builder and independent review contracts | `skills/planning/references/execution/` | REUSE | — |
| 3 | Final adversarial verification | `commands/verify.md` and `workflows/ultra-verify.js` | REUSE | — |
| 4 | Public opt-in route | `commands/implement.md` pattern | NEW | A separate public intent needs its own command entrypoint; duplicating Phase C is forbidden. |
| 5 | Canonical profile delta | Planning references | NEW | Keeping the detailed delta in the adapter would exceed listing/context budgets and duplicate Phase C. |
| 6 | Cross-client projection | Existing Claude/Codex/Cursor/Grok generators and Hermes translation | EXTEND | — |

## Regression watchlist

| # | Existing behaviour that must still work | How to prove it | Phase |
|---|---|---|---|
| 1 | `/implement` keeps the default Phase C route and `/verify quick` close | Planning evals plus focused source assertions | 3 |
| 2 | L1-L2 stay local and do not gain orchestration | Gauntlet negative evals | 1 |
| 3 | Structured plan validation remains fail-closed for malformed plans | `python3 skills/planning/scripts/test_sdd.py` | 2 |
| 4 | Claude remains the single source for generated Codex/Cursor/Grok surfaces | client checks and installer dry-runs | 6 |
| 5 | Context and listing limits remain unchanged | budget gates | 6 |

## Execution graph

`T1.1 → T2.1 → T3.1 → T3.2 → T3.3 → T4.1 → T5.1 → T5.2 → G6.1`

- T2.1 reads T1.1's failing pressure cases.
- T3.1 reads T2.1's normalized tier contract.
- T3.2 reads T3.1's canonical Gauntlet profile.
- T3.3 reads the adapter and profile call site.
- T4.1 reads the complete routing/profile behavior before capturing fresh GREEN responses.
- Documentation and version metadata follow behavior evidence.
- Final validation reads every prior deliverable.

## Dispatch matrix

| Task | Agent | Skill | Owns | Needs |
|---|---|---|---|---|
| T1.1 | `graph-powers:debugger` | `skill-improve` | Planning eval definition and ignored RED response cache | none |
| T2.1 | `graph-powers:debugger` | `debugger` | SDD parser and focused tests | T1.1 |
| T3.1 | `graph-powers:debugger` | `skill-improve` | canonical profile reference | T2.1 |
| T3.2 | `graph-powers:debugger` | `skill-improve` | public command adapter | T3.1 |
| T3.3 | `graph-powers:debugger` | `skill-improve` | Planning and Phase B/C routing | T3.2 |
| T4.1 | `graph-powers:debugger` | `skill-improve` | Hermes translation and ignored GREEN response cache | T3.3 |
| T5.1 | `graph-powers:debugger` | `skill-improve` | human documentation and provenance | T4.1 |
| T5.2 | `graph-powers:debugger` | `skill-improve` | synchronized version manifests | T5.1 |

## Phase 1 — Pressure-test contract  [SEQUENTIAL]

- [x] **T1.1** — Add eleven Gauntlet pressure cases and capture genuine RED responses
  Owns: skills/planning/evals/evals.json, .graph-powers/cache/gauntlet-evals/red
  Needs: none
  Agent: graph-powers:debugger · Skill: skill-improve · Effort: focused
  Basis: `skills/planning/evals/evals.json`, confidence 5
  Parallel: no; the eval contract must exist before any behavior content that could satisfy it
  Mode: write
  TDD: not-applicable (this task defines and baselines the tests before production prompt changes)
  Steps:
    1. Add three positive and eight negative cases without reading desired answers into the response.
    2. Generate fresh read-only responses against the current Planning skill and prove critical assertion failures.
  CHECK: `python3 skills/skill-improve/scripts/run_evals.py --skill-path skills/planning --evals-path skills/planning/evals/evals.json --response-dir .graph-powers/cache/gauntlet-evals/red --threshold 1.0`
  EXPECT: FAILED: at least one case is below the threshold
  EVIDENCE: RED — 11/11 fresh responses against immutable HEAD 215b36d7 failed at least two critical Gauntlet assertions; runner exit 1
  Rollback: remove only the eleven new eval objects and the ignored RED response directory
  Acceptance: all eleven named pressure cases have genuine current-source responses and fail for the missing Gauntlet contract
  Risk: medium

### Phase 1 gate

- [x] **G1.1** — RED is observable before production prompt changes
  CHECK: `python3 skills/skill-improve/scripts/run_evals.py --skill-path skills/planning --evals-path skills/planning/evals/evals.json --response-dir .graph-powers/cache/gauntlet-evals/red --threshold 1.0`
  EXPECT: FAILED: at least one case is below the threshold
  EVIDENCE: RED — final prompts replayed against HEAD: all eleven gauntlet-* cases FAIL with critical assertion misses; exit 1

## Phase 2 — Mechanical plan contract  [SEQUENTIAL]

- [x] **T2.1** — Require and normalize the structured plan tier
  Owns: skills/planning/scripts/sdd.py, skills/planning/scripts/test_sdd.py
  Needs: T1.1 (reads: failing Gauntlet cases that depend on mechanical tier routing)
  Agent: graph-powers:debugger · Skill: debugger · Effort: focused
  Basis: `skills/planning/scripts/sdd.py:623`, confidence 5
  Parallel: no; tests and parser form one behavior seam
  Mode: write
  TDD: required
  Steps:
    1. Add focused tests for valid normalization plus missing and malformed tier and observe RED.
    2. Implement the minimum parser change, observe GREEN and refactor only while green.
  CHECK: `python3 skills/planning/scripts/test_sdd.py`
  EXPECT: `OK`
  EVIDENCE: RED — missing tier was accepted and malformed L7 passed; GREEN — 37 tests ran in 1.967s, OK, including Gauntlet Acceptance, Skill, writer and acquire admission
  Rollback: revert only the tier tests, tier expression and normalized output field
  Acceptance: validate/acquire return normalized `tier`, and missing or malformed tiers route to `/plan`
  Risk: medium

### Phase 2 gate

- [x] **G2.1** — Structured plan tier contract is green
  CHECK: `python3 skills/planning/scripts/test_sdd.py`
  EXPECT: `OK`
  EVIDENCE: 37 tests ran in 1.967s; OK; validate/acquire normalize L1-L6 and repeat Gauntlet admission before lease

## Phase 3 — Explicit Gauntlet execution profile  [SEQUENTIAL]

- [x] **T3.1** — Author the canonical bounded Gauntlet profile
  Owns: skills/planning/references/gauntlet-loop.md
  Needs: T2.1 (reads: normalized tier value and invalid-plan behavior)
  Agent: graph-powers:debugger · Skill: skill-improve · Effort: deep
  Basis: `skills/planning/references/phase-c-executing-plans.md:52`, confidence 5
  Parallel: no; this is the single source consumed by the adapter and Planning route
  Mode: write
  TDD: required
  Steps:
    1. Use the failing pressure assertions as RED criteria for scheduler, critic, caps, visual A/B and final close.
    2. Add only the delta over Phase C, then run the pressure probe toward GREEN.
  CHECK: `python3 skills/skill-improve/scripts/quick_validate.py skills/planning`
  EXPECT: `Skill is valid!`
  EVIDENCE: RED — baseline Gauntlet cases missed bounded lanes, critic matrix, caps and final close; GREEN — Planning quick validation prints Skill is valid! and full evals pass 24/24
  Rollback: remove the new canonical reference
  Acceptance: one reference defines the logical lane, objective critic, bounded corrections, optional visual comparison and `/verify loop`
  Risk: medium

- [x] **T3.2** — Add the thin `/gauntlet` public adapter
  Owns: commands/gauntlet.md
  Needs: T3.1 (reads: canonical profile path and entry/exit contract)
  Agent: graph-powers:debugger · Skill: skill-improve · Effort: focused
  Basis: `commands/implement.md`, confidence 5
  Parallel: no; the adapter must point at the completed canonical profile
  Mode: write
  TDD: required
  Steps:
    1. Keep argument, approval, dry-run and eligibility rules as explicit RED criteria.
    2. Add the minimum conditional profile load and Phase C handoff, then prove those criteria GREEN without copying the engine.
  CHECK: `python3 .github/check_context_budget.py`
  EXPECT: `within budget`
  EVIDENCE: RED — baseline had no public adapter or generated Codex route; GREEN — command is 1,250 B, context floor 269,392 B and listing 10,300/10,752
  Rollback: remove `commands/gauntlet.md`
  Acceptance: the command requires an explicit approved plan, rejects unknown flags, has side-effect-free dry-run and never changes default `/implement`
  Risk: medium

- [x] **T3.3** — Wire Gauntlet into Planning, Phase B and Phase C without changing defaults
  Owns: skills/planning/SKILL.md, skills/planning/references/phase-b-writing-plans.md, skills/planning/references/phase-c-executing-plans.md
  Needs: T3.2 (reads: public adapter contract and canonical profile call site)
  Agent: graph-powers:debugger · Skill: skill-improve · Effort: deep
  Basis: `skills/planning/SKILL.md:74`, confidence 5
  Parallel: no; all three files describe one routing contract
  Mode: write
  TDD: required
  Steps:
    1. Use the Gauntlet RED eval failures to constrain the explicit route and L3 plan exception.
    2. Add a minimal conditional branch, reach GREEN, and preserve ordinary L3 inline execution and `/verify quick`.
  CHECK: `python3 skills/skill-improve/scripts/quick_validate.py skills/planning`
  EXPECT: `Skill is valid!`
  EVIDENCE: RED — baseline route assertions failed for L3/L4, focused review and /verify loop; GREEN — 24/24 eval cases pass and default /implement retains approved L4 plus /verify quick
  Rollback: remove only Gauntlet-specific routing sentences from the three files
  Acceptance: only explicit Gauntlet loads the profile; L3 is sequential; L4+ waves remain ownership-safe; default Phase C still closes with `/verify quick`
  Risk: high

### Phase 3 gate

- [x] **G3.1** — Prompt and routing contracts validate within budget
  CHECK: `python3 .github/check_context_budget.py`
  EXPECT: within budget
  EVIDENCE: quick_validate exit 0; context 269,392/270,000 B floor and 406,025/500,000 B ceiling; listing 10,300/10,752

## Phase 4 — Client translation and real GREEN  [SEQUENTIAL]

- [x] **T4.1** — Translate Gauntlet honestly for Hermes and capture twenty-four fresh GREEN responses
  Owns: hermes/skills/graph-engineering/SKILL.md, .graph-powers/cache/gauntlet-evals/green
  Needs: T3.3 (reads: complete canonical Gauntlet route and default-route boundary)
  Agent: graph-powers:debugger · Skill: skill-improve · Effort: deep
  Basis: `hermes/skills/graph-engineering/SKILL.md:14`, confidence 5
  Parallel: no; fresh responses must observe the final prompt source
  Mode: write
  TDD: required
  Steps:
    1. Preserve the RED route assertions while adding only the translated Hermes method and state `/gauntlet` and `/verify loop` slash availability as NOT SUPPORTED.
    2. Generate fresh read-only responses for all twenty-four cases and require threshold 1.0 — GREEN.
  CHECK: `python3 skills/skill-improve/scripts/run_evals.py --skill-path skills/planning --evals-path skills/planning/evals/evals.json --response-dir .graph-powers/cache/gauntlet-evals/green --threshold 1.0`
  EXPECT: `/Cases:\s+24\s+\|\s+Passed:\s+24\s+\|\s+Failed:\s+0/`
  EVIDENCE: RED — baseline Hermes/Gauntlet response failed 5/5 capability assertions; GREEN — 24 fresh per-case responses pass 96/96 assertions at threshold 1.0
  Rollback: remove the Hermes Gauntlet translation and ignored GREEN response directory
  Acceptance: every case passes on a fresh response and Hermes does not claim unavailable slash commands
  Risk: medium

### Phase 4 gate

- [x] **G4.1** — Full Planning eval set is genuinely GREEN
  CHECK: `python3 skills/skill-improve/scripts/run_evals.py --skill-path skills/planning --evals-path skills/planning/evals/evals.json --response-dir .graph-powers/cache/gauntlet-evals/green --threshold 1.0`
  EXPECT: `/Cases:\s+24\s+\|\s+Passed:\s+24\s+\|\s+Failed:\s+0/`
  EVIDENCE: Cases: 24 | Passed: 24 | Failed: 0; every case reached threshold 1.0; exit 0

## Phase 5 — Human surface and release metadata  [SEQUENTIAL]

- [x] **T5.1** — Update current inventory, usage, changelog and provenance
  Owns: README.md, NOTICE, CHANGELOG.md
  Needs: T4.1 (reads: proven public behavior and client limitations)
  Agent: graph-powers:debugger · Skill: skill-improve · Effort: focused
  Basis: `README.md:110`, confidence 5
  Parallel: no; documentation follows the proven behavior
  Mode: write
  TDD: not-applicable (human documentation and attribution only)
  Steps:
    1. Document the opt-in command and correct current command inventory to twelve.
    2. Record the informed MIT provenance without copying external prompt text.
  CHECK: `python3 .github/check_wiring.py`
  EXPECT: `0 unresolved`
  EVIDENCE: file-reference check exit 0; README reports 12 commands; NOTICE attributes both MIT sources without redistributed prompt text
  Rollback: revert the bounded README, NOTICE and CHANGELOG additions
  Acceptance: users can discover the exact syntax and limits, current counts are correct, and provenance is explicit
  Risk: low

- [x] **T5.2** — Synchronize version 1.15.0 across all manifests
  Owns: package.json, .claude-plugin/plugin.json, .codex-plugin/plugin.json, .cursor-plugin/plugin.json, .grok-plugin/plugin.json, plugin.yaml
  Needs: T5.1 (reads: finalized public release notes)
  Agent: graph-powers:debugger · Skill: skill-improve · Effort: mechanical
  Basis: `package.json:3`, confidence 5
  Parallel: no; all version declarations are one atomic release identity
  Mode: write
  TDD: not-applicable (synchronized declarative metadata)
  Steps:
    1. Change only the six canonical version fields from 1.14.0 to 1.15.0.
    2. Run the version and manifest checks.
  CHECK: `python3 .github/check_version_bump.py`
  EXPECT: 7 shipped file(s) changed
  EVIDENCE: six manifest surfaces report 1.15.0; version gate exit 0: 7 shipped file(s) changed, version 1.13.2 -> 1.15.0
  Rollback: restore all six version fields to 1.14.0 together
  Acceptance: every version surface reports 1.15.0 and the bump policy passes
  Risk: low

### Phase 5 gate

- [x] **G5.1** — Documentation and release metadata agree
  CHECK: `python3 .github/check_version_bump.py`
  EXPECT: 7 shipped file(s) changed
  EVIDENCE: file references exit 0; version gate exit 0; Claude manifest validation passed

## Phase 6 — Full proof and review  [SEQUENTIAL]

Phase 6 is controller-owned verification, not a writer task. The controller runs the complete gate
matrix, client dry-runs and independent report-only audits after T5.2, then records G6.1. This keeps
the read-only verifier out of Phase C's Gauntlet writer lanes.

### Phase 6 gate

- [x] **G6.1** — The public capability is ready for an explicit human commit decision
  CHECK: `python3 .github/check_wiring.py`
  EXPECT: 0 unresolved
  EVIDENCE: 22/22 official gates plus Cursor and Grok checks exit 0; Codex/Cursor/Grok dry-runs exit 0; wiring 452/0; no stage, commit, push, release or deploy

## Verification

- Run every command listed in the mission's implementation gates without substituting tools.
- Run `python3 .github/check_cursor.py` and `python3 .github/check_grok.py`.
- Use concrete safe temporary directories for Codex, Cursor and Grok dry-runs; do not install.
- Run Planning Mode A validation with genuine responses, never fabricated regex fixtures.
- End with an independent diff review and report unavailable tools as NOT RUN or BLOCKED.
- Post-success: `/evolve auto` is part of future Gauntlet executions, not a mutation performed while implementing this command.

## Rollback

Remove the new adapter and profile, revert only the Gauntlet-specific Planning/Hermes/documentation
edits, remove the eleven eval objects, revert the SDD tier parser/tests and restore all six manifests
to 1.14.0. Ignored response and validation caches may be removed separately. Do not reset the worktree,
touch user data or rewrite Git history.

## Out of scope

- No new agent, skill, workflow, schema field, state machine, ledger, dependency or alias.
- No copied generated client artifact and no product/game-specific behavior.
- No installation, staging, commit, push, PR, release, publication or deploy.
- No promise of perfection and no increase to any budget or loop cap.

## Not yet specified

No fog: the approved architecture, public syntax, caps, pressure cases, client behavior and stop
conditions are closed. A discovery that requires widening these boundaries needs new approval.
