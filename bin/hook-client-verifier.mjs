import { spawnSync } from "node:child_process";
import { join } from "node:path";

export function verifierPath(pluginRoot) {
  return join(pluginRoot, "bin/verify-hook-clients.py");
}

function pythonCandidates(platform = process.platform) {
  return platform === "win32"
    ? [["python", []], ["py", ["-3"]]]
    : [["python3", []], ["python", []]];
}

function pythonInvocation({ cwd, env, args }) {
  const candidates = pythonCandidates();
  for (const [command, prefix] of candidates) {
    const probe = spawnSync(command, [
      ...prefix,
      "-c",
      "import sys; raise SystemExit(sys.version_info[0] != 3)",
    ], {
      cwd,
      env,
      stdio: "ignore",
      timeout: 5000,
      windowsHide: true,
    });
    if (!probe.error && probe.status === 0) {
      return { command, args: [...prefix, ...args] };
    }
  }
  const [command, prefix] = candidates[0];
  return { command, args: [...prefix, ...args] };
}

export function verifyHookClient({
  client,
  pluginRoot,
  projectDir = process.cwd(),
  scope = "user",
  autonomy = "guarded",
  packageRoot = null,
  expectedVersion = null,
  checkPosture = false,
  probe = true,
  env = process.env,
} = {}) {
  const path = verifierPath(pluginRoot);
  const args = [
    "-X",
    "utf8",
    path,
    "--client",
    client,
    "--plugin-root",
    pluginRoot,
    "--project-dir",
    projectDir,
    "--scope",
    scope,
    "--autonomy",
    autonomy,
    "--json",
  ];
  if (packageRoot) args.push("--package-root", packageRoot);
  if (expectedVersion) args.push("--expected-version", expectedVersion);
  if (checkPosture) args.push("--check-posture");
  if (probe) args.push("--probe-guardrail");
  const invocation = pythonInvocation({ cwd: projectDir, env, args });
  const run = spawnSync(invocation.command, invocation.args, {
    cwd: projectDir,
    encoding: "utf8",
    timeout: 60000,
    env,
  });
  let body;
  try {
    body = JSON.parse(run.stdout ?? "");
  } catch {
    body = {
      ok: false,
      errors: [
        `hook verifier emitted invalid JSON: ${`${run.stdout ?? ""}${run.stderr ?? ""}`.trim()}`,
      ],
    };
  }
  return {
    ok: run.status === 0 && body?.ok === true,
    status: run.status ?? 1,
    body,
    stderr: run.stderr ?? "",
    path,
  };
}

export function proofFailure(proof) {
  return [...(proof?.body?.errors ?? []), String(proof?.stderr ?? "").trim()]
    .filter(Boolean)
    .join("; ");
}
