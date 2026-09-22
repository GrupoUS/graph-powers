#!/usr/bin/env bun
/**
 * Contract for the centralized Codex semantic model policy.
 *
 * This is intentionally independent of generated files: it calls the exported resolver directly,
 * so overrides and compatibility behaviour cannot be made to pass by duplicating resolver logic in
 * a checker. The Python artefact checks consume the same explicit oracle for clone/native parity.
 */

import { existsSync, mkdtempSync, mkdirSync, readFileSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
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
  debugger: ["executor", "gpt-6-astra", "high"],
  "frontend-specialist": ["executor", "gpt-6-astra", "high"],
  "mobile-developer": ["executor", "gpt-6-astra", "high"],
  "performance-optimizer": ["executor", "gpt-6-astra", "high"],
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

let policy;
try {
  policy = await import("../codex/model-policy.mjs");
} catch (error) {
  console.error(
    "::error::Codex semantic model policy is missing or cannot be loaded — " +
      "expected codex/model-policy.mjs to export CODEX_AGENT_PROFILES, CODEX_PROFILE_DEFAULTS, " +
      "CODEX_REASONING_EFFORTS and resolveCodexAgentPolicy.",
  );
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
}

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
const resolve = (name, settings = {}) =>
  compact(resolveCodexAgentPolicy(name, settings, sourceAgent(name, EXPECTED_POLICY[name])));

assert(Object.keys(EXPECTED_POLICY).length === 12, "oracle must contain all 12 canonical agents");
assert(
  CODEX_AGENT_PROFILES && typeof CODEX_AGENT_PROFILES === "object",
  "CODEX_AGENT_PROFILES is missing",
);
assert(
  CODEX_PROFILE_DEFAULTS && typeof CODEX_PROFILE_DEFAULTS === "object",
  "CODEX_PROFILE_DEFAULTS is missing",
);
assert(
  CODEX_WARNING_CATEGORIES && typeof CODEX_WARNING_CATEGORIES === "object",
  "CODEX_WARNING_CATEGORIES is missing",
);
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

// Precedence and migration cases exercise the real resolver, not a reimplementation in this file.
const perAgent = { model: "override-model", reasoningEffort: "high" };
assert(
  equal(
    resolve("explorer", { agentOverrides: { explorer: perAgent }, agents: { explorer: perAgent } }),
    {
      profile: "scout",
      model: "override-model",
      effort: "high",
      topLevelOnly: false,
    },
  ),
  "explicit per-agent override did not win",
);
assert(
  resolveCodexAgentPolicy(
    "explorer",
    { agents: { explorer: perAgent } },
    sourceAgent("explorer", EXPECTED_POLICY.explorer),
  ).warnings.includes(CODEX_WARNING_CATEGORIES.modelOverrideUnverified),
  "arbitrary model override did not emit its fixed diagnostic category",
);
assert(
  equal(resolve("explorer", { profile: "judge" }), {
    profile: "judge",
    model: "gpt-6-astra",
    effort: "high",
    topLevelOnly: false,
  }),
  "explicit profile override did not win",
);
assert(
  resolveCodexAgentPolicy(
    "explorer",
    { profile: "judge" },
    sourceAgent("explorer", EXPECTED_POLICY.explorer),
  ).warnings.includes(CODEX_WARNING_CATEGORIES.profileOverrideUnverified),
  "cross-tier profile override did not emit its fixed diagnostic category",
);
assert(
  equal(
    resolve("explorer", {
  profiles: { scout: { model: "gpt-5.6-terra", reasoningEffort: "high" } },
    }),
    {
      profile: "scout",
      model: "gpt-5.6-terra",
      effort: "high",
      topLevelOnly: false,
    },
  ),
  "semantic profile settings did not override the default",
);
assert(
  equal(
    resolve("explorer", {
  profiles: { scout: { model: "gpt-5.6-terra", reasoningEffort: "high" } },
  agents: { explorer: { model: "agent-model", reasoningEffort: "low" } },
    }),
    {
      profile: "scout",
      model: "agent-model",
      effort: "low",
      topLevelOnly: false,
    },
  ),
  "per-agent settings did not outrank profile settings",
);
assert(
  resolve("evaluator", { models: { heavy: "legacy-heavy" }, reasoningEffort: "high" }).model ===
    "legacy-heavy",
  "legacy codex.models.heavy was not accepted",
);
assert(
  resolve("explorer", { models: { light: "legacy-light" } }).model === "legacy-light",
  "legacy codex.models.light was not accepted",
);
assert(
  equal(resolve("verification", { model: "flat-model", reasoningEffort: "low" }), {
    profile: "verifier",
    model: "flat-model",
    effort: "low",
    topLevelOnly: false,
  }),
  "flat codex.model fallback was not accepted",
);
assert(
  resolve("evaluator", { reasoningEffort: "max" }).effort === "max",
  "max override was not accepted",
);

const extensionAgent = resolveCodexAgentPolicy(
  "extension-agent",
  {},
  { name: "extension-agent", model: "opus", effort: "xhigh" },
);
assert(
  extensionAgent.profile === null && extensionAgent.reasoningEffort === "xhigh",
  `unknown extension agent did not retain legacy fallback: ${JSON.stringify(extensionAgent)}`,
);

let invalidRejected = false;
try {
  resolveCodexAgentPolicy(
    "evaluator",
    { reasoningEffort: "turbo" },
    sourceAgent("evaluator", EXPECTED_POLICY.evaluator),
  );
} catch {
  invalidRejected = true;
}
assert(invalidRejected, "invalid reasoning effort turbo was accepted");

let claudeModelRejected = false;
try {
  resolveCodexAgentPolicy(
    "evaluator",
    { agents: { evaluator: { model: "opus" } } },
    sourceAgent("evaluator", EXPECTED_POLICY.evaluator),
  );
} catch {
  claudeModelRejected = true;
}
assert(claudeModelRejected, "Claude model family leaked through an explicit Codex override");

const ultra = CODEX_PROFILE_DEFAULTS["native-ultra"];
assert(
  ultra && effortOf(ultra) === "ultra" && ultra.topLevelOnly === true,
  "native-ultra must be explicit and top-level-only",
);
const economic = CODEX_PROFILE_DEFAULTS["native-economic"];
assert(
  economic &&
    economic.model === "gpt-6-luna" &&
    effortOf(economic) === "low" &&
    economic.topLevelOnly === true,
  "native-economic must be Luna low and top-level-only",
);
let evaluatorUltra;
try {
  evaluatorUltra = resolve("evaluator", { profile: "native-ultra" });
} catch {
  evaluatorUltra = null;
}
if (evaluatorUltra) {
  assert(
    evaluatorUltra.effort === "high" && evaluatorUltra.model === "gpt-6-astra",
    `evaluator Ultra must reject or safely downgrade to Astra High, got ${JSON.stringify(evaluatorUltra)}`,
  );
}

const directUltra = resolveCodexAgentPolicy(
  "evaluator",
  { reasoningEffort: "ultra" },
  sourceAgent("evaluator", EXPECTED_POLICY.evaluator),
);
assert(
  directUltra.model === "gpt-6-astra" && directUltra.reasoningEffort === "high",
  `evaluator Ultra safe fallback is not Astra High: ${JSON.stringify(directUltra)}`,
);
assert(
  equal(directUltra.warnings, [CODEX_WARNING_CATEGORIES.topLevelEffortDowngraded]),
  "evaluator Ultra fallback did not emit its fixed diagnostic category",
);
const economicLeaf = resolve("debugger", { profile: "native-economic" });
assert(
  equal(economicLeaf, {
    profile: "executor",
    model: "gpt-6-astra",
    effort: "high",
    topLevelOnly: false,
  }),
  `native-economic was not safely downgraded for a leaf: ${JSON.stringify(economicLeaf)}`,
);
assert(
  equal(
    resolveCodexAgentPolicy(
      "debugger",
      { profile: "native-economic" },
      sourceAgent("debugger", EXPECTED_POLICY.debugger),
    ).warnings,
    [CODEX_WARNING_CATEGORIES.topLevelProfileDowngraded],
  ),
  "native-economic leaf rejection did not emit its fixed diagnostic category",
);
const topLevelUltra = resolveCodexTopLevelProfile("native-ultra");
assert(
  topLevelUltra.model === "gpt-6-sol" &&
    topLevelUltra.reasoningEffort === "ultra" &&
    topLevelUltra.topLevelOnly === true,
  "native-ultra did not resolve as an explicit top-level profile",
);
const topLevelEconomic = resolveCodexTopLevelProfile("native-economic");
assert(
  topLevelEconomic.model === "gpt-6-luna" &&
    topLevelEconomic.reasoningEffort === "low" &&
    topLevelEconomic.topLevelOnly === true,
  "native-economic did not resolve as an explicit top-level profile",
);

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
for (const invalid of [{ reasoningEffort: "high" }, { timeoutMs: 0 }, { enabled: "yes" }, [], null]) {
  let rejected = false;
  try {
    policy.resolveCodexEvaluationPolicy({ evaluation: invalid });
  } catch {
    rejected = true;
  }
  assert(rejected, "invalid evaluation configuration was accepted");
}
for (const settings of [
  { agents: { evaluator: { model: "typesafe-ai/jev" } } },
  { profiles: { judge: { model: "typesafe-ai/jev" } } },
  { model: "typesafe-ai/jev" },
  { models: { standard: "typesafe-ai/jev" } },
]) {
  let rejected = false;
  try {
    agentToToml(readFileSync(new URL("../agents/evaluator.md", import.meta.url), "utf8"), settings);
  } catch {
    rejected = true;
  }
  assert(rejected, "Jev leaked into a chat role");
}
assert(
  schema.properties.codex.properties.evaluation.additionalProperties === false,
  "evaluation schema must reject chat-only fields",
);

const { evaluateRouting } = await import("../codex/evaluate.mjs");

function adapterFixture({ enabled = true } = {}) {
  const root = mkdtempSync(join(tmpdir(), "graph-powers-evaluate-"));
  mkdirSync(join(root, ".graph-powers"));
  writeFileSync(
    join(root, ".graph-powers", "config.json"),
    JSON.stringify({
      codex: { evaluation: { enabled, timeoutMs: 100 } },
    }),
  );
  const plan = join(root, "PLAN.md");
  writeFileSync(plan, "# Plan\n");
  const git = spawnSync("git", ["init", "-q"], { cwd: root, encoding: "utf8" });
  assert(git.status === 0, `adapter fixture git init failed: ${git.stderr}`);
  return { root, plan };
}

const evaluationInput = (overrides = {}) => ({
  materialDoubt: true,
  taskId: "T2.1",
  decisionKey: "route-model",
  question: "Which role should route this bounded task?",
  evidence: ["policy check"],
  risk: "wrong specialist",
  requesterRole: "parent",
  depth: 0,
  state: { task: "T2.1", boundary: "codex" },
  candidates: [
    {
      id: "debugger",
      role: "debugger",
      capability: {
        model: "gpt-6-astra",
        reasoningEffort: "high",
        status: "SUPPORTED",
        evidence: "parent verified debugger capability",
      },
    },
    {
      id: "explorer",
      role: "explorer",
      capability: {
        model: "gpt-6-luna",
        reasoningEffort: "medium",
        status: "SUPPORTED",
        evidence: "parent verified explorer capability",
      },
    },
  ],
  ...overrides,
});

const response = (body, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
const validEvaluation = {
  model: "typesafe-ai/jev",
  providerMetadata: { requestId: "mock-response" },
  usage: { inputTokens: 12 },
  answers: {
    route: {
      type: "choice",
      choice: "debugger",
      probabilities: { debugger: 0.75, explorer: 0.25 },
    },
  },
};

{
  const fixture = adapterFixture();
  let requests = 0;
  try {
    const result = await evaluateRouting(evaluationInput(), {
      projectDir: fixture.root,
      planPath: "PLAN.md",
      env: { AI_GATEWAY_API_KEY: "test-key" },
      fetchImpl: async (url, init) => {
        requests += 1;
        assert(
          url === "https://ai-gateway.vercel.sh/v1/evaluate",
          "adapter changed the official endpoint",
        );
        assert(init.redirect === "error", "adapter must reject redirects");
        assert(init.headers.Authorization === "Bearer test-key", "adapter omitted authorization");
        const body = JSON.parse(init.body);
        assert(
          equal(Object.keys(body).sort(), ["model", "questions", "state"]),
          "adapter sent ledger-only candidate or policy fields to Jev",
        );
        assert(
          body.model === "typesafe-ai/jev" && body.questions.route.type === "choice",
          "adapter did not build the typed Jev request",
        );
        assert(
          body.state.task === "T2.1" && body.questions.route.criteria.debugger,
          "adapter dropped caller state or a resolved candidate",
        );
        return response(validEvaluation);
      },
    });
    assert(
      requests === 1 &&
        result.status === "RECORDED" &&
        result.verdict === "debugger" &&
        !Object.hasOwn(result.evaluationResult, "providerMetadata") &&
        !Object.hasOwn(result.evaluationResult, "usage"),
      `adapter did not record the typed response: ${JSON.stringify(result)}`,
    );

    const replay = await evaluateRouting(evaluationInput(), {
      projectDir: fixture.root,
      planPath: fixture.plan,
      env: {},
      fetchImpl: async () => {
        throw new Error("replay must not send network");
      },
    });
    assert(
      replay.status === "RECORDED" && replay.verdict === "debugger",
      "adapter did not recover a recorded result without a credential",
    );
  } finally {
    rmSync(fixture.root, { recursive: true, force: true });
  }
}

{
  const fixture = adapterFixture();
  try {
    let requests = 0;
    const result = await evaluateRouting(
      evaluationInput({
        candidates: [
          evaluationInput().candidates[0],
          {
            ...evaluationInput().candidates[0],
            id: "frontend-specialist",
            role: "frontend-specialist",
            capability: {
              ...evaluationInput().candidates[0].capability,
              evidence: "parent verified frontend capability",
            },
          },
        ],
      }),
      {
        projectDir: fixture.root,
        planPath: fixture.plan,
        env: {},
        fetchImpl: async () => {
          requests += 1;
          return response(validEvaluation);
        },
      },
    );
    assert(
      result.status === "SKIPPED" && requests === 0,
      "roles with the same resolved model and effort must not call Jev",
    );
  } finally {
    rmSync(fixture.root, { recursive: true, force: true });
  }
}

{
  const fixture = adapterFixture();
  try {
    let requests = 0;
    const result = await evaluateRouting(
      evaluationInput({
        candidates: [
          {
            ...evaluationInput().candidates[0],
            capability: {
              ...evaluationInput().candidates[0].capability,
              model: "gpt-6-luna",
            },
          },
        ],
      }),
      {
        projectDir: fixture.root,
        planPath: fixture.plan,
        env: { AI_GATEWAY_API_KEY: "test-key" },
        fetchImpl: async () => {
          requests += 1;
          return response(validEvaluation);
        },
      },
    );
    assert(
      result.status === "BLOCKED" &&
        result.evaluationError?.code === "CAPABILITY_MISMATCH" &&
        requests === 0,
      "capability evidence must match the resolved role model and effort before network",
    );
  } finally {
    rmSync(fixture.root, { recursive: true, force: true });
  }
}

for (const [label, fetchImpl, expected] of [
  ["unauthorized", async () => response({}, 401), "HTTP_UNAUTHORIZED"],
  ["forbidden", async () => response({}, 403), "HTTP_FORBIDDEN"],
  ["rate limited", async () => response({}, 429), "HTTP_RATE_LIMITED"],
  ["server failure", async () => response({}, 503), "HTTP_SERVER_ERROR"],
  ["invalid JSON", async () => new Response("not JSON", { status: 200 }), "INVALID_RESPONSE"],
  ["wrong model", async () => response({ ...validEvaluation, model: "other" }), "INVALID_RESPONSE"],
  [
    "wrong choice",
    async () =>
      response({
        ...validEvaluation,
        answers: { route: { ...validEvaluation.answers.route, choice: "missing" } },
      }),
    "INVALID_RESPONSE",
  ],
  [
    "invalid probabilities",
    async () =>
      response({
        ...validEvaluation,
        answers: {
          route: {
            ...validEvaluation.answers.route,
            probabilities: { debugger: 0.8, explorer: 0.1 },
          },
        },
      }),
    "INVALID_RESPONSE",
  ],
]) {
  const fixture = adapterFixture();
  try {
    let requests = 0;
    const result = await evaluateRouting(
      evaluationInput({ decisionKey: `transport-${label.replaceAll(" ", "-").toLowerCase()}` }),
      {
        projectDir: fixture.root,
        planPath: fixture.plan,
        env: { AI_GATEWAY_API_KEY: "test-key" },
        fetchImpl: async (...args) => {
          requests += 1;
          return fetchImpl(...args);
        },
      },
    );
    assert(
      requests === 1 && result.status === "BLOCKED" && result.evaluationError?.code === expected,
      `${label} did not record one sanitized terminal failure: ${JSON.stringify(result)}`,
    );
  } finally {
    rmSync(fixture.root, { recursive: true, force: true });
  }
}

{
  const fixture = adapterFixture();
  try {
    let requests = 0;
    const result = await evaluateRouting(evaluationInput({ decisionKey: "transport-timeout" }), {
      projectDir: fixture.root,
      planPath: fixture.plan,
      env: { AI_GATEWAY_API_KEY: "test-key" },
      fetchImpl: (_url, init) =>
        new Promise((_resolve, reject) => {
          requests += 1;
          init.signal.addEventListener("abort", () => reject(new DOMException("aborted", "AbortError")));
        }),
    });
    assert(
      requests === 1 && result.evaluationError?.code === "TIMEOUT",
      "adapter did not bound the complete HTTP request with its timeout",
    );
  } finally {
    rmSync(fixture.root, { recursive: true, force: true });
  }
}

{
  const fixture = adapterFixture();
  try {
    let requests = 0;
    const result = await evaluateRouting(evaluationInput({ decisionKey: "body-timeout" }), {
      projectDir: fixture.root,
      planPath: fixture.plan,
      env: { AI_GATEWAY_API_KEY: "test-key" },
      fetchImpl: async (_url, init) => {
        requests += 1;
        return {
          ok: true,
          json: () => new Promise((_resolve, reject) => {
            init.signal.addEventListener("abort", () => reject(new Error("aborted")));
          }),
        };
      },
    });
    assert(
      requests === 1 && result.evaluationError?.code === "TIMEOUT",
      "adapter did not include response-body parsing in the timeout",
    );
  } finally {
    rmSync(fixture.root, { recursive: true, force: true });
  }
}

{
  const fixture = adapterFixture();
  try {
    let requests = 0;
    for (const decisionKey of ["cap-one", "cap-two", "cap-three"]) {
      const result = await evaluateRouting(evaluationInput({ decisionKey }), {
        projectDir: fixture.root,
        planPath: fixture.plan,
        env: {},
        fetchImpl: async () => {
          requests += 1;
          return response(validEvaluation);
        },
      });
      assert(
        result.evaluationError?.code === "CREDENTIAL_UNAVAILABLE",
        "fresh reservation did not record missing credential",
      );
    }
    const capped = await evaluateRouting(evaluationInput({ decisionKey: "cap-four" }), {
      projectDir: fixture.root,
      planPath: fixture.plan,
      env: {},
      fetchImpl: async () => {
        requests += 1;
        return response(validEvaluation);
      },
    });
    assert(
      capped.status === "USER_REQUIRED" && requests === 0,
      "consultation cap must stop the HTTP call before credential or transport use",
    );
  } finally {
    rmSync(fixture.root, { recursive: true, force: true });
  }
}

{
  const fixture = adapterFixture({ enabled: false });
  try {
    const cli = spawnSync(
      "bun",
      ["codex/evaluate.mjs", "--project", fixture.root, "--plan", fixture.plan],
      {
        cwd: ROOT,
        encoding: "utf8",
        input: JSON.stringify({ materialDoubt: false }),
      },
    );
    assert(
      cli.status === 0 && JSON.parse(cli.stdout).status === "SKIPPED",
      `disabled CLI must not need credentials or network: ${cli.stderr}`,
    );
  } finally {
    rmSync(fixture.root, { recursive: true, force: true });
  }
}

{
  const fixture = adapterFixture();
  const outside = adapterFixture();
  const nested = join(fixture.root, "nested-repository");
  try {
    const nestedPlan = join(nested, "PLAN.md");
    mkdirSync(nested);
    writeFileSync(nestedPlan, "# Nested plan\n");
    assert(spawnSync("git", ["init", "-q"], { cwd: nested, encoding: "utf8" }).status === 0,
      "nested adapter fixture git init failed");
    symlinkSync(outside.plan, join(fixture.root, "outside-plan.md"));
    for (const planPath of ["outside-plan.md", "nested-repository/PLAN.md"]) {
      let requests = 0;
      const result = await evaluateRouting(evaluationInput({ decisionKey: `contain-${planPath.includes("outside") ? "symlink" : "nested"}` }), {
        projectDir: fixture.root,
        planPath,
        env: { AI_GATEWAY_API_KEY: "test-key" },
        fetchImpl: async () => { requests += 1; return response(validEvaluation); },
      });
      assert(result.evaluationError?.code === "INVALID_CONFIGURATION" && requests === 0,
        `adapter accepted mixed project/plan Git roots: ${planPath}`);
    }
    assert(!existsSync(join(outside.root, ".graph-powers", "logs", "sdd")) &&
      !existsSync(join(nested, ".graph-powers", "logs", "sdd")),
    "rejected plan wrote a ledger outside the host project");
  } finally {
    rmSync(fixture.root, { recursive: true, force: true });
    rmSync(outside.root, { recursive: true, force: true });
  }
}

{
  const fixture = adapterFixture();
  try {
    const invalid = spawnSync("bun", ["codex/evaluate.mjs", "--project", fixture.root, "--plan", "PLAN.md"], {
      cwd: ROOT,
      encoding: "utf8",
      input: "[]",
    });
    const missingCredential = spawnSync("bun", ["codex/evaluate.mjs", "--project", fixture.root, "--plan", "PLAN.md"], {
      cwd: ROOT,
      encoding: "utf8",
      input: JSON.stringify(evaluationInput({ decisionKey: "cli-missing-credential" })),
      env: { ...process.env, AI_GATEWAY_API_KEY: "" },
    });
    assert(invalid.status === 2 && JSON.parse(invalid.stdout).evaluationError.code === "INVALID_INPUT" && !invalid.stderr,
      "CLI invalid input must return exit 2 without stderr payload");
    assert(missingCredential.status === 4 && JSON.parse(missingCredential.stdout).evaluationError.code === "CREDENTIAL_UNAVAILABLE" && !missingCredential.stderr,
      "CLI terminal operational block must return exit 4 without stderr payload");
  } finally {
    rmSync(fixture.root, { recursive: true, force: true });
  }
}

{
  const fixture = adapterFixture();
  try {
    const runCli = (decisionKey) => spawnSync(
      "bun",
      ["codex/evaluate.mjs", "--project", fixture.root, "--plan", "PLAN.md"],
      {
        cwd: ROOT,
        encoding: "utf8",
        input: JSON.stringify(evaluationInput({ decisionKey })),
        env: { ...process.env, AI_GATEWAY_API_KEY: "" },
      },
    );
    for (const decisionKey of ["cli-cap-one", "cli-cap-two", "cli-cap-three"]) {
      const result = runCli(decisionKey);
      assert(result.status === 4 && JSON.parse(result.stdout).status === "BLOCKED" && !result.stderr,
        "CLI missing-credential reservation did not return terminal exit 4");
    }
    const capped = runCli("cli-cap-four");
    assert(capped.status === 4 && JSON.parse(capped.stdout).status === "USER_REQUIRED" && !capped.stderr,
      "CLI cap result did not return USER_REQUIRED with exit 4");
  } finally {
    rmSync(fixture.root, { recursive: true, force: true });
  }
}

console.log(
  `codex-policy: ${Object.keys(EXPECTED_POLICY).length} defaults, overrides, native-companion parity and Ultra guard checked`,
);
