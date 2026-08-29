#!/usr/bin/env python3
"""The version is the delivery channel. A change that does not bump it never reaches anyone.

`claude plugin update` compares the **version** in `.claude-plugin/plugin.json`, not the commit it
came from. Push a fix without bumping, and every installed machine keeps the old files while the
command cheerfully reports "already at the latest version". That is worse than no updater: the
report says covered and the guardrail is the old one.

This is not a style rule, so it is not left to memory. Touch anything the plugin ships, and the
version has to move in the same change.

Run from the repository root:  python3 .github/check_version_bump.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import cast

# What a user actually receives. Docs, CI config and the repository's own rules are excluded:
# nobody's installed harness behaves differently because CONTRIBUTING.md gained a paragraph.
SHIPPED = (
    "agents/", "skills/", "commands/", "hooks/", "references/", "templates/", "workflows/",
    "schema/", "codex/", "cursor/", "grok/", "hermes/", "bin/", ".claude-plugin/", ".cursor-plugin/",
    ".grok-plugin/", "examples/", "plugin.yaml", "__init__.py",
    "DESIGN.md", "PRODUCT.md", "REVIEW.md", "AGENT_SETUP.md",
)


def run(*args: str) -> str:
    return subprocess.run(args, capture_output=True, encoding="utf-8", errors="replace",
                          check=False).stdout.strip()


def base_ref() -> str:
    """What to compare against: the PR's base, or the previous commit on a push."""
    if os.environ.get("GITHUB_BASE_REF"):
        base = f"origin/{os.environ['GITHUB_BASE_REF']}"
        _ = run("git", "fetch", "--quiet", "--depth", "50", "origin", os.environ["GITHUB_BASE_REF"])
        return base
    before = os.environ.get("GITHUB_EVENT_BEFORE") or ""
    if before and not set(before) <= {"0"} and run("git", "cat-file", "-t", before) == "commit":
        return before
    return "HEAD~1"


def version_at(ref: str, path: str) -> str:
    """The version recorded at a git ref, or "" when the file is absent or unreadable there."""
    raw = run("git", "show", f"{ref}:{path}")
    if not raw:
        return ""
    try:
        data = cast("dict[str, object]", json.loads(raw))
        return str(data.get("version") or "")
    except (ValueError, AttributeError):
        return ""


def version_on_disk(path: str) -> str:
    """The version of a manifest in the checkout. Malformed JSON still raises, as it must."""
    data = cast("dict[str, object]", json.loads(Path(path).read_text(encoding="utf-8")))
    return str(data.get("version") or "")


def main() -> int:
    manifest = ".claude-plugin/plugin.json"
    here = version_on_disk(manifest)
    pkg = version_on_disk("package.json")

    cursor_path = ".cursor-plugin/plugin.json"
    cursor_ver = version_on_disk(cursor_path) if Path(cursor_path).exists() else here
    grok_path = ".grok-plugin/plugin.json"
    grok_ver = version_on_disk(grok_path) if Path(grok_path).exists() else here

    if here != pkg or here != cursor_ver or here != grok_ver:
        print(
            f"::error::plugin.json says {here}, package.json says {pkg}, "
            f".cursor-plugin/plugin.json says {cursor_ver}, "
            f".grok-plugin/plugin.json says {grok_ver} — they must match"
        )
        return 1

    base = base_ref()
    if run("git", "cat-file", "-t", base) != "commit":
        print(f"no comparable base ({base}) — first commit, or a shallow checkout. Skipping.")
        return 0

    changed = run("git", "diff", "--name-only", base, "HEAD").splitlines()
    shipped = [f for f in changed if f.startswith(SHIPPED)]
    if not shipped:
        print(f"{len(changed)} file(s) changed, none of them shipped — no bump needed")
        return 0

    before = version_at(base, manifest)
    if before and before == here:
        print("\n".join(f"  shipped: {f}" for f in shipped[:10]))
        if len(shipped) > 10:
            print(f"  ... and {len(shipped) - 10} more")
        print(" ".join([
            f"::error::{len(shipped)} shipped file(s) changed and the version is still {here}.",
            "Installed machines compare versions, not commits — without a bump this change",
            "reaches nobody. Bump plugin.json and package.json together.",
        ]))
        return 1

    print(f"{len(shipped)} shipped file(s) changed, version {before or '?'} -> {here}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
