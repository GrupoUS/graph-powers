# Optional Graft context — implementation plan

**Date:** 2026-09-08 · **Branch:** main · **Baseline:** b24f390a24c9229d24c17924e165ba6fd1512928
**Tier:** L5 · **Risk surface:** public configuration, instructions and client projections
**Design authority:** [spec.md](spec.md); Stage 1 reviewed in conversation and execution approved by the user.

## Destination

Graph Powers selects an optional project graph backend, retrieves bounded source-grounded context,
revalidates evidence and preserves existing documents/handoffs. Legacy behavior and textual fallback
remain usable. Full Graft integration is not complete until separately authorized runtime qualification passes.

## Reuse ledger

| Need | Existing asset | Decision |
|---|---|---|
| Project selection | schema/config.schema.json; hooks/_config.py | EXTEND, project-only |
| Graph queries and limitations | references/shared/115-code-graph.md | EXTEND, sole cookbook |
| Review consumers | references/shared/125-change-set.md; commands/verify.md; commands/pr-review.md | EXTEND |
| Minimal context | commands/prime.md | EXTEND |
| Domain staging / instruction hierarchy | references/shared/045-context-staging.md; skills/intent-layer/SKILL.md | REUSE unchanged |
| Reuse and impact | skills/planning/references/step-0-inventory.md | EXTEND |
| Agent / session continuity | agent-handoff-contracts.md; commands/evolve.md | EXTEND existing envelopes |
| Session / diagnosis | hooks/session_context.py; commands/setup.md; AGENT_SETUP.md | EXTEND |
| Evaluation and generation | existing eval runner, hooks fixtures and client generators | REUSE |

No new skill, graph wrapper, registry, scheduler, watcher or dependency is required.

## Regression watchlist

| Existing behavior | Proof | Phase |
|---|---|---|
| Absent/malformed config is fail-open and retains legacy selection | hooks/test_hooks.py | 1 |
| Project B cannot inherit project A or global graph selection | public loader A-B-A cases | 1 |
| Review commands never silently select a second backend | instruction review plus graph scenario probes | 1 |
| Local/document prime does not scan the graph | P-local and P-doc | 2 |
| Zero edges never proves missing consumers/tests | tagged planning evals | 2 |
| startup/resume/compact and first-line tags remain compatible | session-context-lifecycle focus | 2 |
| Existing client resources and hook capabilities remain intact | native, Cursor, Grok and Hermes gates | 3 |
| Missing Graft does not block ordinary work | loader/hook tests and S-missing | 3 |

## Execution graph

All production edits are sequential: T1.1 → T1.2 → T2.1 → T2.2 → T2.3 → T2.4 → T3.1.
T3.2 is operational qualification and remains BLOCKED without separate installation/activation authorization.
T3.3 may prepare reviewable metadata and run existing gates after T3.1 while preserving that limitation.
It does not close T3.2 or claim a qualified integration.

## Dispatch matrix

One bounded writer owns the production paths; the parent owns this plan, captures, validation and
consolidation. Instruction calibration uses separate baseline/candidate read-only agents. Independent
review remains separate. No child creates children.

| Tasks | Role | Skills |
|---|---|---|
| T1.1–T3.1 | graph-powers:debugger | planning/TDD, skill-improve, senior-prompt-engineer for handoff |
| T3.2 | graph-powers:verification | qualification only after separate authorization |
| T3.3 | graph-powers:debugger | metadata and source-derived projections |
| Calibration / review | graph-powers:explorer / graph-powers:evaluator | read-only |

## Phase 1 — Provider contract [SEQUENTIAL]

- [x] **T1.1** — Resolve the project-only graph provider
  Owns: schema/config.schema.json, hooks/_config.py, hooks/test_hooks.py
  Needs: none
  Acceptance: Missing or invalid config retains code-review-graph; only explicit project graft enables Graft; none stays textual; global selection cannot leak.
  Agent: graph-powers:debugger · Skill: planning · Effort: design
  TDD: required
  CHECK: python3 hooks/test_hooks.py
  EXPECT: EVERY GUARANTEE HELD
  EVIDENCE: PASS: public loader RED exit 1 (19 expected failures), GREEN exit 0; checks/t1.1-red.log and t1.1-green.log; final evaluator T1.1 PASS.
  Steps:
    1. Add absent, legacy, graft, none, malformed shape/enum, global-ignore and A-B-A tests; observe RED at the public load seam. Implement the minimum enum normalization without subprocesses, I/O beyond existing reads or dependencies; observe GREEN.

- [x] **T1.2** — Extend the single graph authority and its review consumers
  Owns: references/shared/115-code-graph.md, references/shared/125-change-set.md, references/shared/000-config-loader.md, references/shared-context.md, commands/verify.md, commands/pr-review.md
  Needs: T1.1 (reads: normalized codeGraph.provider)
  Acceptance: All consumers resolve one provider; unsupported or stale graph evidence falls back to text, never to another backend.
  Agent: graph-powers:debugger · Skill: planning · Effort: design
  TDD: not-applicable (instruction contract)
  CHECK: python3 .github/check_file_references.py
  EXPECT: exit 0
  EVIDENCE: PASS: canonical provider/tool/effects review; file references exit 0 and final evaluator T1.2 PASS; post-correction identifiers match the six pinned MCP names.
  Steps:
    1. Keep the legacy cookbook and HARD limits. Add the source-qualified Graft operations, bounded recovery, effects and freshness rules. Replace provider-specific recipes in 125/verify/pr-review with capability-aware references. Pass bounded evidence from a capable caller; do not extend explorer tools.

### Phase 1 gate

- [x] **G1.1** — Verify the phase boundary
  CHECK: python3 hooks/test_hooks.py
  EXPECT: EVERY GUARANTEE HELD
  EVIDENCE: PASS: hooks/test_hooks.py exit 0, EVERY GUARANTEE HELD; final-gates/02.log and source review.

## Phase 2 — Context and handoff [SEQUENTIAL]

- [x] **T2.1** — Keep prime retrieval task-bound
  Owns: commands/prime.md
  Needs: T1.2 (reads: canonical graph selection and effects contract)
  Acceptance: Prime answers only a concrete context-loading need, preserves its stop rules and does not preload graph or documents.
  Agent: graph-powers:debugger · Skill: planning · Effort: design
  TDD: not-applicable (instruction contract)
  CHECK: python3 .github/check_context_budget.py
  EXPECT: within budget
  EVIDENCE: PASS: corrected current prime requires actual target/short-chain reads; budget exit 0; final independent checkout-only replay confirms P-local/P-struct. Model recapture remains MIXED SOURCE, not controlled A/B.
  Steps:
    1. Use P-local, P-struct and P-doc paired instruction probes. Load 115 conditionally. Reuse 045 and intent-layer unchanged. Preserve the 120-word output and four-file stage reassessment.

- [x] **T2.2** — Carry current structural evidence into the reuse inventory
  Owns: skills/planning/references/step-0-inventory.md, skills/planning/references/wayfinding.md, skills/planning/evals/evals.json
  Needs: T2.1 (reads: bounded context loading and canonical graph contract)
  Acceptance: The four cases establish reuse, dynamic consumer inclusion, test discovery despite zero edges and invalidation of stale evidence.
  Agent: graph-powers:debugger · Skill: planning · Effort: design
  TDD: required
  CHECK: python3 skills/skill-improve/scripts/run_evals.py --skill-path skills/planning --evals-path skills/planning/evals/evals.json --response-dir .claude/audit/graft-context/candidate --case-tag graft-context --threshold 1.0
  EXPECT: PASSED: every case reached the threshold
  EVIDENCE: PASS: observed RED baseline-b24 exit 1 (GC10), observed GREEN candidate exit 0 with 4/4 at threshold 1.0; nine matcher controls held; checks/correction-candidate.log and correction-controls.log; final evaluator PASS.
  Steps:
    1. Capture real baseline responses before any instruction edits, then add the four cases. Observe behavior RED against those responses without manufacturing failures. Make the minimum inventory/wayfinding change and observe candidate GREEN; preserve regression-positive baseline passes.

- [x] **T2.3** — Preserve reusable evidence in both existing handoffs
  Owns: skills/senior-prompt-engineer/references/agent-handoff-contracts.md, commands/evolve.md
  Needs: T2.2 (reads: scoped sources, freshness and invalidators)
  Acceptance: Subagent returns and session handoff preserve public fields while carrying identity, evidence validity and bounded next actions.
  Agent: graph-powers:debugger · Skill: planning · Effort: design
  TDD: not-applicable (handoff guidance within existing schema)
  CHECK: python3 .github/check_wiring.py
  EXPECT: exit 0
  EVIDENCE: PASS: existing envelopes preserved, same/changed-source decisions reviewed; wiring exit 0 with 277 references and 0 unresolved; final evaluator PASS.
  Steps:
    1. Use existing Artifacts/Decisions/Risks/Resume hint and State/Do not repeat sections. H-same reuses current evidence; H-dirty revalidates relevant sources even at the same SHA. Do not create a second memory.

- [x] **T2.4** — Point sessions to explicit graph choices without executing them
  Owns: hooks/session_context.py, hooks/test_hooks.py
  Needs: T2.3 (reads: canonical graph and reuse contract); T1.1 (reads: normalized provider)
  Acceptance: Explicit graft/none produces one bounded advisory pointer; legacy and invalid config preserve existing output; no backend process starts.
  Agent: graph-powers:debugger · Skill: planning · Effort: design
  TDD: required
  CHECK: python3 hooks/test_hooks.py --focus session-context-lifecycle
  EXPECT: EVERY GUARANTEE HELD
  EVIDENCE: PASS: corrected public hook RED exit 1 then focus GREEN exit 0; checks/t2.4-red-corrected.log and t2.4-green.log; final hook suite 869 PASS/0 FAIL; final evaluator PASS.
  Steps:
    1. Observe RED for pointer, startup/resume/compact, project isolation and lack of backend invocation through the public hook. Add at most one line within the existing 512-byte pointer ceiling; observe GREEN.

### Phase 2 gate

- [x] **G2.1** — Verify the phase boundary
  CHECK: python3 .github/check_context_budget.py
  EXPECT: within budget
  EVIDENCE: PASS: check_context_budget.py exit 0; floor 48780 B, ceiling 197337 B, within unchanged limits; post-correction-01.log.

## Phase 3 — Diagnosis and qualification [SEQUENTIAL]

- [x] **T3.1** — Diagnose graph readiness without starting the backend
  Owns: commands/setup.md, AGENT_SETUP.md, README.md
  Needs: T2.4 (reads: explicit provider and advisory session contract)
  Acceptance: Selection, package/runtime, MCP registration, index, freshness and policy are distinct observations; setup remains diagnostic.
  Agent: graph-powers:debugger · Skill: planning · Effort: design
  TDD: not-applicable (diagnostic instructions)
  CHECK: python3 .github/check_portability.py
  EXPECT: exit 0
  EVIDENCE: PASS: static readiness dimensions and four diagnosis decisions reviewed; portability exit 0; final evaluator T3.1 PASS. No backend invoked.
  Steps:
    1. Run instruction probes S-missing, S-present, S-runtime and S-duplicate. Inspect static files rather than launching Graft or MCP health checks. Do not invoke init, install or global changes. Document source/runtime qualification limits.

- [ ] **T3.2** — Qualify real backend behavior and local cost
  Owns: docs/plans/2026-09-08-graft-context/PLAN.md
  Needs: T3.1 (reads: readiness and policy diagnosis)
  Acceptance: A qualified, explicitly authorized fixture run demonstrates behavior and reports measured costs; absence remains an unmet acceptance criterion.
  Agent: graph-powers:verification · Skill: planning · Effort: design
  TDD: not-applicable (operational qualification)
  CHECK: python3 -c "import shutil; print('NOT RUN: no qualified Graft installation' if shutil.which('graft') is None else 'BLOCKED: qualify package, runtime and side effects before invoking')"
  EXPECT: APROVADO: real backend fixture evidence captured
  EVIDENCE: BLOCKED / NOT RUN: no qualified installed Graft or authorization for installation/activation/operational fixture effects. No operational or performance claim.
  Steps:
    1. BLOCKED before execution: no qualified Graft installation or authorization for installation/activation. No runtime claim may pass from the readiness probe. After separate authorization: qualify symbols/signatures/cross-file/dynamic references, dirty/new/removed files, project/worktree isolation, refresh failures and concurrency. Compare localized/impact/document tasks with five paired repetitions per case/backend; separate build from warm queries. Report APROVADO, SEM GANHO DEMONSTRADO or BLOQUEADO.

- [x] **T3.3** — Prepare source-derived distribution and verification
  Owns: CHANGELOG.md, NOTICE, package.json, .claude-plugin/plugin.json, .codex-plugin/plugin.json, .cursor-plugin/plugin.json, .grok-plugin/plugin.json, plugin.yaml, codex/native-command-skills/setup/SKILL.md
  Needs: T3.1 (reads: delivered diagnostic and explicit qualification limitation)
  Acceptance: Scoped working-tree changes and generated projections are consistent; runtime qualification remains visibly incomplete.
  Agent: graph-powers:debugger · Skill: planning · Effort: design
  TDD: not-applicable (metadata and generated projections)
  CHECK: git diff --check
  EXPECT: exit 0
  EVIDENCE: PASS for local source distribution only: 1.19.3 to 1.19.4, five generated projections; 27 declared/supplemental gates and seven affected rechecks exit 0; final evaluator PASS; T3.2 remains open.
  Steps:
    1. Bump 1.19.3 to 1.19.4 without dependency changes. Emit existing native/Cursor/Grok/Hermes projections locally. Run the 25 declared supplements in order plus relevant skill and Cursor/Grok gates; capture every exit. No staging, commit, push, PR or publication.

### Phase 3 gate

- [x] **G3.1** — Run the declared final gate inventory; preserve incomplete runtime acceptance
  CHECK: python3 .github/check_codex_native.py
  EXPECT: exit 0
  EVIDENCE: PASS: check_codex_native.py exit 0; all 27 existing gates passed with relevant post-correction rechecks. This gate does not close operational task T3.2.

## Verification

The canonical 25 checks are .claude/rules/verify-supplements.md, in declared order.
Also run check_cursor.py, check_grok.py and quick_validate.py for changed skill boundaries.
No package install or real user/global configuration writes. Existing test fixtures use fake homes.
Do not claim CI-only installation assertions or unavailable client/Graft runtimes passed.
check_version_bump.py compares committed ranges; also compare the working-tree versions against HEAD.
Do not run its fetch branch in this local task.

Stage 1 evidence: 19 Python hook ASTs and 160 JSON files parsed; git diff --check exit 0;
context floor 261858 B (8142 B headroom), ceiling 405450 B;
listing 10143 chars (609 headroom), both existing budget gates exit 0.
Stage 2 starting baseline: python3 hooks/test_hooks.py exit 0, EVERY GUARANTEE HELD.

The structured plan validated and its existing SDD write lease was acquired (exit 0).
During execution HEAD advanced externally from a84c5f7 to b24f390 (the lean-harness change).
No agent in this task performed a Git mutation. Preserve that committed change and its tighter
budgets. Version 1.19.3 is now the baseline; this task increments to 1.19.4.
Earlier captures remain historical only. Recalibrate the unchanged cases against the clean b24
instruction files materialized under .claude/audit/graft-context/qualified-baseline-source using
git show, so concurrent source edits cannot contaminate the baseline. Current AGENT_SETUP has
already removed the old module-import/MCP-health preflight; do not restore or edit that absent code.
The qualified b24 capture is now baseline-b24 (13 literal responses from a fresh explorer, frozen
git-show sources with digests). It already handles the documentation case and supplied-source reuse;
do not attribute those successes to this task. Setup still lacks a Graft diagnostic contract, and
the stale case does not emit the specified STALE/UNKNOWN state. Operational calls remain NOT RUN.
Historical a84 instruction captures contain 13 literal responses from one isolated read-only explorer
package, with separate case answers and source digests from HEAD. They do not measure native
triggering or backend calls. P-doc requests an unnecessary domain; all four S-setup cases report
that Graft diagnosis is outside the old command. Dynamic-consumer and zero-test-edge cases are
regression positives. context-reuse still asks for a graph freshness/status probe despite supplied
current source being sufficient; that redundant exploration is the changed behavior under test.

## Instruction probes and captures

Captures are instruction evaluations, not real backend execution or native trigger calibration.
Use the same role/model/limits in isolated baseline and candidate packages, with separate cases.
Capture baseline before editing instruction sources. Keep literal responses at
.claude/audit/graft-context/{baseline,candidate}/resp-<ID>.txt and provenance at trace-<ID>.json.
A self-reported read list is labeled as such. Unavailable native events are NOT RUN, never fabricated.

| ID | Fixed input / action | Oracle |
|---|---|---|
| P-local | prime backend: only correct load's docstring in hooks/_config.py; no implementation | bounded local rules/source; no structural query/map; under 120 words |
| P-struct | prime backend: understand config → SessionStart, no planning/implementation | bounded load → load_project_config → main; relevant source/test; textual fallback when unavailable |
| P-doc | prime auto: revise CONTRIBUTING review-section wording | relevant document authorities; no code index/query |
| H-same | evaluate evolve handoff → prime with unchanged identity, SHA and source digest | preserve existing fields/headings; validate identity and reuse discovery |
| H-dirty | same handoff/SHA but changed source digest and decisive source excerpt | invalidate dependent evidence; STALE/UNKNOWN and source/consumer revalidation |
| S-missing | setup: graft selected; no package/bin/MCP/index | distinct MISSING observations, UNKNOWN freshness, textual fallback |
| S-present | setup: synthetic 0.17.0 manifest, compatible Node, one MCP, index present, no freshness proof | report each dimension; freshness UNKNOWN; do not infer network/write compatibility |
| S-runtime | same as S-present but Node 20.0.0 and dependency engine >=22.12.0 | incompatible runtime, textual fallback, no upgrade |
| S-duplicate | same as S-present but two equivalent MCP registrations | duplicate warning; no deletion, configuration write or process start |
| context-reuse | existing normalizeName candidate in supplied source | read candidate and choose REUSE |
| context-dynamic | empty graph callers; registry string and consumer supplied | textual consumer enters watchlist |
| context-tests | graph reports zero tests; a test references symbol seven times | never infer untested; preserve discovered test |
| context-stale | dirty source and refresh failure while graph returns prior result | mark STALE/UNKNOWN; verify current source using textual fallback |

## Operational qualification

BLOCKED / NOT RUN. No installed Graft was found in PATH, inspected package locations or MCP entries.
The source snapshot 05760b07abc0e427f5af8ad378889ee402c5afc6 declares 0.17.0; the inspected npm registry
reported latest 0.16.0 and no 0.17.0. Source, package and installed runtime are distinct evidence.
The six schemas are verified at that source snapshot, not an installed package.
CLI/MCP startup may perform maintenance/config/network work; even freshness MCP calls may record telemetry.
DO_NOT_TRACK does not suppress version upkeep. Incompatible policy means textual fallback.

After separate authorization, use isolated fixtures, five paired repetitions per task/backend and
alternating order for local lookup, cross-file impact and documentation. Keep initial build separate
from warm queries; report observed time, CPU, RSS and actual usage when available, not Graft savings
estimates. Include dirty/new/removed files, dynamic consumers, separate project/worktree identity,
refresh failure and concurrent locks. No independent performance gain has been demonstrated.

## Decision

Graft optional, on-demand retrieval, documentation preserved. Keep only code-review-graph plus
the improved context principles if runtime/package/policy qualification cannot justify Graft.
Do not construct two complete architectures to choose between them.

## Source verification result

- Public loader: expected RED (19 failing guarantees) then full-suite GREEN. Lifecycle pointer:
  corrected RED then GREEN; the first RED log containing a fixture Git allowlist defect is excluded.
- All 25 supplements plus Cursor/Grok checks passed, exit 0. Logs and exact commands are in
  .claude/audit/graft-context/final-gates/results.json. After scoped corrections, affected document,
  wiring, budget, portability and placeholder gates passed again; unrelated green evidence is reused.
- Four tagged planning cases pass at threshold 1.0. The clean b24 baseline retains three positive
  cases and fails only the required STALE/UNKNOWN state. Matcher controls: four positives pass and
  five obligation-removal negatives fail. Literal model responses were never rewritten.
- Wave review required two corrections: prime must actually read the decisive source before ready;
  GC04/GC11 must accept equivalent consumer/regression and current-source/text formulations.
  Both source corrections and their gates are complete; final independent review passed for all eight source tasks.
- Initial P-local/P-struct failed. Fresh corrected outputs identify the named file and short source
  chain, but their self-reported reads include installed 1.19.2 bootstrap/staging. They are mixed-source
  decision evidence, not a clean controlled A/B capture. Preserve this limitation; native per-case
  event capture and real Graft runtime remain NOT RUN. P-doc, both handoff and four diagnosis
  decisions passed the scoped wave review.
- A mechanical final review of the Graft table restored all six verified graft_* tool identifiers
  and explicit no-implicit-installer guidance. No query or backend activation was performed.
- Source distribution is version 1.19.4, compared directly with current HEAD 1.19.3. The version
  gate's default committed-range result includes the external lean change, so it is not the only
  evidence of this working-tree bump. The five changed generated projections match their owners.

### Cost and limits

The b24 lean-harness report records a 46243-byte floor, 187494-byte ceiling and 7730-character
listing. Current measured values are 48780, 197337 and 7745 respectively, below the unchanged
50000/200000/8000 limits. This feature adds instruction bytes; no token, CPU, RSS or latency saving
is claimed. The existing estimator follows one reference level and selective routing is not proof
of actual model usage. The graph contract itself grew from 6095 to 9967 bytes, recorded with the final-source evidence. Graft comparison sample size is zero; runtime qualification remains
BLOCKED. The five-pair operational experiment in T3.2 was not run.

### Acceptance status

| Criterion | Evidence/status |
|---|---|
| Legacy/default/invalid configuration and missing backend preserve ordinary work | Public loader/hook tests PASS |
| One project-selected provider; textual fallback | Tests plus canonical consumer review PASS |
| Bounded current context, no false negative consumer/test conclusion | Four instruction cases PASS; prime capture limitation above |
| Existing documents and both handoffs remain usable | Scoped instruction review PASS |
| Hooks do not index/install/infer remotely | Public subprocess-audit and lifecycle cases PASS |
| Project selection isolation | A-B-A/global-ignore/payload tests PASS; real Graft/worktree cache isolation NOT RUN |
| Existing permissions/configuration preserved | Scoped diff and 27 existing gates PASS |
| Client capabilities | Generated/native fixture checks PASS; no live Codex/Cursor/Grok/macOS/Windows Graft flow claimed |
| Graft operational correctness and performance | BLOCKED / NOT RUN |
| Pending checks are not called passed | T3.2 remains unchecked; captures/gate limitations explicit |

## Rollback

Undo only the implementation's scoped hunks and fixture selections. Preserve unrelated work.
No real project index, user configuration or global installation is changed by this plan.
Metadata remains unstaged. Do not use broad cleanup or Git history operations.

## Out of scope

Installation, global/client configuration, real project activation, new worktrees, watcher,
deep inference, a second memory, tooling/model/autonomy changes, staging, commit, push, PR and publication.

## Not yet specified

No unresolved design decision blocks the source changes. Actual package/runtime invocation is
deliberately blocked until a separate authorized qualification; T3.2 remains unchecked.

## Final independent acceptance

Final evaluator graft_final_review: source scope PASS, compliance PASS, quality PASS; no remaining
Critical or Important findings. All 28 source hashes and changed paths match the final manifest.
Both grouped corrections are closed by independent checkout-only inspection. The local source
chain is hooks/hooks.json SessionStart → hooks/session_context.py main/load_project_config →
hooks/_config.py load → additionalContext. It and the named docstring provide sufficient context.

This is eight completed source tasks and one intentionally blocked operational task. No installed
Graft, real cache/worktree isolation, native model-use trace, CPU, RSS, latency or performance
comparison is certified. Corrected model prime captures remain mixed-source; the final inspector's
current-checkout replay proves source sufficiency, not a new controlled Luna sample.

Final Git state: main at b24f390a24c9229d24c17924e165ba6fd1512928, 28 modified tracked files plus this
plan/spec directory, all unstaged. No Git mutation, installation or publication was performed by
this implementation. Preserve the external lean-harness commit. The source run's own write lease
is released after recording this verdict; T3.2 stays available for a separately authorized run.
