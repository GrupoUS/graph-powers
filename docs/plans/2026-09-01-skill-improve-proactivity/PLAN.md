# Proactive `skill-improve` lifecycle — implementation plan

**Date:** 2026-09-01 · **Branch:** `fix/bounded-agent-fanout` · **Baseline:** `8b6eb28`
**Tier:** L5 · **Risk surface:** SessionStart hooks, clean provider subprocesses, generated manifests, licence provenance
**Design authority:** `docs/plans/2026-09-01-skill-improve-proactivity/spec.md` — recovery Gate 1 PASS after one bounded correction

**Recovery run:** two prior Phase C attempts were safely aborted. The first bounded Claude routing;
the second exposed a producer false positive that treated any raw occurrence of `authentication` as
an auth failure even when the Codex child exited `0`. This amended run preserves completed T1.3 and
the lifecycle candidate, hardens provider-error classification and diagnostics, recreates RED from
an immutable `HEAD` plugin snapshot, and creates all four digest-consistent provider traces afresh.

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
| W1 | One weak description remains Mode A; a new skill runs Mode A before Mode B | `proactivity-contract` good/bad fixtures in `test_run_evals.py` | Phase 1 |
| W2 | Agent prompt design routes to `senior-prompt-engineer`; only later registration/wiring invokes Mode B | boundary fixture plus `claude:bound-agent-prompt-draft` live trace | Phase 1 |
| W3 | Ordinary application source, one isolated product failure and unrelated upgrades do not invoke `skill-improve` | three negative fixtures with explicit owner and no load event | Phase 1 |
| W4 | Mode B stays report-only and its paired judge cannot Write/Edit | wiring, Codex native-policy and semantic-policy gates | Phase 1 |
| W5 | Session context still reports project, branch, gates and the execution-floor pointer | full hook suite for Claude Code and Codex, including unchanged first line | Phase 1 |
| W6 | Bounded-fanout skill and release work from baseline remains byte-for-byte intact | the two exact SHA-256 preservation probes in G1.8 and G1.9 | Phase 1 |
| W7 | Skill listing remains below its entry and shared ceilings | `quick_validate.py` and `check_listing_budget.py` | Phase 1 |
| W8 | Always-on posture is exactly one bounded line and does not duplicate the lifecycle matrix | hook assertions plus `check_context_budget.py` | Phase 1 |
| W9 | Current unrelated edits, including the concurrent planning/workflow batch discovered during Gate 2, remain untouched | G1.10 hashes all ten unrelated dirty files against the post-drift planning snapshot; G1.11 permits them but never leases them | Phase 1 |

## File map

| Responsibility | Sole owner | Interface |
|---|---|---|
| Tagged assertion selection, live case data, provider adapters and deterministic RED | T1.1 | emits `PRODUCER_READY`, then baseline responses/traces under ignored `.claude/audit/`; failed trials emit bounded content-free diagnostics |
| Lifecycle activation, routing, follow-up state, CC BY source and generated projections | T1.2 | consumes controller tokens `RED_RECORDED` and `GREEN_RECORDED`; emits `CANDIDATE_READY`, then `FINALIZED` |
| Human-facing attribution and root package SPDX | T1.3 | uses the locked SPDX literal; emits `ATTRIBUTION_READY` and never reads a sibling patch |
| RED/GREEN provider execution | controller | runs the four exact commands in T1.1/T1.2; neither writer launches a child session |
| Assertions | existing `run_evals.py` | remains the single grader; the producer only captures responses and traces |

## Execution graph

```text
Lane A: T1.1 producer recovery ── PRODUCER_READY ── C1: two HEAD-snapshot BASELINE sessions ── RED_RECORDED ── T1.1 CHECK ── T1.2 candidate
Prior run: frozen T1.3 outside-digest attribution ────────────────────────────────────────┤
                                                                                         ├─ C2: two CANDIDATE sessions
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
| T1.1 → C1 | tagged eval schema, capture CLI, exact prompt digests and producer-ready freeze |
| C1 → T1.1/T1.2 | `RED_RECORDED`, baseline directory, common baseline digest, two parsed trace outcomes and the passing T1.1 CHECK |
| T1.2 → C2 | frozen digest surface, regenerated projections and `CANDIDATE_READY` |
| T1.3 → C2 | `ATTRIBUTION_READY`; no digest-root path is part of this payload |
| C2 → T1.2 | `GREEN_RECORDED`, two GREEN response/trace pairs, changed digest proof and tagged grader output |
| T1.2 → wave review | `FINALIZED`, CLOSED `R10-F1`, evaluated/final digest output and passing composite task CHECK |
| wave review → phase gate | per-task compliance/quality verdict plus one integration verdict |

The control nodes are parent operations, not task dependencies. T1.1 and T1.2 are dispatched once
as one stateful Lane A package; T1.2 waits in that reserved writer session for `RED_RECORDED`, then
for `GREEN_RECORDED` after it freezes the candidate. Controller follow-ups resume that same session
and do not consume a new dispatch slot. T1.3 is a separate, incompatible mechanical context and
therefore a second writer package even though both packages use the same canonical writer role.

## Dispatch budget

| Slot | Operation | Accounting evidence |
|---:|---|---|
| 1 | Recovery Lane A writer for T1.1 + T1.2 | `sdd.py dispatch` writer reservation |
| 2-3 | Codex positive + Claude negative BASELINE sessions | exactly two new RED trace files |
| 4-5 | Codex positive + Claude negative CANDIDATE sessions | exactly two new GREEN trace files |
| 6 | one consolidated wave Evaluator, including frozen T1.3 | `sdd.py dispatch` evaluator reservation |
| 7 | separate final Evaluator | reserved before the first wave |
| 8 | unused failure boundary | no dispatch; any required correction returns bounded `NEEDS_WORK` |

The four provider subprocesses are not Graph Powers roles accepted by the SDD dispatch ledger, so
their exact trace count is the mechanical accounting surface; the controller combines those four
with the three SDD reservations before dispatch. T1.3's prior writer is historical evidence, not a
dispatch in this run. No other provider trial, bootstrap, consultation, confirmation or correction
is permitted. Any failure that needs another dispatch ends
the run as bounded `NEEDS_WORK`; it is never hidden by resetting the ledger.

## Dispatch matrix

| Task | Agent | Skill | Owns | Needs |
|---|---|---|---|---|
| T1.1 | `graph-powers:debugger` | `graph-powers:skill-improve` | `hooks/test_hooks.py`; `skills/skill-improve/evals/evals.json`; `skills/skill-improve/scripts/run_evals.py`; `skills/skill-improve/scripts/test_run_evals.py`; `skills/skill-improve/scripts/capture_trigger_evals.py`; `skills/skill-improve/scripts/test_capture_trigger_evals.py` | — |
| T1.2 | `graph-powers:debugger` | `graph-powers:skill-improve` | `.claude/rules/artifacts.md`; `hooks/session_context.py`; `skills/skill-improve/SKILL.md`; `skills/skill-improve/references/authoring.md`; `skills/skill-improve/learning.md`; `skills/skill-improve/LICENSE-CC-BY-4.0.txt`; `.claude-plugin/plugin.json`; `.codex-plugin/plugin.json`; `.cursor-plugin/plugin.json`; `.grok-plugin/plugin.json`; `plugin.yaml` | — |
| T1.3 | `graph-powers:debugger` | `graph-powers:skill-improve` | `NOTICE`; `CHANGELOG.md`; `package.json` | — |

### Mini-contract: Phase 1

**Sprint 1:** installs a measured, bounded proactive lifecycle in `skill-improve`, verified by the
fresh-session pair, focused contracts and repository gates, and excludes a general observer,
scheduler, automatic patching, global configuration changes and any claim of suite-wide hit rate.

## Risk controls

| # | Failure mode | Control |
|---|---|---|
| R1 | A concurrent writer changes the digest during RED/GREEN | all digest-root changes and projections are in Lane A; files freeze at both controller checkpoints |
| R2 | A primed prompt manufactures a positive | producer rejects skill names, modes, load instructions and eval/probe vocabulary before launch |
| R3 | Provider absence, authentication, timeout or malformed JSONL is mistaken for a negative, or ordinary response text is mistaken for auth failure | capture exits `1` on infrastructure failures; authentication requires a top-level structured error record, not raw substring search; every failure writes only hashes/counts and controlled metadata; Claude is non-persistent and exposes exactly the `Skill` tool |
| R4 | Mode B or its judge gains a write path | lifecycle matrix keeps Mode B report-only; wiring/native/policy gates remain mandatory |
| R5 | Attribution drops MIT/Apache or generated manifests drift | exact target is `MIT AND Apache-2.0 AND CC-BY-4.0`; Claude is source and all four clients regenerate |
| R6 | First review needs correction but only one of eight slots remains | a correction requires its writer plus a fresh Evaluator; persist completed evidence and return `NEEDS_WORK`, and only a later user-requested run may continue |
| R7 | Concurrent work changes again after approval and contaminates RED/GREEN | G1.10 is a byte-for-byte preflight and phase gate; any mismatch stops before provider capture and requires a refreshed plan snapshot |

## Phase 1 — Measured proactive lifecycle  [PARALLEL-SAFE]

- [ ] **T1.1** — Build the tagged eval selector and clean-session capture boundary
  Owns: hooks/test_hooks.py, skills/skill-improve/evals/evals.json, skills/skill-improve/scripts/run_evals.py, skills/skill-improve/scripts/test_run_evals.py, skills/skill-improve/scripts/capture_trigger_evals.py, skills/skill-improve/scripts/test_capture_trigger_evals.py
  Needs: none
  Acceptance: tagged cases are selected only with per-case response directories; zero matches and missing responses fail; fake Claude/Codex streams prove fresh unprimed capture, the exact bounded Claude command, the required alternate-owner event, structured provider failures and exact-schema content-free failure diagnostics; stdout/stderr/environment sentinels never escape; a successful JSONL stream containing `authentication` passes; snapshot tests prove dirty-byte exclusion, reject non-`HEAD`/candidate-phase refs plus absolute, traversal, symlink and hard-link archive members; exactly two new parseable baseline traces record the one resolved full `HEAD` OID with `git_dirty=false` before candidate finalization.
  Agent: `graph-powers:debugger` · Skill: `graph-powers:skill-improve` · Effort: design
  TDD: required
  CHECK: `python3 -X utf8 -c "from pathlib import Path; import json,subprocess,sys; commands=[[sys.executable,'skills/skill-improve/scripts/test_run_evals.py'],[sys.executable,'skills/skill-improve/scripts/test_capture_trigger_evals.py']]; [subprocess.run(command,check=True) for command in commands]; root=Path('.claude/audit/skill-improve-proactivity/run-3/red'); names=['trace-codex-pro-precreate-skill.json','trace-claude-bound-agent-prompt-draft.json']; responses=['resp-pro-precreate-skill.txt','resp-bound-agent-prompt-draft.txt']; assert all((root/name).is_file() for name in names+responses); traces=[json.loads((root/name).read_text(encoding='utf-8')) for name in names]; required={'phase','backend','case_id','expected','observed','selected_owner','candidate_digest','candidate_file_count','prompt_digest','cli_version','reported_model','captured_at_utc','git_revision','git_dirty','child_exit'}; assert all(required<=set(trace) for trace in traces); assert {(trace['phase'],trace['backend'],trace['case_id'],trace['expected']) for trace in traces}=={('baseline','codex','pro-precreate-skill','load'),('baseline','claude','bound-agent-prompt-draft','skip')}; claude=next(trace for trace in traces if trace['backend']=='claude'); assert claude['selected_owner']=='graph-powers:senior-prompt-engineer'; oid=subprocess.run(['git','rev-parse','HEAD'],check=True,capture_output=True,text=True,encoding='utf-8').stdout.strip(); assert len({trace['candidate_digest'] for trace in traces})==1 and all(trace['child_exit']==0 and trace['git_revision']==oid and trace['git_dirty'] is False for trace in traces); print('baseline eval capture boundary verified')"`
  EXPECT: `baseline eval capture boundary verified`
  EVIDENCE: pending
  Steps:
    1. Read the owned files and the preserved Round 9/design authority before editing; do not touch any T1.2 or T1.3 path.
    2. RED: retain the runner selector coverage and add a producer regression whose child exits `0` with valid JSONL and response/tool content containing `authentication`; prove the current raw substring detector fails it. Add a separate top-level structured authentication-error case that must fail. Put unique sentinels in fake stdout, stderr and environment; capture console and audit files; assert the exact diagnostic key set, closed `failure_kind`, byte counts/digests, absence of all sentinels, and absence of normal response/trace files. Before implementing snapshot support, add cases proving a committed file wins over a conflicting dirty edit; only literal `HEAD` is accepted; candidate phase rejects the flag; and absolute, parent-traversal, symlink and hard-link archive members fail before extraction. Retain fresh-directory, exact-prompt, polarity, malformed/incomplete JSONL, timeout, missing executable and exact alternate-owner cases.
    3. Preserve the historical lifecycle RED without reverting the candidate. After the snapshot helper is green, run the exact non-mutating command below against archived `HEAD`; require the focused hook to exit `1` with exactly the two missing-pointer labels, record its controlled output in T1.1 EVIDENCE, and never edit the snapshot:
       `python3 -X utf8 -c "import runpy,subprocess,sys,tempfile; from pathlib import Path; api=runpy.run_path('skills/skill-improve/scripts/capture_trigger_evals.py'); temporary=tempfile.TemporaryDirectory(); root=Path(temporary.name); oid=api['materialize_plugin_ref'](Path('.').resolve(),'HEAD',root); result=subprocess.run([sys.executable,str(root/'hooks'/'test_hooks.py'),'--focus','session-context-lifecycle'],cwd=root,capture_output=True,text=True,encoding='utf-8'); expected='FAILURES: claude emits one lifecycle pointer, codex emits one lifecycle pointer'; assert result.returncode==1 and expected in result.stdout,(result.returncode,result.stdout[-500:]); print('HEAD lifecycle hook RED verified '+oid); temporary.cleanup()"`
    4. Add the approved `proactivity-contract` cases and exact allowed lifecycle slugs to `evals.json`; tag only `pro-precreate-skill` and `bound-agent-prompt-draft` as `proactive-live`, and give the bounded Claude negative the exact `expected_owner` value `graph-powers:senior-prompt-engineer`.
    5. GREEN: preserve the existing grader and capture interfaces, then replace raw auth substring matching with top-level structured provider-error classification. Add baseline-only literal `--plugin-ref HEAD`: resolve it once to a full OID, archive that OID, reject absolute/traversal/link members before extraction, and stamp the OID with `git_dirty=false`; candidate phase rejects the flag. Responses remain `resp-<case-id>.txt`; successful traces retain their existing schema. Failures use only the spec's closed kind vocabulary and exact diagnostic keys. Console prints only backend/case/kind; never persist or print raw output, exception text or environment values. Preserve the exact Claude isolation command and prompt bytes.
    6. Run these exact commands and record exit codes:
       `python3 skills/skill-improve/scripts/quick_validate.py skills/skill-improve`
       `python3 skills/skill-improve/scripts/test_run_evals.py`
       `python3 skills/skill-improve/scripts/test_capture_trigger_evals.py`
       the exact non-mutating `HEAD lifecycle hook RED verified` command from Step 3
    7. Recovery run: first run the successful-stream `authentication` regression RED against the current producer, then implement only the structured-error, diagnostic and `--plugin-ref` corrections and rerun the three focused commands. Refactor while green, signal `PRODUCER_READY`, freeze every owned path and wait; never invoke Claude or Codex from the writer.
    8. Controller only: run the baseline commands verbatim and retain both outputs even when the assertion gate is the expected RED:
       `python3 skills/skill-improve/scripts/capture_trigger_evals.py --phase baseline --timeout-seconds 300 --plugin-root . --plugin-ref HEAD --evals-path skills/skill-improve/evals/evals.json --response-dir .claude/audit/skill-improve-proactivity/run-3/red --trial codex:pro-precreate-skill --trial claude:bound-agent-prompt-draft`
       `python3 skills/skill-improve/scripts/run_evals.py --skill-path skills/skill-improve --evals-path skills/skill-improve/evals/evals.json --response-dir .claude/audit/skill-improve-proactivity/run-3/red --case-tag proactive-live --threshold 1.0`
    9. Controller confirms two responses, two traces, one common baseline digest and the recorded `HEAD lifecycle hook RED verified <full-oid>` output, then sends `RED_RECORDED` to Lane A. Missing provider infrastructure is `BLOCKED`.
    10. Lane A consumes `RED_RECORDED`, runs the T1.1 CHECK, records its output in EVIDENCE and only then starts T1.2 production edits.

- [ ] **T1.2** — Activate the lifecycle and stabilize the licensed candidate projections
  Owns: .claude/rules/artifacts.md, hooks/session_context.py, skills/skill-improve/SKILL.md, skills/skill-improve/references/authoring.md, skills/skill-improve/learning.md, skills/skill-improve/LICENSE-CC-BY-4.0.txt, .claude-plugin/plugin.json, .codex-plugin/plugin.json, .cursor-plugin/plugin.json, .grok-plugin/plugin.json, plugin.yaml
  Needs: none
  Acceptance: both clients receive one fail-open lifecycle pointer of at most 512 UTF-8 bytes; the single lifecycle matrix routes every approved stage and exclusion; Round 10 disposes `R10-F1`; the pinned CC BY source and all generated clients preserve MIT/Apache and the mandatory live candidate pair passes at `1.0` with a changed digest.
  Agent: `graph-powers:debugger` · Skill: `graph-powers:skill-improve` · Effort: design
  TDD: required
  CHECK: `python3 -X utf8 -c "from pathlib import Path; import hashlib,json,runpy,subprocess,sys; commands=[[sys.executable,'hooks/test_hooks.py','--focus','session-context-lifecycle'],[sys.executable,'skills/skill-improve/scripts/quick_validate.py','skills/skill-improve'],[sys.executable,'skills/skill-improve/scripts/run_evals.py','--skill-path','skills/skill-improve','--evals-path','skills/skill-improve/evals/evals.json','--response-dir','.claude/audit/skill-improve-proactivity/run-3/green','--case-tag','proactive-live','--threshold','1.0']]; [subprocess.run(command,check=True) for command in commands]; skill=Path('skills/skill-improve/SKILL.md').read_text(encoding='utf-8'); authoring=Path('skills/skill-improve/references/authoring.md').read_text(encoding='utf-8'); learning=Path('skills/skill-improve/learning.md').read_text(encoding='utf-8'); stage_markers=['Stage observed before task close','Create a skill','Register a newly authored skill','Design or revise one agent','Register, remove or rename an agent','Plugin/model upgrade','Two materially similar misses','Competing descriptions','Task boundary','Mode A','Mode B','senior-prompt-engineer','Typo/prose-only','application/product failure']; assert all(marker in skill for marker in stage_markers); slugs=['skill-authoring','skill-wiring','agent-wiring','harness-upgrade','repeated-skill-miss','trigger-collision','proactive-routing']; assert all(slug in skill+'\n'+authoring for slug in slugs); tick=chr(96); open_record='**Follow-up '+tick+'R10-F1'+tick+' — OPEN:**'; closed_record='**Disposition '+tick+'R10-F1'+tick+' — CLOSED:**'; assert learning.count(open_record)==1 and learning.count(closed_record)==1 and '.claude/audit/skill-improve-proactivity/run-3/green' in learning; root=Path('.claude/audit/skill-improve-proactivity/run-3'); names=['trace-codex-pro-precreate-skill.json','trace-claude-bound-agent-prompt-draft.json']; red=[json.loads((root/'red'/name).read_text(encoding='utf-8')) for name in names]; green=[json.loads((root/'green'/name).read_text(encoding='utf-8')) for name in names]; assert {(trace['backend'],trace['case_id'],trace['expected'],trace['observed']) for trace in green}=={('codex','pro-precreate-skill','load','load'),('claude','bound-agent-prompt-draft','skip','skip')}; assert next(trace for trace in red if trace['backend']=='claude')['selected_owner']=='graph-powers:senior-prompt-engineer'; assert next(trace for trace in green if trace['backend']=='claude')['selected_owner']=='graph-powers:senior-prompt-engineer'; assert len({trace['candidate_digest'] for trace in red})==1 and len({trace['candidate_digest'] for trace in green})==1 and red[0]['candidate_digest']!=green[0]['candidate_digest']; assert {(trace['backend'],trace['case_id'],trace['prompt_digest']) for trace in red}=={(trace['backend'],trace['case_id'],trace['prompt_digest']) for trace in green}; licence=Path('skills/skill-improve/LICENSE-CC-BY-4.0.txt').read_bytes(); assert len(licence)==18652 and hashlib.sha256(licence).hexdigest()=='50bfbf25300f4b6c06f5c286bc9f63b2fe43a548233d633a6798a78a785bdb98'; target='MIT AND Apache-2.0 AND CC-BY-4.0'; paths=['package.json','.claude-plugin/plugin.json','.codex-plugin/plugin.json','.cursor-plugin/plugin.json','.grok-plugin/plugin.json']; assert all(json.loads(Path(path).read_text(encoding='utf-8'))['license']==target for path in paths) and 'license: \"'+target+'\"' in Path('plugin.yaml').read_text(encoding='utf-8'); compute=runpy.run_path('skills/skill-improve/scripts/capture_trigger_evals.py')['compute_candidate_digest']; final_digest,file_count=compute(Path('.')); evaluated=green[0]['candidate_digest']; assert final_digest!=evaluated; print('evaluated candidate digest '+evaluated); print('final evidence-only digest '+final_digest+' files='+str(file_count)); print('proactive lifecycle candidate finalized')"`
  EXPECT: `proactive lifecycle candidate finalized`
  EVIDENCE: pending
  Steps:
    1. Read `hooks/AGENTS.md`, every owned source and the design authority. On initial Lane A dispatch, inspect only; do not edit until the controller sends `RED_RECORDED`.
    2. GREEN: extend `session_context.py` with one conditional pointer after the execution-floor line, canonical-path resolution, relative fallback at 512 UTF-8 bytes and fail-open behavior; make the T1.1 hook RED pass without changing the first line.
    3. Add the single `Stage observed before task close` → owner → timing → minimum evidence → exclusion matrix to `SKILL.md`, preserving the approved row wording that the task CHECK names and the allowed slugs `skill-authoring`, `skill-wiring`, `agent-wiring`, `harness-upgrade`, `repeated-skill-miss`, `trigger-collision` and `proactive-routing`; add lifecycle RED, repeated-miss threshold, unprimed trials and structured follow-up dispositions to `authoring.md` outside the preserved `5b` block; update the existing local artefact reminder without copying the matrix.
    4. Extend the learning template, append Round 10 and create `R10-F1` as OPEN. Do not alter any earlier round or claim a suite-wide hit rate.
    5. Retrieve the full CC BY 4.0 text only from pinned source `https://raw.githubusercontent.com/rebelytics/one-skill-to-rule-them-all/510caad26c907793e48306262af216ff9f71c9f7/LICENSE.txt`; require 18,652 bytes and SHA-256 `50bfbf25300f4b6c06f5c286bc9f63b2fe43a548233d633a6798a78a785bdb98`, add it as `LICENSE-CC-BY-4.0.txt`, retain `LICENSE.txt`, and set `.claude-plugin/plugin.json` to `MIT AND Apache-2.0 AND CC-BY-4.0`.
    6. Regenerate, never hand-edit, the four projections:
       `bun codex/native-plugin.mjs --emit-only`
       `bun cursor/install.mjs --emit-only`
       `bun grok/install.mjs --emit-only`
       `bun hermes/install.mjs --emit-only`
    7. Run these focused checks exactly and require exit `0`: `python3 hooks/test_hooks.py --focus session-context-lifecycle`; `python3 skills/skill-improve/scripts/quick_validate.py skills/skill-improve`; the literal G1.8 preservation CHECK; the literal G1.10 unrelated-dirty-files CHECK; and `python3 -X utf8 -c "from pathlib import Path; import hashlib,json; skill=Path('skills/skill-improve/SKILL.md').read_text(encoding='utf-8'); authoring=Path('skills/skill-improve/references/authoring.md').read_text(encoding='utf-8'); learning=Path('skills/skill-improve/learning.md').read_text(encoding='utf-8'); stage_markers=['Stage observed before task close','Create a skill','Register a newly authored skill','Design or revise one agent','Register, remove or rename an agent','Plugin/model upgrade','Two materially similar misses','Competing descriptions','Task boundary','Mode A','Mode B','senior-prompt-engineer','Typo/prose-only','application/product failure']; assert all(marker in skill for marker in stage_markers); slugs=['skill-authoring','skill-wiring','agent-wiring','harness-upgrade','repeated-skill-miss','trigger-collision','proactive-routing']; assert all(slug in skill+'\n'+authoring for slug in slugs); tick=chr(96); open_record='**Follow-up '+tick+'R10-F1'+tick+' — OPEN:**'; closed_record='**Disposition '+tick+'R10-F1'+tick+' — CLOSED:**'; assert learning.count(open_record)==1 and learning.count(closed_record)==0; licence=Path('skills/skill-improve/LICENSE-CC-BY-4.0.txt').read_bytes(); assert len(licence)==18652 and hashlib.sha256(licence).hexdigest()=='50bfbf25300f4b6c06f5c286bc9f63b2fe43a548233d633a6798a78a785bdb98'; target='MIT AND Apache-2.0 AND CC-BY-4.0'; paths=['.claude-plugin/plugin.json','.codex-plugin/plugin.json','.cursor-plugin/plugin.json','.grok-plugin/plugin.json']; assert all(json.loads(Path(path).read_text(encoding='utf-8'))['license']==target for path in paths) and 'license: \"'+target+'\"' in Path('plugin.yaml').read_text(encoding='utf-8'); print('candidate static contract verified')"`. Refactor while green, then signal `CANDIDATE_READY` and freeze all owned paths. Repository-wide wiring, policy, clone and full-hook commands remain only in the phase gate.
    8. Controller waits for `ATTRIBUTION_READY`, then runs the candidate commands verbatim:
       `python3 skills/skill-improve/scripts/capture_trigger_evals.py --phase candidate --timeout-seconds 300 --plugin-root . --evals-path skills/skill-improve/evals/evals.json --response-dir .claude/audit/skill-improve-proactivity/run-3/green --baseline-dir .claude/audit/skill-improve-proactivity/run-3/red --trial codex:pro-precreate-skill --trial claude:bound-agent-prompt-draft`
       `python3 skills/skill-improve/scripts/run_evals.py --skill-path skills/skill-improve --evals-path skills/skill-improve/evals/evals.json --response-dir .claude/audit/skill-improve-proactivity/run-3/green --case-tag proactive-live --threshold 1.0`
    9. Controller verifies both GREEN traces and the tagged gate, then sends `GREEN_RECORDED` with their directory, common evaluated digest and grader output to the reserved Lane A session; no new writer or provider slot is opened.
    10. Lane A appends only the dated CLOSED disposition for `R10-F1`, naming the bounded two-case sample and trace directory, then runs the composite T1.2 CHECK. Its PLAN EVIDENCE records the earlier `HEAD lifecycle hook RED verified <full-oid>` line, current hook GREEN, evaluated candidate digest and different final evidence-only digest; PLAN is outside the digest surface. Lane A emits `FINALIZED`; no owned path changes after that token, and only `FINALIZED` releases the wave Evaluator.

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

- [ ] **G1.4** — capture producer fake-stream suite passes
  CHECK: `python3 skills/skill-improve/scripts/test_capture_trigger_evals.py`
  EXPECT: `OK`
  EVIDENCE: pending

- [ ] **G1.5** — mandatory unprimed candidate sample passes
  CHECK: `python3 skills/skill-improve/scripts/run_evals.py --skill-path skills/skill-improve --evals-path skills/skill-improve/evals/evals.json --response-dir .claude/audit/skill-improve-proactivity/run-3/green --case-tag proactive-live --threshold 1.0`
  EXPECT: `PASSED: every case reached the threshold`
  EVIDENCE: pending

- [ ] **G1.6** — wrong and nearest-negative responses are rejected
  CHECK: `python3 -X utf8 -c "import subprocess,sys,tempfile; from pathlib import Path; runner='skills/skill-improve/scripts/run_evals.py'; common=['--skill-path','skills/skill-improve','--evals-path','skills/skill-improve/evals/evals.json','--threshold','1.0']; handle=tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',delete=False); handle.write('generic answer with no lifecycle evidence'); handle.close(); wrong=subprocess.run([sys.executable,runner,*common,'--response-file',handle.name,'--test-case','pro-precreate-skill']).returncode; nearest=subprocess.run([sys.executable,runner,*common,'--response-file','.claude/audit/skill-improve-proactivity/run-3/green/resp-pro-precreate-skill.txt','--test-case','bound-agent-prompt-draft']).returncode; Path(handle.name).unlink(missing_ok=True); assert (wrong,nearest)==(1,1),(wrong,nearest); print('wrong-direction evals rejected')"`
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
  CHECK: `python3 -X utf8 -c "from pathlib import Path; import hashlib; H=lambda b:hashlib.sha256(b).hexdigest(); V=lambda t:next(x for x in t.splitlines(keepends=True) if '\"version\"' in x).encode(); c=Path('CHANGELOG.md').read_text(encoding='utf-8'); end='verification to the balanced Terra tier; both Codex generators consume the same semantic policy.'; cb=(c[c.index('## 1.17.0'):c.index(end)+len(end)].rstrip()+'\n').encode(); ps=['package.json','.claude-plugin/plugin.json','.codex-plugin/plugin.json','.cursor-plugin/plugin.json','.grok-plugin/plugin.json']; raw={p:Path(p).read_text(encoding='utf-8') for p in ps}; cl=raw['.codex-plugin/plugin.json'].splitlines(keepends=True); s=next(i for i,x in enumerate(cl) if '\"skills\"' in x); e=next(i for i in range(s+1,len(cl)) if cl[i].strip() in {']','],'}); cp=V(raw['.codex-plugin/plugin.json'])+(''.join(cl[s:e+1])+'commands_present='+str('\"commands\"' in raw['.codex-plugin/plugin.json'])+'\n').encode(); y=next(x for x in Path('plugin.yaml').read_text(encoding='utf-8').splitlines(keepends=True) if x.startswith('version:')); got=(H(cb),H(V(raw['package.json'])),H(V(raw['.claude-plugin/plugin.json'])),H(cp),H(V(raw['.cursor-plugin/plugin.json'])),H(V(raw['.grok-plugin/plugin.json'])),H(y.encode())); want=('c8075ea28f5c9a6e335bc8a976ed5096420af7fc549fce27f9f4c7d99e42d29b','944d9f558ff298640a3e895a02cce431f6ebc8f3fd0e78ec983bad07a5fbcd7f','944d9f558ff298640a3e895a02cce431f6ebc8f3fd0e78ec983bad07a5fbcd7f','fdaabf49e7bdc8373b59fff57128040917fc98d9d349064cc36ef8c9de55476b','944d9f558ff298640a3e895a02cce431f6ebc8f3fd0e78ec983bad07a5fbcd7f','944d9f558ff298640a3e895a02cce431f6ebc8f3fd0e78ec983bad07a5fbcd7f','f65bad2f72a503c9b4714371f2a34731da8b9a989463e4c5e537bd79fbbd1963'); assert got==want,(got,want); print('pre-existing distribution work preserved')"`
  EXPECT: `pre-existing distribution work preserved`
  EVIDENCE: pending

- [ ] **G1.10** — unrelated dirty files remain byte-identical
  CHECK: `python3 -X utf8 -c "from pathlib import Path; import hashlib; paths=['.github/check_codex_native.py','.github/check_workflows.mjs','AGENT_SETUP.md','codex/install.mjs','commands/debug.md','skills/planning/references/phase-c-executing-plans.md','skills/planning/scripts/sdd.py','skills/planning/scripts/test_sdd.py','workflows/ultra-plan.js','workflows/ultra-verify.js']; got=tuple(hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in paths); want=('d7288a91e2e0bc6a4b8bb7863bb00ad2499bb3efb422f7ce3ebeff4f906f9cf4','d9e7feeb2a58454371bd4e31c83cf7def763fc558429a614950a737eefb80d1a','ef0be22bbccb3166fa8b1b70b0575f248869d9ac1aa2fbed9420d1f41af3b304','cfc989e4ca7fce77412ef7126f975db9068eecc2b63ca55e50ef7a5a9ba3828a','329ebafd8e3d57f1572e6dd23e832ef5a3d4b4ffa497a6279ecbeea69aa5d212','d8d9e4a7cd2708d9e6b06dca8551f66174395f7af0766bb7304aab8ac5f79a91','3bdd7acb8b8ae35965ee9fc1862031481778e13f3b4ecd07875c028b1fa88c7b','594da69b999254081dc530ba613bc785889be24f2c041b39e75143f1e517a469','c3847d67cb08d43ce09f45acd77a8fab52f152e5e1bb67c2b57b2b76e2c731c1','80bfd8afa7ca4e46ba9bfcb9747ea34751d147226278906297286c9525011c1b'); assert got==want,(got,want); print('pre-existing unrelated dirty work preserved')"`
  EXPECT: `pre-existing unrelated dirty work preserved`
  EVIDENCE: pending

- [ ] **G1.11** — no unowned path entered the working tree
  CHECK: `python3 -X utf8 -c "import subprocess; allowed={'.github/check_codex_native.py','.github/check_workflows.mjs','AGENT_SETUP.md','codex/install.mjs','commands/debug.md','skills/planning/references/phase-c-executing-plans.md','skills/planning/scripts/sdd.py','skills/planning/scripts/test_sdd.py','workflows/ultra-plan.js','workflows/ultra-verify.js','docs/plans/2026-09-01-skill-improve-proactivity/spec.md','docs/plans/2026-09-01-skill-improve-proactivity/PLAN.md','hooks/test_hooks.py','skills/skill-improve/evals/evals.json','skills/skill-improve/scripts/run_evals.py','skills/skill-improve/scripts/test_run_evals.py','skills/skill-improve/scripts/capture_trigger_evals.py','skills/skill-improve/scripts/test_capture_trigger_evals.py','.claude/rules/artifacts.md','hooks/session_context.py','skills/skill-improve/SKILL.md','skills/skill-improve/references/authoring.md','skills/skill-improve/learning.md','skills/skill-improve/LICENSE-CC-BY-4.0.txt','.claude-plugin/plugin.json','.codex-plugin/plugin.json','.cursor-plugin/plugin.json','.grok-plugin/plugin.json','plugin.yaml','NOTICE','CHANGELOG.md','package.json'}; raw=subprocess.run(['git','status','--porcelain=v1','-z','--untracked-files=all'],check=True,capture_output=True,text=True,encoding='utf-8').stdout; got={item[3:] for item in raw.split('\0') if item}; extra=got-allowed; assert not extra,sorted(extra); print('phase ownership scope preserved')"`
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

- [ ] **G1.14** — four live traces prove polarity and candidate-digest change without another provider run
  CHECK: `python3 -X utf8 -c "from pathlib import Path; import json,subprocess; root=Path('.claude/audit/skill-improve-proactivity/run-3'); names=['trace-codex-pro-precreate-skill.json','trace-claude-bound-agent-prompt-draft.json']; red=[json.loads((root/'red'/name).read_text(encoding='utf-8')) for name in names]; green=[json.loads((root/'green'/name).read_text(encoding='utf-8')) for name in names]; required={'phase','backend','case_id','expected','observed','selected_owner','candidate_digest','candidate_file_count','prompt_digest','cli_version','reported_model','captured_at_utc','git_revision','git_dirty','child_exit'}; assert all(required<=set(trace) for trace in red+green); assert len({trace['candidate_digest'] for trace in red})==1; assert len({trace['candidate_digest'] for trace in green})==1; assert red[0]['candidate_digest']!=green[0]['candidate_digest']; assert {(trace['backend'],trace['case_id'],trace['expected'],trace['observed']) for trace in green}=={('codex','pro-precreate-skill','load','load'),('claude','bound-agent-prompt-draft','skip','skip')}; assert {trace['selected_owner'] for trace in red+green if trace['backend']=='claude'}=={'graph-powers:senior-prompt-engineer'}; assert {(trace['backend'],trace['case_id'],trace['prompt_digest']) for trace in red}=={(trace['backend'],trace['case_id'],trace['prompt_digest']) for trace in green}; oid=subprocess.run(['git','rev-parse','HEAD'],check=True,capture_output=True,text=True,encoding='utf-8').stdout.strip(); assert all(trace['child_exit']==0 for trace in red+green); assert all(trace['git_revision']==oid and trace['git_dirty'] is False for trace in red); print('four live traces and candidate digest verified')"`
  EXPECT: `four live traces and candidate digest verified`
  EVIDENCE: pending

- [ ] **G1.15** — pinned CC BY text and every licence projection agree
  CHECK: `python3 -X utf8 -c "from pathlib import Path; import hashlib,json; licence=Path('skills/skill-improve/LICENSE-CC-BY-4.0.txt').read_bytes(); assert len(licence)==18652 and hashlib.sha256(licence).hexdigest()=='50bfbf25300f4b6c06f5c286bc9f63b2fe43a548233d633a6798a78a785bdb98'; target='MIT AND Apache-2.0 AND CC-BY-4.0'; paths=['package.json','.claude-plugin/plugin.json','.codex-plugin/plugin.json','.cursor-plugin/plugin.json','.grok-plugin/plugin.json']; assert all(json.loads(Path(path).read_text(encoding='utf-8'))['license']==target for path in paths); assert 'license: \"'+target+'\"' in Path('plugin.yaml').read_text(encoding='utf-8'); print('pinned CC BY and licence projections verified')"`
  EXPECT: `pinned CC BY and licence projections verified`
  EVIDENCE: pending

- [ ] **G1.16** — the applicable follow-up is CLOSED and both candidate digests are recorded outside the digest surface
  CHECK: `python3 -X utf8 -c "from pathlib import Path; import json,runpy; learning=Path('skills/skill-improve/learning.md').read_text(encoding='utf-8'); tick=chr(96); open_record='**Follow-up '+tick+'R10-F1'+tick+' — OPEN:**'; closed_record='**Disposition '+tick+'R10-F1'+tick+' — CLOSED:**'; assert learning.count(open_record)==1 and learning.count(closed_record)==1 and '.claude/audit/skill-improve-proactivity/run-3/green' in learning; root=Path('.claude/audit/skill-improve-proactivity/run-3'); names=['trace-codex-pro-precreate-skill.json','trace-claude-bound-agent-prompt-draft.json']; green=[json.loads((root/'green'/name).read_text(encoding='utf-8')) for name in names]; assert len({trace['candidate_digest'] for trace in green})==1; evaluated=green[0]['candidate_digest']; compute=runpy.run_path('skills/skill-improve/scripts/capture_trigger_evals.py')['compute_candidate_digest']; final_digest,file_count=compute(Path('.')); assert final_digest!=evaluated and file_count>0; plan=Path('docs/plans/2026-09-01-skill-improve-proactivity/PLAN.md').read_text(encoding='utf-8'); block=plan[plan.index('- [x] **T1.2**'):plan.index('- [x] **T1.3**')]; assert 'EVIDENCE: pending' not in block and evaluated in block and final_digest in block; print('follow-up closed and both candidate digests recorded')"`
  EXPECT: `follow-up closed and both candidate digests recorded`
  EVIDENCE: pending

## Verification

Focused acceptance is G1.2-G1.16. After the separate final Evaluator resolves every Critical and
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
substitute for the four live sessions.

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
