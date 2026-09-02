---
name: pr-review
description: "Review a PR, branch or diff before merge. Uses one adversarial Evaluator plus only surface-required security/design specialists, then returns prioritized findings, a verdict and a ready comment. Read-only unless --fix; never approves or merges. Modes — <PR#> · --current · --branch <name> · full. Flags — --quick, --fix. Not for plan execution ($graph-powers:implement) or gate proof ($graph-powers:verify)."
---

# $graph-powers:pr-review

This is the native Codex entrypoint for the Graph Powers command named `pr-review`.

1. Read `${CLAUDE_PLUGIN_ROOT}/commands/pr-review.md` completely before acting.
2. Treat the text after `$graph-powers:pr-review` as that command's arguments.
3. When the command names another Graph Powers slash command, invoke the matching
   `$graph-powers:<name>` skill; do not send that slash token to Codex's built-in parser.
