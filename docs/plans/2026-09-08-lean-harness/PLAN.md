# Lean harness — implementation plan

**Date:** 2026-09-08 · **Branch:** `codex/lean-harness` · **Baseline:** `a84c5f7`
**Tier:** L5 · **Risk surface:** instruction routing, lifecycle hooks, five client projections
**Design authority:** the user's explicit local simplification and Gauntlet request, captured below.
**Depth:** Standard; existing architecture and public contracts remain in place.

## Destination

Graph Powers loads less instruction text while retaining every existing command mode, skill route,
agent capability and client-specific contract. Completion requires lower measured command floor and
ceiling, a listing no larger than baseline, unchanged safety assertions, passing existing gates,
and an evidence-backed before/after report. No arbitrary percentage target.

The chosen change is in-place deletion of duplicate explanations and conditional loading of existing
detailed guides. Keep the actionable trigger, owner, stopping condition and proof at each entrypoint;
keep shared rules in their existing canonical source. Detailed troubleshooting, histories and examples
load only when their subject applies. Reuse successful evidence until a changed dependency, new
failure or unresolved finding invalidates it. Sufficient verified evidence ends the work.

Scope includes prompts, rules, templates, hooks and client projections. Remove the forced response
format from session lifecycle context while retaining routing, gate discovery and safety behavior.
No new schema, framework, dependency, AI feature, public mode, migration or deprecation is needed.
AI is the existing harness runtime; additional AI functionality is out of scope.

## Baseline and constraints

The controller recorded `.graph-powers/logs/lean-harness-baseline.json` on 2026-09-08 using
`.github/check_context_budget.py` and `.github/check_listing_budget.py`: command floor **261858 B**,
ceiling **405450 B**, listing **10143 characters**; 12 commands, 12 agents and 13 skills.
Repeat the same measurement algorithm on both versions; its one-level load estimate is a proxy,
not a claim about observed token usage. Also report source bytes and remaining conditional loads,
so moving text beyond that estimator cannot masquerade as deletion. Baseline suite status is
unverified by this planner; the controller records actual gate results without inventing counts.

User authorization covers local execution and internal phase transitions. Preserve the current
branch, manual model choices and existing changes; no global installation, staging, commit, push,
merge or publication. The config's `main`/automatic-Git defaults do not override this instruction.
Preserve fail-open configuration handling, tenant/PII and irreversible-data protections, secrets,
read-only reviewers, explicit per-agent model tiers, portability and Oxc/tooling contracts.

## Reuse ledger

| Need | Existing authority | Decision |
|---|---|---|
| One shared safety/execution contract | `references/safety-floor.md`, `references/execution-floor.md`, `references/shared/` | EXTEND by removing repetition; retain callable anchors |
| Short entries with detailed methods | `commands/`, `skills/`, `agents/` | EXTEND existing routes and conditional references |
| Session context without prescribed final prose | `hooks/session_context.py`, `hooks/test_hooks.py` | EXTEND the existing lifecycle check |
| Measure and prove projection parity | `.github/check_context_budget.py`, `.github/check_listing_budget.py`, existing generators and gates | REUSE; do not weaken assertions or raise ceilings |

## Regression watchlist

| Existing behavior | Proof at integration | Owner |
|---|---|---|
| Modes, triggers, exclusions, file links and live anchors resolve | Route-preservation table in results; `check_wiring.py`, `check_file_references.py`, `check_workflows.mjs` | T4 |
| Hooks fail open; safety/permission and client posture remain enforced | `hooks/test_hooks.py`, `.github/test_hook_clients.py` | T4 |
| Claude, Codex, Cursor, Grok and Hermes retain registration and supported behavior | Existing generator checks, `check_codex_native.py`, `check_codex_policy.mjs`, `check_clone.py` | T4 |
| Planning/Gauntlet remain bounded with evidence, leases, independent critics and opt-in profile | `skills/planning/scripts/test_sdd.py`; evaluator traces unchanged default and explicit Gauntlet routes | T4 |
| No tooling, portability, listing or context regression | All applicable existing `AGENTS.md` gates, with unchanged assertions | T4 |

## Execution graph

`{T1, T2, T3} → T4`: one disjoint writer wave, followed by controller integration and final gates.
T4 reads T1's canonical anchors/Hermes adapter, T2's mode/load map and T3's method/load map plus
affected eval evidence. Each handoff names changed paths, retained contracts and focused results.
Writers preserve existing cross-boundary paths and anchors during the wave; any unavoidable rename
is a controller-coordinated dependency change before dispatch, not an unannounced sibling edit.

## Dispatch matrix

| Task | Canonical lane | Skill | Ownership | Needs |
|---|---|---|---|---|
| T1 | graph-powers:performance-optimizer | senior-prompt-engineer | Agents, shared references, rules/templates, Hermes adapter | none |
| T2 | graph-powers:performance-optimizer | skill-improve | Command Markdown | none |
| T3 | graph-powers:performance-optimizer | skill-improve | Skill entries/method references and affected skill-improve evals | none |
| T4 | graph-powers:debugger | debugger | Hook behavior, integration, generators, budgets, release metadata and results | T1, T2, T3 |

The canonical lanes keep the current SDD registry valid. The controller explicitly uses the native
`implementer` profile for T1–T3, as authorized by the user's personal policy, and performs T4
integration itself, using `debugger` if a defect needs a specialist. Record that mapping; do not
edit the registry or override models to accommodate this plan. Workers are leaves. Respect the
configured concurrency/spawn caps and reserve independent evaluator capacity after the wave.

## Phase 1 — Simplify existing instruction sources [PARALLEL-SAFE]

- [x] **T1** — Reduce shared instructions and the Hermes adapter
  Owns: agents, references, AGENTS.md, .claude/rules, templates, hermes/skills/graph-engineering/SKILL.md
  Needs: none
  Acceptance: shared invariants have one authoritative statement; all agent IDs, frontmatter capabilities/model tiers and referenced anchors survive; Hermes points to canonical methods and retains its supported/unsupported operations; handoff maps each removed duplicate to its surviving authority.
  Agent: graph-powers:performance-optimizer · Skill: senior-prompt-engineer · Effort: design
  TDD: not-applicable (instruction condensation without executable behavior changes)
  CHECK: python3 -X utf8 -c "import subprocess; subprocess.run(['git','diff','--check','--','agents','references','AGENTS.md','.claude/rules','templates','hermes/skills/graph-engineering/SKILL.md'],check=True); print('T1 diff clean')"
  EXPECT: T1 diff clean
  EVIDENCE: T1 diff clean; correction review 48cc9b0 PASS (LH-01–LH-03 resolved); agent models/tools unchanged.
  Steps:
    1. Read applicable AGENTS/rules and the controller's audit; reuse existing safety, execution and handoff authorities. Do not rescan the whole repository.
    2. Remove repeated ceremony and mandatory irrelevant loads; retain safety meaning and anchors consumed by T2/T3. Keep Hermes-specific limitations beside its canonical links.
    3. Run CHECK and return changed paths, source-byte comparison and duplicate-to-authority mapping for independent review. Do not edit sibling scopes or create children.

- [x] **T2** — Reduce command adapters while retaining modes
  Owns: commands
  Needs: none
  Acceptance: every existing command name, argument, mode, exclusion and fallback remains reachable; each detailed guide has an explicit relevant load condition; adapters do not copy canonical methods or require repeated green gates; handoff enumerates preserved routes.
  Agent: graph-powers:performance-optimizer · Skill: skill-improve · Effort: design
  TDD: not-applicable (existing command contract preserved by prose condensation)
  CHECK: python3 -X utf8 -c "import subprocess; subprocess.run(['git','diff','--check','--','commands'],check=True); print('T2 diff clean')"
  EXPECT: T2 diff clean
  EVIDENCE: T2 diff clean; correction review PASS; command paths restored; Codex native/clone check exit 0.
  Steps:
    1. Read command artifact rules and inventory modes before editing, starting with debug, pr-review, perf and verify.
    2. Keep parsing/routing and decisive completion evidence; point at current skill/shared paths instead of duplicating their procedures. Preserve explicit Gauntlet activation and final verification semantics.
    3. Run CHECK and return mode/load map plus source-byte comparison. Leave shared sources, skill files and budget constants to their owners.

- [x] **T3** — Make skill method detail conditional
  Owns: skills/*/SKILL.md, skills/*/references, skills/skill-improve/evals
  Needs: none
  Acceptance: all skill names, positive triggers, exclusions and domain capabilities remain; planning and skill-improve load only the relevant phase/mode guidance; learning history is no longer an unconditional full read; changed evals preserve behavioral assertions and document only the changed prompt contract.
  Agent: graph-powers:performance-optimizer · Skill: skill-improve · Effort: design
  TDD: not-applicable (instruction condensation; executable scripts and safety assertions remain unchanged)
  CHECK: python3 -X utf8 -c "import subprocess; from pathlib import Path; paths=sorted(Path('skills').glob('*/SKILL.md')); [subprocess.run(['python3','skills/skill-improve/scripts/quick_validate.py',str(p.parent)],check=True) for p in paths]; print('T3 skill entries valid')"
  EXPECT: T3 skill entries valid
  EVIDENCE: T3 skill entries valid (13); correction review PASS (LH-04–LH-06 resolved); eval runner 11/11.
  Steps:
    1. Read skills/AGENTS.md and skill rules; use the existing inventory to identify entry bodies and central method references that duplicate each other.
    2. Condense them without removing routes, required evidence, recovery caps or TDD applicability. Keep scripts, learning history and unrelated evals untouched; only skill-improve evals affected by the simplified contract may change.
    3. Run CHECK; return retained capability/load map, changed-eval rationale and any real eval results. Do not call rewritten fixtures a fresh model evaluation.

### Phase 1 gate

- [x] **G1.1** — Validate shared references after the complete wave
  CHECK: python3 -X utf8 -c "import subprocess; subprocess.run(['python3','.github/check_file_references.py'],check=True); print('Live references valid')"
  EXPECT: Live references valid
  EVIDENCE: Live references valid; exit 0 after final Animate reference corrections.
- [x] **G2.1** — Validate routing after the complete wave
  CHECK: python3 .github/check_wiring.py
  EXPECT: 0 unresolved; 12 agents checked, 0 that would not register
  EVIDENCE: 280 routing references checked, 0 unresolved; 12 agents checked, 0 that would not register.
- [x] **G3.1** — Validate plan ownership and dependency payloads
  CHECK: python3 skills/planning/scripts/sdd.py validate docs/plans/2026-09-08-lean-harness/PLAN.md --max-tasks 4 --profile gauntlet
  EXPECT: /"tier":\s*"L5"/
  EVIDENCE: sdd.py validate --max-tasks 4 --profile gauntlet: exit 0, tier L5 and four tasks.

The controller additionally compares actual changed paths with each Owns set and obtains one
independent evaluator verdict covering all three acceptance blocks, safety meaning and integration.
The text checks above prove syntax/routing only; they do not substitute for semantic review.
Gate IDs follow task IDs for the existing validator; T1–T3 still form one writer wave.

## Phase 2 — Integrate and prove the result [SEQUENTIAL]

- [x] **T4** — Integrate lifecycle simplification and all client projections
  Owns: hooks, .github, codex, cursor, grok, hermes/install.mjs, .claude-plugin, .codex-plugin, .cursor-plugin, .grok-plugin, plugin.yaml, package.json, CHANGELOG.md, skills/skill-improve/scripts/test_run_evals.py, docs/plans/2026-09-08-lean-harness
  Needs: T1 (reads: retained canonical anchors and Hermes adapter), T2 (reads: preserved command modes and conditional load map), T3 (reads: preserved skill methods and affected eval evidence)
  Acceptance: session start retains routing/gate discovery without prescribing final response prose; five clients keep existing capabilities; measured floor/ceiling decrease and listing does not grow; all declared gates and independent review pass without weakened assertions; results document before/after values, commands and limitations.
  Agent: graph-powers:debugger · Skill: debugger · Effort: design
  TDD: required
  CHECK: python3 hooks/test_hooks.py --focus session-context-lifecycle
  EXPECT: EVERY GUARANTEE HELD
  EVIDENCE: Lifecycle RED exit 1 (seven expected failures), GREEN exit 0; 27 final gates PASS; independent final review 1e67fc6 PASS for T1–T4, no open findings.
  Steps:
    1. Read hooks/AGENTS.md and handoffs; add the focused lifecycle assertion rejecting forced final prose while keeping routing, gate discovery, client parity and fail-open assertions. Observe RED on the unchanged hook.
    2. Remove only the forced output protocol in hooks/session_context.py and observe GREEN with CHECK. Refactor only while green; leave security/permission assertions intact.
    3. Integrate generators/projections from canonical sources using existing local generation/check paths, never a global installation; preserve the T1-owned Hermes body. Synchronize existing release manifests and CHANGELOG if required by the version gate.
    4. Re-measure with the baseline algorithm; record source bytes, load conditions and preserved routes in docs/plans/2026-09-08-lean-harness/RESULTS.md. Tighten an existing budget only when derived from measured output; never raise it or alter accounting to manufacture savings.
    5. Run final declared gates once on the integrated tree, reuse still-valid wave evidence, resolve only attributable failures, and record the independent final review and explicit Gauntlet verification result.

Integration scope refinement: the existing eval-runner test also asserts the removed response-prefix
policy. T4 owns that test's update; runtime runner and security/path assertions remain unchanged.
The observed failure is recorded in the integration evidence, not hidden by restoring obsolete prose.

### Phase 2 gate

- [x] **G4.1** — Keep the integrated context measurement within existing limits
  CHECK: python3 .github/check_context_budget.py
  EXPECT: within budget
  EVIDENCE: within budget — floor 46,243 B, ceiling 187,494 B; exit 0.
- [x] **G4.2** — Keep the integrated listing within existing limits
  CHECK: python3 .github/check_listing_budget.py
  EXPECT: within budget
  EVIDENCE: within budget — 7,730 characters under the 8,000 ceiling; exit 0.
- [x] **G4.5** — Prove the complete hook safety contract
  CHECK: python3 hooks/test_hooks.py
  EXPECT: EVERY GUARANTEE HELD
  EVIDENCE: EVERY GUARANTEE HELD — 676 assertions, exit 0.

## Verification

The controller runs every remaining gate declared in root AGENTS.md, preserving commands/assertions
and recording exit codes and deciding output in RESULTS.md. Do not repeat a green gate unless later
changes invalidate it. Type-check, build, UI/browser and production probes are NOT APPLICABLE here.
Explicit Gauntlet uses the existing independent final review and `/verify loop` closure, with the
documented one-shot fallback if unavailable; `/evolve auto` records only an actual reusable finding.
No completion with pending required evidence, open Critical/Important findings or an unverified
client projection. These checks and review establish compatibility; byte counts alone do not.

## Rollback

All changes remain local and unstaged. Before editing, preserve the baseline and each wave's changed
paths. If a task fails, restore only its own hunks from the baseline/current-turn backup, preserving
other writers and user changes; never reset the checkout. A hook regression restores its prior
lifecycle behavior and reruns the focused check. Regenerate affected local projections from the
restored canonical source. There is no installed-client or data migration to reverse.

## Out of scope

New commands, agents, abstractions, dependencies, schema fields, runtime features and broader
security redesign require a separate request. Global installation, model-selection changes and all
Git/publication actions require their own explicit authorization. Historical plans and learning
archives stay intact unless the current diff creates a concrete broken live reference.

## Not yet specified

No blocking product or architecture decision remains. File-level deletions and final byte savings
follow measured evidence; they are implementation choices within the declared owners. The parent
obtains evaluator Mode 1 approval before dispatch; this planner does not claim that review passed.
