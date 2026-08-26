#!/usr/bin/env python3
"""Run `turbo --dry=json` with stdout on a real file.

turbo 2.x panics at Rust stdio.rs:1165 on Broken pipe (os error 32) when
`--dry=json` writes to a pipe whose reader already closed. An agent's Bash
tool IS that pipe. The JS wrapper then `process.kill(pid, SIGABRT)` and bun
`abort()`s — three coredumps, no graph.

This process opens a file, hands turbo that fd, and prints only the path
plus a short summary. Load `Skill("debugger")` and use its JS/TS gate resolver
before running it. Never pass `--dry=json` to bun/turbo/node in the shell tool.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def _os_arch() -> tuple[str, str]:
    system = platform.system().lower()
    os_name = {"linux": "linux", "darwin": "darwin", "windows": "windows"}.get(system, system)
    machine = platform.machine().lower()
    arch = "arm64" if machine in {"arm64", "aarch64"} else "64"
    return os_name, arch


def resolve_turbo(cwd: Path) -> list[str]:
    """Argv prefix that launches turbo. Prefer the native binary over the Node wrapper."""
    os_name, arch = _os_arch()
    ext = ".exe" if os.name == "nt" else ""
    candidates: list[Path] = [
        cwd / "node_modules" / "@turbo" / f"{os_name}-{arch}" / "bin" / f"turbo{ext}",
    ]
    bun_root = cwd / "node_modules" / ".bun"
    if bun_root.is_dir():
        pattern = (
            f"@turbo+{os_name}-{arch}@*/node_modules/@turbo/{os_name}-{arch}/bin/turbo{ext}"
        )
        candidates.extend(sorted(bun_root.glob(pattern)))
    for path in candidates:
        if path.is_file():
            return [str(path)]

    js_wrapper = cwd / "node_modules" / "turbo" / "bin" / "turbo"
    node = shutil.which("node")
    if js_wrapper.is_file() and node:
        return [node, str(js_wrapper)]

    which = shutil.which("turbo")
    if which:
        return [which]

    raise FileNotFoundError(
        "turbo is not installed in this project (no native binary, no "
        "node_modules/turbo/bin/turbo, nothing named turbo on PATH)"
    )


def output_path(cwd: Path, explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit if explicit.is_absolute() else cwd / explicit
    return cwd / ".graph-powers" / "cache" / "turbo-dry.json"


def run_dry(cwd: Path, task: str, extra: list[str], dest: Path) -> int:
    argv = [*resolve_turbo(cwd), "run", task, "--dry=json", *extra]
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as out:
        completed = subprocess.run(
            argv,
            stdout=out,
            stderr=sys.stderr,
            cwd=str(cwd),
            check=False,
        )
    return int(completed.returncode)


def summarize(dest: Path) -> str:
    size = dest.stat().st_size if dest.is_file() else 0
    packages = "?"
    try:
        payload = json.loads(dest.read_text(encoding="utf-8"))
        tasks = payload.get("tasks")
        if isinstance(tasks, list):
            names = sorted({
                str(item.get("package") or item.get("taskId") or "")
                for item in tasks
                if isinstance(item, dict)
            } - {""})
            packages = str(len(names))
        elif isinstance(payload.get("packages"), list):
            packages = str(len(payload["packages"]))
    except (OSError, UnicodeError, json.JSONDecodeError, AttributeError):
        packages = "?"
    return f"TURBO_DRY_JSON={dest}\nbytes={size}\npackages={packages}\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Write turbo --dry=json to a file so Rust never sees EPIPE. "
            "Prints the path. Then Read that file."
        )
    )
    parser.add_argument("--task", default="test", help="turbo task name (default: test)")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="destination file (default: .graph-powers/cache/turbo-dry.json)",
    )
    parser.add_argument(
        "--cwd",
        type=Path,
        default=None,
        help="project root (default: current working directory)",
    )
    parser.add_argument(
        "extra",
        nargs=argparse.REMAINDER,
        help="extra turbo args; a leading -- is stripped",
    )
    args = parser.parse_args(argv)
    extra = list(args.extra)
    if extra and extra[0] == "--":
        extra = extra[1:]

    cwd = (args.cwd or Path.cwd()).resolve()
    dest = output_path(cwd, args.output)
    try:
        code = run_dry(cwd, args.task, extra, dest)
    except FileNotFoundError as err:
        sys.stderr.write(f"{err}\n")
        return 1
    sys.stdout.write(summarize(dest))
    sys.stdout.write(f"exit={code}\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
