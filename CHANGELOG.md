# Changelog

## 1.4.0 — the harness answers a sentence, and a preference survives the clone

### Changed — 24 descriptions rewritten, because that is where automatic invocation lives

The commands and skills were already model-invocable; Claude Code merged commands into skills, and
every one of them has been in the model's listing all along. What was missing is that the listing
entry is the *only* text a plain sentence is matched against, and all 24 were written as
documentation — explaining what an artefact is, to a reader who had already typed its name.

They now split by the load they carry. The 12 **commands** are the intent surface: each one leads
with what happens, then the sentences a person actually types, then a "do not use for" clause
naming the neighbouring command. The 12 **skills** are the knowledge surface, loaded by a command
that already routed or by a model already inside the domain, and they were cut to their domain and
their nearest neighbour. Commands went 3,238 → 5,706 characters; skills went 7,514 → 3,625.

Nothing was flagged wrong on the way in: zero `disable-model-invocation`, zero malformed
frontmatter, 24 of 24 parsing. The defect was entirely in what the text said.

### Added — `check_listing_budget.py`, because the ceiling is shared and invisible

Claude Code budgets the skill listing at roughly 1% of the context window across *every* source on
the machine, and on overflow it drops descriptions rather than failing — starting with whatever is
invoked least. Three of this plugin's own skills were measured in that state: listed by name,
matching nothing.

That makes growth here a cost paid by somebody else's skill, so it is now a gate. The plugin
measured 10,752 characters before this release; the ceiling is that number and the current total is
9,331, leaving the headroom visible instead of spendable in silence. The one setting that raises the
budget cannot ship from a plugin — only `agent` and `subagentStatusLine` are honoured from a
plugin's `settings.json` — so `AGENT_SETUP.md` now documents `skillListingBudgetFraction`, and the
two cheaper `skillOverrides` moves to try before spending context on it.

### Fixed — a hand-written workflow script failed at parse, and nothing could have caught it

```
Error: Invalid workflow script: Script parse error: Unexpected token (156:63)
0 lines per rule. Note: this project uses `globs:` not `paths:` in frontmatter —
                                           ^
```

The caret is on a backtick and the line is prose. A workflow script is mostly agent prompts, prompts
are template literals, and a prompt about code is dense with backticks — so the first one inside the
prose ends the literal and the rest is parsed as JavaScript. The script reaches the runtime as text,
so the failure lands after it is fully written and before anything runs.

`check_workflows.mjs` has always performed exactly the right check — it applies the runtime's own
wrapper, because these scripts use a top-level `return` and `node --check` rejects correct ones, then
executes the body against stubbed `agent()`, `parallel()` and `pipeline()`. It was reachable only for
`workflows/*.js`, which is the one case that never has this problem, because CI already gates it.

It now takes file arguments: `node .github/check_workflows.mjs <script.js>` parses and dry-runs any
script before it is handed to `Workflow`. Explicit-path mode drops the two checks that only mean
something for a shipped workflow — filename/`meta.name` agreement and the refuses-empty-args guard —
and keeps the parse and the dry run, which is what actually breaks. Since `Workflow` persists every
inline script and returns its `scriptPath`, this is also the iteration loop: edit that file, re-check,
re-invoke by path.

`references/shared/130-workflow-authoring.md` carries the rule, cited from `agent-orchestration`
(where fan-out is decided) and `harness-audit` Phase 5 (whose own prompt escapes its backticks
correctly, and is the pattern the failing script imitated without the escapes). The quoting table
leads with the cheapest fix: drop the backticks. `paths:` reads the same to an agent as `` `paths:` ``
and cannot break the parse.

The `globs:` claim inside that failed prompt came from `000-config-loader.md`, which said Tier 2
rules auto-load via `globs:` frontmatter until this release corrected it to `paths:`. The script was
repeating the plugin's own error back to it.

### Fixed — `/verify` advertised a mechanism it never read

`000-config-loader.md` has listed `${rulesDir}/verify-supplements.md` as "loaded by `/verify`" for
as long as the table has existed. `commands/verify.md` never read it — the string appears in that one
table row and nowhere else in the plugin. So a project whose real gate set does not fit the four rows
`/verify` knows about had a documented place to put the rest, and putting it there did nothing.

This repository is the case in point: `tooling.commands` accepts seven named keys, none of which is
"validate the plugin manifest" or "check nothing POSIX-only entered a command an agent runs", so it
declares one gate out of thirteen. `/verify` ran that one and printed a clean line. `§ 0` now reads
the supplement and runs what it declares, and `.claude/rules/verify-supplements.md` carries this
repository's thirteen with what each failure means.

The same reference said Tier 2 rules auto-load via `globs:` frontmatter. The field is `paths:`, and
the difference is not cosmetic: a rule with no `paths:` field loads unconditionally into every
session at `.claude/CLAUDE.md` priority, so the wrong field name does not fail loudly — it silently
converts a scoped rule into an always-on one, which is the opposite of what scoping it was for. The
note now says so, and the new supplement carries a narrow `paths:` for exactly that reason.

### Added — how to configure Biome and oxlint so the lint gate checks something

`AGENT_SETUP.md` told installers to install both tools and declare the commands, and stopped there. A
declared linter with no config file runs, exits 0 and reports nothing, which is the worst possible
gate because the line reads as covered. Step 3 now carries both config files against the current
official references, the division of labour between them — Biome formats, oxlint is the lint gate,
because both linting the same rules yields two diagnostics per finding — and the reason
`tooling.commands.format` must be `biome format --write` rather than `biome check --write`: `check`
auto-fixes, the hook runs it after every Write, and a fix landing inside a half-finished refactor
cascades into the next edit. Also the CI-only variants, `biome ci` and `oxlint --deny-warnings`, and
the instruction not to add either to a project already on ESLint or Prettier.

### Fixed — a project that mandates `bun` could not run `bunx`

`autonomy.allowPackageManagers` compared the literal first word of the command against the list, so
`bunx` under a `["bun"]` declaration was refused — bun's own package runner, the correct tool in
that project, denied by the rule that exists to keep the project on bun. The refusal even read
"`bunx` is not one of them" with `bun` sitting in the same sentence, which looks like a broken
guardrail rather than an applied rule.

The allowlist now names families. A command resolves to the manager that ships it — `bunx`→`bun`,
`npx`→`npm`, `pnpx`→`pnpm`, `uvx`→`uv`, `pipx`→`pip` — and the family is what gets checked, so
`["bun"]` admits `bunx` and still refuses `npx`. Resolution is one-directional: declaring `npx` does
not hand over `npm`, because someone who asked for one-off execution did not ask for the lockfile to
be rewritten. What the setting protects is unchanged — running a package through the manager the
project already chose forks nothing.

Every real project on the author's machine was carrying the workaround, `["bun", "bunx"]`, and so
was the test fixture — which is precisely why CI never saw it. The fixture now declares `["bun"]`,
the form the fix enables, and the explicit two-entry form is covered separately so the repositories
already carrying it are not punished for the plugin's defect.

### Fixed — the plugin told agents to run `npx`, then denied it

`AGENT_SETUP.md`, `README.md` and `commands/design.md` all hardcoded `npx impeccable install`. In
any project standardised on something else that instruction is refused by this plugin's own
`smart_bash_approver` — the harness firing its guardrail at its own documentation, and `/design`
losing its craft passes to it. A package manager is a project's choice, which cardinal 1 says makes
it a parameter; all three now resolve the runner from `tooling.packageManager` and give the mapping.

The same commands were missing `--yes`. With `--providers` and `--scope` supplied the installer is
still interactive, so a command an agent runs unattended stopped on a prompt nobody was going to
answer. `AGENT_SETUP.md` also now records where the Codex half actually lands —
`~/.agents/skills/impeccable`, the shared skills directory, not `~/.codex/skills` — and how to
verify the hooks merge left every other tool's entries standing.

### Added — a user-scope config, so autonomy stops being re-decided per clone

`_config.py` read one file: the project's. Everything in it was therefore per repository, including
`autonomy`, which is the block deciding whether a session feels like work or like clicking Approve.
A person who had already turned that off met the same prompt flood in the next clone, and it read
as the setting having stopped working when it had simply never been asked.

`~/.graph-powers/config.json` now answers it once, resolved `defaults < user < project`. Three
limits keep the layer safe rather than merely convenient:

- Only `autonomy`, `graphGuardrails`, `protectedFiles` and `autoUpdate` are read from it. The rest
  of the schema describes a repository, and a `paths.frontendRoot` written once at home is wrong
  everywhere except where it was meant.
- `git` never crosses. `optInPrefix` is per repository so an approval typed in one cannot release
  the same gate in another, and a home-directory prefix would delete that isolation for every
  project at once.
- `autonomy` is owned whole by whichever scope declares it. Field-merging a user's
  `git.commit: ask` under a project's `level: autonomous` would leave a repository that asked to run
  unattended stopping at every commit — its own declaration silently half-applied.

### Fixed — the test suite was not hermetic, and the new layer proved it

`test_hooks.py` invoked every hook with the real home directory, so once hooks began reading
`~/.graph-powers/config.json` the suite inherited whatever the person running it had set. It did not
fail honestly either: it failed as six unrelated cases about guarded defaults. Every invocation now
runs against an empty temporary home unless a case sets one deliberately — the same isolation the
two-project cases have always proved, one level up.

Six new cases cover the layer: it reaches a project that declares nothing, it is absent when the
user file is, the project outranks it, a user-level `optInPrefix` does not release the commit gate,
and a malformed user file still exits 0 with the project's own config deciding.

### Changed — 12 agent descriptions are routing rules now

The field that drives automatic delegation read as a job title on all 12. Each now opens with the
action cue the documentation calls for, states whether it writes or only reports, and names the
neighbouring agent that owns the adjacent job — so two agents sharing vocabulary stop splitting one
task between them.

## 1.3.1 — the Codex install stops accumulating

### Fixed — the Codex escalation path named an agent that does not exist

Eleven citations of `codex:rescue`, in the escalation path of `/debug` (six), `/implement` (two)
and three shared fragments. The plugin that provides it ships `agents/codex-rescue.md`, so the
address is `codex:codex-rescue`; `codex:rescue` resolves to nothing. Two of the eleven called it a
*skill*, and that plugin's skills are `codex-cli-runtime`, `codex-result-handling` and
`gpt-5-4-prompting` — no `rescue` among them either. So `/debug`'s documented route out of a stuck
fix, and `/implement --codex`, pointed at nothing, and the failure is the quiet kind: the model
reads the instruction, finds no such agent, and continues with less than it thinks it has.

Eight of the eleven predate this release. The other three were created *by* it — the bare-to-
namespaced migration corrected every `graph-powers:` name and copied the wrong `codex:` one into
three new `references/shared/` fragments. A migration that fixes one namespace and propagates
another is worse than none, because the corrected neighbours make the wrong one look reviewed.

Alongside it, `agent-handoff-contracts.md:89` listed `code-reviewer` among the reviewer agents.
This plugin has never shipped one. It now names `graph-powers:evaluator` and
`graph-powers:security-reviewer`, which it does ship.

**The gate that should have caught it now does.** `check_wiring.py` skipped every namespaced
reference on the stated principle that another plugin's tree cannot be opened in CI. True, and it
does not follow that nothing can be checked: the fix is not to verify the dependency but to
**declare** it. `EXTERNAL_ROUTES` lists every external agent and skill this harness routes to, each
checked by hand against the plugin that ships it, and a namespaced name outside the set fails.

Two details decide whether a gate like this survives. It matches only namespaces already declared,
not the shape `<word>:<word>` — the shape alone flagged `path:line`, `file:line`,
`client:visible`, `main:main` and `skipped:true`, sixty-eight of them, which is how a check ends up
with `|| true` after it. And four superpowers skills were nearly declared from memory —
`condition-based-waiting`, `defense-in-depth`, `root-cause-tracing`, `webapp-testing` — none of
which exists in superpowers 6.3.0. A declaration is worth something only if somebody opened the
other plugin before writing the line.

### Verified — every agent this harness routes to actually runs

Not inferred from frontmatter. Each of the twelve was spawned with a probe that forces a real tool
call and returns evidence, plus `codex:codex-rescue` at its corrected address. Twelve of twelve
returned; the Codex side generates twelve TOMLs that all parse. Two observations worth keeping:
`explorer` and `performance-optimizer` answered with Bash rather than Glob/Grep, because a
session-level directive to prefer shell tools reaches subagents too — which silently defeats the
Windows-safe path `/debug § 2.2` prescribes, where `find` is a different program. And
`mobile-developer` has no call site in any command or skill; it is reachable only through
`workflows/*.js`, and only when `paths.mobileRoot` is set.

### Fixed — the spawn ceiling had become a session-lifetime quota

Found the way these are supposed to be found: by the guardrail firing on work that was not what it
guards. A `/pr-review` fan-out of three review agents got one through and two denied. The command
then ran one path where it declares three, and nothing in its output would have said so — a
skipped path reading as a passed path is the exact failure `/pr-review § 8` promises not to have.

G2 counted `Agent` spawns from the start of the session and never let go of one. Its own docstring
says what it is for — *"a runaway fan-out burns a budget in one afternoon"* — and a runaway fan-out
is a burst. A session that lives all day is not one. Counted cumulatively the ceiling stopped
measuring bursts and started measuring session age: once a long session crossed 25, it refused the
**first** spawn of every unrelated later task for the rest of the day. Both ceilings now count
inside `graphGuardrails.spawnWindowMinutes` (default 60).

Two smaller defects fell out of the same file:

**A refused spawn was charged for.** `bump()` incremented, then compared, so a denial consumed a
slot it never used and every retry pushed the number higher. The message read `27 agent spawns` in
a session where 25 ran and 2 were refused. The old behaviour had a comment defending it — *without
it a caller retries forever at no cost* — which does not hold: a refused retry never ran, and the
spawns that did run are still inside the window, so the refusal repeats on its own. All the charge
bought was a number that described nothing.

**One specialist, two counters.** G3 keyed on the `subagent_type` verbatim, so a plugin agent and
the same agent named without its prefix were counted separately and the ceiling granted double the
rounds. This repository's own session log carried `agent:evaluator: 1` beside the prefixed key at
3 while the namespacing migration was in flight. The key is now normalised on the last segment.

`hooks/test_hooks.py` goes from 166 checks to 173: the window (aged events do not count, fresh ones
do), the migration (a counter written before timestamps existed cannot be placed in a window, so it
stands down rather than denying on evidence that is not there), the uncharged refusal, and the two
spellings sharing one counter.


### Fixed — every guardrail on the Codex side was registered twice

Found by updating a real machine rather than a fixture. `~/.codex/hooks.json` pointed all twelve
hooks at a scratch clone under `/tmp`, left by a session weeks earlier — a directory that survives
until the next reboot clears it, at which point every Codex guardrail silently stops existing.

Re-installing from a stable plugin root did not repair it, it doubled it. `mergeHooks` recognised
its own previous entries by exact command string, and the string contains the plugin root, so the
same hook installed from a different directory read as a stranger's and was kept. The result was
twenty-four registrations: each guardrail running once from the current code and once from a
version-old copy in a doomed directory.

The merge now recognises a command by the manifest template with the root wildcarded, so a hook
this plugin wrote is replaced wherever it was written from, and a third party's hook — which never
matches a template of ours — still survives untouched.

### Fixed — the diagnosis, twice, and then the actual cause

Every `graph-powers:*` spawn was refused for most of this release's development, and the first two
explanations here were wrong. Recording both, because the wrong ones looked exactly as convincing.

**First wrong answer: a stale session.** The message `Unknown subagent_type 'graph-powers:explorer'.
Valid: … explorer …` was read as a registry snapshot older than the running plugin, and a restart
was prescribed in three files. One command falsified it: the same spawn in a fresh process —
`claude -p "spawn subagent_type 'graph-powers:explorer' …"` — returned the identical refusal. A
fresh process carries a fresh registry, so nothing was stale.

**Second wrong answer: frontmatter.** `security-reviewer` and `skill-improver` were missing from
that refusal's list, and a YAML block sequence in their `disallowedTools` was blamed. The CLI's own
registry listed both while they still carried the block form. They were missing from the *other*
list, which is not the CLI's.

**The cause.** A `PreToolUse` hook matching `Agent`, holding its own allowlist, denying before the
call reached the registry. The allowlist was built by scanning `.claude/agents/` plus a hardcoded
baseline — and a plugin's agents are in neither, because they live in the plugin and are addressed
`<plugin>:<agent>`. Two validators in series, opposite verdicts, no name satisfying both. The
phantom entries in that list — `explorer-agent`, `orchestrator`, `general` — were the tell: names
that exist in no file anywhere on the machine.

`README.md` now carries both failures under **When something refuses and it is not this plugin**,
with the evidence that separates a hook denial from a CLI one — the CLI says `Agent type 'X' not
found. Available agents: …` and lists plugin agents namespaced; a `Valid:` phrasing listing bare
names is somebody's hook. It includes the discovery snippet a hook needs to see plugin agents, and
the second failure of the same family: a linter handed a JSON-only batch, exiting non-zero with
"No files found to lint", counted as a lint error and blocking every stop.

Nothing in the plugin was at fault for either. It is documented here because the plugin is what gets
blamed, and because the fix is three lines in a file most people have never opened.

### Added — an agent name that does not resolve is a route, not the end of the work

`/plan` has always treated an unresolved *workflow* name as a route: it says which of three things
happened and runs the phases by hand. Agents had no equivalent, so a spawn that failed to resolve
ended the work instead of redirecting it — measured in this session, where every
`graph-powers:*` spawn was refused and each attempt simply stopped.

`030-agent-assignment-matrix.md` now carries the rule, and it distinguishes the two failures because
they have opposite causes: a bare name is a defect in the caller, and `Unknown subagent_type
'graph-powers:explorer'` does not come from the CLI at all. Neither is a reason to stop. Fall back to `general-purpose` with the plugin agent's contract restated in the
prompt, or to the main thread when the subagent bought only isolation — then say which happened.

The fallback is deliberately not offered for write-capable agents. `graph-powers:debugger` and
`graph-powers:frontend-specialist` edit files, and standing in for them with a general agent
discards the disjoint-file ownership the wave grouping depends on. And when a read-only agent is
replaced this way, the report has to say so: the read-only promise moved from frontmatter into a
prompt, which is weaker, and the reader needs to know.

### Fixed — every agent this plugin prescribed was named in a way the registry rejects

`references/shared/030-agent-assignment-matrix.md` closed with `Use subagent_type: "explorer"`, and
the twelve commands and the planning skills copied it. The agents ship inside a plugin, so the
registry knows them as `graph-powers:explorer`. The bare name does not resolve, and the failure says
so in a sentence that contains the answer:

    Agent type 'explorer' not found. Available agents: ... graph-powers:explorer ...

Twenty-one literal prescriptions carried the bare form, plus the `subagent_type` column of
`references/audit-agent-prompts.md` — and an audit that decompiled the CLI's own loader found 175
more the literal check could never see: role labels in fenced blocks, table cells, and prose reading
"spawn `explorer`". Thirty-four files in all; every one is namespaced now, and the gate checks both
shapes. It skips the root specs, the rubrics, the prompt-engineering references and `workflows/*.js`,
where a bare name is the artefact's own name rather than a dispatch — `PLUGIN_AGENTS` holds bare
names precisely so `AG()` can add the namespace.

Two more from that audit. `agents/mobile-developer.md` carried `triggers:` as a YAML flow sequence,
the only one in the tree, which `codex/lib.mjs` comma-splits without stripping brackets or quotes —
every element arrived corrupted on the Codex install path. Nothing read the field, so it is gone.
And `commands/implement.md` listed `librarian` under skill routing; there is no `skills/librarian/`,
so a model obeying the heading called `Skill("librarian")` and got nothing. This was the cause of the workflow
spawn failure recorded in 1.3.0 as unexplained: `ultra-plan` used the bare name because this matrix
told it to.

`check_wiring.py` did not catch it, and could not: `agents/explorer.md` exists and the reference
resolved. The path was right and the name was wrong, which is the one combination a path check
cannot see. It now refuses a bare plugin-agent name in any prescribed `subagent_type` — a name that
is not one of ours still passes, because a project may route to its own agent.

The mirrored failure has a different cause, so `AGENT_SETUP.md` Step 10 now carries both:

    Unknown subagent_type 'graph-powers:explorer'. Valid: ... explorer ...

is **not the CLI**. Its own refusal reads `Agent type 'X' not found. Available agents: ...`. A
`Valid:` phrasing listing bare names is a `PreToolUse` hook matching `Agent`, denying from an
allowlist built by scanning `.claude/agents/` — which never contains a plugin's agents, because
those live in the plugin and are addressed `<plugin>:<agent>`.

This release first shipped the wrong diagnosis for that message: a stale session, fixed by
restarting. It is not, and restarting does not help. The evidence that settles it costs one command
— run the same spawn in a fresh process, `claude -p "spawn subagent_type 'graph-powers:explorer' …"`.
A fresh process carries a fresh registry, so the same refusal means nothing was stale. That check is
now in Step 10 rather than the guess.

### Added — a declared linter that is not installed says so, instead of doing nothing

`ultracite.py` runs `tooling.commands.format` after every edit and `tooling.commands.lint` at every
stop. It runs the command the project declared and nothing more — deliberately, because an earlier
version shelled out to `biome` and `oxlint` unconditionally and rewrote files in repositories that
had chosen Prettier.

What that left behind: if the declared command names a tool that is not on PATH, the run raised
`FileNotFoundError` into an `except` that swallowed it. A session could edit files for hours
believing they were being formatted. The session tag printed `gates: lint+test` either way, which is
the exact failure `session_context.py` already had a comment about — *a line that reads as covered
and never runs* — one level further down.

So the question is now answered once, in `_config.py`, for every caller:

    | NOT INSTALLED: lint needs `oxlint`, format needs `biome` — install globally or these never run

A gate whose tool is absent is dropped from the gate list rather than listed as if it ran.
`ultracite.py` checks before running instead of catching afterwards, and still never blocks a stop
over a missing tool. The install is global on purpose — a session follows you into repositories that
do not carry these as dependencies:

    bun add -g @biomejs/biome oxlint      # or: npm i -g @biomejs/biome oxlint

A command routed through the package manager (`bun run lint`) is never reported: the tool is named
in the project's manifest rather than in the command, and a warning that guesses is worse than
none. The requirement is now written where somebody configuring this will meet it — the schema
descriptions, `README.md`, `AGENT_SETUP.md` Steps 3 and 10, and the guardrails index.

### Fixed — under Codex, the session tag described the wrong repository

`session_context.py` read the payload and then resolved the project without it. Codex CLI does not
export `CLAUDE_PROJECT_DIR`; it puts the working directory in the payload, so the hook fell through
to the git root of wherever its process started. The project name, the branch and the gate list all
belonged to somebody else's checkout. `.claude/rules/hooks.md` has required passing the payload
since it was written; this was the one hook that did not, and the suite now asserts it.

`hooks/test_hooks.py` goes from 154 checks to 166.

### Fixed — the portability gate read one line at a time, and calls are not one line

`subprocess.run(...)` is routinely written across four lines. Every check in
`.github/check_portability.py` matched a single line, so a call with the opening paren on one line
and `text=True` on the next was invisible: the gate reported zero while three real instances sat in
the tree — `.github/check_clone.py`, and two in `skills/debugger/scripts/fetch_logs.py`. Each
decodes subprocess output with the machine's locale code page, which is how a non-ASCII filename
stops matching on a Windows checkout. The scanner now reads a call whole, however many lines it
spans, and the three are fixed.

### Fixed — `strip()` used as if it removed a suffix, for the second time

`fetch_logs.py` resolved the repository slug with `.rstrip(".git")`. `strip` takes a **set of
characters**, so it keeps eating: `owner/my-agent.git` becomes `owner/my-agen`, and every log
lookup for that repository silently queries one that does not exist. `owner/digit.git` becomes
`owner/d`.

This is the same defect that made `protect_files.py` use `.lstrip("./")` and quietly unprotect every
declared dotfile. Twice is a pattern, so the gate now refuses it — but only for a literal shaped
like an affix: `"\n"` and `"> "` are genuine character sets, and a gate that reports those is a gate
somebody switches off.

### Fixed — `--force` did nothing

`install()` and `installGlobal()` have honoured a `force` option since they were written. The argv
parser never set it, so `--force` on the command line was ignored, including in the CI fixture whose
second install was proving an idempotence it had not exercised. `README.md` has documented the flag
the whole time.

It matters beyond tidiness: a global install whose plugin root moved is skipped as "already at this
version", so without `--force` there was no way to repair one short of a version bump.

### Added — a CI step for the scenario that produced both

`.github/workflows/ci.yml` installs from one root, then from a second root at a higher version, then
again with `--force` at the same version, and asserts three things: no command points at the old
root, no guardrail is registered more than once, and the third party's hook is still there.

## 1.3.0 — the chain ships, and the bash gate asks about the right things

### Added — the plan → build → verify chain

Three workflows now ship with the plugin (`workflows/`), and Claude Code registers them as
`graph-powers:ultra-plan`, `graph-powers:ultra-build` and `graph-powers:ultra-verify`.

`/plan` runs them end to end and stops **once**: at the only edge `git revert` cannot undo cheaply,
which is committing to a plan before any code exists. Research fans out, the plan is scored against
calibration anchors in code rather than by self-report, implementation runs in waves of disjoint
files, and verification refutes from several angles at once before looping on what it found.

They existed before this release — in two projects, copied, and already diverged: 287 lines of diff
between the two copies of one of them, 99 in another. That is the exact failure this repository was
created to end, reproduced in the most expensive layer. Worse, the plugin already *depended* on one
of the copies: `commands/plan.md` promised an `approved` flag and a `splitByFileOwnership` re-slice
that only one of the two ever had, and shipped neither.

Everything specific to a repository was lifted out into config. A workflow script cannot read a file
— its scope holds six names and none of them is a filesystem — so the contract arrives as `args`,
passed by `/plan` or read by one cheap agent when a workflow is invoked on its own.

### Changed — the shared context is seventeen files, and a command loads the ones it reads

`references/shared-context.md` was 22 KB and every command opened by loading all of it. `/plan` used
one section. `/delegate` and `/recover` used none, and paid the full 22 KB anyway — for `/recover`
that was 88 % of everything it loaded.

Each `## Section N` is now its own file under `references/shared/`, extracted byte for byte with its
heading, so the words a citation lands on are unchanged. Each command's header names only what it
acts on. **The shared layer went from 267,816 bytes across the twelve commands to 80,940 — 69.8 %
less** — the sum, per command, of the `references/shared*` files it cites, on a worktree of
`750d2ea` and on this tree. Against a worktree of the pre-split tree measured with the same script, what the twelve
commands load on **every** invocation fell from 523,746 bytes to 289,512 — **44.7 % less** — and the
worst case, every conditional branch taken at once, fell 31 %.

Deciding what each command *needs* could not be done by grepping citations, because a citation is
not a need and this repository had both kinds of error: sections named in a header and never used,
and sections used without ever being named. Twelve agents read one command each against the whole
file. Their disagreements were the useful part, and are recorded here rather than smoothed over:

- **§ 5 (Tool Usage) had no consumer at all.** Its one inbound citation was `/debug`'s AutoResearch
  line, which said § 5 while meaning § 10. Meanwhile `/research` restated a chunk of it inline. The
  command now loads the fragment for *which* tool and keeps only *how* to drive it — the half the
  table never had.
- **§ 11 (Guardrails Index) indexed no guardrails.** It listed eight rule files and not one of the
  twelve hooks that actually deny. An index that omits everything enforced is worse than none:
  somebody looking up "what stops me here" found the wrong list. It now separates what denies in
  code from what is convention, and `/prime` and `harness-audit` read it.
- **§ 9 claimed `/verify` as its consumer**, which returns three literal words and has no matrix.
  **§ 11.5 claimed `/verify § 3`**, which has no code-graph step. Both now name who really reads
  them.
- **§ 1.5's apply-at list named `/design`, `/evolve` and `/verify`**, none of which invoke the skill
  it describes. Left as a finding rather than papered over by adding the fragment to their headers:
  that would launder a behavioural gap into a reading assignment.

`shared-context.md` stays at its path as a one-page index — `codex/install.mjs` writes it into the
generated `AGENTS.md`, and installed copies of older versions still point at it. What they find is
a map, not a 404 and not 22 KB.

### Fixed — three artefacts that looked orphaned, and one that was miswired

`mobile-developer` is reachable again: the three workflows route to it, gated on `paths.mobileRoot`.
`verification` — the browser-QA specialist, read-only, that nothing had ever spawned — is now the
Evidence Collector in the debugging packs, which is the job it was written for.
`agent-orchestration` is **not** deleted: a skill is invoked by its description as well as by
`Skill()`, and its description is a routing trigger. What it lacked was an edge to `/delegate`, the
command that owns the delegation contract. `second-opinion` is invoked by a person running
`claude -p`, by design; it is now named at the moment it helps — recovery Step 4, where the thread
has spent three attempts justifying one reading and needs a session that never saw it.

### Added — `chain` in the config contract

`schema/config.schema.json` gains one group. Its arrays are the reason it is a group and not a
handful of booleans: `invariants` (code that looks redundant and must never be "simplified" away — a
tenant filter, a PII gate, an idempotency guard), `lenses` (extra review angles), `contractGates`
(commands that run only when a given surface changed), `hardRules`, `domainSkills`, `surfaces`.

The plugin supplies the mechanism; a project supplies the content. Without these, adopting the
plugin would cost a repository the review coverage it already had, which is not an upgrade.

Also new: `paths.mobileRoot` (absent removes `mobile-developer` from every routing enum — an agent
with nothing to work on is worse than no agent), `tooling.commands.deadCode` and
`tooling.commands.renderHealth`, and three ceilings in `graphGuardrails` that were previously
constants inside the workflows.

### Fixed — one writer per file was armed and disarmed at the same time

`graph_guardrails.py` has always refused a write outside `.graph-powers/logs/write-lease.json`. No
code ever wrote that file, so the check stood down every time. `/plan` Step 4.2 now writes it, from
the disjoint file sets `ultra-build` already computes to slice its waves.

### Fixed — `subagent_type` could come from generated text

Two schemas in the verification workflow typed `agent` as a bare string, so whatever an evaluator
wrote became a subagent type: a hallucinated name either failed to spawn or silently degraded. Every
`agent` field is now an enum, built from the lanes the project actually has.

### Fixed — a routing target the plugin did not ship

`/plan` sent L4+ work to a workflow that was not in the plugin, and reported the miss as an error.
An unresolved name is a route, not a defect: the fallback is named, the three distinct failures are
distinguished, and `FF-8.0` stops the post-return checks from running against a call that never
happened.

### Changed — the bash approver sorts by one question: does git undo it?

The two lists were wrong in opposite directions. Measured before the change, on the shipped code:

```
guarded     ASK    git add · git checkout · git merge · git pull · rm -rf __pycache__ · bun run dev
autonomous  ALLOW  git clean -fdx · git reset --hard · git stash clear · git gc --prune=now
                   git filter-branch --all
```

It asked about work git restores for free, and ran what git cannot bring back. `destructiveFloor`
was on the whole time; those commands simply were not on the list.

Now: `git clean -f`, `reset --hard`, `stash drop|clear`, `reflog expire`, `gc --prune=now`,
`filter-branch`, `filter-repo` and `update-ref -d` are on the floor, denied even under
`autonomous`. Reversible git verbs, build artefacts (`__pycache__`, bundler and framework caches,
coverage) and `mv`/`chown`/`gh pr create` run without a prompt.

`git commit`, `git push` and `git checkout` also stop asking **here** — not because they became
safe, but because `git_commit_gate`, `git_push_gate` and `git_branch_gate` already refuse them, and
Claude Code merges hook decisions most-restrictive-first (`deny` > `defer` > `ask` > `allow`, every
matching hook run to completion). One decision, one owner; what disappears is the second prompt for
it. Both halves are proved in the suite: the approver allows, the dedicated gate still denies.

The approver also stopped naming a package manager. `bun run dev` used to ask while `pnpm run dev`
did not, in the same project, for the same kind of command.

`hooks/test_hooks.py` goes from 71 checks to 154. Every reclassification carries the violation and
the mirrored legitimate case, because a gate that fails the correct case trains people to ignore
gates.

### Fixed — every routing reference in the repository now resolves

Found by the new gate and by reading the targets, not by trusting the citations:

- **`/recover` was a second, divergent copy of the recovery protocol.** It announced five steps
  under the same numbers as `references/recovery-protocol.md` — different steps — ended at an
  `oracle` agent that has never existed in this repository, and carried a page of Astro and
  Tailwind troubleshooting that reads as general advice and was general to one project. `/debug`
  had the same defect from the other side: it said "execute its 5 steps verbatim" and then listed
  five that were not in the file. The protocol is now written once, and both commands point at it.
- **`${rulesDir}/DESIGN.md`, cited five times, where the shipped template is `design.md`.** On a
  case-sensitive filesystem that has never resolved.
- **`shared-context.md § 7.5`, cited twice, does not exist** — and § 7 does not cite those files
  back. Both headers now name their real consumers, which for one of them is all twelve agents.
- **`.claude/CLAUDE.md § Stopping conditions`, cited five times**, is in neither this repository
  nor `templates/CLAUDE.md`. The table is real and lives in the planning skill; the citations point
  there, and the skill stopped calling itself a mirror of a section that never existed.
- **`/debug` sent the AutoResearch Loop to § 5** (Tool Usage). It is § 10.
- **`/research` described `explorer` as `.claude/agents/explorer.md`** — the path where a project
  would put an override, which is to say the one place it is guaranteed not to be.
- **"D.R.P.I.V" was named in three files and defined in none.**

**The spawn ceiling had three numbers and no conflict.** 25 (`maxSpawnsPerSession`) is a session
total the hook refuses at; 5 is the width of a single fan-out, stated in a dozen places and enforced
by nobody. They measure different things and nothing said so. The width is now
`graphGuardrails.maxParallelWave`, the same field the build chain slices waves with, and § 7 spells
out which quantity is which.

**`/verify` now reads the plan sections that were produced for it.** `/plan` emits a Reuse ledger, a
Regression watchlist and a Rollback, each labelled "consumed by /verify" — and `/verify` had never
read any of them, while `/plan` cited three phases of it (1.5, 1.6, 4) that were never written. The
three checks are now in `/verify § 3`, in the existing checklist rather than as new phases: the
heavy verify was refused once already, for injecting 93 KB before any work started, and that
decision still holds.

### Fixed — three ceilings that shipped with no assertion behind them

G2 (spawn ceiling), G3 (round ceiling) and G4 (write lease) had been in the plugin since the first
release with zero tests, which is the state `.claude/rules/hooks.md` explicitly forbids: "a guardrail
never seen denying is an assumption with syntax". All three now carry the violation, the mirrored
legitimate case, the opt-in release, and the garbage-input case.

Writing the tests surfaced one behaviour worth knowing: a spawn refused by the ceiling still consumes
its slot, because the counter increments before the check. That is correct — the alternative lets a
caller retry forever at no cost — and it is now asserted rather than merely true.

### Added — two gates that would have caught this

- `node .github/check_workflows.mjs`: four checks on every shipped workflow.
  1. It **parses**, wrapped the way the runtime wraps it — `node --check` rejects a legal workflow
     outright, because top-level `return` is only legal inside that wrapper.
  2. `meta.name` matches the filename. A mismatch registers the workflow under a name nobody calls.
  3. The set of plugin-owned agent names in the script matches `agents/` on disk, in both
     directions. That set decides which spawns get the `graph-powers:` prefix, and a name missing
     from it silently loses its namespace and fails at spawn time.
  4. It **runs**, against stubs. Every runtime hook is replaced — `agent()` returns a minimal
     object synthesised from the schema it was handed — so the whole control flow executes without
     spawning anything. Parsing proves the file is legal; this proves it survives its own logic.
     It also asserts the input guard fires on empty args.

  Check 4 found a defect on its first execution: `ultra-verify` accepted an empty plan path and
  went on to ask its agents to verify "the plan at ``" — a prompt that reads as valid and produces
  confident findings about nothing, at the cost of a full skeptic panel. It now refuses, and points
  at `/verify` for the gates-only pass that request actually wanted. The empty-diff exit became
  honest in the same pass: a plan whose build wrote no files returns `NEEDS-WORK`, not the
  `VERIFIED` an empty tree looks like to a gate.
- `python3 .github/check_wiring.py`: every routing reference resolves. The old dangling gate checked
  file paths, which is the easy half; this one checks the agent a command spawns, the workflow it
  invokes, the skill it loads, the rule template it names, and the section of another file it tells
  the reader to apply. Pointed at the tree before this release it found eight live misses, including
  five citations of `${rulesDir}/DESIGN.md` where the shipped template is `design.md` — a reference
  that has never resolved on a case-sensitive filesystem and reads as correct in every review.
- The dangling-reference and machine-path gates now cover `workflows/` and `.js`. The copy of the
  dangling regex in `CONTRIBUTING.md` had already drifted from the one in CI; both are updated.

### Fixed — the plugin now actually runs on Windows

It never claimed otherwise, and it did not. A full read of every shipped surface found defects on
all of them, and the thing they had in common is that **none of them raised**. They returned the
wrong answer quietly, which is why this release adds a gate rather than a paragraph.

**The three that were worst:**

- **A clone on Windows installed nothing, and said it worked.** `codex/lib.mjs` matched frontmatter
  with `^---\n`, which does not match `---\r\n`, and Git for Windows checks out CRLF by default
  because the repository never said otherwise. Every agent and every command-as-skill was dropped
  by the `if (!data.name)` guard downstream, and the installer printed success. Fixed at the
  parser, and a `.gitattributes` now pins `eol=lf` so the clone never gets there.
- **The uninstaller could delete every other tool's skills.** `codex/install.mjs` refused to
  `rmSync` a shared directory with a guard written `(^|/)`. On Windows the manifest paths carry
  `\`, the guard never matched, and `~/.agents/skills` was in scope for a recursive force delete.
- **The destructive floor did not exist under PowerShell.** Every list in `smart_bash_approver.py`
  was POSIX grammar, so `Remove-Item -Recurse -Force C:\` matched nothing and fell through to
  `bashDefault` — which under `autonomous` is allow. The mirror image was as bad: `Get-ChildItem`,
  a pure read, fell through to `ask`. Windows was prompted about the harmless and waved through the
  catastrophic, while the docstring promised "always denied". The approver now speaks both
  grammars, with `format`, `diskpart`, `vssadmin delete shadows`, `cipher /w` and `bcdedit` on the
  floor beside `rm -rf /`.

**A `--scope user` install wrote into somebody else's repository.** `process.env.HOME` is undefined
on Windows, and every fallback landed on the project directory — so `.codex/`, `.agents/skills/`
and the permission allowlist were created inside the user's repo. Now `homedir()`, everywhere.

**The installer decided Claude Code was not installed** on machines where it was: an npm-installed
CLI is `claude.cmd`, and `CreateProcess` does not run `.cmd`. Same for the Python probe, where
`python3` is not the name and a Microsoft Store stub by that name exits non-zero.

**The write lease denied every write it was meant to permit** — a native-separator path compared
against a lease written with `/`. It was armed for the first time in this same release, so the
defect shipped and was caught in the same breath.

**Smaller, and all of the same shape:** `commit_audit_gate` read only exit 127 for "command not
found", while cmd.exe answers 9009 — turning fail-open into fail-closed and blocking every commit
on a machine without the audit tool. `protect_files` compared `contains` patterns against the raw
path, so a project declaring `config/secrets/` got no protection and no warning — and `.lstrip("./")`
strips *characters*, so every dotfile in `exact` (`.env`, `.gitignore`) was quietly unprotected.
`select.select` takes only sockets on Windows, losing the `cwd` the Codex CLI sends. `text=True`
without an encoding decodes with the locale code page, so an accented branch name stopped matching
the protected list. `shlex.split` ate the backslashes out of a Windows path in
`tooling.commands.format`, and `CreateProcess` could not run the `.cmd` shim anyway, so the
formatter silently never ran.

**In the prose an agent executes**, roughly forty commands were POSIX-only: `awk`, `find | wc -l`,
`ls -lh | sort | head`, `jq`, `grep`, `date +%F`, `$( )`, `/dev/null`, `/tmp`, `~/`, `export VAR=`,
and trailing-`\` continuations. They are now the agent's own tools (`Grep`, `Glob`, `Read`) or one
line of `python -X utf8 -c`. One of them was a bug on Linux too: `a || b || c | sort | head` parses
as `a || b || (c | sort | head)`, so the common case was never sorted or truncated.

**The opt-in mechanism turned out to be portable already, and nobody was told.** `opted_in` matches
the key as *text*, not as shell syntax, so `$env:KEY=1; git commit …` and `set KEY=1 && git commit …`
release a gate exactly as the POSIX form does. Nine files taught only the POSIX form — including
the message each gate prints at the moment it blocks. All three forms are now in
`110-guardrails-index.md`, in the gates' own denial messages, in the rule template that ships into
every project, and asserted in the suite so a refactor to `^KEY=1\s` cannot quietly lock Windows out.

**`python3 .github/check_portability.py`** is what keeps this from coming back: POSIX binaries and
constructs in executable blocks, and the silent half in Python — `startswith("a/")` on a glob
result, bare `HOME`, `select.select`, `subprocess` without an encoding, `shlex.split` without
`posix=`. `AGENTS.md` gains cardinal 8 to say why.

### Fixed — the Windows fixtures turned the machine-path gate red

The destructive floor now has tests, and a test that proves the floor stops
`Remove-Item -Recurse -Force C:\` has to contain that string. The machine-path gate matched any
drive letter, so the evidence that the plugin defends Windows was what failed CI — eight hits, all
of them either a hazard being named or `C:\Windows\System32`, which is the same path on every
Windows install.

The rule is now stated as one class instead of three shapes: a **home directory** — a path whose
first segment is `home` or `Users`, in any of its three spellings. That is the thing that only
exists on the machine that wrote it, and the POSIX arm never caught `/opt/x` either, so the three
arms now agree.

**`python3 .github/check_machine_paths.py`** replaces the pattern that lived inline in three files —
`ci.yml`, `AGENTS.md` and `CONTRIBUTING.md` — where correcting one left the other two wrong. It
prints what it deliberately lets through, so the next person does not re-widen it.

### Fixed — commands loaded on every run what they need on one branch

`/verify` measured 51 KB, and 42 KB of it was three domain skills its own text loads *conditionally*
— `Skill("debugger")` when chasing a failure, `Skill("astro")` when the stack is Astro. A `/verify`
on a passing typecheck loads none of them. The same shape appeared five more times: `/debug` named
the audit prompts, the recovery protocol and three debugger references in sentences beginning
"Load", so a session debugging a crash paid for the audit mode and the recovery mode as well;
`/implement` declared the planning skill in its header, charging 14 KB to every run that already
had a plan; `/plan` read the issue-triage rubric whether or not the argument was an issue;
`/pr-review` loaded the `full`-mode set in every mode.

Each of those sentences now names the branch that pays for it. That is a change to the instruction,
not to the measurement: an agent reading `/debug` was previously told to open files it had no use
for, and did.

**`python3 .github/check_context_budget.py` now reports two numbers**, because one was lying in
both directions. FLOOR is what an invocation pays before it has read its arguments; CEILING is the
floor plus every branch taken at once. Conditionality is read off the line — a stated `when`/`if`,
a routing-table row, or a fenced block, since what a subagent reads is paid out of the subagent's
context — so the rule applies unchanged to a tree written before the script existed, and a
before/after comparison stays fair. A baseline written by the previous single-number version is
refused rather than silently compared.

Measured across the twelve commands, pre-work tree in a `git worktree` and both sides run through
the same script: floor 523,746 → 289,512 B (**44.7 %**), ceiling 578,666 → 399,043 B (31.0 %).
Every one of the twelve fell.

`.claude/rules/artifacts.md` now covers `workflows/**`, which shipped in this release with no rule
declaring its contract: `meta` as a pure literal, `agentType` namespaced, the six-name script scope,
no `fs` and no `Date.now()`, and an `enum` on every field that becomes a `subagent_type`.

### Verified in this session

- The bash reclassification ran under itself for the whole of the work that produced this release.
- `node .github/check_workflows.mjs` dry-runs all three workflows against stubs: 3, 9 and 15
  stubbed spawns respectively, and all three refuse empty args.
- `python3 .github/check_wiring.py`: 130 routing references, 0 unresolved.
- `python3 hooks/test_hooks.py`: 154 checks, exit 0.
- `python3 .github/check_context_budget.py --compare`: 44.7 % less on every invocation, 31 % less
  in the worst case, against a `git worktree` of the pre-work tree measured with the same script.
- The Codex installer fixture (install, reinstall, uninstall, both scopes) still passes, a third
  party's skill survives it, and no workflow leaks into the Codex tree — correctly, since Codex has
  no `Workflow`.

**Not verified: the chain end to end.** `Workflow({name:'graph-powers:ultra-plan'})` was called in
this session and returned `not found`, exactly as the paragraph below predicts — the registry was
built before `workflows/` existed. That is the documented behaviour observed rather than assumed,
and the fallback it triggers is what produced this release. Running the chain itself needs a
session started after the install.

### Known

Workflows are loaded when a session starts. Installing or updating the plugin mid-session leaves the
new workflows invisible until a restart, and the symptom is
`Workflow "graph-powers:ultra-plan" not found`. `AGENT_SETUP.md § Step 10` says so, and `/plan`
treats it as a route rather than a failure.

Codex has no `Workflow`, so the chain is Claude Code only. Under Codex — and under Claude Code when
the name does not resolve — `/plan`, `/implement` and `/verify` do the same work as commands.

## 1.2.0 — the version is the delivery channel

A CI gate now refuses any change that touches what the plugin ships without bumping the version in
both manifests.

That is not bookkeeping. `claude plugin update` compares the **version** in
`.claude-plugin/plugin.json`, not the commit it came from — so a fix pushed without a bump sits on
`main` while every installed machine keeps the old files and the command reports "already at the
latest version". This release exists because that happened: 1.1.0 shipped, a follow-up fix landed
without a bump, and the installed copy stayed on the commit before it, reporting itself current.

Also fixed: the installer died with "neither claude nor codex was found on PATH" even when the
caller had passed `--target` and said exactly what to wire. Generating Codex artefacts for a CLI
that is not installed yet is a real case — a container image, a CI runner, a machine being
prepared for someone else — and it is the case the project's own CI hits. A missing CLI is now
fatal only when nobody said what to wire; Claude Code stays fatal either way, because its half of
the install *is* the CLI.

## 1.1.0 — it updates itself, and there is nothing to publish

### Changed — distribution

**npm is gone. Two ways in remain: the Claude Code marketplace, and `git clone`.**

1.0.0 published to a registry, and the cost showed up on the first fix: an account, a 2FA device
and a release standing between a one-line correction and the machine that needed it. A publish was
refused mid-session for a missing OTP while the same commit was already on `main` and already
correct.

What a registry buys is dependency resolution, versioned installs and a build artefact. This
repository has none of those: no dependencies, no build step, and its artefact is markdown, JSON
and standard-library Python. The checkout **is** the thing that runs. So the registry was charging
a release and buying nothing.

```
# Claude Code
/plugin marketplace add GrupoUS/graph-powers
/plugin install graph-powers@graph-powers

# Codex CLI, or a clone on either harness
git clone https://github.com/GrupoUS/graph-powers.git ~/.graph-powers/src
node ~/.graph-powers/src/bin/graph-powers.mjs
```

`--update` fast-forwards the clone and reinstalls from it; the auto-updater's Codex half does the
same thing on its own, pulling the clone the manifest recorded at install time. `--ff-only`
throughout: a merge commit made by a background process is a state nobody chose, and a clone with
local edits refuses to update and says so.

The trade-off, stated plainly: consumers get no version pinning, because a clone tracks a branch
rather than a tag. That is acceptable for a harness meant to converge — a project pinned to an old
copy of the guardrails is the failure this repository exists to end — and anyone who needs a pin
can check out a tag.

`package.json` is now `private: true`: it exists so `node` treats the `.mjs` files as modules, not
as a manifest for anything to publish.

### The rest

1.0.0 shipped the harness. This release closes the two gaps that made it a snapshot rather than
something you install once: it had no way to reach an installed machine after publication, and its
Codex artefacts were generated with defects that were invisible in the generated files.

### Added

- **The harness keeps itself current.** `hooks/auto_update.py` runs at session start, reads a
  throttle file, and at most once every twelve hours starts a *detached* worker. The worker asks
  each CLI to update itself through its own supported path — `claude plugin marketplace update`
  then `claude plugin update`, and a regenerate from the published package on Codex. Nothing waits
  on the network, so no session start pays for a DNS lookup, and nothing inside the project is
  ever touched. The session after an update opens with one line naming the new version, printed
  once. Configurable under `autoUpdate`; `GRAPH_POWERS_NO_AUTO_UPDATE=1` turns it off for one
  machine without editing the project's config.

  Two details only running it against the real CLI surfaced: `claude plugin update` needs the
  qualified `<plugin>@<marketplace>` form (the bare name is "not found"), and it exits 0 when it
  fails — so the worker trusts neither its exit code nor its output, and reads the version out of
  `installed_plugins.json` before and after. That registry is also the only thing that moves: the
  update unpacks a *new* version directory and leaves the running one untouched, which is exactly
  why it says "restart to apply".
- **On Codex, an unchanged `hooks.json` is left alone.** Codex trusts a hooks file by its content,
  so rewriting an identical one costs a `/hooks` re-approval and leaves the guardrails inert until
  it is given. An update that quietly disarms what it updated is worse than no update.
- **A CI gate for undeclared placeholders.** Every `${config.key}` in an artefact must exist in
  the schema. One that does not resolves to an empty string, and the instruction that depended on
  it reads as satisfied — thirteen such keys shipped in an earlier version of this harness.
- The `codex` job now runs both scopes against an isolated `HOME`, and asserts what the generated
  files must be true of rather than only that they exist.

### Fixed

- **The Codex frontmatter reader split every `description:` on its commas.** Multi-clause
  descriptions became arrays, so each generated Codex skill carried a description truncated at the
  first comma. A skill nobody can find is a skill that is not installed. The shape is now decided
  by the key.
- **Generated subagents ignored the agent's own `model:` and `effort:`.** Twelve deliberately
  different agents came out of the generator identical — the scout and the evaluator
  indistinguishable. Effort now comes from the agent's declaration, then from what its Claude
  model implies, then from its role, then from the project's config.
- **`${CLAUDE_PLUGIN_ROOT}` survived into the Codex copies.** Codex never sets that variable, so
  86 cross-references pointed at nothing: the reference read as present and loaded as empty. Each
  subtree is now rewritten to the path Codex actually reads.
- **The Codex manifest was written last.** An install that died halfway left artefacts with no
  record of them, and `--uninstall` then reported success while every one of those files stayed.
  It is now written first, listing what the run intends to create, and rewritten complete at the
  end.
- **The project half wrote no manifest at all**, so `--uninstall` left `.codex/rules/` and the
  `AGENTS.md` block behind. It does now — and the rules are recorded as *adopted*, so removal
  keeps them: they were copied as a starting point and then edited, and the line somebody added
  after an incident lives in those files.
- **`--uninstall` removed only one half.** The scope flag says where to *write* on an install; on
  a removal it silently meant what to leave behind. Removal now defaults to both halves.
- **An unparseable `.codex/hooks.json` was treated as absent** — the exact overwrite the merge
  exists to prevent, pointed at somebody else's guardrails. A file that exists and does not parse
  is now copied aside, and the caller is told where it went.
- **The installer's Codex verification read the wrong manifest** at user scope, so it warned "no
  Codex manifest was written" on every run that had just succeeded.
- `codex.model` and `codex.reasoningEffort` from the project config never reached the generator.

### Changed

- **`fallow_gate.py` is now `commit_audit_gate.py`, and it runs what the project declared.** The
  old hook fetched and executed a pinned third-party auditor from the network before every commit,
  in every repository that installed this plugin — a download and execution on a machine whose
  owner never asked for it. The tool is now named in `gates.preCommitAudit`; declare nothing and
  no audit runs, which is the default. Exit 0 lets the commit through, anything else blocks it and
  shows the command's own output, `127` fails open because a missing binary is a fact about the
  machine and not a verdict about the changeset, and `<PREFIX>_ALLOW_AUDIT=1` releases one call.
- Python **3.10** is stated as the floor and checked by the installer. `engines` cannot express a
  Python requirement, and several hooks use `X | None` in annotations evaluated at import time.
- `license` is `MIT AND Apache-2.0` in both manifests: the package vendors two Apache-2.0 skills,
  and a bare `MIT` was a false statement about the tarball's contents.
- `NOTICE` now names every third-party origin — including the MIT material adapted from
  `mattpocock/skills` and `obra/superpowers` — and records the modifications Apache-2.0 §4(b)
  requires, with a matching notice in each modified skill.
- `docs/`, `AGENTS.md` and `CONTRIBUTING.md` ship in the package; the README linked all three and
  every link was a 404 inside the tarball.
- The guardrail suite went from 32 checks to 71.

## 1.0.0 — first public release

Graph Powers began as `gpus-harness`, the single copy of a harness that had been maintained by
hand in five private repositories. This release is what it took to make that copy safe for anyone
else to install.

### Added

- **Codex CLI support, generated from the Claude Code artefacts.** `.codex/hooks.json`,
  `.agents/skills/`, `.codex/agents/*.toml`, `.codex/rules/` and a delimited `AGENTS.md` block. The
  event names, stdin payload and deny semantics are identical between the two harnesses, so the
  eleven Python guardrails run unchanged. Hooks are merged rather than overwritten, and every entry
  added is recorded so `--uninstall` removes exactly what was added.
- **`AGENT_SETUP.md`** — the setup playbook an agent executes after installation: install the
  required external plugins, read the repository, write or merge the config, improve `CLAUDE.md`
  and `AGENTS.md`, build the rules layer, create the three project authorities, clean what shadows
  the plugin, audit `settings.json`, wire Codex, verify. Every step stops for approval before it
  writes.
- **`DESIGN.md`, `PRODUCT.md`, `REVIEW.md` as installable specs.** Each says what the host
  project's counterpart must contain, how to source every section from that repository, and how to
  improve an existing one without destroying decisions.
- **`references/safety-floor.md`** — the invariants eleven agents already mirrored by section
  number, and that had never existed as a file.
- **`references/audit-agent-prompts.md`** and **`references/recovery-protocol.md`** — written, not
  just cited; `/debug audit` and `/debug recover` both depended on files that were not there.
- CI gates for broken symlinks, frontmatter name-versus-filename, dangling file references, package
  size, and the Codex generator's idempotence.

### Changed

- **Autonomy is configurable, and the installer defaults it to automatic.** A harness that asks
  permission to run `git status` teaches people to approve without reading, which is more dangerous
  than anything it was guarding. `autonomy.level: autonomous` makes unrecognised commands run,
  cleanup run, and commit and push need no opt-in key; any single action can still be pinned back
  to `ask` without leaving the level. The installer also writes a permission allowlist covering
  everything the harness itself runs — additively, so nothing already allowed is removed.
  `destructiveFloor` holds at either level and refuses only what git cannot give back; deleting a
  file inside a committed repository is deliberately not on that list.
- **Global installation is now the default.** The harness is identical in every project, so it
  installs once per machine (`--scope user`) and serves every repository, including ones that do
  not exist yet. Only what genuinely differs per project stays local: the config, the rules, and
  the three authorities. The installer detects an existing global install and skips it, so setting
  up a tenth project writes two files rather than thirty. What makes this correct rather than
  sloppy is that the guardrails read *the project's own* config at runtime — one copy enforces a
  different branch and a different opt-in key in every repository.
- Renamed to **Graph Powers**; the default opt-in prefix is now `GRAPHPOWERS`.
- Configuration moved to `.graph-powers/config.json`, with `.claude/config.json` still read as a
  fallback. Runtime state moved to `.graph-powers/logs/`.
- Guardrail denial messages name the project's configured work branch instead of a hardcoded one.
- The shared-patterns file moved out of `commands/` into `references/shared-context.md`. It had
  been registering as a 410-line slash command nobody meant to ship, and commands only mentioned it
  in prose.
- `/verify` and `/pr-review` rewritten against `tooling.commands` and the project's own
  `REVIEW.md`; `NOT DECLARED` is now a distinct outcome from passing.
- `/design`, `/design-fix` and `/design-improve` (1155 lines) collapsed into one `/design` that
  delegates craft passes to the external impeccable plugin.
- All documentation is in English.

### Removed

- `skills/xlsx` — a proprietary skill redistributed without its licence.
- `skills/ui-ux-pro-max` — a third-party dataset with no declared provenance.
- `skills/impeccable` — a 3.3 MB vendored snapshot of an external Apache-2.0 package, one minor
  version behind its own registry. It is now a declared dependency.
- `skills/evolution-core` — every script it invoked was missing.
- `skills/gpus-theme`, `skills/drizzle-neon-clerk-auth` — single-product branding and stack.
- `skills/adhd` — a broken symlink that shipped in the npm tarball.

### Fixed

- `smart_bash_approver.py` blocked `npm`, `npx`, `pnpm` and `yarn` outright, with the comment
  "GPUS projects are Bun-only". In a public plugin that means a stranger installs it and cannot
  run `npm install`. Every package manager now runs by default; a project that genuinely cannot mix
  them declares `autonomy.allowPackageManagers`.

- `CONFIG_PATHS` listed the same path twice, so the documented `.claude/config.json` fallback never
  resolved.
- `protectedFiles.exact` compared basenames only: a project declaring `ops/secrets.yaml` got no
  protection and no warning.
- Four command frontmatters contained an unquoted `description` with a `: ` in it and did not parse
  as YAML at all. CI only validated agents.
- The CI gate against absolute paths matched its own documentation and failed on a repository
  containing none.
- `skills/debugger` and `skills/planning` declared suffixed names while commands invoked both
  forms, so half the calls never resolved.
- `security-reviewer`, `skill-improver` and `verification` described themselves as read-only in
  prose only; all three now declare `disallowedTools`.
- Zero dangling file references (was 28) and zero dangling `Skill()` targets (was 5).

Package size: 4.7 MB → 348 KB.
