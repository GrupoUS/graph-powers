# Verification Agent On-Demand Rubric

Load for mandatory checks, severity, or defect-report structure.

## Mandatory checks

- Acceptance happy path plus invalid input, cancel/back, retry, refresh, and
  double-submit where relevant.
- Loading, empty, partial, error, permission-denied, and success feedback.
- Mobile viewport, keyboard navigation, visible focus, labels, contrast, zoom,
  reduced motion, and scroll containment.
- Console errors, uncaught page errors, failed/cancelled network requests, and
  stale or duplicated state.

## Severity

- P0: security/data-loss/cross-tenant or system-wide blocker.
- P1: core flow impossible or corrupting with no reasonable workaround.
- P2: important degradation with workaround or limited scope.
- P3: minor usability/visual defect with low task impact.

## Defect fields

Flow and environment; preconditions; numbered reproduction; expected; actual;
severity and confidence; screenshot/log/network evidence; likely owning boundary;
concrete fix direction; adjacent regression checks.

Redact tokens, PII, and sensitive response bodies from all evidence.
