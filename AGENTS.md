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
6. **The node that judges runs on a strong model, declared.** Explicit `model:`, never inherited. A
   cheap evaluator produces a false positive other nodes "correct", and the origin of the error is
   lost.
7. **Both harnesses, one source.** Anything Codex needs is *generated* from the artefacts that
   already exist for Claude Code (`codex/install.mjs`). A second hand-maintained list is the
   divergence this repository exists to end.

## Gates

There is no build and no type check: the repository is markdown, JSON and standard-library Python.
These are the gates, and all of them pass before anything ships:

```bash
claude plugin validate .                    # manifest and marketplace
python3 hooks/test_hooks.py                 # guardrails, 71 checks in a sandbox
python3 -c "import ast,glob;[ast.parse(open(f).read()) for f in glob.glob('hooks/*.py')]"
python3 -c "import json,glob;[json.load(open(f)) for f in glob.glob('**/*.json',recursive=True)+glob.glob('.*/*.json')]"
node bin/graph-powers.mjs --help > /dev/null
git ls-files | wc -l                       # a clone is the artefact; nothing is packed
python3 .github/check_version_bump.py       # a shipped change bumps the version
```

Before opening a PR, also run the sweep that protects cardinal 2 — it must come back empty:

```bash
grep -rnE '(/home/|/Users/|[A-Za-z]:[\\/])' --include='*.md' --include='*.py' --include='*.json' \
  --include='*.mjs' . | grep -v node_modules | grep -v 'grep -rnE'
```

## Where things live

| Directory | What it is | Who consumes it |
|---|---|---|
| `agents/` | subagents, one `.md` with frontmatter each | Claude Code by `subagent_type`; Codex via generated `.codex/agents/*.toml` |
| `skills/` | skills, one folder with a `SKILL.md` each | `Skill("<name>")`, namespaced as `graph-powers:<name>`; Codex reads the same files |
| `commands/` | commands, exposed as `/<name>` | the user; Codex gets them as generated skills |
| `references/` | plugin-owned shared content: the safety floor, the shared context, audit prompts, the recovery protocol | agents and commands, by explicit read |
| `hooks/` | guardrails in Python plus `_config.py` | declared in `.claude-plugin/plugin.json`; generated into `.codex/hooks.json` |
| `codex/` | the generators for the Codex side | `bin/graph-powers.mjs` |
| `schema/` | the contract for each project's config | editors, and the setup playbook |
| `templates/` | starting points a project copies and adapts | the setup playbook |
| `examples/` | starting configs per stack | people, by copying |
| `DESIGN.md` · `PRODUCT.md` · `REVIEW.md` | **specs, not documentation.** What the host project's counterparts must contain, and how the agent builds or improves them | `AGENT_SETUP.md § 6` |
| `docs/` · `CONTRIBUTING.md` | this plugin's own architecture, audience and review process | people |

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
