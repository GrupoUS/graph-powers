## Section 0.5: Method bootstrap

Before a task action, load a skill when the user explicitly asks for it or its documented trigger
clearly matches the task. Announce the choice once. Do not load a skill merely because it might be
relevant; use the project rules and available tools when no clear match exists.

Process skills precede domain skills: `graph-powers:planning` for discovery, design, plan authoring,
approved-plan execution and TDD; `Skill("debugger")` for broken behaviour; `/pr-review § 4.1` for
review feedback. Full ordering is `120-skill-invocation-order.md`.

### Implementation minimum

- Execute an approved plan only through `/implement` and planning Phase C; do not invent a parallel
  task loop.
- Apply `skills/planning/references/execution/tdd-policy.md` to behaviour changes; do not restate
  its RED/GREEN/exception contract here.
- `025-solution-ladder.md`: only what the plan and failing test require.
- Completion evidence follows `015-verification-gate.md`; an agent report or visual inspection is
  not enough on its own.

Exceptions: `/prime` only recommends; a subagent follows its dispatch contract (`execution-floor.md § 4`).

Precedence: the user's instructions and AGENTS.md > skills > defaults.
