"""The Claude preset reuses Codex policy without replacing operator settings."""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "bin/claude-codex-preset.py"


class ClaudeCodexPresetTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.settings = Path(self.directory.name) / "settings.json"

    def run_preset(self, *args, script=SCRIPT):
        env = {**os.environ, "CLAUDE_CODE_SUBAGENT_MODEL_FORCE": "0"}
        return subprocess.run(
            [sys.executable, str(script), "--settings", str(self.settings), *args],
            capture_output=True, text=True, encoding="utf-8", check=False, env=env,
        )

    def test_preview_does_not_create_settings(self):
        result = self.run_preset()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.settings.exists())
        self.assertIn("gpt-6.1-sol", result.stdout)
        self.assertIn("gpt-6-luna", result.stdout)

    def test_apply_preserves_settings_and_is_idempotent(self):
        original = {
            "model": "opus", "effortLevel": "medium",
            "env": {
                "ANTHROPIC_BASE_URL": "http://127.0.0.1:18800",
                "ANTHROPIC_DEFAULT_OPUS_MODEL": "claude-opus-5-5",
                "ANTHROPIC_AUTH_TOKEN": "credential-sentinel",
            },
            "permissions": {"defaultMode": "default"},
            "hooks": {"SessionStart": []},
        }
        self.settings.write_text(json.dumps(original), encoding="utf-8")
        first = self.run_preset("--apply")
        self.assertEqual(first.returncode, 0, first.stderr)
        expected = json.loads(json.dumps(original))
        expected["env"].update({
            "ANTHROPIC_DEFAULT_SONNET_MODEL": "gpt-6.1-sol",
            "ANTHROPIC_DEFAULT_HAIKU_MODEL": "gpt-6-luna",
        })
        self.assertEqual(json.loads(self.settings.read_text()), expected)
        before = self.settings.stat().st_mtime_ns
        second = self.run_preset("--apply")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(self.settings.stat().st_mtime_ns, before)
        self.assertNotIn("credential-sentinel", first.stdout + first.stderr)

    def test_invalid_settings_are_never_overwritten(self):
        for content in ["{broken", "[]", '{"env": []}']:
            with self.subTest(content=content):
                self.settings.write_text(content, encoding="utf-8")
                result = self.run_preset("--apply")
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.settings.read_text(), content)

    def test_forced_model_blocks_apply_without_changes(self):
        content = '{"env": {"CLAUDE_CODE_SUBAGENT_MODEL_FORCE": "1"}}'
        self.settings.write_text(content, encoding="utf-8")
        result = self.run_preset("--apply")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.settings.read_text(), content)

    def test_models_come_from_the_plugin_policy(self):
        plugin = Path(self.directory.name) / "plugin"
        (plugin / "bin").mkdir(parents=True)
        (plugin / "codex").mkdir()
        shutil.copyfile(SCRIPT, plugin / "bin" / SCRIPT.name)
        policy = {
            "agentDefaults": {"evaluator": {"model": "custom-sol"}},
            "profiles": {"scout": {"model": "custom-luna"}},
        }
        (plugin / "codex/model-policy.json").write_text(json.dumps(policy), encoding="utf-8")
        result = self.run_preset("--apply", script=plugin / "bin" / SCRIPT.name)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(self.settings.read_text())["env"], {
            "ANTHROPIC_DEFAULT_SONNET_MODEL": "custom-sol",
            "ANTHROPIC_DEFAULT_HAIKU_MODEL": "custom-luna",
        })

    def test_requested_agents_declare_the_policy_model_id(self):
        policy = json.loads((ROOT / "codex/model-policy.json").read_text(encoding="utf-8"))
        for name in [
            "evaluator", "debugger", "project-planner", "verification",
            "performance-optimizer", "explorer", "librarian",
        ]:
            with self.subTest(agent=name):
                source = (ROOT / "agents" / f"{name}.md").read_text(encoding="utf-8")
                front = source.split("---", 2)[1]
                model_match = re.search(r"^model:\s*(.+)$", front, re.MULTILINE)
                assert model_match is not None, f"{name} has no model declaration"
                declared = model_match.group(1)
                expected = policy.get("agentDefaults", {}).get(name, {}).get("model")
                if expected is None:
                    expected = policy["profiles"][policy["agents"][name]]["model"]
                self.assertEqual(declared, expected)

    def test_plugin_agents_do_not_display_codex_models_as_claude_aliases(self):
        for path in (ROOT / "agents").glob("*.md"):
            with self.subTest(agent=path.stem):
                front = path.read_text(encoding="utf-8").split("---", 2)[1]
                model_match = re.search(r"^model:\s*(.+)$", front, re.MULTILINE)
                assert model_match is not None, f"{path.stem} has no model declaration"
                model = model_match.group(1)
                self.assertNotIn(model, {"haiku", "sonnet"})


if __name__ == "__main__":
    unittest.main()
