#!/usr/bin/env python3
"""Focused RED/GREEN checks for the native Hermes projection."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]


def load_entrypoint():
    path = ROOT / "__init__.py"
    spec = importlib.util.spec_from_file_location("graph_powers_hermes_entry", path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(*command: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=ROOT,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env=env,
    )


def test_source_registration() -> None:
    module = load_entrypoint()
    registrations = module.planned_registrations(ROOT)
    names = [name for name, _path, _description in registrations]
    expected_skills = {path.parent.name for path in (ROOT / "skills").glob("*/SKILL.md")}
    expected_commands = {
        path.stem
        for path in (ROOT / "commands").glob("*.md")
        if path.name.upper() != "AGENTS.MD"
    }
    expected_agents = {
        f"agent-{path.stem}"
        for path in (ROOT / "agents").glob("*.md")
        if path.name.upper() != "AGENTS.MD"
    }
    expected = expected_skills | expected_commands | expected_agents | {"graph-engineering"}
    assert expected <= set(names), f"missing Hermes registrations: {sorted(expected - set(names))}"
    assert len(names) == len(set(names)), "Hermes registration names must not collide"
    assert all(path.is_file() for _name, path, _description in registrations)


def test_collision_is_explicit() -> None:
    module = load_entrypoint()
    with TemporaryDirectory(prefix="hermes-registration-") as raw:
        root = Path(raw)
        (root / "skills" / "same").mkdir(parents=True)
        (root / "skills" / "same" / "SKILL.md").write_text(
            "---\nname: same\n---\n", encoding="utf-8"
        )
        (root / "commands").mkdir()
        (root / "commands" / "same.md").write_text(
            "---\ndescription: same\n---\n", encoding="utf-8"
        )
        try:
            module.planned_registrations(root)
        except ValueError as exc:
            assert "same" in str(exc)
        else:
            raise AssertionError("duplicate Hermes names must fail explicitly")


def test_generator_check() -> None:
    result = run("bun", "hermes/install.mjs", "--check")
    assert result.returncode == 0, result.stdout + result.stderr


def test_verifier_route() -> None:
    result = run(
        sys.executable,
        "-X",
        "utf8",
        "bin/verify-hook-clients.py",
        "--client",
        "hermes",
        "--plugin-root",
        str(ROOT),
        "--json",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["client"] == "hermes"
    assert payload["status"] in {"PASS", "SKIPPED"}
    assert payload["present"] is True
    assert payload["registrations"] >= 1


def test_missing_runtime_is_visible() -> None:
    with TemporaryDirectory(prefix="hermes-no-runtime-") as raw:
        env = dict(os.environ)
        env["PATH"] = raw
        result = run(
            sys.executable,
            "-X",
            "utf8",
            "bin/verify-hook-clients.py",
            "--client",
            "hermes",
            "--plugin-root",
            str(ROOT),
            "--json",
            env=env,
        )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "SKIPPED"
    assert any("runtime is not installed" in warning for warning in payload["warnings"])


def main() -> int:
    tests: list[tuple[str, Callable[[], None]]] = [
        ("source registration", test_source_registration),
        ("collision", test_collision_is_explicit),
        ("generator", test_generator_check),
        ("verifier", test_verifier_route),
        ("missing runtime", test_missing_runtime_is_visible),
    ]
    failures: list[str] = []
    for name, test in tests:
        try:
            test()
        except Exception as exc:
            failures.append(f"{name}: {exc}")
    if failures:
        print("Hermes focused tests: FAIL")
        print("\n".join(f"  - {failure}" for failure in failures))
        return 1
    print(f"Hermes focused tests: PASS ({len(tests)} checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
