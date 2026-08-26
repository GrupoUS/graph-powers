---
name: test-driven-development
description: "Before implementation code for any feature or bug fix. Failing test first."

---

# Test-Driven Development

Write the test first. Watch it fail. Write the minimum that passes. **If you did not watch the
test fail, you do not know it tests the right thing.**

Loaded by `/implement` (Hard TDD gate, L3+) and by `Skill("debugger")` Step 5, as
`Skill("graph-powers:test-driven-development")`.

## The Iron Law

```text
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

**Always:** new features, bug fixes, refactors, behaviour changes. **Exceptions — each one asked
of the user, never assumed:** throwaway prototypes, generated code, configuration files. "Skip TDD
just this once" is a rationalization, not an exception.

Wrote code before the test? Delete it and implement fresh from the tests: not kept "as
reference", not "adapted", not looked at. Delete means delete.

## Red, Green, Refactor

The test command is `${tooling.commands.test}` from `.graph-powers/config.json`; on a JS/TS tree,
`${CLAUDE_PLUGIN_ROOT}/references/shared/130-bun-tsgo-gates.md` resolves it. Never hardcode a
package-manager command.

| Step | Do | Gate |
|---|---|---|
| **RED** | One minimal test for one behaviour: clear name, real code, no mocks unless unavoidable. | — |
| **Verify RED** (mandatory) | Run the test command on that file. | **Fails**, not errors, for the expected reason: feature missing, not a typo. Passes? You are testing existing behaviour — fix the test. Errors? Fix and re-run until it fails correctly. |
| **GREEN** | The simplest code that passes. No extra features, no refactoring elsewhere, no "improving" beyond the test. | — |
| **Verify GREEN** (mandatory) | Run the test command again. | Passes, every other test still passes, output pristine (no errors, no warnings). Fails? Fix the code, not the test. Others fail? Fix now. |
| **REFACTOR** | After green only: remove duplication, improve names, extract helpers. | Tests stay green; no behaviour added. |
| **Repeat** | Next failing test for the next behaviour. | — |

Each Verify step is a claim, and a claim carries its output and exit code —
`${CLAUDE_PLUGIN_ROOT}/references/shared/015-verification-gate.md`.

### Example: retry

```typescript
// Good: clear name, real code, one behaviour
test('retries a failing operation until the third attempt succeeds', async () => {
  let attempts = 0;
  const op = () => { attempts++; if (attempts < 3) throw new Error('fail'); return 'ok'; };
  expect(await retryOperation(op)).toBe('ok');
  expect(attempts).toBe(3);
});
// Bad: vague name, asserts on the mock instead of the code
test('retry works', async () => {
  const mock = jest.fn().mockRejectedValueOnce(new Error()).mockRejectedValueOnce(new Error()).mockResolvedValueOnce('ok');
  await retryOperation(mock);
  expect(mock).toHaveBeenCalledTimes(3);
});
```

GREEN is a three-iteration loop; an options bag (`maxRetries`, `backoff`) is YAGNI until a test
asks for it.

## The seam

A bug's RED test exercises the **actual production code path** that fails — not a private helper
called with synthetic arguments, not a happy-path stub beside it. No seam a test can reach?
Refactor to expose one *first*, still inside RED, then write the test. A helper that passes while
the production route still fails proves nothing;
`${CLAUDE_PLUGIN_ROOT}/skills/debugger/references/methodology.md § 5` relies on this.

## Good tests

| Quality | Good | Bad |
|---|---|---|
| Minimal | One thing; an "and" in the name means split it | `validates email and domain and whitespace` |
| Clear | The name describes the behaviour | `test1` |
| Shows intent | Demonstrates the desired API | Obscures what the code should do |

When writing or changing any test, read `references/writing-good-tests.md`:

- Name the production change that would fail the test, before writing it.
- Assert on real behaviour, never on a mock's behaviour.
- Test-only code lives in test utilities, out of production classes.
- Understand a dependency's side effects before mocking it.

## Rationalizations

| Excuse | Reality |
|---|---|
| "Too simple to test" | Simple code breaks; the test takes thirty seconds. |
| "I'll test after" | A test written after passes at once, so it never proved it can catch the bug. |
| "Tests after achieve the same goals" | Tests-after ask "what does this do", biased by the code; tests-first ask "what should this do". |
| "Already manually tested" | No record, no re-run, and cases forgotten under pressure. |
| "Deleting X hours is wasteful" | Sunk cost: the time is spent either way; untrusted code is the real waste. |
| "Keep as reference, write tests first" | You will adapt it, which is testing after; delete means delete. |
| "Need to explore first" | Fine: throw the exploration away and start with TDD. |
| "Test hard = design unclear" | Listen to the test: hard to test is hard to use. |
| "TDD will slow me down" | TDD is the pragmatic path; the shortcut is debugging in production, which is slower. |
| "Manual test faster" | Manual proves no edge case and repeats on every change. |
| "Existing code has no tests" | You are improving it: add the tests. |

## Red flags — stop and start over

Code before test · test after implementation · test passes immediately · cannot explain why the
test failed · tests added "later" · "just this once" · "already manually tested" · "tests after
achieve the same purpose" · "spirit not ritual" · "keep as reference" or "adapt existing code" ·
"already spent X hours" · "TDD is dogmatic, I'm being pragmatic" · "this is different because...".
All of them mean: delete the code, start over with TDD.

## Verification checklist

- [ ] Every new function or method has a test
- [ ] Watched each test fail before implementing
- [ ] Each failed for the expected reason (feature missing, not a typo)
- [ ] Wrote the minimal code to pass each test
- [ ] All tests pass
- [ ] Output pristine (no errors, no warnings)
- [ ] Tests use real code (mocks only when unavoidable)
- [ ] Edge cases and errors covered

Cannot check every box? You skipped TDD. Start over.

## When stuck

| Problem | Solution |
|---|---|
| Do not know how to test | Write the wished-for API, then the assertion first; ask the user. |
| Test too complicated | Design too complicated: simplify the interface. |
| Must mock everything | Code too coupled: use dependency injection. |
| Test setup huge | Extract helpers; still complex? Simplify the design. |

## Debugging integration

A bug is a failing test first: reproduce it on the seam above, then run the cycle — the test
proves the fix and prevents the regression. Never fix a bug without one. `Skill("debugger")` owns
everything before RED (feedback loop, reproduce, hypothesise); this skill owns RED to GREEN inside
its Step 5.

## Final rule

```text
Production code  ->  a test exists and failed first
Otherwise        ->  not TDD
```

No exceptions without the user's permission. The cycle ends at green working-tree changes;
committing them is the user's call, in the current turn
(`${CLAUDE_PLUGIN_ROOT}/references/safety-floor.md § 1`).
