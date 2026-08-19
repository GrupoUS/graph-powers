# Changelog

## 1.1.0 — it updates itself, and the Codex side is real

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
