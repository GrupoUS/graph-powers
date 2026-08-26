#!/usr/bin/env python3
"""Plan workspaces, task briefs, review packages and plan validation.

One script, four subcommands, one location rule — so a brief and the package that reviews it can
never land in different directories:

    python -X utf8 sdd.py workspace PLAN_FILE                  -> prints the plan's workspace
    python -X utf8 sdd.py brief     PLAN_FILE N [OUT]          -> task N's text, to a file
    python -X utf8 sdd.py package   PLAN_FILE BASE HEAD [OUT]  -> commits, stat and diff, to a file
    python -X utf8 sdd.py validate  PLAN_FILE --max-tasks N   -> tasks, gates and lease as JSON

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

Exit codes, as upstream: 0 done · 2 usage or bad input · 3 task not found. A failure is one line on
stderr.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
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
TASK_MARKER = re.compile(r"^[ \t]*-[ \t]+\[[ xX]\]")
MALFORMED_STRUCTURED = re.compile(r"^[ \t]*-[ \t]+\[[ xX]\][ \t]+\*\*T", re.IGNORECASE)
MALFORMED_GATE = re.compile(r"^[ \t]*-[ \t]+\[[ xX]\][ \t]+\*\*G", re.IGNORECASE)
FIELD = re.compile(r"^(?P<indent>[ \t]+)(?P<name>[A-Za-z][A-Za-z0-9_-]*):[ \t]*(?P<value>.*)$")
TASK_ID = re.compile(r"^T[0-9]+(?:\.[0-9]+)*[A-Za-z]?$")
NEED_REF = re.compile(
    r"(?P<id>T[0-9]+(?:\.[0-9]+)*[A-Za-z]?)\s*\(\s*reads\s*:\s*(?P<reads>[^()]*?\S)\s*\)",
    re.IGNORECASE,
)

AGENT_ID = re.compile(r"^graph-powers:(?P<slug>[a-z0-9][a-z0-9-]*)$")
AGENTS_DIR = Path(__file__).resolve().parents[3] / "agents"


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
    return "routable" if re.search(r"^role_type:\s*worker\s*$", frontmatter[1], re.MULTILINE) else "other"


def git(args: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args], cwd=str(cwd), env=env, capture_output=True,
            encoding="utf-8", errors="replace", check=False,
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


def workspace(plan: Path) -> Path:
    base = repo_root(plan) / ".graph-powers" / "logs" / "sdd"
    directory = base / plan_slug(plan)
    directory.mkdir(parents=True, exist_ok=True)
    ignore = base / ".gitignore"
    if not ignore.is_file() or ignore.read_text(encoding="utf-8") != "*\n":
        ignore.write_text("*\n", encoding="utf-8")
    return directory


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


def brief(plan: Path, number: str, out: str | None) -> None:
    wanted = task_id(number)
    lines = plan.read_text(encoding="utf-8", errors="replace").splitlines()
    section = extract_task(lines, wanted)
    if not section:
        fail(f"task {number} not found in {plan.as_posix()} "
             f"(no heading 'Task {wanted}' and no checkbox 'T{wanted}')", 3)
    target = Path(out) if out else workspace(plan) / f"task-{wanted}-brief.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(section) + "\n", encoding="utf-8")
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
        # Any checkbox ends the preceding block. Fields never bleed through a boundary even when
        # a plan omits a blank line.
        for candidate in range(index + 1, end):
            if TASK_MARKER.match(visible[candidate][1]):
                end = candidate
                break
        blocks.append((line_no, task_id_value, visible[index:end]))
    return blocks, errors


def _task_blocks(visible: list[tuple[int, str]]) -> tuple[list[tuple[int, str, list[tuple[int, str]]]], list[str]]:
    blocks, errors = _structured_blocks(
        visible, STRUCTURED_TASK, MALFORMED_STRUCTURED, "task", "- [ ] **T1.1** — title"
    )
    if not blocks:
        if any(TASK_MARKER.match(line) for _, line in visible):
            errors.append("legacy or unstructured plan: route to /plan and regenerate the structured task grammar")
        else:
            errors.append("plan contains no structured tasks: route to /plan")
    return blocks, errors


def _gate_blocks(visible: list[tuple[int, str]]) -> tuple[list[tuple[int, str, list[tuple[int, str]]]], list[str]]:
    blocks, errors = _structured_blocks(
        visible, STRUCTURED_GATE, MALFORMED_GATE, "gate", "- [ ] **G1.1** — title"
    )
    if not blocks:
        errors.append("plan is missing structured gate blocks: route to /plan")
    return blocks, errors


def _parse_task(block: tuple[int, str, list[tuple[int, str]]], errors: list[str]) -> dict[str, Any]:
    line_no, task_id_value, lines = block
    header = STRUCTURED_TASK.match(lines[0][1])
    assert header is not None
    fields: dict[str, str] = {}
    steps: list[str] = []
    task_indent = len(header.group("indent"))
    in_steps = False
    for _source_line, line in lines[1:]:
        field = FIELD.match(line)
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
                if value:
                    steps.append(value)
            else:
                fields[name] = value
                in_steps = False
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
    for name in required:
        if not fields.get(name, "").strip():
            errors.append(f"{task_id_value}: missing required field {name.title()}")
    title = header.group("title").strip()
    if not title or title.lower() in {"tbd", "todo"}:
        errors.append(f"{task_id_value}: task title is empty or a placeholder")
    owns = _owns(fields.get("owns", ""), task_id_value, errors) if "owns" in fields else []
    needs = _needs(fields.get("needs", ""), task_id_value, errors) if "needs" in fields else []
    tdd = _unquote(fields.get("tdd", "")).strip()
    tdd_match = re.match(r"^(required|not-applicable|exception-approved)(?:\s*\(([^)]*)\))?$", tdd, re.IGNORECASE)
    if tdd and not tdd_match:
        errors.append(f"{task_id_value}: TDD must be required, not-applicable (<reason>) or exception-approved (<reason>)")
    elif tdd_match and tdd_match.group(1).lower() != "required" and not (tdd_match.group(2) or "").strip():
        errors.append(f"{task_id_value}: {tdd_match.group(1)} requires a reason")
    if tdd_match and tdd_match.group(1).lower() == "required":
        step_text = " ".join(steps)
        if not re.search(r"\bRED\b", step_text, re.IGNORECASE):
            errors.append(f"{task_id_value}: TDD required but Steps has no RED step")
        if not re.search(r"\bGREEN\b", step_text, re.IGNORECASE):
            errors.append(f"{task_id_value}: TDD required but Steps has no GREEN step")
    if fields.get("agent", "").strip() and not steps and fields["agent"].strip().lower() != "main":
        errors.append(f"{task_id_value}: subagent task requires Steps")

    agent = fields.get("agent", "")
    normalized_agent = _unquote(agent)
    lane = _agent_lane(normalized_agent) if normalized_agent else "unknown"
    if lane == "human-chain":
        errors.append(f"{task_id_value}: Agent main is not routable in Phase C")
    elif normalized_agent and lane == "unknown":
        errors.append(f"{task_id_value}: unknown Agent {normalized_agent}")
    elif normalized_agent and lane != "routable":
        errors.append(f"{task_id_value}: Agent {normalized_agent} is not routable in Phase C")
    skill = fields.get("skill", "")
    effort = fields.get("effort", "")
    task: dict[str, Any] = {
        "id": task_id_value,
        "title": title,
        "checked": header.group("checked").lower() == "x",
        "owns": owns,
        "needs": [edge["id"] for edge in needs],
        "reads": {edge["id"]: edge["reads"] for edge in needs},
        "agent": normalized_agent,
        "skill": _unquote(skill),
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
    if task["checked"] and task["evidence"].strip().lower() == "pending":
        errors.append(f"{task_id_value}: checked task still has EVIDENCE pending")
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


def validate_plan(plan: Path, max_tasks: int) -> tuple[dict[str, Any] | None, list[str]]:
    """Validate Phase B's structured plan and return its normalized execution graph."""
    errors: list[str] = []
    if max_tasks < 1:
        return None, ["--max-tasks must be a positive integer"]
    lines = plan.read_text(encoding="utf-8", errors="replace").splitlines()
    visible = _visible_plan_lines(lines)
    blocks, errors = _task_blocks(visible)
    if not blocks:
        return None, errors
    gate_blocks, gate_errors = _gate_blocks(visible)
    errors.extend(gate_errors)
    if len(blocks) > max_tasks:
        errors.append(f"plan has {len(blocks)} tasks, exceeding --max-tasks {max_tasks}")
    tasks = [_parse_task(block, errors) for block in blocks]
    gates = [_parse_gate(block, errors) for block in gate_blocks]
    ids = [task["id"] for task in tasks]
    if len(ids) != len(set(ids)):
        duplicates = sorted({item for item in ids if ids.count(item) > 1})
        errors.append(f"duplicate task id(s): {', '.join(duplicates)}")
    gate_ids = [gate["id"] for gate in gates]
    if len(gate_ids) != len(set(gate_ids)):
        duplicates = sorted({item for item in gate_ids if gate_ids.count(item) > 1})
        errors.append(f"duplicate gate id(s): {', '.join(duplicates)}")
    task_phases = {task["id"][1:].split(".", 1)[0] for task in tasks}
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
        for right in tasks[index + 1:]:
            overlap = sorted({a for a in left["owns"] for b in right["owns"] if a == b or a.startswith(b + "/") or b.startswith(a + "/")})
            if overlap and not (_reachable(left["id"], right["id"], edges) or _reachable(right["id"], left["id"], edges)):
                errors.append(f"concurrent Owns conflict: {left['id']} and {right['id']} overlap {', '.join(overlap)}")
    if errors:
        return None, errors
    lease = sorted({path for task in tasks for path in task["owns"]})
    return {"tasks": tasks, "gates": gates, "writeLease": lease}, []


def resolve_ref(ref: str, label: str, root: Path) -> str:
    done = git(["rev-parse", "--verify", "--quiet", ref], root)
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


def package(plan: Path, base: str, head: str, out: str | None) -> None:
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

    text = "\n".join([
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
    ])
    target = Path(out) if out else workspace(plan) / f"review-{base_sha[:7]}..{end[:7]}.diff"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    size = target.stat().st_size
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
    p_brief.add_argument("out", nargs="?")

    p_pkg = sub.add_parser("package", help="write commits, stat and diff for BASE..HEAD to a file")
    p_pkg.add_argument("plan")
    p_pkg.add_argument("base")
    p_pkg.add_argument("head")
    p_pkg.add_argument("out", nargs="?")

    p_validate = sub.add_parser("validate", help="validate a structured plan and print its task graph")
    p_validate.add_argument("plan")
    p_validate.add_argument("--max-tasks", type=int, required=True)

    args = parser.parse_args(argv)
    plan = plan_file(args.plan)
    if args.command == "workspace":
        print(workspace(plan).as_posix())
    elif args.command == "brief":
        brief(plan, args.task, args.out)
    elif args.command == "validate":
        normalized, errors = validate_plan(plan, args.max_tasks)
        if errors:
            fail("plan validation failed: " + "; ".join(errors), 2)
        assert normalized is not None
        print(json.dumps(normalized, ensure_ascii=False, indent=2, sort_keys=False))
    else:
        package(plan, args.base, args.head, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
