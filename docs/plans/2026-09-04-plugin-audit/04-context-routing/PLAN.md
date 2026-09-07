# Context, routing and capability contracts — implementation plan

**Date:** 2026-09-04 · **Branch:** main · **Baseline:** 0a59d3a7
**Tier:** L5
**Risk surface:** instructions, generated capability contracts and local release metadata
**Design authority:** [shared specification](../spec.md).
**Authorization:** user explicitly authorized local Gauntlet execution, excluding commits, publication,
global installation and changes to the operator's models. Independent plan review precedes writers.

## Destination

Close N8-N10 / F08-F10 with smaller unconditional debug context, a correct perf resource route,
accurate capability descriptions and coherent local release metadata. Keep every existing mode,
client, role, safety contract and shared method. No live routing-quality claim is made.

## Reuse ledger

| Need | Existing owner | Decision |
|---|---|---|
| N8, N9 | commands/debug.md, commands/perf.md, .github/check_wiring.py | EXTEND the current routing contract; no new mode or agent |
| N10 | current source-paired docs, schema and agent; existing generators | Correct evidence-backed claims; generate the one changed companion |
| Local delivery metadata | canonical manifest, client manifest builders, version helper | Reuse version parsing and emitted manifests; no release service |

## Regression watchlist

| Existing behavior | Proof | Phase |
|---|---|---|
| Debug root cause, direct small fixes, specialist and recovery routes | python3 .github/check_wiring.py | 1 |
| Context and listing remain inside existing caps | python3 .github/check_context_budget.py; python3 .github/check_listing_budget.py | 1 |
| Native companions retain canonical policy and advisory permission contract | python3 .github/check_codex_native.py | 2 |
| All five clients and six version-bearing files stay coherent | worktree version comparison plus client-generation checks | 2 |

## Execution graph

T1.1 -> T2.1 (reads: corrected routing contracts and measured context delta).
T1.1 -> T2.2 (reads: accepted routing changes for the release record).
T2.1 and T2.2 have disjoint ownership and no data dependency. Their task blocks may run in one
writer package, followed by one independent review for that complete wave. Prior sibling plans
are accepted before this final slice; do not modify their implementation.

## Dispatch matrix

| Task | Agent | Skill | Owns | Needs |
|---|---|---|---|---|
| T1.1 | graph-powers:debugger | none | commands/debug.md, commands/perf.md, .github/check_wiring.py | none |
| T2.1 | graph-powers:debugger | graph-powers:senior-prompt-engineer | agent, selected companion, schema and named capability documents below | T1.1 |
| T2.2 | graph-powers:debugger | none | six version-bearing files and CHANGELOG.md | T1.1 |

## Runtime budget and review

Two writer waves + two independent wave-review passes + one final reviewer = five dispatches.
The documented verify-loop fallback adds zero dispatches because Workflow is unavailable here.
Reserve the final reviewer first. The remaining three slots fit one correction writer/critic pair;
a further failure stops at the configured cap. No children and no new model selection.
The runtime retains only three child contexts; reuse the registered evaluator for distinct
independent acceptance passes and disclose that these are not newly isolated reviewer contexts.

Capture a TASK_BASE working-tree snapshot before each wave. Existing/concurrent
hooks/_config.py and hooks/test_hooks.py changes are excluded from ownership and rollback.
The formatting already present in .codex-plugin/plugin.json is preserved; its intended later
version change is the only authorized modification to that file in this slice.

## Risk

Keep the shared spec's risk register. The specific failure to avoid is making documentation shorter
while leaving a false promise, or recording a release as passing because an older committed bump
passed. Source-paired semantic review and direct working-tree version comparison close those gaps.

## Phase 1 — Existing operational routes [SEQUENTIAL]

- [x] **T1.1** — Align debug and resource routing with their existing owners
  Owns: commands/debug.md, commands/perf.md, .github/check_wiring.py
  Needs: none
  Acceptance: Small debug fixes retain the direct root-cause/test path without spawn-only eager loads; read-only inspection uses the shared background rule; perf resources/hooks/tests target section 2.0; all existing modes and recovery paths remain reachable.
  Agent: graph-powers:debugger · Skill: none · Effort: design
  TDD: required
  CHECK: python3 .github/check_wiring.py
  EXPECT: /0 unresolved/
  EVIDENCE: RED eager loads/foreground/wrong resource target; GREEN parent wiring460/0, negative mutations rejected, debug floor59276->52147B and total268985->261858B, listing10143; evaluator PASS at6328f40.
  Steps:
    1. Read both command routers and their shared authorities. Record the existing one-level debug floor, initially 59,276 bytes, before editing.
    2. Establish RED for the two concrete source contracts in the existing wiring gate: foreground read-only inspection and resource aliases pointing to the failure section. These are routing contracts, not claims of live model behavior.
    3. Move only assignment/spawn/autoresearch references behind actual consumers. Keep config, root-cause method, safety, tests, all modes and recovery reachable.
    4. Make read-only inspection follow the canonical rule and correct the perf row to existing section 2.0. Do not create new agents, modes or duplicate procedures.
    5. Observe GREEN in the routing gate and negative mutation checks. Run context/listing gates without raising a ceiling.
    6. Record real byte delta and source-contract evidence. Do not add unmeasured eval cases or claim paid/live trigger evaluation.

### Phase 1 gate

- [x] **G1.1** — Routing contract passes
  CHECK: python3 .github/check_wiring.py
  EXPECT: /0 unresolved/
  EVIDENCE: 460 routing references checked, 0 unresolved; exit 0.

- [x] **G1.2** — Context budget passes
  CHECK: python3 .github/check_context_budget.py
  EXPECT: within budget
  EVIDENCE: within budget: floor261858B, debug52147B; exit 0.

- [x] **G1.3** — Listing budget passes
  CHECK: python3 .github/check_listing_budget.py
  EXPECT: within budget
  EVIDENCE: within budget: listing10143/10752; exit 0.

Parent records actual changed paths against the task ownership and independent compliance/quality
verdict before advancing. The measured floor must decrease by actual conditional loading rather
than hiding an unconditional load from the estimator.

## Phase 2 — Capability truth and local delivery record [PARALLEL-SAFE]

- [x] **T2.1** — Correct current capability claims at their sources
  Owns: agents/skill-improver.md, codex/native-agents/skill-improver.toml, schema/config.schema.json, docs/ARCHITECTURE.md, AGENTS.md, skills/AGENTS.md, references/execution-floor.md, skills/skill-improve/references/harness-wiring-audit.md
  Needs: T1.1 (reads: corrected command routing and context measurement)
  Acceptance: Native Codex updating is documented accurately; Codex role permissions remain explicitly advisory; five-client and eval descriptions reflect current source; the auditor no longer assumes a host's global matcher; only the changed companion is regenerated.
  Agent: graph-powers:debugger · Skill: graph-powers:senior-prompt-engineer · Effort: design
  TDD: not-applicable (evidence-backed prose and generated artifact correction; semantic acceptance is reviewed against named runtime sources)
  CHECK: python3 -c "import subprocess; checks=[['python3','.github/check_codex_native.py'],['python3','.github/check_file_references.py'],['python3','.github/check_wiring.py']]; results=[subprocess.run(c,check=False) for c in checks]; assert all(r.returncode==0 for r in results); print('CAPABILITY STRUCTURE PASS')"
  EXPECT: CAPABILITY STRUCTURE PASS
  EVIDENCE: Source-pair review PASS: updater/schema, advisory role permissions, host matcher, five-client projections/explicit listing layers, eval/critical behavior; CAP21 resolved by interim final-evaluator stageA at e8bc80c. Structure native12/wiring460/refscan PASS.
  Steps:
    1. Read the independent audit F10 source pairs, senior-prompt-engineer contract and current generators. Preserve operator-authored preferences and historical reports.
    2. Replace the auditor's global matcher assumption with the canonical handoff and conditional inspection of host overrides. Correct both the source agent and its generated companion.
    3. Correct schema autoUpdate.codex against hooks/auto_update.py; architecture role permissions against codex/install.mjs and its gate; eval coverage against existing capture/runner modules and CI.
    4. Correct current client-count and critical-eval descriptions, including the audit reference. Use links to canonical contracts instead of expanding prose.
    5. Generate the owned companion through the existing exported builder and write only that path; do not run a broad emit that writes release metadata or other roles.
    6. Run CHECK. The independent critic must additionally record one semantic criterion per source pair, with both source paths and a PASS/FAIL; structural checks alone do not prove the prose true.

- [x] **T2.2** — Synchronize the selected local release metadata
  Owns: CHANGELOG.md, package.json, .claude-plugin/plugin.json, .codex-plugin/plugin.json, .cursor-plugin/plugin.json, .grok-plugin/plugin.json, plugin.yaml
  Needs: T1.1 (reads: accepted routing delta and the prior accepted improvement slices)
  Acceptance: The six disk versions are identical and newer than HEAD, the changelog describes only accepted changes, and the pre-existing Codex manifest formatting survives; no commit, publication or real installation occurs.
  Agent: graph-powers:debugger · Skill: none · Effort: mechanical
  TDD: not-applicable (release metadata only; direct version and snapshot checks are the acceptance evidence)
  CHECK: python3 -c "import runpy; m=runpy.run_path('.github/check_version_bump.py'); paths=['.claude-plugin/plugin.json','.codex-plugin/plugin.json','.cursor-plugin/plugin.json','.grok-plugin/plugin.json','package.json','plugin.yaml']; values=[m['version_on_disk'](p) for p in paths]; before=m['version_at']('HEAD',paths[0]); assert len(set(values))==1; assert tuple(map(int,values[0].split('.')))>tuple(map(int,before.split('.'))); print('WORKTREE VERSIONS PASS',before,'->',values[0])"
  EXPECT: WORKTREE VERSIONS PASS
  EVIDENCE: Six disk versions1.19.2 vsHEAD1.19.1; WORKTREE VERSIONS PASS; native manifest byte-equal to127b548 with version-only substitution; META22 resolved; changelog/source-generation review PASS.
  Steps:
    1. Read current six disk versions and HEAD. Use 1.19.2 only if no later version has landed; otherwise select the next patch without overwriting another writer's release.
    2. Update canonical metadata and derive client manifest values through existing exported generators. Write only owned version-bearing paths, not all native agents/wrappers.
    3. Record accepted changes in CHANGELOG.md. Preserve the pre-existing Codex JSON formatting; snapshot comparison must show only its intended version line changed.
    4. Run the direct disk-versus-HEAD CHECK, not merely check_version_bump.py, whose committed range cannot prove this unstaged release.
    5. Run existing client-generation/version gates and compare actual diff ownership. Do not stage, commit, publish or refresh the operator installation.

### Phase 2 gate

- [x] **G2.1** — Capability structural gates pass
  CHECK: python3 -c "import subprocess; checks=[['python3','.github/check_codex_native.py'],['python3','.github/check_file_references.py'],['python3','.github/check_wiring.py']]; results=[subprocess.run(c,check=False) for c in checks]; assert all(r.returncode==0 for r in results); print('CAPABILITY STRUCTURE PASS')"
  EXPECT: CAPABILITY STRUCTURE PASS
  EVIDENCE: CAPABILITY STRUCTURE PASS after final sentence correction; semantic source-pair evaluator checks PASS.

- [x] **G2.2** — Working-tree release versions agree and advance
  CHECK: python3 -c "import runpy; m=runpy.run_path('.github/check_version_bump.py'); paths=['.claude-plugin/plugin.json','.codex-plugin/plugin.json','.cursor-plugin/plugin.json','.grok-plugin/plugin.json','package.json','plugin.yaml']; values=[m['version_on_disk'](p) for p in paths]; before=m['version_at']('HEAD',paths[0]); assert len(set(values))==1; assert tuple(map(int,values[0].split('.')))>tuple(map(int,before.split('.'))); print('WORKTREE VERSIONS PASS',before,'->',values[0])"
  EXPECT: WORKTREE VERSIONS PASS
  EVIDENCE: WORKTREE VERSIONS PASS 1.19.1 -> 1.19.2; exact native-format snapshot PASS.

- [x] **G2.3** — Diff whitespace and conflict-marker checks pass
  CHECK: git diff --check
  EXPECT: empty stdout and exit 0
  EVIDENCE: git diff --check empty stdout; exit 0.

- [x] **G2.5** — Full existing hook guarantees hold at final boundary
  CHECK: python3 hooks/test_hooks.py
  EXPECT: EVERY GUARANTEE HELD
  EVIDENCE: Full hook suite675assertions: EVERY GUARANTEE HELD, exit0; final declared25gate batch allPASS.

The phase critic records the five capability source-pair decisions, ownership of both tasks and
the native manifest formatting comparison against TASK_BASE. No task closes from a structural
PASS alone when its semantic criterion remains unreviewed.

## Verification

Run the root declared gates and corrected verification supplement once after integration.
Use existing Codex user/project fixture checks, Cursor/Grok generation and Hermes checks.
The final reviewer is a separate acceptance pass; verify-loop then uses its documented inline
fallback with the same safety floor, reuse ledger, regression watchlist and rollback checks.
No unrun platform/provider check becomes a PASS.

## Rollback

Restore only this slice against its TASK_BASE snapshots. Preserve the original manifest formatting,
external hook changes and accepted sibling changes. Metadata can be reversed locally without
changing HEAD. No blanket reset, destructive cleanup or real reinstall is allowed.

## Out of scope

Model upgrades, permission-policy changes, live provider evaluation, global cleanup, new agents,
new schedulers, new dependencies, commit/push/publication and historical document rewrites.

## Not yet specified

No implementation-blocking fog remains. Cross-platform and live-session verification not
available locally remains explicit. Additional independent defects are notes, not automatic tasks.
