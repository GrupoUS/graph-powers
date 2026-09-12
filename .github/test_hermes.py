#!/usr/bin/env python3
"""Hermes static CLI regressions. Never import a source or generated plugin."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "bin/verify-hook-clients.py"


class HermesStaticTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="hermes-static-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "source"
        self.root.mkdir()
        self.marker = self.root.parent / "EXECUTED"
        self.sentinel = (
            f"from pathlib import Path\nPath({str(self.marker)!r}).write_text('executed')\n"
        )
        self.put("__init__.py", self.sentinel)
        self.put("hooks/_config.py", self.sentinel)
        self.put(
            ".claude-plugin/plugin.json",
            json.dumps({"name": "graph-powers", "version": "0.0.1", "description": "fixture"}),
        )
        self.put(
            "skills/demo/SKILL.md",
            "---\nname: demo\ndescription: Fixture\n---\nRead `references/guide.md`.\n",
        )
        self.put("skills/demo/references/guide.md", "# Guide\nStatic content.\n")
        self.put("LICENSE", "Fixture license\n")
        self.put("NOTICE", "Fixture notice\n")
        for source in ("hermes/install.mjs", "hermes/package_builder.py", "codex/lib.mjs"):
            destination = self.root / source
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / source, destination)
        result = subprocess.run(
            ["bun", str(self.root / "hermes/install.mjs"), "--package-only"],
            capture_output=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.package = self.root / "hermes/package"

    def put(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")

    def run_cli(self, *extra, proof="static", package=True):
        command = [
            sys.executable,
            "-X",
            "utf8",
            str(VERIFIER),
            "--client",
            "hermes",
            "--hermes-proof",
            proof,
            "--plugin-root",
            str(self.root),
            "--json",
        ]
        if package:
            command.extend(["--package-root", str(self.package)])
        result = subprocess.run(
            command + list(extra), capture_output=True, encoding="utf-8", check=False
        )
        self.assertFalse(self.marker.exists(), "route executed a plugin or config sentinel")
        return result

    def tamper(self, relative, text):
        path = self.package / relative
        path.write_text(text, encoding="utf-8")
        provenance_path = self.package / "PROVENANCE.json"
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        for row in provenance["files"]:
            if row["path"] == relative:
                row["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        provenance_path.write_text(json.dumps(provenance), encoding="utf-8")

    def test_static_success_never_imports_source_entrypoint_or_hook_config(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            (payload["status"], payload["proof"], payload["runtime"]),
            ("PASS", "static", "UNVERIFIED"),
        )
        self.assertEqual(payload["skills"]["names"], ["demo"])

    def test_static_rejects_self_hashed_entrypoint_without_importing_it(self):
        self.tamper("__init__.py", self.sentinel)
        result = self.run_cli()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("source", result.stdout.lower())

    def test_static_rejects_self_hashed_main_and_auxiliary_edits(self):
        for path in ("skills/demo.md", "skills/content/skills/demo/references/guide.md"):
            with self.subTest(path=path):
                original = (self.package / path).read_bytes()
                provenance = (self.package / "PROVENANCE.json").read_bytes()
                try:
                    self.tamper(path, "# Forged content\n")
                    result = self.run_cli()
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    self.assertIn("source", result.stdout.lower())
                finally:
                    (self.package / path).write_bytes(original)
                    (self.package / "PROVENANCE.json").write_bytes(provenance)

    def test_caller_supplied_generator_is_data_never_executed(self):
        self.put(
            "hermes/install.mjs",
            f"import fs from 'node:fs'; fs.writeFileSync({json.dumps(str(self.marker))}, 'executed');\n",
        )
        result = self.run_cli()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("source", result.stdout.lower())

    def test_static_rejects_omitted_registration(self):
        path = self.package / "PROVENANCE.json"
        provenance = json.loads(path.read_text(encoding="utf-8"))
        provenance["registrations"] = []
        path.write_text(json.dumps(provenance), encoding="utf-8")
        result = self.run_cli()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("source", result.stdout.lower())

    def test_static_rejects_extra_missing_and_malformed_payloads(self):
        extra = self.package / "unexpected.py"
        extra.write_text(self.sentinel, encoding="utf-8")
        result = self.run_cli()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("unexpected.py", result.stdout)
        extra.unlink()
        (self.package / "skills/demo.md").unlink()
        result = self.run_cli()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("skills/demo.md", result.stdout)
        (self.package / "PROVENANCE.json").write_text("[invalid", encoding="utf-8")
        result = self.run_cli()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("PROVENANCE", result.stdout)

    def test_static_rejects_source_drift(self):
        self.put("skills/demo/references/guide.md", "# Updated source\n")
        result = self.run_cli()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("source", result.stdout.lower())

    def test_static_rejects_symlink_payload(self):
        path = self.package / "skills/demo.md"
        path.unlink()
        try:
            path.symlink_to(self.root / "skills/demo/SKILL.md")
        except OSError as error:
            self.skipTest(str(error))
        result = self.run_cli()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("symlink", result.stdout.lower())

    def test_runtime_missing_args_never_falls_back_to_checkout(self):
        result = self.run_cli(proof="runtime", package=False)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["runtime"], "UNVERIFIED")
        self.assertIn("--package-root", result.stdout)
        self.assertIn("--expected-version", result.stdout)

    def test_runtime_complete_args_cannot_claim_unimplemented_proof(self):
        self.tamper("__init__.py", self.sentinel)
        result = self.run_cli("--expected-version", "0.0.1", proof="runtime")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["runtime"], "UNVERIFIED")
        self.assertIn("not implemented", result.stdout.lower())

    def test_wiring_reads_invalid_native_calls_in_generated_bytes(self):
        for command in ("verify", "debug", "perf"):
            self.put(f"commands/{command}.md", "# Fixture\n")
        self.tamper("skills/demo.md", 'Load skill_view("graph-powers:definitely-missing").\n')
        result = subprocess.run(
            [sys.executable, str(ROOT / ".github/check_wiring.py")],
            cwd=self.root,
            capture_output=True,
            encoding="utf-8",
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertIn("definitely-missing", result.stdout)

    def test_wiring_canonical_pair_only_and_case_collisions(self):
        for name in ("verify", "debug", "perf", "demo"):
            self.put(f"commands/{name}.md", "# Fixture\n")

        def collisions():
            result = subprocess.run(
                [sys.executable, str(ROOT / ".github/check_wiring.py")], cwd=self.root,
                capture_output=True, encoding="utf-8", check=False,
            )
            self.assertEqual(result.stderr, "")
            return result.stdout

        self.assertNotIn("Hermes registration", collisions())
        self.put("hermes/skills/demo/SKILL.md", "# Unrelated duplicate\n")
        self.assertIn("Hermes registration `demo` collides", collisions())
        (self.root / "hermes/skills/demo/SKILL.md").unlink()
        (self.root / "commands/demo.md").unlink()
        self.put("commands/Demo.md", "# Wrong case\n")
        self.assertIn("Hermes registration `Demo` collides", collisions())

    def test_wiring_preserves_source_role_classification_for_generated_agents(self):
        for command in ("verify", "debug", "perf"):
            self.put(f"commands/{command}.md", "# Fixture\n")
        self.put(
            "agents/explorer.md",
            "---\nname: explorer\nrole_type: researcher\nmodel: haiku\ntools: Read\ndisallowedTools: Write, Edit\n---\n# Explorer\n",
        )
        self.put(
            "hermes/package/skills/agent-explorer.md",
            "A contract uses `explorer` as its own name.\n",
        )
        result = subprocess.run(
            [sys.executable, str(ROOT / ".github/check_wiring.py")],
            cwd=self.root,
            capture_output=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(result.stderr, "")
        self.assertNotIn("hermes/package/skills/agent-explorer.md", result.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--static", action="store_true")
    mode.add_argument("--runtime", action="store_true")
    parser.add_argument("--package-root")
    parser.add_argument("--expected-version")
    args = parser.parse_args()
    if args.runtime:
        command = [
            sys.executable,
            "-X",
            "utf8",
            str(VERIFIER),
            "--client",
            "hermes",
            "--hermes-proof",
            "runtime",
            "--json",
        ]
        for name in ("package_root", "expected_version"):
            if getattr(args, name):
                command.extend(["--" + name.replace("_", "-"), getattr(args, name)])
        return subprocess.run(command, check=False).returncode
    result = unittest.TextTestRunner().run(
        unittest.defaultTestLoader.loadTestsFromTestCase(HermesStaticTests)
    )
    print(
        "Hermes verifier: STATIC PASS" if result.wasSuccessful() else "Hermes verifier: STATIC FAIL"
    )
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
