/**
 * The single Codex model-routing authority for Graph Powers.
 *
 * Canonical agent Markdown remains Claude-oriented. Both Codex generators call this resolver,
 * and workflows read the adjacent JSON contract through their existing configuration bootstrap.
 * Model selection is semantic: judges and architects spend Sol; iterative workers and scouts use
 * Luna. Ultra is deliberately absent from the subagent effort set because Codex treats it as a
 * proactive orchestration policy, not a larger single-agent reasoning budget.
 */

import { readFileSync } from "node:fs";

const raw = JSON.parse(readFileSync(new URL("./model-policy.json", import.meta.url), "utf8"));

function deepFreeze(value) {
  if (!value || typeof value !== "object" || Object.isFrozen(value)) return value;
  for (const child of Object.values(value)) deepFreeze(child);
  return Object.freeze(value);
}

export const CODEX_MODEL_POLICY = deepFreeze(raw);
export const CODEX_AGENT_PROFILES = CODEX_MODEL_POLICY.agents;
export const CODEX_PROFILE_DEFAULTS = CODEX_MODEL_POLICY.profiles;
export const CODEX_REASONING_EFFORTS = CODEX_MODEL_POLICY.reasoningEfforts;
export const CODEX_TOP_LEVEL_REASONING_EFFORTS = CODEX_MODEL_POLICY.topLevelReasoningEfforts;
export const CODEX_WARNING_CATEGORIES = CODEX_MODEL_POLICY.warningCategories;
export const CODEX_LEAF_AGENTS = new Set(CODEX_MODEL_POLICY.leafAgents ?? []);
export const TIER_BY_MODEL = CODEX_MODEL_POLICY.legacyTiers;
export const CLAUDE_MODEL_FAMILIES = new Set(Object.keys(TIER_BY_MODEL));

const SUBAGENT_EFFORTS = new Set(CODEX_REASONING_EFFORTS);
const SUBAGENT_PROFILES = new Set(
  Object.entries(CODEX_PROFILE_DEFAULTS)
    .filter(([, value]) => value.topLevelOnly !== true)
    .map(([name]) => name),
);

for (const key of ["topLevelProfileDowngraded", "topLevelEffortDowngraded", "modelOverrideUnverified"]) {
  if (typeof CODEX_WARNING_CATEGORIES?.[key] !== "string") {
    throw new Error("Codex model policy warning categories are incomplete");
  }
}

function text(value) {
  return typeof value === "string" ? value.trim() : "";
}

function own(object, key) {
  return object && typeof object === "object" && Object.hasOwn(object, key);
}

function firstModel(candidates) {
  for (const candidate of candidates) {
    const value = text(candidate.value);
    if (!value) continue;
    if (!isCodexModelSlug(value)) {
      throw new Error("invalid Codex model override; Claude model families cannot enter Codex output");
    }
    return { ...candidate, value };
  }
  return null;
}

function validateEffort(value, source, allowed = SUBAGENT_EFFORTS) {
  const effort = text(value).toLowerCase();
  if (!effort) return null;
  if (!allowed.has(effort)) {
    throw new Error("invalid Codex reasoning effort override");
  }
  return effort;
}

function legacySource(sourceAgent = {}) {
  const family = text(Array.isArray(sourceAgent.model) ? sourceAgent.model[0] : sourceAgent.model)
    .toLowerCase();
  return {
    family,
    tier: TIER_BY_MODEL[family] ?? null,
    effort: text(
      Array.isArray(sourceAgent.effort) ? sourceAgent.effort[0] : sourceAgent.effort,
    ).toLowerCase(),
  };
}

function agentOverride(settings, agentName) {
  const current = settings?.agents?.[agentName];
  if (current && typeof current === "object") return current;
  // `agentOverrides` shipped briefly in development builds. Accepting it costs nothing and keeps
  // those configs readable, while the public schema exposes the shorter `agents` spelling.
  const migration = settings?.agentOverrides?.[agentName];
  return migration && typeof migration === "object" ? migration : {};
}

function requestedProfile(agentName, settings, override, warnings) {
  const semantic = CODEX_AGENT_PROFILES[agentName] ?? null;
  const requested = text(override.profile) || text(settings?.profile) || semantic;
  if (!requested) return null;
  if (!own(CODEX_PROFILE_DEFAULTS, requested)) {
    throw new Error("unknown Codex profile override");
  }
  if (CODEX_PROFILE_DEFAULTS[requested].topLevelOnly === true) {
    if (!semantic) {
      throw new Error("top-level-only Codex profile cannot configure an extension agent");
    }
    warnings.push(CODEX_WARNING_CATEGORIES.topLevelProfileDowngraded);
    return semantic;
  }
  return requested;
}

/** True for a usable Codex model slug and false for a leaked Claude family. */
export function isCodexModelSlug(model) {
  const name = text(model);
  if (!name) return false;
  const lower = name.toLowerCase();
  if (CLAUDE_MODEL_FAMILIES.has(lower) || lower.startsWith("claude")) return false;
  return true;
}

/** Legacy Claude-family tier selection, retained as an operator override rather than a default. */
export function legacyCodexModelFor(claudeFamily, { model, models } = {}) {
  const tier = TIER_BY_MODEL[text(claudeFamily).toLowerCase()];
  return firstModel([
    { value: tier ? models?.[tier] : null, source: tier ? `legacy-models.${tier}` : null },
    { value: model, source: "legacy-model" },
  ])?.value ?? null;
}

/**
 * Resolve one generated Graph Powers subagent.
 *
 * Precedence keeps the old tier-over-flat behavior for existing explicit configurations:
 * per-agent override -> profile override -> legacy tier -> legacy flat -> semantic default.
 * Reasoning uses per-agent -> profile -> legacy global -> semantic default. Claude frontmatter is
 * consulted only for an unknown extension agent, never for the twelve canonical Codex roles.
 */
export function resolveCodexAgentPolicy(agentName, settings = {}, sourceAgent = {}) {
  const name = text(agentName);
  if (!name) throw new Error("Codex agent policy requires an agent name");

  const warnings = [];
  const override = agentOverride(settings, name);
  const profile = requestedProfile(name, settings, override, warnings);
  const profileDefault = profile ? CODEX_PROFILE_DEFAULTS[profile] : null;
  const profileOverride = profile ? settings?.profiles?.[profile] : undefined;
  if (profileOverride !== undefined && (!profileOverride || typeof profileOverride !== "object")) {
    throw new Error("Codex profile override must be an object");
  }

  const legacy = legacySource(sourceAgent);
  const modelChoice = firstModel([
    { value: override.model, source: "agent-override" },
    { value: profileOverride?.model, source: "profile-override" },
    {
      value: legacy.tier ? settings?.models?.[legacy.tier] : null,
      source: legacy.tier ? `legacy-models.${legacy.tier}` : null,
    },
    { value: settings?.model, source: "legacy-model" },
    { value: profileDefault?.model, source: "semantic-default" },
  ]);
  if (modelChoice?.source !== "semantic-default" && modelChoice?.source !== "session-inheritance") {
    warnings.push(CODEX_WARNING_CATEGORIES.modelOverrideUnverified);
  }

  let effortChoice = null;
  for (const candidate of [
    { value: override.reasoningEffort ?? override.effort, source: "agent-override" },
    {
      value: profileOverride?.reasoningEffort ?? profileOverride?.effort,
      source: "profile-override",
    },
    { value: settings?.reasoningEffort, source: "legacy-reasoning-effort" },
    { value: profileDefault?.reasoningEffort, source: "semantic-default" },
  ]) {
    const value = text(candidate.value).toLowerCase();
    if (!value) continue;
    if (value === "ultra") {
      const safe = profileDefault?.reasoningEffort;
      if (!safe || safe === "ultra") {
        throw new Error("top-level-only Codex effort has no safe semantic fallback");
      }
      warnings.push(CODEX_WARNING_CATEGORIES.topLevelEffortDowngraded);
      effortChoice = { value: safe, source: "ultra-safe-fallback" };
      break;
    }
    effortChoice = { value: validateEffort(value, candidate.source), source: candidate.source };
    break;
  }

  // Extension agents that predate the semantic map retain their old frontmatter behavior. The
  // twelve canonical agents never reach this branch, so Claude tuning cannot override Codex.
  if (!effortChoice && !profile) {
    const legacyEffort = validateEffort(legacy.effort, "source-agent-frontmatter");
    if (legacyEffort) effortChoice = { value: legacyEffort, source: "source-agent-frontmatter" };
  }

  let finalModel = modelChoice;
  if (effortChoice?.source === "ultra-safe-fallback") {
    finalModel = { value: profileDefault.model, source: "ultra-safe-fallback" };
  }

  return {
    profile,
    model: finalModel?.value ?? null,
    reasoningEffort: effortChoice?.value ?? null,
    modelSource: finalModel?.source ?? "session-inheritance",
    reasoningEffortSource: effortChoice?.source ?? "session-inheritance",
    policySource: profile ? "codex/model-policy.json" : "legacy-extension-agent",
    topLevelOnly: false,
    escalationProfile: profileDefault?.escalationProfile ?? null,
    leaf: CODEX_LEAF_AGENTS.has(name),
    warnings,
  };
}

/** Resolve the explicit top-level Codex orchestration profile. Never call this for a subagent. */
export function resolveCodexTopLevelProfile(profileName, settings = {}) {
  const name = text(profileName);
  const base = CODEX_PROFILE_DEFAULTS[name];
  if (!base?.topLevelOnly) {
    throw new Error("requested Codex profile is not top-level-only");
  }
  const override = settings?.profiles?.[name] ?? {};
  if (!override || typeof override !== "object") {
    throw new Error("Codex profile override must be an object");
  }
  const model = firstModel([
    { value: override.model, source: "profile-override" },
    { value: base.model, source: "semantic-default" },
  ]);
  const reasoningEffort = validateEffort(
    override.reasoningEffort ?? override.effort ?? base.reasoningEffort,
    "top-level profile",
    new Set([base.reasoningEffort]),
  );
  return {
    profile: name,
    model: model?.value ?? null,
    reasoningEffort,
    modelSource: model?.source ?? "session-inheritance",
    reasoningEffortSource: own(override, "reasoningEffort") || own(override, "effort")
      ? "profile-override"
      : "semantic-default",
    policySource: "codex/model-policy.json",
    topLevelOnly: true,
    warnings: model?.source === "profile-override"
      ? [CODEX_WARNING_CATEGORIES.modelOverrideUnverified]
      : [],
  };
}

if (Object.keys(CODEX_AGENT_PROFILES).length !== 12) {
  throw new Error("Codex model policy must assign exactly the 12 canonical Graph Powers agents");
}
for (const [agent, profile] of Object.entries(CODEX_AGENT_PROFILES)) {
  if (!SUBAGENT_PROFILES.has(profile)) {
    throw new Error(`Codex agent ${agent} references non-subagent profile ${profile}`);
  }
}
for (const agent of CODEX_LEAF_AGENTS) {
  if (!Object.hasOwn(CODEX_AGENT_PROFILES, agent)) {
    throw new Error(`Codex leaf agent ${agent} has no semantic profile`);
  }
}
