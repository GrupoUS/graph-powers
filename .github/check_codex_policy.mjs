#!/usr/bin/env bun
/**
 * Contract for the centralized Codex semantic model policy.
 *
 * This is intentionally independent of generated files: it calls the exported resolver directly,
 * so overrides and compatibility behaviour cannot be made to pass by duplicating resolver logic in
 * a checker. The Python artefact checks consume the same explicit oracle for clone/native parity.
 */

import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const EXPECTED_POLICY = {
  evaluator: ["judge", "gpt-5.6-sol", "max"],
  "security-reviewer": ["judge", "gpt-5.6-sol", "max"],
  "skill-improver": ["judge", "gpt-5.6-sol", "max"],
  "ui-ux-designer": ["judge", "gpt-5.6-sol", "max"],
  "project-planner": ["architect", "gpt-5.6-sol", "max"],
  debugger: ["executor", "gpt-5.6-luna", "max"],
  "frontend-specialist": ["executor", "gpt-5.6-luna", "max"],
  "mobile-developer": ["executor", "gpt-5.6-luna", "max"],
  "performance-optimizer": ["executor", "gpt-5.6-luna", "max"],
  verification: ["verifier", "gpt-5.6-luna", "max"],
  explorer: ["scout", "gpt-5.6-luna", "medium"],
  librarian: ["scout", "gpt-5.6-luna", "medium"],
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
assert(CODEX_AGENT_PROFILES && typeof CODEX_AGENT_PROFILES === "object", "CODEX_AGENT_PROFILES is missing");
assert(CODEX_PROFILE_DEFAULTS && typeof CODEX_PROFILE_DEFAULTS === "object", "CODEX_PROFILE_DEFAULTS is missing");
assert(CODEX_WARNING_CATEGORIES && typeof CODEX_WARNING_CATEGORIES === "object", "CODEX_WARNING_CATEGORIES is missing");
const efforts = Array.from(CODEX_REASONING_EFFORTS ?? []);
assert(efforts.includes("max"), `max is not accepted; efforts=${JSON.stringify(efforts)}`);
const topLevelEfforts = Array.from(CODEX_TOP_LEVEL_REASONING_EFFORTS ?? []);
assert(topLevelEfforts.includes("low") && topLevelEfforts.includes("ultra"),
  "top-level policy must accept both economical low and Ultra efforts");

for (const [name, expected] of Object.entries(EXPECTED_POLICY)) {
  const actual = resolve(name);
  assert(equal(actual, { profile: expected[0], model: expected[1], effort: expected[2], topLevelOnly: false }),
    `${name}: expected ${expected.join(" / ")}, got ${JSON.stringify(actual)}`);
}

// Missing settings must be deterministic, and cannot fall through to session inheritance.
for (const name of Object.keys(EXPECTED_POLICY)) {
  assert(equal(resolve(name), resolve(name, {})), `${name}: missing config is not deterministic`);
}

// Precedence and migration cases exercise the real resolver, not a reimplementation in this file.
const perAgent = { model: "override-model", reasoningEffort: "high" };
assert(equal(resolve("explorer", { agentOverrides: { explorer: perAgent }, agents: { explorer: perAgent } }), {
  profile: "scout", model: "override-model", effort: "high", topLevelOnly: false,
}), "explicit per-agent override did not win");
assert(resolveCodexAgentPolicy("explorer", { agents: { explorer: perAgent } },
  sourceAgent("explorer", EXPECTED_POLICY.explorer)).warnings.includes(
  CODEX_WARNING_CATEGORIES.modelOverrideUnverified,
), "arbitrary model override did not emit its fixed diagnostic category");
assert(equal(resolve("explorer", { profile: "judge" }), {
  profile: "judge", model: "gpt-5.6-sol", effort: "max", topLevelOnly: false,
}), "explicit profile override did not win");
assert(resolveCodexAgentPolicy("explorer", { profile: "judge" },
  sourceAgent("explorer", EXPECTED_POLICY.explorer)).warnings.includes(
  CODEX_WARNING_CATEGORIES.profileOverrideUnverified,
), "cross-tier profile override did not emit its fixed diagnostic category");
assert(equal(resolve("explorer", {
  profiles: { scout: { model: "gpt-5.6-terra", reasoningEffort: "high" } },
}), {
  profile: "scout", model: "gpt-5.6-terra", effort: "high", topLevelOnly: false,
}), "semantic profile settings did not override the default");
assert(equal(resolve("explorer", {
  profiles: { scout: { model: "gpt-5.6-terra", reasoningEffort: "high" } },
  agents: { explorer: { model: "agent-model", reasoningEffort: "low" } },
}), {
  profile: "scout", model: "agent-model", effort: "low", topLevelOnly: false,
}), "per-agent settings did not outrank profile settings");
assert(resolve("evaluator", { models: { heavy: "legacy-heavy" }, reasoningEffort: "high" }).model === "legacy-heavy",
  "legacy codex.models.heavy was not accepted");
assert(resolve("explorer", { models: { light: "legacy-light" } }).model === "legacy-light",
  "legacy codex.models.light was not accepted");
assert(equal(resolve("verification", { model: "flat-model", reasoningEffort: "low" }), {
  profile: "verifier", model: "flat-model", effort: "low", topLevelOnly: false,
}), "flat codex.model fallback was not accepted");
assert(resolve("evaluator", { reasoningEffort: "max" }).effort === "max", "max override was not accepted");

const extensionAgent = resolveCodexAgentPolicy(
  "extension-agent",
  {},
  { name: "extension-agent", model: "opus", effort: "xhigh" },
);
assert(extensionAgent.profile === null && extensionAgent.reasoningEffort === "xhigh",
  `unknown extension agent did not retain legacy fallback: ${JSON.stringify(extensionAgent)}`);

let invalidRejected = false;
try {
  resolveCodexAgentPolicy("evaluator", { reasoningEffort: "turbo" }, sourceAgent("evaluator", EXPECTED_POLICY.evaluator));
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
assert(ultra && effortOf(ultra) === "ultra" && ultra.topLevelOnly === true,
  "native-ultra must be explicit and top-level-only");
const economic = CODEX_PROFILE_DEFAULTS["native-economic"];
assert(economic && economic.model === "gpt-5.6-luna" && effortOf(economic) === "low" &&
  economic.topLevelOnly === true, "native-economic must be Luna low and top-level-only");
let evaluatorUltra;
try {
  evaluatorUltra = resolve("evaluator", { profile: "native-ultra" });
} catch {
  evaluatorUltra = null;
}
if (evaluatorUltra) {
  assert(evaluatorUltra.effort === "max" && evaluatorUltra.model === "gpt-5.6-sol",
    `evaluator Ultra must reject or safely downgrade to Sol Max, got ${JSON.stringify(evaluatorUltra)}`);
}

const directUltra = resolveCodexAgentPolicy(
  "evaluator",
  { reasoningEffort: "ultra" },
  sourceAgent("evaluator", EXPECTED_POLICY.evaluator),
);
assert(directUltra.model === "gpt-5.6-sol" && directUltra.reasoningEffort === "max",
  `evaluator Ultra safe fallback is not Sol Max: ${JSON.stringify(directUltra)}`);
assert(equal(directUltra.warnings, [CODEX_WARNING_CATEGORIES.topLevelEffortDowngraded]),
  "evaluator Ultra fallback did not emit its fixed diagnostic category");
const economicLeaf = resolve("debugger", { profile: "native-economic" });
assert(equal(economicLeaf, {
  profile: "executor", model: "gpt-5.6-luna", effort: "max", topLevelOnly: false,
}), `native-economic was not safely downgraded for a leaf: ${JSON.stringify(economicLeaf)}`);
assert(equal(resolveCodexAgentPolicy("debugger", { profile: "native-economic" },
  sourceAgent("debugger", EXPECTED_POLICY.debugger)).warnings,
  [CODEX_WARNING_CATEGORIES.topLevelProfileDowngraded]),
  "native-economic leaf rejection did not emit its fixed diagnostic category");
const topLevelUltra = resolveCodexTopLevelProfile("native-ultra");
assert(topLevelUltra.model === "gpt-5.6-sol" && topLevelUltra.reasoningEffort === "ultra" &&
  topLevelUltra.topLevelOnly === true, "native-ultra did not resolve as an explicit top-level profile");
const topLevelEconomic = resolveCodexTopLevelProfile("native-economic");
assert(topLevelEconomic.model === "gpt-5.6-luna" && topLevelEconomic.reasoningEffort === "low" &&
  topLevelEconomic.topLevelOnly === true, "native-economic did not resolve as an explicit top-level profile");

const schema = JSON.parse(
  readFileSync(new URL("../schema/config.schema.json", import.meta.url), "utf8"),
);
const schemaEfforts = schema.definitions?.codexReasoningEffort?.enum ?? [];
assert(equal(schemaEfforts, efforts),
  `schema effort enum drifted from model policy: ${JSON.stringify(schemaEfforts)}`);
assert(!schemaEfforts.includes("ultra"), "schema exposes Ultra as an ordinary subagent effort");
assert(equal(schema.definitions?.codexTopLevelReasoningEffort?.enum, topLevelEfforts),
  "schema top-level effort enum drifted from model policy");
assert(schema.properties?.codex?.properties?.profiles?.properties?.["native-economic"],
  "schema does not expose native-economic profile overrides");

// Exercise both renderers with non-default settings. Sharing the resolver is necessary but this
// comparison proves neither renderer drops or renames the resolved fields on its own surface.
const ROOT = fileURLToPath(new URL("../", import.meta.url));
const [
  { agentToToml, codexSettingsFromConfig },
  { buildNativeAgents, topLevelProfileToToml },
] = await Promise.all([
  import("../codex/install.mjs"),
  import("../codex/native-plugin.mjs"),
]);
const ultraToml = topLevelProfileToToml("native-ultra");
assert(/^model\s*=\s*"gpt-5\.6-sol"$/m.test(ultraToml),
  "native-ultra profile file lost the Sol model");
assert(/^model_reasoning_effort\s*=\s*"ultra"$/m.test(ultraToml),
  "native-ultra profile file lost Ultra reasoning");
assert(!/name\s*=|developer_instructions\s*=|sandbox_mode\s*=/.test(ultraToml),
  "top-level native-ultra output was rendered as a subagent role");
const exampleSettings = codexSettingsFromConfig(JSON.parse(
  readFileSync(new URL("../examples/config.monorepo.json", import.meta.url), "utf8"),
));
assert(exampleSettings.profiles?.executor?.model === "gpt-5.6-luna" &&
  exampleSettings.profiles?.scout?.reasoningEffort === "medium",
"config reader dropped semantic profile overrides");
const paritySettings = {
  profiles: { executor: { model: "gpt-5.6-terra", reasoningEffort: "high" } },
  agents: { evaluator: { model: "operator-sol", reasoningEffort: "xhigh" } },
};
const nativeWarnings = [];
const nativeAgents = buildNativeAgents(ROOT, paritySettings, (warning) => nativeWarnings.push(warning));
const cloneWarnings = [];
const scalar = (source, key, separator = "=") => {
  const re = new RegExp(`^${key}\\s*${separator}\\s*["']?([^"'\\r\\n#]+)`, "m");
  return re.exec(source)?.[1]?.trim() ?? null;
};
for (const name of Object.keys(EXPECTED_POLICY)) {
  const source = readFileSync(new URL(`../agents/${name}.md`, import.meta.url), "utf8");
  const clone = agentToToml(source, paritySettings, (warning) => cloneWarnings.push(warning));
  const native = nativeAgents[`${name}.toml`];
  assert(scalar(clone, "model") === scalar(native, "model"),
    `${name}: override model differs between clone and native renderers`);
  assert(scalar(clone, "model_reasoning_effort") === scalar(native, "model_reasoning_effort"),
    `${name}: override effort differs between clone and native renderers`);
}
assert(equal(cloneWarnings, nativeWarnings), "override diagnostics differ between clone and native renderers");

const secretSentinel = "CODEX_SECRET_OVERRIDE_SENTINEL";
const secretProbe = spawnSync(process.execPath, ["-e", `
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
`], { encoding: "utf8" });
const secretOutput = `${secretProbe.stdout ?? ""}${secretProbe.stderr ?? ""}`;
assert(!secretOutput.includes(secretSentinel), "override diagnostics leaked a secret sentinel");

console.log(`codex-policy: ${Object.keys(EXPECTED_POLICY).length} defaults, overrides, native-companion parity and Ultra guard checked`);
