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
changes things is this playbook: it installs the required external plugins, writes the project's
parameters, **improves the instruction files that already exist** rather than replacing them, and
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
| The Claude Code plugin: agents, skills, commands, guardrails, workflows, shared references | `~/.claude/settings.json` (`--scope user`) — one install, no copies |
| Codex native plugin: skills, subagents, guardrails and references | versioned cache reported by `codex plugin list --json` |
| Codex clone fallback: skills | `~/.agents/skills/` |
| Codex clone fallback: subagents, guardrails and references | `~/.codex/agents/*.toml` · `~/.codex/hooks.json` · `~/.codex/graph-powers/` |
| Clone fallback machine-wide instruction block | `~/.codex/AGENTS.md` |

| Stays LOCAL — belongs to this repository and nothing else | Where |
|---|---|
| The parameters: branch, gate commands, paths, opt-in prefix | `.graph-powers/config.json` |
| Domain rules | `.claude/rules/` · `.codex/rules/` |
| The three authorities | `DESIGN.md` · `PRODUCT.md` · `REVIEW.md` |
| Project identity and invariants | `CLAUDE.md` · `AGENTS.md` |
| Anything this project genuinely overrides | `.claude/agents/`, `.claude/skills/`, `.claude/commands/` |

**Why global is correct here rather than sloppy:** the guardrails read *the project's own*
`.graph-powers/config.json` at runtime, through `hooks/_config.py`. One global copy therefore
enforces a different work branch and a different opt-in key in every repository. Copying the
harness into each project would buy nothing and reintroduce the divergence this plugin exists to
end — eleven skills copied into five repositories is five copies that drift.

**The only reason to go local instead:** the team must receive the harness by cloning the
repository, on machines where nobody will run an installer. Then use `--scope project`, and accept
that the copy is now yours to keep in sync.

### Check before you install

Global installation is idempotent, and skipping it when it is already there is the difference
between a five-second setup and a needless one:

```bash
# Already installed for this whole machine? Both harnesses, one answer.
# Python rather than `cat ~/... 2>/dev/null`: `~` is not expanded by PowerShell and there is no
# /dev/null on Windows, so the shell form reported "not installed" on every Windows machine —
# which reads as a clean check and is really the check never running.
python3 - <<'CHECK'
import json, os
claude = os.path.expanduser("~/.claude/plugins/installed_plugins.json")
d = json.load(open(claude)) if os.path.exists(claude) else {"plugins": {}}
hits = [(k, i) for k, v in d.get("plugins", {}).items() if k.startswith("graph-powers@")
        for i in v if i.get("scope") == "user"]
print("claude:", hits or "not installed globally")

codex = os.path.expanduser("~/.codex/graph-powers-installed.json")
print("codex clone install:",
      json.load(open(codex)) if os.path.exists(codex) else "not installed")
CHECK

# The native Codex plugin is a different installation route from the clone manifest above.
codex plugin list --json
```

In the JSON, `graph-powers@graph-powers` with `installed: true` and `enabled: true` is the preferred
Codex route. If that entry and the clone manifest both exist, do not proceed as though one were a
backup of the other: they register the same hooks from different roots and both run. Step 9c
migrates that state before project setup continues.

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

for tool in ("claude", "codex", "python3", "node"):
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
2. the `path` for `graph-powers@graph-powers` in `codex plugin list --json` — the native Codex cache;
3. `~/.claude/plugins/cache/graph-powers/graph-powers/*/` — where Claude Code keeps installed
   plugins. Prefer the highest version directory there;
4. `~/.graph-powers/src/`, or any other clone of `GrupoUS/graph-powers` on this machine;
5. if none exists, install it and say which route you took:

   ```bash
   # Claude Code, inside a session:
   #   /plugin marketplace add GrupoUS/graph-powers
   #   /plugin install graph-powers@graph-powers
   # Anywhere, from a clone:
   git clone https://github.com/GrupoUS/graph-powers.git ~/.graph-powers/src
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
$env:PLUGIN = "<the directory you just found>"

# prove it before going on, on either
python3 -c "import os,sys;p=os.environ.get('PLUGIN','');sys.exit(print('PLUGIN=' + p) if os.path.isfile(os.path.join(p,'AGENT_SETUP.md')) else 'PLUGIN does not point at a plugin root')"
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

## Step 1 — Install what the harness depends on

Two kinds of dependency, and this step installs both: the **plugins** the commands call into, and
the **binaries** the skills shell out to. Neither is vendored. A copied snapshot of somebody else's
work goes stale and cannot be updated — which is the exact failure this harness exists to end, one
level up.

Start by running the preflight at the end of this step. It prints one line per prerequisite and is
the fastest way to know which halves of this step you can skip.

**The two plugins are required.** Nine of the ten commands call superpowers skills; without it
`/plan`, `/debug` and `/implement` stop mid-run. `/design` delegates every craft pass to impeccable.

### superpowers — the method layer

Brainstorming, writing plans, executing plans, test-driven development, systematic debugging,
verification before completion. Maintained at [obra/superpowers](https://github.com/obra/superpowers).

- **Claude Code**, at user scope so it serves every project like the rest of the harness:
  ```
  /plugin marketplace add obra/superpowers-marketplace
  /plugin install superpowers@superpowers-marketplace
  ```
  Check first — `claude plugin list | grep superpowers`. If it is there, skip.
  (It is also on the official Claude plugin marketplace: `/plugin install superpowers@claude-plugins-official`.)
- **Codex CLI:** open `/plugins`, search `superpowers`, select *Install Plugin*.

Verify: `Skill("superpowers:using-superpowers")` resolves. If it does not, **stop** and tell the
user — do not carry on and let commands fail halfway through a task.

### impeccable — the design layer

Design, critique, audit and anti-pattern detection for interfaces. Apache-2.0, maintained at
[pbakaus/impeccable](https://github.com/pbakaus/impeccable).

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

```bash
# Global first, like everything else that is identical per project.
# Substitute <runner> from the table above.
<runner> impeccable install --providers=claude,codex --scope=global --yes

# Only fall back to --scope=project when the team must get it by cloning the repository.
```

**`--yes` is not optional here.** Without it the installer prompts for the harnesses and the scope,
and a command an agent runs unattended stops on a question nobody answers. With `--providers` and
`--scope` both given, `--yes` is what makes the run deterministic instead of merely defaulted.

**Where it lands, so you can verify it.** The Codex half installs to `~/.agents/skills/impeccable`,
not `~/.codex/skills` — `.agents/skills` is the shared skills directory Codex reads, and it is the
same one `codex/install.mjs` writes this plugin's skills into. Confirm with a directory listing of
`~/.agents/skills` and by checking that `~/.codex/hooks.json` still holds this plugin's hook
commands alongside impeccable's.

**Order matters.** Run this *before* Step 3 writes the Codex artefacts: impeccable also writes
`.codex/hooks.json`, and although the Graph Powers installer merges rather than overwrites, doing
it in this order means the merge happens once and you can verify it once.

### Keeping them current

Both age independently of this plugin. Add these to whatever the project uses for routine
maintenance, and tell the user they exist:

```bash
<runner> impeccable update      # same runner as the install above
claude plugin update graph-powers
# superpowers updates through the plugin marketplace it was installed from
```

### The other two plugins, both conditional

| Plugin | Reached from | Without it |
|---|---|---|
| `codex@openai-codex` | `/debug` escalation (`commands/debug.md` § 1.3, § 1.6, § 1.7) and `/implement --codex` | escalation falls through to `/debug recover`; nothing hangs |
| `code-review@claude-plugins-official` | `/pr-review` § 3C, already labelled best-effort | one of four review paths is missing; the other three still run |

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
| **Works either way, better global** | resolves through a runner, but re-downloads every call and keeps state between them | `agent-browser`, `biome`, `oxlint` |

That distinction is the point of this section. Most of what you will see in fenced blocks across the
skills is the middle class, so the real prerequisite list is far shorter than the list of tool names.

#### `python3` is the name, and 3.10 is the floor

All twelve hook scripts — thirteen event registrations because the Bash approver also handles
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
has this plugin's own guardrail refuse `bunx`, correctly — the same trap the impeccable half of this
step warns about, with the same runner table as its answer. A global install sidesteps the runner
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
| `claude` | REQUIRED | the harness; `second-opinion` runs it headless | `npm install -g @anthropic-ai/claude-code` |
| `gh` | CONDITIONAL — required the moment a PR or an issue is involved | `gh pr checkout`, `gh issue view` | cli.github.com — then `gh auth login`, because `gh auth status` failing is its own stop |
| `agent-browser` | RECOMMENDED | `/debug frontend`, `webapp-testing`, the `graph-powers:verification` agent | `npm install -g agent-browser` |
| a Chrome-family browser | RECOMMENDED | what `agent-browser` drives | already present on most machines; otherwise `agent-browser install` |
| `gitleaks` | OPTIONAL | `/perf security-baseline` secret scan | github.com/gitleaks/gitleaks |
| `psql` | OPTIONAL | database evidence in `/debug auth-db` and `/debug backend` | your OS package manager |
| `codex` | OPTIONAL | the Codex half, and `codex:codex-rescue` escalation | `npm install -g @openai/codex` |
| `code-review-graph` | OPTIONAL | `/plan` Step 0 structural search | `python3 -m pip install code-review-graph` |
| `timeout` | OPTIONAL, and unavailable on Windows | `second-opinion` wraps its headless `claude` call in it | GNU coreutils: present on Linux; macOS needs `brew install coreutils` and the binary is `gtimeout`. Windows has an unrelated `timeout.exe` that pauses — there, drop the wrapper and watch the run yourself |

`code-review-graph` is the one whose absence is designed for: `references/shared/115-code-graph.md`
says the graph steps are **SKIPPED, never blocking**, and `/plan` falls back to grep. Install it for
speed, not for correctness.

`biome` and `oxlint` are not in this table on purpose — they are gate tooling, they depend on what
the project declares, and Step 3 installs them where that decision is made.

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
    ("python3",       "REQUIRED",    "the literal name all 12 hook scripts register; see below"),
    ("git",           "REQUIRED",    "every command; the guardrails read the worktree"),
    ("node",          "REQUIRED",    "workflows, bin/, the Codex installer, 18+"),
    ("claude",        "REQUIRED",    "the harness; second-opinion runs it headless"),
    ("gh",            "CONDITIONAL", "/pr-review, and /plan in issue mode"),
    ("agent-browser", "RECOMMENDED", "/debug frontend and the browser QA agent"),
    ("gitleaks",      "OPTIONAL",    "/perf security-baseline"),
    ("psql",          "OPTIONAL",    "database evidence in /debug auth-db"),
    ("codex",         "OPTIONAL",    "the Codex half and codex:codex-rescue"),
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
                         ("superpowers",  "REQUIRED",    "nine of the ten commands call it"),
                         ("codex",        "OPTIONAL",    "codex:codex-rescue escalation"),
                         ("code-review",  "OPTIONAL",    "one of /pr-review's four paths")):
    hit = [n for n in names if n.startswith(want + "@")]
    row(want, hit[0] if hit else "MISSING", level, who)
row("impeccable", "present" if os.path.isdir(os.path.join(home, ".claude/skills/impeccable"))
    else "MISSING", "REQUIRED", "/design delegates every craft pass to it")

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

**Only declare a command whose tool is installed, and choose one owner for its version.**
`tooling.commands.format` runs after every edit and `tooling.commands.lint` at every stop; the
plugin runs what you wrote and nothing more. There are two valid installation models, but mixing
them is how the CLI, editor and schema end up describing different releases:

| Model | Use when | Commands in `.graph-powers/config.json` | Version owner |
|---|---|---|---|
| project-local | the repository has a JavaScript package manifest and lockfile | package scripts such as `bun run format` and `bun run lint` | manifest + lockfile |
| global | the repository must not acquire tool dependencies, or one machine-wide baseline is deliberate | direct `biome …` and `oxlint …` commands | the global package installation |

For a project-local installation, add both tools with the package manager the project already
uses, put the real commands in its manifest, and route Graph Powers through those scripts:

```bash
bun add -D @biomejs/biome oxlint
```

```json
{
  "scripts": {
    "format": "biome format --write",
    "lint": "oxlint --deny-warnings"
  }
}
```

```json
"tooling": {
  "commands": {
    "format": "bun run format",
    "lint": "bun run lint"
  }
}
```

Replace `bun run` with the runner declared by the project; do not install one package manager just
for these two commands.

For the global model, install both globally because this harness follows the session into
repositories that do not carry them as dependencies:

```bash
bun add -g @biomejs/biome oxlint
biome --version
oxlint --version
```

Editor extensions have their own binary discovery and update behavior; installing a CLI does not
prove the IDE launched it. Prefer the project-local binary when the project-local model was chosen,
or pin the global binary in the IDE's user settings when GUI launches cannot see the shell's
`PATH`. Do not let an extension download become a silent third version. VS Code and compatible
editors such as Cursor use the official `biomejs.biome` extension and, when oxlint diagnostics are
deliberate, `oxc.oxc-vscode`. Zed uses the official Biome and Oxc extensions. Other IDEs follow the
same contract below even when their setting names differ.

Nothing is hidden if the direct-command model is wrong: every session start names what did not
resolve (`NOT INSTALLED: lint needs oxlint`). A command routed through the package manager
(`bun run lint`) cannot be preflighted from its name; the setup verification below must execute it.

### Configuring Biome and oxlint so the gate actually checks something

A declared command with no config file behind it runs, exits 0, and reports nothing — the worst
possible gate, because the line reads as covered. Both tools need a config committed to the
repository, and they need to divide the work or they duplicate it.

#### Scope before rules — this is where the noise comes from

Measured on a real Astro project in this org, running each tool at the repository root with no
scoping, against the same tool scoped to the project's own source:

| Run | Files | Findings |
|---|---|---|
| oxlint, no config | — | 468 warnings |
| oxlint, defaults + `ignorePatterns` | — | **5** |
| Biome, `includes: ["**"]` | 387 | 1,093 errors · 1,090 warnings · 1,345 infos |
| Biome, `includes` minus harness dirs | 62 | 56 errors (50 of them *formatting* of JSON config files) · 163 warnings |

**Ninety-nine per cent of it was in files the project did not write.** Nearly all of it sat in
`.claude/` and a timestamped `.claude.bak-*/` — bundled third-party JavaScript that skills ship,
where `no-unused-vars` (169), `no-unused-expressions` (156) and `no-loss-of-precision` fire on
minified output and on colour-conversion constants that are supposed to be long doubles. Correct
code, correctly flagged, in somebody else's file.

That makes it this plugin's problem rather than the project's chore: **the harness is what puts
that code in the tree**, so the harness has to be what excludes it. Put these in both configs, and
add `.claude.bak*` because a backup taken during setup is linted like source:

```
.claude/**   .claude.bak*/**   .codex/**   .agents/**
node_modules/**   dist/**   build/**   .astro/**   .next/**   coverage/**   *.min.js
```

`.gitignore` is not a substitute. oxlint does respect it — verified — but `.claude/` is *deliberately
committed*, since the harness config is meant to be shared, so an ignore file will never exclude it.
The exclusion has to be in the linter config.

Do this first and measure again before touching a single rule. A project whose declared lint already
passes has nothing to fix; the number that alarmed you may be entirely outside its source. Check
what the project actually declares before running anything wider:

```bash
python3 -c "import json;print(json.load(open('.graph-powers/config.json'))['tooling']['commands'])"
```

**The division.** Biome formats; oxlint lints. Both *can* lint, and turning both loose on the same
rules produces two diagnostics per finding, which trains people to skim. Biome's linter still earns
its place for the editor and for a manual full pass; it is simply not the thing the Stop gate runs.

| Tool | Owns | Runs as |
|---|---|---|
| Biome | formatting, import sorting, editor diagnostics | `tooling.commands.format`, on every edit |
| oxlint | the lint gate — correctness across the whole tree | `tooling.commands.lint`, at Stop |

```json
"tooling": {
  "commands": {
    "format": "biome format --write",
    "lint": "oxlint --deny-warnings"
  }
}
```

`--deny-warnings` is part of the gate contract, not a strictness flourish. Without it, oxlint can
print warnings and still exit 0, so the Stop hook records a pass for findings it just displayed.

**`format` is `biome format --write`, not `biome check --write`.** `check` runs the linter and the
assists with auto-fix, so it rewrites imports and code shape between two edits of a half-finished
refactor — the hook applies it after *every* Write, and a fix landing mid-edit cascades errors into
the next one. `format` touches whitespace and nothing else. For the same reason `lint` never carries
`--fix` or `--write`: at Stop the job is to report, not to change code the person is about to read.

**`biome.json`** — `biome init` writes a starter; these are the keys that matter
([reference](https://biomejs.dev/reference/configuration/)). Pin `$schema` to the exact version
printed by `biome --version` so the editor validates against the rules the CLI actually runs.
Replace `<BIOME_VERSION>` before committing; it is an instruction, not a literal schema URL:

```json
{
  "$schema": "https://biomejs.dev/schemas/<BIOME_VERSION>/schema.json",
  "vcs": { "enabled": true, "clientKind": "git", "useIgnoreFile": true },
  "files": {
    "ignoreUnknown": true,
    "includes": [
      "src/**", "tests/**", "*.config.*",
      "!**/.claude/**", "!**/.claude.bak*/**", "!**/.codex/**", "!**/.agents/**",
      "!**/node_modules/**", "!**/dist/**", "!**/build/**", "!**/.astro/**",
      "!**/.next/**", "!**/coverage/**"
    ]
  },
  "formatter": { "enabled": true, "indentStyle": "space", "indentWidth": 2, "lineWidth": 100 },
  "javascript": {
    "formatter": { "quoteStyle": "double", "semicolons": "always", "trailingCommas": "all" }
  },
  "linter": {
    "enabled": true,
    "rules": {
      "preset": "recommended",
      "correctness": { "noUnusedVariables": "error", "noUnusedImports": "error" }
    }
  },
  "assist": { "enabled": true, "actions": { "source": { "organizeImports": "on" } } }
}
```

Three details in `files.includes` decide whether this is a gate or a wall of noise.

**Name the source; do not take the whole tree minus exclusions.** `biome check` runs the formatter
as well as the linter, so `["**", …]` asks the repository to format every `package.json`,
`tsconfig.json`, `vercel.json` and `.vscode/` file it can find. Measured on the project above: the
tree-minus-exclusions form reported 255 findings of which **6 were lint** and the rest formatting of
config files nobody formats with Biome. Listing `src/**` and the config files you actually own gave
41 files and a clean exit on the same repository.

**The patterns resolve relative to the config file**, not to where you run the command. `src/**` in
a root `biome.json` means the project's `src`, wherever Biome is invoked from.

**`vcs.useIgnoreFile` is the one people skip** and then wonder why the formatter walks `dist/`. It is
not a substitute for the exclusion list, since the harness directories are committed on purpose.

Rule severities are `off`, `info`, `warn`, `error`; `rules.preset` accepts `recommended`, `all` or
`none`, and the domains are a11y, complexity, correctness, nursery, performance, security, style and
suspicious.

**`.oxlintrc.json`** — the file oxlint reads by default
([reference](https://oxc.rs/docs/guide/usage/linter/config-file-reference.html)):

```json
{
  "ignorePatterns": [
    "**/.claude/**", "**/.claude.bak*/**", "**/.codex/**", "**/.agents/**",
    "**/node_modules/**", "**/dist/**", "**/build/**", "**/.astro/**",
    "**/.next/**", "**/coverage/**", "**/*.min.js"
  ]
}
```

The `$schema` field depends on the installation model. With project-local oxlint, add
`"$schema": "./node_modules/oxlint/configuration_schema.json"`. With global-only oxlint, omit it:
that relative file does not exist, and adding it creates an editor error even though the linter
itself works. `$schema` improves completion; it does not change oxlint's runtime behavior.

**That is the whole file, and the omissions are the point.** oxlint's default is the `correctness`
category — rules that flag code that is wrong, not code that is unfashionable. On the project
measured above that default plus these ignores produced **5 findings**, every one worth a look.

Adding `plugins` and widening `categories` is not free, and the direction is the opposite of what it
looks like. The same project, same ignores, with `["import","node","promise","unicorn","oxc",
"typescript"]` and `suspicious`/`perf` at warn: **68 findings**. What the extra rules bought:

| Rule | Count | Why it was noise here |
|---|---|---|
| `no-underscore-dangle` | 27 | Google Apps Script *requires* a trailing `_` to keep a function private. The rule was arguing with the platform |
| `no-await-in-loop` | 17 | Deliberate sequencing in a smoke-test script. Parallelising it would have been the bug |
| `consistent-function-scoping` | 8 | Test helpers and inline handlers, hoisted for no benefit |
| `no-array-sort` | 6 | Wants `toSorted()`. Every call sorted an array `map` had just produced — nothing to mutate |

None of those is a false positive in the sense of the rule misfiring; each is the rule correctly
reporting something this codebase decided on purpose. That is still noise, and it is worse than
silence: 63 entries nobody will read, hiding the 5 that mattered.

So widen only after measuring, one axis at a time, and write down what each addition bought. If a
rule fires more than a handful of times and every hit is intentional, turn that rule off by name and
say why in the config — a rule disabled with a reason is a decision, and one disabled silently is a
mystery for whoever inherits it. `"react"` and `"jsx-a11y"` are the two additions that usually do pay
for themselves in a React project; add `"vitest"` or `"jest"` if the suite is large enough to have
its own smells. Severities are `off`, `warn`, `error`, and a rule entry overrides its category.

One option worth setting the moment `no-unused-vars` is on, because the underscore prefix is the
language-wide convention for "deliberately unused" and the rule does not assume it:

```json
"rules": {
  "no-unused-vars": ["warn", {
    "argsIgnorePattern": "^_",
    "varsIgnorePattern": "^_",
    "caughtErrorsIgnorePattern": "^_"
  }]
}
```

#### IDE wiring is a separate gate

A clean CLI does not prove that an IDE launched the same binary. The setting names vary, but the
contract does not:

1. Install the official Biome integration for that IDE.
2. Start it only when `biome.json` or `biome.jsonc` exists.
3. Make Biome the only formatter for each supported language.
4. Choose exactly one editor diagnostic provider: Biome by default, or oxlint deliberately.
5. Keep machine-local binary paths in user settings; commit only portable workspace settings.
6. Restart the language server after installing or upgrading a binary.

The baseline in this playbook is **Biome formats and reports editor diagnostics; oxlint runs as the
Stop/CI gate**. It needs no oxlint editor extension. If an Oxc extension is already installed
machine-wide, disable both its oxlint and Oxfmt services in this workspace so it cannot become a
second diagnostic provider or formatter.

| IDE family | Official integrations | Portable workspace settings | Recovery command |
|---|---|---|---|
| VS Code, Cursor, VSCodium and compatible editors | `biomejs.biome`; optional `oxc.oxc-vscode` | `.vscode/settings.json` | `Developer: Reload Window`; Oxc also provides `Oxc: Restart oxlint Server` |
| Zed | Biome; optional Oxc | `.zed/settings.json` | restart the Biome/Oxlint language server |
| IntelliJ-family and other IDEs | use the official Biome integration where available | the IDE's project settings | restart the plugin or IDE language service |

##### VS Code, Cursor and compatible editors

Cursor and other VS Code derivatives use the same workspace keys. This baseline requires a Biome
configuration and enables format-on-save only for named languages:

```json
{
  "biome.enabled": true,
  "biome.requireConfiguration": true,
  "[javascript]": {
    "editor.defaultFormatter": "biomejs.biome",
    "editor.formatOnSave": true
  },
  "[javascriptreact]": {
    "editor.defaultFormatter": "biomejs.biome",
    "editor.formatOnSave": true
  },
  "[typescript]": {
    "editor.defaultFormatter": "biomejs.biome",
    "editor.formatOnSave": true
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "biomejs.biome",
    "editor.formatOnSave": true
  }
}
```

Add language blocks only for formats the project owns. Do not set `editor.defaultFormatter`
globally, because Biome does not support every language in a mixed repository. Do not enable
`source.fixAll.biome` or `source.fixAll.oxc` on save by default: either turns a format operation into
a lint-fix operation, contradicting the `biome format --write` boundary above.

If `oxc.oxc-vscode` is installed globally but this project follows the baseline, add these workspace
settings to keep it inactive here. Do not add unknown `oxc.*` keys when the extension is absent:

```json
{
  "oxc.enable.oxlint": false,
  "oxc.enable.oxfmt": false
}
```

If the team chooses oxlint for IDE diagnostics, install `oxc.oxc-vscode` and reverse only the
diagnostic ownership:

```json
{
  "biome.inlineConfig": { "linter": { "enabled": false } },
  "oxc.enable.oxlint": true,
  "oxc.enable.oxfmt": false,
  "oxc.requireConfig": true
}
```

The Oxc extension does not bundle oxlint. Its recommended path is the project-local package; after
installing while the IDE is open, run `Oxc: Restart oxlint Server` or reload the window.

##### Zed

For Zed, configure the same ownership explicitly per language. The Biome extension from `0.2.0`
onward requires Biome v2; the current Oxc extension requires oxlint `1.35.0` or newer.

```json
{
  "lsp": {
    "biome": {
      "settings": { "require_config_file": true }
    }
  },
  "languages": {
    "JavaScript": {
      "language_servers": ["biome", "!oxlint", "!oxfmt", "..."],
      "formatter": { "language_server": { "name": "biome" } }
    },
    "TypeScript": {
      "language_servers": ["biome", "!oxlint", "!oxfmt", "..."],
      "formatter": { "language_server": { "name": "biome" } }
    },
    "TSX": {
      "language_servers": ["biome", "!oxlint", "!oxfmt", "..."],
      "formatter": { "language_server": { "name": "biome" } }
    }
  }
}
```

Repeat the language block only for formats the project owns; do not set Biome as a top-level global
formatter or language server. If oxlint should own diagnostics, enable it in the language list and
set `lsp.biome.settings.inline_config` to `{ "linter": { "enabled": false } }`.

##### Binary pinning and recovery in any IDE

Sandboxed editors and GUI launches may not inherit the shell's `PATH`. Put machine-local paths in
**user settings**, never in committed workspace settings:

For VS Code, Cursor and compatible editors:

```json
{
  "biome.lsp.bin": "<path-to-biome>",
  "oxc.path.oxlint": "<path-to-oxlint>"
}
```

For Zed:

```json
{
  "lsp": {
    "biome": {
      "binary": {
        "path": "<path-to-biome>",
        "arguments": ["lsp-proxy"]
      }
    },
    "oxlint": {
      "binary": {
        "path": "<path-to-oxlint>",
        "arguments": ["--lsp"]
      }
    }
  }
}
```

Other IDEs expose equivalent binary-path fields. Biome speaks LSP through `lsp-proxy`; oxlint uses
`--lsp`, but an extension may add those arguments itself — use the extension's documented binary
field rather than putting a raw command into an unrelated setting.

| Symptom | First proof | Correct response |
|---|---|---|
| Biome initialization times out with `Connection refused` | `biome rage --daemon-logs` shows whether a daemon and its config loaded | run `biome stop`, restart the IDE language server, then inspect its output/log for the binary path and version; do not edit lint rules |
| CLI passes but the IDE fails | IDE output/log names a different binary than `biome --version` | align the local/global versions or pin the intended binary in user settings |
| `.oxlintrc.json` schema cannot be resolved | oxlint is global but `$schema` points into `node_modules` | omit `$schema`, or install oxlint project-locally |
| every finding appears twice | both Biome and oxlint integrations report diagnostics | choose one editor diagnostic provider |
| files change back and forth on save | Biome and Oxfmt/Prettier are both formatters | keep one formatter per language |

`biome clean` removes daemon **logs**, not a broken socket or mismatched binary; it is not the fix for
`Connection refused`. `biome rage --daemon-logs` is the diagnostic command, and `biome stop` plus a
single IDE language-server restart is the portable recovery path.

**Prove the CLI and IDE separately before moving on**, and show the output — a config that is
present but not being read looks exactly like a clean run:

```bash
biome --version
oxlint --version
biome format . --reporter=summary
biome lint . --reporter=summary
oxlint --deny-warnings
biome rage
```

The format command reports drift without writing; the lint commands prove each rule engine loads;
`biome rage` names the loaded configuration and, while the editor is open, the daemon version. Then
open the IDE's language-server output/log and confirm the launched Biome path/version is the one
selected by the installation model.

**In CI, preserve the same division with check-only commands:** run
`biome ci --linter-enabled=false` for formatting and assists, then `oxlint --deny-warnings` for lint.
Both are read-only and exit non-zero on their own findings; they do not duplicate lint diagnostics.

**If the project already has ESLint or Prettier, do not add these.** Two formatters fighting over
the same file is worse than the one that was already there, and this plugin's contract is to run
what the project declared, not to migrate it.

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
  "paths": { "frontendRoot": "…", "backendRoot": "…", "schemaRoot": "…" }
}
```

Set `autonomy` deliberately and say what you set:

```json
"autonomy": { "level": "autonomous", "destructiveFloor": true }
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

- **Write the permission allowlist too.** `node "$PLUGIN/bin/graph-powers.mjs" --target claude`
  adds it, additively — whatever the settings file already allowed stays. Without it the person
  approves the harness's own gate commands several times an hour.
- **`optInPrefix` must differ per project.** With the same prefix in two repositories, an approval
  given in one starts counting in the other. The versioned test covers exactly this case.
- **Omit a path the project does not have.** An empty `schemaRoot` tells the planner there is no
  data layer. A guessed one makes it plan a phase for a repository that does not exist.
- **`testRunner: null` is an answer.** It says the absence is deliberate. Omitting the field says
  nobody looked.

**Leave `autoUpdate` alone unless the project asks otherwise.** The harness keeps itself current
on its own: at session start, at most once every twelve hours, a detached worker asks each CLI to
update itself through its own supported path. Nothing waits on the network and nothing inside the
project is touched. Do **not** write a cron job, a CI step or a git hook to do this — there is
already one mechanism, and a second one is how two of them start disagreeing.

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

## Step 4 — Improve `CLAUDE.md` and `AGENTS.md`

These files already exist and carry decisions nobody remembers making. The goal is **not** to
replace them. It is to take out what now comes from the plugin, keep what only exists here, and
lose nothing on the way.

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
  belong to the project. **Do not touch them.** If the audit suggests permissions, *append* to the
  existing array; never replace the list.

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

## Step 9 — Wire Codex, if the project uses it

Read this before running the installer, because it is the one step where getting it wrong does not
degrade the harness — it takes the CLI down.

Four states are separate and each has its own proof:

| State | Proof | If absent |
|---|---|---|
| Plugin installed and enabled | `codex plugin list --json` contains enabled `graph-powers@graph-powers` | install with 9c |
| Hooks discovered | `/hooks` lists thirteen registrations sourced from `graph-powers@graph-powers` | restart once; then verify the package contains `hooks/hooks.json` |
| Hooks approved | `/hooks` shows those entries enabled/trusted | approve them explicitly; installation never grants trust |
| Hooks executing | `codex exec --skip-git-repo-check "reply with: ok"` reports `Completed` | use the diagnostic matrix in 9e |

**Codex reads a hook's exit code as a decision, not as a status.** `0` succeeds. `2` denies, with
whatever the hook wrote to stderr as the reason: the prompt on `UserPromptSubmit`, the tool call on
`PreToolUse`, the result on `PostToolUse`. Any other code is an error Codex reports and steps over.

Which is why a wrong path is not a broken guardrail but a locked session. A hook that reads
`python "C:/…/hooks/agent_hooks.py"` on a Linux machine does not fail to start: `python` starts,
cannot open the file, and exits **2**. Codex reads a deny. Every prompt is refused, the message
names a path rather than a cause, and a fresh session behaves identically — the hook lives in
`~/.codex/hooks.json`, which is read before the session accepts anything. Nothing distinguishes
that from a hook simply being strict.

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
python3 - <<'CODEX'
import glob, json, os, re, shutil, sys

home = os.path.expanduser("~")
codex = os.path.join(home, ".codex")
if not os.path.isdir(codex):
    print("codex home: absent — nothing to check")
    sys.exit(0)

hooks_file = os.path.join(codex, "hooks.json")
try:
    doc = json.load(open(hooks_file, encoding="utf-8")) if os.path.exists(hooks_file) else {"hooks": {}}
except (OSError, ValueError) as exc:
    print(f"BLOCKS  {hooks_file} does not parse: {exc}")
    sys.exit(1)

# A path counts only where the command names it literally. The lookbehind drops the `%VAR%` and
# `$VAR` forms, which the shell resolves and this process cannot.
PATHS = re.compile(r"""(?<![\w%$])((?:[A-Za-z]:)?[\\/][^\s"';|&()]*\.(?:py|mjs|js|sh|ps1|exe|cmd|bat))""")
DRIVE = re.compile(r"^[A-Za-z]:[\\/]")
KEYWORDS = {"if", "for", "while", "case", "test", "[", "{", "command", "then", "else", "do", ":"}
windows_here = os.name == "nt"

entries = [(event, h) for event, groups in doc.get("hooks", {}).items()
           for g in groups for h in g.get("hooks", [])]
blocks, risks, no_windows = [], [], []

for event, hook in entries:
    posix, windows = hook.get("command", ""), hook.get("commandWindows", "")
    native, other = (windows or posix, posix) if windows_here else (posix, windows)
    first = re.match(r"\s*([^\s]+)", native)
    if first and first.group(1) not in KEYWORDS:
        exe = first.group(1)
        if not shutil.which(exe) and not os.path.exists(exe):
            blocks.append(f"{event}: interpreter {exe!r} is not on PATH")
    for path in set(PATHS.findall(native)):
        if bool(DRIVE.match(path)) != windows_here:
            blocks.append(f"{event}: the command this machine runs carries the other platform's path — {path}")
        elif not os.path.exists(path):
            blocks.append(f"{event}: command points at a file that is not here — {path}")
    for path in set(PATHS.findall(other)):
        if bool(DRIVE.match(path)) == windows_here:
            risks.append(f"{event}: the other platform's command carries this platform's path — {path}")
    if posix and not windows and PATHS.search(posix):
        no_windows.append(event)

config = os.path.join(codex, "config.toml")
if os.path.exists(config):
    text = open(config, encoding="utf-8", errors="replace").read()
    notify = re.search(r"^notify\s*=\s*\[([^\]]*)\]", text, re.M)
    if notify:
        quoted = re.findall(r'"((?:[^"\\]|\\.)*)"', notify.group(1))
        target = quoted[0].replace("\\\\", "\\") if quoted else ""
        if target and not shutil.which(target) and not os.path.exists(target):
            risks.append(f"notify names a command that is absent on this machine — {target}")
    if re.search(r"^\[\[?hooks\.(?!state)[A-Za-z]", text, re.M):
        risks.append("config.toml declares hooks as well as hooks.json — Codex loads both and warns")

conflicts = [p for d in (codex, os.path.join(home, ".claude"))
             for pattern in ("*conflicted*", "*sync-conflict*", "*conflicted copy*")
             for p in glob.glob(os.path.join(d, pattern))]

print(f"hooks.json: {len(entries)} entries")
for line in blocks:
    print(f"BLOCKS  {line}")
for line in risks:
    print(f"RISK    {line}")
if no_windows:
    print(f"NOTE    {len(no_windows)} hook(s) have no commandWindows and stay silent on Windows")
if conflicts:
    print(f"NOTE    {len(conflicts)} conflict cop(ies) from a file-sync tool in the Codex or Claude home")
if not (blocks or risks):
    print("every hook resolves on this machine")
CODEX
```

| Severity | What it found | What you do about it |
|---|---|---|
| `BLOCKS` | a command **this** machine runs names an interpreter or a file that is not here | fix it before installing. On Codex this is a deny, not a warning, and it will be blamed on whatever was installed last |
| `RISK` | the hook works here and is wrong on the machine this home syncs to; or `notify` names an absent binary; or hooks are declared twice | fix it now if the user works on two machines, and say so either way |
| `NOTE` | hooks with no `commandWindows`, or conflict copies left by a file-sync tool | report it. Neither breaks this machine; both are how the next break arrives |

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

Then restart Codex and approve the thirteen registrations in `/hooks`. The native loader discovers
`hooks/hooks.json` inside the plugin cache and resolves `${CLAUDE_PLUGIN_ROOT}` itself; no generated
copy in `~/.codex/hooks.json` is involved.

**Fallback — clone installer:** use this only when the marketplace is unavailable or a
project-scoped copy is required.

```bash
node "$PLUGIN/bin/graph-powers.mjs" --target codex          # global half + project half
```

That same script takes `--update`: it fast-forwards the clone and reinstalls from it. Native Codex
plugins update with `codex plugin marketplace upgrade graph-powers`; do not run the clone updater
against a marketplace cache.

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
the manifest's `pluginRoot` and `hookCommands`. After approval, run the recorded clone's installer:

```bash
python3 - <<'MIGRATE'
import json, os, subprocess
p = os.path.expanduser("~/.codex/graph-powers-installed.json")
m = json.load(open(p, encoding="utf-8"))
installer = os.path.join(m["pluginRoot"], "bin", "graph-powers.mjs")
subprocess.run(["node", installer, "--uninstall"], check=True)
MIGRATE
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
| `Failed` | hook errored and Codex stepped over it | inspect the named command, interpreter and path with 9b |
| `Blocked` | hook deliberately denied the event, or a wrong path exited 2 | read stderr; use 9b to distinguish policy from a broken command |
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

Recover in this order, and do not skip to reinstalling — a reinstall merges into the file that is
denying and changes nothing.

1. **Read the hooks without obeying them.** The trust flag runs every hook, including ones not yet
   approved, which is what tells you whether the problem is trust or the hook itself:

   ```bash
   codex exec --dangerously-bypass-hook-trust --skip-git-repo-check "responda apenas: ok"
   ```

   All `Completed` and a normal answer means the hooks are fine and unapproved — go to `/hooks`.
   A `Blocked` or `Failed` line names the event; 9b names the entry.
2. **Run 9b.** Every failure of this kind that has been seen so far shows up there as `BLOCKS`.
3. **If `hooks.json` itself does not parse**, Codex loads no hooks at all rather than some — move it
   aside, confirm the CLI answers, then repair it from the copy.
4. **If the CLI fails before the first turn** with `failed to load models cache`, the cache was
   written by a different version. It is a cache: move `~/.codex/models_cache.json` aside and let
   Codex refetch it.

## Step 10 — Verify, with output

Not one of these is optional, and each needs its output shown:

```bash
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
#    The usual failure is not a broken gate but an absent tool — `biome`, `oxlint`, `eslint`,
#    `ruff` — declared and never installed. This prints the same verdict the session tag will:
python3 -c "
import sys; sys.path.insert(0, '$PLUGIN/hooks')
import _config as gp
cmds = (gp.load().get('tooling') or {}).get('commands') or {}
for key, command in cmds.items():
    missing = gp.missing_tool(str(command))
    print(f'{key:12} {command!r:38} ' + (f'MISSING: {missing}' if missing else 'ok'))
"    

# 5. a commit without approval is denied
git commit --allow-empty -m "guardrail check"     # expected: denied, naming <PREFIX>_ALLOW_COMMIT

# 6. the workflows are registered
#    RESTART the session first — the workflow registry is built at startup, so a plugin
#    installed or updated during this session ships workflows this session cannot see.
#    Then, in the new session, ask for the chain: /plan on any L4+ task should reach
#    `graph-powers:ultra-plan`. If it reports `Workflow "graph-powers:ultra-plan" not found`,
#    the plugin is installed but the session predates it — restart again, do not debug.

# 7. the agents resolve, by the name the registry uses
#    Spawn one, in the new session, and read the error rather than guessing:
#      Agent({ subagent_type: "graph-powers:explorer", prompt: "list the files in agents/" })

# 8. Codex answers, and its hooks run — only if Step 9 ran
codex doctor                                      # expected: 0 fail
codex exec --skip-git-repo-check "reply with: ok" # one line per hook, then the answer
#    Every hook line must read `Completed`. `Blocked` means a hook denied the turn — Codex reads
#    exit 2 as a decision, so this is what a wrong path looks like — and `Failed` means one errored
#    and was stepped over. Neither is a finished state; § 9b names the entry behind either. A hook
#    that appears in `/hooks` and in no output line is unapproved: approve it there.
```

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

**Restart the session.** Hooks and skills are read at startup; until then none of this is live.

---

## Step 11 — Report, and stop

```markdown
## Graph Powers — setup complete

**External plugins:** superpowers <version, installed|already present> · impeccable <version, installed|already present>
**Config:** <created | merged> — branch <x>, opt-in prefix <Y>, gates <list>
**CLAUDE.md:** <lines before> → <lines after> · removed: <what> · preserved: <what>
**Rules:** <n> kept · <n> replaced by templates · <n> removed (<why>)
**Authorities:** DESIGN.md <created|improved|skipped, why> · PRODUCT.md <…> · REVIEW.md <…>
**Cleanup:** <n> local copies removed · <n> kept as deliberate overrides (<which, and why>)
**settings.json:** <n> duplicate hooks removed · other keys untouched
**Global:** <installed | already present at version X, skipped> — Claude plugin scope, Codex skills/agents/hooks
**Project:** <what was written here, and nothing else>
**Codex health:** <§ 9b before: n BLOCKS / n RISK> → <after: same, and what was repaired>
**Codex hooks:** <approved by the user in /hooks | pending — guardrails inert until then>
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
