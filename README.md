# Graph Powers

A shared harness for [Claude Code](https://claude.com/claude-code),
[Codex CLI](https://developers.openai.com/codex), [Cursor](https://cursor.com),
[Grok CLI](https://docs.x.ai/build) and [Hermes Agent](https://hermes-agent.nousresearch.com/):
agents, skills, commands and guardrails that work in any repository. Whatever changes from
project to project leaves the code and enters one config file.

**Claude Code** — two lines in any session:

```
/plugin marketplace add GrupoUS/graph-powers
/plugin install graph-powers@graph-powers
```

**Codex CLI** — two commands, then restart and approve the hooks in `/hooks`:

```bash
codex plugin marketplace add GrupoUS/graph-powers
codex plugin add graph-powers@graph-powers
```

**Cursor** — install the plugin from the marketplace, then once per machine write the IDE Run Mode
(this is the file Auto-review actually reads; `cli-config.json` is only `cursor-agent`):

```bash
node <clone>/bin/graph-powers.mjs --target cursor
```

Reload the window. Git commit and push still ask. `rm -rf /` still denies.

**Grok CLI** — install the plugin, then once per machine write the user config (project
`.grok/config.toml` cannot set `permission_mode`):

```bash
grok plugin marketplace add GrupoUS/graph-powers
grok plugin install graph-powers --trust
node <clone>/bin/graph-powers.mjs --target grok
```

The installer verifies the exact Grok-reported package path and its fifteen fail-open hooks before
writing `always-approve`. Restart the Grok session. Git commit and push still ask. `rm -rf /` still
denies.

**Hermes Agent** — skills and agent contracts, no executable git hooks (same class as Zed):

```bash
hermes plugins install GrupoUS/graph-powers --enable
hermes plugins show graph-powers
hermes plugins doctor <clone> --ci
```

The native package derives `graph-powers:<name>` from every `skills/*/SKILL.md`, command document,
and `graph-powers:agent-<slug>` from every `agents/<slug>.md`. Git hooks are **NOT ENFORCED** in
Hermes; use the parent agent's approvals for that boundary.

Some Hermes releases scan community Git trees before installation and may block this repository's
intentional security examples. That is an upstream scanner decision; review its report or use an
approved organization policy, and do not treat `--force` as a way around a dangerous verdict.

Then one prompt, pasted into an agent session opened in your project:

```
Read AGENT_SETUP.md from the graph-powers plugin (https://github.com/GrupoUS/graph-powers) and execute it for this project.
```

That second step is not decoration. Installing wires the plugin in; the playbook is what makes
it take effect — it checks optional integrations and workflow binaries, writes your project's
parameters, improves the `CLAUDE.md` / `AGENTS.md` / rules you already have instead of replacing
them, and
removes the local copies that would otherwise keep shadowing the plugin. It stops for your approval
before every write.

---

## The problem

Anyone who uses an agent CLI seriously ends up building a harness: a few subagents, a few skills,
chained commands, hooks that stop an agent committing on its own. It works. Then a second project
arrives, and the fastest way to have the same harness is to copy the folder.

From there you have two harnesses. Then five. Each gets fixes the others do not, and nobody notices,
because nothing breaks — they just drift apart.

Measured across five projects in one group, which is what produced this repository:

| | |
|---|---|
| Files with the same name in ≥4 of the 5 projects | 221 |
| Of those, **byte-for-byte identical** | **45** |
| Of those, diverged | **176** |
| Files that existed in only one project | 178 |

The cost is not tidiness. Two security defects fixed in **one** of the projects were still live in
the other four:

- **a researcher with write permission**, against its own description, because the `memory:` field
  injects `Read`/`Write`/`Edit` on top of the `tools:` allowlist;
- **an evaluator carrying the `Agent` tool** with no turn limit, closing a recursion loop with the
  debugger.

Fixing it in one repository never reached the others. There was no copy — there were five.

## The solution

One copy of each artefact, in a plugin. Each project declares what is different about it:

```
graph-powers/                        your project/
  agents/       12 agents              .graph-powers/config.json  <- the parameters
  skills/       13 bundled skills      .claude/rules/             <- only your domain
  commands/     12 commands            .claude/agents/            <- only what is yours alone
  hooks/        12 guardrails
  workflows/    2 orchestrations
  references/   safety + execution floors
    shared/     18 shared patterns, loaded one at a time
  schema/       the config contract
  DESIGN.md     specs for the three authorities
  PRODUCT.md      the plugin installs into
  REVIEW.md       your project
```

Claude Code precedence is `Managed > CLI > Project > User > Plugin`. A project that needs its own
version of anything puts the file in its `.claude/` and it beats the plugin's — no fork, no
uninstall. **The plugin is the floor, not the cage.**


---

## Global by preference, local only when it must be

The harness is byte-for-byte identical in every project. So it installs **once per machine** and
serves every repository you have — including the ones you have not created yet. Only what genuinely
differs per project stays in that project.

| Installed once, globally | Where it lands |
|---|---|
| The Claude Code plugin — 12 agents, 13 bundled skills, 12 commands, 12 guardrails, 2 workflows, shared references | `~/.claude/settings.json` (`--scope user`). One install, zero copies |
| Codex native plugin: skills, guardrails and references | the versioned plugin cache shown by `codex plugin list --json` |
| Codex native companion roles | `<codex-home>/agents/*.toml`, explicitly emitted from the plugin's tracked policy |
| Codex clone fallback: skills and commands-as-skills | `~/.agents/skills/` |
| Codex clone fallback: subagents, guardrails and references | `~/.codex/agents/*.toml` · `~/.codex/hooks.json` · `~/.codex/graph-powers/` |

| Stays in the project | Why it cannot be global |
|---|---|
| `.graph-powers/config.json` | The branch, the gate commands, the paths, the opt-in prefix — different in every repository by definition |
| `.claude/rules/` · `.codex/rules/` | Domain knowledge. Generic process comes from the plugin; these answer questions only this project asks |
| `DESIGN.md` · `PRODUCT.md` · `REVIEW.md` | This project's design, product and review authorities |
| `CLAUDE.md` · `AGENTS.md` | Its identity and invariants |
| `.claude/agents/`, `.claude/skills/`, `.claude/commands/` | Only what this project genuinely overrides — and by precedence, an override here beats the plugin |

**Why one global copy is correct rather than sloppy:** the guardrails read *the project's own*
config at runtime. The same twelve files enforce `dev-test` and `ACME_ALLOW_COMMIT` in one
repository and `develop` and `OTHER_ALLOW_COMMIT` in the next. Copying the harness into each project
would buy nothing and reintroduce exactly the divergence this plugin exists to end — eleven skills
copied into five repositories is five copies that drift.

**Installing in your second project costs almost nothing.** The installer checks whether the global
half is already present at this version and skips it: what gets written is the rules and the
instruction block, and that is all.

On Claude Code there is nothing to do: a plugin installed at user scope already serves every
project on the machine, including ones that do not exist yet. On Codex, from your clone:

```bash
node ~/.graph-powers/src/bin/graph-powers.mjs                    # global by default
node ~/.graph-powers/src/bin/graph-powers.mjs --scope project    # everything into this repository
```

Use `--scope project` only when the team has to receive the harness by cloning the repository, on
machines where nobody will run an installer. That copy is then yours to keep in sync, which is the
cost you are choosing.

---

## Five harnesses, one source

Codex CLI, Cursor, Grok and Hermes read different files from Claude Code, but the shapes line up.
The installers and native entrypoint generate those sides from the artefacts that already exist —
nothing is maintained twice.

| Surface | Claude Code | Codex CLI | Cursor | Grok CLI | Hermes Agent |
|---|---|---|---|---|---|
| Guardrails | `hooks/hooks.json` | The same declaration, merged into `~/.codex/hooks.json` | Generated `hooks/hooks-cursor.json` (PermissionRequest and Notification skipped) | The same `hooks/hooks.json` (Claude nested shape; payload adapted in `_config.py`) | **NOT ENFORCED**; no Hermes hook surface |
| Skills | `skills/<name>/SKILL.md` | `.agents/skills/<name>/SKILL.md` | The same files, via `.cursor-plugin/` | The same files, via `.grok-plugin/` | `plugin.yaml` + `__init__.py`; `graph-powers:<name>` |
| Subagents | `agents/*.md` | Native companion `codex/native-agents/*.toml` and clone `.codex/agents/*.toml` are both generated through `codex/model-policy.json`: explicit semantic profile, Codex model and reasoning effort | The same markdown files | The same markdown files | `agents/*.md` as `graph-powers:agent-<slug>` contracts |
| Commands | `commands/*.md` (`/name`) | skills (Codex deprecated custom prompts) | The same markdown files | The same markdown files | namespaced skills, e.g. `graph-powers:plan` |
| IDE/CLI approval | `~/.claude/settings.json` | `~/.codex/config.toml` | `~/.cursor/permissions.json` (IDE) and `cli-config.json` (`cursor-agent`) | `~/.grok/config.toml` (`[ui] permission_mode`) | parent agent approvals |

The Codex hooks file is **merged, never overwritten**. Other tools' installers write it too, and
clobbering it would silently disable someone else's guardrails, which is this
project's own failure mode pointed the other way. Every entry added is recorded, so
`node <clone>/bin/graph-powers.mjs --uninstall` removes exactly what was added and leaves the rest
standing. Cursor's permission file is operator posture and is not removed. Grok's `config.toml`
is operator posture and is not removed.

### Gauntlet execution

`/gauntlet <approved-plan-file-or-directory> [--dry-run]` is the opt-in, high-assurance execution
profile for an already approved structured plan. It keeps coupled work sequential, permits bounded
parallel lanes only for disjoint ownership, and gives each lane a builder, focused check, fresh
read-only critic and capped correction cycle before the final `/verify loop`. L1-L2 work stays on
the normal local route. The dry run validates and prints the schedule without acquiring a lease,
writing or spawning. Codex exposes the same command as the generated `graph-powers-gauntlet` skill;
Hermes translates the method but does not claim a `/gauntlet` slash-command surface.

---

## Optional extensions

Nothing required is external. The method layer — discovery, design, planning, execution and
test-driven development — has one authority in `skills/planning`; the evidence gate, parallel
dispatch and review protocol live in shared references and `/pr-review`. It is adapted from
[obra/superpowers](https://github.com/obra/superpowers)
(MIT) and recorded in `NOTICE`, the way `landing-page-design`, `animate` and `intent-layer`
entered before it: nine of the ten commands stopped mid-run without that plugin, and a dependency
nine commands cannot run without is not tooling around the harness, it is the harness. A copied
snapshot would go stale, so none of it is a snapshot — each piece is rewritten for this plugin's
rules, and what stays external is optional.

| Dependency | What it brings | Why it stays external |
|---|---|---|
| [emil-design-eng and apple-design](https://github.com/emilkowalski/skills) (skills, MIT) | Optional supplements to the plugin's own `animate` skill: `/design` loads them when installed — the invisible details, materials, gesture-driven fluidity. Absent, `animate` carries the pass alone | Two skill folders from one repository, one `SKILL.md` each; install by copy with the one-liner below |

```bash
# emil-design-eng and apple-design — optional; one SKILL.md each, into both skills directories
# the harness reads. The same command installs them and updates them.
python -X utf8 -c "import os,urllib.request;h=os.path.expanduser('~');[(os.makedirs(os.path.join(h,*d,s),exist_ok=True),urllib.request.urlretrieve('https://raw.githubusercontent.com/emilkowalski/skills/main/skills/'+s+'/SKILL.md',os.path.join(h,*d,s,'SKILL.md'))) for s in ('emil-design-eng','apple-design') for d in (('.claude','skills'),('.agents','skills'))]"
```

None of those details is cosmetic.

`--yes` is what makes the command non-interactive. Without it the installer asks which harnesses and
which scope, and an agent running it waits on a prompt nobody is going to answer.

The runner has to match because a project that declares `autonomy.allowPackageManagers` refuses the
ones it did not choose — that is the setting keeping its lockfile from forking. Reaching for `npx`
inside a bun project is denied by this plugin's own guardrail, correctly, and the fix is to use the
runner the project already standardised on rather than to widen the allowlist.

Two more plugins are optional, and only the commands that call them notice their absence:
`code-review` from Claude's official plugin marketplace (invoked by `/pr-review`), and the Codex
plugin's `rescue` and `codex-result-handling` skills (invoked by `/debug` and `/research` when a
second implementation pass is worth having).

Some skills also expect MCP servers (Context7 for library docs, Tavily for research,
sequential-thinking for multi-step reasoning) and `bunx agent-browser` for browser verification.
Each skill states what it needs; none is required for the guardrails.

---

## Installing

### Requirements

- [Claude Code](https://claude.com/claude-code), [Codex CLI](https://developers.openai.com/codex), [Cursor](https://cursor.com), [Grok CLI](https://docs.x.ai/build), or [Hermes Agent](https://hermes-agent.nousresearch.com/) — any one of them, or all five
- **Python 3.10 or newer available as the literal `python3` command** — every hook declaration invokes
  that name; the installer refuses permissive posture if it is absent. The guardrails are standard
  library only, with no dependencies.
- Node 18+ (or Bun) — only to run the installer; nothing here has dependencies to fetch
- Git

There is no package to publish and none to install. The plugin is markdown, JSON and
standard-library Python: a clone **is** the artefact, and a `git pull` **is** the update. A
registry in between would add an account, a token and a release for every fix, and buy nothing.

### Claude Code

```
/plugin marketplace add GrupoUS/graph-powers
/plugin install graph-powers@graph-powers
```

Agents, skills, commands and guardrails are live at the next session start. Nothing else is needed
unless you also use Codex, Cursor, Grok or Hermes. Zed consumes instructions/editor settings only; this
repository does not implement a Zed lifecycle/tool-hook target.

### Codex CLI — native plugin (recommended)

```bash
codex plugin marketplace add GrupoUS/graph-powers
codex plugin add graph-powers@graph-powers
```

Restart Codex, open `/hooks`, and approve the fifteen Graph Powers registrations (fourteen scripts;
the Bash approver is registered for two events). Installation makes the hooks discoverable;
approval makes them executable. Then run the setup playbook in the project so
its config, rules and authorities are established.

Codex loads `.codex-plugin/` first. Codex Desktop is not a second Graph Powers install route: some
Desktop builds launch a bundled Codex `app-server` against the same Codex home, but the setup
playbook requires a separate Desktop proof and full app restart instead of inheriting the CLI verdict.

The current upstream plugin manifest has no agent-role resource; an `agents` field is ignored rather
than installed ([pinned Codex manifest source](https://github.com/openai/codex/blob/90854393966b21e9ebfd21b122334eb09a20c93d/codex-rs/plugin/src/manifest.rs)).
After the marketplace install, explicitly emit the tracked companion roles into the Codex config
layer that discovers them:

```bash
node codex/native-plugin.mjs --out <codex-home>/agents
```

This companion step writes roles only; it does not install a second hook or skill route. Those TOMLs
and the clone fallback use the same resolver from `codex/model-policy.json`, so neither generated
route inherits one session model for all twelve agents. The defaults encode the economic role of the
node:

- judges and architects: `gpt-5.6-sol` + `max`;
- executors and the verifier: `gpt-5.6-luna` + `max`;
- scouts: `gpt-5.6-luna` + `medium`.

The tracked files under `codex/native-agents/` are portable source snapshots. The `--out` step
resolves every `${CLAUDE_PLUGIN_ROOT}` reference to the actual installed plugin root before Codex
loads the role; pointing Codex directly at the tracked snapshots is unsupported.

There is one upstream capability boundary the generator does not simulate. Codex 0.150.1's
[role projection](https://github.com/openai/codex/blob/90854393966b21e9ebfd21b122334eb09a20c93d/codex-rs/core/src/agent/role.rs)
applies model and reasoning fields but not a per-role sandbox or spawn deny; its
[regression test](https://github.com/openai/codex/blob/90854393966b21e9ebfd21b122334eb09a20c93d/codex-rs/core/src/agent/role_tests.rs#L352-L391)
explicitly preserves the parent sandbox. Generated roles therefore omit the ignored
`sandbox_mode` key. Claude Code still enforces `disallowedTools`; on Codex, hard read-only review
requires the whole parent session to start with `--sandbox read-only`. In a mixed write-capable
workflow, read-only and evaluator-leaf boundaries are explicit instructions and orchestrator rules,
not hard per-role runtime capabilities.

The non-judge profiles name `judge` as their escalation target, but the resolver never retries by
itself. Existing bounded stopping conditions decide when to hand an ambiguity to Sol; there is no
automatic Luna → Terra → Sol chain and no new retry loop.

Model selects which intelligence/cost tier executes the node. Reasoning effort controls that
model's single-agent reasoning budget. Terra has no automatic role or retry hop, but an operator can
select it explicitly through a profile or individual-agent override:

```json
"codex": {
  "profiles": {
    "executor": { "model": "gpt-5.6-terra", "reasoningEffort": "max" }
  },
  "agents": {
    "debugger": { "model": "gpt-5.6-luna", "reasoningEffort": "max" }
  }
}
```

The clone resolver preserves old explicit choices. Precedence is per-agent override, profile
override, legacy matching `codex.models.{heavy,standard,light}` tier, legacy flat `codex.model`, then
the semantic default. For effort it is per-agent, profile, legacy `codex.reasoningEffort`, then the
semantic default. The old tier mapping remains a migration path, not the default mechanism.

To render project overrides into that operator-managed native companion directory, pass the config
explicitly. `--models heavy=...,light=...` remains as the legacy shorthand:

```bash
node codex/native-plugin.mjs --config .graph-powers/config.json --out <codex-home>/agents
```

`native-ultra` is intentionally never emitted into a subagent. Ultra asks Codex to use proactive
multi-agent orchestration; it is not a larger Max budget. Use it only as an explicit top-level
alternative when Graph Powers is not also running `/pr-review`, `ultra-plan` or `ultra-verify` fan-out.
The generator writes it as Codex's separate v2 top-level profile file, never as agent-role TOML:

```bash
node codex/native-plugin.mjs --top-level-profile native-ultra --out <codex-home>
codex --profile native-ultra
```

The installed Codex build still decides whether the selected model/account can execute Ultra; a
runtime rejection is reported rather than translated to another model. Judges remain on Sol Max.

### Cursor

Cursor marketplace installs the same repository through `.cursor-plugin/plugin.json`. That is the
plugin. The confirmation flood is not: the IDE reads `~/.cursor/permissions.json`, and
`~/.cursor/cli-config.json` only covers `cursor-agent`. **Install the marketplace plugin first.**
`--target cursor` does not install it and now refuses to loosen posture when its cache is absent;
after installation it writes the posture the marketplace cannot. Reload the
window. If a team dashboard still forces Auto-review, set Settings → Agents → Approvals &
Execution → **Run Everything**. Git commit/push still ask; `rm -rf /` still denies.

```bash
node ~/.graph-powers/src/bin/graph-powers.mjs --target cursor
```

### Grok CLI

Grok marketplace installs the same repository through `.grok-plugin/plugin.json` and reads
`hooks/hooks.json` directly. That is the plugin. The confirmation flood is `config.toml` under
`GROK_HOME`, falling back to `~/.grok`, with `[ui] permission_mode = "always-approve"`. A project
`.grok/config.toml` cannot set that key. After installing the plugin, run the clone installer once
(or the setup playbook Step 9h): it reads `grok plugin list --json`, verifies the exact reported path,
manifest, fifteen guarded runners and their targets, and only then changes posture. Restart the
session. Do not add user `hooks/*.json` beside plugin hooks. Under guarded posture the installer
still wires discovery without writing always-approve. Git commit/push still ask; `rm -rf /` still
denies.

```bash
node ~/.graph-powers/src/bin/graph-powers.mjs --target grok
```

### Zed and Oxc editors

Graph Powers has no Zed hook target: native Zed tool calls are not intercepted by the commit, push,
protected-file or destructive-command hooks, so that surface remains `NOT ENFORCED`. It does provide
an explicit project setup for the official Oxc editor integrations. Run it from the project root:

```bash
bun <clone>/bin/graph-powers.mjs --setup-oxc
```

The setup installs local TypeScript 7, `oxlint` and `oxfmt`, verifies their project-local binaries, and
merges `.zed/settings.json` plus the VS Code-compatible `.vscode/settings.json` and
`extensions.json`. Oxfmt is the sole formatter for JavaScript, TypeScript, JSON, JSONC and CSS;
Oxlint supplies interactive diagnostics. Install the official **Oxc** extension once in Zed
(`zed: extensions`) or
VS Code/Cursor (`oxc.oxc-vscode`); project setup cannot install GUI extensions or change global IDE
settings. Restart the language server after the package install. Other LSP editors can launch the
same local Oxlint binary with `--lsp`.

### Clone installer — fallback and project-scoped installs

```bash
git clone https://github.com/GrupoUS/graph-powers.git ~/.graph-powers/src
node ~/.graph-powers/src/bin/graph-powers.mjs
```

Use this route when the Codex marketplace is unavailable or the repository must carry a
project-scoped copy. It detects which CLIs are present, writes the Codex artefacts — global half
then project half — and verifies. Do not combine it with the native plugin: both registrations run,
so an older clone install must be removed before switching routes.

Clone anywhere you like; `~/.graph-powers/src` is only a suggestion, and the installer records
wherever it actually ran from so updates find it again.

| Option | What it does |
|---|---|
| `--target claude\|codex\|cursor\|grok\|both\|all` | Which supported client to configure. Cursor still requires its marketplace plugin first; Zed has no hook target. `both` is Claude + Codex |
| `--scope user` | Writes to `~/.claude/settings.json`. **Default** — one install serves every project on the machine |
| `--scope project` | Writes to `.claude/settings.json`, versioned. Use when the team must get the harness by cloning the repository |
| `--scope local` | Writes to `.claude/settings.local.json`, gitignored. To try it without affecting the team |
| `--force` | Reinstall the global half even when it is already at this version |
| `--config` | Also writes a starting `.graph-powers/config.json`, inferred from the stack |
| `--setup-oxc` | Installs local TypeScript 7, `oxlint` and `oxfmt`, then configures Zed plus VS Code/Cursor project settings |
| `--package-manager NAME` | Overrides Oxc setup detection: `bun`, `npm`, `pnpm` or `yarn` |
| `--prefix NAME` | Opt-in key prefix (with `--config`). Default: the directory name |
| `--source <org/repo\|path>` | Where the marketplace comes from. Useful for a fork or a local clone |
| `--update` | `git pull --ff-only` on the clone, then reinstall from it |
| `--uninstall` | Removes exactly the Codex artefacts a previous run recorded. Cursor permissions and Grok config.toml stay |

### Staying current

A plugin is a copy, and a copy starts ageing the moment it is installed. Six months later five
machines run five versions of guardrails that were meant to be identical — which is the failure
this harness exists to end, one level up. So it updates itself.

At session start, at most once every twelve hours, a detached worker updates only the routes it
actually implements:

| Harness | What runs | Applies |
|---|---|---|
| Claude Code | `claude plugin marketplace update graph-powers`, then `claude plugin update graph-powers@graph-powers` | Next session start |
| Codex CLI clone fallback | `git pull --ff-only` on the clone, then regenerate — only if it moved | Next session start |

Native Codex, Cursor and Grok are updated in the foreground through their own marketplace/client
path, never by this worker: replacing a client-owned cache while a process retains its old absolute
hook commands recreates the stale-session failure `1.11.1` fixes. After any native cache replacement,
run `python3 -X utf8 <clone>/bin/verify-hook-clients.py --client <client>`, then restart every
process/task that loaded the old definitions; a fresh process does not certify an already-open one.
Nothing inside your project is touched.

`--ff-only` is deliberate: a merge commit created by a background process is a state nobody chose,
and a clone you have edited locally refuses to update and says so rather than rewriting itself.

On the clone fallback, artefacts are regenerated **only when the clone actually moved**. Codex
trusts a hook definition by its content, so an identical rewrite would cost a `/hooks` re-approval
and leave the guardrails inert until you gave it.

To update the clone fallback by hand, at any moment:

```bash
node ~/.graph-powers/src/bin/graph-powers.mjs --update
```

```jsonc
// .graph-powers/config.json — all optional, these are the defaults
"autoUpdate": { "enabled": true, "intervalHours": 12, "claude": true, "codex": true }
```

`GRAPH_POWERS_NO_AUTO_UPDATE=1` turns it off for one machine without editing the project's
config.
| `--agent-setup` | Prints the setup prompt and exits |
| `--dry-run` | Shows what it would do, without doing it |

`--config` reads the repository rather than guessing: the stack from the config files present, the
package manager from the lockfile, the branch from git, and **only gate commands that genuinely
exist in the scripts** — a gate pointing at a missing script dies as "script not found", and the
report line reads as covered.

The result is a starting point for you to review, not a verdict. The installer says so when it
finishes.

### Then: the setup playbook

```
Read AGENT_SETUP.md from the graph-powers plugin and execute it for this project.
Stop for my approval before each write, as the playbook instructs.
```

Ten steps, every one of them with a stop before it writes: locate the plugin and back up →
check optional integrations and workflow binaries → read the repository → write or merge the
config → improve `CLAUDE.md` and `AGENTS.md` → create or improve the rules layer → clean what
shadows the plugin →
audit `settings.json` → wire Codex → verify with output.

> **Installing without cleaning the project's `.claude/` does nothing.** Precedence is
> `Project > Plugin`. While a local copy with the same name as a plugin agent, skill or command
> exists, the local copy is what runs — and you conclude, wrongly, that the plugin does not work.

The full procedure is [`AGENT_SETUP.md`](AGENT_SETUP.md). It is written for the agent to execute,
but it reads fine if you want to see what it will do before you let it.

---

## Configuration

One file per project, with a safe default for everything. The full contract is
[`schema/config.schema.json`](schema/config.schema.json); starting points are in
[`examples/`](examples/).

```json
{
  "$schema": "https://raw.githubusercontent.com/GrupoUS/graph-powers/main/schema/config.schema.json",
  "project": { "name": "acme-web", "stack": "astro-tailwind" },
  "git": {
    "workBranch": "dev-test",
    "protectedBranches": ["main"],
    "optInPrefix": "ACMEWEB"
  },
  "tooling": {
    "packageManager": "bun",
    "testRunner": null,
    "commands": { "lint": "bun run lint", "build": "bun run build" }
  },
  "paths": { "frontendRoot": "src" }
}
```

| Field | What it is for |
|---|---|
| `git.workBranch` · `git.protectedBranches` | Where work happens, and what no agent touches without approval |
| `git.optInPrefix` | Prefix of the keys that release a risky action |
| `tooling.commands.*` | The literal command behind each gate — **and the tool it names has to be installed**, see below |
| `paths.*` | Where code lives. An empty field means the project has no such layer, and plans must not invent one |
| `project.stack` | Turns on the stack-gated skills |
| `codex.profile` · `codex.profiles.*` · `codex.agents.*` | Semantic Codex model/effort overrides; per-agent wins, and `native-ultra` is top-level-only |
| `codex.model` · `codex.models.{heavy,standard,light}` · `codex.reasoningEffort` | Backward-compatible flat/tier/global overrides used before the semantic default |
| `autonomy.*` | How much runs without asking — see below |

### The tools you declare have to exist

`tooling.commands.format` runs once for a changed supported file after an edit, and
`tooling.commands.lint` runs at Stop only for changed JS/TS paths. The hooks remain fail-open; they
do not install packages, select a global binary, or silently replace the project's toolchain.

For a JavaScript/TypeScript project, keep the tools in the project manifest and route the plugin
through package scripts:

```bash
bun add -d oxlint oxfmt typescript@7
```

```json
{
  "scripts": {
    "format": "oxfmt --write",
    "lint": "oxlint --deny-warnings",
    "type-check": "oxlint --type-aware --type-check --threads 1"
  }
}
```

Session start reports missing local tools without pretending that a gate ran. A package-script
command such as `bun run lint --` is resolved by the project's manifest; hooks pass only the edited
or changed paths and never invoke a network launcher. Type-aware Oxlint is a final gate only at
`/verify`, commit or CI. Test runners keep their project configuration.

### Oxc + Zed for JS/TS

Oxlint is the sole editor diagnostic provider, Oxfmt is the sole formatter, and vtsls is the sole
TypeScript provider for types, completion and navigation. The editor uses vtsls's bundled compatible
TypeScript SDK; the project-local `typescript@7` remains the compiler used by gates. Do not set
`tsdk` to `node_modules/typescript/lib`, because TypeScript 7 does not ship the legacy `tsserver.js`
that vtsls expects. Keep `vtsls.autoUseWorkspaceTsdk` disabled in
`templates/zed/settings.json`. Type-aware Oxlint belongs only to `/verify`, commit and CI; edit
hooks use regular diagnostics and formatting.

The full policy and official links live in
[`references/shared/130-typescript7-oxc-gates.md`](references/shared/130-typescript7-oxc-gates.md).

Graph Powers' own ESM verification gates also run through Bun 1.4. The installer remains
Node-compatible, but agents and CI do not use Node as the test executor.

**Use a different `optInPrefix` per project.** With the same key in two repositories, a commit
approval given in one starts counting in the other. The versioned test covers exactly that case.

A project **without** a config keeps working on the defaults — the git rails still hold, just with
the default branch and prefix. The file lives at `.graph-powers/config.json`; `.claude/config.json`
is still read, for projects that only ever run Claude Code.


---

## Autonomy — how much runs without asking

A harness that asks permission to run `git status` teaches people to approve without reading, and
that habit is more dangerous than any command it was guarding. So the installer writes a permission
allowlist covering everything the harness itself runs, writes `~/.graph-powers/config.json` if it
is missing, repairs a project config whose `level: autonomous` is defeated by `bashDefault: ask`,
and the guardrails take their default from one config field.

```json
"autonomy": {
  "level": "autonomous",
  "bashDefault": "allow",
  "cleanup": "allow",
  "toolDefault": "allow",
  "destructiveFloor": true
}
```

Do not write `"bashDefault": "ask"` under `"level": "autonomous"`. The per-field override wins,
and that combination is `Hook PreToolUse:Bash requires confirmation for this command`. To keep
asking, use `"level": "guarded"` (or `--autonomy guarded`).

| Level | An unrecognised command | Cleanup (`rm -rf build`, caches) | Commit / push |
|---|---|---|---|
| `autonomous` **(installer default)** | runs | runs | run without an opt-in key |
| `guarded` (schema default when the field is absent) | asks | asks | need `<PREFIX>_ALLOW_COMMIT=1` in the turn |

Override any single action without leaving the level:

```json
"autonomy": { "level": "autonomous", "git": { "push": "ask" } }
```

The installer writes that user file if it is missing (git stays at `ask` there). To write it by
hand:

```jsonc
// ~/.graph-powers/config.json
{
  "autonomy": {
    "machineWide": true,
    "level": "autonomous",
    "destructiveFloor": true,
    "git": { "commit": "ask", "push": "ask", "protectedBranch": "ask" }
  }
}
```

Without `machineWide: true`, user scope may tighten a repository but cannot loosen one the operator
has not reviewed. Even with it, git automation and disabling the destructive floor do not cross
from the home directory; those remain project-scoped decisions.

### The floor that holds at either level

`destructiveFloor` keeps refusing the operations **git cannot give back**:

`rm -rf /` · `rm -rf ~` · `mkfs` · `dd` to a device · `chmod -R 777 /` · `--no-preserve-root` ·
`DROP DATABASE` · `TRUNCATE` · force-pushing a protected branch · writing to `.env` and the other
`protectedFiles`.

**Deleting a file inside a committed repository is not on that list** — git restores it, so
autonomous mode does it without asking. The line is drawn at recoverable, not at scary.

Set `"destructiveFloor": false` to remove even that. Nothing else in the harness will stop those
commands; the field exists so the choice is explicit and written down rather than discovered.

### Package managers

The plugin does not pick one for you. Every manager runs by default. A project that genuinely
cannot mix them — a lockfile that must not fork — declares its own:

```json
"autonomy": { "allowPackageManagers": ["bun", "bunx"] }
```

Declaring only a manager keeps its runner in the same lockfile family. Guarded mode asks before the
runner downloads and executes an unnamed package; autonomous mode proceeds. A runner from another
manager family is still denied.

---

## The guardrails

Fourteen hook scripts, wired through fifteen registrations in
[`hooks/hooks.json`](hooks/hooks.json), are discovered by Claude Code, Codex and Grok when the
plugin is installed. Cursor loads the generated [`hooks/hooks-cursor.json`](hooks/hooks-cursor.json)
(twelve registrations: PermissionRequest and Notification do not exist there). Grok uses the
Claude file; `_config.py` adapts camelCase payloads and Grok tool names so the same gates run. `smart_bash_approver` runs at `PreToolUse` to block the destructive floor and again at
`PermissionRequest` to approve an escalation that the same classifier already allowed;
`tool_approver` answers the same event for everything that is **not** a shell command. A
guarded `ask` is left to the normal approval flow; an autonomous allow never reaches the user.
Codex still requires explicit trust in `/hooks` before the registrations execute. That closes one
of the audit's findings: two of the projects had **nine hooks each, written and never connected**.
They existed on disk and never ran once.

| Guardrail | What it does | How to release it |
|---|---|---|
| `git_commit_gate` · `git_push_gate` · `git_branch_gate` | Nothing is committed, pushed, or lands on a protected branch without approval in the turn | `<PREFIX>_ALLOW_COMMIT=1` etc. |
| `graph_guardrails` | Kill switch (`AGENT_STOP` at the root), spawn ceiling, per-agent round ceiling, write lease | `<PREFIX>_ALLOW_SPAWN_OVER=1`, `<PREFIX>_ALLOW_OFF_LEASE=1` |
| `protect_files` | `.env`, lockfiles, `.git/`, and whatever the project lists in `protectedFiles` | — |
| `commit_audit_gate` · `smart_bash_approver` · `ultracite` | The audit this project declared, run before a commit; refusal of destructive commands; formatting after an edit | `gates.preCommitAudit`, `autonomy`, `tooling.commands` |
| `tool_approver` | The approval prompt for every tool that is not Bash — subagent spawns, MCP calls, fetches, workflows. Answers it under `autonomous`, stays out of the way under `guarded`, and never overrides a `PreToolUse` denial | `autonomy.toolDefault` |
| `auto_update` | Updates Claude Code and the Codex clone fallback in a detached process; native Codex, Cursor and Grok stay foreground-only | `autoUpdate.enabled: false` |
| `branch_session_notice` · `session_context` · `notify` | Inform; never block | — |

All of them are **fail-open**: missing, unreadable or mistyped configuration falls back to the
defaults instead of taking the session down. A guardrail that breaks your work when *it* has the
bug teaches people to switch guardrails off.

```bash
python3 hooks/test_hooks.py     # sandboxed guardrails; exit 0 = everything holds
```

The suite proves the property that matters: **the same hook file, in two different projects**,
denies with each one's key, and one project's key does **not** work in the other. It covers both
harnesses — the Claude environment variable and the Codex payload — because a guardrail that
resolves the wrong project denies and permits against somebody else's rules.

---

## Context cost

```bash
claude plugin details graph-powers
```

Reports the inventory and the always-on cost of having everything available. Hooks show up as
`harness-only — no model context cost`: they consume none.

If that is too much for a small project, `claude plugin disable` the components it does not use.
Editing the plugin to fit one project is the beginning of the problem it was built to solve.

---

## Why the cleanup is manual

The installer does not delete a single file, and that is a decision rather than a limitation.

Cleaning up means telling a diverged copy apart from the only existing version of something. A
`diff` settles the easy case; the hard case is the file that looks identical but gained three lines
months ago that nobody remembers writing. Automating that means deleting without review.

So the cleanup is a procedure that lists, compares, classifies and **stops**. It is slower on
purpose.

---

## Documentation

**The specs the plugin installs into your project.** These three are not documents about Graph
Powers — each one specifies what the *host project's* counterpart must contain, how to source every
section from the repository, and how to improve an existing one without destroying decisions. The
setup playbook applies them in Step 6.

| Spec | Produces, in your project | Answers |
|---|---|---|
| [`DESIGN.md`](DESIGN.md) | your `DESIGN.md` | When two visual decisions conflict, which one wins? |
| [`PRODUCT.md`](PRODUCT.md) | your `PRODUCT.md` | When a change is technically fine but the product is worse, what catches it? |
| [`REVIEW.md`](REVIEW.md) | your `REVIEW.md` | What does this project refuse to merge? |

**About the plugin itself.**

| File | What it holds |
|---|---|
| [`AGENT_SETUP.md`](AGENT_SETUP.md) | The setup playbook the agent executes |
| [`docs/AUDIENCE.md`](docs/AUDIENCE.md) | Who Graph Powers is for, what it solves, what it does **not** |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | The decisions, and what was refused, with reasons |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | How to review a change to Graph Powers |
| [`AGENTS.md`](AGENTS.md) | Rules for agents working in this repository |
| [`schema/config.schema.json`](schema/config.schema.json) | The project parameter contract |

---

## Maintenance

A fix lands here and reaches every project on the next update:

```bash
claude plugin update graph-powers@graph-powers        # Claude Code
node ~/.graph-powers/src/bin/graph-powers.mjs --update  # the clone, and the Codex artefacts
```

Both happen on their own at session start — this is only the manual form.

That is the only reason this repository exists. If a change ever has to be made in five places
again, something went back to the old model.

Before adding anything, one question earns its keep: **does this artefact have anything that
invokes it?** The originating audit found 13 orphans and 32 dangling references. A harness that only
grows carries assumptions that expired.

Contributions: read [`CONTRIBUTING.md`](CONTRIBUTING.md) before opening a PR.

---

## When something refuses and it is not this plugin

Two failures look like plugin defects and are not. Both come from a hook of your own, and both were
diagnosed wrong here first — the wrong diagnosis cost several hours, so the evidence that separates
them is written down rather than the conclusion.

### An agent will not spawn

    Unknown subagent_type 'graph-powers:explorer'. Valid: explorer, debugger, evaluator, ...

Claude Code's own refusal never reads like that. Its wording is `Agent type 'X' not found. Available
agents: ...`, and its list shows plugin agents **namespaced**. A `Valid:` phrasing listing **bare**
names is a `PreToolUse` hook matching `Agent`, denying the call before the CLI ever sees it.

Why a hook gets this wrong: an allowlist is usually built by scanning `.claude/agents/`, and a
plugin's agents are not there. They live in the plugin and are addressed `<plugin>:<agent>`, so
every one of them is unknown to that list — including agents added after the list was written.

Two checks, in order:

```bash
claude plugin details graph-powers@graph-powers    # what the plugin actually ships
grep -rn "subagent_type" ~/.claude/hooks/*.py      # who else is validating it
```

Then fix the hook. It must not deny a name containing `:` — the runtime registry validates plugin
agents itself and rejects an invalid one with its own clear error, so a second opinion from a local
list can only produce false denials. Better still, teach the discovery to read plugin agents:

```python
for base in (Path.home() / ".claude/plugins/marketplaces",
             Path.home() / ".claude/plugins/cache"):
    for md in base.glob("*/**/agents/*.md"):
        plugin = md.parts[md.parts.index(base.name) + 1]
        known.add(f"{plugin}:{md.stem}")     # and md.stem, for callers still using the short name
```

**Restarting does not help**, whatever it looks like. The hook runs on every call and rebuilds its
list each time. The one-command test that settles it: run the same spawn in a fresh process —
`claude -p "spawn subagent_type 'graph-powers:explorer' ..."`. A fresh process carries a fresh
registry, so an identical refusal means nothing about your session was stale.

### A stop is blocked by a linter with nothing to lint

    Lint found 1 error(s) after safe auto-fix.
    No files found to lint. Please check your paths and ignore patterns.

Oxlint reads JavaScript and TypeScript. Handed a batch that is JSON alone it may report no lintable
source, and a hook counting exit codes can mistake that for a lint error — on a change whose only
matching file was a config or a schema. Oxfmt formats JSON while Oxlint receives only existing
changed JavaScript/TypeScript paths:

```python
OXLINT_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
```

and treat a change with no relevant source paths as clean, as the changed-path Stop hook does.

This plugin's own `hooks/ultracite.py` runs only `tooling.commands.format` and
`tooling.commands.lint` as the project declared them, and never chooses a linter for you — so if the
message names a tool your config does not, it is not coming from here.

## Compatibility notes

There is no npm package. Installing from a fork is the same two paths pointed somewhere else:

```bash
# from a fork's clone
git clone https://github.com/<you>/graph-powers && node graph-powers/bin/graph-powers.mjs

# or the native Claude Code commands, no installer at all
claude plugin marketplace add <you>/graph-powers
claude plugin install graph-powers@graph-powers --scope user
```

A `graph-powers` package exists on npm at 1.0.0 and is **not** maintained. It was the first
release's distribution channel and was dropped: publishing put an account, a token and a release
between a one-line fix and the machine that needed it, for a plugin with no build step and no
dependencies. Use git.

Codex tracks hook trust by definition, so after an install or update, open `/hooks` in Codex and
approve the project hooks.

---

## Licence

MIT — see [`LICENSE`](LICENSE). Third-party attribution is in [`NOTICE`](NOTICE).
