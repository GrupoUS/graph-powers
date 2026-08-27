# Hook hardening next steps — Design spec

## Destination

Graph Powers is done with this slice when automatic project-configured commands execute only from
a machine-approved config digest, Stop responses never inject arbitrary checker output, Cursor
client identity is explicit in generated wiring, agent-issued commits attempt every declared core
gate under one bounded and cache-aware runner, and Windows CI records the six-handler PreToolUse
latency without prematurely replacing the handlers with a dispatcher.

## Context

The first hook-evolution pass connected `Stop`, made exit codes authoritative, covered the complete
working change-set, and propagated the lifecycle registration through generated clients. Its
remaining P1/P2 items are security and operational hardening, not more prompt rules. This design
keeps enforcement in Python hooks and adds no always-loaded context file.

## Reuse ledger

| # | Need | Existing asset (`path:line`) | Verdict | Justification |
|---|---|---|---|---|
| N1 | Trust project-configured commands outside repository control | `hooks/_config.py:317` | NEW | Config discovery remains canonical, but no existing unit owns machine-local approval state; `hooks/command_trust.py` is consumed by all three automatic command runners and exposes the approval CLI. |
| N2 | Eliminate arbitrary Stop diagnostic injection | `hooks/stop_verify.py:64` | EXTEND | Keep the outcome taxonomy and replace checker output with a fixed summary. |
| N3 | Identify Cursor without payload heuristics | `cursor/install.mjs:66` | EXTEND | The generator already owns client-specific command adaptation. |
| N4 | Run declared core gates before agent-issued commits | `hooks/commit_audit_gate.py:57` | EXTEND | One existing PreToolUse owner already intercepts commit and push. |
| N5 | Fingerprint staged, unstaged and untracked content | `hooks/_change_set.py:48` | EXTEND | The canonical Git change-set module gains content attestation. |
| N6 | Cache successful gates locally | `.graph-powers/cache/` | EXTEND | The ignored runtime directory already owns ephemeral hook state. |
| N7 | Measure Windows handler overhead | `.github/workflows/ci.yml` | NEW | No reusable benchmark exists; the new script is invoked by a report-only Windows job. |
| N8 | Activate telemetry, dispatcher or modern events | `hooks/hooks.json` | REUSE | No activation: existing independent registrations stay authoritative until evidence supplies a concrete incident. |

## Regression watchlist

| # | Existing behaviour that must still work | How to prove it | Owner phase |
|---|---|---|---|
| W1 | Missing, invalid or unreadable config never wedges a session | `python3 hooks/test_hooks.py` | 1 |
| W2 | Red lint blocks and green lint releases Stop | `python3 hooks/test_hooks.py` | 1 |
| W3 | `stop_hook_active=true` terminates the Stop loop | `python3 hooks/test_hooks.py` | 1 |
| W4 | Formatter remains file-scoped and fail-open | `python3 hooks/test_hooks.py` | 1 |
| W5 | Legacy `gates.preCommitAudit` remains compatible | `python3 hooks/test_hooks.py` | 2 |
| W6 | Cursor artefacts remain generated and bounded to five follow-ups | `python3 .github/check_cursor.py` | 3 |
| W7 | Codex and Grok retain the shared Stop registration | `python3 .github/check_codex.py` in its CI fixture and `python3 .github/check_grok.py` | 3 |
| W8 | Independent PreToolUse handlers preserve ordering and isolation | `python3 hooks/test_hooks.py` plus the report-only benchmark | 3 |

## Background research

- Official Claude documentation, checked 2026-08-27, confirms blocking `Stop`,
  `stop_hook_active`, `SubagentStop`, `TaskCompleted` and `PostToolBatch`, but these events do not
  have equivalent semantics everywhere: <https://code.claude.com/docs/en/hooks>.
- Official Cursor documentation, checked 2026-08-27, confirms `followup_message`, `loop_count` and
  bounded `loop_limit` behavior: <https://prod.cursor.com/docs/hooks>.
- Official Codex schemas and integration tests now confirm a `Stop` `decision: "block"` contract;
  parity across Desktop, `exec`, loop limits, interruption and UX remains **NOT CONFIRMED**:
  <https://github.com/openai/codex/blob/main/codex-rs/hooks/schema/generated/stop.command.input.schema.json>,
  <https://github.com/openai/codex/blob/main/codex-rs/hooks/schema/generated/stop.command.output.schema.json>,
  <https://github.com/openai/codex/blob/main/codex-rs/core/tests/suite/hooks.rs>.
- Official Grok documentation does not provide a lifecycle contract detailed enough to claim
  blocking Stop parity: <https://docs.x.ai/build/features/skills-plugins-marketplaces>.
- A repository-local `trusted: true` value is self-authorizing and therefore not a trust boundary.

## Approach (chosen)

Use a machine-local trust registry keyed by canonical repository root, canonical contained config
path and SHA-256 of raw config bytes. A missing or changed approval yields `SKIP_UNTRUSTED` and no
configured process starts. Remove checker stdout/stderr from model-facing responses entirely.
Extend the existing commit audit hook into a single sequential runner for declared
`typeCheck`, `lint`, `test` and `build` commands, with worktree scope, total timeout and per-gate
success cache. Preserve `preCommitAudit` as an optional additional command. Generate an explicit
Cursor CLI marker. Add a dependency-free Windows benchmark job that reports data but cannot fail on
latency until a baseline exists.

## Architecture

- **Canonical project/config identity:** payload `cwd`/`workspaceRoot`, then the harness environment,
  then the process cwd resolves to the enclosing Git top-level when one exists; a non-Git directory
  uses its canonical resolved directory. A missing/non-directory start produces no trusted config.
  Config lookup remains canonical `.graph-powers/config.json` before legacy `.claude/config.json`;
  the first existing file is authoritative, including when malformed. A config symlink is accepted
  only when its resolved target remains inside the canonical project root. If the canonical path
  exists but resolves outside the root, project config is absent and lookup does **not** fall back to
  legacy config; fallback occurs only when the canonical path does not exist.
- **Machine trust registry:** `hooks/command_trust.py` owns
  `Path.home()/.graph-powers/command-trust.json`, schema
  `{version:1, projects:{rootHash:{configPathHash,configSha256,approvedAt}}}`. Hashes are SHA-256 of
  normalized canonical path text and raw config bytes; raw project paths and commands are not
  stored. The file is capped at 256 projects, oldest approval first on eviction, written through a
  same-directory temporary file plus `os.replace`, and set to mode `0600` where POSIX permissions
  exist. Parse/read/write/permission failure means untrusted, never trusted.
- **Path normalization:** resolve with `Path.resolve(strict=True)`, apply `os.path.normcase` (case
  folding only on platforms whose filesystem rules require it), replace `\` with `/`, normalize
  Unicode to NFC, then encode UTF-8 with `surrogatepass`. Containment uses resolved `Path.is_relative_to`
  and fails safely across Windows drives. These exact bytes feed `rootHash` and `configPathHash`.
- **Human approval:** the entrypoint supports `approve [PROJECT]`, `status [PROJECT]` and
  `revoke [PROJECT]`. Documentation invokes it with the active interpreter rather than a literal
  executable name; runtime command construction uses `sys.executable`, `subprocess.list2cmdline` on
  Windows and `shlex.join` elsewhere. Hook responses never echo that path-bearing command. Approval
  never comes from repository config.
- **Automatic command consumers:** `hooks/ultracite.py`, `hooks/stop_verify.py` and
  `hooks/commit_audit_gate.py` check the same trust decision before launching project commands.
- **Git attestation:** `hooks/_change_set.py` fingerprints HEAD, raw status, staged and unstaged
  binary diffs, index entries, untracked file bytes or symlink targets, config bytes, command text,
  platform/runtime and executable identity.
- **Commit runner:** `hooks/commit_audit_gate.py` keeps one lifecycle registration and sequentially
  resolves declared core gates. Only a process that actually returns nonzero denies; unavailable,
  timeout and internal failures remain explicit fail-open outcomes and are never cached green.
- **Client adapter:** `cursor/install.mjs` appends `--graph-powers-client cursor` only to the
  generated Stop verifier command. `hooks/stop_verify.py` recognizes only that exact argument pair;
  an unknown/malformed marker uses the native response, and `status`/`loop_count` payload fields
  never influence client selection. Generator checks reject a marker in Claude source or any
  generated non-Cursor command.
- **Evidence:** `.github/benchmark_hooks.py` measures individual and full-chain p50/p95; Windows CI
  invokes it report-only. Existing checkers continue to own wiring parity.

## Data flow

1. A lifecycle event resolves the canonical project and its contained project config.
2. The command consumer computes the config identity and checks the user-local registry.
3. Untrusted or changed identity returns a fixed skip outcome without launching the configured
   command. The approval CLI records only canonical identity, digest and timestamp.
4. Stop runs dirty-tree lint only and emits a fixed block/skip contract.
5. An agent-issued commit resolves the declared core gate plan, computes the worktree fingerprint,
   reuses only fresh matching green entries, then runs remaining commands within the total budget.
6. Success updates the small atomic cache; failures never create a green attestation.

## Stop response contract

- `ALLOW` and `SKIP_NOT_DECLARED`: no stdout.
- `DENY` on Claude/Codex/default clients: exactly `{decision:"block", reason:"<fixed summary>"}`.
- `DENY` with the explicit Cursor marker: exactly `{followup_message:"<fixed summary>"}`.
- Fail-open `SKIP_UNAVAILABLE`, `SKIP_UNTRUSTED`, `TIMEOUT` and `INTERNAL_ERROR` on native clients:
  exactly `{systemMessage:"<fixed summary>"}`; Cursor emits nothing for these outcomes so it cannot
  start a repair loop for a checker that did not run.
- Permitted dynamic values are the fixed outcome code, one fixed gate name, integer exit code,
  schema-validated opt-in key and first 12 hex characters of the config digest. Checker
  stdout/stderr, command text, local paths, approval commands, ANSI/control content and arbitrary
  exception text never enter any response field.

For the PreToolUse commit/audit runner, PASS and cache hit are silent. An executed failing gate exits
2 and writes one fixed UTF-8 stderr line shaped as `DENY + fixed gate + integer exit code + opt-in
key`. Fail-open outcomes exit 0 and write at most one fixed line:
`[<reason-code>] <fixed-gate> skipped`; untrusted state may add only the first 12 digest hex
characters. No subprocess output, command, exception, local path or control character is forwarded.

## Pre-commit configuration and trigger contract

`gates.preCommit` is an optional object. Absence uses these backward-compatible enforcement
defaults: `enabled: true`, `commands`: every actually declared member of
`[typeCheck, lint, test, build]`, `scope: "worktree"`, `timeoutTotal: 120`, and
`cacheSeconds: 300`. An explicit `commands` array restricts that fixed allowlist; an empty array
runs no core gate. `timeoutTotal` is bounded to 1–600 seconds and `cacheSeconds` to 0–86400.
Unsupported scope or malformed shapes yield an explicit fail-open skip, not a staged emulation.

The fixed core order is type-check → lint → test → build. `git commit` runs enabled core gates and
then the legacy `preCommitAudit`; `git push` runs only the legacy audit, preserving current behavior.
`preCommitAudit.timeout` remains a per-command ceiling (default 120, maximum 600) and, on commit, is
also capped by the remaining **combined** `timeoutTotal` after core gates. Budget exhaustion skips
the audit as `TIMEOUT`, exits 0 and creates no cache entry. On push, where no core gate runs, the
audit timeout is the complete budget. Its new `cache` field defaults false because an arbitrary audit may
depend on network/external state. The core success cache uses `cacheSeconds`; audit caching requires
`cache: true`. `<PREFIX>_ALLOW_VERIFY=1` releases core gates only and
`<PREFIX>_ALLOW_AUDIT=1` releases the audit only. The manifest grants this one hook 610 seconds so
the schema maximum can complete; its internal total budget remains authoritative.

This is agent lifecycle coverage only: it intercepts Bash tool calls that contain `git commit` or
`git push`. It does not claim to cover a human terminal, IDE Git integration or Git-native hooks.

## Fingerprint and cache contract

The SHA-256 protocol is versioned `gp-precommit-v1`. Every frame is encoded as label length, label,
byte length and bytes, preventing concatenation ambiguity. Frames cover canonical-root hash,
canonical config-path hash and raw config bytes; HEAD; raw porcelain-v1 `-z` status; raw
`git ls-files --stage -z`; staged and unstaged `--binary --no-ext-diff` streams; every non-ignored
untracked path plus file type, mode and bytes (or symlink target); scope; gate name/literal command;
platform, architecture and Python version; SHA-256 of PATH; and resolved first-executable canonical
path hash, mode and complete executable bytes. Size and `mtime_ns` are recorded only as metadata,
never as the identity. If executable bytes cannot be hashed inside the fingerprint budget, caching
is disabled for that run.

Git metadata capture is capped at 8 MiB; file and diff content is hashed in 1 MiB streaming chunks
without retention; the complete fingerprint has a 15-second total budget. Exceeding either bound,
unreadable content or any subprocess error produces “fingerprint unavailable”: gates still run but
no result is cached. The cache schema is versioned, contains at most one current success per fixed
gate (five entries including audit) and is capped at 32 KiB. It stores only gate name, fingerprint
and completion timestamp. Expired/corrupt/oversized cache is a miss. Writes use same-directory
temporary files and atomic replacement; a concurrent lost update can cause a later rerun but cannot
create a false hit. Environment values other than a hash of PATH are deliberately outside the
attestation, so the short TTL makes this cache an acceleration, not a cross-environment proof.

## Error handling

- Malformed payload/config/cache, unreadable paths, missing executables, timeouts and internal
  exceptions exit the hook with code 0 and a fixed skip reason; no arbitrary command output is
  emitted. Trust is stricter: missing, malformed, unreadable or mismatched registry state is always
  `SKIP_UNTRUSTED`, still exits 0, and launches no project-configured command.
- A checker that launched and returned nonzero is `DENY`.
- External config symlinks are treated as no project config.
- Cache corruption is a miss; concurrent writes use same-directory atomic replacement.
- `scope: worktree` is explicit. Staged-only isolation is not emulated and is reported unsupported
  if requested.

## Testing

- RED/GREEN tests cover external-symlink rejection, trust approval/invalidation/revocation, all
  automatic command consumers, fixed diagnostic output, secret and prompt-injection suppression,
  explicit Cursor identity, staged/unstaged/untracked fingerprint invalidation, config/command and
  executable invalidation, cache hit/miss/corruption, total timeout, legacy audit compatibility and
  all failure taxonomy branches.
- Generator checks prove the Cursor marker comes only from `cursor/install.mjs` and that the tracked
  artefact is fresh.
- The benchmark selects exactly the PreToolUse catch-all and Bash matcher groups from
  `hooks/hooks.json` (currently six handlers), substitutes the active plugin root and interpreter,
  and feeds a UTF-8 safe `git status` payload in a temporary Git fixture. “Cold” is the first
  process invocation for each handler; three unrecorded warm-ups precede 20 recorded samples.
  It records individual and sequential-chain p50/p95 with `perf_counter_ns`.
- Benchmark JSON is `{version, platform, python, handlerCount, warmups, samples, handlers[], chain}`;
  each metric object contains `coldMs`, `p50Ms`, `p95Ms` and `failures`. The report-only Windows job
  may fail for script errors, a handler count other than six, nonzero handler results or malformed
  output, but never for latency. The JSON is CI evidence printed to the job log, not runtime
  telemetry and not retained by a hook.
- Final verification runs every repository gate declared in `AGENTS.md` and the project verify
  supplement.

## Assumptions

- No assumptions. The user explicitly selected the recommended options, and current official
  lifecycle facts were rechecked against primary sources.

## Out of scope

- Git-native hooks for human terminal commits; reopen only if the user requests coverage outside
  agent lifecycle events.
- Staged-snapshot execution; reopen only when a real project requires commit-object-only gates.
- Structured telemetry; reopen after a concrete incident defines required fields, retention,
  rotation and sanitization.
- A PreToolUse dispatcher; reopen only if Windows and Linux evidence show material overhead and
  parity tests define the migration threshold.
- `PostToolBatch`, `TaskCompleted`, `SubagentStop` or `StopFailure` registrations; reopen only with a
  concrete blockable incident and confirmed semantics for each target client.

## Not yet specified

No fog: the path to the destination is closed.

## Rollback

- Revoke or remove the machine-local trust entry to stop every configured automatic command.
- Set `gates.preCommit.enabled` false to disable core commit gates while retaining the legacy audit.
- Delete `.graph-powers/cache/precommit-verification.json`; it is disposable and rebuilt on demand.
- Remove the generated Cursor marker transformation and regenerate the tracked Cursor manifest.
- Revert the shared manifest/schema/runtime change and rerun the official Codex, Cursor and Grok
  generators/checkers; Codex and Grok have no separate hand-maintained Stop artefact to edit.
- Remove `Path.home()/.graph-powers/command-trust.json` or revoke individual entries; the registry
  has no repository-schema migration and older plugin versions simply ignore it.
- The benchmark job is report-only and can be removed without changing runtime hooks.

## References

- User-provided “Evolução dos Hooks do Graph Powers” source prompt (session attachment)
- `docs/plans/2026-08-24-verify-runtime-performance.md`
- `references/shared/110-guardrails-index.md`
- `references/shared/125-change-set.md`
