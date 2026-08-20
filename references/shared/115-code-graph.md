## Section 11.5: Code graph (`code-review-graph`) — canonical contract

> Structural map of the repo (Tree-sitter → SQLite) used to answer "does this already exist?" and
> "what does changing this break?" without a grep sweep. Consumed by `/plan` Step 0 and by
> `skills/planning/references/wayfinding.md`.
> Canonical here; those commands reference this section instead of restating it.
>
> Local-first: graph lives in `.code-review-graph/` (gitignored + dockerignored). No cloud calls, no
> telemetry. Never pass `--embedding-provider openai|google|minimax` — those transmit source-derived
> text off-machine.

### Invocation

```bash
CRG="python -m code_review_graph"      # console script is NOT on PATH in Git Bash — use the module form
# Pass `-X utf8` to the interpreter instead of exporting a variable — `export` is POSIX-only,
# which made the previous form of this line unusable on the very platform it was written for.
# Without UTF-8 the Rich panels crash with
                                       # UnicodeEncodeError on the cp1252 console otherwise
$CRG update -q                         # incremental re-parse (seconds). ALWAYS run before querying
$CRG status                            # nodes/edges/files + "Built at commit" — the staleness check
```

Not installed / no `.code-review-graph/graph.db` → the graph steps are **SKIPPED, never blocking**.
Record `SKIPPED (graph unavailable)` and use the grep fallback. Rebuild from scratch with
`$CRG build` (~2 min on this monorepo). Install: `python -m pip install code-review-graph`.

### Query cookbook

| Question | Command |
|---|---|
| Does this capability already exist? | `$CRG search "<terms>" --kind Function\|Class\|File --limit 15` |
| Who calls this function? | `$CRG query callers_of "<symbol>"` |
| Who imports this module? | `$CRG query importers_of "<file>"` |
| What does this file pull in? | `$CRG query imports_of "<file>"` |
| Which tests touch it? | `$CRG query tests_for "<symbol>"` (see limits) |
| Blast radius of a change | `$CRG impact --files <f1> <f2> --depth 2 --max-results 60` |
| Risk-scored diff summary | `$CRG detect-changes --base <base> --brief` |
| Layer overview (L4+ framing) | `$CRG architecture --detail-level minimal` |
| Orphans after a refactor | `$CRG dead-code --kind Function --file-pattern "<path>" --limit 20` |
| Rename impact before doing it | `$CRG refactor rename --old-name <a> --new-name <b> --kind Function` |

Output is JSON and can be large. Always bound it (`--limit` / `--max-results`, pipe through `head`)
and quote only the `file_path:line_start` rows you act on — dumping raw graph JSON into the report
defeats the purpose of using it.

`--base` for `detect-changes` / `impact`: `HEAD~1` for the last commit, `$(git merge-base main HEAD)`
for the whole branch. On a long-lived `dev-test` the merge-base form can span 1000+ files and caps at
500 functions (`CRG_MAX_CHANGED_FUNCS`) — prefer explicit `--files` from the diff when that happens.

### Limits — where the graph is NOT authoritative `[HARD]`

The parser resolves **static** imports and call sites. It does not see anything reached through a
string or assembled at runtime. For these five, **grep is the authority and the graph is the hint**:

1. tRPC client paths (`trpc.<domain>.<proc>.useQuery`) — the procedure↔caller edge does not exist.
2. TanStack Router route ids / `to="/…"` targets.
3. Drizzle column reads (a column is not a node).
4. Anything behind a dynamic `import()`, a registry map, or a string key.
5. **`tests_for` is incomplete** — verified on this repo: `applyMovement` returns 0 tests while
   `stock-service.test.ts` references it 7×. A zero here means "no static edge found", NEVER
   "untested". Confirm with `grep -rln "<symbol>" apps/*/src/**/*.test.ts*` before claiming a test gap.

A graph result therefore **widens** the search and **never narrows** a safety check: it may add
consumers you would have missed, but an empty result never authorizes skipping the grep that a
`[HARD]` rule (tenant filter, PII gate, financial mirror) depends on.
