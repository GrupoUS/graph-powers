"""Focused contract tests for the clean-session trigger-eval producer."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("capture_trigger_evals.py")
SPEC = importlib.util.spec_from_file_location("capture_trigger_evals", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
CAPTURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CAPTURE)


def eval_document() -> dict:
    return {
        "skill_name": "skill-improve",
        "evals": [
            {
                "id": "pro-precreate-skill",
                "tags": ["proactive-live"],
                "prompt": "Create a reusable skill for safely redacting support exports.",
                "expected": "load",
                "assertions": [],
            },
            {
                "id": "bound-agent-prompt-draft",
                "tags": ["proactive-live"],
                "prompt": "Draft the prompt for a new reviewer agent.",
                "expected": "skip",
                "assertions": [],
            },
        ],
    }


def executable(root: Path, backend: str, mode: str = "good") -> Path:
    path = root / f"fake-{backend}.py"
    source = f"#!{sys.executable}\n" + """import json, os, sys
if '--version' in sys.argv:
    print('fake-1.0')
    raise SystemExit(0)
marker = os.environ.get('CAPTURE_CWD_MARKER')
if marker:
    with open(marker, 'a', encoding='utf-8') as handle:
        handle.write(os.getcwd() + '\\n')
prompt = sys.argv[-1]
mode = os.environ.get('CAPTURE_MODE', 'good')
if mode == 'auth':
    print('authentication failed')
    raise SystemExit(1)
if mode == 'malformed':
    print('{not json')
    raise SystemExit(0)
if mode == 'incomplete':
    print(json.dumps({'type': 'assistant'}))
    raise SystemExit(0)
load = 'Create a reusable skill' in prompt
if 'claude' in os.path.basename(sys.argv[0]):
    if load:
        print(json.dumps({'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': 'Skill', 'input': {'skill': 'graph-powers:skill-improve'}}]}}))
else:
    if load:
        print(json.dumps({'type': 'item.completed', 'item': {'arguments': json.dumps({'path': '.agents/skills/skill-improve/SKILL.md'})}}))
print(json.dumps({'type': 'result', 'result': 'skill-improve Mode A' if load else 'senior-prompt-engineer'}))
"""
    path.write_text(source, encoding="utf-8")
    path.chmod(0o700)
    return path


class CaptureTriggerEvalsTests(unittest.TestCase):
    def test_digest_is_stable_and_rejects_symlinks_in_candidate_surface(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "skills").mkdir()
            (root / "skills" / "entry.txt").write_text("one\n", encoding="utf-8")
            first = CAPTURE.compute_candidate_digest(root)
            second = CAPTURE.compute_candidate_digest(root)
            self.assertEqual(first, second)
            try:
                (root / "skills" / "link.txt").symlink_to("entry.txt")
            except OSError as error:
                self.skipTest(f"symlinks unavailable: {error}")
            with self.assertRaisesRegex(ValueError, "symlink"):
                CAPTURE.compute_candidate_digest(root)

    def test_fake_streams_capture_fresh_projects_exact_prompts_and_polarity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plugin = root / "plugin"
            (plugin / "skills").mkdir(parents=True)
            (plugin / "skills" / "entry.txt").write_text("candidate\n", encoding="utf-8")
            evals = root / "evals.json"
            evals.write_text(json.dumps(eval_document()), encoding="utf-8")
            responses = root / "responses"
            marker = root / "cwds.txt"
            old_marker = os.environ.get("CAPTURE_CWD_MARKER")
            os.environ["CAPTURE_CWD_MARKER"] = str(marker)
            try:
                result = CAPTURE.capture_trials(
                    phase="candidate", plugin_root=plugin, evals_path=evals, response_dir=responses,
                    trials=["codex:pro-precreate-skill", "claude:bound-agent-prompt-draft"],
                    timeout_seconds=5, executable_paths={
                        "codex": executable(root, "codex"),
                        "claude": executable(root, "claude"),
                    }, install_codex=False,
                )
            finally:
                if old_marker is None:
                    os.environ.pop("CAPTURE_CWD_MARKER", None)
                else:
                    os.environ["CAPTURE_CWD_MARKER"] = old_marker

            self.assertEqual(result, 0)
            traces = [json.loads((responses / f"trace-{backend}-{case}.json").read_text(encoding="utf-8"))
                      for backend, case in [("codex", "pro-precreate-skill"), ("claude", "bound-agent-prompt-draft")]]
            self.assertEqual([(trace["expected"], trace["observed"]) for trace in traces], [("load", "load"), ("skip", "skip")])
            self.assertEqual(len({trace["candidate_digest"] for trace in traces}), 1)
            self.assertEqual((responses / "resp-pro-precreate-skill.txt").read_text(encoding="utf-8"), "skill-improve Mode A")
            self.assertEqual((responses / "resp-bound-agent-prompt-draft.txt").read_text(encoding="utf-8"), "senior-prompt-engineer")
            cwd_values = marker.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(cwd_values), 2)
            self.assertEqual(len(set(cwd_values)), 2)
            self.assertTrue(all(not Path(value, "AGENTS.md").exists() for value in cwd_values))

    def test_declared_infrastructure_failures_are_failures(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plugin = root / "plugin"
            (plugin / "skills").mkdir(parents=True)
            (plugin / "skills" / "entry.txt").write_text("candidate\n", encoding="utf-8")
            evals = root / "evals.json"
            evals.write_text(json.dumps(eval_document()), encoding="utf-8")
            fake = executable(root, "codex")
            for mode in ("auth", "malformed", "incomplete"):
                old_mode = os.environ.get("CAPTURE_MODE")
                os.environ["CAPTURE_MODE"] = mode
                try:
                    result = CAPTURE.capture_trials(
                        phase="candidate", plugin_root=plugin, evals_path=evals, response_dir=root / mode,
                        trials=["codex:pro-precreate-skill"], timeout_seconds=5,
                        executable_paths={"codex": fake}, install_codex=False,
                    )
                finally:
                    if old_mode is None:
                        os.environ.pop("CAPTURE_MODE", None)
                    else:
                        os.environ["CAPTURE_MODE"] = old_mode
                self.assertEqual(result, 1, mode)
            self.assertEqual(CAPTURE.capture_trials(
                phase="candidate", plugin_root=plugin, evals_path=evals, response_dir=root / "missing",
                trials=["codex:pro-precreate-skill"], timeout_seconds=5,
                executable_paths={"codex": root / "absent"}, install_codex=False,
            ), 1)
            self.assertEqual(CAPTURE.capture_trials(
                phase="candidate", plugin_root=plugin, evals_path=evals, response_dir=root / "timeout",
                trials=["codex:pro-precreate-skill"], timeout_seconds=0.0001,
                executable_paths={"codex": fake}, install_codex=False,
            ), 1)

    def test_primed_prompt_is_rejected_before_provider_execution(self) -> None:
        document = eval_document()
        document["evals"][0]["prompt"] = "Load skill-improve before writing the answer."
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evals = root / "evals.json"
            evals.write_text(json.dumps(document), encoding="utf-8")
            self.assertEqual(CAPTURE.capture_trials(
                phase="baseline", plugin_root=root, evals_path=evals, response_dir=root / "responses",
                trials=["codex:pro-precreate-skill"], timeout_seconds=5,
                executable_paths={"codex": root / "not-called"}, install_codex=False,
            ), 1)


if __name__ == "__main__":
    unittest.main()
