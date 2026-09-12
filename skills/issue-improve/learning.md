# Issue improve — focused authoring evidence

## 2026-09-11 — initial Mode A

Intent: improve a GitHub issue into a concise reviewed plan comment; implementation of the host
issue is outside this entry. Technique/discipline boundary: Planning owns interpretation and plan
grammar; the helper owns only author/marker selection and approved publication mechanics.

Measured on the local source checkout with Python 3 and Bun; no real GitHub write, installation,
clean-session capture or fresh-model trigger run. Fixtures below were manually authored response
traces from the accepted contract; their embedded plan-review/validation text is simulated,
not evidence those plans were run. Assertion scores measure fixtures only.

| Proof | Actual result |
|---|---|
| Helper preview before implementation | `python3 skills/issue-improve/scripts/test_issue_comment.py IssueCommentTests.test_preview_is_default_and_never_calls_gh` exited 1: `issue_comment.py` absent |
| Real helper CLI, mocked gh | `python3 skills/issue-improve/scripts/test_issue_comment.py` exited 0: 14 tests, `OK`; actual main/argparse, Unicode JSON stdin, persisted fake comment outcomes, page-two and duplicate selection, preview, auth/API failure and ambiguous retry |
| Canonical URL normalization regression | Adding a trailing newline/empty query reproduced an unintended mocked POST before BLOCKED (exit 1, 2 failing subcases). Requiring the parsed URL to equal the supplied canonical URL now blocks before any gh call; the complete 14-test check is green |
| Documented validator syntax | The CLI test extracts the method's command and runs real `sdd.py validate` on an invalid temporary plan; exit 2 with `plan contains no structured tasks` proves the positional parser was reached. The initial assertion wrongly expected JSON/exit 1; corrected to the existing stderr/exit 2 contract. This was a test expectation correction, not a production fix |
| Static negative baseline | Existing plan adapter, graded as `boundary`, exited 1: 1/5 assertions, 4 critical failures. This document comparison is not a model RED |
| Focused contract fixtures | Per-case runner exited 0: 5/5 cases, 22/22 assertions, threshold 1.0 |
| Entry validation | `quick_validate.py skills/issue-improve` exited 0: `Skill is valid!` |

Response fixtures (shipped with the canonical source, not with client projections) and per-case scores:

- L3 order (`evals/fixtures/resp-l3-order.txt`): 5/5; review and validation before exact payload.
- L1 short plan (`evals/fixtures/resp-l1-short.txt`): 4/4; bounded evidence and check.
- Retrieval failure (`evals/fixtures/resp-retrieval-error.txt`): 4/4; JSON comments, BLOCKED, no guess.
- Injection containment (`evals/fixtures/resp-injection.txt`): 4/4; sanitized ledger and human precedence.
- Approval boundary (`evals/fixtures/resp-boundary.txt`): 5/5; changed target/payload waits at preview.

Reproduce the fixture score (one response per case):

```text
python3 "${CLAUDE_PLUGIN_ROOT}/skills/skill-improve/scripts/run_evals.py" --skill-path "${CLAUDE_PLUGIN_ROOT}/skills/issue-improve" --evals-path "${CLAUDE_PLUGIN_ROOT}/skills/issue-improve/evals/evals.json" --response-dir "${CLAUDE_PLUGIN_ROOT}/skills/issue-improve/evals/fixtures" --threshold 1.0
```

The response trace alone cannot prove live ordering, human approval or model compliance. Actual
publication mechanics have CLI evidence; retrieval/plan-only behavior has the method and focused
fixture contract evidence. Independent publishers remain a documented single-writer ceiling.

## 2026-09-12 — final-review corrections

Two Minor findings from the Gauntlet final review changed the helper: selection now requires the
marker as the comment's first line (a same-author comment quoting the marker on its own line, for
example inside a fence, is no longer an update target), and a draft over GitHub's 65,536-character
comment limit blocks before any `gh` call. `python3 skills/issue-improve/scripts/test_issue_comment.py`
exited 0: 15 tests, `OK`; the fixture score above was re-run unchanged (5/5, 22/22). Fixture links
became plain paths because client projections do not ship `evals/fixtures/`.
