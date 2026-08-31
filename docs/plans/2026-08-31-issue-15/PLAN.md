# Issue 15 — economical routing and bounded evaluator consultation

**Tier:** L6 · controller-owned orchestration, generated projections, and model-policy changes

This plan implements issue 15 on top of the existing Gauntlet branch. The semantic Codex policy
remains the single model authority. Ordinary reviews stay separate from economical-worker
consultations. The parent/controller owns the consultation ledger, deduplication, capability
fallback, and stop conditions; hooks remain guidance-only.

## Acceptance contract

- Codex routine workers resolve to Luna; the evaluator resolves to Sol/max; Ultra is a separate
  top-level-only profile and never a subagent leaf.
- The alternate-harness evaluator uses Fable/xhigh only after a positive harness/provider
  capability check. Unsupported or unknown capability falls back to the existing Opus/xhigh
  evaluator, with no Fable emitted.
- A consultation request has a task identity, stable decision key, evidence, options,
  recommendation, risk, verdict, backend, capability status, and depth. One key is consulted once;
  at most three distinct keys are allowed per task. The fourth or unresolved required request
  returns an explicit user/block state without spawning or retrying.
- Review/evaluator/critic passes are not consultations and do not consume the consultation budget;
  evaluators, reviewers, and nested/deeper requests cannot request another consultation.
- Override diagnostics use fixed, value-free warning categories and never echo configured model,
  profile, effort, or secret-sentinel values.
- Both workflows preserve each canonical agent's declared family, with only named mechanical
  downgrades remaining explicit and tested. Generated Codex companions stay derived and drift-free.

## Tasks

- [ ] **T1** — Extend the semantic policy, top-level economy, and sanitized override diagnostics
  Owns: codex/model-policy.json, codex/model-policy.mjs, schema/config.schema.json, .github/check_codex_policy.mjs, .github/check_codex_native.py, codex/native-agents
  Needs: none
  Agent: graph-powers:debugger · Skill: graph-powers:skill-improve · Effort: high
  Check: `bun .github/check_codex_policy.mjs` and `python3 .github/check_codex_native.py`
  Expect: Luna economical top-level profile, Sol/max evaluator, Ultra top-level-only, capability-safe policy metadata, and sanitized collapse warnings all pass source and generated parity checks.
  Evidence: pending
  TDD: required
  Steps:
    - RED: add focused assertions for the economic top-level profile, invalid leaf use, exact canonical mappings, and secret-sentinel-free warnings.
    - GREEN: update the single policy source, resolver, schema, and policy/native oracles; regenerate companions through the existing generator.
    - VERIFY: run the two focused policy gates and inspect generated diff for drift.

- [ ] **T2** — Add the executable parent-mediated consultation ledger and canonical handoff contract
  Owns: skills/planning/scripts/sdd.py, skills/planning/scripts/test_sdd.py, references/execution-floor.md, skills/senior-prompt-engineer/references/agent-handoff-contracts.md, skills/planning/references/phase-c-executing-plans.md, skills/planning/references/gauntlet-loop.md, agents/evaluator.md
  Needs: none
  Agent: graph-powers:debugger · Skill: graph-powers:debugger · Effort: high
  Check: `python3 skills/planning/scripts/test_sdd.py`
  Expect: stable-key dedupe, three-key task cap, fresh-task budget, explicit blocked/user-required result, capability fallback metadata, no evaluator/reviewer/depth recursion, and review-versus-consultation separation are deterministic and documented.
  Evidence: pending
  TDD: required
  Steps:
    - RED: add CLI and contract tests for first reservation, duplicate reuse, three allowed keys, fourth capped key, fresh task, unresolved result, malformed identity, and forbidden requester/depth.
    - GREEN: implement secure atomic consultation state in the existing SDD workspace and document the request/result envelope and parent-only routing rules.
    - VERIFY: run the focused SDD suite, symlink/concurrency tests, and inspect the existing Gauntlet content for preserved behavior.

- [ ] **T3** — Make planning and verification workflows preserve declared families and route consultations through the parent
  Owns: workflows/ultra-plan.js, workflows/ultra-verify.js, .github/check_workflows.mjs
  Needs: T1 (reads: semantic policy profile names and evaluator capability metadata), T2 (reads: consultation envelope, caps, and requester restrictions)
  Agent: graph-powers:debugger · Skill: graph-powers:debugger · Effort: high
  Check: `bun .github/check_workflows.mjs`
  Expect: dry-runs pass with complete declared-family maps; ordinary review calls remain outside the consultation ledger; only a parent can reserve/record a consultation and no evaluator-originated or nested request is emitted.
  Evidence: pending
  TDD: required
  Steps:
    - RED: extend workflow dry-run assertions with declared-family parity, supported/unknown evaluator capability fixtures, consultation dedupe/cap scenarios, and non-consumption by review critics.
    - GREEN: derive the complete canonical model map at bootstrap, add bounded parent consultation state/routing, and keep explicit mechanical gate downgrades named.
    - VERIFY: run the workflow oracle and inspect every agent call's model source and consultation path.

- [ ] **T4** — Project conditional economical routing into canonical agents and user-facing documentation
  Owns: agents/debugger.md, agents/frontend-specialist.md, agents/mobile-developer.md, agents/performance-optimizer.md, agents/verification.md, README.md, CHANGELOG.md, .claude-plugin/plugin.json, .codex-plugin/plugin.json, .cursor-plugin/plugin.json, .grok-plugin/plugin.json, package.json, plugin.yaml
  Needs: T1 (reads: final semantic policy names and warnings), T2 (reads: final consultation and capability contract), T3 (reads: workflow family behavior)
  Agent: graph-powers:debugger · Skill: graph-powers:skill-improve · Effort: high
  Check: `python3 .github/check_version_bump.py` and `python3 .github/check_wiring.py`
  Expect: routine alternate-harness workers use the lower declared family, evaluator documents Fable only on positive capability and safe Opus fallback, docs explain limits and no hook spawning, and all package projections share one bumped version while preserving Gauntlet notes.
  Evidence: pending
  TDD: required
  Steps:
    - RED: add or extend source/projection assertions for worker/evaluator frontmatter and version/changelog documentation.
    - GREEN: update only canonical agent metadata and generated-facing documentation/manifests; do not hand-edit Codex snapshots.
    - VERIFY: run wiring/version checks and inspect the branch diff for unrelated changes.

- [ ] **T5** — Run the complete repository acceptance suite and reconcile residual capability risk
  Owns: docs/plans/2026-08-31-issue-15/PLAN.md
  Needs: T1 (reads: policy gate evidence), T2 (reads: consultation test evidence), T3 (reads: workflow gate evidence), T4 (reads: projection and documentation evidence)
  Agent: graph-powers:debugger · Skill: graph-powers:skill-improve · Effort: high
  Check: all commands in the repository root AGENTS.md Gates section plus `git diff --check`
  Expect: every available gate passes, unavailable tools are recorded rather than substituted, the plan records observed RED/GREEN and gate evidence, and no commit/push is performed.
  Evidence: pending
  TDD: required
  Steps:
    - RED: run the focused and full gate suite to expose integration failures or generated drift.
    - GREEN: apply only scoped fixes required by fresh gate output, preserving the one-writer and source-of-truth rules.
    - VERIFY: rerun all affected gates and record the final evidence and any external Fable entitlement limitation.

## Phase gates

- [ ] **G1** — Policy contract is executable
  Check: `bun .github/check_codex_policy.mjs && python3 .github/check_codex_native.py`
  Expect: source policy and generated companions agree, with no Ultra leaf or sensitive warning output.
  Evidence: pending

- [ ] **G2** — Consultation contract is bounded and secure
  Check: `python3 skills/planning/scripts/test_sdd.py`
  Expect: exact-once keys, three-key cap, recursion refusal, explicit fallback/block state, and secure state tests pass.
  Evidence: pending

- [ ] **G3** — Workflows preserve model families
  Check: `bun .github/check_workflows.mjs`
  Expect: every non-mechanical spawn uses the canonical declared family and review critics do not consume consultation capacity.
  Evidence: pending

- [ ] **G4** — Projections and docs are wired
  Check: `python3 .github/check_wiring.py && python3 .github/check_version_bump.py`
  Expect: all references resolve, the version is bumped consistently, and the issue behavior is documented without absolute paths or project-specific routing.
  Evidence: pending

- [ ] **G5** — Full repository acceptance
  Check: the complete root AGENTS.md Gates list and `git diff --check`
  Expect: all runnable gates pass and residual risk is limited to unproven external account/provider capability.
  Evidence: pending
