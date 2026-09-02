#!/usr/bin/env python3
"""Capture unprimed Claude/Codex trigger evidence; grading stays in run_evals.py."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

ROOTS = (
    ".claude-plugin",
    "agents",
    "codex",
    "commands",
    "hooks",
    "references",
    "schema",
    "skills",
    "templates",
    "workflows",
)
FORBIDDEN_PROMPT_TERMS = (
    "skill-improve",
    "mode a",
    "mode b",
    "load skill.md",
    "load the skill",
    "eval",
    "probe",
)
TRACE_KEYS = {
    "phase",
    "backend",
    "case_id",
    "expected",
    "observed",
    "selected_owner",
    "candidate_digest",
    "candidate_file_count",
    "prompt_digest",
    "cli_version",
    "reported_model",
    "captured_at_utc",
    "git_revision",
    "git_dirty",
    "child_exit",
}
FAILURE_KINDS = {
    "prompt-invalid",
    "executable-unavailable",
    "candidate-install",
    "timeout",
    "child-exit",
    "provider-authentication",
    "provider-error",
    "stream-malformed",
    "stream-incomplete",
    "snapshot-invalid",
    "filesystem",
}
FAILURE_KEYS = {
    "phase",
    "backend",
    "case_id",
    "failure_kind",
    "candidate_digest",
    "candidate_file_count",
    "child_exit",
    "captured_at_utc",
    "stdout_bytes",
    "stdout_sha256",
    "stderr_bytes",
    "stderr_sha256",
}


class CaptureFailure(Exception):
    """A content-free classified failure that may be written to the audit boundary."""

    def __init__(
        self, kind: str, *, child_exit: int | None = None, stdout: str = "", stderr: str = ""
    ):
        super().__init__(kind)
        self.kind = kind
        self.child_exit = child_exit
        self.stdout = stdout
        self.stderr = stderr


def compute_candidate_digest(plugin_root: Path) -> tuple[str, int]:
    """Hash the locked candidate surface in platform-independent sorted order."""
    files: list[tuple[str, Path]] = []
    for root_name in ROOTS:
        root = plugin_root / root_name
        if not root.exists():
            continue
        if root.is_symlink():
            raise ValueError(f"candidate root is a symlink: {root}")
        for path in root.rglob("*"):
            if path.is_symlink():
                raise ValueError(f"candidate surface contains a symlink: {path}")
            if path.is_file():
                files.append((path.relative_to(plugin_root).as_posix(), path))
    digest = hashlib.sha256()
    for relative, path in sorted(files):
        try:
            body = path.read_bytes()
        except OSError as error:
            raise ValueError(f"candidate file is unreadable: {path}: {error}") from error
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(len(body)).encode("ascii"))
        digest.update(b"\0")
        digest.update(body)
    return digest.hexdigest(), len(files)


def _extract_archive(archive_bytes: bytes, destination: Path) -> None:
    """Validate every POSIX tar member before extracting any snapshot content."""
    try:
        with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:") as bundle:
            members = bundle.getmembers()
            for member in members:
                path = PurePosixPath(member.name)
                backslash = chr(92)
                windows_absolute = (
                    len(member.name) >= 3
                    and member.name[0].isalpha()
                    and member.name[1] == ":"
                    and member.name[2] in ("/", backslash)
                )
                if (
                    not member.name
                    or member.name.startswith(("/", backslash))
                    or windows_absolute
                    or backslash in member.name
                    or ".." in path.parts
                    or member.issym()
                    or member.islnk()
                ):
                    raise ValueError("snapshot-invalid")
                if not (member.isdir() or member.isfile()):
                    raise ValueError("snapshot-invalid")
            destination.mkdir(parents=True, exist_ok=True)
            for member in members:
                target = destination.joinpath(*PurePosixPath(member.name).parts)
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    source = bundle.extractfile(member)
                    if source is None:
                        raise ValueError("snapshot-invalid")
                    target.write_bytes(source.read())
    except (OSError, subprocess.TimeoutExpired, tarfile.TarError) as error:
        raise ValueError("snapshot-invalid") from error


def materialize_plugin_ref(plugin_root: Path, ref: str, destination: Path) -> str:
    """Extract one immutable full-OID Git archive after validating every member."""
    if not re.fullmatch(r"[0-9a-f]{40}", ref):
        raise ValueError("snapshot-invalid")
    try:
        resolved = subprocess.run(
            ["git", "rev-parse", f"{ref}^{{commit}}"],
            cwd=plugin_root,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
        oid = resolved.stdout.strip()
        if resolved.returncode != 0 or oid != ref:
            raise ValueError("snapshot-invalid")
        archive = subprocess.run(
            ["git", "archive", "--format=tar", oid],
            cwd=plugin_root,
            capture_output=True,
            timeout=30,
            check=False,
        )
        if archive.returncode != 0:
            raise ValueError("snapshot-invalid")
        _extract_archive(archive.stdout, destination)
        return oid
    except (OSError, subprocess.TimeoutExpired, tarfile.TarError) as error:
        raise ValueError("snapshot-invalid") from error


def _walk(value: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(value, dict):
        found.append(value)
        for child in value.values():
            found.extend(_walk(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_walk(child))
    return found


def _parse_stream(
    stream: str, backend: str, *, codex_skill_paths: tuple[str, ...]
) -> tuple[str, str, str | None, str | None]:
    """Return polarity, response, model and the Skill owner actually selected."""
    records: list[dict[str, Any]] = []
    for line in stream.splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"malformed JSONL: {error.msg}") from error
        if not isinstance(record, dict):
            raise ValueError("malformed JSONL: record is not an object")
        # Provider errors are top-level protocol records. Never scan ordinary response/tool text:
        # a correct answer can discuss authentication without being an authentication failure.
        error_value = record.get("error")
        if record.get("type") == "error" or isinstance(error_value, dict):
            detail = error_value if isinstance(error_value, dict) else record
            values = " ".join(str(detail.get(key, "")) for key in ("code", "message", "type"))
            kind = (
                "provider-authentication"
                if re.search(r"auth(entication|orization)?", values, re.IGNORECASE)
                else "provider-error"
            )
            raise CaptureFailure(kind)
        records.append(record)
    if not records:
        raise ValueError("incomplete JSONL: no records")
    nodes = [node for record in records for node in _walk(record)]
    if backend == "codex":
        response = next(
            (
                str(item["text"])
                for record in reversed(records)
                for item in [record.get("item")]
                if record.get("type") == "item.completed"
                and isinstance(item, dict)
                and item.get("type") == "agent_message"
                and isinstance(item.get("text"), str)
                and item["text"].strip()
            ),
            "",
        )
    else:
        response = next(
            (
                str(node[key])
                for node in reversed(nodes)
                for key in ("result", "response", "text")
                if isinstance(node.get(key), str) and node[key].strip()
            ),
            "",
        )
    if not response:
        raise ValueError("incomplete JSONL: no response text")
    model = next((str(node["model"]) for node in nodes if isinstance(node.get("model"), str)), None)
    if backend == "claude":
        owners = [
            str(input_value[key])
            for node in nodes
            if node.get("name") == "Skill"
            for input_value in [node.get("input")]
            if isinstance(input_value, dict)
            for key in ("skill", "name")
            if isinstance(input_value.get(key), str)
        ]
        selected_owner = owners[-1] if owners else None
        loaded = "graph-powers:skill-improve" in owners
    else:
        paths = tuple(path.replace("\\", "/") for path in codex_skill_paths)
        loaded = any(
            record.get("type") == "item.completed"
            and isinstance(record.get("item"), dict)
            and record["item"].get("type") == "command_execution"
            and record["item"].get("status") == "completed"
            and type(record["item"].get("exit_code")) is int
            and record["item"]["exit_code"] == 0
            and isinstance(record["item"].get("command"), str)
            and any(path in record["item"]["command"].replace("\\", "/") for path in paths)
            for record in records
        )
        selected_owner = "graph-powers:skill-improve" if loaded else None
    return ("load" if loaded else "skip"), response, model, selected_owner


def _git_metadata(plugin_root: Path) -> tuple[str, bool]:
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=plugin_root,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            check=False,
        )
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=plugin_root,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            check=False,
        )
        return revision.stdout.strip() if revision.returncode == 0 else "unknown", bool(
            status.stdout.strip()
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown", False


def _version(executable: Path, timeout_seconds: float) -> str:
    try:
        completed = subprocess.run(
            [str(executable), "--version"],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unavailable"
    return (completed.stdout or completed.stderr).strip() or "unknown"


def _command(backend: str, executable: Path, plugin_root: Path, prompt: str) -> list[str]:
    if backend == "claude":
        return [
            str(executable),
            "-p",
            prompt,
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
            str(plugin_root),
        ]
    return [
        str(executable),
        "--ask-for-approval",
        "never",
        "exec",
        "--json",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--sandbox",
        "read-only",
        "--dangerously-bypass-hook-trust",
        "--skip-git-repo-check",
        prompt,
    ]


def _install_codex(plugin_root: Path, project: Path, timeout_seconds: float) -> None:
    result = subprocess.run(
        [
            "bun",
            str(plugin_root / "codex" / "install.mjs"),
            "--project",
            str(project),
            "--plugin",
            str(plugin_root),
            "--scope",
            "project",
        ],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError("Codex project installer failed")


def _load_cases(evals_path: Path) -> dict[str, dict[str, Any]]:
    document = json.loads(evals_path.read_text(encoding="utf-8"))
    return {
        str(case.get("id")): case
        for case in document.get("evals", [])
        if "proactive-live" in case.get("tags", [])
    }


def _write_failure(
    response_dir: Path,
    *,
    phase: str,
    backend: str,
    case_id: str,
    kind: str,
    digest: str | None,
    file_count: int | None,
    child_exit: int | None,
    stdout: str = "",
    stderr: str = "",
) -> None:
    """Persist only fixed-shape, content-free failure metadata."""
    if kind not in FAILURE_KINDS:
        kind = "filesystem"
    out = stdout.encode("utf-8")
    err = stderr.encode("utf-8")
    payload = {
        "phase": phase,
        "backend": backend,
        "case_id": case_id,
        "failure_kind": kind,
        "candidate_digest": digest,
        "candidate_file_count": file_count,
        "child_exit": child_exit,
        "captured_at_utc": datetime.now(UTC).isoformat(),
        "stdout_bytes": len(out),
        "stdout_sha256": hashlib.sha256(out).hexdigest(),
        "stderr_bytes": len(err),
        "stderr_sha256": hashlib.sha256(err).hexdigest(),
    }
    response_dir.mkdir(parents=True, exist_ok=True)
    (response_dir / f"failure-{backend}-{case_id}.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _trial_identity(trial: str) -> tuple[str, str]:
    """Return a safe audit identity without carrying a previous trial's identity."""
    try:
        backend, case_id = trial.split(":", 1)
    except ValueError:
        return "unknown", "unknown"
    if backend not in {"claude", "codex"} or not case_id or "/" in case_id or "\\" in case_id:
        return "unknown", "unknown"
    return backend, case_id


def _write_preflight_failures(
    response_dir: Path, *, phase: str, trials: list[str], kind: str
) -> int:
    """Record a closed diagnostic for every trial when no provider may start."""
    for trial in trials:
        backend, case_id = _trial_identity(trial)
        _write_failure(
            response_dir,
            phase=phase,
            backend=backend,
            case_id=case_id,
            kind=kind,
            digest=None,
            file_count=None,
            child_exit=None,
        )
        print(f"ERROR: {backend}:{case_id}: {kind}", file=sys.stderr)
    return 1


def capture_trials(
    *,
    phase: str,
    plugin_root: Path,
    evals_path: Path,
    response_dir: Path,
    trials: list[str],
    timeout_seconds: float,
    executable_paths: dict[str, Path] | None = None,
    baseline_dir: Path | None = None,
    install_codex: bool = True,
    plugin_ref: str | None = None,
) -> int:
    """Capture supplied live trials. Returns 1 for all declared provider/integrity failures."""
    if phase != "baseline" and plugin_ref is not None:
        return _write_preflight_failures(
            response_dir, phase=phase, trials=trials, kind="snapshot-invalid"
        )
    snapshot: tempfile.TemporaryDirectory[str] | None = None
    snapshot_oid: str | None = None
    try:
        if plugin_ref is not None:
            snapshot = tempfile.TemporaryDirectory(prefix="skill-improve-snapshot-")
            snapshot_oid = materialize_plugin_ref(plugin_root, plugin_ref, Path(snapshot.name))
            plugin_root = Path(snapshot.name)
        cases = _load_cases(evals_path)
        digest, file_count = compute_candidate_digest(plugin_root)
    except (OSError, ValueError, json.JSONDecodeError):
        if snapshot is not None:
            snapshot.cleanup()
        kind = "snapshot-invalid" if plugin_ref is not None else "filesystem"
        return _write_preflight_failures(response_dir, phase=phase, trials=trials, kind=kind)
    if (
        phase == "candidate"
        and baseline_dir is not None
        and not _verify_baseline(baseline_dir, trials, digest)
    ):
        return 1
    response_dir.mkdir(parents=True, exist_ok=True)
    executable_paths = executable_paths or {}
    all_ok = True
    for trial in trials:
        backend, case_id = _trial_identity(trial)
        try:
            if backend == "unknown" or case_id not in cases:
                raise CaptureFailure("prompt-invalid")
            case = cases[case_id]
            prompt = str(case.get("prompt", ""))
            if not prompt or any(term in prompt.lower() for term in FORBIDDEN_PROMPT_TERMS):
                raise CaptureFailure("prompt-invalid")
            executable = executable_paths.get(backend) or Path(shutil.which(backend) or "")
            if not executable.is_file():
                raise CaptureFailure("executable-unavailable")
            with tempfile.TemporaryDirectory(prefix="skill-improve-trigger-") as temporary:
                project = Path(temporary)
                codex_skill_paths = (
                    (plugin_root / "skills" / "skill-improve" / "SKILL.md").resolve().as_posix(),
                    (project / ".agents" / "skills" / "skill-improve" / "SKILL.md")
                    .resolve()
                    .as_posix(),
                )
                if backend == "codex" and install_codex:
                    try:
                        _install_codex(plugin_root, project, timeout_seconds)
                    except (OSError, subprocess.TimeoutExpired, ValueError):
                        raise CaptureFailure("candidate-install") from None
                try:
                    completed = subprocess.run(
                        _command(backend, executable, plugin_root, prompt),
                        cwd=project,
                        capture_output=True,
                        encoding="utf-8",
                        errors="replace",
                        timeout=timeout_seconds,
                        check=False,
                    )
                except subprocess.TimeoutExpired:
                    raise CaptureFailure("timeout") from None
            if completed.returncode != 0:
                raise CaptureFailure(
                    "child-exit",
                    child_exit=completed.returncode,
                    stdout=completed.stdout,
                    stderr=completed.stderr,
                )
            try:
                observed, response, model, selected_owner = _parse_stream(
                    completed.stdout, backend, codex_skill_paths=codex_skill_paths
                )
            except CaptureFailure as error:
                error.stdout = completed.stdout
                error.stderr = completed.stderr
                error.child_exit = completed.returncode
                raise
            except ValueError as error:
                kind = (
                    "stream-malformed"
                    if str(error).startswith("malformed JSONL")
                    else "stream-incomplete"
                )
                raise CaptureFailure(
                    kind,
                    child_exit=completed.returncode,
                    stdout=completed.stdout,
                    stderr=completed.stderr,
                ) from None
            expected = str(case.get("expected", ""))
            expected_owner = case.get("expected_owner")
            revision, dirty = (snapshot_oid, False) if snapshot_oid else _git_metadata(plugin_root)
            trace = {
                "phase": phase,
                "backend": backend,
                "case_id": case_id,
                "expected": expected,
                "observed": observed,
                "selected_owner": selected_owner,
                "candidate_digest": digest,
                "candidate_file_count": file_count,
                "prompt_digest": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "cli_version": _version(executable, timeout_seconds),
                "reported_model": model,
                "captured_at_utc": datetime.now(UTC).isoformat(),
                "git_revision": revision,
                "git_dirty": dirty,
                "child_exit": completed.returncode,
            }
            (response_dir / f"resp-{case_id}.txt").write_text(response, encoding="utf-8")
            (response_dir / f"trace-{backend}-{case_id}.json").write_text(
                json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            if (phase == "candidate" and observed != expected) or (
                isinstance(expected_owner, str) and selected_owner != expected_owner
            ):
                all_ok = False
        except CaptureFailure as error:
            _write_failure(
                response_dir,
                phase=phase,
                backend=backend,
                case_id=case_id,
                kind=error.kind,
                digest=digest,
                file_count=file_count,
                child_exit=error.child_exit,
                stdout=error.stdout,
                stderr=error.stderr,
            )
            print(f"ERROR: {backend}:{case_id}: {error.kind}", file=sys.stderr)
            all_ok = False
        except (OSError, ValueError, subprocess.TimeoutExpired):
            _write_failure(
                response_dir,
                phase=phase,
                backend=backend,
                case_id=case_id,
                kind="filesystem",
                digest=digest,
                file_count=file_count,
                child_exit=None,
            )
            print(f"ERROR: {backend}:{case_id}: filesystem", file=sys.stderr)
            all_ok = False
    if snapshot is not None:
        snapshot.cleanup()
    return 0 if all_ok else 1


def _verify_baseline(baseline_dir: Path, trials: list[str], candidate_digest: str) -> bool:
    traces = []
    try:
        for trial in trials:
            backend, case_id = trial.split(":", 1)
            traces.append(
                json.loads(
                    (baseline_dir / f"trace-{backend}-{case_id}.json").read_text(encoding="utf-8")
                )
            )
        baseline_digests = {trace["candidate_digest"] for trace in traces}
        if len(baseline_digests) != 1 or candidate_digest in baseline_digests:
            raise ValueError("baseline digest does not differ from candidate")
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: baseline verification: {error}", file=sys.stderr)
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture clean-session trigger evidence.")
    parser.add_argument("--phase", choices=("baseline", "candidate"), required=True)
    parser.add_argument("--timeout-seconds", type=float, required=True)
    parser.add_argument("--plugin-root", type=Path, required=True)
    parser.add_argument("--plugin-ref")
    parser.add_argument("--evals-path", type=Path, required=True)
    parser.add_argument("--response-dir", type=Path, required=True)
    parser.add_argument("--baseline-dir", type=Path)
    parser.add_argument("--trial", action="append", required=True)
    args = parser.parse_args()
    if args.phase == "candidate" and args.baseline_dir is None:
        parser.error("--baseline-dir is required for candidate capture")
    if args.phase == "candidate" and args.plugin_ref is not None:
        parser.error("--plugin-ref is baseline-only")
    return capture_trials(
        phase=args.phase,
        plugin_root=args.plugin_root.resolve(),
        evals_path=args.evals_path,
        response_dir=args.response_dir,
        trials=args.trial,
        timeout_seconds=args.timeout_seconds,
        baseline_dir=args.baseline_dir,
        install_codex=True,
        plugin_ref=args.plugin_ref,
    )


if __name__ == "__main__":
    sys.exit(main())
