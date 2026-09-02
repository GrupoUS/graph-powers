---
name: perf
description: "Make something measurably faster, lighter or more findable — slow page, slow query, oversized bundle, poor Core Web Vitals, weak SEO or security baseline. Use when the user says something takes too long, feels sluggish, times out, or that the bundle is too big. Modes (positional) — default runtime audit · build · db · vercel · doctor · seo · sec. Pass URL, scope or strategy after the mode. Do not use when the output is wrong rather than slow ($graph-powers:debug)."
---

# $graph-powers:perf

This is the native Codex entrypoint for the Graph Powers command named `perf`.

1. Read `${CLAUDE_PLUGIN_ROOT}/commands/perf.md` completely before acting.
2. Treat the text after `$graph-powers:perf` as that command's arguments.
3. When the command names another Graph Powers slash command, invoke the matching
   `$graph-powers:<name>` skill; do not send that slash token to Codex's built-in parser.
