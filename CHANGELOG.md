# Changelog

## 1.10.0 — A direction pass that refuses the defaults

### Added — `skills/designer`, loaded by `/design` before `uxmaster`

A visual-direction skill that runs before any code: ground the surface in its subject, mine the
subject's own world for material, diverge into three directions that differ in kind, commit one
signature, and run the mirror test — the any-brief test that catches a plan any brief in the
category would have produced, and remove-one-accessory. It writes a direction contract that
`/design § 3` builds from and `§ 5` measures against.

The point is freedom with a floor. Where the brief leaves an axis open, the axis is spent on the
subject, never on the category habit; where the brief pins a look, the brief wins, including when
it asks for one of the catalogued defaults. The floor — WCAG 2.2 AA numbers, the project's tokens,
no invented claims — is held without commentary. `references/defaults-catalogue.md` carries the
tells axis by axis (the three AI looks, the indigo gradient, the coloured left border, Inter as the
only decision, the fade-up on every section, the headline that belongs to anyone) with the rewrite
for each, measured against sixteen sources; `references/mirror-test.md` carries the two tests with
one worked contract.

Synthesised from Emil Kowalski's `emil-design-eng` and `apple-design`, Anthropic's
`frontend-design`, the craft floor impeccable used to supply, and the official and practitioner sources the
catalogue lists. It picks the direction; its own craft passes (Removed, below) build to it, and
`animate` — with Emil's skills when they are installed — tunes the motion.

### Removed — the `impeccable` dependency

`/design § 3` no longer delegates to the external plugin. The craft passes are `designer`'s own:
`references/craft-passes.md` defines `shape`, `build`, `audit`, `harden`, `typeset`, `layout`,
`adapt`, `optimize`, `bolder`, `quieter`, `colorize` and `polish` — what each asks, reads, changes
and when it is done, who runs it (`graph-powers:ui-ux-designer` read-only for `audit`,
`graph-powers:frontend-specialist` for the rest) — and `references/craft-floor.md` the checks every
pass is measured against on the built result. The `animate` pass is the `animate` skill in build
mode. Written for this harness rather than copied: a pass that needed a package runner, a plugin
install and a hook merge in every project put three refusable setup steps in front of a design task.
`AGENT_SETUP.md § Step 1`, README, NOTICE, the docs and the skill matrices no longer name it; the
hook test fixtures that used its install command as a sample package-runner call use
`agent-browser` instead.

### Added — `skills/animate`, four modes on one rulebook

A motion skill that starts from the question the rest of the field skips: should this animate at
all? The gate — frequency tier, named purpose, function — runs before any ingredient, and a request
that fails it gets a plain refusal and the non-motion alternative instead of a beautiful easing on
a command palette. Past the gate, the rulebook is Emil Kowalski's: `transform` and `opacity` only,
never `scale(0)`, never `ease-in` on UI, three strong curves as tokens, per-element duration
budgets under 300ms, springs for gestures, reduced motion and hover gating shipped with the
animation. Four modes are verbs on that one rulebook — **build** writes the code from
`references/recipes.md` (button press, dropdown, tooltip, modal, drawer, toast, accordion, stagger,
hold-to-confirm, tab indicator, scroll reveal, drag-to-dismiss, masked crossfade, WAAPI);
**review** returns a Before · After · Why table and Block or Approve (`references/review.md`);
**audit** surveys a codebase read-only, ranks by leverage and writes self-contained plans into
`paths.planDir` (`references/audit.md`); **find** proposes at most 5–7 opportunities and lists the
candidates it rejected, with the gate question that killed each.

Merged from four skills of emilkowalski/skills (MIT, credited in NOTICE) — `animate`,
`review-animations`, `improve-animations`, `find-animation-opportunities` — which carried the same
frequency table, the same three curves and the same duration budgets in four copies and differed
only in the verb. One copy of the rulebook lives in `SKILL.md`; the block list is one table with
three readers. Read-only is stated honestly: a skill cannot restrict its own tools, so review, audit
and find run inside `ui-ux-designer`, whose `disallowedTools` is what keeps the promise. Wired
from `/design § 3` before the `animate` craft pass, from `/pr-review` track 3D when a diff touches
motion, and from the skill-domain matrix. Nine eval cases: five modes and refusals, four borders
(`designer`, `/debug`, `mobile-developer`, the project's Astro route doctrine).

### Changed — `/design § 1` runs the five moves; `§ 3` loads `animate`, and Emil's skills when installed

Surgical work inherits the surface's world and runs moves 1 and 5; structural work runs all five
and offers the category standard as the explicit exit. `emil-design-eng` and `apple-design` are
declared optional external skills in `check_wiring.py` and README, loaded beside the plugin's own
`animate` skill before the `animate` pass when present and named as absent otherwise. The skill-domain matrix, the WISC context load
and the invocation order name `designer` ahead of `uxmaster`.

### Added — `skills/intent-layer`, run by the setup playbook at step 4b

The hierarchy of `AGENTS.md` files — the root node plus a child node in every subtree that earns
one — is now built, grown and audited by a skill, and the setup playbook runs it after the root pair
is rewritten. The harness already read those nodes (`/prime` loads `${paths.backendRoot}/AGENTS.md`
and the nearest node under `${paths.frontendRoot}`; `explorer`, `debugger` and
`frontend-specialist` load the nearest one before touching a subtree) and every one of those reads
returned nothing in a repository that never grew the layer.

Adapted from crafter-station's `intent-layer` (MIT; see `NOTICE`). Three changes are the point of
the adaptation. The upstream shell scripts became one Python standard-library script,
`scripts/intent_layer.py`, with `state` and `measure` as reads and a third subcommand upstream does
not have: `check`, a gate that fails on an orphan node, a dangling downlink, a node over 4k tokens,
a `{{placeholder}}`, a child with no purpose line, or a root-to-leaf chain over the 32 KiB at which
Codex stops reading `AGENTS.md` files. The upstream "one root file — pick `CLAUDE.md` or
`AGENTS.md`" rule became this harness's root pair: `AGENTS.md` is the root node, `CLAUDE.md`
beside it is behaviour and pointers, and a `CLAUDE.md` in a subdirectory is reported as a node
three of the four harnesses never read. And the root's `## Intent Layer` section became a row in
the `Where things live` table the root template already carries, so the downlink index has one
home.

`AGENT_SETUP.md § 4b` runs it at install, `§ 10` runs `check` as a verification, `§ 11` reports
it; `/evolve § 5` loads it when a learning lands in a subtree with no node or a node past its cap.
The skill's own script is allowed by the Bash approver under `guarded` the way `turbo_dry_json.py`
is, and `hooks/test_hooks.py` proves each of the seven `check` failures fires and that the
legitimate tree passes. Nine eval cases sit on the borders with `/prime`, the rules layer,
`skill-improve` and a single `/evolve` capture.

### Changed — `second-opinion` is `evaluator` Mode 5

The blind review moved from a standalone skill into the agent that already judges.
`skills/second-opinion/` is gone; `graph-powers:evaluator` gains a fifth mode, Second Opinion, and
its description carries the trigger the skill used to own — a fix that keeps not sticking, a
decision that feels right mainly because the thread has been staring at it. The rubric's Mode 5
section holds both halves: what the agent refuses to read (`HANDOFF.md`, `PROGRESS.md`, any record
of prior attempts) and what the caller sends (the artifact by path, the decision stated neutrally,
the real constraint, the three-part answer shape — verdict, strongest argument against, the one
settling check).

Three things the move measured. The skill's published invocation never ran as written:
`--disallowedTools` is variadic and swallowed the question placed after it — on CLI 2.1.245 the
CLI reported each word of the prompt as a permission deny rule matching no known tool, and exited
0 having asked nothing. The question now goes first. Blindness needs no separate session: a
subagent starts from its prompt and nothing else, so the default engine is an ordinary spawn, and
the headless `claude -p "<question>" --agent graph-powers:evaluator` run stays for the one thing
only print mode has, `--max-budget-usd` — measured to run the agent on its own declared model,
$0.11 for a one-word reply. The coreutils `timeout` wrapper is gone: cardinal 8, it does not exist
on Windows; the Bash tool's own timeout is the wall-clock cap, and `AGENT_SETUP.md` drops the row
that installed it.

Call sites rewired: recovery Step 4, the skill-domain matrix, `/debug` § 0 and § 7, the debugger
and planning escalation tables, and the guardrail docstring that named the headless wrapper.
Listing budget: −344 chars.

### Added — `skills/landing-page-design`, the page system, adapted from elayadesign

The landing-page layer stops being an install-by-copy dependency and ships with the plugin as an
adapted work (MIT, attributed in `NOTICE`). What it keeps whole is the page system: the intake in
one batch, the twelve-section order, the four layout types, the conversion and copy rules, the
build order, the index decision, and the ship floor of content realism, states and the
landing-specific ship list. What changed is ownership: the upstream visual canon — a font
whitelist, six hex backgrounds, an icon set, one curve, a mandatory word-by-word tagline reveal —
moved to `references/house-canon.md` as a fallback behind the project's design authority, the
`designer` direction contract and the `animate` rulebook, each value tagged craft or house taste
with its reason, and the catalogued defaults among them (gradient text, glass, the fade-up on
every section) named as such. The description was narrowed from "any web UI" to landing and
marketing surfaces, so it no longer out-triggers `designer` on a dashboard.

Measured against the siblings before writing: 45 collisions, 5 of them P0 in the visual canon,
all resolved by precedence rather than by a second copy of a value. Two upstream claims corrected
against 2026 sources — Google removed FAQ rich results in May 2026, and `text-wrap: pretty` is
Chromium-only — and one upstream rule inverted: "organic" fake numbers made invented proof more
plausible, which is the honesty gate's exact failure; numbers are now real or absent. Eight eval
cases sit at the real borders; the round is in `skills/skill-improve/learning.md`.

### Removed — the `landing-page-design` external dependency

`AGENT_SETUP.md § Step 1` no longer installs it; its preflight row now reads `SHADOWS` when a
personal copy under `~/.claude/skills` is still present, because a personal-scope skill of the same
name wins over the plugin's under a bare `Skill("landing-page-design")`, and the step carries the
removal command. `check_wiring.py` drops the `EXTERNAL_SKILLS` entry; README,
`docs/ARCHITECTURE.md § 7` and `docs/AUDIENCE.md` record the reversal and what measured it.

### Removed — the standalone `astro` skill

The ten-file framework manual (46,531 B, 1,034 non-empty lines) mixed the small delivery floor a
landing page needs with Content Collections, Actions, Sessions, middleware, adapters, CSP, version
watchlists and troubleshooting. The useful subset now lives once in `landing-page-design`: static
`.astro` sections, native controls or a local script before a client island, deliberate hydration,
responsive `astro:assets` images and no router, adapter or server rendering without a concrete
requirement. `/verify` keeps using the project's declared gates; deeper framework work reads the
project rules and official Astro documentation on demand. The standalone skill and all nine of its
references are gone.

### Changed — `skill-improve` Mode B learns from its own ancestors, and the eval runner stops lying

The global `~/.agents/skills/harness-audit/` (2026-08-19, zero rounds in its `learning.md`) was
diffed section by section against Mode B. Nothing of substance had been lost in the 2026-08-20
merge — every drop was portability or a recorded decision — but the comparison exposed what neither
copy had: the ancestors themselves. Both pre-merge skills are still served from the personal layer
(`~/.claude/skills/harness-audit` and `~/.claude/skills/skill-creator`, symlinks into
`~/.agents/skills/`), listed in every session beside `graph-powers:skill-improve`: three
descriptions claiming the same phrases, the trigger collision Mode B exists to detect, with the
answer already known. Phase 3 now crosses every layer that serves a listing (`~/.claude/skills`,
`~/.agents/skills`, the plugin cache, the marketplace clone) and greps each for the retired names
that `learning.md`, `CHANGELOG.md` or `NOTICE` record; a hit is `REMOVAL_CANDIDATE` with double
evidence and is never unlinked by the skill. Three eval cases cover it — `pos-ancestor-collision`,
`pos-escalate-a-to-b` for the one border the merge created, and `pos-periodic-audit` for the
open-ended prompt the global's prose used to carry — each run against a passing and a failing
response.

A five-lens review with one refuter per P0/P1 (13 agents, 1.06M tokens) returned 62 findings, 6
confirmed on disk. Inside the skill, all fixed: `init_skill.py` scaffolded a `description` that was
not YAML — unquoted, with a colon-space — and `quick_validate.py` passed it, because the validator
tested for the substring and never the shape; the template is quoted and the validator now rejects
that shape. The two caps were two quantities all along — 1,024 on `description` alone in the
validator, 1,536 on `description` plus `when_to_use` in the listing gate — and Round 1's "only the
1,536 is enforced by anything" was wrong; both are in the table now. The settings-JSON gate raised
`FileNotFoundError` in this very repository, which has no `.claude/settings.json`, six lines under
a red flag that says "never a stack trace"; it is a fail-open one-liner, measured absent, valid and
malformed. One assertion regex was wrong in both directions under a note that said it had been
tested; seven assertions were rewritten and every one run against a passing and a failing string.

`run_evals.py` — which `NOTICE` called unmodified upstream code, and which never existed upstream
(no commit in anthropics/skills touches that path; `NOTICE` now says so, and says which scripts are
modified from which revision) — gains `--response-dir`: every case against its own
`resp-<case-id>.txt`, one line per case, a missing response or a file with zero cases counted as a
failure, exit 0 only when every case passes. That is the per-case discipline without the shell loop
the global carried, which cardinal 8 bans. A failed `critical` assertion exits 1 at any threshold;
an unknown assertion id, a missing `check`, a colon-less check and a value the check cannot parse
are red rows that name the defect, not tracebacks. Measured on 12 cases in eight directions.

Also in Mode B: a first-round branch for the auditor memory (`MEMORY.md: absent — first round in
this repository` replaces the paste, never an empty file); a host-project audit records its round in
the host's `.claude/audit/learning.md`, because the plugin's own `learning.md` is overwritten by the
next update; `--phase N` is defined; the Phase 5 prompt says the artefacts are on disk rather than
"attached"; the report names the layers the scope did not cover; `.claude/audit/` is gitignored
here. The description gains the proactive trigger (`before adding an agent or skill and after a
plugin or model upgrade`) at +2 chars net, paid for by trimming.

Reported, not applied, because they live outside the skill: `agents/skill-improver.md` carries a
stale claim about one machine's `SubagentStart` matcher (it lists `skill-improver` today); the
rubric's W2c and its known-failure catalogue cite another repository's paths; rubric and agent name
`agentRouting.aliases`, a key the schema does not declare. Round 7 in
`skills/skill-improve/learning.md`.

## 1.9.5 — Explicit model tiers and low-resource JS/TS gates

### Changed — JS/TS verification no longer fans out across the machine

The inferred host-project gates are now native tsgo forced through Bun with `--checkers 1`, serial
`bun test --smol` for the final suite, and changed-only fail-fast tests during fix loops. Unbounded
`bun test --parallel` was removed as a default because Bun 1.4 can start one process per CPU core.
Whole-project gates run once at phase/final boundaries instead of once per implementation task.

The Bash guardrail denies Node's test runner, legacy `tsc`, bare `tsgo` (the npm launcher has a Node
shebang), and unbounded Bun workers even under autonomous mode. Plugin ESM verification and CI now
run through Bun 1.4; the installer remains Node-compatible, but Node is not a gate executor. The
installer skips unsafe package scripts and preconfigures Bun + `tsconfig.json` projects with the safe tsgo command. Setup, compatibility limits
and official sources live in `skills/debugger/references/low-resource-js-ts-gates.md`.

### Fixed — the model tier is declared everywhere it is spent

An agent's `model:` line is the tier: `opus` for the nodes that judge, design, fix and verify,
`haiku` for the scouts. Two surfaces spent a different one than the line says.

### Fixed — a workflow spawned every specialist on the session's model

`agent()` inside `workflows/*.js` resolves `opts.model` and never opens `agents/*.md`. Eleven of
the twenty-four call sites in `ultra-build`, `ultra-plan` and `ultra-verify` passed none, so
`frontend-specialist` — `model: opus` in its own frontmatter — implemented on whatever model the
user happened to be driving, `project-planner` and `evaluator` judged on it, and `librarian`, a
`haiku` scout, researched on it. The cheap lane failed the same way in reverse: a caller that
passes `model` by hand at an `Agent` spawn site overrides frontmatter that was already correct, and
one session spawned `explorer` on `opus`.

Every workflow call now states its model through an `M()` helper drawn from the frontmatter tier; a
deliberate downgrade for a mechanical unit (gates, re-gates) stays written literally.
`.github/check_workflows.mjs` reads the resolved `opts` of every stubbed spawn — so the dynamic
call sites are covered too — and fails a call with no `model`, or one that spawns a light agent on
a heavier model than its own file declares. `references/shared/070` §8, `020` §2 and `130` carry
the rule; cardinal 6 of `AGENTS.md` now covers both ends of the ladder.

### Added — `codex.models`, one Codex slug per tier

Generated Codex subagents all took the project's single `codex.model`, so twelve deliberately
different agents came out of the generator on one model and only their reasoning effort differed —
and a cheap-effort call on the strong model is still billed as the strong model.

`codex.models.heavy` / `.standard` / `.light` map the Claude family each source agent declares onto
this project's slugs (`opus` → heavy, `sonnet` → standard, `haiku` → light), falling back to
`codex.model` for a tier left empty and to nothing at all when neither is configured. `node
codex/install.mjs` now reads the project config itself, so a direct invocation generates what the
`graph-powers` CLI generates instead of subagents with no model line at all.

For the native surface, `node codex/native-plugin.mjs --models heavy=…,light=… --out <dir>` writes
the agents with those slugs into a directory the operator names. `--models` without `--out` is
refused: a Codex slug is account-specific, and `codex/native-agents/` is tracked.

## 1.9.4 — Turbo `--dry=json` on a pipe is denied; Codex native agents drop Claude model families

Agents running `turbo run test --dry=json` (or `bun run test --dry=json`) through the Bash
tool dumped core: turbo 2.x panics on EPIPE (`failed printing to stdout: Broken pipe`), the
JS wrapper `process.kill(pid, SIGABRT)`, bun abort()s. The Bash tool is that pipe.

`smart_bash_approver.py` now denies those forms even under `autonomous`. The replacement is
`skills/debugger/scripts/turbo_dry_json.py`, which writes JSON to
`.graph-powers/cache/turbo-dry.json` and prints the path. Declared test gates are unchanged.
Debugger anti-pattern 37 stops treating the Node SIGABRT as a Node bug.

### Fixed — Codex native plugin spent the Spark / Bengal Fox window

Codex discovers `.codex-plugin/plugin.json` before `.claude-plugin/plugin.json`. This plugin
had no Codex-native manifest, so the CLI loaded `agents/*.md` including `model: haiku` and
`model: opus`. Those names are Claude families. Codex has no haiku; the cheap-model fallback
is Spark, whose rate-limit bucket is `codex_bengalfox` ("Bengal Fox") — a separate pool from
the user's own Codex/Pro limit, and the one the status line then showed.

`.codex-plugin/` now exists. Native agents are generated from `agents/*.md` with Claude
model lines stripped (`codex/native-agents/`), so a spawned child inherits the session model
and that session's limit. The clone generator already refused to write those names into
TOML; it now also drops a `codex.model` that is itself a Claude family. Gate:
`.github/check_codex_native.py`. Regenerate with `node codex/native-plugin.mjs`.

## 1.9.3 — `/verify` is quick by default; Turbo gates get `--filter`

Everyday `/verify` (no arguments) is **`quick`**: process gates + floor. The explorer /
evaluator / security / design batch runs only for `/verify full` or `/verify loop`. That
batch was the RAM spike, not Bash.

The JS/TS resolver now scopes a declared `turbo run …` with `--filter=<apps|packages name>`
from the change set, keeps Vitest as `bun run test` (never bare `bun test`), and refuses to
infer Bun tests over a Python/`null` runner. Resolver: `references/shared/130-bun-tsgo-gates.md`.

## 1.9.2 — `landing-page-design` joins the required design layer

`/design` now loads `Skill("landing-page-design")` whenever the surface is a landing or marketing
page: intake, section order, conversion copy, and the visual canon for type, spacing, radius,
background, hero and motion. `uxmaster` still owns the direction and `impeccable` still owns every
craft pass — the new skill sits between them and owns the page system.

It is the third external dependency and the first that is a **skill folder rather than a plugin**
([elayadesign/ai-design-skills](https://github.com/elayadesign/ai-design-skills), MIT, one
`SKILL.md`). It is not vendored, for the same reason the other two are not: the file is meant to be
forked at its Design Values section, and a copy stops tracking upstream the day it lands. Upstream
spells the install with `curl`, `cp` and `/tmp`, none of which runs on the Windows shells this
plugin supports; `AGENT_SETUP.md § Step 1` carries a `python -X utf8 -c` equivalent that writes both
`~/.claude/skills` and `~/.agents/skills`, and re-running it is the update. Where the skill's values
meet the project's, the project's design rule still wins and the conflict is reported.

`check_wiring.py` gains `EXTERNAL_SKILLS`, the bare-name counterpart of `EXTERNAL_ROUTES`: a
dependency that installs as a skill folder is invoked with no namespace and would otherwise read as
a missing `skills/<name>/SKILL.md`. Declaring it is what the gate asks for; it does not verify the
other repository.

**Context budget, paid rather than raised.** Wiring the skill in left 47 B of floor headroom, so two
duplications went out in the same change — neither a command losing content, both a second copy of
something another file already owns:

| Cut | Owner it duplicated | Command floors charged |
|---|---|---|
| The 21-row placeholder table in `000-config-loader.md`, an identity mapping of `${a.b}` → `a.b` | `schema/config.schema.json`, the parameter contract | 9 |
| The domain-skill enumeration in `005-superpowers-bootstrap.md` | `120-skill-invocation-order.md` | 10 |

`${rulesDir}` → `paths.rulesDir` survives the first cut, because it is the one mapping that is not
identity. Floor: 329,953 B → 322,414 B.

**And 30,604 B that were never a real load.** `/verify § 0.3 Database` fires only when the change
set mapped the `schema` surface; `/implement § 7.5` step 3 fires only on the `optIn` apply branch.
In both, the condition sat on the line *above* the `Skill("performance-optimization")` call, and
`check_context_budget.py` reads the line rather than the section — deliberately — so it charged
15,323 B to every `/verify` on a passing typecheck and every `/implement` with no schema work. The
condition now sits on the line that orders the load, which is the sentence both steps should have
been writing anyway. Nothing changed for a run that does hit the branch: it loads the same skill.

`/perf` keeps it in the floor, correctly — that command loads it on every run.

| Command | Floor before | Floor after |
|---|---|---|
| `/verify` | 44,894 B | 29,591 B |
| `/implement` | 49,620 B | 34,319 B |

Floor total: 329,953 B → **291,810 B**. `FLOOR_CEILING` drops 330,000 → 295,000 in the same commit,
so 3,190 B stays spendable and the other 35,000 B cannot be spent without someone noticing.

## 1.9.1 — Bun 1.4 + tsgo is the inferred JS/TS gate

`/verify` and the skill matrix now route undeclared JavaScript/TypeScript type-check and
unit tests through the JS/TS resolver: native `tsgo` and `bun test --parallel`, never
`npx tsc` or `node --test`. A project that already names `tooling.commands` is unchanged.
The resolver lives in `references/shared/130-bun-tsgo-gates.md`. Example config:
`examples/config.bun.json`.

## 1.9.0 — Database verification is a gate, and apply is not

`/verify` reports a **Database** row when the `schema` surface moved: `PASS` / `DRIFT` /
`UNREACHABLE` / `NOT DECLARED` / `SKIPPED`. The command is `${database.commands.status}` from
`.graph-powers/config.json`, never an ORM the harness guessed. Exit code alone does not name
drift — common status tools exit 1 for a down database too — so classification is by output
class (skill **Schema state**). `DRIFT` prints `${database.commands.apply}` and a rollback line
and returns `NEEDS-WORK`. `/verify` never applies, under either `applyPolicy` value.

Apply is `/implement` § 7.5: default `applyPolicy: never` prints and stops; `optIn` runs apply
only after explicit current-turn approval, then re-runs status and refuses to claim success
unless that re-run is `PASS`.

The public contract is a new optional `database` block (`engine`, `commands.status|generate|apply`,
`applyPolicy`). Setup fills it when the project has a `schemaRoot`; a static site still omits it.

## 1.8.6 — Grok CLI is the fourth harness, and config.toml is the one that asks

Grok Build reads Claude marketplaces, plugins and `hooks/hooks.json` already. That is not enough:
the stdin payload is camelCase (`toolName`, `toolInput`) and the shell tool is
`run_terminal_command`, so a gate that only looked at `tool_input.command` would fail open.

`_config.py` now canonicalises Grok names onto the Claude ones the gates already branch on, and
`emit_pretool_deny` writes both Grok's top-level `{ "decision": "deny" }` and Claude's
`hookSpecificOutput`. There is no `hooks-grok.json`. `grok/install.mjs` emits `.grok-plugin/`
and merges `~/.grok/config.toml` additively: `[ui] permission_mode = "always-approve"` (user
file only), web_fetch, subagents, marketplace source, plugin enablement. It does not TOML-deny
git commit. `--target grok|all` joins the installer; `both` stays Claude + Codex. Auto-update
asks `grok plugin update` when the CLI is on PATH.

## 1.8.5 — Cursor is the third harness, and the IDE file is the one that asks

Cursor's confirmation flood was never `cli-config.json`. The Agent Run Mode lives in
`~/.cursor/permissions.json` (`approvalMode: unrestricted` is Settings → Agents → Run Everything).
The CLI file can already be unrestricted while every Shell call still waits on Auto-review.

Cursor is now generated from the Claude Code artefacts, the same way Codex is. `cursor/install.mjs`
translates `hooks/hooks.json` into `hooks/hooks-cursor.json` and `.cursor-plugin/plugin.json`.
PermissionRequest and Notification are skipped — Cursor has no event for them — and `preToolUse`
still runs the git gates and `smart_bash_approver`. The installer writes the IDE permission file
additively, sets `autoAcceptWebSearch` on the CLI file, and does not remove either on `--uninstall`.
`--target cursor|all` joins `claude|codex|both`. `both` stays Claude + Codex.

## 1.8.4 — Installer writes Bash autonomy instead of documenting it

`level: autonomous` with `bashDefault: ask` is a contradiction the schema allows and the hook
honours: the per-field override wins, and every unclassified command becomes
`Hook PreToolUse:Bash requires confirmation for this command. [plugin:graph-powers]`. The
installer wrote only `level` and `destructiveFloor`, left `bashDefault` implied, never created
`~/.graph-powers/config.json`, and never repaired a project file that already had the
contradiction. The playbook documented the user file as something to know, not something to
write. A person who installed the plugin and still clicked Yes on every `python3` heredoc was
running the default.

The installer now, on `--autonomy autonomous` (the default):

- writes `~/.graph-powers/config.json` if it is missing (`machineWide`, `bashDefault: allow`,
  git still `ask`)
- writes `bashDefault` / `cleanup` / `toolDefault` explicitly in a new project config
- repairs those three fields from `ask` → `allow` in an existing project config whose `level`
  is already `autonomous`, without touching git, the destructive floor, or anything else
- appends `"Bash"` to the Claude Code allowlist, and sets `permissions.defaultMode` to
  `bypassPermissions` when it was missing / `auto` / `default`, plus
  `skipAutoPermissionPrompt: true`

`--autonomy guarded` writes none of that. `AGENT_SETUP.md` Step 3 is the same procedure for a
session that did not run the installer, with a probe that has to print `allow` before Step 4.

## 1.8.3 — Autonomy stopped at the shell prompt

`autonomy.bashDefault` is described as the field that decides whether a session feels like work or
like clicking Approve, and it was true of `Bash` only. `smart_bash_approver` was the sole hook
registered at `PermissionRequest`, and it answers for shell commands. Every other tool call — a
subagent spawn, an MCP call, a fetch, a workflow, a file tool — reached the user as a prompt in a
repository that had already declared `level: autonomous`. The setting looked like it had stopped
working; it had never covered that half of the session.

`hooks/tool_approver.py` is that decision for everything that is not a shell command, registered at
`PermissionRequest` with matcher `*` and driven by the new `autonomy.toolDefault` field —
`allow` under `autonomous`, `ask` under `guarded`, overridable on its own like `bashDefault` and
`cleanup`. Raising it machine-wide from `~/.graph-powers/config.json` needs the same
`machineWide: true` acknowledgement the other two need.

Two things it deliberately does not do. It never answers for `Bash`: one owner per decision, and
the destructive floor and package-manager rules live in the classifier that reads the command line.
And it never reaches a call a `PreToolUse` hook already denied — `protect_files`, `graph_guardrails`
and the three git gates run first and short-circuit, so the floors are unchanged.

### Fixed — every background shell poll asked for confirmation

`hooks.json` matches the Bash lane with the string `Bash`, and the harness applies a matcher as a
regex by substring. `BashOutput` and `KillBash` match it. Their payloads carry a shell id and no
command line, so `smart_bash_approver` read an empty command and took the branch that asks —
"Hook PreToolUse:Bash requires confirmation for this command. [plugin:graph-powers]", once per poll
of a background shell, naming a command that was never in the payload. The branch existed to keep
an *unclassified* command from falling through to allow; an absent one is a different case.

A payload with no command line now produces no verdict at all. Nothing is granted that the harness
would not have granted on its own — silence leaves the normal approval flow in charge — and a real
command is still classified exactly as before.

## 1.8.2 — Codex plugin installs now carry their hooks

The Codex marketplace installed Graph Powers skills and agents but showed no Graph Powers entries
in `/hooks`. The twelve declarations lived inside `.claude-plugin/plugin.json`; native Codex plugin
discovery reads `hooks/hooks.json`. Machines that appeared covered had received their hooks from a
separate, older clone install recorded in `~/.codex/graph-powers-installed.json`.

`hooks/hooks.json` is now the single declaration used by both native plugin loaders and by the
clone-based Codex generator. The embedded copy was removed from `plugin.json`, the clone installer
still merges and unmerges exact commands without touching third-party hooks, and CI asserts that
all twelve scripts exist across thirteen event registrations. The setup playbook now separates installed,
discovered, approved and executing states, recommends native Codex installation, and includes a
manifest-backed migration that prevents native and legacy registrations from running twice.

### Fixed — Codex asked again after the Bash hook had already allowed the command

`smart_bash_approver` only ran at `PreToolUse`. That can block a command, but an `allow` does not
approve a later sandbox or network escalation; Codex then opened its ordinary approval prompt.
Worse, the hook returned plain `permissionDecision: ask` or `allow` at `PreToolUse`, values Codex
does not support there without an input rewrite, so calls were reported as failed hook runs before
continuing anyway.

The same classifier is now also registered at `PermissionRequest`. Allowed commands return the
event's `decision.behavior: allow` response and proceed without reaching the user; guarded asks
decline to decide, and destructive denials keep winning. Codex `PreToolUse` payloads now emit only
denials; ordinary allow/ask handling belongs to `PermissionRequest`. An in-family package runner
such as `bunx` under a declared `bun` project follows the same rule: guarded asks, autonomous
proceeds, another manager family is still denied.

### Added — explicit machine-wide Bash autonomy

The user config described `autonomy.level` as the operator's machine-wide posture, but the loader
stripped `level: autonomous`, `bashDefault: allow` and `cleanup: allow` before they reached any
repository. Users therefore configured autonomy once and kept receiving the guarded defaults.

`autonomy.machineWide: true` is now the explicit acknowledgement that routine Bash and cleanup
autonomy may reach repositories with no project autonomy block. It does not make git automatic and
cannot disable the destructive floor from user scope. The setup playbook also documents Codex's
`workspace-write` + `auto_review` posture and enables ordinary workspace network access, so
remaining boundary crossings are reviewed automatically rather than becoming repeated prompts.

## 1.8.1 — the Codex step assumed the Codex home was empty

`AGENT_SETUP.md § 9` was thirty-seven lines: run the installer, approve `/hooks`, gitignore two
paths. It described what the plugin writes and said nothing about what is already there — which is
where the failure lives, because the installer merges rather than overwrites and a broken entry it
inherited survives the install and gets blamed on it.

### Added — § 9a, a preflight that reads the Codex home before anything is written

Codex reads a hook's exit code as a decision: `0` succeeds, `2` denies — the prompt on
`UserPromptSubmit`, the tool call on `PreToolUse` — and anything else is an error it steps over.
So a hook whose script is not on this machine does not degrade the harness, it locks the CLI:
`python` starts, fails to open the file, exits **2**, and Codex reads a deny. Every prompt is
refused, the message names a path rather than a cause, and a fresh session behaves identically.

The preflight reports three severities against `~/.codex/hooks.json` and `~/.codex/config.toml`:
`BLOCKS` for a command this machine cannot run — a foreign-platform absolute path, a missing script,
an interpreter not on `PATH`; `RISK` for one that works here and is wrong on the machine this home
syncs to, plus a `notify` naming an absent binary and hooks declared in both files at once; `NOTE`
for hooks with no `commandWindows` and for conflict copies left by a file-sync tool. It runs again
after the install, so a new `BLOCKS` line is attributable.

### Added — § 9c, the sync hazard stated as a rule rather than discovered as a bug

`~/.codex` is a directory people point Dropbox, pCloud, OneDrive, Syncthing and Resilio at, and
what those carry between machines is one machine's absolute paths. The step now names the two
things that prevent it: a hook is written for both platforms in one file — `command` for POSIX,
`commandWindows` for Windows, which is the field Codex provides for exactly this — and the files
that describe the machine rather than the setup are never synced at all. `config.toml`,
`auth.json`, `models_cache.json`, `.codex-global-state.json`, `sessions/` and `rollouts/` are
listed by name, each with the reason.

### Added — § 9e, recovery for a CLI that is already refusing every prompt

In order, because reinstalling first is the instinct and it changes nothing — the merge lands in
the file that is denying. `codex exec --dangerously-bypass-hook-trust` runs every hook including
the unapproved ones, which is what separates a trust problem from a broken hook; § 9a names the
entry; a `hooks.json` that does not parse loads no hooks at all rather than some; and a CLI that
dies before the first turn with `failed to load models cache` has a cache written by another
version, which is a file to move aside rather than a fault to debug.

### Added — Step 10 gets a Codex check, and the report a Codex health line

`codex doctor` for the installation, then one `codex exec` turn, which prints a line per hook:
`Completed` ran, `Failed` errored and was stepped over, `Blocked` denied the turn. A hook present
in `hooks.json` and absent from every line is unapproved, and the fix for that is `/hooks`, not a
reinstall. Step 11's report template gains `**Codex health:**`, carrying the before and after
counts so a setup that repaired something says which entry and a setup that repaired nothing says
that too.

## 1.8.0 — the multi-agent /verify the reference layer had already specified

Four shipped files described a `/verify` that consolidates signals from parallel agents: `090-verdict-matrix.md:3` said it consolidates "gates + agents + reviews", `parallel-batch-contracts.md:19` listed a "Phase 8 — parallel codex review + adversarial review", `agent-handoff-contracts.md:58` described its "consolidator" reading handoff JSON, and `015-verification-gate.md:13` cited a "Phase 0". The command had five sections, zero agent spawns, and loaded none of the four. This release builds the command those files were describing, and deletes the two claims that were never true.

### Added — `references/shared/125-change-set.md`, and both commands now compute a scope

`/verify` § 2 asserted that no file outside the task's scope had changed **without the command ever computing a scope**, and `/pr-review` § 1 derived its risk from a line count and path names. The new shared reference carries the three-tier base detection `ultra-verify` already had — `git diff HEAD`, then `merge-base origin/<workBranch> HEAD`, then `HEAD~1`, with a union rule and a confidence label — plus the surface map and the code-graph contract. It is charged to the ceiling, not to either command's floor.

### Added — the code graph reaches the two commands that judge changes

Neither mentioned it; only `/plan` did. `/pr-review` § 1 gains `detect-changes --brief` (a per-file risk score, which is what the cookbook built it for) and `impact --depth 2` (the "12 files changed, 80 affected" case a PR view structurally hides). `/verify` § 3 gains `callers_of` intersected with the change set for the reuse ledger — the same question `/plan` asked to produce the row, asked again after the fact — and `impact` for watchlist rows the plan's own author could not have known to write. Every one of them degrades: the probe is `status`, unavailable is recorded `SKIPPED (graph unavailable)`, and grep continues. `tests_for` is explicitly a candidate proof and never a coverage finding, because a measured case in `115-code-graph.md` returns zero tests for a symbol its test file references seven times.

### Added — `/verify § 1.5`, a real parallel review batch

Its three tree-reading blocks share no data: the safety floor runs `git status`/`git log`/`git diff --cached`, and the review checklist reads the plan, the rules directory, the host `REVIEW.md` and the branch. Neither consumes a gate exit code. Written `1 → 2 → 3` they looked sequential and were not. Four tracks now dispatch in one message — floor, correctness, security, design — every one read-only by frontmatter, surface-gated, and extensible through `chain.lenses`, the same config contract `ultra-verify` honours.

### Added — `/verify loop`, the first way to reach `ultra-verify` without `/plan`

`commands/plan.md:306` was the only line in the repository that invoked the 509-line workflow. The workflow's own header says the division out loud — verifying without a plan "already has a home: `/verify`" — but only one side of that contract was written down. `/verify loop` now hands the plan-measured half over when a plan exists, carrying the three-failure fallback doctrine `/plan` already proved, and keeps what the workflow does not do: the safety floor, `verify-supplements.md`, `NOT DECLARED` per gate, `## Rollback` and the `## Reuse ledger` walk.

### Fixed — one need, two rival mechanisms for the project's extra gates

`chain.contractGates` in the schema and `${rulesDir}/verify-supplements.md` answer the same question — where a repository keeps the checks it already had beyond type-check, lint and test — and neither knew the other existed. `ultra-verify` honoured the first and never read the second; `/verify` read the second and never knew about the first, so a project that put its checks in the config got them run by the chain and skipped by a direct `/verify`. `/verify § 0` now reads both, fires the contract gates whose `when` matches the surfaces from § 0.1, and reports which mechanism produced each row. The difference between them is real rather than historical: one is prose every run executes, the other is structured and conditional.

### Fixed — a third verdict vocabulary, in the file nothing loaded

`090-verdict-matrix.md` decided in Ship / Hold / Ship-with-follow-up while `/verify` and `ultra-verify` both return VERIFIED / VERIFIED-WITH-NOTES / NEEDS-WORK. Now that `/verify § 4` actually loads it, the third vocabulary would have been a contradiction shipped into the one place the verdict is written down. It adopts the three words, and states that a signal which did not run is its own row — `SKIPPED` and `NOT DECLARED` are different answers from `PASS`.

### Fixed — `/pr-review § 3` was titled "parallel" and dispatched nothing

Zero `subagent_type`, zero `Agent(`, four prose headings. It is a dispatch table now, and it gained the two lenses `ultra-verify` has always had and the review command never did: `performance-regression` and `design-tokens-a11y`. Projects extend it through `chain.lenses`; a lens naming an agent this plugin does not ship is named in the output **before** the batch, because a misspelt value otherwise spawns nothing and the review reports one check fewer than it claims.

### Fixed — the demotion half of the consolidation rule was dead text

§ 4 demoted a finding "only one path raised **and the others explicitly checked**", while the § 2 return contract said "Findings only. No praise, no summary" — so no track could ever report what it checked and found clean. Every track now returns a `COVERED` line, all on one P0-P3 scale, and the third case is spelled out: raised once with nothing else looking is a coverage gap, not agreement.

### Fixed — three of four audit agents could write to the diff they were auditing

`references/audit-agent-prompts.md` routed D3/D8/D9 and D4/D5 to `graph-powers:debugger` and D6/D7 to `graph-powers:frontend-specialist`, all carrying `Write` and `Edit`. The only thing between them and the tree was a prose "MUST NOT DO: edit any file" — a request, not a permission, and this repository has already paid for that: a review agent partitioned ownership of the diff it was reviewing and reverted about eighty lines of it. `/pr-review § 3F` reaches those agents through `/debug audit pr`, so the command was violating its own Iron Law transitively. All four slots are now read-only by frontmatter; D7 moved to the explorer slice because judging whether a gate can fail needs `Bash`, which the UX critic deliberately lacks.

### Fixed — the performance lens was a write-capable agent, in both places

`ultra-verify` has dispatched `performance-optimizer` as its `performance-regression` skeptic since the lens roster was written, and the first draft of `/pr-review § 3C` copied it. That agent resolves with `Write` and `Edit` and no `disallowedTools`, and a skeptic only reports — so both were handing review work to an agent that could edit the diff it was judging, which is the one rule this repository wrote down as an incident rather than a preference. Both now ask the performance question through `graph-powers:explorer`, which is read-only by frontmatter and has the `Bash` a pattern hunt needs. The fix loop is a separate dispatch and stays write-capable, which is where that specialist belongs. Every agent either command dispatches for review was re-checked against its own frontmatter, not against its description.

### Fixed — `ultra-verify` requested a build gate and silently never ran it

`commands.build` was declared in `CONFIG_SHAPE`, named in the config prompt, and consumed nowhere: `gateList` was `[typeCheck, lint, test]`. A project declaring `tooling.commands.build` got a gate that read as covered and never ran, while `/verify` ran it. It now runs **once**, in the opening gate pass, and deliberately not in `REGATE` — that list re-runs after every fix batch, and rebuilding per round is the most expensive thing this workflow could do. A project wanting it per round declares it as a `chain.contractGates` entry, which is what the file's own comment already recommended.

### Fixed — three smaller things that had gone stale

`/pr-review` hardcoded "three failed attempts" while the schema default for `graphGuardrails.maxRepatch` is 2 and `/verify` reads the key; it reads the key now. Its "read-only by default" claim did not survive § 3F writing `docs/AUDIT-REPORT-<date>.md` in the default mode — the claim is now accurate about what it means. And `ultra-verify.js` justified replicating a simplify pass partly because "the `debugger` agent has no Skill tool", which stopped being true in 1.7.0 when that agent was granted it; the remaining reason — an inner `/simplify` re-fans-out — stands on its own.

### Changed — `/perf` and `performance-optimization` each keep one copy of a procedure

The command and the skill were two implementations of the same seven procedures. The Vercel RUM run existed three times — `perf.md § 2.7` (4,097 B), the `vercel-rum` pack (4,243 B) and `vercel-data.md` — and the database scan, the PSI invocation, the CWV target table and the React-Doctor loop twice each. On top of that the skill carried three separate "bottleneck routing" tables and seven report templates, and both files are charged to `/perf`'s floor, so every duplicated byte was paid on every invocation. The split is now stated in both files and applied: **the command is the procedure** (which mode, what to run, what comes out), **the skill is the method and the catalogue** (rules, targets, pattern-to-fix), **a reference is one tool's exact invocation**. `/perf`'s floor drops from 49,326 B to 32,873 B — a third — with no mode and no pack removed.

Two anchors were held deliberately fixed because code and prose cite them: `ultra-verify.js:358` reads `perf.md § 4.2-4.4` for the N+1, `select *` and foreign-key-index scan, and `parallel-batch-contracts.md:121` cites `/perf § 2.5` as the worked per-route fan-out.

### Added — `/perf seo` and `/perf sec`

The `seo-geo-baseline` and `security-baseline` packs had no route through the command that loads them: `/perf`'s dispatch table listed seven modes, none of which reached either pack, while `AGENT_SETUP.md:364` and `:448` told installers that `gitleaks` is needed by `/perf security-baseline` — a mode that did not exist. Both are now dispatch rows, and the two `AGENT_SETUP` references point at `/perf sec`.

### Removed — the parts that were filler

`references/unlighthouse.md` was a 13-line file whose body began "TODO: full reference deferred"; its four useful lines are now the Unlighthouse row of `psi-api.md`'s tool ladder. The memory pack's 11-step playbook lost steps 9 to 11 — container limits, alerting dashboards and "production memory management" — which were generic SRE advice with no call site in this harness; what remains is the baseline rule, a four-row browser/Node triage table and the four anti-patterns.

### Fixed — POSIX-only commands the portability gate could not see

`check_portability.py` anchors its binary check to the start of a line, so `curl -s … | jq` passed. The performance skill and its references carried five such blocks: the PSI and robots/sitemap fetches, the SEO score parse, a `<title>` check piped into `grep -oP`, and a CSV path hardcoded to `/tmp/vercel-cwv.csv`. All are `python -X utf8 -c` now. Two more in the same territory: `vercel-data.md § 3` built its dashboard URL from `$SCOPE`, a variable it never set — empty string in POSIX, literal text in cmd.exe, a plausible-looking wrong link either way — and the `security-baseline` pack opened with `bun audit` in a plugin that resolves `${tooling.packageManager}`. The gate's own blind spot is left as its own defect.

### Fixed — the PSI quota note said the wrong thing

`/perf § 2.1` promised "25k/day free, no key needed for ad-hoc use". The 25,000/day figure is the quota of a Google Cloud **project that has a key**; keyless requests are rate-limited per IP at a level Google does not publish. `psi-api.md` now says which is which, so a repeated run reaches for a key before it reaches a 429.

## 1.7.0 — the browser reference that shipped with the binary, and nobody read it

`skills/webapp-testing/references/browser-setup.md` was 465 lines of hand-written `agent-browser` command reference. The CLI ships its own usage skill — `bunx agent-browser skills get core --full`, 432 lines, versioned with the binary and therefore never stale. The file already knew: it recommended that command twice, at `:309-318` and `:382-392`, in two byte-identical blocks, and the second one stated the thesis out loud — *"This file covers what a project has to decide … everything else is upstream."* It then kept mirroring upstream for another 250 lines. This release makes the file obey the sentence it was already carrying.

### Added — Step 1 now installs the binaries too, not just the plugins

`AGENT_SETUP.md` documented two plugin dependencies and none of the tools the skills actually shell out to. Nothing said that `/pr-review` needs `gh`, that `/debug frontend` needs a browser CLI, that `/perf security-baseline` runs `gitleaks`, or that two agents declare MCP tools that resolve only when the server carries an exact name. A missing one of those does not fail at startup; it fails mid-task as `command not found`, after the agent has already promised evidence it can no longer produce. Step 1 is retitled and carries a second half: the three dependency classes, a table of every tool with its level and its install line, the MCP naming rule, and one preflight block that reads the whole list and installs nothing. Step numbers did not move — `PRODUCT.md`, `DESIGN.md`, `REVIEW.md` and `AGENTS.md:117` cite `AGENT_SETUP.md § 5` and `§ 6`, and `check_wiring.py` resolves those.

### Fixed — the interpreter is named `python3`, and nothing said so

All twelve hook registrations in `.claude-plugin/plugin.json` spell it `python3`, with no fallback to `python` or `py -3`. Where the interpreter does not answer to that name — the common case on Windows — every guardrail fails to start, and because cardinal 3 makes hooks fail open, nothing reports it: the session looks normal and has no commit gate, no push gate, no branch gate, no destructive floor and no write lease. Now stated in Step 1 as a prerequisite with that consequence attached, rather than left as an inference from a JSON file nobody reads.

### Fixed — the librarian's MCP servers were graded as optional, and they are not

The first draft of the section above called Tavily `RECOMMENDED` on the reasoning that the agent
lists `WebFetch` and so degrades rather than breaks. Reading `agents/librarian.md:4` disproves it:
the allowlist holds exactly one non-MCP tool, `WebFetch`, with no `WebSearch`, no `Grep` and no
`Glob`. `WebFetch` retrieves a URL you already have and cannot discover one, so without the MCP
servers that agent cannot do the job its own description promises. The sentence was true of
`agents/evaluator.md`, which does carry `WebSearch` — two agents, two answers, and the frontmatter is
what separates them. Tavily is now `REQUIRED` for the librarian in both the table and the preflight.

### Changed — `agent-browser` is a global install, not a `bunx` call

The skills spell it `bunx agent-browser` in twenty-five places. In a project that declares `autonomy.allowPackageManagers` without bun, this plugin's own guardrail refuses `bunx` — correctly, and it is the same trap Step 1 already documents for impeccable. A global `npm install -g agent-browser` makes every one of those twenty-five call sites work as a plain binary regardless of the project's package manager. Two more places hardcode bun the same way and are named in the section: `skills/debugger/scripts/find_polluter.py:92` runs `["bun", "run", "test", …]`, whose failure is worse than a missing command because the bisect then reports no polluter, and `skills/performance-optimization/SKILL.md:215` opens `security-baseline` with `bun audit`. The verification is `agent-browser doctor`, which checks the CLI, the state directory, disk, an available Chrome, the CDN and a real headless launch; `agent-browser install` is only needed when it reports a Chrome failure, since a machine that already has Chrome, Chromium, Brave or Edge passes without it.

### Changed — `webapp-testing` delegates the command reference upstream

`browser-setup.md` went 20,073 B to 8,024 B (-60%) and now documents only what the CLI cannot know: which environment to point at, the CDP path for authenticated routes with its three non-optional traps, the staging-write policy, the verdict rules, and when Playwright earns its place. `SKILL.md` went 83 to 77 lines. Its `description` also stopped advertising a call site that never existed: it claimed to be loaded by `/verify`, and `commands/verify.md` has never contained a line of browser content, never loaded this skill, and never spawned `graph-powers:verification`.

### Added — named sessions, which were missing and mattered

The default `agent-browser` session is a single browser shared by every agent on the machine, and it persists across conversations: working in it navigates over whatever page another agent left open. `export AGENT_BROWSER_SESSION="$(bunx agent-browser session id --scope worktree --prefix task)"` is now the second thing the skill tells you to do. This is upstream guidance the mirrored reference had never picked up — the cost of maintaining a copy, paid in a missing feature rather than in a wrong one.

### Removed — `skills/webapp-testing/examples/` (3 files, 109 lines)

No prose referenced them, `pyrightconfig.json` excluded them from type checking, and they hardcoded `localhost:5173`, `/tmp/page_discovery.png` and `/mnt/user-data/outputs/`. That last path exists only on claude.ai: it violates the portability cardinal and passed CI solely because `check_portability.py` does not scan `/tmp` and `~/` inside `.py`. The one capability that was theirs alone — `file://` automation of a local HTML file — is one line in `browser-setup.md` now. `NOTICE` § 4(b) records the removal, as Apache-2.0 requires.

### Changed — `/debug` stopped carrying a second copy of two skills

`commands/debug.md` went 530 to 436 lines and its context floor went 67,315 B to 54,679 B — from 2,685 B under the 70,000 B per-command cap to 15,321 B under it. What left: ~60 lines mirroring `browser-setup.md` in a file that already pointed at it; the Iron Law, in this repository's fourth copy of it; a "Hard STOP signs" list that repeated the stopping conditions printed 480 lines earlier in the same file; two parallel-research prompts weaker than the ones `pack-guides.md` already held, without the return cap or the read-only-by-frontmatter contract; and the agent/mode matrix, folded into the dispatch table it duplicated. Total command-set floor: 313,200 B to 298,442 B.

### Fixed — a TDD exemption that contradicted the Iron Law it cited

`commands/debug.md` granted L1-L2 fixes an exemption from the failing-test-first rule. `Skill("debugger")` Iron Law #3 grants none. One of them had to be wrong, and it was the command — this was the only place in the harness where "too small to test" was an argument. Removed; if the exemption is ever wanted, it belongs in the skill as an explicit exception, not hidden in a mode file.

### Fixed — the debugger agent could not run the gates it was told to run

`agents/debugger.md` declared `tools: Read, Write, Edit, Bash, Glob, Grep` — no `Skill`. The skill it preloads instructs it to invoke `superpowers:systematic-debugging`, `test-driven-development` and `verification-before-completion` at Steps 5 and 6. Inside that agent all three resolved to nothing, silently, and `workflows/ultra-verify.js:34` had recorded the defect without anyone acting on it. `Skill` is now in the toolset, with a comment saying why it cannot be removed.

### Fixed — one process, three numbering schemes

`SKILL.md` said Steps 0-6, `agents/debugger.md` said Phases 1-4, `commands/debug.md` said Phases 0-7. Three names for the same seven moves, which makes every cross-citation unverifiable. Steps 0-6 is now the only scheme, and the agent and the command cite it instead of restating it.

### Removed — `commands/recover.md`

A second entry point into `references/recovery-protocol.md`, which `/debug recover` already opened. The file documented that hazard about itself, at `:14-20`, and kept existing anyway. Its two genuinely unique blocks moved into the protocol where they belong: the stale-state pre-step is now Step 0 (a recovery run against a stale build reaches confident wrong conclusions), and the post-Step-5 gate checklist closes the file. The trigger phrases it owned — "we've tried three fixes", "we're going in circles", "back out and start over" — moved into the `/debug` description, so the intent still routes.

### Removed — `skills/debugger/scripts/run_tests.py`

Nineteen lines hardcoding `bun run check` and `bun run test`, in a plugin whose safety floor § 5 forbids substituting a different tool for the one the project declared. Its whole job is `references/shared/010-quality-gates.md`, which resolves the command from `config.json`.

### Fixed — the debugger evals were unrunnable where they sat

`skills/debugger/evals.json` moved to `skills/debugger/evals/evals.json`. Nothing executed it before: `run_evals.py` resolves `<skill-path>/evals/evals.json`, and the flat file matched no consumer. Same 14 assertions and 5 cases, now reachable by the runner that already ships.

### Changed — the bug catalogue keeps the bugs, and stops re-indexing the rules

`references/anti-patterns.md` went 12,699 B to 8,860 B. The 28-entry catalogue survives whole and was renumbered — it had two runs of duplicate numbers, 17-21 appearing in both the frontend and integrations sections. What left is the Negative Constraints index: git, secrets and tooling rules already stated verbatim in `safety-floor.md` §1/§5, plus entries naming a specific ORM, a specific storage API and a project-internal protocol, which cardinal 1 says are parameters and not content. One entry stayed uncompressed because it is an incident and not a policy: the review agent that held `Write` and reverted 80 lines of the diff it was reviewing.

### Changed — `pack-guides.md` had one flow written four times

`10,205 B` to `7,199 B`. The `frontend`, `backend` and `auth-db` execution flows were the same eight numbered steps differing by two lines each, and all three were already `SKILL.md`'s Steps 0-6. They are one flow and a delta table now. `systematic-audit` keeps its own flow, because inventory-before-any-fix is a real difference and not a formatting one. The four parallel-research templates were untouched — they are the strong copy, and `/debug` now dispatches them instead of its own.

## 1.6.0 — the two skills that policed a border neither could hold

`skill-creator` and `harness-audit` covered one territory between them: what a skill should say, and how skills resolve to each other. Keeping them apart cost 677 characters of the shared listing budget, two eval cases, five statements of prose and two routing-table rows — and the border still leaked. The repository had already measured that. The eval case `neg-skill-does-not-fire` carried a note recording that "my skill does not fire" was the exact prompt where the two collided and that no eval covered it; the response at the time was to add a case defending the border. The border was the defect. They are now one skill, `skill-improve`, paired with the `skill-improver` agent that already existed and whose self-audit clause had been pointing at `skills/skill-improve/` — a path that dangled until this change made it real.

### Changed — two skills became one, and the body shrank by 72%

`skills/skill-creator/` and `skills/harness-audit/` merged into `skills/skill-improve/`, a two-mode router: Mode A authors or iterates one skill, Mode B audits how a harness is wired. The detail moved into `references/authoring.md` and `references/harness-wiring-audit.md`, because a command that loads a skill is charged the SKILL.md bytes and not the references. SKILL.md bodies went 235 + 149 = 384 non-empty lines to 107. The listing budget went 9,331 to 8,898 against the same 10,752 ceiling, and headroom went 1,421 characters to 1,854. Neither skill had a functional call site; the merged one has its first.

### Fixed — fifteen rules that were written twice and believed twice

The merge surfaced fifteen pairs where the two skills, or a skill and its own reference, stated the same rule in incompatible terms. The description cap was 1024 in three files and 1,536 in three others, and only 1,536 is enforced by anything. The eval path was documented as nested in one section and flat in another of the same file, while that file's own evals used the form its own instructions forbade. The frontmatter contract said "`name` and `description` only" while the sibling skill shipped five fields. A naming rule demanded gerund form, which condemns every skill name this plugin ships, and the documented exit codes `2` and `3` for `quick_validate.py` do not exist — it emits `0` or `1`. None of these was a disagreement between authors: each was one author writing the same rule twice, months apart, and believing both. That is now recorded in `skills/skill-improve/learning.md` as the pattern to watch, because fixing a contradiction displaces it unless one home is made canonical.

### Fixed — a validator that rejected the form it forces

`quick_validate.py` captured the opening quote of a YAML scalar as part of the value, so a quoted `description` could never satisfy the "Use when" prefix rule and a quoted `name` failed the hyphen-case check. A folded block scalar is rejected by the angle-bracket test, so a quoted single-line scalar is the only form left — and the validator was warning about the one form it permits. An `unquote` helper now strips one matching pair before the checks. Verified in both directions: the warning fires on `planning`, whose description really does start with "Layer ordering", and no longer on `skill-improve`.

### Fixed — an eval assertion that failed the correct answer

`contains: precedence` is case-sensitive, and a real report capitalises the word at the start of a sentence. Four prose assertions became `regex: (?i)...`; literal filenames, flags and identifiers were left as substring checks. Measured before the fix: 8 of 9 cases exit 0. After: 9 of 9, with a deliberately wrong response exiting 1 and a positive response scored against a negative case exiting 1. The two cases that used to be negatives against `skill-creator` were repointed rather than deleted — "create a skill for X" and "my skill does not fire" must now fire this skill, and the second one carries an assertion that Mode B did **not** run, which is the internal border the merge created in place of the one it removed.

### Changed — `/evolve` now calls a skill that exists in this plugin

`commands/evolve.md` invoked `Skill("superpowers:writing-skills")` for the job `skill-creator` claimed, which meant the only functional call site in this territory pointed at an external plugin. It now calls `Skill("skill-improve")`, whose `references/testing-skills.md` carries the RED-GREEN-REFACTOR discipline. That edge was previously charged zero bytes by `check_context_budget.py`, because its regex matches no name containing a colon — the gate was measuring a load it could not see.

### Changed — the context ceiling rose to 470,000, and the commit says what bought it

Two separate things. 18,585 B was already over the old 440,000 ceiling before this change and had no owner. The rest is the merged 8.6 KB body now being charged to `/evolve` through a call site that finally resolves locally. Lower it again when the pre-existing overage is paid down.

### Fixed — four defects the gates could not see, found by asking what invokes it

Every gate passed on the merged skill, so a second pass asked two questions instead: what invokes this without a person typing it, and when does it open the files it writes. Four answers came back wrong. The merge had deleted `user-invocable: true` and `argument-hint` along with `allowed-tools` — only `allowed-tools` was retired by the rubric, and the other two are live fields, so the skill had stopped being typeable as a slash command while its reference still documented `--all` and `--phase N`. `learning.md` was written at the end of every round and opened at the start of none, which makes an inherited failure pattern decorative. The Phase 5 prompt ordered `MEMORY.md` pasted verbatim without ever saying where it lives, while Phase 0's skip-list named `agent-memory/` as skipped — the skill told itself to skip the directory it must read from. And nothing triggered it automatically at all.

`.claude/rules/artifacts.md` now names it. That file auto-loads on `agents/**`, `skills/**`, `commands/**`, `references/**` and `workflows/**` — the exact territory the skill owns — and its own section titled "What invokes it" was the missing call site. A path glob is the only trigger in this repository that does not depend on a model reading a description and choosing.

The first of those four is the deduplication pattern eating its own author: collapsing "`name` and `description` only" against a sibling that shipped five fields deleted two fields the disagreement was never about. Resolving a contradiction by picking a side also discards whatever the losing side carried incidentally.

### Changed — NOTICE, because the Apache-2.0 obligation follows the directory

`skills/skill-creator/` is Apache-2.0 material from anthropics/skills, and the section 4(b) modification statement names it by path. The path moved, so both the redistribution list and the modification statement were rewritten rather than string-replaced: the sentence claiming the iteration loop had "absorbed the separate `skill-improve` skill this repository used to carry" becomes self-contradictory the moment the merged skill is named `skill-improve`.

## 1.5.0 — one task format, evidence instead of a checkbox, dispatch that stops waiting, and an execution floor that is always on

Three defects in the planning chain, all measured in this repository before anything was edited — and the coordination rules, which were optional, are not any more.

### Fixed — the skill taught a plan format the chain could not consume

`commands/plan.md` mandates seven sections and `commands/verify.md` reads three of them verbatim.
The template in `skills/planning/references/phase-b-writing-plans.md` — the one `ultra-plan` tells
its synthesizer to "follow exactly" — contained none of them: `Reuse ledger`, `Regression
watchlist`, `Rollback` and `Execution graph` appeared nowhere under `skills/planning/`. So the
workflow was instructed to produce a plan that fails `/plan`'s own post-return checks, and this
repository's real plan file followed the command rather than the skill. The template now carries
all seven, and `ultra-plan` names them in the synthesis prompt.

### Changed — a task is now written in one grammar, and its acceptance is a command

A plan task was a `### Task N.M` block whose acceptance was a sentence. Nothing ran it, and the
implementer self-reported PASS. It is now a checkbox — the syntax `/implement` already parses and
this repository already writes — carrying `Owns:` (the paths that task alone writes), `Needs:` with
the payload named, and `CHECK:` / `EXPECT:` / `EVIDENCE:` in place of the sentence.

**A checked box whose `EVIDENCE` still reads `pending` is unmet — worse than unchecked, not
better.** A checkbox is a claim; the evidence is the proof, and the gap between them was where
self-certification lived. A check that turns out impossible is surrendered in the open with
`ABANDON: <id> <reason>` and listed in the report. The idea and its wording come from
[unlazy](https://github.com/Leonxlnx/unlazy) (MIT), read at `ed9e8d2`.

Atomicity is now testable from both sides: too big if it would need two independent commits or two
unrelated `EXPECT` strings; too small if its `Owns` set overlaps a sibling's or its `EXPECT` is a
sub-assertion of one. The unverifiable `Estimated time: 2-5 min` field is gone; the granularity rule
stays.

### Changed — whole-project checks moved to the phase gate, and dispatch rolls

Every task used to run `format`, `type-check` and `lint` over the whole repository: a twelve-task
plan paid twelve times for one fact. Those commands now live in the phase's gate block and run once
per phase. A task's own `CHECK` is scoped to the task.

`workflows/ultra-build.js` dispatched a wave, awaited all of it, then dispatched the next — so every
task waited for the slowest sibling, including the ones it never reads. It now starts a task the
moment its own `needs` are done and no in-flight task holds one of its files. Three bounds keep that
honest: a topological check that **throws** on a dependency cycle rather than awaiting a promise
that can never settle, `graphGuardrails.maxParallelWave` as in-flight width, and `maxTasksPerPlan`
as the total. A task the classifier could not give edges for falls back to the old wave barrier,
which is the safe degradation. `check_workflows.mjs` dry-runs the scheduler's happy path; the other
eight properties — the cycle, a self-reference, an unknown dependency id, the width cap, a file
collision and a twelve-long chain among them — were checked once on a throwaway fixture and are not
covered by a standing gate.

### Fixed — an adversarial pass could widen the work it was reviewing

`ultra-verify`'s skeptic panel had no scope boundary, so a finding past the plan's edge became a fix
round, which became a new diff, which became a new panel. Findings now carry `inScope`, and only a
defect the diff introduced, a regression of a `## Regression watchlist` row, or something that makes
the plan's `## Destination` false can start a fix round. Everything else is reported and returned as
`outOfScope` — logged, never silently dropped, never work. `commands/verify.md` says the same in
prose, plus the rule that the same finding surviving its fix twice goes to a person rather than to a
third patch.

### Changed — one plan is one directory

`${paths.planDir}/YYYY-MM-DD-<slug>/` holds `PLAN.md`, `spec.md` and the phase gates. Reading still
accepts a bare `.md` written before this convention. `references/shared/007-path-conventions.md` is
where that is defined, and every other file cites it.

### Removed — the copies that disagreed

The tier ladder existed in five places with three different ceilings, one of which prescribed more
agents than the spawn cap allows; it is now only in `references/shared/020-complexity-routing.md`,
which also absorbed the model/effort tiering. The disjoint-file rule was stated ten times and is now
in `references/shared/070-parallel-agent-spawn.md`. The spawn cap was hardcoded as `5` in fourteen
places and is `graphGuardrails.maxParallelWave` everywhere. `phase-b`'s duplicate confidence-scoring
table and its three restatements of sprint contracts are gone; the canonical ones remain.
`phase-c-executing-plans.md` carried twelve project-specific rules — "no hardcoded hex", "FK index",
"webhooks idempotent" — inside a distributed artefact, against cardinal 1; they are now
`chain.hardRules` and `chain.invariants`, which already existed and which `ultra-build` already
reads.

Two dangling citations that CI cannot see, because `check_wiring.py` only resolves numeric `§` ids:
`.claude/CLAUDE.md § Intent classification` never existed, and `${rulesDir}/execution.md § Agents &
Dispatch` had no such heading — the first now points at the tier ladder, and the second exists in
`templates/rules/execution.md`.

`/plan` cost 67,731 bytes before it did anything, 51% of it `commands/plan.md`. Its Step 0 reasoning
and table templates moved to `skills/planning/references/step-0-inventory.md`, read at L3+, and the
three shared fragments a direct edit never needs became conditional reads. Floor now 47,889 —
**29.3% less on every invocation** — with the full text still reachable and still counted in the
ceiling.

### Added — `references/execution-floor.md`, the counterpart of the safety floor

`safety-floor.md` says what must never happen. Nothing said how the work is *run*, so that half was
optional: it lived in a skill the model had to choose to invoke, and in reference fragments a command
had to name. A session that never invoked either coordinated nothing and reported success.

The new floor holds eight sections: delegating is refused below L3 and required above it; a batch
goes out in one message with read-only agents in the background; one writer per file; the
seven-section delegation contract; the split between Claude Code delegating on its own and Codex
needing to be told in words; one cloud thread per scope; what the parent does with the returns; and
that an unresolved agent name is a route rather than a stop.

What it deliberately does not carry is every number and table that already has an owner —
`020-complexity-routing.md` keeps the ladder, `030-agent-assignment-matrix.md` the agent table,
`070-parallel-agent-spawn.md` the spawn rules and the two configuration ceilings. A floor that
restated them would be the fifteenth copy of `5`, which the release above had just finished removing.

It reaches both harnesses without a new hook. Codex gets it from the `references/` copy the installer
already writes, named in the delimited `AGENTS.md` block beside the safety floor.
`hooks/session_context.py` puts one line in front of every Claude Code session: the posture, and the
resolved path of the file. Four cases in `hooks/test_hooks.py` hold it to that, including on Codex.

### Removed — `agent-orchestration`, folded into the floor

1.3.0 decided explicitly **not** to delete this skill, on the reasoning that a skill's description is
itself a routing trigger. That reasoning was sound while the content was lazy — the description was
the only thing that could bring it into a session. A rule that is resident from the first turn needs
no trigger, so the argument goes with the skill.

Its unique content moved: the delegation contract into §4, the Claude-versus-Codex split into §5,
cloud threads into §6, parent consolidation into §7. Its two agent rows that `030` was missing —
`project-planner` and `verification` — moved into `030` rather than into the floor. Its restatements
of the spawn rules and the hardcoded "cap at 5" were dropped rather than moved.

`/delegate` no longer invokes a skill to decide the fan-out and no longer defines a second,
different seven-section contract: it mirrors §4 with a provenance comment, the same convention the
safety floor uses, so a divergence between the two is visible rather than silent. That also makes
`/delegate` cheaper — the skill it used to load unconditionally is 4.5 KB of floor it no longer pays.

### Fixed — a rename ate the sentence that taught the namespace

`030-agent-assignment-matrix.md` read "`graph-powers:explorer` is not `graph-powers:explorer`" — an
automated prefixing pass had rewritten the bare name on both sides of the comparison, in the one file
that exists to teach the difference between them. The sentence is rewritten to make the point without
needing the bare token, because `check_wiring.py` is right to refuse one.

### Changed — `senior-prompt-engineer` says half as much and answers the same questions

288 lines to 181, 16 KB to 9.6 KB, and the three `scripts/` are gone. What was cut was not detail —
it was content that had a different owner, or no owner at all:

- **§ 12, a seventeen-step refactoring checklist**, absorbed in May from a `/refactor-code` command
  that was deleted in the same change. Nothing has cited it since. Steps like "run linters",
  "update documentation" and "feature flags for gradual rollout" are true of any codebase, which is
  what made them free to write and worthless to read. The bundled `/simplify` and
  `superpowers:test-driven-development` already own that ground.
- **`scripts/prompt_optimizer.py`, `rag_evaluator.py`, `agent_orchestrator.py`** — 97 lines each,
  byte-identical apart from the class name, every one with a `_execute()` that returns
  `{'success': True}` and a `# Add validation logic` where the logic would go. Three years of
  "reserved for future automation" with no caller, no test and no concrete use case. A docstring
  reading "Production-grade tool" above a stub is the shape of the problem.
- **The spawn template and the parallel-batch rules**, which the execution floor and
  `070-parallel-agent-spawn.md` now own. The skill points at them instead of holding a third copy of
  the width cap.
- **An invented table.** "Default preload assignments" prescribed `senior-prompt-engineer` for an
  Orchestrator role this plugin does not have. The four agents that do preload something preload
  their own domain skill; the table now says what is true instead of what would be tidy.

The same pass removed the duplication *inside* the skill: `agentic_system_design.md` restated the
file contract, the preload table and the anti-patterns almost line for line, and now starts where
`SKILL.md` stops. `parallel-batch-contracts.md` lost a "remaining spawn budget" table that quietly
contradicted the width-versus-total distinction the spawn rules exist to make.

The floor gained the other half of the edge: filling the seven sections needs no skill, and when only
the return shape is needed the one reference is read rather than the skill around it.

### Fixed — three claims in that skill that the documentation does not support

`python3 .github/check_wiring.py` cannot see any of these: two are prose, and one was true when it
was written.

- **"A subagent cannot spawn a subagent — Anthropic spec."** It can, to a default depth of three
  layers below the main conversation. The anti-pattern is now the real one: nesting that nobody
  decided on, which spends the session spawn ceiling without a fan-out ever being planned.
- **A model-selection table recommending agents that do not exist.** It prescribed `opus` for an
  `orchestrator` and an `oracle`, neither of which is in `agents/`, and named the rest by loose
  description — "code reviewer", "codebase explorer". The bare-name lint cannot catch a name it has
  never heard of. The rows are the real twelve now, namespaced. A batch example was corrected the
  other way: `regression-hunter` is not a ghost but a **role label** for a second
  `graph-powers:explorer` instance, and the table now says so rather than reading as an agent name.
- **A citation that was never true.** `llm_evaluation_frameworks.md` opened by declaring itself
  "cited by `evaluator` agent (Mode 3)". `agents/evaluator.md` has never named it — it loads
  `references/rubrics/evaluator-rubric.md`. Also removed: two `${rulesDir}/execution.md § Agents &
  Dispatch → …` sub-anchors pointing at headings the shipped template does not contain, and the
  lineage prose citing `orchestrator.md`, a file this repository does not have.

### Removed — `/delegate`, whose subject is now the floor

The command had no caller. Nothing in the plugin invoked it; the only three mentions were a matrix
row, a historical note about context budget, and the sentence the execution floor had just added to
give it an edge. Everything it did was already defined a level up — the seven sections were a mirror
of `execution-floor.md` §4, and which agent to pick was a pointer to `030`.

What was genuinely its own moved into §4 rather than being dropped:

- **The pre-delegation declaration** — agent, why that one, skills included **and the ones omitted,
  with the reason**, expected deliverable. The omission line is the half that earns its place: an
  included skill announces itself, and a skill that should have been loaded and was not leaves no
  trace at all.
- **The three questions after it returns** — does it work, does it follow the patterns already here,
  did it honour MUST DO and MUST NOT DO.
- **The brainstorming escape** for a delegation whose scope nobody has pinned down.

Ten commands now, and the floor answers the question the eleventh was asking.

### Changed — `/prime` stopped paying for what it never read

The context loader was the second most expensive command in the set: 27,924 B before it did
anything, of which its header ordered six shared fragments and the body acted on three. The agent
matrix, the spawn rules and the guardrail index — 11,285 B — were loaded on every invocation and used
on none. `shared-context.md` has stated the rule the whole time: *"A command's header names what it
reads, and nothing else… if it does not, the line is wrong."*

They are also exactly what the execution floor now carries without being read, so the header is three
fragments and the body says why.

The per-domain staging then moved out of the command and into
`references/shared/045-context-staging.md`, one section per domain, read only for the mode that was
dispatched. Floor **27,924 → 11,765 B (−58 %)**, worst case 34,512 → 16,576. The pointer carries a
load verb on purpose, so the moved bytes still show up in the ceiling rather than disappearing from
the measurement.

## 1.4.1 — the approver stops vouching for what nobody owns

A review of 1.4.0 ran the guardrails instead of reading them, and the two answers disagreed. Six
commands had moved from `ask` to `allow` on the theory that a dedicated hook owned each decision.
For `git commit` and `git push` that was exactly right and is documented — Claude Code runs every
matching `PreToolUse` hook and applies the most restrictive answer, `deny` over `defer` over `ask`
over `allow`, so the gates still decide. For the other four there was no owner, and the review
found it by executing them rather than by trusting the comment.

### Fixed — `git checkout -- .` was allowed by everything

`checkout` reads as navigation, so it was sorted with the branch verbs and handed to
`git_branch_gate`. But `git checkout -- <paths>` is not navigation; it is `git clean`'s twin. It
overwrites the working tree from the index, and the edits it discards exist in no object git can
name. `git_branch_gate` never answered for that form — its `target_branch()` gives up the moment
`--` appears — so `smart_bash_approver` returned `allow` and the other four hooks returned silence.
Measured on both levels: `guarded` and `autonomous` alike.

The unambiguous destructive spellings are now on the destructive floor, where `git clean -f` and
`git reset --hard` already were: `checkout -- <paths>`, `checkout .`, `checkout -f`,
`switch --discard-changes`, and `git restore` without `--staged`. `restore` had been sitting in
`ASK_PATTERNS`, which resolves to `bashDefault` — `allow` under `autonomous`.

What is left is genuinely ambiguous: `git checkout main` is a branch, `git checkout main.py` is a
path, and nothing separates them without asking the filesystem. That form went back to `ask`, so
`guarded` stops and `autonomous` proceeds. It costs no extra prompt where it matters, because
`deny` outranks `ask` — where `git_branch_gate` refuses, its answer is the one the user sees.

### Fixed — a home directory could turn off the git gates in every repository

`autonomy` is user-scoped so a person's posture survives `git clone`. The comment said `git` was
excluded deliberately, and that was true of the top-level `git` block — branch names and the
opt-in prefix. The three *decisions* live under `autonomy`, which is scoped, so they crossed:
`~/.graph-powers/config.json` with `autonomy.git.{commit,push,protectedBranch}: "auto"` silenced
`git_commit_gate`, `git_push_gate` and `git_branch_gate` in every repository that declares no
`autonomy` block of its own — which is most of them, since that is why the layer exists. `level`
went on reporting `guarded` throughout.

A home directory may now tighten a git decision and not release one. `ask` under a personal
`autonomous` is somebody holding themselves to a stricter line and costs nobody anything; `auto`
has to be written in the repository it applies to, where a reviewer sees it. Dropping the whole
sub-block instead would have quietly loosened the operators who had pinned it to `ask`.

`protectedFiles` was the same shape with a worse ending. Lists replace on merge, so
`{"segments": []}` at home deleted the defaults machine-wide — and unlike `autonomy`, a project
declaring its own block did not win them back; it merged onto the emptied one. The user layer may
now only add. `graphGuardrails` is deliberately untouched: its ceilings are spend on the operator's
own machine, which is what a personal scope is for.

### Fixed — one prefix defeated `allowPackageManagers`, and a runner was waved through

The check ran once against the whole command line, so it only ever read the first word. With
`["bun"]` declared, `npm install` was refused and `echo ok && npm install` was allowed. It now runs
per segment, inside `_classify`, alongside every other rule.

The family map added in 1.4.0 is right that `bunx` belongs to `bun` — the lockfile guarantee is
what the setting protects, and running a package through the manager the project already chose
forks nothing. But `allow` was the wrong answer: `bunx <package>` resolves and executes code from a
registry the project never named, and the consent on record was about lockfiles. An in-family
runner now asks. Declaring the manager outright still allows, and `npx` under `["bun"]` is still
refused.

### Fixed — `gh pr create`, `chown` and a remote `rsync` had no owner either

All three moved to the always-allow list in 1.4.0. No hook in this plugin gates `gh`, and
`safety-floor.md §1` wants approval in the turn before anything leaves the machine. Ownership is
outside git entirely. And "additive" describes what `rsync` does to the destination filesystem,
which says nothing about the destination *host* — a remote target is egress. All three ask again;
a local-to-local `rsync` without `--delete` still runs unprompted, which was the change worth
keeping.

### Fixed — a symlink walked past every protected path

`protect_files` matched the path as a string, so `ln -s .env notes.md` followed by a write to
`notes.md` matched nothing and landed in `.env`. Both names are checked now — the link, because a
project may protect the link itself, and its target, because that is where the bytes go. A failure
to resolve falls back to the literal path: fewer names checked, never fewer than before.

### Fixed — two gates that could not fail, and one that could not see

`check_context_budget.py` shipped with no threshold and no step in CI, while `AGENTS.md` and
`.claude/rules/verify-supplements.md` both listed it among the gates that pass before anything
ships. Every mode returned 0. It now has a floor, a ceiling and a per-command cap, and it runs.

`check_portability.py` named three `.mjs` defects in its own docstring as its motivation and
scanned no `.mjs` file, so it could not have caught a regression of any of them. It scans the
installers now, and the five checks are the five defects this repository actually shipped —
verified against a synthetic file carrying all of them. Its markdown scan also skipped the
repository root, where `AGENT_SETUP.md` — which ships, and which an agent follows — carried
twenty-six POSIX-only lines. Those are rewritten as the Python the file already uses elsewhere.
`README.md` and `CONTRIBUTING.md` are exempt and say why: they are prose for a person, not a block
an agent executes.

Two of the gate's own rules were wrong in the other direction and were narrowed rather than
obeyed. `~/` inside `os.path.expanduser("~/…")` is the fix for the defect, not the defect, and a
POSIX line beside its PowerShell counterpart is coverage. Both are now judged by their context —
the file for the first, the fenced block for the second.

### Fixed — CI could not go green on a correct changelog

The dangling-reference gate held every `**/*.md` to today's tree. A changelog names files that
were deleted and files this repository never owned: `agents/codex-rescue.md` belongs to the codex
plugin, and the 1.3.1 entry describing it is accurate prose the regex cannot distinguish from a
broken link. Requiring a history to resolve against the present means it can never record a
removal, which is most of what a history is for. `CHANGELOG.md` is skipped; nothing else in the
tree dangles.

### Changed — the suite grew by twenty-seven cases, and four changed their answer

`hooks/test_hooks.py` runs 212 checks. The four that changed are the four behaviours above that
were asserted as correct in 1.4.0: `bunx` now asks rather than runs, `gh pr create` and a remote
`rsync` ask, and the approver's vote on `git checkout` is `ask` rather than `allow` with
`git_branch_gate`'s `deny` still proving what decides. The rest are new negative cases — the
destructive `checkout`/`restore`/`switch` spellings and their legitimate mirrors, the per-segment
package-manager refusal, `autonomy.git` in both directions, `protectedFiles` in both directions,
and the symlink, which skips loudly on a platform that refuses to create one.

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

Measured against a real Astro project in this org rather than reasoned about, because the first
version of this section was wrong in a way only measurement catches.

The reported symptom was ~2,400 findings. The project's own declared lint was **clean, exit 0, both
tools**: the numbers came from running the linters unscoped at the repository root, where they walk
`.claude/` and a timestamped `.claude.bak-*/`. 463 of oxlint's 468 warnings sat there, against 5 in
the project's source; Biome went from 387 files and 1,093 errors to 62 files and 6 lint findings on
the same repository once the harness directories were excluded.

Almost all of it was bundled third-party JavaScript that a skill installs — `no-unused-vars` and
`no-unused-expressions` on minified output, `no-loss-of-precision` on sRGB luminance constants that
are supposed to be long doubles, `no-misleading-character-class` on an emoji range regex. Correct
code, correctly flagged, in a file the project did not write. **The harness is what puts that code
in the tree, so the harness is what has to exclude it** — the exclusion list is now part of both
templates, and `.gitignore` is explicitly not a substitute, since `.claude/` is committed on purpose.

Two corrections to the first version of this section, both from measurement:

- **The oxlint template was noisier than oxlint's own default.** Same project, same ignores: the
  default `correctness` category gave 5 findings; the recommended `plugins` + `suspicious`/`perf`
  gave 68. The additions bought `no-underscore-dangle` (27 — Google Apps Script *requires* the
  trailing underscore for private functions), `no-await-in-loop` (17 — deliberate sequencing),
  `consistent-function-scoping` (8) and `no-array-sort` (6 — which this plugin's own config already
  disables, with a reason). The template is now the ignore list and nothing else, with the widening
  path described as something to measure one axis at a time.
- **`biome check` runs the formatter too**, so scoping it as the whole tree minus exclusions asks the
  repository to format every JSON config it can find: 255 findings of which 6 were lint. `includes`
  now names the source, which is what the measured project's own working config does.

Also documented: the triage order for someone handed four figures of findings — run what the project
declares first, then group by *directory* before ever grouping by rule, because that is the step that
ends most of these.


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
