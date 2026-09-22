# Issue 27 — complete Jev coordination

**Tier:** L4 · **Baseline:** main 7adc0d3 · **Risk surfaces:** schema, env.
**Authority:** user explicitly requested executing the remaining coordination and closing issue 27.
Original routing/setup work is complete in Git history and verification.md; this replaces its
completed task inventory. No commit/push permission. Existing installed-plugin refresh and issue
comments/closure are authorized. The prior one-call Jev smoke budget was consumed; the user now authorized two additional synthetic
evaluations (route and post-handoff), without retries, and +64 KiB in the source byte budget.

## Destination and architecture

When enabled, Jev selects a canonical agent/method/command action, including roles on the same
model. Main performs native execution with a seven-section handoff, validates returned Context
Handoff and runs the original approved checks. Returned evidence feeds the next Jev decision;
completion is eligible only with fresh successful proof. UI work includes verification through
webapp-testing and a real browser when an authorized target is available; use focused smoke first. No model response grants permissions.
A persistent SDD coordination context supports entry before a user PLAN exists and prevents
redispatch/recharging on resume. Phase C remains the implementation engine for linked plans.

## Reuse and graph

Extend evaluate.mjs for canonical action options and sdd.py for bounded state/receipts. Reuse
frontmatter catalogs, model policy, consultation cap/lock/fingerprint, dispatch ownership and
handoff schema. Add one native-controller bridge, not a daemon/MCP/second inventory.
T1.1 (typed records/state) -> T1.2 (catalog, route, return, fresh checks) -> T2.1 (bootstrap/Phase C)
-> T2.2 (generated package, verification, installed update, issue evidence).

## Phase 1 — Runtime [SEQUENTIAL]

- [x] **T1.1** — Extend typed route records and persistent coordination state
  Owns: skills/planning/scripts/sdd.py, skills/planning/scripts/test_sdd.py
  Needs: none
  Acceptance: Canonical richer actions preserve legacy records; init/select/return/finish enforce parent, identity, exclusive execution, caps and proof before completion.
  Agent: graph-powers:debugger · Skill: planning · Effort: design
  TDD: required
  Steps:
    1. Add production-interface regressions and capture RED.
    2. Implement the smallest change and capture GREEN, preserving existing checks.
  CHECK: python3 skills/planning/scripts/test_sdd.py
  EXPECT: OK
  EVIDENCE: RED/GREEN recorded by ledger specialist; final exit 0, 85 tests OK; coordination-final/04-Structured-plans.log.

- [x] **T1.2** — Connect action routing to native handoffs and verified returns
  Owns: codex/evaluate.mjs, codex/coordinate.mjs, .github/check_codex_policy.mjs, .github/check_jev_coordination.mjs
  Needs: T1.1 (reads: coordinate CLI and extended evaluationRequest candidates)
  Acceptance: Roles sharing a model remain distinct; catalog comes from canonical files; initial selection and post-return next/finish work through persistent SDD state; missing proof, stale artifacts and duplicate execution are refused.
  Agent: graph-powers:debugger · Skill: planning · Effort: design
  TDD: required
  Steps:
    1. Add production-interface regressions and capture RED.
    2. Implement the smallest change and capture GREEN, preserving existing checks.
  CHECK: bun .github/check_codex_policy.mjs
  EXPECT: codex-policy:
  EVIDENCE: RED/GREEN for same-model route, return/finish and linked-plan boundaries; final exit 0, policy and coordination integration PASS.

### Phase 1 gate

- [x] **G1.1** — Runtime contract and integrated fixture path pass
  CHECK: bun .github/check_codex_policy.mjs
  EXPECT: codex-policy:
  EVIDENCE: Exit 0; policy and integrated coordination fixture PASS, coordination-final/14-Codex-policy.log.

## Phase 2 — Call sites and delivery [SEQUENTIAL]

- [x] **T2.1** — Wire initial routing and Phase C returns to the coordinator
  Owns: agents/verification.md, references/shared/005-method-bootstrap.md, references/shared/030-agent-assignment-matrix.md, references/execution-floor.md, skills/senior-prompt-engineer/references/agent-handoff-contracts.md, skills/planning/references/phase-c-executing-plans.md, README.md, AGENT_SETUP.md
  Needs: T1.2 (reads: executable catalog/start/next/return CLI and its status contract)
  Acceptance: Main has an explicit executable call site before selecting methods and on worker returns; existing user authority, reviewers, guards and disabled-mode behavior remain intact.
  Agent: graph-powers:debugger · Skill: senior-prompt-engineer · Effort: design
  TDD: not-applicable (instructions; behavior tested through controller interface)
  Steps:
    1. Update only affected canonical call sites and validate references.
  CHECK: python3 .github/check_wiring.py
  EXPECT: 0 unresolved
  EVIDENCE: Exit 0; 534 routing references checked, 0 unresolved; independent final wiring review PASS.

- [x] **T2.2** — Regenerate and prove the candidate, refresh the installed plugin and report
  Owns: .github/test_hook_clients.py, hermes/package/skills/content/commands/issue-improve.md, hermes/package_builder.py, hermes/package/NOTICE, hermes/package/skills/content/skills/webapp-testing/SKILL.md, hermes/package/skills/webapp-testing.md, .github/check_clone.py, .claude/rules/verify-supplements.md, codex/native-agents/verification.toml, hermes/package/skills/agent-verification.md, hermes/package/skills/content/agents/verification.md, CHANGELOG.md, package.json, .claude-plugin/plugin.json, .codex-plugin/plugin.json, .cursor-plugin/plugin.json, .grok-plugin/plugin.json, plugin.yaml, hermes/package/PROVENANCE.json, hermes/package/plugin.yaml, hermes/package/skills/content/AGENT_SETUP.md, hermes/package/skills/content/codex/evaluate.mjs, hermes/package/skills/content/codex/coordinate.mjs, hermes/package/skills/content/skills/planning/scripts/sdd.py, hermes/package/skills/content/references/execution-floor.md, hermes/package/skills/content/references/shared/005-method-bootstrap.md, hermes/package/skills/content/references/shared/030-agent-assignment-matrix.md, hermes/package/skills/content/skills/senior-prompt-engineer/references/agent-handoff-contracts.md, hermes/package/skills/content/skills/planning/references/phase-c-executing-plans.md, docs/plans/2026-09-22-issue-27/verification.md, docs/plans/2026-09-22-issue-27/smoke.md
  Needs: T2.1 (reads: final source contract and bounded generated dependency closure)
  Acceptance: Applicable gates and independent review pass; installed sources match; report separates fixture/native/provider evidence; issue closes only with supported completion claims.
  Agent: graph-powers:debugger · Skill: none · Effort: mechanical
  TDD: not-applicable (generation, verification and publication)
  Steps:
    1. Regenerate exact outputs, run gates, refresh installed package and publish factual evidence.
  CHECK: bun hermes/install.mjs --check
  EXPECT: source manifest and package are current
  EVIDENCE: Exit 0; 39 registrations, source manifest and package current. Thirty final gate commands exit 0; installed 1.23.0 matches 12 decisive sources, five personal roles and global config preserved; real cycle in smoke.md.

### Phase 2 gate

- [x] **G2.1** — Preserve guardrails
  CHECK: python3 hooks/test_hooks.py
  EXPECT: EVERY GUARANTEE HELD
  EVIDENCE: Exit 0; EVERY GUARANTEE HELD, coordination-final/02-Guardrails.log.

## Validation, risk and rollback

Run focused RED/GREEN, independent review and applicable ordered verify-supplements gates. Reuse
prior evidence only for unchanged relevant inputs. Retain the authorized source ceiling (4 MiB +64 KiB) and unchanged Hermes ceiling (2 MiB).
No frontend/database product surface changes. Preserve existing personal settings and model choices.
Rollback only owned hunks and generated mirrors; keep recorded coordination/consultation attempts
on resume. No automatic API retries, budget resets or dispatch from a pending reservation.
Native role availability and newly authorized live evaluation are explicit proof boundaries.
