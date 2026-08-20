# AGENT_SETUP.md — the setup playbook

> **You are the agent reading this.** This file is not documentation for a person to follow; it is
> the procedure you execute, in order, in the repository the session is open in.
>
> A human is watching. **Stop for their approval before every write.** Nothing here is urgent
> enough to justify overwriting something they wrote and cannot get back.

---

## What you are setting up

Graph Powers is a shared harness — agents, skills, commands and guardrails — that installs once and
adapts to each project through one config file. Installing it changes nothing on its own. What
changes things is this playbook: it installs the required external plugins, writes the project's
parameters, **improves the instruction files that already exist** rather than replacing them, and
removes the local copies that currently shadow the plugin.

That last part is the step that decides whether any of this works, and it is the one that needs
judgement. Which is why it is a procedure with approval gates, and not a script.

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
| Codex skills, including the commands Codex reads as skills | `~/.agents/skills/` |
| Codex subagents | `~/.codex/agents/*.toml` |
| Codex guardrails | `~/.codex/hooks.json` |
| Shared references (safety floor, shared context) | `~/.codex/graph-powers/` |
| The machine-wide instruction block | `~/.codex/AGENTS.md` |

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
end — twelve skills copied into five repositories is five copies that drift.

**The only reason to go local instead:** the team must receive the harness by cloning the
repository, on machines where nobody will run an installer. Then use `--scope project`, and accept
that the copy is now yours to keep in sync.

### Check before you install

Global installation is idempotent, and skipping it when it is already there is the difference
between a five-second setup and a needless one:

```bash
# Claude Code — is the plugin already installed for this whole machine?
python3 - <<'CHECK'
import json, os
p = os.path.expanduser("~/.claude/plugins/installed_plugins.json")
d = json.load(open(p)) if os.path.exists(p) else {"plugins": {}}
hits = [(k, i) for k, v in d.get("plugins", {}).items() if k.startswith("graph-powers@")
        for i in v if i.get("scope") == "user"]
print(hits or "not installed globally")
CHECK

# Codex — same question
cat ~/.codex/graph-powers-installed.json 2>/dev/null || echo "not installed globally"
```

**If both say it is already installed at the current version, skip the global half entirely and do
only the project steps.** Say so in your report; do not reinstall to be safe. If the versions
differ, update the global install rather than adding a second copy beside it.

---

## Step 0 — Establish where you are

Report all of this back before touching anything:

```bash
# harnesses present
claude --version 2>/dev/null || echo "claude: not installed"
codex --version  2>/dev/null || echo "codex: not installed"
python3 --version                      # the guardrails are Python stdlib; without it they cannot run

# the repository
git rev-parse --show-toplevel
git branch --show-current
git status --short                     # dirty files are the user's; you do not touch them

# what already exists globally — decides whether the global half runs at all
claude plugin list 2>/dev/null | grep -A3 graph-powers || echo "no global Claude plugin"
cat ~/.codex/graph-powers-installed.json 2>/dev/null || echo "no global Codex install"

# what already exists in this project
ls -a .claude .codex .graph-powers 2>/dev/null
ls .claude/agents .claude/skills .claude/commands .claude/rules 2>/dev/null
test -f CLAUDE.md && wc -l CLAUDE.md
test -f AGENTS.md && wc -l AGENTS.md
test -f .claude/settings.json && echo "settings.json present"
```

Then locate the plugin on this machine, in this order, and **say which one you found**:

1. `$GRAPH_POWERS`, if the variable is set;
2. `~/.claude/plugins/cache/graph-powers/graph-powers/*/` — where Claude Code keeps installed
   plugins. Prefer the highest version directory there;
3. `~/.graph-powers/src/`, or any other clone of `GrupoUS/graph-powers` on this machine;
4. if none exists, install it and say which route you took:

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
export PLUGIN=<the directory you just found>
test -f "$PLUGIN/AGENT_SETUP.md" && echo "PLUGIN=$PLUGIN"   # prove it before going on
```

**Back up before the first write, and show the command you ran:**

```bash
cp -r .claude ".claude.bak-$(date +%Y%m%d-%H%M%S)" 2>/dev/null || true
cp CLAUDE.md "CLAUDE.md.bak-$(date +%Y%m%d-%H%M%S)" 2>/dev/null || true
cp AGENTS.md "AGENTS.md.bak-$(date +%Y%m%d-%H%M%S)" 2>/dev/null || true
```

---

## Step 1 — Install the required external plugins

Graph Powers builds on two external plugins and vendors neither. A copied snapshot of somebody
else's work goes stale and cannot be updated — which is the exact failure this harness exists to
end, one level up.

**Both are required.** Ten of the twelve commands call superpowers skills; without it `/plan`,
`/debug` and `/implement` stop mid-run. `/design` delegates every craft pass to impeccable.

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

**Report back:** which plugins were already present, which you installed, and the version of each.

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
    "level": "autonomous",          // unrecognised commands and cleanup run
    "destructiveFloor": true,       // what git cannot undo is still refused
    "git": { "commit": "ask", "push": "ask", "protectedBranch": "ask" }
  }
}
```

Undo is deleting the file. Prove it is being read with the snippet at the end of this step — from a
repository that has no config of its own, `gp.autonomy()['bashDefault']` should print `allow`.

**Only declare a command whose tool is installed.** `tooling.commands.format` runs after every
edit and `tooling.commands.lint` at every stop; the plugin runs what you wrote and nothing more, so
a command naming a binary that is not on PATH simply never runs. Install them globally — this
harness follows the session into repositories that do not carry them as dependencies:

```bash
bun add -g @biomejs/biome oxlint      # or: npm i -g @biomejs/biome oxlint
biome --version && oxlint --version   # both must answer before you declare them
```

Nothing is hidden if you get it wrong: every session start names what did not resolve
(`NOT INSTALLED: lint needs \`oxlint\``). A command routed through the package manager
(`bun run lint`) is never reported, because the tool is named in the manifest rather than here.

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
    "lint": "oxlint"
  }
}
```

**`format` is `biome format --write`, not `biome check --write`.** `check` runs the linter and the
assists with auto-fix, so it rewrites imports and code shape between two edits of a half-finished
refactor — the hook applies it after *every* Write, and a fix landing mid-edit cascades errors into
the next one. `format` touches whitespace and nothing else. For the same reason `lint` never carries
`--fix` or `--write`: at Stop the job is to report, not to change code the person is about to read.

**`biome.json`** — `biome init` writes a starter; these are the keys that matter
([reference](https://biomejs.dev/reference/configuration/)). Pin `$schema` to the installed version
(`biome --version`) so the editor validates against the rules you actually run:

```json
{
  "$schema": "https://biomejs.dev/schemas/2.5.2/schema.json",
  "vcs": { "enabled": true, "clientKind": "git", "useIgnoreFile": true },
  "files": { "includes": ["**", "!**/node_modules", "!**/dist", "!**/*.md"] },
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

`vcs.useIgnoreFile` is the one people skip and then wonder why the formatter walks `dist/`. Rule
severities are `off`, `info`, `warn`, `error`; `rules.preset` accepts `recommended`, `all` or
`none`, and the domains are a11y, complexity, correctness, nursery, performance, security, style and
suspicious.

**`.oxlintrc.json`** — the file oxlint reads by default
([reference](https://oxc.rs/docs/guide/usage/linter/config-file-reference.html)):

```json
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "ignorePatterns": [
    "**/.claude/**", "**/.claude.bak*/**", "**/.codex/**", "**/.agents/**",
    "**/node_modules/**", "**/dist/**", "**/build/**", "**/.astro/**",
    "**/.next/**", "**/coverage/**", "**/*.min.js"
  ]
}
```

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

**Prove both are wired before moving on**, and show the output — a config that is present but not
being read looks exactly like a clean run:

```bash
biome --version && oxlint --version          # both must answer
biome check --reporter=summary               # names the files it would touch
oxlint --max-warnings 0                      # exit 1 on any finding; 0 means genuinely clean
```

**In CI, use the check-only variants**, which never write and exit non-zero on a finding:
`biome ci` and `oxlint --deny-warnings`. `biome ci` is Biome's own CI mode — same checks as `check`,
no writes.

**If the project already has ESLint or Prettier, do not add these.** Two formatters fighting over
the same file is worse than the one that was already there, and this plugin's contract is to run
what the project declared, not to migrate it.

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
ls .claude/agents .claude/skills .claude/commands 2>/dev/null
ls "$PLUGIN/agents" "$PLUGIN/skills" "$PLUGIN/commands"
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

```bash
node "$PLUGIN/bin/graph-powers.mjs" --target codex          # global half + project half
```

If `$PLUGIN` is a git clone, that same script takes `--update`: it fast-forwards the clone and
reinstalls from it. If it is a Claude Code plugin cache, updates come from
`claude plugin update graph-powers@graph-powers` instead — note the qualified form, because the
bare name is not found and the command exits 0 either way.

It does the two halves in order, and **skips the global half when it is already there at this
version** — so running it in a tenth project costs two files, not thirty.

**Global** (written once for the machine, reused by every project): `~/.codex/hooks.json` merged
with whatever is already there, `~/.agents/skills/`, `~/.codex/agents/*.toml`,
`~/.codex/graph-powers/`, and the block in `~/.codex/AGENTS.md`. Everything it added is recorded in
`~/.codex/graph-powers-installed.json`, so removal is exact.

**Project**: `.codex/rules/` and the delimited block in this repository's `AGENTS.md`. That block
points at `~/.codex/graph-powers/` — a path that is identical on every machine, so the file stays
portable when it is committed.

Then tell the user two things:

1. **Open `/hooks` in Codex and approve the hooks.** Codex tracks trust by hook definition, so a
   change to the file needs approval again. Until they approve, those guardrails do not run — say
   that plainly rather than letting them assume they are covered. The installer will not rewrite
   an unchanged `hooks.json` for exactly this reason, so a routine update costs no re-approval;
   a genuine change to the guardrails does, and it should.
2. **What to gitignore.** Far less than before, because the harness is global now:

   ```gitignore
   .graph-powers/logs/
   AGENT_STOP
   ```

   `.codex/rules/` and the `AGENTS.md` block are the project's own and **should** be committed.

## Step 10 — Verify, with output

Not one of these is optional, and each needs its output shown:

```bash
# 1. no placeholder survived
grep -rn '{{' .claude/ .codex/ CLAUDE.md AGENTS.md 2>/dev/null || echo "no pending placeholders"

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
**Codex hooks:** <approved by the user in /hooks | pending — guardrails inert until then>
**Verification:** <each check, with its result>
**Backup:** <path> — restore with `rm -rf .claude && mv <backup> .claude`
```

**Do not commit anything.** The changes stay in the working tree; the person commits them, having
seen what changed.

---

## Rules that hold for this entire playbook

1. **Stop before every write.** Show what changes, get approval, then write.
2. **Never delete without a `diff` on screen.** The one file that looks identical is the one that
   is not.
3. **Never invent a value.** No path, no command, no domain, no branch name. Read it, or ask.
4. **Preserve every `[HARD]` invariant and every routing row exactly.** Those cannot be
   reconstructed.
5. **A step that could not be completed is reported as not completed.** "I could not verify this"
   and "this is fine" are different answers, and collapsing them is how a broken setup ships
   looking green.
