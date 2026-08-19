# Project Planner On-Demand Rubric

Load the matching depth and output needs only.

## Depth

- Quick: localized, reversible work with known patterns; direct scoped plan.
- Standard: multi-file or cross-layer work; research, shadow paths, risks.
- Deep: migrations, integrations, security/PII, architecture, irreversible or
  production-impacting work; alternatives, ADRs, rollback, staged verification.

## Spec fields

Problem, users/jobs, scope, non-goals, current behavior, proposed behavior, user
flows, affected ownership, data/API/config changes, integrations, migrations,
security/privacy, observability, rollback, risks, open questions, and measurable
acceptance criteria.

## Sprint/task fields

Goal, dependencies, owned paths, changes, invariants, focused tests, broader
gates, browser/runtime probes, checkpoint artifact, and explicit do-not-touch
scope. End at a reviewable working tree unless Git action is separately approved.

## Adversarial gates

1. Every vague adjective becomes an observable criterion.
2. Failure, retry, empty, permission, concurrency, migration, and rollback paths
   are covered where applicable.
3. Existing patterns are reused or divergence is justified.
4. Tasks are dependency ordered and independently verifiable.
5. Critical assumptions have confidence at least 3 or block execution.
