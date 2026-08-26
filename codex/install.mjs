#!/usr/bin/env node
/**
 * Generate the Codex CLI side of Graph Powers.
 *
 *   node codex/install.mjs [--project <dir>] [--plugin <dir>] [--scope project|user] [--dry-run]
 *
 * Codex reads four surfaces, and this writes all four from the artefacts that already exist
 * for Claude Code:
 *
 *   .codex/hooks.json          <- hooks/hooks.json             (identical event names and schema)
 *   .agents/skills/<name>/     <- skills/ and commands/        (identical SKILL.md frontmatter)
 *   .codex/agents/<name>.toml  <- agents/*.md                  (translated)
 *   AGENTS.md                  <- a delimited, idempotent block
 *
 * Two properties matter more than anything else here:
 *
 *   **Merge, never overwrite.** Other tools write `.codex/hooks.json` too — any skill installer
 *   with a hooks half is one of them. Clobbering it would silently disable somebody else's guardrails,
 *   which is the same failure this plugin exists to prevent, pointed the other way.
 *
 *   **Record what was written.** `.graph-powers/installed.json` lists every generated path and
 *   every hook entry added, so removal is exact rather than a guess with a glob.
 */

import { copyFileSync, existsSync, readdirSync, readFileSync, realpathSync, rmSync } from "node:fs";
import { homedir } from "node:os";
import { basename, dirname, isAbsolute, join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

import {
  asList,
  copyTree,
  listDirs,
  listMarkdown,
  parseFrontmatter,
  readJson,
  rewriteForCodex,
  tomlBlock,
  tomlString,
  writeFile,
} from "./lib.mjs";

const MARKER_START = "<!-- graph-powers:start -->";
const MARKER_END = "<!-- graph-powers:end -->";
const MANIFEST = ".graph-powers/installed.json";

// ── hooks ────────────────────────────────────────────────────────────────────

/**
 * Codex event names, payload shape and blocking semantics match Claude Code's, so the Python
 * files run unchanged. Only the wiring is regenerated, and only the plugin-root placeholder
 * has to be resolved — Codex does not export CLAUDE_PLUGIN_ROOT.
 */
export function buildHooks(hookManifest, pluginRoot) {
  const out = {};
  const added = [];
  for (const [event, matchers] of Object.entries(hookManifest.hooks ?? {})) {
    out[event] = matchers.map((group) => {
      const entry = {};
      if (group.matcher) entry.matcher = group.matcher;
      entry.hooks = group.hooks.map((h) => {
        const command = h.command.replaceAll("${CLAUDE_PLUGIN_ROOT}", pluginRoot);
        added.push({ event, command });
        const hook = { type: h.type, command };
        if (h.timeout) hook.timeout = h.timeout;
        return hook;
      });
      return entry;
    });
  }
  return { hooks: out, added };
}

/**
 * Read a hooks file that another tool may own.
 *
 * The distinction that matters: **absent is not the same as unreadable.** Treating a file we
 * failed to parse as an empty one is how the merge below turns into the overwrite its own header
 * promises never to do — somebody else's guardrails, deleted silently, by the code written to
 * protect them. A file that exists and does not parse is copied aside first, and the caller is
 * told where it went.
 */
export function readHooksFile(path, log = () => {}) {
  if (!existsSync(path)) return { hooks: {} };
  let raw;
  try {
    raw = readFileSync(path, "utf8");
  } catch (e) {
    throw new Error(
      `${path} exists but could not be read (${e.message}) — refusing to overwrite it.`,
      {
        cause: e,
      },
    );
  }
  try {
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === "object") return parsed;
  } catch {
    /* handled below */
  }

  const backup = `${path}.unparseable-backup`;
  try {
    copyFileSync(path, backup);
  } catch {
    /* the warning below is still the important part */
  }
  log(`${path} is not valid JSON — a copy was kept at ${backup}; its entries are NOT carried over`);
  return { hooks: {} };
}

/** Union of an existing hooks file and ours, keyed by (event, matcher, command). */
/**
 * A command this plugin wrote, recognised whatever root it was written with.
 *
 * The manifest command is a template — `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/notify.py"` — so the
 * same hook installed from two different plugin roots produces two different strings. Matching on
 * the string alone therefore treats our own previous block as a stranger's and keeps it: measured
 * on a real machine, re-pointing the plugin root left every guardrail registered twice, one copy
 * of each running code from a directory that no longer had a reason to exist. Comparing against
 * the template with the root wildcarded is what makes the merge idempotent across a move.
 */
const escapeRe = (value) => value.replaceAll(/[.*+?^${}()|[\]\\]/g, "\\$&");

function ourCommandPattern(template, roots) {
  // The roots this install can vouch for: where it is running from now, plus wherever the manifest
  // says the previous install ran from. `.+` used to stand in for "any root", and it matched more
  // than any root — `python3 "/opt/other-tool/hooks/notify.py"` satisfies
  // `^python3 "(.+)/hooks/notify\.py"$`, so a third party's hook with the same basename was
  // deleted on the next install. That is destruction of a file this installer did not create, in
  // the one file the uninstall path and the CI fixture are both explicit about preserving.
  //
  // An unknown root now matches nothing, which at worst leaves a duplicate registration — visible,
  // and repaired by `--force`. Deleting somebody else's hook is neither.
  if (!roots.length) return null;
  const alternation = roots.map(escapeRe).join("|");
  const escaped = escapeRe(template);
  return new RegExp(`^${escaped.replaceAll("\\$\\{CLAUDE_PLUGIN_ROOT\\}", `(?:${alternation})`)}$`);
}

export function mergeHooks(existing, ours, templates = [], roots = [], known = []) {
  const merged = JSON.parse(JSON.stringify(existing?.hooks ? existing : { hooks: {} }));
  merged.hooks ??= {};
  const mine = templates.map((t) => ourCommandPattern(t, roots)).filter(Boolean);
  // Two ways to recognise our own: the exact strings the last manifest recorded writing, and the
  // templates resolved against a root we know about. The first is identity, not inference, and it
  // is what makes a moved root repairable without guessing at paths.
  const recorded = new Set(known);
  const isMine = (command) => recorded.has(command) || mine.some((re) => re.test(command));

  for (const [event, groups] of Object.entries(ours)) {
    merged.hooks[event] ??= [];
    const target = merged.hooks[event];
    for (const group of groups) {
      const slot = target.find((g) => (g.matcher ?? null) === (group.matcher ?? null));
      if (!slot) {
        target.push(JSON.parse(JSON.stringify(group)));
        continue;
      }
      slot.hooks ??= [];
      // Drop our own earlier copies first — the ones about to be replaced by the same hook under
      // the current root. A third party's hook never matches a template of ours and stays.
      const fresh = new Set(group.hooks.map((h) => h.command));
      slot.hooks = slot.hooks.filter((h) => !(isMine(h.command) && !fresh.has(h.command)));
      for (const hook of group.hooks) {
        if (!slot.hooks.some((h) => h.command === hook.command)) {
          slot.hooks.push({ ...hook });
        }
      }
    }
  }
  // An entry we emptied of everything says nothing and should not survive as `{"hooks": []}`.
  for (const [event, groups] of Object.entries(merged.hooks)) {
    merged.hooks[event] = groups.filter((g) => (g.hooks ?? []).length > 0);
    if (merged.hooks[event].length === 0) delete merged.hooks[event];
  }
  return merged;
}

/** Remove only the entries a previous run recorded; leave every other tool's hooks alone. */
export function unmergeHooks(existing, addedCommands) {
  if (!existing?.hooks) return existing;
  const kill = new Set(addedCommands);
  const out = { ...existing, hooks: {} };
  for (const [event, groups] of Object.entries(existing.hooks)) {
    const kept = [];
    for (const g of groups) {
      const hooks = (g.hooks ?? []).filter((h) => !kill.has(h.command));
      if (hooks.length > 0) kept.push({ ...g, hooks });
    }
    if (kept.length) out.hooks[event] = kept;
  }
  return out;
}

/**
 * Write a hooks file only when its content differs from what is already there.
 *
 * The path is still recorded either way: the manifest answers "is this ours to remove", not
 * "did this run touch it".
 */
export function emitHooks(path, merged, { dryRun = false, log = () => {}, written = [] } = {}) {
  const next = `${JSON.stringify(merged, null, 2)}\n`;
  written.push(path);
  let current = null;
  try {
    current = readFileSync(path, "utf8");
  } catch {
    /* absent — write it */
  }
  if (current === next) {
    log(`${path} — unchanged, left alone (a rewrite would cost a /hooks re-approval)`);
    return false;
  }
  log(path);
  if (!dryRun) writeFile(path, next);
  return true;
}

// ── subagents ────────────────────────────────────────────────────────────────

const JUDGING_ROLES = new Set(["evaluator", "researcher", "orchestrator"]);

/**
 * `agents/*.md` -> `.codex/agents/<name>.toml`.
 *
 * The one translation that carries meaning: `disallowedTools: Write, Edit` becomes
 * `sandbox_mode = "read-only"`. Codex has no per-tool denylist, and a read-only claim that
 * survives only as prose in the body is exactly the defect this plugin found in its own agents.
 */
/**
 * Claude model families have no Codex equivalent, so a `model: opus` cannot travel as written.
 * What does travel is the *intent* behind it — this agent was given the strongest model, or the
 * cheapest one — and Codex expresses the same intent through reasoning effort.
 *
 * Ignoring the agent's own frontmatter, as the first version did, flattened twelve deliberately
 * different agents into twelve identical ones: the `haiku` scout and the `opus` evaluator came
 * out of the generator indistinguishable.
 */
const EFFORT_BY_MODEL = { haiku: "low", sonnet: "medium", opus: "high" };
const VALID_EFFORT = new Set(["low", "medium", "high", "xhigh"]);

/** Claude Code family names. Codex has no haiku/sonnet/opus, and treating `haiku` as a
 *  model slug routes the child onto the Spark / `codex_bengalfox` pool instead of the
 *  user's own Codex limit. */
export const CLAUDE_MODEL_FAMILIES = new Set(["haiku", "sonnet", "opus", "fable"]);

/**
 * Claude family -> tier. The family an agent declares is the only place a tier is written down, so
 * it is what travels: `opus` means "this node judges, designs or verifies", `haiku` means "this
 * node is a scout". Codex has no such families, but it does have a strong model and a cheap one,
 * and `codex.models` in the project config is where those two names live.
 */
export const TIER_BY_MODEL = { haiku: "light", sonnet: "standard", fable: "standard", opus: "heavy" };

/**
 * The Codex slug a generated subagent gets: the tier its Claude family implies, else the project's
 * flat `codex.model`, else nothing (inherit the session model, which is what the first version did
 * for every agent alike).
 *
 * Without the tier the twelve agents came out of the generator on ONE model, so the scout that
 * reads a config file and the reviewer that judges a plan spent the same window. Effort alone does
 * not fix that: a cheap-effort call on the strong model is still billed as the strong model.
 */
export function codexModelFor(claudeFamily, { model, models } = {}) {
  const tier = TIER_BY_MODEL[String(claudeFamily ?? "").toLowerCase()];
  const candidates = [tier ? models?.[tier] : null, model];
  return candidates.find((m) => isCodexModelSlug(m)) ?? null;
}

/**
 * This project's Codex model settings, from the config the harness already defines.
 *
 * One reader, two callers: the `graph-powers` CLI and this file's own `--project` mode. They used
 * to disagree — the CLI passed the model, the direct invocation passed nothing — so the same
 * project generated subagents with a model or without one depending on which command ran, and the
 * CI fixture only ever exercised the second.
 */
export function readCodexSettings(projectDir) {
  const cfg =
    readJson(join(projectDir, ".graph-powers/config.json")) ??
    readJson(join(projectDir, ".claude/config.json")) ??
    {};
  const codex = cfg.codex ?? {};
  const models = Object.fromEntries(
    Object.entries(codex.models ?? {}).filter(([, v]) => typeof v === "string" && v),
  );
  return {
    ...(Object.keys(models).length ? { models } : {}),
    ...(typeof codex.model === "string" && codex.model ? { model: codex.model } : {}),
    ...(typeof codex.reasoningEffort === "string" && codex.reasoningEffort
      ? { reasoningEffort: codex.reasoningEffort }
      : {}),
  };
}

export function isCodexModelSlug(model) {
  const name = String(model ?? "").trim();
  if (!name) return false;
  const lower = name.toLowerCase();
  if (CLAUDE_MODEL_FAMILIES.has(lower)) return false;
  if (lower.startsWith("claude")) return false;
  return true;
}

export function agentToToml(markdown, { model, models, reasoningEffort } = {}) {
  const { data, body } = parseFrontmatter(markdown);
  if (!data.name || !data.description) return null;

  // Read-only means the agent cannot produce a file. Denying only `Edit` (as the planner does,
  // to keep Write for its plan file) is not read-only, and sandboxing it as such would break it.
  const denied = asList(data.disallowedTools).map((t) => String(t).toLowerCase());
  const readOnly = denied.includes("write");

  const lines = [
    `# Generated by graph-powers from agents/${data.name}.md — do not edit by hand.`,
    "# Change the source agent and re-run the installer; an edit here is lost on the next update.",
    "",
    `name = ${tomlString(data.name)}`,
    `description = ${tomlString(data.description)}`,
  ];

  // The Codex model is a project-wide setting, never one written into the generator: a model name
  // in code is a file that ages out the week the next model ships. Claude family names are not
  // Codex slugs — writing them made the native plugin spend the Spark / Bengal Fox window.
  //
  // Which of the project's slugs this agent gets is not project-wide, though: it follows the tier
  // the agent's own frontmatter declares, so `codex.models.light` reaches the scouts and
  // `codex.models.heavy` reaches the nodes that judge.
  const codexModel = codexModelFor(asList(data.model)[0], { model, models });
  if (codexModel) lines.push(`model = ${tomlString(codexModel)}`);

  // Effort, most specific source first: the agent said so; else its Claude model implies it; else
  // the role is a judging one and judging wants headroom; else whatever the project configured.
  const declared = String(asList(data.effort)[0] ?? "").toLowerCase();
  const fromModel = EFFORT_BY_MODEL[String(asList(data.model)[0] ?? "").toLowerCase()];
  const byRole = JUDGING_ROLES.has(String(asList(data.role_type)[0] ?? "")) ? "high" : null;
  const effort = [declared, fromModel, byRole, reasoningEffort].find(
    (e) => e && VALID_EFFORT.has(String(e)),
  );
  if (effort) lines.push(`model_reasoning_effort = ${tomlString(effort)}`);

  if (readOnly) lines.push(`sandbox_mode = "read-only"`);

  lines.push("", `developer_instructions = ${tomlBlock(body)}`, "");
  return lines.join("\n");
}

// ── AGENTS.md ────────────────────────────────────────────────────────────────

export function agentsBlock(refsDir = "~/.codex/graph-powers", { global: isGlobal = false } = {}) {
  return [
    MARKER_START,
    "## Graph Powers",
    "",
    isGlobal
      ? "This machine runs the Graph Powers harness, installed once and shared by every project."
      : "This project runs the Graph Powers harness.",
    "",
    "Three files carry everything else:",
    "",
    `- \`${refsDir}/shared-context.md\` — an index of the shared patterns, one file each under`,
    `  \`${refsDir}/shared/\`: config loader, quality gates, complexity routing, agent matrix,`,
    "  spawn patterns, and the rest. Read the index, then only the fragments the task needs.",
    `- \`${refsDir}/safety-floor.md\` — the invariants that hold regardless of the task: git and`,
    "  outward-facing actions, tenant and personal data, irreversible operations, secrets, tooling,",
    "  scope, completion claims, accessibility.",
    `- \`${refsDir}/execution-floor.md\` — how the work is coordinated, in force from the first turn:`,
    "  delegation is required above L3 and refused below it, read-only agents go to the background in",
    "  a single message, one writer per file, and the seven-section contract every spawned prompt",
    "  carries. On Codex nothing spawns on its own — the prompt has to say so. Read it before",
    "  spawning anything.",
    "",
    "**What is global and what is this project's.** The harness itself — skills, subagents,",
    "commands, guardrails — is installed once for the whole machine, because it is identical",
    "everywhere. What belongs to this repository and nothing else lives here:",
    "",
    "- `.graph-powers/config.json` — the branch, the gate commands, the paths, the opt-in prefix",
    "- `.codex/rules/` and `.claude/rules/` — this project's domain rules",
    "- `DESIGN.md`, `PRODUCT.md`, `REVIEW.md` — its design, product and review authorities",
    "",
    "The guardrails are what make one global copy correct rather than sloppy: they read **this**",
    "project's config at runtime, so the same files enforce a different work branch and a different",
    "opt-in key in every repository.",
    "",
    "Read the config; never assume it. A denied command is the rule working, not a bug to route",
    "around: it names the environment variable that releases it, and a person sets that variable,",
    "in the turn they approved it.",
    MARKER_END,
  ].join("\n");
}

export function upsertBlock(existing, block) {
  const text = existing ?? "";
  const start = text.indexOf(MARKER_START);
  const end = text.indexOf(MARKER_END);
  if (start !== -1 && end !== -1 && end > start) {
    return text.slice(0, start) + block + text.slice(end + MARKER_END.length);
  }
  return text.trimEnd() ? `${text.trimEnd()}\n\n${block}\n` : `${block}\n`;
}

// ── orchestration ────────────────────────────────────────────────────────────

// Where each surface lives, by scope.
//
// The split is not arbitrary. **The harness is identical in every project, so it installs once,
// globally.** What differs per project — the branch, the gate commands, the paths, the opt-in
// prefix, the domain rules, the design and product and review authorities — is what stays local.
//
// The guardrails make this work rather than break it: one global copy of the hooks reads each
// project's own `.graph-powers/config.json` at runtime through `_config.py`. So a single install
// enforces a different work branch and a different opt-in key in every repository, without a
// second copy of anything.
export function codexPaths(scope, projectDir) {
  // `process.env.HOME` is undefined on Windows — the variable is `USERPROFILE`. Every fallback
  // below used to land on the project directory instead, which turned a `--scope user` install into
  // a silent project install: `.codex/`, `.agents/skills/` and the permission allowlist were written
  // into somebody else's repository. `homedir()` reads the right variable on every platform.
  const home = process.env.CODEX_HOME || join(homedir(), ".codex");
  const agentsHome = homedir();
  return scope === "user"
    ? {
        skills: join(agentsHome, ".agents/skills"),
        agents: join(home, "agents"),
        hooks: join(home, "hooks.json"),
        references: join(home, "graph-powers"),
        // `~/.codex/` is the same path on every machine, so an AGENTS.md that points there stays
        // portable when it is committed — unlike an absolute plugin path.
        referencesRef: "~/.codex/graph-powers",
        instructions: join(home, "AGENTS.md"),
        manifest: join(home, "graph-powers-installed.json"),
      }
    : {
        skills: join(projectDir, ".agents/skills"),
        agents: join(projectDir, ".codex/agents"),
        hooks: join(projectDir, ".codex/hooks.json"),
        references: join(projectDir, ".codex/graph-powers"),
        referencesRef: ".codex/graph-powers",
        instructions: join(projectDir, "AGENTS.md"),
        manifest: join(projectDir, MANIFEST),
      };
}

/** Is the harness already installed globally for Codex, at this version? */
export function globallyInstalled(pluginRoot) {
  const paths = codexPaths("user", process.cwd());
  const manifest = readJson(paths.manifest);
  if (!manifest) return { installed: false };
  const pluginJson = readJson(join(pluginRoot, ".claude-plugin/plugin.json")) ?? {};
  return {
    installed: true,
    sameVersion: manifest.version === pluginJson.version,
    version: manifest.version,
    available: pluginJson.version,
    manifest: paths.manifest,
  };
}

// ── the shared half ──────────────────────────────────────────────────────────
//
// Both scopes write the same six artefacts; only their destinations differ. Keeping two copies of
// that logic is precisely the divergence this plugin exists to end, and it had already started:
// the project-scope path was still resolving `${CLAUDE_PLUGIN_ROOT}` the old way weeks after the
// global path stopped. One implementation, two sets of paths.

/**
 * The record of what an install created — the only thing that makes removal exact rather than a
 * glob and a hope.
 *
 * `adopted` is separate from `paths` on purpose: rule templates are copied as a starting point and
 * then edited by the project, so the line somebody added after an incident lives in them. Removal
 * reports where they are and leaves them alone.
 */
function manifestBuilder({
  manifestPath,
  version,
  pluginRoot,
  scope,
  hookCommands,
  adopted = [],
  extra = {},
}) {
  const excluded = new Set([manifestPath, ...adopted]);
  return (list, complete) =>
    `${JSON.stringify(
      {
        version,
        scope,
        complete,
        pluginRoot,
        hookCommands,
        paths: list.filter((path) => !excluded.has(path)),
        ...(adopted.length ? { adopted } : {}),
        ...extra,
      },
      null,
      2,
    )}\n`;
}

/**
 * The first two writes of any install, in the order that matters: the manifest that says what is
 * about to be created, then the hooks file.
 *
 * Both scopes did this identically and one of them had already started to drift. The order is the
 * load-bearing part — a manifest written after the files it describes cannot survive an install
 * that dies in between.
 */
function openInstall({
  paths,
  hookManifest,
  pluginRoot,
  manifestBody,
  extraPlanned,
  dryRun,
  log,
  written,
}) {
  const planned = plannedPaths(pluginRoot, paths, extraPlanned);
  // Read before the write, because the write destroys it. The previous manifest is the only record
  // of which command strings this plugin put in a shared hooks file and which root it used; the
  // line below replaces it with this run's. Reading it afterwards returns the current root twice
  // and leaves the old block in place — which is the duplication this whole path exists to stop.
  const previous = readJson(paths.manifest) ?? {};
  if (!dryRun) writeFile(paths.manifest, manifestBody(planned, false));

  // Hooks, merged. Another tool may write this file too (any installer with a hooks half), and
  // clobbering it would silently disable somebody else's guardrails.
  //
  // Written only when the bytes change. Codex trusts a hooks file by its content, so an identical
  // rewrite is not a no-op: it costs the user a `/hooks` re-approval, and until they give it the
  // guardrails are inert. An update that quietly disarms the thing it updated is worse than none.
  const { hooks, added } = buildHooks(hookManifest, pluginRoot);
  // The manifest's own command templates, root still unresolved: what lets the merge recognise a
  // block this plugin wrote from somewhere else and replace it instead of doubling it.
  const templates = Object.values(hookManifest.hooks ?? {})
    .flat()
    .flatMap((g) => (g.hooks ?? []).map((h) => h.command));
  // What the previous install left behind, read from its own manifest: the exact command strings
  // and the root they were written with. Without this the merge has to infer ownership from the
  // path shape, and a path shape is exactly what a third party can share by accident.
  const roots = [...new Set([pluginRoot, previous.pluginRoot].filter(Boolean))];
  const known = Array.isArray(previous.hookCommands) ? previous.hookCommands : [];
  emitHooks(
    paths.hooks,
    mergeHooks(readHooksFile(paths.hooks, log), hooks, templates, roots, known),
    { dryRun, log, written },
  );
  return { planned, added };
}

/** A recorder: `emit` writes and remembers, `written` is what a manifest will list. */
function recorder({ dryRun, log }) {
  const written = [];
  const emit = (path, contents) => {
    log(path);
    if (!dryRun) writeFile(path, contents);
    written.push(path);
  };
  return { written, emit };
}

/** Every path an install of this plugin creates, before it creates any of them. */
function plannedPaths(pluginRoot, paths, extra = []) {
  return [
    ...extra,
    ...listDirs(join(pluginRoot, "skills")).map((n) => join(paths.skills, n)),
    ...listMarkdown(join(pluginRoot, "commands")).map((f) =>
      join(paths.skills, `graph-powers-${basename(f, ".md")}`),
    ),
    ...listMarkdown(join(pluginRoot, "agents")).map((f) =>
      join(paths.agents, `${basename(f, ".md")}.toml`),
    ),
  ];
}

/** The interpreter's leftovers. They are not artefacts, so they are not copied and not recorded. */
const skipJunk = (_src, entry) => entry === "__pycache__" || entry.endsWith(".pyc");

/**
 * Skills, commands-as-skills, subagents and shared references — the four surfaces Codex reads.
 *
 * `rewrite` resolves `${CLAUDE_PLUGIN_ROOT}` on the way through. Codex never sets that variable,
 * so a copy that still carries it points at nothing: the reference reads as present and loads as
 * empty, which is worse than a missing file because nothing reports it.
 */
function writeHarness({ pluginRoot, paths, rewrite, codex, dryRun, log, written, emit }) {
  // **Record each skill directory, never the parent.** `~/.agents/skills` is shared: it already
  // holds whatever else the person installed. Putting the parent in the manifest would make
  // `--uninstall` delete their other tools' skills along with ours.
  if (!dryRun) copyTree(join(pluginRoot, "skills"), paths.skills, skipJunk, rewrite);
  for (const name of listDirs(join(pluginRoot, "skills"))) written.push(join(paths.skills, name));
  log(`${paths.skills}/ (${listDirs(join(pluginRoot, "skills")).length} skills)`);

  // Commands become skills: Codex deprecated custom prompts in favour of them.
  for (const file of listMarkdown(join(pluginRoot, "commands"))) {
    const name = basename(file, ".md");
    const { data, body } = parseFrontmatter(
      readFileSync(join(pluginRoot, "commands", file), "utf8"),
    );
    if (!data.description) continue;
    written.push(join(paths.skills, `graph-powers-${name}`));
    emit(
      join(paths.skills, `graph-powers-${name}`, "SKILL.md"),
      rewrite(
        [
          "---",
          `name: graph-powers-${name}`,
          `description: ${JSON.stringify(String(data.description))}`,
          "---",
          "",
          `> Generated from the \`/${name}\` command of Graph Powers. On Claude Code this is a slash`,
          "> command; Codex reads it as a skill, which is the surface Codex kept.",
          "",
          body.trimStart(),
        ].join("\n"),
      ),
    );
  }

  // Subagents. Rewritten before translation, not after: the agent bodies carry the same
  // plugin-root references the skills do, and a subagent pointed at a path that resolves to
  // nothing loads an empty rubric and reports as if it had read one.
  for (const file of listMarkdown(join(pluginRoot, "agents"))) {
    const toml = agentToToml(
      rewrite(readFileSync(join(pluginRoot, "agents", file), "utf8")),
      codex,
    );
    if (toml) emit(join(paths.agents, `${basename(file, ".md")}.toml`), toml);
  }

  if (!dryRun) copyTree(join(pluginRoot, "references"), paths.references, () => false, rewrite);
  log(`${paths.references}/ (shared references)`);
  written.push(paths.references);
}

/** The AGENTS.md block, upserted between markers so a second install is not a second copy. */
function writeInstructions({ path, referencesRef, global: isGlobal, emit }) {
  const current = existsSync(path) ? readFileSync(path, "utf8") : "";
  emit(path, upsertBlock(current, agentsBlock(referencesRef, { global: isGlobal })));
}

/**
 * The global half: everything that is identical in every project.
 *
 * Skipped entirely when it is already present at the same version — re-copying 11 skills on every
 * project setup is work nobody asked for, and on Codex it would also churn `hooks.json`, which
 * costs the user a re-approval prompt for no change.
 */
export function installGlobal({
  pluginRoot,
  dryRun = false,
  force = false,
  codex = {},
  log = () => {},
}) {
  const paths = codexPaths("user", process.cwd());
  const pluginJson = readJson(join(pluginRoot, ".claude-plugin/plugin.json"));
  if (!pluginJson) throw new Error(`plugin.json not found under ${pluginRoot}`);
  const hookManifest = readJson(join(pluginRoot, "hooks/hooks.json"));
  if (!hookManifest) throw new Error(`hooks/hooks.json not found under ${pluginRoot}`);

  const state = globallyInstalled(pluginRoot);
  if (state.installed && state.sameVersion && !force) {
    log(`already global at ${state.version} — skipped`);
    return { skipped: true, written: [], ...state };
  }

  const { written, emit } = recorder({ dryRun, log });

  // The manifest is written FIRST, listing everything this run intends to create. Written last,
  // an install that dies halfway — a full disk, a permission error, a terminated process — leaves
  // artefacts on disk and no record of them, and `--uninstall` then reports success while every
  // one of those files stays. Over-listing is harmless: removal skips what is not there.
  const manifestBody = manifestBuilder({
    manifestPath: paths.manifest,
    version: pluginJson.version,
    pluginRoot,
    scope: "user",
    hookCommands: buildHooks(hookManifest, pluginRoot).added.map((a) => a.command),
  });
  const { planned } = openInstall({
    paths,
    hookManifest,
    pluginRoot,
    manifestBody,
    extraPlanned: [paths.hooks, paths.instructions, paths.references],
    dryRun,
    log,
    written,
  });

  const home = homedir();
  const rewrite = (text) =>
    rewriteForCodex(text, {
      skillsRef: home ? paths.skills.replace(home, "~") : paths.skills,
      referencesRef: paths.referencesRef,
      pluginRoot,
    });

  writeHarness({ pluginRoot, paths, rewrite, codex, dryRun, log, written, emit });
  writeInstructions({
    path: paths.instructions,
    referencesRef: paths.referencesRef,
    global: true,
    emit,
  });

  // Rewritten with what actually landed, and marked complete.
  log(paths.manifest);
  if (!dryRun)
    writeFile(paths.manifest, manifestBody([...new Set([...planned, ...written])], true));

  return { skipped: false, written, version: pluginJson.version, manifest: paths.manifest };
}

/**
 * The project half: only what cannot be anything but local.
 *
 * Rules, and the instruction block that names this project's config. Everything else already
 * exists globally, so a second copy here would be the divergence this plugin was built to end.
 */
export function installProject({ projectDir, pluginRoot, dryRun = false, log = () => {} }) {
  const globalPaths = codexPaths("user", projectDir);
  const manifestPath = join(projectDir, MANIFEST);
  const { written, emit } = recorder({ dryRun, log });

  const rulesSrc = join(pluginRoot, "templates/rules");
  const rulesDst = join(projectDir, ".codex/rules");
  const agentsPath = join(projectDir, "AGENTS.md");

  // Same reasoning as the global half: recorded before it is created, never after. Without this
  // the project half had no manifest at all, so `--uninstall` left `.codex/rules/` and the
  // AGENTS.md block behind while reporting it had removed everything.
  // No hooks in the project half: they are global, and they read this project's config at
  // runtime. An empty list keeps `unmergeHooks` from being handed `undefined`.
  const manifestBody = manifestBuilder({
    manifestPath,
    version: readJson(join(pluginRoot, ".claude-plugin/plugin.json"))?.version ?? null,
    pluginRoot,
    scope: "project",
    hookCommands: [],
    adopted: [rulesDst],
  });
  if (!dryRun) writeFile(manifestPath, manifestBody([agentsPath], false));

  // Rule templates — the project adapts them; they are its own, and they diverge on purpose.
  if (existsSync(rulesSrc)) {
    if (!dryRun) copyTree(rulesSrc, rulesDst);
    log(`${rulesDst}/ (rule templates — adapt them, they are yours)`);
    written.push(rulesDst);
  }

  writeInstructions({
    path: agentsPath,
    referencesRef: globalPaths.referencesRef,
    global: true,
    emit,
  });

  log(manifestPath);
  if (!dryRun) writeFile(manifestPath, manifestBody(written, true));
  written.push(manifestPath);

  return written;
}

/** Backwards-compatible entry point: global first, then the project half. */
export function install({
  projectDir,
  pluginRoot,
  scope = "user",
  dryRun = false,
  force = false,
  codex = {},
  log = () => {},
}) {
  if (scope === "project") {
    return installProjectOnlyLegacy({ projectDir, pluginRoot, dryRun, codex, log });
  }
  const global = installGlobal({ pluginRoot, dryRun, force, codex, log });
  const project = installProject({ projectDir, pluginRoot, dryRun, log });
  return [...global.written, ...project];
}

/**
 * Everything into the project, nothing global. Kept for the case the global default cannot serve:
 * a machine where several people share a home directory, or a repository that must carry its own
 * pinned copy. It is not the default, and the setup playbook says why.
 */
function installProjectOnlyLegacy({
  projectDir,
  pluginRoot,
  dryRun = false,
  codex = {},
  log = () => {},
}) {
  const paths = codexPaths("project", projectDir);
  const pluginJson = readJson(join(pluginRoot, ".claude-plugin/plugin.json"));
  if (!pluginJson) throw new Error(`plugin.json not found under ${pluginRoot}`);
  const hookManifest = readJson(join(pluginRoot, "hooks/hooks.json"));
  if (!hookManifest) throw new Error(`hooks/hooks.json not found under ${pluginRoot}`);

  const { written, emit } = recorder({ dryRun, log });
  const agentsPath = join(projectDir, "AGENTS.md");
  const rulesDst = join(projectDir, ".codex/rules");

  const manifestBody = manifestBuilder({
    manifestPath: paths.manifest,
    version: pluginJson.version,
    pluginRoot,
    scope: "project",
    hookCommands: buildHooks(hookManifest, pluginRoot).added.map((a) => a.command),
    adopted: [rulesDst],
    extra: { machineSpecific: [".codex/hooks.json", ".codex/agents/", ".agents/skills/"] },
  });
  const { planned } = openInstall({
    paths,
    hookManifest,
    pluginRoot,
    manifestBody,
    extraPlanned: [paths.hooks, agentsPath, paths.references],
    dryRun,
    log,
    written,
  });

  const rewrite = (text) =>
    rewriteForCodex(text, {
      skillsRef: ".agents/skills",
      referencesRef: paths.referencesRef,
      pluginRoot,
    });

  writeHarness({ pluginRoot, paths, rewrite, codex, dryRun, log, written, emit });

  const rulesSrc = join(pluginRoot, "templates/rules");
  if (existsSync(rulesSrc)) {
    if (!dryRun) copyTree(rulesSrc, rulesDst);
    written.push(rulesDst);
  }

  writeInstructions({ path: agentsPath, referencesRef: paths.referencesRef, global: false, emit });

  emit(paths.manifest, manifestBody([...new Set([...planned, ...written])], true));

  return written;
}

// ── containment ──────────────────────────────────────────────────────────────
//
// Everything below exists to answer one question before `rmSync` or `writeFile` is handed a path
// that came out of a JSON file: **did this installer write inside there?** `manifest.paths` is
// `JSON.parse` with no schema over a file on disk, and in the project scope that file is
// `.graph-powers/installed.json` — a normal, committable artefact of any repository that installs
// the plugin. Whoever can land a commit can therefore name a path, and until this check existed
// the only things standing between that name and a recursive delete were a basename regex and a
// suffix test, neither of which asks where the path is.
//
// It is not only the hostile case. Manifest paths are absolute, so a manifest committed from one
// machine names *that* machine's directories; a teammate on a shared-path machine — a container, a
// `/workspace` checkout, the same username — running `--uninstall` deletes them by name.

/** Keys of `codexPaths()` that are not filesystem paths, and so cannot bound a deletion. */
const NOT_A_PATH = new Set(["kind", "referencesRef"]);

/**
 * A path in the only form containment can be decided on: absolute, `..` collapsed, symlinks
 * followed as far as the filesystem actually goes, and — on Windows — spelled the way the volume
 * spells it, drive letter included.
 *
 * Neither half is sufficient alone. `resolve` is purely lexical, so a symlink sitting inside an
 * install root and pointing anywhere at all passes through it unchanged. `realpathSync` throws for
 * a path that is not on disk, and both a manifest entry for a file already gone and a root that
 * was never created are ordinary. So the deepest ancestor that does exist is resolved for real,
 * and the remainder — which cannot be a symlink, because it does not exist — is joined back on.
 *
 * Roots and candidates go through this same function, which is what keeps a home directory that is
 * itself a symlink (a dotfiles farm does this) from refusing every legitimate removal.
 */
function canonicalPath(value) {
  if (typeof value !== "string" || !value) return null;
  let head;
  try {
    head = resolve(value);
  } catch {
    return null;
  }
  const tail = [];
  for (;;) {
    try {
      return join(realpathSync.native(head), ...tail);
    } catch {
      const parent = dirname(head);
      // A volume root is its own parent on every platform, so this terminates. Reaching it means
      // nothing on the branch exists: the lexical form is the best available, and it is applied to
      // both sides of the comparison, so the two stay comparable.
      if (parent === head) return resolve(value);
      tail.unshift(basename(head));
      head = parent;
    }
  }
}

/**
 * Is `candidate` the root itself, or something beneath it?
 *
 * A `startsWith` on the two strings is not this test, and cardinal 8 is why: `<root>-evil` starts
 * with `<root>` and is not inside it, Windows spells the separator the other way, and its drive
 * letter comes back in either case. `relative` knows all three — `""` for the root itself, a path
 * beginning with `..` for anything above it, an absolute path when the two sit on different
 * volumes. The `..` test is anchored on the separator on purpose: a sibling directory named
 * `..cache` inside the root yields `..cache`, which a bare `startsWith("..")` would refuse.
 */
function isInside(root, candidate) {
  const rel = relative(root, candidate);
  if (rel === "") return true;
  if (isAbsolute(rel)) return false;
  return rel !== ".." && !rel.startsWith(`..${sep}`);
}

/**
 * The directories one uninstall target is allowed to touch: every destination `codexPaths()` named
 * for that scope, and nothing else.
 *
 * Derived from the target rather than written out, so a seventh surface added to `codexPaths()` is
 * bounded here without a second edit — the divergence this repository exists to end.
 *
 * `projectDir` itself is deliberately *not* a root. The manifest is a committable file inside the
 * project it describes, so admitting the whole repository would leave `.git` in the blast radius of
 * a path anybody can send in a pull request. Everything the project half writes and records already
 * lives under one of the paths below; the rule templates are `adopted`, and never deleted at all.
 *
 * An empty list is a refusal of everything, which is the intended direction: a root that cannot be
 * resolved must not be read as permission.
 */
function installRoots(target) {
  const roots = [];
  for (const [key, value] of Object.entries(target)) {
    if (NOT_A_PATH.has(key)) continue;
    const root = canonicalPath(value);
    if (root) roots.push(root);
  }
  return roots;
}

/**
 * Remove exactly what a previous run recorded — in both scopes.
 *
 * There are two manifests, because there are two halves: the global one in the Codex home and the
 * project one. An uninstall that reads only one leaves the other half installed while reporting
 * success, which is how a "clean" machine keeps running old hooks.
 */
export function uninstall({ projectDir, scope = "all", dryRun = false, log = () => {} }) {
  const targets = [];
  if (scope !== "project") targets.push({ kind: "global", ...codexPaths("user", projectDir) });
  if (scope !== "user") {
    targets.push({
      kind: "project",
      ...codexPaths("project", projectDir),
      manifest: join(projectDir, MANIFEST),
    });
  }

  const removed = [];
  for (const target of targets) {
    const manifest = readJson(target.manifest);
    if (!manifest) {
      log(`${target.kind}: no manifest — nothing recorded, nothing removed`);
      continue;
    }

    // Hooks: subtract only the entries we added. Another tool writes this file too.
    const existing = readJson(target.hooks);
    if (existing) {
      const cleaned = unmergeHooks(existing, manifest.hookCommands ?? []);
      log(target.hooks);
      if (!dryRun) writeFile(target.hooks, `${JSON.stringify(cleaned, null, 2)}\n`);
    }

    for (const path of manifest.adopted ?? []) {
      if (existsSync(path)) log(`${path} — kept: adapted by this project, not ours to delete`);
    }

    // The roots this scope installed into, resolved once per target.
    const roots = installRoots(target);

    for (const path of manifest.paths ?? []) {
      if (path === target.hooks) continue;

      // Before anything below is allowed to write to this path or delete it. The two branches that
      // follow both act on it — one rewrites a file, the other removes a tree recursively — and
      // neither of their own filters asks where the path is. This one does, and a path that is not
      // under something this scope installed into is refused and the removal carries on.
      const canonical = canonicalPath(path);
      if (!canonical || !roots.some((root) => isInside(root, canonical))) {
        log(`${path} — refused: outside every directory this install writes to`);
        continue;
      }

      if (path.endsWith("AGENTS.md")) {
        const text = existsSync(path) ? readFileSync(path, "utf8") : "";
        const a = text.indexOf(MARKER_START);
        const b = text.indexOf(MARKER_END);
        if (a !== -1 && b !== -1) {
          log(`${path} (block removed)`);
          if (!dryRun)
            writeFile(path, `${(text.slice(0, a) + text.slice(b + MARKER_END.length)).trim()}\n`);
        }
        continue;
      }

      // Never delete a directory that other tools share. `~/.agents/skills` holds whatever else
      // the person installed; only the specific skill folders below it are ours.
      if (/(^|[\\/])(\.agents|skills|\.codex|agents)$/.test(path)) {
        log(`${path} — refused: shared directory, not ours to delete`);
        continue;
      }
      if (!existsSync(path)) continue;
      log(path);
      if (!dryRun) rmSync(path, { recursive: true, force: true });
      removed.push(path);
    }

    if (!dryRun) rmSync(target.manifest, { force: true });
  }

  // Prune only directories we created, and only when nothing else moved in.
  for (const dir of [
    join(projectDir, ".codex/agents"),
    join(projectDir, ".codex/graph-powers"),
    join(projectDir, ".codex/rules"),
    join(projectDir, ".graph-powers"),
    join(codexPaths("user", projectDir).references),
    join(codexPaths("user", projectDir).agents),
  ]) {
    try {
      if (existsSync(dir) && readdirSync(dir).length === 0 && !dryRun)
        rmSync(dir, { recursive: true });
    } catch {
      /* non-empty or unreadable stays — never guess here */
    }
  }
  return removed;
}

// ── CLI ──────────────────────────────────────────────────────────────────────

if (process.argv[1] && resolve(process.argv[1]) === resolve(fileURLToPath(import.meta.url))) {
  const argv = process.argv.slice(2);
  const value = (flag, fallback) => {
    const i = argv.indexOf(flag);
    return i !== -1 && argv[i + 1] && !argv[i + 1].startsWith("-") ? argv[i + 1] : fallback;
  };
  const opts = {
    projectDir: resolve(value("--project", process.cwd())),
    pluginRoot: resolve(
      value("--plugin", join(fileURLToPath(new URL(".", import.meta.url)), "..")),
    ),
    scope: value("--scope", "user"),
    dryRun: argv.includes("--dry-run"),
    // `install()` and `installGlobal()` have honoured `force` since they were written; the argv
    // parser never set it, so `--force` on the command line did nothing at all — including in the
    // CI fixture, whose second install was proving idempotence it had not actually exercised.
    // It is the only way to repair a global install whose plugin root moved without a version bump.
    force: argv.includes("--force"),
    log: (p) => console.log(`  ${p}`),
  };
  // The project's own model tiers, so a direct `node codex/install.mjs` generates what the
  // `graph-powers` CLI generates rather than twelve subagents with no model at all.
  opts.codex = readCodexSettings(opts.projectDir);
  if (argv.includes("--uninstall")) {
    // Removal defaults to both halves. `--scope` on an install says where to write; on a removal
    // it would say what to leave behind, and "uninstalled" that leaves half the artefacts running
    // is the state this manifest exists to make impossible.
    uninstall({ ...opts, scope: argv.includes("--scope") ? opts.scope : "all" });
  } else {
    install(opts);
  }
}
