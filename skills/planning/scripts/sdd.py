#!/usr/bin/env python3
"""Plan workspaces, task briefs, review packages, consultation ledgers and plan validation.

One script, seven subcommands, one location rule — so a brief and the package that reviews it can
never land in different directories:

    python -X utf8 sdd.py workspace PLAN_FILE                  -> prints the plan's workspace
    python -X utf8 sdd.py brief     PLAN_FILE N                -> task N's text, to the workspace
    python -X utf8 sdd.py package   PLAN_FILE BASE HEAD        -> review diff, to the workspace
    python -X utf8 sdd.py validate  PLAN_FILE --max-tasks N [--profile gauntlet]
    python -X utf8 sdd.py acquire   PLAN_FILE --max-tasks N [--profile gauntlet]
    python -X utf8 sdd.py release   PLAN_FILE                 -> remove only that plan's lease
    python -X utf8 sdd.py consult reserve PLAN_FILE --request-json JSON
    python -X utf8 sdd.py consult record  PLAN_FILE --result-json JSON

Provenance: a port of the `sdd-workspace`, `task-brief` and `review-package` shell scripts of
obra/superpowers (MIT), rewritten on the Python standard library because this repository ships no
shell scripts — the Bash tool maps to PowerShell or cmd.exe on a share of the machines the plugin
installs on, where `awk`, `wc` and `$(...)` do not exist.

The workspace is `<git root>/.graph-powers/logs/sdd/<plan-slug>/`, one directory per plan, kept out
of `git status` by a self-ignoring `.gitignore` one level up. It lives in the working tree rather
than under `.git/` because agent writes there are denied, which would block an implementer from
writing its report. The slug is the plan file's stem — or its directory's name when the file is
`PLAN.md`, since one plan is one directory (`references/shared/007-path-conventions.md`).

`brief` accepts both task grammars: upstream's `### Task N` heading (any `#` depth) and this
harness's checkbox, `- [ ] **T2.1** — ...` with its indented fields. `validate` deliberately accepts
only that grammar plus structured `G*` phase gates: an unstructured or legacy plan is routed back
to `/plan` instead of being guessed.
Fenced blocks are skipped when matching, so a heading quoted inside a code sample never starts a
task.

What differs from upstream, and why: upstream's implementer commits after every task, so a review
package is `BASE..HEAD`. Here a task ends as a working-tree checkpoint and is committed only with the
user's approval in that turn (`references/safety-floor.md § 1`), so `BASE..HEAD` would usually be
empty. When HEAD names the checkout's own HEAD, `package` snapshots the working tree — untracked
files included — into a tree object through a temporary index and diffs BASE against that. The real
index, HEAD and every ref are untouched; only blob and tree objects are written, which is what
`git stash create` writes too. The snapshot id is printed and named inside the file, so the next fix
round packages `SNAPSHOT..HEAD` and the re-review sees only the fix.

Exit codes, as upstream: 0 done · 2 usage or bad input · 3 task not found. Consultation states
`USER_REQUIRED` and `BLOCKED` return 4 with their JSON result on stdout; all other failures are one
line on stderr.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, NoReturn

FENCE = re.compile(r"^\s*(```|~~~)")
TASK_HEADING = re.compile(r"^(#{1,6})[ \t]+Task[ \t]+([0-9][0-9.]*[A-Za-z]?)")
TASK_CHECKBOX = re.compile(
    r"^([ \t]*)[-*][ \t]+\[[ xX]\][ \t]+\**(?:Task[ \t]+|T)([0-9][0-9.]*[A-Za-z]?)"
)

# Phase B's structured task grammar. Keep this separate from TASK_CHECKBOX: brief is intentionally
# backwards-compatible, while validation must never silently infer fields from an old plan.
STRUCTURED_TASK = re.compile(
    r"^(?P<indent>[ \t]*)-[ \t]+\[(?P<checked>[ xX])\][ \t]+"
    r"\*\*(?P<id>T[0-9]+(?:\.[0-9]+)*[A-Za-z]?)\*\*[ \t]+—[ \t]+(?P<title>.+?)\s*$"
)
STRUCTURED_GATE = re.compile(
    r"^(?P<indent>[ \t]*)-[ \t]+\[(?P<checked>[ xX])\][ \t]+"
    r"\*\*(?P<id>G[0-9]+(?:\.[0-9]+)*[A-Za-z]?)\*\*[ \t]+—[ \t]+(?P<title>.+?)\s*$"
)
TASK_MARKER = re.compile(r"^(?P<indent>[ \t]*)-[ \t]+\[[ xX]\]")
MALFORMED_STRUCTURED = re.compile(r"^[ \t]*-[ \t]+\[[ xX]\][ \t]+\*\*T", re.IGNORECASE)
MALFORMED_GATE = re.compile(r"^[ \t]*-[ \t]+\[[ xX]\][ \t]+\*\*G", re.IGNORECASE)
FIELD = re.compile(r"^(?P<indent>[ \t]+)(?P<name>[A-Za-z][A-Za-z0-9_-]*):[ \t]*(?P<value>.*)$")
TIER_MARKER = re.compile(r"^[ \t]*\*\*Tier:\*\*", re.IGNORECASE)
TIER_FIELD = re.compile(
    r"^[ \t]*\*\*Tier:\*\*[ \t]*(?P<tier>L[1-6])(?:[ \t]*(?:·.*)?)$",
    re.IGNORECASE,
)
TASK_ID = re.compile(r"^T(?P<phase>[0-9]+)(?:\.[0-9]+)*[A-Za-z]?$")
SAFE_REF = re.compile(r"^(?:HEAD|[0-9A-Fa-f]{7,64})$")
NEED_REF = re.compile(
    r"(?P<id>T[0-9]+(?:\.[0-9]+)*[A-Za-z]?)\s*\(\s*reads\s*:\s*(?P<reads>[^()]*?\S)\s*\)",
    re.IGNORECASE,
)

AGENT_ID = re.compile(r"^graph-powers:(?P<slug>[a-z0-9][a-z0-9-]*)$")
SKILL_ID = re.compile(r"^(?:graph-powers:)?(?P<slug>[a-z0-9][a-z0-9-]*)$")
AGENTS_DIR = Path(__file__).resolve().parents[3] / "agents"
SKILLS_DIR = Path(__file__).resolve().parents[2]


def fail(message: str, code: int) -> NoReturn:
    print(message, file=sys.stderr)
    sys.exit(code)


def _agent_lane(agent: str) -> str:
    """Classify an agent from the canonical agent files, without duplicating their registry."""
    if agent == "main":
        return "human-chain"
    match = AGENT_ID.fullmatch(agent)
    if not match:
        return "unknown"
    agent_file = AGENTS_DIR / f"{match.group('slug')}.md"
    try:
        source = agent_file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "unknown"
    frontmatter = source.split("---", 2)
    if len(frontmatter) < 3:
        return "unknown"
    metadata = frontmatter[1]
    if not re.search(r"^role_type:\s*worker\s*$", metadata, re.MULTILINE):
        return "other"
    tools_match = re.search(r"^tools:\s*(.*)$", metadata, re.MULTILINE)
    denied_match = re.search(r"^disallowedTools:\s*(.*)$", metadata, re.MULTILINE)
    tools = {item.strip() for item in (tools_match.group(1) if tools_match else "").split(",")}
    denied = {item.strip() for item in (denied_match.group(1) if denied_match else "").split(",")}
    return (
        "routable"
        if {"Write", "Edit"}.issubset(tools) and not ({"Write", "Edit"} & denied)
        else "read-only"
    )


def _skill_is_routable(skill: str) -> bool:
    """Accept the explicit no-skill lane or a canonical bundled skill name."""
    if skill.lower() == "none":
        return True
    match = SKILL_ID.fullmatch(skill)
    return bool(match and (SKILLS_DIR / match.group("slug") / "SKILL.md").is_file())


def git(
    args: list[str], cwd: Path, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(  # NOSONAR -- fixed git argv; shell=False; variable refs validated.
            ["git", *args],
            cwd=str(cwd),
            env=env,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError:
        fail("git is not on PATH", 2)


def git_out(args: list[str], cwd: Path, env: dict[str, str] | None = None) -> str:
    done = git(args, cwd, env)
    if done.returncode != 0:
        detail = done.stderr.strip() or f"exit {done.returncode}"
        fail(f"git {' '.join(args)} failed: {detail}", 2)
    return done.stdout


def plan_file(raw: str) -> Path:
    plan = Path(raw)
    if not plan.is_file():
        fail(f"no such plan file: {raw}", 2)
    return plan.resolve()


def repo_root(plan: Path) -> Path:
    done = git(["rev-parse", "--show-toplevel"], plan.parent)
    if done.returncode != 0:
        fail(f"not inside a git repository: {plan}", 2)
    return Path(done.stdout.strip()).resolve()


def plan_slug(plan: Path) -> str:
    slug = plan.parent.name if plan.name.lower() == "plan.md" else plan.stem
    if slug in {"", ".", ".."}:
        fail(f"cannot derive a workspace name from: {plan}", 2)
    return slug


def _secure_directory(root: Path, *parts: str) -> Path:
    """Create one repository-local directory chain while refusing every symlink component."""
    root = root.resolve()
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink():
            fail(f"refusing symlink in SDD state path: {current.as_posix()}", 2)
        try:
            current.mkdir()
        except FileExistsError:
            if current.is_symlink():
                fail(f"refusing symlink in SDD state path: {current.as_posix()}", 2)
            if not current.is_dir():
                fail(f"SDD state path is not a directory: {current.as_posix()}", 2)
        try:
            current.resolve().relative_to(root)
        except ValueError:
            fail(f"SDD state path escapes the repository: {current.as_posix()}", 2)
    return current


def _existing_secure_directory(root: Path, *parts: str) -> Path | None:
    """Resolve an existing state directory without creating or following symlink components."""
    root = root.resolve()
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink():
            fail(f"refusing symlink in SDD state path: {current.as_posix()}", 2)
        if not current.exists():
            return None
        if not current.is_dir():
            fail(f"SDD state path is not a directory: {current.as_posix()}", 2)
        try:
            current.resolve().relative_to(root)
        except ValueError:
            fail(f"SDD state path escapes the repository: {current.as_posix()}", 2)
    return current


def _write_text_no_symlink(target: Path, text: str, *, exclusive: bool = False) -> None:
    """Write state without following a symlink; publish exclusive files only when complete."""
    if target.is_symlink():
        fail(f"refusing symlink SDD output: {target.as_posix()}", 2)
    if exclusive:
        try:
            descriptor, staging_name = tempfile.mkstemp(
                dir=target.parent,
                prefix=f".{target.name}.",
                suffix=".tmp",
                text=True,
            )
        except OSError as error:
            fail(f"cannot stage SDD state {target.as_posix()}: {error}", 2)
        staging = Path(staging_name)
        try:
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                    handle.write(text)
                    handle.flush()
                    os.fsync(handle.fileno())
            except OSError as error:
                fail(f"cannot write SDD state {target.as_posix()}: {error}", 2)
            try:
                os.link(staging, target)
            except FileExistsError:
                raise
            except OSError as error:
                fail(f"cannot publish SDD state {target.as_posix()}: {error}", 2)
        finally:
            try:
                staging.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                # The canonical path is either absent or already complete; stale staging cannot
                # impersonate the lease and must not turn a successful acquisition into failure.
                pass
        return

    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(target, flags, 0o600)
    except FileExistsError:
        raise
    except OSError as error:
        fail(f"cannot write SDD state {target.as_posix()}: {error}", 2)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def workspace(plan: Path) -> Path:
    root = repo_root(plan)
    directory = _secure_directory(root, ".graph-powers", "logs", "sdd", plan_slug(plan))
    base = directory.parent
    ignore = base / ".gitignore"
    if ignore.is_symlink():
        fail(f"refusing symlink SDD output: {ignore.as_posix()}", 2)
    if not ignore.is_file() or ignore.read_text(encoding="utf-8") != "*\n":
        _write_text_no_symlink(ignore, "*\n")
    return directory


CONSULTATION_FIELDS = (
    "taskId",
    "decisionKey",
    "question",
    "evidence",
    "options",
    "recommendation",
    "risk",
    "verdict",
    "requesterRole",
    "depth",
    "backend",
    "capabilityStatus",
    "status",
)
CONSULTATION_STATUSES = {"RESERVED", "RECORDED", "USER_REQUIRED", "BLOCKED"}
CAPABILITY_STATUSES = {"SUPPORTED", "UNSUPPORTED", "UNKNOWN", "UNAVAILABLE", "FALLBACK_UNAVAILABLE"}
IDENTITY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
DECISION_KEY = re.compile(r"^[a-z0-9][a-z0-9._:-]{0,127}$")
CONSULTATION_BACKENDS = {"evaluator", "fable", "advisor"}
MAX_CONSULTATION_TEXT = 4096
MAX_CONSULTATION_ITEM = 2048
MAX_CONSULTATION_OPTIONS = 32
CONSULTATION_EXIT = 4


def _consultation_error(message: str) -> NoReturn:
    fail(f"consultation: {message}", 2)


def _bounded_text(value: Any, name: str, limit: int = MAX_CONSULTATION_TEXT) -> str:
    if not isinstance(value, str) or not value.strip():
        _consultation_error(f"{name} must be a non-empty string")
    value = value.strip()
    if len(value) > limit:
        _consultation_error(f"{name} exceeds {limit} characters")
    return value


def _bounded_list(value: Any, name: str) -> list[str]:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list) or not value or len(value) > MAX_CONSULTATION_OPTIONS:
        _consultation_error(f"{name} must contain 1-{MAX_CONSULTATION_OPTIONS} items")
    result: list[str] = []
    for item in value:
        result.append(_bounded_text(item, f"{name} item", MAX_CONSULTATION_ITEM))
    return result


def _validate_consultation_envelope(raw: Any, action: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        _consultation_error("envelope must be a JSON object")
    missing = [field for field in CONSULTATION_FIELDS if field not in raw]
    if missing:
        _consultation_error(f"missing required field(s): {', '.join(missing)}")
    task = raw["taskId"]
    if not isinstance(task, str) or not IDENTITY.fullmatch(task):
        _consultation_error("taskId must be a bounded stable identifier")
    decision = raw["decisionKey"]
    if not isinstance(decision, str) or not DECISION_KEY.fullmatch(decision):
        _consultation_error("decisionKey must be a bounded lowercase stable key, never prompt text")
    question = _bounded_text(raw["question"], "question")
    evidence = _bounded_list(raw["evidence"], "evidence")
    options = _bounded_list(raw["options"], "options")
    recommendation = _bounded_text(raw["recommendation"], "recommendation")
    risk = _bounded_text(raw["risk"], "risk")
    role = raw["requesterRole"]
    if not isinstance(role, str) or role.strip().lower() not in {"parent", "controller"}:
        _consultation_error(
            "requesterRole must be parent or controller; evaluator/reviewer/critic cannot consult"
        )
    depth = raw["depth"]
    if isinstance(depth, bool) or not isinstance(depth, int) or depth != 0:
        _consultation_error("depth must be exactly 0; nested consultation is forbidden")
    backend = raw["backend"]
    if not isinstance(backend, str) or backend.strip().lower() not in CONSULTATION_BACKENDS:
        _consultation_error("backend must be evaluator, fable, or advisor")
    capability = raw["capabilityStatus"]
    if not isinstance(capability, str) or capability.strip().upper() not in CAPABILITY_STATUSES:
        _consultation_error(
            f"capabilityStatus must be one of {', '.join(sorted(CAPABILITY_STATUSES))}"
        )
    verdict = raw["verdict"]
    status = raw["status"]
    if not isinstance(verdict, str) or not verdict.strip():
        _consultation_error("verdict must be a non-empty string")
    if not isinstance(status, str) or status.strip().upper() not in CONSULTATION_STATUSES:
        _consultation_error(f"status must be one of {', '.join(sorted(CONSULTATION_STATUSES))}")
    normalized_status = status.strip().upper()
    if action == "reserve" and normalized_status not in {"RESERVED", "BLOCKED"}:
        _consultation_error("reserve requires status RESERVED or BLOCKED")
    if action == "record" and normalized_status not in {"RECORDED", "BLOCKED", "USER_REQUIRED"}:
        _consultation_error("record requires status RECORDED, BLOCKED, or USER_REQUIRED")
    if (
        action == "reserve"
        and normalized_status == "RESERVED"
        and verdict.strip().upper() not in {"PENDING", "RESERVED"}
    ):
        _consultation_error("a new reservation must have verdict PENDING")
    if (
        action == "record"
        and normalized_status == "RECORDED"
        and verdict.strip().upper() == "PENDING"
    ):
        _consultation_error("a recorded result cannot have verdict PENDING")
    if (
        normalized_status in {"BLOCKED", "USER_REQUIRED"}
        and verdict.strip().upper() != normalized_status
    ):
        _consultation_error(f"{normalized_status} requires matching verdict")
    return {
        "taskId": task,
        "decisionKey": decision,
        "question": question,
        "evidence": evidence,
        "options": options,
        "recommendation": recommendation,
        "risk": risk,
        "verdict": verdict.strip(),
        "requesterRole": role.strip().lower(),
        "depth": 0,
        "backend": backend.strip().lower(),
        "capabilityStatus": capability.strip().upper(),
        "status": normalized_status,
    }


def _consultation_route(envelope: dict[str, Any]) -> tuple[str, bool, str | None]:
    """Resolve only declared capability metadata; never probe a provider or harness."""
    backend = envelope["backend"]
    capability = envelope["capabilityStatus"]
    if backend in {"fable", "advisor"}:
        if capability == "SUPPORTED":
            return backend, False, None
        if capability in {"UNSUPPORTED", "UNKNOWN"}:
            return "evaluator", True, None
        return (
            "evaluator",
            True,
            "requested native capability and its read-only fallback are unavailable",
        )
    if capability in {"UNAVAILABLE", "FALLBACK_UNAVAILABLE"}:
        return "evaluator", False, "the requested strong evaluator is unavailable"
    return "evaluator", False, None


def _consultation_output(
    envelope: dict[str, Any],
    *,
    status: str,
    backend: str | None = None,
    fallback: bool = False,
    reason: str | None = None,
) -> dict[str, Any]:
    output = dict(envelope)
    output["backend"] = backend or envelope["backend"]
    output["status"] = status
    output["verdict"] = status if status in {"BLOCKED", "USER_REQUIRED"} else envelope["verdict"]
    output["fallback"] = fallback
    if reason:
        output["reason"] = reason
    return output


def _read_consultation_ledger(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        fail(f"refusing symlink consultation ledger: {path.as_posix()}", 2)
    if not path.exists():
        return {"version": 1, "tasks": {}}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        fail(f"cannot read consultation ledger {path.as_posix()}: {error}", 2)
    if (
        not isinstance(value, dict)
        or value.get("version") != 1
        or not isinstance(value.get("tasks"), dict)
    ):
        fail(f"invalid consultation ledger: {path.as_posix()}", 2)
    return value


def _write_consultation_ledger(path: Path, value: dict[str, Any]) -> None:
    if path.is_symlink():
        fail(f"refusing symlink consultation ledger: {path.as_posix()}", 2)
    encoded = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    try:
        descriptor, staging_name = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            text=True,
        )
        staging = Path(staging_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(staging, path)
            try:
                directory_descriptor = os.open(path.parent, os.O_RDONLY)
            except OSError:
                directory_descriptor = -1
            if directory_descriptor >= 0:
                try:
                    os.fsync(directory_descriptor)
                finally:
                    os.close(directory_descriptor)
        finally:
            try:
                staging.unlink()
            except FileNotFoundError:
                pass
    except OSError as error:
        fail(f"cannot publish consultation ledger {path.as_posix()}: {error}", 2)


@contextmanager
def _consultation_lock(directory: Path) -> Iterator[None]:
    lock = directory / "consultations.lock"
    deadline = time.monotonic() + 5
    descriptor = -1
    while True:
        if lock.is_symlink():
            fail(f"refusing symlink consultation lock: {lock.as_posix()}", 2)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(lock, flags, 0o600)
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                fail("consultation ledger lock timeout", CONSULTATION_EXIT)
            time.sleep(0.01)
        except OSError as error:
            fail(f"cannot acquire consultation ledger lock: {error}", 2)
    try:
        os.close(descriptor)
        yield
    finally:
        try:
            lock.unlink()
        except FileNotFoundError:
            pass
        except OSError as error:
            fail(f"cannot release consultation ledger lock: {error}", 2)


def _consultation_result_code(output: dict[str, Any]) -> int:
    return CONSULTATION_EXIT if output["status"] in {"USER_REQUIRED", "BLOCKED"} else 0


def consult(plan: Path, action: str, raw_json: str) -> tuple[dict[str, Any], int]:
    if action == "record":
        return record_consultation(plan, raw_json)
    try:
        raw = json.loads(raw_json)
    except (TypeError, ValueError) as error:
        _consultation_error(f"invalid JSON envelope: {error}")
    envelope = _validate_consultation_envelope(raw, action)
    backend, fallback, route_reason = _consultation_route(envelope)
    if route_reason:
        envelope = _consultation_output(
            envelope,
            status="BLOCKED",
            backend=backend,
            fallback=fallback,
            reason=route_reason,
        )
    else:
        envelope = _consultation_output(
            envelope,
            status="RESERVED",
            backend=backend,
            fallback=fallback,
        )
    directory = workspace(plan)
    ledger_path = directory / "consultations.json"
    with _consultation_lock(directory):
        ledger = _read_consultation_ledger(ledger_path)
        tasks = ledger["tasks"]
        task_decisions = tasks.setdefault(envelope["taskId"], {})
        existing = task_decisions.get(envelope["decisionKey"])
        if existing is not None:
            if not isinstance(existing, dict):
                fail("invalid consultation record", 2)
            return existing, _consultation_result_code(existing)
        if len(task_decisions) >= 3:
            return _consultation_output(
                envelope,
                status="USER_REQUIRED",
                fallback=fallback,
                reason="consultation cap reached; parent must ask the user",
            ), CONSULTATION_EXIT
        task_decisions[envelope["decisionKey"]] = envelope
        _write_consultation_ledger(ledger_path, ledger)
        return envelope, _consultation_result_code(envelope)


def record_consultation(plan: Path, raw_json: str) -> tuple[dict[str, Any], int]:
    try:
        raw = json.loads(raw_json)
    except (TypeError, ValueError) as error:
        _consultation_error(f"invalid JSON envelope: {error}")
    envelope = _validate_consultation_envelope(raw, "record")
    directory = workspace(plan)
    ledger_path = directory / "consultations.json"
    with _consultation_lock(directory):
        ledger = _read_consultation_ledger(ledger_path)
        tasks = ledger["tasks"]
        task_decisions = tasks.get(envelope["taskId"], {})
        existing = task_decisions.get(envelope["decisionKey"])
        if existing is None:
            _consultation_error("record requires a prior reservation for this decisionKey")
        if existing["status"] != "RESERVED":
            return existing, _consultation_result_code(existing)
        if (
            envelope["backend"] != existing["backend"]
            or envelope["capabilityStatus"] != existing["capabilityStatus"]
        ):
            _consultation_error("record identity does not match its reservation")
        envelope["backend"] = existing["backend"]
        envelope["fallback"] = existing.get("fallback", False)
        task_decisions[envelope["decisionKey"]] = envelope
        _write_consultation_ledger(ledger_path, ledger)
        return envelope, _consultation_result_code(envelope)


def task_id(raw: str) -> str:
    """`3`, `2.1`, `T2.1` and `Task 3` all name the same task."""
    wanted = raw.strip()
    lowered = wanted.lower()
    if lowered.startswith("task"):
        wanted = wanted[4:].strip()
    elif lowered.startswith("t") and len(wanted) > 1 and wanted[1].isdigit():
        wanted = wanted[1:]
    return wanted.rstrip(".")


def extract_task(lines: list[str], wanted: str) -> list[str]:
    """The lines of one task, or an empty list.

    A heading task runs to the next heading of the same or shallower depth, or the next task
    heading of any depth. A checkbox task runs to the first non-blank line indented no deeper than
    the checkbox itself — the fields below it are indented, the next task is not.
    """
    out: list[str] = []
    in_fence = False
    mode = ""
    depth = 0
    indent = 0
    for line in lines:
        if FENCE.match(line):
            in_fence = not in_fence
            if mode:
                out.append(line)
            continue
        if in_fence:
            if mode:
                out.append(line)
            continue
        heading = TASK_HEADING.match(line)
        checkbox = TASK_CHECKBOX.match(line)
        if mode == "heading":
            other_heading = line.startswith("#") and len(line) - len(line.lstrip("#")) <= depth
            if heading or other_heading:
                break
        elif mode == "checkbox":
            if line.strip() and len(line) - len(line.lstrip(" \t")) <= indent:
                break
        elif heading and heading.group(2).rstrip(".") == wanted:
            mode, depth = "heading", len(heading.group(1))
        elif checkbox and checkbox.group(2).rstrip(".") == wanted:
            mode, indent = "checkbox", len(checkbox.group(1))
        else:
            continue
        out.append(line)
    while out and not out[-1].strip():
        out.pop()
    return out


def brief(plan: Path, number: str) -> None:
    wanted = task_id(number)
    lines = plan.read_text(encoding="utf-8", errors="replace").splitlines()
    section = extract_task(lines, wanted)
    if not section:
        fail(
            f"task {number} not found in {plan.as_posix()} "
            f"(no heading 'Task {wanted}' and no checkbox 'T{wanted}')",
            3,
        )
    target = workspace(plan) / f"task-{wanted}-brief.md"
    _write_text_no_symlink(target, "\n".join(section) + "\n")
    print(f"wrote {target.as_posix()}: {len(section)} lines")


def _visible_plan_lines(lines: list[str]) -> list[tuple[int, str]]:
    """Return non-fenced lines with their one-based source line numbers."""
    visible: list[tuple[int, str]] = []
    in_fence = False
    for number, line in enumerate(lines, 1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            visible.append((number, line))
    return visible


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == "`":
        return value[1:-1].strip()
    return value


def _is_placeholder(value: str) -> bool:
    """Recognize an unexpanded plan field without rejecting real shell syntax inside a command."""
    normalized = _unquote(value).strip()
    return normalized.lower() in {"pending", "tbd", "todo"} or bool(
        re.fullmatch(r"<[^<>]+>", normalized)
    )


def _is_unobservable_acceptance(value: str) -> bool:
    """Reject the documented vague outcomes only in the stricter Gauntlet profile."""
    return _unquote(value).strip().lower() in {
        "looks correct",
        "looks good",
        "seems correct",
        "seems fine",
        "works",
        "funciona",
        "está correto",
        "parece correto",
    }


def _owns(value: str, task: str, errors: list[str]) -> list[str]:
    """Parse and normalize repository-relative ownership paths."""
    raw = _unquote(value)
    if not raw or raw.lower() == "none":
        errors.append(f"{task}: Owns must name at least one path")
        return []
    paths: list[str] = []
    for item in re.split(r"\s*(?:,|;|\|)\s*", raw):
        raw_path = _unquote(item)
        if not raw_path:
            errors.append(f"{task}: Owns contains an empty path")
            continue
        portable_path = PurePosixPath(raw_path.replace("\\", "/"))
        windows_path = PureWindowsPath(raw_path)
        if portable_path.is_absolute() or windows_path.is_absolute() or windows_path.drive:
            errors.append(f"{task}: Owns path must be repository-relative: {raw_path}")
            continue
        parts = portable_path.parts
        if portable_path == PurePosixPath(".") or not parts or ".." in parts:
            errors.append(f"{task}: Owns path escapes the repository: {raw_path}")
            continue
        normalized = PurePosixPath(*parts).as_posix()
        if normalized in paths:
            errors.append(f"{task}: duplicate Owns path: {normalized}")
        else:
            paths.append(normalized)
    return sorted(paths)


def _needs(value: str, task: str, errors: list[str]) -> list[dict[str, str]]:
    """Parse Needs edges, requiring a named ``reads`` payload on every edge."""
    raw = _unquote(value)
    if raw.strip().lower() == "none":
        return []
    matches = list(NEED_REF.finditer(raw))
    if not matches:
        errors.append(f"{task}: every Needs edge must include (reads: <payload>)")
        return []
    remainder = NEED_REF.sub("", raw)
    remainder = re.sub(r"[\s,;|]+", "", remainder)
    if remainder:
        errors.append(f"{task}: malformed Needs value: {raw}")
    result: list[dict[str, str]] = []
    for match in matches:
        result.append({"id": match.group("id"), "reads": match.group("reads").strip()})
    return result


def _structured_blocks(
    visible: list[tuple[int, str]],
    pattern: re.Pattern[str],
    malformed: re.Pattern[str],
    label: str,
    example: str,
) -> tuple[list[tuple[int, str, list[tuple[int, str]]]], list[str]]:
    """Find one kind of structured checkbox block without field bleed."""
    starts: list[tuple[int, int, str]] = []
    errors: list[str] = []
    for index, (line_no, line) in enumerate(visible):
        match = pattern.match(line)
        if match:
            starts.append((index, line_no, match.group("id")))
        elif malformed.match(line):
            errors.append(f"line {line_no}: malformed structured {label}; use '{example}'")
    blocks: list[tuple[int, str, list[tuple[int, str]]]] = []
    for position, (index, line_no, task_id_value) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(visible)
        header = pattern.match(visible[index][1])
        assert header is not None
        block_indent = len(header.group("indent"))
        # A peer checkbox ends the preceding block. Nested checklist steps remain part of it.
        # Fields still cannot bleed through a boundary when a plan omits a blank line.
        for candidate in range(index + 1, end):
            marker = TASK_MARKER.match(visible[candidate][1])
            if marker and len(marker.group("indent")) <= block_indent:
                end = candidate
                break
        blocks.append((line_no, task_id_value, visible[index:end]))
    return blocks, errors


def _task_blocks(
    visible: list[tuple[int, str]],
) -> tuple[list[tuple[int, str, list[tuple[int, str]]]], list[str]]:
    blocks, errors = _structured_blocks(
        visible, STRUCTURED_TASK, MALFORMED_STRUCTURED, "task", "- [ ] **T1.1** — title"
    )
    if not blocks:
        if any(TASK_MARKER.match(line) for _, line in visible):
            errors.append(
                "legacy or unstructured plan: route to /plan and regenerate the structured task grammar"
            )
        else:
            errors.append("plan contains no structured tasks: route to /plan")
    return blocks, errors


def _gate_blocks(
    visible: list[tuple[int, str]],
) -> tuple[list[tuple[int, str, list[tuple[int, str]]]], list[str]]:
    blocks, errors = _structured_blocks(
        visible, STRUCTURED_GATE, MALFORMED_GATE, "gate", "- [ ] **G1.1** — title"
    )
    if not blocks:
        errors.append("plan is missing structured gate blocks: route to /plan")
    return blocks, errors


def _parse_task(
    block: tuple[int, str, list[tuple[int, str]]],
    errors: list[str],
    profile: str,
) -> dict[str, Any]:
    line_no, task_id_value, lines = block
    header = STRUCTURED_TASK.match(lines[0][1])
    assert header is not None
    fields: dict[str, str] = {}
    steps: list[str] = []
    task_indent = len(header.group("indent"))
    in_steps = False
    steps_indent: int | None = None
    for _source_line, line in lines[1:]:
        field = FIELD.match(line)
        if (
            in_steps
            and line.strip()
            and (field is None or steps_indent is None or len(field.group("indent")) > steps_indent)
        ):
            steps.append(line.strip())
            continue
        if field and len(field.group("indent")) > task_indent:
            name = field.group("name").lower()
            value = field.group("value").strip()
            if name in fields and name != "steps":
                errors.append(f"{task_id_value}: duplicate field {field.group('name')}")
            elif name == "steps":
                if "steps" in fields:
                    errors.append(f"{task_id_value}: duplicate field Steps")
                fields["steps"] = value
                in_steps = True
                steps_indent = len(field.group("indent"))
                if value:
                    steps.append(value)
            else:
                fields[name] = value
                in_steps = False
                steps_indent = None
            continue
        if in_steps and line.strip():
            steps.append(line.strip())

    # The documented compact form puts Agent, Skill and Effort on one line. Expand it before
    # checking required fields so the compact and one-field-per-line forms validate identically.
    if "agent" in fields and "·" in fields["agent"]:
        parts = [part.strip() for part in fields["agent"].split("·")]
        fields["agent"] = parts[0]
        for part in parts[1:]:
            match = re.match(r"Skill:\s*(.*)$", part, re.IGNORECASE)
            if match:
                fields["skill"] = match.group(1).strip()
            match = re.match(r"Effort:\s*(.*)$", part, re.IGNORECASE)
            if match:
                fields["effort"] = match.group(1).strip()

    required = ("owns", "needs", "agent", "skill", "effort", "check", "expect", "evidence", "tdd")
    if profile == "gauntlet":
        required = (*required, "acceptance")
    for name in required:
        if not fields.get(name, "").strip():
            errors.append(f"{task_id_value}: missing required field {name.title()}")
    title = header.group("title").strip()
    if not title or title.lower() in {"tbd", "todo"}:
        errors.append(f"{task_id_value}: task title is empty or a placeholder")
    owns = _owns(fields.get("owns", ""), task_id_value, errors) if "owns" in fields else []
    needs = _needs(fields.get("needs", ""), task_id_value, errors) if "needs" in fields else []
    tdd = _unquote(fields.get("tdd", "")).strip()
    tdd_match = re.match(
        r"^(required|not-applicable|exception-approved)(?:\s*\(([^)]*)\))?$", tdd, re.IGNORECASE
    )
    if tdd and not tdd_match:
        errors.append(
            f"{task_id_value}: TDD must be required, not-applicable (<reason>) or exception-approved (<reason>)"
        )
    elif (
        tdd_match
        and tdd_match.group(1).lower() != "required"
        and not (tdd_match.group(2) or "").strip()
    ):
        errors.append(f"{task_id_value}: {tdd_match.group(1)} requires a reason")
    if tdd_match and tdd_match.group(1).lower() == "required":
        step_text = " ".join(steps)
        if not re.search(r"\bRED\b", step_text, re.IGNORECASE):
            errors.append(f"{task_id_value}: TDD required but Steps has no RED step")
        if not re.search(r"\bGREEN\b", step_text, re.IGNORECASE):
            errors.append(f"{task_id_value}: TDD required but Steps has no GREEN step")
    for field_name in ("acceptance", "check", "expect"):
        if fields.get(field_name) and _is_placeholder(fields[field_name]):
            errors.append(f"{task_id_value}: {field_name.title()} is a placeholder")
    if (
        profile == "gauntlet"
        and fields.get("acceptance")
        and _is_unobservable_acceptance(fields["acceptance"])
    ):
        errors.append(f"{task_id_value}: Acceptance is not observable")
    if fields.get("agent", "").strip() and not steps and fields["agent"].strip().lower() != "main":
        errors.append(f"{task_id_value}: subagent task requires Steps")

    agent = fields.get("agent", "")
    normalized_agent = _unquote(agent)
    lane = _agent_lane(normalized_agent) if normalized_agent else "unknown"
    if lane == "human-chain":
        errors.append(f"{task_id_value}: Agent main is not routable in Phase C")
    elif normalized_agent and lane == "unknown":
        errors.append(f"{task_id_value}: unknown Agent {normalized_agent}")
    elif normalized_agent and lane == "read-only":
        if profile == "gauntlet":
            errors.append(
                f"{task_id_value}: Agent {normalized_agent} is not a write-capable Phase C lane"
            )
    elif normalized_agent and lane != "routable":
        errors.append(f"{task_id_value}: Agent {normalized_agent} is not routable in Phase C")
    skill = _unquote(fields.get("skill", "")).strip()
    if profile == "gauntlet" and skill and not _skill_is_routable(skill):
        errors.append(f"{task_id_value}: unknown Skill {skill}")
    effort = fields.get("effort", "")
    task: dict[str, Any] = {
        "id": task_id_value,
        "title": title,
        "checked": header.group("checked").lower() == "x",
        "owns": owns,
        "needs": [edge["id"] for edge in needs],
        "reads": {edge["id"]: edge["reads"] for edge in needs},
        "acceptance": _unquote(fields.get("acceptance", "")),
        "agent": normalized_agent,
        "skill": skill,
        "effort": _unquote(effort),
        "check": _unquote(fields.get("check", "")),
        "expect": _unquote(fields.get("expect", "")),
        "evidence": _unquote(fields.get("evidence", "")),
        "tdd": tdd,
        "steps": steps,
        "line": line_no,
    }
    if "risk" in fields:
        task["risk"] = _unquote(fields["risk"])
    if task["checked"]:
        if task["evidence"].strip().lower() == "pending":
            errors.append(f"{task_id_value}: checked task still has EVIDENCE pending")
        if tdd_match and tdd_match.group(1).lower() == "required":
            evidence = task["evidence"]
            if not (
                re.search(r"\bRED\b", evidence, re.IGNORECASE)
                and re.search(r"\bGREEN\b", evidence, re.IGNORECASE)
            ):
                errors.append(
                    f"{task_id_value}: checked TDD task is missing observed RED/GREEN evidence"
                )
    return task


def _parse_gate(block: tuple[int, str, list[tuple[int, str]]], errors: list[str]) -> dict[str, Any]:
    """Validate one executable phase-gate claim."""
    line_no, gate_id_value, lines = block
    header = STRUCTURED_GATE.match(lines[0][1])
    assert header is not None
    gate_indent = len(header.group("indent"))
    fields: dict[str, str] = {}
    for _source_line, line in lines[1:]:
        field = FIELD.match(line)
        if field and len(field.group("indent")) > gate_indent:
            name = field.group("name").lower()
            if name in fields:
                errors.append(f"{gate_id_value}: duplicate field {field.group('name')}")
            else:
                fields[name] = field.group("value").strip()
    for name in ("check", "expect", "evidence"):
        if not fields.get(name, "").strip():
            errors.append(f"{gate_id_value}: missing required field {name.title()}")
    for field_name in ("check", "expect"):
        if fields.get(field_name) and _is_placeholder(fields[field_name]):
            errors.append(f"{gate_id_value}: {field_name.title()} is a placeholder")
    title = header.group("title").strip()
    if not title or title.lower() in {"tbd", "todo"}:
        errors.append(f"{gate_id_value}: gate title is empty or a placeholder")
    checked = header.group("checked").lower() == "x"
    evidence = _unquote(fields.get("evidence", ""))
    if checked and evidence.strip().lower() == "pending":
        errors.append(f"{gate_id_value}: checked gate still has EVIDENCE pending")
    phase_match = re.match(r"^G(?P<phase>[0-9]+)", gate_id_value)
    assert phase_match is not None
    return {
        "id": gate_id_value,
        "phase": phase_match.group("phase"),
        "title": title,
        "checked": checked,
        "check": _unquote(fields.get("check", "")),
        "expect": _unquote(fields.get("expect", "")),
        "evidence": evidence,
        "line": line_no,
    }


def _reachable(source: str, target: str, edges: dict[str, set[str]]) -> bool:
    pending = list(edges.get(source, set()))
    visited: set[str] = set()
    while pending:
        current = pending.pop()
        if current == target:
            return True
        if current not in visited:
            visited.add(current)
            pending.extend(edges.get(current, set()))
    return False


def _plan_tier(visible: list[tuple[int, str]], errors: list[str]) -> str:
    """Return the one mechanically routable L1-L6 tier declared by Phase B."""
    candidates = [(line_no, line) for line_no, line in visible if TIER_MARKER.match(line)]
    if not candidates:
        errors.append("plan is missing required Tier (`**Tier:** L<n>`): route to /plan")
        return ""
    if len(candidates) > 1:
        errors.append("plan has multiple Tier fields: route to /plan")
        return ""
    line_no, line = candidates[0]
    match = TIER_FIELD.fullmatch(line)
    if not match:
        errors.append(
            f"line {line_no}: malformed Tier; expected `**Tier:** L1` through `L6`: route to /plan"
        )
        return ""
    return match.group("tier").upper()


def validate_plan(
    plan: Path,
    max_tasks: int,
    profile: str = "default",
) -> tuple[dict[str, Any] | None, list[str]]:
    """Validate Phase B's structured plan and return its tiered execution graph."""
    errors: list[str] = []
    if max_tasks < 1:
        return None, ["--max-tasks must be a positive integer"]
    lines = plan.read_text(encoding="utf-8", errors="replace").splitlines()
    visible = _visible_plan_lines(lines)
    blocks, errors = _task_blocks(visible)
    if not blocks:
        return None, errors
    tier = _plan_tier(visible, errors)
    gate_blocks, gate_errors = _gate_blocks(visible)
    errors.extend(gate_errors)
    if len(blocks) > max_tasks:
        errors.append(f"plan has {len(blocks)} tasks, exceeding --max-tasks {max_tasks}")
    tasks = [_parse_task(block, errors, profile) for block in blocks]
    gates = [_parse_gate(block, errors) for block in gate_blocks]
    ids = [task["id"] for task in tasks]
    if len(ids) != len(set(ids)):
        duplicates = sorted({item for item in ids if ids.count(item) > 1})
        errors.append(f"duplicate task id(s): {', '.join(duplicates)}")
    gate_ids = [gate["id"] for gate in gates]
    if len(gate_ids) != len(set(gate_ids)):
        duplicates = sorted({item for item in gate_ids if gate_ids.count(item) > 1})
        errors.append(f"duplicate gate id(s): {', '.join(duplicates)}")
    task_phase_matches = [TASK_ID.fullmatch(task["id"]) for task in tasks]
    assert all(match is not None for match in task_phase_matches)
    task_phases = {match.group("phase") for match in task_phase_matches if match is not None}
    gate_phases = {gate["phase"] for gate in gates}
    for phase in sorted(task_phases - gate_phases, key=int):
        errors.append(f"phase {phase}: missing structured gate")
    by_id = {task["id"]: task for task in tasks}
    edges = {task["id"]: set(task["needs"]) for task in tasks}
    for task in tasks:
        for dependency in task["needs"]:
            if dependency not in by_id:
                errors.append(f"{task['id']}: unknown dependency {dependency}")
    state: dict[str, int] = {}

    def visit(node: str, stack: list[str]) -> None:
        if state.get(node) == 1:
            cycle = " -> ".join([*stack, node])
            errors.append(f"dependency cycle: {cycle}")
            return
        if state.get(node) == 2:
            return
        state[node] = 1
        for dependency in edges.get(node, set()):
            if dependency in by_id:
                visit(dependency, [*stack, node])
        state[node] = 2

    for task_id_value in ids:
        visit(task_id_value, [])
    for index, left in enumerate(tasks):
        for right in tasks[index + 1 :]:
            overlap = sorted(
                {
                    a
                    for a in left["owns"]
                    for b in right["owns"]
                    if a == b or a.startswith(b + "/") or b.startswith(a + "/")
                }
            )
            if overlap and not (
                _reachable(left["id"], right["id"], edges)
                or _reachable(right["id"], left["id"], edges)
            ):
                errors.append(
                    f"concurrent Owns conflict: {left['id']} and {right['id']} overlap {', '.join(overlap)}"
                )
    if errors:
        return None, errors
    lease = sorted({path for task in tasks for path in task["owns"]})
    return {"tier": tier, "tasks": tasks, "gates": gates, "writeLease": lease}, []


def _relative_plan(plan: Path, root: Path) -> str:
    try:
        return plan.relative_to(root).as_posix()
    except ValueError:
        fail(f"plan is outside the repository: {plan.as_posix()}", 2)


def _read_lease(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        fail(f"refusing symlink write lease: {path.as_posix()}", 2)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        fail(f"cannot read existing write lease {path.as_posix()}: {error}", 2)
    if (
        not isinstance(value, dict)
        or not isinstance(value.get("plan"), str)
        or not isinstance(value.get("paths"), list)
    ):
        fail(f"invalid existing write lease: {path.as_posix()}", 2)
    return value


def acquire(plan: Path, max_tasks: int, profile: str = "default") -> dict[str, Any]:
    """Validate the plan and create its write lease with an atomic create-if-absent."""
    normalized, errors = validate_plan(plan, max_tasks, profile)
    if errors:
        fail("plan validation failed: " + "; ".join(errors), 2)
    assert normalized is not None
    root = repo_root(plan)
    relative_plan = _relative_plan(plan, root)
    logs = _secure_directory(root, ".graph-powers", "logs")
    lease_path = logs / "write-lease.json"
    state_paths = [
        relative_plan,
        ".graph-powers/logs/progress.md",
        f".graph-powers/logs/sdd/{plan_slug(plan)}/task-reviews.md",
    ]
    paths = sorted({*normalized["writeLease"], *state_paths})
    payload = {"plan": relative_plan, "paths": paths}
    encoded = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    try:
        _write_text_no_symlink(lease_path, encoded, exclusive=True)
    except FileExistsError:
        existing = _read_lease(lease_path)
        if existing != payload:
            fail(
                f"write lease conflict: {existing['plan']} already owns {lease_path.as_posix()}", 2
            )
    return normalized


def release(plan: Path) -> None:
    """Remove the active lease only when this exact canonical plan owns it."""
    root = repo_root(plan)
    relative_plan = _relative_plan(plan, root)
    logs = _existing_secure_directory(root, ".graph-powers", "logs")
    if logs is None:
        print(f"no write lease to release for {relative_plan}")
        return
    lease_path = logs / "write-lease.json"
    if lease_path.is_symlink():
        fail(f"refusing symlink write lease: {lease_path.as_posix()}", 2)
    if not lease_path.exists():
        print(f"no write lease to release for {relative_plan}")
        return
    existing = _read_lease(lease_path)
    if existing["plan"] != relative_plan:
        fail(f"write lease belongs to {existing['plan']}, not {relative_plan}", 2)
    try:
        lease_path.unlink()
    except OSError as error:
        fail(f"cannot release write lease {lease_path.as_posix()}: {error}", 2)
    print(f"released write lease for {relative_plan}")


def resolve_ref(ref: str, label: str, root: Path) -> str:
    if not SAFE_REF.fullmatch(ref):
        fail(f"bad {label}: {ref}", 2)
    done = git(["rev-parse", "--verify", "--quiet", "--end-of-options", ref], root)
    if done.returncode != 0 or not done.stdout.strip():
        fail(f"bad {label}: {ref}", 2)
    return done.stdout.strip()


def object_type(sha: str, root: Path) -> str:
    return git_out(["cat-file", "-t", sha], root).strip()


def snapshot(root: Path) -> str:
    """A tree object of the working tree as it is now, untracked files included.

    Written through a throwaway index so the checkout's own index, HEAD and refs stay exactly as
    they were. `git add` honours `.gitignore`, so the workspace itself never enters the snapshot.
    """
    with tempfile.TemporaryDirectory(prefix="sdd-index-") as tmp:
        env = dict(os.environ)
        env["GIT_INDEX_FILE"] = str(Path(tmp) / "index")
        git_out(["read-tree", "HEAD"], root, env)
        git_out(["add", "--all", "--", "."], root, env)
        return git_out(["write-tree"], root, env).strip()


def package(plan: Path, base: str, head: str) -> None:
    root = repo_root(plan)
    base_sha = resolve_ref(base, "BASE", root)
    head_sha = resolve_ref(head, "HEAD", root)
    checkout = resolve_ref("HEAD", "checkout HEAD", root)
    snap = snapshot(root) if head_sha == checkout else ""
    end = snap or head_sha
    range_end = checkout if snap else head_sha

    commits = ""
    count = 0
    if object_type(base_sha, root) == "commit":
        commits = git_out(["log", "--oneline", f"{base_sha}..{range_end}"], root).strip()
        count = int(git_out(["rev-list", "--count", f"{base_sha}..{range_end}"], root).strip() or 0)
    else:
        commits = "(BASE is a working-tree snapshot, not a commit — no commit range)"
    if snap:
        commits = (commits + "\n" if commits else "") + (
            f"+ working-tree snapshot {snap[:7]} (uncommitted and untracked changes, as of now)"
        )

    stat = git_out(["diff", "--stat", base_sha, end], root).rstrip()
    diff = git_out(["diff", "-U10", base_sha, end], root).rstrip()

    text = "\n".join(
        [
            f"# Review package: {base_sha}..{end}",
            "",
            "End is a working-tree snapshot, not a commit." if snap else "End is a commit.",
            "",
            "## Commits",
            commits or "(none)",
            "",
            "## Files changed",
            stat or "(no changes)",
            "",
            "## Diff",
            diff or "(empty)",
            "",
        ]
    )
    target = workspace(plan) / f"review-{base_sha[:7]}..{end[:7]}.diff"
    _write_text_no_symlink(target, text)
    size = len(text.encode("utf-8"))
    line = f"wrote {target.as_posix()}: {count} commit(s), {size} bytes"
    if snap:
        line += f"; worktree snapshot {snap[:7]} — the next fix round packages {snap[:7]}..HEAD"
    print(line)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sdd.py",
        description="Workspace, task briefs, review packages and structured plan validation.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_ws = sub.add_parser("workspace", help="ensure and print the plan's workspace directory")
    p_ws.add_argument("plan")

    p_brief = sub.add_parser("brief", help="extract one task's text to a brief file")
    p_brief.add_argument("plan")
    p_brief.add_argument("task", help="task number: 3, 2.1, T2.1")

    p_pkg = sub.add_parser("package", help="write commits, stat and diff for BASE..HEAD to a file")
    p_pkg.add_argument("plan")
    p_pkg.add_argument("base")
    p_pkg.add_argument("head")

    p_validate = sub.add_parser(
        "validate", help="validate a structured plan and print its task graph"
    )
    p_validate.add_argument("plan")
    p_validate.add_argument("--max-tasks", type=int, required=True)
    p_validate.add_argument("--profile", choices=("default", "gauntlet"), default="default")

    p_acquire = sub.add_parser(
        "acquire", help="validate and atomically acquire the plan write lease"
    )
    p_acquire.add_argument("plan")
    p_acquire.add_argument("--max-tasks", type=int, required=True)
    p_acquire.add_argument("--profile", choices=("default", "gauntlet"), default="default")

    p_release = sub.add_parser("release", help="release only the write lease owned by this plan")
    p_release.add_argument("plan")

    p_consult = sub.add_parser("consult", help="reserve or record a parent-mediated consultation")
    consult_sub = p_consult.add_subparsers(dest="consult_action", required=True)
    p_reserve = consult_sub.add_parser("reserve", help="reserve one stable decision key")
    p_reserve.add_argument("plan")
    p_reserve.add_argument(
        "--request-json", required=True, help="canonical request envelope as JSON"
    )
    p_record = consult_sub.add_parser(
        "record", help="record the result for a reserved decision key"
    )
    p_record.add_argument("plan")
    p_record.add_argument("--result-json", required=True, help="canonical result envelope as JSON")

    args = parser.parse_args(argv)
    plan = plan_file(args.plan)
    if args.command == "workspace":
        print(workspace(plan).as_posix())
    elif args.command == "brief":
        brief(plan, args.task)
    elif args.command == "validate":
        normalized, errors = validate_plan(plan, args.max_tasks, args.profile)
        if errors:
            fail("plan validation failed: " + "; ".join(errors), 2)
        assert normalized is not None
        print(json.dumps(normalized, ensure_ascii=False, indent=2, sort_keys=False))
    elif args.command == "acquire":
        normalized = acquire(plan, args.max_tasks, args.profile)
        print(json.dumps(normalized, ensure_ascii=False, indent=2, sort_keys=False))
    elif args.command == "release":
        release(plan)
    elif args.command == "consult":
        if args.consult_action == "reserve":
            output, code = consult(plan, "reserve", args.request_json)
        else:
            try:
                json.loads(args.result_json)
            except (TypeError, ValueError) as error:
                _consultation_error(f"invalid JSON envelope: {error}")
            output, code = record_consultation(plan, args.result_json)
        print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=False))
        return code
    else:
        package(plan, args.base, args.head)
    return 0


if __name__ == "__main__":
    sys.exit(main())
