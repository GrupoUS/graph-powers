# Changelog

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
