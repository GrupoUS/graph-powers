#!/usr/bin/env node
/**
 * Generate the Kilo side of Graph Powers from the Claude Code artefacts.
 *
 *   node kilo/install.mjs [--scope user|project] [--project <dir>] [--dry-run] [--json]
 *                         [--uninstall] [--force]
 *
 * Cardinal 7 still holds: nothing here is a second list. `agents/`, `commands/`, `skills/` and
 * `references/` stay canonical; this file translates their wiring into the shape Kilo loads.
 *
 * Where Kilo reads, proven against 7.6.2:
 *
 *   ~/.kilo/agent/<name>.md        agents          (`kilo agent list`)
 *   ~/.kilo/command/<name>.md      commands        (`kilo debug config` -> command)
 *   ~/.kilo/skills/<name>/SKILL.md skills          (`kilo debug skill`)
 *   ~/.kilo/plugin/*.ts            plugins         (`kilo debug config` -> plugin)
 *   ~/.config/kilo/kilo.jsonc      config          (shadowed by ~/.kilo/kilo.jsonc when present)
 *
 * `~/.config/kilo/` holds the config *file* and the type packages, not the artefacts. Installing
 * agents there produced a directory Kilo never reads and an install that reported success.
 *
 * What this deliberately does NOT do: fake a lifecycle Kilo does not have. There is no Stop event
 * and no workflow runtime, so `stop_verify.py` and `Workflow(...)` are not projected. The plugin
 * carries only the events Kilo actually triggers.
 */

import { existsSync, rmSync } from "node:fs";
import { basename, delimiter, dirname, isAbsolute, join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

import { listDirs, listMarkdown, parseFrontmatter, readJson } from "../codex/lib.mjs";
import {
  copyTree,
  emitMarkdown,
  isFile,
  kiloConfigDir,
  kiloConfigFiles,
  kiloHome,
  kiloPaths,
  parseJsonc,
  readText,
  removeManagedKeys,
  rewriteForKilo,
  upsertManagedKeys,
  writeFile,
} from "./lib.mjs";
import { KILO_LEAF_AGENTS, isKiloModelId, resolveKiloAgentPolicy } from "./model-policy.mjs";

const HERE = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const VERSION_FILE = ".claude-plugin/plugin.json";

/** Tools we will switch off. UX tools (question, todowrite, suggest) are left alone on purpose. */
const GOVERNED_TOOLS = [
  "write",
  "edit",
  "apply_patch",
  "bash",
  "task",
  "webfetch",
  "websearch",
  "skill",
];

/** The Claude names that gate each governed Kilo tool. */
const GOVERNING_CLAUDE = {
  write: ["Write", "NotebookEdit"],
  edit: ["Edit", "Write", "NotebookEdit"],
  apply_patch: ["Edit", "Write", "NotebookEdit"],
  bash: ["Bash"],
  task: ["Agent", "Task"],
  webfetch: ["WebFetch"],
  websearch: ["WebSearch"],
  skill: ["Skill"],
};

/**
 * A shell deny-list for read-only roles. Deliberately not an allowlist: a research or review agent
 * legitimately runs `git log`, `rg`, `python3 -c` and repository scripts, and an allowlist wide
 * enough for those is an allowlist that no longer prevents mutation. Kilo evaluates the last
 * matching rule, and these are appended after the inherited defaults, so they can only tighten.
 */
const READ_ONLY_BASH_DENY = [
  "rm *",
  "rm -rf *",
  "rm -r *",
  "mv *",
  "dd *",
  "shred *",
  "truncate *",
  "tee *",
  "chmod *",
  "chown *",
  "mkfs*",
  "sudo *",
  "kill *",
  "pkill *",
  "git add*",
  "git commit*",
  "git push*",
  "git reset*",
  "git clean*",
  "git checkout*",
  "git switch*",
  "git restore*",
  "git merge*",
  "git rebase*",
  "git cherry-pick*",
  "git stash*",
  "git tag -d*",
  "git branch -d*",
  "git branch -D*",
  "git remote*",
  "git worktree*",
];

function asArray(value) {
  if (value === undefined || value === null) return null;
  return Array.isArray(value) ? value : [value];
}

function containedIn(root, target) {
  const rel = relative(root, target);
  return rel === "" || (!rel.startsWith("..") && !rel.includes(`..${sep}`) && !isAbsolute(rel));
}

/**
 * Translate canonical `tools` / `disallowedTools` into a Kilo `tools` map plus agent permissions.
 *
 * `tools:` is an allowlist in Claude Code, so a governed tool missing from it is off. `disallowedTools`
 * overrides that for the write family. The returned `permissions` add the same denials a second
 * time, because a role guardrail that only exists in one place is a role guardrail a copied file
 * can lose.
 */
export function projectAgentTools(frontmatter) {
  const allowed = asArray(frontmatter.tools);
  const disallowed = new Set((asArray(frontmatter.disallowedTools) ?? []).map(String));
  const tools = {};
  const permissions = {};

  for (const id of GOVERNED_TOOLS) {
    const claudeNames = GOVERNING_CLAUDE[id] ?? [];
    const blockedByDisallow = claudeNames.some((name) => disallowed.has(name));
    const blockedByAllowlist =
      allowed !== null &&
      claudeNames.length > 0 &&
      !claudeNames.some((name) => allowed.includes(name));
    if (blockedByDisallow || blockedByAllowlist) tools[id] = false;
  }

  if (tools.write === false && tools.edit === false && tools.apply_patch === false) {
    permissions.edit = "deny";
  }
  if (tools.task === false) permissions.task = "deny";

  const role = String(frontmatter.role_type ?? "").toLowerCase();
  if ((role === "evaluator" || role === "researcher") && tools.bash !== false) {
    permissions.bash = Object.fromEntries(READ_ONLY_BASH_DENY.map((p) => [p, "deny"]));
  }

  return { tools, permissions };
}

// ── agents ───────────────────────────────────────────────────────────────────

export function buildAgent(pluginRoot, file, { settings = {}, refs }) {
  const name = basename(file, ".md");
  const source = readText(join(pluginRoot, "agents", file));
  const { data, body } = parseFrontmatter(source);
  const policy = resolveKiloAgentPolicy(name, settings, data);
  if (!policy.model) {
    throw new Error(`Kilo agent ${name} has no resolvable model`);
  }
  const { tools, permissions } = projectAgentTools(data);
  if (KILO_LEAF_AGENTS.has(name)) permissions.task = "deny";

  const frontmatter = {
    description: data.description ?? `Graph Powers ${name}`,
    mode: "subagent",
    model: policy.model,
  };
  if (Object.keys(tools).length) frontmatter.tools = tools;
  if (Object.keys(permissions).length) frontmatter.permission = permissions;

  return {
    name,
    policy,
    contents: emitMarkdown(frontmatter, rewriteForKilo(body, refs)),
  };
}

export function buildAgents(pluginRoot, { settings = {}, refs }) {
  return listMarkdown(join(pluginRoot, "agents")).map((file) =>
    buildAgent(pluginRoot, file, { settings, refs }),
  );
}

// ── commands ─────────────────────────────────────────────────────────────────

/**
 * Which specialists each slash command must dispatch.
 *
 * Kilo runs a slash command **inside** the agent named by the command's `agent:` frontmatter, and
 * every canonical Graph Powers role is a `subagent` whose `tools:` allowlist excludes `Agent`. So a
 * command pinned to `evaluator` would run with no way to spawn the security reviewer it is
 * instructed to fan out to. The commands therefore run in one primary router — `graph-powers` —
 * and name the specialists they need by exact `subagent_type`.
 *
 * This is the routing the canonical method already declares; the projection makes it explicit and
 * testable instead of leaving the primary to infer it from prose.
 */
export const COMMAND_ROUTING = {
  debug: ["debugger", "explorer", "frontend-specialist"],
  design: ["ui-ux-designer"],
  evolve: ["skill-improver"],
  gauntlet: ["project-planner", "debugger", "evaluator"],
  implement: ["debugger", "frontend-specialist", "mobile-developer", "performance-optimizer", "verification"],
  "issue-improve": ["project-planner", "evaluator"],
  perf: ["performance-optimizer"],
  plan: ["project-planner", "evaluator"],
  prime: [],
  "pr-review": ["evaluator", "security-reviewer", "ui-ux-designer"],
  research: ["explorer", "librarian"],
  setup: [],
  verify: ["evaluator", "security-reviewer", "ui-ux-designer"],
};

const ROUTER = "graph-powers";

function routingFooter(name) {
  const agents = COMMAND_ROUTING[name] ?? [];
  const head = "> **Kilo routing.** Runs in the `graph-powers` primary.";
  if (!agents.length) return head;
  return `${head} Dispatch by exact \`task\` \`subagent_type\`: ${agents.map((a) => `\`${a}\``).join(", ")}.`;
}

export function buildCommand(pluginRoot, file, { refs }) {
  const name = basename(file, ".md");
  const source = readText(join(pluginRoot, "commands", file));
  const { data, body } = parseFrontmatter(source);
  const frontmatter = {
    description: data.description ?? `Graph Powers /${name}`,
    agent: ROUTER,
  };
  const projected = `${rewriteForKilo(body, refs).trimEnd()}\n\n${routingFooter(name)}\n`;
  return { name, contents: emitMarkdown(frontmatter, projected) };
}

export function buildCommands(pluginRoot, { refs }) {
  return listMarkdown(join(pluginRoot, "commands")).map((file) => buildCommand(pluginRoot, file, { refs }));
}

// ── router primary ────────────────────────────────────────────────────────────

/**
 * The one primary agent Graph Powers installs.
 *
 * Kilo's built-ins `ask`, `code`, `plan` and `debug` already claim the obvious names, so routing
 * `/debug` to Graph Powers instead of Kilo's own `debug` needs a description that separates them,
 * not just a name. Kilo chooses by description when nothing else decides.
 *
 * No `model:` on purpose: the main model is the operator's choice and belongs in `kilo.jsonc`.
 */
export function buildRouterAgent(pluginRoot, { refs, agents }) {
  const body = [
    "# Graph Powers",
    "",
    "You are the Graph Powers primary for this repository. You run the slash commands in",
    "`.kilo/command/` (or `~/.kilo/command/`) and you own their fan-out. You are not a substitute",
    "for Kilo's built-in `plan`, `debug` or `code` agents: when the request is a Graph Powers",
    "command, the method below it is binding.",
    "",
    "## Routing",
    "",
    "Dispatch specialists with the `task` tool, `subagent_type` set to the exact bare name. There is",
    "no namespace prefix on Kilo — a namespaced name resolves to no agent.",
    "",
    "| Command | Dispatch |",
    "|---|---|",
    ...Object.entries(COMMAND_ROUTING).map(
      ([name, list]) => `| \`/${name}\` | ${list.length ? list.map((a) => `\`${a}\``).join(", ") : "none — local work"} |`,
    ),
    "",
    "## Rules that survived the projection",
    "",
    "- A builder is never its own inspector. Reviewer and verifier roles (`evaluator`,",
    "  `security-reviewer`, `verification`, `ui-ux-designer`, `skill-improver`) are read-only here:",
    "  they carry `edit: deny` and, for research roles, a shell deny-list.",
    "- `evaluator` is a leaf: its `task` permission is denied. Do not ask it to spawn.",
    "- Gates come from `.graph-powers/config.json` and the Kilo guardrail plugin, not from this file.",
    "- Kilo has no workflow runtime and no Stop event. Where a canonical command says to invoke a",
    "  named workflow, use its declared fallback instead — never retry the name.",
    "",
    `Shared references live at \`${refs.referencesRef}\`; skills at \`${refs.skillsRef}\`.`,
    "",
  ].join("\n");

  return {
    name: ROUTER,
    contents: emitMarkdown(
      {
        description:
          "Graph Powers router: runs the Graph Powers slash commands and dispatches the " +
          `${agents.length} specialists by exact name. Use for /plan, /implement, /debug, ` +
          "/verify, /pr-review, /research, /design, /perf, /prime, /evolve, /gauntlet and " +
          "/issue-improve. Not the built-in Kilo plan/debug/code agent.",
        mode: "primary",
      },
      body,
    ),
  };
}

// ── skills ───────────────────────────────────────────────────────────────────

const SKIP = (src, entry) =>
  entry === "__pycache__" ||
  entry.endsWith(".pyc") ||
  (entry === "AGENTS.md" && src.replace(/\\/g, "/").endsWith("/skills/AGENTS.md"));

export function buildSkills(pluginRoot, paths, refs, { dryRun, written }) {
  const records = [];
  for (const name of listDirs(join(pluginRoot, "skills"))) {
    const target = join(paths.skills, name);
    const entry = join(target, "SKILL.md");
    records.push({ record: target, entry });
    if (dryRun) continue;
    copyTree(join(pluginRoot, "skills", name), target, SKIP, (text) =>
      rewriteForKilo(text, refs),
    );
    written.push(target);
  }
  for (const subtree of ["references", "schema", "templates"]) {
    const from = join(pluginRoot, subtree);
    if (!existsSync(from)) continue;
    const target = join(paths.assets, subtree);
    records.push({ record: target, entry: target });
    if (dryRun) continue;
    copyTree(from, target, SKIP, (text) => rewriteForKilo(text, refs));
    written.push(target);
  }
  return records;
}

// ── native hooks plugin ──────────────────────────────────────────────────────

/**
 * The registrations the Kilo plugin carries.
 *
 * `PermissionRequest`, `Notification`, `SubagentStart` and `Stop` have no confirmed Kilo event, so
 * they are absent rather than translated into something Kilo never calls. `subagent_context.py`
 * supplies the solution ladder to children, which Kilo cannot inject; the child agents carry the
 * ladder in their own prompt instead.
 */
export const KILO_HOOK_EVENTS = [
  { hook: "PreToolUse", matcher: "*", script: "graph_guardrails.py", timeout: 10 },
  { hook: "PreToolUse", matcher: "Bash", script: "git_commit_gate.py", timeout: 10 },
  { hook: "PreToolUse", matcher: "Bash", script: "git_push_gate.py", timeout: 10 },
  { hook: "PreToolUse", matcher: "Bash", script: "git_branch_gate.py", timeout: 10 },
  { hook: "PreToolUse", matcher: "Bash", script: "smart_bash_approver.py", timeout: 10 },
  { hook: "PreToolUse", matcher: "Bash", script: "commit_audit_gate.py", timeout: 610 },
  { hook: "PreToolUse", matcher: "Edit", script: "protect_files.py", timeout: 10 },
  { hook: "PostToolUse", matcher: "Edit", script: "ultracite.py", timeout: 30 },
];

export function buildHooksPlugin(pluginRoot) {
  const registrations = KILO_HOOK_EVENTS.map((entry) => ({
    event: entry.hook,
    matcher: entry.matcher,
    script: `${pluginRoot}/hooks/${entry.script}`,
    timeout: entry.timeout,
  }));
  return `/**
 * Graph Powers guardrails for Kilo — generated by kilo/install.mjs, do not edit.
 *
 * Kilo triggers plugin hooks from the same Python policies Claude Code, Codex, Cursor and Grok use.
 * The plugin is a transport, not a second policy: it hands each policy the canonical PreToolUse
 * payload and blocks the tool call only when the policy answers with an explicit denial.
 *
 * Fail-open is the repo contract. A missing interpreter, a timeout, a non-JSON answer or a crashed
 * policy never blocks a tool call — a guardrail that breaks the session is a guardrail people switch
 * off. A deliberate \`permissionDecision: deny\` does block.
 *
 * Kilo has no Stop event and no workflow runtime, so this file registers neither. Nothing here
 * auto-approves: \`permission.ask\` is intentionally absent.
 */

const REGISTRATIONS = ${JSON.stringify(registrations, null, 2)};

const TOOL_ALIASES = {
  bash: "Bash",
  read: "Read",
  write: "Edit",
  edit: "Edit",
  apply_patch: "Edit",
  glob: "Glob",
  grep: "Grep",
  webfetch: "WebFetch",
  websearch: "WebSearch",
  task: "Agent",
  skill: "Skill",
};

const DEFAULT_TIMEOUT_MS = 10000;

async function runPolicy(script, timeoutSeconds, payload) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutSeconds * 1000);
  try {
    const proc = Bun.spawn(["python3", "-X", "utf8", script], {
      stdin: "pipe",
      stdout: "pipe",
      stderr: "ignore",
      cwd: payload.cwd,
      signal: controller.signal,
    });
    proc.stdin.write(JSON.stringify(payload));
    await proc.stdin.end();
    const output = await new Response(proc.stdout).text();
    const code = await proc.exited;
    if (code !== 0) return null;
    try {
      return JSON.parse(output);
    } catch {
      return null;
    }
  } catch {
    return null;
  } finally {
    clearTimeout(timeout);
  }
}

function decisionOf(response) {
  if (!response || typeof response !== "object") return null;
  const specific = response.hookSpecificOutput;
  if (specific && specific.permissionDecision === "deny") {
    return String(specific.permissionDecisionReason ?? "denied by Graph Powers policy");
  }
  if (response.permissionDecision === "deny") {
    return String(response.permissionDecisionReason ?? "denied by Graph Powers policy");
  }
  return null;
}

function matches(matcher, tool) {
  if (!matcher || matcher === "*") return true;
  return String(matcher)
    .split("|")
    .map((part) => part.trim())
    .includes(tool);
}

function payloadFor(input, args, cwd) {
  const tool = TOOL_ALIASES[input.tool] ?? input.tool;
  return {
    hook_event_name: "PreToolUse",
    session_id: input.sessionID,
    cwd,
    tool_name: tool,
    tool_input: args && typeof args === "object" ? args : {},
  };
}

export default {
  id: "graph-powers-guardrails",
  server: async ({ directory, worktree }) => {
    const projectDir = worktree || directory || process.cwd();
    return {
      "tool.execute.before": async (input, output) => {
        const tool = TOOL_ALIASES[input.tool] ?? input.tool;
        const cwd = projectDir;
        const payload = payloadFor(input, output.args, cwd);
        for (const registration of REGISTRATIONS) {
          if (registration.event !== "PreToolUse") continue;
          if (!matches(registration.matcher, tool)) continue;
          const timeout = registration.timeout || DEFAULT_TIMEOUT_MS / 1000;
          const response = await runPolicy(registration.script, timeout, payload);
          const reason = decisionOf(response);
          if (reason) throw new Error(\`Graph Powers denied \${tool}: \${reason}\`);
        }
      },
      "tool.execute.after": async (input, output) => {
        const tool = TOOL_ALIASES[input.tool] ?? input.tool;
        const payload = {
          hook_event_name: "PostToolUse",
          session_id: input.sessionID,
          cwd: projectDir,
          tool_name: tool,
          tool_input: input.args && typeof input.args === "object" ? input.args : {},
        };
        for (const registration of REGISTRATIONS) {
          if (registration.event !== "PostToolUse") continue;
          if (!matches(registration.matcher, tool)) continue;
          await runPolicy(registration.script, registration.timeout || 10, payload);
        }
      },
      "shell.env": async (_input, output) => {
        output.env = output.env ?? {};
        output.env.GRAPH_POWERS_PROJECT_DIR = projectDir;
      },
    };
  },
};
`;
}

// ── LSP and formatting ───────────────────────────────────────────────────────

/**
 * The managed Kilo config keys.
 *
 * `formatter: false` is not "formatting off" — it is "one owner". `ultracite.py` formats the file
 * that changed, once, from the PostToolUse registration. Leaving Kilo's built-in formatter enabled
 * as well would format the same file twice and let two formatters disagree in the same repository.
 *
 * `lsp` disables the duplicate linter by its real built-in id (`eslint`) because Oxlint is the
 * declared local owner. A TS server is added only when `vtsls` actually resolves: pointing LSP at
 * a command that does not exist produces a server that reports itself started and answers nothing.
 * A vtsls-supplied TS server replaces the built-in `typescript` entry, which otherwise competes
 * with it.
 */
export function managedConfigKeys({ resolveCommand }) {
  const lsp = {
    eslint: { disabled: true },
  };
  const vtsls = resolveCommand("vtsls");
  if (vtsls) {
    lsp.typescript = { disabled: true };
    lsp.vtsls = {
      command: [vtsls, "--stdio"],
      extensions: [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts"],
    };
  }
  return {
    updates: { lsp, formatter: false },
    unavailable: vtsls ? [] : ["vtsls (TypeScript semantics): install it and re-run to enable"],
  };
}

/** Resolve a command without executing it: PATH first, then the project's own node_modules. */
export function defaultResolver(projectDir) {
  return (name) => {
    const local = join(projectDir, "node_modules", ".bin", name);
    if (isFile(local)) return local;
    const path = (process.env.PATH ?? "").split(delimiter).filter(Boolean);
    for (const dir of path) {
      const candidate = join(dir, name);
      if (isFile(candidate)) return candidate;
    }
    return null;
  };
}

// ── operator model overrides ─────────────────────────────────────────────────

/**
 * Where per-role model overrides come from.
 *
 * The generated agent's `model:` field is authoritative — proven with `kilo debug agent`: a config
 * `agent.<id>.model` in `kilo.jsonc` does **not** override an agent Markdown file. So the override
 * surface cannot be Kilo's config, and this file is it.
 *
 * It is operator-scoped (never tracked, never shipped in a repository) because a role→model choice
 * is a property of the person and the machine, not of the clone. `GRAPH_POWERS_KILO_MODELS` carries
 * the same object for CI and tests without touching a home directory.
 */
export function loadModelSettings(pluginRoot, { projectDir = process.cwd(), env = process.env } = {}) {
  if (env.GRAPH_POWERS_KILO_MODELS) {
    try {
      return JSON.parse(env.GRAPH_POWERS_KILO_MODELS);
    } catch (error) {
      throw new Error(`GRAPH_POWERS_KILO_MODELS is not valid JSON: ${error.message}`, { cause: error });
    }
  }
  for (const path of [
    join(kiloConfigDir(), "graph-powers.json"),
    join(projectDir, ".graph-powers", "kilo-models.json"),
    join(pluginRoot, "kilo", "model-overrides.json"),
  ]) {
    const raw = readText(path);
    if (!raw.trim()) continue;
    try {
      return JSON.parse(raw);
    } catch (error) {
      throw new Error(`${path} is not valid JSON: ${error.message}`, { cause: error });
    }
  }
  return {};
}

// ── install ──────────────────────────────────────────────────────────────────

function manifestBody({ version, scope, pluginRoot, planned, complete, configKeys, agents }) {
  return `${JSON.stringify(
    {
      version,
      scope,
      complete,
      pluginRoot,
      paths: planned,
      configKeys,
      agents,
    },
    null,
    2,
  )}\n`;
}

function plannedPaths(pluginRoot, paths) {
  return [
    ...listMarkdown(join(pluginRoot, "agents")).map((f) =>
      join(paths.agents, basename(f, ".md") + ".md"),
    ),
    join(paths.agents, `${ROUTER}.md`),
    ...listMarkdown(join(pluginRoot, "commands")).map((f) =>
      join(paths.commands, basename(f, ".md") + ".md"),
    ),
    ...listDirs(join(pluginRoot, "skills")).map((name) => join(paths.skills, name)),
    paths.references,
    join(paths.assets, "schema"),
    join(paths.assets, "templates"),
    join(paths.plugins, "graph-powers-guardrails.ts"),
  ];
}

/**
 * Record the manifest before writing anything, then mark it complete at the end.
 *
 * An install that dies halfway leaves `complete: false` behind — the only honest signal that the
 * tree on disk cannot be trusted. Writing the manifest afterwards loses exactly that.
 */
export function install({
  pluginRoot = HERE,
  scope = "user",
  projectDir = process.cwd(),
  dryRun = false,
  force = false,
  settings = null,
  log = () => {},
} = {}) {
  const paths = kiloPaths(scope, projectDir, pluginRoot);
  const version = readJson(join(pluginRoot, VERSION_FILE), {})?.version ?? "0.0.0";
  const modelSettings = settings ?? loadModelSettings(pluginRoot, { projectDir });
  const refs = {
    skillsRef: scope === "user" ? "~/.kilo/skills" : ".kilo/skills",
    referencesRef: paths.referencesRef,
    commandsRef: scope === "user" ? "~/.kilo/command" : ".kilo/command",
    agentsRef: scope === "user" ? "~/.kilo/agent" : ".kilo/agent",
    pluginRoot: scope === "user" ? "~/.kilo/graph-powers" : ".kilo/graph-powers",
  };
  const planned = plannedPaths(pluginRoot, paths);
  const written = [];

  const previous = readJson(paths.manifest, null);
  const ownedConfigKeys = Array.isArray(previous?.configKeys) ? previous.configKeys : [];
  const previousPaths = new Set(Array.isArray(previous?.paths) ? previous.paths : []);

  // Ownership: a file we would write that exists but is not in the previous manifest was written
  // by somebody else, and an install that takes it over is how a harness deletes a person's work.
  const foreign = [];
  for (const path of planned) {
    if (!existsSync(path)) continue;
    if (previousPaths.has(path) || force) continue;
    if (!force) foreign.push(path);
  }
  if (foreign.length && !force) {
    throw new Error(
      `refusing to overwrite unowned Kilo artefact(s): ${foreign.join(", ")}. ` +
        "Move them, or re-run with --force if they really are a previous Graph Powers install.",
    );
  }

  if (!dryRun) writeFile(paths.manifest, manifestBody({
    version,
    scope,
    pluginRoot,
    planned,
    complete: false,
    configKeys: ownedConfigKeys,
    agents: {},
  }));

  const agents = buildAgents(pluginRoot, { settings: modelSettings, refs });
  for (const agent of agents) {
    if (!isKiloModelId(agent.policy.model)) {
      throw new Error(`Kilo agent ${agent.name} resolves to a non-Kilo model: ${agent.policy.model}`);
    }
    const path = join(paths.agents, `${agent.name}.md`);
    log(path);
    if (!dryRun) writeFile(path, agent.contents);
    written.push(path);
  }

  const router = buildRouterAgent(pluginRoot, { refs, agents });
  const routerPath = join(paths.agents, `${router.name}.md`);
  log(routerPath);
  if (!dryRun) writeFile(routerPath, router.contents);
  written.push(routerPath);

  const commands = buildCommands(pluginRoot, { refs });
  for (const command of commands) {
    const path = join(paths.commands, `${command.name}.md`);
    log(path);
    if (!dryRun) writeFile(path, command.contents);
    written.push(path);
  }

  const skillRecords = buildSkills(pluginRoot, paths, refs, { dryRun, written });

  const pluginPath = join(paths.plugins, "graph-powers-guardrails.ts");
  log(pluginPath);
  if (!dryRun) writeFile(pluginPath, buildHooksPlugin(pluginRoot));
  written.push(pluginPath);

  // Config: comments and unrelated keys survive, managed keys are only taken when absent or ours.
  // User scope only: `formatter` and `lsp` describe how this machine's editor behaves, and a
  // repository has no business writing them.
  const resolver = defaultResolver(projectDir);
  const { updates, unavailable } = scope === "user"
    ? managedConfigKeys({ resolveCommand: resolver })
    : { updates: {}, unavailable: [] };
  // A managed key already present in the *other* global config is a conflict, not something to
  // shadow: the home file wins a conflicting key, so writing ours there would silently disable a
  // formatter the operator configured in the XDG file.
  const secondaryConflicts = [];
  for (const other of kiloConfigFiles().slice(1)) {
    if (!existsSync(other)) continue;
    let parsed;
    try {
      parsed = parseJsonc(readText(other));
    } catch {
      continue;
    }
    for (const key of Object.keys(updates)) {
      if (!Object.hasOwn(parsed, key)) continue;
      if (ownedConfigKeys.includes(key)) continue;
      if (JSON.stringify(parsed[key]) === JSON.stringify(updates[key])) continue;
      secondaryConflicts.push(`${other}:${key}`);
    }
  }
  if (secondaryConflicts.length) {
    throw new Error(
      `Kilo config defines managed key(s) elsewhere without Graph Powers ownership: ` +
        `${secondaryConflicts.join(", ")}. Merge them by hand, then re-run`,
    );
  }
  const configText = existsSync(paths.config) ? readText(paths.config) : "{}\n";
  const merged = upsertManagedKeys(configText, updates, ownedConfigKeys);
  if (merged.conflicts.length) {
    throw new Error(
      `Kilo config already defines ${merged.conflicts.join(", ")} without Graph Powers ownership; ` +
        "merge it by hand or remove the key, then re-run",
    );
  }
  const configChanged = merged.changed.length > 0;
  if (configChanged) {
    log(paths.config);
    if (!dryRun) writeFile(paths.config, merged.text.endsWith("\n") ? merged.text : `${merged.text}\n`);
    written.push(paths.config);
  }
  if (unavailable.length) for (const message of unavailable) log(`  ! ${message}`);

  if (!dryRun) {
    // The config file is recorded even when this run changed nothing, or a second install would
    // drop it from the manifest and an uninstall would leave the managed keys behind.
    const owned = scope === "user" && Object.keys(updates).length
      ? [...new Set([...planned, ...written, paths.config])]
      : [...new Set([...planned, ...written])];
    writeFile(paths.manifest, manifestBody({
      version,
      scope,
      pluginRoot,
      planned: owned.filter((p) => p !== paths.manifest),
      complete: true,
      configKeys: Object.keys(updates),
      agents: Object.fromEntries(agents.map((a) => [a.name, a.policy.model])),
    }));
  }

  return {
    written,
    planned,
    skillRecords,
    agents: agents.map(({ name, policy }) => Object.assign({ name }, policy)),
    configChanged,
    configConflicts: merged.conflicts,
    unavailable,
    manifest: paths.manifest,
    complete: !dryRun,
    version,
  };
}

export function uninstall({
  pluginRoot = HERE,
  scope = "user",
  projectDir = process.cwd(),
  dryRun = false,
  log = () => {},
} = {}) {
  const paths = kiloPaths(scope, projectDir, pluginRoot);
  const manifest = readJson(paths.manifest, null);
  if (!manifest) {
    log("no Kilo manifest recorded — nothing to remove");
    return { removed: [] };
  }
  // Containment, not trust: a manifest is a file on disk, and a corrupted one must never turn into
  // an `rm -rf` of somebody's home. A path is removable only when it sits under a directory this
  // installer owns.
  const roots = [paths.agents, paths.commands, paths.skills, paths.plugins, paths.assets].map(
    (p) => resolve(p),
  );
  const removed = [];
  for (const path of manifest.paths ?? []) {
    const target = resolve(path);
    const contained = roots.some((root) => containedIn(root, target));
    if (!contained) continue;
    if (!existsSync(target)) continue;
    if (dryRun) {
      removed.push(target);
      log(`(dry-run) ${target}`);
      continue;
    }
    try {
      rmSync(target, { recursive: true, force: true });
      removed.push(target);
      log(target);
    } catch (error) {
      log(`  ! could not remove ${target}: ${error.message}`);
    }
  }
  if (dryRun) return { removed };
  try {
    rmSync(paths.manifest, { force: true });
  } catch {
    // The manifest is ours; a failure here is not worth aborting the removals above.
  }
  // Restore the config surface too. A rollback that leaves `formatter: false` behind is the
  // harness still speaking after it was removed.
  const configKeys = Array.isArray(manifest.configKeys) ? manifest.configKeys : [];
  if (scope === "user" && configKeys.length && existsSync(paths.config)) {
    const text = readText(paths.config);
    const trimmed = removeManagedKeys(text, configKeys).trim();
    if (trimmed && trimmed !== "{}") {
      writeFile(paths.config, `${trimmed}\n`);
      log(`${paths.config} (managed keys restored)`);
    } else {
      rmSync(paths.config, { force: true });
      log(`${paths.config} (emptied by Graph Powers, removed)`);
    }
  }
  return { removed };
}

export function globallyInstalled(pluginRoot = HERE) {
  const paths = kiloPaths("user", process.cwd(), pluginRoot);
  const manifest = readJson(paths.manifest, null);
  if (!manifest) return { installed: false };
  const version = readJson(join(pluginRoot, VERSION_FILE), {})?.version ?? "0.0.0";
  const artifacts = (manifest.paths ?? []).every((path) => existsSync(path));
  return {
    installed: true,
    complete: manifest.complete === true && artifacts,
    version: manifest.version,
    available: version,
    sameVersion: manifest.complete === true && artifacts && manifest.version === version,
    manifest: paths.manifest,
    agents: manifest.agents ?? {},
  };
}

// ── CLI ──────────────────────────────────────────────────────────────────────

function argValue(argv, name, fallback) {
  const i = argv.indexOf(name);
  return i !== -1 && argv[i + 1] && !argv[i + 1].startsWith("-") ? argv[i + 1] : fallback;
}

function main() {
  const argv = process.argv.slice(2);
  const dryRun = argv.includes("--dry-run");
  const scope = argValue(argv, "--scope", "user");
  const projectDir = resolve(argValue(argv, "--project", process.cwd()));
  if (!["user", "project"].includes(scope)) {
    console.error(`invalid scope: ${scope} (use user|project)`);
    process.exitCode = 1;
    return;
  }
  if (argv.includes("--uninstall")) {
    const result = uninstall({ scope, projectDir, log: (m) => console.log(`  ${m}`) });
    console.log(`kilo: ${result.removed.length} path(s) removed`);
    return;
  }
  try {
    const result = install({
      scope,
      projectDir,
      dryRun,
      force: argv.includes("--force"),
      log: (m) => console.log(`  ${m}`),
    });
    if (argv.includes("--json")) {
      console.log(JSON.stringify({ ...result, written: result.written }, null, 2));
      return;
    }
    if (result.configConflicts.length) {
      console.error(`kilo: config conflicts: ${result.configConflicts.join(", ")}`);
      process.exitCode = 1;
      return;
    }
    console.log(
      dryRun
        ? `kilo: dry-run — ${result.planned.length} path(s) planned`
        : `kilo: ${result.written.length} path(s) written into ${kiloHome()}`,
    );
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  }
}

const invoked = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invoked) main();
