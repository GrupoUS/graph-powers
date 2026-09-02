---
name: debug
description: "Diagnose and fix a defect — error, crash, stack trace, failing test, 500, hydration mismatch, CI gone red, or behaviour that changed after a deploy. Use when the user reports something broken, pastes an error, says a test is failing, says it worked yesterday, or asks why staging differs from local. Modes (positional) — default: triage and fix · audit: 9-dimension full-stack audit · frontend: React/UI plus browser E2E · backend: API and services · auth-db: auth, permissions, RLS · recover: after two or more failed attempts, when the user says we tried three times and it is still broken, that we are going in circles, or asks to back out and start over. Do not use to add behaviour that never worked ($graph-powers:implement), to judge code that already works ($graph-powers:pr-review), or to prove gates pass ($graph-powers:verify)."
---

# $graph-powers:debug

This is the native Codex entrypoint for the Graph Powers command named `debug`.

1. Read `${CLAUDE_PLUGIN_ROOT}/commands/debug.md` completely before acting.
2. Treat the text after `$graph-powers:debug` as that command's arguments.
3. When the command names another Graph Powers slash command, invoke the matching
   `$graph-powers:<name>` skill; do not send that slash token to Codex's built-in parser.
