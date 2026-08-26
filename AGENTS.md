# Graph Powers — repository rules

This file applies to any agent working in **this** repository (the plugin itself). It is not
distributed to the projects that install the plugin — what travels to them is the content of
`agents/`, `skills/`, `commands/`, `hooks/` and `references/`.

## What this repository is

One copy of a harness, installed in many projects. It exists because five copied harnesses
diverged: 221 files with the same name, only 45 identical, and two security defects fixed in one
project that never reached the other four.

From which follows the rule that governs every other one: **one thing, one place.** If a fix has to
be made in two files of this repository, the repository is reproducing the problem it came to solve.

## Cardinals

1. **Nothing specific to one project enters here.** Product name, staging domain, database table,
   payment provider, branch name, variable prefix — all of that is a parameter, not content. The
   parameter contract is `schema/config.schema.json`; the reader is `hooks/_config.py`.
2. **No absolute paths**, in any file. Hooks resolve the project through the hook payload's `cwd`,
   `${CLAUDE_PROJECT_DIR}`, or the git root; the plugin resolves through `${CLAUDE_PLUGIN_ROOT}`.
   Documentation uses `<org>/<repo>` or a shell variable it defines itself.
3. **Every hook is fail-open.** A missing, unreadable or mistyped config falls back to the defaults;
   it never takes the session down. A guardrail that breaks the work when it has the bug itself
   teaches people to switch guardrails off.
4. **Every artefact has something that invokes it.** An agent no skill or command dispatches, a
   skill no routing mentions, a reference to a file that does not exist — none of it enters. The
   audit that produced this repository found 13 orphans and 32 dangling references.
5. **No verifier writes.** Agents that judge or research declare `disallowedTools: Write, Edit`.
   Watch the `memory:` field, which injects `Read`/`Write`/`Edit` on top of the `tools:` allowlist —
   that is how the `librarian` became write-capable against its own description.
6. **Every node declares its model, and the tier travels.** Explicit `model:` in the frontmatter,
   never inherited: a cheap evaluator produces a false positive other nodes "correct", and the
   origin of the error is lost — and a scout that inherits an expensive one turns the cheap lane
   into the expensive lane without anybody deciding to. That one line is the tier, and the rest
   derives from it: the Codex generator maps the family to this project's `codex.models` slug, and
   the reasoning effort follows the same family.

   Two surfaces do not read it, so both are checked rather than trusted. A `Workflow` `agent()`
   call never opens the agent file — an omitted `model` runs on the session's, which is how an
   `opus`-pinned `frontend-specialist` implemented on `sonnet`; `.github/check_workflows.mjs`
   fails the omission and any upgrade of a light agent. An `Agent` spawn does read it, so a
   `model:` passed at the spawn site only overrides what was already right — do not pass one.
7. **Four harnesses, one source.** Anything Codex, Cursor or Grok needs is *generated* from the
   artefacts that already exist for Claude Code (`codex/install.mjs`, `cursor/install.mjs`,
   `grok/install.mjs`). A second hand-maintained list is the divergence this repository exists
   to end. Cursor has no PermissionRequest or Notification; those events are skipped, not
   rewritten. Grok reads `hooks/hooks.json` unchanged — do not invent `hooks-grok.json`. Payload
   shape differences (camelCase, `run_terminal_command`) are adapted in `_config.py`.

8. **It runs on Linux, macOS and Windows.** The Bash tool maps to whatever shell the user has —
   PowerShell and cmd.exe included — so a POSIX-only construct in a command an agent executes is a
   command that does not run for a third of the people who install this.

   Banned in anything an agent is told to execute: `rm`, `ls`, `cat`, `grep`, `sed`, `awk`, `find`,
   `wc`, `which`, `jq`, `time` and the rest of coreutils · `$(…)` · `/dev/null` · `/tmp` · `~/` ·
   `export VAR=` · inline `VAR=value command` · a trailing `\` continuation. The substitutes are
   the agent's own tools (`Grep`, `Glob`, `Read`) and `python -X utf8 -c`, which the plugin already
   requires and which behaves the same everywhere.

   In Python, the silent half: `glob` returns the platform separator, so `path.startswith("a/")` is
   False on Windows while `os.path.exists` keeps working. Compare with `PurePath(...).as_posix()`,
   never with a string. `HOME` is `USERPROFILE` there; `select.select` takes only sockets;
   `subprocess` without `encoding="utf-8"` decodes with the locale code page; `shlex.split` eats
   backslashes unless you pass `posix=`.

   Why this is a cardinal and not advice: every one of those was live in this repository, and none
   of them raised. The frontmatter reader did not match CRLF, so a Windows clone installed zero
   agents and reported success. The guard on a recursive delete only knew `/`, so `~/.agents/skills`
   was in scope for `rmSync`. The bash approver spoke only POSIX, so the destructive floor did not
   exist under PowerShell. `python3 .github/check_portability.py` is what keeps them gone.

## Gates

There is no build and no type check: the repository is markdown, JSON and standard-library Python.
These are the gates, and all of them pass before anything ships:

```bash
claude plugin validate .                    # manifest and marketplace
python3 hooks/test_hooks.py                 # guardrails in a sandbox
python3 skills/planning/scripts/test_sdd.py # structured plans, TDD and review packaging
python3 skills/skill-improve/scripts/test_run_evals.py # eval runner path and CLI contract
python3 -c "import ast,glob;[ast.parse(open(f).read()) for f in glob.glob('hooks/*.py')]"
python3 -c "import json,glob;[json.load(open(f)) for f in glob.glob('**/*.json',recursive=True)+glob.glob('.*/*.json')]"
bun .github/check_workflows.mjs              # workflow scripts parse, and each name matches its file
python3 .github/check_wiring.py             # every agent, skill, workflow and § cited resolves
python3 .github/test_file_references.py      # negative tests for the live-file reference gate
python3 .github/check_file_references.py     # every live Markdown path resolves
python3 .github/check_portability.py        # nothing POSIX-only in what an agent executes
python3 .github/check_context_budget.py     # what each command costs before it does anything
python3 .github/check_listing_budget.py     # what the plugin costs before anything is invoked
python3 .github/check_machine_paths.py      # no home directory reached a tracked file
python3 .github/check_placeholders.py       # every ${…} is a key the schema declares
bun bin/graph-powers.mjs --help               # the installer still starts under Bun
python3 .github/check_clone.py              # a clone is the artefact; nothing is packed
python3 .github/check_version_bump.py       # a shipped change bumps the version
```

On Windows the interpreter is `python` or `py -3`, not `python3` — there is a Microsoft Store
stub by that name which opens the Store and exits non-zero, so the gates above look like they
ran and did not.

### The linter configuration is not a gate

`ruff.toml`, `pyrightconfig.json`, `.oxlintrc.json` and `biome.json` exist so that the tools a
contributor's editor launches say the same thing on every machine. Left unconfigured they resolve
whatever that machine carries: the same tree reported 190 ruff findings and 737 basedpyright
warnings here while CI was green, almost all of them about code working exactly as designed —
`Any` is the shape of a JSON payload read from stdin, and catching `Exception` is cardinal 3, not
an oversight. Each file carries its reasoning; `pyrightconfig.json` cannot, because the JSON gate
above parses it and comments would fail that parse, so its reasoning is here: `standard` mode, to
keep the three findings worth keeping — an attribute that does not exist, an argument of the wrong
type, a return that contradicts its own annotation.

None of them run in CI. A gate has to be able to fail a pull request; these only stop the editor
from inventing work.

## Where things live

| Directory | What it is | Who consumes it |
|---|---|---|
| `agents/` | subagents, one `.md` with frontmatter each | Claude Code by `subagent_type`; Codex via generated `.codex/agents/*.toml` |
| `skills/` | skills, one folder with a `SKILL.md` each — read `skills/AGENTS.md` first | `Skill("<name>")`, namespaced as `graph-powers:<name>`; Codex reads the same files |
| `commands/` | commands, exposed as `/<name>`. No node: each file is its own entry document, and `.claude/rules/artifacts.md` loads on any edit | the user; Codex gets them as generated skills |
| `references/` | plugin-owned shared content: the safety floor, the execution floor, audit prompts, the recovery protocol, and `shared/` — one file per shared pattern, so a command loads the ones it acts on rather than all 22 KB. No node: `references/shared-context.md` is already the index | agents and commands, by explicit read; the two floors are in force whether or not anyone reads them |
| `hooks/` | `hooks.json` plus guardrails in Python and `_config.py` — read `hooks/AGENTS.md` first | discovered natively by Claude Code and Codex; the clone installer can also merge them into `.codex/hooks.json` |
| `workflows/` | deterministic multi-agent orchestration, one `.js` each | Claude Code, as `graph-powers:<name>`; invoked by `commands/plan.md`. Loaded at session start — an install mid-session is invisible until restart |
| `codex/` | the generators for the Codex side. No node: cardinal 7 is the rule and each generator's docstring is its map | `bin/graph-powers.mjs` |
| `schema/` | the contract for each project's config | editors, and the setup playbook |
| `templates/` | starting points a project copies and adapts | the setup playbook |
| `examples/` | starting configs per stack | people, by copying |
| `DESIGN.md` · `PRODUCT.md` · `REVIEW.md` | **specs, not documentation.** What the host project's counterparts must contain, and how the agent builds or improves them | `AGENT_SETUP.md § 6` |
| `docs/` · `CONTRIBUTING.md` | this plugin's own architecture, audience and review process. No node: prose for people, and `README.md` is its index | people |

### 2026-08-24 Turbo dry-json EPIPE abort cascade

> Added after turbo 2.x panicking on a captured stdout pipe, with Node/bun aborting in sympathy.

**Problem:** Agents ran `turbo run test --dry=json` through Bash. Turbo panicked, Node forwarded
SIGABRT, bun aborted. Three coredumps. No tests ran.
**Cause:** Rust `println!` panics on EPIPE. The Bash tool is a pipe. `turbo/bin/turbo` then
`process.kill(pid, signal)`.
**Solution:** Hook denies the Bash form. Script `skills/debugger/scripts/turbo_dry_json.py`
writes JSON to `.graph-powers/cache/` and prints the path. Anti-pattern 37 on the debugger
catalogue. Hosts inherit the rule via `templates/rules/stability.md`.

## When adding something

Answer before writing, and leave the answer in the PR:

- **What invokes this?** Without a concrete call site, it does not enter.
- **Does it work in a repository I have never seen?** If it depends on a convention, the convention
  becomes a field in the schema.
- **What already exists that covers part of this?** Extending beats creating a second one.
- **How is it proven to work?** A guardrail without a negative test is an assumption with syntax.

## Git

Work on a branch, PR to `main`, and never commit or push without an explicit request from whoever
is reviewing. This repository distributes the gates that impose that rule on other projects;
violating it here would be the most expensive contradiction available.

## The three specs

`DESIGN.md`, `PRODUCT.md` and `REVIEW.md` at the root are the most easily misread files here. They
are **not** documentation about Graph Powers — they are the specifications the agent applies to the
project the plugin is installed into. Anything written in them lands in somebody else's repository.

So they hold: required sections, how to source each one from the target repository, how to improve
an existing counterpart without destroying decisions, and a quality bar. They do not hold: opinions
about this plugin, or content the host project's file is supposed to contain (that is invented
detail — every value in the generated file traces back to that repository or to its owner).

This plugin's own equivalents live in `docs/ARCHITECTURE.md`, `docs/AUDIENCE.md` and
`CONTRIBUTING.md`.

<!-- graph-powers:start -->
## Graph Powers

This machine runs the Graph Powers harness, installed once and shared by every project.

Three files carry everything else:

- `~/.codex/graph-powers/shared-context.md` — an index of the shared patterns, one file each under
  `~/.codex/graph-powers/shared/`: config loader, quality gates, complexity routing, agent matrix,
  spawn patterns, and the rest. Read the index, then only the fragments the task needs.
- `~/.codex/graph-powers/safety-floor.md` — the invariants that hold regardless of the task: git and
  outward-facing actions, tenant and personal data, irreversible operations, secrets, tooling,
  scope, completion claims, accessibility.
- `~/.codex/graph-powers/execution-floor.md` — how the work is coordinated, in force from the first turn:
  delegation is required above L3 and refused below it, read-only agents go to the background in
  a single message, one writer per file, and the seven-section contract every spawned prompt
  carries. On Codex nothing spawns on its own — the prompt has to say so. Read it before
  spawning anything.

**What is global and what is this project's.** The harness itself — skills, subagents,
commands, guardrails — is installed once for the whole machine, because it is identical
everywhere. What belongs to this repository and nothing else lives here:

- `.graph-powers/config.json` — the branch, the gate commands, the paths, the opt-in prefix
- `.codex/rules/` and `.claude/rules/` — this project's domain rules
- `DESIGN.md`, `PRODUCT.md`, `REVIEW.md` — its design, product and review authorities

The guardrails are what make one global copy correct rather than sloppy: they read **this**
project's config at runtime, so the same files enforce a different work branch and a different
opt-in key in every repository.

Read the config; never assume it. A denied command is the rule working, not a bug to route
around: it names the environment variable that releases it, and a person sets that variable,
in the turn they approved it.
<!-- graph-powers:end -->
