export const meta = {
  name: 'ultra-plan',
  description: 'Fan-out research from many angles + synthesize one reviewed implementation plan (framing → competing approaches → writing-plans format → anchor-scored evaluator gate). Writes the plan to the project\'s plan directory and commits nothing.',
  whenToUse: 'Start of any L3+ feature. Researches the codebase + external docs in parallel, drafts competing approaches, synthesizes one phased plan with atomic disjoint-file tasks, then adversarially reviews it against the calibration anchors. L1-L2 trivial tasks exit early (direct edit). Pass the task as args, or { task, config }.',
  phases: [
    { title: 'Frame', model: 'haiku' },
    { title: 'Fan-out research' },
    { title: 'Synthesize' },
    { title: 'Plan review' },
  ],
}

// ── Design notes (read before editing) ───────────────────────────────────────
// After editing, run `node .github/check_workflows.mjs`. Top-level `return` is legal only because
// the runtime wraps the body, so `node --check` and most linters reject this file outright; that
// script wraps it the same way the runtime does, and it is the only syntax gate there is. A stray
// backtick inside one of the prompt template literals is otherwise invisible until a run starts
// and has already spent agents.
//
// This file ships inside the plugin and runs in repositories nobody here has seen. Nothing in it
// may name a product, a stack, a package manager, a provider or a directory layout — all of that
// arrives through `config` and traces back to `schema/config.schema.json`.
//
// This workflow IS the planning chain run as deterministic orchestration. Sub-agents must NOT
// invoke `Skill("planning")` — that skill is itself an agent-dispatching chain (Phase A fans out
// explorer + librarian, its gates re-dispatch) and `project-planner` carries the Agent tool, so an
// inner `Skill()` call re-fans-out and the spawn count explodes. Each agent instead READS the
// relevant guide for conventions and format, and does focused work.
//   Guide map, all under `<pluginRoot>/skills/planning/references/`:
//     framing + Phase 0  → phase-a-brainstorm.md § Phase 0 — Framing / § Step 4
//     plan format        → phase-b-writing-plans.md (+ § Risk for L6+ pre-mortem/ADR)
//     review anchors     → loop-engineering.md § Calibration anchors
//     agent routing      → dispatch-matrix.md
//
// Worst-case spawns: 1 config (bare invocation only) + 1 frame + (≤4 explore + 1 librarian)
//   + 2 approaches + 1 synth + 1 review (+1 revise +1 re-review) (+1 L6 architecture pass) = ≤ 14.
//
// Fail fast, never half-succeed: each stage throws if its input did not survive (dead frame → no
// angles; every research agent dead; both approaches dead; synthesize returned no path). All four
// throws fire BEFORE the spawns they protect and before any plan file exists, so nothing is lost.
// This is deliberate and does not contradict the no-throw rule on the review gate below, which
// exists to preserve a plan that IS already on disk.
//
// Model tiering: retrieval and classification (frame + explore) → 'haiku'. Judgment (approaches,
// synthesize, review, librarian) inherits the main-loop model — plan quality depends on it.
//
// Review gate: the anchor thresholds are ENFORCED in code (§ Gate, bottom), not merely stated in
// the prompt. The evaluator self-reports `verdict`, so nothing stopped it from returning APPROVED
// with a 6 — the scores it gave us are re-checked here, and `next` refuses to hand a failed plan
// on. Never throw on a failed gate: the plan file is already on disk and the caller needs the
// payload to decide what to do with it.
// ─────────────────────────────────────────────────────────────────────────────

const TASK = typeof args === 'string' ? args : (args?.task ?? args?.description ?? '')
if (!TASK) throw new Error('ultra-plan: pass the feature/task description as args')

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
const CONFIG_SHAPE = { type: 'object', required: ['pluginRoot', 'planDir'], properties: {
  pluginRoot: { type: 'string' },
  planDir: { type: 'string' },
  displayName: { type: 'string' },
  locale: { type: 'string' },
  paths: { type: 'object', properties: {
    frontendRoot: { type: 'string' }, backendRoot: { type: 'string' },
    schemaRoot: { type: 'string' }, mobileRoot: { type: 'string' },
  } },
  riskSurfaces: { type: 'array', items: { type: 'string' } },
} }

async function resolveConfig() {
  if (args?.config) return args.config
  return await agent(
    `Two things, both read-only.

1. Locate the graph-powers plugin root — the directory that contains \`skills/planning/references/phase-b-writing-plans.md\`. Use Glob, never a hardcoded path: it differs per machine and per install. Return it as \`pluginRoot\`, without a trailing slash. If you cannot find it, return the empty string rather than guessing.

2. Read \`.graph-powers/config.json\` at the repository root (fall back to \`.claude/config.json\`, then to an empty object — a project with no config is valid and takes the defaults). Return, flattened:
     planDir       <- paths.planDir, else "docs/plans"
     displayName   <- project.displayName, else project.name, else ""
     locale        <- project.locale, else "en-US"
     paths         <- paths.frontendRoot / backendRoot / schemaRoot / mobileRoot; omit any that is absent
     riskSurfaces  <- chain.riskSurfaces, else ["auth","payment","PII","schema","env","ci"]

Do not invent a value that is not in the file: an absent field is absent, never a plausible default of your own.`,
    { agentType: AG('explorer'), phase: 'Frame', schema: CONFIG_SHAPE, label: 'config', model: 'haiku' }
  )
}

const cfg = (await resolveConfig()) ?? {}
const paths = cfg.paths ?? {}
const PLAN_DIR = cfg.planDir || 'docs/plans'
const SURFACES = (cfg.riskSurfaces ?? []).length
  ? cfg.riskSurfaces
  : ['auth', 'payment', 'PII', 'schema', 'env', 'ci']

if (!cfg.pluginRoot) {
  throw new Error('ultra-plan: could not locate the graph-powers plugin root, so no agent can read the planning guides. Pass it as args.config.pluginRoot.')
}
const SKILL = `${cfg.pluginRoot}/skills/planning/references`

// Shared guards — appended to every prompt instead of repeating per agent.
const NO_SKILL = 'Do NOT invoke Skill("planning") — this workflow owns the orchestration; READ the named guide only for format and conventions.'
const RO = 'Read-only — never write or commit.'

// Only the lanes this repository actually has, so the plan cannot route a task to an agent with
// nothing to work on. Kept identical to ultra-build's enum: a plan that names an agent ultra-build
// cannot route is a plan that silently reassigns half its tasks.
const LANES = [
  paths.frontendRoot && 'frontend-specialist',
  'debugger',
  'performance-optimizer',
  paths.mobileRoot && 'mobile-developer',
].filter(Boolean)

// riskSurfaces is `required`: it is the sole switch for the whole L6 branch (pre-mortem, ADR,
// Mode 3) via isL6 below, so an omitted key would silently disable all three.
const FRAME = { type: 'object', required: ['intentLevel', 'restatedGoal', 'researchAngles', 'riskSurfaces'], properties: {
  intentLevel: { type: 'string', enum: ['L1', 'L2', 'L3', 'L4', 'L5', 'L6'] },
  restatedGoal: { type: 'string' },
  unknowns: { type: 'array', items: { type: 'string' } },
  researchAngles: { type: 'array', items: { type: 'string' } },
  riskSurfaces: { type: 'array', items: { type: 'string', enum: [...SURFACES, 'none'] } },
} }
const RESEARCH = { type: 'object', required: ['angle', 'findings'], properties: {
  angle: { type: 'string' },
  findings: { type: 'array', items: { type: 'string' } },
  reusable: { type: 'array', items: { type: 'object', properties: { path: { type: 'string' }, why: { type: 'string' } } } },
  citations: { type: 'array', items: { type: 'string' } },
} }
const APPROACH = { type: 'object', required: ['name', 'summary', 'tradeoffs'], properties: {
  name: { type: 'string' }, summary: { type: 'string' }, tradeoffs: { type: 'string' }, risk: { type: 'string' },
} }
const PLAN = { type: 'object', required: ['planPath', 'recommendedApproach', 'taskCount'], properties: {
  planPath: { type: 'string' }, recommendedApproach: { type: 'string' }, taskCount: { type: 'number' }, summary: { type: 'string' },
} }
// Review verdict is derived from the calibration anchors, not vibes (skill GATE 2 goal).
const REVIEW = { type: 'object', required: ['verdict', 'scores'], properties: {
  verdict: { type: 'string', enum: ['APPROVED', 'REVISION_REQUIRED'] },
  scores: { type: 'object', required: ['completeness', 'atomicity', 'riskCoverage', 'dependencyOrder'], properties: {
    completeness: { type: 'number' }, atomicity: { type: 'number' }, riskCoverage: { type: 'number' }, dependencyOrder: { type: 'number' },
  } },
  issues: { type: 'array', items: { type: 'string' } },
} }
// Schema'd so a revision that never happened is distinguishable from one that did.
const REVISED = { type: 'object', required: ['revised'], properties: {
  revised: { type: 'boolean' }, changes: { type: 'string' },
} }

// 1. Frame — classify intent + list the highest-signal research angles (haiku)
phase('Frame')
const frame = await agent(
  `Frame and classify this task following ${SKILL}/phase-a-brainstorm.md § Phase 0 — Framing (problem framing + scope decomposition + divergent angles). ${NO_SKILL}
TASK: ${TASK}
Return: intent level L1-L6 (per the skill's Step 0 tier gate), a one-paragraph restated goal, open unknowns, and 3-4 research angles — only the highest-signal ones (prefer fewer, sharper angles; mix codebase areas + external topics), plus risk surfaces (${SURFACES.join('/')}, or none). ${RO}`,
  { agentType: AG('explorer'), phase: 'Frame', schema: FRAME, label: 'frame', model: 'haiku' }
)

// A dead frame is not an L4 task. With no angles there is nothing to research (the plan would be
// synthesized from the librarian alone, or from nothing) and with no riskSurfaces the L6 branch
// evaporates. Fail here: it is before every expensive spawn, and no plan file exists yet.
if (!frame?.researchAngles?.length) {
  throw new Error('ultra-plan: the frame agent returned no research angles — cannot tier or research this task')
}
const level = frame.intentLevel ?? 'L4'
const risky = (frame.riskSurfaces ?? []).filter((r) => r && r !== 'none')
const isL6 = level === 'L6' || risky.length > 0

// Tier gate (skill Step 0): trivial tasks get no plan — direct edit is faster than the chain.
// A risk surface overrides the tier: a haiku "L2" on a task touching a declared risk surface must
// not exit with no plan AND no risk review.
if ((level === 'L1' || level === 'L2') && !risky.length) {
  return {
    skipped: true,
    intentLevel: level,
    restatedGoal: frame.restatedGoal,
    reason: `${level} trivial — the planning chain's Step 0 routes this to direct edit (no plan file). Implement directly; no ultra-plan output. If you disagree with the classification, re-run stating an explicit tier floor in the task string.`,
  }
}

// 2. Fan-out — parallel research (codebase haiku + 1 external) AND 2 competing approaches
phase('Fan-out research')
const angles = frame.researchAngles.slice(0, 4)
// Librarian FIRST: the results array is JSON-stringified and hard-sliced before it reaches the
// downstream prompts, so whatever sits last is what gets truncated away. External findings
// (security advisories, version pitfalls) are the most expensive to recover and the least
// recoverable by a later agent — they must not be the tail.
const research = (await parallel([
  () => agent(
    `Research EXTERNAL knowledge for this task: library/API behavior, current best practices, version pitfalls, security advisories.
TASK: ${TASK}
Return findings + citations. Never touch the filesystem.`,
    { agentType: AG('librarian'), phase: 'Fan-out research', schema: RESEARCH, label: 'librarian' }
  ),
  ...angles.map((a, i) => () => agent(
    `Research this angle (internal codebase ONLY): existing patterns, reusable helpers/primitives, impacted files, conventions to match.
TASK: ${TASK}
ANGLE: ${a}
Return concrete findings + reusable files (path + why). ${RO}`,
    { agentType: AG('explorer'), phase: 'Fan-out research', schema: RESEARCH, label: `explore:${i}`, model: 'haiku' }
  )),
])).filter(Boolean)
// parallel() maps a dead agent to null, so a total wipeout arrives here as []. Synthesizing from
// [] produces an internally consistent plan with no evidence behind it — and the reviewer only
// reads the plan file, never the research, so that plan scores well and passes the gate.
if (!research.length) {
  throw new Error('ultra-plan: every research agent failed — refusing to synthesize a plan with no evidence behind it')
}

const riskWord = cfg.displayName ? `${cfg.displayName} risks` : 'project-specific risks'
const approaches = (await parallel(
  ['reuse-first', 'robustness-first'].map((lens) => () => agent(
    `Propose ONE implementation approach through the "${lens}" lens, following the option format in ${SKILL}/phase-a-brainstorm.md § Step 4 (recommendation + pros/cons + ${riskWord} + layer chain). ${NO_SKILL}
TASK: ${TASK}
RESEARCH: ${JSON.stringify(research).slice(0, 6000)}
Return name, summary, tradeoffs, risk. ${RO}`,
    { agentType: AG('project-planner'), phase: 'Fan-out research', schema: APPROACH, label: `approach:${lens}` }
  ))
)).filter(Boolean)
if (!approaches.length) {
  throw new Error('ultra-plan: both competing-approach agents failed — refusing to synthesize with nothing to choose between')
}

// Anonymize before the synthesizer chooses. `robustness-first` and `reuse-first` are loaded names:
// whichever label sounds safer for the task wins arguments the content never had to make, and the
// synthesizer is explicitly told to "pick the best approach". Stripping the label forces the choice
// onto the tradeoffs. Order is derived from a content hash, not from the lens order — `Math.random`
// throws in workflow scripts (it would break resume), and a fixed order just trades label bias for
// position bias. The legend is kept so the returned winner is still traceable to its lens.
const contentHash = (str) => {
  let h = 0
  for (let i = 0; i < str.length; i++) h = (Math.imul(h, 31) + str.charCodeAt(i)) | 0
  return h
}
const LENSES = ['reuse-first', 'robustness-first']
const blinded = approaches
  .map((a, i) => ({ a, lens: LENSES[i] ?? `lens-${i}`, key: contentHash(JSON.stringify(a)) }))
  .sort((x, y) => x.key - y.key)
// The objects were just built by the `map` above, so labelling them in place copies nothing.
for (const [i, e] of blinded.entries()) e.id = String.fromCharCode(65 + i)
const approachesForSynthesis = blinded.map((e) => ({ ...e.a, name: `Approach ${e.id}` }))
const approachLegend = Object.fromEntries(blinded.map((e) => [`Approach ${e.id}`, { lens: e.lens, name: e.a.name }]))
log(`Approaches anonymized for synthesis: ${blinded.map((e) => `${e.id}=${e.lens}`).join(' · ')}`)

// 3. Synthesize — merge into one phased plan file (writing-plans format)
phase('Synthesize')
const schemaRule = paths.schemaRoot
  ? ` Carry over the one semantic exception: any task writing ${paths.schemaRoot}/** MUST be [SEQUENTIAL] and alone in its wave, because foreign-key and index ordering make schema work unsafe to parallelize.`
  : ''
const l6Extra = isL6
  ? `\nL6+/RISKY (${[level, ...risky].join(', ')}): per ${SKILL}/phase-b-writing-plans.md § Risk, ALSO add a pre-mortem table (Probability×Impact, BLOCK items mitigated), an ADR for the chosen approach, and a per-task Risk field. Add a tenant/PII/idempotency/index guard note to each affected task.`
  : ''
const plan = await agent(
  `Synthesize ONE phased implementation plan. Read ${SKILL}/phase-b-writing-plans.md and follow its format exactly: atomic 2-5min tasks → [SEQUENTIAL]/[PARALLEL-SAFE] phase grouping (layer order via ${SKILL}/layer-map.md) → DISJOINT-file enforcement per wave → dispatch matrix table (agent/skill per ${SKILL}/dispatch-matrix.md) → Loop contract. ${NO_SKILL}
TASK: ${TASK}
FRAME: ${JSON.stringify(frame)}
RESEARCH: ${JSON.stringify(research).slice(0, 12000)}
APPROACHES (anonymized on purpose — judge the tradeoffs, you are not told which lens produced which): ${JSON.stringify(approachesForSynthesis)}
Pick + justify the best approach (graft good ideas from the runner-up). Write EVERY task in the grammar of ${SKILL}/phase-b-writing-plans.md § Step 1 — a \`- [ ] **T<n>** — <action>\` checkbox carrying \`Owns:\` (the paths this task alone writes), \`Needs:\` naming the task it reads AND what it reads from it, \`Agent:\` — MUST be one of ${LANES.join('|')} — and \`CHECK:\`/\`EXPECT:\`/\`EVIDENCE: pending\` in place of a prose acceptance line. \`Needs:\` with no payload named is a false edge: delete it and let the two tasks run together. Close every phase with its gate block, and put the whole-project commands THERE rather than inside each task. Those are the only values ultra-build can route: where phase-b-writing-plans.md and dispatch-matrix.md offer a wider list including "main", they are describing the human chain, which has a main-thread lane — this workflow does not, so ignore that column here and send docs/config/schema tasks to debugger.${schemaRule}${l6Extra}
Write the plan to ${PLAN_DIR}/<YYYY-MM-DD>-<slug>/PLAN.md — one plan is one directory, per ${cfg.pluginRoot}/references/shared/007-path-conventions.md — using today's date, which you already have — do NOT shell out for it. \`date +%F\` is coreutils: on Windows \`date\` either opens an interactive prompt asking for a new system date, or rejects the argument. The path is what the build step receives as its input, so an invented date is a broken handoff. The plan MUST carry, besides its phases: ## Destination, ## Reuse ledger, ## Regression watchlist, ## Execution graph, ## Verification with executable steps, ## Rollback, ## Out of scope and ## Not yet specified — /verify reads the ledger, the watchlist and the rollback verbatim, and a plan without them degrades it to a generic gate run. HARD: commit NOTHING — leave the file in the working tree only.
Return planPath, recommendedApproach, taskCount, summary.`,
  { agentType: AG('project-planner'), phase: 'Synthesize', schema: PLAN, label: 'synthesize' }
)
// No plan path = no plan. Stop before the review spawns: `PLAN.planPath` is `required` but the
// schema still accepts "", and a review of "the plan at undefined" burns up to 4 opus agents and
// can end with approved:true pointing at nothing (ultra-build treats "undefined" as a real path).
if (!plan?.planPath) {
  throw new Error('ultra-plan: the synthesize agent returned no plan path — refusing to spend review spawns on a plan that does not exist')
}

// 4. Adversarial plan review — evaluator Mode 1, scored against the calibration anchors
phase('Plan review')
const ANCHORS = 'Score 1-10 on the four calibration anchors in ' + SKILL + '/loop-engineering.md § Calibration anchors. Verdict APPROVED only if Completeness ≥ 8 AND Atomicity ≥ 7 AND Risk Coverage ≥ 7 AND Dependency Order ≥ 8; otherwise REVISION_REQUIRED with concrete issues.'
const reviewPrompt = (n) =>
  `evaluator Mode 1 (Plan Review)${n > 1 ? ' — re-review after revision' : ''}. Read the plan at ${plan?.planPath}. Critique for: ambiguities, vague or missing acceptance criteria, scope creep, wrong agent dispatch, disjoint-file violations, missing tenant/PII/idempotency/index guards, layer-ordering errors. ${ANCHORS} ${RO}`

let review = await agent(reviewPrompt(1), { agentType: AG('evaluator'), phase: 'Plan review', schema: REVIEW, label: 'review:1' })
// Only revise when there is something to revise, and only re-review when the revision actually
// happened: an unschema'd revise agent that died silently is otherwise indistinguishable from a
// real revision, and the re-review then spends an opus agent re-reading an unchanged file and
// returning the same issues — which reads as "the planner could not fix these".
if (review?.verdict === 'REVISION_REQUIRED' && review?.issues?.length) {
  const revision = await agent(
    `Revise the plan at ${plan.planPath} to resolve these issues, keeping the ${SKILL}/phase-b-writing-plans.md format. ${NO_SKILL} Keep it on disk, commit nothing.
ISSUES: ${JSON.stringify(review.issues)}
Return revised:true only if you actually edited the file, plus a one-line summary of the changes.`,
    { agentType: AG('project-planner'), phase: 'Plan review', schema: REVISED, label: 'revise' }
  )
  if (revision?.revised) {
    review = await agent(reviewPrompt(2), { agentType: AG('evaluator'), phase: 'Plan review', schema: REVIEW, label: 'review:2' })
  } else {
    log('Revision did not happen (agent returned nothing or reported no edit) — keeping the first review verdict')
  }
}

// L6+/risky: one architecture pass (skill GATE 3 — evaluator Mode 3) on top of Mode 1.
let architecture = null
if (isL6) {
  architecture = await agent(
    `evaluator Mode 3 (Architecture Analysis) on the plan at ${plan?.planPath}. This task touches risky surfaces (${[level, ...risky].join(', ')}). Assess: irreversible-data risk, tenant isolation, auth/permission scope, migration safety, idempotency, rollback path.
VERDICT RULE — apply literally, because this verdict BLOCKS the run: return APPROVED unless you find a blocking architectural defect (irreversible or unrecoverable data loss · cross-tenant or PII exposure · auth/permission bypass · unsafe or irreversible migration · no rollback path). Advisory improvements, "consider also", and second-order nice-to-haves belong in issues and must NOT flip the verdict to REVISION_REQUIRED. Mode 3's own rubric has no pass/fail concept, so this rule is the criterion.
Return verdict + concrete issues. ${RO}`,
    { agentType: AG('evaluator'), phase: 'Plan review', schema: REVIEW, label: 'review:arch' }
  )
}

// ── Gate — the anchors are a contract, not a suggestion ──────────────────────
// ANCHORS (above) tells the evaluator the thresholds, but the verdict is self-reported:
// re-check the scores it returned so an APPROVED that misses a floor cannot pass, and a
// REVISION_REQUIRED that survived the revise pass cannot be handed off as if it were fine.
const ANCHOR_FLOOR = { completeness: 8, atomicity: 7, riskCoverage: 7, dependencyOrder: 8 }
const belowFloor = Object.entries(ANCHOR_FLOOR)
  .filter(([k, min]) => !(review?.scores?.[k] >= min))
  .map(([k, min]) => `${k} ${review?.scores?.[k] ?? 'n/a'} < ${min}`)
// A risky task whose architecture pass never returned is NOT the same as one that passed:
// a dead Mode 3 agent must block, or the L6 gate silently evaporates. Same for review.
const archMissing = isL6 && !architecture
const archBlocked = archMissing || (!!architecture && architecture.verdict !== 'APPROVED')
const approved = review?.verdict === 'APPROVED' && belowFloor.length === 0 && !archBlocked
const gateReasons = [
  !review ? 'plan review agent returned nothing' : '',
  review?.verdict === 'REVISION_REQUIRED' ? 'evaluator verdict REVISION_REQUIRED' : '',
  review && belowFloor.length ? `anchors below floor: ${belowFloor.join(', ')}` : '',
  archMissing ? `architecture pass (evaluator Mode 3) did not return on a risky task (${[level, ...risky].join(', ')})` : '',
  !archMissing && archBlocked ? 'architecture pass (evaluator Mode 3) verdict not APPROVED' : '',
].filter(Boolean)
if (!approved) log(`Plan review did NOT pass — ${gateReasons.join(' · ')}`)

return {
  planPath: plan.planPath,
  intentLevel: level,
  riskSurfaces: risky,
  approach: plan?.recommendedApproach,
  approachChosen: approachLegend[plan?.recommendedApproach] ?? null, // de-anonymized: which lens actually won
  approachLegend,
  taskCount: plan?.taskCount,
  approved,
  reviewVerdict: review?.verdict,
  reviewScores: review?.scores,
  belowFloor,
  architectureVerdict: architecture?.verdict ?? null,
  openIssues: [...(review?.issues ?? []), ...(architecture?.issues ?? [])],
  next: approved
    ? `Present the plan for human approval, then run ultra-build with ${plan?.planPath}`
    : `BLOCKED — the plan did NOT pass review (${gateReasons.join(' · ')}). Do NOT run ultra-build yet: resolve openIssues in ${plan?.planPath}, then re-review. The plan file is on disk and uncommitted.`,
}
