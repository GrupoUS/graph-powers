# Oxc + Zed toolchain — implementation plan

**Date:** 2026-08-28 · **Branch:** `main` · **Baseline:** `1ca980a`
**Tier:** L6 · **Risk surface:** harness hooks, cross-platform command execution, generated adapters and editor configuration
**Design authority:** user request in the current turn, validated against the official Oxc, Zed and TypeScript documentation

## Destination

Done when the repository has one local Oxc lint/format path, a single Zed TypeScript server declaration, an on-demand diagnostic setup command, no active references to the retired toolchain, and all declared repository gates pass without committing or publishing changes.

## Reuse ledger

| #   | Need                                                                  | Existing asset (`path:line`)                                     | Verdict | Why extending fails (NEW only)                                                                                                                                         |
| --- | --------------------------------------------------------------------- | ---------------------------------------------------------------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| N1  | Format only the edited source file                                    | `hooks/ultracite.py:82`                                          | EXTEND  | —                                                                                                                                                                      |
| N2  | Lint only changed JavaScript/TypeScript files at Stop                 | `hooks/stop_verify.py:113` and `_change_set.py:67`               | EXTEND  | —                                                                                                                                                                      |
| N3  | Preserve command trust, fail-open behavior and cross-platform parsing | `hooks/_config.py:624`, `hooks/command_trust.py`                 | EXTEND  | —                                                                                                                                                                      |
| N4  | Keep generated Codex companions aligned with source agents            | `codex/native-plugin.mjs:77`                                     | REUSE   | —                                                                                                                                                                      |
| N5  | Provide project setup guidance on demand                              | `commands/verify.md` as command frontmatter pattern              | NEW     | No existing command owns local tool/editor diagnostics; extending verification would make setup run heavy checks and violate the on-demand boundary.                   |
| N6  | Assert the Oxc/Zed contract in CI                                     | `.github/check_wiring.py` and `.github/check_file_references.py` | NEW     | The existing wiring/file checks do not inspect editor ownership or forbidden active tool references; a focused read-only policy check is the smallest direct consumer. |

## Regression watchlist

| #   | Existing behaviour that must still work                                                             | How to prove it                                                                                                                                   | Phase |
| --- | --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | ----- |
| W1  | PostToolUse formatting remains fail-open, trusted and single-file                                   | `python3 hooks/test_hooks.py` formatter cases                                                                                                     | 2     |
| W2  | Stop verifier skips clean trees, handles Unicode/rename/delete paths and never forwards diagnostics | `python3 hooks/test_hooks.py` Stop cases                                                                                                          | 2     |
| W3  | Commit, branch, push, protected-file and package-approval rails remain intact                       | `python3 hooks/test_hooks.py` and `python3 .github/test_hook_clients.py`                                                                          | 4     |
| W4  | Claude/Codex/Cursor/Grok generated surfaces stay synchronized                                       | `python3 .github/check_codex_native.py`, `bun .github/check_codex_policy.mjs`, `python3 .github/check_cursor.py`, `python3 .github/check_grok.py` | 4     |
| W5  | Markdown/JSON/Python/ESM repository gates still resolve every live reference                        | `python3 .github/check_wiring.py`, `python3 .github/check_file_references.py`, `python3 .github/check_portability.py`                             | 4     |

## Execution graph

```text
T1.1 policy/config/schema → T1.2 examples/Zed fixture → T1.3 setup command
T1.1 → T2.1 formatter hook → T2.2 changed-file lint hook → T2.3 hook tests
T1.1 → T3.1 shared references and commands → T3.2 stack detector and generated companion
T1.2 + T2.3 + T3.2 → T4.1 CI policy check → T4.2 complete verification
```

Edges carry these payloads: T1.2 reads the schema's command and editor contract; T1.3 reads the setup paths and package-manager rules; T2.1/T2.2 read the local-command and relevant-extension rules; T2.3 reads both hook interfaces; T3.1 reads the renamed shared reference; T3.2 reads the detector's command shape; T4.1 reads the committed example and active-file policy; T4.2 reads all prior evidence.

## Dispatch matrix

All tasks run inline in the main task because repository policy forbids unsolicited delegation. `skill-improve` is loaded for harness wiring; no task changes the generated companion by hand.

| Task | Agent | Skill         | Owns                                                                                                                             | Needs                                             |
| ---- | ----- | ------------- | -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| T1.1 | main  | skill-improve | `schema/config.schema.json`, `package.json`, `.oxlintrc.json`, manifests, versions                                               | none                                              |
| T1.2 | main  | skill-improve | `examples/`, `templates/zed/settings.json`                                                                                       | T1.1 — schema and Oxc command names               |
| T1.3 | main  | skill-improve | `commands/setup.md`                                                                                                              | T1.2 — example path and diagnostics               |
| T2.1 | main  | skill-improve | `hooks/ultracite.py`                                                                                                             | T1.1 — local format command and extensions        |
| T2.2 | main  | skill-improve | `hooks/stop_verify.py`                                                                                                           | T1.1 — local lint command and relevant extensions |
| T2.3 | main  | skill-improve | `hooks/test_hooks.py`                                                                                                            | T2.1/T2.2 — observable hook behavior              |
| T3.1 | main  | skill-improve | `references/`, `skills/debugger/`, `commands/`, `templates/rules/`, `.claude/rules/`, `README.md`, `AGENT_SETUP.md`, `AGENTS.md` | T1.1 — final vocabulary                           |
| T3.2 | main  | skill-improve | `bin/graph-powers.mjs`, `agents/skill-improver.md`, generated native companion                                                   | T1.1/T3.1 — detector and source policy            |
| T4.1 | main  | skill-improve | `.github/check_oxc_policy.py`, `.github/workflows/ci.yml`, `.github/check_machine_paths.py`                                      | T1.2/T2.3/T3.1 — committed contract               |
| T4.2 | main  | skill-improve | plan evidence only                                                                                                               | T4.1 — all final gates                            |

## Phase 1 — Config, schema, examples and setup [SEQUENTIAL]

- [x] **T1.1** — Make local Oxc commands and TypeScript 7/vtsls metadata the only current defaults
      Owns: `schema/config.schema.json`, `package.json`, `.oxlintrc.json`, `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, `.cursor-plugin/plugin.json`, `.grok-plugin/plugin.json`, `CHANGELOG.md`
      Needs: none
      Agent: main · Skill: skill-improve · Effort: design
      TDD: not-applicable (configuration contract is verified by JSON and policy gates)
      CHECK: `python3 -X utf8 -c "import json; [json.load(open(p, encoding='utf-8')) for p in ['schema/config.schema.json','package.json','.claude-plugin/plugin.json','.codex-plugin/plugin.json','.cursor-plugin/plugin.json','.grok-plugin/plugin.json']]; print('config JSON OK')"`
      EXPECT: `config JSON OK`
      EVIDENCE: config JSON gate passed; `package.json` declares Oxfmt 0.65.0+, Oxlint 1.80.0+ and TypeScript 7.0.2+; policy checker passed.

- [x] **T1.2** — Add the portable Zed project settings example with one semantic server, one linter and one formatter
      Owns: `examples/config.bun.json`, `examples/config.astro.json`, `examples/config.monorepo.json`, `templates/zed/settings.json`
      Needs: T1.1 (reads the schema's command vocabulary and package-manager boundary)
      Agent: main · Skill: skill-improve · Effort: design
      TDD: not-applicable (static examples are covered by the policy checker)
      CHECK: `python3 -X utf8 -c "import json; d=json.load(open('templates/zed/settings.json', encoding='utf-8')); assert d['languages']['TypeScript']['language_servers']==['oxlint','vtsls']; assert d['languages']['TypeScript']['formatter']=={'language_server':{'name':'oxfmt'}}; print('Zed example contract OK')"`
      EXPECT: `Zed example contract OK`
      EVIDENCE: `Zed example contract OK`; `.github/check_oxc_policy.py` passed with one vtsls server, Oxlint diagnostics and the Oxfmt language-server formatter for all six configured Zed language entries; JSX is covered by JavaScript.

- [x] **T1.3** — Add the on-demand setup command that diagnoses tools and suggests local installation without writing
      Owns: `commands/setup.md`
      Needs: T1.2 (reads the committed Zed example and diagnostic checks)
      Agent: main · Skill: skill-improve · Effort: design
      TDD: not-applicable (command is an instruction surface; wiring and content checks cover it)
      CHECK: `python3 .github/check_wiring.py`
      EXPECT: `0 unresolved`
      EVIDENCE: `check_wiring.py` passed with 449 references and 0 unresolved; `node bin/oxc-setup.mjs --help` passed without changing user settings.

### Phase 1 gate

- [x] **G1.1** — T1.1–T1.3 acceptance checks pass
      CHECK: rerun the three Phase 1 CHECK commands
      EXPECT: `Zed example contract OK`
      EVIDENCE: config JSON, Zed example contract and wiring checks passed; no unresolved reference was reported.
- [x] **G1.2** — the repository schema and examples remain valid JSON
      CHECK: `python3 -X utf8 -c "import json,glob; [json.load(open(p, encoding='utf-8')) for p in glob.glob('examples/*.json')]; print('examples JSON OK')"`
      EXPECT: `examples JSON OK`
      EVIDENCE: recursive JSON gate passed with `JSON OK`.
- [x] **G1.3** — no out-of-scope paths changed in Phase 1
      CHECK: `git diff --name-only`
      EXPECT: only paths listed in T1.1–T1.3
      EVIDENCE: final diff inventory was reviewed against the phase ownership matrix; unrelated user-owned `.oxfmtrc.json` remains untracked and was not modified or removed.

## Phase 2 — Hook behavior and regression tests [SEQUENTIAL]

- [x] **T2.1** — Restrict PostToolUse formatting to local Oxfmt on supported edited files
      Owns: `hooks/ultracite.py`
      Needs: T1.1 (reads local command and Oxfmt extension rules)
      Agent: main · Skill: skill-improve · Effort: mechanical
      TDD: required
      CHECK: `python3 hooks/test_hooks.py`
      EXPECT: `an installed formatter is actually invoked`
      EVIDENCE: `hooks/test_hooks.py` passed; formatter cases prove one trusted local Oxfmt invocation per supported edited file and no check-and-write path.

- [x] **T2.2** — Restrict Stop linting to local Oxlint on changed relevant files, with no full-tree run
      Owns: `hooks/stop_verify.py`
      Needs: T2.1 (reads the single-file command invocation and trust/fail-open conventions)
      Agent: main · Skill: skill-improve · Effort: design
      TDD: required
      CHECK: `python3 hooks/test_hooks.py`
      EXPECT: `changed-only lint receives only relevant paths`
      EVIDENCE: `hooks/test_hooks.py` passed; changed-file, clean-tree, rename/delete and interactive type-aware-Oxlint cases are covered.

- [x] **T2.3** — Update hook tests for Oxc-only commands, changed-file filtering and forbidden interactive type analysis
      Owns: `hooks/test_hooks.py`
      Needs: T2.1/T2.2 (reads the final hook behavior)
      Agent: main · Skill: skill-improve · Effort: design
      TDD: required
      CHECK: `python3 hooks/test_hooks.py`
      EXPECT: `EVERY GUARANTEE HELD`
      EVIDENCE: `hooks/test_hooks.py` exited 0 with `EVERY GUARANTEE HELD`, including the explicit Stop typed-Oxlint regression.

### Phase 2 gate

- [x] **G2.1** — all hook tests pass with real changed-file assertions
      CHECK: `python3 hooks/test_hooks.py`
      EXPECT: `EVERY GUARANTEE HELD`
      EVIDENCE: `python3 -X utf8 hooks/test_hooks.py` exited 0 and reported `EVERY GUARANTEE HELD`.
- [x] **G2.2** — hook syntax parses
      CHECK: `python3 -X utf8 -c "import ast,glob; [ast.parse(open(p, encoding='utf-8').read()) for p in glob.glob('hooks/*.py')]; print('hook AST OK')"`
      EXPECT: `hook AST OK`
      EVIDENCE: Python AST gate exited 0 with `hook AST OK`.
- [x] **G2.3** — no out-of-scope paths changed in Phase 2
      CHECK: `git diff --name-only`
      EXPECT: only hook files and plan evidence are changed
      EVIDENCE: final diff inventory was reviewed against the phase ownership matrix; no unrelated tracked path was introduced.

## Phase 3 — Shared guidance and generated adapters [SEQUENTIAL]

- [x] **T3.1** — Rewrite active guidance, safety notes and command references around Oxc, Oxfmt, vtsls and Zed
      Owns: `references/`, `skills/debugger/`, `commands/`, `templates/rules/`, `.claude/rules/`, `README.md`, `AGENT_SETUP.md`, `AGENTS.md`
      Needs: T2.3 (reads the behavior the guidance must describe)
      Agent: main · Skill: skill-improve · Effort: design
      TDD: not-applicable (documentation is checked by active-reference policy and wiring gates)
      CHECK: `python3 .github/check_oxc_policy.py`
      EXPECT: `TypeScript 7/Oxc/Zed policy OK`
      EVIDENCE: `.github/check_oxc_policy.py` passed with `TypeScript 7/Oxc/Zed policy OK`; active guidance uses the canonical shared reference and documents the TS6 programmatic-API boundary.

- [x] **T3.2** — Replace legacy stack inference and regenerate the native skill-improver companion from source
      Owns: `bin/graph-powers.mjs`, `agents/skill-improver.md`, `codex/native-agents/skill-improver.toml`
      Needs: T3.1 (reads the final shared reference path and vocabulary)
      Agent: main · Skill: skill-improve · Effort: design
      TDD: not-applicable (generator and companion parity gates are the proof)
      CHECK: `python3 .github/check_codex_native.py`
      EXPECT: `0 drift`
      EVIDENCE: `check_codex_native.py` passed with 12 companion roles and manifest version 1.13.0; generator and companion remain aligned.

### Phase 3 gate

- [x] **G3.1** — active editor and runtime surfaces have no retired-tool wiring
      CHECK: rerun T3.1's policy checker and inspect the documented rejection references separately
      EXPECT: `TypeScript 7/Oxc/Zed policy OK`
      EVIDENCE: policy checker passed; remaining Oxfmt/legacy strings are confined to rejection guards, compatibility filenames or historical/review text, not active formatter wiring.
- [x] **G3.2** — shared references and generated companions resolve
      CHECK: `python3 .github/check_wiring.py && python3 .github/check_file_references.py && python3 .github/check_codex_native.py`
      EXPECT: `0 unresolved`
      EVIDENCE: wiring passed with 449 references and 0 unresolved; file-reference and native-companion checks also exited 0.
- [x] **G3.3** — no out-of-scope paths changed in Phase 3
      CHECK: `git diff --name-only`
      EXPECT: only paths listed in T3.1–T3.2 and the plan
      EVIDENCE: final diff inventory was reviewed against the phase ownership matrix; no unrelated tracked path was introduced.

## Phase 4 — Policy, CI and final verification [SEQUENTIAL]

- [x] **T4.1** — Add a read-only Oxc/Zed policy checker and run it in CI
      Owns: `.github/check_oxc_policy.py`, `.github/workflows/ci.yml`, `.github/check_machine_paths.py`
      Needs: T1.2/T2.3/T3.1 (reads the final committed contract)
      Agent: main · Skill: skill-improve · Effort: design
      TDD: required
      CHECK: `python3 .github/check_oxc_policy.py`
      EXPECT: `Oxc/Zed policy OK`
      EVIDENCE: `.github/check_oxc_policy.py` exited 0 with `TypeScript 7/Oxc/Zed policy OK`; the checker is wired as a CI step in `.github/workflows/ci.yml`.

- [x] **T4.2** — Run every declared validator and record the compatibility boundary
      Owns: `docs/plans/2026-08-28-oxc-zed-toolchain/PLAN.md`
      Needs: T4.1 (reads final policy and CI wiring)
      Agent: main · Skill: skill-improve · Effort: mechanical
      TDD: not-applicable (final verification task)
      CHECK: `python3 hooks/test_hooks.py && git diff --check`
      EXPECT: `EVERY GUARANTEE HELD`
      EVIDENCE: complete local validator matrix exited 0; the compatibility boundary records the local TypeScript 7 package, bundled-compatible vtsls, no-install launchers, and unavailable live Zed/Vitest target measurements.

### Phase 4 gate

- [x] **G4.1** — policy checker, hook suite, JSON, portability, wiring and generated adapters pass
      CHECK: `python3 .github/check_oxc_policy.py && python3 hooks/test_hooks.py && python3 .github/check_portability.py && python3 .github/check_wiring.py && python3 .github/check_file_references.py && python3 .github/check_codex_native.py && git diff --check`
      EXPECT: `Oxc/Zed policy OK`
      EVIDENCE: all listed commands exited 0; policy, hook, JSON, portability, wiring, file-reference, native-companion and diff-check gates are green.
- [x] **G4.2** — all remaining CI validators pass or are explicitly reported unavailable
      CHECK: run the commands listed in `.github/workflows/ci.yml`
      EXPECT: every executed command exits 0
      EVIDENCE: declared local CI validators exited 0, including client posture, workflow, Codex policy/native, budgets, clone, placeholders, version and plugin validation; live CI, Zed binary and a Vitest application were unavailable locally.
- [x] **G4.3** — no out-of-scope paths changed
      CHECK: `git status --short`
      EXPECT: only planned tracked files are modified or deleted; existing staging is preserved
      EVIDENCE: `git status --short` was reviewed; tracked changes are within the implementation scope, `.oxfmtrc.json` is preserved as pre-existing untracked user state, and no commit or push was performed.

## Verification

- Run the complete command list declared by `.github/workflows/ci.yml`, including client, workflow, policy, portability, budget, wiring, clone and generated-adapter checks.
- Run the focused policy checker for active runtime/editor wiring; review rejection examples and historical records separately so they are not mistaken for live providers.
- Run `python3 -X utf8 -c` probes for tool presence, versions, package manager and Zed project settings; report absent local binaries instead of installing them.
- Check the TypeScript 7/vtsls boundary: the local TypeScript 7 package is the compiler gate, while vtsls uses its bundled compatible SDK; do not point vtsls at the TypeScript 7 `lib` directory.
- Measure hook invocation count and elapsed time with the existing test fixtures where possible. Do not claim memory or Zed startup improvements without a real target project and installed tools.

## Rollback

- Phase 1: restore the changed config/schema/example/setup files from the working-tree diff; remove the project example and return command names to the prior declared contract only if the user explicitly chooses that older architecture.
- Phase 2: restore the two hook modules and test fixture changes; the existing command-trust and fail-open rails remain the safety fallback.
- Phase 3: restore shared guidance and regenerate native companions from the restored source agent; never edit the generated file independently.
- Phase 4: remove the new policy-check CI step and checker if the policy is abandoned; preserve unrelated staging and do not rewrite history.
- No machine-global installation, commit, push, merge or machine-global Zed change is part of this plan.

## Out of scope

- Installing packages or editing any user/global Zed settings; trigger: the operator explicitly runs the printed package-manager command or applies the project example.
- Replacing the TypeScript server with a different provider; trigger: a later request chooses an editor/server compatible with TypeScript 7.
- Adding a watcher, daemon, global cache or new hook architecture; trigger: measured evidence from a target project proves the simple changed-file path insufficient.
- Migrating unrelated Python, Go or Rust project toolchains; trigger: a separate project-specific configuration request.
- Commit, push, merge, release or branch changes; trigger: explicit authorization in a later turn.

## Not yet specified

No fog: the path is closed. The only external compatibility result is an evidence-backed blocker recorded in the setup/report, not an invented fallback.

## Risk

| #   | Risk                                                                      | Score | Mitigation                                                                                                                                       |
| --- | ------------------------------------------------------------------------- | ----: | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| R1  | Stop invokes a package-script wrapper with unsafe or empty path arguments |     6 | append only shell-quoted changed paths, skip non-relevant files, preserve trust/fail-open and add fixture assertions                             |
| R2  | Zed silently launches a second TypeScript/lint/format provider            |     6 | committed settings use explicit server/formatter arrays and a CI policy checker                                                                  |
| R3  | vtsls is pointed at the incompatible TypeScript 7 SDK                     |     9 | setup preserves explicit user settings, configures vtsls to use its bundled compatible SDK, and keeps TypeScript 7 visible for the compiler gate |
| R4  | Generated Codex companion drifts from its source                          |     4 | regenerate through the canonical generator and run the parity gate                                                                               |
| R5  | Documentation or CI retains an active retired-tool reference              |     6 | negative search plus policy checker in CI; historical changelog entries remain clearly historical                                                |

### ADR: one local Oxc path, explicit Zed ownership

**Context:** The old setup duplicated lint/format/type-server responsibilities and used launchers that could fetch packages.
**Options:** A) keep generic global/fetching fallbacks / B) use project-local Oxc commands and explicit Zed ownership.
**Decision:** B, because it minimizes processes and makes the package lockfile the version owner.
**Consequences:** Python and other non-JS projects retain their declared native tools; JS/TS projects get one Oxc path, while vtsls uses its bundled compatible SDK and TypeScript 7 remains the explicit compiler gate.
