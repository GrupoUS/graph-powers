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

    def test_generated_history_keeps_canonical_classification(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, "hermes/package/skills/content/skills/demo/learning.md", "Removed scripts/retired.py.\n")
            self.assertEqual(check_file_references.scan(root), {})

    def test_generated_operational_reference_cannot_fall_back_to_source_tree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            citing = "hermes/package/skills/demo.md"
            self.write(root, citing, "Read content/skills/demo/references/required.md.\n")
            self.write(root, "skills/demo/references/required.md", "# Source exists\n")
            self.assertEqual(check_file_references.scan(root), {
                "content/skills/demo/references/required.md": [citing],
            })
            self.write(root, "hermes/package/skills/content/skills/demo/references/required.md", "# Packaged\n")
            self.assertEqual(check_file_references.scan(root), {})

    def test_generated_auxiliary_uses_the_common_registration_parent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, "hermes/package/skills/content/references/shared/guide.md",
                       "Read content/skills/demo/references/required.md.\n")
            self.write(root, "hermes/package/skills/content/skills/demo/references/required.md", "# Present\n")
            self.assertEqual(check_file_references.scan(root), {})

    def test_relative_reference_resolves_from_its_owner(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, "skills/demo/SKILL.md", "Read references/present.md before acting.\n")
            self.write(root, "skills/demo/references/present.md", "# Present\n")
            self.assertEqual(check_file_references.scan(root), {})

    def test_explicit_dot_relative_references_resolve_only_from_the_owner(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(
                root,
                "skills/space demo/SKILL.md",
                "Read ./references/present.md.\n",
            )
            self.write(root, "skills/space demo/references/present.md", "# Present\n")
            self.write(root, "hooks/space demo.md", "Read ../skills/present.md.\n")
            self.write(root, "skills/present.md", "# Present\n")
            self.assertEqual(check_file_references.scan(root), {})

    def test_missing_explicit_dot_relative_reference_is_rejected_despite_root_homonym(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, "skills/demo/SKILL.md", "Read ../skills/missing.md.\n")
            self.write(root, "skills/missing.md", "# Wrong level\n")
            missing = check_file_references.scan(root)
            self.assertEqual(missing, {"../skills/missing.md": ["skills/demo/SKILL.md"]})

    def test_missing_current_directory_reference_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, "skills/demo/SKILL.md", "Read ./references/missing.md.\n")
            self.assertEqual(
                check_file_references.scan(root),
                {"./references/missing.md": ["skills/demo/SKILL.md"]},
            )

    def test_explicit_dot_relative_repository_escape_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, "skills/demo/SKILL.md", "Read ../../../skills/outside.md.\n")
            self.assertEqual(
                check_file_references.scan(root),
                {"../../../skills/outside.md": ["skills/demo/SKILL.md"]},
            )

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
            ".graph-powers/codex-native/generated.md",
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

    def test_untracked_project_contract_is_live_outside_generated_subtrees(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(
                root,
                ".graph-powers/policy.md",
                "Read references/missing.md before acting.\n",
            )
            self.assertEqual(
                check_file_references.scan(root),
                {"references/missing.md": [".graph-powers/policy.md"]},
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
