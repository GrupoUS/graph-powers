# Mobile Developer On-Demand Rubric

Load for native modules, offline-first design, performance diagnosis, or store
readiness.

## Native module gate

- Confirm the capability is unavailable in current dependencies.
- Compare maintained alternatives and platform support.
- Identify permissions, entitlements, linking/build changes, and fallback.
- Obtain authorization before installation or signing changes.

## Offline-first gate

- Define source of truth, queue semantics, idempotency, conflict resolution,
  retry/backoff, connectivity transitions, and user-visible sync state.
- Encrypt sensitive persisted data and minimize retention.

## Runtime and UX

- Profile startup, frames, list virtualization, images, bridge calls, and memory.
- Verify safe areas, keyboard avoidance, orientation, back behavior, deep links,
  screen-reader semantics, dynamic type, and touch targets.

## Store readiness

- Builds, signing, privacy declarations, permissions copy, icons/splash, release
  configuration, crash reporting, rollback, and platform policy evidence.
