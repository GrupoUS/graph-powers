# Authoring and iterating one skill

Use this only for Mode A. Change one explicit behaviour at a time; retain the folder name/frontmatter
contract and move detail into a referenced file rather than growing the entry.

## Step 1 — Capture intent
State the user wording that should trigger, the boundary that must not trigger, the owner, and one
observable acceptance condition. Reuse an existing skill or reference before creating another.

## Step 2 — Plan and research
Inspect the target and its call site. Research only when the behaviour depends on an external fact.
Classify the skill as technique, pattern, reference, or discipline so its proof matches the risk.

## Step 3 — Initialize
Keep `SKILL.md` as the entry, `references/` for conditional detail, `scripts/` only for runnable
mechanics, and `evals/` only for behavioural calibration. Name paths from the entry; unreferenced
detail is an orphan.

## Step 4 — Write the skill
The description names user trigger words and exclusion, not the workflow. Keep the body short:
trigger, minimum method, acceptance/stop, and conditional references. Preserve frontmatter limits and
the folder/name match; use one canonical owner for a contract.

## Step 5 — Test and evaluate
For a changed trigger or rule, capture a failing/baseline case, make the smallest edit, then run
`quick_validate.py <skill-path>`. Add or update only the focused semantic assertions needed for the
changed contract. A broad set is for `--all`, observed collision, or an explicit request; fixture
assertions are not a fresh model evaluation.

### 5c. Draft assertions while the runs complete

Assertions must distinguish correct from incorrect behavior: use word boundaries for short tokens,
test both match and non-match samples, express prohibitions through the desired behavior ("no patch
applied" contains "patch applied"), and use `(?i)` when prose casing is irrelevant. Test paths and
commands in their real quoted form. These rules apply to focused cases as well as broad runs.

### Lifecycle-triggered evidence
Report the intent, changed edge and actual focused result. Read `learning.md` only when an observed
failure matches a named pattern; do not manufacture a history round for ordinary prose.

### Validator and runner edge cases
`run_evals.py` grades either one `--test-case`/response file or a response directory with one file
per case. Never flatten multiple cases into the default mode: positive and negative assertions can
cancel. Use `--threshold 1.0`; a critical failure exits nonzero.

## Step 6 — Improve and iterate
If the focused proof fails, revise the smallest relevant wording/rule and rerun it. Escalate to Mode
B only when a second claimant, call site, resolver or registration edge is evidenced.

## Step 7 — Optimise the description
Front-load the trigger and meaningful exclusion. Test overlap against neighbours only when it is
plausible, not as a mandatory inventory.

## Degrees of freedom
Do not prescribe a format when user language, repository conventions, or the domain already decides
it. Add guidance only when it prevents an observed failure.

## Anti-patterns
Do not summarise the procedure in the description, duplicate a canonical reference, create an eval
just to inflate coverage, or call a captured fixture a model run.

## Quality checklist
The entry routes correctly, detail is conditional, the changed rule has proportionate proof, and all
live paths resolve.
