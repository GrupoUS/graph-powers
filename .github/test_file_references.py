"""Regression tests for the live-file reference gate."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import check_file_references


class FileReferenceTests(unittest.TestCase):
    def write(self, root: Path, relative: str, text: str = "") -> Path:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    def test_live_missing_reference_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, "skills/demo/SKILL.md", "Read references/missing.md before acting.\n")
            missing = check_file_references.scan(root)
            self.assertEqual(missing, {"references/missing.md": ["skills/demo/SKILL.md"]})

    def test_relative_reference_resolves_from_its_owner(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, "skills/demo/SKILL.md", "Read references/present.md before acting.\n")
            self.write(root, "skills/demo/references/present.md", "# Present\n")
            self.assertEqual(check_file_references.scan(root), {})

    def test_hidden_project_rules_are_live_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, ".claude/rules/demo.md", "Read references/missing.md.\n")
            missing = check_file_references.scan(root)
            self.assertEqual(missing, {"references/missing.md": [".claude/rules/demo.md"]})

    def test_live_rule_named_learning_is_not_misclassified_as_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, ".claude/rules/learning.md", "Read references/missing.md.\n")

            missing = check_file_references.scan(root)

            self.assertEqual(
                missing,
                {"references/missing.md": [".claude/rules/learning.md"]},
            )

    def test_historical_records_do_not_describe_the_current_tree(self) -> None:
        historical = (
            "CHANGELOG.md",
            "skills/demo/learning.md",
            "docs/plans/2026-01-01-retired/PLAN.md",
            "docs/AUDIT-REPORT-2026-01-01.md",
            ".graph-powers/logs/learnings.md",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in historical:
                self.write(root, relative, "Removed scripts/retired.py.\n")
            self.assertEqual(check_file_references.scan(root), {})

    def test_tracked_runtime_rule_is_a_live_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            rule = self.write(
                root,
                ".graph-powers/logs/tracked-rule.md",
                "Read references/missing.md before acting.\n",
            )
            subprocess.run(
                ["git", "add", "-f", rule.relative_to(root).as_posix()],
                cwd=root,
                check=True,
            )

            missing = check_file_references.scan(root)

            self.assertEqual(
                missing,
                {"references/missing.md": [".graph-powers/logs/tracked-rule.md"]},
            )

    def test_git_failure_in_a_worktree_scans_runtime_rules_conservatively(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            self.write(
                root,
                ".graph-powers/logs/tracked-rule.md",
                "Read references/missing.md before acting.\n",
            )

            with mock.patch.object(
                check_file_references.subprocess,
                "run",
                side_effect=OSError("git unavailable"),
            ):
                missing = check_file_references.scan(root)

            self.assertEqual(
                missing,
                {"references/missing.md": [".graph-powers/logs/tracked-rule.md"]},
            )


if __name__ == "__main__":
    unittest.main()
