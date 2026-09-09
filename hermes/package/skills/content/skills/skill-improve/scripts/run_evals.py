#!/usr/bin/env python3
"""
run_evals.py — Binary Assertion Eval Runner for Skills

Inspired by karpathy/autoresearch: clear binary metrics, autonomous loop.
Runs assertions from evals.json against an agent response file.

Usage, one case against the response captured for it (the honest single-case mode):
    python3 run_evals.py --skill-path <skill-dir> --evals-path <skill-dir>/evals/evals.json --response-file .claude/audit/eval-responses/resp-<case-id>.txt --test-case <case-id> --threshold 1.0

Usage, every case, each against its own response (the honest multi-case mode):
    python3 run_evals.py --skill-path <skill-dir> --evals-path <skill-dir>/evals/evals.json --response-dir .claude/audit/eval-responses --threshold 1.0

    --response-dir reads resp-<case-id>.txt for every case in the file, prints one line per
    case, and exits 0 only when every case reaches the threshold. A case whose response file
    is missing is a FAILED case, never a skipped one: a loop that skips what it cannot find
    reports green over the cases it never measured.

Default mode (no --test-case and no --response-dir) flattens the assertions of EVERY case
against ONE response, so a positive `contains: X` and a negative `not_contains: X` cancel
out and the ceiling lands near 81% on correct artefacts. The runner warns on stderr when a
multi-case file is run that way; the mode is kept only for single-case files.

Exit codes:
    0 — no critical assertion failed AND pass_rate >= threshold (default 0.95), for the case or
        for every case under --response-dir
    1 — a failed critical assertion (fatal at any threshold), a rate below the threshold, a case
        with nothing machine-checkable, a missing response, an unknown assertion id, an invalid
        check, or an error
"""

import argparse
import json
import re
import sys
from pathlib import Path

SAFE_CASE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def normalize_evals(doc: dict) -> dict:
    """
    Accept both eval-file shapes used in this repo and return the runner's shape
    (top-level `assertions` + `test_cases` with `expected_assertions`).

    Shape A (runner-native): {"assertions": [...],
                              "test_cases": [{"id", "expected_assertions"}]}
    Shape B (per-case):      {"skill_name",
                              "evals": [{"id", "prompt", "assertions": [...]}]}
    Shape C (prose):         {"skill_name",
                              "evals": [{"id", "prompt", "expectations": [str]}]}

    Shapes B and C appear in real skills in the wild. Before this normalizer the runner
    raised KeyError on `assertions` for those files, so nothing they declared ever ran —
    a whole eval suite reporting green because it never executed. Shape C has no machine-checkable predicate, so its entries
    become assertions flagged `manual: True` with no `check` at all: reported for human
    review, printed as `◻ MANUAL`, and excluded from pass_rate (neither pass nor fail).
    """
    if "assertions" in doc:
        return doc

    cases = doc.get("evals") or doc.get("test_cases") or []
    assertions: list[dict] = []
    test_cases: list[dict] = []

    for position, case in enumerate(cases, start=1):
        case_id = str(case.get("id") or f"case-{position}")
        ids = []
        prose = [
            {
                "id": f"M{i + 1:02d}",
                "description": text,
                "manual": True,
                "critical": False,
            }
            for i, text in enumerate(case.get("expectations", []))
        ]
        for assertion in list(case.get("assertions", [])) + prose:
            # Namespace unconditionally: two cases may reuse an id like A01, and making
            # the prefix conditional on "seen already" would make the first occurrence
            # bare and later ones prefixed — ids that depend on case order.
            merged = dict(assertion)
            merged["id"] = f"{case_id}/{assertion['id']}"
            assertions.append(merged)
            ids.append(merged["id"])
        carried = {
            k: v for k, v in case.items() if k not in ("assertions", "expectations")
        }
        test_cases.append({**carried, "id": case_id, "expected_assertions": ids})

    return {**doc, "assertions": assertions, "test_cases": test_cases}


def load_json(path: str) -> dict:
    """Load and parse a JSON file."""
    with open(path, encoding="utf-8") as f:  # NOSONAR -- explicit local CLI input.
        return normalize_evals(json.load(f))


def load_response(path: str) -> str:
    """Load the agent response text file."""
    with open(path, encoding="utf-8") as f:  # NOSONAR -- explicit local CLI input.
        return f.read()


def parse_check(check_str: str) -> tuple[str, str]:
    """Parse a check string like 'contains: "foo"' into (type, value)."""
    # Format: "check_type: value"
    colon_idx = check_str.index(":")
    check_type = check_str[:colon_idx].strip()
    value = check_str[colon_idx + 1:].strip()
    return check_type, value


def strip_quotes(s: str) -> str:
    """Remove surrounding quotes from a string."""
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    return s


def run_assertion(assertion: dict, response: str) -> dict:
    """
    Run a single assertion against the response.
    Returns: { id, description, type, critical, passed, detail }
    """
    # Manual assertions carry no machine predicate at all (the `expectations` shape).
    # Short-circuit BEFORE parse_check: fabricating a "manual: <text>" string only to
    # re-parse it here would encode data into syntax for no gain.
    description = assertion.get("description", "")
    if assertion.get("manual"):
        return {
            "id": assertion["id"],
            "description": description,
            "type": "manual",
            "critical": False,
            "manual": True,
            "passed": None,
            "detail": f"MANUAL — review by hand: {description}",
        }

    # An assertion with no `check`, or a check with no `type: value` colon, used to surface as a
    # traceback — a red row nobody could tell apart from a crashed runner. It is a failed
    # assertion with a detail that names the defect, so the table stays readable.
    check = assertion.get("check")
    if not isinstance(check, str) or ":" not in check:
        return {
            "id": assertion["id"],
            "description": description,
            "type": "invalid",
            "critical": assertion.get("critical", False),
            "manual": False,
            "passed": False,
            "detail": (
                "INVALID assertion: no `check` key"
                if check is None
                else f"INVALID assertion: check {check!r} has no `type: value` colon"
            ),
        }

    check_type, raw_value = parse_check(check)
    try:
        passed, detail = _evaluate(check_type, raw_value, response)
    except (ValueError, re.error) as exc:
        # `word_count_max: many`, `contains_one_of: not-json`, `regex: (unclosed` — a value the
        # check cannot parse used to raise out of the run. json.JSONDecodeError is a ValueError.
        passed, detail = False, f"INVALID assertion: check {check!r} cannot be evaluated ({exc})"

    return {
        "id": assertion["id"],
        "description": description,
        "type": assertion.get("type", "unknown"),
        "critical": assertion.get("critical", False),
        "manual": False,
        "passed": passed,
        "detail": detail,
    }


def _evaluate(check_type: str, raw_value: str, response: str) -> tuple[bool, str]:
    """Evaluate one parsed check against the response. Raises on an unparseable value."""
    passed = False
    detail = ""

    if check_type == "contains":
        needle = strip_quotes(raw_value)
        passed = needle in response
        detail = f"Looking for '{needle}': {'found' if passed else 'NOT found'}"

    elif check_type == "not_contains":
        needle = strip_quotes(raw_value)
        passed = needle not in response
        detail = f"Checking absence of '{needle}': {'absent (good)' if passed else 'FOUND (bad)'}"

    elif check_type == "word_count_max":
        max_words = int(raw_value)
        actual_words = len(response.split())
        passed = actual_words <= max_words
        detail = f"Word count: {actual_words} (max {max_words})"

    elif check_type == "contains_one_of":
        # Parse JSON array: ["a", "b", "c"]
        options = json.loads(raw_value)
        found = [opt for opt in options if opt in response]
        passed = len(found) > 0
        detail = f"Looking for one of {options}: found {found or 'NONE'}"

    elif check_type == "regex":
        pattern = strip_quotes(raw_value)
        match = re.search(pattern, response)
        passed = match is not None
        detail = f"Regex /{pattern}/: {'matched' if passed else 'no match'}"

    else:
        detail = f"Unknown check type: {check_type}"
        passed = False

    return passed, detail


def run_eval_suite(
    evals: dict,
    response: str,
    test_case_id: str | None = None,
) -> dict:
    """
    Run the full eval suite (or a specific test case) against a response.
    Returns structured results with pass_rate and per-assertion details.
    """
    assertions_map = {a["id"]: a for a in evals["assertions"]}

    # Determine which assertions to run
    if test_case_id:
        test_case = next(
            (tc for tc in evals.get("test_cases", []) if tc["id"] == test_case_id),
            None,
        )
        if not test_case:
            return {
                "error": f"Test case '{test_case_id}' not found",
                "available": [tc["id"] for tc in evals.get("test_cases", [])],
            }
        assertion_ids = test_case["expected_assertions"]
        # An unknown id used to be filtered out silently, so a case whose ids were all mistyped
        # ran zero assertions and reported pass_rate 0.0 over an empty table — indistinguishable
        # at a glance from a real failure. It is an error that names the ids.
        unknown = [aid for aid in assertion_ids if aid not in assertions_map]
        if unknown:
            return {
                "error": f"Test case '{test_case_id}' references unknown assertion ids: {unknown}",
                "available_assertions": sorted(assertions_map),
            }
        assertions_to_run = [assertions_map[aid] for aid in assertion_ids]
    else:
        assertions_to_run = evals["assertions"]

    # Run each assertion
    results = [run_assertion(a, response) for a in assertions_to_run]

    # Manual assertions have no machine predicate, so they are neither pass nor fail —
    # counting them either way would make pass_rate a lie.
    auto = [r for r in results if not r.get("manual")]
    manual = sum(1 for r in results if r.get("manual"))

    total = len(auto)
    passed = sum(1 for r in auto if r["passed"])
    failed = sum(1 for r in auto if not r["passed"])
    critical_failures = sum(1 for r in auto if not r["passed"] and r["critical"])
    pass_rate = passed / total if total > 0 else 0.0

    return {
        # Shape A uses `skill`; shapes B/C use `skill_name`.
        "skill": evals.get("skill") or evals.get("skill_name", "unknown"),
        "version": evals.get("version", "0.0.0"),
        "test_case": test_case_id,
        "total_assertions": total,
        "passed": passed,
        "failed": failed,
        "manual": manual,
        "critical_failures": critical_failures,
        "pass_rate": round(pass_rate, 4),
        "results": results,
    }


def print_results(summary: dict) -> None:
    """Print human-readable results to stdout."""
    print(f"\n{'=' * 60}")
    print(f"  EVAL RESULTS: {summary['skill']} v{summary['version']}")
    if summary.get("test_case"):
        print(f"  Test Case: {summary['test_case']}")
    print(f"{'=' * 60}\n")

    for r in summary["results"]:
        status = "◻ MANUAL" if r.get("manual") else "✅ PASS" if r["passed"] else "❌ FAIL"
        critical_tag = " [CRITICAL]" if r["critical"] and not r["passed"] else ""
        print(f"  {status}  {r['id']}: {r['description']}{critical_tag}")
        print(f"         {r['detail']}")

    print(f"\n{'─' * 60}")
    print(f"  Total: {summary['total_assertions']}  |  "
          f"Passed: {summary['passed']}  |  "
          f"Failed: {summary['failed']}  |  "
          f"Critical Failures: {summary['critical_failures']}")
    print(f"  Pass Rate: {summary['pass_rate']:.2%}")
    print(f"{'─' * 60}\n")


def run_response_dir(
    evals: dict, response_dir: Path, threshold: float, case_tag: str | None = None,
) -> tuple[list[dict], bool]:
    """
    Run every case against its own captured response, `resp-<case-id>.txt` under response_dir.

    The multi-case form of the only honest mode: one case per response keeps polarity intact,
    where default mode flattens a positive `contains` and a negative `not_contains` on the same
    token into a cancellation. A missing response is a failed case, never a skipped one.
    """
    rows: list[dict] = []
    all_ok = True
    cases = evals.get("test_cases", [])
    if case_tag is not None:
        cases = [case for case in cases if case_tag in case.get("tags", [])]
        if not cases:
            return [_failed_row(
                "(none)", f"no test cases carry tag {case_tag!r}; nothing was measured"
            )], False
    if not cases:
        # Zero cases would exit 0 having measured nothing — the exact green-over-nothing this
        # mode exists to prevent.
        return [_failed_row("(none)", "the eval file declares no test cases; nothing was measured")], False
    for position, case in enumerate(cases, 1):
        if "id" not in case or case["id"] is None:
            rows.append(_failed_row(f"case-{position}", "missing test case id"))
            all_ok = False
            continue
        case_id = str(case["id"])
        if not SAFE_CASE_ID.fullmatch(case_id):
            rows.append(_failed_row(case_id, f"unsafe test case id: {case_id!r}"))
            all_ok = False
            continue
        path = response_dir / f"resp-{case_id}.txt"
        if path.is_symlink():
            rows.append(_failed_row(case_id, f"response file is a symlink: {path}"))
            all_ok = False
            continue
        if not path.exists():
            rows.append(_failed_row(case_id, f"response file not found: {path}"))
            all_ok = False
            continue
        try:
            resolved_dir = response_dir.resolve(strict=True)
            resolved_path = path.resolve(strict=True)
            resolved_path.relative_to(resolved_dir)
        except (OSError, ValueError):
            rows.append(_failed_row(case_id, f"response file escapes its directory: {path}"))
            all_ok = False
            continue
        try:
            response = load_response(str(resolved_path))
        except (OSError, UnicodeError) as error:
            rows.append(_failed_row(case_id, f"could not read response file: {error}"))
            all_ok = False
            continue
        summary = run_eval_suite(evals, response, case_id)
        if "error" in summary:
            rows.append(_failed_row(case_id, summary["error"]))
            all_ok = False
            continue
        if summary["total_assertions"] == 0:
            rows.append(_failed_row(case_id, "no machine-checkable assertions — a gate cannot pass on manual review"))
            all_ok = False
            continue
        summary["ok"] = summary["critical_failures"] == 0 and summary["pass_rate"] >= threshold
        all_ok = all_ok and summary["ok"]
        rows.append(summary)
    return rows, all_ok


def _failed_row(case_id: str, error: str) -> dict:
    return {
        "test_case": case_id,
        "error": error,
        "total_assertions": 0,
        "passed": 0,
        "failed": 0,
        "manual": 0,
        "critical_failures": 0,
        "pass_rate": 0.0,
        "results": [],
        "ok": False,
    }


def print_case_table(rows: list[dict], threshold: float) -> None:
    """One line per case, then only the failed assertions — a table for a glance, not a log."""
    print(f"\n{'=' * 60}")
    print(f"  EVAL RESULTS, per case  (threshold {threshold:.0%})")
    print(f"{'=' * 60}\n")
    for row in rows:
        status = "PASS" if row["ok"] else "FAIL"
        if row.get("error"):
            print(f"  {status}  {row['test_case']:<34} {row['error']}")
            continue
        print(
            f"  {status}  {row['test_case']:<34} {row['passed']}/{row['total_assertions']}"
            f"  ({row['pass_rate']:.0%}, critical failures {row['critical_failures']})"
        )
        for r in row["results"]:
            if not r.get("manual") and not r["passed"]:
                print(f"           x {r['id']}: {r['detail']}")
    ok = sum(1 for r in rows if r["ok"])
    print(f"\n{'─' * 60}")
    print(f"  Cases: {len(rows)}  |  Passed: {ok}  |  Failed: {len(rows) - ok}")
    print(f"{'─' * 60}\n")


def main():
    # The report prints non-ASCII glyphs; on a console whose code page is not UTF-8 that is an
    # encoding error at the first row, which reads as a crashed runner. Replace, never raise.
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Run binary assertion evals against an agent skill response.",
        epilog="Inspired by karpathy/autoresearch — clear metrics, autonomous loop.",
    )
    parser.add_argument(
        "--skill-path",
        required=True,
        help="Path to the SKILL.md being evaluated (for context/logging)",
    )
    parser.add_argument(
        "--evals-path",
        required=True,
        help="Path to the evals.json file with assertions and test cases",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--response-file",
        default=None,
        help="Text file with the agent's output for ONE case (pair it with --test-case)",
    )
    source.add_argument(
        "--response-dir",
        default=None,
        help="Directory holding resp-<case-id>.txt for EVERY case; each case runs against its own response",
    )
    parser.add_argument(
        "--test-case",
        default=None,
        help="Specific test case ID to run (e.g. T01). Runs all assertions if omitted.",
    )
    parser.add_argument(
        "--case-tag",
        default=None,
        help="Run only cases carrying this tag; requires --response-dir",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.95,
        help="Minimum pass rate to exit 0 (default: 0.95)",
    )
    args = parser.parse_args()
    if args.response_dir and args.test_case:
        parser.error("--test-case selects one case; --response-dir already runs every case")
    if args.case_tag and not args.response_dir:
        parser.error("--case-tag requires --response-dir")

    # Validate paths
    for label, path in [
        ("skill", args.skill_path),
        ("evals", args.evals_path),
        ("response", args.response_file or args.response_dir),
    ]:
        if not Path(path).exists():
            print(f"ERROR: {label} file not found: {path}", file=sys.stderr)
            sys.exit(1)

    # Load inputs
    evals = load_json(args.evals_path)

    if args.response_dir:
        rows, ok = run_response_dir(evals, Path(args.response_dir), args.threshold, args.case_tag)
        print_case_table(rows, args.threshold)
        if ok:
            print("  PASSED: every case reached the threshold")
            sys.exit(0)
        print("  FAILED: at least one case is below the threshold or has no response file")
        sys.exit(1)

    response = load_response(args.response_file)
    cases = evals.get("test_cases", [])
    if not args.test_case and len(cases) > 1:
        print(
            f"WARNING: default mode flattens the assertions of all {len(cases)} cases against one "
            "response, so a positive `contains` and a negative `not_contains` on the same token "
            "cancel out and the pass rate cannot reach 100% on correct artefacts. "
            "Use --test-case <id> for one case, or --response-dir <dir> for every case against "
            "its own response.",
            file=sys.stderr,
        )

    # Run evaluation
    summary = run_eval_suite(evals, response, args.test_case)

    # Handle errors
    if "error" in summary:
        print(f"ERROR: {summary['error']}", file=sys.stderr)
        if "available" in summary:
            print(f"Available test cases: {summary['available']}", file=sys.stderr)
        if "available_assertions" in summary:
            print(f"Available assertion ids: {summary['available_assertions']}", file=sys.stderr)
        sys.exit(1)

    # Print results
    print_results(summary)

    # Exit code: a failed critical assertion fails the run at any threshold; the threshold then
    # decides the non-critical ones. Before this, `critical` was a label in the printed report
    # and a case could fail its one critical assertion out of twenty and still exit 0 at 0.95.
    if summary["total_assertions"] == 0:
        print("  ❌ FAILED (no machine-checkable assertions — nothing was measured)")
        sys.exit(1)
    if summary["critical_failures"] > 0:
        print(f"  ❌ FAILED ({summary['critical_failures']} critical assertion(s) failed — fatal at any threshold)")
        sys.exit(1)
    if summary["pass_rate"] >= args.threshold:
        print(f"  ✅ PASSED (pass_rate {summary['pass_rate']:.2%} >= threshold {args.threshold:.2%})")
        sys.exit(0)
    else:
        print(f"  ❌ FAILED (pass_rate {summary['pass_rate']:.2%} < threshold {args.threshold:.2%})")
        sys.exit(1)


if __name__ == "__main__":
    main()
