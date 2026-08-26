#!/usr/bin/env python3
"""Workspace, task briefs and review packages for `Skill("graph-powers:executing-plans")`.

One script, three subcommands, one location rule — so a brief and the package that reviews it can
never land in different directories:

    python -X utf8 sdd.py workspace PLAN_FILE                  -> prints the plan's workspace
    python -X utf8 sdd.py brief     PLAN_FILE N [OUT]          -> task N's text, to a file
    python -X utf8 sdd.py package   PLAN_FILE BASE HEAD [OUT]  -> commits, stat and diff, to a file

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
harness's checkbox, `- [ ] **T2.1** — ...` with its indented fields. Fenced blocks are skipped when
matching, so a heading quoted inside a code sample never starts a task.

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
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import NoReturn

FENCE = re.compile(r"^\s*(```|~~~)")
TASK_HEADING = re.compile(r"^(#{1,6})[ \t]+Task[ \t]+([0-9][0-9.]*[A-Za-z]?)")
TASK_CHECKBOX = re.compile(
    r"^([ \t]*)[-*][ \t]+\[[ xX]\][ \t]+\**(?:Task[ \t]+|T)([0-9][0-9.]*[A-Za-z]?)"
)


def fail(message: str, code: int) -> NoReturn:
    print(message, file=sys.stderr)
    sys.exit(code)


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
        description="Workspace, task briefs and review packages for executing-plans.",
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

    args = parser.parse_args(argv)
    plan = plan_file(args.plan)
    if args.command == "workspace":
        print(workspace(plan).as_posix())
    elif args.command == "brief":
        brief(plan, args.task, args.out)
    else:
        package(plan, args.base, args.head, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
