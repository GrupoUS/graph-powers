---
name: implement
description: "Execute an approved implementation plan through planning Phase C. Supports only --dry-run; use $graph-powers:plan to decide and $graph-powers:verify to confirm."
---

# $graph-powers:implement

This is the native Codex entrypoint for the Graph Powers command named `implement`.

1. Read `${CLAUDE_PLUGIN_ROOT}/commands/implement.md` completely before acting.
2. Treat the text after `$graph-powers:implement` as that command's arguments.
3. When the command names another Graph Powers slash command, invoke the matching
   `$graph-powers:<name>` skill; do not send that slash token to Codex's built-in parser.
