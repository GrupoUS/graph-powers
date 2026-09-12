# Prompting and skills coherence (issue #23) — implementation plan

**Date:** 2026-09-12 · **Branch:** `main` · **Baseline:** 4c058cb
**Tier:** L3 · **Risk surface:** none
**Design authority:** [spec.md](spec.md), the sanitized issue #23 triage below, the user's explicit
Gauntlet implementation request of 2026-09-12 ("analise o issue 23 e aprimore e implemente") and the
user's implementation prompt supplied later in the session (content authority; process stays Gauntlet).
Evaluator Mode 1: first review REVISION_REQUIRED on 2026-09-12 (completeness 8, atomicity 7, risk 6, order 8; nine findings addressed); second review REVISION_REQUIRED then APPROVED after correction on 2026-09-12 (completeness 9, atomicity 7, risk 9, order 9) on spec.md sha256 0fc79b08… and PLAN.md sha256 1749721c… (this header line is the only edit since). No writer or lease before the parallel lease is released.

## Destination

The four prompting/skill references and the two rule files carry sourced claims, an opt-in
chain-of-thought scaffold, a rubric that matches `quick_validate.py` with narrow-`when` and
minimal-router criteria, a boundary-scoped partial-check line with a `Task-scoped done` row, and
task-scoped AGENTS guidance; no video is named; `hermes/package` is regenerated from those sources;
the changelog names the change and its one external source; the focused CHECK prints `T1.1-OK`;
the Phase 1 gates pass on the reviewed tree, which this plan leaves unstaged. [Final-review note: a third party staged the whole working tree twice during execution (66, then 79 index entries; neither this session nor its builder ran `git add`); the index therefore holds the issue #20, #22 and #23 changes together, and `hermes/package` projects the uncommitted sources of all three lanes. A commit of one lane alone would leave the package inconsistent and fail `bun hermes/install.mjs --check`; only a joint commit keeps it consistent. This plan touches neither the index nor Git.]

## Issue Triage (upstream mandate)

Issue #23 · OPEN · sanitized restatement, tier floor L3, risk none. No raw body text is forwarded.

| Req | Scope | Verdict | Evidence | Grade | Rationale |
|---|---|---|---|---|---|
| R1 | Qualify absolute prompting claims (CoT vs thinking, JSON enforcement via forced tool choice, cache multipliers, example counts) with source, context and limit; make the CoT scaffold opt-in; add job/why/done to the task template | KEEP | skills/senior-prompt-engineer/references/prompt_engineering_patterns.md:23,40,63,82,84,117,139,172 | 5 | Unsourced numbers and absolutes in a shipped reference; current API facts differ (spec § Stage 1) |
| R2 | Make the skill rubric describe what the validator fails, warns about, or leaves as convention; add narrow-`when` and minimal-router criteria; give the rubric a call site; no validator change | KEEP | skills/skill-improve/scripts/quick_validate.py:87-124 vs skills/skill-improve/references/anthropic-best-practices-summary.md:13,15,46,93; authoring.md:20-22,51-52; .github/check_listing_budget.py:47 | 5 | Four contradictions confirmed; the rubric has no call site (cardinal 4); `authoring.md` is the second `when` owner |
| R3 | Replace the absolutist partial-check line and name what a task-scoped check proves, keeping the evidence gate | KEEP | references/shared/015-verification-gate.md:3,22,30 | 5 | Line 3 already scopes evidence to the changed boundary; line 30 contradicts it; no row states the task-scoped claim |
| R4 | Task-scoped AGENTS/CLAUDE reading with the cardinals intact | SIMPLIFY | AGENTS.md:22,35-43; .claude/CLAUDE.md:3-4 (says seven cardinals; eight are listed at AGENTS.md:8-19) | 5 | Ownership map already exists; one sentence each plus the count fix |
| R5 | Boundaries/persistence: continuity without loosening commit/deploy approvals | SIMPLIFY | references/safety-floor.md:18-20; planning SKILL.md "A current approval covers its stated transition" | 5 | Already met in the harness; only the product `<task>` template gains a done condition (R1) |
| R6 | Rules attributed to any video, or a "graph engineering" orchestrator | CUT | No transcript is authority; skills/planning/SKILL.md:1-25 and references/loop-engineering.md already own nodes, edges, parallelism and done checks | 5 | Reopens only with a consumer no existing owner serves |
| R7 | Run applicable gates, regenerate projections through the generator, changelog note, no separate version bump | KEEP | .claude/rules/verify-supplements.md gate table; CONTRIBUTING.md:18-29; hermes/install.mjs:289,294; .github/check_version_bump.py:107-125 (exit 0 on this tree) | 5 | Rides on the 1.20.6 bump owned by the parallel issue #22 lane |

KEEP 4 · SIMPLIFY 2 · CUT 1 · DEFER 0. Scope removed: R6 — reopens per the rationale column.

## Reuse ledger

| # | Need | Existing asset (`path:line`) | Verdict | Why extending fails (NEW only) |
|---|---|---|---|---|
| N1 / R1 | Sourced, bounded prompting claims; opt-in CoT; job/why/done | skills/senior-prompt-engineer/references/prompt_engineering_patterns.md:6,23,61 | EXTEND | — |
| N2 / R2 | Rubric aligned with the validator, `when`/router criteria | skills/skill-improve/references/anthropic-best-practices-summary.md:13,19,58; skills/skill-improve/scripts/quick_validate.py:96 (unchanged) | EXTEND | — |
| N3 / R2 | Live call site for the rubric and the narrow-`when` sentence | skills/skill-improve/references/authoring.md:28,52 | EXTEND | — |
| N4 / R3 | Boundary-scoped partial-check line and `Task-scoped done` row | references/shared/015-verification-gate.md:22,30,38 | EXTEND | — |
| N5 / R4 | Task-scoped rule loading, correct cardinal count | AGENTS.md:22; .claude/CLAUDE.md:3 | EXTEND | — |
| N6 / R7 | Projections and changelog | hermes/install.mjs:289; CHANGELOG.md top entry | REUSE / EXTEND | — |
| N7 / R5 | Scope-bound approval continuity | references/safety-floor.md:18 | REUSE | — |
| N8 / R6 | Nodes, edges, parallelism, done checks | skills/planning/SKILL.md:1-25; references/loop-engineering.md | REUSE | — |

Evidence provider: direct text over the current checkout on 2026-09-12; API facts from the bundled
`claude-api` reference (cached 2026-06-24). Invalidators: any change to the six owned source files,
to `quick_validate.py`, to `hermes/install.mjs`, or to the lease/dirty state named in spec.md.

## Regression watchlist

| # | Existing behaviour that must still work | How to prove it | Phase |
|---|---|---|---|
| W1 | `skill-improve` and `senior-prompt-engineer` still validate | python3 skills/skill-improve/scripts/quick_validate.py skills/skill-improve; python3 skills/skill-improve/scripts/quick_validate.py skills/senior-prompt-engineer | 1 |
| W2 | Every routing reference and cited section still resolves | python3 .github/check_wiring.py | 1 |
| W3 | Every live Markdown path resolves, including the new rubric link | python3 .github/check_file_references.py; python3 .github/test_file_references.py | 1 |
| W4 | Listing and command-context budgets do not grow past their caps | python3 .github/check_listing_budget.py; python3 .github/check_context_budget.py | 1 |
| W5 | Hermes package stays source-derived and byte-consistent | python3 -X utf8 .github/test_hermes_package.py; python3 -X utf8 .github/test_hermes.py --static | 1 |
| W6 | Hook guarantees unchanged | python3 hooks/test_hooks.py | 1 |
| W7 | No POSIX-only command, home path or unknown placeholder entered a shipped file | python3 .github/check_portability.py; python3 .github/check_machine_paths.py; python3 .github/check_placeholders.py | 1 |
| W8 | The version checker still passes without a bump for this diff | python3 .github/check_version_bump.py | 1 |

Baseline on the dirty tree, measured 08:48 on 2026-09-12 while the issue #22 lane was still active
(its counts move; every number is re-measured at gate time): W1, W2 (526 refs / 0 unresolved), W3
(exit 0), W4 listing 7,853 / 8,000 and context budget within caps 51,500 / 208,000 with 586 B floor
and 568 B ceiling headroom, W5 (STATIC PASS), W6 (EVERY GUARANTEE HELD), W7 (0 / 0) and W8 (exit 0)
all pass. None of this plan's files is
cited by a command, so the context budget changes by 0 bytes; the byte caps on
015-verification-gate.md (0 to +40) and AGENTS.md (under +120) are hygiene. A gate that fails at
gate time is a failure of this tree and is reported with its numbers; it is never pre-attributed
to another lane.

## Execution graph

One sequential builder lane, one task, one wave Evaluator, one separate final review, then
`/verify loop`. Inside T1.1 the order is fixed: anchored edits E1–E14 → focused claims check →
`bun hermes/install.mjs --package-only` → `bun hermes/install.mjs --check` → changelog paragraph →
task CHECK. The single producer/consumer edge: the final bytes of
`prompt_engineering_patterns.md`, `015-verification-gate.md`, `authoring.md` and the newly linked
`anthropic-best-practices-summary.md` → `hermes/install.mjs --package-only` → the mirrored files
and `PROVENANCE.json` under `hermes/package`.

Configured limits come from schema/config resolution: maxTasksPerPlan 12, maxParallelWave 3,
maxSpawnsPerWorkflow 8, maxSpawnsPerSession 25, maxRoundsPerAgent 4, maxRepatch 2. Two Mode 1 plan
reviews (the first draft and this revision) precede the lease and are counted by hand, so every
reservation passes `--max-spawns 6`: writer, wave Evaluator, final Evaluator and verify-loop
Evaluator reserve four; two remain for one bounded correction (writer + re-review). Exceeding that
stops with evidence.

Entry precondition: the foreign lease of `docs/plans/2026-09-12-gauntlet-sha-bound` must be released
(its owner session confirmed it will announce the release); until then hook G4 denies every
repository write and this plan stays a draft.

## Requirement coverage

| Need | Surface | Applicable evidence | Task(s) and Owns | Producer → consumer payload/path | Acceptance evidence |
|---|---|---|---|---|---|
| N1/R1 | frontend/client (agent-facing reference text) | prompt_engineering_patterns.md:6-176 | T1.1: skills/senior-prompt-engineer/references/prompt_engineering_patterns.md | edited reference → Claude/Codex/Cursor/Grok by path; → Hermes mirror via generator | T1.1 CHECK (stale phrases absent, sources and `(opt-in)` present) |
| N2/R2 | frontend/client | anthropic-best-practices-summary.md:13-96; quick_validate.py:87-124 | T1.1: skills/skill-improve/references/anthropic-best-practices-summary.md | rubric rows and bullets → readers of Mode A; validator unchanged | T1.1 CHECK; G1.1 |
| N3/R2 | frontend/client | authoring.md:28,52 | T1.1: skills/skill-improve/references/authoring.md | Step 5 sentence → `references/anthropic-best-practices-summary.md` (resolved by check_file_references nearest-three rule and by the Hermes builder) → Hermes closure; Step 7 sentence → Mode A authors | G1.3 (file references), G1.7; T1.1 CHECK (`references/anthropic-best-practices-summary.md` and `1,536` present) |
| N4/R3 | frontend/client | 015-verification-gate.md:22,30,38 | T1.1: references/shared/015-verification-gate.md | one cell, one row, one trimmed line → every skill and command that loads the gate → Hermes mirror | T1.1 CHECK; G1.5 |
| N5/R4 | frontend/client | AGENTS.md:22; .claude/CLAUDE.md:3 | T1.1: AGENTS.md, .claude/CLAUDE.md | one sentence each → every session reading repository rules | T1.1 CHECK |
| N6/R7 | frontend/client | hermes/install.mjs:289; CHANGELOG.md top entry | T1.1: hermes/package, CHANGELOG.md | regenerated package + appended paragraph → installed Hermes client and release notes | T1.1 CHECK (`test_hermes_package.py` OK); G1.7 |
| N1–N8 | database N/A | .graph-powers/config.json declares only planDir and rulesDir; no schema directory in the tree | none | no table, migration or tenant path | owned-diff review |
| N1–N8 | backend/API N/A | no script, hook, generator or CLI changes; quick_validate.py and hermes/install.mjs are consumed unchanged | none | no handler, procedure or environment variable | owned-diff review; G1.6 |

## Dispatch matrix

| Task | Agent | Skill | Owns | Needs |
|---|---|---|---|---|
| T1.1 | graph-powers:debugger | graph-powers:skill-improve | Exact paths in the task block | none |

The write-capable canonical lane; native Claude spawn inherits the role's frontmatter model. Mode A
authoring context and spec.md § Exact edits are supplied verbatim. The builder creates no children.

## Phase 1 — Coherent prompting references and projections [SEQUENTIAL]

**Sprint 1:** apply the fourteen anchored edits, regenerate the Hermes mirror, append the changelog
paragraph, prove it with one focused check, and stop at a reviewable unstaged tree.

- [x] **T1.1** — Qualify claims and make CoT opt-in, align the rubric with `when`/router criteria, scope the partial-check line, add the AGENTS sentences, regenerate Hermes and note the change (R1, R2, R3, R4, R7)
  Owns: skills/senior-prompt-engineer/references/prompt_engineering_patterns.md, skills/skill-improve/references/anthropic-best-practices-summary.md, skills/skill-improve/references/authoring.md, references/shared/015-verification-gate.md, AGENTS.md, .claude/CLAUDE.md, hermes/package, CHANGELOG.md
  Needs: none
  Acceptance: Every edit E1–E14 in spec.md is applied at its anchor with no other byte changed in those six files (the `.claude/CLAUDE.md` replacement is three lines for two); `015-verification-gate.md` grows by exactly 49 bytes (2026→2075) and `AGENTS.md` by exactly 126 (2924→3050, including the two wrap newlines) — the spec's authoritative texts measure that, neither file enters the context budget, and the earlier 40/120 caps were an arithmetic defect of the plan corrected after wave review F1; none of the six files or the changelog paragraph mentions a video, a channel or "7 rules"; `hermes/package` is regenerated by the generator and `bun hermes/install.mjs --check` exits 0; one paragraph is appended at the end of the current top `CHANGELOG.md` entry without altering existing lines; the focused CHECK prints `T1.1-OK`; no file outside Owns changes.
  Agent: graph-powers:debugger · Skill: graph-powers:skill-improve · Effort: design
  TDD: not-applicable (documentation, rule text and a generated mirror; no behaviour or script changes)
  CHECK: python3 -c "import pathlib,subprocess,sys;r=lambda p:pathlib.Path(p).read_text(encoding='utf-8');a=r('skills/senior-prompt-engineer/references/prompt_engineering_patterns.md');b=r('skills/skill-improve/references/anthropic-best-practices-summary.md');c=r('references/shared/015-verification-gate.md');d=r('skills/skill-improve/references/authoring.md');e=r('AGENTS.md');f=r('.claude/CLAUDE.md');allsix=a+b+c+d+e+f;stale=[s for s in ['~10×','~2× faster','often replaces hand-rolled CoT','outperform','tool_choice=','claude-opus-4-7','last instruction strongest','One sentence describing what to produce','Use tool-use with','Claude follows XML tags reliably','sectioned prompts beat','2-3 worked examples','For multi-step reasoning (debugging output','| Pick one |','Anthropic prompt design:','85%','90%'] if s in a]+[s for s in ['Frontmatter has only','under 500 lines','Strict policy anchors','Pattern match','len(name) < 64','Grepped exclusion'] if s in b]+[s for s in ['Partial proves nothing','then forgetting to check exit code'] if s in c]+[s for s in ['seven cardinals','before any edit'] if s in f]+[s for s in ['youtu','7 rules','seven rules','Montano','Ben AI'] if s.lower() in allsix.lower()];need=[s for s in ['claude-prompting-best-practices','build-with-claude/thinking','fable-5-1/migration-guide','are not supported for this model','build-with-claude/structured-outputs','output_config','strict: true','1.25×','0.025×','up to 4,096','claude-opus-5','(opt-in)','Opt-in, not the default','Double-check','The whole corpus in every prompt','the condition that means done','Structure prompts with XML tags','rather than a fixed set','Use examples effectively','Include 3–5 examples for best results','general instructions over prescriptive steps','refreshed for no additional cost','only as an output contract'] if s not in a]+[s for s in ['1,024','non-empty','warns on stderr','argument-hint','the symptom or context that selects the skill','minimal router','adds no evidence','convention; not validated','stay out by convention','invalid YAML'] if s not in b]+[s for s in ['references/anthropic-best-practices-summary.md','1,536'] if s not in d]+[s for s in ['Proves only what it measures.','Task-scoped done','exit code nobody read'] if s not in c]+(['nearest the files you touch'] if 'nearest the files you touch' not in e else [])+[s for s in ['eight cardinals','local fix follows the rule file'] if s not in f];h=subprocess.run([sys.executable,'-X','utf8','.github/test_hermes_package.py'],capture_output=True,text=True);ok=not stale and not need and h.returncode==0;print('T1.1-OK' if ok else 'STALE='+str(stale)+' MISSING='+str(need)+' HERMES-EXIT='+str(h.returncode));sys.exit(0 if ok else 1)"
  EXPECT: T1.1-OK
  EVIDENCE: CHECK `T1.1-OK` exit 0 (controller, gates/t1.1-check.log wave 1 and gates/t1.1-check-r2.log after correction 1); `bun hermes/install.mjs --check` exit 0 (39 registrations current); wave W1 Evaluator compliance/quality/integration PASS with F1 (criterion amended) and F2 (regeneration also refreshed the planning evals.json and sdd.py mirrors to the issue #22 lane's dirty sources — expected, whole-tree generator) noted; correction round 1 fixed F3 (listing cap sums name) and F5 (rewrap) and the fresh correction Evaluator marked both ADDRESSED with no new breakage; owned diff vs HEAD snapshot bef80a505712; only the eight Owns paths changed by this task; closed 2026-09-12T13:39Z
  Steps:
    1. Read AGENTS.md, skills/AGENTS.md, .graph-powers/config.json, .claude/rules/verify-supplements.md, skill-improve Mode A (`skills/skill-improve/references/authoring.md`) and spec.md § Exact edits. Confirm the foreign write lease is gone and this plan's lease is held; confirm each anchor string in spec.md still matches its file. A missing anchor is BLOCKED with the line quoted, never a guessed edit.
    2. Apply E1–E10 to `prompt_engineering_patterns.md` as anchored replacements (the References block; lines 14 and 23; 34; 40; the § 3 heading, intro, line 82 and the caveat; the whole § 4 section; the caching example model id; the cost line; the § 7 rows 172, 173 and 176 plus the two appended rows). Keep every other line, fence and heading byte-identical.
    3. Apply E11 to `anthropic-best-practices-summary.md` (intro line, the frontmatter table rows including the split 1,024 / 1,536 rows and the added quoting row, the trigger-phrasing heading, bullet and added narrow-`when` bullet, the 500 non-empty lines bullet, the minimal-router bullet, the script-is-the-check line, the two Quality Gates checkboxes). Keep table alignment readable; the validator itself is not edited.
    4. Apply E12 to `authoring.md` (Step 5 link sentence, Step 7 narrow-`when` sentence), E13 to `015-verification-gate.md` (cell, inserted row, trimmed anti-pattern line), and E14 to `AGENTS.md` (Working rules bullet) and `.claude/CLAUDE.md` (lines 3–4). Measure `wc -c` before and after for `015-verification-gate.md` (+49 measured; the earlier 0 to +40 cap was a plan defect) and `AGENTS.md` (+126 measured after the F5 rewrap; the earlier < +120 cap likewise); do not touch the generated `graph-powers:start/end` block in AGENTS.md.
    5. Run the focused claims part of CHECK mentally against each file, then `bun hermes/install.mjs --package-only` followed by `bun hermes/install.mjs --check`. Only paths under `hermes/package` may change from regeneration, and within it only the mirrors of the four touched references (`prompt_engineering_patterns.md`, `015-verification-gate.md`, `authoring.md`, the newly linked `anthropic-best-practices-summary.md`) plus `PROVENANCE.json` and any manifest that records their digests; `bun hermes/install.mjs --check` passed before this task, so any other changed package path means the other lane left the package inconsistent — report those paths and stop before any other diff. [Amended after final review: the generator re-derives the whole package from the current sources, so it also refreshed the mirrors of the issue #20/#22 lanes' uncommitted sources (18 foreign package paths, among them `skills/planning/scripts/sdd.py` and the five new `issue-improve` files); this is expected generator behaviour, was recorded as wave finding F2, and is not a stop condition — the stop applies only to hand edits or to a `--check` failure.]
    6. Append the changelog paragraph from spec.md § Exact edits as the last paragraph of the current top `## 1.20.x` entry in `CHANGELOG.md` (1.20.6 if the parallel lane has landed it, otherwise the existing top entry). Do not edit, reorder or rewrap any existing line and add no version heading.
    7. Run the task CHECK verbatim and report its output, `git status --short` for the owned paths, the byte deltas, and the Context Handoff. Do not run whole-project gates; do not stage or commit.

### Phase 1 gate

- [x] **G1.1** — Touched skills keep their frontmatter contract
  CHECK: python3 skills/skill-improve/scripts/quick_validate.py skills/skill-improve
  EXPECT: Skill is valid!
  EVIDENCE: quick_validate skill-improve exit 0 `Skill is valid!` (senior-prompt-engineer also valid); gates/G1.1-r2.log (2026-09-12T13:39Z, snapshot bef80a505712)
- [x] **G1.2** — Routing references and cited sections resolve
  CHECK: python3 .github/check_wiring.py
  EXPECT: 0 unresolved
  EVIDENCE: check_wiring exit 0: 527 routing references, 0 unresolved; 12 agents register; gates/G1.2-r2.log (2026-09-12T13:39Z, snapshot bef80a505712)
- [x] **G1.3** — Live Markdown paths resolve, including the new rubric link
  CHECK: python3 -c "import subprocess,sys;r=subprocess.run([sys.executable,'.github/check_file_references.py']);print('FILE-REFS-OK' if r.returncode==0 else 'FILE-REFS-FAIL');sys.exit(r.returncode)"
  EXPECT: FILE-REFS-OK
  EVIDENCE: FILE-REFS-OK exit 0 (new `references/anthropic-best-practices-summary.md` link resolves); gates/G1.3-r2.log (2026-09-12T13:39Z, snapshot bef80a505712)
- [x] **G1.4** — Listing budget within its ceiling
  CHECK: python3 .github/check_listing_budget.py
  EXPECT: within budget
  EVIDENCE: listing budget exit 0: 7,853 / 8,000, `within budget`; gates/G1.4-r2.log (2026-09-12T13:39Z, snapshot bef80a505712)
- [x] **G1.5** — Command context budget within its caps
  CHECK: python3 -c "import subprocess,sys;r=subprocess.run([sys.executable,'.github/check_context_budget.py']);print('CONTEXT-BUDGET-OK' if r.returncode==0 else 'CONTEXT-BUDGET-FAIL');sys.exit(r.returncode)"
  EXPECT: CONTEXT-BUDGET-OK
  EVIDENCE: CONTEXT-BUDGET-OK exit 0: floor 562 B and ceiling 424 B of headroom; this plan's files enter no command budget; gates/G1.5-r2.log (2026-09-12T13:39Z, snapshot bef80a505712)
- [x] **G1.6** — Declared test gate: hook guarantees hold
  CHECK: python3 hooks/test_hooks.py
  EXPECT: EVERY GUARANTEE HELD
  EVIDENCE: hooks/test_hooks.py exit 0 `EVERY GUARANTEE HELD`; gates/G1.6-r2.log (2026-09-12T13:39Z, snapshot bef80a505712)
- [x] **G1.7** — Hermes static isolation and closure hold on the regenerated package
  CHECK: python3 -X utf8 .github/test_hermes.py --static
  EXPECT: OK
  EVIDENCE: test_hermes.py --static exit 0 `Hermes verifier: STATIC PASS` after `bun hermes/install.mjs --check` exit 0; gates/G1.7-r2.log (2026-09-12T13:39Z, snapshot bef80a505712)

Phase close also requires the wave Evaluator verdict, exact ownership review (only the eight owned
paths changed; the parallel lanes' dirty files untouched), and the recorded byte deltas. Type-check,
lint and build are NOT DECLARED here; do not manufacture them.

## Verification

Before execution: `python -X utf8 "${CLAUDE_PLUGIN_ROOT}/skills/planning/scripts/sdd.py" validate <this PLAN.md> --max-tasks 12 --profile gauntlet`, then an evaluator Mode 1 PASS on this plan and spec.md.
The validator checks structure; the independent review checks meaning and surface coverage.

Final: run the complete declared inventory from `.claude/rules/verify-supplements.md` in order, including
`bun hermes/install.mjs --check` before the Hermes gates. Report the CI-only Codex assertion as
CI-only and the installed Hermes runtime as UNVERIFIED. Any failing gate is a failure of this tree:
report its numbers and stop; no failure is attributed to another lane or silently accepted. Close through the Gauntlet final review and `/verify loop <PLAN_FILE>`
(`graph-powers:ultra-verify`) with configured caps; on PASS run `/evolve auto`, release only this
plan's lease, and stop reviewed and unstaged. Closing issue #23 with a comment is a separate outward
action the user authorized in the same request; it runs after the verdict and states exactly what
was verified, the acceptance list of issue #23 item by item, D1–D9 as applied, checks not run, the
residual dirty state, the rollback and `git status` plus HEAD.

## Rollback

Restore the six owned source files to their pre-task bytes (their anchors are quoted in spec.md),
regenerate `hermes/package` from the restored sources with the same generator, and remove the one
appended changelog paragraph. No Git state is created, so nothing is reverted in history; the
parallel lanes' files are never touched. No `reset --hard`, no `clean`.

## Out of scope

Changes to `quick_validate.py` or any script (reopens if the rubric cannot be made truthful
without one); a new skill, agent, workflow, orchestrator or reference for "graph engineering" or
Astra-style guidance (reopens only with a consumer no existing owner can serve); any version bump,
NOTICE or manifest edit (owned by the issue #22 lane); rules attributed to any video (reopens with a
transcript and a user decision); a mass rewrite of skill descriptions or of `commands/*` and
`agents/*` (reopens as its own plan after a measured listing failure); safety-floor or commit/deploy
approval wording (reopens only on an evidenced early-stop defect); Git actions; touching the issue
#20 or #22 dirty files.

## Not yet specified

No fog: the anchors, replacement texts, gates and ownership are closed. Pending are the evaluator
Mode 1 PASS on this revision, the release of the foreign lease, and the execution evidence.
