# Hermes native plugin integration

**Date:** 2026-08-31  
**Branch:** `codex/gauntlet`  
**Baseline:** `b00d038`  
**Tier:** L6  
**Risk surface:** `ci`, `env`, and public client integration

## Destination

Graph Powers has one native Hermes package at the repository root. Hermes loads the same
repository-owned skills, agent contracts, and command documents that the other clients project
from the Claude source tree. No personal Hermes directory is a source, and Hermes receives no
claim that Claude hook guardrails execute there.

## Restated requirements

| ID | Requirement | Acceptance signal |
|---|---|---|
| R1 | Hermes discovers, installs, enables, inspects, and doctors the native package. | Native manifest/entrypoint, versioned package, and `hermes plugins doctor <root> --ci`. |
| R2 | Hermes projection has a generator and no hand-maintained inventory. | `hermes/install.mjs` derives manifest and registration plan from repository sources; check is idempotent. |
| R3 | Every `skills/*/SKILL.md` and `agents/*.md` is namespaced by Hermes. | `graph-powers:<skill>` and `graph-powers:agent-<agent>` resolve to package files. |
| R4 | Every command document is available through a Hermes-supported namespaced skill surface. | `commands/<name>.md` becomes `graph-powers:<name>` through the same directory scan. |
| R5 | Hook coverage is explicit and honest. | Hermes declares no hooks; documentation and verifier report `NOT ENFORCED`. |
| R6 | Repository support is complete. | Setup/README/architecture, verifier, clone/version checks, CI, and synchronized manifests cover Hermes. |

## Triage ledger

| # | Requirement | Verdict | Evidence | Confidence |
|---|---|---|---|---:|
| 1 | R1 native package and runtime proof | KEEP | `plugin.yaml` and `__init__.py` exist, but install/registration coverage is not yet gated | 5 |
| 2 | R2 fifth generator | KEEP | Codex/Cursor/Grok have generators; no `hermes/install.mjs` exists | 5 |
| 3 | R3 skill and agent namespace | KEEP | Hermes `register_skill` derives `plugin:name`; current entrypoint scans skills/agents | 5 |
| 4 | R4 commands | KEEP | `commands/` is canonical, but current entrypoint never scans it | 5 |
| 5 | R5 hook posture | KEEP | Hermes callback APIs do not establish Claude hook payload/guardrail parity | 5 |
| 6 | R6 docs/gates/version | KEEP | Existing files mention Hermes partially; verifier, clone, CI, and architecture omit it | 5 |

## Locked decisions

1. Keep the native package at the repository root so `doctor . --ci` exercises the same checkout
   that contains the canonical sources.
2. `__init__.py` remains directory-driven. It will scan Hermes-only translation content, canonical
   skills, command documents, and agent contracts; it will not contain a list of names.
3. Commands use their source stem as the Hermes skill name (`plan` becomes `graph-powers:plan`). A
   collision is an error in the generated registration plan rather than a silent replacement.
4. `hermes/install.mjs` generates the Hermes manifest from `.claude-plugin/plugin.json` and checks
   the source-derived registration plan. It does not create a second source tree or rewrite the
   canonical documents.
5. Choose hook option B: `provides_hooks: []` and `NOT ENFORCED`. The parent Hermes safety contract
   and approvals remain advisory/documentary until an upstream payload-compatible proof exists.
6. The verifier runs static registration checks and Hermes Doctor when the Hermes executable is
   available. An unavailable executable is reported as `SKIPPED (runtime not installed)`, never as
   an unqualified pass.

## External compatibility note

The Hermes version installed on this machine scans a Git clone before installation. Its scanner
currently classifies intentional guardrail examples and agent-governance prose in the full Graph
Powers repository as dangerous, and `--force` cannot override that verdict. This implementation
must not weaken that security setting or disguise the result. The local acceptance matrix records
the scanner result separately from native package/Doctor proof; making the default root Git install
pass with scanning enabled requires an upstream Hermes scanner policy/allowlist and is not solved by
rewriting or hiding Graph Powers source files.

## Out of scope

- Upstream Hermes changes or a personal `HERMES_HOME` adapter.
- Product-specific content or NeonDash behavior.
- Translating Claude `hooks/hooks.json` without a proven Hermes payload contract.
- Commits, pushes, merges, releases, or publication.
