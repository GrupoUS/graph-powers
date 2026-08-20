export const meta = {
  name: 'ultra-build',
  description: 'Classify each plan task by domain + dependency, then execute in disjoint-file waves routed to the paired specialist agent (classify-and-act). Writes to the working tree; commits nothing.',
  whenToUse: 'Execute an approved plan from ultra-plan. Reads the plan, builds a wave graph (disjoint files run in parallel, dependents run later), routes each task to the specialist that owns those paths. Pass the plan path as args, or { planPath, config }.',
  phases: [{ title: 'Classify', model: 'haiku' }, { title: 'Act' }],
}

// ── Design notes (read before editing) ───────────────────────────────────────
// After editing, run `node .github/check_workflows.mjs`. Top-level `return` is legal only because
// the runtime wraps the body, so `node --check` and most linters reject this file outright; that
// script wraps it the same way the runtime does, and it is the only syntax gate there is.
//
// This file ships inside the plugin and runs in repositories nobody here has seen. Nothing in it
// may name a product, a stack, a package manager, a provider or a directory layout — all of that
// arrives through `config` (see `resolveConfig` below) and traces back to
// `schema/config.schema.json`. A package manager hardcoded here is a broken workflow in every
// project that chose a different one.
//
// Agent budget: 1 config (only when invoked bare) + 1 classify + one implementer per plan task.
// The runtime caps live CONCURRENCY but not the TOTAL, so a malformed plan could enqueue hundreds
// of implementers; the two ceilings below are the hard stop. Neither silently drops work — an
// oversized wave is SPLIT and logged, and blowing the total throws instead of implementing part
// of a plan and reporting success.
//
// One writer per file is enforced here, not requested: `classify` is asked for disjoint file sets,
// but it is a haiku node and asking is not proving. `splitByFileOwnership` re-slices any wave where
// two tasks claim the same path, so a bad classification costs an extra wave, never a corrupted
// file. This function is the structural half of guardrail G4 in `hooks/graph_guardrails.py`.
//
// No nested orchestration: task agents LOAD a domain skill for conventions (knowledge, no agent
// dispatch) but must NOT invoke a process skill that dispatches agents — this workflow already
// orchestrates, and an inner dispatch re-fans-out. The debug chain belongs to ultra-verify's fix
// loop, not to a greenfield build.
//
// Model tiering: Classify transcribes an already-structured plan into waves → 'haiku'.
// Implementers inherit the main-loop model; code quality depends on it, so do not downgrade them.
// ─────────────────────────────────────────────────────────────────────────────

const PLAN_PATH = typeof args === 'string' ? args : (args?.planPath ?? args?.path ?? '')
// The literal strings are what a template-interpolated `next` produces when the upstream plan path
// was missing. Without this they pass the empty check, classify reads nothing, and the run returns
// `tasksTotal: 0` — a silent success that implemented none of the plan.
if (!PLAN_PATH || PLAN_PATH === 'undefined' || PLAN_PATH === 'null') {
  throw new Error(`ultra-build: pass the plan file path as args (got: ${JSON.stringify(PLAN_PATH)})`)
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
// and `budget`. So the project's contract arrives one of two ways — passed in by the command that
// called us (free), or read by one cheap agent when someone invokes this workflow directly.
const CONFIG_SHAPE = { type: 'object', required: ['paths', 'commands'], properties: {
  displayName: { type: 'string' },
  paths: { type: 'object', properties: {
    frontendRoot: { type: 'string' }, backendRoot: { type: 'string' },
    schemaRoot: { type: 'string' }, mobileRoot: { type: 'string' },
  } },
  commands: { type: 'object', properties: {
    typeCheck: { type: 'string' }, lint: { type: 'string' }, test: { type: 'string' },
  } },
  hardRules: { type: 'array', items: { type: 'string' } },
  domainSkills: { type: 'array', items: { type: 'object', properties: {
    match: { type: 'string' }, skill: { type: 'string' },
  } } },
  maxParallelWave: { type: 'number' },
  maxTasksPerPlan: { type: 'number' },
} }

async function resolveConfig() {
  if (args?.config) return args.config
  return await agent(
    `Read \`.graph-powers/config.json\` at the repository root (fall back to \`.claude/config.json\`, then to an empty object if neither exists — a project with no config is valid and takes the defaults).

Return, flattened:
  displayName      <- project.displayName, else project.name, else ""
  paths            <- paths.frontendRoot / backendRoot / schemaRoot / mobileRoot; omit any that is absent
  commands         <- tooling.commands.typeCheck / lint / test; omit any that is absent
  hardRules        <- chain.hardRules, else []
  domainSkills     <- chain.domainSkills, else []
  maxParallelWave  <- graphGuardrails.maxParallelWave, else 5
  maxTasksPerPlan  <- graphGuardrails.maxTasksPerPlan, else 40

Read only. Do not invent a value that is not in the file: an absent field is absent, never a plausible default of your own.`,
    { agentType: AG('explorer'), phase: 'Classify', schema: CONFIG_SHAPE, label: 'config', model: 'haiku' }
  )
}

const cfg = (await resolveConfig()) ?? {}
const paths = cfg.paths ?? {}
const commands = cfg.commands ?? {}
const WAVE_CAP = cfg.maxParallelWave ?? 5
const TOTAL_CAP = cfg.maxTasksPerPlan ?? 40

// Only the lanes this repository actually has. A project with no mobile root must not be able to
// route a task to `mobile-developer`: the agent would run with nothing to work on, and the enum is
// what makes that unrepresentable rather than merely discouraged.
const LANES = [
  paths.frontendRoot && { agent: 'frontend-specialist', where: `${paths.frontendRoot}/** and *.tsx/*.jsx` },
  { agent: 'debugger', where: [paths.backendRoot && `${paths.backendRoot}/**`, paths.schemaRoot && `${paths.schemaRoot}/**`, 'tests, and any bug fix'].filter(Boolean).join(', ') },
  { agent: 'performance-optimizer', where: 'performance, security baseline and SEO work' },
  paths.mobileRoot && { agent: 'mobile-developer', where: `${paths.mobileRoot}/** and *.{kt,swift,kts}` },
].filter(Boolean)
const AGENT_ENUM = LANES.map((l) => l.agent)
const ROUTING = LANES.map((l) => `${l.agent} for ${l.where}`).join('; ')

// Re-slice a wave so no two tasks running in parallel claim the same file, then chunk to WAVE_CAP.
// Returns a list of sub-waves that run sequentially in place of the original wave.
function splitByFileOwnership(tasks) {
  const subWaves = []
  for (const t of tasks) {
    const owned = new Set(t.files ?? [])
    // First sub-wave that neither collides on a file nor is already full.
    let slot = subWaves.find(
      (sw) => sw.length < WAVE_CAP && !sw.some((o) => (o.files ?? []).some((f) => owned.has(f)))
    )
    if (!slot) { slot = []; subWaves.push(slot) }
    slot.push(t)
  }
  return subWaves
}

// Listed, not chained: `;` is a literal argument in cmd.exe, and this string is pasted into
// every implementer prompt of every wave.
const gateLine = [commands.typeCheck, commands.lint, commands.test].filter(Boolean).map((c) => `\`${c}\``).join(', ')
const projectRules = (cfg.hardRules ?? []).map((r) => ` ${r}`).join('')
const GIT_RAILS =
  'HARD RULES (you do NOT inherit project config — obey these literally): never run git commit / ' +
  'git push / git checkout / git reset / git stash. Leave ALL changes in the working tree. Match ' +
  'existing patterns and the surrounding code style. Touch ONLY the files you own.' +
  projectRules +
  (gateLine
    ? ` After editing, run the relevant gate on your touched files — each as a separate command, never chained: ${gateLine} — and capture the exit code as evidence.`
    : ' This project declares no gate commands: say so in gateEvidence rather than inventing one.')

const TASK_GRAPH = { type: 'object', required: ['waves'], properties: {
  waves: { type: 'array', items: { type: 'object', required: ['tasks'], properties: {
    tasks: { type: 'array', items: { type: 'object', required: ['id', 'title', 'agent', 'files', 'criterion'], properties: {
      id: { type: 'string' }, title: { type: 'string' },
      agent: { type: 'string', enum: AGENT_ENUM },
      files: { type: 'array', items: { type: 'string' } },
      criterion: { type: 'string' }, detail: { type: 'string' },
    } } },
  } } },
} }
const TASK_RESULT = { type: 'object', required: ['id', 'status', 'changedPaths'], properties: {
  id: { type: 'string' }, status: { type: 'string', enum: ['done', 'partial', 'blocked'] },
  changedPaths: { type: 'array', items: { type: 'string' } }, gateEvidence: { type: 'string' }, notes: { type: 'string' },
} }

// 1. Classify — transcribe the structured plan into a wave graph (disjoint files, dependency order). haiku.
phase('Classify')
const graph = await agent(
  `Read the plan at ${PLAN_PATH}. Extract every atomic task and CLASSIFY each: domain → agent (${ROUTING}); file ownership; dependency; acceptance criterion. Those ${AGENT_ENUM.length} are the ONLY routable values — a task the plan left unassigned, or assigned to anything else (including "main"), goes to debugger as the generic lane; say so in its detail so the reassignment is visible rather than silent.
Group into WAVES: tasks in the same wave MUST have DISJOINT file sets and no inter-dependency (safe to run in parallel). Any task that depends on another or shares a file goes in a later wave. Order waves by dependency. Read-only — return the wave structure.`,
  { agentType: AG('explorer'), phase: 'Classify', schema: TASK_GRAPH, label: 'classify', model: 'haiku' }
)

// 2. Act — waves sequential, tasks within a wave parallel, routed to specialists
phase('Act')
const results = []
const rawWaves = graph?.waves ?? []
const plannedTasks = rawWaves.reduce((n, w) => n + (w.tasks?.length ?? 0), 0)
if (plannedTasks > TOTAL_CAP) {
  throw new Error(
    `ultra-build: plan has ${plannedTasks} tasks, over the ceiling of ${TOTAL_CAP}. ` +
    `Split the plan and run it in parts — refusing to spawn ${plannedTasks} implementers.`
  )
}

// Expand each classified wave into the sub-waves that are actually safe to run in parallel.
const waves = []
for (const w of rawWaves) {
  const subWaves = splitByFileOwnership(w.tasks ?? [])
  if (subWaves.length > 1) {
    log(`Wave split into ${subWaves.length}: ${(w.tasks ?? []).length} task(s) exceeded the parallel cap of ${WAVE_CAP} or shared a file`)
  }
  waves.push(...subWaves.map((tasks) => ({ tasks })))
}

const skillLine = (cfg.domainSkills ?? []).length
  ? `Load the DOMAIN skill matching your files for conventions (knowledge only, no agent dispatch): ${(cfg.domainSkills ?? []).map((d) => `${d.skill} for ${d.match}`).join('; ')}. `
  : ''

for (let w = 0; w < waves.length; w++) {
  const wave = waves[w]
  log(`Wave ${w + 1}/${waves.length}: ${wave.tasks.length} task(s) in parallel`)
  // Waves are the barrier: wave N+1 builds on files wave N wrote, so this await is the point.
  // oxlint-disable-next-line no-await-in-loop
  const waveResults = await parallel(
    wave.tasks.map((t) => () => agent(
      `Implement this task from ${PLAN_PATH}. ${skillLine}Do NOT invoke any process skill that dispatches agents — this workflow already orchestrates; implement directly (the debug chain is reserved for ultra-verify's fix loop).
TASK ${t.id}: ${t.title}
DETAIL: ${t.detail ?? ''}
FILES YOU OWN (do not touch anything outside this set): ${JSON.stringify(t.files)}
ACCEPTANCE: ${t.criterion}
${GIT_RAILS}
Return id, status, changedPaths, gateEvidence.`,
      { agentType: AG(t.agent), phase: 'Act', schema: TASK_RESULT, label: `${t.agent}:${t.id}` }
    ))
  )
  results.push(...waveResults.filter(Boolean))
}

const blocked = results.filter((r) => r.status !== 'done')
return {
  planPath: PLAN_PATH,
  wavesPlanned: rawWaves.length,
  wavesRun: waves.length,
  tasksTotal: results.length,
  done: results.filter((r) => r.status === 'done').length,
  blocked: blocked.map((r) => ({ id: r.id, status: r.status, notes: r.notes })),
  changedPaths: [...new Set(results.flatMap((r) => r.changedPaths ?? []))],
  // One writer per file, made checkable: `hooks/graph_guardrails.py` reads this list from
  // `.graph-powers/logs/write-lease.json` and refuses a write outside it. The script cannot write
  // the file, so the caller does — see `commands/plan.md`.
  writeLease: [...new Set(rawWaves.flatMap((w) => (w.tasks ?? []).flatMap((t) => t.files ?? [])))],
  next: blocked.length ? 'Resolve blocked tasks, then run ultra-verify' : `ultra-verify ${PLAN_PATH}`,
}
