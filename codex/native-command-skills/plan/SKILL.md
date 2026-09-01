---
name: plan
description: "Decide how to build a multi-step feature before code: scope, architecture trade-offs, integrations, ordering, issue triage and implementation plans. Routes all planning through the planning skill. Do not use to execute an existing plan or fix a known bug."
---

# $graph-powers:plan

This is the native Codex entrypoint for the Graph Powers command named `plan`.

1. Read `${CLAUDE_PLUGIN_ROOT}/commands/plan.md` completely before acting.
2. Treat the text after `$graph-powers:plan` as that command's arguments.
3. When the command names another Graph Powers slash command, invoke the matching
   `$graph-powers:<name>` skill; do not send that slash token to Codex's built-in parser.
