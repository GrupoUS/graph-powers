---
name: verify
description: "Prove work holds before handoff: declared gates, safety floor, and an evidence-backed verdict. Modes: quick, full, loop. Use before claiming L3+ complete; not for review ($graph-powers:pr-review) or fixing failures ($graph-powers:debug)."
---

# $graph-powers:verify

This is the native Codex entrypoint for the Graph Powers command named `verify`.

1. Read `${CLAUDE_PLUGIN_ROOT}/commands/verify.md` completely before acting.
2. Treat the text after `$graph-powers:verify` as that command's arguments.
3. When the command names another Graph Powers slash command, invoke the matching
   `$graph-powers:<name>` skill; do not send that slash token to Codex's built-in parser.
