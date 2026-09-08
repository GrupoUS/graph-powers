---
name: design-fix
description: "Use when repairing an implemented UI in place while preserving behavior and visual direction. Trigger on design fix, production readiness, responsive or accessibility cleanup, missing loading, empty or error states, token or spacing drift. Not for new surfaces or identities (designer), broken behavior (/debug), or speed (/perf)."
user-invocable: true
argument-hint: "[target]"
---

# Design Fix

Repair an existing surface without changing its product behaviour or visual direction. Inspect the
current states first, then fix the smallest visible defect across responsive layout, hierarchy,
tokens, accessibility and loading/empty/error states. Preserve interaction contracts; route broken
behaviour to `/debug`, measurable speed to `/perf`, and a new identity to `designer`.

Read `${CLAUDE_PLUGIN_ROOT}/skills/designer/references/craft-floor.md` for the acceptance floor and
`${CLAUDE_PLUGIN_ROOT}/skills/designer/references/craft-passes.md` only for a pass that applies. Use browser evidence for rendered changes. Stop when
the requested states meet the floor and the focused verification passes; do not turn cleanup into a
redesign.
