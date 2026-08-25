export const meta = {
  name: 'ultra-build',
  description: 'Classify each plan task by domain + dependency, then dispatch it the moment its own dependencies are done and no in-flight task holds one of its files, routed to the paired specialist agent (classify-and-act). Writes to the working tree; commits nothing.',
  whenToUse: 'Execute an approved plan from ultra-plan. Reads the plan, builds a dependency graph from each task Needs and Owns, dispatches on a rolling basis instead of in lockstep waves, and routes each task to the specialist that owns those paths. Pass the plan path as args, or { planPath, config }.',
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
// oversized group is SPLIT and logged, and blowing the total throws instead of implementing part
// of a plan and reporting success.
//
// Dispatch is ROLLING, not lockstep. A wave barrier made every task wait for the slowest task of
// the previous wave, including the ones it never reads. A task here starts when its own `needs`
// are done and no in-flight task holds one of its files. Three things bound it: a topological
// check that THROWS on a dependency cycle (awaiting a cyclic promise is a hang, not an error),
// `maxParallelWave` as in-flight width, and `maxTasksPerPlan` as the total.
//
// One writer per file is enforced here, not requested: `classify` is asked for disjoint file sets,
// but it is a haiku node and asking is not proving. `splitByFileOwnership` orders any group where
// two tasks claim the same path, and the in-flight file set refuses the overlap again at dispatch
// time, so a bad classification costs an extra turn, never a corrupted file. This is the structural
// half of guardrail G4 in `hooks/graph_guardrails.py`.
//
// No nested orchestration: task agents LOAD a domain skill for conventions (knowledge, no agent
// dispatch) but must NOT invoke a process skill that dispatches agents — this workflow already
// orchestrates, and an inner dispatch re-fans-out. The debug chain belongs to ultra-verify's fix
// loop, not to a greenfield build.
//
// Model tiering: Classify transcribes an already-structured plan into a task graph → 'haiku'.
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
// and `budget`. So the project's contract arrives one of two ways — passed in by the command that
// called us (free), or read by one cheap agent when someone invokes this workflow directly.
const CONFIG_SHAPE = { type: 'object', required: ['paths'], properties: {
  displayName: { type: 'string' },
  paths: { type: 'object', properties: {
    frontendRoot: { type: 'string' }, backendRoot: { type: 'string' },
    schemaRoot: { type: 'string' }, mobileRoot: { type: 'string' },
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

  hardRules        <- chain.hardRules, else []
  domainSkills     <- chain.domainSkills, else []
  maxParallelWave  <- graphGuardrails.maxParallelWave, else 5
  maxTasksPerPlan  <- graphGuardrails.maxTasksPerPlan, else 40

Read only. Do not invent a value that is not in the file: an absent field is absent, never a plausible default of your own.`,
    { agentType: AG('explorer'), phase: 'Classify', schema: CONFIG_SHAPE, label: 'config', model: M('explorer') }
  )
}

const cfg = (await resolveConfig()) ?? {}
const paths = cfg.paths ?? {}
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

// Split a group so no two tasks claiming the same file land in the same one, then chunk to
// WAVE_CAP. With rolling dispatch this only refines the FALLBACK ordering used for tasks whose
// `needs` the classifier could not determine; the in-flight file set is what actually enforces it.
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

const projectRules = (cfg.hardRules ?? []).map((r) => ` ${r}`).join('')
const GIT_RAILS =
  'HARD RULES (you do NOT inherit project config — obey these literally): never run git commit / ' +
  'git push / git checkout / git reset / git stash. Leave ALL changes in the working tree. Match ' +
  'existing patterns and the surrounding code style. Touch ONLY the files you own.' +
  projectRules +
  ' After editing, run only the task-specific CHECK named by the plan or the narrowest test for your touched files. Never run a whole-project type-check, lint, build or full test suite here; ultra-verify owns those gates once after the build. Capture the focused exit code as evidence, or say the plan named no focused check.'

const TASK_GRAPH = { type: 'object', required: ['waves'], properties: {
  waves: { type: 'array', items: { type: 'object', required: ['tasks'], properties: {
    tasks: { type: 'array', items: { type: 'object', required: ['id', 'title', 'agent', 'files', 'criterion'], properties: {
      id: { type: 'string' }, title: { type: 'string' },
      agent: { type: 'string', enum: AGENT_ENUM },
      files: { type: 'array', items: { type: 'string' } },
      needs: { type: 'array', items: { type: 'string' } },
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
For each task also return \`needs\`: the ids of the tasks whose OUTPUT it reads. Copy the plan's \`Needs:\` field when the plan has one; otherwise infer it, and only where you can name what is read — a task that merely comes later in the plan does NOT need it. An empty \`needs\` on a task the plan really does gate is the one error that costs correctness here, so when a dependency is genuinely unclear, declare it.
Group into WAVES: tasks in the same wave MUST have DISJOINT file sets and no inter-dependency. Order waves by dependency. Waves remain the fallback ordering for tasks whose \`needs\` you could not determine. Read-only — return the wave structure.`,
  { agentType: AG('explorer'), phase: 'Classify', schema: TASK_GRAPH, label: 'classify', model: M('explorer') }
)

// 2. Act — waves sequential, tasks within a wave parallel, routed to specialists
phase('Act')
const results = []
const rawWaves = graph?.waves ?? []
// The PLANNED ids, in plan order. Everything below reconciles against this list rather than against
// whatever survived: it is what the plan asked for, and no later step may shrink it in silence.
const plannedIds = rawWaves.flatMap((w) => (w.tasks ?? []).map((t) => t.id))
const plannedTasks = plannedIds.length
if (plannedTasks > TOTAL_CAP) {
  throw new Error(
    `ultra-build: plan has ${plannedTasks} tasks, over the ceiling of ${TOTAL_CAP}. ` +
    `Split the plan and run it in parts — refusing to spawn ${plannedTasks} implementers.`
  )
}

// An id is the key the whole scheduler runs on: `byId`, `remaining` and `started` below are all Maps
// keyed by it, so two tasks sharing one id collapse into a single node — the second overwrites the
// first, one task is never dispatched, and the run still reports the survivors as the total. That is
// a malformed plan, not something to reconcile, so it throws HERE, before any implementer is spawned
// and while the duplicated id can still be named.
const duplicateIds = [...new Set(plannedIds.filter((id, i) => plannedIds.indexOf(id) !== i))]
if (duplicateIds.length) {
  throw new Error(
    `ultra-build: duplicate task id(s) in the classified plan — ${duplicateIds.map((id) => JSON.stringify(id)).join(', ')}. ` +
    'Ids key the dependency graph, so a repeat drops a task without a trace. Give every task its own id and re-run.'
  )
}

// Expand each classified wave into the sub-waves that are actually safe to run in parallel.
const waves = []
for (const w of rawWaves) {
  const subWaves = splitByFileOwnership(w.tasks ?? [])
  if (subWaves.length > 1) {
    log(`Group split into ${subWaves.length}: ${(w.tasks ?? []).length} task(s) exceeded the width of ${WAVE_CAP} or shared a file`)
  }
  waves.push(...subWaves.map((tasks) => ({ tasks })))
}

const skillLine = (cfg.domainSkills ?? []).length
  ? `Load the DOMAIN skill matching your files for conventions (knowledge only, no agent dispatch): ${(cfg.domainSkills ?? []).map((d) => `${d.skill} for ${d.match}`).join('; ')}. `
  : ''

// Rolling dispatch. A wave barrier makes every task in wave N+1 wait for the SLOWEST task in wave
// N, including the ones it never reads — so a plan of disjoint tasks ran in the sum of its waves
// instead of the length of its longest chain. Here a task starts the moment its own dependencies
// are done and no in-flight task holds one of its files.
//
// Two bounds keep this from becoming a loop with no floor:
//   - the topological check below throws on a dependency cycle instead of awaiting a promise that
//     can never settle (`Promise.all` on a cycle is a hang, not an error);
//   - `WAVE_CAP` still bounds how many run at once, now as in-flight width rather than wave size.
const flat = waves.flatMap((w, i) => w.tasks.map((t) => ({ ...t, wave: i })))
const byId = new Map(flat.map((t) => [t.id, t]))

// A task with no usable `needs` falls back to the old barrier — everything in an earlier wave.
// That is the honest degradation: no declared edge means the classifier could not name what is
// read, and guessing "independent" there is how a task runs against a file that does not exist yet.
const depsOf = (t) => {
  const declared = (t.needs ?? []).filter((id) => id !== t.id && byId.has(id))
  return declared.length ? declared : flat.filter((o) => o.wave < t.wave).map((o) => o.id)
}

// Topological order, and the cycle guard. Kahn's algorithm: whatever is left when no node has an
// in-degree of zero is the cycle, and it is named rather than hung on.
const order = []
const remaining = new Map(flat.map((t) => [t.id, new Set(depsOf(t))]))
let progressed = true
while (remaining.size && progressed) {
  progressed = false
  for (const [id, deps] of remaining) {
    if ([...deps].every((d) => !remaining.has(d))) {
      order.push(byId.get(id)); remaining.delete(id); progressed = true
    }
  }
}
if (remaining.size) {
  throw new Error(
    `ultra-build: the task dependencies form a cycle — ${[...remaining.keys()].join(' -> ')}. ` +
    'Fix the plan\'s Needs edges; refusing to dispatch a graph that cannot finish.'
  )
}

// In-flight width and file ownership, enforced here rather than trusted from the plan.
const held = new Set()
let inFlight = 0
const waiting = []
const wake = () => { while (waiting.length) waiting.shift()() }
const canStart = (t) => inFlight < WAVE_CAP && !(t.files ?? []).some((f) => held.has(f))
const acquire = async (t) => {
  // Awaiting in this loop IS the wait: the task parks until a release wakes it, re-checks, and
  // parks again. There is nothing to collect into a Promise.all — the condition is what it waits on.
  // oxlint-disable-next-line no-await-in-loop
  while (!canStart(t)) await new Promise((resolve) => waiting.push(resolve))
  inFlight++
  for (const f of t.files ?? []) held.add(f)
}
const release = (t) => {
  inFlight--
  for (const f of t.files ?? []) held.delete(f)
  wake()
}

// Every dispatched task produces an outcome, including the ones whose agent died. `agent()` returns
// null when the spawn produced nothing, and dropping those — which is what the collection below used
// to do with `.filter(Boolean)` — deletes the task from the outcome while the run reports the
// survivors as a clean build. A dead agent is a FAILED task: recorded, with its id and the reason.
//
// The id is the ORCHESTRATOR's, never the agent's self-report. A model that renames itself in its
// own result must not make its task look unaccounted-for in the reconciliation after the loop.
const TERMINAL = new Set(['done', 'partial', 'blocked', 'failed'])
const outcomeOf = (t, r) => {
  if (!r || typeof r !== 'object') {
    return { id: t.id, status: 'failed', changedPaths: [], notes: `${t.agent} returned no result — the agent died or produced nothing, so this task was NOT implemented` }
  }
  if (!TERMINAL.has(r.status)) {
    return { ...r, id: t.id, status: 'failed', changedPaths: r.changedPaths ?? [], notes: `${r.notes ?? ''} [reported a status this workflow cannot interpret: ${JSON.stringify(r.status)} — treated as failed rather than as done]`.trim() }
  }
  return { ...r, id: t.id }
}

log(`Rolling dispatch: ${order.length} task(s), up to ${WAVE_CAP} in flight, dependency-ordered`)
const started = new Map()
for (const t of order) {
  started.set(t.id, (async () => {
    await Promise.all(depsOf(t).map((d) => started.get(d)))
    await acquire(t)
    try {
      return outcomeOf(t, await agent(
        `Implement this task from ${PLAN_PATH}. ${skillLine}Do NOT invoke any process skill that dispatches agents — this workflow already orchestrates; implement directly (the debug chain is reserved for ultra-verify's fix loop).
TASK ${t.id}: ${t.title}
DETAIL: ${t.detail ?? ''}
FILES YOU OWN (do not touch anything outside this set): ${JSON.stringify(t.files)}
ACCEPTANCE: ${t.criterion}
${GIT_RAILS}
Return id, status, changedPaths, gateEvidence.`,
        { agentType: AG(t.agent), phase: 'Act', schema: TASK_RESULT, label: `${t.agent}:${t.id}`, model: M(t.agent) }
      ))
    } finally {
      release(t)
    }
  })())
}
results.push(...(await Promise.all(started.values())))

// Every planned task, exactly once, in a terminal state — checked, not assumed. This is the
// structural half of the promise in the design notes at the top of this file: the run accounts for
// the whole plan or it throws. Without it a three-task plan whose scheduler lost two of them
// returned `tasksTotal: 1, done: 1, blocked: []` and handed the tree to verification as complete,
// which is a false success — the most expensive thing this workflow can produce.
const seen = new Map()
for (const r of results) seen.set(r.id, (seen.get(r.id) ?? 0) + 1)
const unaccounted = plannedIds.filter((id) => (seen.get(id) ?? 0) !== 1)
const unplanned = [...seen.keys()].filter((id) => !plannedIds.includes(id))
if (unaccounted.length || unplanned.length || results.length !== plannedTasks) {
  throw new Error(
    `ultra-build: ${results.length} outcome(s) for ${plannedTasks} planned task(s) — the run cannot account for the whole plan. ` +
    (unaccounted.length ? `Never reported exactly once: ${unaccounted.map((id) => JSON.stringify(id)).join(', ')}. ` : '') +
    (unplanned.length ? `Reported but never planned: ${unplanned.map((id) => JSON.stringify(id)).join(', ')}. ` : '') +
    'Refusing to hand a partial build to verification as a complete one.'
  )
}

const blocked = results.filter((r) => r.status !== 'done')
return {
  planPath: PLAN_PATH,
  wavesPlanned: rawWaves.length,
  dispatchGroups: waves.length, // the fallback ordering; real dispatch is per task, not per group
  tasksTotal: plannedTasks, // what the PLAN asked for, never what survived — the two diverging is the false success above
  done: results.filter((r) => r.status === 'done').length,
  blocked: blocked.map((r) => ({ id: r.id, status: r.status, notes: r.notes })),
  changedPaths: [...new Set(results.flatMap((r) => r.changedPaths ?? []))],
  // One writer per file, made checkable: `hooks/graph_guardrails.py` reads this list from
  // `.graph-powers/logs/write-lease.json` and refuses a write outside it. The script cannot write
  // the file, so the caller does — see `commands/plan.md`.
  writeLease: [...new Set(rawWaves.flatMap((w) => (w.tasks ?? []).flatMap((t) => t.files ?? [])))],
  next: blocked.length ? 'Resolve blocked tasks, then run ultra-verify' : `ultra-verify ${PLAN_PATH}`,
}
