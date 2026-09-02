---
name: setup
description: "Diagnose the local Oxc (Oxlint/Oxfmt), TypeScript 7, vtsls and Zed setup without changing the machine. Use when the user asks to configure or check project toolchain, editor diagnostics, format-on-save or competing linters and formatters. Reports missing tools and compatibility blockers, then prints local package-manager commands and a portable project-settings example. Never installs packages or edits global editor settings."
---

# $graph-powers:setup

This is the native Codex entrypoint for the Graph Powers command named `setup`.

1. Read `${CLAUDE_PLUGIN_ROOT}/commands/setup.md` completely before acting.
2. Treat the text after `$graph-powers:setup` as that command's arguments.
3. When the command names another Graph Powers slash command, invoke the matching
   `$graph-powers:<name>` skill; do not send that slash token to Codex's built-in parser.
