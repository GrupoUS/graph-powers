# Graph Powers — repository rules

This repository is the shared harness, not a host project. One rule or mechanism has one canonical
owner; do not add product, domain, branch, provider, or secret-specific content here.

## Cardinals

1. Project variation is declared by `schema/config.schema.json` and read by `hooks/_config.py`.
2. Tracked files use portable paths; plugin paths use `${CLAUDE_PLUGIN_ROOT}`.
3. Hooks fail open: malformed input/config falls back safely and exits successfully.
4. Every agent, skill, command, workflow, and reference has a live call site.
5. Review/research agents declare `disallowedTools: Write, Edit`; `memory:` needs the same denial.
6. Every agent declares its model tier. Workflows state their explicit model because they do not
   read agent frontmatter.
7. Claude artifacts are canonical; Codex, Cursor, Grok, Kilo, and Hermes are generated/adapted
   projections. Do not maintain a second inventory.
8. Instructions must run on Linux, macOS, and Windows. Use portable Python or agent tools instead
   of POSIX shell constructs; normalize Python paths with `PurePath(...).as_posix()`.

## Working rules

- Before editing, read `.graph-powers/config.json` and the `AGENTS.md` nearest the files you touch;
  load only the shared-context fragments the task needs — the safety and execution floors always
  apply.
- Keep changes scoped, preserve dirty user work, and do not commit, push, publish, or alter data
  without explicit approval for that action and scope.
- Reuse existing patterns and run the smallest applicable declared check. Evidence can be reused
  only while its diff, configuration, and environment remain relevant and unchanged.
- Agent, skill, command, hook, or reference edits must preserve a live invocation and public names,
  anchors, frontmatter, and client projections.

## Gates

`/verify` owns the complete gate inventory in `.claude/rules/verify-supplements.md`. Run its
applicable checks before shipping; do not call an undeclared check passed.

## Ownership map

| Path | Authority |
|---|---|
| `agents/` | Claude agent definitions; generated Codex companions follow them |
| `skills/`, `commands/`, `references/` | Canonical methods and reusable contracts |
| `hooks/` | Runtime guardrails; read `hooks/AGENTS.md` before edits |
| `workflows/` | Deterministic Claude orchestration |
| `codex/`, `cursor/`, `grok/`, `hermes/` | Client projections and adapters |
| `templates/`, `schema/`, `examples/` | Host-project starting contracts |

`DESIGN.md`, `PRODUCT.md`, and `REVIEW.md` specify host-project counterparts; this plugin's own
architecture and audience live in `docs/`.

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
