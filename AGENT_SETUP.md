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
| The Claude Code plugin: agents, skills, commands, guardrails, shared references | `~/.claude/settings.json` (`--scope user`) — one install, no copies |
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
2. `~/.claude/plugins/cache/graph-powers/graph-powers/*/` (where Claude Code keeps installed plugins);
3. the `node_modules/graph-powers/` of this project, if it was installed as a dependency;
4. if none exists, **ask**. Do not guess a path.

Call it `$PLUGIN` for the rest of this playbook.

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

**Both are required.** Ten of the fourteen commands call superpowers skills; without it `/plan`,
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

```bash
# Global first, like everything else that is identical per project:
npx impeccable install --providers=claude,codex --scope=global

# Only fall back to --scope=project when the team must get it by cloning the repository.
```

**Order matters.** Run this *before* Step 3 writes the Codex artefacts: impeccable also writes
`.codex/hooks.json`, and although the Graph Powers installer merges rather than overwrites, doing
it in this order means the merge happens once and you can verify it once.

### Keeping them current

Both age independently of this plugin. Add these to whatever the project uses for routine
maintenance, and tell the user they exist:

```bash
npx impeccable update
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

---

## Step 9 — Wire Codex, if the project uses it

```bash
node "$PLUGIN/bin/graph-powers.mjs" --target codex          # global half + project half
```

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
   that plainly rather than letting them assume they are covered.
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
#    run each command from tooling.commands and report its exit code

# 5. a commit without approval is denied
git commit --allow-empty -m "guardrail check"     # expected: denied, naming <PREFIX>_ALLOW_COMMIT
```

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
