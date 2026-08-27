#!/usr/bin/env python3
"""Regression tests for installed hook-package verification and safe posture ordering."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
VERIFY = ROOT / "bin" / "verify-hook-clients.py"
INSTALLER = ROOT / "bin" / "graph-powers.mjs"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def copy_package(destination: Path) -> Path:
    for name in (".claude-plugin", ".codex-plugin", ".cursor-plugin", ".grok-plugin", "hooks"):
        source = ROOT / name
        target = destination / name
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)
    planning = destination / "skills/planning"
    planning.mkdir(parents=True)
    shutil.copy2(ROOT / "skills/planning/SKILL.md", planning / "SKILL.md")
    for relative in (
        "references/phase-c-executing-plans.md",
        "references/execution/tdd-policy.md",
    ):
        target = planning / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / "skills/planning" / relative, target)
    return destination


def environment(home: Path, **extra: str) -> dict[str, str]:
    env = dict(os.environ)
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    env.pop("CLAUDE_CONFIG_DIR", None)
    env.pop("CODEX_HOME", None)
    env.pop("GROK_HOME", None)
    env.update(extra)
    return env


def verify(
    home: Path,
    client: str,
    *extra: str,
    env_extra: dict[str, str] | None = None,
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    env = environment(home, **(env_extra or {}))
    result = subprocess.run(
        [
            sys.executable,
            str(VERIFY),
            "--client",
            client,
            "--plugin-root",
            str(ROOT),
            "--json",
            *extra,
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=60,
    )
    try:
        body = json.loads(result.stdout)
    except ValueError as exc:
        raise AssertionError(
            f"verifier did not emit JSON (exit {result.returncode}):\n{result.stdout}\n{result.stderr}"
        ) from exc
    return result, body


def old_direct_commands(package: Path, *, cursor: bool = False) -> None:
    relative = "hooks/hooks-cursor.json" if cursor else "hooks/hooks.json"
    path = package / relative
    data = json.loads(path.read_text(encoding="utf-8"))
    if cursor:
        entries = [hook for hooks in data["hooks"].values() for hook in hooks]
    else:
        entries = [
            hook
            for groups in data["hooks"].values()
            for group in groups
            for hook in group["hooks"]
        ]
    for hook in entries:
        hook["command"] = hook["command"].replace(
            "python3 -X utf8 -c \"import os,runpy,sys;p=sys.argv[1];runpy.run_path(p,run_name='__main__') if os.path.isfile(p) else None\" ",
            "python3 ",
        )
    write_json(path, data)


def test_claude_uses_the_exact_scoped_install() -> None:
    with tempfile.TemporaryDirectory(prefix="gp-client-claude-") as raw:
        base = Path(raw)
        home = base / "home"
        project = base / "project"
        user_package = copy_package(base / "user-package")
        project_package = copy_package(base / "project-package")
        old_direct_commands(project_package)
        version = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))["version"]
        registry = {
            "plugins": {
                "graph-powers@graph-powers": [
                    {
                        "scope": "user",
                        "installPath": str(user_package),
                        "version": version,
                    },
                    {
                        "scope": "project",
                        "projectPath": str(project),
                        "installPath": str(project_package),
                        "version": version,
                    },
                ]
            }
        }
        write_json(home / ".claude/plugins/installed_plugins.json", registry)
        settings_path = home / ".claude/settings.json"
        write_json(settings_path, {"enabledPlugins": {"graph-powers@graph-powers": True}})

        result, body = verify(
            home,
            "claude",
            "--scope",
            "user",
            "--project-dir",
            str(project),
        )
        assert result.returncode == 0, body
        assert body["root"] == str(user_package.resolve()), body

        write_json(settings_path, {"enabledPlugins": {"graph-powers@graph-powers": False}})
        result, body = verify(home, "claude", "--scope", "user", "--project-dir", str(project))
        assert result.returncode != 0, body
        assert any("not enabled" in message for message in body["errors"]), body

        write_json(settings_path, {"enabledPlugins": {"graph-powers@graph-powers": True}})
        old_direct_commands(user_package)
        result, body = verify(home, "claude", "--scope", "user", "--project-dir", str(project))
        assert result.returncode != 0, body
        assert any("fail-open" in message for message in body["errors"]), body


def test_cursor_rejects_corrupt_and_ambiguous_cache_entries() -> None:
    with tempfile.TemporaryDirectory(prefix="gp-client-cursor-") as raw:
        home = Path(raw) / "home"
        cache = home / ".cursor/plugins/cache/graph-powers/graph-powers"
        valid = copy_package(cache / "valid")
        corrupt = cache / "newer-corrupt"
        (corrupt / ".cursor-plugin").mkdir(parents=True)
        (corrupt / ".cursor-plugin/plugin.json").write_text("{not json", encoding="utf-8")

        result, body = verify(home, "cursor")
        assert result.returncode != 0, body
        assert any("corrupt" in message for message in body["errors"]), body

        shutil.rmtree(corrupt)
        result, body = verify(home, "cursor")
        assert result.returncode == 0, body
        assert body["root"] == str(valid.resolve()), body

        copy_package(cache / "same-version")
        result, body = verify(home, "cursor")
        assert result.returncode != 0, body
        assert any("ambiguous" in message for message in body["errors"]), body


def test_grok_inventory_and_posture_use_grok_home() -> None:
    with tempfile.TemporaryDirectory(prefix="gp-client-grok-") as raw:
        base = Path(raw)
        home = base / "home"
        grok_home = base / "custom-grok-home"
        package = copy_package(base / "grok-package")
        version = json.loads((package / ".grok-plugin/plugin.json").read_text(encoding="utf-8"))["version"]
        inventory = base / "grok-plugins.json"
        write_json(
            inventory,
            [
                {
                    "status": "installed",
                    "name": "graph-powers",
                    "version": version,
                    "path": str(package),
                }
            ],
        )
        grok_home.mkdir(parents=True)
        (grok_home / "config.toml").write_text(
            '[ui]\npermission_mode = "always-approve"\n', encoding="utf-8"
        )

        result, body = verify(
            home,
            "grok",
            "--inventory-file",
            str(inventory),
            "--check-posture",
            "--autonomy",
            "autonomous",
            env_extra={"GROK_HOME": str(grok_home)},
        )
        assert result.returncode == 0, body
        assert body["posture"]["config"] == str((grok_home / "config.toml").resolve()), body

        (grok_home / "config.toml").write_text(
            '[ui]\npermission_mode = "ask"\n', encoding="utf-8"
        )
        result, body = verify(
            home,
            "grok",
            "--inventory-file",
            str(inventory),
            "--check-posture",
            "--autonomy",
            "autonomous",
            env_extra={"GROK_HOME": str(grok_home)},
        )
        assert result.returncode != 0, body
        assert any("always-approve" in message for message in body["errors"]), body

        (grok_home / "config.toml").write_text(
            '[other]\npermission_mode = "always-approve"\n[ui]\npermission_mode = "ask"\n',
            encoding="utf-8",
        )
        result, body = verify(
            home,
            "grok",
            "--inventory-file",
            str(inventory),
            "--check-posture",
            "--autonomy",
            "autonomous",
            env_extra={"GROK_HOME": str(grok_home)},
        )
        assert result.returncode != 0, body
        assert body["posture"]["permissionMode"] == "ask", body


def test_codex_home_distinguishes_blocked_from_inert_missing_paths() -> None:
    with tempfile.TemporaryDirectory(prefix="gp-codex-home-audit-") as raw:
        base = Path(raw)
        home = base / "home"
        missing_old = base / "removed-old/hooks/graph_guardrails.py"
        missing_guarded = base / "removed-new/hooks/git_commit_gate.py"
        guarded = (
            "python3 -X utf8 -c \"import os,runpy,sys;p=sys.argv[1];"
            "runpy.run_path(p,run_name='__main__') if os.path.isfile(p) else None\" "
            f'\"{missing_guarded}\"'
        )
        write_json(
            home / ".codex/hooks.json",
            {
                "hooks": {
                    "PreToolUse": [
                        {
                            "hooks": [
                                {"type": "command", "command": f'python3 "{missing_old}"'},
                                {"type": "command", "command": guarded},
                            ]
                        }
                    ]
                }
            },
        )
        result, body = verify(home, "codex-home")
        assert result.returncode != 0, body
        assert any(str(missing_old) in message for message in body["blocks"]), body
        assert any(str(missing_guarded) in message for message in body["risks"]), body
        assert not any(str(missing_guarded) in message for message in body["blocks"]), body


def test_incomplete_codex_clone_install_is_repaired() -> None:
    bun = shutil.which("bun")
    assert bun, "bun is required for the Codex installer regression"
    with tempfile.TemporaryDirectory(prefix="gp-client-codex-") as raw:
        base = Path(raw)
        home = base / "home"
        project = base / "project"
        project.mkdir()
        env = environment(home)
        command = [
            bun,
            str(ROOT / "codex/install.mjs"),
            "--project",
            str(project),
            "--plugin",
            str(ROOT),
        ]
        first = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=120,
        )
        assert first.returncode == 0, first.stderr
        manifest_path = home / ".codex/graph-powers-installed.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["complete"] = False
        write_json(manifest_path, manifest)

        second = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=120,
        )
        assert second.returncode == 0, second.stderr
        repaired = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert repaired["complete"] is True, repaired
        assert "skipped" not in second.stdout.lower(), second.stdout

        result, body = verify(home, "codex", "--codex-route", "clone")
        assert result.returncode == 0, body
        assert body["route"] == "clone", body


def test_installer_refuses_stale_cursor_before_unrestricted() -> None:
    bun = shutil.which("bun")
    assert bun, "bun is required for the installer ordering regression"
    with tempfile.TemporaryDirectory(prefix="gp-installer-cursor-") as raw:
        base = Path(raw)
        home = base / "home"
        project = base / "project"
        project.mkdir()
        package = copy_package(
            home / ".cursor/plugins/cache/graph-powers/graph-powers/stale"
        )
        old_direct_commands(package, cursor=True)
        result = subprocess.run(
            [
                bun,
                str(INSTALLER),
                "--target",
                "cursor",
                "--skip-marketplace",
                "--autonomy",
                "autonomous",
            ],
            cwd=project,
            env=environment(home),
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=120,
        )
        assert result.returncode != 0, result.stdout
        assert not (home / ".cursor/permissions.json").exists(), result.stdout
        assert "fail-open" in f"{result.stdout}{result.stderr}", (result.stdout, result.stderr)


def test_installer_refuses_stale_grok_clone_before_always_approve() -> None:
    bun = shutil.which("bun")
    assert bun, "bun is required for the installer ordering regression"
    with tempfile.TemporaryDirectory(prefix="gp-installer-grok-") as raw:
        base = Path(raw)
        home = base / "home"
        project = base / "project"
        project.mkdir()
        clone = base / "graph-powers"
        shutil.copytree(
            ROOT,
            clone,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
        )
        old_direct_commands(clone)
        result = subprocess.run(
            [
                bun,
                str(clone / "bin/graph-powers.mjs"),
                "--target",
                "grok",
                "--skip-marketplace",
                "--autonomy",
                "autonomous",
            ],
            cwd=project,
            env=environment(home),
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=120,
        )
        assert result.returncode != 0, result.stdout
        assert not (home / ".grok/config.toml").exists(), result.stdout
        assert "fail-open" in f"{result.stdout}{result.stderr}", (result.stdout, result.stderr)


def test_standalone_cursor_installer_requires_verified_cache() -> None:
    bun = shutil.which("bun")
    assert bun, "bun is required for the standalone installer regression"
    with tempfile.TemporaryDirectory(prefix="gp-standalone-cursor-") as raw:
        base = Path(raw)
        home = base / "home"
        project = base / "project"
        project.mkdir()
        result = subprocess.run(
            [bun, str(ROOT / "cursor/install.mjs"), "--plugin", str(ROOT)],
            cwd=project,
            env=environment(home),
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=120,
        )
        assert result.returncode != 0, result.stdout
        assert not (home / ".cursor/permissions.json").exists(), result.stdout
        assert "verification failed" in result.stderr, result.stderr


def test_standalone_grok_installer_rejects_stale_clone() -> None:
    bun = shutil.which("bun")
    assert bun, "bun is required for the standalone installer regression"
    with tempfile.TemporaryDirectory(prefix="gp-standalone-grok-") as raw:
        base = Path(raw)
        home = base / "home"
        project = base / "project"
        project.mkdir()
        clone = copy_package(base / "stale-grok")
        shutil.copytree(ROOT / "bin", clone / "bin")
        shutil.copytree(ROOT / "codex", clone / "codex")
        shutil.copytree(ROOT / "grok", clone / "grok")
        old_direct_commands(clone)
        result = subprocess.run(
            [bun, str(clone / "grok/install.mjs"), "--plugin", str(clone)],
            cwd=project,
            env=environment(home),
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=120,
        )
        assert result.returncode != 0, result.stdout
        assert not (home / ".grok/config.toml").exists(), result.stdout
        assert "fail-open" in result.stderr, result.stderr


def test_auto_update_worker_never_replaces_grok_cache() -> None:
    module_path = ROOT / "hooks/auto_update.py"
    spec = importlib.util.spec_from_file_location("graph_powers_auto_update_test", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    calls: list[list[str]] = []
    states: list[dict[str, Any]] = []
    update = cast(Any, module)
    def record_state(patch: dict[str, Any]) -> None:
        states.append(patch)

    update.run = lambda command, timeout=180: (calls.append(command) or (0, ""))
    update.which = lambda _binary: True
    update.registered_version = lambda: ""
    update.write_state = record_state
    previous = {
        key: os.environ.get(key)
        for key in (
            "GRAPH_POWERS_UPDATE_CLAUDE",
            "GRAPH_POWERS_UPDATE_CODEX",
            "GRAPH_POWERS_UPDATE_GROK",
        )
    }
    try:
        os.environ["GRAPH_POWERS_UPDATE_CLAUDE"] = "0"
        os.environ["GRAPH_POWERS_UPDATE_CODEX"] = "0"
        os.environ["GRAPH_POWERS_UPDATE_GROK"] = "1"
        assert module.worker() == 0
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    assert not any(command and command[0] == "grok" for command in calls), calls
    assert "grok" not in module.settings({}), module.settings({})


def fake_claude(bin_dir: Path) -> None:
    bin_dir.mkdir(parents=True, exist_ok=True)
    script = bin_dir / "fake_claude.py"
    script.write_text(
        "import sys\nprint('2.0.0' if '--version' in sys.argv else '')\n",
        encoding="utf-8",
    )
    if os.name == "nt":
        (bin_dir / "claude.cmd").write_text(
            f'@echo off\r\n"{sys.executable}" "{script}" %*\r\n', encoding="utf-8"
        )
    else:
        launcher = bin_dir / "claude"
        launcher.write_text(
            f"#!{sys.executable}\nimport runpy\nrunpy.run_path({str(script)!r}, run_name='__main__')\n",
            encoding="utf-8",
        )
        launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR)


def test_installer_refuses_stale_claude_before_bypass() -> None:
    bun = shutil.which("bun")
    assert bun, "bun is required for the installer ordering regression"
    with tempfile.TemporaryDirectory(prefix="gp-installer-claude-") as raw:
        base = Path(raw)
        home = base / "home"
        project = base / "project"
        project.mkdir()
        package = copy_package(base / "stale-package")
        old_direct_commands(package)
        version = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))["version"]
        write_json(
            home / ".claude/plugins/installed_plugins.json",
            {
                "plugins": {
                    "graph-powers@graph-powers": [
                        {
                            "scope": "user",
                            "installPath": str(package),
                            "version": version,
                        }
                    ]
                }
            },
        )
        write_json(
            home / ".claude/settings.json",
            {"enabledPlugins": {"graph-powers@graph-powers": True}},
        )
        fake_bin = base / "bin"
        fake_claude(fake_bin)
        env = environment(home)
        env["PATH"] = str(fake_bin) + os.pathsep + env.get("PATH", "")
        result = subprocess.run(
            [
                bun,
                str(INSTALLER),
                "--target",
                "claude",
                "--skip-marketplace",
                "--autonomy",
                "autonomous",
            ],
            cwd=project,
            env=env,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=120,
        )
        assert result.returncode != 0, result.stdout
        settings = json.loads((home / ".claude/settings.json").read_text(encoding="utf-8"))
        assert settings == {"enabledPlugins": {"graph-powers@graph-powers": True}}, settings
        assert "fail-open" in f"{result.stdout}{result.stderr}", (result.stdout, result.stderr)


def main() -> int:
    tests = [
        test_claude_uses_the_exact_scoped_install,
        test_cursor_rejects_corrupt_and_ambiguous_cache_entries,
        test_grok_inventory_and_posture_use_grok_home,
        test_codex_home_distinguishes_blocked_from_inert_missing_paths,
        test_incomplete_codex_clone_install_is_repaired,
        test_installer_refuses_stale_cursor_before_unrestricted,
        test_installer_refuses_stale_grok_clone_before_always_approve,
        test_standalone_cursor_installer_requires_verified_cache,
        test_standalone_grok_installer_rejects_stale_clone,
        test_auto_update_worker_never_replaces_grok_cache,
        test_installer_refuses_stale_claude_before_bypass,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"hook client verifier: {len(tests)} regressions held")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
