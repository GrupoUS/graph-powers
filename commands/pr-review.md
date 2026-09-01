---
description: "Review a PR, branch or diff before merge. Uses one adversarial Evaluator plus only surface-required security/design specialists, then returns prioritized findings, a verdict and a ready comment. Read-only unless --fix; never approves or merges. Modes — <PR#> · --current · --branch <name> · full. Flags — --quick, --fix. Not for plan execution (/implement) or gate proof (/verify)."
workflow_type: prompt-chaining
---

# /pr-review — Unified PR Review

**ARGUMENTS**: $ARGUMENTS

> **Read before step 0 — never reconstruct these from memory:** `${CLAUDE_PLUGIN_ROOT}/references/shared/000-config-loader.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/005-method-bootstrap.md`
> Read `${CLAUDE_PLUGIN_ROOT}/references/shared/070-parallel-agent-spawn.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/125-change-set.md`

```
gh pr checkout <PR#>
/pr-review <PR#>              # full path
/pr-review --current          # already on the PR branch
/pr-review --branch <name>    # local branch review, no PR open
/pr-review <PR#> --quick      # 3B only, and only on a sensitive surface (§ 7)
/pr-review <PR#> full         # deep: every path, references loaded in full
/pr-review <PR#> --fix        # opt-in: apply P0/P1 findings, test-first
```

---

## Iron Law

```
NEVER run `gh pr review --approve`, `gh pr merge`, or push to a protected branch.
NEVER apply an adversarial finding automatically — findings are presented, then decided.
NEVER give a review task to a write-capable agent.
Every PR comment and every P0/P1 finding passes through the § 4.1 receiving-feedback protocol
before it turns into a decision.
```

This command changes **source** only under an explicit `--fix`, through the smallest bounded set of
existing write-capable Graph Powers roles with disjoint ownership.

The default creates no report and nests no review command; `code-review` and `/debug audit pr`
remain separate, explicit products.

---

## Stopping conditions

- Phase 0 finds a branch mismatch (PR head ≠ current branch) → ask for `gh pr checkout`; never run it silently.
- `gh auth status` fails → tell the user; never attempt `gh auth login`.
- Any field of the § 2 review bundle fails to resolve (base SHA, head SHA, description, focus) → stop. Dispatching an agent with an unresolved placeholder is the anti-pattern this bundle exists to prevent.
- The diff exceeds 1000 lines with no scope justification in the PR body → surface it before spawning the deep review; a review that large is a review nobody actually performed.
- A path returns P0/P1 → present and ask. Never auto-fix.
- A `chain.lenses` entry names an agent that does not resolve → say so in the output before the batch;
  never let the lens drop out silently.
- § 4.1 classifies a comment as **clarify** → surface every open question before deciding anything.
- `graphGuardrails.maxRepatch` failed fix attempts on the same file (`--fix` mode) → escalate to `/debug recover`.

---

## 0. Pre-flight

Resolve the config (`${CLAUDE_PLUGIN_ROOT}/references/shared/000-config-loader.md`). Confirm the working tree state, the branch, the diff
base, and — for a PR — `gh` auth and PR metadata.

**Only when `full` mode is requested**, additionally load, in full: `${CLAUDE_PLUGIN_ROOT}/references/safety-floor.md`,
`${CLAUDE_PLUGIN_ROOT}/skills/debugger/references/structural-quality.md`,
`${CLAUDE_PLUGIN_ROOT}/skills/debugger/references/anti-patterns.md`, and the nearest `AGENTS.md`
for every touched path. `full` overrides `--quick`.

---

## 1. Scope and risk signals

Collect, from the diff alone — no memory, no assumption:

Resolve the base ref and the surfaces per
`${CLAUDE_PLUGIN_ROOT}/references/shared/125-change-set.md § A-B`, and probe the graph once (§ C).

| Signal | How |
|---|---|
| Files touched, by layer | diff paths mapped onto `paths.*` |
| Total added/removed lines | `git diff --shortstat <base>...HEAD` |
| Any file crossing 1000 lines | `git diff --numstat`, then the **Read tool** for length — `wc` does not exist on Windows |
| Sensitive surfaces touched | auth, payment, personal data, schema, environment, CI |
| Declared gates that changed | anything under the CI config or the scripts the gates call |
| **Risk, ranked, from structure** | `detect-changes --base <baseRef> --brief` — a per-file score the line count cannot give |
| **What the diff reaches but does not show** | `impact --files <changed> --depth 2` — the "12 files changed, 80 affected" case a PR view structurally hides |

The last two are `SKIPPED (graph unavailable)` when § C said so, and the review continues. They are
the reason this section stopped being a line count and a path-name guess.

A sensitive surface in the diff raises the floor: it is reported in the output **even when the
verdict is approve**. Hiding drift because the decision went the other way is how a review stops
being worth reading.

The project's own mechanical checks live in root `REVIEW.md § Mechanical checks`, and its blocking
findings — what has actually broken *this* repository — in `§ Blocking findings`. Run the checks
here, before any judgement path, and treat a hit as a blocker rather than a note. This plugin ships
none of its own: a check that does not match the repository is a line that reads as coverage.

`REVIEW.md § Surfaces that raise the bar` decides which parts of the diff get the harder review.

---

## 2. Review bundle

One resolved block, reused verbatim by every path in § 3. Build it once:

```
REPO        <name> · branch <head> vs base <base ref>
COMMITS     <n> · files <n> · +<added>/-<removed>
DESCRIPTION <PR body, or the branch's stated intent>
FOCUS       <what the author asked to be reviewed, or "unstated">
GATES       <command → result, per declared gate>
SENSITIVE   <surfaces from § 1, or "none">
FLOOR       Read ${CLAUDE_PLUGIN_ROOT}/references/safety-floor.md before reporting.
RETURN      Findings only: severity | file:line | defect | failure scenario. No praise, no summary.
```

Every unresolved field is a stop, not a placeholder.

---

## 3. Review paths (parallel)

Follow `070-parallel-agent-spawn.md`, then dispatch **every applicable track in one message**, each
`run_in_background: true`. The table below is the complete dispatch.

**Codex routing note.** This command owns the deterministic review fan-out and its bounds; the
semantic agent policy only selects the model lane for each dispatched role. Do not layer the
top-level `native-ultra` orchestration policy on this fan-out.

**Read-only by frontmatter, never by instruction.** Every agent here resolves with
`disallowedTools: Write, Edit` or an allowlist without them. A prompt saying "do not fix" is a
request; the incident behind that rule is in
`${CLAUDE_PLUGIN_ROOT}/skills/debugger/references/anti-patterns.md`.

| # | Agent | The question it asks | Fires when |
|---|---|---|---|
| 3A | `graph-powers:evaluator` | is it correct, structurally sound, and free of hot-path regressions | always |
| 3B | `graph-powers:security-reviewer` | is it exploitable — tenant, personal data, authorization, secrets | sensitive surface touched, or `full` |
| 3C | `graph-powers:ui-ux-designer` | tokens, states, keyboard, contrast, smallest viewport; motion via `animate` review mode | `web` touched |

The Evaluator's consolidated prompt includes the hot-path checklist when `api`, `schema` or `web`
is touched: N+1, `select *`, missing FK index and bundle growth. This keeps one adversarial owner for
correctness and structural quality instead of spawning another generalist over the same diff.

**The project extends these questions.** `chain.lenses` in the config is a first-class contract — each
entry a `name`, its own binding `checks`, an optional `agent` and a `when` — and the schema states
the principle it exists for: *each lens is a distinct question; identical skeptics agree with each
other and miss the same things*. Fold compatible checks into 3A-3C; never spawn one agent per lens.
A genuinely distinct role replaces the least relevant optional track so the batch stays at three. A lens
naming an agent this plugin does not ship is **named in the output before the batch runs**, because
a misspelt value otherwise spawns nothing and the review reports one check fewer than it claims.

### What every track returns

The findings table of
`${CLAUDE_PLUGIN_ROOT}/skills/senior-prompt-engineer/references/parallel-batch-contracts.md`, with
severity on the **P0-P3 scale** — one scale for every track, so § 4 can compare them. Then, and this
is the part the bundle used to forbid:

```
COVERED   <what this track examined and found clean, one line>
```

Without it, § 4's "only one path raised it, the others checked" cannot be evaluated — the previous
return contract said "findings only, no summary", which made half of the consolidation rule dead
text. Negative coverage is evidence and has to be asked for.

Each dispatched track is blind to the others by construction. One consolidated Evaluator review is
the acceptance boundary; do not add a refuter for each finding.

## 4. Receive and consolidate

### 4.1 Receiving feedback protocol

This is the single source for handling code-review feedback. `/debug recover` and the Phase C
review loops in `skills/planning/references/phase-c-executing-plans.md` read this section; they do
not restate it. Feedback is evaluated technically,
not performed socially: **verify before implementing, ask before assuming, correctness over
comfort.**

For every human comment and generated finding:

1. **Read** the whole item without reacting.
2. **Understand** — restate the requirement in your own words, or ask a specific question.
3. **Verify** — check the claim against the current code, tests and supported runtime.
4. **Evaluate** — decide whether it is technically sound for this codebase.
5. **Respond** — classify it `implement`, `clarify` or `pushback`, with the evidence or question.
6. **Implement** — preserve one-item traceability while clustering compatible items into the
   bounded role packages in § 6. This runs only under explicit `--fix`; otherwise it is deferred.

Nothing is edited until **every** item has reached step 5. One unclear item blocks all fixes: list
every unclear item and ask first, because related feedback implemented from a partial understanding
is still wrong.

**Check the source.** User feedback is trusted once understood, but unclear scope still blocks.
For an external reviewer — including this harness's evaluator and security or design review —
verify five things before implementing: it is correct here; it preserves
existing behaviour; the reason for the current code is understood; it works on every supported
platform and version; and the reviewer had the necessary context. A finding with confidence 2 or
below is not implemented unless marked `[ASSUMED]` and accepted explicitly. Wrong feedback gets
technical pushback; unverifiable feedback states what evidence is missing and asks whether to
investigate, ask or proceed. A conflict with a user decision stops for the user.

**Run the YAGNI check.** When asked to implement something "properly", search for real callers
first. If nothing uses it, propose removal instead of adding an unneeded feature.

**Respond without theatre.** Never lead with "You're absolutely right", "Great point", thanks or
"Let me implement that" before verification. State the requirement, ask the question, give the
technical reason for pushback, or let the fix speak. Push back when the suggestion breaks working
behaviour, lacks context, violates YAGNI, is wrong for the stack or compatibility floor, or
contradicts an architectural decision; cite the code or test that proves it. Correct feedback gets
`Fixed — <what changed>` or just the fix; no apology, defence or over-explanation.

After every ambiguity is resolved, work in this order: blocking/security → simple
(typos/imports) → complex (logic/refactors). Test each fix independently, then run the regression
check after the last one. Never batch untested fixes, assume a reviewer is right, avoid warranted
pushback, implement only the clear subset, or proceed when the claim cannot be verified. Leave an
uncommitted working-tree checkpoint; commit only with the user's approval in the current turn.

**GitHub threads.** An inline review comment is answered in its own thread through
`gh api repos/{owner}/{repo}/pulls/{pr}/comments/{id}/replies`, never as a top-level comment.
Posting leaves the repository and requires the user's approval in the current turn.

### 4.2 Consolidation

1. **Collect** every path's findings into one table, de-duplicated by `file:line` + defect.
2. **Merge** with the PR's existing human comments — an unanswered reviewer comment is a finding.
3. **Classify each item**: `implement` (real, fix it), `clarify` (needs the author or the user),
   `pushback` (technically wrong, with the reason).

4. **Weigh by agreement**, on the P0-P3 scale every track now returns:
   - raised by two or more tracks → **promote one level**, capped at P0;
   - raised by one track, and another track's `COVERED` line names that same ground → **demote one
     level**, floored at P3;
   - raised by one track and nothing else looked → **keep the severity, and say no other track
     covered it.** That is a coverage gap, not agreement, and collapsing the two is how a review
     reads as thorough while one opinion carries it.

   The `COVERED` line is what makes the second rule evaluable at all. Before it, demotion asked
   whether "the others explicitly checked" while the return contract forbade them from saying.

---

## 5. Output

```markdown
## Review — <PR #N or branch> · <date>

### Summary
<what this change does, in the reviewer's words, not the author's>

### Blocking
| Sev | Location | Defect | Failure scenario |

### Non-blocking
| Sev | Location | Defect | Why it is not blocking |

### Structural quality
<size crossings, growth patterns, duplication — or "no structural findings">

### Sensitive surfaces
<auth / payment / personal data / schema / environment / CI touched by this diff — always present,
even when the verdict is approve>

### Verdict matrix
| Path | Result | Findings |
|---|---|---|
| evaluator (3A) | APPROVED / CHANGES_REQUESTED / SKIPPED | P0=<n> P1=<n> P2=<n> |
| security-reviewer (3B) | PASS / FINDINGS / SKIPPED (+reason) | <n> |
| ui-ux-designer (3C) | PASS / FINDINGS / SKIPPED (surface untouched) | <n> |
| project lenses (`chain.lenses`) | per lens: PASS / FINDINGS / SKIPPED / AGENT NOT FOUND | <names> |
| Change set | baseRef `<ref>` · confidence high/low · graph USED / SKIPPED | <n files> |
| Declared gates | per gate: PASS / FAIL / NOT DECLARED | <evidence> |
| Project blocking list (`REVIEW.md`) | per ID: PASS / HIT / NOT DECLARED | <which IDs> |
| CI checks | PASS / PENDING / FAIL | <failing names or "all green"> |
| Comments triaged | implement=<n> clarify=<n> pushback=<n> | — |

### Decision
**APPROVE** · **COMMENT** · **REQUEST CHANGES**

<Three lines at most. Name the sensitive surfaces if any were touched.>

**Structural approval bar** (per `structural-quality.md § Approval Bar`, active whenever 3A ran):
any presumptive blocker present ⇒ default **REQUEST CHANGES**, unless the author justified it in the
PR in one line naming the blocker — a file crossing 1000 lines, spaghetti growth in an existing
flow, incidental complexity preserved, wrapper/cast/optionality churn, a layer boundary leak, or a
near-duplicate of an existing helper.

### Ready to post
<the comment body, verbatim, for `gh pr review --comment --body-file -`>
```

**Never print a suggested `gh pr review --approve` or `gh pr merge`.** The command produces a body;
the person decides and runs it.

---

## 6. Fix loop (`--fix` only)

1. After every item has reached § 4.1 step 5 and no `clarify` item remains, list the `implement`
   items, P0 first.
2. Group compatible items by disjoint ownership and existing writer role: general or security fix →
   `graph-powers:debugger`; web UI → `graph-powers:frontend-specialist`; measured performance →
   `graph-powers:performance-optimizer`; mobile → `graph-powers:mobile-developer`. Never dispatch a
   read-only reviewer as a fixer, invent a role, or create one agent per finding.
3. Reserve one fresh Evaluator re-review, then dispatch at most `graphGuardrails.maxParallelWave`
   writer packages in one bounded wave. The initial review, writers and re-review together stay
   within `graphGuardrails.maxSpawnsPerWorkflow`; defer excess packages explicitly.
4. Inside each package, keep item-level evidence: failing behavior test first, minimal fix, then its
   focused regression check. Run resolved project-wide gates once after the wave; JS/TS gates follow
   `references/shared/130-typescript7-oxc-gates.md`.
5. Stop after `graphGuardrails.maxRepatch` failed attempts on the same file → `/debug recover`.
   Read the number from config; do not hardcode it.
6. Give the whole corrected diff and original accepted findings to one fresh
   `graph-powers:evaluator`. This is the only correction re-review; do not re-run one path per
   finding. Open P0/P1 remains `REQUEST CHANGES`.

Never commit. The fixes land in the working tree; the person commits them.

---

## 7. Mode matrix

| Phase | default | `full` | `--quick` | `--branch` | `--fix` |
|---|---|---|---|---|---|
| 0 pre-flight | yes | yes (+ full reference load) | yes | yes (no PR metadata) | yes |
| 1 scope and risk | yes | yes | yes | yes | yes |
| 2 bundle | yes | yes | yes | yes | yes |
| 3A evaluator | yes | yes (+ source citation per finding) | skip | yes | yes |
| 3B security-reviewer | yes | yes | only if sensitive surface | yes | yes |
| 3C ui-ux-designer | if `web` touched | yes | skip | if `web` touched | yes |
| project `chain.lenses` | per `when` | all | skip | per `when` | per `when` |
| 4 consolidate | yes | yes | yes | yes (no PR comments) | yes |
| 5 output | yes | yes | yes | yes | yes |
| 6 fix loop | no | no | no | no | **yes** |

---

## 8. Output guarantees

- Never states APPROVE without 3A having run and passed. `--quick` skips 3A, so **`--quick` cannot
  produce APPROVE** — it produces COMMENT and names the mode as the reason.
- Never hides drift: a sensitive surface in the diff appears in the output regardless of the verdict.
- Never reports a skipped path as a passed path, and never reports a lens whose agent did not
  resolve as a lens that ran.
- Every severity in the table traces to a `file:line` someone opened. The blocking and non-blocking
  tables carry the locations; the matrix carries the counts, and the two must reconcile.
- Never claims the graph was used when § 1 recorded `SKIPPED`, and never turns a `tests_for` zero
  into a coverage finding.
