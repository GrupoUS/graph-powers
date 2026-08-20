#!/usr/bin/env python3
"""
run_evals.py — Binary Assertion Eval Runner for Skills

Inspired by karpathy/autoresearch: clear binary metrics, autonomous loop.
Runs assertions from evals.json against an agent response file.

Usage:
    python3 run_evals.py \
        --skill-path ${CLAUDE_PLUGIN_ROOT}/skills/meta-api-integration/SKILL.md \
        --evals-path ${CLAUDE_PLUGIN_ROOT}/skills/meta-api-integration/evals.json \
        --response-file /tmp/agent_response.txt \
        [--test-case T01] \
        [--threshold 0.95] \
        [--json-output /tmp/eval_results.json]

Exit codes:
    0 — pass_rate >= threshold (default 0.95)
    1 — pass_rate < threshold or error
"""

import argparse
import json
import re
import sys
from pathlib import Path


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
    with open(path, encoding="utf-8") as f:
        return normalize_evals(json.load(f))


def load_response(path: str) -> str:
    """Load the agent response text file."""
    with open(path, encoding="utf-8") as f:
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
    if assertion.get("manual"):
        return {
            "id": assertion["id"],
            "description": assertion["description"],
            "type": "manual",
            "critical": False,
            "manual": True,
            "passed": None,
            "detail": f"MANUAL — revise a mao: {assertion['description']}",
        }

    check_type, raw_value = parse_check(assertion["check"])
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

    return {
        "id": assertion["id"],
        "description": assertion["description"],
        "type": assertion.get("type", "unknown"),
        "critical": assertion.get("critical", False),
        "manual": False,
        "passed": passed,
        "detail": detail,
    }


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
        assertions_to_run = [assertions_map[aid] for aid in assertion_ids if aid in assertions_map]
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


def main():
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
    parser.add_argument(
        "--response-file",
        required=True,
        help="Path to text file containing the agent's output to evaluate",
    )
    parser.add_argument(
        "--test-case",
        default=None,
        help="Specific test case ID to run (e.g. T01). Runs all assertions if omitted.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.95,
        help="Minimum pass rate to exit 0 (default: 0.95)",
    )
    parser.add_argument(
        "--json-output",
        default=None,
        help="Optional path to write JSON results",
    )

    args = parser.parse_args()

    # Validate paths
    for label, path in [("skill", args.skill_path), ("evals", args.evals_path), ("response", args.response_file)]:
        if not Path(path).exists():
            print(f"ERROR: {label} file not found: {path}", file=sys.stderr)
            sys.exit(1)

    # Load inputs
    evals = load_json(args.evals_path)
    response = load_response(args.response_file)

    # Run evaluation
    summary = run_eval_suite(evals, response, args.test_case)

    # Handle errors
    if "error" in summary:
        print(f"ERROR: {summary['error']}", file=sys.stderr)
        if "available" in summary:
            print(f"Available test cases: {summary['available']}", file=sys.stderr)
        sys.exit(1)

    # Print results
    print_results(summary)

    # Write JSON output if requested
    if args.json_output:
        with open(args.json_output, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(f"  JSON results written to: {args.json_output}")

    # Exit code based on threshold
    if summary["pass_rate"] >= args.threshold:
        print(f"  ✅ PASSED (pass_rate {summary['pass_rate']:.2%} >= threshold {args.threshold:.2%})")
        sys.exit(0)
    else:
        print(f"  ❌ FAILED (pass_rate {summary['pass_rate']:.2%} < threshold {args.threshold:.2%})")
        sys.exit(1)


if __name__ == "__main__":
    main()
