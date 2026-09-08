---
paths:
  - "agents/**"
  - "skills/**"
  - "commands/**"
  - "references/**"
  - "workflows/**"
---

# Distributed artifact contract

Keep names and YAML valid, descriptions trigger-focused, and agent `tools:` explicit. Read-only
agents require `disallowedTools: Write, Edit`, including when `memory:` is present. Every artifact
needs a live invocation; plugin-owned paths use `${CLAUDE_PLUGIN_ROOT}` and host paths use declared
placeholders.

Workflow files use literal `meta`, a filename-matching name, namespaced agent types, and explicit
models; validate them with `bun .github/check_workflows.mjs`.

For a behavior change to an agent, skill, command, reference, or workflow, load the relevant method
and run the focused validation. A mechanical text correction does not require a harness audit.
