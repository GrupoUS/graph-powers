---
name: perf
description: "Make something measurably faster, lighter or more findable. Modes: runtime audit, build, db, vercel, doctor, seo and sec; `resources`, `hooks`, and `tests` use the resource audit. Do not use when output is wrong ($graph-powers:debug)."
---

# $graph-powers:perf

This is the native Codex entrypoint for the Graph Powers command named `perf`.

1. Read `${CLAUDE_PLUGIN_ROOT}/commands/perf.md` completely before acting.
2. Treat the text after `$graph-powers:perf` as that command's arguments.
3. When the command names another Graph Powers slash command, invoke the matching
   `$graph-powers:<name>` skill; do not send that slash token to Codex's built-in parser.
