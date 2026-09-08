---
name: evolve
description: "Capture a session learning so the next one inherits it. Modes: default capture, auto for the AutoResearch Loop, handoff for session state. Do not store a personal preference in repository rules."
---

# $graph-powers:evolve

This is the native Codex entrypoint for the Graph Powers command named `evolve`.

1. Read `${CLAUDE_PLUGIN_ROOT}/commands/evolve.md` completely before acting.
2. Treat the text after `$graph-powers:evolve` as that command's arguments.
3. When the command names another Graph Powers slash command, invoke the matching
   `$graph-powers:<name>` skill; do not send that slash token to Codex's built-in parser.
