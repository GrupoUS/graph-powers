---
description: "Review a pull request or a branch before it merges. Use when the user names a PR number, asks to review the branch, the diff or their changes, or asks what a reviewer would say. Runs an adversarial evaluator, a security reviewer, the code-review skill and /debug audit in parallel, consolidates through superpowers:receiving-code-review, and returns a verdict plus a ready-to-post comment body. Read-only; never approves or merges. Modes — <PR#> · --current · --branch <name> · full. Flags — --quick, --fix, --no-debug. Do not use to apply the findings (/implement) or to run the gates (/verify)."
workflow_type: prompt-chaining
---

# /pr-review — Unified PR Review

**ARGUMENTS**: $ARGUMENTS

> **Read before step 0 — never reconstruct these from memory:** `${CLAUDE_PLUGIN_ROOT}/references/shared/000-config-loader.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/005-superpowers-bootstrap.md`
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
Every PR comment and every P0/P1 finding passes through superpowers:receiving-code-review
before it turns into a decision.
```

This command changes **source** only under an explicit `--fix`, and then only through a foreground
`graph-powers:debugger` agent with gates between fixes.

One honest exception, because "read-only" was overstated before: § 3F runs `/debug audit pr`, which
writes its consolidated report to `docs/AUDIT-REPORT-<YYYY-MM-DD>.md`. That happens in the default
mode, with no `--fix`. It touches no source and no git state, but it is a file this command creates
— say so in the output rather than letting the claim stand. `--no-debug` skips 3F and with it the
report.

---

## Stopping conditions

- Phase 0 finds a branch mismatch (PR head ≠ current branch) → ask for `gh pr checkout`; never run it silently.
- `gh auth status` fails → tell the user; never attempt `gh auth login`.
- Any field of the § 2 review bundle fails to resolve (base SHA, head SHA, description, focus) → stop. Dispatching an agent with an unresolved placeholder is the anti-pattern this bundle exists to prevent.
- The diff exceeds 1000 lines with no scope justification in the PR body → surface it before spawning the deep review; a review that large is a review nobody actually performed.
- A path returns P0/P1 → present and ask. Never auto-fix.
- A `chain.lenses` entry names an agent that does not resolve → say so in the output before the batch;
  never let the lens drop out silently.
- `receiving-code-review` classifies a comment as **clarify** → surface the question before deciding.
- `graphGuardrails.maxRepatch` failed fix attempts on the same file (`--fix` mode) → escalate to `/debug recover`.

---

## 0. Pre-flight

```typescript
Skill("superpowers:using-superpowers");
Skill("superpowers:requesting-code-review");
```

Resolve the config (`${CLAUDE_PLUGIN_ROOT}/references/shared/000-config-loader.md`). Confirm the working tree state, the branch, the diff
base, and — for a PR — `gh` auth and PR metadata.

**Only when `full` mode is requested**, additionally load, in full: `${CLAUDE_PLUGIN_ROOT}/references/safety-floor.md`,
`${CLAUDE_PLUGIN_ROOT}/skills/debugger/references/structural-quality.md`,
`${CLAUDE_PLUGIN_ROOT}/skills/debugger/references/anti-patterns.md`, and the nearest `AGENTS.md`
for every touched path. `full` overrides `--quick` and `--no-debug`.

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

Invoke `Skill("superpowers:dispatching-parallel-agents")`, then dispatch **every applicable track in
one message**, each `run_in_background: true`. Until 1.7.0 this section was titled "(parallel)" and
said "dispatch in one message" while naming no agent to dispatch — four prose headings and no
`subagent_type` anywhere. The table below is the dispatch.

**Read-only by frontmatter, never by instruction.** Every agent here resolves with
`disallowedTools: Write, Edit` or an allowlist without them. A prompt saying "do not fix" is a
request; the incident behind that rule is in
`${CLAUDE_PLUGIN_ROOT}/skills/debugger/references/anti-patterns.md`.

| # | Agent | The question it asks | Fires when |
|---|---|---|---|
| 3A | `graph-powers:evaluator` | is it correct, and does it hold structurally | always |
| 3B | `graph-powers:security-reviewer` | is it exploitable — tenant, personal data, authorization, secrets | sensitive surface touched, or `full` |
| 3C | `graph-powers:explorer` | did this regress a hot path — N+1, `select *`, missing FK index, bundle growth | `api`, `schema` or `web` touched |
| 3D | `graph-powers:ui-ux-designer` | tokens, states, keyboard, contrast, smallest viewport | `web` touched |
| 3E | `code-review:code-review` | the bundled skill's own lens | when the plugin is installed |
| 3F | `/debug audit pr` | code quality, dependencies, technical debt on changed files | not `--quick`, not `--no-debug` |

3C and 3D are new, and they are not inventions: `graph-powers:ultra-verify` has run
`performance-regression` and `design-tokens-a11y` as built-in lenses all along. A review command
missing two lenses its sibling workflow already had was the gap, not the addition.

3C asks the performance question through `graph-powers:explorer` rather than through
`graph-powers:performance-optimizer`, and the reason is the rule three lines above: that specialist
resolves with `Write` and `Edit` and no `disallowedTools`. It is the right agent to *fix* a hot path
and the wrong one to *review* it. The question it is asked here is a pattern hunt over a diff, which
is what the explorer is for.

**The project extends this table.** `chain.lenses` in the config is a first-class contract — each
entry a `name`, its own binding `checks`, an optional `agent` and a `when` — and the schema states
the principle it exists for: *each lens is a distinct question; identical skeptics agree with each
other and miss the same things*. Honour every lens whose `when` matches the touched surfaces. A lens
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

Each track is blind to the others by construction, and where it cannot be — 3E is a `Skill()` and 3F
a slash command, both running in this thread — say so rather than claiming an isolation that is not
there.

### 3F narrows

`/debug audit pr` covers code quality, dependencies and technical debt on changed files only. It
writes `docs/AUDIT-REPORT-<YYYY-MM-DD>.md`; see the Iron Law note about what "read-only" means here.

## 4. Consolidate

```typescript
Skill("superpowers:receiving-code-review");
```

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
| performance-optimizer (3C) | PASS / FINDINGS / SKIPPED (surface untouched) | <n> |
| ui-ux-designer (3D) | PASS / FINDINGS / SKIPPED (surface untouched) | <n> |
| code-review skill (3E) | PASS / FINDINGS / UNAVAILABLE | <n> |
| /debug audit pr (3F) | PASS / FINDINGS / SKIPPED | <n> |
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

1. List the `implement` items, P0 first.
2. One item at a time, foreground `graph-powers:debugger`: failing test first, then the fix.
3. Gates from `tooling.commands` between items — not once at the end.
4. Stop after `graphGuardrails.maxRepatch` failed attempts on the same file → `/debug recover`.
   Read the number from the config; do not hardcode one. This line said "three" while the schema
   default is 2 and `/verify` reads the key — three sibling artefacts, two ceilings.
5. Re-run the affected review path on the result. A fix nobody re-reviewed is an untested claim.

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
| 3C performance-optimizer | if surface touched | yes | skip | if surface touched | yes |
| 3D ui-ux-designer | if `web` touched | yes | skip | if `web` touched | yes |
| 3E code-review skill | yes | yes | skip | yes | yes |
| 3F /debug audit pr | yes (skip on `--no-debug`) | yes (`--no-debug` overridden) | skip | limited | yes |
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
