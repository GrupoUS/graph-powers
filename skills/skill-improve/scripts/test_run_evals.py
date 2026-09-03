"""Security and CLI contract tests for run_evals.py."""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("run_evals.py")
SPEC = importlib.util.spec_from_file_location("run_evals", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
RUN_EVALS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUN_EVALS)


def eval_doc(case_id: str) -> dict:
    return {
        "skill": "fixture",
        "assertions": [
            {"id": "A01", "description": "contains ok", "check": "contains: ok", "critical": True}
        ],
        "test_cases": [{"id": case_id, "expected_assertions": ["A01"]}],
    }


def tagged_eval_doc() -> dict:
    return {
        "skill": "fixture",
        "assertions": [
            {
                "id": "A01",
                "description": "contains alpha",
                "check": "contains: alpha",
                "critical": True,
            },
            {
                "id": "A02",
                "description": "contains beta",
                "check": "contains: beta",
                "critical": True,
            },
        ],
        "test_cases": [
            {"id": "tagged", "tags": ["live"], "expected_assertions": ["A01"]},
            {"id": "untagged", "expected_assertions": ["A02"]},
        ],
    }


class RunEvalsTests(unittest.TestCase):
    def test_mode_a_entry_precedes_the_preserved_blocker(self) -> None:
        entry = "skill-improve Mode A — skill-authoring: RED established by evidence"
        preserved = "I’m blocked by a pre-existing permission constraint."
        synthetic = f"{entry}\n\n{preserved}"

        def first(response: str) -> str:
            return next(line.strip() for line in response.splitlines() if line.strip())

        pattern = r"skill-improve Mode A — skill-authoring: RED (pending|established by evidence)"
        self.assertIsNone(re.fullmatch(pattern, first(preserved)))
        self.assertIsNotNone(re.fullmatch(pattern, first(synthetic)))

        skill = SCRIPT.parents[1] / "SKILL.md"
        content = skill.read_text(encoding="utf-8")
        self.assertLess(content.index("[HARD] Entry protocol"), content.index("| Stage observed"))

    def test_case_tag_requires_per_case_response_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / "skill"
            skill.mkdir()
            evals = root / "evals.json"
            evals.write_text(json.dumps(tagged_eval_doc()), encoding="utf-8")
            response = root / "response.txt"
            response.write_text("alpha\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--skill-path",
                    str(skill),
                    "--evals-path",
                    str(evals),
                    "--response-file",
                    str(response),
                    "--case-tag",
                    "live",
                ],
                capture_output=True,
                encoding="utf-8",
                check=False,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("--case-tag requires --response-dir", result.stderr)

    def test_case_tag_selects_only_tagged_cases_and_missing_response_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            responses = root / "responses"
            responses.mkdir()
            (responses / "resp-tagged.txt").write_text("alpha\n", encoding="utf-8")

            rows, ok = RUN_EVALS.run_response_dir(
                tagged_eval_doc(), responses, threshold=1.0, case_tag="live"
            )

            self.assertTrue(ok)
            self.assertEqual([row["test_case"] for row in rows], ["tagged"])
            (responses / "resp-tagged.txt").unlink()
            rows, ok = RUN_EVALS.run_response_dir(
                tagged_eval_doc(), responses, threshold=1.0, case_tag="live"
            )
            self.assertFalse(ok)
            self.assertIn("response file not found", rows[0]["error"])

    def test_case_tag_with_zero_matches_fails_without_falling_back_to_all_cases(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            responses = root / "responses"
            responses.mkdir()

            rows, ok = RUN_EVALS.run_response_dir(
                tagged_eval_doc(), responses, threshold=1.0, case_tag="missing"
            )

            self.assertFalse(ok)
            self.assertIn("no test cases carry tag", rows[0]["error"])

    def test_existing_all_case_and_single_case_semantics_stay_unchanged(self) -> None:
        document = tagged_eval_doc()
        with tempfile.TemporaryDirectory() as directory:
            responses = Path(directory)
            (responses / "resp-tagged.txt").write_text("alpha\n", encoding="utf-8")
            (responses / "resp-untagged.txt").write_text("beta\n", encoding="utf-8")

            rows, ok = RUN_EVALS.run_response_dir(document, responses, threshold=1.0)
            self.assertTrue(ok)
            self.assertEqual([row["test_case"] for row in rows], ["tagged", "untagged"])
            single = RUN_EVALS.run_eval_suite(document, "beta\n", "untagged")
            self.assertEqual(single["pass_rate"], 1.0)

    def test_response_dir_reports_a_missing_case_id_without_aborting(self) -> None:
        document = eval_doc("T01")
        del document["test_cases"][0]["id"]
        with tempfile.TemporaryDirectory() as directory:
            responses = Path(directory)

            rows, ok = RUN_EVALS.run_response_dir(document, responses, threshold=1.0)

            self.assertFalse(ok)
            self.assertIn("missing test case id", rows[0]["error"])

    def test_response_dir_rejects_case_ids_that_can_escape_the_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            responses = root / "responses"
            (responses / "resp-x").mkdir(parents=True)
            (root / "secret.txt").write_text("ok\n", encoding="utf-8")

            rows, ok = RUN_EVALS.run_response_dir(
                eval_doc("x/../../secret"), responses, threshold=1.0
            )

            self.assertFalse(ok)
            self.assertIn("unsafe test case id", rows[0]["error"])

    def test_response_dir_rejects_a_symlinked_response(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            responses = root / "responses"
            responses.mkdir()
            secret = root / "secret.txt"
            secret.write_text("ok\n", encoding="utf-8")
            response = responses / "resp-T01.txt"
            try:
                response.symlink_to(secret)
            except OSError as error:
                self.skipTest(f"symlinks unavailable: {error}")

            rows, ok = RUN_EVALS.run_response_dir(eval_doc("T01"), responses, threshold=1.0)

            self.assertFalse(ok)
            self.assertIn("symlink", rows[0]["error"])

    def test_response_dir_reports_an_unreadable_response_without_aborting(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            responses = Path(directory)
            (responses / "resp-T01.txt").write_bytes(b"\xff\xfe\x00")

            rows, ok = RUN_EVALS.run_response_dir(eval_doc("T01"), responses, threshold=1.0)

            self.assertFalse(ok)
            self.assertIn("could not read response file", rows[0]["error"])

    def test_cli_has_no_arbitrary_json_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / "skill"
            skill.mkdir()
            evals = root / "evals.json"
            evals.write_text(json.dumps(eval_doc("T01")), encoding="utf-8")
            responses = root / "responses"
            responses.mkdir()
            (responses / "resp-T01.txt").write_text("ok\n", encoding="utf-8")
            outside = root / "outside.json"

            result = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(SCRIPT),
                    "--skill-path",
                    str(skill),
                    "--evals-path",
                    str(evals),
                    "--response-dir",
                    str(responses),
                    "--threshold",
                    "1.0",
                    "--json-output",
                    str(outside),
                ],
                capture_output=True,
                encoding="utf-8",
                check=False,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("unrecognized arguments", result.stderr)
            self.assertFalse(outside.exists())

    def test_response_file_mode_still_runs_after_json_output_removal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / "skill"
            skill.mkdir()
            evals = root / "evals.json"
            evals.write_text(json.dumps(eval_doc("T01")), encoding="utf-8")
            response = root / "response.txt"
            response.write_text("ok\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(SCRIPT),
                    "--skill-path",
                    str(skill),
                    "--evals-path",
                    str(evals),
                    "--response-file",
                    str(response),
                    "--test-case",
                    "T01",
                    "--threshold",
                    "1.0",
                ],
                capture_output=True,
                encoding="utf-8",
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("AttributeError", result.stderr)


if __name__ == "__main__":
    unittest.main()
