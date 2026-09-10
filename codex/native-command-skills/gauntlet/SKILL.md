---
name: gauntlet
description: "Use only for $graph-powers:gauntlet objective/plan or --dry-run; excludes L1-L2/generic."
---

# $graph-powers:gauntlet

This is the native Codex entrypoint for the Graph Powers command named `gauntlet`.

1. Read `${CLAUDE_PLUGIN_ROOT}/commands/gauntlet.md` completely before acting.
2. Treat the text after `$graph-powers:gauntlet` as that command's arguments.
3. When the command names another Graph Powers slash command, invoke the matching
   `$graph-powers:<name>` skill; do not send that slash token to Codex's built-in parser.
