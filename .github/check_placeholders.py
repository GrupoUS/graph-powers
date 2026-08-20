#!/usr/bin/env python3
"""Every `${config.key}` an artefact reads has to exist in schema/config.schema.json.

A placeholder with no schema entry is a promise nothing keeps. The agent resolves it to an empty
string, the instruction reads as satisfied, and the gate it was supposed to name never runs — the
failure looks like a clean report. Thirteen such keys shipped in an earlier version of this
harness; this gate is what stops the fourteenth.

Fenced code blocks are skipped: `${base}` inside a JavaScript template literal is a language
feature, not a config read, and treating it as one would train people to add exemptions.

Run from the repository root:  python3 .github/check_placeholders.py
"""

from __future__ import annotations

import glob
import json
import re
import sys
from typing import Any

# Names resolved by something other than the project config: the harness itself, and the
# parameters the rule templates take when they are instantiated.
EXEMPT = {"CLAUDE_PLUGIN_ROOT", "rulesDir", "SCOPE", "PROJECT_NAME"}

PLACEHOLDER = re.compile(r"\$\{([a-zA-Z][a-zA-Z0-9_.]*)\}")
FENCE = re.compile(r"^\s*(```|~~~)")


def strip_code_blocks(text: str) -> str:
    out, inside = [], False
    for line in text.splitlines():
        if FENCE.match(line):
            inside = not inside
            continue
        out.append("" if inside else line)
    return "\n".join(out)


def declared(schema: dict[str, Any], dotted: str) -> bool:
    node: Any = schema.get("properties", {})
    for part in dotted.split("."):
        if not isinstance(node, dict):
            return False
        props = node.get("properties") if "properties" in node else node
        if not isinstance(props, dict) or part not in props:
            # A group declared without `properties` accepts anything below it — `commands` is one.
            return isinstance(node, dict) and node.get("type") == "object" and "properties" not in node
        node = props[part]
    return True


def main() -> int:
    with open("schema/config.schema.json", encoding="utf-8") as fh:
        schema = json.load(fh)

    files: list[str] = []
    for root in ("skills", "commands", "agents", "references", "templates"):
        files += glob.glob(f"{root}/**/*.md", recursive=True)

    undeclared: dict[str, list[str]] = {}
    for path in sorted(files):
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = strip_code_blocks(fh.read())
        for name in set(PLACEHOLDER.findall(text)):
            if name in EXEMPT or name.startswith("CLAUDE_") or name.isupper():
                continue
            if not declared(schema, name):
                undeclared.setdefault(name, []).append(path)

    for name, where in sorted(undeclared.items()):
        print(f"UNDECLARED: ${{{name}}}  <- {', '.join(sorted(set(where))[:3])}")
    if undeclared:
        print("::error::a placeholder no schema key backs resolves to nothing, silently")
    else:
        print(f"{len(files)} artefacts scanned, every placeholder is a declared config key")
    return 1 if undeclared else 0


if __name__ == "__main__":
    sys.exit(main())
