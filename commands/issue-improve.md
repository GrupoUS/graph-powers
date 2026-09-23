---
description: "Turn a GitHub issue into a reviewed plan comment. Planning only."
---

# /issue-improve

**ARGUMENTS:** $ARGUMENTS.

When an issue is supplied, read `${CLAUDE_PLUGIN_ROOT}/skills/issue-improve/SKILL.md` and apply it
with the original arguments. The skill acknowledges first and owns config, one bounded plan route and
approval. On `BLOCKED`/cap, preserve state and stop without retry. Empty asks for an issue.
