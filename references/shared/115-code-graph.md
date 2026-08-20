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
# The module form, written out on every line: the console script is NOT on PATH in Git Bash.
# Abbreviating it to a shell variable is what this block used to do, and it does not work —
# `export` is POSIX-only, so the name is undefined in PowerShell, and each command an agent
# runs is its own shell, so even on POSIX the definition is gone by the next line. Either way
# the command silently vanishes and only the subcommand is left.
# `-X utf8` rides on every line below and is why the Rich panels no longer crash with
# UnicodeEncodeError on a cp1252 console. It is an interpreter flag, so it needs no variable
# exported into the environment to take effect.
python -X utf8 -m code_review_graph update -q   # incremental re-parse (seconds). ALWAYS run before querying
python -X utf8 -m code_review_graph status      # nodes/edges/files + "Built at commit" — the staleness check
```

If `python` is not the interpreter on this machine, it is `python3` or `py -3` — try in that order
rather than assuming.

Not installed / no `.code-review-graph/graph.db` → the graph steps are **SKIPPED, never blocking**.
Record `SKIPPED (graph unavailable)` and fall back to the agent's own `Grep` tool. Rebuild from
scratch with `python -X utf8 -m code_review_graph build` — a full parse rather than the incremental
one, so it costs whatever the size of the tree costs. Install: `python -m pip install code-review-graph`.

### Query cookbook

Every row below is prefixed by the same `python -X utf8 -m code_review_graph` as the block above —
written out in full each time, for the reason given there.

| Question | Command |
|---|---|
| Does this capability already exist? | `python -X utf8 -m code_review_graph search "<terms>" --kind Function\|Class\|File --limit 15` |
| Who calls this function? | `python -X utf8 -m code_review_graph query callers_of "<symbol>"` |
| Who imports this module? | `python -X utf8 -m code_review_graph query importers_of "<file>"` |
| What does this file pull in? | `python -X utf8 -m code_review_graph query imports_of "<file>"` |
| Which tests touch it? | `python -X utf8 -m code_review_graph query tests_for "<symbol>"` (see limits) |
| Blast radius of a change | `python -X utf8 -m code_review_graph impact --files <f1> <f2> --depth 2 --max-results 60` |
| Risk-scored diff summary | `python -X utf8 -m code_review_graph detect-changes --base <base> --brief` |
| Layer overview (L4+ framing) | `python -X utf8 -m code_review_graph architecture --detail-level minimal` |
| Orphans after a refactor | `python -X utf8 -m code_review_graph dead-code --kind Function --file-pattern "<path>" --limit 20` |
| Rename impact before doing it | `python -X utf8 -m code_review_graph refactor rename --old-name <a> --new-name <b> --kind Function` |

Output is JSON and can be large. Always bound it at the source, with `--limit` / `--max-results` —
not by trimming the output afterwards, which needs a pager this plugin cannot assume is installed.
Quote only the `file_path:line_start` rows you act on: dumping raw graph JSON into the report
defeats the purpose of using it.

`--base` for `detect-changes` / `impact`: resolve it per
`${CLAUDE_PLUGIN_ROOT}/references/shared/125-change-set.md § A`, which carries the three tiers, the
confidence label and the reason a merge-base composed inline — the `git merge-base` call wrapped in
a shell substitution and pasted into the same command — must not be used: that is POSIX
substitution, and cmd.exe passes it through as literal text. Run `git merge-base` on its own line,
read the SHA it prints, and pass that SHA. The branch it forks from is `${git.workBranch}`, not a
hardcoded name. On a long-lived work branch the merge-base can span 1000+ files and caps at 500
functions (`CRG_MAX_CHANGED_FUNCS`) — prefer explicit `--files` from the diff when that happens.

### Limits — where the graph is NOT authoritative `[HARD]`

The parser resolves **static** imports and call sites. It does not see anything reached through a
string or assembled at runtime. For these five, **`Grep` is the authority and the graph is the
hint** — the agent's own `Grep` tool, never a shell `grep`: that binary does not exist on Windows,
and cmd.exe does not treat `'` as a quote, so an `--include='*test*'` matches nothing and the empty
result reads as "nothing found" when it means "the command did not run".

1. tRPC client paths (`trpc.<domain>.<proc>.useQuery`) — the procedure↔caller edge does not exist.
2. TanStack Router route ids / `to="/…"` targets.
3. Drizzle column reads (a column is not a node).
4. Anything behind a dynamic `import()`, a registry map, or a string key.
5. **`tests_for` is incomplete** — measured: one exported function returned 0 tests while a single
   test file referenced it 7×. A zero here means "no static edge found", NEVER "untested". Before
   claiming a test gap, confirm with the `Grep` tool: the symbol under `${paths.backendRoot}` and
   `${paths.frontendRoot}`, then again with `glob: "*test*"` and with `glob: "*spec*"`. The union is
   the answer. A project whose tests live somewhere else says so in `paths` — do not assume a layout
   this repository cannot see.

A graph result therefore **widens** the search and **never narrows** a safety check: it may add
consumers you would have missed, but an empty result never authorizes skipping the `Grep` that a
`[HARD]` rule (tenant filter, PII gate, financial mirror) depends on.
