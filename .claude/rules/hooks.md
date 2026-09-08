---
paths:
  - "hooks/**"
  - ".claude-plugin/plugin.json"
  - ".cursor-plugin/plugin.json"
  - ".grok-plugin/plugin.json"
  - "codex/**"
  - "cursor/**"
  - "grok/**"
---

# Hook contract

`hooks/AGENTS.md` is the canonical hook method. Keep hooks fail-open, configuration-driven,
portable, registered from `hooks/hooks.json`, and covered by deny, allow, and malformed-input
tests. Preserve project-scoped opt-ins and client-specific lifecycle limits; projections are
generated, not hand-maintained.
