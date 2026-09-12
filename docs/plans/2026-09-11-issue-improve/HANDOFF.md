# Issue 20 — implementation handoff

## Objective and authorization

Implement issue 20 (`/issue-improve`) locally through the requested Gauntlet. The user's
2026-09-12 request (`/gauntlet analise o issue 20 e aprimore e implemente e apos feche a issue com
comentarios`) authorizes local implementation and closing issue 20 with comments. It does not
authorize staging, commit, push, installation or any other outward write. Checkout `main` at
4c058cbe7e9e39730529f0b1852a0b753866ad11. The pre-existing dirty `bin/graph-powers.mjs`
(SHA256 c889f134c66633b83c5191221f1c0bee31e04669179131d0eb8c1b1d6345932f) is out of scope and
untouched.

## Completed

[PLAN.md](PLAN.md) T1.1 implemented; G1.1–G1.5 checked with evidence. Version 1.20.5 in six
manifests. Wave review PASS, security review PASS, final review `WITH FIXES` (both fixes applied:
complete inventory rerun and this handoff). Evaluator Minors 3, 5, 6 and 8 were also corrected:
fixture links became plain paths, the helper selects only comments whose first line is the marker,
`--repo`/URL wording fixed, and drafts over 65,536 characters block before any `gh` call.

Context-budget decision: `.github/check_context_budget.py` caps raised 50,000→50,500 and
200,000→205,000 under the gate's own documented path (the command set sat at 49,995 B floor, so no
new command could fit); the file joined T1.1 Owns and the lease; CHANGELOG 1.20.5 records why.

Evidence: complete declared inventory (31 commands, in order) 31/31 exit 0 on the final tree at
`.graph-powers/logs/sdd/2026-09-11-issue-improve/gates/inventory-2026-09-12-final/`; helper 15
tests OK; evals 5/5 (22 assertions); Hermes `--check` current (39 registrations). Ledger:
`task-reviews.md` in the same log directory. Sources and generated package remain unstaged and
untracked.

## Closed

Verify loop `VERIFIED-WITH-NOTES` (fresh evaluator reran every declared gate on the live tree);
its two text corrections applied (cited skill bytes 7,379; closed-tree package
`review-closed-4c058cb..107a34b.diff`). Learnings entry appended to `.graph-powers/logs/learnings.md`;
lease released. Issue 20 received the marked plan comment through
`issue_comment.py --publish` (first real publication; an immediate rerun reported `unchanged`) and
was closed with a completion comment on 2026-09-12. Installed Codex/Cursor/Grok/Hermes runtime
remains UNVERIFIED (static proofs only).

## Exactly one next action

Commit and push are not authorized by this turn: when the user asks, stage exactly the paths in
T1.1 Owns plus `docs/plans/2026-09-11-issue-improve/`, leaving `bin/graph-powers.mjs` and other
sessions' work out, and rerun `python3 .github/check_version_bump.py` before the commit.
