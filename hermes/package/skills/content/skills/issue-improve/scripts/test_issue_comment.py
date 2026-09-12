#!/usr/bin/env python3
"""Real CLI regressions with only the external gh subprocess mocked; no network."""

from __future__ import annotations

import json
import runpy
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).with_name("issue_comment.py")
MARKER = "<!-- graph-powers:issue-improve -->"
URL = "https://github.example/acme/widgets/issues/20"
COMMENT_URL = URL + "#issuecomment-91"
BODY = MARKER + '\n\nR1: Corrigir "ação" — 中文; `$(false)`\n'


def fake_gh_runner():
    """Isolate argparse/main in a child process, replacing just gh's I/O seam."""
    state_file = Path(sys.argv[2])
    sys.argv = [str(SCRIPT), *sys.argv[3:]]
    state = json.loads(state_file.read_text(encoding="utf-8"))

    def gh(argv, **kwargs):
        assert argv[:2] == ["gh", "api"], argv
        assert kwargs.get("shell", False) is False
        assert argv[argv.index("--hostname") + 1] == "github.example"
        endpoint = argv[2]
        method = argv[argv.index("--method") + 1] if "--method" in argv else "GET"
        state["calls"].append({"endpoint": endpoint, "method": method})
        if state.get("missing"):
            raise FileNotFoundError("gh")
        if state.get("timeout") == method:
            raise subprocess.TimeoutExpired(argv, 30)
        if state.get("fail") in (endpoint, method):
            return subprocess.CompletedProcess(
                argv, 1, "", state.get("stderr", "HTTP 403: forbidden")
            )
        if endpoint == "user":
            result = {"id": 7, "login": "fixture-author"}
        elif method == "GET":
            assert (
                endpoint.rpartition("=")[0]
                == "repos/acme/widgets/issues/20/comments?per_page=100&page"
            ), endpoint
            page = int(endpoint.rsplit("=", 1)[1])
            result = state["comments"][(page - 1) * 100 : page * 100]
        else:
            assert argv[argv.index("--input") + 1] == "-"
            body = json.loads(kwargs["input"])["body"]
            if method == "POST":
                assert endpoint == "repos/acme/widgets/issues/20/comments", endpoint
                result = {"id": 91, "user": {"id": 7}, "body": body, "html_url": COMMENT_URL}
                state["comments"].append(result)
            else:
                assert method == "PATCH", method
                assert endpoint.rpartition("/")[0] == "repos/acme/widgets/issues/comments", endpoint
                comment_id = int(endpoint.rsplit("/", 1)[1])
                result = next(row for row in state["comments"] if row["id"] == comment_id)
                result["body"] = body
        if state.get("malformed") == endpoint:
            return subprocess.CompletedProcess(argv, 0, "not json", "")
        if state.get("shape") == endpoint:
            result = None
        return subprocess.CompletedProcess(argv, 0, json.dumps(result), "")

    try:
        with patch("subprocess.run", gh):
            runpy.run_path(str(SCRIPT), run_name="__main__")
    finally:
        state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")


class IssueCommentTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="issue-comment-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.draft = self.root / "reviewed draft.md"
        self.draft.write_text(BODY, encoding="utf-8")
        self.state_file = self.root / "fake.json"
        self.state = {"calls": [], "comments": []}

    def comment(self, body=MARKER + "\nold plan", author=7, comment_id=91):
        return {"id": comment_id, "user": {"id": author}, "body": body, "html_url": COMMENT_URL}

    def cli(self, *extra, issue_url=URL, required=True):
        self.state_file.write_text(json.dumps(self.state), encoding="utf-8")
        arguments = ["--issue-url", issue_url, "--body-file", str(self.draft)] if required else []
        result = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--fake-gh-runner",
                str(self.state_file),
                *arguments,
                *extra,
            ],
            capture_output=True,
            encoding="utf-8",
            check=False,
        )
        self.state = json.loads(self.state_file.read_text(encoding="utf-8"))
        return result

    def assert_blocked(self, result):
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("BLOCKED", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse(any(call["method"] in ("POST", "PATCH") for call in self.state["calls"]))

    def test_preview_is_default_and_never_calls_gh(self):
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(URL, result.stdout)
        self.assertIn(BODY, result.stdout)
        self.assertEqual(self.state["calls"], [])

    def test_creates_exact_unicode_payload_and_retry_is_unchanged(self):
        result = self.cli("--publish")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("created", result.stdout)
        self.assertIn(COMMENT_URL, result.stdout)
        self.assertNotIn(BODY, result.stdout)
        self.assertEqual(self.state["comments"][0]["body"], BODY)
        result = self.cli("--publish")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("unchanged", result.stdout)
        self.assertEqual(len(self.state["comments"]), 1)
        self.assertEqual(sum(row["method"] == "POST" for row in self.state["calls"]), 1)

    def test_updates_owned_marked_comment_and_preserves_unrelated(self):
        foreign = self.comment(author=8, comment_id=92)
        unmarked = self.comment(body="human discussion", comment_id=93)
        self.state["comments"] = [foreign, unmarked, self.comment()]
        result = self.cli("--publish")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("updated", result.stdout)
        self.assertEqual(self.state["comments"], [foreign, unmarked, self.comment(BODY)])

    def test_match_on_page_two_updates_instead_of_creating(self):
        self.state["comments"] = [self.comment(author=8, comment_id=n + 100) for n in range(100)]
        self.state["comments"].append(self.comment())
        result = self.cli("--publish")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("updated", result.stdout)
        self.assertEqual(len(self.state["comments"]), 101)
        self.assertEqual(self.state["comments"][-1]["body"], BODY)

    def test_foreign_unmarked_and_inline_markers_are_not_update_targets(self):
        existing = [
            self.comment(author=8),
            self.comment(body="plain", comment_id=92),
            self.comment(body="quoted " + MARKER, comment_id=93),
            self.comment(body="```\n" + MARKER + "\n```", comment_id=94),
        ]
        self.state["comments"] = existing.copy()
        result = self.cli("--publish")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("created", result.stdout)
        self.assertEqual(self.state["comments"][:-1], existing)

    def test_multiple_owned_markers_block_without_a_write(self):
        self.state["comments"] = [self.comment(), self.comment(comment_id=92)]
        self.assert_blocked(self.cli("--publish"))

    def test_duplicate_on_later_page_is_not_missed(self):
        self.state["comments"] = [self.comment()] + [
            self.comment(author=8, comment_id=n + 100) for n in range(99)
        ]
        self.state["comments"].append(self.comment(comment_id=92))
        self.assert_blocked(self.cli("--publish"))

    def test_invalid_or_noncanonical_targets_block_before_gh(self):
        for url in (
            "#20",
            "http://github.example/a/b/issues/20",
            "https://user:secret@github.example/a/b/issues/20",
            URL + "?other=1",
            URL + "#comment",
            "https://github.example/a/../issues/20",
            URL + "/extra",
            "https://github.example/a/b/issues/0",
            URL + "\n",
            URL + "?",
        ):
            with self.subTest(url=url):
                self.state = {"calls": [], "comments": []}
                self.assert_blocked(self.cli("--publish", issue_url=url))
                self.assertEqual(self.state["calls"], [])

    def test_oversized_draft_blocks_before_gh(self):
        self.draft.write_text(MARKER + "\n" + "x" * 65536, encoding="utf-8")
        self.assert_blocked(self.cli("--publish"))
        self.assertEqual(self.state["calls"], [])

    def test_missing_arguments_block(self):
        self.assert_blocked(self.cli(required=False))

    def test_missing_empty_unmarked_and_marker_only_drafts_block(self):
        self.draft.unlink()
        self.assert_blocked(self.cli("--publish"))
        for body in ("", " ", "plan without marker", MARKER, "prefix " + MARKER + "\nplan"):
            with self.subTest(body=body):
                self.draft.write_text(body, encoding="utf-8")
                self.assert_blocked(self.cli("--publish"))

    def test_missing_gh_auth_list_and_json_failures_block(self):
        endpoint = "repos/acme/widgets/issues/20/comments?per_page=100&page=1"
        for fault in (
            {"missing": True},
            {"fail": "user"},
            {"fail": endpoint},
            {"malformed": "user"},
            {"malformed": endpoint},
            {"shape": "user"},
            {"shape": endpoint},
            {"timeout": "GET"},
        ):
            with self.subTest(fault=fault):
                self.state = {"comments": [], "calls": [], **fault}
                self.assert_blocked(self.cli("--publish"))

    def test_write_failure_never_falls_back_or_retries(self):
        for method in ("POST", "PATCH"):
            with self.subTest(method=method):
                self.state = {
                    "comments": [self.comment()] if method == "PATCH" else [],
                    "calls": [],
                    "fail": method,
                    "stderr": "HTTP 403: token ghp_secret123 user@example.test",
                }
                result = self.cli("--publish")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("BLOCKED", result.stderr)
                self.assertIn("403", result.stderr)
                self.assertNotIn("ghp_secret123", result.stderr)
                self.assertNotIn("user@example.test", result.stderr)
                self.assertEqual(
                    [call["method"] for call in self.state["calls"] if call["method"] != "GET"],
                    [method],
                )

    def test_ambiguous_post_timeout_requires_fresh_read_on_retry(self):
        self.state = {"calls": [], "comments": [], "timeout": "POST"}
        result = self.cli("--publish")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("BLOCKED", result.stderr)
        self.assertEqual(sum(call["method"] == "POST" for call in self.state["calls"]), 1)
        self.state = {"calls": [], "comments": [self.comment(BODY)]}
        result = self.cli("--publish")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("unchanged", result.stdout)
        self.assertTrue(all(call["method"] == "GET" for call in self.state["calls"]))

    def test_documented_validation_command_reaches_real_plan_validator(self):
        plugin_root = SCRIPT.resolve().parents[3]
        method = SCRIPT.parents[1].joinpath("SKILL.md").read_text(encoding="utf-8")
        command = next(line for line in method.splitlines() if 'sdd.py" validate ' in line)
        plan = self.root / "PLAN.md"
        plan.write_text("# Deliberately invalid plan\n", encoding="utf-8")
        command = command.replace("${CLAUDE_PLUGIN_ROOT}", plugin_root.as_posix())
        command = command.replace("<resolved-plan-directory>", self.root.as_posix()).replace(
            "<resolved-cap>", "12"
        )
        argv = shlex.split(command, posix=True)
        argv[0] = sys.executable
        result = subprocess.run(
            argv, cwd=self.root, capture_output=True, encoding="utf-8", check=False
        )
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr.strip(),
            "plan validation failed: plan contains no structured tasks: route to /plan",
        )


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--fake-gh-runner":
        fake_gh_runner()
    else:
        unittest.main()
