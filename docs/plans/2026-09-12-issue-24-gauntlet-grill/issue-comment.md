<!-- graph-powers:issue-improve -->
## Completed implementation — issue #24 (local 1.20.7)

Scope: L3, risk surfaces `none`. Extend the existing Gauntlet flow; no new `/grill` command,
listed skill, runtime ledger or vendored repository. The current request explicitly authorizes
implementation, superseding the earlier Stage 2 hold.

Evidence: `commands/gauntlet.md` routes objectives into Planning; the pre-change Phase A Step 2 asked a
single clarification batch; `gauntlet-loop.md` validates the plan and its bound review before
execution. A pre-change isolated agent response reproduced the gap: prior session approval was
treated as sufficient to omit frontier rounds and shared-understanding confirmation.

All six requirements are KEEP: (R1) frontier plus confirmation; (R2) recommendations and factual
lookup; (R3) hole-only inspection for approved plans; (R4) dry-run/review-only/L1-L2 boundaries;
(R5) existing HARD-STOP and one canonical owner; (R6) focused proof, attribution and projections.

1. **T1.1 — R1–R6:** extend `commands/gauntlet.md`, Phase A Step 2, Gauntlet Entry and planning
   evals. Each ready decision gets a recommendation; answers advance the frontier. Pending
   research/dependent branches and assumptions cannot count as completion. Explicit confirmation
   precedes Phase B/C, lease and product writers. Approved plans inspect only unresolved holes;
   edits invalidate the bound review. Dry-run describes without live questions; review-only stops.
   **CHECK:** `python3 skills/skill-improve/scripts/run_evals.py --skill-path skills/planning
   --evals-path skills/planning/evals/evals.json --response-file
   .graph-powers/logs/issue-24/resp-gauntlet-neg-objective-no-grill-no-phase-c.txt
   --test-case gauntlet-neg-objective-no-grill-no-phase-c --threshold 1.0` → `PASSED`, 100%.
   Structural quick_validate and the other focused cases are complementary checks.
   **Evidence:** baseline remains RED (exit 1); post-change response passes 5/5 at threshold 1.0.
   Nine selected responses passed: seven initial and two complementary captures after a request
   for more detail. Eighteen positive and 28 negative parser controls matched expected exits.
   Captures are policy simulations, not installed runtime telemetry.
2. **T1.2 — R6, depends on T1.1's canonical bytes:** update NOTICE, CHANGELOG and six version
   owners to 1.20.7; regenerate Codex and Hermes projections using existing generators.
   **CHECK:** `bun hermes/install.mjs --check` → `source manifest and package are current`.
   **Evidence:** six version owners read 1.20.7; Codex/Hermes static gates pass; Hermes reports
   39 registrations and current source/package. The thin Codex command wrapper stays identical.

Ownership: one sequential implementation lane; independent plan and final diff reviews.
Final validation: the repository's declared gate inventory, focused parser controls and isolated
agent pressure responses. Preserve existing SDD review binding and non-Gauntlet planning.
The grill is a controller instruction contract; this change does not make the CLI independently
verify human answers. Installed-client behavior and Hermes runtime are not claimed by static proof.

Frontend/backend/database product changes: N/A; this is the shared harness. No commit, push or
installation is included. Final independent review: **PASS, no P1/P2 introduced**. The ordered inventory ran: **27/28 gate
   groups passed**, including 62 SDD tests. Gate 24 remains failed because the preexisting untracked
   `yaml` file alone occupies 12,221,795 bytes; it was preserved. At the gate snapshot, source size
   excluding that unrelated file was 3,882,812 bytes, below 4 MiB; the Hermes package also fits its
   2 MiB limit. No checker or cap was weakened. This is a disclosed workspace issue, not a regression
   from #24; the full workspace is not claimed all-green.

   Closing as implemented within the requested scope. Changes remain local and unstaged: **no
   commit, push, release or active-client installation was performed**.
