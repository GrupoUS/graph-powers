#!/usr/bin/env bun
/** Bounded typed Jev routing: validate, reserve once, evaluate once, then record. */

import { spawnSync } from "node:child_process";
import { readFileSync, realpathSync } from "node:fs";
import { dirname, isAbsolute, join, posix, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

import { readCodexSettings } from "./install.mjs";
import { asList, listDirs, listMarkdown, parseFrontmatter } from "./lib.mjs";
import {
  CODEX_MODEL_POLICY,
  resolveCodexAgentPolicy,
  resolveCodexEvaluationPolicy,
} from "./model-policy.mjs";

const SDD = fileURLToPath(new URL("../skills/planning/scripts/sdd.py", import.meta.url));
const JEV_MODEL = CODEX_MODEL_POLICY.evaluation.model;
const JEV_ENDPOINT = CODEX_MODEL_POLICY.evaluation.endpoint;
const ID = /^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/;
const ROLE = /^[a-z][a-z0-9-]{0,63}$/;
const MAX_CANDIDATES = 64;
const MAX_TEXT = 4096;
const MAX_ITEM = 2048;
const MAX_REQUEST = 65536;
const MAX_STATE = 16384;
const SOURCE_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");

function blocked(code) {
  return {
    status: "BLOCKED",
    verdict: "BLOCKED",
    evaluationError: { code, reason: "typed evaluation failed" },
  };
}

function skipped(reason) {
  return { status: "SKIPPED", reason };
}

function gitRoot(directory) {
  const done = spawnSync("git", ["rev-parse", "--show-toplevel"], {
    cwd: directory,
    encoding: "utf8",
  });
  if (done.status !== 0 || !done.stdout.trim()) throw new Error("project or plan is not in Git");
  return realpathSync(done.stdout.trim());
}

function projectPaths(projectDir, planPath) {
  if (typeof projectDir !== "string" || typeof planPath !== "string") {
    throw new Error("invalid project or plan path");
  }
  const root = realpathSync(resolve(projectDir));
  const plan = realpathSync(resolve(root, planPath));
  const planRelative = relative(root, plan);
  if (
    !planRelative ||
    planRelative === ".." ||
    planRelative.startsWith(`..${sep}`) ||
    isAbsolute(planRelative)
  ) {
    throw new Error("plan escapes project");
  }
  if (gitRoot(root) !== gitRoot(dirname(plan))) throw new Error("plan belongs to another Git root");
  return { root, planPath: planRelative };
}

function isObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function isJson(value, seen = new Set()) {
  if (value === null || typeof value === "string" || typeof value === "boolean") return true;
  if (typeof value === "number") return Number.isFinite(value);
  if (typeof value !== "object" || seen.has(value)) return false;
  seen.add(value);
  const values = Array.isArray(value) ? value : Object.values(value);
  return values.every((item) => isJson(item, seen));
}

function jsonSize(value) {
  if (!isJson(value)) throw new Error("invalid JSON value");
  return Buffer.byteLength(JSON.stringify(value), "utf8");
}

function text(value, name, limit = MAX_TEXT) {
  if (typeof value !== "string" || !value.trim() || value.trim().length > limit) {
    throw new Error(`invalid ${name}`);
  }
  return value.trim();
}

function list(value, name) {
  if (!Array.isArray(value) || value.length === 0 || value.length > 32) {
    throw new Error(`invalid ${name}`);
  }
  return value.map((item) => text(item, name, MAX_ITEM));
}

function state(value) {
  if (!isObject(value) || Object.keys(value).length === 0 || jsonSize(value) > MAX_STATE) {
    throw new Error("invalid state");
  }
  return value;
}

/** Source-derived actions; method names are bare, with optional graph-powers: or /command input. */
export function routingCatalog(settings = {}) {
  const entries = [];
  for (const [kind, paths] of [
    ["skill", listDirs(join(SOURCE_ROOT, "skills")).map((name) => `skills/${name}/SKILL.md`)],
    ["command", listMarkdown(join(SOURCE_ROOT, "commands")).map((name) => `commands/${name}`)],
    ["agent", listMarkdown(join(SOURCE_ROOT, "agents")).map((name) => `agents/${name}`)],
  ]) {
    for (const path of paths) {
      const target = realpathSync(join(SOURCE_ROOT, path));
      const rel = relative(realpathSync(SOURCE_ROOT), target);
      if (isAbsolute(rel) || rel === ".." || rel.startsWith(`..${sep}`))
        throw new Error("catalog path escapes source");
      const { data } = parseFrontmatter(readFileSync(target, "utf8"));
      const name =
        kind === "skill" ? posix.basename(posix.dirname(path)) : posix.basename(path, ".md");
      if (!ROLE.test(name)) throw new Error("invalid catalog name");
      const agent = kind === "agent";
      const resolved = agent ? resolveCodexAgentPolicy(name, settings, data) : {};
      const skills = agent
        ? asList(data.skills).map((value) => methodName(value, "skill"))
        : kind === "skill"
          ? [name]
          : [];
      entries.push({
        id: `${kind}:${name}`,
        kind,
        role: agent ? name : "main",
        skills,
        command: kind === "command" ? name : null,
        model: resolved.model ?? null,
        reasoningEffort: resolved.reasoningEffort ?? null,
        description: text(data.description, "catalog description"),
        path,
      });
    }
  }
  for (const entry of entries) {
    if (entry.skills.some((name) => !entries.some((item) => item.id === `skill:${name}`)))
      throw new Error("unknown required skill");
  }
  return entries;
}

function methodName(value, kind) {
  let name = text(value, kind, 128).replace(/^graph-powers:/, "");
  if (kind === "command") name = name.replace(/^\//, "");
  if (!ROLE.test(name)) throw new Error(`invalid ${kind}`);
  return name;
}

function resolveCandidates(rawCandidates, settings) {
  if (
    !Array.isArray(rawCandidates) ||
    !rawCandidates.length ||
    rawCandidates.length > MAX_CANDIDATES
  )
    throw new Error("invalid candidates");
  const catalog = new Map(routingCatalog(settings).map((entry) => [entry.id, entry]));
  const ids = new Set();
  const actions = new Set();
  const candidates = [];
  for (const candidate of rawCandidates) {
    if (
      !isObject(candidate) ||
      Object.keys(candidate).some(
        (key) => !["id", "kind", "role", "skills", "command", "capability"].includes(key),
      )
    )
      throw new Error("invalid candidate");
    const id = text(candidate.id, "candidate id", 128);
    if (!ID.test(id) || ids.has(id)) throw new Error("invalid candidate identity");
    ids.add(id);
    const kind = candidate.kind ?? "agent";
    const role = text(candidate.role, "candidate role", 64);
    if (!["agent", "skill", "command", "finish"].includes(kind)) throw new Error("invalid kind");
    const source = kind === "agent" ? catalog.get(`agent:${role}`) : null;
    if (kind === "agent" ? !source : role !== "main") throw new Error("unknown candidate role");
    if (
      candidate.skills !== undefined &&
      (!Array.isArray(candidate.skills) || candidate.skills.length > 32)
    )
      throw new Error("invalid skills");
    const skills = [
      ...new Set([
        ...(source?.skills ?? []),
        ...(candidate.skills ?? []).map((value) => methodName(value, "skill")),
      ]),
    ].sort();
    if (skills.some((name) => !catalog.has(`skill:${name}`))) throw new Error("unknown skill");
    const command = candidate.command == null ? null : methodName(candidate.command, "command");
    if (command && !catalog.has(`command:${command}`)) throw new Error("unknown command");
    if (
      (kind === "skill" && (!skills.length || command)) ||
      (kind === "command" && !command) ||
      (kind === "finish" && (skills.length || command))
    )
      throw new Error("invalid action methods");
    let capabilityEvidence;
    if (source) {
      const capability = candidate.capability;
      if (
        !isObject(capability) ||
        Object.keys(capability).some(
          (key) => !["model", "reasoningEffort", "status", "evidence"].includes(key),
        )
      )
        throw new Error("invalid capability");
      capabilityEvidence = text(capability.evidence, "capability evidence", MAX_ITEM);
      if (capability.status !== "SUPPORTED") throw new Error("unsupported capability");
      if (
        !source.model ||
        !source.reasoningEffort ||
        source.model !== capability.model ||
        source.reasoningEffort !== capability.reasoningEffort
      )
        throw new Error("capability mismatch");
    } else if (candidate.capability != null) throw new Error("main does not select a model");
    const identity = JSON.stringify([kind, role, skills, command]);
    if (actions.has(identity)) continue;
    actions.add(identity);
    const legacy = ["kind", "skills", "command"].every((key) => !Object.hasOwn(candidate, key));
    const descriptions = [
      source?.description,
      ...skills.map((name) => catalog.get(`skill:${name}`).description),
      command && catalog.get(`command:${command}`).description,
    ].filter(Boolean);
    candidates.push({
      id,
      role,
      model: source?.model ?? null,
      reasoningEffort: source?.reasoningEffort ?? null,
      ...(!legacy && { kind, skills, command }),
      capabilityEvidence,
      criterion:
        `${kind} ${role}; skills: ${skills.join(", ") || "none"}; command: ${command ?? "none"}. ${
          kind === "finish"
            ? "Finish only after the controller confirms completion and required evidence."
            : descriptions.join(" ")
        }`.slice(0, MAX_ITEM),
    });
  }
  return candidates;
}

function requestFor(input, policy, candidates) {
  const request = {
    model: JEV_MODEL,
    state: state(input.state),
    questions: {
      route: {
        type: "choice",
        instructions: text(input.question, "question"),
        criteria: Object.fromEntries(
          candidates.map((candidate) => [candidate.id, candidate.criterion]),
        ),
      },
    },
    candidates: candidates.map(
      ({ capabilityEvidence: _capabilityEvidence, criterion: _criterion, ...candidate }) =>
        candidate,
    ),
    policy: {
      endpoint: policy.endpoint,
      timeoutMs: policy.timeoutMs,
      capabilities: Object.fromEntries(
        candidates
          .filter((candidate) => candidate.role !== "main")
          .map((candidate) => [
            candidate.id,
            {
              model: candidate.model,
              reasoningEffort: candidate.reasoningEffort,
              status: "SUPPORTED",
              evidence: candidate.capabilityEvidence,
            },
          ]),
      ),
    },
  };
  if (jsonSize(request) > MAX_REQUEST) throw new Error("evaluation request too large");
  return request;
}

function envelopeFor(input, request) {
  return {
    taskId: text(input.taskId, "taskId", 128),
    decisionKey: text(input.decisionKey, "decisionKey", 128),
    question: text(input.question, "question"),
    evidence: list(input.evidence, "evidence"),
    options: request.candidates.map((candidate) => candidate.id),
    recommendation: request.candidates[0].id,
    risk: text(input.risk, "risk"),
    verdict: "PENDING",
    requesterRole: input.requesterRole === "controller" ? "controller" : "parent",
    depth: input.depth,
    backend: "jev",
    capabilityStatus: "SUPPORTED",
    status: "RESERVED",
    evaluationRequest: request,
  };
}

function ledger(action, paths, envelope) {
  const windows = process.platform === "win32";
  const command = windows ? "py" : "python3";
  const args = [
    ...(windows ? ["-3"] : []),
    "-B",
    "-X",
    "utf8",
    SDD,
    "consult",
    action,
    paths.planPath,
    action === "reserve" ? "--request-json" : "--result-json",
    JSON.stringify(envelope),
  ];
  const done = spawnSync(command, args, {
    cwd: paths.root,
    encoding: "utf8",
  });
  let output;
  try {
    output = JSON.parse(done.stdout);
  } catch {
    throw new Error("consultation ledger failed");
  }
  if (done.status !== 0 && done.status !== 4) throw new Error("consultation ledger failed");
  return output;
}

function validateResult(result, candidates) {
  if (
    !isObject(result) ||
    result.model !== JEV_MODEL ||
    !isObject(result.answers) ||
    !isObject(result.answers.route)
  ) {
    throw new Error("invalid result");
  }
  const route = result.answers.route;
  const ids = new Set(candidates.map((candidate) => candidate.id));
  if (
    route.type !== "choice" ||
    typeof route.choice !== "string" ||
    !ids.has(route.choice) ||
    !isObject(route.probabilities) ||
    Object.keys(route.probabilities).length !== ids.size ||
    Object.keys(route.probabilities).some((id) => !ids.has(id))
  ) {
    throw new Error("invalid result");
  }
  let total = 0;
  for (const id of ids) {
    const probability = route.probabilities[id];
    if (!Number.isFinite(probability) || probability < 0 || probability > 1)
      throw new Error("invalid result");
    total += probability;
  }
  if (Math.abs(total - 1) > 1e-9) throw new Error("invalid result");
  return {
    model: JEV_MODEL,
    answers: {
      route: {
        type: "choice",
        choice: route.choice,
        probabilities: Object.fromEntries([...ids].map((id) => [id, route.probabilities[id]])),
      },
    },
  };
}

function record(paths, reservation, update) {
  try {
    return ledger("record", paths, { ...reservation, ...update });
  } catch {
    return {
      ...reservation,
      callAuthorized: false,
      evaluationError: { code: "RECORD_FAILED", reason: "typed evaluation failed" },
    };
  }
}

async function send(request, policy, fetchImpl, credential) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), policy.timeoutMs);
  try {
    const response = await fetchImpl(policy.endpoint, {
      method: "POST",
      headers: { "content-type": "application/json", Authorization: `Bearer ${credential}` },
      body: JSON.stringify({
        model: request.model,
        state: request.state,
        questions: request.questions,
      }),
      redirect: "error",
      signal: controller.signal,
    });
    if (!response?.ok) {
      const code =
        response?.status === 401
          ? "HTTP_UNAUTHORIZED"
          : response?.status === 403
            ? "HTTP_FORBIDDEN"
            : response?.status === 429
              ? "HTTP_RATE_LIMITED"
              : response?.status >= 500
                ? "HTTP_SERVER_ERROR"
                : "HTTP_ERROR";
      return { error: code };
    }
    try {
      return {
        result: await Promise.race([
          response.json(),
          new Promise((_, reject) =>
            controller.signal.addEventListener("abort", reject, { once: true }),
          ),
        ]),
      };
    } catch {
      return { error: controller.signal.aborted ? "TIMEOUT" : "INVALID_RESPONSE" };
    }
  } catch {
    return { error: controller.signal.aborted ? "TIMEOUT" : "NETWORK_FAILURE" };
  } finally {
    clearTimeout(timer);
  }
}

/** Evaluate a material routing doubt. `fetchImpl` and `env` exist solely for bounded local tests. */
export async function evaluateRouting(
  input,
  { projectDir, planPath, fetchImpl = fetch, env = process.env } = {},
) {
  let paths;
  let settings;
  let policy;
  try {
    paths = projectPaths(projectDir, planPath);
    settings = readCodexSettings(paths.root);
    policy = resolveCodexEvaluationPolicy(settings);
  } catch {
    return blocked("INVALID_CONFIGURATION");
  }
  if (!policy.enabled) return skipped("EVALUATION_DISABLED");
  if (!isObject(input) || typeof input.materialDoubt !== "boolean") return blocked("INVALID_INPUT");
  if (!input.materialDoubt) return skipped("NO_MATERIAL_DOUBT");
  if (policy.model !== JEV_MODEL || policy.endpoint !== JEV_ENDPOINT)
    return blocked("INVALID_CONFIGURATION");

  let candidates;
  let request;
  let reservation;
  try {
    if (input.requesterRole !== "parent" && input.requesterRole !== "controller")
      throw new Error("invalid requester");
    if (input.depth !== 0) throw new Error("invalid depth");
    candidates = resolveCandidates(input.candidates, settings);
    request = requestFor(input, policy, candidates);
    reservation = envelopeFor(input, request);
    reservation = ledger("reserve", paths, reservation);
  } catch (error) {
    return blocked(
      error instanceof Error && error.message === "capability mismatch"
        ? "CAPABILITY_MISMATCH"
        : "INVALID_INPUT",
    );
  }
  if (reservation.status !== "RESERVED" || reservation.callAuthorized !== true) return reservation;

  const credential = env?.AI_GATEWAY_API_KEY;
  if (typeof credential !== "string" || !credential) {
    return record(paths, reservation, {
      status: "BLOCKED",
      verdict: "BLOCKED",
      evaluationError: { code: "CREDENTIAL_UNAVAILABLE", reason: "typed evaluation failed" },
    });
  }
  const sent = await send(request, policy, fetchImpl, credential);
  if (sent.error) {
    return record(paths, reservation, {
      status: "BLOCKED",
      verdict: "BLOCKED",
      evaluationError: { code: sent.error, reason: "typed evaluation failed" },
    });
  }
  try {
    const evaluationResult = validateResult(sent.result, candidates);
    return record(paths, reservation, {
      status: "RECORDED",
      verdict: evaluationResult.answers.route.choice,
      evaluationResult,
    });
  } catch {
    return record(paths, reservation, {
      status: "BLOCKED",
      verdict: "BLOCKED",
      evaluationError: { code: "INVALID_RESPONSE", reason: "typed evaluation failed" },
    });
  }
}

function cliArguments(argv) {
  if (argv.length !== 4 || argv[0] !== "--project" || argv[2] !== "--plan") return null;
  return { projectDir: argv[1], planPath: argv[3] };
}

function cliExitCode(result) {
  if (result.status === "USER_REQUIRED" || result.status === "RESERVED") return 4;
  if (result.status !== "BLOCKED") return 0;
  return ["INVALID_INPUT", "INVALID_CONFIGURATION"].includes(result.evaluationError?.code) ? 2 : 4;
}

if (import.meta.main) {
  const options = cliArguments(process.argv.slice(2));
  if (!options) {
    process.stderr.write("usage: evaluate.mjs --project <hostRoot> --plan <planPath>\n");
    process.exitCode = 2;
  } else {
    let input;
    try {
      input = JSON.parse(readFileSync(0, "utf8"));
    } catch {
      process.stdout.write(`${JSON.stringify(blocked("INVALID_INPUT"))}\n`);
      process.exitCode = 2;
    }
    if (input !== undefined) {
      try {
        const result = await evaluateRouting(input, options);
        process.stdout.write(`${JSON.stringify(result)}\n`);
        process.exitCode = cliExitCode(result);
      } catch {
        process.stdout.write(`${JSON.stringify(blocked("ADAPTER_FAILURE"))}\n`);
        process.exitCode = 1;
      }
    }
  }
}
