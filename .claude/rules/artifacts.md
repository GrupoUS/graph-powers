---
paths:
  - "agents/**"
  - "skills/**"
  - "commands/**"
  - "references/**"
---

# The contract for distributed artefacts

Applies to everything that travels to the projects: `agents/`, `skills/`, `commands/`, `references/`.

## Frontmatter

- `name` identical to the file or folder name. A divergence breaks invocation silently.
- `description` says **when** to use it, not what it is. It is what the model chooses on.
- `description` must be valid YAML. A value containing `: ` needs quoting — four command files here
  once did not parse at all, and nothing noticed because CI only validated agents.
- `tools:` explicit in every agent. **Without that field the agent inherits the entire toolset,
  including `Write` and `Edit`** — and the read-only promise written in the body becomes decoration.
- `disallowedTools: Write, Edit` in every agent that judges or researches.
- `model:` declared in whoever judges. Never `inherit` in an evaluator.

## The `memory:` trap

The `memory:` field injects `Read`, `Write` and `Edit` into the resolved set, **on top of** the
`tools:` allowlist. Measured: an agent declaring `tools: [Read]` plus `memory: project` resolves
with `Read, Write, Edit`. That is how a researcher became write-capable against its own description.

If the agent needs memory and must not write, declare both: `memory:` and `disallowedTools`.

## No coupling

No artefact names a product, domain, table, external provider, branch or variable prefix. What
varies per project comes from `.graph-powers/config.json` through the contract in
`schema/config.schema.json`.

Paths between artefacts inside the same skill are relative (`references/x.md`). Paths to another
part of the plugin go through `${CLAUDE_PLUGIN_ROOT}/...`, because a bare `references/x.md` read
from a command resolves against the wrong directory. Paths into the host project go through
`${rulesDir}` and the other config placeholders.

## What invokes it

Every artefact needs a real call site. An agent no skill dispatches, and a skill no routing
mentions, are dead weight in the context budget of every session. The audit that produced this
repository found 13 orphans of exactly that kind.
