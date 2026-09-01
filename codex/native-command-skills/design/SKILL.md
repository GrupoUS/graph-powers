---
name: design
description: "Use when creating or improving UI layout, type, hierarchy, tokens, states, responsiveness or direction. Routes new work to designer and existing repair to design-fix. Not for broken behavior ($graph-powers:debug) or speed ($graph-powers:perf)."
---

# $graph-powers:design

This is the native Codex entrypoint for the Graph Powers command named `design`.

1. Read `${CLAUDE_PLUGIN_ROOT}/commands/design.md` completely before acting.
2. Treat the text after `$graph-powers:design` as that command's arguments.
3. When the command names another Graph Powers slash command, invoke the matching
   `$graph-powers:<name>` skill; do not send that slash token to Codex's built-in parser.
