# Audit — graph-powers — 2026-08-27

**Scope:** diff against `main` (`7c2df934ba5aeb486d817d3b4dff5bcc28af25cf`)
**Gates at audit time:** `python3 hooks/test_hooks.py` → PASS; `python3 .github/test_hook_clients.py` → PASS; `claude plugin validate .` → PASS; `bun .github/check_workflows.mjs` → PASS; `bun .github/check_codex_policy.mjs` → PASS; `python3 .github/check_codex_native.py` → PASS; `python3 .github/check_cursor.py` → FAIL (tracked Cursor artefact is stale); `python3 .github/check_version_bump.py` → FAIL (9 shipped files changed while version remains 1.12.1); GitHub CI → FAIL (`gates`, `cursor`, `clone`)
**Repository shape:** 59 tracked Python/JavaScript source artefacts · 20 test/check artefacts · 4 commits in the PR

## Findings

| # | Sev | Dimension | Location | Defect | Failure scenario |
|---|-----|-----------|----------|--------|------------------|
| 1 | P1 | D7 | `hooks/hooks-cursor.json:30-32`; `cursor/install.mjs:98-101` | The tracked Cursor hook package is stale, and the generator does not add the client discriminator required by `stop_verify.py`. | `check_cursor.py` fails now; after a lint failure Cursor receives Claude's `decision` response instead of `followup_message`, so its bounded repair loop is not engaged. |
| 2 | P1 | D7 | `.github/workflows/ci.yml:164-166,399-405,528-534` | CI still encodes the previous 14-registration contract and creates partial Cursor fixtures that omit the verifier's required package files. | The `gates`, `cursor`, and `clone` jobs fail before they can certify the release. |
| 3 | P1 | D7 | `bin/verify-hook-clients.py:32,241-273` | Hook-target discovery does not match Cursor's quote-prefixed relative commands (`"hooks/name.py"`), so the missing-script check sees an empty set. | A package can contain the manifest and planning files but no hook implementation files and still pass `inspect_package`; only the separate `git_commit_gate.py` probe can catch one missing target, while Stop and other guards remain absent. |
| 4 | P1 | D8/D7 | `bin/hook-client-verifier.mjs:41-45`; `bin/verify-hook-clients.py:86-120` | Client verification hardcodes the `python3` executable. | On Windows, a supported Python installation exposed as `python.exe` or `py -3` cannot verify a package, so install/update paths fail even though Python 3.10+ is present. |
| 5 | P1 | D7 | `package.json:3`; `.claude-plugin/plugin.json:3`; `.github/check_version_bump.py` | Shipped hook/config changes were added after the 1.12.1 release without a version bump. | Installed machines compare versions, so these changes are rejected as not shipped; the version gate fails with nine changed shipped files. |
| 6 | P1 | D3/D7 | `hooks/commit_audit_gate.py:219-224,312-318` | The dispatcher computes the full worktree fingerprint even when `preCommitAudit.cache` is false. | On a large repository with a short audit timeout, fingerprinting consumes the deadline and the declared audit is skipped fail-open without ever launching. |
| 7 | P2 | D3 | `hooks/stop_verify.py:35`; `hooks/_change_set.py:22-24,330-380`; `hooks/hooks.json:110-117` | Stop's 30-second lifecycle budget is smaller than the possible 10-second Git status assessment plus 25-second lint run, while the fingerprint path can also spend 15 seconds per gate. | A slow but valid repository can be terminated before a result is emitted; the verifier then fails open and repeated Stop events can redo the work. |
| 8 | P2 | D3 | `hooks/_change_set.py:283-305,330-380` | Fingerprints include only the first executable's bytes, not scripts or modules supplied as command arguments outside the repository. | A cached `python3 /opt/lint.py` success remains valid after `/opt/lint.py` changes to fail, so a later commit can reuse stale green verification. |
| 9 | P2 | D9 | `.github/check_codex_policy.mjs:13-36`; `.github/check_codex_native.py:23-40`; `.github/check_codex.py:15-32` | The canonical semantic policy and read-only set are copied into three independent checker oracles. | A policy change requires synchronized edits or a stale checker blocks release; synchronized stale values can certify the same wrong routing in every lane. |
| 10 | P1 | D9 | `bin/verify-hook-clients.py:1-1119` | A new verifier monolith crosses the 1,000-line structural threshold without a PR-body justification. | Discovery, package validation, posture parsing, probing, and CLI output share one oversized module, so changes to one client path can regress unrelated clients and fail the structural approval bar. |
| 11 | P2 | D3/D7 | `hooks/_change_set.py:432-467`; `AGENT_SETUP.md:1854-1859` | The verifier writes `.graph-powers/cache/precommit-verification.json`, but the setup playbook does not tell host projects to ignore that path. | In a host repository without its own ignore rule, `git add . && git commit` can stage the hook's generated cache, and Stop's ordinary change collector sees it as a persistent change. |

## What was dropped

No agent reached its 15-finding cap. The fallback review sessions were not used as independent evidence after one violated the read-only contract and wrote temporary source edits; the findings above were re-opened and verified against clean `HEAD`.

## Not audited

The PR variant did not run browser/UI checks, frontend journeys, database-state checks, or a full documentation/missing-flow audit. The code-review skill lens was unavailable in this Zed runtime. The repository code graph was unavailable (`.code-review-graph/graph.db` missing), so impact/risk graph queries were skipped. No external dependency advisory lookup was needed; no new runtime dependency was added.

## Recommended order

1. Repair and regenerate the Cursor artefacts, update the CI fixtures/count contract, and bump all release manifests together; these are immediate red gates.
2. Fix package verification to validate exact event/matcher/command identities, all transitive hook modules, and the expected source version before any permissive posture is enabled.
3. Close the trust boundary: use a portable interpreter resolver, prevent an autonomous agent from self-approving command trust, and remove Unicode-normalization identity collisions.
4. Make Git verification recognize canonical global options and align its lifecycle budget with status/fingerprint/lint work; do not skip a declared gate merely because caching is disabled.
5. Split the verifier and centralize model-policy/checker data, then add regression cases for the failure scenarios above.
