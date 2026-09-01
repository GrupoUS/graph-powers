---
name: evolve
description: "Turn what this session learned into something the next one inherits — updates the project's rules and AGENTS.md so a mistake does not recur. Use when the user says to capture the learning, make sure this does not happen again, or write the convention down. Do not use for a personal preference, which belongs in memory rather than in the repository."
---

# $graph-powers:evolve

This is the native Codex entrypoint for the Graph Powers command named `evolve`.

1. Read `${CLAUDE_PLUGIN_ROOT}/commands/evolve.md` completely before acting.
2. Treat the text after `$graph-powers:evolve` as that command's arguments.
3. When the command names another Graph Powers slash command, invoke the matching
   `$graph-powers:<name>` skill; do not send that slash token to Codex's built-in parser.
