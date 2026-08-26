## Section 0.5: Method bootstrap

After the command's required references are loaded, but before its first task action or response,
check whether a skill applies. A clarifying question and a task file read count as actions; loading
the instructions that define this check does not. Even a small chance means: invoke the skill,
announce `Using <skill> to <purpose>`, follow it. A skill that proves wrong can be dropped; the check
cannot be skipped.

**Process skills before implementation skills.** The chain: `graph-powers:planning` for discovery, design and plan
authoring · `graph-powers:executing-plans` with an approved plan · `Skill("debugger")` for anything
broken · `graph-powers:test-driven-development` before production code · `/pr-review § 4.1` when
review feedback arrives. Domain skills after, per
`120-skill-invocation-order.md`.

### Implementation minimum

- An approved plan is executed through `graph-powers:executing-plans`; the caller does not invent a
  second task, review or retry loop.
- A feature, bug fix, refactor or behaviour change starts with
  `graph-powers:test-driven-development`: expected RED, minimum GREEN, then refactor while green.
  The skill owns its explicit-exception rule.
- KISS and YAGNI bind the GREEN step: implement only what the current plan and failing test require;
  no speculative feature, option, abstraction, compatibility layer or adjacent refactor.
- Completion follows `015-verification-gate.md`. Agent reports and visual inspection are not a
  substitute for fresh command output and its exit code.

| Thought | Reality |
|---|---|
| "Just a simple question" | Questions are tasks. Check. |
| "I need context first" | The check precedes the question. |
| "Let me explore first" | Skills say how to explore. |
| "I remember this skill" | Skills change. Read it. |
| "The skill is overkill" | Simple things grow. Use it. |
| "This doesn't count as a task" | Action = task. Check. |

Exceptions: `/prime` only recommends; a subagent skips this — its prompt is its contract (`execution-floor.md § 4`).

Precedence: the user's instructions and AGENTS.md > skills > defaults.
