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
7. Claude artifacts are canonical; Codex, Cursor, Grok, and Hermes are generated/adapted
   projections. Do not maintain a second inventory.
8. Instructions must run on Linux, macOS, and Windows. Use portable Python or agent tools instead
   of POSIX shell constructs; normalize Python paths with `PurePath(...).as_posix()`.

## Working rules

- Read `.graph-powers/config.json` and the applicable `AGENTS.md` before editing.
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

This machine runs the shared Graph Powers harness. Read its shared-context index, then only the
fragments the task needs; safety and execution floors always apply. Project-specific parameters,
rules, and product specifications remain in this repository. A hook denial names the opt-in that a
person must set for the approved action.
<!-- graph-powers:end -->
