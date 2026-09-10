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

function configSyntaxConflict(text) {
  // This editor only owns bare table/key lines, not the full TOML grammar. Refuse
  // ambiguous structure; broader support needs a TOML parser with lossless edits.
  let multiline = false;
  const structure = text.replace(
    /"""|'''|"(?:\\[^\r\n]|[^"\\\r\n])*"|'[^'\r\n]*'|#[^\r\n]*/g,
    (token) => {
      if (token === '"""' || token === "'''") multiline = true;
      return token.startsWith("#") ? "" : "@";
    },
  );
  const conflict =
    "TOML structure cannot be safely edited; use bare tables/keys and single-line strings";
  if (multiline || /["']/.test(structure)) return conflict;

  const namespaces = new Set(["ui", "features", "subagents", "plugins", "marketplace"]);
  const scalarKeys = new Set(["ui.permission_mode", "features.web_fetch", "subagents.enabled"]);
  let table = "";
  let arrayDepth = 0;
  for (const line of structure.split(/\r?\n/)) {
    let content = line.trim();
    if (!content) continue;
    if (arrayDepth === 0) {
      if (content.startsWith("[")) {
        const header = /^(\[\[?)([A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*)(\]\]?)$/.exec(content);
        if (!header || header[1].length !== header[3].length) return conflict;
        table = header[2];
        const namespace = table.split(".")[0];
        if (
          namespaces.has(namespace) &&
          !(table === namespace && header[1] === "[") &&
          !((table === "subagents.models" || table === "subagents.toggle") && header[1] === "[") &&
          !(table === "marketplace.sources" && header[1] === "[[")
        ) {
          return conflict;
        }
        continue;
      }
      const assignment = /^([A-Za-z0-9_-]+)[\t ]*=[\t ]*(.+)$/.exec(content);
      if (!assignment) return conflict;
      const [, key, value] = assignment;
      if (!table && namespaces.has(key)) return conflict;
      if (table === "marketplace" && key === "sources") return conflict;
      if (namespaces.has(table.split(".")[0]) && value.includes("{")) return conflict;
      if (scalarKeys.has(`${table}.${key}`) && value.includes("[")) return conflict;
      content = value;
    }
    arrayDepth += (content.match(/\[/g) || []).length - (content.match(/\]/g) || []).length;
    if (arrayDepth < 0) return conflict;
  }
  return arrayDepth === 0 ? null : conflict;
}

function tableSpan(text, table) {
  const re = new RegExp(`^[\\t ]*\\[${escapeRe(table)}\\][\\t ]*(?:#.*)?\\r?$`, "m");
  const match = re.exec(text);
  if (!match) return null;
  const start = match.index + match[0].length;
  const rest = text.slice(start);
  const next = rest.search(/^[\t ]*(?:\[\[[^\]\r\n]+\]\]|\[[^\]\r\n]+\])[\t ]*(?:#.*)?\r?$/m);
  const end = next === -1 ? text.length : start + next;
  return { start, end };
}

function setTableKey(text, table, key, value) {
  const formatted = `${key} = ${tomlLiteral(value)}`;
  const newline = text.includes("\r\n") ? "\r\n" : "\n";
  const span = tableSpan(text, table);
  if (!span) {
    const separator = text && !text.endsWith(newline) ? newline : "";
    const blank = text ? newline : "";
    return {
      text: `${text}${separator}${blank}[${table}]${newline}${formatted}${newline}`,
      changed: true,
    };
  }
  const body = text.slice(span.start, span.end);
  const keyRe = new RegExp(`^([\\t ]*)${escapeRe(key)}[\\t ]*=.*?(\\r?)$`, "m");
  const keyMatch = keyRe.exec(body);
  if (keyMatch) {
    const content = keyMatch[2] ? keyMatch[0].slice(0, -keyMatch[2].length) : keyMatch[0];
    const comment = content.match(/([\t ]+#.*)$/)?.[1] ?? "";
    const nextBody = body.replace(keyRe, `${keyMatch[1]}${formatted}${comment}${keyMatch[2]}`);
    if (nextBody === body) return { text, changed: false };
    return { text: text.slice(0, span.start) + nextBody + text.slice(span.end), changed: true };
  }
  const insert = `${body.endsWith(newline) ? "" : newline}${formatted}${newline}`;
  return {
    text: `${text.slice(0, span.end)}${insert}${text.slice(span.end)}`,
    changed: true,
  };
}

function parseStringArray(raw) {
  const out = [];
  let index = 0;
  let expectingValue = true;

  const skipWhitespaceAndComments = () => {
    while (index < raw.length) {
      if (/\s/.test(raw[index])) {
        index += 1;
      } else if (raw[index] === "#") {
        const nextLine = raw.indexOf("\n", index);
        index = nextLine === -1 ? raw.length : nextLine + 1;
      } else {
        break;
      }
    }
  };

  skipWhitespaceAndComments();
  if (raw[index] !== "[") return null;
  index += 1;
  while (true) {
    skipWhitespaceAndComments();
    if (raw[index] === "]") return out;
    if (!expectingValue) {
      if (raw[index] !== ",") return null;
      index += 1;
      expectingValue = true;
      continue;
    }
    const quote = raw[index];
    if (quote !== '"' && quote !== "'") return null;
    const valueStart = index;
    index += 1;
    let escaped = false;
    while (index < raw.length) {
      const character = raw[index];
      if (quote === '"' && escaped) escaped = false;
      else if (quote === '"' && character === "\\") escaped = true;
      else if (character === quote) break;
      index += 1;
    }
    if (index >= raw.length) return null;
    const encoded = raw.slice(valueStart, index + 1);
    try {
      out.push(quote === '"' ? JSON.parse(encoded) : encoded.slice(1, -1));
    } catch {
      return null;
    }
    index += 1;
    expectingValue = false;
  }
}

function arrayValueSpan(body, key) {
  const keyRe = new RegExp(`^([\\t ]*)${escapeRe(key)}[\\t ]*=[\\t ]*`, "m");
  const keyMatch = keyRe.exec(body);
  if (!keyMatch) return null;
  const arrayStart = keyMatch.index + keyMatch[0].length;
  if (body[arrayStart] !== "[") return { malformed: true };
  let quote = null;
  let escaped = false;
  let depth = 0;
  for (let i = arrayStart; i < body.length; i += 1) {
    const character = body[i];
    if (quote) {
      if (quote === '"' && escaped) escaped = false;
      else if (quote === '"' && character === "\\") escaped = true;
      else if (character === quote) quote = null;
      continue;
    }
    if (character === '"' || character === "'") {
      quote = character;
      continue;
    }
    if (character === "#") {
      const nextLine = body.indexOf("\n", i);
      if (nextLine === -1) break;
      i = nextLine;
      continue;
    }
    if (character === "[") depth += 1;
    if (character === "]") {
      depth -= 1;
      if (depth === 0) {
        const lineEnd = body.indexOf("\n", i);
        const end = lineEnd === -1 ? body.length : lineEnd;
        const trailing = body.slice(i + 1, end);
        if (!/^[\t ]*(?:#.*)?\r?$/.test(trailing)) return { malformed: true };
        return {
          start: keyMatch.index,
          end,
          indent: keyMatch[1],
          raw: body.slice(arrayStart, i + 1),
          trailing,
        };
      }
    }
  }
  return { malformed: true };
}

function removeStringFromArrayKey(text, table, key, item) {
  const span = tableSpan(text, table);
  if (!span) return { text, changed: false };
  const body = text.slice(span.start, span.end);
  const value = arrayValueSpan(body, key);
  if (!value) return { text, changed: false };
  if (value.malformed)
    return { text, changed: false, error: `${table}.${key} cannot be safely read` };
  const current = parseStringArray(value.raw);
  if (!current) return { text, changed: false, error: `${table}.${key} cannot be safely read` };
  const next = current.filter((entry) => entry !== item);
  if (next.length === current.length) return { text, changed: false };
  const formatted = `${value.indent}${key} = ${tomlLiteral(next)}${value.trailing}`;
  const nextBody = body.slice(0, value.start) + formatted + body.slice(value.end);
  return { text: text.slice(0, span.start) + nextBody + text.slice(span.end), changed: true };
}

function mergeStringArrayKey(text, table, key, extra) {
  const span = tableSpan(text, table);
  if (!span) return setTableKey(text, table, key, extra);
  const body = text.slice(span.start, span.end);
  const value = arrayValueSpan(body, key);
  if (!value) return setTableKey(text, table, key, extra);
  if (value.malformed)
    return { text, changed: false, error: `${table}.${key} cannot be safely read` };
  const current = parseStringArray(value.raw);
  if (!current) return { text, changed: false, error: `${table}.${key} cannot be safely read` };
  const next = [...current];
  let changed = false;
  for (const item of extra) {
    if (!next.includes(item)) {
      next.push(item);
      changed = true;
    }
  }
  if (!changed) return { text, changed: false };
  const formatted = `${value.indent}${key} = ${tomlLiteral(next)}${value.trailing}`;
  const nextBody = body.slice(0, value.start) + formatted + body.slice(value.end);
  return { text: text.slice(0, span.start) + nextBody + text.slice(span.end), changed: true };
}

function stringArrayValue(text, table, key) {
  const span = tableSpan(text, table);
  if (!span) return { values: [] };
  const value = arrayValueSpan(text.slice(span.start, span.end), key);
  if (!value) return { values: [] };
  if (value.malformed) return { error: `${table}.${key} cannot be safely read` };
  const values = parseStringArray(value.raw);
  return values ? { values } : { error: `${table}.${key} cannot be safely read` };
}

function ensureMarketplaceSource(text, { name, git }) {
  const nameRe = new RegExp(`name\\s*=\\s*"${escapeRe(name)}"`);
  if (nameRe.test(text)) return { text, changed: false };
  const block = `\n[[marketplace.sources]]\nname = ${tomlLiteral(name)}\ngit = ${tomlLiteral(git)}\n`;
  return { text: text.trimEnd() + block, changed: true };
}

export function mergeGrokConfig(current, { autonomous, pluginRoot, forgetClone = false } = {}) {
  let text = typeof current === "string" ? current : "";
  const original = text;
  const changed = [];
  const conflicts = [];
  const syntaxConflict = configSyntaxConflict(text);
  if (syntaxConflict) return { next: original, changed, conflicts: [syntaxConflict] };

  const disabled = stringArrayValue(text, "plugins", "disabled");
  if (disabled.error) conflicts.push(disabled.error);
  if (disabled.values?.includes("graph-powers")) {
    conflicts.push("plugins.disabled contains graph-powers");
  }

  if (autonomous) {
    const mode = setTableKey(text, "ui", "permission_mode", "always-approve");
    if (mode.changed) changed.push("ui.permission_mode");
    text = mode.text;

    const fetch = setTableKey(text, "features", "web_fetch", true);
    if (fetch.changed) changed.push("features.web_fetch");
    text = fetch.text;
  }

  const sub = setTableKey(text, "subagents", "enabled", true);
  if (sub.changed) changed.push("subagents.enabled");
  text = sub.text;

  if (!conflicts.some((conflict) => conflict.startsWith("plugins.disabled"))) {
    const enabled = mergeStringArrayKey(text, "plugins", "enabled", ["graph-powers"]);
    if (enabled.error) conflicts.push(enabled.error);
    if (enabled.changed) changed.push("plugins.enabled");
    text = enabled.text;
  }

  if (pluginRoot && forgetClone) {
    const paths = removeStringFromArrayKey(text, "plugins", "paths", pluginRoot);
    if (paths.error) conflicts.push(paths.error);
    if (paths.changed) changed.push("plugins.paths");
    text = paths.text;
  } else if (pluginRoot) {
    const paths = mergeStringArrayKey(text, "plugins", "paths", [pluginRoot]);
    if (paths.error) conflicts.push(paths.error);
    if (paths.changed) changed.push("plugins.paths");
    text = paths.text;
  }

  const source = ensureMarketplaceSource(text, { name: "graph-powers", git: MARKETPLACE_GIT });
  if (source.changed) changed.push("marketplace.sources");
  text = source.text;

  if (conflicts.length) return { next: original, changed: [], conflicts };
  if (text.length && !text.endsWith("\n")) text += "\n";
  return { next: text, changed, conflicts };
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

  const home = process.env.GROK_HOME || join(homedir(), ".grok");
  const configFile = join(home, "config.toml");
  const current = !emitOnly && existsSync(configFile) ? readFileSync(configFile, "utf8") : "";
  const { next, changed, conflicts } = mergeGrokConfig(current, {
    autonomous,
    pluginRoot,
    forgetClone: !discoverClone,
  });
  if (conflicts.length) {
    throw new Error(
      `Grok config conflicts with ${autonomous ? "autonomous" : "guarded"} posture (${conflicts.join(", ")}); config.toml was not changed`,
    );
  }

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

  if (!dryRun && !verified) {
    const proof = verifyHookClient({
      client: "grok",
      pluginRoot,
      packageRoot: pluginRoot,
      projectDir: process.cwd(),
      autonomy: autonomous ? "autonomous" : "guarded",
      requireGrokRuntime: autonomous,
      probe: true,
    });
    if (!proof.ok) {
      throw new Error(
        `Grok hook package verification failed; ${autonomous ? "always-approve posture" : "guarded configuration"} was not changed: ${proofFailure(proof)}`,
      );
    }
  }

  if (changed.length) {
    if (dryRun) log(`(dry-run) would write ${configFile}: ${changed.join(", ")}`);
    else {
      writeFile(configFile, next);
      written.push(configFile);
    }
  } else {
    log(`Grok config.toml already matches ${autonomous ? "autonomous" : "guarded"} posture`);
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
