## Section 12: Skill invocation order

When a task touches multiple domains, invoke skills in this order:

1. **Method floor** — `005-method-bootstrap.md`, read before the first skill call (a reference, not a skill)
2. **Method surfaces** (the plugin's own) — `graph-powers:planning` for discovery, design and plan authoring / `graph-powers:executing-plans` / `graph-powers:test-driven-development`; and the two gates that are references rather than skills, `015-verification-gate.md` and `070-parallel-agent-spawn.md` (HOW: discipline + format).
   Review feedback enters through `${CLAUDE_PLUGIN_ROOT}/commands/pr-review.md § 4.1`.
3. **Harness knowledge** — `graph-powers:debugger`, `senior-architect`, `skill-improve`, `graph-powers:intent-layer` (WHAT: anti-pattern catalogue, architecture trade-offs, the project's AGENTS.md hierarchy)
4. **Domain skills** — the project's own database/provider/deploy skills, `performance-optimization`, `webapp-testing`, `senior-prompt-engineer`
5. **Implementation and design skills last** — `designer` (direction first, then its craft passes), `uxmaster`, `animate` (motion), `landing-page-design` (a landing or marketing page), and the external `emil-design-eng` and `apple-design` skills

Multiple skills can be loaded in the same response; order matters because earlier skills set context that later ones build on. The pipeline `spec + plan (graph-powers:planning) → execute (executing-plans) → verify (015 + /verify) → review (/pr-review § 4.1) → finish (reviewed working-tree changes; the git step the user authorises in that turn)` is the canonical flow for any L3+ feature work.
