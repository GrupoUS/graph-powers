export const meta = {
  name: 'ultra-verify',
  description: 'Adversarial loop-until-done verification of the working tree vs the plan: gates+scope → simplify (folds dead-code cleanup) → multi-lens skeptics (folds the perf scan) → completeness → bounded fix loop (root-cause first, re-patch cap). Combats self-preferential bias, agentic laziness and goal drift. Token-lean: skeptics bracket the loop rather than running per round, folded checks are surface-gated, an empty diff exits early, and the final confirm re-runs only the lenses that flagged. Commits nothing.',
  whenToUse: 'After /implement, to verify the working tree against the approved plan before committing. Pass { planPath, config }, or the plan path as a plain string; args.deep enables the networked render-health scan when the project declares one. Always terminates (max rounds + re-patch cap); never commits.',
  phases: [{ title: 'Gates', model: 'haiku' }, { title: 'Simplify' }, { title: 'Adversarial verify' }, { title: 'Completeness' }, { title: 'Fix loop' }],
}

// ── Design notes (read before editing) ───────────────────────────────────────
// After editing, run `node .github/check_workflows.mjs`. Top-level `return` is legal only because
// the runtime wraps the body, so `node --check` and most linters reject this file outright.
//
// This file ships inside the plugin and runs in repositories nobody here has seen. Nothing in it
// may name a product, a stack, a package manager, a provider or a directory layout — all of that
// arrives through `config` and traces back to `schema/config.schema.json`. The project's own
// invariants and extra review lenses arrive the same way: this workflow supplies the mechanism,
// the project supplies the content, and a project that declares neither still gets the full
// generic pass.
//
// This workflow IS the orchestration. Sub-agents must NOT invoke a process skill that dispatches
// agents — those re-fan-out and the spawn count explodes. Skeptics and fixers READ the debugging
// anti-pattern catalogue for the checklist and report or fix directly.
//
// Cost shape (the adversarial skeptic panel is the heaviest repeated cost):
//   - Skeptics run ONCE up front + ONCE after the loop converges (to catch fix-induced
//     regressions) — NOT per round. Intermediate rounds drive on the cheap objective pair
//     (gates + completeness). The final confirm re-runs ONLY the lenses that flagged.
//   - Empty change set → early exit (gates only); nothing to simplify, skeptic or complete.
//   - The folded perf and dead-code passes are surface-gated by ONE haiku `scope` agent running in
//     parallel with gates: an untouched surface spawns ZERO extra work.
//   - Fix fan-out is capped per round, and a non-converging item is dropped after it fails its
//     gate `maxRepatch` times (reported `blocked`, not looped to the round ceiling).
//
// Why the Simplify phase REPLICATES a simplify pass instead of calling a skill (do not "fix"):
//   1. A bundled `/simplify` fans out its own parallel agents — an inner call is exactly the
//      re-fan-out the note above forbids. The prompt below mirrors its four angles.
//
// Model tiering: mechanical work (gates, regate, extract-reqs, scope) → 'haiku'. Judgment
// (simplify, skeptics, completeness, fixes) inherits the main-loop model — do not downgrade it.
// ─────────────────────────────────────────────────────────────────────────────

const PLAN_PATH = typeof args === 'string' ? args : (args?.planPath ?? '')
const DEEP = !!(args && typeof args === 'object' && args.deep) // opt-in: the networked render-health scan

// The plan is not optional. Without it this workflow used to fall through and ask its agents to
// verify "the plan at ``" — a prompt that reads as valid, produces confident findings about
// nothing, and costs a full skeptic panel to discover. The literal strings are what a
// template-interpolated `next` produces when the upstream path was missing.
//
// Verifying without a plan is a real thing to want, and it already has a home: `/verify` runs the
// declared gates and the safety floor. What this workflow adds is everything measured AGAINST a
// plan — requirement completeness, scope drift, the adversarial panel — and none of it means
// anything with nothing to compare to.
if (!PLAN_PATH || PLAN_PATH === 'undefined' || PLAN_PATH === 'null') {
  throw new Error(
    `ultra-verify: pass the plan path as args (got: ${JSON.stringify(PLAN_PATH)}). ` +
    'For a gates-only pass with no plan, run /verify instead.'
  )
}

// ── Agent names ──────────────────────────────────────────────────────────────
// Every subagent this workflow spawns is one the PLUGIN ships, so the name has to carry the plugin
// namespace. A bare `explorer` resolves only where the project happens to define an agent by that
// name — which is exactly how the upstream copies of this workflow were written, because there the
// agents were project files. Inside a plugin-distributed workflow the bare name is not found, and
// the run dies on the first spawn with "agent type 'explorer' not found".
//
// Namespacing also settles precedence deliberately: this workflow was written against the
// contracts of these agents (read-only frontmatter, pinned models, declared tools), so it should
// keep getting them even in a project that defines an agent of the same name.
//
// Only the plugin's own agents are prefixed. A project that names one of ITS agents — in
// `chain.lenses[].agent`, or in a plan the classifier read — must reach that agent, not a
// same-named one from here, so an unrecognised name passes through untouched.
const PLUGIN_AGENTS = new Set([
  'explorer', 'librarian', 'project-planner', 'evaluator', 'debugger', 'frontend-specialist',
  'performance-optimizer', 'mobile-developer', 'ui-ux-designer', 'security-reviewer',
  'verification', 'skill-improver',
])
// Naming, and an unresolved contradiction worth writing down rather than re-deriving.
// Measured 2026-08-20 on CLI 2.1.235: the Agent tool rejects `graph-powers:evaluator` with a valid
// list of BARE names, and rejects bare `evaluator` with an available list of PREFIXED ones. Two
// validators in series, disagreeing — so in that session no agent of this plugin could be spawned
// at all. The prefixed form is kept because it is the list that names all twelve agents and matches
// what the session advertises; if a future session proves otherwise, this helper is the only line
// to change, and `.github/check_workflows.mjs` asserts the set it draws from.
const AG = (name) => (PLUGIN_AGENTS.has(name) ? `graph-powers:${name}` : name)

// ── Model tier ───────────────────────────────────────────────────────────────
// Declared per call, never inherited (AGENTS.md cardinal 6). A workflow does NOT read the `model:`
// line of `agents/<name>.md`: `agent()` without `model` takes the SESSION model, so an opus-pinned
// specialist ran on whatever the user happened to be driving, and a haiku scout spent an opus
// window. `M()` restores the tier the agent's own frontmatter declares; a mechanical unit may still
// ask for a cheaper model explicitly (§2 of `references/shared/020-complexity-routing.md`) — that is
// a downgrade, and downgrades are written literally so they read as deliberate.
//
// The set below is a second copy of what `agents/` already says, so it is checked rather than
// trusted: `.github/check_workflows.mjs` fails a spawn that omits `model`, a set that drifts from
// the frontmatter, and a light agent pinned to a heavy model.
const LIGHT_AGENTS = new Set(['explorer', 'librarian'])
const M = (name) => (LIGHT_AGENTS.has(name) ? 'haiku' : 'opus')

// ── Config ───────────────────────────────────────────────────────────────────
// A workflow script has no filesystem: its scope is `agent`, `parallel`, `phase`, `log`, `args`
// and `budget`. The project's contract arrives passed in by the caller, or read by one cheap agent.
const CONFIG_SHAPE = { type: 'object', required: ['pluginRoot'], properties: {
  pluginRoot: { type: 'string' },
  workBranch: { type: 'string' },
  paths: { type: 'object', properties: {
    frontendRoot: { type: 'string' }, backendRoot: { type: 'string' },
    schemaRoot: { type: 'string' }, mobileRoot: { type: 'string' },
  } },
  commands: { type: 'object', properties: {
    typeCheck: { type: 'string' }, lint: { type: 'string' }, test: { type: 'string' },
    build: { type: 'string' }, deadCode: { type: 'string' }, renderHealth: { type: 'string' },
  } },
  contractGates: { type: 'array', items: { type: 'object', properties: {
    name: { type: 'string' }, command: { type: 'string' },
    when: { type: 'array', items: { type: 'string' } },
    needsServer: { type: 'string' }, runtime: { type: 'string' },
  } } },
  surfaces: { type: 'array', items: { type: 'object', properties: {
    name: { type: 'string' }, match: { type: 'string' },
  } } },
  lenses: { type: 'array', items: { type: 'object', properties: {
    name: { type: 'string' }, agent: { type: 'string' },
    when: { type: 'array', items: { type: 'string' } },
    checks: { type: 'array', items: { type: 'string' } },
  } } },
  hardRules: { type: 'array', items: { type: 'string' } },
  invariants: { type: 'array', items: { type: 'string' } },
  maxParallelWave: { type: 'number' },
  maxRepatch: { type: 'number' },
  maxFixRounds: { type: 'number' },
} }

async function resolveConfig() {
  if (args?.config) return args.config
  return await agent(
    `Two things, both read-only.

1. Locate the graph-powers plugin root — the directory that contains \`skills/debugger/references/anti-patterns.md\`. Use Glob, never a hardcoded path: it differs per machine and per install. Return it as \`pluginRoot\`, without a trailing slash. If you cannot find it, return the empty string rather than guessing.

2. Read \`.graph-powers/config.json\` at the repository root (fall back to \`.claude/config.json\`, then to an empty object — a project with no config is valid and takes the defaults). Return, flattened:
     workBranch     <- git.workBranch, else "main"
     paths          <- paths.frontendRoot / backendRoot / schemaRoot / mobileRoot; omit any that is absent
     commands       <- tooling.commands.typeCheck / lint / test / build / deadCode / renderHealth; omit any that is absent
     contractGates  <- chain.contractGates, else []
     surfaces       <- chain.surfaces, else []
     lenses         <- chain.lenses, else []
     hardRules      <- chain.hardRules, else []
     invariants     <- chain.invariants, else []
     maxParallelWave <- graphGuardrails.maxParallelWave, else 5
     maxRepatch     <- graphGuardrails.maxRepatch, else 2
     maxFixRounds   <- chain.maxFixRounds, else 0 (0 means "let the workflow decide from its budget")

Do not invent a value that is not in the file: an absent field is absent, never a plausible default of your own.`,
    { agentType: AG('explorer'), phase: 'Gates', schema: CONFIG_SHAPE, label: 'config', model: M('explorer') }
  )
}

const cfg = (await resolveConfig()) ?? {}
const paths = cfg.paths ?? {}
const commands = cfg.commands ?? {}
const WORK_BRANCH = cfg.workBranch || 'main'
const FIX_CAP = cfg.maxParallelWave ?? 5
const REPATCH_CAP = cfg.maxRepatch ?? 2

if (!cfg.pluginRoot) {
  throw new Error('ultra-verify: could not locate the graph-powers plugin root, so no agent can read the debugging catalogue. Pass it as args.config.pluginRoot.')
}
const DBG_GUIDE = `${cfg.pluginRoot}/skills/debugger/references/anti-patterns.md`
const PERF_GUIDE = `${cfg.pluginRoot}/commands/perf.md`
const GATE_GUIDE = `${cfg.pluginRoot}/references/shared/130-bun-tsgo-gates.md`

// Same lane set as ultra-plan and planning Phase C. Kept as an enum on every `agent` field below: this
// is the one thing the upstream copies of this workflow got wrong — `agent` was a free string, so
// whatever an evaluator wrote became a `subagent_type`, and a hallucinated name either failed to
// spawn or silently degraded to a default nobody chose.
const AGENT_ENUM = [
  paths.frontendRoot && 'frontend-specialist',
  'debugger',
  'performance-optimizer',
  'evaluator',
  'ui-ux-designer',
  paths.mobileRoot && 'mobile-developer',
].filter(Boolean)

const projectRules = (cfg.hardRules ?? []).map((r) => ` ${r}`).join('')
const gateList = [commands.typeCheck, commands.lint, commands.test].filter(Boolean)
const quickTest = (command) => {
  if (!/^bun(?:\.exe)?\s+test(?:\s|$)/i.test(command)) return command
  const flags = []
  if (!/(?:^|\s)--changed(?=\s|$)/i.test(command)) flags.push('--changed')
  if (!/(?:^|\s)--bail(?:=|\s|$)/i.test(command)) flags.push('--bail=1')
  if (!/(?:^|\s)--smol(?=\s|$)/i.test(command)) flags.push('--smol')
  return [command, ...flags].join(' ')
}
const quickGateList = [commands.typeCheck, commands.lint, commands.test && quickTest(commands.test)].filter(Boolean)
// `build` is deliberately NOT in `gateList`: that list also drives REGATE, which runs after every
// fix batch, and rebuilding per round is the most expensive thing this workflow could do. It runs
// ONCE, in the opening gate pass, because a tree that type-checks can still fail to build — a
// bundler resolution error, a missing asset, a plugin that only runs at build time. Before this it
// was requested in CONFIG_SHAPE, named in the config prompt, and then consumed nowhere: a declared
// gate that silently never ran, which is the exact failure the gate table exists to prevent.
// A project wanting the build re-run per round declares it as a `chain.contractGates` entry instead.
const openingGateList = [...gateList, commands.build].filter(Boolean)
// Presented one per line, never chained: `;` is not a separator in cmd.exe, and a chained
// line makes "capture each exit code" unanswerable even where the chain does work.
const quickGateBlock = quickGateList.map((c) => `  - \`${c}\``).join('\n')
const openingGateBlock = openingGateList.map((c) => `  - \`${c}\``).join('\n')
const GIT_RAILS =
  'HARD RULES (no inherited config): never git commit/push/checkout/reset/stash. Leave changes in ' +
  'the working tree.' + projectRules +
  ' After editing, run only a focused regression check for the files you changed. Never run the whole-project gate list; the workflow owns it once per round and once at the final boundary.'
const ROOT_CAUSE = 'Name the exact root cause BEFORE patching (read ' + DBG_GUIDE + '; do NOT invoke a Skill). Fix the source, not the symptom; no "while I am here" scope creep.'
const REGATE = quickGateList.length
  ? `Read ${GATE_GUIDE} first. Re-run this low-resource gate set from the repository root. Run each as a SEPARATE command — never chained with \`;\` or \`&&\` — and capture the exit code of each:\n${quickGateBlock}\nA forbidden command is a failed gate: do not execute it and do not fall back. Read-only.`
  : 'This project declares no gate commands. Report allGreen:true with an empty gates list and say so — a project with no gates is a finding about the project, not a pass. Read-only.'

const GATES = { type: 'object', required: ['allGreen', 'gates'], properties: {
  allGreen: { type: 'boolean' },
  gates: { type: 'array', items: { type: 'object', properties: { name: { type: 'string' }, exitCode: { type: 'number' }, pass: { type: 'boolean' }, failing: { type: 'string' } } } },
} }
const FIX = { type: 'object', required: ['status'], properties: {
  status: { type: 'string', enum: ['done', 'partial', 'blocked'] }, applied: { type: 'array', items: { type: 'string' } },
  changedPaths: { type: 'array', items: { type: 'string' } }, gateEvidence: { type: 'string' },
} }
const REQS = { type: 'object', required: ['requirements'], properties: {
  requirements: { type: 'array', items: { type: 'object', properties: { id: { type: 'string' }, text: { type: 'string' }, agent: { type: 'string', enum: AGENT_ENUM } } } },
  verificationSteps: { type: 'array', items: { type: 'string' } },
} }
// SKEPTIC is declared with the lens list in § "Adversarial verify", not here: its `lens` field is an
// enum over the lenses this run actually dispatches, and that set is not known until the scope agent
// has reported which surfaces the diff touched.
const COMPLETENESS = { type: 'object', required: ['items'], properties: {
  items: { type: 'array', items: { type: 'object', properties: { id: { type: 'string' }, status: { type: 'string', enum: ['done', 'missing', 'partial'] }, evidence: { type: 'string' }, agent: { type: 'string', enum: AGENT_ENUM } } } },
  drift: { type: 'array', items: { type: 'string' } },
} }

// Surfaces: the built-in path surfaces this plugin can derive, plus whatever the project declared.
// A project that names its own surface (a payment provider, a public inventory file) gets it gated
// exactly like the built-ins, which is what keeps its existing review coverage after adoption.
const BUILTIN_SURFACES = [
  paths.frontendRoot && { name: 'web', match: `any path under ${paths.frontendRoot}/` },
  paths.backendRoot && { name: 'api', match: `any path under ${paths.backendRoot}/` },
  paths.schemaRoot && { name: 'schema', match: `any path under ${paths.schemaRoot}/` },
  { name: 'auth', match: 'any path matching /auth|session|webhook|rls|policy/' },
].filter(Boolean)
const SURFACES = [...BUILTIN_SURFACES, ...(cfg.surfaces ?? [])]
const SCOPE = { type: 'object', required: ['changedFiles', 'baseRef'], properties: {
  touched: { type: 'object', additionalProperties: { type: 'boolean' } },
  changedFiles: { type: 'array', items: { type: 'string' } },
  baseRef: { type: 'string' }, deadCodeVersion: { type: 'string' }, confidence: { type: 'string', enum: ['high', 'low'] },
} }

// 1. Gates + Scope (surface gate for the folded perf and dead-code passes) —
//    both mechanical, run in parallel (no extra wall-clock; both haiku).
phase('Gates')
const deadCodeProbe = commands.deadCode
  ? `\n3. Resolve the dead-code tool once: run \`${commands.deadCode} --version\` and return its major as \`deadCodeVersion\`; if it cannot be resolved, return the empty string.`
  : ''
const [g0, scope] = await parallel([
  () => agent(
    openingGateList.length
      ? `Read ${GATE_GUIDE} first. Run these gates from the repository root. Run each as a SEPARATE command — never chained with \`;\` or \`&&\` — and capture the exit code of each:\n${openingGateBlock}\nA forbidden command is a failed gate: do not execute it and do not fall back. Report pass/fail per gate with exit code + failing lines. Read-only — do NOT fix here.`
      : `This project declares no gate commands in its config. Return allGreen:true with an empty gates list, and note in \`failing\` that no gate was declared. Read-only.`,
    { agentType: AG('debugger'), phase: 'Gates', schema: GATES, label: 'gates', model: 'haiku' }
  ),
  () => agent(
    `Compute the working-tree change set + the surfaces it touches, for surface-gating the downstream checks. Read-only — run git, do NOT edit.
1. Resolve the change set with this 3-tier base detection:
   a) \`git diff --name-only HEAD\` (the normal post-build state — the build writes the working tree and does not commit). Set baseRef="HEAD".
   b) If (a) is EMPTY (the environment auto-committed the build): run \`git merge-base origin/${WORK_BRANCH} HEAD\` ON ITS OWN, read the SHA it prints, then run \`git diff --name-only <that-SHA> HEAD\` — the branch's cumulative diff vs its fork point. Do NOT use \`$(...)\` substitution: it is POSIX syntax, and cmd.exe passes it through as literal text. Set baseRef to that SHA.
   c) If merge-base fails (no local origin/${WORK_BRANCH} ref): fall back to \`git diff --name-only HEAD~1 HEAD\`, baseRef="HEAD~1", confidence="low".
   d) If (a) and (b) are BOTH non-empty, UNION them. confidence="high" unless (c) was used.
2. Return \`touched\` as an object with one boolean per surface below, keyed by its name:
${SURFACES.map((s) => `   ${s.name} = ${s.match}`).join('\n')}${deadCodeProbe}
Return changedFiles (the union), touched, baseRef, confidence. Empty diff → changedFiles:[] and every boolean false.`,
    { agentType: AG('explorer'), phase: 'Gates', schema: SCOPE, label: 'scope', model: M('explorer') }
  ),
])
let g = g0
const sc = scope ?? { changedFiles: [], baseRef: 'HEAD', touched: {}, confidence: 'low' }
const touched = sc.touched ?? {}
const scopeOut = () => ({ confidence: sc.confidence ?? 'low', deep: DEEP, touched })

// A plan with an empty change set means the build implemented none of it. Walking every
// requirement to conclude "all missing" costs an evaluator and a full skeptic panel to reach an
// answer already visible here, so it short-circuits — and it does NOT report VERIFIED, which is
// what an empty diff would otherwise look like to a gates-only check.
//
// Guarded on `scope` being truthy: a scope agent that died returns null, and the empty fallback
// must not be mistaken for a genuinely empty tree.
if (scope && (sc.changedFiles?.length ?? 0) === 0) {
  return {
    verdict: 'NEEDS-WORK',
    rounds: 0,
    reason: 'The working tree is unchanged, so nothing in the plan was implemented. Verifying it would report every requirement missing, one expensive agent at a time.',
    gates: g?.allGreen ? 'green' : 'RED',
    gateDetail: g?.gates ?? [],
    missing: [], openFindings: [], unconfirmed: [], blocked: [], drift: [], scope: scopeOut(),
    next: 'Run the build for this plan first, or check whether the environment committed the changes out from under the diff.',
  }
}

const sourceSurface = !!(touched.web || touched.api)
const perfApiSurface = !!(touched.api || touched.schema)

// Conditional contract gates: commands a project runs only when a given surface changed. This is
// how a repository keeps the checks it already had — a link-inventory check, a smoke test, a build
// that only matters when the public site moved — without any of them being named in this file.
const firedGates = (cfg.contractGates ?? []).filter(
  (cg) => !cg.when?.length || cg.when.some((w) => touched[w])
)
if (firedGates.length) {
  log(`Contract gates fired by the touched surfaces: ${firedGates.map((cg) => cg.name).join(', ')}`)
  const extra = await agent(
    `Run these additional project gates and capture each exit code. They are declared by the project, not by this workflow; run each exactly as written. Read-only — do NOT fix.
${firedGates.map((cg) => `- ${cg.name}: ${cg.command}${cg.needsServer ? ` (needs a server: start \`${cg.needsServer}\` in the background, run the gate, then terminate that process — \`taskkill /PID <pid> /T /F\` on Windows, \`kill <pid>\` elsewhere. Say so if you cannot stop it: a server left holding the port makes the NEXT gate fail for the wrong reason)` : ''}${cg.runtime ? ` (run under ${cg.runtime}, not the project's default runtime)` : ''}`).join('\n')}`,
    { agentType: AG('debugger'), phase: 'Gates', schema: GATES, label: 'contract-gates', model: 'haiku' }
  )
  if (extra) {
    g = {
      allGreen: !!(g?.allGreen) && !!extra.allGreen,
      gates: [...(g?.gates ?? []), ...(extra.gates ?? [])],
    }
  }
}

// 2. Simplify — a quality pass on the diff (no behavior change, no bug hunt), plus a
//    diff-scoped dead-code sweep when the project declares a tool and source was touched.
phase('Simplify')
const invariantClause = (cfg.invariants ?? []).length
  ? `\nPROJECT INVARIANTS — never "simplify" any of these away. They look redundant and are HARD requirements; report the skip instead of removing it:\n${(cfg.invariants ?? []).map((i) => `- ${i}`).join('\n')}`
  : ''
const deadCodeClause = (commands.deadCode && sourceSurface)
  ? `\nTHEN run a diff-scoped dead-code sweep with the tool this project declared: \`${commands.deadCode}\`. INTERSECT its findings with the changed files (${JSON.stringify(sc.changedFiles)}) and remove ONLY grep-confirmed cascade-orphans THIS diff created (imports, vars and exports left dangling by the change). IRON LAWS: never touch the dependency manifest; honor the tool's own allowlist file if one exists; such tools typically do NOT count test files as consumers, so search the whole repository with the **Grep tool** (tests and dynamic imports included) before deleting anything — do not shell out to \`grep\`, which does not exist on every platform this runs on.`
  : ''
await agent(
  `Replicate a simplify pass on the working-tree diff (git diff). Review ONLY changed code, through these four angles, then apply safe quality-only cleanups — do NOT change behavior, do NOT hunt for bugs (that is the skeptics' job):
- REUSE: flag new code that re-implements something the codebase already has — search shared/utility modules and files adjacent to the change with the Grep tool, and name the existing helper to call instead.
- SIMPLIFICATION: flag unnecessary complexity the diff adds — redundant or derivable state, copy-paste with slight variation, deep nesting, dead code left behind. Name the simpler form that does the same job. Remove only dead code THIS diff created; pre-existing dead code is flagged, never deleted.
- EFFICIENCY: flag wasted work the diff introduces — redundant computation or repeated I/O, independent operations run sequentially, blocking work added to startup or hot paths. Also flag long-lived objects built from closures or captured environments (they keep the whole enclosing scope alive — a leak when that scope holds large values); prefer a structure copying only the fields it needs. Name the cheaper alternative.
- ALTITUDE: check each change is implemented at the right depth, not as a fragile bandaid. Special cases layered on shared infrastructure mean the fix is not deep enough — prefer generalizing the underlying mechanism over adding special cases.${invariantClause}${deadCodeClause} ${GIT_RAILS}
Return applied changes + gate evidence.`,
  { agentType: AG('debugger'), phase: 'Simplify', schema: FIX, label: 'simplify', model: M('debugger') }
)

// 3. Adversarial verify (fan-out skeptics) — combat self-preferential bias
phase('Adversarial verify')
const reqs = await agent(
  `Read the plan at ${PLAN_PATH}. Extract the flat requirement list (R1..Rn) from the acceptance criteria + the ## Verification steps. Read-only.`,
  { agentType: AG('explorer'), phase: 'Adversarial verify', schema: REQS, label: 'extract-reqs', model: M('explorer') }
)
// Lenses are distinct QUESTIONS, never the same question asked N times — identical skeptics agree
// with each other and miss the same things. Spec compliance is deliberately absent: the
// Completeness phase already walks every requirement against the diff.
// Each lens is surface-gated: on a diff that never touches that surface it would burn a spawn to
// report nothing, which is exactly the fan-out the stop rule forbids.
const BUILTIN_LENSES = [
  { name: 'correctness', agent: 'evaluator', when: [] },
  { name: 'security-tenant-PII', agent: 'security-reviewer', when: [] },
  // `explorer`, not `performance-optimizer`: a lens is a SKEPTIC and skeptics only report, while
  // that specialist resolves with `Write` and `Edit` and no `disallowedTools`. Handing review work
  // to a write-capable agent is the incident recorded in the debugging anti-pattern catalogue, and
  // a prose "report only" is a request rather than a permission. The fixers below are a separate
  // dispatch and stay write-capable, which is where that specialist belongs.
  { name: 'performance-regression', agent: 'explorer', when: [] },
  paths.frontendRoot && { name: 'design-tokens-a11y', agent: 'ui-ux-designer', when: ['web'] },
].filter(Boolean)
// `chain.lenses[].agent` stays a free string on purpose — a project must be able to name its own
// agent — but a free string that becomes a `subagent_type` and resolves to nothing spawns nothing,
// and the lens then drops out of the panel with no trace. The pass-through is kept and the silence
// is not: every lens reaching for an agent this plugin does not ship is named before the wave runs,
// so a hallucinated or misspelt value in a config an agent transcribed is visible in the log rather
// than in a verification that quietly checked one thing fewer than it reported.
const ALL_LENSES = [...BUILTIN_LENSES, ...(cfg.lenses ?? [])]
const foreignLenses = ALL_LENSES.filter((l) => l.agent && !PLUGIN_AGENTS.has(l.agent))
if (foreignLenses.length) {
  log(`lenses naming a non-plugin agent (must exist in this project, or the lens will not run): ${foreignLenses.map((l) => `${l.name}->${l.agent}`).join(', ')}`)
}
const lenses = ALL_LENSES.filter((l) => !l.when?.length || l.when.some((w) => touched[w]))

// `lens` is the key the final confirm at the bottom of this file matches findings on, and a match
// key an agent fills as free text is the same defect the comment above records for `agent`: whatever
// the model writes becomes the key. A panel member that answered `lens: "correctness lens"` matched
// no lens, the confirm re-ran nothing, and three open P0s were reported as VERIFIED. So the field is
// an enum over exactly the lenses this run dispatches — the model cannot name one nothing knows.
const LENS_ENUM = lenses.map((l) => l.name)
const KNOWN_LENS = new Set(LENS_ENUM)
const SKEPTIC = { type: 'object', required: ['lens', 'satisfied'], properties: {
  lens: { type: 'string', enum: LENS_ENUM }, satisfied: { type: 'boolean' },
  findings: { type: 'array', items: { type: 'object', properties: { title: { type: 'string' }, file: { type: 'string' }, severity: { type: 'string', enum: ['P0', 'P1', 'P2', 'P3'] }, inScope: { type: 'boolean' }, agent: { type: 'string', enum: AGENT_ENUM } } } },
} }

// Folded perf pass — only the performance-regression lens runs these, only for touched surfaces.
const perfParts = []
if (perfApiSurface) perfParts.push(`statically scan the changed files (${JSON.stringify(sc.changedFiles)}) for N+1 (a database call inside a loop), \`select *\`, and any new foreign-key column missing its index (see ${PERF_GUIDE} § 4.2-4.4)${touched.schema ? ' — run the index check even when the service layer was untouched' : ''}`)
if (DEEP && commands.renderHealth && touched.web) perfParts.push(`run \`${commands.renderHealth}\` (local/advisory) and fold render/effect regressions in`)
const perfClause = perfParts.length
  ? `\nPERF: ${perfParts.join('; ')}. SEVERITY RULE: render-health score deltas and \`select *\` are P2 (report, never auto-fix); ONLY a diff-introduced N+1 or a render loop from a missing effect dependency is P1. EXCLUDE anything needing a full build or a deployed environment.`
  : ''
// The design lens asks its own question: not "is it correct?" but "does it obey the design contract?"
const designClause = `
DESIGN CONTRACT: semantic tokens only — flag every hardcoded color literal (\`#rgb\`/\`#rrggbb\`/\`rgb()\`/\`hsl()\`) introduced by this diff in ${JSON.stringify(sc.changedFiles)}. Check WCAG AA contrast on changed surfaces, keyboard focus visibility, reduced-motion support, and that loading/empty/error states still exist where the diff touched them. SEVERITY RULE: a color literal or a lost focus ring is P1; contrast below AA on text is P1; taste and spacing preferences are P3 and never justify a fix round.`
const clauseFor = (l) => {
  if (l.name === 'performance-regression') return perfClause
  if (l.name === 'design-tokens-a11y') return designClause
  if (l.checks?.length) return `\nPROJECT CHECKS for this lens — these are the project's own, and are as binding as the generic ones:\n${l.checks.map((c) => `- ${c}`).join('\n')}`
  return ''
}

// A skeptic that is free to widen the question is a loop with no floor: every fix it demands is a
// new diff, and a new diff is a new panel. So the panel's mandate is bounded to the plan, and the
// boundary is a field the fixer reads — `inScope: false` is reported and never spawns a fixer.
const SCOPE_LOCK = `
SCOPE — this decides whether a finding can start a fix round, so apply it literally.
Set inScope: true ONLY when the finding is one of: (a) a defect this diff introduces, (b) a
regression of a row in the plan's "## Regression watchlist", or (c) something that makes the plan's
"## Destination" false. Everything else is inScope: false — a pre-existing issue the diff did not
touch, a refactor you would prefer, a hardening idea, anything matching a row under the plan's
"## Out of scope". Report those; they are useful. They do NOT become work.
Do not propose new features, new files, new abstractions, or a redesign. Do not widen the plan. The
question is "does what was built hold?", never "what else could be built".`

// P0/P1 AND in scope. `inScope` absent counts as in scope: an older lens that never learned the
// field must not go silent. Out-of-scope findings are kept for the report and logged, never
// truncated in silence — they are the panel's most useful output and its least actionable.
const actionable = (f) => (f.severity === 'P0' || f.severity === 'P1') && f.inScope !== false
const outOfScopeFrom = (arr) => (arr ?? []).flatMap((s) => (s?.findings ?? []).filter((f) => f.inScope === false))
// Findings are lifted out of the panel member that raised them, so each one has to carry that lens
// with it: the confirm pass can only clear a finding through the lens able to see it. `lensResolved`
// is the same question asked defensively — a lens name that resolves to nothing is a finding nothing
// can re-check, and one nothing can re-check stays OPEN. Unparseable never means clean.
const refutedFrom = (arr) => (arr ?? []).flatMap((s) => (s?.findings ?? []).filter(actionable).map((f) => Object.assign({}, f, {
  lens: s?.lens, lensResolved: KNOWN_LENS.has(s?.lens),
})))
// A finding has no id, and the confirm pass has to recognise the SAME finding coming back from a
// freshly spawned agent. Lens + file + title is that identity.
const findingKey = (f) => JSON.stringify([f?.lens ?? '', f?.file ?? '', f?.title ?? ''])

const skMaker = (pass, lensList = lenses) => lensList.map((l) => () => agent(
  `Adversarially verify the working tree against the plan through the "${l.name}" lens. DEFAULT to "not satisfied" when uncertain — your job is to REFUTE, not to confirm. Apply the checklist in ${DBG_GUIDE} (read it); do NOT invoke a skill — this workflow is the orchestration, report only.${clauseFor(l)}
PLAN: ${PLAN_PATH}
REQUIREMENTS: ${JSON.stringify(reqs?.requirements ?? [])}
Surface concrete failures with file:line + severity P0-P3 + inScope + which agent should fix it. Read-only.${SCOPE_LOCK}`,
  { agentType: AG(l.agent ?? 'evaluator'), phase: pass === 'final' ? 'Fix loop' : 'Adversarial verify', schema: SKEPTIC, label: `skeptic:${pass}:${l.name}`, model: M(l.agent ?? 'evaluator') }
))
let sk = (await parallel(skMaker('init'))).filter(Boolean)
const outOfScope = outOfScopeFrom(sk)
if (outOfScope.length) log(`${outOfScope.length} finding(s) outside this plan's scope — reported, not fixed: ${outOfScope.slice(0, 4).map((f) => f.title).join(' · ')}${outOfScope.length > 4 ? ` (+${outOfScope.length - 4})` : ''}`)

// 4. Completeness — every requirement vs the diff, plus drift
phase('Completeness')
const completeMaker = (round) => agent(
  `Walk EVERY requirement from the plan at ${PLAN_PATH} against the ACTUAL git diff. Mark each done (file:line) / missing / partial, and record which agent should implement any gap. Detect scope drift (changed files not cited in the plan). This is the guard against agentic laziness and goal drift. Read-only.
REQUIREMENTS: ${JSON.stringify(reqs?.requirements ?? [])}`,
  { agentType: AG('evaluator'), phase: round ? 'Fix loop' : 'Completeness', schema: COMPLETENESS, label: `completeness:${round || 0}`, model: M('evaluator') }
)
let c = await completeMaker(0)

// 5. Loop-until-done — fix → re-verify until clean or capped.
// Intermediate rounds drive on the cheap objective pair (gates + completeness); the expensive
// skeptic panel is NOT re-fanned-out per round — it brackets the loop.
phase('Fix loop')
// Which lenses have something to re-check. A panel member whose `lens` resolves to nothing yields no
// entry here — deliberately: it is not re-run, so its findings are never cleared by the confirm
// below, they are carried out open and named.
const lensesThatFlagged = (arr) => {
  const names = new Set((arr ?? []).filter((s) => (s?.findings ?? []).some(actionable)).map((s) => s.lens))
  return lenses.filter((l) => names.has(l.name))
}
const openItems = (completeness, refuted, gates) => {
  const missing = (completeness?.items ?? []).filter((i) => i.status !== 'done')
  const gateFail = !(gates?.allGreen)
  return { missing, refuted, gateFail, total: missing.length + refuted.length + (gateFail ? 1 : 0) }
}
const fixThunks = (state, round) => [
  ...state.missing.map((m) => () => agent(
    `Implement this MISSING plan item, following the conventions of the code around it. Do NOT invoke a process skill that re-dispatches agents (this workflow orchestrates). ${ROOT_CAUSE} ${GIT_RAILS}
PLAN: ${PLAN_PATH}
ITEM: ${JSON.stringify(m)}`,
    { agentType: AG(m.agent || 'debugger'), phase: 'Fix loop', schema: FIX, label: `fix-missing:${round}`, model: M(m.agent || 'debugger') }
  )),
  ...state.refuted.map((f, i) => () => agent(
    `Fix this confirmed P0/P1 finding. Apply the relevant fix pattern from ${DBG_GUIDE} (read it); do NOT invoke a skill. ${ROOT_CAUSE} ${GIT_RAILS}
FINDING: ${JSON.stringify(f)}`,
    { agentType: AG(f.agent || 'debugger'), phase: 'Fix loop', schema: FIX, label: `fix-bug:${round}:${i}`, model: M(f.agent || 'debugger') }
  )),
]
// Shared re-verify after a fix batch (used by the loop AND by the final cleanup round).
const reverify = async (round) => {
  g = await agent(REGATE, { agentType: AG('debugger'), phase: 'Fix loop', schema: GATES, label: `regate:${round}`, model: 'haiku' })
  c = await completeMaker(round)
}

const MAX_ROUNDS = cfg.maxFixRounds || (budget?.total ? 4 : 3)
// Drop a non-converging item after it fails its gate REPATCH_CAP times across rounds. The
// orchestrator respawns a fresh fixer each round, so this counter MUST live here, not in the agent
// prompt. It stops the loop burning rounds on something it cannot fix.
const keyOf = (it) => it?.id ?? it?.title ?? JSON.stringify(it)
const attempts = new Map()
const blocked = []
const dropExhausted = (it) => {
  const k = keyOf(it)
  if ((attempts.get(k) || 0) >= REPATCH_CAP) {
    if (!blocked.some((b) => keyOf(b) === k)) blocked.push({ ...it, blocked: 're-patch limit' })
    return false
  }
  return true
}
let round = 0
let state = openItems(c, refutedFrom(sk), g)
while (state.total > 0 && round < MAX_ROUNDS) {
  round++
  state.missing = state.missing.filter(dropExhausted)
  state.refuted = state.refuted.filter(dropExhausted)
  if (state.missing.length + state.refuted.length === 0) break // only gate failures / exhausted items remain
  const thunks = fixThunks(state, round)
  const deferred = thunks.length - Math.min(thunks.length, FIX_CAP)
  log(`Fix round ${round}/${MAX_ROUNDS}: ${state.missing.length} missing · ${state.refuted.length} P0/P1 · gates ${g?.allGreen ? 'green' : 'RED'}${blocked.length ? ` · ${blocked.length} blocked (re-patch cap)` : ''}${deferred ? ` · deferring ${deferred} past the spawn cap of ${FIX_CAP}` : ''}`)
  for (const it of [...state.missing, ...state.refuted].slice(0, FIX_CAP)) attempts.set(keyOf(it), (attempts.get(keyOf(it)) || 0) + 1)
  // Each round reads the tree the previous round wrote, so the loop is serial by construction.
  // oxlint-disable-next-line no-await-in-loop
  await parallel(thunks.slice(0, FIX_CAP))
  // oxlint-disable-next-line no-await-in-loop
  await reverify(round)
  // Skeptics are not re-run mid-loop; refuted is cleared and re-checked by the final pass.
  state = openItems(c, [], g)
}

// 6. Final adversarial pass — catch regressions the fixes introduced (skeptics bracket the loop).
let openFindings = []
let unconfirmed = [] // open findings no lens re-checked — carried to the caller, never quietly dropped
if (round > 0) {
  const finalSk = (await parallel(skMaker('final'))).filter(Boolean)
  openFindings = refutedFrom(finalSk)
  if (openFindings.length && round < MAX_ROUNDS) {
    round++
    log(`Final skeptic pass found ${openFindings.length} P0/P1 — one bounded cleanup round.`)
    await parallel(fixThunks({ missing: [], refuted: openFindings }, round).slice(0, FIX_CAP))
    await reverify(round)
    // Token-lean confirm: re-run ONLY the lenses that flagged. The cleanup touched exactly those
    // findings; clean lenses were just verified, and re-running them is duplicate work.
    //
    // What the confirm is allowed to DO with the answer is the part that has to be exact. It used to
    // OVERWRITE `openFindings` with whatever came back, which makes every kind of silence read as
    // "all clear": a lens name that matched nothing, an empty re-run list, an agent that died. That
    // is how three open P0s left this workflow as `VERDICT: VERIFIED`. It now INTERSECTS — a finding
    // stays open unless the lens that raised it ran again and did not raise it again. Clearing is a
    // positive act; the absence of a match is not evidence of a fix.
    const confirmLenses = lensesThatFlagged(finalSk)
    const confirmRuns = await parallel(skMaker('final', confirmLenses))
    // A lens counts as re-run only when its agent came back AND identified itself as that lens. A
    // dead agent and a mis-identified panel member both mean "not checked", never "fixed".
    const reran = new Set(confirmLenses.filter((l, i) => confirmRuns[i]?.lens === l.name).map((l) => l.name))
    const confirmed = refutedFrom(confirmRuns.filter(Boolean))
    const stillFlagged = new Set(confirmed.map(findingKey))
    const carried = openFindings.filter((f) => !reran.has(f.lens) || stillFlagged.has(findingKey(f)))
    const carriedKeys = new Set(carried.map(findingKey))
    // Union, not replacement: what the cleanup failed to fix, plus anything the cleanup introduced.
    openFindings = [...carried, ...confirmed.filter((f) => !carriedKeys.has(findingKey(f)))]
    unconfirmed = openFindings.filter((f) => !f.lensResolved || !reran.has(f.lens))
    if (unconfirmed.length) {
      log(`${unconfirmed.length} finding(s) no lens could re-check after the cleanup round — kept OPEN: ${unconfirmed.map((f) => `${f.title} (lens ${JSON.stringify(f.lens)}${f.lensResolved ? ', not re-run' : ', unknown to this run'})`).join(' · ')}`)
    }
  }
} else {
  openFindings = refutedFrom(sk) // no fix rounds ran → the init panel already reflects the final tree
}

// Intermediate rounds use changed-only Bun tests when possible. Once every write is finished, the
// full declared gate set runs exactly once against the final tree; otherwise a quick green loop could
// be mistaken for a final verdict, or a passing opening build could survive fixes that broke it.
if (round > 0 && openingGateList.length) {
  g = await agent(
    `Read ${GATE_GUIDE} first. Run the FINAL gate set once from the repository root, each as a separate command:\n${openingGateBlock}\nA forbidden command is a failed gate: do not execute it and do not fall back. Capture every exit code. Read-only.`,
    { agentType: AG('debugger'), phase: 'Fix loop', schema: GATES, label: 'gates:final', model: 'haiku' }
  )
}

const missing = (c?.items ?? []).filter((i) => i.status !== 'done')
const totalOpen = missing.length + openFindings.length + (g?.allGreen ? 0 : 1)
// `VERIFIED` requires `totalOpen === 0`, so a non-empty `openFindings` can never reach it — that is
// the invariant, and it is why the confirm above may not overwrite that list.
// The second half is the softer leak: `VERIFIED-WITH-NOTES` is for a green tree carrying residual
// P1 observations, and a still-open P0 is not a note. Neither is a finding nothing re-checked. The
// caller reads this one field to decide whether to commit, so both route to NEEDS-WORK.
const hardOpen = openFindings.some((f) => f.severity === 'P0') || unconfirmed.length > 0
const verdict = totalOpen === 0 ? 'VERIFIED' : (g?.allGreen && !hardOpen ? 'VERIFIED-WITH-NOTES' : 'NEEDS-WORK')
return {
  verdict,
  rounds: round,
  capped: totalOpen > 0 && round >= MAX_ROUNDS,
  gates: g?.allGreen ? 'green' : 'RED',
  gateDetail: g?.gates ?? [],
  missing,
  openFindings,
  unconfirmed, // a subset of openFindings: raised, never re-checked. Not a pass — an unanswered question
  blocked, // items dropped after hitting the re-patch cap — these need a human, not another round
  outOfScope, // real findings the panel raised past this plan's edge: reported, never fixed here
  drift: c?.drift ?? [],
  scope: scopeOut(),
  next: verdict === 'VERIFIED'
    ? 'Review the working tree. The workflow never commits; the caller decides.'
    : `Address the listed gaps and findings${blocked.length ? ' (including the re-patch-capped items, which need manual root-cause work)' : ''}, then re-run ultra-verify.`,
}
