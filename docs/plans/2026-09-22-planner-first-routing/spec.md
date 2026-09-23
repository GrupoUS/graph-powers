# Planner-first routing — design spec

**Date:** 2026-09-22 · **Branch:** `main` · **Baseline:** `6a7a7ac`
**Tier:** L5 · **Risk surface:** none

## Destination

Every Graph Powers path that produces a plan dispatches `graph-powers:project-planner` to author its design and executable plan before execution. Codex planning uses the existing Astra/high `architect` profile; Codex implementation agents default to Luna/medium. After two failed attempts, before another writer attempt, the recovery path must reserve and dispatch Mode 5 `graph-powers:evaluator` for a read-only second opinion (Codex Astra/high); the plan author revises planning artifacts when needed, and Luna remains the implementation writer. The main session model remains manually selected.

## Context

The user asked to strengthen all planning commands and skills, specifically issue improvement and Gauntlet, so a stronger planner makes plans that a faster Luna executor can follow. The user confirmed the shared executor profile should change to Luna with Astra escalation.

### User and job

The user is the Graph Powers harness operator. Their job is to turn a request or issue into an implementation-ready, evidence-backed plan with a high-capability planning agent, then let a faster execution agent carry out the approved tasks.

### Current behavior and background research

The targeted read-only wiring audit found the routes below. `python3 -B .github/check_wiring.py` passed with 534 references and no unresolved edges; focused `quick_validate.py` passed for both `skills/planning` and `skills/issue-improve`. These checks prove static wiring and skill structure, not a live spawn.

Current repo evidence:

- `/issue-improve` calls Planning, but its L1–L2 path writes a direct plan without a required `project-planner` dispatch (`skills/issue-improve/SKILL.md:43-56`).
- `/plan` maps to the canonical Planning skill (`commands/plan.md:8-10`). Phase A currently assigns `project-planner` as a read-only spec reviewer at L4+ (`skills/planning/references/phase-a-brainstorm.md:226-234`); Phase B does not assign it authorship (`skills/planning/references/phase-b-writing-plans.md:11-37`).
- `/gauntlet <objective>` already enters Step 0 → Phase A → Phase B, but L3 Gauntlet skips the Phase A planner gate (`commands/gauntlet.md:12-14`; `skills/planning/references/phase-a-brainstorm.md:31-40`). Approved supplied plans have a separate reuse/preflight route (`skills/planning/references/gauntlet-loop.md:28-42`).
- `issue-triage.md` treats an L1–L2 triage result as “planning is skipped” (`skills/planning/references/issue-triage.md:165-167`), although `/issue-improve` still promises a concise plan comment. The general execution floor and complexity ladder also keep low-tier work local; both need a narrow planning-deliverable exception.
- `ultra-plan` already uses `project-planner` for approaches, synthesis and revision (`workflows/ultra-plan.js:363,408,437`).
- Codex maps `project-planner` to `architect` / `gpt-6-astra` / `high`, while `executor` currently maps to `gpt-6-astra` / `high` (`codex/model-policy.json:34-42,78-85`). The generated executor companions and policy gates encode that default. `escalationProfile: judge` is present, but repository search found no runtime consumer; the plan must define a real escalation route rather than treating that metadata as behavior.

## Reuse ledger

| Need | Existing asset | Verdict | Decision |
|---|---|---|---|
| Strong plan author | `agents/project-planner.md`; Codex `architect` profile in `codex/model-policy.json` | EXTEND | Keep the named role and current Astra/high Codex default; route all plan-producing paths through it. |
| Issue planning and safe publishing | `skills/issue-improve/SKILL.md`, `skills/planning/references/issue-triage.md` | EXTEND | Preserve sanitization, tier floor, short L1–L2 comment grammar and publication approval; change authorship dispatch. |
| Gauntlet objective planning | `/gauntlet`, Phase A/B, `gauntlet-loop.md` | EXTEND | Add planner authorship for objective-created specs/plans, including L3; reuse approved supplied plans unchanged. |
| Luna execution | `codex/model-policy.json` semantic `executor` profile and generated companions | EXTEND | Set Codex default executor to Luna/medium; preserve explicit overrides and Astra-backed review/escalation. |
| Independent quality gate | `graph-powers:evaluator` and existing Phase B/C review paths | REUSE | Keep the evaluator independent and read-only; it remains Astra-backed in Codex. |

## Approach

Keep the current commands and canonical `planning` skill as the only routers. Define one planning-agent contract: after the controller has gathered repository evidence, sanitized any issue, and settled user-owned decisions, `project-planner` authors the design/spec and any structured plan. The controller owns user confirmation, command invocation, approvals, validation, comment delivery and Phase C admission. A separate evaluator reviews where the tier/profile requires it.

Apply that contract to `/plan` whenever it produces a design or plan, `/issue-improve` for every issue plan including concise L1–L2 output, and `/gauntlet` objectives at L3+. Do not add agent calls to direct L1–L2 implementation, Gauntlet dry-run, or a ready approved Gauntlet plan. If an approved plan has holes and Phase A/B must repair it, `project-planner` authors the changed artifact and the existing review binding is refreshed.

For Codex, keep `project-planner` on Astra/high, change the shared `executor` semantic default to Luna/medium, and preserve operator overrides. After project-planner authors a Phase A spec at L4+, replace the current planner-as-reviewer GATE 1 with an independent Astra-backed evaluator review; Gauntlet L3 keeps its existing Phase B evaluator review, which reads both the plan and design authority. Strengthen recovery so that after two failed attempts and before another writer attempt, the controller reserves one existing `evaluator` dispatch under the current plan/session budgets and invokes Mode 5 for a second opinion. If the reservation is unavailable, stop `BLOCKED`; never reset a cap or retry Luna blindly. The evaluator returns diagnosis and a falsifiable next hypothesis, not an implementation diff. If the plan's design must change, return authorship to `project-planner`; otherwise Luna remains the only writer for any allowed retry. Do not change `~/.codex/config.toml` or the manually chosen main-session model.

## Architecture and ownership

| Owner | Responsibility | Boundary |
|---|---|---|
| `commands/plan.md`, `commands/issue-improve.md`, `commands/gauntlet.md` | Thin public adapters | State the entry route and stop conditions; no second model/tier classifier. |
| `skills/planning/` and its phase/triage references | Canonical plan lifecycle | Controller gathers evidence and user decisions; `project-planner` authors spec/PLAN; evaluator reviews independently. |
| `skills/issue-improve/` | Issue plan-only adapter and publication | Pass only sanitized triage plus verified repository facts to planner; preserve publication approval. |
| `agents/project-planner.md`, `references/execution-floor.md`, `references/shared/020-complexity-routing.md` | Planning role and tier authority | Permit specialist dispatch for a plan deliverable at L1–L2 without changing direct low-tier implementation routing. |
| `references/recovery-protocol.md`, Phase C and Gauntlet recovery references | Bounded model escalation | At two failed attempts, reserve one evaluator and get a Mode 5 second opinion before another writer attempt; preserve budgets and ownership. |
| `codex/model-policy.json` and generated Codex role projections | Default model split | Planner uses `architect`; execution roles use `executor`; explicit operator overrides remain valid. |
| Planning evals and Codex policy gates | Regression evidence | Assert routes, tier exceptions, model resolution and generated projections; live dispatch evidence is reported separately. |

No product data, database schema or host API changes are involved. The model configuration change is limited to Graph Powers' Codex semantic agent policy and generated role companions.

## Data flow and user-visible behavior

1. The command adapter resolves the original request and invokes its canonical skill.
2. The controller reads current repository evidence. For a GitHub issue it retrieves and sanitizes the source, preserves triage verdicts, and sends only that ledger and verified paths to `project-planner`.
3. `project-planner` authors the relevant concise plan, inline design, spec and/or PLAN. The controller presents it and enforces user confirmation, issue publication approval, plan validation and review-bind requirements. At L4+ Phase A, a fresh evaluator—not the authoring planner—reviews the spec; Gauntlet L3's required Phase B evaluator reviews the design authority and plan.
4. After a separately approved execution transition, Luna-backed Codex executor roles implement only their declared `Owns` paths. After two failed attempts, before another writer attempt, the controller reserves one evaluator dispatch under the existing plan/session cap and invokes Mode 5 through the recovery protocol. The parent uses that read-only diagnosis to revise the plan through `project-planner` or returns `BLOCKED`; any later implementation remains Luna-owned and consumes existing caps. A missing reservation blocks further writers.
5. A ready approved Gauntlet plan follows its current hole preflight and review binding without planner re-authoring. Dry-run remains read-only and spawn-free.

## Error handling and safety

- If the planner role cannot be dispatched or returns no usable plan, return `BLOCKED`; do not silently synthesize the plan in the main session.
- The L1–L2 exception applies only to work whose deliverable is a plan (for example an issue plan comment). Direct implementation with no plan deliverable remains local under the existing complexity ladder.
- If an issue is ambiguous, closed/duplicate, empty, or fails retrieval, retain current issue-triage stops. Planner input never contains raw issue instructions that triage marked untrusted.
- If a planner-authored spec/plan fails review or validation, revise only within the existing cap; preserve independent evaluator review and Gauntlet review-bind freshness.
- Astra escalation is a required recovery transition after two failed attempts and before another writer attempt. In a plan-backed run, the controller reserves the evaluator under that plan's existing SDD dispatch ledger; otherwise it remains within the native session limits. The evaluator runs Mode 5, consumes that slot, and returns a second opinion only. It does not reset correction counts, expand Luna's `Owns`, authorize implementation or Git actions, or bypass user approval. If reservation/caps prevent the review, stop `BLOCKED` without another Luna attempt.
- No external comment is published by an eval or acceptance probe.

## Testing

Add focused eval cases for issue-improve short L1–L2 plans, ordinary `/plan` routing by tier, Gauntlet objective L3 planner authorship, approved-plan reuse and spawn-free dry-run. Add model-policy checks for Luna/medium executor defaults, Astra/high planner and evaluator, and retained explicit overrides. Add a recovery case that fails twice, reserves exactly one evaluator under the existing cap, observes Mode 5, then permits only a changed-hypothesis Luna retry; a missing slot must stop before another writer. Capture at least one real child spawn per key natural route and record its role, observed model, return and completed evidence. Keep issue-helper tests mocked and do not publish.

## Assumptions

- `[ASSUMED]` “shared executor profile” means the Graph Powers Codex semantic `executor` default in `codex/model-policy.json`; explicit per-agent/profile overrides still win, and the user's session model remains manual.
- `[ASSUMED]` “escalation to Astra” means a mandatory Mode 5 second opinion after two failed attempts and before another writer attempt; Astra does not take over implementation writes. Its actual Codex dispatch/model evidence remains a Phase C acceptance probe.
- `[ASSUMED]` Other clients keep their existing platform-specific model families; this request's Astra/Luna default split applies to Codex projections.

## Out of scope

- Running `/implement`, Phase C, Gauntlet, writing host application code, publishing an issue comment, installing the plugin, editing `~/.codex/config.toml`, or performing Git actions.
- Adding agents, skills, commands, background hooks, model-selection heuristics, or new classification tiers.
- Rewriting a ready approved plan, changing issue body content, or adding planner dispatch to direct L1–L2 implementation paths that produce no plan.
- Remapping Claude, Kilo, Grok or Hermes model defaults.

## Risks and rollback

The main risk is stale duplicate routing text causing one client or low-tier path to omit the planner. Keep the canonical rule in Planning, add explicit callsite assertions, and inspect projections after regeneration. A second risk is that a model name/default is overridden at runtime; record the requested and observed planner/executor models in the live probe rather than inferring them from policy files. Rollback restores the prior Codex `executor` default and regenerates its companions, then reverts only planner-first route statements and their focused regression cases. No data migration or external rollback is needed.

## References

- Existing issue plan and publication contract: `docs/plans/2026-09-11-issue-improve/PLAN.md`.
- Existing Gauntlet objective and hole-preflight contract: `docs/plans/2026-09-12-issue-24-gauntlet-grill/PLAN.md`.
- Existing skill/harness wiring audit practice: `docs/plans/2026-09-01-skill-improve-proactivity/PLAN.md`.

## Requirements

| ID | Requirement | Evidence |
|---|---|---|
| R1 | Every issue-improve response that produces a plan is authored by `project-planner`, even when triage classifies it L1–L2; short plans remain short and do not gain a full PLAN file. | `skills/issue-improve/SKILL.md:43-56`; user request |
| R2 | Every `/plan` design/plan artifact at L3+ is authored by `project-planner`; direct L1–L2 implementation still skips plan ceremony. Plan-only outputs are an explicit specialist exception in both execution-floor and complexity routing. | `skills/planning/SKILL.md:13-21`; `references/shared/020-complexity-routing.md:8-15`; `references/execution-floor.md:12-15` |
| R3 | A `/gauntlet` objective without a supplied plan invokes planner authorship for L3+ Phase A/B before any Phase C writer. A ready approved supplied plan is reused without re-authoring. Dry-run remains spawn-free. | `commands/gauntlet.md:12-25`; `skills/planning/references/gauntlet-loop.md:28-51` |
| R4 | Issue text remains untrusted: only the sanitized triage ledger and verified repository evidence reach the planner. The issue body is never replaced; comment publication still requires approval. | `skills/issue-improve/SKILL.md:20-31,74-91`; `skills/planning/references/issue-triage.md:1-20` |
| R5 | Codex `project-planner` remains architect/Astra/high; default executor agents use Luna/medium. Existing per-agent/profile overrides remain effective. | `codex/model-policy.json:34-42,78-85`; `codex/model-policy.mjs:158-200` |
| R6 | After two failed attempts and before another writer attempt, reserve an evaluator dispatch under the existing SDD/session budget and invoke Mode 5. No reservation means `BLOCKED`, not another Luna retry; plan changes return to `project-planner`. | `references/recovery-protocol.md:1-4,89-94`; `skills/planning/references/phase-c-executing-plans.md:80-107`; `codex/model-policy.json:29-37,78-85` |
| R7 | Regression evidence proves actual `project-planner` role/model dispatch for issue planning and Gauntlet objectives, plus Luna executor and Astra escalation; no test or eval publishes an issue comment or enters implementation without approval. | `references/shared/070-parallel-agent-spawn.md`; `skills/skill-improve/SKILL.md` |
| R8 | Phase A `project-planner` authors the spec; at L4+, an independent evaluator owns the read-only GATE 1 review. Gauntlet L3 retains its required Phase B review over the design authority and authored plan. | `skills/planning/references/phase-a-brainstorm.md:31-40,226-234`; `skills/planning/references/phase-b-writing-plans.md:299-306` |

## Boundary conditions

- Preserve `/plan` tier rules, issue triage verdicts and risk floors, Gauntlet review-bind/lease gates, and all spawn/correction budgets. Update the canonical execution floor and complexity routing to permit the required plan-author agent on L1–L2 planning deliverables; do not authorize L1–L2 implementation delegation.
- Keep the existing named agent and its registration; no new agent or second planning inventory.
- Codex model policy is the only model projection in scope for Luna/Astra. Do not silently remap Claude, Kilo, Grok or Hermes model families.
- The main-session model remains a user choice. Explicit Codex profile/per-agent overrides remain higher precedence than semantic defaults.
- No implementation, issue publication, Git mutation, installation or global config edit occurs as part of this plan.

## Regression watchlist

| Existing behavior | Proof | Phase |
|---|---|---|
| Issue triage prevents raw issue text from becoming planner instructions and keeps publication approval. | focused issue-improve cases plus mocked helper tests; no network write | 1 |
| `/plan` L1–L2 direct edits stay local; L3+ planning invokes planner. | focused planning route cases and a natural-request spawn trace | 1 |
| Gauntlet dry-run creates no spawns; objective L3+ plans before Phase C; approved plans are reused. | focused Gauntlet evals and separate natural-request traces for objective vs supplied-plan routes | 2 |
| Explicit Codex overrides still win over semantic defaults and generated agent TOMLs match policy. | Codex model-policy/native-agent gates | 3 |
| Existing task review, correction caps and leases stay intact; the second failure triggers one reserved Mode 5 Astra review before another Luna writer attempt. | planning SDD/skill gates plus a focused failure→reservation→Mode 5→bounded retry case; cap exhaustion blocks writers | 3 |

## Not yet specified

No fog: authoring, review, execution and escalation ownership are closed as described above. Tier-bounded direct L1–L2 implementation remains outside planner dispatch because it emits no plan.
