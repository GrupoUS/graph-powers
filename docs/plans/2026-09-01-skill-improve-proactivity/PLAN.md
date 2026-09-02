# Proactive `skill-improve` lifecycle — implementation plan

**Date:** 2026-09-01 · **Branch:** `fix/bounded-agent-fanout` · **Baseline:** `8b6eb28`
**Tier:** L5 · **Risk surface:** SessionStart hooks, clean provider subprocesses, generated manifests, licence provenance
**Design authority:** `docs/plans/2026-09-01-skill-improve-proactivity/spec.md` — recovery Gate 1 PASS for the run-8 bridge correction

**Recovery run:** earlier bounded leases exposed, in order, a Claude timeout, a raw-authentication
false positive, pre-provider `HEAD` drift, a run-4 response-contract miss, and a run-5 trace-oracle
failure after both textual graders passed. Run 5 observed Codex `skip` despite the Mode A response
and Claude `skill-improve` load where `senior-prompt-engineer` was required. Independent audits
isolated two seams: the Codex parser used an impossible fake event, searched every nested string and
accepted only the installed path; the pre-load description and hook pointer also described agent
work too broadly. This run preserves completed T1.3 and immutable run-5 evidence, corrects both
seams under RED tests, recreates baseline from commit
`08a312ed3424376c7568c6d51b3dc263f7a31847`, and creates all four run-6 traces afresh. Run 6
proved discovery and routing but left a post-load first-line RED; run 7 attempted a body-only
correction and remains immutable control evidence. This approved follow-up is run 8.

## Run 7 recovery delta (historical)

Run 6 is immutable historical evidence. Run 7 owned only `skills/skill-improve/SKILL.md` and
`skills/skill-improve/scripts/test_run_evals.py`. Its single writer added a deterministic first
non-empty-line RED for the preserved blocker-first response, then moves the existing entry protocol
before the lifecycle matrix and makes it precede blocker, refusal, permission/tool observation,
clarification, plan, draft and edit — including unavailable tools or Write permission. The existing
matrix, description, SessionStart pointer, parser, sandbox, prompts, assertions, attribution and all
unrelated dirty files are frozen. The controller runs exactly four fresh run-7 provider sessions
(Codex/Claude baseline, then Codex/Claude candidate), and no retry is allowed. `R10-F1` closes only
after the run-7 textual grader, trace polarity and first-line probe all pass. The run-7 candidate
failed its live first-line gate and is retained as the body-only control.

## Run 8 recovery delta (active)

Run 7 is immutable control evidence. This round owns only `hooks/session_context.py`,
`hooks/test_hooks.py` and the post-GREEN disposition in `skills/skill-improve/learning.md`; the
canonical `skills/skill-improve/SKILL.md`, description, parser, producer, prompts, assertions,
sandbox, installer and matrix are frozen. The single writer adds a deterministic RED assertion for
the SessionStart bridge, extends only `lifecycle_pointer()` with the first-entry precedence reminder,
and runs all static gates. The controller then runs exactly one fresh Codex positive and Claude
negative candidate pair in `run-8/bridge-candidate`, using `run-7/green` as the immutable body-only
control. No baseline rerun or retry is allowed. `R10-F1` closes only after the bridge candidate's
tagged grader, trace polarity, equal prompt digests, changed digest and first-line probe all pass.

## Destination

Done means a fresh Claude Code or Codex session receives one bounded lifecycle pointer and
`skill-improve` proactively selects Mode A, Mode B, or an explicit exclusion at the approved
skill/harness lifecycle boundaries. The two unprimed live cases pass at threshold `1.0`, every
trace identifies the exact candidate digest, the task-close follow-up is disposed, the existing
report-only and routing boundaries remain intact, and all repository gates pass without touching
unrelated dirty work.

## Reuse ledger

| # | Need | Existing asset (`path:line`) | Verdict | Why extending fails (NEW only) |
|---|---|---|---|---|
| N1 | Put the lifecycle reminder in every supported session without loading the full skill | `hooks/session_context.py:59-82,165-166`; `hooks/test_hooks.py:2280-2311` | EXTEND | — |
| N2 | Select the owner at lifecycle stages | `skills/skill-improve/SKILL.md:3,23-56,144-148`; `references/shared/060-skill-domain-matrix.md:20-29` | EXTEND | — |
| N3 | Turn changed behaviour into RED and per-case evidence | `skills/skill-improve/references/authoring.md:181-262`; `skills/skill-improve/scripts/run_evals.py:309-376`; `skills/skill-improve/evals/evals.json:1-359` | EXTEND | — |
| N4 | Produce reproducible clean-session responses, traces and bounded failure diagnostics | nearest consumer `skills/skill-improve/scripts/run_evals.py:309-376`; installer `codex/install.mjs:1-24,800-850` | NEW | The grader must remain provider-agnostic; coupling provider process, authentication and JSONL failures into it would create a second responsibility. |
| N5 | Preserve and close follow-up measurements | `skills/skill-improve/learning.md:1-16,120-122,240-241,539-541,611-634` | EXTEND | — |
| N6 | Capture general session learning | `commands/evolve.md:69-95`; `references/shared/100-autoresearch-loop.md:1-56` | REUSE | — |
| N7 | Bound research, fan-out and independent judgment | `references/execution-floor.md:1-80`; `references/shared/070-parallel-agent-spawn.md:1-39`; `agents/skill-improver.md:1-18,91-97` | REUSE | — |
| N8 | Credit and license the adapted methodology | `NOTICE:9-57`; `.claude-plugin/plugin.json:8`; `package.json:26`; `skills/skill-improve/LICENSE.txt:1-202` | EXTEND | — |

## Regression watchlist

| # | Existing behaviour that must still work | How to prove it | Phase |
|---|---|---|---|
| W1 | One weak description remains Mode A; a new skill makes Mode A/RED observable before clarification and runs Mode A before Mode B | `proactivity-contract` good/bad fixtures plus the Codex live response | Phase 1 |
| W2 | Agent prompt design routes to `senior-prompt-engineer`; only later registration/wiring invokes Mode B | boundary fixture plus `claude:bound-agent-prompt-draft` live trace | Phase 1 |
| W3 | Ordinary application source, one isolated product failure and unrelated upgrades do not invoke `skill-improve` | three negative fixtures with explicit owner and no load event | Phase 1 |
| W4 | Mode B stays report-only and its paired judge cannot Write/Edit | wiring, Codex native-policy and semantic-policy gates | Phase 1 |
| W5 | Session context still reports project, branch, gates and the execution-floor pointer | full hook suite for Claude Code and Codex, including unchanged first line | Phase 1 |
| W6 | Bounded-fanout skill and release work from baseline remains byte-for-byte intact | the two exact SHA-256 preservation probes in G1.8 and G1.9 | Phase 1 |
| W7 | Skill listing remains below its entry and shared ceilings | `quick_validate.py` and `check_listing_budget.py` | Phase 1 |
| W8 | Always-on posture is exactly one bounded line and does not duplicate the lifecycle matrix | hook assertions plus `check_context_budget.py` | Phase 1 |
| W9 | Current unrelated edits, including the concurrent planning/hook batch discovered during Gate 2, remain untouched | G1.10 hashes all 33 frozen dirty files against the stabilized post-drift snapshot; G1.11 permits them but never leases them | Phase 1 |
| W10 | A loaded Mode A response emits its lifecycle line before any blocker or permission report | deterministic first-line RED/GREEN probe plus the fresh Codex response | Phase 1 |

## File map

| Responsibility | Sole owner | Interface |
|---|---|---|
| Provider adapters and deterministic trace oracle | T1.1 | replaces the impossible Codex fake, scopes load detection to a successful official command event over either canonical path, and contributes `PARSER_READY` |
| Lifecycle entry bridge and follow-up state | T1.2 | adds the bounded SessionStart precedence reminder without duplicating the matrix, emits `STATIC_READY`, consumes `GREEN_RECORDED`, then emits `FINALIZED`; the canonical body and runner regression are historical and frozen |
| Human-facing attribution and root package SPDX | T1.3 | uses the locked SPDX literal; emits `ATTRIBUTION_READY` and never reads a sibling patch |
| RED/GREEN provider execution | controller | runs the two exact bridge-candidate commands in T1.2; neither writer launches a child session |
| Assertions | existing `run_evals.py` | remains the single grader; the producer only captures responses and traces |

## Execution graph

```text
Lane A: run-7 body-only response RED → bridge assertion RED → pointer GREEN → STATIC_READY
Prior run: frozen T1.3 outside-digest attribution ────────────────────────────────────────┤
Controller: C1 immutable run-7/green control → CONTROL_RECORDED → C2 two run-8 BRIDGE sessions
T1.3 ATTRIBUTION_READY ──────────────────────────────────────────────────────────────────┘
                                                                                              │
                                                                                              ▼
                                                   GREEN_RECORDED → Lane A closes R10-F1 + final CHECK
                                                                                              │
                                                                                         FINALIZED
                                                                                              │
                                                                                              ▼
                                                       one wave Evaluator → phase gates → separate final Evaluator
```

| Edge | Payload read by destination |
|---|---|
| T1.1 → T1.2 | `PARSER_READY`, passing producer suite, official event-shape fixtures, canonical-path coverage and response/output false-positive rejection |
| T1.2 + T1.3 → C1 | `STATIC_READY` plus prior `ATTRIBUTION_READY`; context floor at most 269,000 B and every digest-root path frozen |
| C1 → C2 | `CONTROL_RECORDED`, immutable run-7/green body-only pair and the passing static CHECK |
| T1.2 → C2 | the same frozen digest surface; no edit occurs between pointer GREEN and bridge capture |
| C2 → T1.2 | `GREEN_RECORDED`, two run-8 bridge response/trace pairs, changed digest proof and tagged grader output |
| T1.2 → wave review | `FINALIZED`, CLOSED `R10-F1`, evaluated/final digest output and passing composite task CHECK |
| wave review → phase gate | per-task compliance/quality verdict plus one integration verdict |

The control nodes are parent operations, not task dependencies. Run 6 completed T1.1 and T1.3, and
run 7 completed its body-only correction; all are historical evidence and receive no run-8 dispatch.
T1.2 is the sole active writer package. It adds the deterministic bridge RED and pointer GREEN
before `STATIC_READY`, then waits while the controller captures the unchanged bridge candidate
against run-7/green. Only `GREEN_RECORDED` permits the final evidence append. Controller follow-ups
resume the same writer session and consume no new dispatch slot. T1.1, T1.3 and the run-7 control
remain frozen evidence.

## Dispatch budget

| Slot | Operation | Accounting evidence |
|---:|---|---|
| 1 | Recovery Lane A writer for active T1.2 only | `sdd.py dispatch` writer reservation; T1.1/T1.3 are historical and not dispatched |
| 2-3 | Codex positive + Claude negative BRIDGE CANDIDATE sessions | exactly two new run-8 trace files |
| 4 | one consolidated wave Evaluator, including frozen T1.3 | `sdd.py dispatch` evaluator reservation |
| 5 | separate final Evaluator | reserved before the first wave |
| 6-7 | unused failure boundary | no dispatch; any required correction returns bounded `NEEDS_WORK` |

The two provider subprocesses are not Graph Powers roles accepted by the SDD dispatch ledger, so
their exact trace count is the mechanical accounting surface; the controller combines those two
with the three SDD reservations before dispatch. T1.3's prior writer and the run-7 control are
historical evidence, not dispatches in this run. No other provider trial, bootstrap, consultation,
confirmation or correction is permitted. Any failure that needs another dispatch ends
the run as bounded `NEEDS_WORK`; it is never hidden by resetting the ledger.

## Dispatch matrix

| Task | Agent | Skill | Owns | Needs |
|---|---|---|---|---|
| T1.1 (historical) | `graph-powers:debugger` | `graph-powers:skill-improve` | `skills/skill-improve/scripts/capture_trigger_evals.py`; `skills/skill-improve/scripts/test_capture_trigger_evals.py` | completed in run 6; no run-7 dispatch |
| T1.2 (active) | `graph-powers:debugger` | `graph-powers:skill-improve` | `hooks/session_context.py`; `hooks/test_hooks.py`; `skills/skill-improve/learning.md` | — |
| T1.3 (historical) | `graph-powers:debugger` | `graph-powers:skill-improve` | `NOTICE`; `CHANGELOG.md`; `package.json` | completed in prior run; no run-7 dispatch |

### Mini-contract: Phase 1

**Sprint 1:** installs a measured, bounded proactive lifecycle in `skill-improve`, verified by the
fresh-session pair, focused contracts and repository gates, and excludes a general observer,
scheduler, automatic patching, global configuration changes and any claim of suite-wide hit rate.

## Risk controls

| # | Failure mode | Control |
|---|---|---|
| R1 | A concurrent writer changes the digest during RED/GREEN | all digest-root changes and projections are in Lane A; files freeze at both controller checkpoints |
| R2 | A primed prompt manufactures a positive | producer rejects skill names, modes, load instructions and eval/probe vocabulary before launch |
| R3 | Provider absence, authentication, timeout or malformed JSONL is mistaken for a negative, or response/output text manufactures a Codex load | capture exits `1` on infrastructure failures; authentication requires a top-level structured error; Codex load requires a successful official completed command event over an explicit source/installed canonical path; all other nested text is ignored |
| R4 | Mode B or its judge gains a write path | lifecycle matrix keeps Mode B report-only; wiring/native/policy gates remain mandatory |
| R5 | Attribution drops MIT/Apache or generated manifests drift | exact target is `MIT AND Apache-2.0 AND CC-BY-4.0`; Claude is source and all four clients regenerate |
| R6 | First review needs correction but only one of eight slots remains | a correction requires its writer plus a fresh Evaluator; persist completed evidence and return `NEEDS_WORK`, and only a later user-requested run may continue |
| R7 | Concurrent work changes again after approval and contaminates RED/GREEN | G1.10 is a byte-for-byte preflight and phase gate; any mismatch stops before provider capture and requires a refreshed plan snapshot |
| R8 | The owner loads but a one-turn trial stops at clarification before reporting lifecycle evidence | Mode A has one terse first user-visible entry line containing `skill-improve`, `Mode A`, the event slug and RED state; run-4 is preserved and run 6 must pass the unchanged response assertions |
| R9 | The lifecycle wording consumes the always-loaded command budget | move existing validator/runner rationale to its canonical Mode A reference, compact only duplicated rationale, keep the 270,000 B ceiling and require a separate `floor <= 269000` probe before providers |
| R10 | Pre-load wording makes agent-prompt design look like skill/harness wiring | description distinguishes prompt drafting from registration/call-site work; the hook defers selection to that metadata; consumer-visible tests reject the old broad pointer while the lifecycle matrix remains the only stage authority |

## Phase 1 — Measured proactive lifecycle  [PARALLEL-SAFE]

- [x] **T1.1** — Repair the Codex trace oracle against the official event boundary
  Owns: skills/skill-improve/scripts/capture_trigger_evals.py, skills/skill-improve/scripts/test_capture_trigger_evals.py
  Needs: none
  Acceptance: Codex reports `load` only for an official `item.completed` command-execution event with `status=completed`, `exit_code=0`, and a command containing one of the exact normalized source/installed skill paths supplied by the caller; successful reads of both paths load, while response-only text, aggregated output, failed commands and Mode A text without a command skip; the fake uses the official wire shape; every prior snapshot, failure-diagnostic, Claude owner, UTF-8 and isolation contract remains green; exactly two new parseable baseline traces record `08a312ed3424376c7568c6d51b3dc263f7a31847` with `git_dirty=false` after `STATIC_READY` and before candidate capture.
  Agent: `graph-powers:debugger` · Skill: `graph-powers:skill-improve` · Effort: design
  TDD: required
  CHECK: `python3 -X utf8 -c "from pathlib import Path; import json,subprocess,sys; commands=[[sys.executable,'skills/skill-improve/scripts/test_run_evals.py'],[sys.executable,'skills/skill-improve/scripts/test_capture_trigger_evals.py']]; [subprocess.run(command,check=True) for command in commands]; root=Path('.claude/audit/skill-improve-proactivity/run-6/red'); names=['trace-codex-pro-precreate-skill.json','trace-claude-bound-agent-prompt-draft.json']; responses=['resp-pro-precreate-skill.txt','resp-bound-agent-prompt-draft.txt']; assert all((root/name).is_file() for name in names+responses); traces=[json.loads((root/name).read_text(encoding='utf-8')) for name in names]; required={'phase','backend','case_id','expected','observed','selected_owner','candidate_digest','candidate_file_count','prompt_digest','cli_version','reported_model','captured_at_utc','git_revision','git_dirty','child_exit'}; assert all(required<=set(trace) for trace in traces); assert {(trace['phase'],trace['backend'],trace['case_id'],trace['expected']) for trace in traces}=={('baseline','codex','pro-precreate-skill','load'),('baseline','claude','bound-agent-prompt-draft','skip')}; claude=next(trace for trace in traces if trace['backend']=='claude'); assert claude['selected_owner']=='graph-powers:senior-prompt-engineer'; oid='08a312ed3424376c7568c6d51b3dc263f7a31847'; assert len({trace['candidate_digest'] for trace in traces})==1 and all(trace['child_exit']==0 and trace['git_revision']==oid and trace['git_dirty'] is False for trace in traces); print('baseline eval capture boundary verified')"`
  EXPECT: `baseline eval capture boundary verified`
  EVIDENCE: run-5 diagnosis established RED: the prior parser classified a real successful source-path command as `skip`, classified path mentions in response/aggregated output as `load`, and the fake emitted nonexistent `item.arguments.path`. Run 6 RED: the focused official-shape test failed because `_parse_stream` did not accept caller-supplied paths. GREEN: 15/15 producer tests and 10/10 grader tests passed. `PINNED lifecycle hook RED verified 08a312ed3424376c7568c6d51b3dc263f7a31847` passed. The fresh baseline capture exited `0`; both traces share digest `ed9127ba3ef90ac8bcaa060e9a007842147480f24a1940defd7e55107e09a165` over 233 files, record the pinned revision with `git_dirty=false` and `child_exit=0`, and T1.1 CHECK printed `baseline eval capture boundary verified`. Codex recorded `(expected=load, observed=skip, selected_owner=null)`; Claude recorded `(expected=skip, observed=skip, selected_owner=graph-powers:senior-prompt-engineer)`. Run-5 artefacts remain immutable.
  Steps:
    1. Read the owned files and the preserved Round 9/design authority before editing. This stateful Lane A writer also owns T1.2, but every file still has one writer and T1.3 remains frozen.
    2. RED: add focused official-shape tests proving source-path and installed-path successful commands load, while response-only, aggregated-output-only, failed-command and implicit-text cases skip. Run only those tests and record their current failures before production edits.
    3. Preserve the historical pinned lifecycle RED without reverting the candidate. After the portable fixture is green, run the exact non-mutating command below against archived commit `08a312ed3424376c7568c6d51b3dc263f7a31847`; require the focused hook to exit `1` with exactly the two missing-pointer labels, record its controlled output in T1.1 EVIDENCE, and never edit the snapshot:
       `python3 -X utf8 -c "import runpy,subprocess,sys,tempfile; from pathlib import Path; api=runpy.run_path('skills/skill-improve/scripts/capture_trigger_evals.py'); temporary=tempfile.TemporaryDirectory(); root=Path(temporary.name); oid=api['materialize_plugin_ref'](Path('.').resolve(),'08a312ed3424376c7568c6d51b3dc263f7a31847',root); result=subprocess.run([sys.executable,str(root/'hooks'/'test_hooks.py'),'--focus','session-context-lifecycle'],cwd=root,capture_output=True,text=True,encoding='utf-8'); expected='FAILURES: claude emits one lifecycle pointer, codex emits one lifecycle pointer'; assert result.returncode==1 and result.stdout.splitlines()[-1]==expected,(result.returncode,result.stdout[-500:]); assert oid=='08a312ed3424376c7568c6d51b3dc263f7a31847',oid; print('PINNED lifecycle hook RED verified '+oid); temporary.cleanup()"`
    4. Verify, without rewriting, that the approved `proactivity-contract` cases and allowed lifecycle slugs already exist; only `pro-precreate-skill` and `bound-agent-prompt-draft` carry `proactive-live`, and the Claude negative keeps `expected_owner=graph-powers:senior-prompt-engineer`.
    5. GREEN: change `_parse_stream` to accept caller-supplied Codex skill paths and inspect only successful official completed command events. In `capture_trials`, supply both `<plugin-root>/skills/skill-improve/SKILL.md` and `<project>/.agents/skills/skill-improve/SKILL.md`; normalize separators without broad suffix or response matching. Preserve every other producer contract.
    6. Run these exact commands and record exit codes:
       `python3 skills/skill-improve/scripts/quick_validate.py skills/skill-improve`
       `python3 skills/skill-improve/scripts/test_run_evals.py`
       `python3 skills/skill-improve/scripts/test_capture_trigger_evals.py`
       `python3 .github/check_portability.py`
       the exact non-mutating `PINNED lifecycle hook RED verified` command from Step 3
    7. Signal `PARSER_READY`, freeze both T1.1 paths and continue directly into T1.2's pre-load routing RED/GREEN; never invoke Claude or Codex from the writer.
    8. Controller only, and only after T1.2 emits `STATIC_READY`: run the baseline commands verbatim and retain both outputs even when the assertion gate is the expected RED:
       `python3 skills/skill-improve/scripts/capture_trigger_evals.py --phase baseline --timeout-seconds 300 --plugin-root . --plugin-ref 08a312ed3424376c7568c6d51b3dc263f7a31847 --evals-path skills/skill-improve/evals/evals.json --response-dir .claude/audit/skill-improve-proactivity/run-6/red --trial codex:pro-precreate-skill --trial claude:bound-agent-prompt-draft`
       `python3 skills/skill-improve/scripts/run_evals.py --skill-path skills/skill-improve --evals-path skills/skill-improve/evals/evals.json --response-dir .claude/audit/skill-improve-proactivity/run-6/red --case-tag proactive-live --threshold 1.0`
    9. Controller confirms two responses, two traces, one common baseline digest and the recorded `PINNED lifecycle hook RED verified 08a312ed3424376c7568c6d51b3dc263f7a31847` output, then sends `RED_RECORDED` to Lane A. Missing provider infrastructure is `BLOCKED`.
    10. The controller runs the T1.1 CHECK, records its output in EVIDENCE, and immediately starts the frozen candidate capture from T1.2; Lane A remains paused and makes no edit.

- [ ] **T1.2** — Harden the post-load lifecycle entry protocol and close the measured candidate
  Owns: hooks/session_context.py, hooks/test_hooks.py, skills/skill-improve/learning.md
  Needs: none
  Acceptance: the existing lifecycle matrix remains the sole routing authority; after load, a Mode A or Mode B response emits its exact first non-empty lifecycle line before blocker, refusal, permission/tool observation, clarification, plan, draft or edit, including unavailable tools or Write permission; the run-8 bridge candidate pair passes the tagged grader at `1.0`, mandatory trace polarity, equal prompt digests, a changed digest against run-7/green and the first-line probe before `R10-F1` closes.
  Agent: `graph-powers:debugger` · Skill: `graph-powers:skill-improve` · Effort: design
  TDD: required
  CHECK: `python3 -X utf8 -c "from pathlib import Path; import json,runpy,re,subprocess,sys; commands=[[sys.executable,'hooks/test_hooks.py','--focus','session-context-lifecycle'],[sys.executable,'skills/skill-improve/scripts/quick_validate.py','skills/skill-improve'],[sys.executable,'skills/skill-improve/scripts/test_run_evals.py'],[sys.executable,'skills/skill-improve/scripts/run_evals.py','--skill-path','skills/skill-improve','--evals-path','skills/skill-improve/evals/evals.json','--response-dir','.claude/audit/skill-improve-proactivity/run-8/bridge-candidate','--case-tag','proactive-live','--threshold','1.0']]; [subprocess.run(command,check=True) for command in commands]; pointer=next(line for line in subprocess.check_output([sys.executable,'hooks/session_context.py'],input=b'{"hook_event_name":"SessionStart","source":"startup"}',cwd='.',stderr=subprocess.DEVNULL).decode(encoding='utf-8').splitlines() if 'Proactive skill lifecycle:' in line); assert len(pointer.encode(encoding='utf-8'))<=512 and 'emit the matching lifecycle entry first' in pointer and 'permission/tool observation' in pointer; skill=Path('skills/skill-improve/SKILL.md').read_text(encoding='utf-8'); assert skill.count('[HARD] Entry protocol')==1 and skill.index('[HARD] Entry protocol')<skill.index('| Stage observed'); learning=Path('skills/skill-improve/learning.md').read_text(encoding='utf-8'); tick=chr(96); assert learning.count('**Follow-up '+tick+'R10-F1'+tick+' — OPEN:**')==1 and learning.count('**Disposition '+tick+'R10-F1'+tick+' — CLOSED:**')==1 and 'run-8/bridge-candidate' in learning; names=['trace-codex-pro-precreate-skill.json','trace-claude-bound-agent-prompt-draft.json']; control=[json.loads((Path('.claude/audit/skill-improve-proactivity/run-7/green')/name).read_text(encoding='utf-8')) for name in names]; candidate=[json.loads((Path('.claude/audit/skill-improve-proactivity/run-8/bridge-candidate')/name).read_text(encoding='utf-8')) for name in names]; required={'phase','backend','case_id','expected','observed','selected_owner','candidate_digest','candidate_file_count','prompt_digest','cli_version','reported_model','captured_at_utc','git_revision','git_dirty','child_exit'}; assert all(required<=set(trace) for trace in control+candidate); assert {(trace['backend'],trace['case_id'],trace['expected'],trace['observed']) for trace in candidate}=={('codex','pro-precreate-skill','load','load'),('claude','bound-agent-prompt-draft','skip','skip')}; assert next(trace for trace in candidate if trace['backend']=='claude')['selected_owner']=='graph-powers:senior-prompt-engineer'; assert len({trace['candidate_digest'] for trace in control})==1 and len({trace['candidate_digest'] for trace in candidate})==1 and control[0]['candidate_digest']!=candidate[0]['candidate_digest']; assert {(trace['backend'],trace['case_id'],trace['prompt_digest']) for trace in control}=={(trace['backend'],trace['case_id'],trace['prompt_digest']) for trace in candidate}; first=next(line.strip() for line in (Path('.claude/audit/skill-improve-proactivity/run-8/bridge-candidate')/'resp-pro-precreate-skill.txt').read_text(encoding='utf-8').splitlines() if line.strip()); assert re.fullmatch(r'skill-improve Mode A — skill-authoring: RED (pending|established by evidence)',first),first; compute=runpy.run_path('skills/skill-improve/scripts/capture_trigger_evals.py')['compute_candidate_digest']; final_digest,file_count=compute(Path('.')); assert final_digest!=candidate[0]['candidate_digest']; print('proactive bridge candidate finalized')"`
  EXPECT: `proactive bridge candidate finalized`
  EVIDENCE: Run 6 remains immutable historical evidence: static discovery/routing passed and the Codex candidate trace was `load`, but its textual response was 0/3 because the blocker preceded the entry line; Claude was 2/2 with the alternate owner. Run 7 static RED/GREEN passed locally and froze `SKILL.md` plus `test_run_evals.py` at candidate digest `847fb4c720b0cd0a224e83d9a64bf0546d16398eaa64acc1c8a1941e6ffb2a98` (270 files). Fresh run-7 traces preserved the required polarity and common prompt digests, but the candidate textual grader exited `1`: Codex `0/3` and Claude `1/2`; the first-line probe also exited `1` because the Codex response began with a read-only blocker. No retry was allowed; `R10-F1` remains OPEN and the bounded run stops `NEEDS_WORK` for a later authorized correction.
  Steps:
    1. Read the design authority, the immutable run-7 body-only control and the current hook. Do not reopen or rewrite the skill body, description, parser, producer, sandbox, prompts, assertions, attribution or unrelated dirty files.
    2. RED: add a deterministic hook assertion that the current pointer lacks entry precedence; run the focused hook test and record the failure before production edits.
    3. GREEN: extend only `lifecycle_pointer()` with a concise conditional reminder that a matching Mode A/B lifecycle entry is first, before blocker, refusal, permission/tool observation, clarification, plan, draft or edit, including unavailable tools or Write permission. Keep the canonical templates and matrix in `SKILL.md`; do not duplicate them in the hook.
    4. Run the focused hook test, `quick_validate.py`, `test_run_evals.py`, portability, listing and context gates; preserve the 512-byte pointer cap and the unchanged first-line gate tag. Signal `STATIC_READY` with hashes and the run-7 control digest.
    5. Controller runs exactly one candidate capture against `run-7/green` into `run-8/bridge-candidate`, then the tagged grader and first-line probe. Require Codex `load` with the exact first line, Claude `skip` with `senior-prompt-engineer`, equal prompt digests and a changed candidate digest. No baseline rerun or retry:
       `python3 skills/skill-improve/scripts/capture_trigger_evals.py --phase candidate --timeout-seconds 300 --plugin-root . --evals-path skills/skill-improve/evals/evals.json --response-dir .claude/audit/skill-improve-proactivity/run-8/bridge-candidate --baseline-dir .claude/audit/skill-improve-proactivity/run-7/green --trial codex:pro-precreate-skill --trial claude:bound-agent-prompt-draft`
       `python3 skills/skill-improve/scripts/run_evals.py --skill-path skills/skill-improve --evals-path skills/skill-improve/evals/evals.json --response-dir .claude/audit/skill-improve-proactivity/run-8/bridge-candidate --case-tag proactive-live --threshold 1.0`
    6. On `GREEN_RECORDED`, Lane A appends only the dated CLOSED disposition for `R10-F1`, naming the run-7 control and run-8 bridge trace directory plus both digests, then runs the composite CHECK and emits `FINALIZED`; only then release the wave Evaluator.

- [x] **T1.3** — Record outside-digest attribution without disturbing the candidate
  Owns: NOTICE, CHANGELOG.md, package.json
  Needs: none
  Acceptance: the pinned repository, Eoghan Henn/Rebelytics, CC BY 4.0 and the nature of the adaptation are recorded; the unreleased `1.17.0` entry is extended after its preserved prefix; package SPDX is exactly `MIT AND Apache-2.0 AND CC-BY-4.0`.
  Agent: `graph-powers:debugger` · Skill: `graph-powers:skill-improve` · Effort: mechanical
  TDD: not-applicable (human-facing attribution and package metadata have no behavior unit; exact content and preservation probes are the executable acceptance)
  CHECK: `python3 -X utf8 -c "from pathlib import Path; import json; notice=Path('NOTICE').read_text(encoding='utf-8'); changelog=Path('CHANGELOG.md').read_text(encoding='utf-8'); package=json.loads(Path('package.json').read_text(encoding='utf-8')); required=['Eoghan Henn','Rebelytics','CC BY 4.0','510caad26c907793e48306262af216ff9f71c9f7']; assert all(value in notice for value in required),required; assert 'one-skill-to-rule-them-all' in changelog; assert package['license']=='MIT AND Apache-2.0 AND CC-BY-4.0'; print('outside-digest attribution verified')"`
  EXPECT: `outside-digest attribution verified`
  EVIDENCE: `outside-digest attribution verified`; preserved in externally created commit `08a312ed3424376c7568c6d51b3dc263f7a31847` before this recovery run.
  Steps:
    1. Run G1.9's distribution preservation probe before editing and read the current unreleased `1.17.0` section completely.
    2. Add one NOTICE attribution naming the pinned source, Eoghan Henn/Rebelytics, CC BY 4.0, the adapted mechanisms and that Graph Powers rewrote the implementation.
    3. Append one `1.17.0` changelog paragraph after the preserved prefix; do not rewrite existing bounded-fanout notes or version lines.
    4. Change only `package.json`'s licence field to `MIT AND Apache-2.0 AND CC-BY-4.0`; preserve all other bytes where practical.
    5. Run the task CHECK and G1.9 preservation command, signal `ATTRIBUTION_READY`, and make no further edit while the controller captures GREEN.

### Phase 1 gate

- [ ] **G1.1** — every Phase 1 task carries non-pending evidence
  CHECK: `python3 -X utf8 -c "from pathlib import Path; import re; text=Path('docs/plans/2026-09-01-skill-improve-proactivity/PLAN.md').read_text(encoding='utf-8'); ids=['T1.1','T1.2','T1.3']; assert all(re.search(r'- \[x\] \*\*'+re.escape(task)+r'\*\*',text) for task in ids); blocks=re.split(r'(?=- \[[ x]\] \*\*T1\.)',text); selected=[block for block in blocks if any(f'**{task}**' in block for task in ids)]; assert len(selected)==3 and all('EVIDENCE: pending' not in block.split('\n- [',1)[0] for block in selected); print('all Phase 1 task evidence recorded')"`
  EXPECT: `all Phase 1 task evidence recorded`
  EVIDENCE: pending

- [ ] **G1.2** — skill frontmatter and body remain valid
  CHECK: `python3 skills/skill-improve/scripts/quick_validate.py skills/skill-improve`
  EXPECT: `Skill is valid`
  EVIDENCE: pending

- [ ] **G1.3** — assertion selector regression suite passes
  CHECK: `python3 skills/skill-improve/scripts/test_run_evals.py`
  EXPECT: `OK`
  EVIDENCE: pending

- [ ] **G1.4** — official-shape capture producer suite passes
  CHECK: `python3 skills/skill-improve/scripts/test_capture_trigger_evals.py`
  EXPECT: `OK`
  EVIDENCE: pending

- [ ] **G1.5** — mandatory unprimed candidate sample passes
  CHECK: `python3 skills/skill-improve/scripts/run_evals.py --skill-path skills/skill-improve --evals-path skills/skill-improve/evals/evals.json --response-dir .claude/audit/skill-improve-proactivity/run-8/bridge-candidate --case-tag proactive-live --threshold 1.0`
  EXPECT: `PASSED: every case reached the threshold`
  EVIDENCE: pending — run-8 is the single bounded bridge sample; no retry is allowed.

- [ ] **G1.6** — wrong and nearest-negative responses are rejected
  CHECK: `python3 -X utf8 -c "import subprocess,sys,tempfile; from pathlib import Path; runner='skills/skill-improve/scripts/run_evals.py'; common=['--skill-path','skills/skill-improve','--evals-path','skills/skill-improve/evals/evals.json','--threshold','1.0']; handle=tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',delete=False); handle.write('generic answer with no lifecycle evidence'); handle.close(); wrong=subprocess.run([sys.executable,runner,*common,'--response-file',handle.name,'--test-case','pro-precreate-skill']).returncode; nearest=subprocess.run([sys.executable,runner,*common,'--response-file','.claude/audit/skill-improve-proactivity/run-8/bridge-candidate/resp-pro-precreate-skill.txt','--test-case','bound-agent-prompt-draft']).returncode; Path(handle.name).unlink(missing_ok=True); assert (wrong,nearest)==(1,1),(wrong,nearest); print('wrong-direction evals rejected')"`
  EXPECT: `wrong-direction evals rejected`
  EVIDENCE: pending

- [ ] **G1.7** — hook routing, wiring and budgets stay green
  CHECK: `python3 -X utf8 -c "import subprocess,sys; commands=[[sys.executable,'.github/check_wiring.py'],[sys.executable,'.github/check_codex_native.py'],['bun','.github/check_codex_policy.mjs'],[sys.executable,'.github/check_listing_budget.py'],[sys.executable,'.github/check_context_budget.py']]; [subprocess.run(command,check=True) for command in commands]; print('routing and budgets passed')"`
  EXPECT: `routing and budgets passed`
  EVIDENCE: pending

- [ ] **G1.8** — pre-existing `skill-improve` work is preserved
  CHECK: `python3 -X utf8 -c "from pathlib import Path; import hashlib; a=Path('skills/skill-improve/references/authoring.md').read_text(encoding='utf-8'); ab=a[a.index('### 5b. Run with-skill against baseline'):a.index('### 5c. Draft assertions while the runs complete')]; l=Path('skills/skill-improve/learning.md').read_text(encoding='utf-8'); rb=l[l.index('## Round 9 —'):].split('\n## Round 10 —',1)[0].rstrip()+'\n'; h=Path('skills/skill-improve/references/harness-wiring-audit.md').read_bytes(); got=(hashlib.sha256(ab.encode()).hexdigest(),hashlib.sha256(rb.encode()).hexdigest(),hashlib.sha256(h).hexdigest()); want=('6e739fb722751c7acd8f80f4fbc1bbcf6235cb2f4263c4763730f95c73496c07','620d42425e629fe3216295c38aa1e717bd13f09ac2bdd1eaf71b12214b8d94d0','ca476b801aea7a1e6ba145a75199af5bc3647510a3913e96e740fe7bf0cfcb72'); assert got==want,(got,want); print('pre-existing skill-improve work preserved')"`
  EXPECT: `pre-existing skill-improve work preserved`
  EVIDENCE: pending

- [ ] **G1.9** — pre-existing distribution work is preserved
  CHECK: `python3 -X utf8 -c "from pathlib import Path; import hashlib; H=lambda b:hashlib.sha256(b).hexdigest(); V=lambda t:next(x for x in t.splitlines(keepends=True) if '\"version\"' in x).encode(); c=Path('CHANGELOG.md').read_text(encoding='utf-8'); end='verification to the balanced Terra tier; both Codex generators consume the same semantic policy.'; cb=(c[c.index('## 1.17.0'):c.index(end)+len(end)].rstrip()+'\n').encode(); ps=['package.json','.claude-plugin/plugin.json','.codex-plugin/plugin.json','.cursor-plugin/plugin.json','.grok-plugin/plugin.json']; raw={p:Path(p).read_text(encoding='utf-8') for p in ps}; cl=raw['.codex-plugin/plugin.json'].splitlines(keepends=True); s=next(i for i,x in enumerate(cl) if '\"skills\"' in x); e=next(i for i in range(s+1,len(cl)) if cl[i].strip() in {']','],'}); cp=V(raw['.codex-plugin/plugin.json'])+(''.join(cl[s:e+1])+'commands_present='+str('\"commands\"' in raw['.codex-plugin/plugin.json'])+'\n').encode(); y=next(x for x in Path('plugin.yaml').read_text(encoding='utf-8').splitlines(keepends=True) if x.startswith('version:')); got=(H(cb),H(V(raw['package.json'])),H(V(raw['.claude-plugin/plugin.json'])),H(cp),H(V(raw['.cursor-plugin/plugin.json'])),H(V(raw['.grok-plugin/plugin.json'])),H(y.encode())); want=('c8075ea28f5c9a6e335bc8a976ed5096420af7fc549fce27f9f4c7d99e42d29b','f0f03e34179575271bdf57f3881c1367b0063c35bb50d2c157c01a8065de4cdc','f0f03e34179575271bdf57f3881c1367b0063c35bb50d2c157c01a8065de4cdc','dec3450975738b7ec6ff1172a7e72a56ab9d052454a3c3e8974862bb80b8ffad','f0f03e34179575271bdf57f3881c1367b0063c35bb50d2c157c01a8065de4cdc','f0f03e34179575271bdf57f3881c1367b0063c35bb50d2c157c01a8065de4cdc','f39e9279fb4d51bc5089e4a6307442badef20079387145cd079d0030efccd966'); assert got==want,(got,want); print('pre-existing distribution work preserved')"`
  EXPECT: `pre-existing distribution work preserved`
  EVIDENCE: pending

- [ ] **G1.10** — unrelated dirty files remain byte-identical
  CHECK: `python3 -X utf8 -c "from pathlib import Path; import hashlib; paths=['.claude-plugin/plugin.json', '.claude/rules/hooks.md', '.codex-plugin/plugin.json', '.cursor-plugin/plugin.json', '.github/check_codex_native.py', '.github/check_cursor.py', '.grok-plugin/plugin.json', 'AGENTS.md', 'AGENT_SETUP.md', 'CHANGELOG.md', 'NOTICE', 'README.md', 'cursor/install.mjs', 'docs/ARCHITECTURE.md', 'hermes/skills/graph-engineering/SKILL.md', 'hooks/AGENTS.md', 'hooks/graph_guardrails.py', 'hooks/hooks.json', 'hooks/subagent_context.py', 'package.json', 'plugin.yaml', 'references/execution-floor.md', 'references/shared-context.md', 'references/shared/005-method-bootstrap.md', 'references/shared/020-complexity-routing.md', 'references/shared/025-solution-ladder.md', 'references/shared/110-guardrails-index.md', 'skills/planning/SKILL.md', 'skills/planning/references/execution/implementer-prompt.md', 'skills/planning/references/issue-triage.md', 'skills/planning/scripts/sdd.py', 'skills/planning/scripts/test_sdd.py', 'skills/skill-improve/references/authoring.md']; got=tuple(hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in paths); want=('78b147136f8602b39264062b7ddfdd0c8f000f3486ffe05846dde42af10dbd50', 'f080d2fc67ea88dd65ec5004cbd3a8e3ba9e602639be52f2cd170c62b72b9725', '7c9d83f3c489aaac9ec18a1c8cff60987574e53f53a9b0bd0cfbecf6bd5cf0f6', '2de620ac56d0244ab7b29afb465dcbcee4155d00938562112e5a3d4406508d19', '092d9f3af55eafabd4952cd9aa82152731d014432c205e8a35101faa49404584', '61fcf8c568e8838aad7b04966a397d78fcbf508a8bfc1713d14c8baf440b6b28', '0bc989c3ab1bb04418d19b6acf70216ac9794059c3e416e420da1622ed897893', '6b220a34cfce07f546765b8d5cc5fc6d884f006bd4b1a450ce880efc81636f8e', '1048e5e28e02ae1bdc150be0a6db62d2798e40ed890adbd022c9e4d886d54ad7', 'e030e4a5b83bbcd039b07e8449d7f45ffe6650fefb421b2f66ae8979e41ff6d2', '08199967fb26405456a39167f31450c0f4d35b1f7ca4534b828ddd07d01292a7', 'a461570d9e0deffd1c420d96126606f62a2eb811edcf9259e34b529d79236302', 'fe1e8dfff854b8164df5c7b33b716372c3f45def04c144b008f83bd689c012e7', '8b81fac321fe4e5b97f01da65e675ed64222165ce40cbc2fa49ce4ff191ced29', 'ae1ebf1e91f37a595cf9b45cf5d911e30804149575b74f92388696c22197df83', 'b160c12ce6fb9dffd497f29b95df30532206db4aae0512dfc80d1ac1fb7eab36', '8d0f2a651b1ca6b170f51377f1caf5bbfa50ae3a10654dc349640c2c0b11d17f', 'bace44b0443586f04bd3959fb05e70e071102ad2933cd2c4fb4ed49dc8cf8e77', '24fa50ac482ac6127a8ebbeebe59b4dbbc9bfc2fd8d5734f5c03f106ba8ed5e5', '724081bd0358e8cf5f4d2c240706eee9df01b990474a1fc8abffcf7cb1e05143', '460b3dfe7be699e8288df92843bf74e14dcd49fcd9420690b4d725ad7fb2298b', 'e60e4296dbfd46b809b7bd7feae94e56fd74ca7a22e9d31f57ef6de967b36875', 'da13194669d43cb01dd648577918aaff5eda6f651d7cbf1670fb43cac069ba97', 'fa8d0ca4b84e235859dae082e8a1bbdfac8a4b457e6cb54ba2b6d627a68a8aef', 'de4c586c9c969bfec7aee6f520ba9b4ab0923db71468fbd364d820b43984482d', 'd4ceedec4d53dcc5dd13881f4a0616c1ade31dec6cc5c7a5c53b41403eb1e7fa', '94790a5110d8c1304e3f3f9857d57efda2148c4fc17c01292f6a33cb3cdcad58', '9481fdab36130acdb33bd4a9f59e60c4dfff9449a017b51ef9a209733d06b67f', 'fbbc015dd046f00f8f616a8a6a90c35d3b888b62c4a421d35bba41573d0fec9d', 'e5cd32bbf5e2f5e5130a8e084faced296197c6911d523da1828a22d7d70820b6', '748dd31e65dbb51b7816f6964c1f10531e605ce953869de31d07de3e820c5470', '273a48c1a9560e1e5f02e643ba8e08d1a07d4ae7ba0cb6b2f9b41145f388e534', '36ebb04a7b8a0c5f7dbb15a0f4950eeaf0e9d91a86052da42105b013a50020fe'); assert got==want,(got,want); print('pre-existing unrelated dirty work preserved')"`
  EXPECT: `pre-existing unrelated dirty work preserved`
  EVIDENCE: pending

- [ ] **G1.11** — no unowned path entered the working tree
  CHECK: `python3 -X utf8 -c "import subprocess; allowed={'.claude-plugin/plugin.json','.claude/rules/hooks.md','.codex-plugin/plugin.json','.cursor-plugin/plugin.json','.github/check_codex_native.py','.github/check_cursor.py','.grok-plugin/plugin.json','AGENTS.md','AGENT_SETUP.md','CHANGELOG.md','NOTICE','README.md','cursor/install.mjs','docs/ARCHITECTURE.md','docs/plans/2026-09-01-skill-improve-proactivity/PLAN.md','docs/plans/2026-09-01-skill-improve-proactivity/spec.md','hermes/skills/graph-engineering/SKILL.md','hooks/AGENTS.md','hooks/graph_guardrails.py','hooks/hooks.json','hooks/session_context.py','hooks/subagent_context.py','hooks/test_hooks.py','package.json','plugin.yaml','references/execution-floor.md','references/shared-context.md','references/shared/005-method-bootstrap.md','references/shared/020-complexity-routing.md','references/shared/025-solution-ladder.md','references/shared/110-guardrails-index.md','skills/planning/SKILL.md','skills/planning/references/execution/implementer-prompt.md','skills/planning/references/issue-triage.md','skills/planning/scripts/sdd.py','skills/planning/scripts/test_sdd.py','skills/skill-improve/SKILL.md','skills/skill-improve/learning.md','skills/skill-improve/references/authoring.md','skills/skill-improve/scripts/capture_trigger_evals.py','skills/skill-improve/scripts/test_capture_trigger_evals.py','skills/skill-improve/scripts/test_run_evals.py'}; raw=subprocess.run(['git','status','--porcelain=v1','-z','--untracked-files=all'],check=True,capture_output=True,text=True,encoding='utf-8').stdout; got={item[3:] for item in raw.split(chr(0)) if item}; extra=got-allowed; assert not extra,sorted(extra); print('phase ownership scope preserved')"`
  EXPECT: `phase ownership scope preserved`
  EVIDENCE: pending

- [ ] **G1.12** — undeclared type-check and lint are reported honestly
  CHECK: `python3 -X utf8 -c "from pathlib import Path; import json; commands=json.loads(Path('.graph-powers/config.json').read_text(encoding='utf-8'))['tooling']['commands']; assert 'typeCheck' not in commands and 'lint' not in commands; print('typeCheck=NOT DECLARED; lint=NOT DECLARED')"`
  EXPECT: `typeCheck=NOT DECLARED; lint=NOT DECLARED`
  EVIDENCE: pending

- [ ] **G1.13** — declared serial full test passes once at the final phase boundary
  CHECK: `python3 hooks/test_hooks.py`
  EXPECT: `EVERY GUARANTEE HELD`
  EVIDENCE: pending

- [x] **G1.14** — four live traces prove polarity and candidate-digest change without another provider run
  CHECK: `python3 -X utf8 -c "from pathlib import Path; import json; root=Path('.claude/audit/skill-improve-proactivity/run-7'); names=['trace-codex-pro-precreate-skill.json','trace-claude-bound-agent-prompt-draft.json']; red=[json.loads((root/'red'/name).read_text(encoding='utf-8')) for name in names]; green=[json.loads((root/'green'/name).read_text(encoding='utf-8')) for name in names]; required={'phase','backend','case_id','expected','observed','selected_owner','candidate_digest','candidate_file_count','prompt_digest','cli_version','reported_model','captured_at_utc','git_revision','git_dirty','child_exit'}; assert all(required<=set(trace) for trace in red+green); assert len({trace['candidate_digest'] for trace in red})==1; assert len({trace['candidate_digest'] for trace in green})==1; assert red[0]['candidate_digest']!=green[0]['candidate_digest']; assert {(trace['backend'],trace['case_id'],trace['expected'],trace['observed']) for trace in green}=={('codex','pro-precreate-skill','load','load'),('claude','bound-agent-prompt-draft','skip','skip')}; assert {trace['selected_owner'] for trace in red+green if trace['backend']=='claude'}=={'graph-powers:senior-prompt-engineer'}; assert {(trace['backend'],trace['case_id'],trace['prompt_digest']) for trace in red}=={(trace['backend'],trace['case_id'],trace['prompt_digest']) for trace in green}; oid='08a312ed3424376c7568c6d51b3dc263f7a31847'; assert all(trace['child_exit']==0 for trace in red+green); assert all(trace['git_revision']==oid and trace['git_dirty'] is False for trace in red); print('four live traces and candidate digest verified')"`
  EXPECT: `four live traces and candidate digest verified`
  EVIDENCE: `four live traces and candidate digest verified despite textual gate failure`; both run-7 trace pairs have `child_exit=0`, expected/observed polarity, stable prompt digests and changed baseline/candidate digests; run-7 candidate worktree is intentionally dirty.

- [ ] **G1.15** — pinned CC BY text and every licence projection agree
  CHECK: `python3 -X utf8 -c "from pathlib import Path; import hashlib,json; licence=Path('skills/skill-improve/LICENSE-CC-BY-4.0.txt').read_bytes(); assert len(licence)==18652 and hashlib.sha256(licence).hexdigest()=='50bfbf25300f4b6c06f5c286bc9f63b2fe43a548233d633a6798a78a785bdb98'; target='MIT AND Apache-2.0 AND CC-BY-4.0'; paths=['package.json','.claude-plugin/plugin.json','.codex-plugin/plugin.json','.cursor-plugin/plugin.json','.grok-plugin/plugin.json']; assert all(json.loads(Path(path).read_text(encoding='utf-8'))['license']==target for path in paths); assert 'license: \"'+target+'\"' in Path('plugin.yaml').read_text(encoding='utf-8'); print('pinned CC BY and licence projections verified')"`
  EXPECT: `pinned CC BY and licence projections verified`
  EVIDENCE: pending

- [ ] **G1.16** — the applicable follow-up is CLOSED and both candidate digests are recorded outside the digest surface
  CHECK: `python3 -X utf8 -c "from pathlib import Path; import json,runpy; learning=Path('skills/skill-improve/learning.md').read_text(encoding='utf-8'); tick=chr(96); assert learning.count('**Follow-up '+tick+'R10-F1'+tick+' — OPEN:**')==1 and learning.count('**Disposition '+tick+'R10-F1'+tick+' — CLOSED:**')==1 and 'run-8/bridge-candidate' in learning; root=Path('.claude/audit/skill-improve-proactivity/run-8/bridge-candidate'); names=['trace-codex-pro-precreate-skill.json','trace-claude-bound-agent-prompt-draft.json']; green=[json.loads((root/name).read_text(encoding='utf-8')) for name in names]; assert len({trace['candidate_digest'] for trace in green})==1; evaluated=green[0]['candidate_digest']; compute=runpy.run_path('skills/skill-improve/scripts/capture_trigger_evals.py')['compute_candidate_digest']; final_digest,file_count=compute(Path('.')); assert final_digest!=evaluated and file_count>0; plan=Path('docs/plans/2026-09-01-skill-improve-proactivity/PLAN.md').read_text(encoding='utf-8'); block=plan[plan.index('- [x] **T1.2**'):plan.index('- [x] **T1.3**')]; assert 'EVIDENCE: pending' not in block and evaluated in block and final_digest in block; print('follow-up closed and bridge candidate digest recorded')"`
  EXPECT: `follow-up closed and bridge candidate digest recorded`
  EVIDENCE: pending

- [ ] **G1.17** — lifecycle entry and pre-load exclusion are observable
  CHECK: `python3 -X utf8 -c "from pathlib import Path; s=Path('skills/skill-improve/SKILL.md').read_text(encoding='utf-8'); required=['first user-visible line','before any clarification, plan, draft or edit','skill-improve Mode A','RED <pending|established by evidence>','skill-improve Mode B','changed-edge baseline <pending|established by evidence>','Rows owned by another skill','agent registration/call-site changes','Agent-prompt drafting is senior-prompt-engineer']; assert all(value in s for value in required),[value for value in required if value not in s]; assert 'before adding an agent' not in s and s.count('skill-improve Mode A')==1 and s.count('skill-improve Mode B')==1; print('observable lifecycle entry contract verified')"`
  EXPECT: `observable lifecycle entry contract verified`
  EVIDENCE: pending

- [ ] **G1.18** — context floor retains at least 1,000 bytes of headroom without raising the ceiling
  CHECK: `python3 -X utf8 -c "import runpy; api=runpy.run_path('.github/check_context_budget.py'); floor,_=api['totals'](api['measure']()); assert api['FLOOR_CEILING']==270000,api['FLOOR_CEILING']; assert floor<=269000,(floor,269000); print('context floor headroom verified '+str(floor))"`
  EXPECT: `context floor headroom verified`
  EVIDENCE: pending

- [ ] **G1.19** — first non-empty Mode A line precedes a blocker
  CHECK: `python3 -X utf8 -c "from pathlib import Path; import re; first=lambda path:next(line.strip() for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()); pattern=r'skill-improve Mode A — skill-authoring: RED (pending|established by evidence)'; old=first('.claude/audit/skill-improve-proactivity/run-6/green/resp-pro-precreate-skill.txt'); control=first('.claude/audit/skill-improve-proactivity/run-7/green/resp-pro-precreate-skill.txt'); new=first('.claude/audit/skill-improve-proactivity/run-8/bridge-candidate/resp-pro-precreate-skill.txt'); assert not re.fullmatch(pattern,old),old; assert not re.fullmatch(pattern,control),control; assert re.fullmatch(pattern,new),new; print('first-line lifecycle bridge probe verified')"`
  EXPECT: `first-line lifecycle bridge probe verified`
  EVIDENCE: pending — run-6 and run-7 remain RED controls; run-8 is the only candidate probe.

- [ ] **G1.20** — SessionStart bridge makes the canonical entry protocol salient
  CHECK: `python3 -X utf8 -c "from pathlib import Path; import json,subprocess,sys; raw=subprocess.check_output([sys.executable,'hooks/session_context.py'],input=b'{\"hook_event_name\":\"SessionStart\",\"source\":\"startup\"}'); text=json.loads(raw.decode(encoding='utf-8'))['hookSpecificOutput']['additionalContext']; pointer=next(line for line in text.splitlines() if line.startswith('Proactive skill lifecycle:')); assert len(pointer.encode(encoding='utf-8'))<=512 and 'when skill-improve\'s description selects the task' in pointer and 'emit the matching lifecycle entry first' in pointer and 'permission/tool observation' in pointer and 'Mode A/B row' in pointer; print('SessionStart bridge precedence verified')"`
  EXPECT: `SessionStart bridge precedence verified`
  EVIDENCE: pending

## Verification

Focused acceptance is G1.2-G1.20. After the separate final Evaluator resolves every Critical and
Important finding, run `/verify loop docs/plans/2026-09-01-skill-improve-proactivity/PLAN.md` with
the lease held. Its final serial boundary runs every command below individually; no shell chaining,
staging, commit, push, PR or merge is authorized.

- `claude plugin validate .`
- `python3 hooks/test_hooks.py`
- `python3 .github/test_hook_clients.py`
- `python3 skills/planning/scripts/test_sdd.py`
- `python3 skills/skill-improve/scripts/test_run_evals.py`
- `python3 skills/skill-improve/scripts/test_capture_trigger_evals.py`
- `python3 -c "import ast,glob;[ast.parse(open(f).read()) for f in glob.glob('hooks/*.py')]"`
- `python3 -c "import json,glob;[json.load(open(f)) for f in glob.glob('**/*.json',recursive=True)+glob.glob('.*/*.json')]"`
- `bun .github/check_workflows.mjs`
- `bun .github/check_codex_policy.mjs`
- `python3 .github/check_codex_native.py`
- `python3 .github/check_oxc_policy.py`
- `python3 .github/check_wiring.py`
- `python3 .github/test_file_references.py`
- `python3 .github/check_file_references.py`
- `python3 .github/check_portability.py`
- `python3 .github/check_context_budget.py`
- `python3 .github/check_listing_budget.py`
- `python3 .github/check_machine_paths.py`
- `python3 .github/check_placeholders.py`
- `bun bin/graph-powers.mjs --help`
- `python3 .github/check_clone.py`
- `python3 .github/check_version_bump.py`
- `git diff --check`

On PASS, run `/evolve auto` and release the plan lease. If either live provider is unavailable,
authentication fails, a trace cannot be parsed, a candidate polarity is wrong, or another dispatch
is required, completion is `BLOCKED`/`NEEDS_WORK` with the exact evidence; synthetic fixtures never
 substitute for the two fresh bridge sessions.

## Rollback

- Remove the SessionStart lifecycle pointer and its focused tests; the existing project/branch/gates
  and execution-floor context remain unchanged.
- Revert the lifecycle matrix, authoring additions, capture producer, tag selector and new eval cases
  together; the original two-mode router, runner semantics and twelve-case suite remain valid.
- Remove only appended Round 10, provenance/changelog hunks and `LICENSE-CC-BY-4.0.txt`; restore
  `MIT AND Apache-2.0` in the two hand-owned sources and regenerate the four client projections.
- Never rewrite existing Round 9, bounded-fanout work or the unrelated dirty files. No database,
  external service, scheduler, installed skill or global configuration needs migration.

## Out of scope

| Excluded work | Trigger that would reopen it |
|---|---|
| General per-session observation log, scheduler or review queue | a separately approved observer product with its own storage/retention contract |
| Automatic patch application by `skill-improver` or another verifier | an explicit change to the no-verifier-writes cardinal |
| Global `SubagentStart` matcher or user configuration | a separate user-authorized global configuration task |
| Agent prompt design | a task explicitly routed to `senior-prompt-engineer` |
| Ordinary application failures, product “agents” or unrelated upgrades | two materially similar skill-rule misses or evidenced harness impact |
| Full cross-product live trigger benchmark | a separately approved measurement plan with additional provider budget |
| Full upstream observer/scheduler/staging transplant | a new destination that existing `/evolve`, SDD and execution-floor state cannot meet |

## Not yet specified

No design fog remains. Provider availability and the lack of a complete two-dispatch correction
pair are runtime stop conditions with explicit outcomes, not decisions delegated to an implementer.
