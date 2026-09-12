# Issue 25 — Concurrent session path leases

**Tier:** L4
**Design authority:** Issue 25 decision map; current user explicitly requests implementation,
completion comments and closure. No commit, push, worktree or installation is authorized.

## Destination

Independent sessions share a checkout with disjoint path leases. Only a live foreign ownership
overlap blocks a write or acquisition; reads and unclaimed paths remain free. Preserve G1–G3,
the opt-in escape, plan-review binding and per-run dispatch accounting.

## Decisions and reuse

Extend G4 and SDD rather than adding a hook or dependency. Use explicit session identity with a
documented run fallback, 45-minute leases, renewal and expired-lease pruning. Serialize only the
short check-and-create transaction with an OS-released advisory lock, never the duration of plan
execution. A terminated holder must not leave a permanent transaction lock. Update every lease
consumer, including dispatch and Gauntlet resume. Isolate progress by plan to avoid a shared-path
conflict. Preserve existing symlink protection and fail-open hook behavior.

## Phase 1 — Runtime and distribution [SEQUENTIAL]

- [x] **T1.1** — Implement concurrent leases and production-interface regressions
  Owns: hooks/graph_guardrails.py, hooks/test_hooks.py, skills/planning/scripts/sdd.py, skills/planning/scripts/test_sdd.py
  Needs: none
  Acceptance: Disjoint concurrent acquisitions and writes pass; foreign overlap denies with owner; expiry, heartbeat, release, malformed data, review resume and dispatch isolation are covered.
  Agent: graph-powers:debugger · Skill: planning · Effort: design
  TDD: required
  CHECK: python3 skills/planning/scripts/test_sdd.py
  EXPECT: OK
  EVIDENCE: RED disjoint acquisitions returned [0,2] and foreign hook claims allowed; GREEN parent 71 SDD tests OK and EVERY GUARANTEE HELD, exit 0. Wave review isolated oversized timestamp P2; regression RED/GREEN and fresh correction review PASS. Logs: .graph-powers/logs/issue-25/correction-gates/results.json.
  Steps:
    1. Add regression at the CLI or hook boundary and capture the expected RED.
    2. Extend existing lease producers and consumers, preserving admission and path safety.
    3. Run focused regressions, then both runtime suites for GREEN.

- [x] **T1.2** — Document identity and lifecycle and regenerate distribution
  Owns: commands/prime.md, skills/planning/references/phase-c-executing-plans.md, skills/planning/references/loop-engineering.md, references/shared/007-path-conventions.md, references/shared/110-guardrails-index.md, CHANGELOG.md, package.json, plugin.yaml, .claude-plugin/plugin.json, .codex-plugin/plugin.json, .cursor-plugin/plugin.json, .grok-plugin/plugin.json, hermes/package
  Needs: T1.1 (reads: final lease CLI and hook lifecycle)
  Acceptance: Resume and release preserve the acquisition session identity; commands match implementation; progress is plan-scoped; git-index concurrency residual is explicit; generated package matches canonical sources.
  Agent: graph-powers:debugger · Skill: none · Effort: mechanical
  TDD: not-applicable (documentation and generated distribution)
  CHECK: bun hermes/install.mjs --check
  EXPECT: source manifest and package are current
  EVIDENCE: Hermes generation/check exit 0: 39 registrations, source manifest and package are current. Static package proof and client checks pass at 1.20.8; WIP issue 24 preserved. Runtime Windows/installed clients remains unverified. Final review F25-01 extends ownership to commands/prime.md to preserve session in resume/status and final release; corrected with generated mirrors; final independent confirmation READY, no open findings.
  Steps:
    1. Update canonical lifecycle and guardrail documentation and increment version, preserving WIP issue 24.
    2. Regenerate Hermes from current sources and validate projections.

### Phase 1 gate

- [x] **G1.1** — Preserve hook guarantees
  CHECK: python3 hooks/test_hooks.py
  EXPECT: EVERY GUARANTEE HELD
  EVIDENCE: Parent final correction-gates/02-0.txt: EVERY GUARANTEE HELD, exit 0. Independent correction review PASS; no remaining runtime finding.

## Verification and rollback

Run the ordered inventory in .claude/rules/verify-supplements.md and independent diff review.
Preexisting WIP issue 24 is preserved. The untracked 12 MB yaml file already fails the clone
budget and must not be deleted. Another task subsequently staged it and renamed its working-tree
copy to yaml.ps; both that external index state and file remain outside this issue. Report this
separately; installed-client runtime is unverified.
Rollback only issue-25 additions; preserve the captured preexisting diff. No repository-wide reset.
