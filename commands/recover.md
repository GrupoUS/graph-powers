---
description: Failure recovery protocol for post-failure handling. Use after 2+ failed fix attempts.
workflow_type: routing
---

# /recover - Structured Failure Recovery

> **Read first:** `${CLAUDE_PLUGIN_ROOT}/references/shared-context.md` — config loader, quality
> gates, complexity routing, agent matrix, spawn patterns. Every section this command cites by
> number lives there. Read it before step 0; do not reconstruct it from memory.

**ARGUMENTS**:$ARGUMENTS

<command-instruction>
Execute Phase 2C Failure Recovery protocol:

## Step 1: STOP

- Halt all current fix attempts immediately
- Do not make any more changes

## Step 2: DOCUMENT

Output a structured failure report:

- What was the original bug/error?
- What fixes were attempted? (list each)
- Why did each fail?
- Current state of the codebase

## Step 3: REVERT (if applicable)

- If changes made the codebase worse, revert to last clean state
- Run `git diff HEAD` to show what changed
- Confirm with user before reverting if uncertain

## Step 3.5: CLEAR CACHES

Before retrying, clear stale state that may cause phantom errors:

```bash
rm -rf <build-tool-cache> <output-dir>   # e.g. node_modules/.vite, dist, .astro, .next
${tooling.packageManager} install         # Reinstall deps
${tooling.commands.typeCheck} && ${tooling.commands.build}   # Verify clean state
```

Then consult the framework skill the project declares for its own recovery patterns. Example, for an
Astro project:
- **Content Collection not found** → Check `src/content/<name>/` exists with at least one file
- **Hydration mismatch** → Guard browser-only APIs with `typeof window !== 'undefined'`
- **Tailwind classes not working** → Verify `@import "tailwindcss"` in global.css + `@tailwindcss/vite` in astro.config.mjs
- **Transition-router error** → Remove `ClientRouter` / `ViewTransitions` when the project is a static MPA
- **config.ts errors** → Astro 5+ reads `src/content.config.ts`; remove accidental `src/content/config.ts` files

## Step 4: CONSULT oracle

- Delegate the failure report to oracle agent
- Prompt format:
  "Here is a failure I cannot resolve: [DOCUMENT output]. Analyze root cause and recommend approach."

## Step 5: REPORT TO USER

- Present oracle analysis
- Present options with effort estimates
- Reference the relevant framework skill sections when the failure is framework-related
- Ask user how to proceed

## Recovery checklist

Before declaring unrecoverable, verify:
- [ ] Build-tool cache cleared
- [ ] `${tooling.commands.typeCheck}` passes
- [ ] `${tooling.commands.build}` succeeds
- [ ] `${tooling.commands.lint}` passes
- [ ] The framework invariants in `${rulesDir}/` still hold for the touched paths

Where the project's stack adds its own invariants, they belong in `${rulesDir}/`, not here. For an
Astro project that list typically reads: content collections declared in `src/content.config.ts`
with explicit schemas, island props passed as plain objects, `client:*` directives only on
component files, no router component in a static MPA.
  </command-instruction>
