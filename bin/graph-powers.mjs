#!/usr/bin/env node
/**
 * graph-powers — one-command installer.
 *
 *   bunx graph-powers        npx graph-powers
 *
 * What it does, in order: detects which harnesses are present, wires the plugin into each of
 * them, optionally writes a starting config, and verifies. Then it prints the one thing that
 * actually finishes the job — the prompt that hands AGENT_SETUP.md to the agent.
 *
 * What it deliberately does NOT do: delete a single file. Cleaning an existing `.claude/` is the
 * step that decides whether adoption works, and it is the only one that needs judgement —
 * telling a divergent copy apart from the only version of something. That lives in AGENT_SETUP.md,
 * behind human approval, not here.
 *
 * Runs unchanged under node and bun: `node:*` only, no dependencies.
 */

import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import {
  installGlobal as installCodexGlobal,
  installProject as installCodexProject,
  globallyInstalled as codexGloballyInstalled,
  uninstall as uninstallCodex,
} from "../codex/install.mjs";

const PLUGIN = "graph-powers";
const MARKETPLACE = "graph-powers";
const DEFAULT_REPO = "GrupoUS/graph-powers";
const PLUGIN_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");

// ── output ───────────────────────────────────────────────────────────────────
const color = process.stdout.isTTY && !process.env.NO_COLOR;
const paint = (code, s) => (color ? `\x1b[${code}m${s}\x1b[0m` : s);
const bold = (s) => paint("1", s);
const dim = (s) => paint("2", s);
const green = (s) => paint("32", s);
const yellow = (s) => paint("33", s);
const red = (s) => paint("31", s);

const step = (n, total, msg) => console.log(`\n${bold(`[${n}/${total}]`)} ${msg}`);
const ok = (msg) => console.log(`  ${green("✔")} ${msg}`);
const warn = (msg) => console.log(`  ${yellow("!")} ${msg}`);
const info = (msg) => console.log(`  ${dim(msg)}`);

function die(msg, hint) {
  console.error(`\n  ${red("✘")} ${msg}`);
  if (hint) console.error(`    ${dim(hint)}`);
  process.exit(1);
}

// ── arguments ────────────────────────────────────────────────────────────────
const argv = process.argv.slice(2);
const has = (...names) => names.some((n) => argv.includes(n));
const valueOf = (name, fallback) => {
  const i = argv.indexOf(name);
  return i !== -1 && argv[i + 1] && !argv[i + 1].startsWith("-") ? argv[i + 1] : fallback;
};

const AGENT_PROMPT = `Read AGENT_SETUP.md from the graph-powers plugin and execute it for this project.
Stop for my approval before each write, as the playbook instructs.`;

if (has("--agent-setup")) {
  console.log(`\n${bold("Paste this into a Claude Code or Codex session opened in your project:")}\n`);
  console.log(AGENT_PROMPT);
  console.log(`\n${dim(`The playbook itself: ${join(PLUGIN_ROOT, "AGENT_SETUP.md")}`)}\n`);
  process.exit(0);
}

if (has("-h", "--help")) {
  console.log(`
${bold("graph-powers")} — install the shared Claude Code + Codex CLI harness in this repository.

${bold("USAGE")}
  node <clone>/bin/graph-powers.mjs [options]

  On Claude Code you do not need this at all — the marketplace installs the plugin:
    /plugin marketplace add ${DEFAULT_REPO}
    /plugin install graph-powers@graph-powers
  This script is what wires Codex CLI, and what installs from a clone on either harness.

${bold("OPTIONS")}
  --target <claude|codex|both>   Which harness to wire. Default: autodetect from the CLIs present.
  --scope <user|project|local>   Where to register. Default: user — install once, serve every
                                 project on this machine, including future ones.
                                 user    = ~/.claude/settings.json (recommended)
                                 project = .claude/settings.json (versioned; use when the team
                                           must get the harness by cloning the repository)
                                 local   = .claude/settings.local.json (gitignored, just you)
  --force                        Reinstall the global half even if it is already at this version.
  --autonomy <autonomous|guarded>
                                 How much runs without asking. Default: autonomous — unrecognised
                                 commands run, cleanup runs, commit and push do not need an opt-in
                                 key. The destructive floor still holds either way. "guarded"
                                 restores a confirmation on each of those.
  --source <org/repo|path>       Where the marketplace comes from. Default: ${DEFAULT_REPO}
  --config                       Also write a starting .graph-powers/config.json, inferred from the stack.
  --prefix <NAME>                Opt-in key prefix (with --config). Default: the directory name.
  --dry-run                      Show what it would do, without doing it.
  --skip-marketplace             Skip registering the marketplace (already registered).
  --update                       Pull the latest commit into this clone and reinstall from it.
  --uninstall                    Remove the generated Codex artefacts recorded by a previous run.
  --agent-setup                  Print the prompt that hands AGENT_SETUP.md to the agent, and exit.
  -h, --help                     This help.

${bold("AFTER INSTALLING")}
  Restart the session — hooks and skills are read at startup.
  Then run the setup playbook: ${dim("node <clone>/bin/graph-powers.mjs --agent-setup")}
  Installing without cleaning the project's existing .claude/ changes nothing: precedence is
  Project > Plugin, so every local copy with the same name keeps winning.
`);
  process.exit(0);
}

// Global by default. The harness is identical in every project, so it installs once and serves
// every repository on the machine — including ones that do not exist yet. Only what genuinely
// differs per project stays local, and the guardrails read that per-project config at runtime.
const scope = valueOf("--scope", "user");
if (!["project", "user", "local"].includes(scope)) {
  die(`invalid scope: ${scope}`, "use --scope project | user | local");
}
const source = valueOf("--source", DEFAULT_REPO);
const dryRun = has("--dry-run");
const wantConfig = has("--config");
const autonomyLevel = valueOf("--autonomy", "autonomous");
if (!["autonomous", "guarded"].includes(autonomyLevel)) {
  die(`invalid autonomy level: ${autonomyLevel}`, "use --autonomy autonomous | guarded");
}
const cwd = process.cwd();

// ── harness detection ────────────────────────────────────────────────────────
function cliVersion(bin) {
  try {
    const r = spawnSync(bin, ["--version"], { encoding: "utf8", timeout: 15000 });
    return r.status === 0 ? (r.stdout ?? "").trim().split("\n")[0] : null;
  } catch {
    return null;
  }
}

const claudeVersion = cliVersion("claude");
const codexVersion = cliVersion("codex");

let target = valueOf("--target", null);
if (!target) {
  target = claudeVersion && codexVersion ? "both" : codexVersion ? "codex" : "claude";
}
if (!["claude", "codex", "both"].includes(target)) {
  die(`invalid target: ${target}`, "use --target claude | codex | both");
}
const wantClaude = target === "claude" || target === "both";
const wantCodex = target === "codex" || target === "both";

// ── is the harness already global? ───────────────────────────────────────────
/**
 * Claude Code records every installed plugin in ~/.claude/plugins/installed_plugins.json, with its
 * scope, its version and the git commit it came from. Reading that is how we avoid reinstalling
 * something that is already serving every project on this machine.
 */
function claudeGlobalInstall() {
  const home = process.env.HOME ?? "";
  const record = readJsonSafe(join(home, ".claude/plugins/installed_plugins.json"));
  const entries = record?.plugins ?? {};
  for (const [key, installs] of Object.entries(entries)) {
    if (!key.startsWith(`${PLUGIN}@`)) continue;
    const userScoped = (installs ?? []).find((i) => i.scope === "user");
    if (userScoped) return { installed: true, key, ...userScoped };
  }
  return { installed: false };
}

function readJsonSafe(p) {
  try {
    return JSON.parse(readFileSync(p, "utf8"));
  } catch {
    return null;
  }
}

// ── update ───────────────────────────────────────────────────────────────────

/**
 * `--update`: fast-forward this clone and reinstall from it.
 *
 * `--ff-only` on purpose. A merge commit created by a background update is a state nobody chose
 * and nobody will be able to explain later; a clone with local edits should refuse to update and
 * say so, not quietly rewrite itself.
 */
function gitUpdate(root) {
  const git = (...args) =>
    spawnSync("git", ["-C", root, ...args], { encoding: "utf8", timeout: 120000 });

  if (git("rev-parse", "--git-dir").status !== 0) {
    die(`${root} is not a git clone.`, "Install with: git clone https://github.com/" + DEFAULT_REPO);
  }
  const before = (git("rev-parse", "HEAD").stdout ?? "").trim();
  const pull = git("pull", "--ff-only");
  if (pull.status !== 0) {
    console.error(`${pull.stdout}${pull.stderr}`.trim());
    die("could not fast-forward the clone.",
        "Local commits or uncommitted changes? Resolve them, then run --update again.");
  }
  const after = (git("rev-parse", "HEAD").stdout ?? "").trim();
  return { changed: before !== after, before, after };
}

if (has("--update")) {
  console.log(`\n${bold("Graph Powers")} ${dim("— updating this clone")}`);
  const { changed, before, after } = gitUpdate(PLUGIN_ROOT);
  if (changed) ok(`${before.slice(0, 8)} → ${after.slice(0, 8)}`);
  else {
    ok("already at the latest commit");
    if (!has("--force")) {
      info("Nothing to reinstall. Use --force to regenerate the artefacts anyway.");
      process.exit(0);
    }
  }
  info("Reinstalling from the updated clone…");
  // Re-exec rather than continue: the files this process already loaded are the old ones.
  const again = spawnSync(process.execPath,
    [join(PLUGIN_ROOT, "bin/graph-powers.mjs"), ...argv.filter((a) => a !== "--update")],
    { stdio: "inherit" });
  process.exit(again.status ?? 0);
}

// ── uninstall ────────────────────────────────────────────────────────────────
if (has("--uninstall")) {
  console.log(`\n${bold("graph-powers")} ${dim("— removing generated Codex artefacts")}`);
  const removed = uninstallCodex({ projectDir: cwd, dryRun, log: (p) => info(p) });
  ok(`${removed.length} path(s) removed; third-party hook entries untouched`);
  info("The Claude Code plugin is removed with `claude plugin uninstall graph-powers`.");
  process.exit(0);
}

// ── commands ─────────────────────────────────────────────────────────────────
function claude(args, { capture = false } = {}) {
  if (dryRun) {
    info(`(dry-run) claude ${args.join(" ")}`);
    return { status: 0, stdout: "", stderr: "" };
  }
  const r = spawnSync("claude", args, {
    stdio: capture ? ["ignore", "pipe", "pipe"] : "inherit",
    encoding: "utf8",
    cwd,
  });
  return { status: r.status ?? 1, stdout: r.stdout ?? "", stderr: r.stderr ?? "" };
}

// ── permissions ──────────────────────────────────────────────────────────────

/**
 * The allowlist that stops the harness asking permission to do its own job.
 *
 * Every entry here is something the plugin itself runs — the gates, the guardrail tests, the
 * inspections the commands depend on. Without it, a person approves the same `git status` several
 * times an hour, which is how people learn to approve without reading. That habit is far more
 * dangerous than any command on this list.
 *
 * Writes are additive: whatever the settings file already allows stays. A permission list is
 * somebody's decision, and replacing it wholesale is how a plugin silently removes a rule.
 */
function permissionAllowlist(pm) {
  const readOnlyGit = [
    "status", "diff", "log", "show", "branch", "fetch", "remote", "reflog", "rev-parse",
    "rev-list", "ls-files", "ls-remote", "blame", "describe", "shortlog", "merge-base",
    "cat-file", "symbolic-ref", "name-rev", "check-ignore", "grep", "diff-tree",
    "count-objects", "stash list", "worktree list",
  ].map((c) => `Bash(git ${c}:*)`);

  // Every manager, not only the one this repository happens to use: the agent runs `npx`/`bunx`
  // for one-off tools regardless, and a missing entry here is a permission prompt per call.
  const managers = [pm, "bun", "bunx", "npm", "npx", "pnpm", "pnpx", "yarn", "uv", "uvx", "pip", "pipx"]
    .filter(Boolean);

  return [
    ...readOnlyGit,
    "Bash(git add:*)",
    "Bash(git config --get:*)",
    ...[...new Set(managers)].map((m) => `Bash(${m}:*)`),
    "Bash(python3:*)", "Bash(python:*)", "Bash(node:*)", "Bash(deno:*)",
    "Bash(make:*)", "Bash(just:*)", "Bash(cargo:*)", "Bash(go:*)",
    "Bash(mkdir:*)", "Bash(cp:*)", "Bash(mv:*)", "Bash(touch:*)", "Bash(diff:*)",
    "Bash(test:*)", "Bash(which:*)", "Bash(env:*)", "Bash(printf:*)", "Bash(echo:*)",
    "Bash(awk:*)", "Bash(sort:*)", "Bash(uniq:*)", "Bash(cut:*)", "Bash(tr:*)", "Bash(du:*)",
    "Bash(ls:*)", "Bash(cat:*)", "Bash(head:*)", "Bash(tail:*)", "Bash(wc:*)",
    "Bash(find:*)", "Bash(grep:*)", "Bash(rg:*)", "Bash(jq:*)", "Bash(sed -n:*)",
    "Bash(gh pr view:*)", "Bash(gh pr list:*)", "Bash(gh pr diff:*)", "Bash(gh pr checks:*)",
    "Bash(gh issue view:*)", "Bash(gh issue list:*)", "Bash(gh api:*)",
    "Read", "Glob", "Grep", "Edit", "Write", "TodoWrite", "Skill",
  ];
}

function settingsPathFor(theScope) {
  if (theScope === "user") return join(process.env.HOME ?? cwd, ".claude/settings.json");
  if (theScope === "local") return join(cwd, ".claude/settings.local.json");
  return join(cwd, ".claude/settings.json");
}

function writePermissions(theScope) {
  const target = settingsPathFor(theScope);
  const current = readJsonSafe(target) ?? {};
  const existing = current.permissions?.allow ?? [];
  const wanted = permissionAllowlist(detectStack().pm);
  const added = wanted.filter((rule) => !existing.includes(rule));

  if (!added.length) {
    info(`permissions already cover the harness (${existing.length} rules) — nothing added`);
    return;
  }
  const next = {
    ...current,
    permissions: { ...(current.permissions ?? {}), allow: [...existing, ...added] },
  };
  if (dryRun) {
    info(`(dry-run) would add ${added.length} allow rules to ${target.replace(process.env.HOME ?? "~", "~")}`);
    return;
  }
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, `${JSON.stringify(next, null, 2)}\n`, "utf8");
  ok(`${added.length} permission rules added (${existing.length} already there, none removed)`);
  info(target.replace(process.env.HOME ?? "~", "~"));
}

// ── stack detection, for --config ────────────────────────────────────────────
function readJson(p) {
  try {
    return JSON.parse(readFileSync(p, "utf8"));
  } catch {
    return null;
  }
}

function detectStack() {
  const pkg = readJson(join(cwd, "package.json")) ?? {};
  const deps = { ...(pkg.dependencies ?? {}), ...(pkg.devDependencies ?? {}) };
  const hasFile = (...names) => names.some((n) => existsSync(join(cwd, n)));
  const parts = [];

  if (hasFile("astro.config.mjs", "astro.config.ts", "astro.config.js") || deps.astro) parts.push("astro");
  if (hasFile("next.config.js", "next.config.mjs", "next.config.ts") || deps.next) parts.push("next");
  if (hasFile("nuxt.config.ts") || deps.nuxt) parts.push("nuxt");
  if (hasFile("svelte.config.js") || deps.svelte) parts.push("svelte");
  if (hasFile("vite.config.ts", "vite.config.js") || deps.vite) parts.push("vite");
  if (hasFile("turbo.json", "pnpm-workspace.yaml") || pkg.workspaces) parts.push("monorepo");
  if (hasFile("drizzle.config.ts", "drizzle.config.js") || deps["drizzle-orm"]) parts.push("drizzle");
  if (hasFile("prisma/schema.prisma") || deps.prisma) parts.push("prisma");
  if (deps.react) parts.push("react");
  if (deps.vue) parts.push("vue");
  if (deps.tailwindcss) parts.push("tailwind");
  if (hasFile("pyproject.toml", "requirements.txt")) parts.push("python");
  if (hasFile("go.mod")) parts.push("go");
  if (hasFile("Cargo.toml")) parts.push("rust");

  // Package manager from the lockfile present — not from the habit of whoever installs.
  const pm = hasFile("bun.lockb", "bun.lock") ? "bun"
    : hasFile("pnpm-lock.yaml") ? "pnpm"
    : hasFile("yarn.lock") ? "yarn"
    : hasFile("package-lock.json") ? "npm"
    : hasFile("uv.lock") ? "uv"
    : null;

  // Only commands that genuinely exist in the scripts get in. A gate pointing at a script that
  // is not there dies as "script not found", and the report line reads as covered.
  const scripts = pkg.scripts ?? {};
  const commands = {};
  const pick = (key, ...candidates) => {
    const found = candidates.find((c) => scripts[c]);
    if (found && pm) commands[key] = `${pm} run ${found}`;
  };
  pick("typeCheck", "type-check", "typecheck", "check", "tsc");
  pick("lint", "lint:check", "lint");
  pick("format", "format", "fmt");
  pick("test", "test");
  pick("build", "build");

  return { stack: parts.join("-") || "unknown", pm, commands, hasTests: Boolean(scripts.test) };
}

/**
 * The Codex model and reasoning effort, from this project's config.
 *
 * Never a default written here. A model name in the installer is a file that ages out the week
 * the next model ships, and every machine that installed before then keeps generating the old one.
 */
function codexSettings() {
  const cfg = readJson(join(cwd, ".graph-powers/config.json"))
    ?? readJson(join(cwd, ".claude/config.json"))
    ?? {};
  const codex = cfg.codex ?? {};
  return {
    ...(typeof codex.model === "string" && codex.model ? { model: codex.model } : {}),
    ...(typeof codex.reasoningEffort === "string" && codex.reasoningEffort
      ? { reasoningEffort: codex.reasoningEffort }
      : {}),
  };
}

function currentBranch() {
  const r = spawnSync("git", ["branch", "--show-current"], { encoding: "utf8", cwd });
  return (r.stdout ?? "").trim() || null;
}

function writeConfig() {
  const target = join(cwd, ".graph-powers", "config.json");
  if (existsSync(target) || existsSync(join(cwd, ".claude", "config.json"))) {
    warn("a config already exists — it was not overwritten.");
    info("Compare it against examples/ and adjust by hand, or delete it and re-run with --config.");
    return;
  }
  const d = detectStack();
  const prefix = valueOf("--prefix", cwd.split(/[\\/]/).filter(Boolean).pop() ?? "GRAPHPOWERS")
    .toUpperCase()
    .replace(/[^A-Z0-9_]/g, "_");
  const branch = currentBranch();

  const cfg = {
    $schema: `https://raw.githubusercontent.com/${DEFAULT_REPO}/main/schema/config.schema.json`,
    project: { name: cwd.split(/[\\/]/).filter(Boolean).pop(), stack: d.stack },
    git: {
      workBranch: branch && branch !== "main" && branch !== "master" ? branch : "dev-test",
      protectedBranches: ["main", "master"],
      optInPrefix: prefix,
    },
    tooling: {
      ...(d.pm ? { packageManager: d.pm } : {}),
      testRunner: d.hasTests ? "detect" : null,
      ...(Object.keys(d.commands).length ? { commands: d.commands } : {}),
    },
    paths: existsSync(join(cwd, "src")) ? { frontendRoot: "src" } : {},
    // Written explicitly rather than left to the schema default, so the file says what it does
    // instead of leaving a stranger to look it up.
    autonomy: {
      level: autonomyLevel,
      destructiveFloor: true,
    },
  };

  if (dryRun) {
    info("(dry-run) would write .graph-powers/config.json:");
    console.log(dim(JSON.stringify(cfg, null, 2).split("\n").map((l) => `      ${l}`).join("\n")));
    return;
  }
  mkdirSync(join(cwd, ".graph-powers"), { recursive: true });
  writeFileSync(target, `${JSON.stringify(cfg, null, 2)}\n`, "utf8");
  ok(`.graph-powers/config.json created (stack: ${d.stack}, prefix: ${prefix})`);
  warn("Review it before trusting it: detection is a starting point, not a verdict.");
  info(`In particular: workBranch=${cfg.git.workBranch}, testRunner=${JSON.stringify(cfg.tooling.testRunner)}`);
}

// ── steps ────────────────────────────────────────────────────────────────────
const steps = [];
if (wantClaude) steps.push("marketplace", "plugin", "permissions");
if (wantCodex) steps.push("codex");
if (wantConfig) steps.push("config");
steps.push("verify");
const TOTAL = steps.length + 1;
let n = 0;

console.log(`\n${bold("Graph Powers")} ${dim("— shared harness for Claude Code and Codex CLI")}`);
if (dryRun) console.log(yellow("  dry-run: nothing will be changed"));

// Installing the harness into its own repository is always an accident, and a quiet one: it adds
// a `.codex/rules/` and a block in the AGENTS.md that *is* the source of those templates, and the
// next commit ships them. It happened here, once, from a `--update` that re-ran the installer in
// the clone's own directory.
if (resolve(cwd) === PLUGIN_ROOT && !has("--force")) {
  die("this is the plugin's own repository — installing it into itself writes the artefacts it generates.",
      "Run it from the project you want to wire, or pass --force if you really mean it.");
}

step(++n, TOTAL, "Checking the environment");
{
  if (claudeVersion) ok(`claude ${claudeVersion}`);
  else info("claude not found");
  if (codexVersion) ok(`codex ${codexVersion}`);
  else info("codex not found");
  if (!claudeVersion && !codexVersion) {
    die(
      "neither `claude` nor `codex` was found on PATH.",
      "Install Claude Code (https://claude.com/claude-code) or Codex CLI first.",
    );
  }
  if (wantClaude && !claudeVersion) {
    die("--target includes claude, but the `claude` CLI is not on PATH.", "Use --target codex, or install Claude Code.");
  }
  if (wantCodex && !codexVersion) {
    warn("codex is not on PATH — the artefacts will still be written, but nothing will read them yet.");
  }

  // 3.10 is the real floor: several hooks use `X | None` in annotations evaluated at import time.
  // `engines` cannot express a Python requirement, so this is the only place it gets checked.
  const py = spawnSync("python3", ["--version"], { encoding: "utf8" });
  if (py.status === 0) {
    const version = (py.stdout || py.stderr).trim();
    const [, major, minor] = /(\d+)\.(\d+)/.exec(version) ?? [];
    if (Number(major) > 3 || (Number(major) === 3 && Number(minor) >= 10)) {
      ok(version);
    } else {
      warn(`${version} — the guardrails need Python 3.10 or newer; they will fail open and never run.`);
    }
  } else {
    warn("python3 not found — the guardrails are Python stdlib and will not run without it.");
  }

  info(`target: ${target}`);
}

if (wantClaude) {
  const already = scope === "user" ? claudeGlobalInstall() : { installed: false };
  const localVersion = readJsonSafe(join(PLUGIN_ROOT, ".claude-plugin/plugin.json"))?.version;

  step(++n, TOTAL, `Registering the marketplace ${dim(`(${source})`)}`);
  if (has("--skip-marketplace")) {
    info("skipped by --skip-marketplace");
  } else {
    const src = existsSync(resolve(source)) ? resolve(source) : source;
    const r = claude(["plugin", "marketplace", "add", src], { capture: true });
    const out = `${r.stdout}${r.stderr}`;
    if (r.status === 0) ok(`marketplace ${MARKETPLACE} registered`);
    else if (/already/i.test(out)) info("marketplace was already registered");
    else {
      console.error(out.trim());
      die("failed to register the marketplace.", "Check that the repository is reachable and the path is right.");
    }
  }

  step(++n, TOTAL, `Installing the plugin ${dim(`(scope: ${scope})`)}`);
  if (already.installed && already.version === localVersion && !has("--force")) {
    ok(`already installed globally at ${already.version} — nothing to do`);
    info(`installed ${already.installedAt ?? "earlier"} from commit ${(already.gitCommitSha ?? "?").slice(0, 8)}`);
    info("It already serves every project on this machine, including ones that do not exist yet.");
  } else if (already.installed && already.version !== localVersion) {
    info(`global install is at ${already.version}, this source is ${localVersion} — updating`);
    // The qualified `<plugin>@<marketplace>` form: the bare name is "not found". The command also
    // exits 0 when it fails, so its output is what gets read, not its status.
    const r = claude(["plugin", "update", `${PLUGIN}@${MARKETPLACE}`, "--scope", "user", "-y"],
                     { capture: true });
    const out = `${r.stdout}${r.stderr}`;
    if (r.status === 0 && !/not found|failed/i.test(out)) {
      ok(`${PLUGIN} updated to ${localVersion} · restart the session to apply`);
    } else {
      console.error(out.trim());
      warn(`update failed — the existing install still works; try \`claude plugin update ${PLUGIN}@${MARKETPLACE}\`.`);
    }
  } else {
    const r = claude(["plugin", "install", `${PLUGIN}@${MARKETPLACE}`, "--scope", scope, "-y"], { capture: true });
    const out = `${r.stdout}${r.stderr}`;
    if (r.status === 0) ok(`${PLUGIN} installed at ${scope} scope`);
    else if (/already installed/i.test(out)) info("already installed in this scope");
    else {
      console.error(out.trim());
      die("failed to install the plugin.");
    }
  }
}

if (wantClaude) {
  step(++n, TOTAL, `Permissions ${dim(`(${autonomyLevel})`)}`);
  writePermissions(scope);
  if (autonomyLevel === "autonomous") {
    info("autonomy: autonomous — unrecognised commands run, cleanup runs, commit and push need no key.");
    info("Still refused, at any level: rm -rf on / or $HOME, mkfs, dd to a device, DROP DATABASE,");
    info("force-pushing a protected branch. Those are what git cannot give back.");
  } else {
    info("autonomy: guarded — an unrecognised command asks, and git actions need an opt-in key.");
  }
}

if (wantCodex) {
  step(++n, TOTAL, "Wiring Codex");
  try {
    if (scope === "user") {
      // The global half: skills, subagents, commands, guardrails and the shared references —
      // everything that is identical in every project, installed once for the machine.
      const g = installCodexGlobal({
        pluginRoot: PLUGIN_ROOT,
        dryRun,
        force: has("--force"),
        codex: codexSettings(),
        log: (p) => info(String(p).replace(process.env.HOME ?? "~", "~")),
      });
      if (g.skipped) ok(`global harness already at ${g.version} — skipped`);
      else ok(`${g.written.length} global path(s) written · hooks merged, never overwritten`);

      // The project half: only what cannot be anything but local.
      const proj = installCodexProject({
        projectDir: cwd,
        pluginRoot: PLUGIN_ROOT,
        dryRun,
        log: (p) => info(String(p).replace(`${cwd}/`, "")),
      });
      ok(`${proj.length} project path(s) written · rules and instructions only`);
      info("Skills, subagents and guardrails stay global; rules, config and the three authorities");
      info("stay in this repository. One copy of the harness, one config per project.");
    } else {
      const { install: installCodexAll } = await import("../codex/install.mjs");
      const written = installCodexAll({
        projectDir: cwd,
        pluginRoot: PLUGIN_ROOT,
        scope: "project",
        dryRun,
        codex: codexSettings(),
        log: (p) => info(String(p).replace(`${cwd}/`, "")),
      });
      ok(`${written.length} path(s) written into this project`);
      warn("Project scope keeps a full copy of the harness here. Prefer --scope user unless the");
      warn("team must get it by cloning the repository.");
    }
  } catch (e) {
    die(`failed to wire Codex: ${e.message}`);
  }
}

if (wantConfig) {
  step(++n, TOTAL, "Writing .graph-powers/config.json");
  writeConfig();
}

step(++n, TOTAL, "Verifying");
{
  if (wantClaude) {
    const r = claude(["plugin", "list"], { capture: true });
    if (!dryRun && !`${r.stdout}${r.stderr}`.includes(PLUGIN)) {
      warn("the plugin did not show up in `claude plugin list` — check manually.");
    } else {
      ok("plugin registered");
    }
  }
  if (wantCodex && !dryRun) {
    // Which manifest to read depends on the scope, and reading the wrong one is not a cosmetic
    // slip: the global install records its hooks in the Codex home, so looking in the project
    // always found nothing and always warned — on a run that had just succeeded.
    const manifest = scope === "user"
      ? readJson(join(process.env.HOME ?? cwd, ".codex", "graph-powers-installed.json"))
      : readJson(join(cwd, ".graph-powers", "installed.json"));
    if (manifest?.hookCommands?.length) {
      ok(`${manifest.hookCommands.length} Codex hook entries recorded`);
      if (manifest.complete === false) warn("the manifest says the install did not finish — re-run it.");
    } else if (manifest) {
      ok("Codex manifest written");
    } else {
      warn("no Codex manifest was written — check the output above.");
    }
    info("Codex asks you to approve hooks once: open a session and run /hooks, or they stay inert.");
  }
}

console.log(`
${bold("Done.")} Two steps the installer does not do for you:

  ${bold("1.")} ${bold("Restart the session.")}
     Hooks and skills are read at startup; until then none of this is live.

  ${bold("2.")} ${bold("Run the setup playbook.")} Paste this into a session opened in this project:

${AGENT_PROMPT.split("\n").map((l) => `       ${dim(l)}`).join("\n")}

     It installs the required external plugins, writes or improves your config, rules and
     instructions, and — the step that decides whether any of this changes anything — cleans the
     local copies that currently shadow the plugin. It stops for your approval before every write.

Updating later: ${dim(`node ${join(PLUGIN_ROOT, "bin/graph-powers.mjs")} --update`)}
${dim("  (the harness also checks for itself at session start — see autoUpdate in the README)")}

Docs: ${dim(`https://github.com/${DEFAULT_REPO}#readme`)}
`);
