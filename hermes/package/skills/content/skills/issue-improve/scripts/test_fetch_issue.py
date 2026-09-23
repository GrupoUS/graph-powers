#!/usr/bin/env python3
"""Bounded issue retrieval tests with only the gh subprocess mocked."""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import unittest
from unittest.mock import patch

import fetch_issue

REPO = "github.example/acme/widgets"
ISSUE_URL = "https://github.example/acme/widgets/issues/20"
ISSUE = {
    "number": 20,
    "title": "Improve the report",
    "body": "Describe the requested change.",
    "state": "OPEN",
    "labels": [],
    "author": {"login": "reporter"},
    "url": ISSUE_URL,
    "createdAt": "2026-09-01T00:00:00Z",
    "closedAt": None,
    "comments": [],
}


class IssueFetchTests(unittest.TestCase):
    def run_cli(self, arguments, result=None, failure=None):
        stdout = io.StringIO()
        stderr = io.StringIO()
        self.call_count = 0
        self.call: tuple[list[str], dict[str, object]] | None = None

        def fake_run(argv, **kwargs):
            self.call_count += 1
            self.call = (argv, kwargs)
            if failure == "missing":
                raise FileNotFoundError("gh")
            if failure == "timeout":
                raise subprocess.TimeoutExpired(argv, kwargs["timeout"])
            if failure == "oserror":
                raise OSError("private details")
            if failure == "exit":
                return subprocess.CompletedProcess(argv, 1, "", "private response details")
            response = result if result is not None else ISSUE
            encoded = response if isinstance(response, str) else json.dumps(response)
            return subprocess.CompletedProcess(argv, 0, encoded, "")

        with (
            patch.object(fetch_issue.subprocess, "run", fake_run),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            code = fetch_issue.main(arguments)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_numeric_issue_uses_resolved_repo_and_timeout(self):
        code, stdout, stderr = self.run_cli(["--repo", REPO, "--issue", "#20"])
        self.assertEqual(code, 0, stderr)
        call = self.call
        assert call is not None
        argv, kwargs = call
        self.assertEqual(argv[:5], ["gh", "issue", "view", "20", "--repo"])
        self.assertEqual(argv[5], REPO)
        self.assertIn("--json", argv)
        self.assertEqual(kwargs["timeout"], fetch_issue.FETCH_TIMEOUT_SECONDS)
        self.assertEqual(json.loads(stdout), ISSUE)

    def test_canonical_url_must_match_resolved_repo(self):
        code, stdout, stderr = self.run_cli(["--repo", REPO, "--issue", ISSUE_URL])
        self.assertEqual(code, 0, stderr)
        call = self.call
        assert call is not None
        self.assertEqual(call[0][3], ISSUE_URL)
        self.assertEqual(json.loads(stdout), ISSUE)

        for url in (
            "http://github.example/acme/widgets/issues/20",
            "https://github.example/other/widgets/issues/20",
            ISSUE_URL + "?page=2",
            ISSUE_URL + "#comment",
        ):
            with self.subTest(url=url):
                code, _, stderr = self.run_cli(["--repo", REPO, "--issue", url])
                self.assertNotEqual(code, 0)
                self.assertIn("BLOCKED", stderr)
                self.assertIsNone(self.call)

    def test_missing_gh_timeout_and_api_errors_block_without_echoing_stderr(self):
        for failure, expected in (
            ("missing", "gh is unavailable"),
            ("timeout", "30-second limit"),
            ("oserror", "gh could not start"),
            ("exit", "gh issue view failed"),
        ):
            with self.subTest(failure=failure):
                code, stdout, stderr = self.run_cli(
                    ["--repo", REPO, "--issue", "20"], failure=failure
                )
                self.assertNotEqual(code, 0)
                self.assertIn("BLOCKED", stderr)
                self.assertIn(expected, stderr)
                self.assertNotIn("private details", stderr)
                self.assertNotIn("private response details", stderr)
                self.assertEqual(stdout, "")
                self.assertEqual(self.call_count, 1)

    def test_malformed_or_incomplete_json_blocks(self):
        for response in ("not json", {"number": 20}):
            with self.subTest(response=response):
                code, stdout, stderr = self.run_cli(
                    ["--repo", REPO, "--issue", "20"], result=response
                )
                self.assertNotEqual(code, 0)
                self.assertIn("BLOCKED", stderr)
                self.assertEqual(stdout, "")


if __name__ == "__main__":
    unittest.main()
