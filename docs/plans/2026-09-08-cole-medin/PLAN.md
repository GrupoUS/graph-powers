# Cole Medin reliability deltas — approved implementation plan

**Date:** 2026-09-08 · **Branch:** main · **Baseline:** b24f390 plus preserved Graft working-tree changes at 1.19.4
**Tier:** L4
**Design authority:** user-approved inline T1–T6 plan in this conversation; execution explicitly approved with “Pode implementar”.

## Destination
Instruction drift is audited only against the selected change; handoffs preserve constraints,
scoped approvals and current evidence; resume/compact reaches the existing reader; persistent
dispatch accounting survives recovery; required independent review uses current snapshots and stops
at acceptance. Finish reviewed and unstaged with all applicable gates, without installation or publication.

## Reuse ledger
| Need | Existing asset | Decision |
|---|---|---|
| Rule drift | intent-layer and pr-review; shared/125 change set | EXTEND |
| Session/plan continuation | evolve, prime, loop-engineering, agent-handoff-contracts | EXTEND; preserve Graft evidence fields |
| Session event | session_context and existing SessionStart registration | EXTEND; no new hook |
| Bounds/models | shared/020, shared/070, execution floor, guardrails and SDD | REUSE; clarify 070 only |
| Evidence/independence | shared/015, Phase C, Evaluator | REUSE; connect current-snapshot check |
| Client delivery | native-plugin generator and six versioned metadata files | REUSE |

## Regression watchlist
- Preserve all pre-existing Graft changes and its project-only provider behavior. Baseline backups
  and the initial SDD tree snapshot identify that boundary.
- Hook startup output without a handoff stays unchanged; malformed input fails open, and resume
  references cannot leak between projects. Prove through the real hook subprocess.
- Keep rolling-window counters distinct from persistent dispatch/consultation ledgers; no resets,
  new coordinator, model overrides, backend activation or command-trust change.
- Preserve current prime source-reading behavior, public names/anchors and generated companions.
- Keep context/listing ceilings unchanged; use only conditional deep references.
- Runtime parity outside the tested clients and Graft qualification remain unconfirmed.

## Execution graph
The approved logical T1-T6 scopes and criteria remain unchanged. After the wave1 review found
W1-F1, combine remaining T3-T6 into one ordered integration package before dispatch; no parallel
writers or acceptance checks are removed. This preserves a fresh correction confirmation and a
separate final review within the existing eight-dispatch cap. Keep every consumed reservation.
Model trials are bounded tests with their own recorded attempts, not claims of native dispatch
coverage. The earlier read-only baseline is preparation evidence.

## Dispatch matrix
| Task | Approved scope | Role | Dependencies |
|---|---|---|---|
| T1.1 | T1 | graph-powers:debugger | none |
| T1.2 | T2 | graph-powers:debugger | none |
| T2.1 | T3, T4, T5, T6 in order | graph-powers:debugger | T1.1, T1.2 |

## Phase 1 — Instruction and continuation contracts [SEQUENTIAL]

- [x] **T1.1** — Reach a diff-scoped advisory instruction audit
  Owns: skills/intent-layer/SKILL.md, skills/intent-layer/references/node-anatomy.md, skills/intent-layer/evals/evals.json, commands/pr-review.md, references/shared/125-change-set.md, .claude/audit/cole-medin
  Needs: none
  Acceptance: Five cole-medin cases pass with real captured responses; rule/source, contradictory evidence, impact, minimal fix and confidence are returned only for relevant drift; valid inheritance and irrelevant diffs need no edit.
  Agent: graph-powers:debugger · Skill: graph-powers:skill-improve · Effort: high
  CHECK: python3 skills/skill-improve/scripts/run_evals.py --skill-path skills/intent-layer --evals-path skills/intent-layer/evals/evals.json --response-dir .claude/audit/cole-medin/intent-layer/candidate --case-tag cole-medin --threshold 1.0
  EXPECT: all five selected cases pass with exit 0
  EVIDENCE: current tagged run_evals exit0,5/5 cases,27 assertions; W1-F1 false-positive sample retained and rejected; fresh wave1_confirmation compliance/quality PASS, source/read hashes checked at HEADba6cd8d.
  TDD: not-applicable (Markdown contracts and semantic evaluations)
  Steps:
    1. Read the current files and preserve Graft changes, especially section C of 125. Add the small advisory procedure to node-anatomy and a conditional caller from intent-layer and pr-review; do not rebuild the full hierarchy or add a skill.
    2. Extend the existing change-set authority to include staged, unstaged and relevant untracked files without assuming main as a consumer base. Explicit target/base takes precedence. Keep graph retrieval conditional.
    3. Add five discriminating cases tagged cole-medin: removed path, replaced command, valid inherited rule, irrelevant change, consultative-only. Do not change existing cases to make this suite pass.
    4. Parent owns actual model capture and baseline preservation; source writer runs static checks, then controller executes the exact CHECK after recording candidate responses. Never synthesize responses or claim a self-reported load proves clean-client routing.

- [x] **T1.2** — Complete the existing handoffs and their recovery writers
  Owns: commands/evolve.md, skills/senior-prompt-engineer/references/agent-handoff-contracts.md, skills/planning/references/loop-engineering.md, skills/planning/references/wayfinding.md, skills/planning/references/step-0-inventory.md, references/recovery-protocol.md
  Needs: none
  Acceptance: A partial-work scenario preserves critical restrictions, scoped approval provenance, decisions, rejected attempts, current state and one next action; session and plan handoffs point to their owners without cloning plans or ledgers.
  Agent: graph-powers:debugger · Skill: graph-powers:senior-prompt-engineer · Effort: high
  CHECK: python3 .github/check_file_references.py
  EXPECT: exit 0 and the documented continuation scenario identifies the stale check and bounded next action
  EVIDENCE: file references exit0; real evolve handoff simulation preserved U17 scope/restrictions, rejected fallback, stale2222222 vs3333333 and5/8 ledger; independent wave1_review T1.2 compliance/quality PASS at snapshot2804890.
  TDD: not-applicable (Markdown contracts; continuation scenarios are reviewed)
  Steps:
    1. Extend existing fields and preserve Graft identity/digest/freshness semantics. Record objective, approved action/scope and provenance, critical constraints, decision rationale, rejected attempts, branch/HEAD/relevant working tree, gate command/result/validity and one next action.
    2. Keep evolve section 4 as the existing session-checkpoint format owner; plan/recovery checkpoints reuse that minimum state and add only their specific pointers. agent-handoff-contracts retains ownership of agent envelopes and links to checkpoint semantics conditionally. Keep .graph-powers/HANDOFF.md as session entry and plan-local HANDOFF.md as plan checkpoint; link active plan, sprint, snapshots and ledgers instead of copying them.
    3. Replace all universal 80K context triggers in loop-engineering, wayfinding and step-0-inventory with actual client signals or task boundaries. Automatic compaction remains supported; never invent telemetry or automatically clear context.
    4. Make recovery-protocol preserve the full session contract when adding blocked diagnostics. Handoff records existing authorization but grants none and activates no opt-ins.

- [x] **G1.1** — Verify instruction boundaries
  CHECK: python3 .github/check_wiring.py
  EXPECT: 0 unresolved routing references
  EVIDENCE: python3 .github/check_wiring.py exit0:283 routing references,0 unresolved; wave1 independently accepted.

## Phase 2 — Runtime integration and finalization [SEQUENTIAL]

- [ ] **T2.1** — Execute approved T3, T4, T5 and T6 in order as one integration package
  Owns: commands/prime.md, hooks/session_context.py, hooks/test_hooks.py, references/shared/070-parallel-agent-spawn.md, skills/planning/references/phase-c-executing-plans.md, skills/planning/references/execution/task-reviewer-prompt.md, skills/planning/evals/evals.json, CHANGELOG.md, NOTICE, package.json, .claude-plugin/plugin.json, .codex-plugin/plugin.json, .cursor-plugin/plugin.json, .grok-plugin/plugin.json, plugin.yaml, .codex-plugin/marketplace.json, codex/native-command-skills, codex/native-agents
  Needs: T1.1 (reads: accepted advisory audit and cases), T1.2 (reads: accepted continuation fields and checkpoint ownership)
  Acceptance: Approved T3-T6 each retain their original acceptance: real-hook RED/GREEN and isolation; unchanged executable caps with clear retention semantics; five current-evidence review cases; consistent next-patch metadata and source-generated client projections. All focused, semantic and final gates must pass before closing.
  Agent: graph-powers:debugger · Skill: graph-powers:debugger · Effort: high
  CHECK: python3 hooks/test_hooks.py --focus session-context-lifecycle
  EXPECT: EVERY GUARANTEE HELD with exit 0; parent additionally grades the five planning cases and complete final inventory before acceptance
  EVIDENCE: Implemented at snapshot35b29ee; real-hook RED/GREEN reported and parent fullsuite exit0; planning5/5 authentic cases/13assertions exit0; six versions1.19.4-to1.19.5;24/25 finalchecks pass. Independent integration_review compliance/quality PASS, source35b29ee; mandatory gate17 fails only on preexisting external docs/RELATORIO.md historical404, scoped editorial approval pending. Full acceptance remains open.
  TDD: required
  Steps:
    1. Approved T3: read TDD policy and writing-good-tests. Preserve Graft tests/provider pointer and prime's current decisive-source reads. Add real-subprocess cases for startup/resume/compact, with/without handoff, bounded JSON/pointer, malformed and non-object payloads, UTF-8 and project A/B/A isolation. Observe RED for missing behavior before production edits.
    2. Reuse project resolution and SessionStart registration. Emit only a short conditional pointer; never read full handoff content, execute its commands, grant authority or scan plan directories. Preserve startup without handoff and fail-open. Observe GREEN, then refactor only while green.
    3. Update prime's existing evidence paragraph with critical constraints, recorded approval scope/provenance and known active plan/checkpoint before readiness, preserving its actual-source reads. Keep this budget-neutral; no new eager deep load.
    4. Approved T4: clarify maxSpawnsPerSession/maxRoundsPerAgent within spawnWindowMinutes versus persistent Phase C dispatch/consultation reservations and correction history. Keep 020, execution-floor, models and executable limits unchanged. Link existing recovery; do not reset counters or add a coordinator.
    5. Approved T5: reuse 015 unchanged. Connect Phase C resume/reviewer to current package/tree/files/config/dependency/environment validity; invalidate affected evidence/dependencies only. Keep wave and final reviews distinct, bounded correction, and explicit lack of independent review.
    6. Add exactly the five planning cases tagged cole-medin from the original case-prompts artifact: stale PASS, valid PASS, exhausted budget, accepted-review stop, independent-review unavailable. Preserve Graft/old cases and exact prompts. Parent owns real model captures and grading; do not synthesize responses. Markdown contract steps are TDD-not-applicable; behavioral model evidence is still required.
    7. Approved T6, after source integration: preserve Graft changelog/NOTICE and version1.19.4 content. Add only this work's behavior/attribution; consistently advance the six metadata files to1.19.5 if baseline stays1.19.4.
    8. Run bun codex/native-plugin.mjs. Reemit the26 known outputs; generally only Codex version metadata changes. Investigate unexpected diffs. Generated metadata is TDD-not-applicable; no installation, global model/profile change, staging or publication.
    9. Focused static checks include quick_validate for affected skills, file references, wiring, context/listing and portability. Keep all caps unchanged. Reduce only redundancy inside owned, changed contracts if needed; preserve semantics and public anchors.
    10. Parent executes the exact planning run_evals command in Verification after capturing stable candidate responses and the current full final gate inventory. The integration-wave Evaluator and separate final Evaluator remain mandatory.

- [x] **G2.1** — Verify portable integration
  CHECK: python3 .github/check_portability.py
  EXPECT: 0 portability problem(s)
  EVIDENCE: python3 .github/check_portability.py exit0,0 portability problem(s); final-gates/20260909T103009-18.stdout.txt.

- [x] **G2.2** — Run declared hook suite at final boundary
  CHECK: python3 hooks/test_hooks.py
  EXPECT: EVERY GUARANTEE HELD with exit 0
  EVIDENCE: python3 hooks/test_hooks.py exit0,EVERY GUARANTEE HELD; final-gates/20260909T102848-02.stdout.txt, current hook/test hashes in integration-evidence.json.

## Verification
Run the 25 exact commands in .claude/rules/verify-supplements.md separately and in order. Include
the contributor's Codex/Cursor/Grok dry-runs in isolated scratch locations. Record exit codes and
decisive outputs; reuse only results that still cover final inputs. No undeclared build/typecheck.
Also run python3 skills/planning/scripts/test_sdd.py and python3 skills/skill-improve/scripts/run_evals.py --skill-path skills/planning --evals-path skills/planning/evals/evals.json --response-dir .claude/audit/cole-medin/planning/candidate --case-tag cole-medin --threshold 1.0.
Quick-validate the three changed skills; grade tagged cases at threshold 1.0; retain authentic
baseline/candidate responses and provenance under .claude/audit/cole-medin. Routing requires real
Skill/Read evidence; a reported skill name alone is insufficient and is not clean-client discovery.
Check the six versions directly against the implementation baseline as well: check_version_bump
uses committed history and alone does not prove an unstaged bump.

## Rollback
Use the before copies and initial working-tree snapshot to remove only these deltas. Preserve all
Graft changes, its plans, stored user handoffs and dispatch/consultation ledgers. Never reset/clean
the checkout or remove another plan's lease.

## Out of scope
Graft qualification/activation, dependencies, a new memory/framework/coordinator, billing telemetry,
global models/settings, installation, staging, commit, push, PR, merge and publication.

## Not yet specified
No solution decision is pending. A concurrent writer, new security boundary or mandatory unavailable
gate is a recorded blocker; never bypass it. Implementation approval already covers these scoped edits.
