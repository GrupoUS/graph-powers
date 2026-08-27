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

## Round 2 — 2026-08-25 · Node/tsc and unbounded workers

**Hypothesis:** the old defaults optimized wall-clock time (`bun test --parallel`) but not machine
health; one worker per CPU core and TypeScript's default checker pool can increase peak RAM. Bare
`tsgo` also follows a Node shebang, contradicting a no-Node gate policy.

**Change:** serial `bun test --smol`, changed-only fail-fast loops, tsgo forced through Bun with one
checker, and a hook deny for Node tests, legacy tsc, bare tsgo, and unbounded Bun workers. Project-
wide gates move to phase/final boundaries instead of every task.

**Measurement:** hook cases cover explicit and package-script-hidden forbidden executors, bounded
Bun forms, and the safe tsgo-through-Bun launcher. Official rationale and commands live in
`references/low-resource-js-ts-gates.md`.

**Verdict:** kept. `python3 hooks/test_hooks.py` returned `EVERY GUARANTEE HELD`.

## Round 3 — 2026-08-26 · fold JS/TS gates into the debugger

**Hypothesis:** the standalone gate skill duplicated the debugger/TDD verification path, while
removing it without redirecting every consumer would leave runtime paths dangling.

**Change:** moved the low-resource guide, Turbo EPIPE guide, wrapper and round history under
`skills/debugger/`; kept `references/shared/130-bun-tsgo-gates.md` as the single execution policy;
removed the standalone skill; redirected the debugger agent, `/debug`, `/verify`, TDD, guardrails,
templates and operator docs. The debugger description now carries concrete trigger symptoms.

**Measurement:** `quick_validate.py skills/debugger` exited 0 with no warning, while the removed
path exited 1. Wiring checked 233 routing references and 12 agents with 0 unresolved or
unregistered. Listing cost was 9,784 / 10,752 characters. The first context run exposed an 87,396 B
`/debug` floor; marking TDD and review feedback as the conditional loads they already were reduced
it to 60,202 B and the total floor to 294,440 / 300,000 B. Portability reported 0 problems and the
hook suite returned `EVERY GUARANTEE HELD`.

**Verdict:** kept. The focused graph has zero references to the removed skill. Isolated trigger
hit-rate remains unmeasured; this round did not dispatch evaluation agents.

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
