# TDD policy

This is the single TDD authority for planning and execution. Apply it to a feature, bug fix,
refactor or behaviour change before production code is written.

## Required cycle

1. Choose one observable behaviour at the real production interface.
2. Write the smallest focused test and run it.
3. Confirm **RED**: it fails for the expected missing behaviour, not because of a typo or broken
   setup. Record the command and deciding output.
4. Write the minimum **GREEN** implementation and run the focused test again.
5. Confirm GREEN, then refactor only while all relevant tests remain green.

Tests exercise the production seam a user or caller uses. Do not test a private helper with
synthetic inputs when the real route can be reached. Trivial getters, constructors, constants and
forwarders need no direct test; cover their first consumer-visible behaviour instead.

When writing or changing a test, also read `writing-good-tests.md` in this directory. The test must
be independent of the implementation. Use literal expectations and assert outcomes,
side effects or emitted contracts. Mock only a slow, external or destructive dependency, keeping
the component under test and its relevant boundary real.

## Task status

Every Phase B task declares exactly one status:

- `TDD: required` — the task includes RED and GREEN steps and evidence.
- `TDD: not-applicable (<motivo>)` — only for documentation, generated artefacts, configuration-
  only work, or a throwaway prototype; the reason is mandatory.
- `TDD: exception-approved (<motivo>)` — only when the user approved a concrete exception; record
  the approval reason and scope.

No other status or implicit exception is valid. A task marked `required` cannot omit RED/GREEN.
An exception never permits skipping the focused validation that applies to the artefact.

## Red flags

Stop and start the task again when production code exists before RED, the test passes immediately,
the failure reason is unknown, or a test asserts only that a mock was called. “Too simple to test,”
“I will test after,” and manual testing are not exceptions.
