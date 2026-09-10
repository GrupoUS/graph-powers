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


def recording_installer_bin(bin_dir: Path, record: Path) -> None:
    bin_dir.mkdir(parents=True, exist_ok=True)
    script = bin_dir / "recording_cli.py"
    script.write_text(
        """import os
import sys
from pathlib import Path

command = os.environ[\"GP_RECORDING_COMMAND\"]
record = Path(os.environ[\"GP_INSTALLER_RECORD\"])
with record.open(\"a\", encoding=\"utf-8\") as handle:
    handle.write(command + \" \" + \" \".join(sys.argv[1:]) + \"\\n\")

args = sys.argv[1:]
if command == \"git\":
    if args[-2:] == [\"rev-parse\", \"--git-dir\"]:
        print(\".git\")
    elif args[-2:] == [\"rev-parse\", \"HEAD\"]:
        print(\"after-update\" if Path(os.environ[\"GP_GIT_UPDATED\"]).exists() else \"before-update\")
    elif args[-2:] == [\"status\", \"--porcelain\"]:
        print(os.environ.get(\"GP_GIT_STATUS\", \"\"))
    elif args[-2:] == [\"pull\", \"--ff-only\"]:
        Path(os.environ[\"GP_GIT_UPDATED\"]).touch()
else:
    if args == [\"--version\"]:
        print(f\"{command} 1.0.0\")
""",
        encoding="utf-8",
    )
    for name in ("git", "claude", "codex", "cursor", "cursor-agent", "grok"):
        launcher = bin_dir / name
        launcher.write_text(
            f"#!{sys.executable}\nimport os, runpy\nos.environ['GP_RECORDING_COMMAND'] = {name!r}\nrunpy.run_path({str(script)!r}, run_name='__main__')\n",
            encoding="utf-8",
        )
        launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR)


def installer_fixture(base: Path) -> tuple[Path, Path, Path, dict[str, str]]:
    source = base / "source"
    project = base / "project"
    home = base / "home"
    record = base / "calls.txt"
    copy_package(source)
    for name in (
        "agents",
        "bin",
        "codex",
        "commands",
        "cursor",
        "grok",
        "references",
        "skills",
        "templates",
    ):
        shutil.copytree(ROOT / name, source / name, dirs_exist_ok=True)
    project.mkdir()
    bin_dir = base / "bin"
    recording_installer_bin(bin_dir, record)
    env = environment(home)
    env.update(
        {
            "PATH": str(bin_dir) + os.pathsep + env.get("PATH", ""),
            # Runtime transpilation must not look like an installer HOME write.
            "BUN_RUNTIME_TRANSPILER_CACHE_PATH": str(base / "bun-transpiler-cache"),
            "GP_INSTALLER_RECORD": str(record),
            "GP_GIT_UPDATED": str(base / "git-updated"),
        }
    )
    return source, project, record, env


def run_installer(
    source: Path, project: Path, env: dict[str, str], *args: str
) -> subprocess.CompletedProcess[str]:
    bun = shutil.which("bun")
    assert bun, "bun is required for the installer regression"
    return subprocess.run(
        [bun, str(source / "bin/graph-powers.mjs"), *args],
        cwd=project,
        env=env,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=120,
    )


def recorded_calls(record: Path) -> list[str]:
    return record.read_text(encoding="utf-8").splitlines() if record.exists() else []


def run_codex_install(
    project: Path, home: Path, scope: str, codex_home: Path | None = None
) -> subprocess.CompletedProcess[str]:
    bun = shutil.which("bun")
    assert bun, "bun is required for the Codex installer regression"
    env = environment(home)
    if codex_home:
        env["CODEX_HOME"] = str(codex_home)
    return subprocess.run(
        [
            bun,
            str(ROOT / "codex/install.mjs"),
            "--project",
            str(project),
            "--plugin",
            str(ROOT),
            "--scope",
            scope,
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=120,
    )


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


def test_grok_runtime_proof_requires_active_exact_plugin_hooks() -> None:
    with tempfile.TemporaryDirectory(prefix="gp-client-grok-runtime-") as raw:
        base = Path(raw)
        home = base / "home"
        package = copy_package(base / "grok-package")
        version = json.loads((package / ".grok-plugin/plugin.json").read_text(encoding="utf-8"))["version"]
        inventory = base / "grok-plugins.json"
        inspect = base / "grok-inspect.json"
        write_json(
            inventory,
            [{"status": "installed", "name": "graph-powers", "version": version, "path": str(package)}],
        )
        active_inspect = {
                "externalCompat": {
                    "cells": [{"vendor": "claude", "surface": "hooks", "enabled": True}]
                },
                "plugins": [
                    {
                        "name": "graph-powers",
                        "path": str(package),
                        "enabled": True,
                        "provides": {"hooks": True},
                    }
                ],
                "hooks": [
                    {
                        "event": "(plugin)",
                        "hookType": "file",
                        "target": str(package / "hooks/hooks.json"),
                        "source": {
                            "type": "plugin",
                            "plugin_name": "graph-powers",
                            "path": str(package),
                        },
                    }
                ],
            }
        write_json(inspect, active_inspect)

        result, body = verify(
            home,
            "grok",
            "--inventory-file",
            str(inventory),
            "--require-grok-runtime",
            "--grok-inspect-file",
            str(inspect),
        )
        assert result.returncode == 0, body
        assert body["runtime"]["active"] is True, body

        write_json(
            inspect,
            {
                "externalCompat": {
                    "cells": [{"vendor": "claude", "surface": "hooks", "enabled": True}]
                },
                "plugins": [],
                "hooks": [],
            },
        )
        result, body = verify(
            home,
            "grok",
            "--inventory-file",
            str(inventory),
            "--require-grok-runtime",
            "--grok-inspect-file",
            str(inspect),
        )
        assert result.returncode != 0, body
        assert any("not active" in message for message in body["errors"]), body

        project = base / "project"
        project.mkdir()
        bin_dir = base / "bin"
        cwd_record = base / "inspect-cwd.txt"
        bin_dir.mkdir()
        grok = bin_dir / "grok"
        grok.write_text(
            "#!" + sys.executable + "\n"
            "import os, sys\n"
            f"open({str(cwd_record)!r}, 'w', encoding='utf-8').write(os.getcwd())\n"
            f"print(open({str(inspect)!r}, encoding='utf-8').read())\n",
            encoding="utf-8",
        )
        grok.chmod(grok.stat().st_mode | stat.S_IXUSR)
        write_json(inspect, active_inspect)
        result, body = verify(
            home,
            "grok",
            "--inventory-file",
            str(inventory),
            "--require-grok-runtime",
            "--project-dir",
            str(project),
            env_extra={"PATH": str(bin_dir) + os.pathsep + os.environ.get("PATH", "")},
        )
        assert result.returncode == 0, body
        assert cwd_record.read_text(encoding="utf-8") == str(project), body


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


def test_codex_references_follow_the_active_home() -> None:
    with tempfile.TemporaryDirectory(prefix="gp-codex-references-") as raw:
        base = Path(raw)
        home = base / "home"
        project = base / "project"
        project.mkdir()

        default = run_codex_install(project, home, "user")
        assert default.returncode == 0, default.stderr
        default_refs = home / ".codex/graph-powers"
        default_instructions = (home / ".codex/AGENTS.md").read_text(encoding="utf-8")
        assert default_refs.is_dir(), default_refs
        assert "~/.codex/graph-powers" in default_instructions, default_instructions

        custom_home = base / "Codex Home"
        custom = run_codex_install(project, home, "user", custom_home)
        assert custom.returncode == 0, custom.stderr
        custom_refs = custom_home / "graph-powers"
        custom_instructions = (custom_home / "AGENTS.md").read_text(encoding="utf-8")
        assert custom_refs.is_dir(), custom_refs
        assert str(custom_refs) in custom_instructions, custom_instructions

        project_scope = run_codex_install(project, home, "project", custom_home)
        assert project_scope.returncode == 0, project_scope.stderr
        local_refs = project / ".codex/graph-powers"
        local_instructions = (project / "AGENTS.md").read_text(encoding="utf-8")
        assert local_refs.is_dir(), local_refs
        assert ".codex/graph-powers" in local_instructions, local_instructions


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
        hooks_path = home / ".codex/hooks.json"
        hooks_before = hooks_path.read_bytes()
        hooks_mtime = hooks_path.stat().st_mtime_ns
        intact = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=120,
        )
        assert intact.returncode == 0, intact.stderr
        assert "skipped" in intact.stdout.lower(), intact.stdout
        assert hooks_path.read_bytes() == hooks_before
        assert hooks_path.stat().st_mtime_ns == hooks_mtime

        role = home / ".codex/agents/debugger.toml"
        role.unlink()
        role_repair = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=120,
        )
        assert role_repair.returncode == 0, role_repair.stderr
        assert "skipped" not in role_repair.stdout.lower(), role_repair.stdout
        assert role.is_file(), role

        skill = home / ".agents/skills/debugger/SKILL.md"
        skill.unlink()
        skill_repair = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=120,
        )
        assert skill_repair.returncode == 0, skill_repair.stderr
        assert "skipped" not in skill_repair.stdout.lower(), skill_repair.stdout
        assert skill.is_file(), skill

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


def test_codex_installer_preserves_adopted_rules() -> None:
    template = (ROOT / "templates/rules/design.md").read_bytes()
    sentinel = b"# Project-specific execution rule\n\nKeep this exact text.\n"
    for scope in ("user", "project"):
        with tempfile.TemporaryDirectory(prefix=f"gp-adopted-rules-{scope}-") as raw:
            base = Path(raw)
            home = base / "home"
            project = base / "project"
            rules = project / ".codex/rules"
            rules.mkdir(parents=True)
            execution = rules / "execution.md"
            execution.write_bytes(sentinel)

            first = run_codex_install(project, home, scope)
            assert first.returncode == 0, first.stderr
            assert execution.read_bytes() == sentinel
            assert (rules / "design.md").read_bytes() == template
            manifest = json.loads(
                (project / ".graph-powers/installed.json").read_text(encoding="utf-8")
            )
            assert manifest["adopted"] == [str(rules)]

            second = run_codex_install(project, home, scope)
            assert second.returncode == 0, second.stderr
            assert execution.read_bytes() == sentinel
            assert (rules / "design.md").read_bytes() == template
            manifest = json.loads(
                (project / ".graph-powers/installed.json").read_text(encoding="utf-8")
            )
            assert manifest["adopted"] == [str(rules)]

    with tempfile.TemporaryDirectory(prefix="gp-adopted-rule-links-") as raw:
        base = Path(raw)
        home = base / "home"
        project = base / "project"
        rules = project / ".codex/rules"
        dangling = base / "outside-rule.md"
        rules.mkdir(parents=True)
        execution = rules / "execution.md"
        execution.symlink_to(dangling)

        result = run_codex_install(project, home, "project")
        assert result.returncode == 0, result.stderr
        assert execution.is_symlink(), execution
        assert not dangling.exists(), dangling

    with tempfile.TemporaryDirectory(prefix="gp-adopted-rules-directory-link-") as raw:
        base = Path(raw)
        home = base / "home"
        project = base / "project"
        external = base / "outside-rules"
        external.mkdir()
        rules = project / ".codex/rules"
        rules.parent.mkdir(parents=True)
        rules.symlink_to(external, target_is_directory=True)

        result = run_codex_install(project, home, "project")
        assert result.returncode == 0, result.stderr
        assert rules.is_symlink(), rules
        assert not (external / "design.md").exists(), external


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


def test_installer_refuses_inactive_native_grok_before_trust() -> None:
    bun = shutil.which("bun")
    assert bun, "bun is required for the installer ordering regression"
    with tempfile.TemporaryDirectory(prefix="gp-installer-grok-native-") as raw:
        base = Path(raw)
        home = base / "home"
        project = base / "project"
        project.mkdir()
        calls = base / "grok-calls.txt"
        bin_dir = base / "bin"
        bin_dir.mkdir()
        version = json.loads((ROOT / ".grok-plugin/plugin.json").read_text(encoding="utf-8"))["version"]
        inventory = [{"status": "installed", "name": "graph-powers", "version": version, "path": str(ROOT)}]
        inspect = {
            "externalCompat": {"cells": [{"vendor": "claude", "surface": "hooks", "enabled": True}]},
            "plugins": [{"name": "graph-powers", "path": str(ROOT), "enabled": False, "provides": {"hooks": True}}],
            "hooks": [],
        }
        grok = bin_dir / "grok"
        grok.write_text(
            "#!" + sys.executable + "\n"
            "import json, os, sys\n"
            f"calls = {str(calls)!r}\n"
            "args = sys.argv[1:]\n"
            "with open(calls, 'a', encoding='utf-8') as handle: handle.write(' '.join(args) + '\\n')\n"
            "if args == ['--version']: print('grok 1.0.25')\n"
            f"elif args == ['plugin', 'list', '--json']: print({json.dumps(json.dumps(inventory))})\n"
            f"elif args == ['inspect', '--json']: print({json.dumps(json.dumps(inspect))})\n",
            encoding="utf-8",
        )
        grok.chmod(grok.stat().st_mode | stat.S_IXUSR)
        env = environment(home)
        env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
        result = subprocess.run(
            [bun, str(INSTALLER), "--target", "grok", "--autonomy", "autonomous"],
            cwd=project,
            env=env,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=120,
        )
        assert result.returncode != 0, result.stdout
        assert not (home / ".grok/config.toml").exists(), result.stdout
        assert "plugin install graph-powers --trust" not in calls.read_text(encoding="utf-8"), calls.read_text(encoding="utf-8")
        assert "not active" in f"{result.stdout}{result.stderr}", (result.stdout, result.stderr)


def test_installer_only_bootstraps_after_a_valid_empty_grok_inventory() -> None:
    bun = shutil.which("bun")
    assert bun, "bun is required for the installer ordering regression"
    cases = {
        "invalid-json": "{ malformed",
        "invalid-object": "{}",
        "missing-name": "[{}]",
        "null-name": '[{"name": null}]',
        "empty-name": '[{"name": " "}]',
        "disabled": json.dumps([{"name": "graph-powers", "status": "disabled"}]),
        "error": json.dumps([{"name": "graph-powers", "status": "error"}]),
        "missing-status": json.dumps([{"name": "graph-powers"}]),
    }

    def empty_inventory_grok(bin_dir: Path, calls: Path, *, fail_add: bool = False) -> None:
        bin_dir.mkdir()
        grok = bin_dir / "grok"
        grok.write_text(
            "#!" + sys.executable + "\n"
            "import sys\n"
            f"calls = {str(calls)!r}\n"
            "args = sys.argv[1:]\n"
            "with open(calls, 'a', encoding='utf-8') as handle: handle.write(' '.join(args) + '\\n')\n"
            "if args == ['--version']: print('grok 1.0.25')\n"
            "elif args == ['plugin', 'list', '--json']: print('[]')\n"
            + (
                "elif args[:3] == ['plugin', 'marketplace', 'add']: raise SystemExit(9)\n"
                if fail_add
                else ""
            ),
            encoding="utf-8",
        )
        grok.chmod(grok.stat().st_mode | stat.S_IXUSR)
    with tempfile.TemporaryDirectory(prefix="gp-installer-grok-inventory-") as raw:
        base = Path(raw)
        for name, inventory_output in cases.items():
            home = base / name / "home"
            project = base / name / "project"
            project.mkdir(parents=True)
            calls = base / name / "grok-calls.txt"
            bin_dir = base / name / "bin"
            bin_dir.mkdir()
            grok = bin_dir / "grok"
            grok.write_text(
                "#!" + sys.executable + "\n"
                "import sys\n"
                f"calls = {str(calls)!r}\n"
                "args = sys.argv[1:]\n"
                "with open(calls, 'a', encoding='utf-8') as handle: handle.write(' '.join(args) + '\\n')\n"
                "if args == ['--version']: print('grok 1.0.25')\n"
                f"elif args == ['plugin', 'list', '--json']: print({inventory_output!r})\n",
                encoding="utf-8",
            )
            grok.chmod(grok.stat().st_mode | stat.S_IXUSR)
            env = environment(home)
            env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
            result = subprocess.run(
                [bun, str(INSTALLER), "--target", "grok", "--autonomy", "autonomous"],
                cwd=project,
                env=env,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=120,
            )
            recorded = calls.read_text(encoding="utf-8")
            assert result.returncode != 0, (name, result.stdout, result.stderr)
            assert "plugin marketplace add" not in recorded, (name, recorded)
            assert "plugin install graph-powers --trust" not in recorded, (name, recorded)
            assert not (home / ".grok/config.toml").exists(), (name, result.stdout)

        home = base / "empty" / "home"
        project = base / "empty" / "project"
        project.mkdir(parents=True)
        calls = base / "empty" / "grok-calls.txt"
        bin_dir = base / "empty" / "bin"
        bin_dir.mkdir()
        grok = bin_dir / "grok"
        grok.write_text(
            "#!" + sys.executable + "\n"
            "import sys\n"
            f"calls = {str(calls)!r}\n"
            "args = sys.argv[1:]\n"
            "with open(calls, 'a', encoding='utf-8') as handle: handle.write(' '.join(args) + '\\n')\n"
            "if args == ['--version']: print('grok 1.0.25')\n"
            "elif args == ['plugin', 'list', '--json']: print('[]')\n"
            "elif args == ['inspect', '--json']: print('{\"externalCompat\": {\"cells\": [{\"vendor\": \"claude\", \"surface\": \"hooks\", \"enabled\": true}]}, \"plugins\": [{\"name\": \"graph-powers\", \"path\": \"" + str(ROOT).replace("\\\\", "\\\\\\\\") + "\", \"enabled\": true, \"provides\": {\"hooks\": true}}], \"hooks\": [{\"event\": \"(plugin)\", \"hookType\": \"file\", \"target\": \"" + str(ROOT / "hooks/hooks.json").replace("\\\\", "\\\\\\\\") + "\", \"source\": {\"type\": \"plugin\", \"plugin_name\": \"graph-powers\", \"path\": \"" + str(ROOT).replace("\\\\", "\\\\\\\\") + "\"}}]}')\n",
            encoding="utf-8",
        )
        grok.chmod(grok.stat().st_mode | stat.S_IXUSR)
        env = environment(home)
        env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
        result = subprocess.run(
            [bun, str(INSTALLER), "--target", "grok", "--autonomy", "autonomous"],
            cwd=project,
            env=env,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=120,
        )
        recorded = calls.read_text(encoding="utf-8")
        assert result.returncode == 0, (result.stdout, result.stderr)
        assert "plugin marketplace add" in recorded, recorded
        assert "plugin install graph-powers --trust" in recorded, recorded

        home = base / "guarded" / "home"
        project = base / "guarded" / "project"
        project.mkdir(parents=True)
        calls = base / "guarded" / "grok-calls.txt"
        bin_dir = base / "guarded" / "bin"
        empty_inventory_grok(bin_dir, calls)
        env = environment(home)
        env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
        result = subprocess.run(
            [bun, str(INSTALLER), "--target", "grok", "--autonomy", "guarded"],
            cwd=project,
            env=env,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=120,
        )
        recorded = calls.read_text(encoding="utf-8")
        assert result.returncode == 0, (result.stdout, result.stderr)
        assert "plugin marketplace add" not in recorded, recorded
        assert "plugin install graph-powers --trust" not in recorded, recorded
        assert (home / ".grok/config.toml").is_file(), result.stdout

        home = base / "operator-disabled" / "home"
        project = base / "operator-disabled" / "project"
        project.mkdir(parents=True)
        config = home / ".grok/config.toml"
        config.parent.mkdir(parents=True)
        original = '[plugins]\ndisabled = ["graph-powers"]\n'
        config.write_text(original, encoding="utf-8")
        calls = base / "operator-disabled" / "grok-calls.txt"
        bin_dir = base / "operator-disabled" / "bin"
        empty_inventory_grok(bin_dir, calls)
        env = environment(home)
        env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
        result = subprocess.run(
            [bun, str(INSTALLER), "--target", "grok", "--autonomy", "autonomous"],
            cwd=project,
            env=env,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=120,
        )
        recorded = calls.read_text(encoding="utf-8")
        assert result.returncode != 0, (result.stdout, result.stderr)
        assert "plugin marketplace add" not in recorded, recorded
        assert "plugin install graph-powers --trust" not in recorded, recorded
        assert config.read_text(encoding="utf-8") == original, result.stdout

        home = base / "add-failure" / "home"
        project = base / "add-failure" / "project"
        project.mkdir(parents=True)
        calls = base / "add-failure" / "grok-calls.txt"
        bin_dir = base / "add-failure" / "bin"
        empty_inventory_grok(bin_dir, calls, fail_add=True)
        env = environment(home)
        env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
        result = subprocess.run(
            [bun, str(INSTALLER), "--target", "grok", "--autonomy", "autonomous"],
            cwd=project,
            env=env,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=120,
        )
        recorded = calls.read_text(encoding="utf-8")
        assert result.returncode != 0, (result.stdout, result.stderr)
        assert "plugin marketplace add" in recorded, recorded
        assert "plugin install graph-powers --trust" not in recorded, recorded


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


def test_installer_validates_operations_before_side_effects() -> None:
    with tempfile.TemporaryDirectory(prefix="gp-installer-operations-") as raw:
        base = Path(raw)
        source, project, record, env = installer_fixture(base)

        for args, expected in (
            (("--target", "codex", "--dry-run", "--unknown"), "unknown option: --unknown"),
            (("--target",), "missing value for --target"),
            (("--target", "not-a-client"), "invalid target: not-a-client"),
            (("--update", "--uninstall"), "cannot combine --update and --uninstall"),
        ):
            result = run_installer(source, project, env, *args)
            assert result.returncode != 0, (args, result.stdout, result.stderr)
            assert expected in result.stderr, (args, result.stdout, result.stderr)
            assert not recorded_calls(record), (args, recorded_calls(record))
            assert not (base / "home").exists(), args

        help_result = run_installer(source, project, env, "-h")
        assert help_result.returncode == 0, help_result.stderr
        assert "USAGE" in help_result.stdout, help_result.stdout
        prompt_result = run_installer(source, project, env, "--agent-setup")
        assert prompt_result.returncode == 0, prompt_result.stderr
        assert "Read AGENT_SETUP.md" in prompt_result.stdout, prompt_result.stdout
        assert not recorded_calls(record), recorded_calls(record)

        dry_run = run_installer(source, project, env, "--target", "codex", "--update", "--dry-run")
        assert dry_run.returncode == 0, (dry_run.stdout, dry_run.stderr)
        assert "would fast-forward this clone" in dry_run.stdout, dry_run.stdout
        assert not recorded_calls(record), recorded_calls(record)
        assert not (base / "home").exists(), dry_run.stdout

        env["GP_GIT_STATUS"] = " M modified-file"
        dirty = run_installer(source, project, env, "--target", "codex", "--update")
        assert dirty.returncode != 0, (dirty.stdout, dirty.stderr)
        assert "clone has uncommitted changes" in dirty.stderr, (dirty.stdout, dirty.stderr)
        assert not any("pull --ff-only" in call for call in recorded_calls(record)), recorded_calls(record)
        assert not (base / "home").exists(), dirty.stdout

        env["GP_GIT_STATUS"] = ""
        clean = run_installer(source, project, env, "--target", "codex", "--update")
        assert clean.returncode == 0, (clean.stdout, clean.stderr)
        assert any("pull --ff-only" in call for call in recorded_calls(record)), recorded_calls(record)
        assert "before-u → after-up" in clean.stdout, clean.stdout


def clone_fixture(base: Path) -> Path:
    source = base / "source"
    source.mkdir()
    inventory = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT, capture_output=True, check=True,
    )
    # Only the existing layout is needed: literal payload sizes below define each boundary.
    for name in set(inventory.stdout.split(b"\0")) - {b""}:
        path = source / os.fsdecode(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
    subprocess.run(["git", "init", "--quiet"], cwd=source, check=True)
    subprocess.run(["git", "add", "--all"], cwd=source, check=True)
    return source


def run_clone_check(source: Path, *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / ".github/check_clone.py")], cwd=source, env=env,
        capture_output=True, encoding="utf-8", errors="replace", check=False,
    )


def test_clone_budgets_count_untracked_candidates_and_exact_package_prefix() -> None:
    with tempfile.TemporaryDirectory(prefix="gp-clone-budgets-") as raw:
        source = clone_fixture(Path(raw))
        payload = source / "source-payload.bin"
        payload.write_bytes(b"s" * 4194304)
        package_payload = source / "hermes/package/payload.bin"
        package_payload.write_bytes(b"h" * 2097152)

        result = run_clone_check(source)
        assert result.returncode == 0, (result.stdout, result.stderr)
        assert "Source: 4194304 bytes (4096.00 KiB) / 4194304 bytes" in result.stdout, result.stdout
        assert "Hermes package: 2097152 bytes (2048.00 KiB) / 2097152 bytes" in result.stdout, result.stdout
        assert "Total: 6291456 bytes (6144.00 KiB) / 6291456 bytes" in result.stdout, result.stdout

        # A similarly named sibling belongs to source, never to the Hermes allocation.
        package_payload.write_bytes(b"")
        sibling = source / "hermes/package-extra.bin"
        sibling.write_bytes(b"s")
        result = run_clone_check(source)
        assert result.returncode != 0, result.stdout
        assert "source grew past 4 MiB" in result.stdout, result.stdout
        sibling.unlink()

        # Exceeding Hermes must fail even when the complete tree is below 4 MiB.
        payload.write_bytes(b"")
        package_payload.write_bytes(b"h" * 2097153)
        result = run_clone_check(source)
        assert result.returncode != 0, result.stdout
        assert "Hermes package grew past 2 MiB" in result.stdout, result.stdout


def test_clone_counts_tracked_ignored_files_and_rejects_compiled_python() -> None:
    with tempfile.TemporaryDirectory(prefix="gp-clone-ignored-") as raw:
        source = clone_fixture(Path(raw))
        (source / ".gitignore").write_bytes(b"*.bin\n*.pyc\n")
        (source / "local.bin").write_bytes(b"l" * 4194305)
        result = run_clone_check(source)
        assert result.returncode == 0, (result.stdout, result.stderr)
        assert "Source: 12 bytes" in result.stdout, result.stdout

        subprocess.run(["git", "add", "--force", "local.bin"], cwd=source, check=True)
        result = run_clone_check(source)
        assert result.returncode != 0, result.stdout
        assert "source grew past 4 MiB" in result.stdout, result.stdout

        (source / "local.bin").write_bytes(b"")
        (source / "compiled.pyc").write_bytes(b"bytecode")
        subprocess.run(["git", "add", "--force", "compiled.pyc"], cwd=source, check=True)
        result = run_clone_check(source)
        assert result.returncode != 0, result.stdout
        assert "JUNK: compiled.pyc" in result.stdout, result.stdout


def test_clone_rejects_failed_or_unavailable_git_inventory() -> None:
    with tempfile.TemporaryDirectory(prefix="gp-clone-inventory-") as raw:
        source = clone_fixture(Path(raw))
        (source / ".git").rename(source.parent / "git-metadata")
        result = run_clone_check(source)
        assert result.returncode != 0, (result.stdout, result.stderr)
        assert "cannot enumerate clone candidates" in result.stdout, result.stdout

        result = run_clone_check(source, env={**os.environ, "PATH": ""})
        assert result.returncode != 0, (result.stdout, result.stderr)
        assert "cannot enumerate clone candidates" in result.stdout, result.stdout


def test_clone_rejects_missing_required_file() -> None:
    with tempfile.TemporaryDirectory(prefix="gp-clone-missing-") as raw:
        source = clone_fixture(Path(raw))
        (source / "README.md").unlink()
        result = run_clone_check(source)
        assert result.returncode != 0, (result.stdout, result.stderr)
        assert "MISSING: README.md" in result.stdout, result.stdout


def main() -> int:
    tests = [
        test_claude_uses_the_exact_scoped_install,
        test_cursor_rejects_corrupt_and_ambiguous_cache_entries,
        test_grok_inventory_and_posture_use_grok_home,
        test_grok_runtime_proof_requires_active_exact_plugin_hooks,
        test_codex_home_distinguishes_blocked_from_inert_missing_paths,
        test_codex_references_follow_the_active_home,
        test_incomplete_codex_clone_install_is_repaired,
        test_codex_installer_preserves_adopted_rules,
        test_installer_refuses_stale_cursor_before_unrestricted,
        test_installer_refuses_stale_grok_clone_before_always_approve,
        test_installer_refuses_inactive_native_grok_before_trust,
        test_installer_only_bootstraps_after_a_valid_empty_grok_inventory,
        test_standalone_cursor_installer_requires_verified_cache,
        test_standalone_grok_installer_rejects_stale_clone,
        test_auto_update_worker_never_replaces_grok_cache,
        test_installer_refuses_stale_claude_before_bypass,
        test_installer_validates_operations_before_side_effects,
        test_clone_budgets_count_untracked_candidates_and_exact_package_prefix,
        test_clone_counts_tracked_ignored_files_and_rejects_compiled_python,
        test_clone_rejects_failed_or_unavailable_git_inventory,
        test_clone_rejects_missing_required_file,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"hook client verifier: {len(tests)} regressions held")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
