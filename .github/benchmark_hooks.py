#!/usr/bin/env python3
"""Measure the six native PreToolUse handlers without retaining hook output."""

from __future__ import annotations

import argparse
import json
import math
import os
import platform
import shlex
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, TypedDict

VERSION = 1
HANDLER_TIMEOUT_SECONDS = 10
TARGET_MATCHERS = ("*", "Bash")


class BenchmarkError(RuntimeError):
    """A malformed benchmark input or failed fixture setup."""


class PreparedHandler(TypedDict):
    matcher: str
    command: str
    name: str
    args: list[str]


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--warmups", type=int, default=3)
    parser.add_argument("--samples", type=int, default=20)
    args = parser.parse_args(argv)
    if args.warmups < 0:
        parser.error("--warmups must be non-negative")
    if args.samples <= 0:
        parser.error("--samples must be positive")
    return args


def _script_name(command: str) -> str:
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError as exc:
        raise BenchmarkError(f"invalid hook command quoting: {exc}") from exc
    for token in tokens:
        normal = token.replace("\\", "/")
        if "/hooks/" in normal and normal.endswith(".py"):
            return normal.rsplit("/hooks/", 1)[1]
    raise BenchmarkError("hook command does not name a hooks/*.py script")


def _select_handlers(manifest_path: Path) -> list[dict[str, str]]:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BenchmarkError(f"cannot read hooks manifest: {exc}") from exc
    if not isinstance(manifest, dict) or not isinstance(manifest.get("hooks"), dict):
        raise BenchmarkError("hooks manifest has no object-valued hooks member")
    pre_tool_use = manifest["hooks"].get("PreToolUse")
    if not isinstance(pre_tool_use, list):
        raise BenchmarkError("hooks manifest has no PreToolUse list")

    targets: list[dict[str, Any]] = []
    seen: set[str] = set()
    commands: set[str] = set()
    for group in pre_tool_use:
        if not isinstance(group, dict) or not isinstance(group.get("matcher"), str):
            raise BenchmarkError("every PreToolUse group must have a string matcher")
        hooks = group.get("hooks")
        if not isinstance(hooks, list) or not hooks:
            raise BenchmarkError(f"PreToolUse {group['matcher']!r} group has no hooks list")
        for hook in hooks:
            if not isinstance(hook, dict) or hook.get("type") != "command":
                raise BenchmarkError(f"PreToolUse {group['matcher']!r} contains a non-command hook")
            command = hook.get("command")
            if not isinstance(command, str) or not command.strip():
                raise BenchmarkError(f"PreToolUse {group['matcher']!r} contains an invalid command")
            if "timeout" in hook and (
                not isinstance(hook["timeout"], (int, float))
                or isinstance(hook["timeout"], bool)
                or not math.isfinite(hook["timeout"])
                or hook["timeout"] <= 0
            ):
                raise BenchmarkError(f"PreToolUse {group['matcher']!r} contains an invalid timeout")
        matcher = group["matcher"]
        if matcher in TARGET_MATCHERS:
            if matcher in seen:
                raise BenchmarkError(f"expected one PreToolUse {matcher!r} matcher group")
            seen.add(matcher)
            targets.append(group)
    missing = [matcher for matcher in TARGET_MATCHERS if matcher not in seen]
    if missing:
        raise BenchmarkError(f"missing PreToolUse matcher group(s): {', '.join(missing)}")

    selected: list[dict[str, str]] = []
    for group in targets:
        for hook in group["hooks"]:
            command = hook["command"]
            if command in commands:
                raise BenchmarkError("duplicate command in selected PreToolUse handlers")
            commands.add(command)
            selected.append({"matcher": group["matcher"], "command": command,
                             "name": _script_name(command)})
    if len(selected) != 6:
        raise BenchmarkError(f"expected exactly six selected handlers, found {len(selected)}")
    return selected


def _prepare_command(command: str, plugin_root: Path) -> list[str]:
    try:
        args = shlex.split(command, posix=True)
    except ValueError as exc:
        raise BenchmarkError(f"invalid hook command quoting: {exc}") from exc
    if not args or not Path(args[0]).name.casefold().startswith("python"):
        raise BenchmarkError("selected hook command does not use a Python interpreter")
    args[0] = sys.executable
    root_text = plugin_root.as_posix()
    return [arg.replace("${CLAUDE_PLUGIN_ROOT}", root_text) for arg in args]


def _invoke(args: list[str], payload: bytes, fixture: Path, env: dict[str, str]) -> tuple[int, int]:
    started = time.perf_counter_ns()
    failed = 0
    try:
        result = subprocess.run(
            args, cwd=fixture, env=env, input=payload,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=HANDLER_TIMEOUT_SECONDS, check=False,
        )
        failed = int(result.returncode != 0)
    except (OSError, subprocess.SubprocessError):
        failed = 1
    return time.perf_counter_ns() - started, failed


def _percentile(values: list[int], fraction: float) -> float:
    ordered = sorted(values)
    return round(ordered[max(0, math.ceil(fraction * len(ordered)) - 1)] / 1_000_000, 3)


def _metric(cold_ns: int, samples_ns: list[int], failures: int) -> dict[str, Any]:
    return {"coldMs": round(cold_ns / 1_000_000, 3),
            "p50Ms": _percentile(samples_ns, 0.50),
            "p95Ms": _percentile(samples_ns, 0.95),
            "failures": failures}


def _validate_report(report: object, warmups: int | None = None,
                     samples: int | None = None) -> None:
    if not isinstance(report, dict):
        raise BenchmarkError("benchmark report is not an object")
    required = {"version", "platform", "python", "handlerCount", "warmups",
                "samples", "handlers", "chain"}
    if not required.issubset(report) or report["version"] != VERSION:
        raise BenchmarkError("benchmark report is missing required fields")
    if not isinstance(report["platform"], str) or not report["platform"] \
            or not isinstance(report["python"], str) or not report["python"]:
        raise BenchmarkError("benchmark report metadata is invalid")
    if not isinstance(report["warmups"], int) or isinstance(report["warmups"], bool) \
            or report["warmups"] < 0 or not isinstance(report["samples"], int) \
            or isinstance(report["samples"], bool) or report["samples"] <= 0:
        raise BenchmarkError("benchmark report sample configuration is invalid")
    if warmups is not None and report["warmups"] != warmups:
        raise BenchmarkError("benchmark report warmups does not match CLI")
    if samples is not None and report["samples"] != samples:
        raise BenchmarkError("benchmark report samples does not match CLI")
    handlers = report["handlers"]
    if not isinstance(report["handlerCount"], int) or isinstance(report["handlerCount"], bool) \
            or report["handlerCount"] != 6 or not isinstance(handlers, list) \
            or len(handlers) != report["handlerCount"]:
        raise BenchmarkError("benchmark report must contain exactly six handlers")

    def metric(value: object, label: str) -> int:
        fields = {"coldMs", "p50Ms", "p95Ms", "failures"}
        if not isinstance(value, dict) or not fields.issubset(value):
            raise BenchmarkError(f"{label} metric is incomplete")
        for key in ("coldMs", "p50Ms", "p95Ms"):
            number = value[key]
            if not isinstance(number, (int, float)) or isinstance(number, bool) \
                    or not math.isfinite(number) or number < 0:
                raise BenchmarkError(f"{label} metric {key} is invalid")
        failures = value["failures"]
        if not isinstance(failures, int) or isinstance(failures, bool) or failures < 0:
            raise BenchmarkError(f"{label} metric failures is invalid")
        return failures

    failures = 0
    names: set[str] = set()
    for index, handler in enumerate(handlers):
        if not isinstance(handler, dict) or not isinstance(handler.get("name"), str) \
                or not handler["name"] or handler.get("matcher") not in TARGET_MATCHERS:
            raise BenchmarkError(f"handler {index} metadata is invalid")
        if handler["name"] in names:
            raise BenchmarkError("benchmark report contains duplicate handlers")
        names.add(handler["name"])
        failures += metric(handler, f"handler {index}")
    failures += metric(report["chain"], "chain")
    if failures:
        raise BenchmarkError(f"benchmark handler failures: {failures}")


def _fixture() -> tempfile.TemporaryDirectory[str]:
    fixture = tempfile.TemporaryDirectory(prefix="graph-powers-hook-benchmark-")
    root = Path(fixture.name)
    try:
        result = subprocess.run(["git", "init"], cwd=root,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                check=False)
    except OSError:
        fixture.cleanup()
        raise BenchmarkError("unable to start git for temporary fixture") from None
    if result.returncode != 0:
        fixture.cleanup()
        raise BenchmarkError("git init failed for temporary fixture")
    (root / "sample.txt").write_text("benchmark ✓\n", encoding="utf-8")
    return fixture


def _run(args: argparse.Namespace) -> dict[str, Any]:
    plugin_root = Path(__file__).resolve().parents[1]
    handlers = _select_handlers(plugin_root / "hooks" / "hooks.json")
    prepared: list[PreparedHandler] = [
        {"matcher": handler["matcher"], "command": handler["command"],
         "name": handler["name"],
         "args": _prepare_command(handler["command"], plugin_root)}
        for handler in handlers
    ]
    environment = os.environ.copy()
    environment["CLAUDE_PLUGIN_ROOT"] = plugin_root.as_posix()
    environment["PYTHONIOENCODING"] = "utf-8"
    hooks_path = str((plugin_root / "hooks").resolve())
    environment["PYTHONPATH"] = hooks_path + os.pathsep + environment.get("PYTHONPATH", "")
    with _fixture() as fixture_name:
        fixture = Path(fixture_name)
        payload = json.dumps(
            {"cwd": str(fixture), "tool_name": "Bash",
             "tool_input": {"command": "git status --short"}},
            ensure_ascii=False,
        ).encode("utf-8")
        output: list[dict[str, Any]] = []
        for handler in prepared:
            cold, failures = _invoke(handler["args"], payload, fixture, environment)
            for _ in range(args.warmups):
                _, failures_now = _invoke(handler["args"], payload, fixture, environment)
                failures += failures_now
            samples: list[int] = []
            for _ in range(args.samples):
                elapsed, failures_now = _invoke(handler["args"], payload, fixture, environment)
                samples.append(elapsed)
                failures += failures_now
            output.append({"name": handler["name"], "matcher": handler["matcher"],
                           **_metric(cold, samples, failures)})

        def chain_once() -> tuple[int, int]:
            started = time.perf_counter_ns()
            failures = 0
            for handler in prepared:
                _, failed = _invoke(handler["args"], payload, fixture, environment)
                failures += failed
            return time.perf_counter_ns() - started, failures

        chain_cold, chain_failures = chain_once()
        for _ in range(args.warmups):
            _, failed = chain_once()
            chain_failures += failed
        chain_samples: list[int] = []
        for _ in range(args.samples):
            elapsed, failed = chain_once()
            chain_samples.append(elapsed)
            chain_failures += failed
    return {"version": VERSION, "platform": platform.platform(),
            "python": platform.python_version(), "handlerCount": len(output),
            "warmups": args.warmups, "samples": args.samples,
            "handlers": output, "chain": _metric(chain_cold, chain_samples, chain_failures)}


def _self_test() -> int:
    plugin_root = Path(__file__).resolve().parents[1]
    manifest = json.loads((plugin_root / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    malformed = json.loads(json.dumps(manifest))
    malformed["hooks"]["PreToolUse"].append({"matcher": "Other", "hooks": "invalid"})
    with tempfile.TemporaryDirectory(prefix="graph-powers-hook-self-test-") as directory:
        path = Path(directory) / "malformed.json"
        path.write_text(json.dumps(malformed), encoding="utf-8")
        try:
            _select_handlers(path)
        except BenchmarkError:
            pass
        else:
            raise BenchmarkError("malformed non-target matcher was accepted")
        target = manifest["hooks"]["PreToolUse"]
        reordered = json.loads(json.dumps(manifest))
        reordered["hooks"]["PreToolUse"] = (
            [group for group in target if group.get("matcher") == "Bash"]
            + [group for group in target if group.get("matcher") == "*"]
            + [group for group in target if group.get("matcher") not in TARGET_MATCHERS]
        )
        path.write_text(json.dumps(reordered), encoding="utf-8")
        selected = _select_handlers(path)
        if [handler["matcher"] for handler in selected] != ["Bash"] * 5 + ["*"]:
            raise BenchmarkError("selected handlers did not preserve manifest order")

    metric = {"coldMs": 1.0, "p50Ms": 2.0, "p95Ms": 3.0, "failures": 0}
    valid = {"version": VERSION, "platform": "test", "python": "3",
             "handlerCount": 6, "warmups": 2, "samples": 4,
             "handlers": [{"name": f"handler-{i}", "matcher": "*", **metric}
                          for i in range(6)], "chain": metric}
    _validate_report(valid, warmups=2, samples=4)
    invalid = json.loads(json.dumps(valid))
    invalid["handlerCount"] = 5
    try:
        _validate_report(invalid)
    except BenchmarkError:
        pass
    else:
        raise BenchmarkError("invalid report handler count was accepted")
    invalid = json.loads(json.dumps(valid))
    invalid["handlers"][0]["failures"] = 1
    try:
        _validate_report(invalid)
    except BenchmarkError:
        pass
    else:
        raise BenchmarkError("report with handler failures was accepted")
    overrides = _parse_args(["--warmups", "2", "--samples", "4"])
    if overrides.warmups != 2 or overrides.samples != 4 or overrides.self_test:
        raise BenchmarkError("CLI overrides were not parsed")
    prepared = _prepare_command(
        'python3 -X utf8 -c "pass" "${CLAUDE_PLUGIN_ROOT}/hooks/example.py"',
        Path("C:/Program Files/Graph Powers"),
    )
    if prepared[0] != sys.executable or prepared[-1] != "C:/Program Files/Graph Powers/hooks/example.py":
        raise BenchmarkError("spaced forward-slash plugin path was not prepared safely")
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--warmups", "0", "--samples", "1"],
        cwd=plugin_root, capture_output=True,
        timeout=HANDLER_TIMEOUT_SECONDS * 2, check=False,
    )
    if result.returncode != 0:
        raise BenchmarkError("normal benchmark failed during self-test")
    try:
        output = result.stdout.decode("utf-8")
        report, end = json.JSONDecoder().raw_decode(output)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BenchmarkError("normal benchmark did not emit JSON") from exc
    if output[end:].strip():
        raise BenchmarkError("normal benchmark emitted more than one JSON document")
    _validate_report(report, warmups=0, samples=1)
    print("benchmark self-test: PASS")
    return 0


def main() -> int:
    args = _parse_args()
    if args.self_test:
        try:
            return _self_test()
        except (BenchmarkError, OSError, json.JSONDecodeError) as exc:
            print(f"benchmark self-test error: {exc}", file=sys.stderr)
            return 1
    report: dict[str, Any] | None = None
    try:
        report = _run(args)
        _validate_report(report, warmups=args.warmups, samples=args.samples)
    except BenchmarkError as exc:
        if report is not None:
            print(json.dumps(report, ensure_ascii=False, separators=(",", ":")))
        print(f"benchmark error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())

