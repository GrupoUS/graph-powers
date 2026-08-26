## Section 0.5: Method bootstrap

After required references load and before any action or response — including a clarifying question
or task-file read — check for applicable skills. A plausible match means invoke it, announce
`Using <skill> to <purpose>`, and follow it; drop it only after reading proves it irrelevant.

Process skills precede domain skills: `graph-powers:planning` for discovery, design, plan authoring,
approved-plan execution and TDD; `Skill("debugger")` for broken behaviour; `/pr-review § 4.1` for
review feedback. Full ordering is `120-skill-invocation-order.md`.

### Implementation minimum

- Execute an approved plan only through `/implement` and planning Phase C; do not invent a parallel
  task loop.
- Apply `skills/planning/references/execution/tdd-policy.md` to behaviour changes; do not restate
  its RED/GREEN/exception contract here.
- KISS/YAGNI: implement only what the plan and failing test require.
- Completion requires fresh command output and exit code per `015-verification-gate.md`; an agent
  report or visual inspection is not evidence.

Exceptions: `/prime` only recommends; a subagent follows its dispatch contract (`execution-floor.md § 4`).

Precedence: the user's instructions and AGENTS.md > skills > defaults.
