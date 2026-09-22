# Issue 27 — current Codex models and typed routing

**Expanded objective — HOLD:** checked tasks below cover the original optional-routing scope.
The latest request requires Jev to select agents/skills/commands and coordinate round-trip handoffs.
Audit found this unimplemented; issue 27 stays OPEN. Revise acceptance and the execution graph
before implementing or declaring the broader goal complete.

**Tier:** L4
**Baseline:** main, d30ccc21f3296c0ecb77d57e94761238bd526585, version 1.21.1, clean.
**Design authority:** User-approved conversation plan, including latest Sol/Luna generation.
**Authorization:** Implement local changes/checks and update the existing installed plugin and
AGENT_SETUP.md. No commit, push, publication or credential changes authorized. A later explicit user reply
authorizes synthetic Codex Astra/high and Luna/medium|max smokes and at most one real Jev call
using an existing process credential; no automatic retry.

## Destination

Ten specialists resolve Astra/high; scouts resolve Luna 6/medium. Document the manually selected
parent Luna 6/max. Keep existing native-economic Luna 6/low and native-ultra Sol 6/ultra top-level.
Jev is optional typed routing, never a chat role or prose reviewer. Only a fresh reservation may
send one request; duplicate/pending/terminal decisions never retry. Preserve overrides and Kilo.

## Reuse ledger

Extend codex/model-policy.json and its resolver/readers; reuse both native and clone generators.
Extend sdd.py consultation locking/storage; reuse three-per-task budget and parent-only envelope.
Add only codex/evaluate.mjs for the absent HTTP evaluation transport. Reuse existing package
generators and native local marketplace update. Read AGENT_SETUP.md during authorized updates.

## Phase 1 — Contracts [SEQUENTIAL]

- [x] **T1.1** — Update model defaults and regression expectations
  Owns: codex/model-policy.json, codex/model-policy.mjs, .github/check_codex_policy.mjs, .github/check_codex_native.py, .github/check_codex.py, README.md
  Needs: none
  Acceptance: Ten Astra/high and two Luna/medium defaults; top-level profiles updated; overrides and role permissions preserved.
  Agent: graph-powers:debugger · Skill: planning · Effort: design
  TDD: required
  CHECK: bun .github/check_codex_policy.mjs
  EXPECT: codex-policy:
  EVIDENCE: RED expected Astra/high but got old Sol/max; GREEN check_codex_policy exit 0 and native 12-role parity exit 0; final independent READY.
  Steps:
    1. Update literal expectations and capture RED on the old default.
    2. Update existing profile values and related prose, preserving explicit override fixtures.
    3. Confirm GREEN; generated snapshot parity closes in T3.1.

- [x] **T1.2** — Separate evaluation configuration and chat resolution
  Owns: codex/model-policy.json, codex/model-policy.mjs, schema/config.schema.json, codex/install.mjs, .github/check_codex_policy.mjs
  Needs: T1.1 (reads: current semantic policy and regression expectations)
  Acceptance: Evaluation configuration is preserved independently; Jev never resolves as a chat role.
  Agent: graph-powers:debugger · Skill: planning · Effort: design
  TDD: required
  CHECK: bun .github/check_codex_policy.mjs
  EXPECT: codex-policy:
  EVIDENCE: RED evaluation resolver absent; GREEN config/modality/override negatives in check_codex_policy exit 0; final independent READY.
  Steps:
    1. Add production-interface configuration and modality regressions; capture RED.
    2. Extend policy/resolver/schema/reader with the minimum evaluation settings.
    3. Confirm GREEN without changing precedence or inventing evaluation reasoning effort.

- [x] **T1.3** — Extend the consultation ledger for typed results and exclusive sending
  Owns: skills/planning/scripts/sdd.py, skills/planning/scripts/test_sdd.py
  Needs: none
  Acceptance: Fresh Jev reservation exclusively authorizes sending; fingerprints reject changed input; terminal and pending duplicates never resend; three-per-task and legacy backends remain valid.
  Agent: graph-powers:debugger · Skill: planning · Effort: design
  TDD: required
  CHECK: python3 skills/planning/scripts/test_sdd.py
  EXPECT: OK
  EVIDENCE: RED unsupported backend, legacy fallback mismatch and verdict/choice mismatch; GREEN SDD 77 OK exit 0; correction confirmation PASS.
  Steps:
    1. Add CLI regressions for Jev, typed results, duplicate identity, concurrent reservation and resume; capture RED.
    2. Extend existing validation and atomic storage without another ledger or lock service.
    3. Confirm GREEN for new and legacy cases.

### Phase 1 gate

- [x] **G1.1** — Contract checks pass
  CHECK: bun .github/check_codex_policy.mjs
  EXPECT: codex-policy:
  EVIDENCE: check_codex_policy exit 0; all contract and transport regressions passed.

## Phase 2 — Integration [SEQUENTIAL]

- [x] **T2.1** — Add the bounded HTTP evaluation adapter
  Owns: codex/evaluate.mjs, .github/check_codex_policy.mjs
  Needs: T1.2 (reads: resolved evaluation settings), T1.3 (reads: exclusive reservation and typed result interface)
  Acceptance: JSON stdin/stdout adapter validates candidates, skips identical models/no doubt, sends at most once with timeout, records typed result/failure and never spawns or retries.
  Agent: graph-powers:debugger · Skill: planning · Effort: design
  TDD: required
  CHECK: bun .github/check_codex_policy.mjs
  EXPECT: codex-policy:
  EVIDENCE: RED absent module and symlink mixed-root acceptance; GREEN real-ledger HTTP mocks, CLI exit codes and containment checks exit 0; correction confirmation PASS.
  Steps:
    1. Add public adapter tests with mocked network; capture RED.
    2. Reuse readCodexSettings and resolver; call sdd.py by stable relative URL and argv.
    3. Send only official evaluation HTTP with credential from environment; validate model, choice and probabilities.
    4. Confirm GREEN for timeout, invalid replies, HTTP failures, dedupe, cap and resume.

- [x] **T2.2** — Connect parent routing and installed setup guidance
  Owns: skills/senior-prompt-engineer/references/agent-handoff-contracts.md, references/shared/030-agent-assignment-matrix.md, README.md, AGENT_SETUP.md
  Needs: T2.1 (reads: exact adapter CLI and response contract)
  Acceptance: Parent has executable routing instructions; setup is explicitly read during updates; latest model verification and capability/activation limits are clear.
  Agent: graph-powers:debugger · Skill: none · Effort: mechanical
  TDD: not-applicable (documentation; behavior covered through adapter tests)
  CHECK: python3 .github/check_file_references.py
  EXPECT: exit 0 (silent success)
  EVIDENCE: File references exit 0; wiring 536 references, 0 unresolved; context 207918/208000; final independent READY.
  Steps:
    1. Document real CLI, minimal payload, duplicate behavior and no-model-comparison rule.
    2. Update existing setup entry without new services/agents; retain manual parent and personal overrides.
    3. Validate references and wiring.

### Phase 2 gate

- [x] **G2.1** — Wiring resolves
  CHECK: python3 .github/check_wiring.py
  EXPECT: 0 unresolved
  EVIDENCE: check_wiring exit 0; 536 routing references, 0 unresolved; 12 registered agents.

## Phase 3 — Distribution and proof [SEQUENTIAL]

- [x] **T3.1** — Regenerate bounded distribution and synchronize version
  Owns: CHANGELOG.md, package.json, .claude-plugin/plugin.json, .cursor-plugin/plugin.json, .grok-plugin/plugin.json, .codex-plugin/plugin.json, plugin.yaml, codex/native-agents/debugger.toml, codex/native-agents/evaluator.toml, codex/native-agents/explorer.toml, codex/native-agents/frontend-specialist.toml, codex/native-agents/librarian.toml, codex/native-agents/mobile-developer.toml, codex/native-agents/performance-optimizer.toml, codex/native-agents/project-planner.toml, codex/native-agents/security-reviewer.toml, codex/native-agents/skill-improver.toml, codex/native-agents/ui-ux-designer.toml, codex/native-agents/verification.toml, hermes/package/skills/content/codex/evaluate.mjs, hermes/package/skills/content/codex/install.mjs, hermes/package/skills/content/codex/lib.mjs, hermes/package/skills/content/codex/model-policy.json, hermes/package/skills/content/codex/model-policy.mjs, hermes/package/skills/content/schema/config.schema.json, hermes/package/skills/content/skills/planning/scripts/sdd.py, hermes/package/skills/content/skills/senior-prompt-engineer/references/agent-handoff-contracts.md, hermes/package/skills/content/references/shared/030-agent-assignment-matrix.md, hermes/package/plugin.yaml, hermes/package/PROVENANCE.json, hermes/package/skills/content/AGENT_SETUP.md, hermes/package/skills/content/kilo/model-policy.json
  Needs: T2.2 (reads: completed sources and documented call site)
  Acceptance: Twelve TOML and exact Hermes closure match sources and versions; no personal installation touched by generation.
  Agent: graph-powers:debugger · Skill: none · Effort: mechanical
  TDD: not-applicable (generated distribution)
  CHECK: bun hermes/install.mjs --check
  EXPECT: source manifest and package are current
  EVIDENCE: Native 12 roles exit 0; Hermes 39 registrations current exit 0; static gates 8-9, clone and version exit 0; 13 explicit Hermes outputs.
  Steps:
    1. Bump coordinated version and changelog.
    2. Generate native companions and Hermes; stop on unowned output.
    3. Run native, Hermes, version and budget gates.

- [x] **T3.2** — Verify and refresh the existing installed plugin
  Owns: docs/plans/2026-09-22-issue-27/verification.md
  Needs: T3.1 (reads: verified candidate package)
  Acceptance: All available declared local gates pass; authorized existing native plugin updated with backup and exact-byte proof; unsupported activation remains explicit.
  Agent: graph-powers:debugger · Skill: none · Effort: mechanical
  TDD: not-applicable (verification and existing installation update)
  CHECK: python3 .github/check_codex_native.py
  EXPECT: codex-native:
  EVIDENCE: Full 30-command inventory passed after documented rechecks; final READY; native plugin add and role emission exit 0; 9 installed source matches, 12 roles, 5 personal hashes preserved; client native guard probe PASS. Global config whole-file hash changed; no manual edit or stale-backup restore, limitation documented.
  Steps:
    1. Run the ordered verification inventory; report unavailable gates honestly.
    2. Review diff independently and resolve material findings.
    3. Back up affected installed files and update the existing registered local plugin; preserve global user settings.
    4. Record proof and separate paid runtime smoke/activation needing further authorization.

- [x] **T3.3** — Run separately authorized runtime smokes
  Owns: docs/plans/2026-09-22-issue-27/smoke.md
  Needs: T3.2 (reads: verified installed candidate and concrete smoke commands)
  Acceptance: Authorized Astra/Luna model-effort and one Jev evaluation prove actual runtime; replay produces no network. Without separate authorization record NOT RUN, never passed.
  Agent: graph-powers:verification · Skill: none · Effort: mechanical
  TDD: not-applicable (external runtime smoke)
  CHECK: python3 .github/check_codex_native.py
  EXPECT: codex-native:
  EVIDENCE: Three real Codex smokes exit 0; user then authorized credential setup. Jev HTTP 200, typesafe-ai/jev, choice inspect/probabilities 0.99 and 0.01; exactly one request; identical recorded replay with empty env and zero fetches. Native-economic/Ultra runtime remains optional and NOT RUN.
  Steps:
    1. Prepare exact synthetic requests and bounded commands after candidate exists.
    2. Obtain specific paid API/credential approval before live calls; static check alone never closes this task.
    3. Capture runtime identity, effort and response evidence or retain BLOCKED/NOT RUN.

### Phase 3 gate

- [x] **G3.1** — Preserve hook guarantees
  CHECK: python3 hooks/test_hooks.py
  EXPECT: EVERY GUARANTEE HELD
  EVIDENCE: hooks/test_hooks.py exit 0, EVERY GUARANTEE HELD after final runtime corrections.

## Regression watchlist

Explicit override precedence; scout roles; evaluator read-only/leaf; no Ultra leaves; legacy
consultation fallback; atomic cap/dedupe; native/clone parity; Kilo and personal settings unchanged.

## Verification and rollback

Use .claude/rules/verify-supplements.md ordered inventory. No typecheck/build/lint gate declared.
check_codex.py needs CI fixtures; Hermes proof is static only. Revert only issue-owned hunks and
restore affected installation backups; never reset the checkout or delete unrelated user data.

## Distribution ownership refinement

The additional user request to update AGENT_SETUP.md adds its existing Hermes projection and
`hermes/package/skills/content/kilo/model-policy.json`: the guide already references that policy
and the generated provenance records this exact dependency edge. The canonical Kilo policy and
installed Kilo settings are unchanged. The explicit Hermes output set is thirteen paths.

## Not yet specified

Jev account integration now passed after explicit credential authorization. Codex smokes and native
refresh passed. Optional native-economic/Ultra and Hermes runtime remain outside activation scope.
Windows CI has a confirmed baseline encoding failure outside this issue. No parent model change.
