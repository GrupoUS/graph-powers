# Graph Powers audit — 2026-09-04

**Final outcome (2026-09-05): VERIFIED-WITH-NOTES.** The ten planned tasks are implemented locally
at version **1.19.2**, with independent writer/reviewer acceptance and all 25 declared checks passing.
Nothing was committed, published or installed into the operator's real environment. The initial
audit below records the pre-change evidence; the completed work is summarized first.

## Completed implementation

| Plan | Tasks / phase gates closed | Result |
|---|---|---|
| Installation | 3 / 7 | Strict CLI/dry-run, adopted-rule preservation, missing-artifact repair |
| Codex settings | 2 / 5 | Custom-home references and safe preservation of manual model/effort |
| Validation | 2 / 7 | Dot-relative path checks, narrow runtime exclusions, capture CI and 25-gate inventory |
| Context/routing | 3 / 7 | Conditional debug loads, correct perf resource route, capability prose and local release metadata |

The full declared gate batch passed **25/25 in 30.372 seconds** on this machine. Relevant checks:
675 hook assertions (including the separately authored concurrent hook correction), 14 client
regressions, 51 SDD tests, 12 file-reference tests, 15 capture tests, 11 eval-runner tests,
12 native companion roles, Cursor/Grok generation, and 38 registrations through the actual local
Hermes doctor. The changed final prose/manifest inputs were checked again after correction.
These are local results; remote CI, provider-backed sessions and other operating systems are not
reported as passed.

Debug's one-level estimated mandatory context decreased **59,276 -> 52,147 bytes**
(**7,129 bytes, about 12.0%**). The total command floor decreased **268,985 -> 261,858 bytes**.
Listing remains 10,143/10,752 characters. No ceiling was raised and no mode or safety check was removed.
This measures input bytes, not end-to-end model latency.

All six disk versions agree on 1.19.2 and are newer than HEAD's 1.19.1. The original expanded
Codex manifest formatting is preserved exactly; only its version differs from the pre-slice
snapshot. HEAD and the real Git index remain unchanged. Concurrent changes to hooks/_config.py
and hooks/test_hooks.py were preserved and are not attributed to this task.

**Known nonblocking note P02-T12-03:** ordinary native refresh preserves the correct runtime model
and effort, but its advisory policy-source comment can still say semantic-default. This has no
runtime effect and was explicitly deferred by the reviewer.

**Runtime adaptations:** only three child contexts were available. Registered writer and evaluator
roles were reused for distinct acceptance passes, with snapshot checks and no self-review by a
builder; newly isolated reviewer contexts were unavailable. At the final dispatch cap, the already
reserved evaluator checked the last sentence, signaled the parent to close phase evidence, then
performed the separate complete-plan acceptance pass in that same running call. All criteria were
reviewed; strict fresh-context Gauntlet isolation is not claimed. Workflow was unavailable, so each
verify-loop used its documented inline fallback. No counters were reset to escape a cap.

Execution ledgers and raw outputs are under the ignored .graph-powers/logs/sdd directories named
after the four plans. Every task and phase checkbox contains deciding evidence; no lease remains.

## Initial audit baseline

**Baseline:** commit `0a59d3a7c1b8d0ecede6d88a64a3a6107d4034a4`, version `1.19.1`, branch `main`.
The pre-existing formatting change in `.codex-plugin/plugin.json` was preserved.
Implementation order and atomic work orders: [roadmap](plans/2026-09-04-plugin-audit/ROADMAP.md).

## Scope and method

Inventory covered **327 tracked files, 3,488,908 bytes and 67,495 lines**. This is a complete
file inventory, not a claim of manual review of every line. Static checks traversed their declared
scopes; focused reading followed installation, generation, update, configuration, hook decisions,
task dispatch and validation. Historical audit reports and plans were context, not current contracts.

All work stayed local. Installation and removal probes used disposable homes and projects.
The dry-run/update probe intercepted Git with a recording stub: it proves that the installer
requests `git pull`; it did not run a real pull. No real installation, global setting, model
choice, commit, branch, index, remote or user file was changed. Initial discovery used no subagents, following the user's local preference. The user then explicitly
authorized the implementation phase with specialists and reviewers, as recorded above.

Local evidence lives in `.claude/audit/plugin-audit-2026-09-04/`:
`inventory.json`, `artifacts.json`, `baseline.json`, the per-gate logs,
`reproduce.py`, `reproductions.json`, `installation-matrix.json`,
`installed-state.json`, `relative-scan-probe.json`, and `benchmark.json`.
These are ignored audit state; the findings and work orders below remain understandable without it.

## What the plugin actually contains

| Surface | Current implementation | Result and boundary |
|---|---|---|
| Distribution | Git checkout and native manifests; private package metadata; no production build | Keep. A registry, packaging service or second distribution pipeline buys no demonstrated benefit. |
| CLI installation | `bin/graph-powers.mjs`; scope and client adapters | Testable locally; fix input/dry-run semantics first. Hermes has a separate native route, so absence from this CLI's hook-client targets is not a defect. |
| Codex projection | `codex/install.mjs`, `codex/native-plugin.mjs`, `codex/lib.mjs`, semantic policy JSON | Native and clone generation share the source. Repair preservation and completeness; keep both documented routes. |
| Cursor / Grok | `cursor/install.mjs`, `grok/install.mjs` | Existing emitted-artifact and additive-merge checks pass. Event asymmetries are intentional. |
| Hermes | `plugin.yaml`, `__init__.py`, `hermes/install.mjs`, one adapter skill | Five focused checks pass. Registers skills/commands/agent contracts; no native hook enforcement is claimed. |
| Configuration | `schema/config.schema.json` and `hooks/_config.py` | Keep one schema and one runtime reader. Global safety settings are sanitized, project autonomy overrides the global block. Some descriptive claims have drifted. |
| Hooks | 16 registrations, 15 registered scripts, 7 events; remaining Python modules are helpers/tests | 672 assertions pass. Imported modules are not orphans. Preserve fail-open behavior, trust and destructive guards. |
| Agents | 12 canonical Markdown roles and generated Codex companions | 12 register in the static gate. Read-only intent on Codex is behavioral in the generated contract, not a proven role sandbox. |
| Skills | 13 shared skill entrypoints; 9 eval files with 106 cases; Hermes has its additional adapter | All 13 shared skills pass quick validation. Eval case existence and runner tests are not proof of live routing quality. |
| Commands | 12 Markdown entrypoints; generated native Codex wrappers | Preserve modes; correct resource routing and condition context loads on actual use. |
| Planning / Gauntlet | One SDD engine, write lease, task grammar, bounded dispatch/consultation state | 51 tests pass. Keep the engine; do not add a second scheduler or ledger. |
| Workflows | `ultra-plan.js`, `ultra-verify.js` | Syntax, model policy, configured limits and oversized dry fixtures pass. Provider runtime behavior was not exercised. |
| Host templates/specs | `templates/`, root `DESIGN.md`, `PRODUCT.md`, `REVIEW.md` | These are host-project contracts, not plugin documentation. Preserve that boundary. |
| Docs/rules | Root rules, subtree rules, architecture, setup guide, verification supplement | Several current claims disagree with source code; narrow corrections are specified below. |
| CI/toolchain | Existing Python/Bun gates, hook runtime OS matrix, editor-only Oxc settings | Preserve declared runners. One existing test module is omitted from CI. No additional formatter, linter or production dependency is justified. |

## Installed state at the audit baseline

The native Codex cache is version **1.19.1**. All **225 compared source files** under agents,
skills, commands, hooks, references and client generators match this checkout byte for byte.
All 12 global companion roles are present. The legacy clone installation marker is absent,
and the user's hooks file contains zero Graph Powers legacy hook registrations.

There are 25 old shared-skill/command entries on disk. All 25 are explicitly disabled in the
native Codex configuration. Their presence is therefore **not evidence of active shadowing**.
Do not delete them or reinstall the plugin as part of this repository change.

Observed local tools: Codex CLI 0.153.3, Claude Code 2.1.261, Bun 1.4.0, Python 3.14.7.
These versions describe the inspected machine; they are not proposed model or tool upgrades.

## Validation baseline

The 24 initially recorded commands all exited zero; their combined wall time was **33.564 s**
on this machine. This is one local baseline, not a performance guarantee.

| Check | Observed result |
|---|---|
| `claude plugin validate .` | PASS |
| `python3 hooks/test_hooks.py` | 672 PASS assertions; EVERY GUARANTEE HELD |
| `python3 .github/test_hook_clients.py` | 11 regressions held |
| `python3 skills/planning/scripts/test_sdd.py` | 51 tests, OK |
| `python3 skills/skill-improve/scripts/test_run_evals.py` | 11 tests, OK |
| `python3 skills/skill-improve/scripts/test_capture_trigger_evals.py` | 15 tests, OK; emitted ERROR lines belong to negative fixtures |
| Hook AST and JSON gates | PASS |
| `bun .github/check_workflows.mjs` | PASS |
| `bun .github/check_codex_policy.mjs` | PASS |
| `python3 .github/check_codex_native.py` | 12 companion roles, native/clone parity |
| Oxc policy, portability, machine paths, placeholders | PASS |
| Wiring | 462 references checked, 0 unresolved; 12 agents accepted |
| File-reference gate and its 7 negative/positive tests | PASS, with the blind spot below |
| Listing and context budgets | PASS, with limited headroom below |
| CLI help, clone artifact, version gate | PASS; version gate compares committed refs, not arbitrary unstaged future changes |
| `python3 .github/test_hermes.py` | 5 checks, PASS |

Additional checks also passed: Cursor and Grok generation checks; all 37 agent/skill/command
frontmatters parsed; all 13 shared skills validated; all 54 non-audit Python source files parsed.
Temporary Codex installations passed `.github/check_codex.py` in user and project scopes
after two installs each: 12 roles, 17 hook entries including the injected third-party hook,
3 effort values, no unresolved placeholders, one instruction block. Temporary uninstall
preserved the third-party hook, unrelated skill directory and adopted project rules directory.

These checks do not include real Windows/macOS execution, real provider sessions, live trigger
captures, actual marketplace downloads, or Codex Desktop end-to-end hook behavior. The CI file
declares an OS matrix; declaration is not evidence that a remote run passed during this audit.

## Confirmed findings

### F01 — P1: update ignores dry-run

`bin/graph-powers.mjs:333` calls `gitUpdate(PLUGIN_ROOT)` before the normal dry-run path;
`gitUpdate` requests `git pull --ff-only` at line 321. The intercepted invocation
`--target codex --update --dry-run` exited zero and requested a pull.

**Minimal correction:** honor dry-run before any mutating update operation. Make the explicit
update check a dirty source before pulling, matching the already existing protection in
`hooks/auto_update.py:373`. Keep normal explicit updates and fast-forward-only behavior.
**Plan:** installation T1.1.

### F02 — P1: reinstall overwrites adopted project rules

`codex/install.mjs:779` and `:869` call unconditional `copyTree` for
`.codex/rules`; `codex/lib.mjs:139` replaces existing destination files.
Both user-scope project setup and legacy project-only setup replaced a custom
`execution.md` sentinel in the probe. This contradicts the documented adopted-file ownership.

**Minimal correction:** seed missing rule files only; never overwrite an existing adopted file.
Use one shared copy behavior rather than duplicating fixes in both call sites.
**Plan:** installation T2.1.

### F03 — P1: automatic companion regeneration discards manual models

`hooks/auto_update.py:502` invokes the native generator with only `--out`.
`codex/native-plugin.mjs:190` then uses default settings and line 234 writes all roles.
A role generated with the supported `--models standard=gpt-5.5` override lost that selection
on the subsequent default generation, exactly the generation form the updater invokes.

**Minimal correction:** preserve existing model/effort assignments on ordinary refresh; explicit
operator overrides remain authoritative. Do not infer a new model, use a project configuration as
a new global owner, or create a second preferences registry.
**Plan:** Codex settings T1.2.

### F04 — P2: same-version install does not detect missing role files

`codex/install.mjs:422` treats a complete marker plus matching hooks as completion;
`:694` skips regeneration. Removing a generated `debugger.toml` in a temporary install
and reinstalling at the same version returned `skipped: true`, leaving the role missing.

**Minimal correction:** verify the already recorded required artifacts before taking the
same-version shortcut. Preserve the cheap no-change path; do not hash the full tree on every setup.
**Plan:** installation T2.2.

### F05 — P2: custom CODEX_HOME leaves references pointing at the default home

`codex/install.mjs:396` honors a custom Codex home for writes, but `:406` always emits
the default home reference. Changing only CODEX_HOME changes the physical reference directory
while leaving the instruction reference unchanged.

**Minimal correction:** derive instruction references from the selected destination. Keep
portable default-home spelling when it is correct. No machine path enters a tracked artifact.
**Plan:** Codex settings T1.1.

### F06 — P2: live relative Markdown paths escape the file-reference gate

The negative lookbehind in `.github/check_file_references.py:19` excludes paths preceded
by a dot or slash. The probe detects a missing bare `skills/...` reference but ignores the
same missing path beginning with `../`. A bounded in-memory matcher extension exposes a real
stale path in `hooks/AGENTS.md:88`: its turbo helper still names the removed bun-verify skill.
`skills/AGENTS.md:77` has a related stale shorthand.

**Minimal correction:** recognize explicit dot-relative prefixes and test owner-relative resolution,
including paths with spaces in the containing directory. Correct the proven stale paths to the
existing debugger helper; retain historical-document exclusions.
**Plan:** validation T1.1.

### F07 — P2: unknown installer flags succeed silently

The argument handling at `bin/graph-powers.mjs:70` never rejects unknown options.
A dry-run with `--this-flag-does-not-exist` exited zero. A misspelled safety option can therefore
be silently ignored.

**Minimal correction:** validate supported flags, required values and incompatible operation
combinations before client discovery. Keep documented aliases and dry-run behavior.
**Plan:** installation T1.1, the same argument-to-operation boundary as F01.

### F08 — P2: debug routing contradicts the shared execution contract

`commands/debug.md:116` explicitly puts a read-only explorer in the foreground, whereas
`references/shared/070-parallel-agent-spawn.md:9` requires background inspection.
The command also eagerly loads the spawn/agent-assignment/autoresearch material before determining
whether a known one-file defect needs any of it (`commands/debug.md:10`).

**Minimal correction:** let the canonical tier rules choose delegation; load spawn-only references
only when dispatching and align read-only dispatch with the shared contract. Keep all debug modes,
root-cause investigation, tests and safety gates. Template labels in backend/auth modes resolve
through pack-guides; they were not classified as missing agents.
**Plan:** context/routing T1.1. Eager loading is a measured optimization opportunity; the
foreground contradiction is the concrete contract defect.

### F09 — P2: perf resource aliases point to the failure section

`commands/perf.md:64` routes resources/hooks/tests to section 6, which is
`## 6. Failures` at line 354. The implemented resource audit is section 2.0 at line 70.

**Minimal correction:** correct the route to the existing resource audit. Do not invent a new mode.
Add a narrow negative check that catches this exact mismatch.
**Plan:** context/routing T1.1.

### F10 — P2: current capability documentation disagrees with implementation

- `schema/config.schema.json:857` says native Codex caches are never replaced by the worker;
  `hooks/auto_update.py:589` explicitly updates that native route.
- `docs/ARCHITECTURE.md:255` promises generated role sandboxing;
  `.github/check_codex.py:111` explicitly rejects that unsupported role key.
- `agents/skill-improver.md:83` distributes a claim about one user's global matcher and asks
  every consumer to repair it. The canonical plugin manifest declares an unfiltered
  SubagentStart hook; a host-specific global override must be inspected, not assumed.
- The same architecture document says no automated eval exists, despite the eval runner and
  capture tests. Distinguish runner coverage from unmeasured live routing.
- Root/subtree descriptions and the verification supplement lag the Hermes and Oxc additions.
  The skill subtree still describes critical eval failures as non-blocking, contrary to the runner.

**Minimal correction:** replace stale claims with links to their current canonical contract.
Keep the known runtime limitations explicit. Do not expand the audit into a new documentation site
or rewrite historical reports.
**Plan:** context/routing T2.1; the validation plan owns the gate inventory update.

### F11 — P2: an existing capture regression suite is absent from CI

`skills/skill-improve/scripts/test_capture_trigger_evals.py` contains 15 passing local tests,
but `.github/workflows/ci.yml` never invokes it. The runner contract check is a different module.

**Minimal correction:** invoke the existing test file beside the existing eval-runner check and
align the local verification supplement. This adds a measured ~0.294 s local check, not a new test
framework or live provider job.
**Plan:** validation T1.2.

## Efficiency measurements and decisions

The existing one-level context estimator reports **268,985 / 270,000 bytes** of total command
floor, with only **1,015 bytes** of headroom. This is the sum across commands, not the cost of
every session. Debug alone is **59,276 bytes**. Listing cost is **10,143 / 10,752 characters**,
leaving 609 characters. Do not inflate either ceiling to make a change pass.

The six-handler PreToolUse benchmark used an isolated home, 3 warmups and 20 samples:
chain p50 **190.274 ms**, p95 **254.647 ms**, zero handler failures. These are observed
subprocess-chain timings, not a demonstrated end-to-end model latency cost. The benchmark's
timer includes process-wait behavior.

Prefer conditional context and fewer repeated instructions before a hook dispatcher.
No hook removal, parallel hook engine, persistent cache, new agent, database, queue, service or
provider abstraction is justified by this evidence. The source has a measured reason for retaining
the six processes. A dispatcher can be revisited only after an equivalent end-to-end benchmark
shows that process launch is the dominant remaining cost.

## Decisions, uncertainty and exclusions

- **Keep:** all five client routes, 12 agents, 13 core skills, 12 commands, both workflows, hook
  trust, fail-open handling, negative tests, manual model choices and structured phase execution.
- **Do not silently change:** `repairProjectAutonomy` intentionally turns selected explicit
  ask settings into allow settings on an autonomous install. This is a policy tradeoff, not an
  accidental omission. It needs an owner decision before changing the behavior; this roadmap does
  not weaken or rewrite permissions.
- **Do not delete:** disabled legacy skill copies, global config, historical plans, attribution or
  caller-visible compatibility routes. Disk presence alone is not a deletion authorization.
- **Independent review:** initially pending, subsequently completed for all plans and implementation
  waves. Reviewer-context reuse and the final two-stage reserved review are disclosed above.
- **Behavioral evaluation:** no new live model traces were purchased or fabricated. Future prompt
  changes need bounded real positive/negative traces, distinct from regex inspection.
- **Execution approval:** the supplied Gauntlet call initially routed to planning. The user then
  explicitly authorized completing the plans and executing the scoped local corrections; all four
  plans passed independent review before their writers.

## Delivery boundary

The requested local work is complete. Review the [completed roadmap](plans/2026-09-04-plugin-audit/ROADMAP.md)
and source diff. Publication, commit/push and refreshing the operator's actual installation remain
separate actions requiring authorization. The nonblocking provenance note above is visible rather
than silently treated as fixed.
