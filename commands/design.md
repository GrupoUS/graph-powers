---
description: "Create or improve UI layout, type, hierarchy, tokens, states, responsiveness or direction. Modes: new target, fix target, improve target. Not for broken behavior (/debug) or speed (/perf)."
workflow_type: prompt-chaining
---

# /design

**ARGUMENTS:** `$ARGUMENTS`. Modes: `/design <target>` creates a surface; `/design fix <target>` repairs an existing UI; `/design improve <target>` raises its visual/motion ceiling.

Read `.graph-powers/config.json`, root `DESIGN.md`, `${rulesDir}/design.md` when present, and files in scope. Load `Skill("landing-page-design")` only for a landing/marketing target; it owns conversion, section and index decisions. Load `Skill("design-fix")` only for `fix`; `Skill("designer")` for new/improve or a structural fix; `Skill("uxmaster")` for UX judgement; and `Skill("animate")` only for `improve` motion.

## 1. Lock the work

Classify surgical work (known component/pattern, unchanged information architecture) versus structural work (new surface or changed flow/hierarchy). Surgical repair follows the design-fix contract. Structural work produces the designer direction contract; for an L4+ structural surface, run Phase A planning and obtain the required user direction choice before code. Project tokens and explicit brief win; missing required token or conflicting established pattern stops for a decision.

## 2. Baseline

Capture shipped-width renders and have the read-only `graph-powers:ui-ux-designer` critique scope, WCAG 2.2 AA, hierarchy and density against the direction. This is the baseline for `fix`/`improve`; the critic never edits.

## 3. Build

`graph-powers:frontend-specialist` performs only the designer craft passes required by the mode: new `shape → build → polish`; fix `audit → harden → typeset → layout → adapt → optimize → polish`; improve `audit → bolder → animate → colorize → polish`. Each handoff carries the direction/baseline, reads its specific designer pass and craft floor, and returns changed files and measured floor evidence. A toolchain defect is reported, not repaired as a design side effect. One fix batch and at most one confirmation pass.

## 4. Close

Run `/verify quick` once. Re-run the read-only critique, compare it with the baseline, and return resolved/accepted/new findings plus `VERIFIED`, `VERIFIED-WITH-NOTES`, or `NEEDS-WORK`. Do not call a visual improvement complete without gate and comparison evidence.
