#!/usr/bin/env node
/**
 * Generate the Codex native-plugin side from the Claude Code artefacts.
 *
 *   node codex/native-plugin.mjs [--plugin <dir>] [--emit-only] [--dry-run]
 *
 * Codex discovers `.codex-plugin/plugin.json` before `.claude-plugin/plugin.json`. Without
 * this file it loaded `agents/*.md` as-is, including `model: haiku` / `model: opus`. Those
 * are Claude families. Codex has no haiku; the cheap-model fallback is Spark, whose rate-limit
 * bucket is `codex_bengalfox` ("Bengal Fox") — not the user's own Codex/Pro window.
 *
 * Native agents are the same markdown with Claude model lines removed, so the child inherits
 * the session model (and that session's limit). Effort stays in frontmatter and still travels
 * through the clone generator as `model_reasoning_effort`.
 *
 *   .codex-plugin/plugin.json           <- .claude-plugin/plugin.json
 *   .codex-plugin/marketplace.json      <- .claude-plugin/marketplace.json
 *   codex/native-agents/<name>.md       <- agents/<name>.md (Claude model family stripped)
 */

import { existsSync, readdirSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { CLAUDE_MODEL_FAMILIES } from "./install.mjs";
import { readJson, writeFile } from "./lib.mjs";

const HERE = resolve(dirname(fileURLToPath(import.meta.url)), "..");
export const NATIVE_AGENTS_DIR = "codex/native-agents";

function pluginRootFromArgv(argv) {
  const i = argv.indexOf("--plugin");
  if (i !== -1 && argv[i + 1] && !argv[i + 1].startsWith("-")) return resolve(argv[i + 1]);
  return HERE;
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
    keywords: [...new Set([...(claudeManifest.keywords ?? []), "codex"])],
    skills: "./skills/",
    agents: `./${NATIVE_AGENTS_DIR}/`,
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

/**
 * Drop `model: haiku|sonnet|opus|fable` from YAML frontmatter. Quoted forms too.
 * Anything else, including a real Codex slug a project might add later, is left alone.
 */
export function stripClaudeModelLine(markdown) {
  const names = [...CLAUDE_MODEL_FAMILIES].join("|");
  const re = new RegExp(
    `^model:\\s*["']?(?:${names})["']?\\s*(?:#.*)?\\r?\\n`,
    "gim",
  );
  return String(markdown).replace(re, "");
}

export function listAgentFiles(pluginRoot) {
  const dir = join(pluginRoot, "agents");
  if (!existsSync(dir)) return [];
  return readdirSync(dir).filter((f) => f.endsWith(".md")).sort();
}

export function buildNativeAgents(pluginRoot) {
  const files = {};
  for (const file of listAgentFiles(pluginRoot)) {
    const src = readFileSync(join(pluginRoot, "agents", file), "utf8");
    files[file] = stripClaudeModelLine(src);
  }
  return files;
}

export function install({
  pluginRoot = HERE,
  dryRun = false,
  emit = false,
  emitOnly = false,
  log = () => {},
} = {}) {
  const written = [];
  const claudeManifest = readJson(join(pluginRoot, ".claude-plugin/plugin.json"), {});
  const claudeMarketplace = readJson(join(pluginRoot, ".claude-plugin/marketplace.json"), {});
  const pluginManifest = buildPluginManifest(claudeManifest);
  const marketplace = buildMarketplace(claudeMarketplace);
  const agents = buildNativeAgents(pluginRoot);

  if (emit || emitOnly) {
    const paths = [
      [join(pluginRoot, ".codex-plugin/plugin.json"), `${JSON.stringify(pluginManifest, null, 2)}\n`],
      [join(pluginRoot, ".codex-plugin/marketplace.json"), `${JSON.stringify(marketplace, null, 2)}\n`],
      ...Object.entries(agents).map(([file, body]) => [
        join(pluginRoot, NATIVE_AGENTS_DIR, file),
        body.endsWith("\n") ? body : `${body}\n`,
      ]),
    ];
    for (const [path, contents] of paths) {
      if (dryRun) {
        log(`(dry-run) would emit ${path}`);
        continue;
      }
      writeFile(path, contents);
      written.push(path);
      log(path);
    }
  }

  return { written, pluginManifest, marketplace, agents };
}

if (process.argv[1] && resolve(process.argv[1]) === resolve(fileURLToPath(import.meta.url))) {
  const argv = process.argv.slice(2);
  const result = install({
    pluginRoot: pluginRootFromArgv(argv),
    dryRun: argv.includes("--dry-run"),
    emit: true,
    emitOnly: true,
    log: (m) => console.log(`  ${m}`),
  });
  if (!argv.includes("--dry-run") && result.written.length) {
    console.log(`codex-native: ${result.written.length} path(s) written`);
  }
}
