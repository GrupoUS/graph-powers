#!/usr/bin/env python3
"""Verify the exact Graph Powers hook package each supported client will execute.

This is the shared precondition for permissive client posture. It reads client-owned registries,
then validates the package at the exact recorded path against the canonical hook declaration inside
that package. It never installs, updates, deletes, enables, trusts, or rewrites anything.

Exit 0 means every requested, present client has an executable fail-open package. Exit 1 means a
client must not be switched to bypass/unrestricted/always-approve. ``--json`` keeps the contract
stable for the JavaScript installer and CI.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import tempfile
from collections.abc import Iterable
from pathlib import Path
from typing import Any

PLUGIN = "graph-powers"
PLUGIN_ID = "graph-powers@graph-powers"
MIN_NATIVE_HOOKS = 14
MIN_CURSOR_HOOKS = 11
RUNNER_MARKERS = ("runpy.run_path", "os.path.isfile", "run_name='__main__'")
SCRIPT_RE = re.compile(r"(?:^|[\\/])hooks[\\/]([A-Za-z_][A-Za-z0-9_]*\.py)")
ABSOLUTE_SCRIPT_RE = re.compile(
    r'''(?<![\w%$])((?:[A-Za-z]:)?[\\/][^\s"';|&()]*\.(?:py|mjs|js|sh|ps1|exe|cmd|bat))'''
)
REQUIRED_PACKAGE_FILES = (
    "skills/planning/SKILL.md",
    "skills/planning/references/phase-c-executing-plans.md",
    "skills/planning/references/execution/tdd-policy.md",
)


def read_json(path: Path) -> tuple[Any | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except FileNotFoundError:
        return None, f"missing {path}"
    except (OSError, ValueError) as exc:
        return None, f"could not parse {path}: {exc}"


def resolved(path: str | os.PathLike[str]) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def base_result(client: str) -> dict[str, Any]:
    return {
        "client": client,
        "status": "FAIL",
        "ok": False,
        "present": True,
        "route": None,
        "root": None,
        "version": None,
        "hooks": {},
        "posture": {},
        "errors": [],
        "warnings": [],
    }


def fail(result: dict[str, Any], message: str) -> None:
    result["errors"].append(message)


def warn(result: dict[str, Any], message: str) -> None:
    result["warnings"].append(message)


def finish(result: dict[str, Any]) -> dict[str, Any]:
    result["ok"] = not result["errors"]
    result["status"] = "PASS" if result["ok"] else "FAIL"
    return result


def python3_proof() -> dict[str, Any]:
    proof: dict[str, Any] = {
        "ok": False,
        "command": "python3",
        "path": shutil.which("python3"),
        "version": None,
        "error": None,
    }
    if not proof["path"]:
        proof["error"] = "literal python3 is not on PATH"
        return proof
    try:
        run = subprocess.run(
            ["python3", "-X", "utf8", "-c", "import json,sys;print(json.dumps(list(sys.version_info[:3])))"],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=15,
        )
        version = json.loads(run.stdout.strip()) if run.returncode == 0 else None
        if not isinstance(version, list) or len(version) < 2:
            proof["error"] = (
                f"literal python3 did not start cleanly (exit {run.returncode}): "
                f"{(run.stderr or run.stdout).strip()}"
            )
            return proof
        proof["version"] = ".".join(str(part) for part in version)
        if tuple(version[:2]) < (3, 10):
            proof["error"] = f"literal python3 is {proof['version']}; hooks require 3.10+"
            return proof
        proof["ok"] = True
        return proof
    except Exception as exc:
        proof["error"] = f"literal python3 probe failed: {exc}"
        return proof


def flatten_native_hooks(document: Any) -> list[str]:
    if not isinstance(document, dict) or not isinstance(document.get("hooks"), dict):
        return []
    commands: list[str] = []
    for groups in document["hooks"].values():
        if not isinstance(groups, list):
            continue
        for group in groups:
            if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                continue
            for hook in group["hooks"]:
                if isinstance(hook, dict) and isinstance(hook.get("command"), str):
                    commands.append(hook["command"])
    return commands


def flatten_cursor_hooks(document: Any) -> list[str]:
    if not isinstance(document, dict) or not isinstance(document.get("hooks"), dict):
        return []
    return [
        hook["command"]
        for entries in document["hooks"].values()
        if isinstance(entries, list)
        for hook in entries
        if isinstance(hook, dict) and isinstance(hook.get("command"), str)
    ]


def package_layout(client: str) -> tuple[str, str, str | None, int]:
    if client == "claude":
        return ".claude-plugin/plugin.json", "hooks/hooks.json", None, MIN_NATIVE_HOOKS
    if client == "codex":
        return ".codex-plugin/plugin.json", "hooks/hooks.json", "./hooks/hooks.json", MIN_NATIVE_HOOKS
    if client == "cursor":
        return (
            ".cursor-plugin/plugin.json",
            "hooks/hooks-cursor.json",
            "./hooks/hooks-cursor.json",
            MIN_CURSOR_HOOKS,
        )
    if client == "grok":
        return ".grok-plugin/plugin.json", "hooks/hooks.json", "./hooks/hooks.json", MIN_NATIVE_HOOKS
    raise ValueError(f"unsupported package client: {client}")


def reference_hook_count(client: str, root: Path) -> tuple[int, str | None]:
    _manifest, hooks_rel, _declared, minimum = package_layout(client)
    document, error = read_json(root / hooks_rel)
    if error:
        return minimum, f"canonical {client} hook reference is unavailable: {error}"
    commands = flatten_cursor_hooks(document) if client == "cursor" else flatten_native_hooks(document)
    if len(commands) < minimum:
        return minimum, (
            f"canonical {client} hook reference has {len(commands)} registrations; "
            f"the historical safety floor is {minimum}"
        )
    return len(commands), None


def inspect_package(
    client: str,
    root: Path,
    *,
    declared_version: str | None = None,
    expected_version: str | None = None,
    python_proof: dict[str, Any] | None = None,
    reference_root: Path | None = None,
) -> dict[str, Any]:
    result = base_result(client)
    result["root"] = str(root)
    result["python"] = python_proof or python3_proof()
    if not result["python"]["ok"]:
        fail(result, str(result["python"]["error"]))

    if not root.is_dir():
        fail(result, f"package root does not exist: {root}")
        return finish(result)

    manifest_rel, hooks_rel, declared_hooks, _minimum_count = package_layout(client)
    expected_count, reference_error = reference_hook_count(client, reference_root or root)
    if reference_error:
        fail(result, reference_error)
    manifest_path = root / manifest_rel
    hooks_path = root / hooks_rel
    manifest, manifest_error = read_json(manifest_path)
    if manifest_error or not isinstance(manifest, dict):
        fail(result, f"corrupt {client} package: {manifest_error or 'manifest is not an object'}")
        return finish(result)

    name = manifest.get("name")
    version = manifest.get("version")
    result["version"] = str(version) if version is not None else None
    result["manifest"] = str(manifest_path)
    if name != PLUGIN:
        fail(result, f"corrupt {client} package: manifest name is {name!r}, expected {PLUGIN!r}")
    if not isinstance(version, str) or not version:
        fail(result, f"corrupt {client} package: manifest version is missing")
    if declared_hooks is not None and manifest.get("hooks") != declared_hooks:
        fail(
            result,
            f"corrupt {client} package: manifest hooks is {manifest.get('hooks')!r}, expected {declared_hooks!r}",
        )
    if declared_version and version != declared_version:
        fail(
            result,
            f"{client} registry says version {declared_version}, but its exact package manifest says {version}",
        )
    if expected_version and version != expected_version:
        fail(
            result,
            f"{client} package is {version}; this installer requires the exact source version {expected_version}",
        )

    hooks, hooks_error = read_json(hooks_path)
    if hooks_error:
        fail(result, f"corrupt {client} package: {hooks_error}")
        return finish(result)
    commands = flatten_cursor_hooks(hooks) if client == "cursor" else flatten_native_hooks(hooks)
    marker_failures = [
        index
        for index, command in enumerate(commands, 1)
        if not all(marker in command for marker in RUNNER_MARKERS)
    ]
    scripts = sorted({match for command in commands for match in SCRIPT_RE.findall(command)})
    missing_scripts = [name for name in scripts if not (root / "hooks" / name).is_file()]
    result["hooks"] = {
        "file": str(hooks_path),
        "registrations": len(commands),
        "expected": expected_count,
        "failOpen": not marker_failures and len(commands) == expected_count,
        "scripts": scripts,
        "missingScripts": missing_scripts,
    }
    if len(commands) != expected_count:
        fail(
            result,
            f"{client} package registration set is stale or incomplete: "
            f"expected {expected_count}, found {len(commands)}",
        )
    if marker_failures:
        fail(
            result,
            f"{client} package does not contain {expected_count} fail-open runners; "
            f"registrations without the guarded runpy runner: {marker_failures}",
        )
    if missing_scripts:
        fail(
            result,
            f"corrupt {client} package: hook targets are missing: {', '.join(missing_scripts)}",
        )
    missing_package_files = [relative for relative in REQUIRED_PACKAGE_FILES if not (root / relative).is_file()]
    result["requiredFiles"] = {
        "checked": list(REQUIRED_PACKAGE_FILES),
        "missing": missing_package_files,
    }
    if missing_package_files:
        fail(
            result,
            f"incomplete {client} package: required method files are missing: "
            f"{', '.join(missing_package_files)}",
        )
    return finish(result)



def effective_policy(plugin_root: Path, project_dir: Path) -> dict[str, Any]:
    fallback = {
        "config": None,
        "level": "guarded",
        "bashDefault": "ask",
        "cleanup": "ask",
        "toolDefault": "ask",
        "error": None,
    }
    try:
        module_path = plugin_root / "hooks/_config.py"
        spec = importlib.util.spec_from_file_location("graph_powers_verify_config", module_path)
        if spec is None or spec.loader is None:
            fallback["error"] = f"could not import {module_path}"
            return fallback
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        policy = module.autonomy(module.load(root=project_dir))
        config = module.config_path(project_dir)
        return {
            "config": str(config) if config else None,
            "level": policy.get("level", "guarded"),
            "bashDefault": policy.get("bashDefault", "ask"),
            "cleanup": policy.get("cleanup", "ask"),
            "toolDefault": policy.get("toolDefault", "ask"),
            "error": None,
        }
    except Exception as exc:
        fallback["error"] = str(exc)
        return fallback


def posture_level(args: argparse.Namespace) -> str:
    if args.autonomy != "auto":
        return args.autonomy
    return effective_policy(args.plugin_root, args.project_dir)["level"]


def claude_root() -> Path:
    configured = os.environ.get("CLAUDE_CONFIG_DIR")
    return resolved(configured) if configured else resolved(Path.home() / ".claude")


def codex_root() -> Path:
    configured = os.environ.get("CODEX_HOME")
    return resolved(configured) if configured else resolved(Path.home() / ".codex")


def grok_root() -> Path:
    configured = os.environ.get("GROK_HOME")
    return resolved(configured) if configured else resolved(Path.home() / ".grok")


def scope_matches(entry: dict[str, Any], scope: str, project_dir: Path) -> bool:
    if entry.get("scope") != scope:
        return False
    if scope == "user":
        return True
    project_path = entry.get("projectPath")
    return isinstance(project_path, str) and resolved(project_path) == project_dir


def claude_settings_path(scope: str, project_dir: Path) -> Path:
    if scope == "user":
        return claude_root() / "settings.json"
    filename = "settings.local.json" if scope == "local" else "settings.json"
    return project_dir / ".claude" / filename


def verify_claude(args: argparse.Namespace, python_proof: dict[str, Any]) -> dict[str, Any]:
    result = base_result("claude")
    result["route"] = "native"
    registry_path = claude_root() / "plugins/installed_plugins.json"
    registry, registry_error = read_json(registry_path)
    if registry_error or not isinstance(registry, dict):
        result["present"] = False
        fail(result, f"Claude Code Graph Powers registry is unavailable: {registry_error}")
        return finish(result)

    raw_entries = (registry.get("plugins") or {}).get(PLUGIN_ID, [])
    entries = [
        entry
        for entry in raw_entries
        if isinstance(entry, dict) and scope_matches(entry, args.scope, args.project_dir)
    ]
    if not entries:
        result["present"] = False
        fail(
            result,
            f"Claude Code has no exact {args.scope}-scope {PLUGIN_ID} install for {args.project_dir}",
        )
        return finish(result)
    roots = {
        str(resolved(entry["installPath"]))
        for entry in entries
        if isinstance(entry.get("installPath"), str) and entry["installPath"]
    }
    if len(roots) != 1:
        fail(result, f"Claude Code install is ambiguous: {len(roots)} scoped package paths in {registry_path}")
        result["candidates"] = sorted(roots)
        return finish(result)
    root = resolved(next(iter(roots)))
    versions = {str(entry.get("version")) for entry in entries if entry.get("version") is not None}
    if len(versions) > 1:
        fail(result, f"Claude Code registry has conflicting scoped versions: {sorted(versions)}")
        return finish(result)
    declared = next(iter(versions), None)
    package = inspect_package(
        "claude",
        root,
        declared_version=declared,
        expected_version=args.expected_version,
        python_proof=python_proof,
        reference_root=args.plugin_root,
    )
    package["route"] = "native"
    package["registry"] = str(registry_path)
    package["scope"] = args.scope
    settings = claude_settings_path(args.scope, args.project_dir)
    document, _ = read_json(settings)
    enabled_plugins = document.get("enabledPlugins", {}) if isinstance(document, dict) else {}
    enabled = enabled_plugins.get(PLUGIN_ID) if isinstance(enabled_plugins, dict) else None
    if enabled is None and args.scope != "user":
        user_document, _ = read_json(claude_settings_path("user", args.project_dir))
        user_plugins = user_document.get("enabledPlugins", {}) if isinstance(user_document, dict) else {}
        enabled = user_plugins.get(PLUGIN_ID) if isinstance(user_plugins, dict) else None
    package["enabled"] = enabled is True
    package["settings"] = str(settings)
    if enabled is not True:
        fail(package, f"Claude Code plugin {PLUGIN_ID} is installed but not enabled in effective settings")
    if args.check_posture:
        permissions = document.get("permissions", {}) if isinstance(document, dict) else {}
        mode = permissions.get("defaultMode") if isinstance(permissions, dict) else None
        skip = document.get("skipAutoPermissionPrompt") if isinstance(document, dict) else None
        package["posture"] = {"settings": str(settings), "defaultMode": mode, "skipPrompt": skip}
        if posture_level(args) == "autonomous" and (mode != "bypassPermissions" or skip is not True):
            fail(package, "Claude autonomous posture requires bypassPermissions and skipAutoPermissionPrompt=true")
    if args.probe_guardrail:
        probe_guardrail(package, root)
    return finish(package)


def semver_key(value: str) -> tuple[tuple[int, ...], int, str] | None:
    match = re.fullmatch(r"(\d+(?:\.\d+)*)(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?", value)
    if not match:
        return None
    numbers = tuple(int(part) for part in match.group(1).split("."))
    padded = numbers + (0,) * (8 - min(len(numbers), 8))
    prerelease = match.group(2)
    return padded[:8], 1 if prerelease is None else 0, prerelease or ""


def verify_cursor(args: argparse.Namespace, python_proof: dict[str, Any]) -> dict[str, Any]:
    result = base_result("cursor")
    result["route"] = "marketplace-cache"
    cache = resolved(Path.home() / ".cursor/plugins/cache/graph-powers/graph-powers")
    if args.package_root:
        package = inspect_package(
            "cursor",
            args.package_root,
            expected_version=args.expected_version,
            python_proof=python_proof,
            reference_root=args.plugin_root,
        )
        package["route"] = "explicit-package"
        selected = package
    else:
        if not cache.is_dir():
            result["present"] = False
            fail(result, f"Cursor Graph Powers plugin cache is missing: {cache}")
            return finish(result)
        directories = sorted((entry for entry in cache.iterdir() if entry.is_dir()), key=lambda path: path.name)
        if not directories:
            result["present"] = False
            fail(result, f"Cursor Graph Powers plugin cache is empty: {cache}")
            return finish(result)
        candidates = [
            inspect_package(
                "cursor",
                path.resolve(),
                python_proof=python_proof,
                reference_root=args.plugin_root,
            )
            for path in directories
        ]
        result["candidates"] = [
            {
                "root": candidate["root"],
                "version": candidate["version"],
                "ok": candidate["ok"],
                "errors": candidate["errors"],
            }
            for candidate in candidates
        ]
        broken = [candidate for candidate in candidates if not candidate["ok"]]
        if broken:
            fail(
                result,
                "Cursor cache contains a corrupt candidate; refusing to mask it with another cached version",
            )
            for candidate in broken:
                for message in candidate["errors"]:
                    fail(result, f"{candidate['root']}: {message}")
            return finish(result)
        keyed: list[tuple[tuple[tuple[int, ...], int, str], dict[str, Any]]] = []
        for candidate in candidates:
            key = semver_key(str(candidate["version"] or ""))
            if key is None:
                fail(result, f"Cursor candidate has an unorderable version: {candidate['version']!r}")
            else:
                keyed.append((key, candidate))
        if result["errors"]:
            return finish(result)
        highest = max(key for key, _ in keyed)
        winners = [candidate for key, candidate in keyed if key == highest]
        if len(winners) != 1:
            fail(
                result,
                f"Cursor cache is ambiguous: {len(winners)} valid candidates claim the highest version",
            )
            result["candidates"] = [candidate["root"] for candidate in winners]
            return finish(result)
        selected = winners[0]
        selected["route"] = "marketplace-cache"
        selected["candidates"] = result["candidates"]
        if len(candidates) > 1:
            warn(selected, f"Cursor retained {len(candidates) - 1} older valid cache candidate(s)")
        if args.expected_version and selected["version"] != args.expected_version:
            fail(
                selected,
                f"Cursor package is {selected['version']}; this installer requires {args.expected_version}",
            )

    if args.check_posture:
        cursor_home = resolved(Path.home() / ".cursor")
        permissions_path = cursor_home / "permissions.json"
        cli_path = cursor_home / "cli-config.json"
        permissions, _ = read_json(permissions_path)
        cli, _ = read_json(cli_path)
        ide_mode = permissions.get("approvalMode") if isinstance(permissions, dict) else None
        cli_mode = cli.get("approvalMode") if isinstance(cli, dict) else None
        selected["posture"] = {
            "permissions": str(permissions_path),
            "ideApprovalMode": ide_mode,
            "cliConfig": str(cli_path),
            "cliApprovalMode": cli_mode,
        }
        if posture_level(args) == "autonomous" and (
            ide_mode != "unrestricted" or cli_mode != "unrestricted"
        ):
            fail(selected, "Cursor autonomous posture requires unrestricted IDE and cursor-agent modes")
    if args.probe_guardrail and selected.get("root"):
        probe_guardrail(selected, resolved(selected["root"]))
    return finish(selected)


def run_inventory(command: list[str]) -> tuple[Any | None, str | None]:
    if not shutil.which(command[0]):
        return None, f"{command[0]} is not on PATH"
    try:
        run = subprocess.run(
            command,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=30,
        )
    except Exception as exc:
        return None, f"{' '.join(command)} failed: {exc}"
    if run.returncode != 0:
        return None, f"{' '.join(command)} exited {run.returncode}: {(run.stderr or run.stdout).strip()}"
    try:
        return json.loads(run.stdout), None
    except ValueError as exc:
        return None, f"{' '.join(command)} returned invalid JSON: {exc}"


def inventory(args: argparse.Namespace, command: list[str]) -> tuple[Any | None, str | None]:
    if args.inventory_file:
        return read_json(args.inventory_file)
    return run_inventory(command)


def native_codex_entry(document: Any) -> dict[str, Any] | None:
    entries = document.get("installed", []) if isinstance(document, dict) else []
    matches = [
        entry
        for entry in entries
        if isinstance(entry, dict)
        and entry.get("pluginId") == PLUGIN_ID
        and entry.get("installed") is True
        and entry.get("enabled") is True
    ]
    return matches[0] if len(matches) == 1 else None


def clone_codex_present() -> bool:
    return (codex_root() / "graph-powers-installed.json").exists()


def verify_codex_clone(args: argparse.Namespace, python_proof: dict[str, Any]) -> dict[str, Any]:
    result = base_result("codex")
    result["route"] = "clone"
    manifest_path = codex_root() / "graph-powers-installed.json"
    manifest, manifest_error = read_json(manifest_path)
    if manifest_error or not isinstance(manifest, dict):
        result["present"] = False
        fail(result, f"Codex clone manifest is unavailable: {manifest_error}")
        return finish(result)
    root_value = manifest.get("pluginRoot")
    if not isinstance(root_value, str) or not root_value:
        fail(result, f"Codex clone manifest has no pluginRoot: {manifest_path}")
        return finish(result)
    package = inspect_package(
        "codex",
        resolved(root_value),
        declared_version=str(manifest.get("version")) if manifest.get("version") is not None else None,
        expected_version=args.expected_version,
        python_proof=python_proof,
        reference_root=args.plugin_root,
    )
    package["route"] = "clone"
    package["installManifest"] = str(manifest_path)
    if manifest.get("complete") is not True:
        fail(package, "Codex clone install manifest is incomplete (complete is not true)")
    recorded = manifest.get("hookCommands")
    expected_count = int(package.get("hooks", {}).get("expected") or MIN_NATIVE_HOOKS)
    if not isinstance(recorded, list) or len(recorded) != expected_count:
        fail(package, f"Codex clone manifest must record {expected_count} hook commands")
        recorded = []
    elif not all(isinstance(command, str) and "runpy.run_path" in command for command in recorded):
        fail(package, "Codex clone manifest records a non-fail-open Graph Powers hook command")
    installed_hooks_path = codex_root() / "hooks.json"
    installed_hooks, installed_error = read_json(installed_hooks_path)
    installed_commands = flatten_native_hooks(installed_hooks)
    missing = [command for command in recorded if command not in installed_commands]
    package["installedHooks"] = {
        "file": str(installed_hooks_path),
        "recorded": len(recorded),
        "present": len(recorded) - len(missing),
    }
    if installed_error:
        fail(package, f"Codex installed hooks are unavailable: {installed_error}")
    elif missing:
        fail(package, f"Codex hooks.json is missing {len(missing)} command(s) recorded by its manifest")
    if args.probe_guardrail and package.get("root"):
        probe_guardrail(package, resolved(package["root"]))
    return finish(package)


def verify_codex_native(
    args: argparse.Namespace,
    python_proof: dict[str, Any],
    document: Any | None = None,
    inventory_error: str | None = None,
) -> dict[str, Any]:
    result = base_result("codex")
    result["route"] = "native"
    if document is None and inventory_error is None:
        document, inventory_error = inventory(args, ["codex", "plugin", "list", "--json"])
    if inventory_error:
        result["present"] = False
        fail(result, f"Codex native plugin inventory is unavailable: {inventory_error}")
        return finish(result)
    entries = document.get("installed", []) if isinstance(document, dict) else []
    matches = [entry for entry in entries if isinstance(entry, dict) and entry.get("pluginId") == PLUGIN_ID]
    if not matches:
        result["present"] = False
        fail(result, f"Codex native plugin {PLUGIN_ID} is not installed")
        return finish(result)
    if len(matches) != 1:
        fail(result, f"Codex native plugin inventory is ambiguous: {len(matches)} matching entries")
        return finish(result)
    entry = matches[0]
    if entry.get("installed") is not True or entry.get("enabled") is not True:
        fail(result, "Codex native plugin is present but not both installed and enabled")
        return finish(result)
    source = entry.get("source")
    root_value = source.get("path") if isinstance(source, dict) else None
    if not isinstance(root_value, str) or not root_value:
        fail(result, "Codex native plugin inventory does not expose source.path")
        return finish(result)
    package = inspect_package(
        "codex",
        resolved(root_value),
        declared_version=str(entry.get("version")) if entry.get("version") is not None else None,
        expected_version=args.expected_version,
        python_proof=python_proof,
        reference_root=args.plugin_root,
    )
    package["route"] = "native"
    package["pluginId"] = PLUGIN_ID
    if args.probe_guardrail and package.get("root"):
        probe_guardrail(package, resolved(package["root"]))
    return finish(package)


def command_entries(document: Any) -> list[tuple[str, dict[str, Any]]]:
    if not isinstance(document, dict) or not isinstance(document.get("hooks"), dict):
        return []
    return [
        (str(event), hook)
        for event, groups in document["hooks"].items()
        if isinstance(groups, list)
        for group in groups
        if isinstance(group, dict) and isinstance(group.get("hooks"), list)
        for hook in group["hooks"]
        if isinstance(hook, dict)
    ]


def audit_codex_home() -> dict[str, Any]:
    result = base_result("codex-home")
    result["route"] = "installed-hooks"
    home = codex_root()
    result["root"] = str(home)
    hooks_path = home / "hooks.json"
    document, error = read_json(hooks_path)
    if error and hooks_path.exists():
        fail(result, f"Codex hooks file does not parse: {error}")
        return finish(result)
    if error:
        result["present"] = False
        result["status"] = "PASS"
        result["ok"] = True
        warn(result, f"Codex hooks file is absent: {hooks_path}")
        return result

    entries = command_entries(document)
    blocks: list[str] = []
    risks: list[str] = []
    notes: list[str] = []
    windows_here = os.name == "nt"
    for event, hook in entries:
        posix_value = hook.get("command")
        windows_value = hook.get("commandWindows")
        posix = posix_value if isinstance(posix_value, str) else ""
        windows = windows_value if isinstance(windows_value, str) else ""
        native, other = (windows or posix, posix) if windows_here else (posix, windows)
        first = re.match(r'\s*["\']?([^\s"\']+)', native)
        if first:
            executable = first.group(1)
            if (
                executable not in {"if", "for", "while", "case", "test", "[", "{", "command", "then", "else", "do", ":"}
                and not shutil.which(executable)
                and not Path(executable).exists()
            ):
                blocks.append(f"{event}: interpreter {executable!r} is not on PATH")
        for path_text in sorted(set(ABSOLUTE_SCRIPT_RE.findall(native))):
            path = Path(path_text)
            foreign_platform = bool(re.match(r"^[A-Za-z]:[\\/]", path_text)) != windows_here
            if foreign_platform:
                blocks.append(f"{event}: active command carries the other platform's path: {path_text}")
            elif not path.exists():
                if "runpy.run_path" in native and "os.path.isfile" in native:
                    risks.append(f"{event}: fail-open target is absent; this guardrail is inert until restart: {path_text}")
                else:
                    blocks.append(f"{event}: active command points at a missing file: {path_text}")
        for path_text in sorted(set(ABSOLUTE_SCRIPT_RE.findall(other))):
            same_platform = bool(re.match(r"^[A-Za-z]:[\\/]", path_text)) == windows_here
            if same_platform:
                risks.append(f"{event}: alternate-platform command carries this platform's path: {path_text}")
        if posix and not windows and ABSOLUTE_SCRIPT_RE.search(posix):
            notes.append(f"{event}: absolute command has no commandWindows")

    config = home / "config.toml"
    try:
        text = config.read_text(encoding="utf-8", errors="replace")
    except OSError:
        text = ""
    notify = re.search(r'^notify\s*=\s*\[([^\]]*)\]', text, re.MULTILINE)
    if notify:
        quoted = re.findall(r'"((?:[^"\\]|\\.)*)"', notify.group(1))
        target = quoted[0].replace("\\\\", "\\") if quoted else ""
        if target and not shutil.which(target) and not Path(target).exists():
            risks.append(f"notify names a command absent on this machine: {target}")
    if re.search(r"^\[\[?hooks\.(?!state)[A-Za-z]", text, re.MULTILINE):
        risks.append("config.toml declares hooks as well as hooks.json; Codex loads both")

    conflict_patterns = ("*conflicted*", "*sync-conflict*", "*conflicted copy*")
    conflicts = sorted(
        {
            str(path)
            for directory in (home, claude_root())
            if directory.is_dir()
            for pattern in conflict_patterns
            for path in directory.glob(pattern)
        }
    )
    if conflicts:
        notes.append(f"{len(conflicts)} file-sync conflict copy/copies exist in Codex or Claude home")

    result["hooks"] = {"file": str(hooks_path), "registrations": len(entries)}
    result["blocks"] = blocks
    result["risks"] = risks
    result["notes"] = notes
    for message in blocks:
        fail(result, message)
    for message in risks + notes:
        warn(result, message)
    return finish(result)


def verify_codex(args: argparse.Namespace, python_proof: dict[str, Any]) -> dict[str, Any]:
    if args.package_root:
        package = inspect_package(
            "codex",
            args.package_root,
            expected_version=args.expected_version,
            python_proof=python_proof,
            reference_root=args.plugin_root,
        )
        package["route"] = "explicit-package"
        return finish(package)
    if args.codex_route == "clone":
        return verify_codex_clone(args, python_proof)
    if args.codex_route == "native":
        return verify_codex_native(args, python_proof)

    document, inventory_error = inventory(args, ["codex", "plugin", "list", "--json"])
    native = native_codex_entry(document) is not None
    clone = clone_codex_present()
    if native and clone:
        result = base_result("codex")
        result["route"] = "ambiguous"
        fail(result, "Codex native and clone Graph Powers routes coexist; both register the same hooks")
        return finish(result)
    if native:
        return verify_codex_native(args, python_proof, document, inventory_error)
    if clone:
        return verify_codex_clone(args, python_proof)
    result = base_result("codex")
    result["present"] = False
    detail = f" ({inventory_error})" if inventory_error else ""
    fail(result, f"Codex has no enabled native plugin or clone manifest{detail}")
    return finish(result)


def grok_entries(document: Any) -> list[dict[str, Any]]:
    values = document if isinstance(document, list) else document.get("installed", []) if isinstance(document, dict) else []
    return [
        entry
        for entry in values
        if isinstance(entry, dict)
        and entry.get("name") == PLUGIN
        and entry.get("status") == "installed"
    ]


def toml_table_value(text: str, table: str, key: str) -> str | None:
    current = ""
    value: str | None = None
    table_pattern = re.compile(r"^\s*\[([^\[\]]+)\]\s*(?:#.*)?$")
    key_pattern = re.compile(
        rf"^\s*{re.escape(key)}\s*=\s*(?:[\"']([^\"']*)[\"']|([^#\s]+))\s*(?:#.*)?$"
    )
    for line in text.splitlines():
        table_match = table_pattern.match(line)
        if table_match:
            current = table_match.group(1).strip()
            continue
        if current != table:
            continue
        key_match = key_pattern.match(line)
        if key_match:
            value = key_match.group(1) if key_match.group(1) is not None else key_match.group(2)
    return value


def grok_posture(result: dict[str, Any], args: argparse.Namespace) -> None:
    config = grok_root() / "config.toml"
    try:
        text = config.read_text(encoding="utf-8")
    except OSError:
        text = ""
    mode = toml_table_value(text, "ui", "permission_mode")
    result["posture"] = {"config": str(config), "permissionMode": mode}
    if str(toml_table_value(text, "compat.claude", "hooks")).lower() == "false":
        fail(result, "Grok config disables Claude-compatible hooks")
    if posture_level(args) == "autonomous" and mode != "always-approve":
        fail(result, "Grok autonomous posture requires permission_mode = always-approve")


def verify_grok(args: argparse.Namespace, python_proof: dict[str, Any]) -> dict[str, Any]:
    if args.package_root:
        package = inspect_package(
            "grok",
            args.package_root,
            expected_version=args.expected_version,
            python_proof=python_proof,
            reference_root=args.plugin_root,
        )
        package["route"] = "clone"
    else:
        document, inventory_error = inventory(args, ["grok", "plugin", "list", "--json"])
        result = base_result("grok")
        result["route"] = "native"
        if inventory_error:
            result["present"] = False
            fail(result, f"Grok plugin inventory is unavailable: {inventory_error}")
            return finish(result)
        entries = grok_entries(document)
        if not entries:
            result["present"] = False
            fail(result, "Grok Graph Powers plugin is not installed")
            return finish(result)
        if len(entries) != 1:
            fail(result, f"Grok plugin inventory is ambiguous: {len(entries)} installed entries")
            return finish(result)
        entry = entries[0]
        root_value = entry.get("path")
        if not isinstance(root_value, str) or not root_value:
            fail(result, "Grok plugin inventory does not expose the installed path")
            return finish(result)
        package = inspect_package(
            "grok",
            resolved(root_value),
            declared_version=str(entry.get("version")) if entry.get("version") is not None else None,
            expected_version=args.expected_version,
            python_proof=python_proof,
            reference_root=args.plugin_root,
        )
        package["route"] = "native"
        package["inventoryPath"] = str(resolved(root_value))
    if args.check_posture:
        grok_posture(package, args)
    if args.probe_guardrail and package.get("root"):
        probe_guardrail(package, resolved(package["root"]))
    return finish(package)


def probe_guardrail(result: dict[str, Any], root: Path) -> None:
    hook = root / "hooks/git_commit_gate.py"
    proof: dict[str, Any] = {"hook": str(hook), "decision": None, "ok": False}
    if not hook.is_file():
        fail(result, f"direct guardrail probe target is missing: {hook}")
        result["probe"] = proof
        return
    try:
        with tempfile.TemporaryDirectory(prefix="graph-powers-hook-proof-") as raw:
            project = Path(raw)
            config = project / ".graph-powers/config.json"
            config.parent.mkdir(parents=True)
            config.write_text(
                json.dumps(
                    {
                        "git": {"optInPrefix": "VERIFY"},
                        "autonomy": {"level": "guarded", "git": {"commit": "ask"}},
                    }
                ),
                encoding="utf-8",
            )
            payload = {
                "tool_name": "Bash",
                "tool_input": {"command": "git commit -m graph-powers-verification"},
                "cwd": str(project),
            }
            env = dict(os.environ)
            env["CLAUDE_PROJECT_DIR"] = str(project)
            run = subprocess.run(
                ["python3", "-X", "utf8", str(hook)],
                input=json.dumps(payload),
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                env=env,
                check=False,
                timeout=30,
            )
            body = json.loads(run.stdout) if run.stdout.strip() else {}
            specific = body.get("hookSpecificOutput", {}) if isinstance(body, dict) else {}
            decision = specific.get("permissionDecision") if isinstance(specific, dict) else None
            proof.update(
                {
                    "exitCode": run.returncode,
                    "decision": decision,
                    "stderr": run.stderr,
                    "ok": run.returncode == 0 and decision == "deny" and not run.stderr,
                }
            )
            if not proof["ok"]:
                fail(
                    result,
                    f"direct git_commit_gate probe failed: exit={run.returncode}, decision={decision!r}",
                )
    except Exception as exc:
        proof["error"] = str(exc)
        fail(result, f"direct git_commit_gate probe failed: {exc}")
    result["probe"] = proof


def client_is_in_use(client: str) -> bool:
    if client == "claude":
        return shutil.which("claude") is not None or claude_root().exists()
    if client == "codex":
        return shutil.which("codex") is not None or codex_root().exists()
    if client == "cursor":
        return shutil.which("cursor-agent") is not None or (Path.home() / ".cursor").exists()
    if client == "grok":
        return shutil.which("grok") is not None or grok_root().exists()
    return False


def verify_one(client: str, args: argparse.Namespace, proof: dict[str, Any]) -> dict[str, Any]:
    if client == "claude":
        return verify_claude(args, proof)
    if client == "codex":
        return verify_codex(args, proof)
    if client == "codex-home":
        return audit_codex_home()
    if client == "cursor":
        return verify_cursor(args, proof)
    if client == "grok":
        return verify_grok(args, proof)
    if client == "zed":
        result = base_result("zed")
        result.update(
            {
                "status": "NOT ENFORCED",
                "ok": True,
                "route": "native-agent",
                "present": True,
                "errors": [],
                "warnings": [
                    "this repository has no Zed plugin manifest, installer target, or executable hook surface"
                ],
            }
        )
        return result
    raise ValueError(client)


def human_line(result: dict[str, Any]) -> str:
    details = []
    if result.get("version"):
        details.append(f"version {result['version']}")
    registrations = result.get("hooks", {}).get("registrations")
    if registrations is not None:
        details.append(f"{registrations} hooks")
    if result.get("route"):
        details.append(str(result["route"]))
    suffix = f" — {', '.join(details)}" if details else ""
    return f"{result['client']:7} {result['status']}{suffix}"


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument(
        "--client",
        required=True,
        choices=("claude", "codex", "codex-home", "cursor", "grok", "zed", "all"),
    )
    cli.add_argument("--plugin-root", type=resolved, default=resolved(Path(__file__).parent.parent))
    cli.add_argument("--package-root", type=resolved)
    cli.add_argument("--project-dir", type=resolved, default=resolved(Path.cwd()))
    cli.add_argument("--scope", choices=("user", "project", "local"), default="user")
    cli.add_argument("--codex-route", choices=("auto", "native", "clone"), default="auto")
    cli.add_argument("--inventory-file", type=resolved)
    cli.add_argument("--expected-version")
    cli.add_argument("--check-posture", action="store_true")
    cli.add_argument("--autonomy", choices=("auto", "autonomous", "guarded"), default="auto")
    cli.add_argument("--probe-guardrail", action="store_true")
    cli.add_argument("--json", action="store_true")
    return cli


def main(argv: Iterable[str] | None = None) -> int:
    args = parser().parse_args(list(argv) if argv is not None else None)
    proof = python3_proof()
    policy = effective_policy(args.plugin_root, args.project_dir)
    if args.client == "all":
        results = []
        for client in ("claude", "codex", "cursor", "grok"):
            result = verify_one(client, args, proof)
            if not result.get("present") and not client_is_in_use(client):
                result["errors"] = []
                result["warnings"] = [f"{client} is not installed on this machine"]
                result["ok"] = True
                result["status"] = "SKIPPED"
            results.append(result)
        results.append(verify_one("zed", args, proof))
        body: dict[str, Any] = {
            "ok": all(result["ok"] for result in results),
            "python": proof,
            "policy": policy,
            "clients": results,
        }
    else:
        body = verify_one(args.client, args, proof)
        body["policy"] = policy
    if args.json:
        print(json.dumps(body, indent=2))
    else:
        rows = body["clients"] if args.client == "all" else [body]
        print(
            "policy  "
            f"{policy['level']} (bash={policy['bashDefault']}, cleanup={policy['cleanup']}, "
            f"tools={policy['toolDefault']}, config={policy['config'] or 'defaults'})"
        )
        for result in rows:
            print(human_line(result))
            if result.get("client") == "codex-home":
                for message in result.get("blocks", []):
                    print(f"  BLOCKS: {message}")
                for message in result.get("risks", []):
                    print(f"  RISK: {message}")
                for message in result.get("notes", []):
                    print(f"  NOTE: {message}")
                classified = set(result.get("risks", [])) | set(result.get("notes", []))
                for message in result.get("warnings", []):
                    if message not in classified:
                        print(f"  NOTE: {message}")
                continue
            for message in result.get("errors", []):
                print(f"  ERROR: {message}")
            for message in result.get("warnings", []):
                print(f"  NOTE: {message}")
        if args.client == "all":
            print("hook clients: PASS" if body["ok"] else "hook clients: FAIL")
    return 0 if body["ok"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise
    except Exception as exc:
        print(json.dumps({"ok": False, "status": "FAIL", "errors": [f"verifier crashed: {exc}"]}))
        raise SystemExit(1) from exc
