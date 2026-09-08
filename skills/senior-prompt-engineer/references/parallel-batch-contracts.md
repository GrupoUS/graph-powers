# Parallel Batch Contracts

Applies only when two or more agents run in one batch. Single-agent work uses
`agent-handoff-contracts.md` alone; scope and wave width remain in the execution floor.

## 1. When this applies
Use only for independent questions that one agent cannot answer in one pass. Each member keeps the
standard Context Handoff and adds this table.

## 2. Findings table schema

```markdown
| # | Finding | Confidence (1-5) | Source | Impact (Low/Med/High) |
|---|---|---|---|---|
| 1 | <one grounded claim> | 4 | code | High |
```

`Source` is `code`, `docs`, `tests`, `tooling`, or `inferred`. Review batches add a sixth
`Severity` column with `P0`–`P3`; do not add other columns.

## 3. Confidence scoring
5 is runtime/code verified; 4 has corroborating sources; 3 has one authoritative source; 2 is
indirect and must be marked `[ASSUMED]`; 1 is speculation and cannot drive implementation.

## 4. Severity scale (review batches only)
P0 blocks shipping (security/data loss/build); P1 must fix; P2 is tracked; P3 is optional.

## 5. Consolidation rules (parent agent)
Deduplicate identical findings, keep maximum confidence/impact/severity, renumber and sort by
severity then confidence. Merge gate evidence; any FAIL fails the batch. Present the consolidated
table, not raw member reports.

## 6. Tool-precedence guidance for batch members
Follow each agent's declared tools. For research, explorer is repository-only and librarian uses
current primary documentation before broad web sources.

## 7. Scope and width belong to the spawn rules
Cluster by root cause when natural fan-out exceeds the wave limit. One agent owns each file.
