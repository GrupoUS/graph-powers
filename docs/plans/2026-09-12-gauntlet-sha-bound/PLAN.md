# Gauntlet SHA-bound review — implementation plan

**Date:** 2026-09-12 · **Branch:** `main` · **Baseline:** 4c058cb
**Tier:** L4 · **Risk surface:** none
**Design authority:** [spec.md](spec.md), GitHub issue #22 (Stage 1 slices) and the user's explicit
Gauntlet implementation request of 2026-09-12. Evaluator Mode 1 is pending; no writer or lease
before PASS.

## Destination

`sdd.py review-bind` records the Mode 1 verdict with the PLAN SHA-256 and appends the review log;
`review-check` returns exit 0 only for an `APPROVED` bind whose bytes are unchanged and exit 4
`STALE` otherwise; `acquire --profile gauntlet` refuses a stale or unreviewed plan before creating a
lease; `/gauntlet --review-only` stops after the bind and `--dry-run` names distinct `builder` and
`inspector` roles; three critical negative evals encode those invariants; NOTICE, CHANGELOG and the
six version owners move to 1.20.6 with regenerated Hermes bytes. Everything stays reviewed and
unstaged.

## Issue Triage (upstream mandate)

| Req | Scope | Verdict | Evidence | Grade | Rationale |
|---|---|---|---|---|---|
| R1 | `--dry-run` declares distinct builder/inspector ids | KEEP | commands/gauntlet.md:12,24; gauntlet-loop.md:30 | 5 | Contract text only; no runtime state |
| R2 | APPROVED binds PLAN SHA-256; change → `review-check` exit 4 `STALE` | KEEP | sdd.py:548 (`_write_json_ledger`), sdd.py:585 (`_ledger_lock`) | 5 | Reuse ledger lock and atomic writers |
| R3 | `--review-only` calls neither `acquire` nor Phase C | KEEP | commands/gauntlet.md:27; phase-c-executing-plans.md:34 | 5 | Contract text plus eval |
| R4 | Controller edits after inspection invalidate it | SIMPLIFY | gauntlet-loop.md § Final close | 4 | Contract rule and eval; no new state machine |
| R5 | L1–L2 stay NOT ELIGIBLE; three new critical evals | KEEP | skills/planning/evals/evals.json (`gauntlet-neg-l1-l2`) | 5 | Extend the existing eval file |
| R6 | NOTICE, CHANGELOG, six manifests > tip, regenerated projections | KEEP | NOTICE § MIT synthesis; .github/check_version_bump.py:27 | 4 | Release lane waits for the parallel `issue-improve` session to release these paths |

KEEP 5 · SIMPLIFY 1 · CUT 0 · DEFER 0.

## Reuse ledger

| # | Need | Existing asset (`path:line`) | Verdict | Why extending fails (NEW only) |
|---|---|---|---|---|
| N1 / R2 | Atomic JSON bind under a lock | skills/planning/scripts/sdd.py:548, :585 | REUSE | — |
| N2 / R2 | Symlink-refusing text writer | skills/planning/scripts/sdd.py:299 | EXTEND | — (append mode is new) |
| N3 / R2 | Bounded-state exit contract | skills/planning/scripts/sdd.py:386 (`BOUNDED_EXIT`) | REUSE | — |
| N4 / R2 | Plan workspace location | skills/planning/scripts/sdd.py:351 | REUSE | — |
| N5 / R3 | Gauntlet admission before lease | skills/planning/scripts/sdd.py:1511 (`acquire`) | EXTEND | — |
| N6 / R1,R3 | Command and loop contract | commands/gauntlet.md; skills/planning/references/gauntlet-loop.md | EXTEND | — |
| N7 / R5 | Eval cases with parser controls | skills/planning/evals/evals.json (`gauntlet-neg-invalid-plan-path-not-objective`) | EXTEND | — |
| N8 / R6 | Hermes mirror of sdd.py and references | hermes/package_builder.py:44; hermes/install.mjs | REUSE | — |

## Regression watchlist

| # | Existing behaviour that must still work | How to prove it | Phase |
|---|---|---|---|
| W1 | Default-profile `acquire`, dispatch, consult and status contracts | `python3 skills/planning/scripts/test_sdd.py` | 1 |
| W2 | Public routes and cited sections resolve | `python3 .github/check_wiring.py` | 1 |
| W3 | Command floor and ceiling stay within the adjusted budget | `python3 .github/check_context_budget.py` | 1 |
| W4 | No POSIX-only construct in an executed command | `python3 .github/check_portability.py` | 1 |
| W5 | Hermes package bytes follow the canonical sources | `bun hermes/install.mjs --check` | 1 |
| W6 | Hook guardrails unchanged | `python3 hooks/test_hooks.py` | 1 |

## Execution graph

One phase, one lane package, one wave: T1.1 → T1.2 → T1.3 → T1.4 run in order inside a single
`graph-powers:debugger` package with pairwise-disjoint `Owns` and a separate CHECK per task. Edge
T1.1 → T1.4 carries the final `sdd.py` bytes the Hermes mirror copies; T1.2 → T1.4 the reference
bytes it copies plus the measured budget overflow the cap adjustment covers; T1.3 → T1.4 the eval
bytes it copies. T1.1's docs contract test reads T1.2's files, so the package runs T1.2 before the
whole-file test run that closes T1.1's step 4. A second builder lane would buy no wall-clock worth
its two dispatches (see the budget below).

Configured limits: maxTasksPerPlan 12, maxParallelWave 3, maxSpawnsPerWorkflow 8,
maxRoundsPerAgent 4, maxRepatch 2. The Phase B Mode 1 evaluator counts against the workflow cap
but precedes the lease, so the ledger cannot record it: every reservation of this run passes
`--max-spawns 7`, which is the configured 8 minus that pre-lease review counted by hand — a
reduction inside the configured limit, not a replacement of it, and the same value on every call
because the ledger refuses a changed cap mid-run. Phase C then reserves one writer, one wave
evaluator and one final evaluator — three of seven; the `/verify loop` fresh evaluator is a fourth.
One correction round costs two (builder plus correction re-review), so exactly one round fits the
workflow cap; a second wave failure stops at the cap with NEEDS-WORK and routes to `/debug
recover`. The evaluator role also has `maxRoundsPerAgent` 4 inside `spawnWindowMinutes`: Mode 1,
wave, final and verify-loop reviews use all four, so a correction re-review consumes the round
reserved for `/verify loop`, which then stops as NEEDS-WORK under the non-convergence rule instead
of spending a fifth round.

## Requirement coverage

| Need | Surface | Applicable evidence | Task(s) and Owns | Producer → consumer payload/path | Acceptance evidence |
|---|---|---|---|---|---|
| N1–N5 / R2 | backend | sdd.py:548, :585, :1511 | T1.1: skills/planning/scripts/sdd.py, test_sdd.py | `review-bind` JSON + LOG line → `review-check` / `acquire --profile gauntlet` exit 0/4 | T1.1 CHECK; G1.1 |
| N6 / R1, R3, R4 | frontend/client | commands/gauntlet.md:12,24,27; gauntlet-loop.md:30,83 | T1.2: commands/gauntlet.md, three planning references, 007-path-conventions.md, README.md | command flags → loop contract → Phase B/C hooks naming the same CLI | G1.1 docs test; G1.2 |
| N7 / R5 | frontend/client | evals.json `gauntlet-neg-l1-l2` | T1.3: skills/planning/evals/evals.json | eval prompts → assertions matching the contract vocabulary | T1.3 CHECK; parser-control run recorded in EVIDENCE |
| N8 / R6 | frontend/client | hermes/package_builder.py:44 | T1.4: NOTICE, CHANGELOG.md, six manifests, hermes/package, .github/check_context_budget.py | canonical bytes → generated package and PROVENANCE | G1.5, G1.6, G1.8 |
| all | database N/A | .graph-powers/config.json declares no database; AGENTS.md ownership map is a harness | — | no query, schema or migration | owned diff review |

## Dispatch matrix

| Task | Agent | Skill | Owns | Needs |
|---|---|---|---|---|
| T1.1 | graph-powers:debugger | none | sdd.py, test_sdd.py | none |
| T1.2 | graph-powers:debugger | none | command, three references, 007 row, README sentence | none |
| T1.3 | graph-powers:debugger | none | evals.json | none |
| T1.4 | graph-powers:debugger | none | NOTICE, CHANGELOG, six manifests, hermes/package, budget caps | T1.1, T1.2, T1.3 |

Inspector for every review is `graph-powers:evaluator` (D1); builders are `graph-powers:debugger`.

## Preconditions

The write lease is one global file (`hooks/graph_guardrails.py` G4; `sdd.py acquire` exits 2 on a
foreign lease and `dispatch reserve` refuses reservations without the plan's own lease). Today it
belongs to `docs/plans/2026-09-11-issue-improve/PLAN.md`, held by a parallel session. The controller
runs `acquire --profile gauntlet` for this plan only after that session releases it; until then no
writer, reservation or workspace write happens for any phase. The parallel session also owns
T1.4's paths until that release; T1.4 adds above its 1.20.5 entries and never overwrites them.

## Phase 1 — Runtime invariants, contract and release [SEQUENTIAL]

- [x] **T1.1** — Add `review-bind` and `review-check` to sdd.py and gate Gauntlet acquire on them (R2, R3)
  Owns: skills/planning/scripts/sdd.py, skills/planning/scripts/test_sdd.py
  Needs: none
  Acceptance: `review-bind` writes plan-review.json and appends one PLAN-REVIEW-LOG.md line per round, refuses inspector == builder and a symlinked plan with exit 2; `review-check` exits 0 only for an unchanged APPROVED bind and exits 4 with JSON status STALE, REVISION_REQUIRED or UNREVIEWED otherwise; `acquire --profile gauntlet` runs the full `review-check` before any lease attempt when no lease or a foreign lease exists and exits 4 without creating one on any non-zero result; a resume (own lease with the same plan and path set) skips the raw check but requires the bind's `scopeSha256` to equal the current scope hash, exiting 4 STALE otherwise with the lease untouched; the default profile is unchanged.
  Agent: graph-powers:debugger · Skill: none · Effort: design
  CHECK: `python3 skills/planning/scripts/test_sdd.py -k review_bind -k review_check -k refuses_unreviewed`
  EXPECT: `OK`
  EVIDENCE: RED: `python3 skills/planning/scripts/test_sdd.py -k review_bind -k review_check -k refuses_unreviewed` before implementation → FAILED (failures=3), `invalid choice: 'review-bind'`, `AssertionError: 0 != 4`; GREEN: same command → Ran 3 tests, OK; whole file Ran 59 tests, OK; wave evaluator compliance/quality PASS at snapshot 0c8bf33; correction attempt 2 (independent inspection I1, M3, M4, M5: log append now precedes the JSON bind, case-insensitive EVIDENCE, whitespace-free plan path, raw-vs-scope test) → focused CHECK Ran 4 tests OK, whole file Ran 60 tests OK; correction round 2 (`/verify loop` V1: scope hash field-scoped through the structured parser — only task/gate EVIDENCE fields and header checkboxes exempt; RED FAILED(3) → GREEN) → focused CHECK Ran 5 tests OK, whole file Ran 61 tests OK; correction round 3 (second `/verify loop` W1 P1: Steps lines shaped like EVIDENCE were exempt — classification now mirrors `_parse_task`/`_parse_gate`, first evidence field per block only; W2: wrapped evidence continuation lines are not drift; RED FAILED(4) → GREEN) → the plan's focused CHECK Ran 5 tests OK (the packet's wider `-k scope` filter Ran 7 tests OK), whole file Ran 61 tests OK; `/debug recover` after the third `/verify loop` (X1 P1: scope hash now splits lines exactly as the validator's `str.splitlines`, reconstructing with `keepends=True`; X2 comment states the real carve-out; X3 `=` refused in the plan path; RED FAILED(4) → GREEN) → whole file Ran 62 tests OK.
  TDD: required
  Steps:
    1. Read spec.md § Contract, sdd.py lines 237-390 (paths, `_secure_directory`, `_write_text_no_symlink`, `workspace`), 548-613 (`_write_json_ledger`, `_ledger_lock`), 1511-1533 (`acquire`) and 1636-1748 (`main`); read test_sdd.py lines 1-120 (helpers) and 827-946 (gauntlet acquire, symlink and concurrent lease tests).
    2. RED: add `test_review_bind_records_sha_and_review_check_detects_stale` (bind APPROVED → JSON fields, LOG line, check exit 0; edit plan → exit 4 STALE; bind round 2 → LOG has two lines with the first unchanged, check exit 0), `test_review_bind_rejects_self_inspection_symlink_and_revision_required` (same id, case-insensitive → exit 2; inspector `main` → exit 2; symlinked plan → exit 2, skip when symlinks unavailable; REVISION_REQUIRED → check exit 4 with that status) and `test_gauntlet_acquire_refuses_unreviewed_or_stale_plan_before_lease` (no bind → exit 4 UNREVIEWED, no lease; bind → exit 0 lease; a second gauntlet acquire after replacing the plan's `EVIDENCE: pending` and checking a box resumes the matching lease with exit 0; a resume after editing a task's Acceptance exits 4 STALE and keeps the lease untouched; release; edit → exit 4 STALE, no lease; with a foreign lease on disk and no bind → exit 4 UNREVIEWED before any conflict; default profile still exit 0 without a bind). Assert read-only behaviour: after `review-check` with no bind the workspace directory does not exist, and after bind and check no `plan-review.lock` remains. Also add `test_gauntlet_contract_docs_bind_stop_and_distinct_roles` asserting commands/gauntlet.md and gauntlet-loop.md contain `--review-only`, `review-bind`, `review-check`, `STALE` and an inspector/builder distinction; it may fail until T1.2 lands and is excluded from the focused CHECK. Run the focused CHECK and confirm the new tests fail for absent behaviour.
    3. GREEN: implement `review_bind(plan, verdict, inspector, builder, model_requested, model_observed)` and `review_check(plan)` per spec.md: `sha256` over raw bytes opened with O_NOFOLLOW after `plan.is_symlink()` refusal, plus `scopeSha256` over the same bytes with every `EVIDENCE:` field line removed and every `[x]`/`[X]` checkbox normalized to `[ ]`; `_relative_plan` for the worktree check; `IDENTITY` regex for both ids, refusing inspector equal to builder (case-insensitive) or `main`; verdict choices APPROVED/REVISION_REQUIRED; JSON written with `_write_json_ledger` under `_ledger_lock(directory, "plan-review", "plan review")`; LOG appended through a new `_append_text_no_symlink` using O_WRONLY|O_CREAT|O_APPEND|O_NOFOLLOW; `review_check` uses `_existing_secure_directory` and never creates state; return `(output, code)` with BOUNDED_EXIT for non-approved states. In `acquire`, after validation and only for profile gauntlet: when the existing lease has this plan and this exact path set, it is a resume — require the bind's `scopeSha256` to equal the current scope hash (controller EVIDENCE and checkbox writes are the only legitimate drift) and exit 4 STALE otherwise, lease untouched; when no lease or a foreign lease exists, require the full `review-check` (raw sha) to exit 0 before attempting the lease, printing its JSON and returning 4 without creating anything when it does not. Register both subcommands in argparse and update the module docstring's subcommand list and exit-code paragraph.
    4. Re-run the focused CHECK until GREEN, then the whole file: every pre-existing test stays green and no default-profile behaviour changes; the only test allowed to stay red is `test_gauntlet_contract_docs_bind_stop_and_distinct_roles` until T1.2 lands, and G1.1 closes it.

- [x] **T1.2** — Extend the command and planning contracts with review-only, SHA binding and role declaration (R1, R3, R4)
  Owns: commands/gauntlet.md, skills/planning/references/gauntlet-loop.md, skills/planning/references/phase-b-writing-plans.md, skills/planning/references/phase-c-executing-plans.md, references/shared/007-path-conventions.md, README.md
  Needs: none
  Acceptance: commands/gauntlet.md accepts `--review-only`, names the `review-bind`/`review-check` commands, states that dry-run declares distinct `builder` and `inspector` ids, that review-only stops before acquire and Phase C, and that exit 4 STALE returns to Phase B without a lease; gauntlet-loop.md, phase-b Step 7 and phase-c Step 1 carry the same rule once each; 007-path-conventions.md lists the two workspace artefacts and README.md § Gauntlet execution states review-only in one sentence; the frontmatter description is byte-identical to before; wiring and file-reference gates stay at zero unresolved.
  Agent: graph-powers:debugger · Skill: none · Effort: design
  CHECK: `python3 .github/check_wiring.py`
  EXPECT: `, 0 unresolved;`
  EVIDENCE: `python3 .github/check_wiring.py` → 527 then 526 routing references checked, 0 unresolved; 12 agents checked, 0 that would not register; docs contract test green; wave evaluator PASS with one Minor (duplicate exit rule, removed); correction attempt 2 (I2 command block now validate + review-check only with the bind owned by Phase B Step 7 or --review-only, I3 single resume rule in § Review binding, M1, M2) → wiring 526/0, budget within (floor 586 B headroom); correction round 2 (V2 single resume rule, V3 objective dry-run builder wording, V4 field-scoped prose) → wiring 527/0, ceiling headroom 424 B.
  TDD: not-applicable (markdown contract; proven by G1.1 docs test and wiring gate)
  Steps:
    1. Read spec.md § Contract, commands/gauntlet.md, gauntlet-loop.md, phase-b-writing-plans.md § Step 7-9 and phase-c-executing-plans.md § Step 1 and § Step 4. Do not change the command frontmatter description (the generated Codex native skill mirrors it).
    2. commands/gauntlet.md: add `--review-only` to the accepted flags; for a plan or objective with `--review-only`, run validation and the Mode 1 review, then `python -X utf8 "${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/sdd.py" review-bind <PLAN_FILE> --verdict <APPROVED|REVISION_REQUIRED> --inspector graph-powers:evaluator --builder <writer role>` and stop without acquire, Phase C, lease or writer; dry-run reports `builder` and `inspector` as two distinct role ids and writes no bind; a non-dry run enters Phase C only when `review-check <PLAN_FILE>` exits 0, and exit 4 (`STALE`, `REVISION_REQUIRED`, `UNREVIEWED`) returns to Phase B without a lease. Keep the file within its current budget class: add at most eight lines.
    3. gauntlet-loop.md: in Activation, list `--review-only` and state that a review request never authorizes Phase C; in Entry and dry-run, require the bind to be current (`review-check` exit 0) before lease and declare the two role ids in dry-run; add a short `## Review binding` section naming plan-review.json, PLAN-REVIEW-LOG.md (append-only, one line per round, model requested vs observed, no silent fallback), the inspector default (D1) and the Codex opt-in by explicit host request; in Final close, state that the final inspector is a fresh evaluator distinct from every builder and that a controller edit after that inspection invalidates it.
    4. phase-b-writing-plans.md § Step 7: after the Mode 1 verdict of an explicit Gauntlet plan, the controller binds it with `review-bind` (PASS → APPROVED, FAIL → REVISION_REQUIRED, BLOCKED not bound) and a later plan edit requires a new round. phase-c-executing-plans.md § Step 1: Gauntlet `acquire` also refuses a stale or unreviewed bind with exit 4 and no lease, returning to Phase B.
    5. references/shared/007-path-conventions.md: add one table row after "Task-review ledger" naming `.graph-powers/logs/sdd/<plan-slug>/plan-review.json` (last round, SHA-256 bound) and `.graph-powers/logs/sdd/<plan-slug>/PLAN-REVIEW-LOG.md` (append-only, one line per round), written by `sdd.py review-bind`; the other references point to that row instead of repeating paths. README.md § Gauntlet execution: after "L1-L2 work stays on the normal local route." add one sentence: `--review-only` runs the independent plan review, binds its verdict to the plan's SHA-256 in the SDD workspace and stops before any lease or writer; builder and inspector are declared as distinct roles, and an approved plan that changes afterwards needs a new review before Phase C. Also add `--review-only` to the README usage line.
    6. Run the CHECK plus `python3 .github/check_file_references.py` and `python3 .github/check_portability.py`; run `python3 .github/check_context_budget.py` and report its floor/ceiling line as is — an overflow here is expected and is resolved by T1.4's cap adjustment, not by cutting contract text.

- [x] **T1.3** — Add the three critical negative Gauntlet evals (R5)
  Owns: skills/planning/evals/evals.json
  Needs: none
  Acceptance: evals.json parses, keeps every existing case unchanged, and adds `gauntlet-neg-review-only-no-phase-c`, `gauntlet-neg-stale-sha-no-lease` and `gauntlet-neg-builder-self-inspect`, each negative with only critical assertions and parser_controls whose positive samples pass and negative samples fail the runner at threshold 1.0.
  Agent: graph-powers:debugger · Skill: none · Effort: mechanical
  CHECK: `python3 -X utf8 -c "import json;d=json.load(open('skills/planning/evals/evals.json',encoding='utf-8'));ids=[c['id'] for c in d['evals']];print('ok' if {'gauntlet-neg-review-only-no-phase-c','gauntlet-neg-stale-sha-no-lease','gauntlet-neg-builder-self-inspect'}<=set(ids) and len(ids)==len(set(ids)) and len(ids)==46 else 'missing')"`
  EXPECT: `ok`
  EVIDENCE: CHECK one-liner → ok (46 unique ids, three new cases); parser controls via run_evals.py --threshold 1.0: 6 positives exit 0, 6 negatives exit 1; keepers byte-identical to 4c058cb; wave evaluator PASS; correction attempt 2 (I4: negations anchored to their verb, critical not_contains per case) → 12 controls plus 2 adversarial texts as expected 14/0; recover X4 (one negative control per case that only R06/T07 reject) → 16/0.
  TDD: not-applicable (JSON fixtures; proven by the runner against parser controls)
  Steps:
    1. Read spec.md § Contract and the existing cases `gauntlet-neg-dry-run`, `gauntlet-neg-approved-plan-missing-review-coverage` and `gauntlet-neg-invalid-plan-path-not-objective` in skills/planning/evals/evals.json for shape, assertion ids and parser_controls.
    2. Append the three cases after `gauntlet-pos-verify-loop-fallback`. Prompts in Portuguese like the neighbours. review-only: `/gauntlet docs/plans/example/PLAN.md --review-only`; assertions: no acquire/lease, no Phase C/writer, bind with APPROVED|REVISION_REQUIRED and LOG append, explicit STOP. stale: PLAN edited after APPROVED; assertions: `review-check` exit 4 STALE, no lease, return to Phase B, new round, and one critical assertion that a REVISION_REQUIRED bind never authorizes Phase C or a lease (`(?is)REVISION_REQUIRED.{0,120}(not|não|nunca|≠).{0,80}(APPROVED|Phase C|Fase C|lease)`) with a negative parser control claiming a prior review suffices to acquire the lease. self-inspect: the builder role asks to inspect its own diff; assertions: refuse, inspector distinct from builder, fresh read-only evaluator, controller edit after inspection invalidates it. Use `(?is)` regexes accepting Portuguese and English wording, mark every assertion `critical: true`, and give each case two positive and two negative parser_controls.
    3. Write each parser control to the scratchpad as `resp-<id>.txt` and run `python3 skills/skill-improve/scripts/run_evals.py --skill-path skills/planning --evals-path skills/planning/evals/evals.json --response-file <file> --test-case <id> --threshold 1.0`; positives must exit 0, negatives non-zero. Record the counts in the report. Then run the CHECK.

- [x] **T1.4** — Record provenance, changelog and version 1.20.6, then regenerate the Hermes package (R6)
  Owns: NOTICE, CHANGELOG.md, package.json, plugin.yaml, .claude-plugin/plugin.json, .codex-plugin/plugin.json, .cursor-plugin/plugin.json, .grok-plugin/plugin.json, hermes/package, .github/check_context_budget.py
  Needs: T1.1 (reads: final skills/planning/scripts/sdd.py bytes mirrored by the Hermes package), T1.2 (reads: final planning reference bytes mirrored by the Hermes package), T1.3 (reads: final skills/planning/evals/evals.json bytes mirrored by the Hermes package)
  Acceptance: NOTICE names chaseai-yt/claudex-loop (MIT) as a source-informed synthesis for gauntlet-loop.md, commands/gauntlet.md and the sdd.py review commands with no upstream file redistributed; CHANGELOG.md gains a 1.20.6 entry above 1.20.5; the six version owners read 1.20.6; `bun hermes/install.mjs --package-only` regenerates hermes/package so `--check` reports the package current at 1.20.6.
  Agent: graph-powers:debugger · Skill: none · Effort: mechanical
  CHECK: `bun hermes/install.mjs --check`
  EXPECT: `source manifest and package are current`
  EVIDENCE: `bun hermes/install.mjs --check` → hermes: 39 registrations, source manifest and package are current; runtime UNVERIFIED; six manifests 1.20.6; check_version_bump → version 1.20.3 -> 1.20.6; budget within 51,500/208,000 (live measurement after every nit and correction round 2: floor 50,938 B, ceiling 207,576 B, i.e. 562 B and 424 B of headroom; the cap comment cites the same numbers and justifies the editing margin); wave evaluator PASS with one Minor (cap comment); correction attempt 2 (M6: NOTICE lists phase-b, phase-c and 007) → hermes --check current, hermes package tests STATIC PASS.
  TDD: not-applicable (metadata and generated output; proven by the Hermes gates)
  Steps:
    1. Ownership note: these paths were released by the parallel `issue-improve` session (see Preconditions); its 1.20.5 CHANGELOG entry, NOTICE block and generated files stay as they are, and every addition goes above or beside them.
    2. NOTICE: add one block under "MIT — source-informed synthesis, not verbatim redistribution" for https://github.com/chaseai-yt/claudex-loop (MIT, read 2026-09-12): SHA-bound approval, review-only stop, inspector distinct from builder and the append-only review log were transferred as invariants into the existing Gauntlet profile; no prompt, script or file was copied. CHANGELOG.md: `## 1.20.6 — Gauntlet review bound to the plan bytes` with four to six lines in the existing voice.
    3. In .github/check_context_budget.py raise FLOOR_CEILING and CEILING_CEILING by the smallest round amounts that cover the measured totals, with a comment line in the existing voice naming 1.20.6 and the bytes bought by the review-only contract; then run `python3 .github/check_context_budget.py` and confirm `within budget`.
    4. Set version 1.20.6 in package.json, plugin.yaml, .claude-plugin/plugin.json, .codex-plugin/plugin.json, .cursor-plugin/plugin.json and .grok-plugin/plugin.json without other edits. Run `bun hermes/install.mjs --package-only`, then the CHECK, `python3 -X utf8 .github/test_hermes_package.py`, `python3 -X utf8 .github/test_hermes.py --static` and `python3 .github/check_version_bump.py`; report each output line.

### Phase 1 gate

- [x] **G1.1** — Structured planning contract, including the new review commands and the docs test
  CHECK: `python3 skills/planning/scripts/test_sdd.py`
  EXPECT: `OK`
  EVIDENCE: `python3 skills/planning/scripts/test_sdd.py` → Ran 62 tests, OK (after the recover fix).
- [x] **G1.2** — Routes and cited sections resolve
  CHECK: `python3 .github/check_wiring.py`
  EXPECT: `, 0 unresolved;`
  EVIDENCE: `python3 .github/check_wiring.py` → 527 routing references checked, 0 unresolved; 12 agents checked, 0 that would not register.
- [x] **G1.3** — Live file references resolve
  CHECK: `python3 -X utf8 -c "import subprocess,sys;r=subprocess.run([sys.executable,'.github/check_file_references.py']);print('refs-ok' if r.returncode==0 else 'refs-fail')"`
  EXPECT: `refs-ok`
  EVIDENCE: wrapper printed refs-ok (check_file_references.py exit 0).
- [x] **G1.4** — Executed commands stay portable
  CHECK: `python3 .github/check_portability.py`
  EXPECT: `0 portability problem(s)`
  EVIDENCE: `python3 .github/check_portability.py` → 0 portability problem(s).
- [x] **G1.5** — Hermes package regression tests
  CHECK: `python3 -X utf8 .github/test_hermes_package.py`
  EXPECT: `OK`
  EVIDENCE: `python3 -X utf8 .github/test_hermes_package.py` → Ran 20 tests, OK, Hermes package: STATIC PASS (after regeneration at 1.20.6).
- [x] **G1.6** — Version bump reaches installed machines
  CHECK: `python3 .github/check_version_bump.py`
  EXPECT: `-> 1.20.6`
  EVIDENCE: `python3 .github/check_version_bump.py` → 17 shipped file(s) changed, version 1.20.3 -> 1.20.6.
- [x] **G1.7** — Declared test gate (hooks) at the final boundary
  CHECK: `python3 hooks/test_hooks.py`
  EXPECT: `OK`
  EVIDENCE: `python3 hooks/test_hooks.py` → EVERY GUARANTEE HELD.
- [x] **G1.8** — Command floor and ceiling within the adjusted budget
  CHECK: `python3 .github/check_context_budget.py`
  EXPECT: `within budget`
  EVIDENCE: `python3 .github/check_context_budget.py` → within budget — floor 562 B and ceiling 424 B of headroom (final tree: 50,938 B / 207,576 B).

## Verification

- Gates: `tooling.commands.test` = `python3 hooks/test_hooks.py` (G1.7); typeCheck, lint and build are NOT DECLARED.
- `.claude/rules/verify-supplements.md` inventory: gates 4, 8, 9, 15, 17, 18, 19, 25 are the ones this diff can move; run them at close.
- No UI changed: no staging E2E.
- Post-success: `/evolve auto`.

## Rollback

Revert the working-tree edits to the owned files (nothing is committed); for T1.4 restore NOTICE,
CHANGELOG.md, the six manifests and the budget caps, then rerun `bun hermes/install.mjs --package-only`.

## Out of scope

| Row | Reopen trigger |
|---|---|
| Codex native, Cursor and Grok projections | only if a projected description changes (kept byte-identical here) |
| skills/planning/SKILL.md, Codex/Cursor/Grok generated projections | only if a projected description or the SKILL routing sentence changes |
| Second loop, vendored Claudex, `/claudex`, model pins, route | anti-goals of #21/#22 |
| Git commit, push, issue closure | separate user-approved actions after review |

## Not yet specified

No fog: the CLI names, exit codes, file names and role defaults are closed in spec.md.
