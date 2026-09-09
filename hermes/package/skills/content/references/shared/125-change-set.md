> Hermes auxiliary: `content/` paths are `file_path` values relative to the registered-document parent. Apply the loaded graph-engineering mapping and host policy; this file is served without template expansion.

## Section 12.5: The change set, and what it is measured against

Every command that judges a change has to answer the same two questions first: **what changed**, and
**what does the graph say it reaches**. Before this file each answered them separately or not at all
— `/verify` asserted "no file outside the task's scope changed" without ever computing a scope, and
`/pr-review` derived its risk signals from line counts and path names.

Loaded by `/verify` § 0.1 and `/pr-review` § 1. Read it once per run; both halves are cheap.

### A. Base detection — explicit scope first, then labeled fallbacks

Explicit target/base wins: use the requested PR metadata, branch or range; never substitute the
checkout or assume `main`. Report target, base, provenance and confidence. A branch name alone does
not specify its base; an unavailable explicit ref blocks that scope rather than enabling fallback.

For the current worktree, union relevant paths from all three states:

| State | Command | Evidence |
|---|---|---|
| staged | `git diff --cached --name-status` | index changes |
| unstaged | `git diff --name-status` | tracked worktree changes |
| untracked | `git ls-files --others --exclude-standard` | inspect relevant new files; absent from diff |

Retain added/renamed/removed status and relevant new consumers/tests; report unrelated exclusions.
Local changes join an explicit current-diff base, but not a PR/branch/range unless requested.

When no explicit base is available, label these fallbacks:

| Tier | Comparison | confidence |
|---|---|---|
| a | current working changes against `HEAD` | high for working state |
| b | declared `git.workBranch`: `git merge-base origin/${git.workBranch} <target>`, then `git diff --name-status <SHA> <target>` | high for declared base |
| c | b unavailable: target's previous commit (current: `git diff --name-status HEAD~1 HEAD`) | low; incomplete branch coverage |

Union a with b (or c), even when both are non-empty. Report unresolved scope or an empty change set,
never infer gate success. Run `merge-base` separately and read its SHA; no shell substitution.

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

Resolve one provider under `content/references/shared/115-code-graph.md` when an
unanswered structural question warrants a query; that file owns selection, effects, freshness,
capabilities and the HARD limits. Sufficient current source or a documentation-only change needs
no graph/status probe. `none` uses text; unavailable/unsupported/stale evidence uses text without
switching providers. A capable caller can supply bounded source-grounded evidence to reviewers.

For impact, reuse, callers and possible orphans, select a supported operation from that cookbook.
Record risk scoring or dead-code detection as UNSUPPORTED when the provider lacks an equivalent;
use the diff and decisive source/test reads. Never treat an absent score as low risk. Preserve the
union with scoped textual consumers/tests, especially registry strings, dynamic imports and Markdown
wiring; zero static test edges never means untested. Report only acted-on `path:line` rows plus
provider, scope and freshness/limitations, not raw graph output.
