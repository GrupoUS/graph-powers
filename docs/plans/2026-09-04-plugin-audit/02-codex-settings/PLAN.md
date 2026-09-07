# Preserve Codex destinations and operator model choices — implementation plan

**Date:** 2026-09-04 · **Branch:** main · **Baseline:** 0a59d3a7c1b8d0ecede6d88a64a3a6107d4034a4
**Tier:** L5
**Risk surface:** local installation ownership and CI/contracts; no live deployment
**Design authority:** [shared specification](../spec.md).
**Authorization:** user authorized completing the plans and applying the local corrections with Gauntlet; no commit, publication or global installation changes. Independent plan review precedes implementation.

## Destination

Complete N4, N5; audit F03, F05. Every task's acceptance must be proved by the existing focused
runner and its new negative/positive fixtures where required. Preserve the functionality listed in
the shared specification. Stop at reviewed, unstaged changes.

## Reuse ledger

| Need | Existing asset | Decision |
|---|---|---|
| T1.1: Resolve references from the active Codex home | codex/install.mjs | EXTEND existing owner and tests; no new subsystem |
| T1.2: Keep explicit model and effort choices across companion refresh | codex/native-plugin.mjs | EXTEND existing owner and tests; no new subsystem |

## Regression watchlist

| Existing behavior | Proof command | Owner phase |
|---|---|---|
| Canonical source agents still generate the declared default policies | `bun .github/check_codex_policy.mjs` | final phase |
| Native and clone permissions remain explicitly advisory where required | `python3 .github/check_codex_native.py` | final phase |

## Execution graph

T1.1: none  
T1.2: none

Task order is sequential where files overlap. Independent tasks may share a writer lane in an
explicitly ordered package, but may never have concurrent writers. Ordering between sibling plans
is review focus, not a fabricated data dependency. Rebase this work order on any already accepted
sibling changes before editing common files.

Before this slice starts, capture a working-tree TASK_BASE. Exclude pre-existing and concurrent
hunks in hooks/_config.py, hooks/test_hooks.py and .codex-plugin/plugin.json from attribution;
compare ownership and rollback against the snapshot rather than HEAD alone.

## Dispatch matrix

| Task | Agent | Skill | Owns | Needs |
|---|---|---|---|---|
| T1.1 | graph-powers:debugger | graph-powers:debugger | codex/install.mjs, .github/test_hook_clients.py | none |
| T1.2 | graph-powers:debugger | graph-powers:debugger | codex/native-plugin.mjs, codex/lib.mjs, .github/check_codex_native.py | none |

## Runtime budget and review

Use the configured caps from the schema/config, never a new literal allowance: 8 cumulative
dispatches per workflow, width 3, 12 tasks, 2 re-patches and 8 rounds per role in the resolved runtime (the schema default is 4).
Before each wave reserve the independent wave review, final review and final verify-loop route.
A capped correction stops with evidence; it cannot silently skip a critic or restart the budget.
No child spawns. Model/effort selection comes from registered roles, never a dispatch override.

## Risk

The shared spec owns the risk register and rollback principles. This slice uses temporary homes
for installer tests, preserves existing dirty changes and has no external effects. A positive
same-version/no-change test is as important as the new negative case.

## Phase 1 — Focused boundary corrections [SEQUENTIAL]

- [x] **T1.1** — Resolve references from the active Codex home
  Owns: codex/install.mjs, .github/test_hook_clients.py
  Needs: none
  Acceptance: All generated reference targets exist with a custom Codex home, including a spaced path; the default home retains its current portable spelling.
  Agent: graph-powers:debugger · Skill: graph-powers:debugger · Effort: design
  TDD: required
  CHECK: python3 .github/test_hook_clients.py
  EXPECT: /hook client verifier: [0-9]+ regressions held/
  EVIDENCE: RED custom HOME used default reference; GREEN parent 14 regressions held, exit 0; default/custom/project targets verified; evaluator compliance/quality/integration PASS at 0bdede1.
  Steps:
    1. Read codexPaths, installGlobal rewrites and the generated AGENTS block. Coordinate after installation-plan edits to these same files have completed.
    2. Add default-home and custom-home fixtures, including spaces and the environment override; observe RED when instructions still name the default directory.
    3. Derive referencesRef from the existing destination values, abbreviating the actual operator home only when correct.
    4. Keep project-scope references local and machine-specific generated outputs ignored; do not write a real global configuration or change model settings.
    5. Observe GREEN and test both install scopes. Refactor only the new repeated path derivation if necessary.
    6. Record the resolved temporary targets and parity check result without embedding local absolute paths in tracked docs.

- [x] **T1.2** — Keep explicit model and effort choices across companion refresh
  Owns: codex/native-plugin.mjs, codex/lib.mjs, .github/check_codex_native.py
  Needs: none
  Acceptance: Ordinary native companion refresh updates instructions while retaining existing model/effort assignments; explicit requested overrides win; an initial install still uses canonical defaults. During ordinary refresh, malformed or unsupported existing model/effort assignments exit nonzero before any destination file is changed.
  Agent: graph-powers:debugger · Skill: graph-powers:debugger · Effort: design
  TDD: required
  CHECK: python3 .github/check_codex_native.py
  EXPECT: /codex-native: 12 companion roles/
  EVIDENCE: RED quoted duplicate and JSON-only slash escape changed output; GREEN parent native checker 12 roles, exit 0; exact header/emitter round-trip and nondefault gpt-5.5/high proved; evaluator Important01/02 resolved, correction2, snapshot c3b1101. Minor provenance03 deferred.
  Steps:
    1. Read native install output generation, model-policy precedence and auto_update.generate_codex_companions. The real updater and global role files are observational only.
    2. Add a generated role with a supported nondefault model and effort, then run the ordinary --out refresh form. Observe RED for lost choices. Include explicit-override and no-existing-file positive cases, malformed/unsupported assignment fixtures, and unchanged-output assertions after failure.
    3. Keep the existing role file as the source of manual scalar model/effort assignments during ordinary refresh. Use the narrow emitted TOML shape; do not introduce a general configuration framework or second preferences file.
    4. Preserve explicit --config/--models precedence. If existing settings cannot be safely understood, exit nonzero before writing any destination file, preserving the full prior output directory byte-for-byte.
    5. Ensure generated tracked defaults remain reproducible and do not absorb operator settings. Verify the updater's unchanged generation call inherits the preservation behavior through the native generator gate; do not edit the concurrently modified hook test module.
    6. Observe GREEN, run policy parity and native generation checks, and record results. Do not select a new model for the user.

### Phase 1 gate

- [x] **G1.4** — Custom-home installation checks pass
  CHECK: python3 .github/test_hook_clients.py
  EXPECT: /hook client verifier: [0-9]+ regressions held/
  EVIDENCE: Parent: hook client verifier: 14 regressions held; exit 0.

- [x] **G1.1** — Focused boundary regression suite passes
  CHECK: python3 .github/check_codex_native.py
  EXPECT: /codex-native: 12 companion roles/
  EVIDENCE: Parent: codex-native: 12 companion roles, native/clone parity; exit 0.

- [x] **G1.2** — Existing wiring remains resolvable
  CHECK: python3 .github/check_wiring.py
  EXPECT: /0 unresolved/
  EVIDENCE: 462 routing references checked, 0 unresolved; exit 0.

- [x] **G1.3** — Whitespace and conflict-marker diff checks pass
  CHECK: git diff --check
  EXPECT: empty stdout and exit 0
  EVIDENCE: git diff --check empty stdout, exit 0.

The parent additionally compares actual changed paths against this phase's Owns union and records
the independent critic's compliance/quality verdict before advancing. No type-check or lint gate
is invented: this repository declares neither as a CI gate.

## Verification

- [x] **G1.5** — Existing complete hook guarantees hold at the final boundary
  CHECK: python3 hooks/test_hooks.py
  EXPECT: EVERY GUARANTEE HELD
  EVIDENCE: EVERY GUARANTEE HELD; full hook suite exit 0.

Run the applicable gates from root AGENTS.md and the verification supplement, plus the focused
watchlist. Final profile is Gauntlet's `/verify loop` with the documented single fallback when
the workflow is unavailable. Keep the lease until that verdict. Do not claim live trigger,
Desktop or cross-OS evidence from source inspection. Completion updates the task evidence,
reviews and project-local learning; it does not stage, commit or install globally.

## Rollback

Restore only this slice's changed files to the pre-slice snapshot, excluding pre-existing edits
and accepted sibling changes. The temporary fixture homes clean themselves up. Never run a blanket
reset or reinstall against the operator's real settings. Release only the matching SDD lease
after success or an explicitly recorded safe abort.

## Out of scope

Global installation, permission-policy changes, model upgrades, orphan deletion, new dependencies,
new schedulers, publication and git history changes. Reopen only with an explicit owner request.

## Not yet specified

No implementation-blocking fog remains in this bounded slice. Native provider/session behavior
outside the local fixtures remains unmeasured and is reported as such. Any newly discovered
independent defect belongs in the audit notes rather than silently expanding this plan.
