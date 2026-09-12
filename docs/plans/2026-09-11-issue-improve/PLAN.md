# Issue improve — implementation plan

**Date:** 2026-09-11 · **Branch:** main · **Baseline:** 4c058cb
**Tier:** L3
**Risk surface:** none
**Design authority:** [spec.md](spec.md), parent-sanitized issue 20 and the user's explicit
Gauntlet implementation request. Evaluator Mode 1 PASS on 2026-09-11 (completeness 9, atomicity 8,
risk 8, order 9); lease acquired after that review.

## Destination

`issue-improve` turns a fetched issue into a concise, evidence-backed executable plan, validates
L3+ with the existing Gauntlet grammar, and can publish/update one authorized marked comment.
All requested clients expose the public entry without duplicate native registrations; focused
proofs and declared gates pass on the reviewed unstaged working tree at version 1.20.5.

## Issue Triage (upstream mandate)

Sanitized parent mandate, six rows, tier floor L3. No raw issue body is forwarded.

| Req | Scope | Verdict | Evidence | Grade | Rationale |
|---|---|---|---|---|---|
| R1 | New issue-improve command and skill | KEEP | commands/plan.md:10; skills/AGENTS.md:11 | 4 | Existing planning entry does not own comment delivery |
| R2 | Accept number/URL; fetch body/comments; fail BLOCKED | SIMPLIFY | skills/planning/references/issue-triage.md:26 | 5 | Reuse canonical retrieval/blockers instead of duplicating them |
| R3 | Host-aware evidence, layers, phases/sprints and tasks | SIMPLIFY | skills/planning/references/step-0-inventory.md:83; phase-b-writing-plans.md:51 | 5 | Reference existing methods and grammar |
| R4 | Validate L3+ before posting; short L1–L2 form | KEEP | skills/planning/scripts/sdd.py:1142; gauntlet-loop.md:31 | 5 | Existing validator supplies the publication prerequisite |
| R5 | Authorized idempotent marked comment; stop before execution | KEEP | references/safety-floor.md:17; commands/plan.md:14 | 4 | Add only missing author/marker selection mechanics |
| R6 | Wiring, evals, generated clients, provenance and patch bump | SIMPLIFY | codex/native-plugin.mjs:91; hermes/install.mjs:122; .github/check_wiring.py:213 | 5 | Canonical same-name skill replaces redundant native wrapper; preserve public names |

KEEP 3 · SIMPLIFY 3 · CUT 0 · DEFER 0. All R1–R6 remain in scope; implementation detail is
simplified by reuse. Design decisions and alternatives are owned by spec.md.

## Reuse ledger

| # | Need | Existing asset (`path:line`) | Verdict | Why extending fails (NEW only) |
|---|---|---|---|---|
| N1 / R1 | Distinct planning-to-comment entry | commands/plan.md:10 | NEW | Extending /plan would add outward behavior to an existing planning contract; the requested entry is its first consumer |
| N2 / R2 | Issue retrieval and sanitization | skills/planning/references/issue-triage.md:26 | REUSE | — |
| N3 / R3 | Host inventory and executable plan | skills/planning/references/step-0-inventory.md:21; phase-b-writing-plans.md:51 | REUSE | — |
| N4 / R4 | Structural validation | skills/planning/scripts/sdd.py:1142 | REUSE | — |
| N5 / R5 | Update the authenticated author's marked comment | commands/plan.md:14; references/safety-floor.md:17 | NEW | Targeted searches found no updater; gh's edit-last selection cannot prove the marker rule |
| N6 / R6 | Registration, evaluation and distribution | skills/skill-improve/references/authoring.md:31; codex/native-plugin.mjs:91; hermes/install.mjs:122 | EXTEND | — |

Evidence provider: direct source/text, current checkout, scope commands/skills/client generators
and their tests. SHA-256 prefixes at inventory: config `ec7e21be96af18ee`, triage
`e5cd32bbf5e2f5e5`, sdd `a2caab06bf19e00a`, native generator `9e22123222e8b7fe`, clone
generator `ef4b43182a955ffb`, Hermes generator `63b4b4cdaac5bd6d`. The only pre-existing dirty
path is `bin/graph-powers.mjs`, digest `c889f134c66633b8`; preserve it. Re-read an edge only when
its relevant source/config/consumer or working-tree identity changes.

## Regression watchlist

| # | Existing behaviour that must still work | How to prove it | Phase |
|---|---|---|---|
| W1 | Planning grammar, default execution and Gauntlet stay separate | python3 skills/planning/scripts/test_sdd.py | 1 |
| W2 | Existing command names, Codex clone wrappers and native companions resolve | python3 .github/check_codex_native.py | 1 |
| W3 | Hermes static closure/bytes and remaining collision protections hold | python3 -X utf8 .github/test_hermes_package.py; python3 -X utf8 .github/test_hermes.py --static | 1 |
| W4 | Public routes/reference anchors and unchanged /plan behavior hold | python3 .github/check_wiring.py; python3 .github/check_file_references.py | 1 |
| W5 | Budgets and portable paths remain below current ceilings | python3 .github/check_context_budget.py; python3 .github/check_listing_budget.py; python3 .github/check_portability.py | 1 |
| W6 | Existing guards and client configuration posture remain unchanged | python3 hooks/test_hooks.py; python3 .github/test_hook_clients.py | 1 |

Parent-reported baseline PASS: wiring 500 refs/zero unresolved; native Codex 12 roles/1.20.4;
listing 7,669/8,000. Other full baseline gates are pending; do not claim them passed.

## Execution graph

One sequential writer task, then one wave critic and a separate final review; no parallel writers.
Inside T1.1: canonical method/helper → routing/projections → final proofs. The first edge carries
the `issue-improve` method/script paths and marker contract; the second carries the final source
inventory and version 1.20.5. The parent preserves leases, snapshots and dispatch reservations.
The execution command is `/gauntlet` for this plan; the new skill itself never runs Phase C.

Configured limits come from schema/config resolution, never a new literal policy: current
defaults are maxTasksPerPlan 12, maxParallelWave 3, maxSpawnsPerWorkflow 8,
maxRoundsPerAgent 4, maxRepatch 2. Audit + planner + plan review + writer + wave review + final
review + verification loop reserve seven dispatches; one remains for a bounded correction.
If another required review would exceed eight, stop with evidence rather than skip/reset a gate.

## Requirement coverage

| Need | Surface | Applicable evidence | Task(s) and Owns | Producer → consumer payload/path | Acceptance evidence |
|---|---|---|---|---|---|
| N1/R1 | frontend/client | commands/plan.md:10; skills/AGENTS.md:11 | T1.1: commands/issue-improve.md, skills/issue-improve | public command → canonical SKILL.md, original issue argument/config | G1.1, G1.2 |
| N2/R2 | backend/API | issue-triage.md:26 | T1.1: skills/issue-improve | gh body/comments → triage, sanitized R ledger and canonical issue URL | Mode A cases; T1.1 CHECK |
| N3/R3 | backend | step-0-inventory.md:21; phase-b-writing-plans.md:51 | T1.1: skills/issue-improve | configured host evidence → spec/PLAN and comment content | Mode A cases; G1.1 |
| N4/R4 | backend | sdd.py:1142 | T1.1: skills/issue-improve | L3+ PLAN/configured cap → sdd validation exit → publication eligibility | Mode A cases; W1 |
| N5/R5 | backend/API | safety-floor.md:17; no existing updater found | T1.1: skills/issue-improve/scripts | approved target/body → gh paginated author/marker lookup → POST/PATCH/no-op | T1.1 CHECK, including negative paths |
| N6/R6 | frontend/client | native-plugin.mjs:91; hermes/install.mjs:122 | T1.1: routing, generators, tests, metadata, generated outputs | canonical command/skill inventory → one client entry and versioned package | G1.2–G1.4 and final inventory |
| N1–N6 | database N/A | .graph-powers/config.json: paths has planDir/rulesDir only; AGENTS.md ownership map identifies a harness | T1.1: documentation/scripts/client metadata only | No tenant query, database schema or migration producer/consumer | Owned diff review; no database probe required |
| N1–N6 | product UI N/A | Same config declares no frontendRoot; requested consumers are agent clients | T1.1: client entry text only | No product route/component/rendered flow | Owned diff review; browser/accessibility probe N/A |

## Dispatch matrix

| Task | Agent | Skill | Owns | Needs |
|---|---|---|---|---|
| T1.1 | graph-powers:debugger | graph-powers:skill-improve | Exact paths in the task block | none |

This is the existing write-capable canonical lane accepted by sdd; dispatch its native `debugger`
companion with the role's model. Mode A authoring and Planning TDD policy are explicit context;
Mode B's completed read-only findings are reused. The writer creates no children.

## Phase 1 — Deliver the planning-to-comment entry [SEQUENTIAL]

**Sprint 1:** One callable planning-only feature and its client projections. Verify the mocked
comment flow, focused skill cases and final gate inventory. Exclude real publication, host code,
installation and Git actions. Stop at a reviewable working tree.

- [x] **T1.1** — Deliver issue-improve through its canonical method and client entries (R1–R6)
  Owns: commands/issue-improve.md, skills/issue-improve, references/shared/060-skill-domain-matrix.md, references/shared/120-skill-invocation-order.md, codex/native-plugin.mjs, .github/check_codex_native.py, .github/check_context_budget.py, .claude/rules/verify-supplements.md, .github/workflows/ci.yml, __init__.py, hermes/install.mjs, .github/check_wiring.py, .github/test_hermes.py, .github/test_hermes_package.py, NOTICE, CHANGELOG.md, package.json, .claude-plugin/plugin.json, .codex-plugin/plugin.json, .codex-plugin/marketplace.json, .cursor-plugin/plugin.json, .grok-plugin/plugin.json, .grok-plugin/marketplace.json, plugin.yaml, codex/native-command-skills, codex/native-agents, hermes/package
  Needs: none
  Acceptance: The real helper CLI passes every mocked publication outcome and failure case, focused method cases preserve R1–R5, and canonical-derived client registrations expose issue-improve once with R6 metadata at 1.20.5; no real outward write occurs.
  Agent: graph-powers:debugger · Skill: graph-powers:skill-improve · Effort: design
  TDD: required
  CHECK: python3 skills/issue-improve/scripts/test_issue_comment.py
  EXPECT: OK
  EVIDENCE: RED helper absent, Hermes canonical collision and Codex redundant wrapper; GREEN helper 15 tests OK (2026-09-12, after final-review Minors 5/8), fixtures 5/5 (22/22), quick_validate PASS; wave evaluator compliance/quality/integration PASS at snapshot 770563b; security PASS on helper bytes 124358ff, later delta = two guards only; final review WITH FIXES (applied); verify loop VERIFIED-WITH-NOTES on the current tree.
  Steps:
    1. Read AGENTS.md, skills/AGENTS.md, .graph-powers/config.json, .claude/rules/artifacts.md, .claude/rules/verify-supplements.md, local Oxc options for the changed ESM, skill-improve Mode A, and planning/references/execution/tdd-policy.md plus writing-good-tests.md. Preserve the dirty bin file; do not alter global settings or hook permissions.
    2. RED: write the smallest unittest cases at skills/issue-improve/scripts/test_issue_comment.py against the real CLI with mocked gh: preview/no publish, create, author+standalone-marker update, unchanged retry, page-two match, foreign/unmarked exclusion, duplicate-own BLOCKED, missing/invalid inputs, Unicode/quotes and gh errors. Confirm failures for absent behavior. Add RED regression fixtures in the existing Codex/Hermes tests for canonical skill plus same-name command yielding one registration; unrelated and case-fold collisions must still fail.
    3. GREEN: implement only issue_comment.py publication mechanics from spec.md. Require --issue-url and --body-file; default preview, explicit --publish after caller approval. Use subprocess argv and JSON stdin, paginated reads, authenticated-author selection and no blind POST retry. Do not persist issue/comment bodies outside the reviewed draft; no secrets in diagnostics. Re-run focused tests; refactor only while GREEN.
    4. Add the short command adapter and canonical skill. Resolve original arguments/config, fetch through one gh issue view call with --json number,title,body,state,labels,author,url,createdAt,closedAt,comments (never combine --comments and --json), read existing issue-triage policy/Step0/A/B on demand and keep planning ownership there. The command reads the skill by path; skill invocation never loops back. Emit concise L1–L2 or validated L3+ executable content and the marker comment. Require approval for the final target/payload before --publish; never invoke Phase C, host implementation, commit or issue-body replacement.
    5. Add focused evals/evals.json cases and learning.md with actual measured results, capture provenance and limitations. Reuse quick_validate.py and per-case run_evals.py --threshold 1.0; use a response directory with one result per case if batching. Fixture assertions are not fresh-model/clean-session evidence. Cover L3 ordering, L1–L2, retrieval/injection containment and no execution or unauthorized publication. Link scripts, evals and learning from the entry so no new file is orphaned.
    6. Add the domain-matrix row and invocation-order location. Combined new names plus descriptions must cost at most 331 listing characters. In buildNativeCommandSkills, skip only a command whose exact canonical skills/name/SKILL.md exists. In Hermes planned_registrations/buildRegistrationPlan and the wiring collision checker, give the same exact canonical pair precedence; keep genuine other collisions rejected. Match tests to the source-derived inventory, preserve existing clone command prefixes and manifest roots, and re-run generator regressions.
    7. Record original in-repository adaptation and any actually used external source in NOTICE without inventing attribution. Add CHANGELOG entry and update six version owners to 1.20.5 through existing generators where applicable. Run bun codex/native-plugin.mjs, bun cursor/install.mjs --emit-only, bun grok/install.mjs --emit-only, bun hermes/install.mjs --emit-only, then bun hermes/install.mjs --package-only. Generated cursor hooks must remain byte-identical; stop before any out-of-ownership diff. Generated artifacts are not hand-maintained.
    8. Register the focused helper regression in .claude/rules/verify-supplements.md and .github/workflows/ci.yml, following their existing test steps and updating the inventory count; preserve CI permissions, events and deployment policy. Run task CHECK, focused evals, phase gates and the complete declared inventory. Return actual RED/GREEN, generated-path changes, matched CHECK/EXPECT and blockers. The parent handles independent wave/final reviews and ledger close. Do not publish a real comment as a test.

### Phase 1 gate

- [x] **G1.1** — The canonical skill meets its frontmatter contract
  CHECK: python3 skills/skill-improve/scripts/quick_validate.py skills/issue-improve
  EXPECT: Skill is valid!
  EVIDENCE: quick_validate exit 0 "Skill is valid!" (gates/final/G1.1-4.log, 2026-09-12, final tree)
- [x] **G1.2** — Public invocations and method paths resolve
  CHECK: python3 .github/check_wiring.py
  EXPECT: 0 unresolved
  EVIDENCE: check_wiring exit 0: 524 routing references, 0 unresolved; 12 agents register (gates/inventory-2026-09-12-final/15.log)
- [x] **G1.3** — Native Codex and clone command projections match their canonical source
  CHECK: python3 .github/check_codex_native.py
  EXPECT: codex-native:
  EVIDENCE: check_codex_native exit 0: 12 companion roles, native/clone parity, manifest 1.20.5 (gates/inventory-2026-09-12-final/14.log)
- [x] **G1.4** — Hermes source package passes collision and closure regression tests
  CHECK: python3 -X utf8 .github/test_hermes_package.py
  EXPECT: OK
  EVIDENCE: test_hermes_package exit 0: Hermes package STATIC PASS (gates/inventory-2026-09-12-final/18.log)
- [x] **G1.5** — The final serial declared test suite preserves guardrails
  CHECK: python3 hooks/test_hooks.py
  EXPECT: EVERY GUARANTEE HELD
  EVIDENCE: hooks/test_hooks.py exit 0: EVERY GUARANTEE HELD (gates/inventory-2026-09-12-final/02.log)

Phase close also requires task/eval evidence, exact ownership review (including baseline dirty
digest), all producer paths named above and the final declared gates. Type-check, lint and build
are NOT DECLARED as gates here; do not manufacture or run them as completion claims.

## Verification

Before execution: `python3 skills/planning/scripts/sdd.py validate docs/plans/2026-09-11-issue-improve/PLAN.md --max-tasks 12 --profile gauntlet`, then a current evaluator Mode 1 PASS.
The validator checks structure; independent review checks meaning and surface coverage.

Mode A: quick_validate plus
`python3 skills/skill-improve/scripts/run_evals.py --skill-path skills/issue-improve --evals-path skills/issue-improve/evals/evals.json --response-dir .claude/audit/issue-improve-evals --threshold 1.0`.
The parent owns real captured responses if used, under that untracked audit path. If only fixture
assertions are used, label the evidence and leave clean-session routing UNVERIFIED.

Final: run the complete declared inventory (27 baseline checks plus the newly registered helper
regression), in order, from `.claude/rules/verify-supplements.md`. Its exact file is the gate inventory authority; no gate is silently
omitted. Hermes preparation is `bun hermes/install.mjs --package-only` and
`bun hermes/install.mjs --check` before static gates. The CI-only Codex installation assertion
remains CI-only; installed Hermes runtime remains UNVERIFIED. No browser or DB checks apply.
Close through the existing Gauntlet final review and `/verify loop` with configured caps; reuse
only evidence valid for the current diff/config/environment. After success, `/evolve auto` writes
only the project's existing learning log, preserving its ownership rules.

## Rollback

Undo only T1.1's owned new files/hunks, regenerate projections from restored canonical sources,
and leave the user's bin change intact. No staged/committed state is created. A future comment correction requires explicit approval for that target/payload; no automatic
comment deletion, remote rollback or migration happens during this implementation.

## Out of scope

Host implementation/Phase C in the new skill, real GitHub writes this turn, issue-body edits,
new agents/workflows/config/SDKs, installation, Git actions, CI-policy changes beyond adding the regression step and unrelated dirty
files. Reopen only on an explicit corresponding action/scope request. Distributed publisher
locking reopens only on demonstrated concurrency demand.

## Not yet specified

No fog: all material design choices are closed. Current evaluator PASS, implementation checks
and final proof remain pending; execution is blocked until the required plan review passes.
