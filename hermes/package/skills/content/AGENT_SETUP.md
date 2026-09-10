> Hermes auxiliary: `content/` paths are `file_path` values relative to the registered-document parent. Apply the loaded graph-engineering mapping and host policy; this file is served without template expansion.

# content/AGENT_SETUP.md — install and verify Graph Powers

Execute this in the **target project**, using the installed plugin or a verified clone as the
source. Install the complete plugin once per machine; keep only project-specific configuration
and rules in each repository. There is no separate installation for individual skills.

Complete authorized, reversible setup and its checks without repeated confirmation. Preserve
existing settings and dirty files. Obtain approval for destructive cleanup, credentials,
publication, or an expansion of the requested scope. Installing does not authorize Git operations.

**Success:** every requested client has a verified package, the applicable hooks execute after
reload, project configuration resolves correctly, and no required check remains unverified.
Skip irrelevant branches. Stop after that proof; do not add audits or optional integrations.

## Command conventions

- Run commands from the target project's Git root, never from the plugin repository.
- Replace `<PLUGIN>` with the verified source directory and `<CODEX_HOME>` with the active home.
  These are path placeholders, not shell variables. Quote paths; do not copy placeholders literally.
- `<CLIENT>` is one requested client; `<SCOPE>` is `user` unless project/local scope was explicitly
  selected for Claude. Use that same scope in installation and verification.
- `<VERSION>` is the target version from the verified plugin manifest. `<HERMES_ROOT>` is the
  installed package path reported by `hermes plugins show graph-powers`.
- Examples use `python` for the verified Python interpreter and `bun` for JavaScript. Substitute
  `python3` or `py -3`, and a supported `node`, when those are the installed runtimes.
- Hooks invoke the literal `python3`: it must work in the **client process's PATH**, regardless
  of which interpreter runs the setup commands.
- `<MODE>` is the selected `autonomous` or `guarded` policy. Preserve an existing explicit
  choice. The installer's default is autonomous; report the effective policy and keep the
  destructive floor enabled. A runtime setting is not approval to commit, push or publish.
- Prefer existing CLIs and native installations. Do not install another copy of a client to make
  a command work. When syntax differs, inspect that installed CLI's help once before proceeding.

## Step 0 — Establish source, target and current state

1. Read the target's `AGENTS.md`, `CLAUDE.md`, existing config and working-tree status.
2. Identify which clients the user actually uses. Scope installation to those clients.
3. Resolve the source from an explicit Graph Powers path or the client's exact registration:
   Claude's scoped `installPath`, Codex's `source.path`, Grok's reported `path`, or Hermes'
   installed package. Let the verifier resolve Cursor candidates; do not select a cache by mtime.
   If no source exists, use the native route in Step 9, then continue from its registered package.
4. Back up only existing files about to change, including relevant client settings. Keep the
   backup outside auto-loaded instruction directories; preserve symlinks and file ownership.

```bash
git rev-parse --show-toplevel
git branch --show-current
git status --short
python -X utf8 "<PLUGIN>/bin/verify-hook-clients.py" --client all --project-dir .
```

Inspect each requested client's result. Exit 0 can include absent runtimes: `SKIPPED` is not an
installed client. Registry presence alone is insufficient; the verifier checks the actual package.
Keep a valid installation matching the intended version and repair only missing or stale components.

## Step 1 — Resolve prerequisites, not every optional tool

| Needed for | Prerequisite / proof |
|---|---|
| Core guardrails | Git and Python 3.10+; literal `python3` works in the client environment |
| Installer/generators | Installed Bun or supported Node; CLI preflight passes |
| A particular client | That client already installed and usable; no other client is mandatory |
| Project commands | The package manager and local tools the project declares |
| Browser work | Available browser automation and a working browser; otherwise mark that workflow unavailable |
| PR/issue work | `gh` and usable authentication |
| External research | Search tools actually available to the selected researcher; check its declared tool names |
| Database/performance/security integrations | Only the CLI/service required by the requested workflow |

```bash
python3 -X utf8 -c "import sys; print(sys.version.split()[0]); raise SystemExit(sys.version_info < (3, 10))"
bun "<PLUGIN>/bin/graph-powers.mjs" --help
```

A Windows Store stub is not a working interpreter. Repair its executable/PATH mapping before
enabling permissive client posture. Do not infer Python health from a different terminal.

Planning, TDD, design, landing-page design and review methods are bundled. Other plugins, MCP
servers, browser downloads and code graphs are conditional; do not install them by default.
When the project selects Graft or explicitly requests its diagnosis, follow only Static readiness
diagnosis and Effects gate in `content/references/shared/115-code-graph.md`. Inspect existing manifests,
configuration and registration metadata; do not start a backend or MCP health check. Keep missing
components and unknown freshness/policy separate; selection does not install or activate anything.
Use the project's package runner. Preserve native Claude/Codex installations and the shared
Codex home. Never print credentials or put secret values in setup commands or reports.

## Step 2 — Read the project facts

Read manifests, lockfiles, scripts, existing rules and the actual directory tree. Record only:

- Stack, package manager and existing test runner; absence is a valid finding.
- Working/protected branches and project-specific opt-in prefix.
- Actual code paths, required environment-variable **names**, and declared check commands.
- Existing design, product and review authorities, including equivalents under other names.

Do not invent a path, runner, gate or database engine. Investigate a missing required fact; ask
only when the repository and current session cannot resolve it.

## Step 3 — Write or improve configuration

Use `content/schema/config.schema.json` as the contract and `examples/` as starting points, relative to
the verified plugin root. Merge `.graph-powers/config.json` field by field; preserve existing
choices and account for the legacy `.claude/config.json` when present.

| Scope | Owner |
|---|---|
| Shared client settings and manual model choices | The client's existing global native config; Codex uses its active home's `config.toml` |
| Graph Powers operator defaults | User configuration read by `https://github.com/GrupoUS/graph-powers/blob/main/hooks/_config.py`; only supported operator-policy groups |
| Branches, paths, gates and necessary exceptions | Target project's `.graph-powers/config.json` |

Avoid repeating global defaults in each project. Keep project opt-in prefixes distinct.
Omit nonexistent layers. Configure a database only when present: status must be genuinely
read-only, and `applyPolicy` remains `never` without explicit authorization. Setup never applies
schema/data changes.

Resolve the effective autonomy policy before Step 9; defer client permission changes until its
package and hook probe pass. Do not overwrite a deliberate restrictive override merely because
the enclosing level is autonomous. Keep Git permissions and the destructive floor explicit when
the operator's requirements differ from the installer defaults.

The installer repairs `ask` to `allow` for routine fields in an autonomous project. If an `ask`
override is intentional, use `--autonomy guarded` for this run. No installer flag combines a new
permissive client posture with preservation of those overrides; report that limitation rather
than silently changing them.

For JS/TS only, read `content/references/shared/130-typescript7-oxc-gates.md`. Reuse the local Oxc/TypeScript
toolchain and declared runner. The explicit `--setup-oxc` installer option changes dependencies
and editor files; use it only when that setup is authorized. Keep vtsls's compatible SDK and
manual model/effort choices. Leave auto-update settings alone unless a change was requested.

Inspect the script behind `tooling.commands.lint`, including its file arguments and exit status.
Stop appends changed JS/TS paths; a wrapper whose script already includes `.` still scans the
whole tree. Do not claim changed-only coverage from the appended paths alone. Report an incompatible
command contract and resolve it within the authorized tooling scope; never hide findings with an opt-in.

After merging, prove the **effective** config rather than trusting valid JSON:

```bash
python -X utf8 -c "import sys; from pathlib import Path; sys.path.insert(0, str(Path(sys.argv[1]) / 'hooks')); import _config as gp; root = Path.cwd(); cfg = gp.load(root); print('config:', gp.config_path(root)); print('branch:', gp.work_branch(cfg)); print('opt-in:', gp.opt_in('COMMIT', cfg))" "<PLUGIN>"
```

Compare the output with the intended path, branch and prefix. Unexpected defaults mean setup
has not verified the config; fix the load before continuing.

## Step 4 — Keep a small instruction layer

### 4a — The root pair

Preserve project identity, hard invariants, routing and existing decisions. Use the plugin's
`content/templates/CLAUDE.md` and `content/templates/AGENTS.md` only as structure; never replace a project's
unique rules wholesale. Put each shared rule in one owner and link from the other file.
The installer owns its delimited Graph Powers block; do not hand-edit inside it.

### 4b — Child nodes only where useful

When responsibility boundaries need their own context, use `graph-powers:intent-layer`.
Reuse its `state`, `measure` and `check` commands; do not duplicate its scanning code here.
Add nodes only for real boundaries, link them from their nearest ancestor, and record justified
deferrals. A small repository needs no artificial hierarchy.

## Step 5 — Keep only project rules

Compare existing rules with `templates/rules/`. Preserve domain-specific decisions; replace
generic process with a pointer to the plugin's owner. Remove redundant files only after the
required approval and a diff proving that no unique content is lost.

Give rules matching `paths:` or an intentional explicit loader. Resolve every `{{placeholder}}`
from repository facts; omit an inapplicable section rather than inventing content.
Update the rules index. Product/design/review authorities belong to Step 6.

## Step 6 — Reuse the project's authorities

The plugin's root `DESIGN.md`, `PRODUCT.md` and `REVIEW.md` are specifications for the host's
documents, not ready-made project content. Read the relevant spec before filling a gap.

Improve an existing equivalent in place, preserve prior decisions, and link to its owner.
Record unknown decisions as unresolved. Do not turn installation into a redesign, product-planning
exercise or a new document hierarchy; report gaps that require separate work.

## Step 7 — Resolve shadowing without deleting custom work

Compare project/user agents, skills and commands with the installed plugin, including symlinks
and legacy personal copies. Use namespaced Graph Powers entrypoints.

- Identical/superseded copies: propose removal with the diff and backup.
- Local additions: preserve as a deliberate override or migrate the unique content first.
- Local-only artifacts: keep them.

Do not delete another tool's files, caches or hooks to make registration pass. If cleanup is not
authorized, report the remaining shadow and its consequence.

## Step 8 — Audit accumulated settings

```bash
bun "<PLUGIN>/bin/audit-settings.mjs" --json
```

The audit is read-only. Inspect duplicate/overlapping hook registrations before removing any.
Preserve unrelated settings, permission arrays, environment values and third-party registrations.
Use the installer for additive posture changes in Step 9; do not recreate that logic manually.

If skill descriptions are actually being dropped, inspect the client's listing diagnostics.
Prefer removing verified duplicates or narrowing descriptions; do not automatically enlarge the
listing budget or disable skills during every installation.

### 8a — Prevent recurring hook errors

Inspect all effective registrations for the requested clients: the plugin manifest, generated
adapters and separately registered global/project hooks. Attribute each to its owner and exact
executable path/version. The package verifier's single guardrail probe does not exercise every
hook; a healthy plugin does not certify custom hooks outside its package.

Classify a reported error before changing settings:

| Evidence | Required response |
|---|---|
| Stop reports `[DENY] lint failed with exit code ...` | Inspect the configured linter's diagnostics in the target project and fix the reported violations. The hook can intentionally block through JSON while exiting 0; this is not a crash. Do not set the suggested opt-in automatically. |
| Traceback, malformed response or timeout | Reproduce against the named entrypoint in an isolated fixture; repair its owner under `https://github.com/GrupoUS/graph-powers/blob/main/hooks/AGENTS.md` or the custom hook's own contract. |
| `SKIP_UNTRUSTED`, unavailable tooling or internal-error summary | Record a skipped/unverified check, not passing lint. Resolve trust with the operator or repair the named prerequisite. |
| Source tests pass, but the error names an older cache | Verify installed bytes/version, update through the client's native route and reload. A source fix alone has not updated that process. |

For a hook repair, follow `https://github.com/GrupoUS/graph-powers/blob/main/hooks/AGENTS.md` and reuse `https://github.com/GrupoUS/graph-powers/blob/main/hooks/test_hooks.py`; use the owner's tests
for custom hooks. Cover legitimate input, deliberate denial and malformed input, including valid
JSON that is not an object (`null`, arrays and scalars) and invalid nested field types. Test backend
timeouts and permission failures; total attempts plus startup must fit the registered client timeout.
Use disposable homes/projects and simulated external services so probes cannot update plugins,
format user files, send notifications or modify real logs. Do not replay every hook against the
operator's home as a smoke test.

After correction, rerun the original failing case and the applicable regression suite. Keep
checker diagnostics local and redact sensitive content from reports. Preserve the lifecycle
boundaries in `https://github.com/GrupoUS/graph-powers/blob/main/hooks/AGENTS.md`: subprocess success does not prove Desktop blocking parity,
and Grok's passive Stop is not an enforced gate.

## Step 9 — Install and prove the selected clients

Use an explicit target. `--target all` covers Claude, Codex, Cursor and Grok; it does **not**
include Hermes or Zed and is unsuitable when it would mix native and clone Codex installations.
Install → verify that client's package/direct guardrail probe → apply the chosen posture → reload
and prove live hook execution. Package checks do not certify an already-running client.

### Claude Code — native plugin

```bash
claude plugin marketplace add GrupoUS/graph-powers
claude plugin install graph-powers@graph-powers --scope <SCOPE>
python -X utf8 "<PLUGIN>/bin/verify-hook-clients.py" --client claude --scope <SCOPE> --project-dir . --expected-version <VERSION> --probe-guardrail
bun "<PLUGIN>/bin/graph-powers.mjs" --target claude --scope <SCOPE> --skip-marketplace --autonomy <MODE>
```

Skip marketplace registration/installation when already valid. Use the exact scoped package
reported by the client. Prefer user scope; project/local scope is an explicit exception.
The installer verifies the package before applying permissive posture. Restart Claude afterwards.

### 9a — Codex settings

Preserve the active `CODEX_HOME`, native installation, sandbox/approval settings and manual model
choices. Keep shared settings in its global `config.toml`; merge rather than replace.
Do not set full access, turn off hook trust, or select an Ultra/model profile to make setup pass.

### 9b — Codex home preflight

```bash
python -X utf8 "<PLUGIN>/bin/verify-hook-clients.py" --client codex-home --project-dir .
```

Resolve `BLOCKS` before installation. A `RISK` can mean an inert guardrail and prevents claiming
that protection. Attribute each entry to its owner; preserve unrelated hooks and settings.

### 9c — One Codex route

**Native preferred:**

```bash
codex plugin marketplace add GrupoUS/graph-powers
codex plugin add graph-powers@graph-powers
codex plugin list --json
```

Refresh `<PLUGIN>` from the newly installed native `source.path`, then emit roles from that source:

```bash
bun "<PLUGIN>/codex/native-plugin.mjs" --plugin "<PLUGIN>" --out "<CODEX_HOME>/agents"
python -X utf8 "<PLUGIN>/bin/verify-hook-clients.py" --client codex --codex-route native --project-dir . --expected-version <VERSION> --probe-guardrail
```

The native manifest does not register agent roles itself. `--out` emits runtime-ready companions
without a second hooks/skills install; do not copy portable TOMLs directly. Preserve existing role
settings and check generated instructions contain no unresolved `CLAUDE_PLUGIN_ROOT` token.
Codex's per-role read-only/leaf limits are advisory where the runtime lacks enforcement.

**Clone fallback**, only when native installation is unavailable or a project-scoped copy is needed:

```bash
bun "<PLUGIN>/bin/graph-powers.mjs" --target codex --scope user --autonomy <MODE>
python -X utf8 "<PLUGIN>/bin/verify-hook-clients.py" --client codex --codex-route clone --project-dir . --expected-version <VERSION> --probe-guardrail
```

Use `--scope project` instead of `--scope user` only for the explicit project-copy exception;
the default user route installs both global components and the local project pointers.
Project scope limits the Codex harness placement, not every wrapper side effect: use guarded
autonomy when the request excludes creating machine-wide operator defaults.
The `--codex-route clone` check above validates the **user** manifest only. For project scope,
use `--package-root "<PLUGIN>"` instead for package-only proof. Separately require the project's
`.graph-powers/installed.json` to be complete, at the target version, with its recorded paths
present and hook commands in `.codex/hooks.json`; then prove the runtime in 9e. This local-manifest
check is not automated by the shared verifier. Report `UNVERIFIED` if it cannot be completed;
do not substitute a passing global installation.
Never enable both routes. For an approved migration, use the manifest-backed `--uninstall` path
before installing the chosen replacement; preserve third-party hooks and adapted rules, then
re-emit native companions and restore project pointers. Never delete the shared hooks file.
A native install uses the client update path; clone `--update` never targets a marketplace cache.

### 9d — Cross-platform homes

Validate commands/interpreters for the actual OS. A synced path or trust record from another
machine is not proof. Keep credentials, machine-specific configuration and model caches separate;
use client-supported platform-specific hook commands when needed.

### 9e — Codex runtime proof

Restart the affected process, approve the actual hooks in `/hooks`, then verify a harmless turn.
Installation does not grant hook trust. For CLI, use `codex doctor` and a minimal `codex exec`
only when available/authenticated; capture actual hook execution, not just the model's answer.

For Desktop, prove the active app-server/home and current plugin from a **new Desktop task** after
a full restart. A passing fresh CLI process does not certify an already-open Desktop task.
When hook telemetry is unavailable, report `UNVERIFIED` instead of borrowing the CLI result.

### 9f — Codex recovery, only on failure

| Evidence | Next action |
|---|---|
| Error names an old native cache; inventory points to a newer one | Restart the affected task/client once; do not rebuild the deleted cache |
| Duplicate native/clone registrations | Use the approved manifest-backed migration in 9c |
| Untrusted hooks | Review and approve them in the client; do not bypass trust |
| Missing interpreter/entrypoint or malformed config | Repair the named, owned entry from its backup and recheck 9b |
| Model cache failure before the first turn | Diagnose the named cache/version; preserve credentials and native installation |
| Failure remains after restart and targeted repair | Report the exact failing stage; stop blind reinstall/restart loops |

### 9g — Cursor

Install Graph Powers through Cursor's marketplace first. `--target cursor` configures posture;
it does not install the plugin. Verify the cache selected by the shared verifier:

```bash
python -X utf8 "<PLUGIN>/bin/verify-hook-clients.py" --client cursor --project-dir . --expected-version <VERSION> --probe-guardrail
bun "<PLUGIN>/bin/graph-powers.mjs" --target cursor --autonomy <MODE>
```

Preserve IDE and CLI settings. Reload the full window. A team-enforced approval policy must be
handled by its owner. Never add a user hook file that bypasses the plugin.

### 9h — Grok

Use the existing native package or one supported clone path; preserve `GROK_HOME`.

If a native package exists, use Grok's supported install/update path when needed and run the version
and guardrail check below **before** applying posture. The wrapper reuses a valid native package;
it does not guarantee an upgrade. For a clone route without native registration, run the installer
line first, then the same check: the wrapper validates the chosen source before configuring posture.

```bash
python -X utf8 "<PLUGIN>/bin/verify-hook-clients.py" --client grok --project-dir . --expected-version <VERSION> --probe-guardrail
bun "<PLUGIN>/bin/graph-powers.mjs" --target grok --autonomy <MODE>
```

The installer validates the selected package before permissive posture and keeps discovery wired
under guarded policy. Hooks remain in the canonical `https://github.com/GrupoUS/graph-powers/blob/main/hooks/hooks.json`; do not create a second
list. Restart Grok after installation/update; the background updater does not replace its cache.

### 9i — Hermes

Static development checks run with the reviewed source checkout as the working directory.
`<SOURCE>` is its absolute path, not an installed Hermes package; these development scripts are
not included in the distribution. The generated candidate is at its `hermes/package` path:

```bash
bun "<SOURCE>/hermes/install.mjs" --package-only
bun "<SOURCE>/hermes/install.mjs" --check
python -X utf8 "<SOURCE>/.github/test_hermes.py" --static
python -X utf8 "<SOURCE>/bin/verify-hook-clients.py" --client hermes --hermes-proof static --plugin-root "<SOURCE>" --package-root "<SOURCE>/hermes/package" --expected-version <VERSION> --json
```

Static proof compares package bytes and provenance with the trusted source generator. It never
imports the plugin, runs Doctor or scans/installs anything; PASS keeps runtime `UNVERIFIED`.
The default Hermes result in `--client all` has the same static meaning.

Native installation is a later, separately approved sandbox task: use disposable credential-free
HOME/HERMES_HOME, an approved package source at a full commit SHA and `--no-enable`. Match the
exact package bytes to the scanner result before any import or enablement. DANGEROUS stops;
CAUTION needs an explicit human decision. Preserve canonical provenance separately from any
sandbox fixture revision. Then prove native installed metadata/identity, authorized Doctor,
fresh loads of planning/plan/agent-explorer and profile isolation.

Runtime validation is not implemented. The reserved `--hermes-proof runtime` route (also selected
by the test runner's `--runtime`) requires explicit installed `--package-root` and
`--expected-version`, then fails nonzero with the pending proof requirements. It cannot certify
an installation. Graph Powers hooks remain `NOT ENFORCED`; model/tool frontmatter is descriptive,
and the parent must apply actual host policy and approvals.

### 9j — Zed

Zed's native agent has no Graph Powers hook target. Report instructions/editor integration
separately and hooks as `NOT ENFORCED`. An external agent launched by Zed is verified as its own
client, not as Zed-native hook coverage.

## Step 10 — Verify once after the final relevant change

```bash
python -X utf8 "<PLUGIN>/bin/verify-hook-clients.py" --client <CLIENT> --project-dir . --expected-version <VERSION> --check-posture --autonomy <MODE> --probe-guardrail
```

Repeat for requested hook clients only, adding the chosen scope/route where needed. Use Hermes'
installed-package check in 9i separately. `--check-posture` covers Claude, Cursor and Grok; Codex
posture/runtime still needs the direct proof in 9e. The verifier derives current registration
counts from manifests; never substitute a historical hard-coded count.

Check only what this setup touched:

1. Effective config path/branch/prefix matches Step 3.
2. Every requested client is present and verified; absent clients are not a passing installation.
3. Changed instruction files have no unresolved placeholders or broken links. If nodes changed,
   run intent-layer `check` and resolve real failures rather than excluding them.
4. Changed project tooling runs its declared focused gates. The exact config must be trusted
   through `https://github.com/GrupoUS/graph-powers/blob/main/hooks/command_trust.py` before automatic configured commands execute; changed config
   invalidates its digest. Do not create trust on the operator's behalf.
5. After reload, confirm one real role/skill invocation in each requested runtime. Check workflows
   only where the runtime supports them; otherwise retain the documented fallback.
6. Report Desktop separately and preserve Hermes/Zed `NOT ENFORCED` boundaries.
7. For hook repairs, include Step 8a's regression and original-error reproduction results;
   distinguish corrected source, updated installed package and reloaded runtime.

Where supported, the verifier's guardrail probe uses a synthetic command/config; it creates no commit. Run the
plugin's full hook/regression suite only when its source or wiring changed, not for every host
installation. Reuse valid evidence until relevant files, config or environment change.

## Step 11 — Report, and stop

Return a compact table: client, source/version/route, package proof, hook execution/trust,
posture and reload result. Add project changes, focused gates, deliberate skips, unresolved
requirements and backup locations. Distinguish `PASS`, `SKIPPED`, `UNVERIFIED` and
`NOT ENFORCED`; never call partial installation complete.

Leave reviewable changes in the working tree. No staging, commit, push, publication, new recurring
automation, or additional cleanup follows setup without its own authorization.
