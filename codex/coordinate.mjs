#!/usr/bin/env bun
/** Parent-side bridge: Jev decisions, native handoffs, fresh proof and persistent SDD state. */
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, readFileSync, realpathSync, readdirSync, statSync } from "node:fs";
import { dirname, isAbsolute, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { isDeepStrictEqual } from "node:util";
import { evaluateRouting, routingCatalog, routingSettings } from "./evaluate.mjs";

const PLUGIN = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const SDD = fileURLToPath(new URL("../skills/planning/scripts/sdd.py", import.meta.url));
const hash = (value) => createHash("sha256").update(value).digest("hex");
// Keep Jev's choice narrow; widen this shortlist only if real routing cases need it.
const MAX_SHORTLIST = 8;
const MIN_ROUTE_CONFIDENCE = 0.7;
const actor = (input) => ({ requesterRole: input.requesterRole, depth: input.depth });
const blocked = (reason) => ({ status: "BLOCKED", reason, executionAuthorized: false });

function ledger(action, input, { projectDir, sessionId }) {
  const windows = process.platform === "win32";
  const result = spawnSync(
    windows ? "py" : "python3",
    [
      ...(windows ? ["-3"] : []),
      "-B",
      "-X",
      "utf8",
      SDD,
      "coordinate",
      action,
      "--project",
      projectDir,
      "--session",
      sessionId,
      "--request-json",
      JSON.stringify(input),
    ],
    { cwd: projectDir, encoding: "utf8", timeout: 15000 },
  );
  if (![0, 4].includes(result.status)) throw new Error("COORDINATION_REJECTED");
  return JSON.parse(result.stdout);
}

function hostPath(root, name) {
  if (typeof name !== "string" || isAbsolute(name)) throw new Error("INVALID_ARTIFACT");
  const path = resolve(root, name),
    rel = relative(root, path);
  if (!rel || rel === ".." || rel.startsWith(`..${sep}`)) throw new Error("INVALID_ARTIFACT");
  let existing = path;
  while (!existsSync(existing)) existing = dirname(existing);
  const actual = relative(root, realpathSync(existing));
  if (actual === ".." || actual.startsWith(`..${sep}`) || isAbsolute(actual))
    throw new Error("INVALID_ARTIFACT");
  return path;
}

function dirty(root) {
  const result = spawnSync("git", ["status", "--porcelain=v1", "-z", "--untracked-files=all"], {
    cwd: root,
    encoding: "utf8",
  });
  if (result.status !== 0) throw new Error("GIT_STATE_UNAVAILABLE");
  const names = [],
    parts = result.stdout.split("\0");
  for (let i = 0; i < parts.length; i++) {
    if (!parts[i]) continue;
    names.push(parts[i].slice(3));
    if (/[RC]/.test(parts[i].slice(0, 2)) && parts[i + 1]) names.push(parts[++i]);
  }
  return Object.fromEntries(
    [...new Set(names)]
      .sort()
      .filter((name) => !name.startsWith(".graph-powers/logs/"))
      .map((name) => {
        const path = hostPath(root, name);
        return [
          name,
          existsSync(path) && statSync(path).isFile() ? hash(readFileSync(path)) : "MISSING",
        ];
      }),
  );
}

function snapshot(root, paths) {
  const files = { ...dirty(root) };
  const visited = new Set();
  function visit(name) {
    const path = hostPath(root, name);
    if (!existsSync(path)) {
      files[name] = "MISSING";
      return;
    }
    if (statSync(path).isDirectory()) {
      const actual = realpathSync(path);
      if (visited.has(actual)) return;
      visited.add(actual);
      for (const entry of readdirSync(path)) visit(`${name}/${entry}`);
    } else files[name] = hash(readFileSync(path));
    if (Object.keys(files).length > 4096) throw new Error("SNAPSHOT_LIMIT");
  }
  for (const path of paths) visit(path);
  return hash(JSON.stringify(Object.entries(files).sort(([a], [b]) => a.localeCompare(b))));
}

function proof(state, handoff, options) {
  const root = options.projectDir,
    context = state.context;
  if (
    !handoff ||
    !Array.isArray(handoff.artifacts) ||
    !Array.isArray(handoff.qualityGates) ||
    !Array.isArray(handoff.decisions) ||
    !Array.isArray(handoff.risks) ||
    typeof handoff.resumeHint !== "string" ||
    typeof handoff.nextAgent !== "string" ||
    !Number.isInteger(handoff.confidence) ||
    !["COMPLETED", "BLOCKED", "REVISION_REQUIRED"].includes(handoff.status)
  )
    throw new Error("INVALID_HANDOFF");
  const checks = context.checks.map((check) => {
    const result = spawnSync(check.argv[0], check.argv.slice(1), {
      cwd: root,
      encoding: "utf8",
      timeout: 60000,
      maxBuffer: 1024 * 1024,
    });
    return { name: check.name, exitCode: result.status ?? -1 };
  });
  const artifacts = handoff.artifacts
    .filter((item) => !String(item.path).startsWith("https://"))
    .map((item) => {
      const path = hostPath(root, item.path);
      if (!existsSync(path) && ["removed", "deleted"].includes(item.action))
        return { path: item.path, sha256: "MISSING" };
      return { path: item.path, sha256: hash(readFileSync(path)) };
    });
  const before = context.baseline ?? {},
    after = dirty(root);
  const outside = [...new Set([...Object.keys(before), ...Object.keys(after)])].some(
    (name) =>
      before[name] !== after[name] &&
      !context.owns.some((owner) => name === owner || name.startsWith(`${owner}/`)),
  );
  return {
    passed:
      handoff.status === "COMPLETED" && !outside && checks.every((check) => check.exitCode === 0),
    checks,
    artifacts,
    snapshot: snapshot(root, [...context.owns, ...artifacts.map((item) => item.path)]),
  };
}

function feedback(state, env = process.env) {
  const receipt = state.handoffs.at(-1);
  if (!receipt) return null;
  const handoff = receipt.handoff;
  const redact = (value) => {
    let result = String(value).replace(/(?:vck_|sk-|gh[pousr]_)[A-Za-z0-9_-]{16,}/g, "[REDACTED]");
    for (const [key, secret] of Object.entries(env)) {
      if (
        /KEY|TOKEN|SECRET|PASSWORD/i.test(key) &&
        typeof secret === "string" &&
        secret.length >= 8
      )
        result = result.split(secret).join("[REDACTED]");
    }
    return result.slice(0, 800);
  };
  return {
    status: handoff.status,
    passed: receipt.verification.passed,
    checks: receipt.verification.checks,
    decisions: handoff.decisions
      .slice(0, 8)
      .map((item) => ({ what: redact(item.what), why: redact(item.why) })),
    risks: handoff.risks
      .slice(0, 8)
      .map((item) => ({ desc: redact(item.desc), mitigation: redact(item.mitigation) })),
    resumeHint: redact(handoff.resumeHint),
  };
}

function prepare(state, root, env, client) {
  const candidate = state.action.candidate;
  const methods = (candidate.skills ?? []).map((name) => ({
    name,
    path: `skills/${name}/SKILL.md`,
  }));
  if (candidate.command)
    methods.unshift({ name: candidate.command, path: `commands/${candidate.command}.md` });
  if (candidate.role !== "main")
    methods.unshift({ name: candidate.role, path: `agents/${candidate.role}.md` });
  for (const method of methods) {
    method.content = readFileSync(resolve(PLUGIN, method.path), "utf8");
    method.sha256 = hash(method.content);
  }
  const context = state.context;
  const prompt = [
    "## TASK",
    context.request,
    "## EXPECTED OUTCOME",
    "Return the requested result with reproducible artifacts and gate evidence.",
    "## MANDATORY CONTEXT",
    `Original request: ${context.request}\nUser decisions: only the supplied scope is authorized.\nPrior findings: ${JSON.stringify(feedback(state, env))}\nCurrent plan state: coordination ticket ${state.action.ticket}.\nDo NOT redo: previous recorded work.`,
    "## REQUIRED SKILLS & TOOLS",
    `Project: ${root}. Read applicable AGENTS.md/config/rules. The selected canonical methods are loaded below:\n${methods.map((method) => `### ${method.path}\n${method.content}`).join("\n")}`,
    "## MUST DO",
    `Owns: ${JSON.stringify(context.owns)}. Approved checks: ${JSON.stringify(context.checks)}. Preserve other workers' edits. For browser work use an authorized target and focused smoke first; return screenshot/console/network evidence or BLOCKED.`,
    "## MUST NOT DO",
    "Do not spawn children, expand scope, publish, expose credentials, or treat a Jev decision as permission. A command/skill action belongs to the main agent; follow its existing workflow and approval gates.",
    "## RETURN FORMAT",
    "Canonical Context Handoff JSON: status, confidence, artifacts, qualityGates, decisions, risks, nextAgent, resumeHint. Return to main with this ticket; main independently checks the result.",
  ].join("\n\n");
  return {
    executor: candidate.role === "main" ? "main" : "agent",
    role: candidate.role,
    methods,
    prompt,
    ...(client === "claude" && {
      nativeRoute: candidate.role === "main"
        ? { tool: "Skill", skill: `graph-powers:${candidate.command ?? candidate.skills[0]}` }
        : { tool: "Agent", subagent_type: `graph-powers:${candidate.role}` },
    }),
  };
}

/** Each event is explicit; native dispatch stays with the parent, never inside Jev. */
export async function coordinate(action, input, options = {}) {
  try {
    if (!input || !["parent", "controller"].includes(input.requesterRole) || input.depth !== 0)
      return blocked("PARENT_REQUIRED");
    const client = options.client ?? "codex";
    if (client !== "codex" && client !== "claude") return blocked("INVALID_CLIENT");
    const projectDir = realpathSync(options.projectDir);
    options = { ...options, projectDir, client };
    const catalog = routingCatalog(routingSettings(projectDir, client), client);
    if (action === "catalog") return { status: "CATALOG", actions: catalog };
    if (action === "init") {
      let existing;
      try {
        existing = ledger("status", actor(input), options);
      } catch {
        /* first init */
      }
      return ledger(
        "init",
        {
          ...input,
          baseline: existing?.context.baseline ?? dirty(projectDir),
          ...(existing?.context.planPath ? { planPath: existing.context.planPath } : {}),
        },
        options,
      );
    }
    const state = ledger("status", actor(input), options);
    if (action === "status") return state;
    if (action === "link-plan") return ledger("link-plan", input, options);
    if (action === "return") {
      if (
        state.status === "RETURNED" &&
        state.action.ticket === input.ticket &&
        isDeepStrictEqual(state.handoffs.at(-1).handoff, input.handoff)
      )
        return state;
      if (state.status !== "PENDING" || state.action.ticket !== input.ticket)
        return blocked("WRONG_TICKET");
      return ledger(
        "return",
        {
          ...actor(input),
          ticket: input.ticket,
          handoff: input.handoff,
          verification: proof(state, input.handoff, options),
        },
        options,
      );
    }
    if (action === "finish") {
      if (state.status === "COMPLETED") return state;
      const receipt = state.handoffs.at(-1);
      if (
        state.status !== "RETURNED" ||
        !receipt ||
        receipt.handoff.status !== "COMPLETED" ||
        !receipt.verification.passed
      )
        return blocked("FINISH_NOT_READY");
      const currentSnapshot = snapshot(projectDir, [
        ...state.context.owns,
        ...receipt.verification.artifacts.map((item) => item.path),
      ]);
      if (currentSnapshot !== receipt.verification.snapshot)
        return blocked("STALE_PROOF");
      const output = ledger("finish", actor(input), options);
      return output.status === "COMPLETED" ? output : blocked("FINISH_NOT_READY");
    }
    if (action !== "next") return blocked("INVALID_ACTION");
    if (["PENDING", "COMPLETED"].includes(state.status)) return state;
    const receipt = state.handoffs.at(-1);
    const allowed = input.allowed;
    if (!Array.isArray(allowed) || !allowed.length || allowed.length > MAX_SHORTLIST)
      return blocked("BOUNDED_ACTION_SET_REQUIRED");
    if (
      new Set(allowed).size !== allowed.length ||
      allowed.some((id) => !catalog.some((item) => item.id === id))
    )
      return blocked("INVALID_ACTION_SET");
    if (allowed.length === 1)
      return { status: "SKIPPED", reason: "NO_MATERIAL_DOUBT", executionAuthorized: false };
    const currentSnapshot = snapshot(projectDir, [
      ...state.context.owns,
      ...(receipt?.verification.artifacts ?? []).map((item) => item.path),
    ]);
    const candidates = catalog
      .filter((entry) => allowed.includes(entry.id))
      .map((entry) => {
        const candidate = {
          id: entry.id,
          kind: entry.kind,
          role: entry.role,
          skills: entry.skills,
          command: entry.command,
        };
        if (entry.kind === "agent") {
          const capability = input.capabilities?.find(
            (item) =>
              item.model === entry.model &&
              item.reasoningEffort === entry.reasoningEffort &&
              item.status === "SUPPORTED",
          );
          if (!capability) throw new Error("CAPABILITY_REQUIRED");
          candidate.capability = capability;
        }
        return candidate;
      });
    const keyState = client === "codex"
      ? { currentSnapshot, candidates }
      : { client, currentSnapshot, candidates };
    const decisionKey = `route-${state.sequence + 1}-${hash(JSON.stringify(keyState)).slice(0, 16)}`;
    const selected = await evaluateRouting(
      {
        ...actor(input),
        materialDoubt: true,
        taskId: state.context.taskId,
        decisionKey,
        candidates,
        question:
          "Choose the next eligible agent, skill or command for the request.",
        evidence: ["Canonical routing catalog and parent-verified results"],
        risk: "Wrong method or unsupported completion",
        state: {
          request: state.context.request,
          snapshot: currentSnapshot,
          previous: state.action?.candidate ?? null,
          verification: feedback(state, options.env),
          planComplete: state.planComplete,
        },
      },
      { projectDir, planPath: state.contextPath, client, fetchImpl: options.fetchImpl, env: options.env },
    );
    if (selected.status !== "RECORDED") return { ...selected, executionAuthorized: false };
    if (selected.evaluationResult.answers.route.probabilities[selected.verdict] < MIN_ROUTE_CONFIDENCE)
      return { status: "SKIPPED", reason: "LOW_CONFIDENCE", executionAuthorized: false };
    if (
      snapshot(projectDir, [
        ...state.context.owns,
        ...(receipt?.verification.artifacts ?? []).map((item) => item.path),
      ]) !== currentSnapshot
    )
      return blocked("STALE_DECISION");
    const output = ledger(
      "select",
      { ...actor(input), decisionKey, snapshot: currentSnapshot },
      options,
    );
    if (output.executionAuthorized) output.handoff = prepare(output, projectDir, options.env, client);
    return output;
  } catch (error) {
    return blocked(
      ["CAPABILITY_REQUIRED", "INVALID_ARTIFACT", "WRONG_TICKET", "SNAPSHOT_LIMIT"].includes(
        error.message,
      )
        ? error.message
        : "COORDINATION_REJECTED",
    );
  }
}

if (import.meta.main) {
  const argv = process.argv.slice(2);
  const [action, flag, projectDir, sessionFlag, sessionId, clientFlag, client] = argv;
  if (
    flag !== "--project" || sessionFlag !== "--session" || !sessionId ||
    (argv.length !== 5 &&
      (argv.length !== 7 || clientFlag !== "--client" || !["codex", "claude"].includes(client)))
  ) {
    process.stderr.write(
      "usage: coordinate.mjs catalog|init|link-plan|next|return|finish|status --project ROOT --session ID [--client codex|claude] (JSON stdin)\n",
    );
    process.exitCode = 2;
  } else {
    try {
      const result = await coordinate(action, JSON.parse(readFileSync(0, "utf8")), {
        projectDir,
        sessionId,
        client: client ?? "codex",
      });
      process.stdout.write(`${JSON.stringify(result)}\n`);
      process.exitCode =
        result.status === "BLOCKED" ||
        result.status === "USER_REQUIRED" ||
        (result.status === "PENDING" && !result.executionAuthorized)
          ? 4
          : 0;
    } catch {
      process.stdout.write(`${JSON.stringify(blocked("INVALID_INPUT"))}\n`);
      process.exitCode = 2;
    }
  }
}
