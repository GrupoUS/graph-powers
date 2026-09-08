---
name: research
description: "Investigate without changes: how this codebase works, what a library/API supports, or what a change touches. Findings only; not for fixing ($graph-powers:debug) or planning ($graph-powers:plan)."
---

# $graph-powers:research

This is the native Codex entrypoint for the Graph Powers command named `research`.

1. Read `${CLAUDE_PLUGIN_ROOT}/commands/research.md` completely before acting.
2. Treat the text after `$graph-powers:research` as that command's arguments.
3. When the command names another Graph Powers slash command, invoke the matching
   `$graph-powers:<name>` skill; do not send that slash token to Codex's built-in parser.
