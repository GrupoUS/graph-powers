# Issue 24 — verification evidence

## Scope and review

Baseline: a815af18baa4c1c14658a655b50ccf646ea7ee05, current main checkout.
Preexisting untracked yaml is excluded and preserved. User authorized implementation and issue
comments/closure; no Git publication or active installation is authorized.

Primary skill-improver audit confirmed the missing decision-frontier gate and unreachable
pre-validation handling of invalid Needs payloads. Mode 1 plan review first rejected a purely
structural T1.1 CHECK; it was replaced with a case-specific behavioral evaluation. Final plan
review PASS: completeness 8/8, atomicity 8/7, risk 7/7, dependency order 9/8. The necessary
planning/SKILL.md router alignment was independently approved. sdd.py validate --profile gauntlet
--max-tasks 12 exited 0 with two L3 tasks.

## Baseline

An isolated verifier read the unmodified instructions and answered a time-pressure scenario.
Its response explicitly omitted frontier rounds and shared-understanding confirmation because
prior session approval covered the transitions. Exact response is retained in the ignored local
log .graph-powers/logs/issue-24/baseline-response.txt. This is an agent policy simulation, not a
live Gauntlet execution or installed-client telemetry.

## Implementation checks

Implementation acceptance: PASS. Final independent diff review: REVIEW_APPROVED, no P1/P2,
confidence 4/5. Twenty-three tracked paths changed within declared ownership; 44 prior evals
preserved, two updated and seven added. No runtime script, cap, public name or description changed.

The final negative case rejects the pre-change baseline (exit 1, two critical failures) and accepts
the independent post-change response (5/5, exit 0). All nine selected responses pass threshold 1.0:
seven initial captures plus two complementary responses from the same agent after a request for
more detailed sequencing. This is not a new blind round. Original responses were never rewritten.
Eighteen positive parser controls exit 0 and twenty-eight negative controls exit 1. The initial
incomplete pipeline response remains a negative control. Negation/word-order false negatives were
corrected, and plan-hole admission was aligned with canonical Phase B after independent review.

Logs: .graph-powers/logs/issue-24/eval-calibration-report.json, final-selected-results.json,
final-focused-controls.log and final-baseline-red.log. The primary CHECK was independently rerun
by the parent: PASSED (pass_rate 100.00% >= threshold 100.00%). Structural quick_validate passed.

Full inventory: 27 of 28 gate groups PASS (28 successful commands out of 29); gate 8 has two
commands. SDD was rerun after the final instruction change: 62 tests OK. Context budget remains
51,216 B floor / 207,611 B ceiling, within unchanged 51,500 / 208,000 caps. Hermes --check reports
39 registrations, source manifest and package current; six version owners read 1.20.7.

Workspace verification verdict: NEEDS-WORK solely for preexisting gate 24. The untracked yaml file,
visible in the initial status, is 12,221,795 bytes and was not moved, ignored, altered or deleted.
The gate measured source 16,104,607 B against 4,194,304 B; subtracting that unrelated file yields
3,882,812 B. Hermes measured 1,824,744 B against 2,097,152 B. These are the executed gate snapshot's
sizes; subsequent parent evidence edits add only documentation. This exception is disclosed; gate
24 is not reported as passed. Implementation acceptance and issue closure do not publish Git changes.

### Ordered gate results

| Gate command | Exit |
|---|---|

| `claude plugin validate .` | 0 |
| `python3 hooks/test_hooks.py` | 0 |
| `python3 .github/test_hook_clients.py` | 0 |
| `python3 skills/planning/scripts/test_sdd.py` | 0 |
| `python3 skills/skill-improve/scripts/test_run_evals.py` | 0 |
| `python3 skills/skill-improve/scripts/test_capture_trigger_evals.py` | 0 |
| `python3 .github/check_oxc_policy.py` | 0 |
| `python3 -X utf8 .github/test_hermes_package.py` | 0 |
| `python3 -X utf8 .github/test_hermes.py --static` | 0 |
| `python3 -X utf8 bin/verify-hook-clients.py --client hermes --hermes-proof static --plugin-root . --package-root hermes/package --json` | 0 |
| `python3 -c import ast,glob;[ast.parse(open(f).read()) for f in glob.glob('hooks/*.py')]` | 0 |
| `python3 -c import json,glob;[json.load(open(f)) for f in glob.glob('**/*.json',recursive=True)+glob.glob('.*/*.json')]` | 0 |
| `bun .github/check_workflows.mjs` | 0 |
| `bun .github/check_codex_policy.mjs` | 0 |
| `python3 .github/check_codex_native.py` | 0 |
| `python3 .github/check_wiring.py` | 0 |
| `python3 .github/test_file_references.py` | 0 |
| `python3 .github/check_file_references.py` | 0 |
| `python3 .github/check_portability.py` | 0 |
| `python3 .github/check_context_budget.py` | 0 |
| `python3 .github/check_listing_budget.py` | 0 |
| `python3 .github/check_machine_paths.py` | 0 |
| `python3 .github/check_placeholders.py` | 0 |
| `bun bin/graph-powers.mjs --help` | 0 |
| `python3 .github/check_clone.py` | 1 |
| `python3 .github/check_version_bump.py` | 0 |
| `python3 .github/check_grok.py` | 0 |
| `python3 .github/check_cursor.py` | 0 |
| `python3 skills/issue-improve/scripts/test_issue_comment.py` | 0 |

## Limits

No product UI/API/database changed. Type-check, lint and build are not declared by this harness.
Codex fixture installation assertion is CI-only. Hermes runtime and installed-client execution
remain UNVERIFIED; static package proof does not establish runtime behavior.
