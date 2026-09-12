# Gauntlet decision frontier

## Architecture

Extend the existing Gauntlet entry and Phase A Step 2. For an objective at L3+, maintain a
decision tree, ask only the ready frontier with a recommendation per question, wait for answers,
then recompute. Look up facts locally; pending research keeps its dependent branch open.
An empty ready frontier is insufficient while research or dependent decisions remain unresolved.
Completion requires every branch settled and explicit user confirmation of shared understanding.
Session execution approval alone does not provide that confirmation. The current user's request
authorizes implementing this bounded issue; it does not invoke Gauntlet on this implementation.

Approved plans retain their settled decisions without a fresh grill or confirmation. Before validation, inspect only unresolved TBD, `[ASSUMED]` and
missing dependency payloads; `Needs: none` is valid and `EVIDENCE: pending` is not a hole. Reopen their dependent decisions only and confirm the repaired understanding. Changed plan bytes require
validation and a new bound review. Dry-run describes the gate without live questions or effects;
review-only reports gaps and stops before execution. L1-L2 remain ineligible.

Reuse Phase A's existing HARD-STOP ceiling for clarification rounds; reaching it preserves open
decisions and stops, never substitutes assumptions or resets the counter. Preserve normal planning
outside the explicit Gauntlet route. No new command, skill, state store or runtime acquire flag.

## Data and boundaries

No product frontend, API, database, auth, PII or deployment changes. Producer/consumer edges:
commands/gauntlet.md → Planning Phase A Step 2 → Gauntlet entry → existing Phase B review/Phase C;
canonical command/reference bytes → generated Codex and Hermes packages.
The grill is a controller instruction contract; the existing review hash check is mechanical.
Do not claim the CLI independently proves human answers.

## Validation

Capture a pre-change agent response, pressure-test the changed instructions and grade focused
cases through run_evals.py with --threshold 1.0. Include missing confirmation, unresolved research,
round ordering, ready plans, plan holes, dry-run, review-only and unchanged L1-L2 rejection.
Parser controls establish assertion discrimination, not installed-client runtime telemetry.
Run quick_validate, projection checks and the repository gate inventory. Record MIT attribution
for Matt Pocock's source-informed grilling adaptation; bump 1.20.6 to 1.20.7 and regenerate.
