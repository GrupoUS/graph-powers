> Hermes auxiliary: `content/` paths are `file_path` values relative to the registered-document parent. Apply the loaded graph-engineering mapping and host policy; this file is served without template expansion.

# Harness wiring audit — does this harness resolve to itself?

Mode B is read-only and changed-edge first. Use `--all` for a whole-harness inventory; otherwise
trace only the reported or changed caller → resolver → target path. Report evidence and do not patch.

## Phase 0 — Inventory
Record the scope, changed paths and relevant artefact types. Reopen the target on disk before calling
an edge missing. Do not enumerate unrelated layers without a collision or `--all`.

## Phase 1 — Static validation
Run the smallest affected structural/configuration check. Corrupt input is a `path:line` finding,
not a reason to stop the scan.

## Phase 2 — The wiring graph
Trace invocations, registrations, imports and generated projections from caller to target. Mark each
edge resolved or `DANGLING` with its cause and evidence.

## Phase 3 — Shadowing and name collision
Run only for duplicate/retired names or listing mismatch. Compare the serving descriptions and
applicable precedence, aliases, symlinks and importers. Classify an unreferenced artefact as
`DOCUMENT`, `DIRECT_INVOCATION_OK`, or `REMOVAL_CANDIDATE`; never delete it in this round.

## Phase 4 — Trigger collision
Compare descriptions only where two real claimants overlap. A single weak description belongs to
Mode A. State the proposed owner/rename, but leave changes for approval.

## Phase 5 — Independent judgement
Use the read-only `graph-powers:skill-improver` only for `--all`, a material collision, or contradictory
evidence. Give it the changed-edge evidence and retain its verdict separately from collection.

## Phase 6 — Synthesis and stop
Return scope, resolved/dangling edges, severity, uncertainty, evidence and next action. Stop; Mode B
does not apply a patch. A P0 with low confidence after two checks is `BLOCKED`.

## Gates for Mode B
Run only affected checks: `content/skills/skill-improve/scripts/quick_validate.py` for altered skills, config JSON when it participates,
and caller/registration/parity checks for the edge. A broad trigger suite is required only for
`--all` or observed collision. Report commands actually run; do not claim a required failure
direction without executing it.

## Stopping and red flags
Stop on incomplete scope, a blocker needing user authority, or a configured spawn cap. Never propose
application/package source edits in this audit.

## References
Use `content/references/rubrics/skill-improver-rubric.md` for the scoring contract and
`content/agents/skill-improver.md` for the judge. Shared quality, verdict and spawn rules remain in
`content/references/shared/`.

## Configuration
Read `.graph-powers/config.json` when present; otherwise report the defaults used. The audit stays
fail-open and writes no harness change.
