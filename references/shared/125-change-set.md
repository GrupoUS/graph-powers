## Section 12.5: The change set, and what it is measured against

Every command that judges a change has to answer the same two questions first: **what changed**, and
**what does the graph say it reaches**. Before this file each answered them separately or not at all
— `/verify` asserted "no file outside the task's scope changed" without ever computing a scope, and
`/pr-review` derived its risk signals from line counts and path names.

Loaded by `/verify` § 0.1 and `/pr-review` § 1. Read it once per run; both halves are cheap.

### A. Base detection — three tiers, and the confidence they carry

The base ref is not obvious, and guessing it wrong silently changes every downstream answer. Resolve
it in this order and **carry the label**, because a reviewer told `confidence: low` reads the rest
differently:

| Tier | Command | baseRef | confidence |
|---|---|---|---|
| a | `git diff --name-only HEAD` | `HEAD` | high |
| b | (a) empty → `git merge-base origin/${git.workBranch} HEAD`, read the SHA, then `git diff --name-only <that-SHA> HEAD` | that SHA | high |
| c | (b) fails, no local `origin/${git.workBranch}` → `git diff --name-only HEAD~1 HEAD` | `HEAD~1` | low |

If (a) and (b) are both non-empty, **union them**.

Two things that look like details and are not. Run the `merge-base` on its own line and read the SHA
it prints: `$(...)` is POSIX substitution and cmd.exe passes it through as literal text, so the
composed form fails on Windows in a way that reads as an empty diff. And an empty change set is an
answer, not a nuisance — a verification run against an unchanged tree must say so rather than report
everything green.

### B. Surfaces — what the change set touched

Map the changed paths onto the surfaces the project declared, and use the result to skip work rather
than to do it. An untouched surface costs nothing:

| Surface | Typically | Gates work on |
|---|---|---|
| `web` | `${paths.frontendRoot}` | design, accessibility, viewport, bundle |
| `api` | `${paths.backendRoot}` | procedure boundaries, authorization, N+1 |
| `schema` | `${paths.schemaRoot}` | migration, index, tenant predicate |
| `ci` | the CI config and the scripts the gates call | whether a gate can still fail |

The project extends this through `chain.surfaces`, and `chain.contractGates[].when` fires its own
commands off the same booleans. A surface list that does not match the repository is worse than
none, because it reads as coverage.

### C. The code graph — a hint, and never a verdict

Probe once, at the start, and record the answer either way:

```bash
python -X utf8 -m code_review_graph status
```

Unavailable, or `Nodes: 0` → record **`SKIPPED (graph unavailable)`** and use grep for everything
below. This is never a failure and never blocks: the contract is in
`${CLAUDE_PLUGIN_ROOT}/references/shared/115-code-graph.md`, and it is the whole reason a design
built on the graph is safe to ship. If the interpreter is not `python`, it is `python3` or `py -3`.

Available → `python -X utf8 -m code_review_graph update -q` first. Never judge on a stale graph.

| Question a review actually asks | Query |
|---|---|
| What does this change reach that the diff does not show? | `impact --files <changed> --depth 2 --max-results 60` |
| Which files carry risk, ranked? | `detect-changes --base <baseRef> --brief` |
| Does the thing this change adds already exist? | `search "<terms>" --kind Function\|Class\|File --limit 15` |
| Who calls the symbol this change touched? | `query callers_of "<symbol>"` |
| Did the change orphan anything? | `dead-code --kind Function --file-pattern "<changed dir>" --limit 20` |

**`[HARD]` Five things the graph does not see**, and where grep is the authority: tRPC client paths,
router route ids, ORM column reads, anything behind a dynamic `import()` or a string key, and
`tests_for`. That last one is the trap: a measured case in `115-code-graph.md` returns **zero** tests
for a symbol its test file references seven times. **A zero from `tests_for` means "no static edge
found", never "untested"** — quote it as a candidate proof to run, never as a coverage finding.

Quote only the `file_path:line_start` rows you act on. Dumping graph JSON into a report spends the
context the graph was meant to save.
