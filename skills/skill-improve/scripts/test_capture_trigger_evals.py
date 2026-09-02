"""Focused contract tests for the clean-session trigger-eval producer."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest
from contextlib import redirect_stderr
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
                "expected_owner": "graph-powers:senior-prompt-engineer",
                "assertions": [],
            },
        ],
    }


def executable(root: Path, backend: str, mode: str = "good") -> Path:
    path = root / f"fake-{backend}.py"
    source = (
        f"#!{sys.executable}\n"
        + """import json, os, sys
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
if mode == 'structured-auth':
    print(json.dumps({'type': 'error', 'error': {'code': 'authentication_required', 'message': 'STDOUT_SENTINEL'}}))
    print(os.environ.get('CAPTURE_ENV_SENTINEL', '') + ' STDERR_SENTINEL', file=sys.stderr)
    raise SystemExit(0)
load = 'Create a reusable skill' in prompt
if 'claude' in os.path.basename(sys.argv[0]):
    if load:
        print(json.dumps({'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': 'Skill', 'input': {'skill': 'graph-powers:skill-improve'}}]}}))
    elif mode != 'no-owner':
        owner = 'graph-powers:wrong-owner' if mode == 'wrong-owner' else 'graph-powers:senior-prompt-engineer'
        print(json.dumps({'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': 'Skill', 'input': {'skill': owner}}]}}))
else:
    if load:
        command = os.path.join(os.getcwd(), '.agents', 'skills', 'skill-improve', 'SKILL.md')
        print(json.dumps({'type': 'item.completed', 'item': {'type': 'command_execution', 'status': 'completed', 'exit_code': 0, 'command': command}}))
result = 'skill-improve Mode A' if load else 'senior-prompt-engineer'
if mode == 'auth-word':
    result += ' explains authentication safely'
if 'claude' in os.path.basename(sys.argv[0]):
    print(json.dumps({'type': 'result', 'result': result}))
else:
    print(json.dumps({'type': 'item.completed', 'item': {'type': 'agent_message', 'text': result}}))
"""
    )
    path.write_text(source, encoding="utf-8")
    path.chmod(0o700)
    return path


class CaptureTriggerEvalsTests(unittest.TestCase):
    def test_codex_load_requires_completed_allowed_command_execution(self) -> None:
        source = "/candidate/skills/skill-improve/SKILL.md"
        installed = "/project/.agents/skills/skill-improve/SKILL.md"

        def parse(*records: dict) -> tuple[str, str, str | None, str | None]:
            return CAPTURE._parse_stream(
                "\n".join(json.dumps(record) for record in records),
                "codex",
                codex_skill_paths=(source, installed),
            )

        message = {
            "type": "item.completed",
            "item": {"type": "agent_message", "text": "skill-improve Mode A"},
        }
        for allowed in (source, installed):
            command = {
                "type": "item.completed",
                "item": {
                    "type": "command_execution",
                    "status": "completed",
                    "exit_code": 0,
                    "command": f"python {allowed}",
                },
            }
            self.assertEqual(
                parse(command, message),
                ("load", "skill-improve Mode A", None, "graph-powers:skill-improve"),
            )

        response_only = {
            "type": "item.completed",
            "item": {"type": "agent_message", "text": source},
        }
        output_only = {
            "type": "item.completed",
            "item": {
                "type": "command_execution",
                "status": "completed",
                "exit_code": 0,
                "aggregated_output": installed,
            },
        }
        failed_command = {
            "type": "item.completed",
            "item": {
                "type": "command_execution",
                "status": "completed",
                "exit_code": 1,
                "command": f"python {source}",
            },
        }
        self.assertEqual(parse(response_only), ("skip", source, None, None))
        self.assertEqual(parse(output_only, message), ("skip", "skill-improve Mode A", None, None))
        self.assertEqual(
            parse(failed_command, message), ("skip", "skill-improve Mode A", None, None)
        )
        self.assertEqual(parse(message), ("skip", "skill-improve Mode A", None, None))

    def test_successful_stream_with_authentication_content_is_not_an_auth_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plugin = root / "plugin"
            (plugin / "skills").mkdir(parents=True)
            (plugin / "skills" / "entry.txt").write_text("candidate\n", encoding="utf-8")
            evals = root / "evals.json"
            evals.write_text(json.dumps(eval_document()), encoding="utf-8")
            prior = os.environ.get("CAPTURE_MODE")
            os.environ["CAPTURE_MODE"] = "auth-word"
            try:
                result = CAPTURE.capture_trials(
                    phase="candidate",
                    plugin_root=plugin,
                    evals_path=evals,
                    response_dir=root / "responses",
                    trials=["codex:pro-precreate-skill"],
                    timeout_seconds=5,
                    executable_paths={"codex": executable(root, "codex")},
                    install_codex=False,
                )
            finally:
                if prior is None:
                    os.environ.pop("CAPTURE_MODE", None)
                else:
                    os.environ["CAPTURE_MODE"] = prior
            self.assertEqual(result, 0)
            self.assertTrue((root / "responses" / "resp-pro-precreate-skill.txt").is_file())
            self.assertTrue((root / "responses" / "trace-codex-pro-precreate-skill.json").is_file())

    def test_structured_auth_failure_uses_exact_content_free_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plugin = root / "plugin"
            (plugin / "skills").mkdir(parents=True)
            (plugin / "skills" / "entry.txt").write_text("candidate\n", encoding="utf-8")
            evals = root / "evals.json"
            evals.write_text(json.dumps(eval_document()), encoding="utf-8")
            old = os.environ.get("CAPTURE_MODE")
            old_secret = os.environ.get("CAPTURE_ENV_SENTINEL")
            os.environ["CAPTURE_MODE"] = "structured-auth"
            os.environ["CAPTURE_ENV_SENTINEL"] = "ENV_SENTINEL_7a1"
            try:
                console = io.StringIO()
                with redirect_stderr(console):
                    result = CAPTURE.capture_trials(
                        phase="baseline",
                        plugin_root=plugin,
                        evals_path=evals,
                        response_dir=root / "responses",
                        trials=["codex:pro-precreate-skill"],
                        timeout_seconds=5,
                        executable_paths={"codex": executable(root, "codex")},
                        install_codex=False,
                    )
            finally:
                if old is None:
                    os.environ.pop("CAPTURE_MODE", None)
                else:
                    os.environ["CAPTURE_MODE"] = old
                if old_secret is None:
                    os.environ.pop("CAPTURE_ENV_SENTINEL", None)
                else:
                    os.environ["CAPTURE_ENV_SENTINEL"] = old_secret
            self.assertEqual(result, 1)
            self.assertEqual(
                console.getvalue(), "ERROR: codex:pro-precreate-skill: provider-authentication\n"
            )
            failure = json.loads(
                (root / "responses" / "failure-codex-pro-precreate-skill.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(set(failure), CAPTURE.FAILURE_KEYS)
            self.assertEqual(failure["failure_kind"], "provider-authentication")
            stdout = b'{"type": "error", "error": {"code": "authentication_required", "message": "STDOUT_SENTINEL"}}\n'
            stderr = b"ENV_SENTINEL_7a1 STDERR_SENTINEL\n"
            self.assertEqual(failure["stdout_bytes"], len(stdout))
            self.assertEqual(failure["stdout_sha256"], hashlib.sha256(stdout).hexdigest())
            self.assertEqual(failure["stderr_bytes"], len(stderr))
            self.assertEqual(failure["stderr_sha256"], hashlib.sha256(stderr).hexdigest())
            audit_text = "".join(
                path.read_text(encoding="utf-8") for path in (root / "responses").iterdir()
            )
            for sentinel in ("STDOUT_SENTINEL", "STDERR_SENTINEL", "ENV_SENTINEL_7a1"):
                self.assertNotIn(sentinel, audit_text)
                self.assertNotIn(sentinel, console.getvalue())
            self.assertFalse((root / "responses" / "resp-pro-precreate-skill.txt").exists())
            self.assertFalse((root / "responses" / "trace-codex-pro-precreate-skill.json").exists())

    def test_snapshot_uses_committed_bytes_and_only_full_lowercase_oid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for command in (
                ["git", "init", "-q"],
                ["git", "config", "user.email", "x@example.invalid"],
                ["git", "config", "user.name", "x"],
            ):
                subprocess.run(command, cwd=root, check=True)
            (root / "skills").mkdir()
            tracked = root / "skills" / "entry.txt"
            tracked.write_text("committed\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "fixture"], cwd=root, check=True)
            oid = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            ).stdout.strip()
            tracked.write_text("dirty\n", encoding="utf-8")
            destination = root / "snapshot"
            self.assertEqual(CAPTURE.materialize_plugin_ref(root, oid, destination), oid)
            self.assertEqual(
                (destination / "skills" / "entry.txt").read_text(encoding="utf-8"), "committed\n"
            )
            for invalid in ("HEAD", "main", oid[:12], oid.upper()):
                with self.assertRaisesRegex(ValueError, "snapshot-invalid"):
                    CAPTURE.materialize_plugin_ref(root, invalid, root / f"bad-{len(invalid)}")

    def test_candidate_phase_rejects_plugin_ref_before_capture(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(
                CAPTURE.capture_trials(
                    phase="candidate",
                    plugin_root=root,
                    evals_path=root / "absent.json",
                    response_dir=root / "out",
                    trials=["codex:pro-precreate-skill"],
                    timeout_seconds=1,
                    plugin_ref="0" * 40,
                ),
                1,
            )

    def test_archive_members_are_rejected_before_any_destination_write(self) -> None:
        for member_kind, kind in [
            ("absolute", tarfile.REGTYPE),
            ("windows-absolute", tarfile.REGTYPE),
            ("parent-traversal", tarfile.REGTYPE),
            ("symlink", tarfile.SYMTYPE),
            ("hardlink", tarfile.LNKTYPE),
        ]:
            with self.subTest(member=member_kind), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                destination = root / "destination"
                escaped = root / f"outside-{member_kind}.txt"
                name = {
                    "absolute": escaped.as_posix(),
                    "windows-absolute": r"C:\\outside.txt",
                    "parent-traversal": f"../{escaped.name}",
                    "symlink": "link.txt",
                    "hardlink": "hard.txt",
                }[member_kind]
                payload = io.BytesIO()
                with tarfile.open(fileobj=payload, mode="w") as archive:
                    archive.addfile(tarfile.TarInfo("safe-before-invalid.txt"), io.BytesIO())
                    member = tarfile.TarInfo(name)
                    member.type = kind
                    member.linkname = f"../{escaped.name}"
                    if kind == tarfile.REGTYPE:
                        member.size = 1
                        archive.addfile(member, io.BytesIO(b"x"))
                    else:
                        archive.addfile(member)
                with self.assertRaisesRegex(ValueError, "snapshot-invalid"):
                    CAPTURE._extract_archive(payload.getvalue(), destination)
                self.assertFalse(destination.exists())
                self.assertFalse(escaped.exists())

    def test_invalid_snapshot_writes_closed_failure_per_trial_without_provider(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evals = root / "evals.json"
            evals.write_text(json.dumps(eval_document()), encoding="utf-8")
            responses = root / "responses"
            console = io.StringIO()
            with redirect_stderr(console):
                result = CAPTURE.capture_trials(
                    phase="baseline",
                    plugin_root=root,
                    evals_path=evals,
                    response_dir=responses,
                    trials=["codex:pro-precreate-skill", "claude:bound-agent-prompt-draft"],
                    timeout_seconds=1,
                    plugin_ref="HEAD",
                )
            self.assertEqual(result, 1)
            self.assertEqual(
                console.getvalue(),
                "ERROR: codex:pro-precreate-skill: snapshot-invalid\n"
                "ERROR: claude:bound-agent-prompt-draft: snapshot-invalid\n",
            )
            for backend, case_id in (
                ("codex", "pro-precreate-skill"),
                ("claude", "bound-agent-prompt-draft"),
            ):
                payload = json.loads(
                    (responses / f"failure-{backend}-{case_id}.json").read_text(encoding="utf-8")
                )
                self.assertEqual(set(payload), CAPTURE.FAILURE_KEYS)
                self.assertEqual(payload["failure_kind"], "snapshot-invalid")
                self.assertIsNone(payload["candidate_digest"])
                self.assertIsNone(payload["candidate_file_count"])
                self.assertIsNone(payload["child_exit"])
            self.assertFalse(
                any(path.name.startswith(("resp-", "trace-")) for path in responses.iterdir())
            )

    def test_invalid_later_trial_does_not_reuse_the_prior_trial_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plugin = root / "plugin"
            (plugin / "skills").mkdir(parents=True)
            (plugin / "skills" / "entry.txt").write_text("candidate\n", encoding="utf-8")
            evals = root / "evals.json"
            evals.write_text(json.dumps(eval_document()), encoding="utf-8")
            responses = root / "responses"
            console = io.StringIO()
            with redirect_stderr(console):
                result = CAPTURE.capture_trials(
                    phase="baseline",
                    plugin_root=plugin,
                    evals_path=evals,
                    response_dir=responses,
                    trials=["codex:pro-precreate-skill", "not-a-trial"],
                    timeout_seconds=5,
                    executable_paths={"codex": executable(root, "codex")},
                    install_codex=False,
                )
            self.assertEqual(result, 1)
            failure = json.loads(
                (responses / "failure-unknown-unknown.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                (failure["backend"], failure["case_id"], failure["failure_kind"]),
                ("unknown", "unknown", "prompt-invalid"),
            )
            self.assertEqual(console.getvalue(), "ERROR: unknown:unknown: prompt-invalid\n")

    def test_claude_command_is_nonpersistent_project_only_and_preserves_prompt(self) -> None:
        prompt = "Draft the prompt for a new reviewer agent."
        command = CAPTURE._command("claude", Path("/fixture/claude"), Path("/candidate"), prompt)

        self.assertEqual(command[command.index("-p") + 1], prompt)
        for flag in (
            "--no-session-persistence",
            "--setting-sources",
            "project",
            "--permission-mode",
            "plan",
            "--output-format",
            "stream-json",
            "--verbose",
            "--tools",
            "Skill",
            "--disallowedTools",
            "Write,Edit",
            "--plugin-dir",
            "/candidate",
        ):
            self.assertIn(flag, command)

    def test_claude_negative_requires_the_exact_alternate_skill_owner(self) -> None:
        no_owner = json.dumps({"type": "result", "result": "senior-prompt-engineer"})
        wrong_owner = "\n".join(
            [
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {
                            "content": [
                                {
                                    "type": "tool_use",
                                    "name": "Skill",
                                    "input": {"skill": "graph-powers:wrong-owner"},
                                }
                            ]
                        },
                    }
                ),
                json.dumps({"type": "result", "result": "senior-prompt-engineer"}),
            ]
        )
        exact_owner = "\n".join(
            [
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {
                            "content": [
                                {
                                    "type": "tool_use",
                                    "name": "Skill",
                                    "input": {"skill": "graph-powers:senior-prompt-engineer"},
                                }
                            ]
                        },
                    }
                ),
                json.dumps({"type": "result", "result": "senior-prompt-engineer"}),
            ]
        )

        self.assertEqual(
            CAPTURE._parse_stream(no_owner, "claude", codex_skill_paths=()),
            ("skip", "senior-prompt-engineer", None, None),
        )
        self.assertEqual(
            CAPTURE._parse_stream(wrong_owner, "claude", codex_skill_paths=()),
            ("skip", "senior-prompt-engineer", None, "graph-powers:wrong-owner"),
        )
        self.assertEqual(
            CAPTURE._parse_stream(exact_owner, "claude", codex_skill_paths=()),
            ("skip", "senior-prompt-engineer", None, "graph-powers:senior-prompt-engineer"),
        )

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
                    phase="candidate",
                    plugin_root=plugin,
                    evals_path=evals,
                    response_dir=responses,
                    trials=["codex:pro-precreate-skill", "claude:bound-agent-prompt-draft"],
                    timeout_seconds=5,
                    executable_paths={
                        "codex": executable(root, "codex"),
                        "claude": executable(root, "claude"),
                    },
                    install_codex=False,
                )
            finally:
                if old_marker is None:
                    os.environ.pop("CAPTURE_CWD_MARKER", None)
                else:
                    os.environ["CAPTURE_CWD_MARKER"] = old_marker

            self.assertEqual(result, 0)
            traces = [
                json.loads((responses / f"trace-{backend}-{case}.json").read_text(encoding="utf-8"))
                for backend, case in [
                    ("codex", "pro-precreate-skill"),
                    ("claude", "bound-agent-prompt-draft"),
                ]
            ]
            self.assertEqual(
                [(trace["expected"], trace["observed"]) for trace in traces],
                [("load", "load"), ("skip", "skip")],
            )
            self.assertEqual(
                [trace["selected_owner"] for trace in traces],
                ["graph-powers:skill-improve", "graph-powers:senior-prompt-engineer"],
            )
            self.assertEqual(len({trace["candidate_digest"] for trace in traces}), 1)
            self.assertEqual(
                (responses / "resp-pro-precreate-skill.txt").read_text(encoding="utf-8"),
                "skill-improve Mode A",
            )
            self.assertEqual(
                (responses / "resp-bound-agent-prompt-draft.txt").read_text(encoding="utf-8"),
                "senior-prompt-engineer",
            )
            cwd_values = marker.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(cwd_values), 2)
            self.assertEqual(len(set(cwd_values)), 2)
            self.assertTrue(all(not Path(value, "AGENTS.md").exists() for value in cwd_values))

    def test_candidate_negative_rejects_no_owner_and_wrong_owner(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plugin = root / "plugin"
            (plugin / "skills").mkdir(parents=True)
            (plugin / "skills" / "entry.txt").write_text("candidate\n", encoding="utf-8")
            evals = root / "evals.json"
            evals.write_text(json.dumps(eval_document()), encoding="utf-8")
            fake = executable(root, "claude")
            for mode in ("no-owner", "wrong-owner"):
                before = os.environ.get("CAPTURE_MODE")
                os.environ["CAPTURE_MODE"] = mode
                try:
                    result = CAPTURE.capture_trials(
                        phase="candidate",
                        plugin_root=plugin,
                        evals_path=evals,
                        response_dir=root / mode,
                        trials=["claude:bound-agent-prompt-draft"],
                        timeout_seconds=5,
                        executable_paths={"claude": fake},
                        install_codex=False,
                    )
                finally:
                    if before is None:
                        os.environ.pop("CAPTURE_MODE", None)
                    else:
                        os.environ["CAPTURE_MODE"] = before
                self.assertEqual(result, 1, mode)

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
                        phase="candidate",
                        plugin_root=plugin,
                        evals_path=evals,
                        response_dir=root / mode,
                        trials=["codex:pro-precreate-skill"],
                        timeout_seconds=5,
                        executable_paths={"codex": fake},
                        install_codex=False,
                    )
                finally:
                    if old_mode is None:
                        os.environ.pop("CAPTURE_MODE", None)
                    else:
                        os.environ["CAPTURE_MODE"] = old_mode
                self.assertEqual(result, 1, mode)
            self.assertEqual(
                CAPTURE.capture_trials(
                    phase="candidate",
                    plugin_root=plugin,
                    evals_path=evals,
                    response_dir=root / "missing",
                    trials=["codex:pro-precreate-skill"],
                    timeout_seconds=5,
                    executable_paths={"codex": root / "absent"},
                    install_codex=False,
                ),
                1,
            )
            self.assertEqual(
                CAPTURE.capture_trials(
                    phase="candidate",
                    plugin_root=plugin,
                    evals_path=evals,
                    response_dir=root / "timeout",
                    trials=["codex:pro-precreate-skill"],
                    timeout_seconds=0.0001,
                    executable_paths={"codex": fake},
                    install_codex=False,
                ),
                1,
            )

    def test_primed_prompt_is_rejected_before_provider_execution(self) -> None:
        document = eval_document()
        document["evals"][0]["prompt"] = "Load skill-improve before writing the answer."
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evals = root / "evals.json"
            evals.write_text(json.dumps(document), encoding="utf-8")
            self.assertEqual(
                CAPTURE.capture_trials(
                    phase="baseline",
                    plugin_root=root,
                    evals_path=evals,
                    response_dir=root / "responses",
                    trials=["codex:pro-precreate-skill"],
                    timeout_seconds=5,
                    executable_paths={"codex": root / "not-called"},
                    install_codex=False,
                ),
                1,
            )


if __name__ == "__main__":
    unittest.main()
