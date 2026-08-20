---
description: Unified PR/branch review. Runs independent review paths in parallel — an adversarial evaluator, a security reviewer, the bundled code-review skill, and /debug audit pr — consolidates them with superpowers:receiving-code-review, and produces a verdict plus a ready-to-post comment body. Read-only by default; never approves or merges. Modes (positional) — <PR#> · --current · --branch <name> · full. Flags — --quick, --fix, --no-debug.
workflow_type: prompt-chaining
---

# /pr-review — Unified PR Review

**ARGUMENTS**: $ARGUMENTS

> **Read before step 0 — never reconstruct these from memory:** `${CLAUDE_PLUGIN_ROOT}/references/shared/000-config-loader.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/005-superpowers-bootstrap.md`
> Read `${CLAUDE_PLUGIN_ROOT}/references/shared/070-parallel-agent-spawn.md`

```
gh pr checkout <PR#>
/pr-review <PR#>              # full path
/pr-review --current          # already on the PR branch
/pr-review --branch <name>    # local branch review, no PR open
/pr-review <PR#> --quick      # skip the deep paths (§ 3C, § 3D, § 4)
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

This command is read-only by default. It mutates only under an explicit `--fix`, and then only
through a foreground `debugger` agent with gates between fixes.

---

## Stopping conditions

- Phase 0 finds a branch mismatch (PR head ≠ current branch) → ask for `gh pr checkout`; never run it silently.
- `gh auth status` fails → tell the user; never attempt `gh auth login`.
- Any field of the § 2 review bundle fails to resolve (base SHA, head SHA, description, focus) → stop. Dispatching an agent with an unresolved placeholder is the anti-pattern this bundle exists to prevent.
- The diff exceeds 1000 lines with no scope justification in the PR body → surface it before spawning the deep review; a review that large is a review nobody actually performed.
- A path returns P0/P1 → present and ask. Never auto-fix.
- `receiving-code-review` classifies a comment as **clarify** → surface the question before deciding.
- Three failed fix attempts on the same file (`--fix` mode) → escalate to `/debug recover`.

---

## 0. Pre-flight

```typescript
Skill("superpowers:using-superpowers");
Skill("superpowers:requesting-code-review");
```

Resolve the config (`${CLAUDE_PLUGIN_ROOT}/references/shared/000-config-loader.md`). Confirm the working tree state, the branch, the diff
base, and — for a PR — `gh` auth and PR metadata.

**`full` mode** additionally loads, in full: `${CLAUDE_PLUGIN_ROOT}/references/safety-floor.md`,
`${CLAUDE_PLUGIN_ROOT}/skills/debugger/references/structural-quality.md`,
`${CLAUDE_PLUGIN_ROOT}/skills/debugger/references/anti-patterns.md`, and the nearest `AGENTS.md`
for every touched path. `full` overrides `--quick` and `--no-debug`.

---

## 1. Scope and risk signals

Collect, from the diff alone — no memory, no assumption:

| Signal | How |
|---|---|
| Files touched, by layer | diff paths mapped onto `paths.*` |
| Total added/removed lines | `git diff --shortstat <base>...HEAD` |
| Any file crossing 1000 lines | `git diff --numstat` plus current file length |
| Sensitive surfaces touched | auth, payment, personal data, schema, environment, CI |
| Declared gates that changed | anything under the CI config or the scripts the gates call |

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

Dispatch in one message. Each path is blind to the others — that is the point; agreement between
independent paths is evidence, agreement inside one path is not.

### 3A. `evaluator` — adversarial review (foreground)

Mode: PR/branch review. Read-only by construction (`disallowedTools: Write, Edit`). Applies the
structural lens from `${CLAUDE_PLUGIN_ROOT}/skills/debugger/references/structural-quality.md`:
size crossings, spaghetti growth, incidental complexity preserved, wrapper/cast churn, layer leaks,
near-duplicates of an existing helper.

### 3B. `security-reviewer` — exploitability (background)

Finder mode over the diff. Report-only. Cross-tenant access, personal-data exposure, injection,
authorization gaps, secrets, weakened production defaults.

Skipped in `--quick` **only** when § 1 found no sensitive surface. A security path skipped over a
diff that touches auth is a skipped path, not a fast one — say which happened.

### 3C. `code-review:code-review` — the bundled skill (best-effort)

Runs when available. Skipped silently is not acceptable: if it is unavailable, the output says so.

### 3D. `/debug audit pr` (skipped in `--quick` or `--no-debug`)

Narrowed to code quality, dependencies and technical debt on changed files only.

---

## 4. Consolidate

```typescript
Skill("superpowers:receiving-code-review");
```

1. **Collect** every path's findings into one table, de-duplicated by `file:line` + defect.
2. **Merge** with the PR's existing human comments — an unanswered reviewer comment is a finding.
3. **Classify each item**: `implement` (real, fix it), `clarify` (needs the author or the user),
   `pushback` (technically wrong, with the reason).

A finding two independent paths raised is promoted one severity level. A finding only one path
raised and the others explicitly checked is demoted.

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
| code-review skill (3C) | PASS / FINDINGS / UNAVAILABLE | <n> |
| /debug audit pr (3D) | PASS / FINDINGS / SKIPPED | <n> |
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
2. One item at a time, foreground `debugger`: failing test first, then the fix.
3. Gates from `tooling.commands` between items — not once at the end.
4. Stop after three failed attempts on the same file → `/debug recover`.
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
| 3C code-review skill | yes | yes | skip | yes | yes |
| 3D /debug audit pr | yes (skip on `--no-debug`) | yes (`--no-debug` overridden) | skip | limited | yes |
| 4 consolidate | yes | yes | yes | yes (no PR comments) | yes |
| 5 output | yes | yes | yes | yes | yes |
| 6 fix loop | no | no | no | no | **yes** |

---

## 8. Output guarantees

- Never states APPROVE without 3A having run and passed.
- Never hides drift: a sensitive surface in the diff appears in the output regardless of the verdict.
- Never reports a skipped path as a passed path.
- Every severity in the table traces to a `file:line` someone opened.
