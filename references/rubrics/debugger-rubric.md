# Debugger On-Demand Rubric

Load only for forensic debugging, cascade analysis, or prevention design.

## Forensic flow

1. Freeze the observed symptom, timestamp, environment, and last known good state.
2. Build an event timeline across client, API, service, persistence, and deployment boundaries.
3. Identify the earliest invariant violation rather than the loudest downstream error.
4. Use logs, tests, diffs, and probes to falsify competing hypotheses.
5. Reproduce the earliest violation and verify the fix at that boundary.

## Cascade checks

- Authentication/tenant context loss before database access.
- Schema/config drift before application exceptions.
- Cache invalidation or async ordering before stale UI.
- Provider/webhook retries before duplicate writes.
- A primary failure hidden by cleanup, retry, or error-mapping failures.

## Prevention artifact selection

- Stable deterministic regression: focused Vitest test.
- Configuration or boundary invariant: validation/probe.
- Operational-only failure: runbook check or monitoring assertion.
- Repeated coding trap: concise canonical rule or skill learning, only when requested.

Do not create a broad refactor, global formatter pass, or unrelated cleanup as prevention.
