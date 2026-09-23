#!/usr/bin/env bun
/**
 * Contract for the centralized Codex semantic model policy.
 *
 * This is intentionally independent of generated files: it calls the exported resolver directly,
 * so overrides and compatibility behaviour cannot be made to pass by duplicating resolver logic in
 * a checker. The Python artefact checks consume the same explicit oracle for clone/native parity.
 */

import {
  existsSync,
  mkdtempSync,
  mkdirSync,
  readFileSync,
  rmSync,
  symlinkSync,
  writeFileSync,
} from "node:fs";
import { spawnSync } from "node:child_process";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const EXPECTED_POLICY = {
  evaluator: ["judge", "gpt-6-astra", "high"],
  "security-reviewer": ["judge", "gpt-6-astra", "high"],
  "skill-improver": ["judge", "gpt-6-astra", "high"],
  "ui-ux-designer": ["judge", "gpt-6-astra", "high"],
  "project-planner": ["architect", "gpt-6-astra", "high"],
  debugger: ["executor", "gpt-6-luna", "medium"],
  "frontend-specialist": ["executor", "gpt-6-luna", "medium"],
  "mobile-developer": ["executor", "gpt-6-luna", "medium"],
  "performance-optimizer": ["executor", "gpt-6-luna", "medium"],
  verification: ["verifier", "gpt-6-astra", "high"],
  explorer: ["scout", "gpt-6-luna", "medium"],
  librarian: ["scout", "gpt-6-luna", "medium"],
};

const READ_ONLY = new Set([
  "evaluator",
  "security-reviewer",
  "skill-improver",
  "ui-ux-designer",
  "explorer",
  "librarian",
  "verification",
]);

const policy = await import("../codex/model-policy.mjs");

const {
  CODEX_AGENT_PROFILES,
  CODEX_PROFILE_DEFAULTS,
  CODEX_REASONING_EFFORTS,
  CODEX_TOP_LEVEL_REASONING_EFFORTS,
  CODEX_WARNING_CATEGORIES,
  resolveCodexAgentPolicy,
  resolveCodexTopLevelProfile,
} = policy;

const fail = (message) => {
  throw new Error(`Codex semantic model policy check: ${message}`);
};
const assert = (condition, message) => {
  if (!condition) fail(message);
};
const effortOf = (value) => value?.reasoningEffort ?? value?.effort;
const profileOf = (value) => value?.profile ?? value?.semanticProfile;
const compact = (value) => ({
  profile: profileOf(value),
  model: value?.model,
  effort: effortOf(value),
  topLevelOnly: Boolean(value?.topLevelOnly),
});
const equal = (a, b) => JSON.stringify(a) === JSON.stringify(b);

const sourceAgent = (name, [profile, _model, effort]) => ({
  name,
  model: profile === "scout" ? "haiku" : "opus",
  effort: effort === "max" ? "xhigh" : "low",
  role_type: profile === "scout" ? "researcher" : profile === "judge" ? "evaluator" : "worker",
  disallowedTools: READ_ONLY.has(name) ? ["Write", "Edit"] : ["Read", "Write", "Edit"],
});
const resolveRaw = (name, settings = {}) =>
  resolveCodexAgentPolicy(name, settings, sourceAgent(name, EXPECTED_POLICY[name]));
const resolve = (name, settings = {}) => compact(resolveRaw(name, settings));
const rejects = (action, message) => {
  let rejected = false;
  try {
    action();
  } catch {
    rejected = true;
  }
  assert(rejected, message);
};

assert(Object.keys(EXPECTED_POLICY).length === 12, "oracle must contain all 12 canonical agents");
for (const [name, value] of Object.entries({
  CODEX_AGENT_PROFILES,
  CODEX_PROFILE_DEFAULTS,
  CODEX_WARNING_CATEGORIES,
})) {
  assert(value && typeof value === "object", `${name} is missing`);
}
const efforts = Array.from(CODEX_REASONING_EFFORTS ?? []);
assert(efforts.includes("max"), `max is not accepted; efforts=${JSON.stringify(efforts)}`);
const topLevelEfforts = Array.from(CODEX_TOP_LEVEL_REASONING_EFFORTS ?? []);
assert(
  topLevelEfforts.includes("low") && topLevelEfforts.includes("ultra"),
  "top-level policy must accept both economical low and Ultra efforts",
);

for (const [name, expected] of Object.entries(EXPECTED_POLICY)) {
  const actual = resolve(name);
  assert(
    equal(actual, {
      profile: expected[0],
      model: expected[1],
      effort: expected[2],
      topLevelOnly: false,
    }),
    `${name}: expected ${expected.join(" / ")}, got ${JSON.stringify(actual)}`,
  );
}

// Missing settings must be deterministic, and cannot fall through to session inheritance.
for (const name of Object.keys(EXPECTED_POLICY)) {
  assert(equal(resolve(name), resolve(name, {})), `${name}: missing config is not deterministic`);
}

// Literal policy cases keep precedence and downgrade coverage in one readable table.
const perAgent = { model: "override-model", reasoningEffort: "high" };
const scoutOverride = { scout: { model: "gpt-5.6-terra", reasoningEffort: "high" } };
for (const [name, settings, expected, warning] of [
  [
    "explorer",
    { agentOverrides: { explorer: perAgent }, agents: { explorer: perAgent } },
    ["scout", "override-model", "high"],
  ],
  [
    "explorer",
    { agents: { explorer: perAgent } },
    ["scout", "override-model", "high"],
    "modelOverrideUnverified",
  ],
  ["explorer", { profile: "judge" }, ["judge", "gpt-6-astra", "high"], "profileOverrideUnverified"],
  ["explorer", { profiles: scoutOverride }, ["scout", "gpt-5.6-terra", "high"]],
  [
    "explorer",
    {
      profiles: scoutOverride,
      agents: { explorer: { model: "agent-model", reasoningEffort: "low" } },
    },
    ["scout", "agent-model", "low"],
  ],
  [
    "verification",
    { model: "flat-model", reasoningEffort: "low" },
    ["verifier", "flat-model", "low"],
  ],
  [
    "evaluator",
    { reasoningEffort: "ultra" },
    ["judge", "gpt-6-astra", "high"],
    "topLevelEffortDowngraded",
  ],
  [
    "debugger",
    { profile: "native-economic" },
    ["executor", "gpt-6-luna", "medium"],
    "topLevelProfileDowngraded",
  ],
]) {
  const actual = resolveRaw(name, settings);
  assert(
    equal(compact(actual), {
      profile: expected[0],
      model: expected[1],
      effort: expected[2],
      topLevelOnly: false,
    }),
    `${name}: policy case ${JSON.stringify(settings)} expected ${expected.join("/")}`,
  );
  if (warning) {
    assert(equal(actual.warnings, [CODEX_WARNING_CATEGORIES[warning]]), `${name}: lost ${warning}`);
  }
}
for (const [name, settings, field, expected] of [
  [
    "evaluator",
    { models: { heavy: "legacy-heavy" }, reasoningEffort: "high" },
    "model",
    "legacy-heavy",
  ],
  ["explorer", { models: { light: "legacy-light" } }, "model", "legacy-light"],
  ["evaluator", { reasoningEffort: "max" }, "effort", "max"],
])
  assert(resolve(name, settings)[field] === expected, `${name}: legacy/max override lost`);

const extensionAgent = resolveCodexAgentPolicy(
  "extension-agent",
  {},
  {
    name: "extension-agent",
    model: "opus",
    effort: "xhigh",
  },
);
assert(
  extensionAgent.profile === null && extensionAgent.reasoningEffort === "xhigh",
  "unknown extension agent lost legacy fallback",
);
for (const settings of [
  { reasoningEffort: "turbo" },
  { agents: { evaluator: { model: "opus" } } },
]) {
  rejects(() => resolveRaw("evaluator", settings), "invalid effort or Claude override accepted");
}
let evaluatorUltra;
try {
  evaluatorUltra = resolve("evaluator", { profile: "native-ultra" });
} catch {
  evaluatorUltra = null;
}
assert(
  !evaluatorUltra || (evaluatorUltra.effort === "high" && evaluatorUltra.model === "gpt-6-astra"),
  "leaf Ultra must reject or safely downgrade to Astra High",
);
for (const [name, model, effort] of [
  ["native-ultra", "gpt-6-sol", "ultra"],
  ["native-economic", "gpt-6-luna", "low"],
]) {
  const preset = CODEX_PROFILE_DEFAULTS[name];
  const resolved = resolveCodexTopLevelProfile(name);
  assert(
    preset && preset.model === model && effortOf(preset) === effort && preset.topLevelOnly === true,
    `${name}: preset must be explicit and top-level-only`,
  );
  assert(
    resolved.model === model &&
      resolved.reasoningEffort === effort &&
      resolved.topLevelOnly === true,
    `${name}: top-level resolution drifted`,
  );
}

const schema = JSON.parse(
  readFileSync(new URL("../schema/config.schema.json", import.meta.url), "utf8"),
);
const schemaEfforts = schema.definitions?.codexReasoningEffort?.enum ?? [];
assert(
  equal(schemaEfforts, efforts),
  `schema effort enum drifted from model policy: ${JSON.stringify(schemaEfforts)}`,
);
assert(!schemaEfforts.includes("ultra"), "schema exposes Ultra as an ordinary subagent effort");
assert(
  equal(schema.definitions?.codexTopLevelReasoningEffort?.enum, topLevelEfforts),
  "schema top-level effort enum drifted from model policy",
);
assert(
  schema.properties?.codex?.properties?.profiles?.properties?.["native-economic"],
  "schema does not expose native-economic profile overrides",
);

// Exercise both renderers with non-default settings. Sharing the resolver is necessary but this
// comparison proves neither renderer drops or renames the resolved fields on its own surface.
const ROOT = fileURLToPath(new URL("../", import.meta.url));
const [{ agentToToml, codexSettingsFromConfig }, { buildNativeAgents, topLevelProfileToToml }] =
  await Promise.all([import("../codex/install.mjs"), import("../codex/native-plugin.mjs")]);
const ultraToml = topLevelProfileToToml("native-ultra");
assert(
  /^model\s*=\s*"gpt-6-sol"$/m.test(ultraToml),
  "native-ultra profile file lost the Sol model",
);
assert(
  /^model_reasoning_effort\s*=\s*"ultra"$/m.test(ultraToml),
  "native-ultra profile file lost Ultra reasoning",
);
assert(
  !/name\s*=|developer_instructions\s*=|sandbox_mode\s*=/.test(ultraToml),
  "top-level native-ultra output was rendered as a subagent role",
);
const exampleSettings = codexSettingsFromConfig(
  JSON.parse(readFileSync(new URL("../examples/config.monorepo.json", import.meta.url), "utf8")),
);
assert(
  exampleSettings.profiles?.executor?.model === "gpt-5.6-luna" &&
    exampleSettings.profiles?.scout?.reasoningEffort === "medium",
  "config reader dropped semantic profile overrides",
);
const paritySettings = {
  profiles: { executor: { model: "gpt-5.6-terra", reasoningEffort: "high" } },
  agents: { evaluator: { model: "operator-sol", reasoningEffort: "xhigh" } },
};
const nativeWarnings = [];
const nativeAgents = buildNativeAgents(ROOT, paritySettings, (warning) =>
  nativeWarnings.push(warning),
);
const cloneWarnings = [];
const scalar = (source, key, separator = "=") => {
  const re = new RegExp(`^${key}\\s*${separator}\\s*["']?([^"'\\r\\n#]+)`, "m");
  return re.exec(source)?.[1]?.trim() ?? null;
};
for (const name of Object.keys(EXPECTED_POLICY)) {
  const source = readFileSync(new URL(`../agents/${name}.md`, import.meta.url), "utf8");
  const clone = agentToToml(source, paritySettings, (warning) => cloneWarnings.push(warning));
  const native = nativeAgents[`${name}.toml`];
  assert(
    scalar(clone, "model") === scalar(native, "model"),
    `${name}: override model differs between clone and native renderers`,
  );
  assert(
    scalar(clone, "model_reasoning_effort") === scalar(native, "model_reasoning_effort"),
    `${name}: override effort differs between clone and native renderers`,
  );
}
assert(
  equal(cloneWarnings, nativeWarnings),
  "override diagnostics differ between clone and native renderers",
);

const secretSentinel = "CODEX_SECRET_OVERRIDE_SENTINEL";
const secretProbe = spawnSync(
  process.execPath,
  [
    "-e",
    `
import { resolveCodexAgentPolicy } from "./codex/model-policy.mjs";
const source = { model: "opus", effort: "xhigh" };
try {
  resolveCodexAgentPolicy("evaluator", {
    agents: { evaluator: { model: "claude-${secretSentinel}", reasoningEffort: "ultra" } },
  }, source);
} catch (error) {
  process.stderr.write(String(error));
}
const result = resolveCodexAgentPolicy("evaluator", {
  agents: { evaluator: { model: "${secretSentinel}", reasoningEffort: "ultra" } },
}, source);
process.stdout.write(result.warnings.join("|"));
`,
  ],
  { encoding: "utf8" },
);
const secretOutput = `${secretProbe.stdout ?? ""}${secretProbe.stderr ?? ""}`;
assert(!secretOutput.includes(secretSentinel), "override diagnostics leaked a secret sentinel");

assert(typeof policy.resolveCodexEvaluationPolicy === "function", "evaluation resolver is missing");
const evaluationSettings = codexSettingsFromConfig({
  codex: { evaluation: { enabled: true, timeoutMs: 5000 } },
});
const evaluation = policy.resolveCodexEvaluationPolicy(evaluationSettings);
assert(
  evaluation.enabled && evaluation.model === "typesafe-ai/jev" && evaluation.timeoutMs === 5000,
  "evaluation configuration was dropped or resolved as chat",
);
assert(
  evaluation.endpoint === "https://ai-gateway.vercel.sh/v1/evaluate" &&
    !Object.hasOwn(evaluation, "reasoningEffort"),
  "evaluation must use its own HTTP modality",
);
assert(policy.resolveCodexEvaluationPolicy().enabled === false, "evaluation must be opt-in");
for (const invalid of [
  { reasoningEffort: "high" },
  { timeoutMs: 0 },
  { enabled: "yes" },
  [],
  null,
]) {
  rejects(
    () => policy.resolveCodexEvaluationPolicy({ evaluation: invalid }),
    "invalid evaluation configuration was accepted",
  );
}
for (const settings of [
  { agents: { evaluator: { model: "typesafe-ai/jev" } } },
  { profiles: { judge: { model: "typesafe-ai/jev" } } },
  { model: "typesafe-ai/jev" },
  { models: { heavy: "typesafe-ai/jev" } },
]) {
  rejects(
    () =>
      agentToToml(
        readFileSync(new URL("../agents/evaluator.md", import.meta.url), "utf8"),
        settings,
      ),
    "Jev leaked into a chat role",
  );
}
assert(
  schema.properties.codex.properties.evaluation.additionalProperties === false,
  "evaluation schema must reject chat-only fields",
);

const { evaluateRouting, routingCatalog } = await import("../codex/evaluate.mjs");

function adapterFixture(enabled = true) {
  const root = mkdtempSync(join(tmpdir(), "graph-powers-evaluate-"));
  mkdirSync(join(root, ".graph-powers"));
  writeFileSync(
    join(root, ".graph-powers/config.json"),
    JSON.stringify({
      codex: { evaluation: { enabled, timeoutMs: 100 } },
    }),
  );
  const plan = join(root, "PLAN.md");
  writeFileSync(plan, "# Plan\n");
  const git = spawnSync("git", ["init", "-q"], { cwd: root, encoding: "utf8" });
  assert(git.status === 0, `fixture git init failed: ${git.stderr}`);
  return { root, plan };
}

const agentCandidate = (role) => ({
  id: role,
  role,
  capability: {
    model: EXPECTED_POLICY[role][1],
    reasoningEffort: EXPECTED_POLICY[role][2],
    status: "SUPPORTED",
    evidence: `fixture verified ${role} capability`,
  },
});
const evaluationInput = (overrides = {}) => ({
  materialDoubt: true,
  taskId: "T2.1",
  decisionKey: "route-model",
  question: "Which action should route this bounded task?",
  evidence: ["policy check"],
  risk: "wrong specialist",
  requesterRole: "parent",
  depth: 0,
  state: { task: "T2.1", boundary: "codex" },
  candidates: [agentCandidate("debugger"), agentCandidate("explorer")],
  ...overrides,
});
const response = (body, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
const evaluationResult = (choice, probabilities) => ({
  model: "typesafe-ai/jev",
  providerMetadata: { requestId: "mock" },
  usage: { inputTokens: 12 },
  answers: { route: { type: "choice", choice, probabilities } },
});
const validEvaluation = evaluationResult("debugger", { debugger: 0.75, explorer: 0.25 });

// Each case owns a real Git host and ledger; only the paid HTTP boundary is replaced.
async function withAdapter(check, enabled = true) {
  const fixture = adapterFixture(enabled);
  let requests = 0;
  const run = (input = {}, options = {}) =>
    evaluateRouting(evaluationInput(input), {
      projectDir: fixture.root,
      planPath: fixture.plan,
      env: { AI_GATEWAY_API_KEY: "test-key" },
      ...options,
      fetchImpl: async (...args) => {
        requests += 1;
        return options.fetchImpl ? options.fetchImpl(...args) : response(validEvaluation);
      },
    });
  const cli = (input, args = []) =>
    spawnSync(
      "bun",
      ["codex/evaluate.mjs", "--project", fixture.root, "--plan", fixture.plan, ...args],
      {
        cwd: ROOT,
        encoding: "utf8",
        input: JSON.stringify(input),
        env: { ...process.env, AI_GATEWAY_API_KEY: "" },
      },
    );
  try {
    await check({ ...fixture, run, cli, calls: () => requests });
  } finally {
    rmSync(fixture.root, { recursive: true, force: true });
  }
}

await withAdapter(async ({ run, calls }) => {
  const result = await run(
    {},
    {
      fetchImpl: async (url, init) => {
        assert(url === "https://ai-gateway.vercel.sh/v1/evaluate", "official endpoint changed");
        assert(
          init.redirect === "error" && init.headers.Authorization === "Bearer test-key",
          "authorization or redirect isolation lost",
        );
        const body = JSON.parse(init.body);
        assert(
          equal(Object.keys(body).sort(), ["model", "questions", "state"]),
          "ledger leaked into HTTP",
        );
        assert(
          body.model === "typesafe-ai/jev" &&
            body.questions.route.type === "choice" &&
            body.state.task === "T2.1" &&
            body.questions.route.criteria.debugger.includes("error"),
          "typed request lost state or actual specialist purpose",
        );
        return response(validEvaluation);
      },
    },
  );
  assert(
    calls() === 1 &&
      result.status === "RECORDED" &&
      result.verdict === "debugger" &&
      !Object.hasOwn(result.evaluationResult, "usage") &&
      !Object.hasOwn(result.evaluationResult, "providerMetadata"),
    "typed response not recorded or provider metadata retained",
  );
  assert(
    equal(Object.keys(result.evaluationRequest.candidates[0]).sort(), [
      "id",
      "model",
      "reasoningEffort",
      "role",
    ]),
    "legacy four-field candidates changed",
  );
  const replay = await run({}, { env: {} });
  assert(
    replay.status === "RECORDED" && replay.verdict === "debugger" && calls() === 1,
    "replay required credential or repeated HTTP",
  );
});

await withAdapter(async ({ run, calls }) => {
  const result = await run(
    { candidates: [agentCandidate("debugger"), agentCandidate("frontend-specialist")] },
    {
      fetchImpl: async () =>
        response(
          evaluationResult("frontend-specialist", { debugger: 0.25, "frontend-specialist": 0.75 }),
        ),
    },
  );
  assert(
    calls() === 1 && result.status === "RECORDED" && result.verdict === "frontend-specialist",
    "different specialties sharing model and effort must be evaluated",
  );
});

const methodCandidates = [
  { id: "method", kind: "skill", role: "main", skills: ["graph-powers:debugger"], command: null },
  { id: "command", kind: "command", role: "main", skills: [], command: "/debug" },
  { id: "finish", kind: "finish", role: "main", skills: [], command: null },
];
await Promise.all(
  methodCandidates.map(({ id }) =>
    withAdapter(async ({ run }) => {
      const probabilities = { method: 0, command: 0, finish: 0, debugger: 0 };
      probabilities[id] = 1;
      const result = await run(
        {
          candidates: [
            ...methodCandidates,
            {
              ...agentCandidate("debugger"),
              kind: "agent",
              skills: [],
              command: null,
            },
          ],
        },
        { fetchImpl: async () => response(evaluationResult(id, probabilities)) },
      );
      assert(result.status === "RECORDED" && result.verdict === id, `main ${id} selection failed`);
      const [skill, command, finish, agent] = result.evaluationRequest.candidates;
      assert(
        skill.model === null &&
          skill.reasoningEffort === null &&
          equal(skill.skills, ["debugger"]) &&
          command.command === "debug" &&
          finish.kind === "finish" &&
          equal(agent.skills, ["debugger"]),
        "canonical methods, mandatory skills or main model preservation lost",
      );
      assert(
        equal(Object.keys(result.evaluationRequest.policy.capabilities), ["debugger"]),
        "main actions invented capability evidence",
      );
    }),
  ),
);

await withAdapter(async ({ run }) => {
  const result = await run(
    {
      candidates: [
        methodCandidates[0],
        { ...methodCandidates[0], id: "same-method", skills: ["debugger", "debugger"] },
        { ...agentCandidate("debugger"), kind: "agent", skills: ["debugger"], command: null },
        {
          ...agentCandidate("debugger"),
          id: "same-role",
          kind: "agent",
          skills: [],
          command: null,
        },
        {
          ...agentCandidate("frontend-specialist"),
          kind: "agent",
          skills: ["debugger"],
          command: null,
        },
      ],
    },
    {
      fetchImpl: async (_url, init) => {
        assert(
          equal(Object.keys(JSON.parse(init.body).questions.route.criteria), [
            "method",
            "debugger",
            "frontend-specialist",
          ]),
          "deduplication collapsed a distinct role or retained an identical method action",
        );
        return response(
          evaluationResult("method", { method: 1, debugger: 0, "frontend-specialist": 0 }),
        );
      },
    },
  );
  assert(
    result.status === "RECORDED" && result.evaluationRequest.candidates.length === 3,
    "deduplicated ledger failed",
  );
});

const catalog = routingCatalog();
assert(
  catalog.length > 32 &&
    catalog.length < 64 &&
    new Set(catalog.map((entry) => entry.id)).size === catalog.length,
  "catalog missing canonical inventory or contains duplicate actions",
);
assert(
  catalog.find((entry) => entry.id === "agent:debugger")?.path === "agents/debugger.md" &&
    catalog.find((entry) => entry.id === "skill:debugger")?.path === "skills/debugger/SKILL.md" &&
    catalog.find((entry) => entry.id === "command:debug")?.path === "commands/debug.md",
  "catalog lost canonical source metadata",
);
assert(
  equal(catalog.find((entry) => entry.id === "agent:verification")?.skills, ["webapp-testing"]),
  "browser verification lost its required method",
);
await withAdapter(async ({ run }) => {
  const candidates = catalog.map(({ id, kind, role, skills, command }) => ({
    id,
    kind,
    role,
    skills,
    command,
    ...(kind === "agent" && { capability: agentCandidate(role).capability }),
  }));
  const result = await run(
    { candidates },
    {
      fetchImpl: async () =>
        response(
          evaluationResult(
            "command:debug",
            Object.fromEntries(candidates.map(({ id }) => [id, id === "command:debug" ? 1 : 0])),
          ),
        ),
    },
  );
  assert(
    result.status === "RECORDED" && result.evaluationRequest.candidates.length === catalog.length,
    "complete source-derived catalog exceeds bounded adapter/ledger contract",
  );
});

const invalidCandidates = [
  {
    ...agentCandidate("debugger"),
    capability: { ...agentCandidate("debugger").capability, model: "gpt-6-astra" },
  },
  ...[
    "missing",
    "../debugger",
    "other:debugger",
    join(tmpdir(), "debugger"),
    "skills/debugger/SKILL.md",
  ].map((skill) => Object.assign({}, methodCandidates[0], { skills: [skill] })),
  ...["missing", "../debug", "other:debug", join(tmpdir(), "debug"), "commands/debug.md"].map(
    (command) => Object.assign({}, methodCandidates[1], { command }),
  ),
  { ...methodCandidates[0], role: "debugger" },
  { ...methodCandidates[0], capability: agentCandidate("debugger").capability },
  { ...methodCandidates[2], skills: ["debugger"] },
];
await Promise.all(
  invalidCandidates.map((candidate, index) =>
    withAdapter(async ({ run, calls }) => {
      const result = await run({ candidates: [candidate] });
      assert(
        result.status === "BLOCKED" &&
          calls() === 0 &&
          result.evaluationError.code === (index === 0 ? "CAPABILITY_MISMATCH" : "INVALID_INPUT"),
        "invalid action reached HTTP",
      );
    }),
  ),
);

const errors = [
  ["unauthorized", async () => response({}, 401), "HTTP_UNAUTHORIZED"],
  ["forbidden", async () => response({}, 403), "HTTP_FORBIDDEN"],
  ["rate limited", async () => response({}, 429), "HTTP_RATE_LIMITED"],
  ["server failure", async () => response({}, 503), "HTTP_SERVER_ERROR"],
  ["invalid JSON", async () => new Response("not JSON"), "INVALID_RESPONSE"],
  ["wrong model", async () => response({ ...validEvaluation, model: "other" }), "INVALID_RESPONSE"],
  [
    "wrong choice",
    async () => response(evaluationResult("missing", { debugger: 1, explorer: 0 })),
    "INVALID_RESPONSE",
  ],
  [
    "invalid probabilities",
    async () => response(evaluationResult("debugger", { debugger: 0.8, explorer: 0.1 })),
    "INVALID_RESPONSE",
  ],
  [
    "secret error",
    async () => {
      throw new Error(secretSentinel);
    },
    "NETWORK_FAILURE",
  ],
  [
    "request timeout",
    (_url, init) =>
      new Promise((_resolve, reject) => {
        init.signal.addEventListener("abort", () => reject(new Error("aborted")));
      }),
    "TIMEOUT",
  ],
  ["body timeout", async () => ({ ok: true, json: () => new Promise(() => {}) }), "TIMEOUT"],
];
await Promise.all(
  errors.map(([label, fetchImpl, expected]) =>
    withAdapter(async ({ run, calls }) => {
      const result = await run({}, { fetchImpl });
      assert(
        calls() === 1 &&
          result.status === "BLOCKED" &&
          result.evaluationError?.code === expected &&
          !JSON.stringify(result).includes(secretSentinel),
        `${label} lost sanitized terminal failure`,
      );
    }),
  ),
);

await withAdapter(async ({ run, calls, cli }) => {
  // Sequential calls intentionally share a ledger to exercise the three-per-task cap.
  const assertMissingCredential = async (decisionKey) => {
    const result = await run({ decisionKey }, { env: {} });
    assert(
      result.evaluationError?.code === "CREDENTIAL_UNAVAILABLE",
      "missing credential not recorded",
    );
  };
  await assertMissingCredential("one");
  await assertMissingCredential("two");
  await assertMissingCredential("three");
  const capped = await run({ decisionKey: "four" });
  assert(capped.status === "USER_REQUIRED" && calls() === 0, "cap did not stop HTTP");
  const cappedCli = cli(evaluationInput({ decisionKey: "five" }));
  assert(
    cappedCli.status === 4 &&
      JSON.parse(cappedCli.stdout).status === "USER_REQUIRED" &&
      !cappedCli.stderr,
    "CLI cap did not return exit 4 without stderr",
  );
});
await withAdapter(async ({ cli }) => {
  const disabled = cli({ materialDoubt: false });
  assert(
    disabled.status === 0 && JSON.parse(disabled.stdout).status === "SKIPPED",
    "disabled CLI failed",
  );
}, false);
await withAdapter(async ({ run, calls, cli }) => {
  assert(
    (await run({ materialDoubt: false })).reason === "NO_MATERIAL_DOUBT" && calls() === 0,
    "direct opt-out lost",
  );
  const invalid = cli([]);
  assert(
    invalid.status === 2 &&
      JSON.parse(invalid.stdout).evaluationError.code === "INVALID_INPUT" &&
      !invalid.stderr,
    "CLI invalid input did not return exit 2",
  );
  for (const decisionKey of ["one", "two", "three"]) {
    const missing = cli(evaluationInput({ decisionKey }));
    assert(
      missing.status === 4 &&
        JSON.parse(missing.stdout).evaluationError.code === "CREDENTIAL_UNAVAILABLE" &&
        !missing.stderr,
      "CLI missing credential did not return exit 4",
    );
  }
});
await withAdapter(async ({ root, run, calls }) => {
  const outside = adapterFixture();
  const nested = join(root, "nested-repository");
  try {
    mkdirSync(nested);
    writeFileSync(join(nested, "PLAN.md"), "# Nested plan\n");
    assert(
      spawnSync("git", ["init", "-q"], { cwd: nested }).status === 0,
      "nested git init failed",
    );
    symlinkSync(outside.plan, join(root, "outside-plan.md"));
    await Promise.all(
      ["outside-plan.md", "nested-repository/PLAN.md"].map(async (planPath) => {
        const result = await run({}, { planPath });
        assert(
          result.evaluationError?.code === "INVALID_CONFIGURATION" && calls() === 0,
          "cross-root plan accepted",
        );
      }),
    );
    assert(
      [outside.root, nested].every(
        (directory) => !existsSync(join(directory, ".graph-powers/logs/sdd")),
      ),
      "rejected plan wrote an external ledger",
    );
  } finally {
    rmSync(outside.root, { recursive: true, force: true });
  }
});
console.log("codex-policy: 12 defaults, overrides, native parity, Ultra and typed routing checked");

await import("./check_jev_coordination.mjs");
