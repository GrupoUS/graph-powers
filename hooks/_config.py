#!/usr/bin/env python3
"""_config.py — the one piece that knows projects are different.

Every guardrail in this plugin runs in repositories with different branches,
toolchains and paths. Instead of each hook guessing, they all read from here, and
this module reads from one place: the project's Graph Powers config file.

Why this shape
--------------
The harness this grew out of had branch names and opt-in variables written inside
the hooks. Copying that to another project meant editing five files and remembering
every spot — and that model is exactly what produced 176 divergent copies of the
same file across five repositories. Here the hook is byte-for-byte identical
everywhere; what changes is the project's JSON.

Contract
--------
Nothing here raises. A missing, unreadable or incomplete config returns the
defaults. A guardrail that breaks the session when YOUR configuration has a typo is
worse than no guardrail, because it teaches people to switch guardrails off.

Harness support
---------------
Claude Code exports CLAUDE_PROJECT_DIR. Codex CLI does not, but passes `cwd` in the
hook payload on stdin — hooks that read the payload should pass it to
`project_dir()`. When neither is available the git worktree root is used, and the
process working directory is the last resort.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

# Where a project declares itself. The first file that parses wins; `.claude/`
# remains supported because a Claude-only project has no reason to move.
CONFIG_PATHS = (
    ".graph-powers/config.json",
    ".claude/config.json",
)

DEFAULTS: dict[str, Any] = {
    # Git — branch names and the opt-in key that releases a risky action.
    "git": {
        "workBranch": "dev-test",
        "protectedBranches": ["main", "master"],
        "optInPrefix": "GRAPHPOWERS",
    },
    # Execution graph ceilings, read by graph_guardrails.py.
    "graphGuardrails": {
        "maxSpawnsPerSession": 25,
        "maxRoundsPerAgent": 8,
    },
    # How much runs without stopping to ask. `guarded` is the default because a stranger's first
    # session should not be the one that discovers what this harness will do unattended.
    "autonomy": {
        "level": "guarded",
        "destructiveFloor": True,
        "allowPackageManagers": [],
    },
    # Files no agent writes, in any project.
    "protectedFiles": {
        "exact": [],
        "segments": [".git", "node_modules"],
        "contains": [".env"],
    },
}


def _git_root(start: Path) -> Path | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=start,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=3,
            check=False,
        )
    except Exception:
        return None
    root = (out.stdout or "").strip()
    return Path(root) if out.returncode == 0 and root else None


def project_dir(payload: dict[str, Any] | None = None) -> Path:
    """The repository the session runs in — never the plugin directory.

    `payload` is the hook event read from stdin. Codex puts the working directory
    there; Claude Code exports it as an environment variable instead.
    """
    if isinstance(payload, dict):
        cwd = payload.get("cwd")
        if isinstance(cwd, str) and cwd:
            return Path(cwd)
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env)
    here = Path.cwd()
    return _git_root(here) or here


def _deep_merge(base: dict[str, Any], over: dict[str, Any]) -> dict[str, Any]:
    """Merge the project's config over the defaults, keeping the default on any shape mismatch.

    A value of the wrong shape is dropped rather than accepted. The alternative was measured and it
    is worse in both directions: `{"git": "dev-test"}` raised a TypeError deep inside a hook —
    breaking the fail-open contract — and `{"protectedBranches": "main"}` was accepted, then
    iterated character by character, so no branch name ever matched and the branch gate silently
    stopped protecting anything. A guardrail that quietly does nothing is the worst outcome
    available, because the report still looks clean.
    """
    out = dict(base)
    for k, v in over.items():
        default = out.get(k)
        if isinstance(default, dict):
            out[k] = _deep_merge(default, v) if isinstance(v, dict) else default
        elif isinstance(default, list):
            out[k] = _coerce_list(v, default)
        elif isinstance(default, bool):
            out[k] = v if isinstance(v, bool) else default
        elif isinstance(default, int) and not isinstance(default, bool):
            out[k] = v if isinstance(v, int) and not isinstance(v, bool) else default
        elif isinstance(default, str):
            out[k] = v if isinstance(v, str) else default
        else:
            out[k] = v
    return out


def _coerce_list(value: Any, default: list[Any]) -> list[Any]:
    """A list stays a list. A bare string becomes a one-item list — the likely intent, and safe.

    Anything else keeps the default: silently widening a guardrail on malformed input is how it
    stops guarding.
    """
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value.strip():
        return [value]
    return list(default)


def config_path(root: Path | None = None) -> Path | None:
    """The config file in use, or None when the project declares nothing."""
    root = root or project_dir()
    for rel in CONFIG_PATHS:
        candidate = root / rel
        try:
            if candidate.is_file():
                return candidate
        except Exception:
            continue
    return None


def load(root: Path | None = None, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    root = root or project_dir(payload)
    found = config_path(root)
    if found is None:
        return dict(DEFAULTS)
    try:
        raw = json.loads(found.read_text(encoding="utf-8"))
    except Exception:
        return dict(DEFAULTS)
    if not isinstance(raw, dict):
        return dict(DEFAULTS)
    return _deep_merge(DEFAULTS, raw)


# ── Shortcuts the hooks use ──────────────────────────────────────────────────

def work_branch(cfg: dict[str, Any] | None = None) -> str:
    value = (cfg or load())["git"]["workBranch"]
    return value if isinstance(value, str) and value else DEFAULTS["git"]["workBranch"]


def protected_branches(cfg: dict[str, Any] | None = None) -> list[str]:
    raw = (cfg or load())["git"]["protectedBranches"]
    return [b for b in _coerce_list(raw, DEFAULTS["git"]["protectedBranches"]) if isinstance(b, str) and b]


def protected_files(cfg: dict[str, Any] | None = None) -> dict[str, list[str]]:
    raw = (cfg or load())["protectedFiles"]
    if not isinstance(raw, dict):
        return dict(DEFAULTS["protectedFiles"])
    return {k: _coerce_list(raw.get(k), DEFAULTS["protectedFiles"][k]) for k in DEFAULTS["protectedFiles"]}


def graph_limits(cfg: dict[str, Any] | None = None) -> dict[str, int]:
    raw = (cfg or load())["graphGuardrails"]
    if not isinstance(raw, dict):
        return dict(DEFAULTS["graphGuardrails"])
    return {k: (raw[k] if isinstance(raw.get(k), int) and not isinstance(raw.get(k), bool) and raw[k] > 0
                else v) for k, v in DEFAULTS["graphGuardrails"].items()}


# ── Autonomy ─────────────────────────────────────────────────────────────────

# Annotated rather than inferred: `autonomy()` adds `destructiveFloor` (a bool) and
# `allowPackageManagers` (a list) to the copy it returns, so the value type is not `str`.
_AUTONOMOUS_DEFAULTS: dict[str, Any] = {"bashDefault": "allow", "cleanup": "allow",
                                        "commit": "auto", "push": "auto", "protectedBranch": "ask"}
_GUARDED_DEFAULTS: dict[str, Any] = {"bashDefault": "ask", "cleanup": "ask",
                                     "commit": "ask", "push": "ask", "protectedBranch": "ask"}


def autonomy(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    """The resolved autonomy settings: level defaults, with per-field overrides on top."""
    node = (cfg or load()).get("autonomy")
    if not isinstance(node, dict):
        node = {}
    level = node.get("level", "guarded")
    base = dict(_AUTONOMOUS_DEFAULTS if level == "autonomous" else _GUARDED_DEFAULTS)
    for key in ("bashDefault", "cleanup"):
        if node.get(key) in ("ask", "allow"):
            base[key] = node[key]
    git = node.get("git")
    if not isinstance(git, dict):
        git = {}
    for key in ("commit", "push", "protectedBranch"):
        if git.get(key) in ("ask", "auto"):
            base[key] = git[key]
    base["level"] = level
    base["destructiveFloor"] = node.get("destructiveFloor", True) is not False
    base["allowPackageManagers"] = list(node.get("allowPackageManagers") or [])
    return base


def auto(action: str, cfg: dict[str, Any] | None = None) -> bool:
    """True when this git action runs without an opt-in key in the turn.

    `action` is COMMIT, PUSH, PUSH_MAIN or MAIN_CHECKOUT — the same vocabulary as `opt_in`.
    """
    a = autonomy(cfg)
    if action == "COMMIT":
        return a["commit"] == "auto"
    if action == "PUSH":
        return a["push"] == "auto"
    if action in ("PUSH_MAIN", "MAIN_CHECKOUT"):
        return a["protectedBranch"] == "auto"
    return False


def _prefix(cfg: dict[str, Any] | None = None) -> str:
    value = (cfg or load())["git"]["optInPrefix"]
    return value if isinstance(value, str) and value.strip() else DEFAULTS["git"]["optInPrefix"]


def opt_in(action: str, cfg: dict[str, Any] | None = None) -> str:
    """Name of the env var that releases an action. `opt_in("COMMIT")` -> `GRAPHPOWERS_ALLOW_COMMIT`.

    The prefix is per project on purpose: running two repositories side by side with
    the same key would make an approval given in one of them count in the other.
    """
    return f"{_prefix(cfg)}_ALLOW_{action}"


def opted_in(action: str, command: str = "", cfg: dict[str, Any] | None = None) -> bool:
    """True when the key appears inline in the command or in the environment.

    The inline form (`GRAPHPOWERS_ALLOW_COMMIT=1 git commit -m "..."`) is the one that
    matters: it is written once, for one command, after a person approved that turn.
    """
    if auto(action, cfg):
        return True
    key = opt_in(action, cfg)
    return os.environ.get(key) == "1" or f"{key}=1" in (command or "")
