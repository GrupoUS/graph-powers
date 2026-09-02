---
name: research
description: "Investigate without changing anything — how this codebase does X, what a library or API actually supports, what a change would touch. Use when the user says to look into it, find out how something works, or explicitly not to edit yet. Explores the codebase and external docs in parallel and returns structured findings only. Do not use to then fix what it found ($graph-powers:debug) or to turn it into a plan ($graph-powers:plan)."
---

# $graph-powers:research

This is the native Codex entrypoint for the Graph Powers command named `research`.

1. Read `${CLAUDE_PLUGIN_ROOT}/commands/research.md` completely before acting.
2. Treat the text after `$graph-powers:research` as that command's arguments.
3. When the command names another Graph Powers slash command, invoke the matching
   `$graph-powers:<name>` skill; do not send that slash token to Codex's built-in parser.
