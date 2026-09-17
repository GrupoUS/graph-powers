/**
 * The single Kilo model-routing authority for Graph Powers.
 *
 * Canonical agent Markdown stays Claude-oriented (`model: opus`). This resolver turns that semantic
 * role into an exact Kilo `provider/model` id, and refuses anything that is not one.
 *
 * Why a resolver instead of writing ids into the agent files: the id in a tracked agent is a
 * personal routing decision, and the harness is shared by every repository on the machine. Kilo
 * already has an authority for the same decision — `agent.<id>.model` in `kilo.jsonc` — so the
 * generated agents carry the semantic default and the operator's config still wins.
 *
 * The defaults route through the operator's own subscriptions (`openai/…`, `xai/…`) rather than the
 * `kilo/…` gateway, so a session does not bill the KiloCode API per token, and they carry a
 * reasoning `variant` because the subscription catalogs advertise one. Proven against 7.6.2: an
 * agent Markdown `model:` and `variant:` are both authoritative, and `agent.<id>.*` in `kilo.jsonc`
 * only fills a field the Markdown left out — which is exactly why a model change made in the TUI
 * reverts, and why the default has to be right here.
 *
 * Claude aliases (`opus`, `sonnet`, `haiku`, `fable`) and Codex slugs (`gpt-5.6-sol`) must never
 * reach a Kilo agent: they resolve to nothing, and a model that resolves to nothing is a subagent
 * that silently stops. `isKiloModelId` is the gate that proves the difference — a Kilo id always
 * carries a provider segment.
 */

import { readFileSync } from "node:fs";

const raw = JSON.parse(readFileSync(new URL("./model-policy.json", import.meta.url), "utf8"));

function deepFreeze(value) {
  if (!value || typeof value !== "object" || Object.isFrozen(value)) return value;
  for (const child of Object.values(value)) deepFreeze(child);
  return Object.freeze(value);
}

export const KILO_MODEL_POLICY = deepFreeze(raw);
export const KILO_AGENT_PROFILES = KILO_MODEL_POLICY.agents;
export const KILO_PROFILE_DEFAULTS = KILO_MODEL_POLICY.profiles;
export const KILO_WARNING_CATEGORIES = KILO_MODEL_POLICY.warningCategories;
export const KILO_LEAF_AGENTS = new Set(KILO_MODEL_POLICY.leafAgents ?? []);
export const TIER_BY_FAMILY = KILO_MODEL_POLICY.legacyTiers;

/** The Claude model families this repository uses. They are never valid on the Kilo side. */
const CLAUDE_FAMILIES = new Set(Object.keys(TIER_BY_FAMILY));

function text(value) {
  return typeof value === "string" ? value.trim() : "";
}

/**
 * A usable Kilo model id: `provider/model`, with neither side empty.
 *
 * The provider segment is what separates a Kilo id from a Claude alias or a Codex slug. Rejecting
 * those here — rather than letting the provider layer fail later — is what keeps a leaked
 * `model: opus` from producing a subagent that starts and never answers.
 */
export function isKiloModelId(model) {
  const name = text(model);
  if (!name || name.includes(" ")) return false;
  if (CLAUDE_FAMILIES.has(name.toLowerCase()) || name.toLowerCase().startsWith("claude")) {
    return false;
  }
  const slash = name.indexOf("/");
  if (slash <= 0 || slash === name.length - 1) return false;
  const provider = name.slice(0, slash).toLowerCase();
  return !CLAUDE_FAMILIES.has(provider);
}

/**
 * Pick the first candidate that carries a model, refusing anything that is not a Kilo id.
 *
 * The model and the reasoning variant resolve independently. A per-agent override that names a
 * model but no variant must not inherit the profile default's variant — a Luna override on an Astra
 * profile would otherwise carry a variant Astra never advertised. A variant-only override still
 * applies, because it is explicit.
 */
function firstModel(candidates) {
  for (const candidate of candidates) {
    const value = text(candidate.value);
    if (!value) continue;
    if (!isKiloModelId(value)) {
      throw new Error(
        "invalid Kilo model override: expected provider/model; Claude aliases and Codex slugs " +
          "cannot enter a Kilo agent",
      );
    }
    return { value, source: candidate.source };
  }
  return null;
}

/** Pick the first explicit reasoning-effort override, rejecting a blank value rather than ignoring it. */
function firstVariant(candidates) {
  for (const candidate of candidates) {
    if (candidate.value === undefined || candidate.value === null) continue;
    const value = text(candidate.value);
    if (!value) {
      throw new Error(
        "invalid Kilo variant override: expected a non-empty reasoning effort such as low, high, xhigh or max",
      );
    }
    return { value, source: candidate.source };
  }
  return null;
}

/** `agent.<id>` in `kilo.jsonc` is the native override surface. `agents` is the legacy spelling. */
function agentOverride(settings, agentName) {
  const native = settings?.agent?.[agentName];
  if (native && typeof native === "object") return native;
  const mirror = settings?.agents?.[agentName];
  return mirror && typeof mirror === "object" ? mirror : {};
}

function sourceFamily(sourceAgent = {}) {
  const model = Array.isArray(sourceAgent.model) ? sourceAgent.model[0] : sourceAgent.model;
  return text(model).toLowerCase();
}

/**
 * Resolve one generated Graph Powers subagent.
 *
 * Precedence: per-agent override -> profile override -> legacy tier -> legacy flat -> semantic
 * default. This matches the Codex resolver on purpose: one harness, one order, and an operator who
 * learned it on one client does not have to learn a second.
 */
export function resolveKiloAgentPolicy(agentName, settings = {}, sourceAgent = {}) {
  const name = text(agentName);
  if (!name) throw new Error("Kilo agent policy requires an agent name");

  const profile = KILO_AGENT_PROFILES[name] ?? null;
  const profileDefault = profile ? KILO_PROFILE_DEFAULTS[profile] : null;
  const override = agentOverride(settings, name);
  const profileOverride = profile ? settings?.profiles?.[profile] : undefined;
  if (profileOverride !== undefined && (!profileOverride || typeof profileOverride !== "object")) {
    throw new Error("Kilo profile override must be an object");
  }

  const warnings = [];
  const family = sourceFamily(sourceAgent);
  const tier = profile ? null : (TIER_BY_FAMILY[family] ?? null);
  const model = firstModel([
    { value: override.model, source: "agent-override" },
    { value: profileOverride?.model, source: "profile-override" },
    { value: tier ? settings?.models?.[tier] : null, source: tier ? `legacy-models.${tier}` : null },
    { value: settings?.model, source: "legacy-model" },
    { value: profileDefault?.model, source: "semantic-default" },
  ]);
  // An explicit override always wins. Otherwise the profile's variant rides only with the profile's
  // own model: an operator who changed the model without naming an effort gets the model's own
  // default, not a variant that belonged to a model they replaced.
  const variantOverride = firstVariant([
    { value: override.variant, source: "agent-override" },
    { value: profileOverride?.variant, source: "profile-override" },
  ]);
  const variant =
    variantOverride?.value ??
    (model?.source === "semantic-default" ? text(profileDefault?.variant) || null : null);
  if (model && model.source !== "semantic-default" && model.source !== "session-inheritance") {
    warnings.push(KILO_WARNING_CATEGORIES.modelOverrideUnverified);
  }

  return {
    agent: name,
    profile,
    model: model?.value ?? null,
    variant,
    modelSource: model?.source ?? "session-inheritance",
    policySource: profile ? "kilo/model-policy.json" : "legacy-extension-agent",
    leaf: KILO_LEAF_AGENTS.has(name),
    warnings,
  };
}

/** The semantic profile for a canonical agent, or null for an extension agent. */
export function kiloProfileFor(agentName) {
  return KILO_AGENT_PROFILES[text(agentName)] ?? null;
}

if (Object.keys(KILO_AGENT_PROFILES).length !== 12) {
  throw new Error("Kilo model policy must assign exactly the 12 canonical Graph Powers agents");
}
for (const [agent, profile] of Object.entries(KILO_AGENT_PROFILES)) {
  if (!Object.hasOwn(KILO_PROFILE_DEFAULTS, profile)) {
    throw new Error(`Kilo agent ${agent} references unknown profile ${profile}`);
  }
}
for (const [profile, body] of Object.entries(KILO_PROFILE_DEFAULTS)) {
  if (!isKiloModelId(body.model)) {
    throw new Error(`Kilo profile ${profile} does not carry a provider/model id`);
  }
  if (!text(body.variant)) {
    throw new Error(`Kilo profile ${profile} does not carry a reasoning variant`);
  }
}
for (const agent of KILO_LEAF_AGENTS) {
  if (!Object.hasOwn(KILO_AGENT_PROFILES, agent)) {
    throw new Error(`Kilo leaf agent ${agent} has no semantic profile`);
  }
}
