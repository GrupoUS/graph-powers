---
name: senior-prompt-engineer
description: "Use when writing or revising an agent file, a handoff schema, a spawn template or a batch return contract — anything about how the harness is built rather than how it is run. Also for LLM features inside the product: RAG, structured extraction, eval harnesses. Not for deciding how many agents a task needs, and not for filling in an ordinary delegation prompt."
---

# Senior Prompt Engineer

Use this skill to design an agent contract, shared handoff/consultation shape, or product LLM
feature. Running an existing harness follows `${CLAUDE_PLUGIN_ROOT}/references/execution-floor.md`;
ordinary delegation does not load this skill.

For an agent file, name the trigger in `description`, use explicit tools, add inline
`disallowedTools: Write, Edit` to read-only work, and declare its model. `memory:` grants Write and
Edit, so pair it with `disallowedTools` or omit it. Mirror only necessary `[HARD]` safety rules with
their source; the mirrored rule must state the actual limit because subagents do not inherit the
parent's instructions. Cite shared methods rather than copying them. The parent must supply required
contract/rubric excerpts to external-only agents that cannot read local files.

`references/agent-handoff-contracts.md` is the sole owner of the spawn context, Context Handoff,
JSON envelope, consultation and recovery semantics. `references/parallel-batch-contracts.md` adds a
findings table only for two or more agents. Preserve the envelope fields and status invariants; do
not redefine them in agent bodies or commands.

Load `references/agentic_system_design.md` for isolation/model/preload choices,
`references/prompt_engineering_patterns.md` for product prompting, and
`references/llm_evaluation_frameworks.md` for product evals. Stop when the contract has one owner,
an observable acceptance check, and a bounded failure path.
