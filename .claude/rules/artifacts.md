---
paths:
  - "agents/**"
  - "skills/**"
  - "commands/**"
  - "references/**"
  - "workflows/**"
---

# The contract for distributed artefacts

Applies to everything that travels to the projects: `agents/`, `skills/`, `commands/`,
`references/`, `workflows/`.

## Frontmatter

- `name` identical to the file or folder name. A divergence breaks invocation silently.
- `description` says **when** to use it, not what it is. It is what the model chooses on.
- `description` must be valid YAML. A value containing `: ` needs quoting — four command files here
  once did not parse at all, and nothing noticed because CI only validated agents.
- `tools:` explicit in every agent. **Without that field the agent inherits the entire toolset,
  including `Write` and `Edit`** — and the read-only promise written in the body becomes decoration.
- `disallowedTools: Write, Edit` in every agent that judges or researches. **Inline,
  comma-separated** — that is the shape the plugin reference documents, and `python3
  .github/check_wiring.py` holds the twelve to it so the set stays uniform.

  A caveat about why, because the first version of this line was wrong: a YAML block sequence was
  blamed for `security-reviewer` and `skill-improver` being unspawnable. They were not. The CLI's
  own registry listed both while they still carried the block form; what did not list them was a
  third-party `PreToolUse` hook with a hardcoded allowlist written before either agent existed. The
  inline form is required by documentation, not by an observed failure — do not cite an incident
  that did not happen.
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

This rule file loads whenever you touch `agents/`, `skills/`, `commands/`, `references/` or
`workflows/` — which is exactly the territory `Skill("skill-improve")` owns. Invoke it when the
edit is more than a typo: Mode A for the body or description of one artefact, Mode B before adding
an agent or a skill and after any model or plugin upgrade, to check that what you just wired still
resolves. The path glob above is the only automatic trigger in this repository that does not depend
on a model reading a description and deciding.

## Workflow scripts

`workflows/*.js` has no frontmatter and none of the rules above about it. Its own contract:

- `export const meta` is a **pure literal** — no variable, call, spread or interpolation. The
  runtime reads it before the body runs, and a computed field fails the whole script.
- `meta.name` identical to the filename. Claude Code registers it as `graph-powers:<name>`.
- Every `agentType` carries the `graph-powers:` prefix. Without it the spawn fails with
  `agent type '<name>' not found`, because a workflow resolves against the global registry, not the
  plugin's.
- The script scope is `agent`, `parallel`, `pipeline`, `workflow`, `phase`, `log`, `args`,
  `budget`. There is no
  `fs`, no `require`, and `Date.now()` / `Math.random()` / `new Date()` throw — they would break
  resume. Config arrives through `args`, never off disk.
- `${CLAUDE_PLUGIN_ROOT}` inside a template literal is a `ReferenceError`. A plugin path reaches the
  script as a value in `args`.
- Any field an agent fills that becomes a `subagent_type` is an `enum`, never a bare `string`.
  Model-generated text naming an agent is how a typo becomes a spawn failure mid-run.

`node .github/check_workflows.mjs` enforces the parse, the name match and the agent set, and
dry-runs each script against stubs. `node --check` does **not** work on these files: they use a
top-level `return`, legal only inside the async wrapper the runtime supplies.
