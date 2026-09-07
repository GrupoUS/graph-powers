# Predictable installation — implementation plan

**Date:** 2026-09-04 · **Branch:** main · **Baseline:** 0a59d3a7c1b8d0ecede6d88a64a3a6107d4034a4
**Tier:** L5
**Risk surface:** local installation ownership and CI/contracts; no live deployment
**Design authority:** [shared specification](../spec.md).
**Authorization:** user authorized completing the plans and applying the local corrections with Gauntlet; no commit, publication or global installation changes. Independent plan review precedes implementation.

## Destination

Complete N1, N2, N3; audit F01, F02, F04, F07. Every task's acceptance must be proved by the existing focused
runner and its new negative/positive fixtures where required. Preserve the functionality listed in
the shared specification. Stop at reviewed, unstaged changes.

## Reuse ledger

| Need | Existing asset | Decision |
|---|---|---|
| T1.1: Validate installer operations before side effects | bin/graph-powers.mjs | EXTEND existing owner and tests; no new subsystem |
| T2.1: Preserve adopted rules in both Codex installation scopes | codex/install.mjs | EXTEND existing owner and tests; no new subsystem |
| T2.2: Repair incomplete same-version global artifacts | codex/install.mjs | EXTEND existing owner and tests; no new subsystem |

## Regression watchlist

| Existing behavior | Proof command | Owner phase |
|---|---|---|
| Existing clone scopes install and uninstall their own artifacts | `python3 .github/test_hook_clients.py` | final phase |
| Native/clone generated policy remains equivalent | `python3 .github/check_codex_native.py` | final phase |

## Execution graph

T1.1: none  
T2.1: T1.1 (reads: the existing client fixture module with strict-operation regressions)  
T2.2: T2.1 (reads: the preservation behavior and temporary install fixtures)

Task order is sequential where files overlap. Independent tasks may share a writer lane in an
explicitly ordered package, but may never have concurrent writers. Ordering between sibling plans
is review focus, not a fabricated data dependency. Rebase this work order on any already accepted
sibling changes before editing common files.

## Dispatch matrix

| Task | Agent | Skill | Owns | Needs |
|---|---|---|---|---|
| T1.1 | graph-powers:debugger | graph-powers:debugger | bin/graph-powers.mjs, .github/test_hook_clients.py | none |
| T2.1 | graph-powers:debugger | graph-powers:debugger | codex/install.mjs, codex/lib.mjs, .github/test_hook_clients.py | T1.1 (reads: the existing client fixture module with strict-operation regressions) |
| T2.2 | graph-powers:debugger | graph-powers:debugger | codex/install.mjs, .github/test_hook_clients.py | T2.1 (reads: the preservation behavior and temporary install fixtures) |

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

- [x] **T1.1** — Validate installer operations before side effects
  Owns: bin/graph-powers.mjs, .github/test_hook_clients.py
  Needs: none
  Acceptance: Unknown flags and missing values fail before installation; update dry-run never requests pull or writes; explicit update refuses a dirty source and still fast-forwards a clean source.
  Agent: graph-powers:debugger · Skill: graph-powers:debugger · Effort: design
  TDD: required
  CHECK: python3 .github/test_hook_clients.py
  EXPECT: /hook client verifier: [0-9]+ regressions held/
  EVIDENCE: RED baseline UNKNOWN_EXIT 0 and UPDATE_DRY_PULL True; GREEN parent rerun: hook client verifier: 12 regressions held (exit 0); evaluator compliance/quality/integration PASS at snapshot 0464bb7.
  Steps:
    1. Read the argument parser, gitUpdate and the --update branch; compare the dirty-source check already present in hooks/auto_update.py.
    2. Add recording CLI/Git fixtures to the existing client test module. Observe RED for --update --dry-run requesting pull and an unknown flag exiting zero. Add missing-value, conflicting-operation and dirty-source cases with positive counterparts.
    3. Validate the currently documented option set before client discovery. Keep --help, --agent-setup, existing aliases and deliberate --setup-oxc-only behavior.
    4. Make update dry-run exit after reporting intent. For real updates, check status before pull and retain --ff-only and re-exec semantics.
    5. Observe GREEN for the focused module. Refactor only duplicated validation created by this patch; run CLI help and a real dry-run against a disposable project.
    6. Record exact outputs and changed paths; do not invoke update on the real checkout or install into the operator home.

### Phase 1 gate

- [x] **G1.1** — Focused boundary regression suite passes
  CHECK: python3 .github/test_hook_clients.py
  EXPECT: /hook client verifier: [0-9]+ regressions held/
  EVIDENCE: Parent focused check at snapshot 0464bb7: hook client verifier: 12 regressions held; exit 0.

- [x] **G1.2** — Existing wiring remains resolvable
  CHECK: python3 .github/check_wiring.py
  EXPECT: /0 unresolved/
  EVIDENCE: 462 routing references checked, 0 unresolved; 12 agents accepted; exit 0.

- [x] **G1.3** — Whitespace and conflict-marker diff checks pass
  CHECK: git diff --check
  EXPECT: empty stdout and exit 0
  EVIDENCE: git diff --check: empty stdout, exit 0.

The parent additionally compares actual changed paths against this phase's Owns union and records
the independent critic's compliance/quality verdict before advancing. No type-check or lint gate
is invented: this repository declares neither as a CI gate.

## Phase 2 — Integration and preservation [SEQUENTIAL]

- [x] **T2.1** — Preserve adopted rules in both Codex installation scopes
  Owns: codex/install.mjs, codex/lib.mjs, .github/test_hook_clients.py
  Needs: T1.1 (reads: the existing client fixture module with strict-operation regressions)
  Acceptance: A custom rule remains byte-identical through first setup and repeated setup in both scopes; absent template files are still seeded.
  Agent: graph-powers:debugger · Skill: graph-powers:debugger · Effort: design
  TDD: required
  CHECK: python3 .github/test_hook_clients.py
  EXPECT: /hook client verifier: [0-9]+ regressions held/
  EVIDENCE: RED sentinel overwritten; GREEN parent: hook client verifier: 13 regressions held, exit 0; evaluator compliance/quality/integration PASS at snapshot 69bd7e0; existing copyTree reused.
  Steps:
    1. Read installProject, installProjectOnlyLegacy and copyTree; identify the two adopted-rules callers and all consumers of the shared helper.
    2. Add a custom execution.md sentinel and an absent sibling rule in isolated user/project fixtures. Observe RED for the overwrite.
    3. Extend the existing copy helper minimally, or reuse its current skip argument with one shared adopted-rule operation. Only adopted rules get non-overwrite semantics; generated skills and agents still update.
    4. Keep existing files and symlinks untouched rather than following a destination into another owner. Test the adopted-file boundary without deleting real paths.
    5. Observe GREEN in both scopes and repeated installs; run the native parity gate to ensure no unintended generator drift.
    6. Keep uninstall preservation and the adopted manifest contract intact; record evidence.

- [x] **T2.2** — Repair incomplete same-version global artifacts
  Owns: codex/install.mjs, .github/test_hook_clients.py
  Needs: T2.1 (reads: the preservation behavior and temporary install fixtures)
  Acceptance: A missing recorded companion or skill prevents same-version skip and is repaired; an intact same-version install still skips without rewriting hooks.
  Agent: graph-powers:debugger · Skill: graph-powers:debugger · Effort: design
  TDD: required
  CHECK: python3 .github/test_hook_clients.py
  EXPECT: /hook client verifier: [0-9]+ regressions held/
  EVIDENCE: RED missing debugger role incorrectly skipped; GREEN parent: 13 regressions held, exit 0; missing role and SKILL.md repaired, intact hook bytes/mtime retained; evaluator PASS at snapshot 765aa69.
  Steps:
    1. Read globallyInstalled, plannedPaths, manifestBuilder and the early return in installGlobal.
    2. Add isolated same-version fixtures with a removed role file and missing skill entrypoint; observe RED because the installer currently skips them.
    3. Check required recorded artifact existence before claiming completion, using the current manifest and canonical source lists. Do not add a second registry or full-tree hashing.
    4. Keep unrelated/adopted paths outside the completion criterion; do not overwrite custom rules during repair.
    5. Observe GREEN for missing-file repair and intact-install skip. Include malformed/incomplete markers already covered by the module.
    6. Run the focused client and native parity checks; record no-change behavior and actual outputs.

### Phase 2 gate

- [x] **G2.1** — Focused boundary regression suite passes
  CHECK: python3 .github/test_hook_clients.py
  EXPECT: /hook client verifier: [0-9]+ regressions held/
  EVIDENCE: Parent focused suite: hook client verifier: 13 regressions held; exit 0.

- [x] **G2.2** — Existing wiring remains resolvable
  CHECK: python3 .github/check_wiring.py
  EXPECT: /0 unresolved/
  EVIDENCE: 462 routing references checked, 0 unresolved; 12 agents accepted; exit 0.

- [x] **G2.3** — Whitespace and conflict-marker diff checks pass
  CHECK: git diff --check
  EXPECT: empty stdout and exit 0
  EVIDENCE: git diff --check: empty stdout and exit 0.

The parent additionally compares actual changed paths against this phase's Owns union and records
the independent critic's compliance/quality verdict before advancing. No type-check or lint gate
is invented: this repository declares neither as a CI gate.

## Verification

- [x] **G2.5** — Existing complete hook guarantees hold at the final boundary
  CHECK: python3 hooks/test_hooks.py
  EXPECT: EVERY GUARANTEE HELD
  EVIDENCE: python3 hooks/test_hooks.py: EVERY GUARANTEE HELD; exit 0; log phase-final-1.log.

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

