# CONTRIBUTING — how to review a change in this repository

A change here reaches every project that installs the plugin. A defect does not affect one
repository — it affects all of them, at the same time, and whoever finds it probably will not
suspect the plugin.

That is why review here is harder than in an ordinary project. It is not bureaucracy: it is the
price of having one copy.

---

## Before looking at the diff

Run the gates. If one fails, the review stops here.

```bash
claude plugin validate .
python3 hooks/test_hooks.py
python3 -c "import ast,glob;[ast.parse(open(f).read()) for f in glob.glob('hooks/*.py')]"
python3 -c "import json,glob;[json.load(open(f)) for f in glob.glob('**/*.json',recursive=True)+glob.glob('.*/*.json')]"
bun bin/graph-powers.mjs --help > /dev/null
git ls-files | wc -l                       # a clone is the artefact; nothing is packed
python3 .github/check_version_bump.py       # a shipped change bumps the version
python3 .github/check_wiring.py             # every agent, skill, workflow and § cited resolves
python3 .github/check_portability.py        # nothing POSIX-only in what an agent executes
bun .github/check_workflows.mjs             # workflow scripts parse, run dry, and name real agents
python3 .github/check_machine_paths.py      # no home directory reached a tracked file
```

On Windows the interpreter is `python` or `py -3`, not `python3` — the Microsoft Store ships a
stub by that name which opens the Store and exits non-zero, so a gate looks like it ran and
did not.

The last one must come back empty: a machine path in the plugin breaks on everyone's machine except
the one it was written on.

---

## The eight questions

In order of what it costs if the answer is wrong.

### 1. Is this generic?

Product name, domain, table, payment provider, branch name, variable prefix, a specific directory
structure — none of it enters. If the change needs one of those, it becomes a field in
`schema/config.schema.json` with a safe default.

**How to check:** read the diff looking for proper nouns. Then ask: does this work in a Python
repository? In a monorepo? In a static site with no tests?

### 2. Did a verifier gain write permission?

Every agent that judges or researches needs `disallowedTools: Write, Edit`.

**The trap:** the `memory:` field injects `Read`, `Write` and `Edit` on top of the `tools:`
allowlist. An agent with `tools: [Read]` and `memory: project` resolves with all three. Adding
`memory:` to an evaluator without adding `disallowedTools` is a silent defect — the description
still says read-only.

**How to check:** for each agent touched, check the `memory:` / `disallowedTools:` pair.

### 3. Is the guardrail still fail-open?

Invalid payload, missing config, JSON with a typo: default and `exit 0`. Never an exception, never a
block caused by its own failure.

**How to check:** look for `json.load`, `open`, `read_text` outside `try/except`. And run:

```bash
echo 'this is not json' | python3 hooks/<hook>.py; echo "exit=$?"
```

It has to exit `0`, with no stack trace. `test_hooks.py` covers this for all eight hooks that read
stdin, so a new hook belongs in that list.

### 4. Does the new guardrail have a negative test — and the positive mirror?

A guardrail never seen denying is an assumption. But a gate that fails the legitimate case is worse:
it trains people to ignore gates.

**How to check:** did `hooks/test_hooks.py` gain both cases? Does the suite exit `0`? Does the
violation case fail if you comment out the blocking line?

### 5. Does it work on every harness?

The same Python file runs under Claude Code, Codex CLI, Cursor and Grok CLI. Claude exports `CLAUDE_PROJECT_DIR`;
Codex and Cursor pass `cwd` in the payload. Grok passes camelCase `toolName` / `toolInput` /
`workspaceRoot` and sets `GROK_WORKSPACE_ROOT`.

**How to check:** does the hook read the payload through `_config` helpers (`bash_command`,
`canonical_tool`, `file_path_from_payload`) rather than `payload["tool_input"]`? Does
`test_hooks.py` cover the change with `harness="codex"` and `harness="grok"`? A guardrail that
resolves the wrong project denies and permits against somebody else's rules.

If the change touches `agents/`, `commands/`, `hooks/hooks.json` or `.claude-plugin/plugin.json`, run
`node codex/install.mjs --project <scratch> --plugin . --dry-run`,
`node cursor/install.mjs --emit-only --dry-run` and
`node grok/install.mjs --emit-only --dry-run` and read what they would generate.

### 6. What invokes this?

A new artefact with no call site is dead weight in the context budget of every session, in every
project. A skill needs routing; an agent needs something that dispatches it; a hook needs a
declaration in `hooks/hooks.json`.

**How to check:** use `rg "<name>" agents skills commands hooks references .claude-plugin`. If it only
appears in its own file, it is an orphan.

### 7. Does this duplicate something?

Extending beats creating a second one. Two skills that do almost the same thing diverge, and the
next person does not know which to call.

**How to check:** does the same subject appear in another file? Does the documentation repeat what
is already in the README? This repository exists because duplicated content diverges — the rule
applies to it too.

### 8. Did any reference come loose?

Every path cited has to exist after the change. That covers `references/` inside skills, scripts,
and paths in prose.

**How to check:**

```bash
python3 - <<'PY'
import os, re, glob
pat = re.compile(r'(?<![\w${./-])(?:references?|scripts|hooks|schema|templates|agents|commands|skills|codex|workflows)/[A-Za-z0-9._/-]+\.(?:md|py|json|mjs|js|txt)')
missing = {}
for f in glob.glob("**/*.md", recursive=True):
    base = os.path.dirname(f)
    for m in set(pat.findall(open(f, encoding="utf-8", errors="replace").read())):
        if any(os.path.exists(p) for p in (m, os.path.join(base, m), os.path.join(base, "..", m), os.path.join(base, "../..", m))):
            continue
        missing.setdefault(m, []).append(f)
for m, files in sorted(missing.items()):
    print(f"DANGLING: {m}  <- {', '.join(sorted(set(files))[:3])}")
PY
```

---

## Signs the change is going the wrong way

- **It grew without removing anything.** A harness that only grows carries expired assumptions.
  Every addition is a good moment to ask what stopped being useful.
- **The justification is "just in case".** A guardrail for a hypothetical scenario, a config field
  no project uses, an agent for work nobody asked for. Wait for the real case.
- **It needed an exception for one project.** If a project needs the plugin to behave differently,
  either it becomes a parameter or it lives in that project's `.claude/` — which beats the plugin by
  precedence.
- **The number has no source.** Ceiling, threshold, budget: say how it was obtained. An invented
  number becomes truth by repetition.
- **It had to be edited in two places.** That is the exact symptom of the problem this repository
  solves.

---

## Changes that need extra attention

| Type | Why | What to demand on top |
|---|---|---|
| **A hook** | Runs in every project, on every tool call, on every harness | Negative and positive tests; proof of fail-open; the Codex payload case |
| **`_config.py`** | The single point where configuration is read; breaks everything at once | Tests with the config missing, invalid, partial, and in the legacy location |
| **`plugin.json`** | Defines the wiring; an error switches guardrails off silently | `claude plugin validate` plus confirming every declared hook exists — and that `codex/install.mjs`, `cursor/install.mjs` and `grok/install.mjs` still generate from it |
| **`codex/*.mjs` · `cursor/*.mjs` · `grok/*.mjs`** | Writes into someone else's files | Proof that a second install produces no duplicates, and that uninstall leaves third-party entries standing |
| **`config.schema.json`** | Public contract; projects already depend on it | A new field with a default; a removed field only with documented migration |
| **Agent frontmatter** | Defines real permissions | Check the resolved tool set, not the declared one |

---

## After approving

The change reaches the projects on the next plugin update (`claude plugin update graph-powers`, plus
`node <clone>/bin/graph-powers.mjs --target all` for the generated Codex, Cursor and Grok sides). There is no gradual rollout: either it is
published or it is not.

If something got through and broke, the path is to revert in the repository and publish again — not
to edit each project's cache. Fixing in one place and propagating is the reason this repository
exists; fixing it in each project is the old model coming back through the side door.
