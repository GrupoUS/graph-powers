# AGENT_SETUP.md — the setup playbook

> **You are the agent reading this.** This file is not documentation for a person to follow; it is
> the procedure you execute, in order, in the repository the session is open in.
>
> Scoped, reversible setup writes and their validation run without pausing. Stop only before a
> destructive cleanup, a credential or secret change, an outward-facing action, or any write whose
> target cannot be attributed safely. Autonomy is useful only while its boundary stays legible.

---

## What you are setting up

Graph Powers is a shared harness — agents, skills, commands and guardrails — that installs once and
adapts to each project through one config file. Installing it changes nothing on its own. What
changes things is this playbook: it checks optional integrations and workflow binaries, writes the
project's parameters, **improves the instruction files that already exist** rather than replacing
them, and
removes the local copies that currently shadow the plugin.

That last part is the step that decides whether any of this works, and it is the one that needs
judgement. Which is why it is a procedure with explicit destructive and outward-action gates, and
not a blind cleanup script.

### The rule everything else follows

Claude Code precedence is `Managed > CLI > Project > User > Plugin`.

**While a local file with the same name as a plugin agent, skill or command exists, the local file
wins.** Install the plugin without cleaning, and the project runs exactly what it ran before — and
the person concludes, wrongly, that the plugin does nothing.


---

## The rule that decides where everything goes

**Global by preference. Local only when it cannot be anything else.**

The harness is byte-for-byte identical in every project, so it installs **once per machine** and
serves every repository — including ones that do not exist yet. What differs per project stays in
that project, and nothing else does.

| Goes GLOBAL — installed once, serves everything | Where |
|---|---|
| Claude Code plugin: agents, skills, commands, guardrails, workflows, shared references | registry under `~/.claude/plugins/installed_plugins.json` plus its versioned plugin cache (`--scope user`) |
| Claude Code permission posture | `~/.claude/settings.json`; this is not the plugin payload |
| Codex native plugin: skills, guardrails and references | source/cache reported by `codex plugin list --json`; Codex Desktop uses it only after the separate proof in Step 9 |
| Codex native companion roles | `<codex-home>/agents/*.toml`, explicitly emitted after native installation because the current plugin manifest has no agent-role resource |
| Codex clone fallback: skills | `~/.agents/skills/` |
| Codex clone fallback: subagents, guardrails and references | `~/.codex/agents/*.toml` · `~/.codex/hooks.json` · `~/.codex/graph-powers/` |
| Clone fallback machine-wide instruction block | `~/.codex/AGENTS.md` |
| Cursor plugin: skills, agents, commands, native hooks | `.cursor-plugin/` in the Cursor marketplace cache; `--target cursor` does not install it |
| Cursor IDE Run Mode (this is what stops the confirmation flood) | `~/.cursor/permissions.json` |
| Cursor CLI (`cursor-agent`) | `~/.cursor/cli-config.json` |
| Grok plugin: skills, agents, commands, Claude-shaped hooks | `.grok-plugin/` plus the canonical `hooks/hooks.json` |
| Grok CLI approval (this is what stops the confirmation flood) | `config.toml` in `GROK_HOME`, or `~/.grok/config.toml` when that variable is unset |
| Hermes native plugin: skills, command documents and agent contracts | `plugin.yaml` + `__init__.py`; native `graph-powers:<name>` registrations |

| Stays LOCAL — belongs to this repository and nothing else | Where |
|---|---|
| The parameters: branch, gate commands, paths, opt-in prefix | `.graph-powers/config.json` |
| Domain rules | `.claude/rules/` · `.codex/rules/` |
| The three authorities | `DESIGN.md` · `PRODUCT.md` · `REVIEW.md` |
| Project identity and invariants | `CLAUDE.md` · `AGENTS.md` |
| Anything this project genuinely overrides | `.claude/agents/`, `.claude/skills/`, `.claude/commands/` |

### Hook capability is per client, not per repository

Do not use one client's green check as proof for another. The repository is shared; discovery,
permission posture and session reload are not:

| Client | Executable Graph Powers hooks | Setup rule |
|---|---|---|
| Claude Code | yes — plugin `hooks/hooks.json` | install first, then permission posture; restart after install/update |
| Codex CLI native | yes — `.codex-plugin/plugin.json` points at the canonical file | use one native/clone route, approve `/hooks`, restart after cache replacement |
| Codex Desktop | conditional — some builds launch a bundled Codex `app-server` against the same Codex home | never infer it from a CLI pass; run the separate Desktop proof in Step 9 and restart the app itself |
| Cursor IDE / `cursor-agent` | yes — generated `hooks/hooks-cursor.json` | marketplace plugin first; `--target cursor` configures posture only |
| Grok CLI | yes — `.grok-plugin/plugin.json` points at the canonical file | native plugin or one clone path, then posture in the active Grok home |
| Hermes Agent | **no executable git hooks** — `plugin.yaml` + `__init__.py` register skills only | `hermes plugins install GrupoUS/graph-powers --enable`, then `hermes plugins doctor <clone> --ci`. Guardrails are `NOT ENFORCED`; report that. Skills load as `graph-powers:<name>` |
| Zed native agent | **no repository hook surface is implemented** | rules, skills and editor settings still load, but executable guardrails are `NOT ENFORCED` and must be reported that way |

**Safety ordering:** never write `bypassPermissions`, `unrestricted` or `always-approve` before the
same client has proved its plugin, hook manifest and literal `python3` command. A permissive client
without executable hooks is not autonomous; it is unguarded.

**Why global is correct here rather than sloppy:** the guardrails read *the project's own*
`.graph-powers/config.json` at runtime, through `hooks/_config.py`. One global copy therefore
enforces a different work branch and a different opt-in key in every repository. Copying the
harness into each project would buy nothing and reintroduce the divergence this plugin exists to
end — eleven skills copied into five repositories is five copies that drift.

**The only reason to go local instead:** the team must receive the harness by cloning the
repository, on machines where nobody will run an installer. Then use `--scope project`, and accept
that the copy is now yours to keep in sync.

### Check before you install

Global installation is idempotent, but a registry row alone is not proof: it may point at a partial
package, an older direct runner, or a cache path an open process retained before an update. First use
the client's own inventory to learn which routes exist (`claude plugin list`,
`codex plugin list --json`, `grok plugin list --json`). Do not select a Cursor cache by mtime or by
"the first valid directory".

After Step 0 establishes `PLUGIN`, run the shared read-only verifier. It reads Claude's exact scoped
`installPath`, Codex's native inventory or clone manifest, every Cursor cache candidate, and Grok's
reported `path`; then it opens the manifest and canonical hook file inside that exact package:

```bash
python3 -X utf8 "$PLUGIN/bin/verify-hook-clients.py" --client all --project-dir .
```

`PASS` requires the exact registration set derived from the canonical source (fifteen native and
twelve on Cursor in `1.12.0`), every guarded `runpy.run_path` runner, all target scripts, and the
packaged planning/TDD method files. A corrupt Cursor candidate or
two candidates claiming the highest version is an error, never a reason to fall back silently. If
native Codex and the clone manifest both exist, the command fails because they register the same
hooks from different roots; Step 9c migrates that state before setup continues. Hermes is checked
separately in the same output: its native registration count and Doctor result must be present, and
its hook posture remains `NOT ENFORCED`.

---

## Step 0 — Establish where you are

Report all of this back before touching anything:

```bash
# the repository — git speaks the same on all three platforms
git rev-parse --show-toplevel
git branch --show-current
git status --short                     # dirty files are the user's; you do not touch them

# everything else, in one pass that runs the same on Linux, macOS and Windows
python3 - <<'STATE'
import json, os, shutil, subprocess, sys

for tool in ("claude", "codex", "cursor-agent", "grok", "hermes", "python3", "node"):
    exe = shutil.which(tool)
    if not exe:
        print(f"{tool:8} not installed")
        continue
    out = subprocess.run([exe, "--version"], capture_output=True, encoding="utf-8",
                         errors="replace", check=False).stdout.strip()
    print(f"{tool:8} {out or exe}")

codex = os.path.expanduser("~/.codex/graph-powers-installed.json")
print("global codex install:",
      json.load(open(codex)) if os.path.exists(codex) else "none")

for d in (".claude", ".codex", ".graph-powers", ".claude/agents", ".claude/skills",
          ".claude/commands", ".claude/rules"):
    print(f"{d:20}", sorted(os.listdir(d)) if os.path.isdir(d) else "absent")

for f in ("CLAUDE.md", "AGENTS.md", ".claude/settings.json"):
    if os.path.exists(f):
        n = sum(1 for _ in open(f, encoding="utf-8", errors="replace"))
        print(f"{f:20} present, {n} lines")
STATE

# what already exists globally for Claude Code — its own command, whatever the shell
claude plugin list
```

Then locate the plugin on this machine, in this order, and **say which one you found**:

1. `$GRAPH_POWERS`, if the variable is set;
2. the `source.path` for enabled `graph-powers@graph-powers` in `codex plugin list --json`;
3. the exact user-scope `installPath` from Claude's `installed_plugins.json` — never an unreferenced cache;
4. Cursor is discovery-only here: `verify-hook-clients.py` inspects every dedicated cache candidate
   and chooses the unique highest valid version; do not reproduce that algorithm by hand;
5. the `path` for Graph Powers in `grok plugin list --json` (respect `GROK_HOME`);
6. the native Hermes package shown by `hermes plugins show graph-powers`;
7. `~/.graph-powers/src/`, or any other clone of `GrupoUS/graph-powers` on this machine;
8. if none exists, install it and say which route you took:

   ```bash
   # Claude Code, inside a session:
   #   /plugin marketplace add GrupoUS/graph-powers
   #   /plugin install graph-powers@graph-powers
   # Anywhere, from a clone:
   git clone https://github.com/GrupoUS/graph-powers.git ~/.graph-powers/src
   # Hermes Agent:
   hermes plugins install GrupoUS/graph-powers --enable
   ```

   There is no package to install from a registry: a clone is the artefact, and `git pull` is the
   update.

**Export it, do not just name it.** The rest of this playbook runs commands that use
`$PLUGIN`, and a convention that lives only in prose resolves to an empty string in a real shell —
turning `node "$PLUGIN/bin/graph-powers.mjs"` into `node /bin/graph-powers.mjs`:

```bash
# bash / zsh
export PLUGIN=<the directory you just found>

# PowerShell
$PLUGIN = "<the directory you just found>"
$env:PLUGIN = $PLUGIN

# prove the source root, then inventory every installed client without writing anything
python3 -c "import os,sys;p=os.environ.get('PLUGIN','');sys.exit(print('PLUGIN=' + p) if os.path.isfile(os.path.join(p,'AGENT_SETUP.md')) else 'PLUGIN does not point at a plugin root')"
python3 -X utf8 "$PLUGIN/bin/verify-hook-clients.py" --client all --project-dir .
```

**Back up before the first write, and show the command you ran:**

```bash
python3 - <<'BACKUP'
import datetime, os, shutil
stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
for src in (".claude", "CLAUDE.md", "AGENTS.md"):
    if not os.path.exists(src):
        print(f"{src}: absent, nothing to back up")
        continue
    dst = f"{src}.bak-{stamp}"
    shutil.copytree(src, dst) if os.path.isdir(src) else shutil.copy2(src, dst)
    print(f"{src} -> {dst}")
BACKUP
```

---

## Step 1 — Check optional integrations and workflow binaries

No plugin is required. This step checks two **optional plugins** that commands can call into and the
**binaries** documented workflows shell out to, then installs only what the user chooses or the
workflow requires. Neither is vendored. A copied snapshot
of somebody else's work goes stale and cannot be updated — which is the exact failure this harness
exists to end, one level up.

Start by running the preflight at the end of this step. It prints one line per prerequisite and is
the fastest way to know which halves of this step you can skip.

**Nothing required is external.** The method layer the commands open with — discovery, design,
writing and executing plans, test-driven development, the evidence gate, parallel dispatch,
receiving a review — ships inside this plugin as `skills/planning`,
`commands/pr-review.md § 4.1` and
`references/shared/005-method-bootstrap.md`, `015-verification-gate.md`,
`070-parallel-agent-spawn.md`.
`/design` needs nothing installed either: its direction, its craft passes and the landing-page
system are the plugin's own `designer` and `landing-page-design` skills.

**There is no per-skill install.** Claude Code, native Codex, Cursor and Grok expose the plugin's
whole `skills/` directory. The Codex clone fallback enumerates every skill directory and copies all
of `references/`; it does not keep a hand-maintained allowlist. Installing or updating Graph Powers
therefore installs planning's Phase C, TDD policy and execution references together. If any part of
that authority is missing, update or reinstall the plugin and restart the session — do not copy one
folder by hand and create a version that cannot be updated as a unit.

A `superpowers` plugin left from an earlier setup is not used by this harness any more — every
method call here is namespaced `graph-powers:` — so it can stay or go at the user's choice; do not
install it on their behalf.

### Package runners — resolve the runner before typing any `npx`

**Resolve the runner from the project before you type the command.** `tooling.packageManager` in the
config (Step 3) decides it, and getting it wrong is not a style question: a project that declares
`autonomy.allowPackageManagers` refuses every manager outside its own family, so `npx` inside a bun
project is denied by this plugin's own guardrail — correctly, since that setting is what keeps the
lockfile from forking. Widening the allowlist to get past it is the wrong fix.

| `tooling.packageManager` | runner |
|---|---|
| `npm` | `npx` |
| `bun` | `bunx` |
| `pnpm` | `pnpm dlx` |
| `yarn` | `yarn dlx` |

Every `<runner>` in this playbook substitutes from this table. A global install sidesteps the
question for a binary; a one-off `npx` never does.

### landing-page-design — now inside the plugin

Until 1.9.5 this skill was installed by copy into `~/.claude/skills` and `~/.agents/skills`. Since
1.10.0 it ships in `skills/landing-page-design/` as an adapted work, and a personal copy left behind
is worse than absent: a personal-scope skill wins over a plugin skill of the same name, so a bare
`Skill("landing-page-design")` keeps loading the old upstream file — the one whose description
claims every web UI — and the plugin's version never runs. The preflight below reports that state as
`SHADOWS`.

Remove both copies. The Claude one is usually a symlink into the Codex one, which is why the
command unlinks before it deletes, and it is a recursive delete under the home directory — the
kind this plugin's own guardrail refuses from an agent, correctly. Run it yourself, or hand it to
the user with `!` in front:

```bash
python -X utf8 -c "import os,shutil;h=os.path.expanduser('~');[(os.unlink(p) if os.path.islink(p) else shutil.rmtree(p)) for p in (os.path.join(h,*d,'landing-page-design') for d in (('.claude','skills'),('.agents','skills'))) if os.path.lexists(p)]"
```

Re-run the preflight; the row reads `ok`. Nothing else changes: `/design` loads the skill only for
a landing or marketing surface, and the project's tokens still win over its canon.

### Keeping them current

The optional plugins age independently of this plugin. Add these to whatever the project uses for
routine maintenance, and tell the user they exist:

```bash
claude plugin update graph-powers@graph-powers
# Codex native, Cursor and Grok use their own marketplace/client update paths; see Step 9
```

### The other two plugins, both conditional

| Plugin | Reached from | Without it |
|---|---|---|
| `codex@openai-codex` | `/debug` escalation (`commands/debug.md` § 1.3, § 1.6, § 1.7) | escalation falls through to `/debug recover`; nothing hangs |
| `code-review@claude-plugins-official` | `/pr-review` § 3E, already labelled best-effort | one review path is missing; the others still run |

The `codex` plugin needs the `codex` binary as well — the plugin routes to it, and the agent it
ships cannot run a CLI that is not installed. Install both or neither.

### The binaries the skills shell out to

Nothing here is bundled, and a missing one does not fail at startup. It fails mid-task, as
`command not found`, after the agent has already promised evidence it can no longer produce.

**The plugin's own code needs no packages.** Every `hooks/*.py`, `.github/*.py` and
`skills/**/*.py` imports only the Python standard library; every `workflows/*.js`, `codex/*.mjs`
and `bin/*.mjs` imports only Node builtins. PyYAML appears in `.github/workflows/ci.yml` and is a
*contributor's* dependency, not a user's — `check_listing_budget.py` deliberately parses frontmatter
by hand rather than assume it. So what follows are tools the documented **workflows** invoke, never
packages this code depends on.

#### Three classes, and only one of them needs installing

| Class | What it means | Members |
|---|---|---|
| **On PATH** | cannot be fetched on demand | `python3`, `git`, `node`, `claude`, `gh`, `gitleaks`, `psql`, a browser |
| **Fetched per call** | the package manager downloads it each invocation; a runner plus network is the whole requirement | `lighthouse`, `unlighthouse`, `vercel`, `playwright` |
| **Works either way, better global** | resolves through a runner, but re-downloads every call and keeps state between them | `agent-browser` |

That distinction is the point of this section. Most of what you will see in fenced blocks across the
skills is the middle class, so the real prerequisite list is far shorter than the list of tool names.

#### `python3` is the name, and 3.10 is the floor

All fourteen hook scripts — fifteen event registrations because the Bash approver also handles
`PermissionRequest` — spell the interpreter `python3`, with no fallback. Where it answers to
`python` or `py -3` and not to `python3` — the common case on
Windows — every guardrail fails to start. **Cardinal 3 makes hooks fail open**, so nothing reports
it: the session looks normal while the commit gate, the push gate, the branch gate, the destructive
floor and the write lease are all absent.

**The floor is 3.10, not 3.9.** Several hooks annotate with `X | None` and have no
`from __future__ import annotations`, so the annotation is evaluated at import time and an older
interpreter raises before the hook runs — `hooks/smart_bash_approver.py:426` and
`hooks/ultracite.py:156` are two. `bin/graph-powers.mjs:536-546` is where that floor is enforced and
is canonical for it; this section does not restate the check, only its consequence.

**One Windows trap worth knowing before you conclude "missing":** there is a Microsoft Store stub
literally named `python3.exe` that opens the Store and exits non-zero, so probing `python3` reports
absent on a machine that has Python 3.12. Probe `python3`, then `python`, then `py -3`
(`bin/graph-powers.mjs:160-165`), and make whichever answers available under the name the hooks
use.

#### `agent-browser`, and why global rather than `bunx`

`/debug frontend`, the `graph-powers:verification` agent and `Skill("webapp-testing")` drive a real browser
through it. The skills spell it `bunx agent-browser` in twenty-five places, and that spelling is a
liability in any project that does not use bun: a project declaring `autonomy.allowPackageManagers`
has this plugin's own guardrail refuse `bunx`, correctly — the same trap the *Package runners* note in
this step warns about, with the same runner table as its answer. A global install sidesteps the runner
question entirely — every `bunx agent-browser …` in the skills then works as plain `agent-browser …`.

One more place hardcodes bun the same way. `skills/debugger/scripts/find_polluter.py:92` runs
`["bun", "run", "test", …]`, and its failure is worse than a missing command: in a non-bun project
the bisect runs nothing and reports no polluter, which reads as a clean result. Both are defects
against this repository's own runner-resolution rule; installing bun globally hides the symptom
without fixing either. (`performance-optimization`'s `security-baseline` pack was the third case;
it resolves `${tooling.packageManager}` now.)

```bash
npm install -g agent-browser
agent-browser doctor
```

`doctor` is the verification, and read its summary rather than assuming: it checks the CLI, the
state directory, disk, an available Chrome, the CDN and a real headless launch. Only if it reports a
Chrome failure do you also need `agent-browser install`, which downloads Chrome for Testing — on a
machine that already has Chrome, Chromium, Brave or Edge, `doctor` passes without it.

#### Everything else, in one table

Package names and the binary each one exposes were read from the registries, not from memory.

| Tool | Level | Who needs it | Install |
|---|---|---|---|
| `python3` | REQUIRED | every hook, gate and bundled script | your OS package manager; **3.10 or newer** |
| `git` | REQUIRED | every command; the guardrails read the worktree | your OS package manager |
| `node` | REQUIRED | workflows, `bin/`, the Codex installer | nodejs.org, 18 or newer |
| a package manager | REQUIRED | every per-call fetch above | whatever `tooling.packageManager` declares. `hooks/_config.py:373` already recognises `npm`, `bun`, `pnpm`, `yarn`, `deno`, `uv`, `uvx`, `pipx` and `poetry` as runners, so a Python project on `uv` is a first-class case |
| `claude` | REQUIRED | the harness; `graph-powers:evaluator` Mode 5 runs it headless for the dollar-capped second opinion | `npm install -g @anthropic-ai/claude-code` |
| `gh` | CONDITIONAL — required the moment a PR or an issue is involved | `gh pr checkout`, `gh issue view` | cli.github.com — then `gh auth login`, because `gh auth status` failing is its own stop |
| `agent-browser` | RECOMMENDED | `/debug frontend`, `webapp-testing`, the `graph-powers:verification` agent | `npm install -g agent-browser` |
| a Chrome-family browser | RECOMMENDED | what `agent-browser` drives | already present on most machines; otherwise `agent-browser install` |
| `gitleaks` | OPTIONAL | `/perf security-baseline` secret scan | github.com/gitleaks/gitleaks |
| `psql` | OPTIONAL | database evidence in `/debug auth-db` and `/debug backend` | your OS package manager |
| `codex` | OPTIONAL | the Codex half, and `codex:codex-rescue` escalation | `npm install -g @openai/codex` |
| `cursor` | OPTIONAL | the Cursor half; the IDE permission file is what stops Auto-review | cursor.com |
| `grok` | OPTIONAL | the Grok CLI half; `~/.grok/config.toml` is what stops the confirmation flood | docs.x.ai/build |
| `hermes` | OPTIONAL | native skills, command documents and agent contracts; hooks are `NOT ENFORCED` | hermes-agent.nousresearch.com |
| `code-review-graph` | OPTIONAL | `/plan` Step 0 structural search | `python3 -m pip install code-review-graph` |

`code-review-graph` is the one whose absence is designed for: `references/shared/115-code-graph.md`
says the graph steps are **SKIPPED, never blocking**, and `/plan` falls back to grep. Install it for
speed, not for correctness.

`oxlint` and `oxfmt` are not in this table on purpose — they are project-local gate tooling, and
Step 3 installs them where that decision is made.

**Five environment variables behave like optional prerequisites**, in that whatever reads them does
nothing at all when they are unset and says so nowhere: `VERCEL_TOKEN`
(`skills/performance-optimization/references/vercel-data.md`), `CHROME_PATH` and `HTTPS_PROXY` for
the browser stack, and `GITHUB_REPO`, `PROJECT_VPS_HOST` plus `DB_STATUS_COMMAND`, which
`skills/debugger/scripts/fetch_logs.py:21-41` reads to know where to look for logs. Set the ones the
project actually uses, and name in your report the ones you left unset.

#### MCP servers, and why the name matters

Two agents declare MCP tools in their frontmatter. A tool name is built from the **server name**,
with `.` and spaces replaced by `_` and hyphens left alone — so `claude.ai Context7` yields
`mcp__claude_ai_Context7__query-docs`. Add that server under any other name and the slug changes,
`agents/librarian.md` stops resolving them, and that agent registers silently without them.

| Server name, exactly | Slug it must produce | Declared by | Level |
|---|---|---|---|
| `tavily` | `tavily` | `graph-powers:librarian`, `graph-powers:evaluator` | REQUIRED for `graph-powers:librarian` |
| `claude.ai Context7` | `claude_ai_Context7` | `graph-powers:librarian` | RECOMMENDED |
| `sequential-thinking` | `sequential-thinking` | `graph-powers:librarian` | OPTIONAL |

**Why `graph-powers:librarian` cannot degrade and `graph-powers:evaluator` can.** Check the
frontmatter rather than assuming. `agents/librarian.md:4` grants exactly one non-MCP tool,
`WebFetch` — no `WebSearch`, no `Grep`, no `Glob`. `WebFetch` retrieves a URL you already hold; it
cannot find one. Strip the MCP servers and that agent can no longer do the job its own description
promises, so `/research` and the external half of `/plan` return nothing useful. `agents/evaluator.md`
carries `WebSearch` alongside Tavily and really does degrade rather than break. Two agents, two
different answers, and the frontmatter is what separates them.

```bash
claude mcp add --transport http tavily "https://mcp.tavily.com/mcp/?tavilyApiKey=${TAVILY_API_KEY}" -s user
claude mcp add sequential-thinking -s user -- npx -y @modelcontextprotocol/server-sequential-thinking
```

Context7 is enabled as a **claude.ai connector**, not with `claude mcp add` — that is what produces
the `claude.ai ` prefix the slug depends on.

#### The preflight

One block, every prerequisite above, run from the project root. It reads state and installs nothing.

```bash
python3 - <<'PREFLIGHT'
import json, os, re, shutil, subprocess, sys

def run(exe, *args, timeout=30):
    try:
        r = subprocess.run([exe, *args], capture_output=True, encoding="utf-8",
                           errors="replace", timeout=timeout, check=False)
        return (r.stdout or r.stderr).strip()
    except Exception as exc:
        return f"<{exc.__class__.__name__}>"

def first(text):
    lines = [l for l in text.splitlines() if l.strip()]
    return lines[0][:38] if lines else "installed"

def row(name, state, level, who):
    print(f"  {name:19} {state:<40} {level:12} {who}")

print("-- runner: at least one package manager --")
managers = [m for m in ("bun", "npm", "pnpm", "yarn") if shutil.which(m)]
row("package manager", ", ".join(managers) or "NONE", "REQUIRED", "every per-call fetch")

print("-- on PATH --")
for name, level, who in (
    ("python3",       "REQUIRED",    "the literal name all 14 hook scripts / 15 registrations invoke"),
    ("git",           "REQUIRED",    "every command; the guardrails read the worktree"),
    ("node",          "REQUIRED",    "workflows, bin/, the Codex installer, 18+"),
    ("claude",        "REQUIRED",    "the harness; evaluator Mode 5 runs it headless"),
    ("gh",            "CONDITIONAL", "/pr-review, and /plan in issue mode"),
    ("agent-browser", "RECOMMENDED", "/debug frontend and the browser QA agent"),
    ("gitleaks",      "OPTIONAL",    "/perf security-baseline"),
    ("psql",          "OPTIONAL",    "database evidence in /debug auth-db"),
    ("codex",         "OPTIONAL",    "the Codex half and codex:codex-rescue"),
    ("cursor",        "OPTIONAL",    "the Cursor IDE half"),
    ("grok",          "OPTIONAL",    "the Grok CLI half"),
):
    exe = shutil.which(name)
    row(name, first(run(exe, "--version")) if exe else "MISSING", level, who)

print("-- a browser for agent-browser to drive --")
found = [b for b in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
                     "brave-browser", "microsoft-edge") if shutil.which(b)]
row("chrome family", ", ".join(found) or "none on PATH", "RECOMMENDED",
    "absent is fine: `agent-browser install` downloads one")

print("-- python --")
found_py = []
for name, extra in (("python3", []), ("python", []), ("py", ["-3"])):
    exe = shutil.which(name)
    if exe:
        found_py.append(f"{name} {first(run(exe, *extra, '--version'))}")
row("spellings present", "; ".join(found_py) or "NONE", "REQUIRED",
    "the hooks register the literal name `python3`")
floor = "ok" if sys.version_info >= (3, 10) else "TOO OLD"
row("running interpreter", f"{sys.version.split()[0]} ({floor})", "REQUIRED",
    "floor 3.10 — bin/graph-powers.mjs:536 enforces it")
try:
    __import__("code_review_graph")
    row("code_review_graph", "present", "OPTIONAL", "/plan structural search")
except ImportError:
    row("code_review_graph", "MISSING", "OPTIONAL", "/plan falls back to grep, never blocks")

print("-- plugins and skills --")
home = os.path.expanduser("~")
pf = os.path.join(home, ".claude/plugins/installed_plugins.json")
names = set(json.load(open(pf, encoding="utf-8")).get("plugins", {})) if os.path.isfile(pf) else set()
for want, level, who in (("graph-powers", "REQUIRED",    "this harness"),
                         ("codex",        "OPTIONAL",    "codex:codex-rescue escalation"),
                         ("code-review",  "OPTIONAL",    "one of /pr-review's four paths")):
    hit = [n for n in names if n.startswith(want + "@")]
    row(want, hit[0] if hit else "MISSING", level, who)
lp = os.path.join(home, ".claude", "skills", "landing-page-design")
row("landing-page-design", "SHADOWS the plugin copy — remove it (Step 1)" if os.path.lexists(lp)
    else "ok", "SHIPPED", "in the plugin since 1.10.0; a personal copy wins over it")

print("-- MCP servers, matched by the slug the tool names need --")
listing = run(shutil.which("claude") or "claude", "mcp", "list", timeout=120)
servers = [m.group(1) for m in (re.match(r"^(\S.*?): ", l) for l in listing.splitlines())
           if m and "Checking" not in m.group(0)]
slugs = {re.sub(r"[ .]", "_", s) for s in servers}
for want, level, who in (("tavily",              "REQUIRED",    "the librarian has no other way to search"),
                         ("claude_ai_Context7",  "RECOMMENDED", "live library docs; claude.ai connector"),
                         ("sequential-thinking", "OPTIONAL",    "long-chain reasoning")):
    row(want, "configured" if want in slugs else "MISSING", level, who)

print("-- the gates this project declared --")
cfg = ".graph-powers/config.json"
declared = {}
commands = {}
if os.path.isfile(cfg):
    declared = json.load(open(cfg, encoding="utf-8"))
    commands = declared.get("tooling", {}).get("commands", {})
if not declared:
    row("config", "no .graph-powers/config.json here", "INFO", "re-run from a project root")
audit = (declared.get("gates") or {}).get("preCommitAudit")
if isinstance(audit, str):
    audit = {"command": audit}
if isinstance(audit, dict) and str(audit.get("command", "")).strip():
    commands["preCommitAudit"] = audit["command"]
for key, value in commands.items():
    parts = [p for p in str(value).split() if not p.startswith("-")]
    tool = parts[0] if parts else ""
    if tool in ("bun", "npm", "pnpm", "yarn", "npx", "bunx") and len(parts) > 1:
        tool = parts[2] if len(parts) > 2 and parts[1] in ("run", "exec", "dlx") else parts[1]
    row(key, "ok" if (not tool or shutil.which(tool)) else f"MISSING `{tool}`",
        "REQUIRED" if key in ("typeCheck", "lint", "test") else "OPTIONAL", str(value)[:36])
PREFLIGHT
```

**Hard stop:** if the literal `python3` row is `MISSING`, or the running interpreter is below 3.10,
do not write any permissive client posture. `python` or `py -3` proving that Python exists is not
enough; make the same interpreter available under the name every hook command actually invokes,
then rerun the preflight.

The last block covers anything the project itself declared and this plugin then runs: the
`tooling.commands.*` gates, plus `gates.preCommitAudit`, which `hooks/commit_audit_gate.py` executes
before every commit. It is the same question `hooks/session_context.py` answers in the session tag
(`NOT INSTALLED: lint needs \`oxlint\``). It is repeated here because the tag only prints at session
start, and a setup run wants the answer while it is still installing things.

**Report back:** which plugins and binaries were already present, which you installed, the version
of each, and — naming them — anything you left `MISSING` on purpose.

---

## Step 2 — Read the repository before writing to it

Do not infer any of this. Read it.

| What | Where to get it |
|---|---|
| Stack | config files present (`astro.config.*`, `next.config.*`, `pyproject.toml`, `go.mod`, `Cargo.toml`, …) |
| Package manager | the **lockfile**, not habit or documentation |
| Gate commands | the `scripts` block, or the project's own task runner — only what genuinely exists |
| Work branch | `git branch --show-current`, plus how the project actually merges |
| Protected branches | the default branch, plus anything with branch protection |
| Where code lives | the actual tree, not a convention you expect |
| Test runner | present, or genuinely absent — both are real answers |

**A gate command that does not exist is worse than no gate.** It fails as "script not found", which
reads exactly like a real failure, and the line in the report reads as covered. Only put a command
in the config if you ran it.

---

## Step 3 — Write or improve the config

Target: `.graph-powers/config.json`. The contract is `$PLUGIN/schema/config.schema.json`; starting
points are in `$PLUGIN/examples/`.

### Two scopes, and which answer belongs in which

The same file shape is read from two places, resolved `defaults < user < project`:

| File | Answers | Read from it |
|---|---|---|
| `~/.graph-powers/config.json` | *How does this person work?* | `autonomy`, `graphGuardrails`, `protectedFiles`, `autoUpdate` |
| `<repo>/.graph-powers/config.json` | *What is this repository?* | everything in the schema |

The split exists because `autonomy` is the one block whose answer does not change between
repositories. Before the user scope existed it was reachable only from inside a repository that
carried it, so a person who had already decided "stop asking me to approve a read" met the same
prompt flood in the next clone — and the setting looked broken when it had simply never been asked.

Everything else stays project-only, `git` most deliberately: `optInPrefix` is per repository so that
an approval typed in one of them cannot release the same gate in another, and a home-directory
prefix would delete that isolation everywhere at once. A key outside the four above is ignored in
the user file rather than applied — a `paths.frontendRoot` written once at home is wrong in every
repository except the one it was meant for.

A project that declares its own `autonomy` block wins. Rules a repository ships apply to everyone
who clones it, including someone whose personal posture is looser.

**One thing to know before writing `level: "autonomous"` at user scope:** the level also implies
`git.commit: auto` and `git.push: auto`. That is defensible inside one repository whose owner chose
it; applied from a home directory it means every repository you open can commit and push without
you in the loop. If what you want is only for routine commands to stop prompting, pin git back:

```jsonc
// ~/.graph-powers/config.json
{
  "autonomy": {
    "machineWide": true,             // explicitly applies routine Bash autonomy to every repo
    "level": "autonomous",          // unrecognised commands and cleanup run
    "destructiveFloor": true,       // what git cannot undo is still refused
    "git": { "commit": "ask", "push": "ask", "protectedBranch": "ask" }
  }
}
```

Without `machineWide: true`, user scope may tighten policy but cannot loosen it for repositories
the operator has not reviewed. Even with it, `git: auto` and `destructiveFloor: false` are stripped
from user scope. Undo is deleting the file. Prove it is being read with the snippet at the end of
this step — from a repository that has no config of its own,
`gp.autonomy()['bashDefault']` should print `allow`.

### Routine Bash must not ask under `autonomous`

This is the step that stops
`Hook PreToolUse:Bash requires confirmation for this command. [plugin:graph-powers]`.
The hook `smart_bash_approver` returns `permissionDecision: ask` whenever
`autonomy.bashDefault` is `ask`. A project that wrote `"level": "autonomous"` and then
`"bashDefault": "ask"` (or `"cleanup": "ask"`, `"toolDefault": "ask"`) has defeated the
level: the per-field override wins, and every unclassified command — a Python heredoc, a
pipeline, a background `BashOutput` poll — becomes a Yes/No. Cursor loads the same plugin
hooks, so the same file is what stops the prompt there.

**Do this without pausing.** It is reversible (set the field back to `ask`) and it is the
installer default.

For client-level modes in items 4–6, installation is a hard precondition. If Step 0 did not prove
that client's plugin and hook manifest, defer its permission write until Step 9 installs and proves
them. Never loosen the client first and hope hooks appear later.

1. **Write the user file if it is missing.** `~/.graph-powers/config.json` is the operator's
   posture for every repository that does not declare its own `autonomy` block. The installer
   writes it; if you are running this playbook without the installer, write the block in the
   previous section. Never overwrite a file that already exists.
2. **When writing a new project config**, write the fields explicitly, matching the level.
   Do not leave them implied:

```json
"autonomy": {
  "level": "autonomous",
  "bashDefault": "allow",
  "cleanup": "allow",
  "toolDefault": "allow",
  "destructiveFloor": true
}
```

   Pin git back if the project wants commits and pushes to keep asking:

```json
"git": { "commit": "ask", "push": "ask", "protectedBranch": "ask" }
```

3. **When a project config already exists** at `.graph-powers/config.json` or
   `.claude/config.json`: if `autonomy.level` is `"autonomous"` and any of
   `bashDefault` / `cleanup` / `toolDefault` is `"ask"`, set that field to `"allow"`.
   Show the diff. Do not touch `git`, `destructiveFloor`, `allowPackageManagers`, or
   any other key. A `guarded` project is left alone. A file with no `autonomy` block is
   left alone — inventing one would loosen a repository that never asked.
4. **Claude Code permission mode — only after**
   `verify-hook-clients.py --client claude --scope <scope> --probe-guardrail` passes. Appenditively,
   in `~/.claude/settings.json` (user install) or the project's settings file (project/local install): if
   `permissions.defaultMode` is missing, `"auto"`, or `"default"`, set it to
   `"bypassPermissions"`, and set `"skipAutoPermissionPrompt": true` if it is not
   already true. The hook remains the gate — `deny` still blocks, the destructive
   floor still holds. Do not replace the `permissions.allow` array; append `"Bash"`
   if the level is autonomous and that entry is missing.
5. **Cursor IDE Run Mode — only after** `verify-hook-clients.py --client cursor --probe-guardrail`
   passes against the marketplace cache. `~/.cursor/cli-config.json` is `cursor-agent`. The confirmation flood lives in the IDE, which
   reads `~/.cursor/permissions.json`. Write, additively:
   `"approvalMode": "unrestricted"`, `"mcpAllowlist"` including `"*:*"`, `"terminalAllowlist"`
   including `"*"`. In `cli-config.json`, set `"approvalMode": "unrestricted"` and
   `"autoAcceptWebSearch": true`, and append `Shell(*)`, `Write(*)`, `Read(*)`, `WebFetch(*)`,
   `WebSearch`, `Mcp(*)` to `permissions.allow` if missing. Do **not** write a user
   `~/.cursor/hooks.json` that always allows — that fights the plugin guardrails. The installer
   does this on `--target cursor` / `--target all` / autodetect, but now refuses a real write when
   the Cursor plugin cache is absent. If you are running the playbook without it, enforce the same
   ordering yourself. If a team dashboard still forces Auto-review, the
   person has to set Settings → Agents → Approvals & Execution → **Run Everything**.
6. **Grok CLI approval — only after** `verify-hook-clients.py --client grok --probe-guardrail`
   passes against the exact `grok plugin list --json` path. Grok reads Claude-shaped plugins already;
   the confirmation flood lives in
   `config.toml` under `GROK_HOME` (falling back to `~/.grok`), which is user config only — a
   project `.grok/config.toml` cannot set
   `permission_mode`. Write, additively: `[ui] permission_mode = "always-approve"`,
   `[features] web_fetch = true`, `[subagents] enabled = true`, enable the `graph-powers` plugin.
   Do **not** write user `hooks/*.json` under the Grok home, and do not TOML-deny `git commit`.
   The installer does this on `--target grok` / `--target all` / autodetect. Under `guarded` it
   still wires plugin discovery and deliberately leaves approval posture unchanged.
7. **Prove it**, from the project directory, and show the output:

```bash
python3 -X utf8 "$PLUGIN/bin/verify-hook-clients.py" --client all --project-dir . --check-posture --probe-guardrail
```

The first line reports the effective config and `level`, `bashDefault`, `cleanup` and `toolDefault`.
Under `autonomous`, all three defaults must be `allow`; do not continue to Step 4 otherwise. Each
present client must then pass its exact package and posture: Claude `bypassPermissions`, both Cursor
IDE/CLI modes `unrestricted`, and the active `GROK_HOME` mode `always-approve`. The direct probe
invokes `git_commit_gate` with a synthetic command and requires a denial without creating a commit.
Commit/push opt-ins and the destructive floor remain separate gates.

To keep asking on every unclassified command, pass `--autonomy guarded` to the installer
or set `"level": "guarded"`. Do not express that as `autonomous` plus `bashDefault: ask`.

**Keep one local owner for the JavaScript/TypeScript toolchain.**

For JavaScript and TypeScript projects, the default editor/toolchain contract is:

| Concern | Owner | Scope |
|---|---|---|
| Editor types, autocomplete, navigation | `vtsls` | Zed only |
| JavaScript/TypeScript diagnostics | `oxlint` | Zed and final verification |
| JavaScript/TypeScript/JSON/CSS formatting | `oxfmt` | Zed format-on-save and PostToolUse |
| Type-aware final gate | local `oxlint` plus `typescript@7` | `/verify`, commit or CI only |

If the project does not already have the local packages, print the commands for the person to run:

```
bun add -d oxlint oxfmt typescript@7
```

The corresponding package scripts stay small and local:

```
{
  "scripts": {
    "format": "oxfmt --write",
    "lint": "oxlint --deny-warnings",
    "type-check": "oxlint --type-aware --type-check --threads 1"
  }
}
```

Adapt the script names to the repository only when they already have an equivalent local convention. Do not add a second JavaScript/TypeScript type provider, diagnostics provider, or formatter to compensate for a missing dependency. Do not use a network launcher from an editor command or hook.

Copy or adapt `${CLAUDE_PLUGIN_ROOT}/templates/zed/settings.json` into the project's `.zed/settings.json` when Zed is in scope. Confirm these invariants:

- JavaScript, TypeScript, and TSX use exactly `vtsls` and `oxlint` as language servers.
- Oxfmt is the only formatter and format-on-save is enabled.
- Zed uses vtsls's bundled compatible TypeScript SDK; `autoUseWorkspaceTsdk` is `false`.
- `node_modules/typescript/lib` is reserved for the TypeScript 7 gate and is not a vtsls SDK.
- dependency, build, cache, coverage, and generated directories stay in `file_scan_exclusions`.
- Prettier and any other competing formatter or language server are disabled for this surface.

The editor and final gate intentionally use separate compatible surfaces. Zed's vtsls adapter
currently expects `tsserver.js` when it uses a workspace SDK, while TypeScript 7 no longer ships
that entrypoint. Keep vtsls as the sole TypeScript provider with its bundled compatible SDK and
report `BLOCKED: vtsls + local TypeScript 7` until the adapter supports the TypeScript 7 SDK. Do not
add another TypeScript server.

Hooks have narrower ownership:

- `PostToolUse` runs one local Oxfmt `--write` process for the edited JS/TS/JSON/CSS file, with a short timeout, and fails open.
- `Stop` runs local Oxlint only on changed JS/TS paths; it never runs a full-tree lint and never runs type-aware analysis.
- Type-aware Oxlint is reserved for `/verify`, commit, and CI gates, with bounded concurrency (`--threads 1`).

The canonical policy is [the TypeScript 7 and Oxc gate](references/shared/130-typescript7-oxc-gates.md). The editor integrations are documented by the [Oxlint guide](https://oxc.rs/docs/guide/usage/linter), [Oxfmt guide](https://oxc.rs/docs/guide/usage/formatter.html), [Oxlint editor guide](https://oxc.rs/docs/guide/usage/linter/editors.html), [Oxfmt formatter guide](https://oxc.rs/docs/guide/usage/formatter/editors.html), [Zed TypeScript guide](https://zed.dev/docs/languages/typescript), and [Zed language configuration](https://zed.dev/docs/configuring-languages).

#### Someone hands you four figures of lint findings

Do not start fixing. Establish, in this order, how many of them are about this project at all:

```bash
# 1. What does the project actually declare? Run THAT first. It is frequently already clean.
python3 -c "import json;print(json.load(open('.graph-powers/config.json'))['tooling']['commands'])"

# 2. Where do the findings live? Directory, not rule — this is the question that resolves it.
#    `grep`/`sed`/`sort`/`uniq`/`head` are five coreutils cardinal 8 bans; Python does the same
#    counting and runs on cmd.exe and PowerShell too.
python -X utf8 -c "import collections,re,subprocess;o=subprocess.run(['oxlint'],capture_output=True,text=True,encoding='utf-8',errors='replace');c=collections.Counter(m.group(1).split('/')[0] for l in (o.stdout+o.stderr).splitlines() if (m:=re.match(r'^([^:\s]+):',l)));[print(f'{n:6} {d}') for d,n in c.most_common(10)]"

# 3. Only once 2 shows the project's own source, group by rule.
python -X utf8 -c "import collections,re,subprocess;o=subprocess.run(['oxlint'],capture_output=True,text=True,encoding='utf-8',errors='replace');c=collections.Counter(re.findall(r'(?:warning|error) ([a-z-]+\([a-z0-9-]+\))',o.stdout+o.stderr));[print(f'{n:6} {r}') for r,n in c.most_common()]"
```

Step 2 is the one that ends most of these. On the project measured above it returned 235 findings
under `.claude/` and 228 under `.claude.bak-*/` against 5 in the source — and the alarming ones,
`no-loss-of-precision` on colour-conversion constants and `no-misleading-character-class` on an emoji
range regex, were correct code inside a bundled third-party detector a skill had installed.

Then triage what survives, and expect to keep less than you fix:

| Finding | Verdict |
|---|---|
| Fires once or twice, names a real defect | Fix it |
| Fires many times, every hit deliberate | Turn the rule off **by name, with the reason in the config** |
| Fires in generated, vendored or bundled code | Widen `ignorePatterns` — never fix somebody else's build output |
| Argues with a platform requirement | Turn it off. A rule that contradicts the runtime is wrong here regardless of how sound it is elsewhere |

A rule disabled with a written reason is a decision the next person can reopen. A rule disabled
silently is a mystery, and a gate with 2,000 open findings is off in practice already — nobody reads
it, so nothing it catches gets seen.

**If a config already exists** (at `.graph-powers/config.json` or the legacy `.claude/config.json`):
merge field by field, show the diff, and keep every value the project already chose. Never
overwrite a config — someone tuned it, and they will not remember which field.

The one exception is the repair above: `level: autonomous` plus `bashDefault` / `cleanup` /
`toolDefault`: `ask` is not a tuned value, it is the level defeating itself. Apply that repair,
show the diff, leave everything else.

**If it does not exist**, write one from what Step 2 found:

```json
{
  "$schema": "https://raw.githubusercontent.com/GrupoUS/graph-powers/main/schema/config.schema.json",
  "project": { "name": "<slug>", "stack": "<detected>", "locale": "<project's language>" },
  "git": {
    "workBranch": "<where work happens>",
    "protectedBranches": ["<default branch>"],
    "optInPrefix": "<PROJECT>"
  },
  "tooling": {
    "packageManager": "<from the lockfile>",
    "testRunner": "<or null, deliberately>",
    "commands": { "typeCheck": "…", "lint": "…", "test": "…", "build": "…" }
  },
  "paths": { "frontendRoot": "…", "backendRoot": "…", "schemaRoot": "…" },
  "database": {
    "engine": "<reporting only — postgres, mysql, sqlite, …>",
    "commands": {
      "status": "<read-only: is the declared schema applied?>",
      "generate": "<writes the migration artefact; does not touch the database>",
      "apply": "<the irreversible edge — /verify never runs this>"
    },
    "applyPolicy": "never"
  }
}
```

Set `autonomy` deliberately and say what you set. Write the fields, do not leave them implied —
`bashDefault: ask` under `level: autonomous` is the confirmation flood, and the repair in
"Routine Bash must not ask under autonomous" exists because that combination shipped:

```json
"autonomy": {
  "level": "autonomous",
  "bashDefault": "allow",
  "cleanup": "allow",
  "toolDefault": "allow",
  "destructiveFloor": true
}
```

`autonomous` is what the installer writes: unrecognised commands run, cleanup runs, and commit and
push need no opt-in key. It exists because a harness that asks permission to run `git status`
teaches people to approve without reading. The floor still refuses what git cannot give back —
`rm -rf /`, `mkfs`, `dd` to a device, `DROP DATABASE`, force-pushing a protected branch — and
deleting a file inside a committed repository is deliberately not on that list.

**Tell the user which level the project ended up on, in one line.** Somebody discovering months
later that commits happen unattended, and not remembering agreeing to it, is the failure this
sentence prevents.

Three things to get right, because they are the ones that go wrong quietly:

- **Write the permission allowlist too.** `node "$PLUGIN/bin/graph-powers.mjs" --target all`
  adds it, additively — whatever the settings file already allowed stays. Without it the person
  approves the harness's own gate commands several times an hour. On Cursor that file is
  `~/.cursor/permissions.json`, not `cli-config.json`. On Grok that file is `~/.grok/config.toml`,
  not a user `hooks.json`.
- **`optInPrefix` must differ per project.** With the same prefix in two repositories, an approval
  given in one starts counting in the other. The versioned test covers exactly this case.
- **Omit a path the project does not have.** An empty `schemaRoot` tells the planner there is no
  data layer. A guessed one makes it plan a phase for a repository that does not exist.
- **`database` is the same kind of omission.** Fill it when the project has a `schemaRoot` and a
  live engine to check against. Omit the whole block when there is no database — a static site,
  this plugin, any repo whose schema never leaves the tree. Ask the operator for the three
  commands; do not guess an ORM. `applyPolicy` defaults to `never` if they do not choose.
  `drizzle-kit check` is not a status command: it never opens the database.
- **`testRunner: null` is an answer.** It says the absence is deliberate. Omitting the field says
  nobody looked.
- **JS/TS gates use local Oxc.** Read `references/shared/130-typescript7-oxc-gates.md`. Regular
  Oxlint diagnostics and Oxfmt formatting stay changed-file/editor scoped. The bounded command
  `oxlint --type-aware --type-check --threads 1` is reserved for `/verify`, commit or CI. Confirm
  the local packages first and never use a network fallback.

**Leave `autoUpdate` alone unless the project asks otherwise.** At session start, at most once every
twelve hours, a detached worker updates only the routes whose cache lifecycle it owns: Claude Code
and the Codex **clone** fallback. Native Codex, Cursor and Grok are never replaced by this worker;
update them in the foreground through their marketplace/client path, run the package verifier, and
restart every process that loaded the old cache. Nothing waits on the network and nothing inside the
project is touched. Do **not** add a second updater for a route already covered.

Write the group only to turn something off, and say why in the same breath:

```json
"autoUpdate": { "enabled": false }
```

Then **prove it is being read**, and show the output:

```bash
python3 -c "
import sys; sys.path.insert(0, '$PLUGIN/hooks')
import _config as gp
print('config file:', gp.config_path())
print('work branch:', gp.work_branch())
print('opt-in key :', gp.opt_in('COMMIT'))
"
```

If that prints `dev-test` and `GRAPHPOWERS_ALLOW_COMMIT` in a project that declared something else,
the config is not being read — a stray comma is enough. The guardrails are fail-open by design, so
this is the only place the mistake becomes visible.

---

## Step 4 — Improve `CLAUDE.md` and `AGENTS.md`, then grow the intent layer under them

These files already exist and carry decisions nobody remembers making. The goal is **not** to
replace them. It is to take out what now comes from the plugin, keep what only exists here, and
lose nothing on the way. Then, once the root pair is right, the subtrees that earn a node of their
own get one (4b).

### 4a — The root pair

Read the current file and `$PLUGIN/templates/CLAUDE.md`. Then classify every section:

| Class | What it looks like | What happens |
|---|---|---|
| **OUT** | Generic process: how to plan, how to debug, how to delegate, how to verify, context hygiene, agent routing | Comes from the plugin now. Remove — and say what you removed. |
| **STAYS** | Identity, invariants that exist because a violation cost something, path routing, decision authority, local pointers | Preserved verbatim. Not paraphrased. |
| **UNCLEAR** | Anything you cannot confidently place | **Ask.** Do not decide alone. |

Rewrite to the template's structure, aiming under 150 lines. Above that, adherence drops and what
survives is usually generic process the plugin already provides.

**Preserve every `[HARD]` invariant and every routing row exactly.** Those are what the project
loses if you get this wrong, and they are the only lines that cannot be reconstructed.

The project's design, product and review authorities are Step 6 — do not fold their
content into `CLAUDE.md`.

If both `CLAUDE.md` and `AGENTS.md` exist, check the split: `AGENTS.md` carries identity and
invariants, `CLAUDE.md` carries behaviour and pointers. Anything duplicated between them lives in
one.

For Codex, the installer maintains a delimited `<!-- graph-powers:start -->` block in `AGENTS.md`.
Do not hand-edit inside those markers — the next install rewrites it.

### 4b — The intent layer: child `AGENTS.md` nodes where the tree earns them

The root pair says what the project is. It cannot say what `packages/core` owns and `packages/api`
does not, and that is the question an agent asks on entering a subtree — so it re-derives the
answer from the files, differently each time. A child `AGENTS.md` in the subtrees that earn one is
the intent layer, and this harness already reads it: `/prime` loads `${paths.backendRoot}/AGENTS.md`
and the nearest node under `${paths.frontendRoot}`; `graph-powers:explorer`, `graph-powers:debugger`
and `graph-powers:frontend-specialist` load the nearest node before touching a subtree. In a
repository that never grew the layer, every one of those reads returns nothing.

Load `Skill("graph-powers:intent-layer")` and follow its procedure. In this playbook's terms:

```bash
# where the tree stands — root present, children linked, candidates due
python -X utf8 "$PLUGIN/skills/intent-layer/scripts/intent_layer.py" state .

# tokens per directory, has-node, verdict — paste the table before proposing anything
python -X utf8 "$PLUGIN/skills/intent-layer/scripts/intent_layer.py" measure . --depth 3
```

Then decide, and say why for each directory: a node where the table says `NODE` or `SPLIT`, where
a directory is a responsibility boundary — its own manifest, deploy or owner — and nowhere else.
Not one per directory, not in tests, not in a utilities folder small enough to read whole. Source
each node from the repository first: the manifest, the validators and guards, the directory's git
history, the last three commits that added the typical thing. Ask, one question at a time, only
what the repository cannot answer. **Never invent a contract.** A node states what the code
enforces or what a person said; a plausible invariant nobody stated is fiction that agents will then
defend.

Every child gets a downlink from the nearest ancestor node — in the root, a row in `Where things
live` — and stays under 4k tokens. The root, the child and every node between them are read
together by Codex, which stops at 32 KiB; the gate measures that chain, not each file alone.

```bash
# the gate — exit 0 or the step is not done; quote its output in Step 11
python -X utf8 "$PLUGIN/skills/intent-layer/scripts/intent_layer.py" check .
```

`--exclude <dir>` on any of the three hides a directory whose `AGENTS.md` is not a node — a template
still carrying `{{placeholders}}`, a vendored example. A `FAIL` is fixed or explained in the
report; it is never hidden with `--exclude`.

What the table flags and the decision refuses is written down twice, on purpose: the directory in
`intentLayer.deferred` of `.graph-powers/config.json` (Step 3's file; the block is in the schema),
and the reason in the nearest ancestor node's row, with the directory in backticks. `check` fails
a deferral the node does not name, and warns when a deferred directory later grows a node — a
decision nobody can read is a default, and a stale one is worse. Exclusions that hold for every run
go into `intentLayer.exclude` the same way, so the commands above need no `--exclude` at all.

A `CLAUDE.md` in a subdirectory is not a node: Codex, Cursor and Grok never read it. `check`
reports it as a warning. Move its content into that directory's `AGENTS.md`, and keep the
`CLAUDE.md` only when it carries Claude-specific behaviour worth a second file.

This sub-step writes only `AGENTS.md` files below the root and rows in the root's table. The rules
layer is Step 5 and the three authorities are Step 6; a contract that belongs in one of those does
not go into a node because the node was open.

---

## Step 5 — Create or improve the rules layer

`.claude/rules/` (and `.codex/rules/`) is where the project's own knowledge lives. Templates are in
`$PLUGIN/templates/rules/`: `README.md`, `stability.md`, `design.md`, `ux.md`, `execution.md`.

For **each rule the project already has**, classify:

- **GENERIC** — describes process that holds in any repository. That now comes from the plugin:
  propose replacing it with the matching template, adapted.
- **DOMAIN** — only makes sense here: data invariants, a specific integration, a convention, the
  thing that already broke once. Stays, intact.
- **DEAD** — describes something that no longer exists, has a `paths:` that never matches, or is
  never cited. Propose removal, saying what proved it dead.

**Before replacing any local rule with a template, run `diff` and show what the local version has
that the template does not.** A local rule almost always carries one line somebody wrote after an
incident. That line migrates to the new file. Losing it is the expensive failure of this whole step.

When adapting a template, substitute every `{{PLACEHOLDER}}` with a value read from the repository.
**A `{{}}` left in a final file is a defect.** If there is no real value for a placeholder, delete
the whole section rather than invent one.

Two properties to hold:

- Every rule needs `paths:` in its frontmatter, or it only loads when someone names it. That is a
  valid choice — but a deliberate one, not an accident. A rule with a `paths:` that never matches is
  invisible dead weight.
- Target 30–90 lines per rule. A long rule is not read, and it enters context every time its
  `paths:` matches.

Finish by updating `.claude/rules/README.md` with the real table: rule, `paths:`, authority.

---

## Step 6 — Create or improve the project's three authorities

The plugin ships **specifications**, not finished documents. Three files at the plugin root say what
the project's own counterparts must contain, how to source each section from the repository, and how
to improve one that already exists without destroying decisions:

| Spec | Produces, in the project | Answers |
|---|---|---|
| `$PLUGIN/DESIGN.md` | `DESIGN.md` | When two visual decisions conflict, which one wins? |
| `$PLUGIN/PRODUCT.md` | `PRODUCT.md` | When a change is technically fine but the product is worse, what catches it? |
| `$PLUGIN/REVIEW.md` | `REVIEW.md` | What does this project refuse to merge? |

**Read the spec before writing the file.** Each one carries its required sections, its sourcing
rules, and a quality bar the result has to pass. They are not templates to fill in — the point is
that every value traces back to the repository or to an answer from the user.

For each of the three, in this order:

1. **Find the existing authority, under any name.** A design source might be `docs/design-system.md`
   or a token file; a product brief might be a README section; a review contract might be
   `CONTRIBUTING.md` or a PR template. **If one exists, improve it in place.** Two authorities on
   the same subject is worse than none, because now "which one wins" has to be answered about the
   files themselves.
2. **Preserve every existing decision verbatim.** Each is the residue of something that already
   happened, and the reason is frequently unwritten. Rewording loses the reason.
3. **Source the missing sections per the spec.** Read the repository first, mine the git history for
   `REVIEW.md`'s blocking list, and ask — one question at a time — about anything only a person
   knows. `PRODUCT.md` is mostly the third kind; expect to ask.
4. **Mark gaps as gaps.** `Not decided — <what would settle it>` is a working document. A section
   filled with plausible defaults is a fiction that agents will then enforce as fact.
5. **Report drift rather than fixing it.** When an existing file and the repository disagree — a
   brief describing a flow the code no longer has, a review rule citing a script that is gone —
   surface it and ask. Which one is stale is the user's call, and it is usually the interesting part.
6. **Show the diff, then write.**

Finally, make the rules layer point at these files instead of restating them.
`templates/rules/design.md` references `DESIGN.md`; `templates/rules/ux.md` references `PRODUCT.md`'s
honesty gate. If a rule ends up repeating a decision from one of the three, the copies will diverge.

---

## Step 7 — Clean what shadows the plugin

**This is the step that decides whether the installation changed anything.**

List what the project has locally against what the plugin provides:

```bash
python3 - <<'SHADOW'
import os
plugin = os.environ.get("PLUGIN", "")
for kind in ("agents", "skills", "commands"):
    local = sorted(os.listdir(f".claude/{kind}")) if os.path.isdir(f".claude/{kind}") else []
    theirs = sorted(os.listdir(os.path.join(plugin, kind))) if plugin else []
    print(f"\n{kind}")
    print("  local :", local or "none")
    print("  plugin:", theirs or "none")
    print("  BOTH  :", sorted(set(local) & set(theirs)) or "no shadowing")
SHADOW
```

For every local artefact whose name matches a plugin one, `diff` them and classify:

- **Identical or older** → propose removing the local copy. The plugin's version takes over, and it
  is the one that receives fixes.
- **Local has something extra** → **do not remove it.** Show the extra part. It is a candidate to
  come *up* into the plugin, or to stay as a deliberate local override.
- **Local only** → stays. It is the project's own, and possibly its only copy.

**Stop for approval before deleting anything.** Then show, for each removal, the diff that justified
it.

The hard case is not the file that differs. It is the file that looks identical but gained three
lines months ago that nobody remembers writing. That is why this is a procedure with a human in it
and not a script.

---

## Step 8 — Audit `settings.json`

```bash
node "$PLUGIN/bin/audit-settings.mjs"
```

It compares the project's `.claude/settings.json` against the plugin's hook declarations and sorts
them into duplicated, overlapping and exclusive. It writes nothing.

- **DUPLICATED** — same event, same matcher, same file. `diff` them; propose removing the local one
  only when the plugin's does everything it does.
- **OVERLAPPING** — same file, different matcher. If the plugin's matcher covers the project's, the
  local one is redundant; if it covers less, removing it loses coverage. Read before deciding.
- **Everything else** — `permissions`, `env`, `statusLine`, `enabledPlugins` and any other key
  belong to the project. **Do not replace them.** If the audit suggests permissions, *append* to the
  existing array; never replace the list. Under `autonomous`, also append `"Bash"` if it is
  missing, and if `permissions.defaultMode` is missing / `"auto"` / `"default"`, set it to
  `"bypassPermissions"` and set `"skipAutoPermissionPrompt": true`. That is the same repair
  the installer writes; without it a PreToolUse hook returning `ask` still prompts in `auto`
  mode. Do not change a `defaultMode` the operator already set to something else.

Validate afterwards: `python3 -c "import json;json.load(open('.claude/settings.json'))"`.

Hooks accumulate across levels rather than overriding — a project hook and an equivalent plugin hook
both run. Nothing breaks immediately, which is why it goes unnoticed.

### The one setting this plugin cannot ship for you

Claude Code loads a listing of every skill and command name plus description into context at session
start, and that listing is the only thing a plain sentence is matched against when the model decides
on its own to reach for `/debug`. Its budget is about **1% of the context window**, shared across
every source on the machine — this plugin, every other plugin, your own skills, the bundled ones. On
overflow nothing fails and nothing warns: Claude Code drops descriptions, starting with whatever you
invoke least, and those entries go on being listed while they stop being reachable.

A plugin cannot raise that budget. Only the `agent` and `subagentStatusLine` keys are honoured from a
plugin's own `settings.json`, so this is yours to set:

```jsonc
// ~/.claude/settings.json
{
  "skillListingBudgetFraction": 0.02    // 2% instead of the default 1%
}
```

Check first, and only spend the budget if you are actually over it:

```bash
# /doctor reports the listing's cost and its biggest contributors.
# /context shows the Skills row after the budget is applied — what the model really got.
# claude --debug writes an overflow warning to the debug log.
```

Two cheaper moves before raising the number, because a bigger listing is context spent every turn:

- `"skillOverrides": { "<name>": "name-only" }` lists a skill without its description — right for
  something you invoke by slash and never want auto-selected.
- `"skillOverrides": { "<name>": "off" }` removes it entirely. A skill unused across a hundred
  sessions is the cheapest thing on the list to cut.

This plugin holds up its own end: `python3 .github/check_listing_budget.py` fails CI if its
contribution grows past what it measured, so what it costs you does not drift upward between
releases.

---

## Step 9 — Wire and prove every agent client the project uses

Read this before running an installer or loosening a permission mode. Getting the order wrong does
not merely degrade the harness: it can leave a client unrestricted without guardrails, or take the
client down with a stale command. Claude is proved first; Codex owns 9a–9f; Cursor, Grok and Zed
follow with their separate capability boundaries.

### Claude Code — install and prove before bypass posture

`claude plugin list` must show one enabled user-scope `graph-powers@graph-powers`; project-scope
copies are separate registrations, not backups. Install/update with the qualified ID first:

```bash
claude plugin update graph-powers@graph-powers
```

Then prove the exact user `installPath` rather than a neighbouring cache directory:

```bash
python3 -X utf8 "$PLUGIN/bin/verify-hook-clients.py" --client claude --scope user --project-dir . --probe-guardrail
```

It must report the canonical `hooks/hooks.json`, fourteen scripts/fifteen registrations and guarded
runners. Only then apply Step 3's posture, run `node "$PLUGIN/bin/audit-settings.mjs"` before removing
any accumulated project hook, and restart Claude Code — the update command itself states that a
restart is required.

Do not set `bypassPermissions` first. The plugin package, literal `python3`, direct hook regression
and settings-duplication audit must pass before Step 3's Claude posture is applied. A process already
open during an update is not certified by a new `claude -p` process; restart the affected process.

### Codex CLI — native or clone, never both

Five states are separate and each has its own proof:

| State | Proof | If absent |
|---|---|---|
| Plugin installed and enabled | `codex plugin list --json` contains enabled `graph-powers@graph-powers` | install with 9c |
| Method skills packaged | Step 10 § 7b reports both skill files present in the listed plugin source | update or reinstall the plugin; never copy one skill separately |
| Hooks discovered | `/hooks` lists fifteen registrations sourced from `graph-powers@graph-powers` | restart once; then verify the package contains `hooks/hooks.json` |
| Hooks approved | `/hooks` shows those entries enabled/trusted | approve them explicitly; installation never grants trust |
| Hooks executing | `codex exec --skip-git-repo-check "reply with: ok"` reports `Completed` | use the diagnostic matrix in 9e |

**Codex reads a hook's exit code as a decision, not as a status.** `0` succeeds. `2` denies, with
whatever the hook wrote to stderr as the reason: the prompt on `UserPromptSubmit`, the tool call on
`PreToolUse`, the result on `PostToolUse`. Any other code is an error Codex reports and steps over.

Which is why ownership of a wrong path matters. A clone registration in `~/.codex/hooks.json`
persists into every fresh process until repaired. A native plugin command, however, can be retained
only by an already-open task while a marketplace update replaces its versioned cache; a fresh
process may load the new cache and pass while the old task keeps calling a deleted path. Both can
exit **2** and look like policy. Never use a fresh process to declare the already-open task healthy.

### 9a — Set the Codex permission posture once

For maximum routine autonomy without removing the sandbox, put these top-level keys before the
first TOML table in `~/.codex/config.toml`, and merge the network key into its existing table:

```toml
approval_policy = "on-request"
approvals_reviewer = "auto_review"
sandbox_mode = "workspace-write"

[sandbox_workspace_write]
network_access = true
```

This makes workspace reads, edits, tests and ordinary network-backed tooling run directly. A call
that still needs to cross the workspace boundary is sent to Codex's reviewer agent instead of
stopping for a person. Do not use `approval_policy = "never"` for this purpose: it removes the
prompt by rejecting escalations, so work fails instead of becoming autonomous. Do not use
`danger-full-access` as a convenience setting; it removes the sandbox that makes automatic review
meaningful.

Graph Powers adds the second half: its `PermissionRequest` registration automatically approves a
Bash escalation only when `smart_bash_approver` already classified the command as allowed, and
declines to decide when guarded policy says to ask. Destructive-floor denials still win. Restart
Codex after changing `config.toml`, then confirm the effective sandbox and reviewer with
`codex doctor`.

### 9b — Prove the Codex home is sane, before you install anything

Native plugin hooks do not need to be copied into `~/.codex/hooks.json`. That file remains relevant
because other tools and older Graph Powers clone installs write it. The clone installer **merges
rather than overwrites** — deliberately, so it never destroys another tool's work. A broken legacy
entry survives a native install and gets blamed on it. Find it first, and report every line this
prints:

```bash
python3 -X utf8 "$PLUGIN/bin/verify-hook-clients.py" --client codex-home --project-dir .
```

The versioned checker parses the active `CODEX_HOME`, chooses `command` or `commandWindows` for this
platform, resolves literal interpreters and paths, distinguishes a pre-`1.11.1` missing entrypoint
from a guarded runner whose target is merely inert, inspects `notify`/duplicate hook declarations,
and reports file-sync conflict copies. It writes nothing.

| Severity | What it found | What you do about it |
|---|---|---|
| `BLOCKS` | the active command names a missing interpreter, a wrong-platform path, or a missing entrypoint without the guarded runner | fix it before installing. On Codex this can be read as a deny and blamed on whatever was installed last |
| `RISK` | a guarded runner's target is absent (session usable but guardrail inert); the synced-platform command is wrong; `notify` is absent; or hooks are declared twice | restart/repair before claiming coverage, and say which guardrail was inert |
| `NOTE` | an absolute hook has no `commandWindows`, or a file-sync tool left conflict copies | report it. Neither necessarily breaks this machine; both are how the next break arrives |

**Do not install over a `BLOCKS` line, and do not delete the entry that produced it** — it belongs
to another tool and the user may want it. Repair it, which is almost always one of two edits:

- the script exists here under a different root — point `command` at the local absolute path and
  move the foreign one into `commandWindows`, which is the field Codex provides for exactly this;
- the script does not exist here at all — set `enabled = false` for that entry under
  `[hooks.state]` in `~/.codex/config.toml`, and tell the user which tool it came from.

### 9c — Choose one installation route, and migrate before combining them

**Preferred — native Codex plugin:**

```bash
codex plugin marketplace add GrupoUS/graph-powers
codex plugin add graph-powers@graph-powers
```

Then restart Codex and approve the fifteen registrations in `/hooks`. The native loader discovers
`hooks/hooks.json` inside the plugin cache and resolves `${CLAUDE_PLUGIN_ROOT}` itself; no generated
copy in `~/.codex/hooks.json` is involved.

The current upstream Codex plugin manifest has no `agents` resource, so marketplace installation
alone cannot register custom roles. Do not retain an ignored `"agents"` field or claim that the
cache is a config layer. Emit the native companion TOMLs explicitly instead:

```bash
node "$PLUGIN/codex/native-plugin.mjs" --out <codex-home>/agents
```

This writes roles only and does not create a second hooks/skills installation route. Each companion
TOML carries explicit `model` and `model_reasoning_effort` resolved from
`codex/model-policy.json`, and the clone TOML route calls the same resolver. Run both repository
checks before installing a changed package:

```bash
bun "$PLUGIN/.github/check_codex_policy.mjs"
python3 -X utf8 "$PLUGIN/.github/check_codex_native.py"
```

The default split is Sol Max for judges/architects, Terra High for executors/verifier and Luna Medium
for scouts. A Claude family in either output, session inheritance for a canonical agent, or a
native-companion/clone mismatch is a failure. `codex.profiles.*`, `codex.agents.*` and the legacy
`codex.model`, `codex.models.*`, `codex.reasoningEffort` fields are clone-generation overrides;
`node "$PLUGIN/codex/native-plugin.mjs" --config .graph-powers/config.json --out <codex-home>/agents`
renders the same overrides for the operator-managed native companion directory.

The tracked `codex/native-agents/*.toml` files are portable snapshots, not runtime-ready config:
the `--out` step resolves `${CLAUDE_PLUGIN_ROOT}` to `$PLUGIN` and its `skills/` and `references/`
subtrees. The generated runtime directory must contain no `CLAUDE_PLUGIN_ROOT` token.

Do not claim per-role permission parity that Codex does not implement. In Codex 0.150.1 the role
layer applies model/reasoning settings but preserves the parent sandbox and exposes no per-role
spawn deny. The generator deliberately omits ignored `sandbox_mode` keys and inserts an explicit
limitation notice for source agents that deny Write. For a hard read-only audit, launch the entire
parent session with `codex --sandbox read-only`; mixed writer/reviewer workflows have advisory
read-only and leaf boundaries until upstream exposes those controls. Claude Code continues to
enforce its own `disallowedTools` declarations.

Ultra is not a subagent reasoning tier. `native-ultra` is reserved for an explicit top-level Codex
session when Graph Powers is not simultaneously running its own deterministic `/pr-review`,
`ultra-plan` or `ultra-verify` fan-out. Never put an evaluator on Ultra: its model fallback is Sol
Max, while its leaf boundary remains an orchestrator instruction under the current role API. Emit
the separate Codex v2 profile with
`node "$PLUGIN/codex/native-plugin.mjs" --top-level-profile native-ultra --out <codex-home>`, then
select it with `codex --profile native-ultra`. This does not alter any generated subagent role.

**Fallback — clone installer:** use this only when the marketplace is unavailable or a
project-scoped copy is required.

```bash
node "$PLUGIN/bin/graph-powers.mjs" --target codex          # global half + project half
```

That same script takes `--update`: it fast-forwards the clone and reinstalls from it. Native Codex
uses `codex plugin marketplace upgrade graph-powers`; compare the version in
`codex plugin list --json`, re-emit `<codex-home>/agents` from the upgraded cache, and restart every
CLI/Desktop process that had already loaded the old definition. Do not run the clone updater against
a marketplace cache.

It does the two halves in order, and **skips the global half when it is already there at this
version** — so running it in a tenth project costs two files, not thirty.

**Global** (written once for the machine, reused by every project): `~/.codex/hooks.json` merged
with whatever is already there, `~/.agents/skills/`, `~/.codex/agents/*.toml`,
`~/.codex/graph-powers/`, and the block in `~/.codex/AGENTS.md`. Everything it added is recorded in
`~/.codex/graph-powers-installed.json`, so removal is exact.

**Project**: `.codex/rules/` and the delimited block in this repository's `AGENTS.md`. That block
points at `~/.codex/graph-powers/` — a path that is identical on every machine, so the file stays
portable when it is committed.

Then run 9b again. It should say the same thing it said before, plus the entries this plugin added.
A new `BLOCKS` line means the install found something the preflight did not, and the fix is the
same: repair the entry, do not delete it.

**Migration from a clone install to the native plugin.** If `codex plugin list --json` reports the
native plugin and `~/.codex/graph-powers-installed.json` also exists, stop before the write and show
the manifest's `pluginRoot` and `hookCommands`. After approval, run the current plugin's manifest-backed
uninstaller (it reads that record; it does not depend on the old root still existing):

```bash
node "$PLUGIN/bin/graph-powers.mjs" --uninstall
```

The manifest makes this subtraction exact: Graph Powers entries are removed from the shared hooks
file, third-party hooks remain, and adapted rule templates are retained. Re-run the project steps
afterwards to restore the local instruction block for the native route, then restart and approve
the native hooks. Never delete `~/.codex/hooks.json` as a migration shortcut.

### 9d — Why a hook that works here can be dead on the machine this home syncs to

`~/.codex` is a directory people sync. Dropbox, pCloud, OneDrive, Syncthing and Resilio all get
pointed at it, because it holds the agent setup somebody spent a weekend on. What they also do is
carry one machine's absolute paths onto another, and Codex has no way to tell an imported path from
an intended one — it runs it, the interpreter exits 2, and the session denies everything.

Two things keep that from happening, and both belong in the report you leave:

**Hooks are written for both platforms in one file.** `command` is what Codex runs on Linux and
macOS; `commandWindows` is what it runs on Windows, and it wins there when it is present. A hook
carrying both is safe to sync. A hook carrying only `command` with an absolute path is a hook that
does nothing on the other machine — silently, which is worse than failing.

**Some files must never be synced at all**, because they describe the machine rather than the
setup. Say these by name:

| Never sync | Why |
|---|---|
| `config.toml` | absolute paths, `notify`, marketplace roots, and the per-hook trust hashes |
| `auth.json` | credentials, in the clear |
| `models_cache.json` | written by one CLI version; a mismatched one fails to load at every start |
| `.codex-global-state.json` · `sessions/` · `rollouts/` | this machine's history, and the bulk of the directory |

The tell that this has already happened is conflict copies — `config [conflicted].toml`,
`hooks.sync-conflict-….json` — which is why 9b counts them. They are inert; what they prove is that
two machines are writing the same file, and that the next import will land the same way.

### 9e — Diagnose the state, then tell the user three things

| Symptom | Meaning | Action |
|---|---|---|
| Plugin absent from `codex plugin list --json` | not installed | run the native install commands in 9c |
| Installed but `enabled: false` | installed, disabled | enable/reinstall it before inspecting hooks |
| Enabled but no Graph Powers rows in `/hooks` | package not discovered or session predates install | restart; then verify `hooks/hooks.json` exists in the listed plugin path |
| Listed in `/hooks` but absent from `codex exec` output | unapproved | approve in `/hooks` |
| Error names a missing versioned native cache while `plugin list` reports a newer version | this task retained its old command in memory | close/reopen the affected task or fully restart that client; do not inspect only `~/.codex/hooks.json` |
| `Failed` | hook errored and Codex stepped over it | inspect the named command, interpreter and path with 9b |
| `Blocked` | hook deliberately denied the event, or a wrong path exited 2 | read stderr and first classify native-cache vs clone ownership |
| Each Graph Powers hook appears twice | native and clone routes coexist | perform the manifest-backed migration in 9c |

1. **Open `/hooks` in Codex and approve the hooks.** Codex tracks trust by the hash of each hook
   definition, so a change to the file needs approval again, and until it is given **those
   guardrails do not run** — say that plainly rather than letting them assume they are covered. The
   installer will not rewrite an unchanged `hooks.json` for exactly this reason, so a routine update
   costs no re-approval; a genuine change to the guardrails does, and it should.
2. **How to tell whether they are actually running.** `codex doctor` reports the installation,
   config, auth and sandbox in one pass and is the fastest evidence that nothing else is broken.
   For the hooks themselves, one non-interactive turn prints a line per hook:

   ```bash
   codex exec --skip-git-repo-check "responda apenas: ok"
   ```

   `Completed` is a hook that ran. `Failed` is a hook that errored and was stepped over. `Blocked`
   is a hook that denied — and if a prompt never reaches the model, that is what to look for.
3. **What to gitignore.** Far less than before, because the harness is global now:

   ```gitignore
   .graph-powers/logs/
   AGENT_STOP
   ```

   `.codex/rules/` and the `AGENTS.md` block are the project's own and **should** be committed.

### 9f — If Codex is already refusing every prompt

Recover in this order. Do not reinstall first, create a partial old cache, or conclude an old task
is healthy because a new process works.

1. **Classify the path in the error.** If it contains a versioned native plugin cache, compare that
   version/path with enabled `graph-powers@graph-powers` from `codex plugin list --json`.
   - old path missing, newer plugin present: close and reopen the affected task. For Desktop, quit
     the app completely so its bundled app-server exits, then reopen it;
   - the task loaded Graph Powers before `1.11.1`: the direct Python command can block on `ENOENT`;
   - the task loaded `1.11.1` or newer: the wrapper fails open, so the task stays usable but every
     missing Graph Powers hook is **inert** until restart. Report it as unguarded, not healthy.
2. **Only for a non-stale process, read unapproved hooks without trusting them permanently:**

   ```bash
   codex exec --dangerously-bypass-hook-trust --skip-git-repo-check "responda apenas: ok"
   ```

   All `Completed` and a normal answer means that **new process** has executable hooks and only trust
   is pending. It says nothing about a task that was already open.
3. **Run 9b for clone/user registrations.** A broken entry in `~/.codex/hooks.json` persists across
   fresh processes; repair that entry or disable it by its owner. Native cache commands do not live
   there.
4. **If `hooks.json` itself does not parse**, Codex loads no hooks at all rather than some — move it
   aside, confirm the CLI answers, then repair it from the copy.
5. **If the CLI fails before the first turn** with `failed to load models cache`, the cache was
   written by a different version. It is a cache: move `~/.codex/models_cache.json` aside and let
   Codex refetch it.

### Codex Desktop — same native route only when proved

Codex Desktop is not another Graph Powers installer target. Some builds launch a bundled Codex
`app-server` against the same Codex home as the CLI; others are not proven by this repository. A CLI
`plugin list` or `codex exec` pass therefore does not, by itself, certify an already-open Desktop
process.

1. Confirm the Desktop process is backed by Codex `app-server` and the same Codex home. If the
   product exposes no evidence, report `Codex Desktop: UNVERIFIED` rather than borrowing the CLI row.
2. After any plugin/cache update, fully quit Desktop and confirm the old app-server process exited;
   then open a new task in the repository.
3. Verify plugin version, fifteen hook registrations/trust, and one harmless completed turn from
   the Desktop task. If Desktop does not expose hook telemetry, say which half could not be proved.

### 9g — Wire Cursor, if the project uses it

Cursor marketplace installs `.cursor-plugin/` from this repository. That is the plugin, including
the generated `hooks/hooks-cursor.json`. It is **not** the confirmation flood. The IDE Agent Run
Mode is `~/.cursor/permissions.json`. `~/.cursor/cli-config.json` only covers `cursor-agent`.

Four states, each with its own proof:

| State | Proof | If absent |
|---|---|---|
| Plugin in the Cursor cache | an installed cache entry contains `.cursor-plugin/plugin.json` for `graph-powers` | add the marketplace with `cursor-agent plugin marketplace add https://github.com/GrupoUS/graph-powers`, then install Graph Powers in Cursor; `--target cursor` does not install it |
| Installed native hooks pointed at the generated file | that cached manifest points at `./hooks/hooks-cursor.json`, and the file has twelve registrations | update/reinstall the Cursor plugin; regenerate the repository source only when developing this plugin |
| IDE Run Mode unrestricted | `~/.cursor/permissions.json` `"approvalMode"` is `"unrestricted"` | only after the two rows above pass, run `node "$PLUGIN/bin/graph-powers.mjs" --target cursor`, then reload the window |
| Team dashboard not overriding | Settings → Agents → Approvals & Execution shows **Run Everything** | the person has to click it; a file cannot beat a dashboard policy |

Do not write a user `~/.cursor/hooks.json` that always allows. The plugin hooks are the
guardrails; unrestricted Run Mode is what stops the Yes/No on classified commands. Git commit
and push still ask. `rm -rf /` still denies. PermissionRequest and Notification do not exist on
Cursor — `tool_approver` and `notify` are skipped on purpose, and `smart_bash_approver` still
runs at `preToolUse`.

Cursor watches hook files, but a marketplace update may also replace its cache root. Before writing
Run Mode, run:

```bash
python3 -X utf8 "$PLUGIN/bin/verify-hook-clients.py" --client cursor --project-dir . --probe-guardrail
```

The command inspects every dedicated cache directory and fails on a corrupt candidate or an
ambiguous highest version; neither mtime nor "some valid cache" is accepted. Reload the Cursor
window after an update; a new Agent chat alone proves Run Mode, not that the old process released
its prior plugin path.

### 9h — Wire Grok CLI, if the project uses it

Grok marketplace installs `.grok-plugin/` from this repository and reads `hooks/hooks.json`
directly. That is the plugin, including Claude-shaped hooks. It is **not** the confirmation flood.
Always-approve lives in `config.toml` under `GROK_HOME`, falling back to `~/.grok`. A project
`.grok/config.toml` cannot set `permission_mode`.

Four states, each with its own proof:

| State | Proof | If absent |
|---|---|---|
| Plugin discovered | `grok plugin list --json` reports installed `graph-powers`, and `grok inspect --json` sees it for this directory | `grok plugin marketplace add GrupoUS/graph-powers` then `grok plugin install graph-powers --trust`, or one clone path through `--target grok` |
| Hooks pointed at `hooks.json` | the installed `.grok-plugin/plugin.json` points at `./hooks/hooks.json`, never a second list | update/reinstall the plugin; regenerate the repository source only when developing it |
| User approval always-approve | active Grok-home `config.toml` `[ui] permission_mode` is `"always-approve"` | run `node "$PLUGIN/bin/graph-powers.mjs" --target grok`, then restart Grok |
| Claude compat still on | do not set `[compat.claude] hooks = false` | that would drop the plugin hooks this harness ships |

Do not write user `hooks/*.json` under the Grok home. Do not TOML-deny `git commit`. The plugin
hooks are the guardrails; `always-approve` is what stops the Yes/No on classified commands. Git
commit and push still ask. `rm -rf /` still denies. Grok has Notification; keep it in
`hooks/hooks.json`. Under `guarded`, clone discovery is still written while approval posture stays
unchanged.

Before writing `always-approve`, prove the exact `path` returned by Grok and the active Grok home:

```bash
python3 -X utf8 "$PLUGIN/bin/verify-hook-clients.py" --client grok --project-dir . --probe-guardrail
```

Grok updates are foreground-only: the `SessionStart` worker never replaces this client-owned cache.
After installation or update, run the verifier, then restart Grok. An already-open session keeps its
loaded plugin commands and permission mode.

### 9i — Hermes Agent: native skills, Graph Powers hooks do not

Hermes installs the root `plugin.yaml` and imports `__init__.py`. That entrypoint derives one
registration set from the checkout: every `hermes/skills/*/SKILL.md`, every
`skills/*/SKILL.md`, every `commands/*.md`, and every `agents/*.md` under the names
`graph-powers:<name>` and `graph-powers:agent-<slug>`. There is no second inventory to keep in sync.

Install and prove the package with Hermes itself:

```bash
hermes plugins install GrupoUS/graph-powers --enable
hermes plugins show graph-powers
hermes plugins doctor <clone> --ci
```

In a fresh session, `skill_view("graph-powers:planning")`,
`skill_view("graph-powers:agent-explorer")`, and `skill_view("graph-powers:plan")` must resolve
the installed checkout package. Hermes does not execute Claude `hooks/hooks.json`, so report
`Graph Powers hooks: NOT ENFORCED` and rely on the parent agent's approvals for git and destructive
actions. Do not create a personal Hermes copy or adapter; the native package is the supported route.

Before calling the package healthy, run the repository-side static and runtime probe:

```bash
python3 -X utf8 "$PLUGIN/bin/verify-hook-clients.py" --client hermes --project-dir .
```

The probe reports `SKIPPED` only when the Hermes executable is absent; static manifest and
registration failures remain failures.

If the install command is blocked before this probe by Hermes' community-plugin scanner, inspect
the reported findings. This repository intentionally documents destructive and credential
guardrails, and the native package does not bypass a dangerous scanner verdict; use only an
organization-approved scanner policy for a reviewed source.

### 9j — Zed: instructions work, Graph Powers hooks do not

This repository has no Zed plugin manifest, installer target or lifecycle/tool-hook declaration.
Zed can consume `AGENTS.md`, project rules, globally installed skills, MCP/ACP integrations and the
editor/LSP settings from Step 3. None of those intercepts a native Zed tool call. Do not write a
fictional Zed hook file and do not describe Zed as protected by the commit/push/destructive rails.

If the user works through Zed's native agent, report `Graph Powers hooks: NOT ENFORCED (Zed has no
implemented hook surface in this repository)`. If Zed launches Claude Code, Codex CLI, Cursor Agent
or Grok as an external agent, verify that external process under its own row; its hooks do not become
Zed-native hooks.

## Step 10 — Verify, with output

Not one of these is optional, and each needs its output shown:

```bash
# 0. the literal interpreter every hook command invokes exists and meets the floor
python3 -c "import sys;print(sys.version);raise SystemExit(sys.version_info < (3,10))"

# 1. no placeholder survived
python3 - <<'PLACEHOLDERS'
import os
hits = []
for root in (".claude", ".codex"):
    for base, _, names in os.walk(root):
        hits += [os.path.join(base, n) for n in names]
hits += [f for f in ("CLAUDE.md", "AGENTS.md") if os.path.exists(f)]
found = False
for path in hits:
    try:
        for i, line in enumerate(open(path, encoding="utf-8", errors="replace"), 1):
            if "{{" in line:
                print(f"{path}:{i}: {line.strip()}")
                found = True
    except OSError:
        pass
print("" if found else "no pending placeholders")
PLACEHOLDERS

# 1b. the intent layer holds — every child AGENTS.md linked, resolving, under its cap, and the
#     root-to-leaf chain under the 32 KiB Codex reads. The check above only scans the root pair.
python -X utf8 "$PLUGIN/skills/intent-layer/scripts/intent_layer.py" check .   # expected: exit 0, last line `intent layer: OK`

# 2. the guardrails hold, and one project's key does not work in another
python3 "$PLUGIN/hooks/test_hooks.py"        # expected: exit 0

# 3. the config is the one being read (repeat of Step 3, after everything changed)
python3 -c "
import sys; sys.path.insert(0, '$PLUGIN/hooks')
import _config as gp
print(gp.config_path(), gp.work_branch(), gp.opt_in('COMMIT'))
"

# 4. every declared gate actually runs
#    run each command from tooling.commands and report its exit code.
#    The usual failure is not a broken gate but an absent tool — `oxlint`, `oxfmt`, `eslint`,
#    `ruff` — declared and never installed. This prints the same verdict the session tag will:
python3 -c "
import sys; sys.path.insert(0, '$PLUGIN/hooks')
import _config as gp
cmds = (gp.load().get('tooling') or {}).get('commands') or {}
for key, command in cmds.items():
    missing = gp.missing_tool(str(command))
    print(f'{key:12} {command!r:38} ' + (f'MISSING: {missing}' if missing else 'ok'))
"    

# 5. commit logic is exercised by verify-hook-clients.py --probe-guardrail below. It invokes the
#    installed package's git_commit_gate against a temporary guarded config; no real commit is made.

# 6. the workflows are registered
#    RESTART the session first — the workflow registry is built at startup, so a plugin
#    installed or updated during this session ships workflows this session cannot see.
#    Then, in the new session, ask for the chain: /plan on any L4+ task should reach
#    `graph-powers:ultra-plan`. If it reports `Workflow "graph-powers:ultra-plan" not found`,
#    the plugin is installed but the session predates it — restart again, do not debug.

# 7. the agents resolve, by the name the registry uses
#    Spawn one, in the new session, and read the error rather than guessing:
#      Agent({ subagent_type: "graph-powers:explorer", prompt: "list the files in agents/" })

# 7b, 9 and 10. One package/posture proof for Claude, Codex, Cursor and Grok.
#     It also reports Zed as NOT ENFORCED instead of inventing a hook target.
python3 -X utf8 "$PLUGIN/bin/verify-hook-clients.py" --client all --project-dir . --check-posture --probe-guardrail

# 8. Codex answers, and its hooks run — only if Step 9 ran
codex doctor                                      # expected: 0 fail
codex exec --skip-git-repo-check "reply with: ok" # one line per hook, then the answer
#    Every hook line must read `Completed`. `Blocked` means a hook denied the turn — Codex reads
#    exit 2 as a decision, so this is what a wrong path looks like — and `Failed` means one errored
#    and was stepped over. Neither is a finished state; § 9b names the entry behind either. A hook
#    that appears in `/hooks` and in no output line is unapproved: approve it there.


```

Two client verdicts are explicit report gates rather than shell commands:

- **Codex Desktop:** `PASS` only when a newly started Desktop process proved the same Codex home,
  current Graph Powers version and hook execution. Otherwise `UNVERIFIED`; never copy the CLI result.
- **Zed:** `NOT ENFORCED` for native tool calls. This is the correct result until this repository has
  a real Zed hook API/target; rules, skills and LSP settings are reported separately as `present` or
  `missing`.

**When an agent will not spawn**, the error names which of the two problems you have. They have
opposite fixes, so read it before changing anything.

| Message | What it means | Fix |
|---|---|---|
| `Agent type 'explorer' not found. Available agents: … graph-powers:explorer …` | The caller used the bare name. This plugin's agents are namespaced, and the error lists the string that works. | Use `graph-powers:<agent>`. Everything this plugin ships already does; a project's own command may not. |
| `Unknown subagent_type 'graph-powers:explorer'. Valid: … explorer …` | **Not the CLI.** Its own refusal reads `Agent type 'X' not found. Available agents: …`. A `Valid:` phrasing with bare names is a `PreToolUse` hook matching `Agent`, denying from a local allowlist that was built by scanning `.claude/agents/` and therefore contains no plugin agent at all. | Fix the hook: it must not deny a `<plugin>:<agent>` name. The registry validates those itself. Restarting does not help — the hook runs on every call. |
| The agent is missing from the list entirely | Check **which** list first. Absent from `claude plugin details <plugin>@<marketplace>` means the plugin does not ship it, or its frontmatter is malformed. Absent only from a hook's `Valid:` list means the hook's allowlist is stale, and the agent is fine. | `claude plugin details` is the authority on what ships; `python3 $PLUGIN/.github/check_wiring.py` checks the frontmatter contract. |

The second row was misdiagnosed here for a while as a stale session, and a restart was prescribed;
it is not, and a restart does not fix it. The distinguishing evidence is cheap: run the same spawn
in a fresh process — `claude -p "spawn subagent_type 'graph-powers:explorer' …"`. A fresh process
carries a fresh registry, so if the same message returns, nothing about the session is stale and the
refusal is coming from a hook. `claude plugin details graph-powers@graph-powers`
lists what the plugin actually ships, which is the tie-breaker when the two error lists disagree.

Then check every path you cited in a file you touched actually exists. A dangling reference is
silent: the agent reads it, finds nothing, and carries on with less context than it thinks it has.

**Restart every client whose plugin, hooks or permission posture changed.** For Codex Desktop, quit
the app completely so its app-server exits. Cursor gets a full window reload. Grok and Claude/Codex
CLI get a new process/session. Zed has no Graph Powers hooks to reload.

---

## Step 11 — Report, and stop

```markdown
## Graph Powers — setup complete

**External dependencies:** none required · optional plugins: codex <present|absent> · code-review <present|absent> · landing-page-design personal copy <none|removed>
**Config:** <created | merged> — branch <x>, opt-in prefix <Y>, gates <list>
**CLAUDE.md:** <lines before> → <lines after> · removed: <what> · preserved: <what>
**Intent layer:** root AGENTS.md · <n> child nodes (<paths>) · <n> candidates deferred (<why>) · check: exit <code>
**Rules:** <n> kept · <n> replaced by templates · <n> removed (<why>)
**Authorities:** DESIGN.md <created|improved|skipped, why> · PRODUCT.md <…> · REVIEW.md <…>
**Cleanup:** <n> local copies removed · <n> kept as deliberate overrides (<which, and why>)
**settings.json:** <n> duplicate hooks removed · other keys untouched
**Interpreter:** python3 <version> — literal command present before any permissive posture
**Global:** <installed | already present at version X, skipped> — Claude plugin scope, Codex skills/agents/hooks
**Project:** <what was written here, and nothing else>
**Claude hooks:** <version · package/discovery · restarted · live proof>
**Codex CLI health:** <§ 9b before: n BLOCKS / n RISK> → <after: same, and what was repaired>
**Codex CLI hooks:** <version · 15 discovered · approved/live | pending — guardrails inert>
**Codex Desktop:** <PASS with separate evidence | UNVERIFIED — why> — never inherited from CLI
**Cursor:** <plugin version · 12 hooks · permissions approvalMode | skipped> — full window reload
**Grok:** <plugin version · 15 hooks · active Grok-home permission_mode | skipped> — restarted
**Zed:** instructions/skills/editor settings <state> · Graph Powers hooks `NOT ENFORCED`
**Verification:** <each check, with its result>
**Backup:** <path> — restore with `rm -rf .claude && mv <backup> .claude`
```

**Do not commit anything.** The changes stay in the working tree; the person commits them, having
seen what changed.

---

## Rules that hold for this entire playbook

1. **Run scoped, reversible writes and validation without pausing.** Stop for destructive cleanup,
   credentials or secrets, outward-facing actions, and writes whose ownership cannot be proven.
2. **Never delete without a `diff` on screen.** The one file that looks identical is the one that
   is not.
3. **Never invent a value.** No path, no command, no domain, no branch name. Read it, or ask.
4. **Preserve every `[HARD]` invariant and every routing row exactly.** Those cannot be
   reconstructed.
5. **A step that could not be completed is reported as not completed.** "I could not verify this"
   and "this is fine" are different answers, and collapsing them is how a broken setup ships
   looking green.
