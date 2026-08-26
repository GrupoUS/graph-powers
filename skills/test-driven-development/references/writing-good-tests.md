# Writing good tests

Read this when writing or changing a test, adding a mock, or adding a helper only tests use. Two
principles govern everything here: every test names the break it catches, and every test
exercises the real thing. Strict TDD produces both — a test written first and watched failing
against real code has proven it can fail, and earns a mock only when the real dependency proves
slow or external.

## Principle 1: name the break

Before writing the test body, answer: **what production change would make this test fail — and is
that change a bug or a decision?** A test earns its place by catching a wrong branch, a missing
side effect, a wrong argument, a boundary case or a broken contract.

**Derive expectations independently.** Literals and hand-checked fixtures; table-driven tests with
literal `want` values are the preferred shape. An expectation computed by the code under test
passes whatever that code does:

```typescript
// Bad: mirror assertion, the same builder computes both sides
const expected = buildSearchQuery({ tag: 'urgent' });
expect(buildSearchQuery({ tag: 'urgent' })).toBe(expected);
// Good: hand-derived literal
expect(buildSearchQuery({ tag: 'urgent' })).toBe('tag:"urgent"');
```

**No change detectors.** If only an intentional decision can fail a test — a constant's value,
exact message wording, private structure — it fires on redesign and sleeps through bugs. Test the
behaviour that depends on the decision: not `expect(MAX_RETRIES).toBe(5)` but "a failing call is
retried five times and a sixth attempt never happens".

**Behaviour, not text.** Asserting that a script contains an exact line proves only that the
source is the source: run it on controlled inputs and assert outputs, side effects or exit codes.
A document that instructs an agent is tested by that agent's behaviour (`Skill("skill-improve")`
owns the loop); prose for people earns no test.

**Your code, not the framework.** Test the contract your code makes at its boundaries — the route
you register, the query you emit, the payload you produce; asserting that your router invokes a
registered handler is the framework's test. When upstream behaviour genuinely surprised you, one
narrow characterization test names the assumption. Constructors, getters, constants and trivial
forwarding earn a test only when they validate, normalize, default, derive, enforce or cause a
side effect — otherwise assert the first consumer-visible result that depends on them.

**Gate, before the test body.** Name the production change that fails it — none nameable means
redesign around an observable behaviour; only a decision means test the behaviour that depends on
it. Then confirm the expected value was derived without the code under test.

## Principle 2: exercise the real thing

**The mock earns no assertions.** A mock assertion passes when the mock is present and fails when
it is absent; it says nothing about the component. Assert the real component's behaviour — if the
mock is what you are checking, unmock it or delete the assertion. Ask: "are we testing the
behaviour of a mock?"

```typescript
expect(screen.getByRole('navigation')).toBeInTheDocument();     // Good: real behaviour
expect(screen.getByTestId('sidebar-mock')).toBeInTheDocument(); // Bad: mock existence
```

**Mock at the right level.** Learn every side effect of the real method before replacing it; mock
the slow or external operation and keep what the test depends on real. Unsure? Run the test
against the real implementation first and watch what has to happen.

```typescript
// Bad: swallows the config write that duplicate detection reads
vi.mock('ToolCatalog', () => ({ discoverAndCacheTools: vi.fn() }));
// Good: only the slow server startup is mocked; the config write stays real
vi.mock('ServerManager');
```

**Make doubles specific.** When arguments, call counts or ordering are part of the contract,
assert them — a fake that accepts anything verifies nothing; each branch gets its own fixture or
spy so the wrong branch cannot satisfy the expectation.

**Mirror real data completely.** A mock response carries the complete real structure, not only
the fields the test reads: a partial mock fails silently when downstream code reads an omitted
field — the test passes while integration breaks.

**Production classes carry production methods only.** Cleanup only tests need lives in test
utilities, never as a `destroy()` on the production class. Called only from tests? Then it is a
test utility.

**Prefer real components over complex mocks.** When mock setup outgrows the test logic or tests
break when the mock changes, switch to an integration test with real components. Ask: "do we
need a mock here at all?"

**Gate, before adding a mock or helper.** List the real method's side effects; keep the ones the
test depends on real and mock the slow or external level below them. About to assert on the mock
itself? Unmock it or delete the assertion.

## Finishing a test file

Tests ship with the implementation — the cycle is what "complete" means — and only the tests the
behaviour needs: trivial code earns none, and a test written to satisfy process costs maintenance
forever.

**The mutation check.** Mentally mutate the production code; at least one test should fail for
each realistic mutation: wrong constant or argument · wrong branch handler · missing state change
or side effect · empty or default return · missing validation for zero, empty, nil, unauthorized or
malformed input. A mutation nothing catches marks the behaviour as unprotected, or the test as
tautological.

## Warning signs

- Setup and assertion share the same object, guaranteeing equality
- The test can fail only through a crash or a missing selector
- The test fails on every intentional change and never on accidental breakage
- Expected values hide behind loops, builders or helpers
- The test exists for coverage and checks no side effect or outcome
- An assertion checks a `*-mock` test id, or fails if the mock is removed
- Mock setup is more than half the test, or nobody can say why the mock is needed
