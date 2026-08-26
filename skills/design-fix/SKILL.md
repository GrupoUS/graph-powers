---
name: design-fix
description: "Use when repairing an implemented UI in place while preserving behavior and visual direction. Trigger on design fix, production readiness, responsive or accessibility cleanup, missing loading, empty or error states, token or spacing drift. Not for new surfaces or identities (designer), broken behavior (/debug), or speed (/perf)."
user-invocable: true
argument-hint: "[target]"
---

# Design Fix

## Overview

Repair an existing interface against evidence, not taste. Establish what already works, classify the
scope, lock the smallest coherent change, then compare the result with the same baseline used to
justify it.

`/design fix` is the controller that loads this skill. This skill owns the baseline, the
surgical/structural decision and the repair contract. `designer` owns visual direction and the craft
pass definitions; duplicating either here would create two authorities.

## Territory

Use it when the target already exists and the request is to make it production-ready without
changing its product contract:

- spacing, hierarchy, typography, token or surface drift;
- responsive, keyboard, focus, contrast or reduced-motion defects;
- missing loading, empty, error, success, disabled or permission states;
- fragile real-content behavior such as overflow, long translations, large collections or touch;
- an existing workflow whose information hierarchy may need repair.

Route elsewhere when the real task differs:

- A new surface, identity or intentionally new visual world starts with `designer`.
- A request for bolder, more expressive or less generic art direction is `/design improve`.
- A control that behaves incorrectly is `/debug`, even if the symptom is visual.
- A speed-only or Core Web Vitals problem is `/perf`.
- A landing or marketing page also loads `landing-page-design`; its visual values remain subordinate
  to the host project's authority.

## Authority order

Resolve conflicts in this order:

1. the user's explicit brief and locked decision;
2. the host project's `DESIGN.md`, design rule, semantic tokens and incumbent components;
3. behavior proven by routes, tests, copy and data contracts;
4. the diagnostic heuristics in this skill and `designer`.

**[HARD] Never import a preferred font, colour, radius, spacing value, icon set, motion curve or
component pattern from this skill.** A reusable repair method cannot know the host's visual system.
If a required role has no token or established pattern, name the gap and ask which authority should
change.

Preserve the stack and working behavior. Check dependencies before proposing a new one; a design
repair is not permission to migrate a framework, replace a styling system or invent a capability.

## Repair protocol

### 1. Resolve and freeze the scope

Turn the target into a sorted file manifest. Read the relevant design authority, token source,
routes, tests, neighboring components and current implementation. If the scope resolves to no files
or crosses a boundary the brief did not authorize, stop and ask one focused question.

State the behavior that must remain unchanged. Mark unsupported inferences `[ASSUMED]`; ask only
when an unknown would alter the primary action, task order, permissions, data shown or layout class.

### 2. Capture the baseline before editing

Capture the current interface at every viewport the project ships and exercise keyboard plus the
reachable states. When a browser is unavailable, label the baseline `CODE-ONLY`; do not report
visual measurements as observed.

Read `${CLAUDE_PLUGIN_ROOT}/skills/designer/references/craft-floor.md` for the audit criteria. Do not
copy its checks here. Record:

- scope manifest, brief, evidence paths and confidence;
- user, primary task, primary action and expected observable result;
- behavior and strengths that must be preserved;
- loading, empty, populated, error and relevant interaction/permission states;
- Critical, High and Medium findings, plus one highest-leverage repair;
- measured values where evidence exists and clearly labelled hypotheses where it does not.

Every finding names a file or render, the observed defect, user impact and smallest coherent fix.
"Looks better" is not evidence.

### 3. Classify before choosing direction

Classify as **SURGICAL** only when every condition holds:

- one component, interaction or state contains the change;
- the happy path, navigation, information architecture and primary task order remain intact;
- page composition, critical-action hierarchy and coordinated component behavior remain intact.

Anything else is **STRUCTURAL**. Mixed or uncertain scope defaults to structural because silently
changing a workflow is riskier than asking for a decision.

### 4. Lock the repair contract

For a surgical repair, write one compact contract and continue under the user's original
authorization. Do not manufacture three layouts. The contract states the smallest change, preserved
strengths and behavior, affected task/action, states, desktop/mobile behavior, non-goals, acceptance
evidence and metric hypothesis.

For a structural repair, load `Skill("designer")`. Its three directions must differ in kind, use
only existing or requested capabilities, and expose task-flow and visual trade-offs. Present the
comparison and wait for the user to select a direction or hybrid. **[HARD] No write-capable work
starts before that selection is locked.**

### 5. Apply the bounded repair

Follow the `fix` routing in `${CLAUDE_PLUGIN_ROOT}/commands/design.md`; it is the single source for
pass order. The worker for each pass reads only its entry in
`${CLAUDE_PLUGIN_ROOT}/skills/designer/references/craft-passes.md`, then the craft floor immediately
before editing. A pass with no baseline finding is skipped with evidence, not run ceremonially.

Each pass stays inside the manifest and traces `finding or locked criterion -> change -> evidence`.
Batch the coherent fixes, inspect the completed surface once across supported widths, repair that
inspection as one batch, allow one confirming look, then stop. Toolchain drift found during a design
pass is reported, not repaired as a side effect.

### 6. Prove the delta

Run the host project's declared gates, not a familiar substitute. Re-capture the same widths and
states as the baseline, then report:

- resolved, accepted and newly introduced findings;
- behavior, task/action hierarchy and states preserved;
- files changed and any deferred out-of-scope work;
- gate commands with current-session exit codes;
- observed results separately from hypotheses that still need user testing.

No completion claim without both the project gates and the baseline-to-result comparison.

## Output contract

```text
DESIGN FIX — SURGICAL | STRUCTURAL
Scope       manifest + evidence paths
Preserve    behavior, strengths, tokens and non-goals
Baseline    task/action + states + prioritised findings + One Big Win
Decision    compact repair contract | user-locked designer direction
Repair      finding/criterion -> change -> evidence
Verification gates + before/after renders + residual findings
Hypotheses  unmeasured usability outcomes and the test that would measure them
```

## Red flags and rationalisations

Stop before editing when any red flag appears:

- no frozen scope or baseline;
- a structural direction was auto-selected;
- a visual value came from this skill instead of project authority;
- behavior, roles, data, permissions or states were invented;
- a pass edits outside its manifest or repairs toolchain drift;
- improvement is claimed without matched before/after evidence and gates.

| Shortcut | Reality |
|---|---|
| "It is only cosmetic" | Focus, overflow, states and responsive changes can break the task even when the data layer is untouched. |
| "Use a trendy palette now; tokens later" | That replaces the project's authority and turns cleanup into an identity change. |
| "Three options look more professional" | On a surgical fix they are false deliberation; spend that effort proving the one bounded repair. |
| "The lead approved it, so skip the baseline" | Approval chooses intent. A baseline proves scope and prevents regressions. |
| "We will compare after shipping" | Without the same before evidence, the comparison cannot distinguish repair from preference. |

## Resources

- `${CLAUDE_PLUGIN_ROOT}/commands/design.md` — controller and the one home for pass routing.
- `${CLAUDE_PLUGIN_ROOT}/skills/designer/SKILL.md` — structural direction contract.
- `${CLAUDE_PLUGIN_ROOT}/skills/designer/references/craft-passes.md` — pass definitions.
- `${CLAUDE_PLUGIN_ROOT}/skills/designer/references/craft-floor.md` — audit and ship floor.
- `evals/evals.json` — positive, boundary-negative and pressure cases for this skill.
- `learning.md` — measured iteration history; read before changing this skill.
