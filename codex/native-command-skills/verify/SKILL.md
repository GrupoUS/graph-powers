---
name: verify
description: "Prove the work actually holds before it is handed off — runs the gates the project declared, checks the safety floor, and returns a verdict with the command output behind it. Use when the user asks whether this is done, to run the gates, to check nothing broke, or before claiming any L3+ task complete. Do not use to review a diff for quality ($graph-powers:pr-review) or to chase a gate that is already failing ($graph-powers:debug)."
---

# $graph-powers:verify

This is the native Codex entrypoint for the Graph Powers command named `verify`.

1. Read `${CLAUDE_PLUGIN_ROOT}/commands/verify.md` completely before acting.
2. Treat the text after `$graph-powers:verify` as that command's arguments.
3. When the command names another Graph Powers slash command, invoke the matching
   `$graph-powers:<name>` skill; do not send that slash token to Codex's built-in parser.
