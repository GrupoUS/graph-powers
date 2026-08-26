# Writing good tests

Read this when a plan adds or changes a test. The test earns its place by naming a real break and
exercising the production behaviour that would reveal it.

## Name the break

Before writing the body, state what incorrect production change would make the test fail: a wrong
branch, missing side effect, invalid boundary, malformed output or broken contract. Derive expected
values independently from the code under test; use literal fixtures rather than rebuilding the
answer with the same helper.

Prefer one behaviour per test and a name that describes the outcome. Do not test private structure,
constants, exact implementation text or framework registration. Test the route, query, payload,
response or side effect visible at the production boundary. Trivial functions need no standalone
test when their behaviour is covered by that first consumer-visible assertion.

## Use real boundaries

Keep the component under test real. Before mocking, list the dependency's side effects and preserve
the ones the behaviour depends on. Mock only the slow, external or destructive operation, and make
doubles complete and specific when arguments, ordering or calls are themselves part of the
contract. Never assert merely that a mock exists or was called.

Mentally mutate the implementation: wrong argument, wrong branch, missing state change, empty
return, and malformed or unauthorized input should each be caught where relevant. If no realistic
mutation would fail the test, redesign the test around an observable behaviour.
