#!/usr/bin/env python3
"""Regression tests for bin/statusline.py: the rendered line and its `--install` contract.

Every install runs against a temporary HOME, never the operator's Claude settings.
Run from the repository root:  python3 bin/test_statusline.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().with_name("statusline.py")


class StatusLineTest(unittest.TestCase):
    def render(self, payload, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            input=json.dumps(payload),
            capture_output=True,
            encoding="utf-8",
            check=True,
        ).stdout

    def test_main_shows_model_directory_and_context(self):
        output = self.render({
            "model": {"id": "claude-opus-5-5", "display_name": "Opus"},
            "workspace": {"current_dir": "/workspace/app", "project_dir": "/workspace/app"},
            "context_window": {"used_percentage": 42},
        })
        self.assertIn("claude-opus-5-5", output)
        self.assertIn("app", output)
        self.assertIn("● 42%", output)
        self.assertNotIn("left", output)
        self.assertNotIn("Opus", output)

    def test_main_survives_null_context(self):
        output = self.render({
            "model": {"id": "claude-opus-5-5"},
            "workspace": {"current_dir": "/workspace/app", "project_dir": "/workspace/app"},
            "context_window": {"used_percentage": None},
        })
        self.assertIn("claude-opus-5-5", output)
        self.assertIn("?", output)

    def test_main_shows_effort_rate_limits_and_worktree_branch(self):
        output = self.render({
            "model": {"id": "claude-opus-5-5"},
            "workspace": {"current_dir": "/workspace/app", "project_dir": "/workspace/app"},
            "context_window": {"used_percentage": 10},
            "effort": {"level": "xhigh"},
            "rate_limits": {
                "five_hour": {"used_percentage": 24, "resets_at": 1},
                "seven_day": {"used_percentage": 91, "resets_at": 2},
                "spend_limit": {"used_percentage": 30},
            },
            "worktree": {"name": "feat", "branch": "worktree-feat"},
        })
        for expected in ("xhigh", "● 10%", "5h 76% left", "7d !9% left", "spend 30%", "worktree-feat"):
            self.assertIn(expected, output)

    def test_null_window_and_sibling_directory_do_not_break_the_line(self):
        output = self.render({
            "model": {"id": "m"},
            "workspace": {"current_dir": "/w/app-old", "project_dir": "/w/app"},
            "context_window": {"used_percentage": 5},
            "rate_limits": {"five_hour": None, "seven_day": {"used_percentage": 7}},
        })
        self.assertIn("7d 93% left", output)
        self.assertIn("● 5%", output)
        self.assertIn("▸ app", output)
        self.assertNotIn("-old", output)

    def test_colour_follows_the_shown_number(self):
        def colour(used, key):
            payload = {"model": {"id": "m"}, "context_window": {"used_percentage": used}}
            if key == "5h":
                payload["rate_limits"] = {"five_hour": {"used_percentage": used}}
                return self.render(payload).split("5h ")[0][-5:]
            return self.render(payload).split("● ")[0][-5:]
        self.assertEqual(colour(89.6, "5h"), "\033[31m")  # shows 5h !10% left: red
        self.assertEqual(colour(49.6, "5h"), "\033[33m")  # shows 5h 50% left: yellow
        self.assertEqual(colour(10, "5h"), "\033[32m")  # shows 5h 90% left: green
        self.assertEqual(colour(89.6, "ctx"), "\033[31m")  # shows ● !90%: red
        self.assertEqual(colour(49.6, "ctx"), "\033[33m")  # shows ● 50%: yellow

    def test_subagents_survive_malformed_input(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--subagents"], input="not json",
            capture_output=True, encoding="utf-8", check=False,
        )
        self.assertEqual((result.returncode, result.stdout, "Traceback" in result.stderr), (0, "", False))

    def test_subagents_show_resolved_models_only(self):
        rows = [
            json.loads(line)
            for line in self.render({"tasks": [
                {"id": "a", "name": "explorer", "model": "m-1", "effort": "xhigh",
                 "tokenCount": 12000, "contextWindowSize": 200000},
                {"id": "b", "name": "pending"},
            ]}, "--subagents").splitlines()
        ]
        self.assertEqual([row["id"] for row in rows], ["a"])
        self.assertIn("xhigh", rows[0]["content"])
        self.assertIn("12000 tokens (6%)", rows[0]["content"])


class InstallTest(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp(prefix="gp-statusline-"))
        self.settings = self.home / ".claude" / "settings.json"
        self.target = self.home / ".claude" / "scripts" / "graph-powers-statusline.py"

    def tearDown(self):
        for path in sorted(self.home.rglob("*"), reverse=True):
            path.rmdir() if path.is_dir() else path.unlink()
        self.home.rmdir()

    def install(self, *flags, env=None):
        if env is None:
            env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CONFIG_DIR"}
            env.update(HOME=str(self.home), USERPROFILE=str(self.home))
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--install", *flags],
            capture_output=True, encoding="utf-8", env=env, check=False,
        )

    def write_settings(self, value):
        self.settings.parent.mkdir(parents=True, exist_ok=True)
        self.settings.write_text(json.dumps(value), encoding="utf-8")

    def read_settings(self):
        return json.loads(self.settings.read_text(encoding="utf-8"))

    def test_fresh_install_copies_script_and_sets_both_lines(self):
        self.write_settings({"model": "opus"})
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(self.target.read_bytes(), SCRIPT.read_bytes())
        settings = self.read_settings()
        command = f'python3 -X utf8 "{self.target.as_posix()}"'
        self.assertEqual(settings["model"], "opus")
        self.assertEqual(settings["statusLine"], {"type": "command", "command": command})
        self.assertEqual(settings["subagentStatusLine"]["command"], f"{command} --subagents")

    def test_second_install_changes_nothing(self):
        self.install()
        before = self.settings.read_bytes()
        result = self.install()
        self.assertIn("script current", result.stdout)
        self.assertEqual(self.settings.read_bytes(), before)
        self.assertFalse(self.target.with_name("graph-powers-statusline.py.bak").exists())

    def test_stale_copy_is_backed_up_then_refreshed(self):
        self.target.parent.mkdir(parents=True)
        self.target.write_text("print('old')\n", encoding="utf-8")
        self.install()
        self.assertEqual(self.target.read_bytes(), SCRIPT.read_bytes())
        backup = self.target.with_name("graph-powers-statusline.py.bak")
        self.assertEqual(backup.read_text(encoding="utf-8"), "print('old')\n")

    def test_operator_line_is_kept_unless_adopted(self):
        own = {"type": "command", "command": "bash ~/my-line.sh", "padding": 1}
        self.write_settings({"statusLine": own})
        kept = self.install()
        self.assertIn("kept the operator's own command", kept.stdout)
        self.assertEqual(self.read_settings()["statusLine"], own)
        adopted = self.install("--adopt")
        line = self.read_settings()["statusLine"]
        self.assertIn("replaced 'bash ~/my-line.sh'", adopted.stdout)
        self.assertIn("graph-powers-statusline.py", line["command"])
        self.assertEqual(line["padding"], 1)

    def test_claude_config_dir_and_userprofile_only(self):
        config = self.home / "custom-claude"
        base = {k: v for k, v in os.environ.items() if k not in ("HOME", "USERPROFILE", "CLAUDE_CONFIG_DIR")}
        result = self.install(env={**base, "USERPROFILE": str(self.home), "CLAUDE_CONFIG_DIR": str(config)})
        self.assertEqual(result.returncode, 0, result.stdout)
        settings = json.loads((config / "settings.json").read_text(encoding="utf-8"))
        self.assertIn((config / "scripts" / "graph-powers-statusline.py").as_posix(), settings["statusLine"]["command"])
        self.assertFalse(self.settings.exists())
        missing = self.install(env=dict(base))
        self.assertEqual(missing.returncode, 1)
        self.assertIn("nothing written", missing.stdout)

    def test_non_object_settings_stop_before_any_write(self):
        self.write_settings([1, 2])
        result = self.install()
        self.assertEqual(result.returncode, 1)
        self.assertFalse(self.target.exists())

    def test_malformed_settings_stop_before_any_write(self):
        self.settings.parent.mkdir(parents=True)
        self.settings.write_text("{not json", encoding="utf-8")
        result = self.install()
        self.assertEqual(result.returncode, 1)
        self.assertIn("nothing written", result.stdout)
        self.assertEqual(self.settings.read_text(encoding="utf-8"), "{not json")
        self.assertFalse(self.target.exists())


if __name__ == "__main__":
    unittest.main()
