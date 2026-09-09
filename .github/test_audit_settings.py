#!/usr/bin/env python3
"""Regression coverage for the read-only Claude settings auditor."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AUDITOR = ROOT / "bin" / "audit-settings.mjs"
HOOKS = ROOT / "hooks" / "hooks.json"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def hook_command(hooks: dict[str, Any], matcher: str, filename: str) -> str:
    for group in hooks["hooks"]["PreToolUse"]:
        if group.get("matcher") != matcher:
            continue
        for hook in group["hooks"]:
            if hook["command"].endswith(filename + '"'):
                return hook["command"]
    raise AssertionError(f"missing canonical {matcher} hook for {filename}")


def test_auditor_reads_canonical_hooks_and_identifies_runpy_wrappers() -> None:
    bun = shutil.which("bun")
    assert bun, "bun is required for the audit-settings regression"
    canonical = read_json(HOOKS)
    canonical_count = sum(
        len(group.get("hooks", []))
        for groups in canonical["hooks"].values()
        for group in groups
    )
    commit_gate = hook_command(canonical, "Bash", "git_commit_gate.py").replace(
        "${CLAUDE_PLUGIN_ROOT}", "/project with spaces/.claude/plugins/graph-powers"
    )
    protect_files = hook_command(canonical, "Edit|Write|NotebookEdit", "protect_files.py").replace(
        "${CLAUDE_PLUGIN_ROOT}", "/project with spaces/.claude/plugins/graph-powers"
    )

    with tempfile.TemporaryDirectory(prefix="gp-audit-settings-") as directory:
        project = Path(directory)
        settings = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Bash",
                        "hooks": [{"type": "command", "command": commit_gate + " --project-hook"}],
                    },
                    {
                        "matcher": "Edit|Write",
                        "hooks": [{"type": "command", "command": protect_files}],
                    },
                    {
                        "matcher": "Read",
                        "hooks": [
                            {"type": "command", "command": "node /project/hooks/audit.js"},
                            {"type": "command", "command": "sh /project/hooks/audit.sh"},
                        ],
                    },
                ]
            }
        }
        settings_path = project / ".claude" / "settings.json"
        settings_path.parent.mkdir()
        settings_path.write_text(json.dumps(settings), encoding="utf-8")

        result = subprocess.run(
            [bun, str(AUDITOR), "--json"],
            cwd=project,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=30,
        )

    assert result.returncode == 0, (result.stdout, result.stderr)
    audit = json.loads(result.stdout)
    assert audit["pluginHooks"] == canonical_count, audit
    assert audit["projectHooks"] == 4, audit
    assert [hook["key"].split("::")[-1] for hook in audit["duplicated"]] == [
        "git_commit_gate.py"
    ], audit
    assert [hook["key"].split("::")[-1] for hook in audit["overlapping"]] == [
        "protect_files.py"
    ], audit
    assert [hook["key"].split("::")[-1] for hook in audit["exclusive"]] == [
        "audit.js",
        "audit.sh",
    ], audit


def main() -> int:
    test_auditor_reads_canonical_hooks_and_identifies_runpy_wrappers()
    print("audit-settings: canonical hook regression held")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
