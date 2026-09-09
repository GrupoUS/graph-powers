#!/usr/bin/env python3
"""Static package regression tests. Execute only the development generator, never plugins."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "hermes/install.mjs"


class HermesPackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="hermes-package-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "source"
        self.root.mkdir()
        self.put(".claude-plugin/plugin.json", json.dumps({
            "name": "graph-powers", "version": "0.0.1", "description": "fixture",
        }))
        self.put("LICENSE", "Fixture license\n")
        self.put("NOTICE", "Fixture notice\n")
        self.put("__init__.py", "raise RuntimeError('ENTRYPOINT MUST NOT EXECUTE')\n")
        self.put("skills/demo/SKILL.md", '---\nname: demo\ndescription: Demo contract\n---\n'
                 '# Demo\nRead `references/guide.md#details`. Use Skill("demo").\n')
        self.put("skills/demo/references/guide.md", "# Details\nRead `../scripts/tool.py`.\n")
        self.put("skills/demo/scripts/tool.py", "from helper import describe\n")
        self.put("skills/demo/scripts/helper.py", "def describe():\n    return 'fixture'\n")

    def put(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")

    def generate(self, *args, root=None, env=None):
        return subprocess.run(
            ["bun", str(GENERATOR), "--plugin", str(root or self.root), *args],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False, env=env,
        )

    def emit(self):
        result = self.generate("--package-only")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        package = self.root / "hermes/package"
        self.assertTrue((package / "PROVENANCE.json").is_file(),
                        "generator did not produce a self-contained Hermes package")
        return package, json.loads((package / "PROVENANCE.json").read_text())

    def test_emits_portable_transitive_content_without_importing_entrypoint(self):
        package, plan = self.emit()
        self.assertEqual([row["name"] for row in plan["registrations"]], ["demo"])
        self.assertEqual(plan["registrations"][0]["path"], "skills/demo.md")
        main = (package / "skills/demo.md").read_text()
        self.assertIn("content/skills/demo/references/guide.md#details", main)
        self.assertIn('skill_view("graph-powers:demo")', main)
        guide = (package / "skills/content/skills/demo/references/guide.md").read_text()
        self.assertIn("content/skills/demo/scripts/tool.py", guide)
        self.assertNotIn("${HERMES_", guide)
        self.assertTrue((package / "skills/content/skills/demo/scripts/helper.py").is_file())
        self.assertNotIn("ENTRYPOINT MUST NOT EXECUTE", (package / "__init__.py").read_text())
        self.assertFalse((self.root / "plugin.yaml").exists(), "package-only touched root metadata")

    @unittest.skipIf(os.name == "nt", "POSIX executable bits are unavailable on Windows")
    def test_generated_shebang_payloads_are_executable_and_repaired(self):
        self.put(
            "skills/demo/scripts/tool.py", "#!/usr/bin/env python3\nfrom helper import describe\n"
        )
        self.put(
            "skills/demo/scripts/helper.py",
            "#!/usr/bin/env python3\ndef describe():\n    return 'fixture'\n",
        )
        self.put("skills/demo/scripts/tool.mjs", "#!/usr/bin/env node\nexport {};\n")
        self.put(
            "skills/demo/references/guide.md",
            "Read `../scripts/tool.py` and `../scripts/tool.mjs`.\n",
        )
        package, _ = self.emit()
        scripts = [
            path
            for path in package.rglob("*")
            if path.is_file() and path.read_bytes().startswith(b"#!")
        ]
        self.assertEqual(len(scripts), 3)
        for path in scripts:
            with self.subTest(path=path.relative_to(package).as_posix()):
                self.assertEqual(path.stat().st_mode & 0o111, 0o111)
                path.chmod(0o644)
        self.emit()
        for path in scripts:
            self.assertEqual(path.stat().st_mode & 0o111, 0o111)
        self.assertEqual((package / "__init__.py").stat().st_mode & 0o111, 0)

    @unittest.skipIf(os.name == "nt", "POSIX executable bits are unavailable on Windows")
    def test_check_rejects_nonexecutable_shebang_payload(self):
        self.put(
            "skills/demo/scripts/tool.py", "#!/usr/bin/env python3\nfrom helper import describe\n"
        )
        package, _ = self.emit()
        (package / "skills/content/skills/demo/scripts/tool.py").chmod(0o644)
        result = self.generate("--check")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not executable", result.stderr)
        self.assertIn("skills/content/skills/demo/scripts/tool.py", result.stderr)

    def test_generation_is_deterministic_and_hashes_cover_every_payload(self):
        package, plan = self.emit()
        before = {p.relative_to(package).as_posix(): p.read_bytes()
                  for p in package.rglob("*") if p.is_file()}
        self.emit()
        after = {p.relative_to(package).as_posix(): p.read_bytes()
                 for p in package.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(set(before), {row["path"] for row in plan["files"]} | {"PROVENANCE.json"})
        for row in plan["files"]:
            self.assertEqual(hashlib.sha256(before[row["path"]]).hexdigest(), row["sha256"])
        source = next(row for row in plan["sources"] if row["path"] == "skills/demo/SKILL.md")
        self.assertEqual(source["sha256"], hashlib.sha256((self.root / source["path"]).read_bytes()).hexdigest())
        self.assertIsNone(plan["source"]["base_revision"])

    def test_unicode_protocol_ignores_inherited_python_pipe_encoding(self):
        description = "Descrição → 中文"
        self.put("skills/demo/SKILL.md", f"---\nname: demo\ndescription: {description}\n---\n# {description}\n")
        for encoding in ("cp1252", "ascii"):
            with self.subTest(encoding=encoding):
                env = {**os.environ, "PYTHONIOENCODING": encoding}
                result = self.generate("--plan-json", env=env)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                plan = json.loads(result.stdout)
                self.assertEqual(plan["registrations"][0]["description"], description)
                result = self.generate("--package-only", env=env)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                rendered = (self.root / "hermes/package/skills/demo.md").read_text(encoding="utf-8")
                self.assertIn(f"# {description}\n", rendered)

    def test_missing_transitive_reference_fails_before_writing(self):
        self.put("skills/demo/references/guide.md", "Read `references/missing.md`.\n")
        result = self.generate("--package-only")
        self.assertNotEqual(result.returncode, 0, "missing dependency was silently accepted")
        self.assertIn("missing.md", result.stderr)
        self.assertFalse((self.root / "hermes/package").exists())

    def test_ambiguous_reference_is_not_guessed(self):
        self.put("references/guide.md", "# Other guide\n")
        result = self.generate("--package-only")
        self.assertNotEqual(result.returncode, 0, "ambiguous reference was silently accepted")
        self.assertIn("ambiguous", result.stderr.lower())

    def test_missing_bare_reference_is_not_classified_as_host_input(self):
        self.put("skills/demo/references/guide.md", "Read `missing.md`.\n")
        result = self.generate("--package-only")
        self.assertNotEqual(result.returncode, 0, "missing shorthand was silently classified as host data")
        self.assertIn("missing.md", result.stderr)

    def test_canonical_instruction_templates_are_bundled_not_host_exemptions(self):
        self.put("skills/demo/SKILL.md", "Read `templates/AGENTS.md` and `templates/CLAUDE.md`.\n")
        self.put("templates/AGENTS.md", "# Instruction structure\n")
        self.put("templates/CLAUDE.md", "# Shared instructions\n")
        package, _ = self.emit()
        for name in ("AGENTS.md", "CLAUDE.md"):
            self.assertTrue((package / "skills/content/templates" / name).is_file(), name)
        (self.root / "templates/CLAUDE.md").unlink()
        result = self.generate("--plan-json")
        self.assertNotEqual(result.returncode, 0, "missing canonical template was silently treated as a host file")
        self.assertIn("templates/CLAUDE.md", result.stderr)

    def test_duplicate_public_name_fails(self):
        self.put("commands/demo.md", "# Duplicate\n")
        result = self.generate("--package-only")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("collision", result.stderr.lower())

    def test_case_insensitive_destination_collision_fails(self):
        self.put("commands/Demo.md", "# Case collision\n")
        result = self.generate("--package-only")
        self.assertNotEqual(result.returncode, 0, "case collision is not portable")
        self.assertIn("collision", result.stderr.lower())

    def test_reference_cannot_escape_source_root(self):
        self.put("skills/demo/SKILL.md", "Read `../../../outside.md`.\n")
        (self.root.parent / "outside.md").write_text("outside\n")
        result = self.generate("--package-only")
        self.assertNotEqual(result.returncode, 0, "escaping reference was accepted")
        self.assertIn("escape", result.stderr.lower())

    def test_symlink_dependency_cannot_escape_source_root(self):
        outside = self.root.parent / "outside.md"
        outside.write_text("outside\n")
        target = self.root / "skills/demo/references/guide.md"
        target.unlink()
        try:
            target.symlink_to(outside)
        except OSError as exc:
            self.skipTest(f"symlink unavailable: {exc}")
        result = self.generate("--package-only")
        self.assertNotEqual(result.returncode, 0, "symlink escape was accepted")
        self.assertIn("escape", result.stderr.lower())

    def test_check_rejects_modified_or_extra_payload(self):
        package, _ = self.emit()
        (package / "unexpected.py").write_text("raise RuntimeError('never execute')\n")
        result = self.generate("--check")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unexpected.py", result.stderr)

    def test_package_root_symlink_does_not_write_outside(self):
        outside = self.root.parent / "output"
        outside.mkdir()
        (self.root / "hermes").mkdir()
        try:
            (self.root / "hermes/package").symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"symlink unavailable: {exc}")
        result = self.generate("--package-only")
        self.assertNotEqual(result.returncode, 0, "package output escaped through root symlink")
        self.assertEqual(list(outside.iterdir()), [])

    def test_repository_plan_preserves_all_38_public_names(self):
        result = self.generate("--plan-json", root=ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        plan = json.loads(result.stdout)
        expected = {path.parent.name for path in (ROOT / "skills").glob("*/SKILL.md")}
        expected |= {path.stem for path in (ROOT / "commands").glob("*.md") if path.name.upper() != "AGENTS.MD"}
        expected |= {"agent-" + path.stem for path in (ROOT / "agents").glob("*.md") if path.name.upper() != "AGENTS.MD"}
        expected.add("graph-engineering")
        self.assertEqual({row["name"] for row in plan["registrations"]}, expected)
        self.assertEqual({str(Path(row["path"]).parent) for row in plan["registrations"]}, {"skills"})
        self.assertEqual(plan["runtime"], "UNVERIFIED")


if __name__ == "__main__":
    result = unittest.main(exit=False)
    if result.result.wasSuccessful():
        print("Hermes package: STATIC PASS")
    raise SystemExit(not result.result.wasSuccessful())
