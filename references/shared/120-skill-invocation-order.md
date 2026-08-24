## Section 12: Skill invocation order

When a task touches multiple domains, invoke skills in this order:

1. **Meta layer** — `superpowers:using-superpowers` (always first, per `005-superpowers-bootstrap.md`)
2. **Superpowers method** — `superpowers:brainstorming` / `writing-plans` / `executing-plans` / `subagent-driven-development` / `test-driven-development` / `systematic-debugging` / `verification-before-completion` / `requesting-code-review` / `receiving-code-review` / `dispatching-parallel-agents` / `using-git-worktrees` / `finishing-a-development-branch` / `writing-skills` (HOW: discipline + format)
3. **Harness knowledge** — `planning`, `graph-powers:debugger`, `senior-architect`, `skill-improve` (WHAT: layer ordering, anti-pattern catalogue, architecture trade-offs)
4. **Domain skills** — the project's own database/provider/deploy skills, `performance-optimization`, `webapp-testing`, `senior-prompt-engineer`
5. **Implementation and design skills last** — `uxmaster`, the external `landing-page-design` skill and `impeccable` plugin

Multiple skills can be loaded in the same response; order matters because earlier skills set context that later ones build on. The pipeline `spec (brainstorming) → plan (writing-plans) → execute (executing-plans / subagent-driven-development) → verify (verification-before-completion) → review (requesting-code-review / receiving-code-review) → finish (finishing-a-development-branch)` is the canonical flow for any L3+ feature work.
