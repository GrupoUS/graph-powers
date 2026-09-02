#!/usr/bin/env python3
"""Capture unprimed Claude/Codex trigger evidence; grading stays in run_evals.py."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOTS = (".claude-plugin", "agents", "codex", "commands", "hooks", "references", "schema", "skills", "templates", "workflows")
FORBIDDEN_PROMPT_TERMS = ("skill-improve", "mode a", "mode b", "load skill.md", "load the skill", "eval", "probe")
TRACE_KEYS = {"phase", "backend", "case_id", "expected", "observed", "selected_owner", "candidate_digest", "candidate_file_count", "prompt_digest", "cli_version", "reported_model", "captured_at_utc", "git_revision", "git_dirty", "child_exit"}


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


def _parse_stream(stream: str, backend: str) -> tuple[str, str, str | None, str | None]:
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
        records.append(record)
    if not records:
        raise ValueError("incomplete JSONL: no records")
    nodes = [node for record in records for node in _walk(record)]
    response = next((str(node[key]) for node in reversed(nodes) for key in ("result", "response", "text")
                     if isinstance(node.get(key), str) and node[key].strip()), "")
    if not response:
        raise ValueError("incomplete JSONL: no response text")
    model = next((str(node["model"]) for node in nodes if isinstance(node.get("model"), str)), None)
    if backend == "claude":
        owners = [
            str(input_value[key])
            for node in nodes if node.get("name") == "Skill"
            for input_value in [node.get("input")]
            if isinstance(input_value, dict)
            for key in ("skill", "name")
            if isinstance(input_value.get(key), str)
        ]
        selected_owner = owners[-1] if owners else None
        loaded = "graph-powers:skill-improve" in owners
    else:
        loaded = any(".agents/skills/skill-improve/SKILL.md" in json.dumps(node) for node in nodes)
        selected_owner = "graph-powers:skill-improve" if loaded else None
    return ("load" if loaded else "skip"), response, model, selected_owner


def _git_metadata(plugin_root: Path) -> tuple[str, bool]:
    try:
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=plugin_root, capture_output=True,
                                  encoding="utf-8", errors="replace", timeout=5, check=False)
        status = subprocess.run(["git", "status", "--porcelain"], cwd=plugin_root, capture_output=True,
                                encoding="utf-8", errors="replace", timeout=5, check=False)
        return revision.stdout.strip() if revision.returncode == 0 else "unknown", bool(status.stdout.strip())
    except (OSError, subprocess.TimeoutExpired):
        return "unknown", False


def _version(executable: Path, timeout_seconds: float) -> str:
    try:
        completed = subprocess.run([str(executable), "--version"], capture_output=True, encoding="utf-8",
                                   errors="replace", timeout=timeout_seconds, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return "unavailable"
    return (completed.stdout or completed.stderr).strip() or "unknown"


def _command(backend: str, executable: Path, plugin_root: Path, prompt: str) -> list[str]:
    if backend == "claude":
        return [str(executable), "-p", prompt, "--no-session-persistence", "--setting-sources", "project",
                "--permission-mode", "plan", "--output-format", "stream-json", "--verbose", "--tools",
                "Skill", "--disallowedTools", "Write,Edit", "--plugin-dir", str(plugin_root)]
    return [str(executable), "--ask-for-approval", "never", "exec", "--json", "--ephemeral",
            "--ignore-user-config", "--ignore-rules", "--sandbox", "read-only",
            "--dangerously-bypass-hook-trust", "--skip-git-repo-check", prompt]


def _install_codex(plugin_root: Path, project: Path, timeout_seconds: float) -> None:
    result = subprocess.run(["bun", str(plugin_root / "codex" / "install.mjs"), "--project", str(project),
                             "--plugin", str(plugin_root), "--scope", "project"], capture_output=True,
                            encoding="utf-8", errors="replace", timeout=timeout_seconds, check=False)
    if result.returncode != 0:
        raise ValueError("Codex project installer failed")


def _load_cases(evals_path: Path) -> dict[str, dict[str, Any]]:
    document = json.loads(evals_path.read_text(encoding="utf-8"))
    return {str(case.get("id")): case for case in document.get("evals", []) if "proactive-live" in case.get("tags", [])}


def capture_trials(*, phase: str, plugin_root: Path, evals_path: Path, response_dir: Path, trials: list[str],
                   timeout_seconds: float, executable_paths: dict[str, Path] | None = None,
                   baseline_dir: Path | None = None, install_codex: bool = True) -> int:
    """Capture supplied live trials. Returns 1 for all declared provider/integrity failures."""
    try:
        cases = _load_cases(evals_path)
        digest, file_count = compute_candidate_digest(plugin_root)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if phase == "candidate" and baseline_dir is not None and not _verify_baseline(baseline_dir, trials, digest):
        return 1
    response_dir.mkdir(parents=True, exist_ok=True)
    executable_paths = executable_paths or {}
    all_ok = True
    for trial in trials:
        try:
            backend, case_id = trial.split(":", 1)
            if backend not in {"claude", "codex"} or case_id not in cases:
                raise ValueError(f"trial must select a proactive-live case: {trial}")
            case = cases[case_id]
            prompt = str(case.get("prompt", ""))
            if not prompt or any(term in prompt.lower() for term in FORBIDDEN_PROMPT_TERMS):
                raise ValueError(f"primed or empty prompt for {case_id}")
            executable = executable_paths.get(backend) or Path(shutil.which(backend) or "")
            if not executable.is_file():
                raise ValueError(f"{backend} executable unavailable")
            with tempfile.TemporaryDirectory(prefix="skill-improve-trigger-") as temporary:
                project = Path(temporary)
                if backend == "codex" and install_codex:
                    _install_codex(plugin_root, project, timeout_seconds)
                completed = subprocess.run(_command(backend, executable, plugin_root, prompt), cwd=project,
                                           capture_output=True, encoding="utf-8", errors="replace",
                                           timeout=timeout_seconds, check=False)
            if completed.returncode != 0:
                raise ValueError(f"{backend} child exited {completed.returncode}: {completed.stderr.strip()}")
            if "authentication" in (completed.stdout + completed.stderr).lower():
                raise ValueError(f"{backend} authentication failed")
            observed, response, model, selected_owner = _parse_stream(completed.stdout, backend)
            expected = str(case.get("expected", ""))
            expected_owner = case.get("expected_owner")
            revision, dirty = _git_metadata(plugin_root)
            trace = {
                "phase": phase, "backend": backend, "case_id": case_id, "expected": expected,
                "observed": observed, "selected_owner": selected_owner, "candidate_digest": digest,
                "candidate_file_count": file_count,
                "prompt_digest": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "cli_version": _version(executable, timeout_seconds), "reported_model": model,
                "captured_at_utc": datetime.now(UTC).isoformat(), "git_revision": revision,
                "git_dirty": dirty, "child_exit": completed.returncode,
            }
            (response_dir / f"resp-{case_id}.txt").write_text(response, encoding="utf-8")
            (response_dir / f"trace-{backend}-{case_id}.json").write_text(
                json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            if (phase == "candidate" and observed != expected) or (
                isinstance(expected_owner, str) and selected_owner != expected_owner
            ):
                all_ok = False
        except (OSError, ValueError, subprocess.TimeoutExpired) as error:
            print(f"ERROR: {trial}: {error}", file=sys.stderr)
            all_ok = False
    return 0 if all_ok else 1


def _verify_baseline(baseline_dir: Path, trials: list[str], candidate_digest: str) -> bool:
    traces = []
    try:
        for trial in trials:
            backend, case_id = trial.split(":", 1)
            traces.append(json.loads((baseline_dir / f"trace-{backend}-{case_id}.json").read_text(encoding="utf-8")))
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
    parser.add_argument("--evals-path", type=Path, required=True)
    parser.add_argument("--response-dir", type=Path, required=True)
    parser.add_argument("--baseline-dir", type=Path)
    parser.add_argument("--trial", action="append", required=True)
    args = parser.parse_args()
    if args.phase == "candidate" and args.baseline_dir is None:
        parser.error("--baseline-dir is required for candidate capture")
    return capture_trials(phase=args.phase, plugin_root=args.plugin_root.resolve(), evals_path=args.evals_path,
                          response_dir=args.response_dir, trials=args.trial, timeout_seconds=args.timeout_seconds,
                          baseline_dir=args.baseline_dir, install_codex=True)


if __name__ == "__main__":
    sys.exit(main())
