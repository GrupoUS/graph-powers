# Lean harness — results

Measured on 2026-09-08 against `a84c5f7` (1.19.2). The candidate is 1.19.3 on
`codex/lean-harness`, with changes local and unstaged.

## Reduction

| Measure | Before | After | Reduction |
|---|---:|---:|---:|
| Command unconditional load estimate | 261,858 B | 46,243 B | 82.3% |
| Command worst-case load estimate | 405,450 B | 187,494 B | 53.8% |
| Skill/command listing | 10,143 characters | 7,730 characters | 23.8% |
| 12 agent sources | 51,028 B | 19,063 B | 62.6% |
| 12 command sources | 118,155 B | 29,343 B | 75.2% |
| 13 skill entrypoints | 150,221 B | 33,917 B | 77.4% |
| All measured instruction sources, including detailed references | 980,587 B | 643,359 B | 34.4% |
| SessionStart advisory text, excluding project tag | 903 B | 687 B | 23.9% |

The command figures use the unchanged algorithm in `.github/check_context_budget.py`; listing
uses `.github/check_listing_budget.py`. These are byte/character estimates, not token counts or
measured model latency. The command estimator follows one level only. The source total also counts
all skill/shared references, rules/templates and the Hermes adapter, so moving a load behind a
condition cannot masquerade as deletion. Histories and earlier plans are outside that total.

The three entrypoint groups together fell from 319,404 to 82,323 bytes (74.2%). Detail remains
available for the modes that use it. No new reference files were created to hide removed text.

Existing ceilings now retain the improvement: command floor 50,000 B, command ceiling 200,000 B,
largest command floor 15,000 B, listing 8,000 characters. Both budget gates reject the recorded
original baseline with exit 1 and accept the candidate with exit 0.

## What changed and what remains

- Shared method selection requires a clear match or explicit request. Context already read and
  still-valid green evidence are reused; changed relevant inputs invalidate that evidence.
- Commands route to existing methods; skills load the relevant phase or mode. The skill-improve
  history and broad audit/eval procedure are conditional, and no response-prefix ceremony remains.
- Agent prompts keep concrete safety mirrors needed by isolated workers. The seven-section
  delegation envelope and consultation schema each have one owner.
- Templates keep project-specific rules. The Hermes adapter retains its actual client limitations
  and points to shared methods. Codex, Cursor, Grok and Hermes projections were regenerated locally.
- Names, model/effort selection and tool/read-only contracts are preserved. Runtime authorization,
  command trust, tenant/secret protection, fail-open behavior and bounded execution remain enforced.

| Command | Preserved routes |
|---|---|
| debug | default/auto, audit, frontend, backend, auth-db, recover and aliases |
| design | new direction versus in-place repair; marketing, UX and motion branches |
| evolve | explicit learning, auto and handoff |
| gauntlet | explicit eligible plan, dry-run, independent critics, caps and final verification |
| implement | approved plan, dry-run and Planning Phase C |
| perf | runtime, resources/hooks/tests, fix, compare, Vercel/RUM, doctor, build, DB, SEO, security |
| plan | discovery, design, structured plan and reviewed execution routing |
| pr-review | PR/current/branch/full, quick and authorized fix |
| prime | auto/backend/frontend/fullstack and optional research |
| research | repository/external investigation, findings only |
| setup | diagnostic Oxc/TypeScript/vtsls/editor checks, no installation |
| verify | quick/full/loop, declared gates, floor, supplements and fallback |

All 13 skills retain their domain route. Animation tokens/timings and resource/build measurement
methods remain concrete; detailed diagnosis packs are reused. Planning retains its grammar,
leases, independent critics, caps and explicit Gauntlet activation. No manual model settings or
global installed package was changed.

## Validation

All 25 checks in `.claude/rules/verify-supplements.md`, plus the Cursor and Grok projection checks,
passed: **27 checks, exit 0**. Recorded commands and output are in the local
`.graph-powers/logs/lean-harness-gates/` directory.

| Evidence | Result |
|---|---|
| `python3 hooks/test_hooks.py` | 676 assertions; EVERY GUARANTEE HELD |
| `python3 .github/test_hook_clients.py` | 14 client-package regressions held |
| `python3 skills/planning/scripts/test_sdd.py` | 51 tests passed |
| `python3 skills/skill-improve/scripts/test_run_evals.py` | 11 tests passed |
| `python3 skills/skill-improve/scripts/test_capture_trigger_evals.py` | 15 tests passed |
| `python3 .github/test_file_references.py` | 12 tests passed |
| `python3 .github/check_wiring.py` | 280 references; 0 unresolved; 12 agents register |
| `python3 .github/check_codex_native.py` | 12 companions; native/clone policy parity |
| `python3 .github/check_cursor.py` / `python3 .github/check_grok.py` | generated projections match |
| `python3 -X utf8 .github/test_hermes.py` | 5 focused checks passed |
| Hermes client verification | native doctor passed; 38 registrations |
| 13 skill `quick_validate.py` checks and `git diff --check` | passed |

The lifecycle regression first failed in seven expected cases against the old hook, then passed
after the change. The complete hook suite retained the safety assertions. The obsolete eval-runner
test for the removed prefix was replaced with positive/negative evidence grading; its path,
symlink and critical-assertion protections were retained. The SDD runtime and its tests are unchanged.
Capture/runner tests validate the tooling; fresh model trigger-evaluation responses were not sampled.

The version gate passed; an additional comparison confirmed the working-tree bump specifically
from HEAD 1.19.2 to 1.19.3. HEAD remains `a84c5f7`, with nothing staged.

## Independent review and limits

Plan review passed. Wave review found six Important regressions; correction review of `48cc9b0`
closed all six: safety mirrors, authorized frontend work, delegation envelope, performance methods,
animation tokens and consultation fallback. Minor Animate references and the explicit Codex recovery
document path were subsequently corrected. Final integrated review of `1e67fc6` passed for T1–T4
with no open findings. The run used eight bounded dispatches and retained its state through correction.

The native Workflow tool is unavailable in this session. Explicit Gauntlet therefore used native
agents, SDD state and the documented one-shot local verification fallback. No Workflow execution
is claimed. Linux checks, portable fixtures and generated-client parity were exercised; no live
macOS/Windows application session or model-latency benchmark was run.

The reusable outcome is recorded in the existing method-selection, verification and authoring
owners. No extra always-loaded learning rule or automatic follow-up was added.
