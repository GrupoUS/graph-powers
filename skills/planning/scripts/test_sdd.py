"""Focused contract tests for the planning SDD helper."""

from __future__ import annotations

import concurrent.futures
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from typing import TypedDict
from unittest import mock

import sdd as sdd_module


class TaskOutput(TypedDict):
    id: str
    acceptance: str
    skill: str
    needs: list[str]
    reads: dict[str, str]
    steps: list[str]


class GateOutput(TypedDict):
    id: str
    checked: bool
    check: str
    expect: str
    evidence: str


class ValidationOutput(TypedDict):
    tier: str
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


def plan_text(*tasks: str, gates: str | None = None, tier: str | None = "L4") -> str:
    if gates is None:
        phases = sorted(set(re.findall(r"\*\*T([0-9]+)", "\n".join(tasks))))
        gates = "\n".join(gate(f"G{phase}.1") for phase in phases)
    tier_line = f"**Tier:** {tier}\n\n" if tier is not None else ""
    return "# Plan\n\n" + tier_line + "## Phase 1 — Work [SEQUENTIAL]\n\n" + "\n".join(tasks) + "\n" + gates + "\n"


def task(task_id: str, owns: str = "src/main.py", needs: str = "none", *, acceptance: str = "the focused check prints ok", skill: str = "none", tdd: str = "not-applicable (configuration)", steps: str = "1. Read the existing contract", evidence: str = "pending", checked: bool = False) -> str:
    mark = "x" if checked else " "
    return f"""- [{mark}] **{task_id}** — Deliver {task_id}
  Owns: `{owns}`
  Needs: {needs}
  Acceptance: {acceptance}
  Agent: graph-powers:debugger · Skill: {skill} · Effort: mechanical
  CHECK: `python -X utf8 -c \"print('ok')\"`
  EXPECT: `ok`
  EVIDENCE: {evidence}
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

    def consult_request(
        self,
        *,
        task_id_value: str = "T2",
        decision_key: str = "architecture-boundary",
        requester_role: str = "parent",
        depth: int = 0,
        backend: str = "evaluator",
        capability_status: str = "SUPPORTED",
    ) -> dict[str, object]:
        return {
            "taskId": task_id_value,
            "decisionKey": decision_key,
            "question": "Which bounded design should the parent choose?",
            "evidence": ["existing contract", "focused test output"],
            "options": ["preserve", "replace"],
            "recommendation": "preserve",
            "risk": "replacement could widen scope",
            "verdict": "PENDING",
            "requesterRole": requester_role,
            "depth": depth,
            "backend": backend,
            "capabilityStatus": capability_status,
            "status": "RESERVED",
        }

    def consult_plan(self, root: Path) -> Path:
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        return self.write_plan(root, plan_text(task("T1.1")))

    def run_consult(
        self,
        action: str,
        plan: Path,
        envelope: dict[str, object],
    ) -> subprocess.CompletedProcess[str]:
        flag = "--request-json" if action == "reserve" else "--result-json"
        return self.run_cli("consult", action, str(plan), flag, json.dumps(envelope))

    def run_dispatch(
        self,
        plan: Path,
        key: str,
        *,
        kind: str = "writer",
        role: str = "graph-powers:debugger",
        maximum: int = 8,
    ) -> subprocess.CompletedProcess[str]:
        return self.run_cli(
            "dispatch", "reserve", str(plan),
            "--key", key,
            "--kind", kind,
            "--role", role,
            "--max-spawns", str(maximum),
        )

    def assert_valid(
        self,
        text: str,
        expected: int = 2,
        *,
        profile: str = "default",
    ) -> ValidationOutput:
        with tempfile.TemporaryDirectory() as directory:
            plan = self.write_plan(Path(directory), text)
            result = self.run_cli(
                "validate", str(plan), "--max-tasks", "10", "--profile", profile,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            output = json.loads(result.stdout)
            self.assertEqual(len(output["tasks"]), expected)
            return output

    def assert_invalid(
        self,
        text: str,
        expected: str,
        *,
        max_tasks: int = 10,
        profile: str = "default",
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plan = self.write_plan(Path(directory), text)
            result = self.run_cli(
                "validate", str(plan), "--max-tasks", str(max_tasks), "--profile", profile,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn(expected, result.stderr)

    def test_valid_dag_normalizes_tasks_and_lease(self) -> None:
        output = self.assert_valid(
            plan_text(
                task("T1.1", "src/api.py", tdd="required", steps="2. Write failing behavior test — RED\n    3. Implement the minimum — GREEN"),
                task("T2.1", "src/web.py", "T1.1 (reads: exported API response contract)"),
            )
        )
        self.assertEqual(output["tier"], "L4")
        self.assertEqual(output["tasks"][0]["acceptance"], "the focused check prints ok")
        self.assertEqual(output["tasks"][1]["needs"], ["T1.1"])
        self.assertEqual(output["tasks"][1]["reads"], {"T1.1": "exported API response contract"})
        self.assertEqual(output["writeLease"], ["src/api.py", "src/web.py"])
        self.assertEqual([item["id"] for item in output["gates"]], ["G1.1", "G2.1"])

    def test_tier_is_required_for_mechanical_execution_routing(self) -> None:
        self.assert_invalid(
            plan_text(task("T1.1"), tier=None),
            "missing required Tier",
        )

    def test_tier_normalizes_lowercase_across_the_supported_boundary(self) -> None:
        for number in range(1, 7):
            with self.subTest(tier=number):
                output = self.assert_valid(
                    plan_text(task("T1.1"), tier=f"l{number}"),
                    expected=1,
                )
                self.assertEqual(output["tier"], f"L{number}")

    def test_malformed_tier_routes_back_to_plan(self) -> None:
        self.assert_invalid(
            plan_text(task("T1.1"), tier="L7"),
            "malformed Tier",
        )

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

    def test_gate_rejects_placeholder_check_and_expect(self) -> None:
        self.assert_invalid(
            plan_text(task("T1.1"), gates=gate("G1.1", check="<run this gate>")),
            "Check is a placeholder",
        )
        self.assert_invalid(
            plan_text(task("T1.1"), gates=gate("G1.1", expect="<success output>")),
            "Expect is a placeholder",
        )

    def test_each_task_phase_requires_a_matching_gate(self) -> None:
        self.assert_invalid(
            plan_text(task("T1.1"), task("T2.1", "src/two.py"), gates=gate("G1.1")),
            "phase 2: missing structured gate",
        )

    def test_letter_suffixed_task_uses_its_numeric_phase(self) -> None:
        output = self.assert_valid(
            plan_text(task("T2a"), gates=gate("G2.1")),
            expected=1,
        )
        self.assertEqual(output["tasks"][0]["id"], "T2a")

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

    def test_field_shaped_lines_inside_steps_remain_steps(self) -> None:
        output = self.assert_valid(
            plan_text(
                task(
                    "T1.1",
                    tdd="required",
                    steps="\n    Check: capture the failing behavior — RED\n    Refactor: implement the minimum — GREEN",
                )
            ),
            expected=1,
        )
        self.assertEqual(
            output["tasks"][0]["steps"],
            [
                "Check: capture the failing behavior — RED",
                "Refactor: implement the minimum — GREEN",
            ],
        )

    def test_nested_step_checkboxes_do_not_truncate_the_task(self) -> None:
        output = self.assert_valid(
            plan_text(
                task(
                    "T1.1",
                    tdd="required",
                    steps="\n    - [ ] capture the failing behavior — RED\n    - [ ] implement the minimum — GREEN",
                )
            ),
            expected=1,
        )
        self.assertEqual(len(output["tasks"][0]["steps"]), 2)

    def test_unknown_agent_is_rejected(self) -> None:
        unknown = task("T1.1").replace("graph-powers:debugger", "graph-powers:not-a-real-agent")
        self.assert_invalid(plan_text(unknown), "unknown Agent")

    def test_codex_clone_resolves_canonical_runtime_files_for_both_scopes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            container = Path(directory)
            plugin_root = SCRIPT.parents[3]

            for scope in ("user", "project"):
                with self.subTest(scope=scope):
                    root = container / f"repo-{scope}"
                    root.mkdir()
                    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
                    home = container / f"home-{scope}"
                    codex_home = home / ".codex"
                    installed_script = (
                        home / ".agents/skills/planning/scripts/sdd.py"
                        if scope == "user"
                        else root / ".agents/skills/planning/scripts/sdd.py"
                    )
                    installed_script.parent.mkdir(parents=True)
                    installed_script.write_bytes(SCRIPT.read_bytes())
                    manifest = (
                        codex_home / "graph-powers-installed.json"
                        if scope == "user"
                        else root / ".graph-powers/installed.json"
                    )
                    manifest.parent.mkdir(parents=True)
                    manifest.write_text(
                        json.dumps(
                            {
                                "version": 1,
                                "pluginRoot": str(plugin_root),
                                "scope": scope,
                                "complete": True,
                                "paths": [str(installed_script.parents[1])],
                            }
                        ),
                        encoding="utf-8",
                    )
                    plan = self.write_plan(root, plan_text(task("T1.1")))
                    env = {
                        **os.environ,
                        "CODEX_HOME": str(codex_home),
                        "HOME": str(home),
                    }

                    validated = subprocess.run(
                        [
                            sys.executable,
                            "-X",
                            "utf8",
                            str(installed_script),
                            "validate",
                            str(plan),
                            "--max-tasks",
                            "10",
                        ],
                        cwd=root,
                        env=env,
                        capture_output=True,
                        encoding="utf-8",
                        check=False,
                    )
                    self.assertEqual(validated.returncode, 0, validated.stderr)

                    acquired = subprocess.run(
                        [
                            sys.executable,
                            "-X",
                            "utf8",
                            str(installed_script),
                            "acquire",
                            str(plan),
                            "--max-tasks",
                            "10",
                        ],
                        cwd=root,
                        env=env,
                        capture_output=True,
                        encoding="utf-8",
                        check=False,
                    )
                    self.assertEqual(acquired.returncode, 0, acquired.stderr)

                    dispatched = subprocess.run(
                        [
                            sys.executable,
                            "-X",
                            "utf8",
                            str(installed_script),
                            "dispatch",
                            "reserve",
                            str(plan),
                            "--key",
                            f"{scope}:writer-1",
                            "--kind",
                            "writer",
                            "--role",
                            "graph-powers:debugger",
                            "--max-spawns",
                            "8",
                        ],
                        cwd=root,
                        env=env,
                        capture_output=True,
                        encoding="utf-8",
                        check=False,
                    )
                    self.assertEqual(dispatched.returncode, 0, dispatched.stderr)
                    self.assertEqual(json.loads(dispatched.stdout)["status"], "RESERVED")

    def test_codex_clone_without_manifest_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            container = Path(directory)
            root = container / "repo"
            root.mkdir()
            installed_script = container / "home/.agents/skills/planning/scripts/sdd.py"
            installed_script.parent.mkdir(parents=True)
            installed_script.write_bytes(SCRIPT.read_bytes())
            plan = self.write_plan(root, plan_text(task("T1.1")))

            result = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(installed_script),
                    "validate",
                    str(plan),
                    "--max-tasks",
                    "10",
                ],
                cwd=root,
                env={
                    **os.environ,
                    "CODEX_HOME": str(container / "empty-codex-home"),
                    "HOME": str(container / "home"),
                },
                capture_output=True,
                encoding="utf-8",
                check=False,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("unknown Agent graph-powers:debugger", result.stderr)

    def test_acceptance_is_required_and_must_be_observable(self) -> None:
        missing = task("T1.1").replace("  Acceptance: the focused check prints ok\n", "")
        self.assert_valid(plan_text(missing), expected=1)
        self.assert_invalid(
            plan_text(missing),
            "missing required field Acceptance",
            profile="gauntlet",
        )
        self.assert_invalid(
            plan_text(task("T1.1", acceptance="<observable outcome>")),
            "Acceptance is a placeholder",
            profile="gauntlet",
        )
        self.assert_valid(
            plan_text(task("T1.1", acceptance="looks correct")), expected=1,
        )
        self.assert_invalid(
            plan_text(task("T1.1", acceptance="looks correct")),
            "Acceptance is not observable",
            profile="gauntlet",
        )

    def test_skill_must_be_none_or_resolve_to_a_bundled_skill(self) -> None:
        self.assert_valid(plan_text(task("T1.1", skill="made-up")), expected=1)
        self.assert_invalid(
            plan_text(task("T1.1", skill="made-up")),
            "unknown Skill",
            profile="gauntlet",
        )
        bare = self.assert_valid(
            plan_text(task("T1.1", skill="debugger")), expected=1, profile="gauntlet",
        )
        self.assertEqual(bare["tasks"][0]["skill"], "debugger")
        namespaced = self.assert_valid(
            plan_text(task("T1.1", skill="graph-powers:debugger")),
            expected=1,
            profile="gauntlet",
        )
        self.assertEqual(namespaced["tasks"][0]["skill"], "graph-powers:debugger")

    def test_gauntlet_acquire_repeats_profile_admission_before_lease(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            missing = task("T1.1").replace("  Acceptance: the focused check prints ok\n", "")
            plan = self.write_plan(root, plan_text(missing))
            default = self.run_cli("validate", str(plan), "--max-tasks", "10")
            self.assertEqual(default.returncode, 0, default.stderr)

            acquire = self.run_cli(
                "acquire", str(plan), "--max-tasks", "10", "--profile", "gauntlet",
            )

            self.assertEqual(acquire.returncode, 2)
            self.assertIn("missing required field Acceptance", acquire.stderr)
            self.assertFalse((root / ".graph-powers/logs/write-lease.json").exists())

    def test_main_thread_agent_is_not_routable_in_phase_c(self) -> None:
        inline = task("T1.1").replace("graph-powers:debugger", "main")
        self.assert_invalid(plan_text(inline), "not routable in Phase C")

    def test_read_only_worker_is_not_a_phase_c_writer(self) -> None:
        read_only = task("T1.1").replace("graph-powers:debugger", "graph-powers:verification")
        self.assert_valid(plan_text(read_only), expected=1)
        self.assert_invalid(
            plan_text(read_only),
            "not a write-capable Phase C lane",
            profile="gauntlet",
        )

    def test_checked_task_requires_persisted_evidence(self) -> None:
        checked = task("T1.1", checked=True)
        self.assert_invalid(plan_text(checked), "checked task still has EVIDENCE pending")

    def test_checked_tdd_task_requires_observed_red_and_green_evidence(self) -> None:
        incomplete = task(
            "T1.1",
            tdd="required",
            steps="1. Write failing behavior test — RED\n    2. Implement minimum fix — GREEN",
            evidence="focused check passed",
            checked=True,
        )
        self.assert_invalid(plan_text(incomplete), "missing observed RED/GREEN evidence")

        complete = task(
            "T1.1",
            tdd="required",
            steps="1. Write failing behavior test — RED\n    2. Implement minimum fix — GREEN",
            evidence="RED: test failed before fix; GREEN: test passed after fix",
            checked=True,
        )
        self.assert_valid(plan_text(complete), expected=1)

    def test_windows_separators_normalize_to_posix_lease_paths(self) -> None:
        output = self.assert_valid(plan_text(task("T1.1", "src\\api.py")), expected=1)
        self.assertEqual(output["writeLease"], ["src/api.py"])

    def test_workspace_rejects_symlinked_directory_and_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            container = Path(directory)
            root = container / "repo"
            root.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            plan = self.write_plan(root, plan_text(task("T1.1")))
            workspace_parent = root / ".graph-powers/logs/sdd"
            workspace_parent.mkdir(parents=True)
            outside = container / "outside"
            outside.mkdir()
            workspace_link = workspace_parent / root.name
            try:
                workspace_link.symlink_to(outside, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"symlinks unavailable: {error}")

            escaped_directory = self.run_cli("brief", str(plan), "T1.1")
            self.assertEqual(escaped_directory.returncode, 2)
            self.assertIn("symlink", escaped_directory.stderr)
            self.assertFalse((outside / "task-1.1-brief.md").exists())

            workspace_link.unlink()
            workspace_link.mkdir()
            outside_file = outside / "brief.md"
            target_link = workspace_link / "task-1.1-brief.md"
            target_link.symlink_to(outside_file)
            escaped_file = self.run_cli("brief", str(plan), "T1.1")
            self.assertEqual(escaped_file.returncode, 2)
            self.assertIn("symlink", escaped_file.stderr)
            self.assertFalse(outside_file.exists())

    def test_concurrent_acquire_keeps_one_plan_lease_and_release_checks_owner(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            plans: list[Path] = []
            for name, owns in (("alpha", "src/a.py"), ("beta", "src/b.py")):
                plan_dir = root / "plans" / name
                plan_dir.mkdir(parents=True)
                plan = plan_dir / "PLAN.md"
                plan.write_text(plan_text(task("T1.1", owns)), encoding="utf-8")
                plans.append(plan)

            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(
                    lambda plan: self.run_cli("acquire", str(plan), "--max-tasks", "10"),
                    plans,
                ))

            self.assertEqual(sorted(result.returncode for result in results), [0, 2])
            lease_path = root / ".graph-powers/logs/write-lease.json"
            lease = json.loads(lease_path.read_text(encoding="utf-8"))
            winner = next(plan for plan, result in zip(plans, results, strict=True) if result.returncode == 0)
            loser = next(plan for plan, result in zip(plans, results, strict=True) if result.returncode == 2)
            self.assertEqual(lease["plan"], winner.relative_to(root).as_posix())

            wrong_release = self.run_cli("release", str(loser))
            self.assertEqual(wrong_release.returncode, 2)
            self.assertTrue(lease_path.exists())
            release = self.run_cli("release", str(winner))
            self.assertEqual(release.returncode, 0, release.stderr)
            self.assertFalse(lease_path.exists())

    def test_dispatch_cap_survives_resume_and_resets_only_for_a_new_lease(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = self.consult_plan(root)
            acquired = self.run_cli("acquire", str(plan), "--max-tasks", "10")
            self.assertEqual(acquired.returncode, 0, acquired.stderr)

            for number in range(1, 8):
                reserved = self.run_dispatch(plan, f"wave-1:writer-{number}")
                self.assertEqual(reserved.returncode, 0, reserved.stderr)
                self.assertEqual(json.loads(reserved.stdout)["sequence"], number)
            final = self.run_dispatch(
                plan,
                "final:evaluator",
                kind="evaluator",
                role="graph-powers:evaluator",
            )
            self.assertEqual(final.returncode, 0, final.stderr)
            self.assertEqual(json.loads(final.stdout)["sequence"], 8)

            duplicate = self.run_dispatch(plan, "wave-1:writer-1")
            self.assertEqual(duplicate.returncode, 0, duplicate.stderr)
            duplicate_output = json.loads(duplicate.stdout)
            self.assertTrue(duplicate_output["resumed"])
            self.assertEqual(duplicate_output["used"], 8)

            ninth = self.run_dispatch(plan, "wave-2:writer-1")
            self.assertEqual(ninth.returncode, 4)
            self.assertEqual(json.loads(ninth.stdout)["status"], "BLOCKED")

            resumed = self.run_cli("acquire", str(plan), "--max-tasks", "10")
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            still_blocked = self.run_dispatch(plan, "wave-2:writer-1")
            self.assertEqual(still_blocked.returncode, 4)

            released = self.run_cli("release", str(plan))
            self.assertEqual(released.returncode, 0, released.stderr)
            reacquired = self.run_cli("acquire", str(plan), "--max-tasks", "10")
            self.assertEqual(reacquired.returncode, 0, reacquired.stderr)
            fresh = self.run_dispatch(plan, "wave-2:writer-1")
            self.assertEqual(fresh.returncode, 0, fresh.stderr)
            self.assertEqual(json.loads(fresh.stdout)["sequence"], 1)

    def test_duplicate_dispatch_key_returns_no_second_launch_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = self.consult_plan(root)
            acquired = self.run_cli("acquire", str(plan), "--max-tasks", "10")
            self.assertEqual(acquired.returncode, 0, acquired.stderr)

            first = self.run_dispatch(plan, "wave-1:writer-1")
            resumed = self.run_cli("acquire", str(plan), "--max-tasks", "10")
            duplicate = self.run_dispatch(plan, "wave-1:writer-1")
            retry = self.run_dispatch(plan, "wave-1:writer-1-retry")

            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            self.assertEqual(duplicate.returncode, 0, duplicate.stderr)
            self.assertEqual(retry.returncode, 0, retry.stderr)
            self.assertEqual(json.loads(first.stdout)["status"], "RESERVED")
            self.assertEqual(json.loads(duplicate.stdout)["status"], "ALREADY_RESERVED")
            self.assertEqual(json.loads(retry.stdout)["sequence"], 2)

    def test_concurrent_duplicate_dispatch_keys_authorize_exactly_one_launch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = self.consult_plan(root)
            acquired = self.run_cli("acquire", str(plan), "--max-tasks", "10")
            self.assertEqual(acquired.returncode, 0, acquired.stderr)

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
                results = list(pool.map(
                    lambda _number: self.run_dispatch(plan, "parallel:writer-1"),
                    range(10),
                ))

            outputs = [json.loads(result.stdout) for result in results]
            self.assertTrue(all(result.returncode == 0 for result in results))
            self.assertEqual([output["status"] for output in outputs].count("RESERVED"), 1)
            self.assertEqual(
                [output["status"] for output in outputs].count("ALREADY_RESERVED"), 9,
            )
            ledger_path = root / ".graph-powers/logs/sdd" / root.name / "dispatches.json"
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            self.assertEqual(len(ledger["reservations"]), 1)

    def test_dispatch_requires_lease_canonical_role_and_schema_ceiling(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = self.consult_plan(root)
            unleased = self.run_dispatch(plan, "wave-1:writer-1")
            self.assertEqual(unleased.returncode, 2)
            self.assertIn("active plan write lease", unleased.stderr)

            acquired = self.run_cli("acquire", str(plan), "--max-tasks", "10")
            self.assertEqual(acquired.returncode, 0, acquired.stderr)
            read_only_writer = self.run_dispatch(
                plan, "wave-1:writer-1", role="graph-powers:evaluator"
            )
            self.assertEqual(read_only_writer.returncode, 2)
            self.assertIn("write-capable", read_only_writer.stderr)
            invented = self.run_dispatch(
                plan, "wave-1:bootstrap", kind="bootstrap", role="graph-powers:invented"
            )
            self.assertEqual(invented.returncode, 2)
            self.assertIn("existing graph-powers agent", invented.stderr)
            over_schema = self.run_dispatch(plan, "wave-1:writer-1", maximum=9)
            self.assertEqual(over_schema.returncode, 2)
            self.assertIn("between 1 and 8", over_schema.stderr)

    def test_concurrent_dispatch_reservations_cannot_cross_the_cap(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = self.consult_plan(root)
            acquired = self.run_cli("acquire", str(plan), "--max-tasks", "10")
            self.assertEqual(acquired.returncode, 0, acquired.stderr)

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
                results = list(pool.map(
                    lambda number: self.run_dispatch(plan, f"parallel:writer-{number}"),
                    range(10),
                ))

            self.assertEqual([result.returncode for result in results].count(0), 8)
            self.assertEqual([result.returncode for result in results].count(4), 2)
            ledger_path = root / ".graph-powers/logs/sdd" / root.name / "dispatches.json"
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            self.assertEqual(len(ledger["reservations"]), 8)
            self.assertEqual(
                sorted(entry["sequence"] for entry in ledger["reservations"].values()),
                list(range(1, 9)),
            )

    def test_exclusive_write_publishes_only_complete_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "write-lease.json"
            entered_write = threading.Event()
            continue_write = threading.Event()
            errors: list[BaseException] = []
            real_fdopen = sdd_module.os.fdopen

            def delayed_fdopen(
                descriptor: int,
                mode: str,
                *,
                encoding: str,
                newline: str,
            ):
                entered_write.set()
                if not continue_write.wait(timeout=5):
                    raise TimeoutError("test writer did not resume")
                return real_fdopen(
                    descriptor,
                    mode,
                    encoding=encoding,
                    newline=newline,
                )

            def write() -> None:
                try:
                    sdd_module._write_text_no_symlink(
                        target,
                        '{"plan": "PLAN.md"}\n',
                        exclusive=True,
                    )
                except BaseException as error:  # pragma: no cover - asserted below
                    errors.append(error)

            with mock.patch.object(sdd_module.os, "fdopen", side_effect=delayed_fdopen):
                writer = threading.Thread(target=write)
                writer.start()
                self.assertTrue(entered_write.wait(timeout=5))
                try:
                    self.assertFalse(
                        target.exists(),
                        "an exclusive state file became visible before its contents were written",
                    )
                finally:
                    continue_write.set()
                    writer.join(timeout=5)

            self.assertFalse(writer.is_alive())
            self.assertEqual(errors, [])
            self.assertEqual(target.read_text(encoding="utf-8"), '{"plan": "PLAN.md"}\n')

    def test_exclusive_write_failure_leaves_no_canonical_file(self) -> None:
        class FailingWriter:
            def __enter__(self) -> FailingWriter:
                return self

            def __exit__(self, *_args: object) -> None:
                return None

            def write(self, _text: str) -> None:
                raise OSError("simulated interrupted write")

        def failing_fdopen(descriptor: int, *_args: object, **_kwargs: object) -> FailingWriter:
            sdd_module.os.close(descriptor)
            return FailingWriter()

        with (
            tempfile.TemporaryDirectory() as directory,
            mock.patch.object(sdd_module.os, "fdopen", side_effect=failing_fdopen),
            mock.patch.object(
                sdd_module,
                "fail",
                side_effect=OSError("expected write failure"),
            ),
        ):
            target = Path(directory) / "write-lease.json"
            self.assertRaises(
                OSError,
                sdd_module._write_text_no_symlink,
                target,
                '{"plan": "PLAN.md"}\n',
                exclusive=True,
            )
            self.assertFalse(target.exists())

    def test_release_rejects_a_symlinked_state_parent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            container = Path(directory)
            root = container / "repo"
            root.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            plan = self.write_plan(root, plan_text(task("T1.1")))
            outside_state = container / "outside-state"
            logs = outside_state / "logs"
            logs.mkdir(parents=True)
            lease = logs / "write-lease.json"
            lease.write_text(json.dumps({"plan": "PLAN.md", "paths": ["PLAN.md"]}), encoding="utf-8")
            try:
                (root / ".graph-powers").symlink_to(outside_state, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"symlinks unavailable: {error}")

            result = self.run_cli("release", str(plan))

            self.assertEqual(result.returncode, 2)
            self.assertIn("symlink", result.stderr)
            self.assertTrue(lease.exists())

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
            outside_brief = root.parent / f"{root.name}-outside-brief.md"
            escaped_brief = self.run_cli("brief", str(plan), "T1.1", str(outside_brief))
            self.assertEqual(escaped_brief.returncode, 2)
            self.assertFalse(outside_brief.exists())
            subprocess.run(["git", "add", "PLAN.md"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "plan"], cwd=root, check=True)
            (root / "src").mkdir()
            (root / "src/main.py").write_text("changed\n", encoding="utf-8")
            package = self.run_cli("package", str(plan), "HEAD", "HEAD")
            self.assertEqual(package.returncode, 0, package.stderr)
            reports = list((root / ".graph-powers/logs/sdd" / root.name).glob("review-*.diff"))
            self.assertEqual(len(reports), 1)
            self.assertIn("working-tree snapshot", reports[0].read_text(encoding="utf-8"))
            outside_package = root.parent / f"{root.name}-outside-package.diff"
            escaped_package = self.run_cli(
                "package", str(plan), "HEAD", "HEAD", str(outside_package)
            )
            self.assertEqual(escaped_package.returncode, 2)
            self.assertFalse(outside_package.exists())
            ref_expression = self.run_cli("package", str(plan), "HEAD^{tree}", "HEAD")
            self.assertEqual(ref_expression.returncode, 2)
            self.assertIn("bad BASE", ref_expression.stderr)

    def test_consult_reserve_record_and_duplicate_reuse(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = self.consult_plan(root)
            request = self.consult_request()

            reserved = self.run_consult("reserve", plan, request)
            self.assertEqual(reserved.returncode, 0, reserved.stderr)
            reservation = json.loads(reserved.stdout)
            self.assertEqual(reservation["status"], "RESERVED")
            self.assertEqual(reservation["decisionKey"], request["decisionKey"])

            result = dict(request)
            result.update({"verdict": "PASS", "status": "RECORDED"})
            recorded = self.run_consult("record", plan, result)
            self.assertEqual(recorded.returncode, 0, recorded.stderr)
            recorded_output = json.loads(recorded.stdout)
            self.assertEqual(recorded_output["status"], "RECORDED")
            self.assertEqual(recorded_output["verdict"], "PASS")

            duplicate = self.run_consult("reserve", plan, request)
            self.assertEqual(duplicate.returncode, 0, duplicate.stderr)
            self.assertEqual(json.loads(duplicate.stdout), recorded_output)

            duplicate_record = self.run_consult("record", plan, result)
            self.assertEqual(duplicate_record.returncode, 0, duplicate_record.stderr)
            self.assertEqual(json.loads(duplicate_record.stdout), recorded_output)

    def test_consultation_cap_is_per_task_and_fresh_task_gets_new_budget(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = self.consult_plan(root)
            for number in range(1, 4):
                request = self.consult_request(decision_key=f"choice-{number}")
                result = self.run_consult("reserve", plan, request)
                self.assertEqual(result.returncode, 0, result.stderr)

            capped = self.run_consult(
                "reserve", plan, self.consult_request(decision_key="choice-4"),
            )
            self.assertEqual(capped.returncode, 4)
            capped_output = json.loads(capped.stdout)
            self.assertEqual(capped_output["status"], "USER_REQUIRED")
            self.assertIn("cap", capped_output["reason"])

            fresh = self.run_consult(
                "reserve", plan, self.consult_request(task_id_value="T3", decision_key="choice-1"),
            )
            self.assertEqual(fresh.returncode, 0, fresh.stderr)
            self.assertEqual(json.loads(fresh.stdout)["status"], "RESERVED")

    def test_consult_rejects_malformed_identity_and_forbidden_requesters(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = self.consult_plan(root)
            for invalid in (
                self.consult_request(task_id_value=""),
                self.consult_request(decision_key="prompt contains sensitive text"),
                self.consult_request(decision_key="../escape"),
            ):
                result = self.run_consult("reserve", plan, invalid)
                self.assertEqual(result.returncode, 2)
                self.assertFalse((root / ".graph-powers/logs/sdd" / root.name / "consultations.json").exists())

            for role in ("evaluator", "reviewer", "critic"):
                result = self.run_consult(
                    "reserve", plan, self.consult_request(requester_role=role),
                )
                self.assertEqual(result.returncode, 2)
            nested = self.run_consult("reserve", plan, self.consult_request(depth=1))
            self.assertEqual(nested.returncode, 2)

    def test_consult_requires_bounded_nonempty_evidence_and_options(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = self.consult_plan(root)
            for field, value in (("evidence", []), ("options", []), ("evidence", ["x" * 4097])):
                request = self.consult_request(decision_key=f"invalid-{field}-{len(str(value))}")
                request[field] = value
                result = self.run_consult("reserve", plan, request)
                self.assertEqual(result.returncode, 2)
            self.assertFalse((root / ".graph-powers/logs/sdd" / root.name / "consultations.json").exists())

    def test_consult_capability_fallback_and_blocked_state_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = self.consult_plan(root)
            supported = self.run_consult(
                "reserve", plan, self.consult_request(decision_key="native-supported", backend="fable"),
            )
            self.assertEqual(supported.returncode, 0, supported.stderr)
            self.assertEqual(json.loads(supported.stdout)["backend"], "fable")
            for status in ("UNSUPPORTED", "UNKNOWN"):
                request = self.consult_request(
                    decision_key=f"fallback-{status.lower()}",
                    backend="fable",
                    capability_status=status,
                )
                result = self.run_consult("reserve", plan, request)
                self.assertEqual(result.returncode, 0, result.stderr)
                output = json.loads(result.stdout)
                self.assertEqual(output["backend"], "evaluator")
                self.assertEqual(output["capabilityStatus"], status)
                self.assertNotIn("fable", result.stdout.lower())
                self.assertTrue(output["fallback"])

            blocked_request = self.consult_request(
                task_id_value="T3",
                decision_key="blocked-capability",
                backend="fable",
                capability_status="UNAVAILABLE",
            )
            blocked = self.run_consult("reserve", plan, blocked_request)
            self.assertEqual(blocked.returncode, 4)
            blocked_output = json.loads(blocked.stdout)
            self.assertEqual(blocked_output["status"], "BLOCKED")
            self.assertEqual(blocked_output["verdict"], "BLOCKED")

            duplicate = self.run_consult("reserve", plan, blocked_request)
            self.assertEqual(duplicate.returncode, 4)
            self.assertEqual(json.loads(duplicate.stdout), blocked_output)

    def test_consult_rejects_symlinked_ledger_and_concurrent_duplicate_is_atomic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            container = Path(directory)
            root = container / "repo"
            root.mkdir()
            plan = self.consult_plan(root)
            request = self.consult_request()
            first = self.run_consult("reserve", plan, request)
            self.assertEqual(first.returncode, 0, first.stderr)
            ledger = root / ".graph-powers/logs/sdd" / root.name / "consultations.json"
            outside = container / "outside.json"
            outside.write_text("outside\n", encoding="utf-8")
            saved = json.loads(ledger.read_text(encoding="utf-8"))
            ledger.unlink()
            try:
                ledger.symlink_to(outside)
            except OSError as error:
                self.skipTest(f"symlinks unavailable: {error}")
            rejected = self.run_consult(
                "reserve", plan, self.consult_request(decision_key="symlink-attempt"),
            )
            self.assertEqual(rejected.returncode, 2)
            self.assertIn("symlink", rejected.stderr.lower())
            self.assertEqual(outside.read_text(encoding="utf-8"), "outside\n")
            ledger.unlink()
            ledger.write_text(json.dumps(saved), encoding="utf-8")

            duplicate_request = self.consult_request(decision_key="concurrent")
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(
                    lambda _: self.run_consult("reserve", plan, duplicate_request), range(2),
                ))
            self.assertEqual([result.returncode for result in results], [0, 0])
            self.assertEqual(json.loads(results[0].stdout), json.loads(results[1].stdout))

    def test_consult_docs_define_one_envelope_and_separate_reviews(self) -> None:
        sources = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                Path("references/execution-floor.md"),
                Path("skills/senior-prompt-engineer/references/agent-handoff-contracts.md"),
                Path("skills/planning/references/phase-c-executing-plans.md"),
                Path("skills/planning/references/gauntlet-loop.md"),
                Path("agents/evaluator.md"),
            )
        )
        for field in (
            "taskId", "decisionKey", "question", "evidence", "options", "recommendation",
            "risk", "verdict", "requesterRole", "depth", "backend", "capabilityStatus", "status",
        ):
            self.assertIn(field, sources)
        self.assertRegex(sources, r"(?i)review.{0,80}(separate|distinct|not).{0,80}consult")
        self.assertRegex(sources, r"(?i)evaluator.{0,80}(no|cannot).{0,80}(spawn|consult)")


if __name__ == "__main__":
    unittest.main()
