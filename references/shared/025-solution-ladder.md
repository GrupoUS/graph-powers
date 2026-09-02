## Section 2.5: Solution ladder

`020` sizes the *process* — how many phases, gates and agents a task earns. This section sizes the
*solution*, and it binds every writer, the main thread and every subagent alike, before the first
edit. Adapted from Ponytail (MIT; `NOTICE`). The rule is not "fewest tokens": it is write only what
the task needs, and never cut validation, error handling, security or accessibility to get there.

### The ladder

Stop at the first rung that holds:

1. **Does this need to exist at all?** A speculative need is skipped, and the skip is said in one
   line. (YAGNI)
2. **Already in this codebase?** A helper, type, util or pattern a few files over is reused, not
   rewritten. Look before writing — re-implementing what already exists is the most common slop.
3. **The standard library does it?** Use it.
4. **A native platform feature covers it?** `<input type="date">` over a picker library, CSS over
   JS, a database constraint over application code.
5. **An installed dependency solves it?** Use it. Never add one for what a few lines do.
6. **Can it be one line?** One line.
7. **Only then:** the minimum code that works.

The ladder is a reflex, not a research project — and it runs *after* the problem is understood,
never instead of it. Read the code the change touches and trace the real flow end to end, then
climb. Two rungs hold → the earlier one, and move on.

**A bug fix is the root cause, not the symptom.** A report names a symptom. Before editing, find
every caller of the function about to change: one guard in the shared function is a smaller diff
than a guard in every caller, and patching only the path the ticket names leaves every sibling
still broken.

### Rules

- No abstraction with one implementation, no factory for one product, no config for a value that
  never changes, no scaffolding "for later" — later can scaffold for itself.
- Deletion over addition. Boring over clever. Fewest files. Shortest working diff — once the problem
  is understood; the smallest change in the wrong place is a second bug.
- A complex request ships the lazy version and questions the rest in the same reply: "Did X; Y
  covers it. Need full X? Say so." At L4+ that question goes into Phase A's spec, not into code —
  the planning gates still hold. Never stall on an answer that has a sensible default — take it,
  label it `[ASSUMED]`, continue.
- Two same-size options → the one correct on edge cases. Less code, never the flimsier algorithm.
- A deliberate corner with a known ceiling (a global lock, an O(n²) scan, a naive heuristic) carries
  a one-line comment naming the ceiling and the upgrade path.

### Never simplified away

Validation at trust boundaries, error handling that prevents data loss, security, accessibility
basics, anything explicitly requested — the user insisting on the full version gets it, with no
re-arguing. And the check: non-trivial logic leaves one runnable check behind, the smallest thing
that fails if the logic breaks (`010-quality-gates.md` names which gate). Trivial one-liners need
none.

### Output

Code first, then at most three short lines: what was skipped, when to add it. An explanation longer
than the code is complexity smuggled back in as prose — delete it. An explanation the caller asked
for (a report, a walkthrough, the return contract of a subagent) is not debt; give it in full.

### Posture when in doubt

The lower tier of `020`, said in one line. A surface in `chain.riskSurfaces`, a second domain or a
failing gate raises it; doubt alone does not. The loops in `skills/planning` and `/gauntlet` exist
for the work that needs them — they are the escalation, not the default shape of a task.
