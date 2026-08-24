---
description: "Prove the work actually holds before it is handed off — runs the gates the project declared, checks the safety floor, and returns a verdict with the command output behind it. Use when the user asks whether this is done, to run the gates, to check nothing broke, or before claiming any L3+ task complete. Do not use to review a diff for quality (/pr-review) or to chase a gate that is already failing (/debug)."
workflow_type: augmented-llm
---

# /verify — Verification Gate

**ARGUMENTS**: $ARGUMENTS

> **Read before step 0 — never reconstruct these from memory:** `${CLAUDE_PLUGIN_ROOT}/references/shared/000-config-loader.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/005-superpowers-bootstrap.md`
> Read `${CLAUDE_PLUGIN_ROOT}/references/shared/060-skill-domain-matrix.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/125-change-set.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/130-bun-tsgo-gates.md`

Modes: `/verify` with **no arguments is `quick`** (gates + floor only — this is the default,
because the agent batch is what burns RAM). `/verify full` runs the review agents.
`/verify loop` hands the plan-measured half to `graph-powers:ultra-verify`, § 1.6.
Load `Skill("bun-verify")` in § 0 when the change set is JS/TS.

The single rule this command exists to enforce: **a gate is passing only if it ran in this session
and exited zero.** A remembered pass is not a pass.

---

## 0. Resolve what this project actually runs

Read the config (`${CLAUDE_PLUGIN_ROOT}/references/shared/000-config-loader.md`). The gates are whatever `tooling.commands` declares —
nothing is assumed:

| Gate | Command | When it is skipped |
|---|---|---|
| Type check | `${tooling.commands.typeCheck}` | field absent |
| Lint | `${tooling.commands.lint}` | field absent |
| Test | `${tooling.commands.test}` | field absent, or `tooling.testRunner` is `null` |
| Build | `${tooling.commands.build}` | field absent |

**A gate with no declared command is reported as `NOT DECLARED`, never as passing** — except a
JS/TS type-check or test inferred by `Skill("bun-verify")`, which is reported as
`INFERRED (bun-verify)` and still must exit zero. Never infer `npx tsc` or `node --test`.
See `${CLAUDE_PLUGIN_ROOT}/references/shared/130-bun-tsgo-gates.md`.

A missing script that exits non-zero as "script not found" reads exactly like a real failure, and a
gate nobody declared reads exactly like a gate nobody needed. Say which one it was.

**Then read `${rulesDir}/verify-supplements.md`, if the project has one, and run what it declares
as well.** The four rows above are the shape a typical application has; they are not the shape every
repository has. A project whose real gate set is a manifest validator, a portability scan and a
schema check has nowhere to put any of it — `tooling.commands` accepts seven named keys and those
are not among them — so without this file `/verify` reports one green gate out of thirteen and the
line reads as full coverage.

The file is a table: gate name, exact command, and one line on what a failure means. Run each in
order, capture the exit code, and report them in the same table as the declared gates, marked as
coming from the supplement. A supplement command that fails is a gate failure like any other. When
the project has no such file, say so in one line — for most projects the four rows are the whole
story, and their absence is a fact, not a gap.

**And read `chain.contractGates` from the config**, which answers the same question in the other
shape: commands that run only when a named surface changed, with an optional `needsServer` and
`runtime`. `graph-powers:ultra-verify` has honoured it all along and this command did not, so a
project that put its extra checks there got them run by the chain and skipped by a direct `/verify`.
Fire the entries whose `when` matches § 0.1's surfaces, and report them as their own rows.

Two mechanisms for one need is one too many, and the difference is real rather than historical:
`verify-supplements.md` is prose a person keeps and every run executes, `contractGates` is
structured and conditional. Run both, report which produced each row, and say in one line when the
project uses neither.

A third block, `database`, answers a different question: **is the declared schema applied?**
`contractGates` still run. A project that put a status command in both gets two rows, and that is
reported rather than collapsed.

### 0.3 Database

Fire only when § 0.1 mapped the `schema` surface. Otherwise one row:
`SKIPPED (schema surface untouched)`.

No `database` block, or block present but `${database.commands.status}` empty → `NOT DECLARED`.
Same voice as the four tooling gates.

When it fires, run `${database.commands.status}` through the Bash tool with a bounded wait.
Classify with `Skill("performance-optimization")` **Schema state** only on that branch (do not
restate the token list here). Report exactly one of `PASS` / `DRIFT` / `UNREACHABLE`.

- **DRIFT** — print the exact `${database.commands.apply}` string (even when
  `${database.applyPolicy}` is `never`) and the rollback line: "Do not apply from `/verify`.
  Rollback, if this apply already ran, is the reverse the project's own tool names (`down` /
  `rollback` / equivalent) — do not invent SQL." Verdict `NEEDS-WORK`. `/verify` never applies.
- **UNREACHABLE** — `NEEDS-WORK`. Say which half could not run. Do not print apply as if it would
  help.

`/verify` never applies, under either `applyPolicy` value. Apply is `/implement` § 7.5.

Load the domain skill for what changed — `Skill("debugger")` when chasing a failure,
`Skill("performance-optimization")` when performance, security or SEO surfaces moved,
`Skill("astro")` when `project.stack` names Astro.

### 0.1 The change set, and the surfaces it touched

Resolve it per `${CLAUDE_PLUGIN_ROOT}/references/shared/125-change-set.md § A`, and report the
`baseRef` and its `confidence` in the output. Until this existed, § 2's floor check asserted that no
file outside the task's scope had changed **without the command ever computing a scope** — two runs
could disagree and neither was wrong.

An empty change set is an answer: say so and stop, rather than reporting four green gates over a
tree nobody touched.

Then map the paths onto surfaces (§ B). Everything below is gated on them: an untouched surface
spawns no work.

### 0.2 Probe the code graph — once, and only by `status`

Per `125-change-set.md § C`. Available → `update -q`, then use it for the § 3 checks. Unavailable or
empty → record `SKIPPED (graph unavailable)` in the output and use grep. **This is never a failure**,
and a run that does not say which of the two happened has left the reader to guess.

---

## 1. Run the gates

Run each declared command and capture the exit code and the last meaningful line of output. Stop at
the first failure unless `$ARGUMENTS` says `--all`.

**They are not a chain.** Type-check, lint, test and build read the tree, not each other's exit
codes — the order is a reporting convention, and stopping early is a cost decision, not a dependency.
Say which one it was.

Report as a table: gate, command, exit code, evidence.

## 1.5 Dispatch the review batch — while the gates run, not after

The three blocks of this command that read the tree — the gates (§ 1), the safety floor (§ 2) and
the review checklist (§ 3) — share no data. § 2 runs `git status`, `git log` and `git diff --cached`;
§ 3 reads the plan, `${rulesDir}/`, the host `REVIEW.md` and the branch. Neither consumes a gate exit
code. Written as `1 → 2 → 3` they looked sequential and were not, and that appearance is what turned
free parallelism into wasted wall-clock.

Invoke `Skill("superpowers:dispatching-parallel-agents")`, then dispatch **in one message**, every
track `run_in_background: true`. Every agent below is read-only **by frontmatter**, never by a prose
"do not fix" — the incident that rule comes from is in
`${CLAUDE_PLUGIN_ROOT}/skills/debugger/references/anti-patterns.md`.

| Track | Agent | Asks | Fires when |
|---|---|---|---|
| Floor | `graph-powers:explorer` | § 2, every clause, with the command that proves each | always |
| Correctness | `graph-powers:evaluator` | does the diff do what the plan said, and nothing else | always |
| Security | `graph-powers:security-reviewer` | tenant, personal data, authorization, secrets, weakened defaults | `auth`, `api` or `schema` touched |
| Design | `graph-powers:ui-ux-designer` | tokens, states, keyboard, contrast, smallest viewport | `web` touched |

The project extends this list through `chain.lenses` — each entry a `name`, its own `checks`, an
optional `agent` and a `when` — the same contract `graph-powers:ultra-verify` honours. A lens naming
an agent this plugin does not ship is **named in the output before the batch runs**: a misspelt value
otherwise drops a lens silently and the run reports one check fewer than it claims.

Each track returns the findings table of
`${CLAUDE_PLUGIN_ROOT}/skills/senior-prompt-engineer/references/parallel-batch-contracts.md`, **plus
one line naming what it checked and found clean.** Without that line "two tracks agree" is not
evidence and "only one track raised it" cannot be told from "only one track looked".

Skipped unless `$ARGUMENTS` contains `full` or `loop`: empty arguments are `quick`, and `quick`
is the gates plus the floor run on the main thread. The agent batch is what made everyday
`/verify` expensive; it is no longer the default.

## 1.6 `loop` mode — hand the plan-measured half to the workflow

`graph-powers:ultra-verify` exists for what this command structurally cannot do: extract the plan's
requirements, walk completeness against the diff, run an adversarial skeptic panel, then **fix and
re-gate in a bounded loop** with a re-patch cap the orchestrator counts rather than asks an agent to
respect. It refuses to run without a plan, and its own header names this command as the answer for
the no-plan case. Until now nothing but `/plan`'s full chain could reach it.

With a plan path and `loop` in `$ARGUMENTS`:

```typescript
Workflow({ name: 'graph-powers:ultra-verify', args: { planPath, config } })
```

Three ways that does not happen, and one response to all of them — run §§ 1-4 as written and say in
one line which occurred: `Workflow` is not a tool in this harness · the name does not resolve
(`Workflow "graph-powers:ultra-verify" not found`) · it ran and declined. **A name that does not
resolve is a route, not an error, and it is never retried.**

What stays here whatever the workflow returns, because the workflow does none of it: the safety floor
(§ 2), `${rulesDir}/verify-supplements.md`, `NOT DECLARED` per gate, the `## Rollback` check and the
`## Reuse ledger` walk. Merge its `verdict`, `blocked` and `capped` into § 4 — `capped: true` means
the round ceiling stopped the loop, not that the work is done.

---

## 2. Safety floor check

**Who runs this.** In full mode the Floor track of § 1.5 gathers the evidence in the background while
the gates run; this section is where its return is checked, clause by clause, and where the verdict
on it is recorded. In `quick` mode there is no batch, so the main thread runs the commands itself.
Either way the clauses and the evidence they require are identical — and an unrun clause is reported
as unrun, never folded into a pass.

From `${CLAUDE_PLUGIN_ROOT}/references/safety-floor.md`:

- **§1** — nothing was committed, pushed or merged during the work. `git status --short` and
  `git log --oneline -1` prove it.
- **§3** — no migration, destructive SQL or irreversible operation ran without approval.
- **§4** — no secret entered a tracked file. `git diff --cached` and the diff of the touched files
  are the evidence, not a recollection.
- **§5** — the commands that ran are the ones the project declared.
- **§6** — no file outside the task's scope changed. A file the user had dirty before the work
  started is called out, not quietly included.

---

## 3. Review checklist (skipped in `quick` mode)

- Work happened on `${git.workBranch}`, or the deviation is stated.
- No dependency added without approval.
- No file in `protectedFiles` changed.
- Every acceptance criterion of the originating task has a line here saying how it was checked.
- Every blocking finding in the project's root `REVIEW.md` was checked, by its ID. That table is
  the project's own scar tissue; skipping it makes this gate generic.
- Project-specific invariants from `${rulesDir}/` that match the touched paths were honoured. When
  the project declares none, say that — it is a finding about the project, not a pass.

When the work came from a plan file, three of its sections are checked here — they exist for this
moment, and a plan that produces them for nobody to read is wasted work:

- **`## Regression watchlist`** — walk every row. Each one names existing behaviour this change was
  not supposed to touch, and how to prove it still works. Run the proof. A row with no proof
  command is itself the finding.
  **With the graph** (§ 0.2): `impact --files <change set> --depth 2` names the consumers the change
  reaches. A consumer on that list with no watchlist row is a gap the plan left, and it is the case
  the plan's own author could not have caught. `tests_for` may suggest a proof file for a row that
  has none — as a candidate to run, never as a coverage claim: a zero there means no static edge was
  found, not that the symbol is untested (`125-change-set.md § C`).
- **`## Reuse ledger`** — for every `REUSE` and `EXTEND` row, confirm the diff calls the asset the
  ledger named instead of a second implementation of it. A rediscovered "new service" beside a
  ledger row saying to reuse one is the most expensive drift this chain has, and it is invisible in
  a diff read on its own.
  **With the graph**, this stops being a reading exercise: `callers_of "<the asset the row named>"`
  intersected with the change set answers it as a set membership, and `search "<the row's terms>"`
  is the same question `/plan` asked to produce the row — asking it again after the fact is how the
  second implementation gets caught.
- **`## Rollback`** — present and specific enough to execute. This is checked whatever the verdict:
  it matters most exactly when everything else failed.

Then the plan's own ledger, if it carries task checkboxes: **a checked box whose `EVIDENCE:` line
still reads `pending` is unmet.** The box is a claim and the evidence is the proof; checked without
evidence counts as worse than unchecked, not better. An `ABANDON: <id> <reason>` line resolves a
task honestly, and every one of them is listed in the report.

No plan file, or the plan has none of these: say so in one line and continue. Their absence is a
fact about the plan, not a gate failure.

### What a finding may and may not become

Review here is adversarial on purpose, and that is exactly why its mandate is bounded. A finding
becomes **work** only when it is a defect this change introduced, a regression of a
`## Regression watchlist` row, or something that makes the plan's `## Destination` false.

Everything else — a pre-existing issue the diff did not touch, a refactor you would prefer, a
hardening idea, anything matching a `## Out of scope` row — is reported under the verdict's notes
and **does not reopen the work**. It is useful; it is not this change's job.

Two rules follow, and they are what keep an adversarial pass from becoming an unbounded one:

- **Never design past the request.** No new feature, no new file, no new abstraction, no redesign.
  The question is "does what was built hold?", never "what else could be built".
- **The same finding twice is a decision, not a third attempt.** A finding that survives its fix
  goes to the user with what was tried. Re-patching the same item past
  `graphGuardrails.maxRepatch` is how a review turns into a loop with no floor.

---

## 4. Verdict

Consolidate every signal into the table of
`${CLAUDE_PLUGIN_ROOT}/references/shared/090-verdict-matrix.md` — one row per gate, per § 1.5 track,
per supplement, plus the `baseRef` and its confidence and whether the graph was used or `SKIPPED`.
That file has always said it was used by this command; until 1.7.0 nothing here loaded it.

Then return exactly one verdict. **These three words are the harness's vocabulary** — `ultra-verify`
returns the same set, so a chained run and a direct run can be compared:

- `VERIFIED` — every declared gate ran and passed; no floor violation; checklist clean.
- `VERIFIED-WITH-NOTES` — gates pass, with non-blocking follow-ups listed.
- `NEEDS-WORK` — a gate failed, an invariant is violated, or something could not be verified.

`NEEDS-WORK` is also the verdict when a gate could not run. "I could not check this" and "this is
fine" are different answers, and collapsing them is the most expensive habit in this harness.

Include the exact commands run and their output summary. A verdict without evidence is an opinion.
