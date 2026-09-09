#!/usr/bin/env node
/**
 * Generate and verify the Hermes side of Graph Powers from the Claude source tree.
 *
 *   bun hermes/install.mjs --check
 *   bun hermes/install.mjs --emit-only
 *
 * Hermes has one native manifest, `plugin.yaml`, and one Python entrypoint. The entrypoint
 * discovers skills, command documents, and agent contracts from the repository directories; this
 * generator checks that projection without maintaining a second inventory. Claude hooks are not
 * translated because Hermes does not expose the verified payload contract needed for the Graph
 * Powers git rails.
 */

import { chmodSync, existsSync, readdirSync, readFileSync, statSync, lstatSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";

import { readJson, writeFile } from "../codex/lib.mjs";

const HERE = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const MANIFEST = "plugin.yaml";

function pluginRootFromArgv(argv) {
  const index = argv.indexOf("--plugin");
  if (index !== -1 && argv[index + 1] && !argv[index + 1].startsWith("-")) {
    return resolve(argv[index + 1]);
  }
  return HERE;
}

function yamlString(value) {
  return JSON.stringify(String(value ?? ""));
}

function requiredClaudeManifest(pluginRoot) {
  const path = join(pluginRoot, ".claude-plugin/plugin.json");
  const manifest = readJson(path, null);
  if (!manifest || typeof manifest !== "object") {
    throw new Error(`cannot read Claude manifest at ${path}`);
  }
  for (const field of ["name", "version", "description"]) {
    if (!manifest[field]) throw new Error(`Claude manifest is missing ${field}`);
  }
  return manifest;
}

export function buildPluginManifest(claudeManifest) {
  const author =
    typeof claudeManifest.author === "object"
      ? claudeManifest.author?.name
      : claudeManifest.author;
  return {
    name: claudeManifest.name,
    version: claudeManifest.version,
    description: claudeManifest.description,
    author: author || "Graph Powers",
    license: claudeManifest.license || "MIT",
    homepage: claudeManifest.homepage || claudeManifest.repository || "",
    tags: [...new Set([...(claudeManifest.keywords || []), "hermes"])],
    kind: "standalone",
    manifest_version: 1,
    provides_tools: [],
    provides_hooks: [],
    capabilities: [],
  };
}

/** Static generator protocol: no Python plugin or packaged script is ever imported. */
export function buildPackagePlan(pluginRoot = HERE) {
  const root = resolve(pluginRoot);
  const manifest = buildPluginManifest(requiredClaudeManifest(root));
  manifest.description = "Graph Powers engineering skills, command documents and agent contracts adapted for Hermes. No tools or hooks.";
  const result = execFileSync(process.platform === "win32" ? "python" : "python3", [
    join(HERE, "hermes/package_builder.py"), root,
  ], {
    input: JSON.stringify({ manifest: renderPluginManifest(manifest), version: manifest.version,
      registrations: buildRegistrationPlan(root) }),
    encoding: "utf8", maxBuffer: 32 * 1024 * 1024,
    stdio: ["pipe", "pipe", "pipe"],
  });
  return JSON.parse(result);
}

export function renderPluginManifest(manifest) {
  const lines = [
    `name: ${yamlString(manifest.name)}`,
    `version: ${yamlString(manifest.version)}`,
    `description: ${yamlString(manifest.description)}`,
    `author: ${yamlString(manifest.author)}`,
    `license: ${yamlString(manifest.license)}`,
    `homepage: ${yamlString(manifest.homepage)}`,
    `kind: ${manifest.kind}`,
    `manifest_version: ${manifest.manifest_version}`,
    "tags:",
    ...manifest.tags.map((tag) => `  - ${yamlString(tag)}`),
    "provides_tools: []",
    "provides_hooks: []",
    "capabilities: []",
    "",
  ];
  return lines.join("\n");
}

function frontmatterDescription(path, fallback) {
  const text = readFileSync(path, "utf8").replace(/\r\n/g, "\n");
  if (!text.startsWith("---")) return fallback;
  const close = text.indexOf("\n---", 3);
  if (close < 0) return fallback;
  const match = /^description\s*:\s*(.*)$/m.exec(text.slice(3, close));
  if (!match) return fallback;
  const value = match[1].trim().replace(/^("|')(.*)\1$/, "$2");
  return value || fallback;
}

function relativePath(root, path) {
  return relative(root, path).split("\\").join("/");
}

/** Build the exact names Hermes will expose from the source directories. */
export function buildRegistrationPlan(pluginRoot = HERE) {
  const root = resolve(pluginRoot);
  const registrations = [];
  const names = new Map();

  function add(name, path, fallback) {
    const previous = names.get(name);
    if (previous) {
      throw new Error(
        `Hermes registration collision for '${name}': ${previous} and ${relativePath(root, path)}`,
      );
    }
    if (!existsSync(path) || !statSync(path).isFile()) {
      throw new Error(`Hermes registration source is missing: ${path}`);
    }
    const relativeName = relativePath(root, path);
    names.set(name, relativeName);
    registrations.push({
      name,
      path: relativeName,
      description: frontmatterDescription(path, fallback),
    });
  }

  function addSkillDirectories(parent) {
    if (!existsSync(parent) || !statSync(parent).isDirectory()) return;
    for (const folderName of readdirSync(parent).sort()) {
      const folder = join(parent, folderName);
      const skill = join(folder, "SKILL.md");
      if (existsSync(skill) && statSync(skill).isFile()) add(folderName, skill, folderName);
    }
  }

  addSkillDirectories(join(root, "hermes/skills"));
  addSkillDirectories(join(root, "skills"));

  const commands = join(root, "commands");
  if (existsSync(commands)) {
    for (const fileName of readdirSync(commands).filter((name) => name.endsWith(".md")).sort()) {
      if (fileName.toUpperCase() === "AGENTS.MD") continue;
      const path = join(commands, fileName);
      add(fileName.slice(0, -3), path, fileName.slice(0, -3));
    }
  }

  const agents = join(root, "agents");
  if (existsSync(agents)) {
    for (const fileName of readdirSync(agents).filter((name) => name.endsWith(".md")).sort()) {
      if (fileName.toUpperCase() === "AGENTS.MD") continue;
      const slug = fileName.slice(0, -3);
      add(`agent-${slug}`, join(agents, fileName), slug);
    }
  }
  return registrations;
}

function checkEntrypoint(pluginRoot, plan) {
  const path = join(pluginRoot, "__init__.py");
  if (!existsSync(path)) throw new Error(`Hermes entrypoint is missing: ${path}`);
  const source = readFileSync(path, "utf8");
  for (const marker of ["planned_registrations", "commands", "agents", "register_skill"]) {
    if (!source.includes(marker)) throw new Error(`Hermes entrypoint lost '${marker}'`);
  }
  if (!plan.length) throw new Error("Hermes registration plan is empty");
}

export function check({ pluginRoot = HERE } = {}) {
  const root = resolve(pluginRoot);
  const planned = buildPackagePlan(root);
  verifyPackageFiles(root, planned.files);
  const expected = renderPluginManifest(buildPluginManifest(requiredClaudeManifest(root)));
  const path = join(root, MANIFEST);
  if (!existsSync(path)) throw new Error(`Hermes manifest is missing: ${path}`);
  const actual = readFileSync(path, "utf8");
  if (actual !== expected) {
    throw new Error(`${MANIFEST} is stale; run bun hermes/install.mjs --emit-only`);
  }
  const registrations = buildRegistrationPlan(root);
  checkEntrypoint(root, registrations);
  return { manifest: buildPluginManifest(requiredClaudeManifest(root)), registrations,
    provenance: planned.provenance };
}

function packagePaths(root, path = join(root, "hermes/package")) {
  for (const parent of [join(root, "hermes"), path]) {
    if (existsSync(parent) && lstatSync(parent).isSymbolicLink()) {
      throw new Error(`package output symlink escape is not supported: ${parent}`);
    }
  }
  if (!existsSync(path)) return [];
  return readdirSync(path, { withFileTypes: true }).flatMap((entry) => {
    const current = join(path, entry.name);
    if (entry.isSymbolicLink()) throw new Error(`package symlink is not supported: ${current}`);
    return entry.isDirectory() ? packagePaths(root, current) : [current];
  });
}

function verifyPackageFiles(root, files) {
  const output = join(root, "hermes/package");
  for (const path of packagePaths(root)) {
    const name = relativePath(output, path);
    if (!Object.hasOwn(files, name)) throw new Error(`unexpected package file: ${name}`);
  }
  for (const [name, contents] of Object.entries(files)) {
    const path = join(output, name);
    if (!existsSync(path) || readFileSync(path, "utf8") !== contents) {
      throw new Error(`Hermes package is stale or missing: ${name}; run bun hermes/install.mjs --package-only`);
    }
    if (process.platform !== "win32" && contents.startsWith("#!") && (statSync(path).mode & 0o111) !== 0o111) {
      throw new Error(`Hermes package file is not executable: ${name}; run bun hermes/install.mjs --package-only`);
    }
  }
}

export function emitPackage({ pluginRoot = HERE, dryRun = false } = {}) {
  const root = resolve(pluginRoot);
  const planned = buildPackagePlan(root);
  // Unknown files are never deleted to make regeneration pass.
  for (const path of packagePaths(root)) {
    if (!Object.hasOwn(planned.files, relativePath(join(root, "hermes/package"), path))) {
      throw new Error(`unexpected package file: ${path}`);
    }
  }
  if (!dryRun) {
    for (const [name, contents] of Object.entries(planned.files)) {
      const path = join(root, "hermes/package", name);
      writeFile(path, contents);
      if (process.platform !== "win32" && contents.startsWith("#!")) {
        chmodSync(path, statSync(path).mode | 0o111);
      }
    }
  }
  return planned;
}

export function install({
  pluginRoot = HERE,
  dryRun = false,
  emit = false,
  emitOnly = false,
  log = () => {},
} = {}) {
  const root = resolve(pluginRoot);
  const manifest = buildPluginManifest(requiredClaudeManifest(root));
  const registrations = buildRegistrationPlan(root);
  const path = join(root, MANIFEST);
  const contents = renderPluginManifest(manifest);
  const written = [];
  if (emit || emitOnly) {
    if (dryRun) log(`(dry-run) would emit ${path}`);
    else {
      writeFile(path, contents);
      written.push(path);
    }
  }
  return { manifest, registrations, written };
}

function main() {
  const argv = process.argv.slice(2);
  const pluginRoot = pluginRootFromArgv(argv);
  if (argv.includes("--plan-json")) {
    console.log(JSON.stringify(buildPackagePlan(pluginRoot).provenance, null, 2));
    return;
  }
  if (argv.includes("--package-only")) {
    const result = emitPackage({ pluginRoot, dryRun: argv.includes("--dry-run") });
    console.log(`hermes: ${result.provenance.registrations.length} packaged registrations; runtime UNVERIFIED`);
    return;
  }
  if (argv.includes("--check")) {
    const result = check({ pluginRoot });
    console.log(`hermes: ${result.registrations.length} registrations, source manifest and package are current; runtime UNVERIFIED`);
    return;
  }
  const result = install({
    pluginRoot,
    dryRun: argv.includes("--dry-run"),
    emit: true,
    emitOnly: argv.includes("--emit-only") || argv.includes("--write"),
    log: (message) => console.log(message),
  });
  console.log(`hermes: ${result.registrations.length} source registrations; ${result.written.length} path(s) written`);
}

const invoked = process.argv[1] && resolve(process.argv[1]) === resolve(fileURLToPath(import.meta.url));
if (invoked) {
  try {
    main();
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  }
}
