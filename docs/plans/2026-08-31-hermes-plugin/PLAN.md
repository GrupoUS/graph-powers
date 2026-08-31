# Hermes native plugin — implementation plan

**Date:** 2026-08-31 · **Branch:** `codex/gauntlet` · **Baseline:** `b00d038`  
**Tier:** L6 · **Risk surface:** `ci`, `env`, and public client integration  
**Design authority:** [spec.md](spec.md)

## Destination

The repository root is a native Hermes plugin. One runtime directory scan projects canonical
skills, commands, and agents into Hermes-qualified names; a fifth generator owns the Hermes
manifest/check contract; verification and docs state that Claude hooks are not enforced there.

## Reuse ledger

| # | Need | Existing asset | Verdict | New work |
|---|---|---|---|---|
| 1 | Native entrypoint and skill registration | `__init__.py` plus Hermes `register_skill` contract | EXTEND | Add commands, collision checks, and registration evidence |
| 2 | Hermes manifest generation | `.claude-plugin/plugin.json` and existing client generators | NEW | Add `hermes/install.mjs` with deterministic check/write modes |
| 3 | Client verifier | `bin/verify-hook-clients.py` | EXTEND | Add Hermes static/Doctor route and explicit missing-runtime status |
| 4 | Generated-surface drift checks | `.github/check_codex_native.py` pattern | EXTEND | Check Hermes generator and source-derived registration set |
| 5 | Clone/version gates | `.github/check_clone.py`, `.github/check_version_bump.py` | EXTEND | Require Hermes files and compare `plugin.yaml` version |
| 6 | Client guidance | `README.md`, `AGENT_SETUP.md`, `docs/ARCHITECTURE.md` | EXTEND | Add fifth-client path and remove manual adapter/symlink guidance |
| 7 | CI runtime gate | `.github/workflows/ci.yml` | EXTEND | Run static checks; run Doctor when Hermes exists, otherwise say SKIPPED explicitly |

## Regression watchlist

| # | Existing behavior | Proof | Phase |
|---|---|---|---|
| 1 | Claude remains the canonical source and all existing clients stay synchronized | Existing client/generator gates and version check | 4 |
| 2 | Native Hermes registration remains read-only and hook-free | Fake context test plus Doctor output | 3 |
| 3 | No command/skill/agent name silently shadows another | Registration-plan collision test | 3 |
| 4 | Verifiers never mutate client state | Source review plus existing verifier tests | 3 |
| 5 | Missing Hermes binary is visible and not reported as PASS | CI branch output and verifier test | 4 |
| 6 | Existing portability and wiring rules remain green | Repository gate suite | 5 |

## Pre-mortem

| Failure mode | Early signal | Mitigation |
|---|---|---|
| Manifest drifts from Claude metadata | `hermes/install.mjs --check` reports stale `plugin.yaml` | Generate from `.claude-plugin/plugin.json`; gate the exact rendered text |
| A new command is omitted | Registration-plan count/set differs from `commands/` | Directory scan plus deterministic collision failure |
| Hermes hooks are accidentally claimed | `provides_hooks` or docs say enabled | Dedicated posture assertion and `NOT ENFORCED` wording |
| CI reports a false runtime PASS | Hermes binary absent but job says green runtime | Print explicit `SKIPPED` and keep static checks separate |
| Upstream scanner blocks the Git install | Install exits with dangerous verdict | Preserve scanner; record blocker and test Doctor/install with scan disabled only as a diagnostic |

## Execution graph

`T1 → G1 → T2 → G2 → T3a/T3b/T3c → G3 → T4 → G4 → T5`

- `T1` is the test-pressure/spec gate; no implementation edits precede it.
- `T2` is the Hermes generator/entrypoint seam and must pass before verifier work.
- `T3a`, `T3b`, and `T3c` own disjoint file families and run in one batch.
- `T4` is documentation/CI/version integration after behavior is proven.
- `T5` is the parent-owned final gate and runtime evidence pass.

## Phase 1 — RED contract

- [ ] **T1 — Add failing Hermes pressure tests**
  - **Owns:** `.github/test_hermes.py`
  - **CHECK:** `python3 -X utf8 .github/test_hermes.py`
  - **EXPECT:** RED against baseline because commands, generator, and Hermes verifier route are absent
  - **Acceptance:** tests assert the desired source-derived names, manifest parity, collision behavior, and explicit missing-runtime posture

### Gate G1

- [ ] Baseline failures are observed and captured before implementation.

## Phase 2 — Native projection

- [ ] **T2 — Implement Hermes generator and directory-driven registration**
  - **Owns:** `hermes/install.mjs`, `__init__.py`, `plugin.yaml`, `hermes/skills/graph-engineering/SKILL.md`
  - **CHECK:** `bun hermes/install.mjs --check` and `python3 -X utf8 .github/test_hermes.py`
  - **Acceptance:** manifest is generated from Claude metadata; all skills, command stems, and `agent-*` contracts have deterministic registrations; no hook/tool registration is present

### Gate G2

- [ ] Generator check and focused Hermes tests are green; Doctor is run when available.

## Phase 3 — Disjoint gates and verifier

Run one writer per path family in a single batch:

| Task | Agent | Owns | Deliverable |
|---|---|---|---|
| T3a | verifier implementer | `bin/verify-hook-clients.py` | Static registration/Doctor verifier |
| T3b | repository-gates implementer | `.github/check_clone.py`, `.github/check_version_bump.py`, `.github/check_wiring.py` | Hermes clone/version/wiring coverage |
| T3c | CI implementer | `.github/workflows/ci.yml` | Explicit runtime gate |

- **CHECK:** focused scripts for each owned family plus `.github/test_hermes.py`.
- **Acceptance:** no verifier writes; all missing-runtime states are visible; generated drift fails.

### Gate G3

- [ ] Focused verifier, clone/version/wiring, generator, and CI syntax checks are green.

## Phase 4 — Human-facing projection

- [ ] **T4 — Update setup, architecture, README, changelog, and synchronized versions**
  - **Owns:** `AGENT_SETUP.md`, `README.md`, `docs/ARCHITECTURE.md`, `CHANGELOG.md`, `package.json`, `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, `.cursor-plugin/plugin.json`, `.grok-plugin/plugin.json`
  - **CHECK:** documentation/reference gates, JSON validation, version checker
  - **Acceptance:** Hermes is the fifth client; no manual `~/.hermes` copy/symlink is prescribed; hook posture is `NOT ENFORCED`; all manifests share one version.

### Gate G4

- [ ] README/setup/architecture, version, JSON, file-reference, and portability checks are green.

## Phase 5 — Final verification

- [ ] **T5 — Run the declared and repository gates**
  - **Owns:** no files; parent only
  - **CHECK:** project gate list plus `hermes plugins doctor . --ci`, explicit verifier, and the clean-home install probe when runtime/security policy permits
  - **Acceptance:** return `VERIFIED-WITH-NOTES` only if every runnable declared gate passes and the external scanner blocker is explicitly recorded; otherwise `NEEDS-WORK`.

## Rollback

Revert only this plan's Hermes generator, registration, verifier, docs, CI, and version changes. Do
not alter the existing Gauntlet files or any user Hermes home.
