#!/usr/bin/env python3
"""_config.py — the one piece that knows projects are different.

Every guardrail in this plugin runs in repositories with different branches,
toolchains and paths. Instead of each hook guessing, they all read from here.

Two scopes, resolved `DEFAULTS < user < project`:

    ~/.graph-powers/config.json     the operator — how much runs without asking
    <repo>/.graph-powers/config.json  the repository — branches, tooling, paths

The user file answers only the blocks in `USER_SCOPED_KEYS`; everything else in the
schema describes a repository and is meaningless from a home directory. The project
file sits on top because rules a repository ships apply to everyone who clones it.

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
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any

# Where a project declares itself. The first file that parses wins; `.claude/`
# remains supported because a Claude-only project has no reason to move.
CONFIG_PATHS = (
    ".graph-powers/config.json",
    ".claude/config.json",
)

# Where a *person* declares themselves, once, for every repository they open. Same filename and
# same shape as the project file — one config format, two scopes.
#
# Why this exists: until it did, `autonomy` was reachable only from inside a repository that
# carried the block. A person who had already decided "I do not want to approve every read"
# had to re-decide it per clone, and every repository without the block silently fell back to
# `guarded` — so the setting looked like it had stopped working when in fact it had never been
# asked. Autonomy is a property of the operator, not of the checkout.
#
# It sits UNDER the project file on purpose (`DEFAULTS < user < project`): a repository that
# states a rule is stating it for everyone who clones it, including a person whose personal
# posture is looser. The strictness a project ships is not the user's to relax by default.
USER_CONFIG_PATHS = (".graph-powers/config.json",)

# Only these blocks are read from the user file. The rest of the schema describes a repository —
# which branch is the work branch, where the frontend lives, what the test command is — and a
# value like that, applied from the home directory, is wrong in every repository except the one
# it was written for.
#
# `git` is the sharp one, and it is excluded deliberately. `optInPrefix` is per project by
# design: two repositories sharing a prefix would make an approval typed in one of them release
# the same gate in the other, and `test_hooks.py` proves that isolation. A user-level prefix
# would delete the guarantee for every project at once.
USER_SCOPED_KEYS = ("autonomy", "graphGuardrails", "protectedFiles", "autoUpdate")

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
        # Both ceilings above are counted inside this rolling window, not from session start. A
        # session that lives all day is normal work; twenty-five spawns inside an hour is not.
        "spawnWindowMinutes": 60,
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
    """The project's config file, or None when the project declares nothing."""
    root = root or project_dir()
    for rel in CONFIG_PATHS:
        candidate = root / rel
        try:
            if candidate.is_file():
                return candidate
        except Exception:
            continue
    return None


def user_config_path() -> Path | None:
    """The person's own config file, or None when they have never written one.

    `Path.home()` is the portable resolution: POSIX reads `HOME`, Windows reads `USERPROFILE`,
    and neither is spelled out anywhere in this repository — cardinal 2. It can raise on a
    machine with no resolvable home, which is why the whole lookup is guarded.
    """
    try:
        home = Path.home()
    except Exception:
        return None
    for rel in USER_CONFIG_PATHS:
        candidate = home / rel
        try:
            if candidate.is_file():
                return candidate
        except Exception:
            continue
    return None


def _read_config(path: Path | None) -> dict[str, Any]:
    """One config file as a dict. Missing, unreadable, or not an object all mean `no opinion`.

    Returning `{}` rather than raising is what keeps cardinal 3 true through two layers: a typo
    in the user's file must not take the session down, and it must not take the project's file
    down with it either.
    """
    if path is None:
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return raw if isinstance(raw, dict) else {}


def load(root: Path | None = None, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """The resolved config: `DEFAULTS < user < project`.

    The user layer is what makes a personal decision survive `git clone`. The project layer stays
    on top because a repository's own rules outrank the preferences of whoever opened it.
    """
    root = root or project_dir(payload)
    project_file = config_path(root)
    user_file = user_config_path()

    # Running a session inside the home directory itself would otherwise read one file as both
    # layers. Harmless — the merge is idempotent — but it makes `user_config_path()` look like it
    # found something it did not.
    if project_file is not None and user_file is not None:
        try:
            if project_file.resolve() == user_file.resolve():
                user_file = None
        except Exception:
            pass

    project = _read_config(project_file)
    user = {k: v for k, v in _read_config(user_file).items() if k in USER_SCOPED_KEYS}

    # `autonomy` is owned by whichever scope declares it, whole. Every other block deep-merges
    # field by field, which is right for them and wrong for this one, because `level` is a preset:
    # it decides `bashDefault`, `cleanup`, `commit` and `push` at once. Field-merging a user's
    # `git.commit: ask` under a project's `level: autonomous` leaves a repository that asked to run
    # unattended stopping at every commit — the project's own declaration silently half-applied.
    #
    # So a user's autonomy is what a repository gets when it has no opinion, and nothing more. The
    # direction this errs in is the safe one: an unrecognised block falls back to the defaults,
    # which ask.
    if isinstance(project.get("autonomy"), dict):
        user.pop("autonomy", None)

    cfg = _deep_merge(DEFAULTS, user)
    return _deep_merge(cfg, project)


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



# ── Declared versus runnable ─────────────────────────────────────────────────
#
# A command in `tooling.commands` is a declaration, not a capability. `session_context.py` prints
# `gates: lint+test` at the start of every session and `ultracite.py` runs the formatter after every
# edit — both from the same config, and both were silent when the tool itself was not installed.
# The formatter raised `FileNotFoundError` into an `except` that swallowed it, so a session could
# edit files for hours believing they were being formatted. The session tag said `lint` either way.
#
# That is the failure this module already names elsewhere: a line that reads as covered and never
# runs. So the question "is this command actually runnable" gets answered here, once, for every
# caller.

# Tokens that launch something else rather than being the tool. `npm`/`bun`/`pnpm`/`yarn` are here
# because `bunx biome check` needs *biome*; whether `bunx` exists says nothing about that.
_RUNNERS = frozenset({
    "npx", "bunx", "pnpm", "yarn", "npm", "bun", "deno", "uvx", "uv", "pipx", "poetry", "dlx",
})


def tool_of(command: str) -> str | None:
    """The executable a declared command needs, or None when that cannot be known.

    None is returned for `npm run lint` and friends: the real tool is named in the project's
    package manifest, not in the command, and guessing it would produce a confident wrong answer.
    Silence is the correct output there — this function is used to warn, and a warning that might
    be wrong is worse than none.
    """
    try:
        parts = shlex.split(str(command or ""), posix=(os.name != "nt"))
    except ValueError:
        return None
    skip_next_is_script = False
    for token in parts:
        bare = token.strip('"').strip("'")
        if not bare or bare.startswith("-"):
            continue
        if skip_next_is_script:
            return None                      # `<runner> run <script>` — the tool lives in the manifest
        if bare in _RUNNERS:
            skip_next_is_script = False
            continue
        if bare in ("run", "exec"):
            skip_next_is_script = True
            continue
        return bare
    return None


def missing_tool(command: str) -> str | None:
    """The tool this command needs and cannot find on PATH, or None when it resolves.

    Never raises: a config that cannot be parsed simply yields no warning.
    """
    name = tool_of(command)
    if not name:
        return None
    try:
        if shutil.which(name):
            return None
        # A declared path rather than a name on PATH — `./node_modules/.bin/biome`, `C:\t\b.exe`.
        if (os.sep in name or "/" in name) and Path(name).exists():
            return None
    except Exception:
        return None
    return name


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
