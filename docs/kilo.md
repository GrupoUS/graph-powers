# Kilo integration

Kilo artifacts are generated from the canonical Claude Code files by `<PLUGIN>/kilo/install.mjs`. Nothing in
the Kilo tree is maintained by hand, and a generated file is not the same evidence as a discovered
file or an executed hook. This page records which is which.

Checked against **Kilo 7.6.2** (`kilo --version`), installed as the bun global `@kilocode/cli`.

## Where Kilo reads

Proven with the installed CLI, not from documentation:

| Kind | Path | How it was proven |
|---|---|---|
| Agents | `~/.kilo/agent/<name>.md` (also `agents/`, `mode/`, `modes/`) | `kilo agent list`, `kilo debug agent <name>` |
| Commands | `~/.kilo/command/<name>.md` (also `commands/`) | `kilo debug config` → `command` |
| Skills | `~/.kilo/skills/<name>/SKILL.md` | `kilo debug skill` |
| Plugins | `~/.kilo/plugin/*.ts` (also `plugins/`) | `kilo debug config` → `plugin` |
| Config (written) | `~/.kilo/kilo.jsonc` | a distinctive key appears in `kilo debug config` |
| Config (also read) | `~/.config/kilo/kilo.jsonc` | indexing config on an installed machine resolves from it |

Kilo's own bundled `kilo-config` skill describes the same layout: two config directories (`.kilo`
canonical, `.kilocode` legacy) scanned at each level, a home pair `~/.kilo/` and `~/.kilocode/`, and
`~/.config/kilo/` as the XDG global loaded at the lowest file-based precedence. The globs it
documents (`{agent,agents}/**/*.md`, `{command,commands}/**/*.md`, `{skill,skills}/<name>/SKILL.md`,
`{plugin,plugins}/*.{ts,js}`) run inside each discovered config directory.

Two rows of that documented model did **not** hold in this build, both tested in an isolated `HOME`
with no Kilo server bound to the working directory:

- An agent written to `~/.config/kilo/agent/<name>.md` was **not** discovered by `kilo agent list`,
  although the documented glob says it should be. Graph Powers installs into `~/.kilo/agent/`.
- A project `.kilo/kilo.jsonc` was **not** read on its own. The project config file Kilo reads is
  `kilo.jsonc` at the repository root. Project-scoped *artifacts* still live under `.kilo/`.

`~/.kilocode/` is the legacy twin of `~/.kilo/` and is scanned too; Graph Powers writes only
`~/.kilo/`. Both global config files are read, and the `~/.kilo` one wins a conflicting key — which
is why the installer writes there and *refuses* to install when the XDG file already defines `lsp`
or `formatter`, since that key would otherwise be silently shadowed.

Do not trust an isolated-`HOME` probe of `kilo debug config` on a machine that is already running
Kilo: it can answer from the server bound to the working directory instead of the home you set.
Agent and skill discovery (`kilo agent list`, `kilo debug skill`) are process-local and were the
reliable probes; `kilo debug config` was reliable when checked on the real home with a distinctive
key and then removed.

## Support matrix

| Capability | Status | Evidence |
|---|---|---|
| Agent discovery from `~/.kilo/agent/` | SUPPORTED | `kilo agent list` |
| Per-role model via agent `model:` | SUPPORTED | `kilo debug agent evaluator` → `{providerID: kilo, modelID: ~openai/gpt-astra-latest}` |
| `tools:` boolean map | SUPPORTED | resolved tool map shows `write: false`, `task: false` |
| `permission.edit` / `permission.bash` (last match wins) | SUPPORTED | resolved permission list; a nested `bash` map accepts per-pattern actions |
| `permission.task: deny` (leaf) | SUPPORTED | evaluator resolves with `{"permission":"task","action":"deny"}` |
| `permission.task` pattern **allow-list** | UNVERIFIED | a map form also produced `tools.task: false`; the router therefore keeps the default and names its specialists in the prompt instead |
| `mode: primary\|subagent` | SUPPORTED | `kilo agent list` groups by mode |
| Command `agent:` + `$ARGUMENTS` | SUPPORTED | `kilo debug config` → `command` |
| Skill discovery by `description` | SUPPORTED | `kilo debug skill` |
| Plugin hooks `tool.execute.before` / `after` | SUPPORTED | installed plugin appears in `kilo debug config` → `plugin`; throwing aborts the tool call (binary: `plugin.trigger("tool.execute.before")`) |
| Plugin hooks `shell.env`, `permission.ask`, `event`, `chat.*` | SUPPORTED | installed `@kilocode/plugin` type definitions |
| `lsp` / `formatter` config keys | SUPPORTED | installed SDK types; `false | { [id]: … }` |
| `subagent_model` config key | UNSUPPORTED | absent from the installed SDK types; not emitted |
| `variant`, `effort`, `xhigh` | NOT APPLICABLE | no such agent fields; the catalog advertises no variants for Astra/Luna, so none are emitted |
| `Stop` event | ABSENT | no such hook exists; `stop_verify.py` has no Kilo projection |
| `PermissionRequest`, `Notification`, `SubagentStart` | ABSENT | no confirmed Kilo event; `tool_approver.py`, `notify.py`, `subagent_context.py` are omitted |
| Workflow runtime (`Workflow({...})`) | ABSENT | commands take their already-declared fallback instead of retrying a name |
| Native formatter | DISABLED BY CHOICE | `formatter: false`; `ultracite.py` on `PostToolUse` is the single formatting owner |
| TypeScript LSP | CONDITIONAL | `vtsls` is configured only when it resolves; otherwise the install reports it as unavailable and adds nothing |
| Whole reference tree | SUPPORTED | copied under `~/.kilo/graph-powers/` |

## What the projection changes

Canonical prose carries literals that resolve to nothing on Kilo. `<PLUGIN>/kilo/lib.mjs` rewrites them the
same way for agents, commands, skills, references and shipped scripts:

| Canonical | Kilo |
|---|---|
| `graph-powers:<agent>` | `<agent>` — there is no namespace prefix |
| `Skill("graph-powers:planning")` | the `planning` skill (directory name) |
| `Workflow({ name: 'graph-powers:ultra-verify', … })` | the declared fallback text, never a retry |
| `${CLAUDE_PLUGIN_ROOT}/skills` | `~/.kilo/skills` |
| `${CLAUDE_PLUGIN_ROOT}/references` | `~/.kilo/graph-powers/references` |
| `${CLAUDE_PLUGIN_ROOT}/commands` | `~/.kilo/command` |
| `${CLAUDE_PLUGIN_ROOT}/agents` | `~/.kilo/agent` |

`<PLUGIN>/kilo/install.mjs` also rewrites shipped code, not just prose: `<PLUGIN>/skills/planning/scripts/sdd.py`
validates `--role` values with a `^graph-powers:(?P<slug>…)$` pattern, and the pattern is projected
too so a bare role name is still accepted.

## Roles, models and boundaries

Twelve canonical agents plus one generated primary, `graph-powers`. The primary's description names
the Graph Powers commands explicitly because Kilo's built-in `ask`, `code`, `plan` and `debug`
agents compete by name, and Kilo chooses by description when nothing else decides.

| Profile | Model | Agents |
|---|---|---|
| judge | `kilo/~openai/gpt-astra-latest` | evaluator, security-reviewer, skill-improver, ui-ux-designer |
| architect | `kilo/~openai/gpt-astra-latest` | project-planner |
| executor | `kilo/~openai/gpt-luna-latest` | debugger, frontend-specialist, mobile-developer, performance-optimizer |
| verifier | `kilo/~openai/gpt-luna-latest` | verification |
| scout | `kilo/~openai/gpt-luna-latest` | explorer, librarian |

`isKiloModelId` refuses a Claude alias (`opus`, `sonnet`, `haiku`, `fable`) and a Codex slug
(`gpt-5.6-sol`), because neither resolves and a subagent with an unresolvable model starts and never
answers. A **DeepSeek Flash** id is not emitted: the catalog exposes several plausible ids
(`deepseek-v4.1-flash`, `deepseek-v4-flash`, `deepseek-v4-flash-0731`) and an ambiguous routing
choice is worse than an explicit one. Add it as an operator override when the exact id is known.

Boundaries, from the canonical frontmatter:

- Review and research roles carry `edit: deny`, with `write`, `edit` and `apply_patch` switched off
  in the tool map. Kilo's edit capability is `write`/`apply_patch`; there is no `edit` tool id, so
  the permission rule is what enforces it.
- `evaluator` is a **leaf**: `permission.task: deny`.
- `evaluator` and `researcher` roles get a shell **deny-list** (`rm *`, `git commit*`, `git push*`,
  `git reset*`, …), not an allowlist. A research agent legitimately runs `git log`, `rg`, `python3`
  and repository scripts; an allowlist wide enough for those stops preventing mutation. Precedence
  is last-match-wins: the resolved list from `kilo debug agent` places inherited and config rules
  first and the agent's own rules after them, so appending denies can only tighten. Kilo's own
  documentation contradicts itself on this point — the permissions section says "first match wins"
  and the MCP section says "the last matching rule wins" — so the ordering was read from the
  resolved rule list rather than from either sentence.

Where a boundary could not be enforced, it is **advisory**, not claimed: the router keeps the
default `task` permission because only `deny` was proven, and the allow-list lives in the prompt.

## Operator overrides

The generated agent's `model:` field is authoritative. `kilo debug agent` proved that
`agent.<id>.model` in `kilo.jsonc` does **not** override an agent Markdown file — so the override
surface is `~/.config/kilo/graph-powers.json` (or `GRAPH_POWERS_KILO_MODELS` for CI):

```jsonc
{
  "agent": { "evaluator": { "model": "kilo/~openai/gpt-sol-latest" } },
  "profiles": { "executor": { "model": "kilo/~openai/gpt-terra-latest" } }
}
```

Precedence: per-agent → profile → legacy family tier → flat → semantic default. The main model is
never written: the router inherits whatever the operator chose.

## Install and rollback

```sh
node "<PLUGIN>/bin/graph-powers.mjs" --target kilo          # from the project you want to wire
node "<PLUGIN>/bin/graph-powers.mjs" --target kilo --uninstall
```

- The manifest (`~/.kilo/graph-powers-installed.json`) is written **incomplete before** any
  artifact and marked complete at the end, so an interrupted install is visible rather than
  indistinguishable from a good one.
- A file that exists but is not recorded as ours is a refusal, not an overwrite. `--force` overrides.
- Output is deterministic: two runs into the same home produce identical bytes.
- `lsp` and `formatter` are merged with a JSONC-preserving editor. Comments, blank lines and
  unrelated keys survive. A managed key defined in the XDG file stops the install. Uninstall removes
  the keys and the file when it only held ours.

Managed config keys: `formatter: false` (one formatter owner — `ultracite.py`) and
`lsp: { "eslint": { "disabled": true } }`, because Oxlint is the declared local linter. `deno` and
`typescript` self-gate on their project files, so they are left enabled.

## Verification

`python3 "<PLUGIN>/.github/check_kilo.py"` is gate 29. It regenerates into a throwaway home and proves the
inventory, model routing, permission boundaries, literal translation, determinism, ownership
refusal, the JSONC merge and the plugin's registration set — with **no Kilo binary required**.

On a machine with Kilo, the runtime half is:

```sh
HOME=/tmp/probe node "<PLUGIN>/kilo/install.mjs"
HOME=/tmp/probe kilo agent list
HOME=/tmp/probe kilo debug agent evaluator
HOME=/tmp/probe kilo debug skill
python3 "<PLUGIN>/bin/verify-hook-clients.py" --client kilo --probe-guardrail
```

`--client kilo` reports posture `PARTIAL`: the tool-level guardrails run through the native plugin,
and the lifecycle registrations that cannot be projected (`Stop`, `PermissionRequest`,
`Notification`, `SubagentStart`) are named rather than implied.

## Known limits

- `kilo debug config` talks to a running Kilo server when one is present for the working directory,
  so isolated-`HOME` probes of that one command can report the real machine's config. Agent and
  skill discovery (`kilo agent list`, `kilo debug skill`) are process-local and were the reliable
  probes.
- The `~/.kilo/skills/graph-powers-*` entries on an existing machine are stale **Codex** projections
  that reference `~/.codex/graph-powers/...`. Graph Powers installs canonical skill names
  (`debugger`, `planning`, …) and never overwrites them; remove the stale ones by hand.
- Kilo's permission model resolves the **last** matching rule, so generated rules are appended, and
  a project `kilo.jsonc` can still widen them. The guardrail plugin, not the permission list, is the
  reliable boundary.
