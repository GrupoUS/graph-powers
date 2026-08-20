# Planning upgrade — one task format, evidence, rolling dispatch

**Date:** 2026-08-20 · **Branch:** `feat/graph-engineering-upgrade` · **Baseline:** `9538ff0`
**Tier:** L4 · **Risk surface:** none of `auth|payment|PII|schema|env|ci` · **Version:** 1.4.1 → 1.5.0

> This file is also the first artefact written in the grammar it introduces: one plan is one
> directory, tasks are checkboxes carrying `Owns` / `Needs` / `CHECK` / `EXPECT` / `EVIDENCE`, and a
> checked box whose evidence still reads `pending` is unmet.

## Destination

Done when all six hold, each provable by a command:

1. `/plan`'s context floor is below 55,000 bytes, from 67,731, with no capability removed.
2. One plan format: the template in `phase-b` and the contract in `commands/plan.md` name the same
   seven sections.
3. A task carries `Owns:`, `Needs:` with a named payload, and `CHECK` / `EXPECT` / `EVIDENCE`;
   `EVIDENCE: pending` on a checked box counts as unmet.
4. `/implement` and `ultra-build` verify a task when it returns and dispatch what it unblocks; the
   whole-project commands run once per phase.
5. An adversarial pass cannot widen the work it reviews, and cannot loop without a floor.
6. Every gate green, `check_wiring.py` at `0 unresolved`.

## Reuse ledger

| # | Need | Existing asset | Verdict | Why not new |
|---|---|---|---|---|
| N1 | One tier ladder | `references/shared/020-complexity-routing.md` | EXTEND | already shared and loaded by three commands; absorbed the model/effort tiering |
| N2 | One plan-path convention | `references/shared/007-path-conventions.md` | EXTEND | already the canonical table; it named files where it had to name a directory |
| N3 | One disjoint-file rule | `references/shared/070-parallel-agent-spawn.md` | EXTEND | ten copies existed; `ultra-build.js splitByFileOwnership` was the only enforced one |
| N4 | A task syntax the tools parse | `commands/implement.md` parses `- [ ]`; this repository already wrote `- [x] **TASK-04**` | REUSE | the repo's own convention is the gate syntax — one grammar, both roles |
| N5 | Confidence scoring | `skills/senior-prompt-engineer/references/parallel-batch-contracts.md § 3` | REUSE | the `phase-b` copy was deleted |
| N6 | Sprint contracts | `loop-engineering.md § Sprint Contracts` | REUSE | `/implement` consumes it; three restatements deleted |
| N7 | Spawn cap as a parameter | `graphGuardrails.maxParallelWave` | REUSE | fourteen sites hardcoded `5` |
| N8 | Per-task hard rules | `chain.hardRules` / `chain.invariants` | REUSE | `phase-c` hardcoded twelve project rules against cardinal 1; `ultra-build.js` already reads the config |
| N9 | Rolling dispatch primitive | a promise per task; the runtime caps concurrency | REUSE | no scheduler library, no new dependency |
| N10 | A gate runner script | (none) | NEW → refused | out of scope: the gate block is markdown the driver runs |

## Execution graph

```
[020 ‖ 007 ‖ 070] ──→ phase-b ──→ SKILL.md ──→ phase-c ──→ step-0-inventory ──→ plan.md ──→ implement/verify
                                        └──→ [ultra-plan ‖ ultra-build ‖ ultra-verify] ──→ ⟨gates⟩ ──→ version + CHANGELOG
```

| Edge | What the destination reads from the source | Verdict |
|---|---|---|
| canon → prose | the section names the prose cites | REAL |
| phase-b → everything downstream | the task grammar every other file must match | REAL |
| prose → workflows | the field names a workflow emits and parses | REAL |
| ultra-plan → ultra-build | nothing — one writes a prompt, the other a scheduler | **FALSE — deleted** |

**Stop rule.** `[020 ‖ 007 ‖ 070]` is the only real fan-out: three small files, no shared content.
The prose rewrites are one chain with one owner — they share a voice and cross-cite each other, so
splitting them would cost more in rebuilt context than it buys and would leave five registers inside
one skill.

## Dispatch matrix

| Task | Agent | Owns | Needs |
|---|---|---|---|
| T1.x | main | `references/shared/*`, `templates/rules/execution.md` | — |
| T2.x | main | `skills/planning/**`, `commands/*.md` | T1.x |
| T3.x | main | `workflows/*.js` | T2.1 |
| T4.x | main | manifests, config, CHANGELOG | T3.x |

## Phase 1 — Canon  [PARALLEL-SAFE]

- [x] **T1.1** — Make `020-complexity-routing.md` the one tier ladder, with model/effort tiering
  Owns: `references/shared/020-complexity-routing.md`
  Needs: none
  Agent: main · Effort: design
  CHECK: `python3 -c "import re,glob;print(sum('L9' in open(f,encoding='utf-8').read() for f in glob.glob('skills/planning/references/*.md')))"`
  EXPECT: `0`
  EVIDENCE: `0` — the L1–L10 table that contradicted every other copy is gone

- [x] **T1.2** — Make `007-path-conventions.md` define one plan directory
  Owns: `references/shared/007-path-conventions.md`
  Needs: none
  Agent: main · Effort: design
  CHECK: `python3 -c "print('One plan is one directory' in open('references/shared/007-path-conventions.md',encoding='utf-8').read())"`
  EXPECT: `True`
  EVIDENCE: `True`

- [x] **T1.3** — Move the one-writer-per-file rule into `070-parallel-agent-spawn.md`, and add the
  `Agents & Dispatch` section three files cite
  Owns: `references/shared/070-parallel-agent-spawn.md`, `templates/rules/execution.md`
  Needs: none
  Agent: main · Effort: design
  CHECK: `python3 .github/check_wiring.py`
  EXPECT: `0 unresolved`
  EVIDENCE: `199 routing references checked, 0 unresolved; 12 agents checked, 0 that would not register`

### Phase 1 gate
- [x] **G1.1** — every citation still resolves
  CHECK: `python3 .github/check_wiring.py`
  EXPECT: `0 unresolved`
  EVIDENCE: `199 routing references checked, 0 unresolved`

## Phase 2 — The skill and the commands  [SEQUENTIAL]

- [x] **T2.1** — Rewrite the task grammar, the phase gates and the seven-section plan template
  Owns: `skills/planning/references/phase-b-writing-plans.md`
  Needs: T1.1 (reads: the tier ladder it now cites instead of restating)
  Agent: main · Effort: design
  CHECK: `python3 -c "t=open('skills/planning/references/phase-b-writing-plans.md',encoding='utf-8').read();print(all(s in t for s in ('## Reuse ledger','## Regression watchlist','## Rollback','## Execution graph','## Destination','## Out of scope','## Not yet specified')))"`
  EXPECT: `True`
  EVIDENCE: `True` — the four sections `/plan` and `/verify` require appeared nowhere under `skills/planning/` before this

- [x] **T2.2** — Slim `SKILL.md` to citations, one stopping table, and the anti-loop rows
  Owns: `skills/planning/SKILL.md`
  Needs: T2.1 (reads: the task grammar it summarises)
  Agent: main · Effort: design
  CHECK: `python3 -c "print(len(open('skills/planning/SKILL.md',encoding='utf-8').read()))"`
  EXPECT: a number below `14027`
  EVIDENCE: `12004` — from 14,027; the phase step lists that restated the phase guides are gone

- [x] **T2.3** — Rolling dispatch, scoped per-task checks, and `chain.hardRules` in place of twelve
  hardcoded project rules
  Owns: `skills/planning/references/phase-c-executing-plans.md`
  Needs: T2.1 (reads: the `Owns`/`Needs` fields the driver schedules on)
  Agent: main · Effort: design
  CHECK: `python3 -c "t=open('skills/planning/references/phase-c-executing-plans.md',encoding='utf-8').read();print('No hardcoded hex' not in t and 'chain.hardRules' in t)"`
  EXPECT: `True`
  EVIDENCE: `True` — cardinal 1 restored; the rules come from the project's own config

- [x] **T2.4** — Lift the Step 0 reasoning and templates out of the command
  Owns: `skills/planning/references/step-0-inventory.md`, `commands/plan.md`
  Needs: T2.1, T2.2
  Agent: main · Effort: design
  CHECK: `python3 .github/check_context_budget.py`
  EXPECT: a `plan` floor below `55,000`
  EVIDENCE: `plan  47,889  88,829` — 29.3% under the 67,731 baseline

- [x] **T2.5** — Fix the citation drift: two dangling `§`, `[PARALLEL]` vs `[PARALLEL-SAFE]`, the
  `main` lane, the two reasoning-gate thresholds, the hardcoded spawn cap
  Owns: `skills/planning/references/dispatch-matrix.md`, `skills/planning/references/loop-engineering.md`, `skills/planning/references/phase-a-brainstorm.md`, `commands/implement.md`, `commands/verify.md`
  Needs: T2.2 (reads: the canonical stopping table it stops restating)
  Agent: main · Effort: mechanical
  CHECK: `python3 -c "import glob;bad=[f for f in glob.glob('skills/**/*.md',recursive=True)+glob.glob('commands/*.md') if 'Intent classification' in open(f,encoding='utf-8').read()];print(bad)"`
  EXPECT: `[]`
  EVIDENCE: `[]`

### Phase 2 gate
- [x] **G2.1** — every citation resolves and every agent still registers
  CHECK: `python3 .github/check_wiring.py`
  EXPECT: `0 unresolved`
  EVIDENCE: `199 routing references checked, 0 unresolved; 12 agents checked, 0 that would not register`
- [x] **G2.2** — nothing POSIX-only reached what an agent executes
  CHECK: `python3 .github/check_portability.py`
  EXPECT: `0 portability problem(s)`
  EVIDENCE: `0 portability problem(s)`

## Phase 3 — The workflows  [PARALLEL-SAFE]

- [x] **T3.1** — Replace the wave barrier in `ultra-build` with rolling dispatch, guarded by a
  topological cycle check
  Owns: `workflows/ultra-build.js`
  Needs: T2.1 (reads: the `Owns`/`Needs` fields the classifier now extracts)
  Agent: main · Effort: design
  CHECK: `node .github/check_workflows.mjs`
  EXPECT: `3 workflow(s) parse`
  EVIDENCE: `ultra-build.js — parses, runs dry in 3 stubbed spawns, refuses empty args`. The dry run
  exercises the scheduler's happy path. The other eight properties — wave fallback, width cap, file
  collision, dependency cycle, self-reference, unknown id, twelve-long chain, rolling start — were
  checked once on a throwaway fixture during implementation (`9 PASS · all green`, including
  `cycle throws — cycle — M -> N`) and are **not** covered by a standing gate. See
  `## Not yet specified`.

- [x] **T3.2** — Scope-lock the skeptic panel in `ultra-verify` so a finding past the plan's edge is
  reported, not turned into a fix round
  Owns: `workflows/ultra-verify.js`
  Needs: none — it edits a different file and reads nothing T3.1 writes
  Agent: main · Effort: design
  CHECK: `python3 -c "t=open('workflows/ultra-verify.js',encoding='utf-8').read();print('SCOPE_LOCK' in t and 'outOfScope' in t)"`
  EXPECT: `True`
  EVIDENCE: `True` — findings carry `inScope`; only a defect in the diff, a watchlist regression, or something that falsifies the Destination can start a round

- [x] **T3.3** — Make `ultra-plan` write the plan directory and emit the task grammar
  Owns: `workflows/ultra-plan.js`
  Needs: T2.1 (reads: the grammar its synthesis prompt now names)
  Agent: main · Effort: mechanical
  CHECK: `python3 -c "print('/PLAN.md' in open('workflows/ultra-plan.js',encoding='utf-8').read())"`
  EXPECT: `True`
  EVIDENCE: `True`

### Phase 3 gate
- [x] **G3.1** — every workflow parses, names match, agent enums valid, dry run passes
  CHECK: `node .github/check_workflows.mjs`
  EXPECT: `3 workflow(s) parse`
  EVIDENCE: `3 workflow(s) parse, and every meta.name matches its file` — 3, 9 and 15 stubbed spawns

## Phase 4 — Release  [SEQUENTIAL]

- [x] **T4.1** — Declare `planDir`, bump both manifests, write the changelog entry
  Owns: `.graph-powers/config.json`, `package.json`, `.claude-plugin/plugin.json`, `CHANGELOG.md`
  Needs: T3.1, T3.2, T3.3
  Agent: main · Effort: mechanical
  CHECK: `python3 .github/check_version_bump.py`
  EXPECT: `-> 1.5.0`
  EVIDENCE: `1 shipped file(s) changed, version 1.4.0 -> 1.5.0`

### Phase 4 gate
- [x] **G4.1** — guardrails intact
  CHECK: `python3 hooks/test_hooks.py`
  EXPECT: `EVERY GUARANTEE HELD`
  EVIDENCE: `EVERY GUARANTEE HELD`
- [x] **G4.2** — manifests valid
  CHECK: `claude plugin validate .`
  EXPECT: `Validation passed`
  EVIDENCE: `✔ Validation passed`
- [x] **G4.3** — the skill listing stays under its ceiling
  CHECK: `python3 .github/check_listing_budget.py`
  EXPECT: `within budget`
  EVIDENCE: `9,331 / 10,752 — within budget, 1,421 chars of headroom`

## Verification

Run from the repository root, each as its own command:

```bash
python3 .github/check_context_budget.py --compare
python3 .github/check_wiring.py
node .github/check_workflows.mjs
python3 hooks/test_hooks.py
python3 .github/check_portability.py
python3 .github/check_machine_paths.py
python3 .github/check_listing_budget.py
python3 .github/check_version_bump.py
claude plugin validate .
node bin/graph-powers.mjs --help
```

End to end: run `/plan` on a small task here and confirm it writes
`docs/plans/<date>-<slug>/PLAN.md` with the seven sections and the task grammar, then `/implement`
on it and confirm a task whose `Needs` are met starts before its siblings return.

## Regression watchlist

| # | Must still work | Proof | Result |
|---|---|---|---|
| W1 | Every routing reference and `§` citation resolves | `python3 .github/check_wiring.py` | `0 unresolved` |
| W2 | The 12 agents still register | same command | `0 that would not register` |
| W3 | Guardrails intact | `python3 hooks/test_hooks.py` | `EVERY GUARANTEE HELD` |
| W4 | Workflows parse and dry-run | `node .github/check_workflows.mjs` | 3/3 |
| W5 | Nothing POSIX-only in agent-executed text | `python3 .github/check_portability.py` | `0 problem(s)` |
| W6 | No home directory in a tracked file | `python3 .github/check_machine_paths.py` | `no home-directory paths` |
| W7 | Listing under its ceiling | `python3 .github/check_listing_budget.py` | `1,421 chars of headroom` |
| W8 | A plan written before this change still reads | `docs/plans/2026-08-20-intent-routing-plan.md` parsed under the new rules; `commands/implement.md` still accepts a bare `*.md` | accepted |
| W9 | `/implement`'s sprint-contract consumer resolves | `check_wiring.py` + `implement.md:158,187,222` | resolves |
| W10 | `ultra-plan`'s named anchors resolve | it reads `phase-a § Phase 0`, `phase-a § Step 4`, `phase-b` (+ `§ Risk`), `layer-map.md`, `dispatch-matrix.md`, `loop-engineering.md § Calibration anchors` | all six headings kept |

## Rollback

Each phase is one commit-sized set of edits: `git revert` per phase, in reverse order. The three
`.js` files are the only behavioural change and revert independently. No schema, no migration, no
deploy. `planDir` is additive — removing the line restores the schema default. Plans already on disk
keep working because the bare-`.md` path stays accepted.

## Out of scope

- **Porting a gate-runner script.** Reopens if `EVIDENCE: pending` survives a `/verify` in practice.
- **A Stop hook that blocks while gates are unmet.** Reopens if sessions end with unmet gates more
  than once; it changes harness behaviour and needs consent per install.
- **Editing `Leonxlnx/unlazy`.** Reference only.
- **`tree N` as a depth dial.** Superseded by `Owns`/`Needs`.
- **Teaching `check_wiring.py` to resolve named `§` citations.** Reopens on a third dangler.

## Not yet specified

- Whether `/verify` should **fail** or merely **report** a checked box with `EVIDENCE: pending` on a
  plan it did not write. Today it reports. Blocking until a real run says which is annoying.
- Whether `commands/implement.md`'s acceptance of a bare `${paths.planDir}/*.md` can eventually be
  dropped — that depends on plans held by installed projects, which is not knowable from here.
- Whether the scheduler's cycle guard and width cap deserve a standing gate. `check_workflows.mjs`
  dry-runs the happy path; the seven other properties were proven once, on a fixture that was not
  kept. A gate would mean either a second copy of the scheduler in the test or extracting it from
  the workflow, and neither is obviously worth it until the code changes again.
