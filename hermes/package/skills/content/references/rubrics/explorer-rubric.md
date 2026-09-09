> Hermes auxiliary: `content/` paths are `file_path` values relative to the registered-document parent. Apply the loaded graph-engineering mapping and host policy; this file is served without template expansion.

# Explorer On-Demand Rubric

Load only for broad impact analysis or a parallel research batch.

## Impact dimensions

- Definition and canonical owner.
- Imports, callers, consumers, and route bindings.
- Writes, reads, transactions, caches, queues, and webhooks.
- Types, schemas, migrations, environment variables, and configuration.
- Unit, integration, browser, and deployment validation surfaces.
- Nearest `AGENTS.md`, rules, skills, and dated architectural decisions.

## Evidence grades

- Confidence 5: direct definition plus caller/test evidence.
- Confidence 4: direct definition and one corroborating path.
- Confidence 3: strong inference with an explicit missing link.
- Confidence 1–2: insufficient; return `BLOCKED` for critical conclusions.

For parallel batches, append the findings table required by
`content/skills/senior-prompt-engineer/references/parallel-batch-contracts.md`.
