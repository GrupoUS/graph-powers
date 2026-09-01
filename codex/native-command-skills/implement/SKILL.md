---
name: implement
description: "Execute an approved implementation plan through planning Phase C. Use when the user says implement, build or execute an existing plan. Supports only --dry-run; use $graph-powers:plan to decide what to build and $graph-powers:verify to confirm the result."
---

# $graph-powers:implement

This is the native Codex entrypoint for the Graph Powers command named `implement`.

1. Read `${CLAUDE_PLUGIN_ROOT}/commands/implement.md` completely before acting.
2. Treat the text after `$graph-powers:implement` as that command's arguments.
3. When the command names another Graph Powers slash command, invoke the matching
   `$graph-powers:<name>` skill; do not send that slash token to Codex's built-in parser.
