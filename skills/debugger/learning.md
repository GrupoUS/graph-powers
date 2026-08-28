# learning.md — round history for `graph-powers:debugger`

## Round 1 — 2026-08-24 · turbo `--dry=json` EPIPE abort

**Hypothesis:** agents invent `turbo run test --dry=json` to inspect the graph; documenting the
safe form in SKILL.md is not enough because they will not load the skill first.

**Change:** [HARD] rule + `scripts/turbo_dry_json.py` in this skill; deny in
`hooks/smart_bash_approver.py` so the crashing argv cannot run even when the debugger skill is not
loaded. Detail in `references/turbo-dry-json-epipe.md`.

**Measurement:** hook suite cases for the six crashing argv (deny under autonomous and guarded)
and the five legitimate test/type-check/wrapper forms (not deny). Script in an empty directory:
non-zero, stdout does not start with `{`.

**Verdict:** kept. The hook is the prevention; the skill is the replacement. A prose-only rule
would have been Round 0 of the same crash.

## Round 2 — 2026-08-28 · Oxc + Zed toolchain

**Hypothesis:** the plugin can keep one small JavaScript/TypeScript path when formatting, editor
diagnostics, and final validation each have one explicit owner.

**Change:** Oxlint owns diagnostics, Oxfmt owns formatting, and vtsls is the only TypeScript editor
provider using its bundled compatible TypeScript SDK. The local TypeScript 7 package is reserved for
the explicit compiler gate. Edit hooks stay changed-file-only and never run type-aware analysis;
`/verify`, commit and CI may run the bounded type-aware Oxlint gate.

**Compatibility:** TypeScript 7 does not ship the legacy `tsserver.js` that vtsls expects. Pointing
vtsls at the local TypeScript 7 `lib` directory produces a fallback warning. The project template
uses the bundled compatible SDK and disables `autoUseWorkspaceTsdk`; setup preserves explicit user
settings and reports the boundary instead of silently deleting them or adding a second provider.

**Measurement:** `python3 hooks/test_hooks.py` returned `EVERY GUARANTEE HELD`; Oxc/Zed policy and
all repository wiring gates remain part of the final verification.

**Verdict:** pending final repository gates for this migration.

## Round 4 — 2026-08-27 · render health stays a capability, not a second debugger

**Hypothesis:** React health scans need one optional capability inside the existing frontend pack;
copying a vendor skill or playbook would duplicate `/perf doctor`, the root-cause engine and project
gates while coupling every host to one scanner.

**Change:** scanner-led cleanup now routes to `/perf doctor`; a concrete React incident may run the
host-declared `tooling.commands.renderHealth` only after its reproducer exists. Findings feed ranked
hypotheses, never automatic fixes, and a missing command skips the debugger/verify probe without
installation. `/perf doctor` owns the atomic remediation loop and keeps its project-script fallback
local; the schema names all three consumers without adding a mode, reference, script or dependency.

**Measurement:** three new behaviour cases were captured against the previous skill and all exited 1
under `--threshold 1.0`: T06 lacked the `/perf doctor` route, T07 lacked probe ordering and evidence
semantics, and T08 lacked the explicit no-install skip. Against the revised skill, T06, T07 and T08
all scored 100% and exited 0. The first GREEN run exposed four prose checks too narrow for a correct
Portuguese response; after replacing phrase checks with action-bound assertions, the same RED
artefacts still failed 3/3 and the GREEN artefacts passed 3/3. Three adversarial responses containing
the expected keywords while choosing the wrong route, appending `--fix`, making gates unnecessary or
recommending installation also failed 3/3.

**Verdict:** kept. One configured command extends the existing method; absence removes only the
optional evidence source. No React Doctor version, flag catalogue, output parser or remote prompt
entered the plugin.
