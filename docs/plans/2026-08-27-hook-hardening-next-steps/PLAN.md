# Hook hardening next steps — Implementation plan

## Destination

Project-configured hook commands run only from a machine-approved config digest; model-facing hook
responses contain fixed summaries rather than checker output; Cursor identity is explicit in its
generated Stop command; agent-issued commits attempt the declared core gates under one bounded,
cache-aware runner; Windows CI records the current six-handler cost without activating a dispatcher.

## Inputs and boundaries

- Design authority: `docs/plans/2026-08-27-hook-hardening-next-steps/spec.md` (Gate 1: PASS).
- Baseline: `5ca2f2e` on `codex/codex-agent-model-routing`.
- Existing unrelated working-tree changes are preserved. In particular, generated manifests and
  `CHANGELOG.md` are merged in place, never restored from the baseline.
- This plan deliberately does not add telemetry, a dispatcher, Git-native hooks, staged-snapshot
  execution or new lifecycle registrations.
- Tier: L5. Implementation is delegated by disjoint ownership; overlapping test ownership is
  sequential through explicit dependencies.

## Regression watchlist

| # | Contract | Proof |
|---|---|---|
| W1 | Every hook remains fail-open for malformed input and unavailable tooling | `python3 hooks/test_hooks.py` |
| W2 | Untrusted or changed project config never launches an automatic command | trust tests in `hooks/test_hooks.py` |
| W3 | Stop blocks only an executed failing lint and never forwards its output | Stop tests in `hooks/test_hooks.py` |
| W4 | Core commit gates, legacy audit, combined timeout and cache obey the spec | commit tests in `hooks/test_hooks.py` |
| W5 | Cursor alone receives the explicit client marker and keeps loop limit five | `python3 .github/check_cursor.py` |
| W6 | Codex and Grok stay generated from the shared hook declaration | official generator checks |
| W7 | Benchmark selects exactly six handlers and reports valid JSON | benchmark smoke plus Windows job |
| W8 | Every shipped artefact has one version and the changelog names the behavior | version gate and JSON check |
| W9 | No machine path, dangling reference, portability defect or context inflation ships | repository static gates |

## Phase 1 — Trust boundary and fixed Stop output  [SEQUENTIAL]

- [x] **T1.1** — Add machine-local command trust and remove arbitrary Stop diagnostics
  Owns: hooks/command_trust.py, hooks/_config.py, hooks/stop_verify.py, hooks/ultracite.py, hooks/test_hooks.py
  Needs: none
  Agent: graph-powers:debugger · Skill: graph-powers:debugger · Effort: high
  CHECK: `python3 hooks/test_hooks.py`
  EXPECT: `EVERY GUARANTEE HELD`
  EVIDENCE: RED `ModuleNotFoundError: command_trust`, old diagnostic forwarding and payload-based Cursor inference; GREEN `EVERY GUARANTEE HELD`, `AST_OK`, `0 portability problem(s)`, `no home-directory paths`, task review PASS
  TDD: required
  Steps:
    1. RED: add focused cases for canonical Git-root resolution, external canonical-config symlink rejection, approve/status/revoke, digest invalidation, corrupt registry and every automatic consumer; run the suite and record the intended failures.
    2. GREEN: implement `command_trust.py` and the strict contained-config identity from the spec, keeping every read/write/permission failure untrusted and fail-open.
    3. RED: add prompt-injection, credential URL, Bearer, provider-token, PEM and control-text lint output; prove none of it reaches any Stop response field.
    4. GREEN: make Stop responses fixed, add `SKIP_UNTRUSTED`, recognize only `--graph-powers-client cursor`, and require the same trust decision before formatter execution.
    5. Run CHECK and the Python AST smoke for the owned hook modules.
  Risk: high (automatic shell execution and lifecycle response semantics)

### Phase 1 gate

- [x] **G1.1** — Trust and Stop contracts are green
  CHECK: `python3 hooks/test_hooks.py`
  EXPECT: `EVERY GUARANTEE HELD`
  EVIDENCE: `EVERY GUARANTEE HELD`; read-only task reviewer reported `T1.1 review: PASS`

## Phase 2 — Bounded pre-commit runner and attestation cache  [SEQUENTIAL]

- [x] **T2.1** — Extend the existing audit hook into the one declared core-gate runner
  Owns: hooks/_change_set.py, hooks/commit_audit_gate.py, hooks/test_hooks.py, schema/config.schema.json, hooks/hooks.json
  Needs: T1.1 (reads: the trust API, canonical config identity and shared test fixture)
  Agent: graph-powers:debugger · Skill: graph-powers:debugger · Effort: high
  CHECK: `python3 hooks/test_hooks.py`
  EXPECT: `EVERY GUARANTEE HELD`
  EVIDENCE: RED: the old audit-only path skipped core gates, reset independent 3-second budgets and let oversized Git capture grow without terminating its child. GREEN: fresh `python3 hooks/test_hooks.py` exits 0 with `EVERY GUARANTEE HELD`; direct tests cover fixed core order, enabled subsets, combined deadlines, trust-before-opt-in, legacy audit compatibility, bounded Git capture/child reap, length-framed fingerprints, staged/unstaged/untracked/config/command/executable invalidation, cache TTL/schema/size and exact hook-cache exclusion. AST, JSON, portability and diff checks also pass.
  TDD: required
  Steps:
    1. RED: add schema/default/order/opt-in, commit-versus-push, combined-timeout, cache and every fingerprint invalidation case before changing the runner.
    2. GREEN: add `gates.preCommit`, the legacy audit `cache` field and the 610-second outer allowance without adding a second lifecycle hook.
    3. GREEN: implement the versioned length-framed worktree fingerprint, bounded streaming and small atomic success cache in `_change_set.py`.
    4. GREEN: execute trusted core gates in fixed order, then the trusted legacy audit within one commit budget; emit only the fixed deny/skip contracts and cache only successful executions.
    5. Run CHECK, schema parse, hook-manifest parse and portability on the owned files.
  Risk: high (commit interception, cache correctness and timeout semantics)

### Phase 2 gate

- [x] **G2.1** — Commit runner and cache contracts are green
  CHECK: python3 hooks/test_hooks.py and python3 .github/check_placeholders.py
  EXPECT: EVERY GUARANTEE HELD and every placeholder declared
  EVIDENCE: `python3 hooks/test_hooks.py` exits 0 (`EVERY GUARANTEE HELD`); `python3 .github/check_placeholders.py` exits 0 (`143 artefacts scanned, every placeholder is a declared config key`).

## Phase 3 — Generated client identity and Windows evidence  [PARALLEL-SAFE]

- [x] **T3.1** — Generate the Cursor-only Stop client marker
  Owns: cursor/install.mjs, .github/check_cursor.py, hooks/hooks-cursor.json
  Needs: T1.1 (reads: exact `--graph-powers-client cursor` runtime contract)
  Agent: graph-powers:debugger · Skill: graph-powers:debugger · Effort: medium
  CHECK: bun cursor/install.mjs --emit-only and python3 .github/check_cursor.py
  EXPECT: generated artefact current; marker exactly once only on Cursor Stop; loop limit five
  EVIDENCE: RED: `python3 .github/check_cursor.py` rejected the stale generator because it accepted malicious marker and fake Stop-command probes. GREEN: `bun cursor/install.mjs --emit-only` writes the two generated paths; `python3 .github/check_cursor.py` exits 0 with 12 registrations, one exact final marker and loop limit 5. Negative probes reject a malicious marker and fake Stop command; the canonical manifest remains marker-free.
  TDD: required
  Steps:
    1. RED: teach `check_cursor.py` to require one exact marker on the Stop verifier and to reject it everywhere else; observe the stale generator failure.
    2. GREEN: append the marker in `cursor/install.mjs`, regenerate `hooks/hooks-cursor.json`, then run CHECK.
    3. Confirm `hooks/hooks.json` remains marker-free and no hand-maintained client list was introduced.
  Risk: medium (generated lifecycle wiring)

- [x] **T3.2** — Add a report-only cross-platform PreToolUse benchmark
  Owns: .github/benchmark_hooks.py, .github/workflows/ci.yml
  Needs: T2.1 (reads: final six-handler manifest and fixed fail-open subprocess contracts)
  Agent: graph-powers:performance-optimizer · Skill: graph-powers:performance-optimization · Effort: medium
  CHECK: `python3 .github/benchmark_hooks.py --warmups 1 --samples 3`
  EXPECT: valid JSON with `handlerCount` 6 and zero handler failures
  EVIDENCE: RED: the Windows job initially referenced a missing benchmark script and six-handler report contract. GREEN: `python3 .github/benchmark_hooks.py --self-test` exits 0 (`benchmark self-test: PASS`); smoke with `--warmups 1 --samples 3` emits valid JSON with `handlerCount` 6 and zero failures. The workflow also runs the hook suite and benchmark self-test on Ubuntu, macOS and Windows; `bun .github/check_workflows.mjs` and portability checks pass. Windows latency remains CI-only and report-only.
  TDD: required
  Steps:
    1. RED: add a Windows job invocation that expects the benchmark CLI and exact six-handler schema; observe that the script is absent.
    2. GREEN: implement the dependency-free temporary-Git-fixture benchmark with cold, warm-up, sample and sequential-chain measurements from `perf_counter_ns`.
    3. GREEN: make Windows fail only for script/schema/count/handler errors, never latency; print JSON to the job log and retain no runtime telemetry.
    4. Run CHECK and workflow parsing.
  Risk: medium (Windows process semantics; latency remains report-only)

### Phase 3 gate

- [x] **G3.1** — Cursor generation and benchmark evidence are sound
  CHECK: `python3 .github/check_cursor.py`, `python3 .github/benchmark_hooks.py --warmups 1 --samples 3`, and `bun .github/check_workflows.mjs`
  EXPECT: Cursor check passes, benchmark reports six handlers with zero failures, workflows parse
  EVIDENCE: Cursor checker, benchmark self-test/smoke and workflow parser all exit 0; report schema validates six handlers and zero failures, with no latency threshold.

## Phase 4 — Contract documentation and delivery channel  [SEQUENTIAL]

- [x] **T4.1** — Document the trust boundary and ship one synchronized patch version
  Owns: hooks/AGENTS.md, .claude/rules/hooks.md, references/shared/110-guardrails-index.md, CHANGELOG.md, package.json, .claude-plugin/plugin.json, .codex-plugin/plugin.json, .cursor-plugin/plugin.json, .grok-plugin/plugin.json
  Needs: T2.1 (reads: final trust, runner and cache behavior), T3.1 (reads: generated Cursor marker behavior), T3.2 (reads: report-only benchmark decision)
  Agent: graph-powers:debugger · Skill: none · Effort: medium
  CHECK: python3 .github/check_version_bump.py, python3 .github/check_file_references.py, and python3 .github/check_context_budget.py
  EXPECT: shipped change has a synchronized version bump; references resolve; context remains within budget
  EVIDENCE: All five package/plugin manifests are `1.12.2`; the official Codex, Cursor and Grok emitters complete successfully. Documentation names machine-local trust, fixed summaries, enabled declared core order, combined commit budget, push audit-only behavior, cache limits, client parity boundaries and deliberate non-activation. Version, file-reference, context/listing-budget, machine-path, portability and diff checks pass.
  TDD: not-applicable (documentation, changelog and manifest delivery metadata)
  Steps:
    1. Update the three existing hook authorities in place: trust approval, fixed output, agent-issued commit scope, cache semantics, Cursor marker, Codex schema-only confirmation and deliberate non-activation decisions.
    2. Prepend a changelog entry and bump the patch version in the canonical package/Claude manifest, then use existing generators or minimal merge-safe edits for all generated manifests.
    3. Preserve concurrent manifest/changelog content and verify all five version fields are identical.
    4. Run CHECK plus machine-path and listing-budget checks.
  Risk: medium (shared documentation and concurrently dirty generated manifests)

### Phase 4 gate

- [x] **G4.1** — Delivery metadata and contract documentation are consistent
  CHECK: python3 .github/check_version_bump.py and python3 .github/check_machine_paths.py
  EXPECT: version gate passes and no home-directory path reached a tracked file
  EVIDENCE: `python3 .github/check_version_bump.py` exits 0 (`53 shipped file(s) changed, version 1.11.1 -> 1.12.2`); `python3 .github/check_machine_paths.py` exits 0 (`no home-directory paths`).

## Fresh verification after Phase 4

The coordinator invokes `graph-powers-verify` after every implementation task and phase gate is
complete. A read-only `graph-powers:verification` agent returns W1–W9 evidence; it owns no file and
does not update this plan. The coordinator reads `REVIEW.md`, the root gate list and
`.claude/rules/verify-supplements.md`, then runs fresh commands rather than reusing implementation
output. Every repository-declared failure remains a failure. The final verdict is `VERIFIED`,
`VERIFIED-WITH-NOTES` or `NEEDS-WORK`; Windows latency itself remains **NOT CONFIRMED** locally and
is reported only by the CI job.

## Rollback

- Revoke the machine-local trust entry to stop every project-configured automatic command.
- Disable `gates.preCommit.enabled` or delete the disposable pre-commit cache to isolate the commit
  runner without weakening unrelated Git/destructive guardrails.
- Remove the Cursor generator transformation and regenerate its tracked artefact.
- Revert the shared runtime/schema/documentation/version slice as one change. No production, network,
  database or user-data migration exists.
