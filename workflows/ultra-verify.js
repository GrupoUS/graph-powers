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

// ── Config ───────────────────────────────────────────────────────────────────
// A workflow script has no filesystem: its scope is `agent`, `parallel`, `phase`, `log`, `args`
// and `budget`. The project's contract arrives passed in by the caller, or read by one cheap agent.
const CONFIG_SHAPE = { type: 'object', required: ['pluginRoot', 'scoutAgents', 'agentModels', 'evaluatorCapability'], properties: {
  pluginRoot: { type: 'string' },
  scoutAgents: { type: 'array', minItems: 1, items: { type: 'string' } },
  agentModels: { type: 'object', minProperties: 1, additionalProperties: { type: 'string', minLength: 1 } },
  evaluatorCapability: { type: 'string', enum: ['SUPPORTED', 'UNSUPPORTED', 'UNKNOWN'] },
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
  maxSpawnsPerWorkflow: { type: 'number' },
  maxRepatch: { type: 'number' },
  maxFixRounds: { type: 'number' },
} }
const SCOUT_POLICY_SHAPE = { type: 'object', required: ['scoutAgents', 'agentModels', 'evaluatorCapability'], properties: {
  scoutAgents: { type: 'array', minItems: 1, items: { type: 'string' } },
  agentModels: { type: 'object', minProperties: 1, additionalProperties: { type: 'string', minLength: 1 } },
  evaluatorCapability: { type: 'string', enum: ['SUPPORTED', 'UNSUPPORTED', 'UNKNOWN'] },
} }

const positiveNumber = (value, fallback) => Number.isFinite(value) && value > 0 ? value : fallback
let WORKFLOW_CAP = 8
let workflowSpawns = 0
let workflowCapped = false
let deferredDispatches = 0
const remainingWorkflowSpawns = () => Math.max(0, WORKFLOW_CAP - workflowSpawns)
const dispatch = async (prompt, options) => {
  if (workflowSpawns >= WORKFLOW_CAP) {
    workflowCapped = true
    log(`ultra-verify dispatch refused at graphGuardrails.maxSpawnsPerWorkflow=${WORKFLOW_CAP}`)
    return null
  }
  workflowSpawns++
  return await agent(prompt, options)
}

async function resolveConfig() {
  const supplied = args?.config && typeof args.config === 'object' ? args.config : null
  if (supplied) {
    const suppliedCapability = String(supplied.evaluatorCapability || '').toUpperCase()
    const policy = await dispatch(
      `Read ${supplied.pluginRoot || '<pluginRoot>'}/codex/model-policy.json and the model field in each canonical agents/*.md frontmatter. Return scoutAgents from the Codex policy, agentModels as the complete agent-name to Claude-family map, and evaluatorCapability. Use SUPPORTED only when the caller supplies positive runtime/provider capability evidence for the Fable/advisor route; otherwise use UNKNOWN. When capability is UNKNOWN or UNSUPPORTED, keep the evaluator route on the safe Opus fallback and never emit Fable. Read-only; do not invent names or perform a live probe.`,
      { agentType: AG('explorer'), phase: 'Gates', schema: SCOUT_POLICY_SHAPE, label: 'config:policy', model: 'haiku' }
    )
    return {
      ...supplied,
      scoutAgents: policy?.scoutAgents,
      agentModels: policy?.agentModels,
      evaluatorCapability: ['SUPPORTED', 'UNSUPPORTED', 'UNKNOWN'].includes(suppliedCapability)
        ? suppliedCapability
        : policy?.evaluatorCapability,
    }
  }
  return await dispatch(
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
      maxParallelWave <- graphGuardrails.maxParallelWave, else 3
      maxSpawnsPerWorkflow <- graphGuardrails.maxSpawnsPerWorkflow, else 8
      maxRepatch     <- graphGuardrails.maxRepatch, else 2
      maxFixRounds   <- chain.maxFixRounds, else 0 (0 means "let the workflow decide from its budget")
      scoutAgents    <- read <pluginRoot>/codex/model-policy.json and return the agent names whose profile is "scout"
      agentModels    <- read the model field from every canonical <pluginRoot>/agents/*.md frontmatter
      evaluatorCapability <- positive runtime/provider evidence supplied by the caller, else "UNKNOWN"; never probe live capability

      If evaluatorCapability is not "SUPPORTED", use "opus" for agentModels.evaluator as the safe read-only fallback. Emit "fable" for that entry only when the caller has already supplied positive supported evidence.

Do not invent a value that is not in the file: an absent field is absent, never a plausible default of your own.`,
    { agentType: AG('explorer'), phase: 'Gates', schema: CONFIG_SHAPE, label: 'config', model: 'haiku' }
  )
}

const cfg = (await resolveConfig()) ?? {}
const paths = cfg.paths ?? {}
const commands = cfg.commands ?? {}
const WORK_BRANCH = cfg.workBranch || 'main'
WORKFLOW_CAP = Math.min(positiveNumber(cfg.maxSpawnsPerWorkflow, 8), 8)
const REPATCH_CAP = Math.min(positiveNumber(cfg.maxRepatch, 2), 2)
const FIX_CAP = Math.min(positiveNumber(cfg.maxParallelWave, 3), 3, WORKFLOW_CAP)
const configuredRounds = positiveNumber(cfg.maxFixRounds, 0)
const MAX_ROUNDS = Math.min(configuredRounds || 1, 1)
// Width and cumulative total are separate. Every inner dispatch goes through `dispatch`; this
// wrapper also reserves later mandatory boundaries before allowing an optional batch to start.
const boundedParallel = async (thunks, reserve = 0, label = 'batch') => {
  const allowed = Math.max(0, Math.min(thunks.length, remainingWorkflowSpawns() - reserve))
  if (allowed < thunks.length) {
    deferredDispatches += thunks.length - allowed
    workflowCapped = true
    log(`${label}: keeping ${allowed}/${thunks.length} dispatches inside graphGuardrails.maxSpawnsPerWorkflow=${WORKFLOW_CAP}`)
  }
  const results = []
  for (let index = 0; index < allowed; index += FIX_CAP) {
    // eslint-disable-next-line no-await-in-loop
    const batch = await parallel(thunks.slice(index, Math.min(index + FIX_CAP, allowed)))
    results.push(...batch)
  }
  return results
}
// The config bootstrap derives the scout set from codex/model-policy.json and the complete model
// map from canonical agent frontmatter. Keep workflow values Claude-native: the semantic Codex
// policy belongs to the generators, while this workflow consumes the caller's capability-validated
// Claude-family map.
const SCOUT_AGENTS = new Set(Array.isArray(cfg.scoutAgents) ? cfg.scoutAgents : [])
const DECLARED_AGENT_MODELS = cfg.agentModels && typeof cfg.agentModels === 'object' ? cfg.agentModels : {}
const EVALUATOR_CAPABILITY = String(cfg.evaluatorCapability || 'UNKNOWN').toUpperCase()
const M = (name) => {
  const declared = typeof DECLARED_AGENT_MODELS[name] === 'string' ? DECLARED_AGENT_MODELS[name].trim().toLowerCase() : ''
  if (name === 'evaluator' && declared === 'fable' && EVALUATOR_CAPABILITY !== 'SUPPORTED') return 'opus'
  if (!declared) throw new Error(`ultra-verify: graph-powers:${name} has no canonical model declaration`)
  return declared
}

if (!SCOUT_AGENTS.size) {
  throw new Error('ultra-verify: config bootstrap returned no scoutAgents from codex/model-policy.json')
}
if (!Object.keys(DECLARED_AGENT_MODELS).length) {
  throw new Error('ultra-verify: config bootstrap returned no canonical agentModels')
}
if (!['SUPPORTED', 'UNSUPPORTED', 'UNKNOWN'].includes(EVALUATOR_CAPABILITY)) {
  throw new Error('ultra-verify: evaluatorCapability must be SUPPORTED, UNSUPPORTED, or UNKNOWN')
}

if (!cfg.pluginRoot) {
  throw new Error('ultra-verify: could not locate the graph-powers plugin root, so no agent can read the debugging catalogue. Pass it as args.config.pluginRoot.')
}
const DBG_GUIDE = `${cfg.pluginRoot}/skills/debugger/references/anti-patterns.md`
const PERF_GUIDE = `${cfg.pluginRoot}/commands/perf.md`
const GATE_GUIDE = `${cfg.pluginRoot}/references/shared/130-typescript7-oxc-gates.md`

// Bootstrap is mandatory. Seven slots are the irreducible non-web route: opening gates/scope,
// one correctness review, one grouped correction, its final evaluator, and final gates. Surface
// routing below may require the eighth slot for security; that case is reported after scope.
const MINIMUM_VERIFY_SPAWNS = 7
if (WORKFLOW_CAP < MINIMUM_VERIFY_SPAWNS) {
  return {
    verdict: 'NEEDS-WORK',
    capped: true,
    workflowSpawns,
    workflowSpawnCap: WORKFLOW_CAP,
    deferredDispatches,
    gates: 'not-run',
    missing: [], openFindings: [], unconfirmed: [], blocked: [], drift: [],
    reason: `ultra-verify needs at least ${MINIMUM_VERIFY_SPAWNS} total workflow slots, including mandatory config bootstrap, to preserve correction, final evaluator, and final gates`,
    next: 'Use a narrower verification path or raise this invocation\'s budget within the schema cap; do not silently omit a final boundary.',
  }
}

// The executable lane set for ultra-verify. Kept as an enum on every `agent` field below: this
// is the one thing the upstream copies of this workflow got wrong — `agent` was a free string, so
// whatever an evaluator wrote became a `subagent_type`, and a hallucinated name either failed to
// spawn or silently degraded to a default nobody chose.
const WRITER_AGENT_ENUM = [
  paths.frontendRoot && 'frontend-specialist',
  'debugger',
  'performance-optimizer',
  paths.mobileRoot && 'mobile-developer',
].filter(Boolean)
const WRITER_AGENTS = new Set(WRITER_AGENT_ENUM)
const writerFor = (requested) => {
  if (WRITER_AGENTS.has(requested)) return requested
  if (requested === 'ui-ux-designer' && WRITER_AGENTS.has('frontend-specialist')) return 'frontend-specialist'
  return 'debugger'
}

const projectRules = (cfg.hardRules ?? []).map((r) => ` ${r}`).join('')
const gateList = [commands.typeCheck, commands.lint, commands.test].filter(Boolean)
// `build` runs in the opening and, after any writes, final boundary. No intermediate per-finding
// re-gate exists: related fixes are grouped and the fresh Evaluator confirmation is the only review
// boundary after them.
const openingGateList = [...gateList, commands.build].filter(Boolean)
// Presented one per line, never chained: `;` is not a separator in cmd.exe, and a chained
// line makes "capture each exit code" unanswerable even where the chain does work.
const openingGateBlock = openingGateList.map((c) => `  - \`${c}\``).join('\n')
const GIT_RAILS =
  'HARD RULES (no inherited config): never git commit/push/checkout/reset/stash. Leave changes in ' +
  'the working tree.' + projectRules +
  ' After editing, run only a focused regression check for the files you changed. Never run the whole-project gate list; the workflow owns it once per round and once at the final boundary.'
const ROOT_CAUSE = 'Name the exact root cause BEFORE patching (read ' + DBG_GUIDE + '; do NOT invoke a Skill). Fix the source, not the symptom; no "while I am here" scope creep.'
const turboGuidance = (changedFiles = []) => {
  const roots = [...new Set((Array.isArray(changedFiles) ? changedFiles : []).flatMap((file) => {
    const match = String(file).replaceAll('\\', '/').match(/^(apps|packages)\/([^/]+)(?:\/|$)/)
    return match ? [`${match[1]}/${match[2]}`] : []
  }))]
  const concurrency = Math.max(1, Math.min(2, FIX_CAP))
  if (!roots.length) {
    return 'If a declared gate invokes Turborepo, inspect the returned changed paths first; use an evidence-backed --filter for actual package roots and --concurrency=1 or 2. Do not invent a filter or swap package managers.'
  }
  return `If a declared gate invokes Turborepo, scope it to the changed package roots ${JSON.stringify(roots)} with ${roots.map((root) => `--filter=./${root}`).join(' ')} and --concurrency=${concurrency}. Do not run an unscoped monorepo gate or swap package managers.`
}
const GATES = { type: 'object', required: ['allGreen', 'gates'], properties: {
  allGreen: { type: 'boolean' },
  gates: { type: 'array', items: { type: 'object', properties: { name: { type: 'string' }, exitCode: { type: 'number' }, pass: { type: 'boolean' }, failing: { type: 'string' } } } },
} }
const FIX = { type: 'object', required: ['status'], properties: {
  status: { type: 'string', enum: ['done', 'partial', 'blocked'] }, applied: { type: 'array', items: { type: 'string' } },
  changedPaths: { type: 'array', items: { type: 'string' } }, gateEvidence: { type: 'string' },
} }
// SKEPTIC is declared with the lens list in § "Adversarial verify", not here: its `lens` field is an
// enum over the lenses this run actually dispatches, and that set is not known until the scope agent
// has reported which surfaces the diff touched.
const COMPLETENESS = { type: 'object', required: ['items'], properties: {
  items: { type: 'array', minItems: 1, items: { type: 'object', required: ['id', 'status', 'evidence', 'agent'], properties: { id: { type: 'string', minLength: 1 }, status: { type: 'string', enum: ['done', 'missing', 'partial'] }, evidence: { type: 'string', minLength: 1 }, agent: { type: 'string', enum: WRITER_AGENT_ENUM } } } },
  drift: { type: 'array', items: { type: 'string' } },
} }
const hasRequirementEvidence = (items) => Array.isArray(items) && items.length > 0
  && items.every((item) => typeof item?.id === 'string' && item.id && typeof item?.evidence === 'string' && item.evidence)

// Built-ins remain usable with an empty config: configured roots sharpen classification but never
// decide whether a generic web/API/schema or user-input boundary exists at all.
const BUILTIN_SURFACES = [
  { name: 'web', match: `${paths.frontendRoot ? `any path under ${paths.frontendRoot}/, or ` : ''}any browser-facing UI, route, component, template, HTML, JSX or TSX file` },
  { name: 'api', match: `${paths.backendRoot ? `any path under ${paths.backendRoot}/, or ` : ''}any HTTP, RPC, webhook, request handler or public service endpoint` },
  { name: 'schema', match: `${paths.schemaRoot ? `any path under ${paths.schemaRoot}/, or ` : ''}any migration, database schema, policy or data-model definition` },
  { name: 'userInput', match: 'any changed code that accepts, parses, renders, executes or persists user/client-controlled input' },
  { name: 'auth', match: 'any path matching /auth|session|webhook|rls|policy/' },
]
const BUILTIN_SURFACE_NAMES = new Set(BUILTIN_SURFACES.map((surface) => surface.name))
const SURFACES = [...BUILTIN_SURFACES, ...(cfg.surfaces ?? []).filter((surface) => !BUILTIN_SURFACE_NAMES.has(surface.name))]
const SCOPE = { type: 'object', required: ['changedFiles', 'baseRef', 'touched', 'confidence'], properties: {
  touched: {
    type: 'object', required: SURFACES.map((surface) => surface.name),
    properties: Object.fromEntries(SURFACES.map((surface) => [surface.name, { type: 'boolean', enum: [false, true] }])),
    additionalProperties: { type: 'boolean' },
  },
  changedFiles: { type: 'array', items: { type: 'string' } },
  baseRef: { type: 'string' }, deadCodeVersion: { type: 'string' }, confidence: { type: 'string', enum: ['high', 'low'] },
} }

// 1. Gates + Scope (surface gate for the folded perf and dead-code passes) —
//    both mechanical, run in parallel (no extra wall-clock; both haiku).
phase('Gates')
const deadCodeProbe = commands.deadCode
  ? `\n3. Resolve the dead-code tool once: run \`${commands.deadCode} --version\` and return its major as \`deadCodeVersion\`; if it cannot be resolved, return the empty string.`
  : ''
const [g0, scope] = await boundedParallel([
  () => dispatch(
    openingGateList.length
      ? `Read ${GATE_GUIDE} first. Run these gates from the repository root. Run each as a SEPARATE command — never chained with \`;\` or \`&&\` — and capture the exit code of each:\n${openingGateBlock}\n${turboGuidance()}\nA forbidden command is a failed gate: do not execute it and do not fall back. Report pass/fail per gate with exit code + failing lines. Read-only — do NOT fix here.`
      : `This project declares no gate commands in its config. Return allGreen:true with an empty gates list, and note in \`failing\` that no gate was declared. Read-only.`,
    { agentType: AG('debugger'), phase: 'Gates', schema: GATES, label: 'gates', model: 'haiku' }
  ),
  () => dispatch(
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
const unresolvedSignals = []

const completeScopeEvidence = !!scope
  && sc.confidence === 'high'
  && sc.touched && typeof sc.touched === 'object'
  && SURFACES.every((surface) => typeof touched[surface.name] === 'boolean')
if (!completeScopeEvidence) {
  return {
    verdict: 'NEEDS-WORK', capped: false, workflowSpawns, workflowSpawnCap: WORKFLOW_CAP,
    deferredDispatches, gates: g?.allGreen ? 'green' : 'RED', gateDetail: g?.gates ?? [],
    missing: [], openFindings: [], unconfirmed: [], blocked: [], drift: [], scope: scopeOut(),
    reason: 'Scope classification was missing, low-confidence, or omitted a required surface; security routing cannot fail open.',
    next: 'Repair or rerun the read-only scope classification before accepting this change.',
  }
}

const normalizeChangedPath = (value) => String(value ?? '').replaceAll('\\', '/').replace(/^\.\/+/, '').replace(/\/+$/, '').toLowerCase()
const changedPaths = sc.changedFiles.map(normalizeChangedPath)
const underConfiguredRoot = (root) => {
  const normalizedRoot = normalizeChangedPath(root)
  return !!normalizedRoot && changedPaths.some((file) => file === normalizedRoot || file.startsWith(`${normalizedRoot}/`))
}
const pathMatches = (pattern) => changedPaths.some((file) => pattern.test(file))
const inferredBuiltins = {
  web: underConfiguredRoot(paths.frontendRoot) || pathMatches(/(^|\/)(web|frontend|client|components?|pages?|templates?)(\/|$)|\.(html?|jsx|tsx|vue|svelte)$/),
  api: underConfiguredRoot(paths.backendRoot) || pathMatches(/(^|\/)(api|backend|server|controllers?|handlers?)(\/|$)|(^|\/)(route|webhook)\.[^/]+$/),
  schema: underConfiguredRoot(paths.schemaRoot) || pathMatches(/(^|\/)(migrations?|schema|database|prisma)(\/|$)|\.(sql|prisma)$/),
  auth: pathMatches(/auth|session|webhook|rls|policy/),
}
const contradictedSurfaces = Object.entries(inferredBuiltins)
  .filter(([name, inferred]) => inferred && touched[name] !== true)
  .map(([name]) => name)
if (contradictedSurfaces.length) {
  return {
    verdict: 'NEEDS-WORK', capped: false, workflowSpawns, workflowSpawnCap: WORKFLOW_CAP,
    deferredDispatches, gates: g?.allGreen ? 'green' : 'RED', gateDetail: g?.gates ?? [],
    missing: [], openFindings: [], unconfirmed: [], blocked: [], drift: [], scope: scopeOut(),
    reason: `Scope classification contradicts changed paths for: ${contradictedSurfaces.join(', ')}; security routing cannot trust this result.`,
    next: 'Rerun scope classification and reconcile every inferred built-in surface before accepting this change.',
  }
}

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
const securitySurface = !!(touched.auth || touched.api || touched.schema || touched.web || touched.userInput)
// A web or user-input-facing diff has the same security boundary as API/auth/schema work. Do not
// spend its reserved slot on a partial panel: return explicit NEEDS-WORK when security, correction,
// final evaluator, and final gates cannot all coexist.
if (securitySurface && WORKFLOW_CAP < 8) {
  return {
    verdict: 'NEEDS-WORK',
    capped: true,
    workflowSpawns,
    workflowSpawnCap: WORKFLOW_CAP,
    deferredDispatches,
    gates: g?.allGreen ? 'green' : 'RED',
    gateDetail: g?.gates ?? [],
    missing: [], openFindings: [], unconfirmed: [], blocked: [], drift: [], scope: scopeOut(),
    reason: 'The touched web/auth/api/schema/user-input surface requires security review, but this cap cannot preserve it together with correction, final evaluator, and final gates.',
    next: 'Raise this invocation\'s budget within the schema cap or use a narrower verification path; do not approve this partial run.',
  }
}

// Conditional contract gates: commands a project runs only when a given surface changed. This is
// how a repository keeps the checks it already had — a link-inventory check, a smoke test, a build
// that only matters when the public site moved — without any of them being named in this file.
const firedGates = (cfg.contractGates ?? []).filter(
  (cg) => !cg.when?.length || cg.when.some((w) => touched[w])
)
if (firedGates.length) {
  log(`Contract gates fired by the touched surfaces: ${firedGates.map((cg) => cg.name).join(', ')}`)
  const extra = await dispatch(
    `Run these additional project gates and capture each exit code. They are declared by the project, not by this workflow; run each exactly as written. Read-only — do NOT fix.
${firedGates.map((cg) => `- ${cg.name}: ${cg.command}${cg.needsServer ? ` (needs a server: start \`${cg.needsServer}\` in the background, run the gate, then terminate that process — \`taskkill /PID <pid> /T /F\` on Windows, \`kill <pid>\` elsewhere. Say so if you cannot stop it: a server left holding the port makes the NEXT gate fail for the wrong reason)` : ''}${cg.runtime ? ` (run under ${cg.runtime}, not the project's default runtime)` : ''}`).join('\n')}`,
    { agentType: AG('debugger'), phase: 'Gates', schema: GATES, label: 'contract-gates', model: 'haiku' }
  )
  if (extra) {
    g = {
      allGreen: !!(g?.allGreen) && !!extra.allGreen,
      gates: [...(g?.gates ?? []), ...(extra.gates ?? [])],
    }
  } else {
    unresolvedSignals.push('declared contract gates returned no evidence')
  }
}

const mandatoryAfterScope = securitySurface ? 5 : 4 // initial review(s) + correction + final evaluator + final gates
if (remainingWorkflowSpawns() < mandatoryAfterScope) {
  return {
    verdict: 'NEEDS-WORK',
    capped: true,
    workflowSpawns,
    workflowSpawnCap: WORKFLOW_CAP,
    deferredDispatches,
    gates: g?.allGreen ? 'green' : 'RED',
    gateDetail: g?.gates ?? [],
    missing: [], openFindings: [], unconfirmed: [], blocked: [], drift: [], scope: scopeOut(),
    reason: `Mandatory ${securitySurface ? 'correctness/security' : 'correctness'} review, correction, final evaluator, and final gates need ${mandatoryAfterScope} remaining slots; only ${remainingWorkflowSpawns()} remain after declared gates.`,
    next: 'Use a narrower verification path or raise this invocation\'s budget within the schema cap; do not silently omit a mandatory boundary.',
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
if (remainingWorkflowSpawns() >= 6) {
  await dispatch(
    `Replicate a simplify pass on the working-tree diff (git diff). Review ONLY changed code, through these four angles, then apply safe quality-only cleanups — do NOT change behavior, do NOT hunt for bugs (that is the skeptics' job):
- REUSE: flag new code that re-implements something the codebase already has — search shared/utility modules and files adjacent to the change with the Grep tool, and name the existing helper to call instead.
- SIMPLIFICATION: flag unnecessary complexity the diff adds — redundant or derivable state, copy-paste with slight variation, deep nesting, dead code left behind. Name the simpler form that does the same job. Remove only dead code THIS diff created; pre-existing dead code is flagged, never deleted.
- EFFICIENCY: flag wasted work the diff introduces — redundant computation or repeated I/O, independent operations run sequentially, blocking work added to startup or hot paths. Also flag long-lived objects built from closures or captured environments (they keep the whole enclosing scope alive — a leak when that scope holds large values); prefer a structure copying only the fields it needs. Name the cheaper alternative.
- ALTITUDE: check each change is implemented at the right depth, not as a fragile bandaid. Special cases layered on shared infrastructure mean the fix is not deep enough — prefer generalizing the underlying mechanism over adding special cases.${invariantClause}${deadCodeClause} ${GIT_RAILS}
Return applied changes + gate evidence.`,
    { agentType: AG('debugger'), phase: 'Simplify', schema: FIX, label: 'review:simplify', model: M('debugger') }
  )
} else {
  log('Simplify pass skipped to reserve the mandatory Evaluator and completion boundary inside the workflow total')
}

// 3. Adversarial verify (fan-out skeptics) — combat self-preferential bias. Every call in this
// panel is a review, not a consultation: it does not reserve or consume the parent SDD ledger.
phase('Adversarial verify')
// Lenses are distinct QUESTIONS, never the same question asked N times — identical skeptics agree
// with each other and miss the same things. Spec compliance is deliberately absent: the
// Completeness phase already walks every requirement against the diff.
// Each lens is surface-gated: on a diff that never touches that surface it would burn a spawn to
// report nothing, which is exactly the fan-out the stop rule forbids.
const BUILTIN_LENSES = [
  { name: 'correctness', agent: 'evaluator', when: [] },
  { name: 'security-tenant-PII', agent: 'security-reviewer', when: ['auth', 'api', 'schema', 'web', 'userInput'] },
  paths.frontendRoot && { name: 'design-tokens-a11y', agent: 'ui-ux-designer', when: ['web'] },
].filter(Boolean)
// Dynamic lenses select an existing Graph Powers review role; they never manufacture a subagent
// name. Compatible questions are folded into one track per role, so four project lenses owned by
// the Evaluator still cost one dispatch. Runtime input is validated defensively in addition to the
// schema because callers may construct args without loading that schema.
const REVIEW_AGENTS = new Set(['evaluator', 'security-reviewer', 'ui-ux-designer'])
const ALL_LENSES = [...BUILTIN_LENSES, ...(cfg.lenses ?? [])]
  .filter((l) => !l.when?.length || l.when.some((w) => touched[w]))
const invalidLensAgents = ALL_LENSES.filter((l) => l.agent && !REVIEW_AGENTS.has(l.agent))
if (invalidLensAgents.length) {
  log(`unsupported lens agents folded into graph-powers:evaluator: ${invalidLensAgents.map((l) => `${l.name}->${l.agent}`).join(', ')}`)
}
const trackByAgent = new Map()
for (const lens of ALL_LENSES) {
  const agentName = REVIEW_AGENTS.has(lens.agent) ? lens.agent : 'evaluator'
  const current = trackByAgent.get(agentName) ?? {
    name: lens.name || agentName,
    agent: agentName,
    lensNames: [],
    checks: [],
  }
  current.lensNames.push(lens.name || agentName)
  current.checks.push(...(lens.checks ?? []))
  trackByAgent.set(agentName, current)
}
const lenses = [...trackByAgent.values()]

// `lens` is the key the final confirm at the bottom of this file matches findings on, and a match
// key an agent fills as free text is the same defect the comment above records for `agent`: whatever
// the model writes becomes the key. A panel member that answered `lens: "correctness lens"` matched
// no lens, the confirm re-ran nothing, and three open P0s were reported as VERIFIED. So the field is
// an enum over exactly the lenses this run dispatches — the model cannot name one nothing knows.
const LENS_ENUM = lenses.map((l) => l.name)
const KNOWN_LENS = new Set(LENS_ENUM)
const SKEPTIC = { type: 'object', required: ['lens', 'satisfied', 'findings'], properties: {
  lens: { type: 'string', enum: LENS_ENUM }, satisfied: { type: 'boolean' },
  findings: { type: 'array', items: { type: 'object', required: ['title', 'file', 'severity', 'inScope', 'agent'], properties: { title: { type: 'string' }, file: { type: 'string' }, severity: { type: 'string', enum: ['P0', 'P1', 'P2', 'P3'] }, inScope: { type: 'boolean' }, agent: { type: 'string', enum: WRITER_AGENT_ENUM } } } },
  items: COMPLETENESS.properties.items,
  drift: COMPLETENESS.properties.drift,
} }
const CORRECTNESS_SKEPTIC = { ...SKEPTIC, required: [...SKEPTIC.required, 'items'] }

// Performance is a conditional checklist inside the consolidated correctness Evaluator, not a
// second general reviewer. The write-capable performance specialist remains the remediation lane.
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
  const projectChecks = l.checks?.length
    ? `\nPROJECT CHECKS consolidated into this role — these are binding:\n${l.checks.map((c) => `- ${c}`).join('\n')}`
    : ''
  if (l.agent === 'evaluator') return `${perfClause}${projectChecks}`
  if (l.agent === 'ui-ux-designer') return `${designClause}${projectChecks}`
  return projectChecks
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

// Every in-scope severity survives into the verdict; only P0/P1 enters an automatic fix package.
// `inScope` absent counts as in scope so an older lens cannot go silent.
const actionable = (f) => (f.severity === 'P0' || f.severity === 'P1') && f.inScope !== false
const findingIsComplete = (finding) => finding && typeof finding === 'object'
  && typeof finding.title === 'string' && typeof finding.file === 'string'
  && ['P0', 'P1', 'P2', 'P3'].includes(finding.severity)
  && typeof finding.inScope === 'boolean' && WRITER_AGENT_ENUM.includes(finding.agent)
const findingArray = (result) => Array.isArray(result?.findings) ? result.findings : []
const malformedFindingSignalsFrom = (arr, pass) => (arr ?? []).flatMap((result) => {
  if (!Array.isArray(result?.findings)) return [`${pass} ${result?.lens ?? 'unknown'} review returned no findings array`]
  const malformed = result.findings.filter((finding) => !findingIsComplete(finding)).length
  return malformed ? [`${pass} ${result?.lens ?? 'unknown'} review returned ${malformed} malformed finding(s)`] : []
})
const outOfScopeFrom = (arr) => (arr ?? []).flatMap((s) => findingArray(s).filter((f) => findingIsComplete(f) && f.inScope === false))
// Findings are lifted out of the panel member that raised them, so each one has to carry that lens
// with it: the confirm pass can only clear a finding through the lens able to see it. `lensResolved`
// is the same question asked defensively — a lens name that resolves to nothing is a finding nothing
// can re-check, and one nothing can re-check stays OPEN. Unparseable never means clean.
const findingsFrom = (arr) => (arr ?? []).flatMap((s) => findingArray(s).filter((f) => findingIsComplete(f) && f.inScope !== false).map((f) => Object.assign({}, f, {
  lens: s?.lens, lensResolved: KNOWN_LENS.has(s?.lens),
})))
const actionableFrom = (arr) => findingsFrom(arr).filter(actionable)
const unsatisfiedFrom = (arr) => (arr ?? []).filter((result) => result?.satisfied !== true).map((result) => ({
  lens: result?.lens ?? 'unknown', reason: 'review did not return satisfied:true',
}))
// A finding has no id, and the confirm pass has to recognise the SAME finding coming back from a
// freshly spawned agent. Lens + file + title is that identity.
const findingKey = (f) => JSON.stringify([f?.lens ?? '', f?.file ?? '', f?.title ?? ''])

const skMaker = (pass, lensList = lenses) => lensList.map((l) => () => dispatch(
  `Adversarially verify the working tree against the plan through the consolidated "${l.name}" track (${l.lensNames.join(', ')}). DEFAULT to "not satisfied" when uncertain — your job is to REFUTE, not to confirm. Apply the checklist in ${DBG_GUIDE} (read it); do NOT invoke a skill — this workflow is the orchestration, report only.${clauseFor(l)}
PLAN: ${PLAN_PATH}
REQUIREMENTS: Read every acceptance criterion and ## Verification step directly from PLAN; include their ids in your response.
Surface concrete failures with file:line + severity P0-P3 + inScope + which agent should fix it.${pass === 'final' && l.name === 'correctness' ? ' This is the one post-correction Evaluator boundary: also walk every requirement against the current diff and return items plus drift.' : ''} Read-only.${SCOPE_LOCK}`,
  { agentType: AG(l.agent), phase: pass === 'final' ? 'Fix loop' : 'Adversarial verify', schema: l.name === 'correctness' ? CORRECTNESS_SKEPTIC : SKEPTIC, label: `review:skeptic:${pass}:${l.name}`, model: M(l.agent) }
))
// Reserve one grouped correction plus the final evaluator and final gates. The optional design
// lens yields first; correctness and the required security lens remain ahead of it.
let sk = (await boundedParallel(skMaker('init'), 3, 'initial adversarial review')).filter(Boolean)
unresolvedSignals.push(...malformedFindingSignalsFrom(sk, 'initial'))
const returnedInitialLenses = new Set(sk.map((result) => result?.lens))
for (const lens of lenses) {
  if (!returnedInitialLenses.has(lens.name)) unresolvedSignals.push(`initial ${lens.name} review returned no evidence`)
}
const outOfScope = outOfScopeFrom(sk)
if (outOfScope.length) log(`${outOfScope.length} finding(s) outside this plan's scope — reported, not fixed: ${outOfScope.slice(0, 4).map((f) => f.title).join(' · ')}${outOfScope.length > 4 ? ` (+${outOfScope.length - 4})` : ''}`)

// 4. Completeness — the mandatory correctness evaluator owns this walk. Folding it into the
// adversarial boundary removes a duplicate explorer pass while keeping the production seam real.
phase('Completeness')
const initialCorrectness = sk.find((result) => result.lens === 'correctness')
let c = hasRequirementEvidence(initialCorrectness?.items)
  ? { items: initialCorrectness.items, drift: initialCorrectness.drift ?? [] }
  : null
if (!hasRequirementEvidence(initialCorrectness?.items)) {
  unresolvedSignals.push('initial correctness/completeness evidence missing')
  log('Mandatory correctness/completeness boundary returned no requirement evidence; preserving NEEDS-WORK rather than treating an empty field as a clean diff')
}
const expectedRequirementIds = new Set((c?.items ?? []).map((item) => item.id))

// 5. Loop-until-done — fix → re-verify until clean or capped.
// Intermediate rounds drive on the cheap objective pair (gates + completeness); the expensive
// skeptic panel is NOT re-fanned-out per round — it brackets the loop.
phase('Fix loop')
const openItems = (completeness, refuted, gates) => {
  const missing = (completeness?.items ?? []).filter((i) => i.status !== 'done')
  const gateFail = !(gates?.allGreen)
  return { missing, refuted, gateFail, total: missing.length + refuted.length + (gateFail ? 1 : 0) }
}
const fixGroups = (state, round) => {
  const grouped = new Map()
  const add = (kind, item) => {
    const agentName = writerFor(item.agent)
    if (!grouped.has(agentName)) grouped.set(agentName, [])
    grouped.get(agentName).push({ kind, item })
  }
  for (const item of state.missing ?? []) add('missing', item)
  for (const item of state.refuted ?? []) add('finding', item)
  return [...grouped.entries()].map(([agentName, entries], index) => ({
    entries,
    run: () => dispatch(
      `Fix this bounded package of related work assigned to one existing specialist. Resolve every entry you can in one pass; report an entry as blocked rather than spawning a child or widening scope. Do NOT invoke a process skill that re-dispatches agents. ${ROOT_CAUSE} ${GIT_RAILS}
PLAN: ${PLAN_PATH}
PACKAGE: ${JSON.stringify(entries)}`,
      { agentType: AG(agentName), phase: 'Fix loop', schema: FIX, label: `fix-group:${round}:${index}`, model: M(agentName) }
    ),
  }))
}
// Drop a non-converging item after it fails its gate REPATCH_CAP times across rounds. The
// orchestrator respawns a fresh fixer each round, so this counter MUST live here, not in the agent
// prompt. It stops the loop burning rounds on something it cannot fix.
const keyOf = (it) => it?.id ?? it?.title ?? JSON.stringify(it)
const attempts = new Map()
const blocked = []
const rememberBlocked = (item, reason, fixResult = null) => {
  const key = keyOf(item)
  if (!blocked.some((entry) => keyOf(entry) === key)) blocked.push({ ...item, blocked: reason, fixResult })
}
const dropExhausted = (it) => {
  const k = keyOf(it)
  if ((attempts.get(k) || 0) >= REPATCH_CAP) {
    rememberBlocked(it, 're-patch limit')
    return false
  }
  return true
}
let round = 0
let state = openItems(c, actionableFrom(sk), g)
while (state.total > 0 && round < MAX_ROUNDS) {
  round++
  state.missing = state.missing.filter(dropExhausted)
  state.refuted = state.refuted.filter(dropExhausted)
  if (state.missing.length + state.refuted.length === 0) break // only gate failures / exhausted items remain
  const groups = fixGroups(state, round)
  const available = Math.max(0, Math.min(FIX_CAP, remainingWorkflowSpawns() - 2))
  const selected = groups.slice(0, available)
  const deferred = groups.length - selected.length
  log(`Fix round ${round}/${MAX_ROUNDS}: ${state.missing.length} missing · ${state.refuted.length} P0/P1 · gates ${g?.allGreen ? 'green' : 'RED'}${blocked.length ? ` · ${blocked.length} blocked (re-patch cap)` : ''}${deferred ? ` · deferring ${deferred} past the spawn cap of ${FIX_CAP}` : ''}`)
  if (deferred) {
    workflowCapped = true
    deferredDispatches += deferred
  }
  if (!selected.length) {
    workflowCapped = true
    break
  }
  for (const it of selected.flatMap((group) => group.entries.map((entry) => entry.item))) {
    attempts.set(keyOf(it), (attempts.get(keyOf(it)) || 0) + 1)
  }
  // Each round reads the tree the previous round wrote, so the loop is serial by construction.
  // oxlint-disable-next-line no-await-in-loop
  const fixResults = await boundedParallel(selected.map((group) => group.run), 2, 'grouped fix round')
  for (const [index, group] of selected.entries()) {
    const result = fixResults[index]
    if (result?.status === 'done') continue
    for (const entry of group.entries) rememberBlocked(entry.item, `fixer ${result?.status ?? 'unavailable'}`, result)
  }
  // The one fresh post-correction Evaluator below owns completeness re-check. Do not spend an
  // intermediate reviewer on the same acceptance boundary.
  state = openItems(c, [], g)
}

// 6. Final adversarial pass — catch regressions the fixes introduced (skeptics bracket the loop).
let openFindings = []
let unconfirmed = [] // findings not re-checked: P0/P1 block; P2/P3 remain explicit notes
let unsatisfiedReviews = []
if (round > 0) {
  const finalSk = (await boundedParallel(skMaker('final'), 1, 'final adversarial confirmation')).filter(Boolean)
  unresolvedSignals.push(...malformedFindingSignalsFrom(finalSk, 'final'))
  const finalCorrectness = finalSk.find((result) => result.lens === 'correctness')
  const finalRequirementIds = new Set((finalCorrectness?.items ?? []).map((item) => item?.id))
  const finalEvidenceComplete = hasRequirementEvidence(finalCorrectness?.items)
    && expectedRequirementIds.size > 0
    && [...expectedRequirementIds].every((id) => finalRequirementIds.has(id))
  if (finalEvidenceComplete) {
    c = { items: finalCorrectness.items, drift: finalCorrectness.drift ?? [] }
  } else {
    unresolvedSignals.push('final correctness/completeness evidence missing, empty, or incomplete')
    log('Final correctness evaluator returned missing, empty, or incomplete requirement evidence; preserving NEEDS-WORK')
  }
  const initialOpen = findingsFrom(sk)
  const reran = new Set(finalSk.map((result) => result.lens).filter((name) => KNOWN_LENS.has(name)))
  const confirmed = findingsFrom(finalSk)
  const carried = initialOpen.filter((finding) => !reran.has(finding.lens))
  const carriedKeys = new Set(carried.map(findingKey))
  openFindings = [...carried, ...confirmed.filter((finding) => !carriedKeys.has(findingKey(finding)))]
  unconfirmed = carried
  unsatisfiedReviews = unsatisfiedFrom([...sk.filter((result) => !reran.has(result?.lens)), ...finalSk])
  if (unconfirmed.length) {
    log(`${unconfirmed.length} initial finding(s) could not be re-checked inside the workflow total and remain OPEN`)
  }
} else {
  openFindings = findingsFrom(sk) // no fix rounds ran → the init panel already reflects the final tree
  unsatisfiedReviews = unsatisfiedFrom(sk)
}

// Intermediate rounds use changed-only Bun tests when possible. Once every write is finished, the
// full declared gate set runs exactly once against the final tree; otherwise a quick green loop could
// be mistaken for a final verdict, or a passing opening build could survive fixes that broke it.
if (round > 0) {
  g = await dispatch(
    openingGateList.length
      ? `Read ${GATE_GUIDE} first. Run the FINAL gate set once from the repository root, each as a separate command:\n${openingGateBlock}\nA forbidden command is a failed gate: do not execute it and do not fall back. Capture every exit code. Read-only.`
      : 'This project declares no final gate commands. Return allGreen:true with an empty gates list and record that the final boundary had no declared command. Read-only.',
    { agentType: AG('debugger'), phase: 'Fix loop', schema: GATES, label: 'gates:final', model: 'haiku' }
  )
}

const missing = (c?.items ?? []).filter((i) => i.status !== 'done')
const drift = c?.drift ?? []
const totalOpen = missing.length + openFindings.length + unsatisfiedReviews.length + unresolvedSignals.length
  + blocked.length + drift.length + (g?.allGreen ? 0 : 1) + (workflowCapped ? 1 : 0)
// `VERIFIED` requires `totalOpen === 0`, so a non-empty `openFindings` can never reach it — that is
// the invariant, and it is why the confirm above may not overwrite that list.
// `VERIFIED-WITH-NOTES` is only for residual P2/P3. Missing requirements/evidence, an unsatisfied
// review, drift, a blocked item, or any P0/P1 all route to NEEDS-WORK.
const hardOpen = workflowCapped || missing.length > 0 || blocked.length > 0 || drift.length > 0
  || unresolvedSignals.length > 0 || unsatisfiedReviews.length > 0
  || openFindings.some((finding) => finding.severity !== 'P2' && finding.severity !== 'P3')
const verdict = totalOpen === 0 ? 'VERIFIED' : (g?.allGreen && !hardOpen ? 'VERIFIED-WITH-NOTES' : 'NEEDS-WORK')
return {
  verdict,
  rounds: round,
  capped: workflowCapped || (totalOpen > 0 && round >= MAX_ROUNDS),
  workflowSpawns,
  workflowSpawnCap: WORKFLOW_CAP,
  deferredDispatches,
  gates: g?.allGreen ? 'green' : 'RED',
  gateDetail: g?.gates ?? [],
  missing,
  openFindings,
  unconfirmed, // subset of openFindings: P0/P1 block, while P2/P3 remain explicit notes
  unsatisfiedReviews,
  unresolvedSignals,
  blocked, // items dropped after hitting the re-patch cap — these need a human, not another round
  outOfScope, // real findings the panel raised past this plan's edge: reported, never fixed here
  drift,
  scope: scopeOut(),
  next: workflowCapped
    ? 'Workflow dispatch cap reached. Review the completed and deferred evidence; narrow any follow-up instead of starting another automatic fan-out.'
    : verdict === 'VERIFIED'
    ? 'Review the working tree. The workflow never commits; the caller decides.'
    : `Address the listed gaps and findings${blocked.length ? ' (including the re-patch-capped items, which need manual root-cause work)' : ''}, then re-run ultra-verify.`,
}
