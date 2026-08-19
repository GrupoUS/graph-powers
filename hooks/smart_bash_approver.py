#!/usr/bin/env python3
"""smart_bash_approver.py - how much runs without stopping to ask.

Trigger: PreToolUse (Bash). Reads a JSON payload on stdin, writes a decision.

Three tiers, and the middle one is configurable:

  DESTRUCTIVE FLOOR   always denied while `autonomy.destructiveFloor` holds — the operations git
                      cannot undo. Deleting a file inside a committed repository is NOT here: git
                      restores that, so autonomous mode does it without asking.
  KNOWN SAFE          always allowed: reads, inspections, the project's own tooling.
  EVERYTHING ELSE     `autonomy.bashDefault`. Under `guarded` it asks, which is where almost every
                      approval prompt comes from. Under `autonomous` it runs.

Fail-open, like every hook here: an unreadable config resolves to the guarded defaults rather than
taking the session down.
"""

import json
import re
import sys
import typing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _config as gp  # noqa: E402

LEADING_CD_PATTERN = re.compile(r"^cd\s+[^&;]+\s+&&\s+")


def normalize_command(raw_command: str) -> str:
    command = raw_command.strip()

    while True:
        normalized = LEADING_CD_PATTERN.sub("", command, count=1).strip()
        if normalized == command:
            return command
        command = normalized


# ── Dangerous patterns (always block) ──
DANGEROUS_PATTERNS = [
    # Destructive shell operations
    re.compile(r"^rm -rf /"),
    re.compile(r"^rm -rf ~"),
    re.compile(r"^rm -rf \$HOME"),
    re.compile(r"^:\(\)\{ :\|:& \};:"),
    re.compile(r"^chmod -R 777 /"),
    re.compile(r"^dd if=.*of=/dev/"),
    re.compile(r"^> /dev/sd"),
    re.compile(r"^sudo rm"),
    re.compile(r"^truncate -s 0"),
    re.compile(r"^> /etc/"),
    re.compile(r"^mkfs"),
    re.compile(r"^dd if=/dev/zero"),
    re.compile(r"rm --no-preserve-root"),
    re.compile(r"chmod -R 000"),
    # Database destructive commands
    re.compile(r"^DROP DATABASE", re.IGNORECASE),
    re.compile(r"^DROP TABLE", re.IGNORECASE),
    re.compile(r"^TRUNCATE", re.IGNORECASE),
    # A force-push rewrites history for everyone who already pulled it.
    re.compile(r"^git\s+push\b.*(--force|-f)\b"),
]

# ── Cleanup patterns (require user approval) ──
CLEANUP_PATTERNS = [
    re.compile(r"(^|\s)rm\s+-rf\s+"),
    re.compile(r"(^|\s)rm\s+-r\s+"),
    re.compile(r"\.turbo/.*\.log"),
    re.compile(r"\.old_modules"),
    re.compile(r"\.sisyphus/.*\.log"),
    re.compile(r"node_modules/\.cache"),
    re.compile(r"\.turbo$"),
    re.compile(r"__pycache__"),
    re.compile(r"\.next/cache"),
    re.compile(r"dist/.*\.log"),
]

# ── Safe patterns (auto-approve) ──
SAFE_PATTERNS = [
    # Git read commands only
    re.compile(r"^git( --no-pager)? status(\s|$)"),
    re.compile(r"^git( --no-pager)? diff(\s|$)"),
    re.compile(r"^git( --no-pager)? log(\s|$)"),
    re.compile(r"^git( --no-pager)? branch(\s+(-a|-r|-v|-vv|--show-current))*\s*$"),
    re.compile(r"^git( --no-pager)? fetch(\s|$)"),
    re.compile(r"^git( --no-pager)? show(\s|$)"),
    re.compile(r"^git( --no-pager)? stash (list|show)(\s|$)"),
    re.compile(r"^git( --no-pager)? remote(\s|$)"),
    re.compile(r"^git( --no-pager)? reflog(\s|$)"),
    re.compile(r"^git( --no-pager)? rev-parse(\s|$)"),
    re.compile(r"^git( --no-pager)? blame(\s|$)"),
    re.compile(r"^git( --no-pager)? grep(\s|$)"),
    re.compile(r"^gh pr (view|list|status)(\s|$)"),
    re.compile(r"^gh run (view|list)(\s|$)"),
    re.compile(r"^gh issue (view|list)(\s|$)"),
    re.compile(r"^gh repo view(\s|$)"),
    # Filesystem read
    re.compile(r"^ls(\s|$)"),
    re.compile(r"^cat "),
    re.compile(r"^head "),
    re.compile(r"^tail "),
    re.compile(r"^grep "),
    re.compile(r"^rg "),
    re.compile(r"^find "),
    re.compile(r"^which "),
    re.compile(r"^pwd$"),
    re.compile(r"^echo "),
    re.compile(r"^tree(\s|$)"),
    re.compile(r"^stat "),
    re.compile(r"^wc -"),
    re.compile(r"^cut "),
    re.compile(r"^sort "),
    re.compile(r"^uniq "),
    re.compile(r"^column -t"),
    re.compile(r"^less "),
    re.compile(r"^more "),
    # Bun-only package manager development commands
    re.compile(r"^bun run (lint|build|predeploy|format|lint:fix)(\s|$)"),
    re.compile(r"^bun install(\s|$)"),
    re.compile(r"^bun -"),
    re.compile(r"^bun x "),
    re.compile(r"^bunx "),
    re.compile(r"^tsgo(\s|$)"),
    re.compile(r"^tsc(\s|$)"),
    re.compile(r'^python(3)?( -X [^ ]+)? "?\.claude/'),
    re.compile(r'^python(3)?( -X [^ ]+)? "?scripts/'),
    re.compile(r'^py -3 "?\.claude/'),
    re.compile(r'^py -3 "?scripts/'),
    # Optional local CLIs (read-only introspection)
    re.compile(r"^(psql|mysql|sqlite3) "),
    # Version checks (Bun-only for package managers)
    re.compile(r"^(python3?|bun|node|deno|docker|git|tsgo|tsc) --version"),
    # Local reversible filesystem helpers
    re.compile(r"^mkdir -p"),
    re.compile(r"^touch "),
    re.compile(r"^cp (-r )?"),
    re.compile(r"^chmod \+x"),
    re.compile(r"^chmod (755|644)"),
    # Process / system read
    re.compile(r"^ps (aux|-ef)"),
    re.compile(r"^(top|htop|free|df|du|uptime|whoami|id) "),
    re.compile(r"^(free|df|du|uptime|whoami|id)$"),
    # Network read
    re.compile(r"^curl -"),
    re.compile(r"^wget -"),
    re.compile(r"^ping -"),
    re.compile(r"^(ssh -V|nc -zv|telnet)"),
    # Build / lint tools
    re.compile(r"^biome(\s|$)"),
    re.compile(r"^tsgo --"),
    re.compile(r"^vite --version"),
    # Optional visual/E2E commands should stay explicit in project scripts.
    re.compile(r"^bun run lighthouse:audit(\s|$)"),
]

# Commands that are often legitimate but must remain user-mediated.
ASK_PATTERNS = [
    re.compile(
        r"^git\s+(add|commit|checkout|switch|restore|clean|rebase|merge|pull|push|reset)\b"
    ),
    re.compile(r"^gh\s+pr\s+create\b"),
    re.compile(r"^gh\s+issue\s+create\b"),
    re.compile(r"^mv\s+"),
    re.compile(r"^rsync\b"),
    re.compile(r"^chown\b"),
    re.compile(r"^bun\s+run\s+(dev|start|preview)\b"),
]

# Any package manager. Which ones a project accepts is `autonomy.allowPackageManagers`; by default
# all of them do, because a plugin that hardcodes one breaks every project that chose another.
PACKAGE_MANAGER_RE = re.compile(r"^(bun|bunx|npm|npx|pnpm|pnpx|yarn|corepack|uv|uvx|pip|pipx|poetry|cargo|go)\b")
DANGEROUS_PM_PATTERN = re.compile(r"(rm -rf|cache clean|publish.*--force)")
COMMAND_SEPARATOR_PATTERN = re.compile(r"\s*(?:&&|\|\||;)\s*")


def read_input() -> dict[str, object]:
    try:
        raw = sys.stdin.read()
        return typing.cast(dict[str, object], json.loads(raw)) if raw.strip() else {}
    except Exception:
        return {}


def _allow() -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                }
            }
        )
    )


def _deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )


def _ask(reason: str | None = None) -> None:
    payload: dict[str, object] = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
        }
    }
    if reason:
        typing.cast(dict[str, object], payload["hookSpecificOutput"])[
            "permissionDecisionReason"
        ] = reason
    print(json.dumps(payload))


def _matches(patterns: list[re.Pattern[str]], command: str) -> bool:
    return any(pattern.search(command) for pattern in patterns)


def _classify(command: str, policy: dict[str, object]) -> tuple[str, str | None]:
    """Return (allow|ask|deny, optional reason) for one shell segment."""
    if policy["destructiveFloor"] and _matches(DANGEROUS_PATTERNS, command):
        return (
            "deny",
            "BLOCKED: Dangerous, non-Bun, or branch-protected command detected",
        )

    if _matches(CLEANUP_PATTERNS, command):
        return policy["cleanup"], (
            None if policy["cleanup"] == "allow" else "Cleanup operation — requires approval"
        )

    if _matches(SAFE_PATTERNS, command):
        if PACKAGE_MANAGER_RE.match(command) and DANGEROUS_PM_PATTERN.search(command):
            return "deny", "BLOCKED: destructive package-manager command"
        return "allow", None

    if _matches(ASK_PATTERNS, command):
        return policy["bashDefault"], (
            None if policy["bashDefault"] == "allow"
            else "State-changing or external command — requires approval"
        )

    if PACKAGE_MANAGER_RE.match(command):
        if DANGEROUS_PM_PATTERN.search(command):
            return "deny", "BLOCKED: destructive package-manager command"
        return "allow", None

    return policy["bashDefault"], None


def main() -> None:
    data: dict[str, object] = read_input()
    command: str = normalize_command(
        str(
            data.get("command")
            or typing.cast(dict[str, object], data.get("tool_input", {})).get(
                "command", ""
            )
        )
    )

    if not command:
        _ask()
        return

    policy = gp.autonomy(gp.load(payload=data))

    # A project that declares which package managers it accepts gets the others refused — a
    # lockfile that forks is a real defect. A project that declares none accepts all of them.
    allowed_pms = policy.get("allowPackageManagers") or []
    if allowed_pms:
        pm = PACKAGE_MANAGER_RE.match(command)
        if pm and pm.group(1) not in allowed_pms:
            _deny(
                f"BLOCKED: this project declares its package managers as "
                f"{', '.join(allowed_pms)}; `{pm.group(1)}` is not one of them "
                "(autonomy.allowPackageManagers)."
            )
            return

    segments = [
        segment.strip()
        for segment in COMMAND_SEPARATOR_PATTERN.split(command)
        if segment.strip()
    ]

    final_decision = "allow"
    ask_reason: str | None = None
    for segment in segments or [command]:
        decision, reason = _classify(segment, policy)
        if decision == "deny":
            _deny(reason or "BLOCKED: Dangerous command")
            return
        if decision == "ask":
            final_decision = "ask"
            ask_reason = ask_reason or reason

    if final_decision == "allow":
        _allow()
        return

    # Unknown or state-changing commands require user approval. Never fall
    # through to allow — unknown commands may be destructive tools, typos, or
    # untrusted invocations.
    _ask(ask_reason)


if __name__ == "__main__":
    main()
    sys.exit(0)
