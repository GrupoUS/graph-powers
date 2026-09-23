---
description: "Decide how to build a multi-step feature before code: scope, trade-offs, integrations, ordering, triage and a plan. Do not use to execute a plan or fix a known defect."
workflow_type: prompt-chaining
---

> Hermes: first load `skill_view("graph-powers:graph-engineering")` for native calls and host-policy limits. `content/` paths are `file_path` values relative to the common registered-document parent. Source tools/model frontmatter is not host enforcement.

# /plan

**ARGUMENTS:** the user-provided arguments. This is the adapter for `skill_view("graph-powers:planning")`; tiers, design, TDD and review live there.

Read `content/references/shared/000-config-loader.md`, `content/references/shared/005-method-bootstrap.md`, `.graph-powers/config.json`, and root `PRODUCT.md` when present; invoke the skill with original arguments/config. Empty scope asks what to plan; GitHub issue triage stays in the skill. It routes L1-L2 direct, L3 Phase A, and L4+ Phase A → B; outside issue triage, run `ultra-plan` only when the user asks for it by name.

Before execution, present destination, approach, plan path/task count, open or `[ASSUMED]` decisions and review verdict; wait for approval. L4 and `--plan-only` stop. Approved L5+ continues to `/implement`, whose Phase C closes with `/verify quick`. Stop with unstaged changes; Git/publication needs separate approval.
