# Execution floor

This is the coordination authority. `safety-floor.md` sets non-negotiable limits; shared
references own the detailed method. Claude, Codex, Cursor and Grok consume projections of this
source; Hermes translates it in its native skill.

Subagents do not inherit the parent context. Agent bodies mirror only the safety limits and return
contract they need, with provenance comments.

## §1 — Delegate only independently useful work

`shared/020-complexity-routing.md` decides whether to delegate. L1-L2 stay local; L3 may use one
existing specialist; L4-L5 use only the disjoint specialists that add value; L6+ needs a
coordinator. Use fewer agents when fewer scopes exist. The assignment and skill authorities are
`shared/030-agent-assignment-matrix.md` and `shared/060-skill-domain-matrix.md`.

## §2 — One message, background by default

Follow `shared/070-parallel-agent-spawn.md`: one batch message, read-only work in the background,
configured limits, and no fabricated workflow. A workflow written by hand follows
`shared/130-workflow-authoring.md`.

## §3 — One writer per file

Parallel tasks declare disjoint paths before dispatch. Re-slice overlap; do not negotiate it after
agents are running. `shared/070-parallel-agent-spawn.md §7` owns the ordering exceptions.

## §4 — The delegation contract

Before dispatch, state the selected agent, why it matches, any required skill and deliberate
omission, and the expected outcome. Every prompt uses the seven-section envelope and every return
uses the Context Handoff in
`${CLAUDE_PLUGIN_ROOT}/skills/senior-prompt-engineer/references/agent-handoff-contracts.md §§1-2`.
The parent checks scope, evidence and MUST DO/MUST NOT DO before using a result. Ordinary dispatch
does not require the prompt-engineering skill; use it when changing this machinery.

### §4a — Parent-mediated consultation ledger

Only the parent/controller may reserve or record a consultation. The canonical envelope, status
rules, capability fallback and `sdd.py consult reserve|record` interface are in
`${CLAUDE_PLUGIN_ROOT}/skills/senior-prompt-engineer/references/agent-handoff-contracts.md §2a`.
Workers never consult or spawn children; review calls are not ledger entries.

## §5 — Client routing differs, intent does not

Claude may route from descriptions and hooks. Codex requires an explicit spawn instruction. Hooks
may guide or validate but never spawn. Keep one thread/worktree per isolated scope and report paths,
checks and blockers.

## §6 — One thread per scope

Do not run two threads against the same files without isolation and a merge plan. Network access is
off during an agent phase unless current external facts require it.

## §7 — Consolidate evidence

Validate the return contract, deduplicate concrete claims, and prioritize severity, confidence and
impact. Findings at confidence 2 or below remain assumptions. Run or reuse the smallest applicable
gate under `shared/015-verification-gate.md` before reporting completion. Parallel-batch columns and
recovery are owned by the handoff contracts.

## §8 — Unresolved agent names

Conditionally load `shared/035-agent-resolution-recovery.md` after a name fails. State the fallback
once; do not retry the same name. A missing write-capable specialist blocks the task.
