#!/usr/bin/env node
/**
 * Generate the Grok CLI side of Graph Powers from the Claude Code artefacts.
 *
 *   node grok/install.mjs [--plugin <dir>] [--emit] [--emit-only] [--dry-run] [--guarded]
 *
 * Grok is the fourth harness. Cardinal 7 still holds: Grok reads `hooks/hooks.json` in the
 * same nested Claude shape, and it sets `CLAUDE_PLUGIN_ROOT` as an alias of `GROK_PLUGIN_ROOT`.
 * There is no second hook list. This file writes:
 *
 *   .grok-plugin/plugin.json        <- .claude-plugin/plugin.json
 *   .grok-plugin/marketplace.json   <- .claude-plugin/marketplace.json
 *   ~/.grok/config.toml             <- autonomy.level (permission_mode, marketplace, plugin path)
 *
 * Do not also write ~/.grok/hooks/*.json. That is how native plugin hooks and a clone copy
 * run twice. Point Grok at the plugin directory; let hooks/hooks.json be the one source.
 *
 * Do not write `[permission] deny` for git commit/push. The Python gates own that, and a TOML
 * deny would block the opt-in key. `permission_mode = "always-approve"` is the confirmation
 * lever; PreToolUse deny still blocks. Project `.grok/config.toml` cannot set permission_mode —
 * that key is user config only (`~/.grok/config.toml` or `$GROK_HOME/config.toml`).
 *
 * User files are merged, never replaced. A permission list is somebody's decision. A standalone
 * autonomous run first calls the shared verifier against this exact package root; `--emit-only`
 * remains a pure generator and writes no posture.
 */

import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { readJson, writeFile } from "../codex/lib.mjs";
import { proofFailure, verifyHookClient } from "../bin/hook-client-verifier.mjs";

const HERE = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const MARKETPLACE_GIT = "https://github.com/GrupoUS/graph-powers.git";

function pluginRootFromArgv(argv) {
  const i = argv.indexOf("--plugin");
  if (i !== -1 && argv[i + 1] && !argv[i + 1].startsWith("-")) return resolve(argv[i + 1]);
  return HERE;
}

function escapeRe(s) {
  return String(s).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function buildPluginManifest(claudeManifest) {
  return {
    name: claudeManifest.name,
    displayName: claudeManifest.displayName ?? "Graph Powers",
    description: claudeManifest.description,
    version: claudeManifest.version,
    author: claudeManifest.author,
    homepage: claudeManifest.homepage,
    repository: claudeManifest.repository,
    license: claudeManifest.license,
    keywords: [...new Set([...(claudeManifest.keywords ?? []), "grok"])],
    skills: "./skills/",
    agents: "./agents/",
    commands: "./commands/",
    hooks: "./hooks/hooks.json",
  };
}

export function buildMarketplace(claudeMarketplace) {
  return {
    name: claudeMarketplace.name ?? "graph-powers",
    description: claudeMarketplace.description,
    owner: claudeMarketplace.owner,
    plugins: (claudeMarketplace.plugins ?? []).map((plugin) =>
      Object.assign({}, plugin, { source: plugin.source ?? "./" }),
    ),
  };
}

function tomlLiteral(value) {
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") return String(value);
  if (Array.isArray(value)) {
    return `[${value.map((v) => (typeof v === "string" ? JSON.stringify(v) : tomlLiteral(v))).join(", ")}]`;
  }
  return JSON.stringify(String(value));
}

function tableSpan(text, table) {
  const re = new RegExp(`^\\[${escapeRe(table)}\\]\\s*$`, "m");
  const match = re.exec(text);
  if (!match) return null;
  const start = match.index + match[0].length;
  const rest = text.slice(start);
  const next = rest.search(/^\s*\[/m);
  const end = next === -1 ? text.length : start + next;
  return { start, end };
}

function setTableKey(text, table, key, value) {
  const formatted = `${key} = ${tomlLiteral(value)}`;
  const span = tableSpan(text, table);
  if (!span) {
    const block = `\n[${table}]\n${formatted}\n`;
    return { text: `${text.trimEnd()}${block}`, changed: true };
  }
  const body = text.slice(span.start, span.end);
  const keyRe = new RegExp(`^${escapeRe(key)}\\s*=\\s*.*$`, "m");
  if (keyRe.test(body)) {
    const nextBody = body.replace(keyRe, formatted);
    if (nextBody === body) return { text, changed: false };
    return { text: text.slice(0, span.start) + nextBody + text.slice(span.end), changed: true };
  }
  const insert = `\n${formatted}`;
  return {
    text: `${text.slice(0, span.end).replace(/\s*$/, "")}${insert}\n${text.slice(span.end)}`,
    changed: true,
  };
}

function parseStringArray(raw) {
  const inner = raw.replace(/^\s*\[/, "").replace(/\]\s*$/, "");
  if (!inner.trim()) return [];
  const out = [];
  const re = /"((?:\\.|[^"\\])*)"|'((?:\\.|[^'\\])*)'/g;
  let match = re.exec(inner);
  while (match) {
    out.push((match[1] ?? match[2]).replace(/\\"/g, '"'));
    match = re.exec(inner);
  }
  return out;
}

function removeStringFromArrayKey(text, table, key, item) {
  const span = tableSpan(text, table);
  if (!span) return { text, changed: false };
  const body = text.slice(span.start, span.end);
  const keyRe = new RegExp(`^${escapeRe(key)}\\s*=\\s*(\\[[\\s\\S]*?\\])`, "m");
  const match = keyRe.exec(body);
  if (!match) return { text, changed: false };
  const current = parseStringArray(match[1]);
  const next = current.filter((entry) => entry !== item);
  if (next.length === current.length) return { text, changed: false };
  const formatted = `${key} = ${tomlLiteral(next)}`;
  const nextBody = body.replace(keyRe, formatted);
  return { text: text.slice(0, span.start) + nextBody + text.slice(span.end), changed: true };
}

function mergeStringArrayKey(text, table, key, extra) {
  const span = tableSpan(text, table);
  if (!span) return setTableKey(text, table, key, extra);
  const body = text.slice(span.start, span.end);
  const keyRe = new RegExp(`^${escapeRe(key)}\\s*=\\s*(\\[[\\s\\S]*?\\])`, "m");
  const match = keyRe.exec(body);
  if (!match) return setTableKey(text, table, key, extra);
  const current = parseStringArray(match[1]);
  const next = [...current];
  let changed = false;
  for (const item of extra) {
    if (!next.includes(item)) {
      next.push(item);
      changed = true;
    }
  }
  if (!changed) return { text, changed: false };
  const formatted = `${key} = ${tomlLiteral(next)}`;
  const nextBody = body.replace(keyRe, formatted);
  return { text: text.slice(0, span.start) + nextBody + text.slice(span.end), changed: true };
}

function ensureMarketplaceSource(text, { name, git }) {
  const nameRe = new RegExp(`name\\s*=\\s*"${escapeRe(name)}"`);
  if (nameRe.test(text)) return { text, changed: false };
  const block = `\n[[marketplace.sources]]\nname = ${tomlLiteral(name)}\ngit = ${tomlLiteral(git)}\n`;
  return { text: text.trimEnd() + block, changed: true };
}

export function mergeGrokConfig(current, { autonomous, pluginRoot, forgetClone = false } = {}) {
  let text = typeof current === "string" ? current : "";
  const changed = [];

  if (autonomous) {
    const mode = setTableKey(text, "ui", "permission_mode", "always-approve");
    if (mode.changed) changed.push("ui.permission_mode");
    text = mode.text;

    const fetch = setTableKey(text, "features", "web_fetch", true);
    if (fetch.changed) changed.push("features.web_fetch");
    text = fetch.text;

    const sub = setTableKey(text, "subagents", "enabled", true);
    if (sub.changed) changed.push("subagents.enabled");
    text = sub.text;
  }

  const enabled = mergeStringArrayKey(text, "plugins", "enabled", ["graph-powers"]);
  if (enabled.changed) changed.push("plugins.enabled");
  text = enabled.text;

  if (pluginRoot && forgetClone) {
    const paths = removeStringFromArrayKey(text, "plugins", "paths", pluginRoot);
    if (paths.changed) changed.push("plugins.paths");
    text = paths.text;
  } else if (pluginRoot) {
    const paths = mergeStringArrayKey(text, "plugins", "paths", [pluginRoot]);
    if (paths.changed) changed.push("plugins.paths");
    text = paths.text;
  }

  const source = ensureMarketplaceSource(text, { name: "graph-powers", git: MARKETPLACE_GIT });
  if (source.changed) changed.push("marketplace.sources");
  text = source.text;

  if (text.length && !text.endsWith("\n")) text += "\n";
  return { next: text, changed };
}

export function install({
  pluginRoot = HERE,
  dryRun = false,
  autonomous = true,
  emit = false,
  emitOnly = false,
  discoverClone = true,
  verified = false,
  log = () => {},
} = {}) {
  const written = [];
  const claudeManifest = readJson(join(pluginRoot, ".claude-plugin/plugin.json"), {});
  const claudeMarketplace = readJson(join(pluginRoot, ".claude-plugin/marketplace.json"), {});
  const pluginManifest = buildPluginManifest(claudeManifest);
  const marketplace = buildMarketplace(claudeMarketplace);

  if (emit) {
    const manifestPath = join(pluginRoot, ".grok-plugin/plugin.json");
    const marketPath = join(pluginRoot, ".grok-plugin/marketplace.json");
    if (dryRun) {
      log(`(dry-run) would emit ${manifestPath}`);
      log(`(dry-run) would emit ${marketPath}`);
    } else {
      writeFile(manifestPath, `${JSON.stringify(pluginManifest, null, 2)}\n`);
      writeFile(marketPath, `${JSON.stringify(marketplace, null, 2)}\n`);
      written.push(manifestPath, marketPath);
    }
  }

  if (emitOnly) return { written, configChanged: [] };

  if (autonomous && !dryRun && !verified) {
    const proof = verifyHookClient({
      client: "grok",
      pluginRoot,
      packageRoot: pluginRoot,
      projectDir: process.cwd(),
      autonomy: "autonomous",
      probe: true,
    });
    if (!proof.ok) {
      throw new Error(
        `Grok hook package verification failed; always-approve posture was not changed: ${proofFailure(proof)}`,
      );
    }
  }

  const home = process.env.GROK_HOME || join(homedir(), ".grok");
  const configFile = join(home, "config.toml");
  const current = existsSync(configFile) ? readFileSync(configFile, "utf8") : "";
  const { next, changed } = mergeGrokConfig(current, {
    autonomous,
    pluginRoot,
    forgetClone: !discoverClone,
  });

  if (changed.length) {
    if (dryRun) log(`(dry-run) would write ${configFile}: ${changed.join(", ")}`);
    else {
      writeFile(configFile, next);
      written.push(configFile);
    }
  } else {
    log("Grok config.toml already matches autonomous posture");
  }
  return { written, configChanged: changed };
}

function main() {
  const argv = process.argv.slice(2);
  const dryRun = argv.includes("--dry-run");
  const emitOnly = argv.includes("--emit-only");
  const emit = argv.includes("--emit") || emitOnly;
  const pluginRoot = pluginRootFromArgv(argv);
  const result = install({
    pluginRoot,
    dryRun,
    emit,
    emitOnly,
    autonomous: !argv.includes("--guarded"),
    discoverClone: !argv.includes("--no-clone-path"),
    log: (m) => console.log(`  ${m}`),
  });
  if (!dryRun && result.written.length) {
    console.log(`grok: ${result.written.length} path(s) written`);
  }
}

const invoked = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invoked) {
  try {
    main();
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  }
}
