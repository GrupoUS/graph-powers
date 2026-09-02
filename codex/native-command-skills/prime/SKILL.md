---
name: prime
description: "Load this project's context at the start of a session — rules, conventions, stack, the paths that matter. Use when the user asks to load context, get up to speed, or what the conventions here are. Modes (positional) — default: auto-classify · backend · frontend · fullstack. Loads the minimum viable context, never eagerly. Do not use to locate one specific thing ($graph-powers:research)."
---

# $graph-powers:prime

This is the native Codex entrypoint for the Graph Powers command named `prime`.

1. Read `${CLAUDE_PLUGIN_ROOT}/commands/prime.md` completely before acting.
2. Treat the text after `$graph-powers:prime` as that command's arguments.
3. When the command names another Graph Powers slash command, invoke the matching
   `$graph-powers:<name>` skill; do not send that slash token to Codex's built-in parser.
