# Gauntlet SHA-bound review — design spec

**Date:** 2026-09-12 · **Branch:** main · **Baseline:** 4c058cb · **Tier:** L4
**Source:** GitHub issue #22 (implements the contract of #21). Stage 1 read-only slices in the issue
comments are the inventory; this spec is Phase A for the explicit Gauntlet implementation request.

## Objective

`/gauntlet` delivers the Claudex invariants at runtime without a second loop: the plan review is
bound to the SHA-256 of the PLAN bytes, a review-only request stops before any lease, the
inspector role is never the builder role, and every review round lands in an append-only log in
the SDD workspace.

## Decisions

| ID | Decision | Choice |
|---|---|---|
| D1 (#21) | Inspector | **A** — default `graph-powers:evaluator`; `codex:codex-rescue` only on an explicit host request in the turn, recorded in the bind. No new flag. |
| D2 (#21) | Log location | **A** — `.graph-powers/logs/sdd/<plan-slug>/PLAN-REVIEW-LOG.md`, already gitignored by `.gitignore` line 4. |
| D3 | Vocabulary | Mode 1 verdict binds as `APPROVED` or `REVISION_REQUIRED`; evaluator `PASS` maps to `APPROVED`, `FAIL` to `REVISION_REQUIRED`, `BLOCKED` is not bound. Claudex `REVISE`/`BLOCKED` are not imported. |
| D4 | Stale check | Exit `4` with JSON on stdout, the existing bounded-state contract of `sdd.py` (`BOUNDED_EXIT`). |
| D5 | Where the check runs | `acquire --profile gauntlet` refuses a non-`APPROVED` or stale bind after validation and before creating the lease; the default profile is unchanged. |
| D6 | Resume | A gauntlet `acquire` that finds its own matching lease (same plan, same path set) is a resume: it skips the raw-byte check but requires the bind's `scopeSha256` — the bytes with `EVIDENCE:` lines removed and checkboxes normalized — to match, because controller evidence writes are the only legitimate drift after the lease; any other edit is `STALE`. No lease or a foreign lease requires the full check before any lease attempt. |
| D7 | Role ids | `inspector` and `builder` are bounded identities; `inspector` may never equal `builder` (case-insensitive) nor be `main`; `builder` may be `main` on the objective route. |

The user's instruction to implement (2026-09-12) closes the inherited D1–D2 with recommendation A.

## Contract

```text
python -X utf8 sdd.py review-bind  PLAN_FILE --verdict APPROVED|REVISION_REQUIRED --inspector ID --builder ID [--model-requested X] [--model-observed Y]
python -X utf8 sdd.py review-check PLAN_FILE
python -X utf8 sdd.py acquire      PLAN_FILE --max-tasks N --profile gauntlet   -> review-check before lease
/gauntlet [<objective>|<plan>] [--plan <path>] [--dry-run] [--review-only]
```

- `review-bind` hashes the raw bytes of the PLAN file in the worktree (`O_NOFOLLOW`; a symlink or a
  plan outside the repository is refused with exit 2), requires `inspector != builder`
  (case-insensitive; exit 2), writes `plan-review.json` in the plan workspace under the existing
  ledger lock, and appends one line to `PLAN-REVIEW-LOG.md`. A different requested/observed model
  is recorded as `fallback=true`, never hidden.
- `review-check` is read-only: it creates no directory, no file and no lock. Exit 0 only when the
  last verdict is `APPROVED` and the current SHA-256 equals the bound one. Otherwise exit 4 with
  `status` `STALE` (approved but bytes changed), `REVISION_REQUIRED` (last verdict) or
  `UNREVIEWED` (no bind).
- `plan-review.json` keeps the latest round (path table: `references/shared/007-path-conventions.md`): `version`, `planFile`, `round`, `verdict`, `sha256`, `scopeSha256`,
  `inspector`, `builder`, `modelRequested`, `modelObserved`, `fallback`, `recordedAt`.
- `PLAN-REVIEW-LOG.md` line: `<UTC timestamp> round=<n> verdict=<v> sha256=<hex> plan=<relative> inspector=<id> builder=<id> model.requested=<x> model.observed=<y> fallback=<bool>`.
- `/gauntlet --review-only`: validate, one evaluator Mode 1 review, `review-bind`, stop. No
  `acquire`, no Phase C, no writer. With `--dry-run` it also writes no bind.
- `/gauntlet --dry-run` declares the two role ids: `builder` = the write-capable role of the plan's
  dispatch matrix (or the matrix default for an objective) and `inspector` = `graph-powers:evaluator`.
- A non-dry, non-review run enters Phase C only when `review-check` exits 0; exit 4 returns to
  Phase B without a lease.
- Phase C close: the final inspection is a separate fresh evaluator; a controller edit after that
  inspection invalidates it and requires a new one.

## Alternatives rejected

- Storing the SHA inside the write lease: the bind happens in Phase B, before any lease exists.
- Adding `plan-review.json` to the lease path set: it would flip every existing lease to
  `CONFLICT` in `status` and the file is a Phase B artifact.
- JSON ledger for the log: the issue requires text append; JSON stays in the bind file.
- A separate `--inspector` command flag: D1 keeps the default and the opt-in as a host request.
- Vendoring Claudex, `/claudex`, shell scripts, Fable/Astra pins or a route: anti-goals of #21/#22.

## Out of scope

Second loop, host projections edited by hand, a second `test_sdd.py`, Git actions, publishing.
