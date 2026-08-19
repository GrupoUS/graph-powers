# Structural Quality — Code Judo Review Standards

> the project adaptation of the "thermo-nuclear code quality review" doctrine (cursor-team-kit, absorbed 2026-07-06). Single source of truth for structural-quality review. Consumers **reference** this file, never duplicate its tables: SKILL.md Step 5 (fix-shape check), `systematic-audit` pack (Code Archaeologist structural sweep, `references/pack-guides.md § 8d`), and `/pr-review` (structural overlay in § 3C; token `full` deep-loads this file integrally per pr-review.md § 0.4).

## Code Judo Doctrine

Be ambitious about structural simplification. Do not stop at "this could be a bit cleaner" — actively hunt the restructuring that preserves behavior while making the implementation dramatically simpler, smaller, and more direct. Assume there is often a "code judo" move available: a reframe that uses the existing architecture more effectively so whole branches, helpers, modes, or layers disappear entirely. Prefer the solution that feels inevitable in hindsight. If a path deletes complexity rather than rearranging it, push hard for that path.

Three central questions for every meaningful change:

1. **Which reframe deletes these branches?** Can the change be restated so fewer concepts, conditionals, or helper layers are needed at all — not centralized, *gone*?
2. **Fewer concepts in the reader's head?** Does the diff reduce (or at least not grow) what a reader must hold to understand the flow? A refactor that moves complexity around without deleting it fails this question.
3. **Does the abstraction earn its keep?** A wrapper, generic mechanism, or optional mode must buy clarity proportional to its indirection — otherwise the direct flow wins.

Boring, direct, maintainable code beats hacky or magical code. Be skeptical of generic mechanisms that hide simple data-shape assumptions.

## Structural Smells (diff-time signals)

| Smell | Signal in the diff | Preferred remedy |
|---|---|---|
| **Spaghetti-growth** | New ad-hoc conditional, one-off boolean, nullable mode, or scattered special case inserted into an unrelated/shared flow — "weird if statements in random places" | Design problem, not a nit. Move the logic behind a dedicated abstraction, helper, state machine, or policy object; or reframe so the special case becomes the default flow |
| **File-size crossing** | File pushed from below **1000** lines to above by the PR (**presumptive blocker**); > 400 lines = flag for split (existing evaluator Mode 4 threshold, unchanged) | Decompose first: extract helpers, subcomponents, focused modules along cohesion lines |
| **Thin wrapper / identity abstraction** | Pass-through helper, wrapper that renames without simplifying, layer that adds indirection without buying clarity | Delete the layer; keep the direct flow |
| **Cast / optionality churn** | New `unknown` casts, unnecessary optional params, loosely-shaped ad-hoc objects, silent fallback papering over an unclear invariant (`as any` is already a NEVER — `anti-patterns.md`) | Make the boundary explicit: typed model or shared contract in the package both sides import, so the control flow gets simpler |
| **Bespoke helper, canonical exists** | Near-duplicate of an existing utility (see Canonical Homes below) | Reuse the canonical helper; extend it if a gap is real |
| **Wrong layer** | Feature logic leaking into shared paths (a `_core/` module, the shared package) or implementation detail leaking through an API | Move the logic to the package/module/layer that already owns the concept |
| **Sequential orchestration of independent work** | `await` chain over calls with no data dependency, when parallel would also be simpler | `Promise.all` when it simplifies (overlaps evaluator Mode 4 perf check — cite once) |
| **Non-atomic multi-step update** | Related writes that can leave state half-applied | Wrap them in a transaction when the project's driver supports one — and check that it does before assuming: some serverless HTTP drivers do not. When transactions are genuinely unavailable, the fallback is an idempotent sequence with a repair path, and that decision belongs in the plan, not in the diff |

## Canonical Homes

Where logic "wants" to live — a bespoke re-implementation next to any of these is a near-duplicate smell. The right-hand column is the *shape* to look for; resolve each one to the project's actual module before citing it in a review.

| Concern | Canonical home |
|---|---|
| Logger, db, AI provider singletons | the backend core module (`${paths.backendRoot}/_core/` or equivalent) — reuse, don't re-instantiate |
| Shared types/constants (backend ↔ frontend) | the shared package both sides import |
| Plan-tier / capability gates | the single capability resolver — never re-derive them per call site |
| Field-level PII access gates | the access-control module that already owns the rule |
| Motion presets/curves | `${paths.libRoot}/animation-variants.ts` or equivalent |
| Design-system primitives vs feature components | `${paths.componentsRoot}/ui/` (primitives only) vs `${paths.componentsRoot}/[feature]/` |

Extension bias: enhance existing structures before creating new files.

## Preferred Remedies (in order of ambition)

1. Delete a whole layer of indirection rather than polishing it.
2. Reframe the state model so conditionals disappear instead of getting centralized.
3. Turn special-case logic into a simpler default flow with fewer exceptions; change the ownership boundary so the feature becomes a natural extension of an existing abstraction.
4. Move the logic behind a dedicated abstraction / into the layer that already owns the concept (see Canonical Homes).
5. Replace condition chains with a typed model or explicit dispatcher; separate orchestration from business logic.
6. Extract a helper, pure function, or focused module (split large files along cohesion lines).
7. Collapse duplicate branches; reuse the canonical helper instead of a near-duplicate.
8. Parallelize independent work when that also simplifies the orchestration; restructure related updates into a more atomic flow.

Never settle for "maybe rename this" feedback when the real issue is structural. Never settle for a merely cleaner version of the same messy idea when a much simpler idea is visible.

## Fix-Shape Check (debugging — SKILL.md Step 5)

A bug fix that adds an ad-hoc conditional / one-off boolean / special case to an unrelated flow is a **symptom patch** in disguise: the special case usually marks the wrong layer (Iron Law #2). Prefer the fix at the model/boundary that deletes the special case. When ≥3 fix attempts fail, stop patching — hunt the code-judo restructure that deletes the whole bug class instead of a fourth patch.

## Output Discipline

Prioritize findings in this order:

1. Structural code-quality regressions
2. Missed opportunities for dramatic simplification (code-judo restructuring)
3. Spaghetti / branching-complexity increases
4. Boundary / abstraction / type-contract problems
5. File-size and decomposition concerns (SIZE_CROSS)
6. Modularity and abstraction issues
7. Legibility and maintainability concerns

**Anti-nit-flooding rule:** a smaller number of high-conviction comments beats a long cosmetic list. Do not flood a review with low-value nits when a larger structural issue exists — nits enter only after (or in the absence of) structural findings.

## Approval Bar — Presumptive Blockers

Correct behavior is not sufficient for approval. Each condition below defaults to **CHANGES_REQUESTED** unless the author supplies an explicit justification (1 line in the PR body naming the blocker — consistent with the project-wide "diverge with a 1-line justification" convention):

1. The PR pushes a file from below 1000 lines to above 1000 lines (SIZE_CROSS).
2. The PR adds ad-hoc branching (one-off booleans, nullable modes, scattered special cases) that makes an existing flow more tangled.
3. The PR preserves substantial incidental complexity when a plausible code-judo move would delete it.
4. The PR adds an unnecessary wrapper, cast-heavy contract, or optionality churn that makes the design more indirect.
5. The PR leaks feature logic across an architecture boundary (wrong layer / shared path).
6. The PR duplicates an existing canonical helper (see Canonical Homes) instead of reusing it.

## Review Tone

Direct, serious, demanding about quality — never rude, never softening a structural issue into a mild suggestion. Useful phrasings:

- "this pushes the file past 1k lines — can we decompose first?"
- "this adds another special-case branch into an already busy flow — can we move it behind its own abstraction?"
- "this works, but makes the surrounding code more spaghetti — keep the behavior, restructure the implementation."
- "this looks like a bespoke helper for something we already have — can we reuse the canonical one?"
- "there's a code-judo move here that makes this much simpler — can we reframe so these branches disappear?"
- "this refactor moves complexity around but doesn't delete it — can the model itself get simpler?"
