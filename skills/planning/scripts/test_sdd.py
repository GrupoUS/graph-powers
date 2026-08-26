"""Focused contract tests for the planning SDD helper."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import TypedDict


class TaskOutput(TypedDict):
    needs: list[str]
    reads: dict[str, str]


class GateOutput(TypedDict):
    id: str
    checked: bool
    check: str
    expect: str
    evidence: str


class ValidationOutput(TypedDict):
    tasks: list[TaskOutput]
    gates: list[GateOutput]
    writeLease: list[str]


SCRIPT = Path(__file__).with_name("sdd.py")


def gate(gate_id: str, *, checked: bool = False, check: str = "python -X utf8 -c \"print('gate ok')\"", expect: str = "gate ok", evidence: str = "pending") -> str:
    mark = "x" if checked else " "
    return f"""- [{mark}] **{gate_id}** — Close {gate_id}
  CHECK: `{check}`
  EXPECT: `{expect}`
  EVIDENCE: {evidence}
"""


def plan_text(*tasks: str, gates: str | None = None) -> str:
    if gates is None:
        phases = sorted(set(re.findall(r"\*\*T([0-9]+)", "\n".join(tasks))))
        gates = "\n".join(gate(f"G{phase}.1") for phase in phases)
    return "# Plan\n\n## Phase 1 — Work [SEQUENTIAL]\n\n" + "\n".join(tasks) + "\n" + gates + "\n"


def task(task_id: str, owns: str = "src/main.py", needs: str = "none", *, tdd: str = "not-applicable (configuration)", steps: str = "1. Read the existing contract") -> str:
    return f"""- [ ] **{task_id}** — Deliver {task_id}
  Owns: `{owns}`
  Needs: {needs}
  Agent: graph-powers:debugger · Skill: none · Effort: mechanical
  CHECK: `python -X utf8 -c \"print('ok')\"`
  EXPECT: `ok`
  EVIDENCE: pending
  TDD: {tdd}
  Steps:
    {steps}
"""


class SddCliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-X", "utf8", str(SCRIPT), *args],
            capture_output=True,
            encoding="utf-8",
            cwd=SCRIPT.parents[3],
            check=False,
        )

    def write_plan(self, root: Path, text: str) -> Path:
        path = root / "PLAN.md"
        path.write_text(text, encoding="utf-8")
        return path

    def assert_valid(self, text: str, expected: int = 2) -> ValidationOutput:
        with tempfile.TemporaryDirectory() as directory:
            plan = self.write_plan(Path(directory), text)
            result = self.run_cli("validate", str(plan), "--max-tasks", "10")
            self.assertEqual(result.returncode, 0, result.stderr)
            output = json.loads(result.stdout)
            self.assertEqual(len(output["tasks"]), expected)
            return output

    def assert_invalid(self, text: str, expected: str, *, max_tasks: int = 10) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plan = self.write_plan(Path(directory), text)
            result = self.run_cli("validate", str(plan), "--max-tasks", str(max_tasks))
            self.assertEqual(result.returncode, 2)
            self.assertIn(expected, result.stderr)

    def test_valid_dag_normalizes_tasks_and_lease(self) -> None:
        output = self.assert_valid(
            plan_text(
                task("T1.1", "src/api.py", tdd="required", steps="2. Write failing behavior test — RED\n    3. Implement the minimum — GREEN"),
                task("T2.1", "src/web.py", "T1.1 (reads: exported API response contract)"),
            )
        )
        self.assertEqual(output["tasks"][1]["needs"], ["T1.1"])
        self.assertEqual(output["tasks"][1]["reads"], {"T1.1": "exported API response contract"})
        self.assertEqual(output["writeLease"], ["src/api.py", "src/web.py"])
        self.assertEqual([item["id"] for item in output["gates"]], ["G1.1", "G2.1"])

    def test_plan_requires_a_structured_phase_gate(self) -> None:
        self.assert_invalid(plan_text(task("T1.1"), gates=""), "missing structured gate")

    def test_checked_gate_requires_persisted_evidence(self) -> None:
        self.assert_invalid(
            plan_text(task("T1.1"), gates=gate("G1.1", checked=True)),
            "checked gate still has EVIDENCE pending",
        )

    def test_gate_requires_check_expect_and_evidence(self) -> None:
        incomplete = """- [ ] **G1.1** — Close G1.1
  CHECK: `python -X utf8 -c \"print('ok')\"`
  EVIDENCE: pending
"""
        self.assert_invalid(plan_text(task("T1.1"), gates=incomplete), "missing required field Expect")

    def test_each_task_phase_requires_a_matching_gate(self) -> None:
        self.assert_invalid(
            plan_text(task("T1.1"), task("T2.1", "src/two.py"), gates=gate("G1.1")),
            "phase 2: missing structured gate",
        )

    def test_duplicate_gate_id_is_rejected(self) -> None:
        self.assert_invalid(
            plan_text(task("T1.1"), gates=gate("G1.1") + gate("G1.1")),
            "duplicate gate id",
        )

    def test_duplicate_id(self) -> None:
        self.assert_invalid(plan_text(task("T1.1"), task("T1.1", "src/other.py")), "duplicate task id")

    def test_unknown_dependency(self) -> None:
        self.assert_invalid(plan_text(task("T2.1", needs="T9.9 (reads: missing output)")), "unknown dependency")

    def test_cycle(self) -> None:
        self.assert_invalid(
            plan_text(task("T1.1", "src/a.py", "T2.1 (reads: b)"), task("T2.1", "src/b.py", "T1.1 (reads: a)")),
            "dependency cycle",
        )

    def test_missing_reads_payload(self) -> None:
        self.assert_invalid(plan_text(task("T1.1"), task("T2.1", "src/b.py", "T1.1")), "reads")

    def test_max_tasks(self) -> None:
        self.assert_invalid(plan_text(task("T1.1"), task("T2.1", "src/b.py")), "exceeding", max_tasks=1)

    def test_concurrent_owns_conflict(self) -> None:
        self.assert_invalid(plan_text(task("T1.1", "src/shared.py"), task("T2.1", "src/shared.py")), "concurrent Owns conflict")

    def test_sequential_reuse_is_allowed(self) -> None:
        output = self.assert_valid(
            plan_text(task("T1.1", "src/shared.py"), task("T2.1", "src/shared.py", "T1.1 (reads: prior implementation)"))
        )
        self.assertEqual(output["writeLease"], ["src/shared.py"])

    def test_legacy_plan_is_rejected_without_field_inference(self) -> None:
        self.assert_invalid(
            "# Plan\n\n### Task 1: legacy prose\n\nImplement the feature.\n",
            "route to /plan",
        )

    def test_tdd_required_needs_red_and_green_steps(self) -> None:
        self.assert_invalid(
            plan_text(task("T1.1", tdd="required", steps="1. Write a test after implementation")),
            "no RED step",
        )

    def test_unknown_agent_is_rejected(self) -> None:
        unknown = task("T1.1").replace("graph-powers:debugger", "graph-powers:not-a-real-agent")
        self.assert_invalid(plan_text(unknown), "unknown Agent")

    def test_main_thread_agent_is_not_routable_in_phase_c(self) -> None:
        inline = task("T1.1").replace("graph-powers:debugger", "main")
        self.assert_invalid(plan_text(inline), "not routable in Phase C")

    def test_checked_task_requires_persisted_evidence(self) -> None:
        checked = task("T1.1").replace("- [ ]", "- [x]", 1)
        self.assert_invalid(plan_text(checked), "checked task still has EVIDENCE pending")

    def test_windows_separators_normalize_to_posix_lease_paths(self) -> None:
        output = self.assert_valid(plan_text(task("T1.1", "src\\api.py")), expected=1)
        self.assertEqual(output["writeLease"], ["src/api.py"])

    def test_workspace_brief_and_package_regressions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            plan = self.write_plan(root, plan_text(task("T1.1", "src/main.py")))
            workspace = self.run_cli("workspace", str(plan))
            self.assertEqual(workspace.returncode, 0, workspace.stderr)
            self.assertTrue(Path(workspace.stdout.strip()).is_dir())
            brief = self.run_cli("brief", str(plan), "T1.1")
            self.assertEqual(brief.returncode, 0, brief.stderr)
            brief_path = root / ".graph-powers/logs/sdd" / root.name / "task-1.1-brief.md"
            self.assertIn("Deliver T1.1", brief_path.read_text(encoding="utf-8"))
            subprocess.run(["git", "add", "PLAN.md"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "plan"], cwd=root, check=True)
            (root / "src").mkdir()
            (root / "src/main.py").write_text("changed\n", encoding="utf-8")
            package = self.run_cli("package", str(plan), "HEAD", "HEAD")
            self.assertEqual(package.returncode, 0, package.stderr)
            reports = list((root / ".graph-powers/logs/sdd" / root.name).glob("review-*.diff"))
            self.assertEqual(len(reports), 1)
            self.assertIn("working-tree snapshot", reports[0].read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
