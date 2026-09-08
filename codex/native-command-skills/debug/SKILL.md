---
name: debug
description: "Diagnose and fix a defect — error, crash, failing test, 500, hydration mismatch, CI failure or regression. Modes: default triage/fix; audit; frontend; backend; auth-db; recover. Do not use for new behavior ($graph-powers:implement), review ($graph-powers:pr-review), or gate proof ($graph-powers:verify)."
---

# $graph-powers:debug

This is the native Codex entrypoint for the Graph Powers command named `debug`.

1. Read `${CLAUDE_PLUGIN_ROOT}/commands/debug.md` completely before acting.
2. Treat the text after `$graph-powers:debug` as that command's arguments.
3. When the command names another Graph Powers slash command, invoke the matching
   `$graph-powers:<name>` skill; do not send that slash token to Codex's built-in parser.
