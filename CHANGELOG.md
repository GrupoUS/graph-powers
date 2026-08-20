# Changelog

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
acts on. **The shared layer went from 272,676 bytes across the twelve commands to 76,303 — 72 %
less**, and the full chain (command + references + skills) fell 28 %; the rest is dominated by the
skills a command loads, which this change does not touch.

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

### Verified in this session

- The bash reclassification ran under itself for the whole of the work that produced this release.
- `node .github/check_workflows.mjs` dry-runs all three workflows against stubs: 3, 9 and 15
  stubbed spawns respectively, and all three refuse empty args.
- `python3 .github/check_wiring.py`: 130 routing references, 0 unresolved.
- `python3 hooks/test_hooks.py`: 154 checks, exit 0.
- `python3 .github/check_context_budget.py --compare`: the twelve commands load 28 % less; the
  shared layer specifically, 72 %.
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
