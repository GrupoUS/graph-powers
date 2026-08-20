# Intent routing for Graph Powers — implementation plan

**Date:** 2026-08-20 · **Branch:** `feat/graph-engineering-upgrade` · **Baseline:** `f710184`
**Complexity:** L4 · **Risk surface:** none of `auth|payment|PII|schema|env|ci` — `hooks/` is touched in
the last task only, behind its own gate.

## Destination

Done when a plain sentence — no slash — routes to the right artefact: a defect report reaches
`/graph-powers:debug` with the `debugger` agent, an interface complaint reaches
`/graph-powers:design` with `uxmaster` and `ui-ux-designer`, and the trigger matrix below scores
≥80% should-trigger / ≤10% false-trigger, with the plugin's share of the skill listing no larger
than the 10,752 characters it occupies today.

## The diagnosis this plan acts on

Measured on Claude Code 2.1.237, plugin 1.3.1, 2026-08-20:

| Finding | Evidence |
|---|---|
| Commands are already model-invocable — the "migrate to skills" premise was false | docs/skills § "Custom commands have been merged into skills"; all 12 commands appear in this session's model-visible listing |
| The listing is overflowing **now** | `graph-powers:skill-improve`, `:uxmaster`, `:webapp-testing` appear name-only, descriptions dropped; the other nine keep theirs |
| The plugin is the largest single contributor | 10,752 of 23,902 local characters — 45% |
| Nothing is misconfigured | zero `disable-model-invocation`, zero malformed frontmatter, 24/24 parse |
| Nothing is written for triggering | zero `when_to_use`, zero `paths`, zero `context: fork`, zero per-skill `model` |

So the defect is not wiring and not flags. It is that 24 descriptions are written as documentation —
explaining what an artefact *is* — while the listing entry is the only thing the model matches a
sentence against. And they are written long, which is what pushes the least-used entries out.

## Architecture — commands and skills carry different loads

Kept separate by decision, and that separation is what the rewrite exploits:

| Surface | What its description is for | Budget posture |
|---|---|---|
| `commands/*.md` — 11 | **The intent surface.** What a person says when they want this to happen. Carries trigger phrases and a "Do not use for…" clause | spend here |
| `skills/*/SKILL.md` — 12 | **The knowledge surface.** Loaded by a command that already decided, or by the model once it is working in that domain. Rarely the thing a sentence names | recover here |

`paths:` is ignored inside a command file, so command precision comes from wording alone; the 12
skills keep `paths:` available.

## Trigger matrix — the baseline, written before any edit

Scoring: **T** = must trigger · **N** = must not trigger (near-miss sharing vocabulary).
English is the artefact language; the PT-BR block at the end is the real-world check, since that is
what actually gets typed.

### `/graph-powers:debug`
| # | Prompt | Expect |
|---|---|---|
| T1 | the checkout page throws a 500 and I can't reproduce it locally | debug |
| T2 | this test has been failing since yesterday, figure out why | debug |
| T3 | something broke after the last deploy | debug |
| N1 | add a retry to the checkout request | implement, not debug |
| N2 | review my error handling for quality | pr-review, not debug |

### `/graph-powers:design`
| # | Prompt | Expect |
|---|---|---|
| T1 | this screen looks cramped, fix the spacing | design |
| T2 | I want to improve the design of the dashboard | design |
| T3 | the empty state is ugly, make it better | design |
| N1 | the button click handler does nothing | debug, not design |
| N2 | the page takes 4s to render | perf, not design |

### `/graph-powers:plan`
| # | Prompt | Expect |
|---|---|---|
| T1 | how should we build multi-tenant billing? | plan |
| T2 | write me an implementation plan for the import feature | plan |
| T3 | I want to think through the approach before coding | plan |
| N1 | execute the plan in docs/plans | implement, not plan |
| N2 | rename this variable everywhere | direct edit, no command |

### `/graph-powers:implement`
| # | Prompt | Expect |
|---|---|---|
| T1 | execute the approved plan | implement |
| T2 | build sprint 2 of the plan | implement |
| T3 | PLEASE IMPLEMENT THIS PLAN | implement |
| N1 | plan the next sprint | plan, not implement |
| N2 | did the implementation actually work? | verify, not implement |

### `/graph-powers:verify`
| # | Prompt | Expect |
|---|---|---|
| T1 | check that everything still passes before I hand this off | verify |
| T2 | run the gates | verify |
| T3 | is this actually done? | verify |
| N1 | review this pull request | pr-review, not verify |
| N2 | the type-check is failing | debug, not verify |

### `/graph-powers:pr-review`
| # | Prompt | Expect |
|---|---|---|
| T1 | review PR 214 | pr-review |
| T2 | review my branch before I open the PR | pr-review |
| T3 | what would a reviewer say about this diff? | pr-review |
| N1 | fix the findings from the review | implement, not pr-review |
| N2 | prove the tests pass | verify, not pr-review |

### `/graph-powers:perf`
| # | Prompt | Expect |
|---|---|---|
| T1 | the dashboard takes 6 seconds to load | perf |
| T2 | our bundle is too big | perf |
| T3 | check the Core Web Vitals on staging | perf |
| N1 | the dashboard renders the wrong number | debug, not perf |
| N2 | the dashboard layout is off on mobile | design, not perf |

### `/graph-powers:research`
| # | Prompt | Expect |
|---|---|---|
| T1 | find out how this codebase handles auth before we change it | research |
| T2 | what does the Stripe API support for partial refunds? | research |
| T3 | investigate, don't change anything yet | research |
| N1 | fix the auth bug | debug, not research |
| N2 | plan the auth migration | plan, not research |

### `/graph-powers:prime`
| # | Prompt | Expect |
|---|---|---|
| T1 | load the project context | prime |
| T2 | get up to speed on this repo | prime |
| T3 | what are the conventions here? | prime |
| N1 | where is the login handler? | research, not prime |
| N2 | document the conventions | direct edit, no command |

### Recovery triggers — now `/debug recover`

> The standalone `/graph-powers:recover` command was removed in 1.7.0: it was a second entry point
> into the same `references/recovery-protocol.md` that `/debug recover` already opens. These
> triggers moved into the `/debug` description; the expectations below did not change.

| # | Prompt | Expect |
|---|---|---|
| T1 | we've tried three fixes and it's still broken | debug (recover mode) |
| T2 | back out and start over, this isn't working | debug (recover mode) |
| T3 | stop, we're going in circles | debug (recover mode) |
| N1 | this is broken (first report) | debug, default mode |
| N2 | revert the last commit | direct git, no command |

### `/graph-powers:evolve`
| # | Prompt | Expect |
|---|---|---|
| T1 | capture what we learned from this bug | evolve |
| T2 | make sure we don't hit this again | evolve |
| T3 | update the rules with this convention | evolve |
| N1 | remember that I prefer tabs | memory, not evolve |
| N2 | write the plan down | plan, not evolve |

### `/graph-powers:delegate`
| # | Prompt | Expect |
|---|---|---|
| T1 | hand this off to a specialist agent | delegate |
| T2 | delegate the frontend part | delegate |
| T3 | spawn an agent for this | delegate |
| N1 | do it yourself | no command |
| N2 | run these three things in parallel | the execution floor decides the fan-out, not delegate |

### Skills — knowledge surface (2 each; these fire mid-work, not from a cold sentence)
| Skill | T | N |
|---|---|---|
| `debugger` | model is already inside a failure investigation | a feature request |
| `planning` | model is already decomposing a multi-layer feature | a one-line fix |
| `performance-optimization` | model is reading a slow query or a bundle report | a visual bug |
| `uxmaster` | model is deciding UX direction or conversion copy | a runtime error |
| `webapp-testing` | model needs real-browser evidence | a unit test |
| `astro` | model is editing `.astro` or `astro.config.mjs` | a React file |
| `skill-improve` | model is authoring one skill, or asking whether `.claude/` is wired correctly | designing one agent's prompt |
| `senior-architect` | model is weighing an architecture trade-off | writing a component |
| `senior-prompt-engineer` | model is authoring an agent prompt or handoff schema | ordinary refactor |
| `second-opinion` | a fix keeps not sticking and needs an uninherited verdict | routine review |

### PT-BR reality check (typed, not translated)
| # | Prompt | Expect |
|---|---|---|
| P1 | preciso de um debug | debug |
| P2 | está dando erro no financeiro | debug |
| P3 | quero aprimorar meu design | design |
| P4 | a tela está feia | design |
| P5 | monta um plano pra isso | plan |
| P6 | implementa o plano | implement |
| P7 | roda os gates | verify |
| P8 | está lento demais | perf |
| N-P1 | melhora isso aí | nothing — too vague to route |

## Reuse ledger

| # | Need | Existing asset | Verdict | Justification |
|---|---|---|---|---|
| N1 | Auto-invocable debug | `commands/debug.md`, `skills/debugger/`, `agents/debugger.md` | EXTEND | already invocable; description is the gap |
| N2 | Auto-invocable design | `commands/design.md`, `skills/uxmaster/`, `agents/ui-ux-designer.md` | EXTEND | same; `design-improve`/`design-reviewer` are not created |
| N3 | Agent auto-delegation | `agents/*.md` ×12 | EXTEND | rewrite `description` as a routing rule |
| N4 | Listing budget gate | `.github/check_context_budget.py` | EXTEND | measures command cost; add the listing sum |
| N5 | Budget setting for installers | `AGENT_SETUP.md` | EXTEND | plugin cannot ship `skillListingBudgetFraction` — only `agent` and `subagentStatusLine` are honoured from a plugin `settings.json` |
| N6 | Intent router | `.claude-plugin/plugin.json` hooks, `hooks/_config.py` | EXTEND | deferred to TASK-10, behind its own gate |

## Regression watchlist

| # | Behaviour that must still work | Proof | Phase |
|---|---|---|---|
| W1 | All 24 `/graph-powers:*` invocations still resolve | `claude plugin validate .` | Sprint 2 |
| W2 | Every cited agent, skill and section resolves | `python3 .github/check_wiring.py` | Sprint 2 |
| W3 | Command context cost has not regressed | `python3 .github/check_context_budget.py --compare` | Sprint 2 |
| W4 | Guardrails still pass their negative tests | `python3 hooks/test_hooks.py` | Sprint 2 |
| W5 | Nothing POSIX-only entered what an agent executes | `python3 .github/check_portability.py` | Sprint 2 |
| W6 | No home directory reached a tracked file | `python3 .github/check_machine_paths.py` | Sprint 2 |
| W7 | Codex side still generates from the same artefacts | `python3 .github/check_codex.py` · `node bin/graph-powers.mjs --help` | Sprint 2 |
| W8 | `evaluator` keeps no `Agent` tool — the one unbraked cycle stays braked | frontmatter inspection after the agent rewrite | Sprint 3 |
| W9 | Every JSON in the tree still parses | the JSON gate from `AGENTS.md § Gates` | Sprint 2 |

## Rollback

`git revert` per task; every change is a text edit in a tracked file. The hook task, when it runs,
additionally needs its entry removed from `.claude-plugin/plugin.json` followed by `/reload-plugins`.
Nothing here is forward-only: no schema, no migration, no outward-facing write.

## Not yet specified

- The exact character budget the runtime applies. `/doctor` reports overflow; it does not print the
  ceiling. The plan therefore targets "no larger than today" rather than a number.
- Whether `paths:` is honoured inside a plugin skill. The frontmatter reference says every field
  applies at every level including plugins; no live test exists. Applied to one skill first.
- Which intents are highest-frequency for the router. Needs usage data, not a guess — TASK-10 is
  gated partly on that.

## Out of scope

- `~/.claude/` and the neondash `.claude/` — *reopens if:* the router's home is changed.
- Creating `design-improve` or `design-reviewer` — *reopens if:* the matrix shows `design` and
  `uxmaster` cannibalising each other.
- Any new `disable-model-invocation` — *reopens if:* a deploy or migration skill enters the plugin.
- Changing `skillListingBudgetFraction` from inside the plugin — impossible; it is documentation.

## Execution graph

```
TASK-04 ──→ TASK-06 ──→ TASK-07 ──→ [TASK-09 ‖ TASK-13] ──→ TASK-08 ──→ ⟨GATE⟩ ──→ TASK-10
                 │
                 └──→ TASK-11 (read-only audit, no writer)
```

| Edge | What the destination reads | Verdict |
|---|---|---|
| 04 → 06 | the trigger phrases the descriptions must contain | REAL |
| 06 → 07 | the final descriptions the frontmatter fields sit beside | REAL |
| 07 → 09 | the measured total, to document the setting against | REAL |
| 06 → 13 | the post-rewrite total, to set the gate's ceiling | REAL |
| 06 → 08 | the vocabulary, so agent and skill descriptions do not collide | REAL |
| 09 ↔ 13 | nothing — docs and a gate script share no file | **FALSE — parallel** |
| 11 → anything | nothing — read-only confirmation | **FALSE — independent** |

**Fan-out justification:** `[TASK-09 ‖ TASK-13]` own `AGENT_SETUP.md` and
`.github/check_context_budget.py` — disjoint, neither reads the other. Everything upstream of them is
one chain over the same 24 frontmatter blocks under one shared character ceiling; splitting it would
hand each writer its own vocabulary and leave the ceiling unowned. One owner, sequential.
**Merge owner:** the main session. No verification node writes.

## Tasks

- [x] **TASK-04** — trigger matrix (this document, above)
- [x] **TASK-06** — rewrite 24 descriptions; ceiling <= 10,752 chars total — **done: 9,331, 1,421 under**
- [x] **TASK-07** — `paths` on `astro` only, as the single live test of the plugin-skill claim. `context: fork`, `agent`, `model` and `effort` **deliberately not applied** — they change runtime behaviour for every existing install and buy nothing for triggering, which is the destination
- [x] **TASK-11** — `disable-model-invocation` confirmed at zero; nothing to remove
- [x] **TASK-13** — `.github/check_listing_budget.py`, registered in `AGENTS.md` and CI
- [x] **TASK-09** — `skillListingBudgetFraction` documented in `AGENT_SETUP.md` Step 8
- [x] **TASK-08** — agent descriptions as routing rules; W8 verified
- [ ] **TASK-10** — `UserPromptSubmit` router — **gated, not in this run**
- [x] **TASK-14** — version bumped to 1.4.0 in both manifests; changelog written
- [x] **TASK-15** (unplanned, requested mid-run) — user-scope config layer in `hooks/_config.py`, six negative tests, test suite made hermetic

## Governance

- Sprint 1 (TASK-04) · Rollback: delete this file · Risk: none · Approval: implicit, it is the baseline.
- Sprint 2 (06, 07, 11, 13, 09) · Rollback: `git revert` per task · Risk: description too aggressive →
  false triggers; budget regression · Approval: gates W1-W7, W9 green.
- Sprint 3a (08) · Rollback: `git revert` · Risk: agent delegation fires too eagerly · Approval: W8 green.
- Sprint 3b (10) · Rollback: remove hook entry + `/reload-plugins` · Risk: latency on every turn;
  fail-open violation · Approval: **isolated human gate. Not in this run.**
- No commit, no push, without an explicit request in the turn that makes it (`AGENTS.md § Git`).
