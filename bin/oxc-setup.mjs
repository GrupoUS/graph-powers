#!/usr/bin/env node
/**
 * Install the project-local TypeScript, Oxlint and Oxfmt binaries and configure editor integrations
 * that can consume them. Declaring a dependency without installing it makes an editor start a
 * missing executable, so setup verifies the exact local paths before reporting success.
 *
 * This is an explicit setup command, never a hook or a package postinstall. It runs the package
 * manager once when a local package is missing, verifies the exact paths used by the official Zed
 * extension, and writes only portable project settings. The extension itself still has to be
 * installed from the Zed or VS Code/Cursor extension marketplace.
 */

import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const OXC_PACKAGES = ["oxlint", "oxfmt", "typescript"];
const PACKAGE_SPECS = {
  oxlint: "oxlint",
  oxfmt: "oxfmt",
  typescript: "typescript@7",
};
const PACKAGE_BINARIES = {
  oxlint: "oxlint",
  oxfmt: "oxfmt",
};
const SUPPORTED_PACKAGE_MANAGERS = new Set(["bun", "npm", "pnpm", "yarn"]);
const PACKAGE_MANAGER_LOCKFILES = [
  ["bun", ["bun.lock", "bun.lockb"]],
  ["pnpm", ["pnpm-lock.yaml"]],
  ["yarn", ["yarn.lock"]],
  ["npm", ["package-lock.json", "npm-shrinkwrap.json"]],
];
const PACKAGE_MANAGER_COMMANDS = {
  bun: { add: ["add", "--dev"], install: ["install"] },
  npm: { add: ["install", "--save-dev"], install: ["install"] },
  pnpm: { add: ["add", "--save-dev"], install: ["install"] },
  yarn: { add: ["add", "--dev"], install: ["install"] },
};

function readJson(file) {
  try {
    return JSON.parse(readFileSync(file, "utf8"));
  } catch {
    return null;
  }
}

function readRequiredJson(file, label) {
  if (!existsSync(file)) return {};
  try {
    const value = JSON.parse(readFileSync(file, "utf8"));
    if (!value || typeof value !== "object" || Array.isArray(value)) {
      throw new Error(`${label} must contain a JSON object`);
    }
    return value;
  } catch (error) {
    throw new Error(`cannot read ${label}: ${error.message}`, { cause: error });
  }
}

function packageManagerName(value) {
  const name = String(value ?? "")
    .trim()
    .split("@")[0]
    .toLowerCase();
  return SUPPORTED_PACKAGE_MANAGERS.has(name) ? name : null;
}

function packageJsonFor(projectDir) {
  const file = join(projectDir, "package.json");
  const packageJson = readRequiredJson(file, "package.json");
  if (!existsSync(file))
    throw new Error("JavaScript/TypeScript setup requires a project package.json");
  return packageJson;
}

function projectConfigFor(projectDir) {
  for (const file of [
    join(projectDir, ".graph-powers", "config.json"),
    join(projectDir, ".claude", "config.json"),
  ]) {
    const config = readJson(file);
    if (config && typeof config === "object") return config;
  }
  return {};
}

export function detectPackageManager(
  projectDir,
  { packageJson = null, packageManager = null } = {},
) {
  const root = resolve(projectDir);
  const pkg = packageJson ?? packageJsonFor(root);
  const explicit = packageManagerName(packageManager);
  if (explicit) return explicit;

  for (const [name, files] of PACKAGE_MANAGER_LOCKFILES) {
    if (files.some((file) => existsSync(join(root, file)))) return name;
  }

  const configured = projectConfigFor(root)?.tooling?.packageManager;
  const configuredName = packageManagerName(configured);
  if (configuredName) return configuredName;

  return packageManagerName(pkg.packageManager);
}

function declaredDependencies(packageJson) {
  return new Set([
    ...Object.keys(packageJson.dependencies ?? {}),
    ...Object.keys(packageJson.devDependencies ?? {}),
  ]);
}

function declaredStableTypeScript7(packageJson) {
  const value = packageJson.dependencies?.typescript ?? packageJson.devDependencies?.typescript;
  return typeof value === "string" && /^[~^<>=\s]*7(?:[.]|\s|$)/.test(value.trim());
}

function localBinaryPath(projectDir, packageName) {
  return join(
    projectDir,
    "node_modules",
    packageName,
    packageName === "typescript" ? "package.json" : join("bin", PACKAGE_BINARIES[packageName]),
  );
}

function expectedLocalPath(packageName) {
  return packageName === "typescript"
    ? "node_modules/typescript/package.json"
    : join("node_modules", packageName, "bin", PACKAGE_BINARIES[packageName]);
}

function isFile(file) {
  try {
    return statSync(file).isFile();
  } catch {
    return false;
  }
}

function hasStableTypeScript7(projectDir) {
  const packageJson = readJson(join(projectDir, "node_modules", "typescript", "package.json"));
  const version = packageJson?.version;
  const match =
    typeof version === "string" ? version.match(/^(\d+)\.\d+\.\d+(?:\+[0-9A-Za-z.-]+)?$/) : null;
  return Boolean(match && Number(match[1]) >= 7 && isFile(localBinaryPath(projectDir, "typescript")));
}

export function missingOxcBinaries(projectDir) {
  const packageJson = readJson(join(projectDir, "package.json")) ?? {};
  const missing = OXC_PACKAGES.filter((name) => !isFile(localBinaryPath(projectDir, name)));
  if (
    (!hasStableTypeScript7(projectDir) || !declaredStableTypeScript7(packageJson)) &&
    !missing.includes("typescript")
  )
    missing.push("typescript");
  return missing;
}

function executableCandidates(name) {
  if (process.platform !== "win32") return [name];
  return [`${name}.cmd`, `${name}.exe`, name];
}

function runPackageManager(packageManager, args, projectDir) {
  let result = null;
  for (const candidate of executableCandidates(packageManager)) {
    result = spawnSync(candidate, args, {
      cwd: projectDir,
      encoding: "utf8",
      stdio: "inherit",
      timeout: 300000,
    });
    if (!(result.error && result.error.code === "ENOENT")) return result;
  }
  throw new Error(`${packageManager} was not found on PATH`);
}

function displayCommand(packageManager, args) {
  return [packageManager, ...args].join(" ");
}

function deepMerge(base, overlay) {
  const result = { ...(base && typeof base === "object" && !Array.isArray(base) ? base : {}) };
  for (const [key, value] of Object.entries(overlay ?? {})) {
    if (value && typeof value === "object" && !Array.isArray(value)) {
      result[key] = deepMerge(result[key], value);
    } else {
      result[key] = value;
    }
  }
  return result;
}

function readTemplate(pluginRoot, path) {
  const file = join(pluginRoot, "templates", ...path);
  if (!existsSync(file)) throw new Error(`plugin template is missing: templates/${path.join("/")}`);
  return readRequiredJson(file, `templates/${path.join("/")}`);
}

function removeInvalidTypeScript7Sdk(settings) {
  const vtslsSettings = settings?.lsp?.vtsls?.settings;
  if (!vtslsSettings || typeof vtslsSettings !== "object") return;

  for (const language of ["typescript", "javascript"]) {
    if (vtslsSettings[language]?.tsdk === "node_modules/typescript/lib") {
      delete vtslsSettings[language].tsdk;
    }
  }
}

function projectRelative(projectDir, file) {
  return relative(projectDir, file).replaceAll("\\", "/") || ".";
}

function writeProjectJson(projectDir, file, value, { dryRun, log }) {
  const label = projectRelative(projectDir, file);
  const serialized = `${JSON.stringify(value, null, 2)}\n`;
  if (dryRun) {
    log(`(dry-run) would write ${label}`);
    return false;
  }
  mkdirSync(dirname(file), { recursive: true });
  const current = existsSync(file) ? readFileSync(file, "utf8") : null;
  if (current === serialized) return false;
  writeFileSync(file, serialized, "utf8");
  log(`${label} written`);
  return true;
}

function configureEditors(projectDir, pluginRoot, { dryRun, log }) {
  const zedTemplate = readTemplate(pluginRoot, ["zed", "settings.json"]);
  const vscodeTemplate = readTemplate(pluginRoot, ["vscode", "settings.json"]);
  const extensionsTemplate = readTemplate(pluginRoot, ["vscode", "extensions.json"]);

  const zedFile = join(projectDir, ".zed", "settings.json");
  const vscodeFile = join(projectDir, ".vscode", "settings.json");
  const extensionsFile = join(projectDir, ".vscode", "extensions.json");
  const zed = deepMerge(readRequiredJson(zedFile, ".zed/settings.json"), zedTemplate);
  removeInvalidTypeScript7Sdk(zed);
  const vscode = deepMerge(readRequiredJson(vscodeFile, ".vscode/settings.json"), vscodeTemplate);
  const currentExtensions = readRequiredJson(extensionsFile, ".vscode/extensions.json");
  const extensions = deepMerge(currentExtensions, extensionsTemplate);
  extensions.recommendations = [
    ...new Set(
      [
        ...(extensions.recommendations ?? []),
        ...(currentExtensions.recommendations ?? []),
        "oxc.oxc-vscode",
      ],
    ),
  ];

  const written = [
    writeProjectJson(projectDir, zedFile, zed, { dryRun, log }),
    writeProjectJson(projectDir, vscodeFile, vscode, { dryRun, log }),
    writeProjectJson(projectDir, extensionsFile, extensions, { dryRun, log }),
  ].filter(Boolean).length;
  return {
    written,
    files: [".zed/settings.json", ".vscode/settings.json", ".vscode/extensions.json"],
  };
}

export function setupOxc({
  projectDir = process.cwd(),
  pluginRoot = HERE,
  packageManager = null,
  dryRun = false,
  configure = true,
  log = console.log,
} = {}) {
  const root = resolve(projectDir);
  const packageJson = packageJsonFor(root);
  const manager = detectPackageManager(root, { packageJson, packageManager });
  const before = missingOxcBinaries(root);
  let install = null;

  if (before.length) {
    if (!manager) {
      throw new Error(
        "cannot install local TypeScript/Oxc tools: no supported package manager lockfile or packageManager setting was found",
      );
    }
    const declared = declaredDependencies(packageJson);
    const allDeclared = before.every(
      (name) => declared.has(name) && !(name === "typescript" && !hasStableTypeScript7(root)),
    );
    const args = [
      ...(allDeclared
        ? PACKAGE_MANAGER_COMMANDS[manager].install
        : PACKAGE_MANAGER_COMMANDS[manager].add),
      ...(allDeclared ? [] : before.map((name) => PACKAGE_SPECS[name])),
    ];
    install = { packageManager: manager, args, command: displayCommand(manager, args) };
    if (dryRun) {
      log(`(dry-run) would run ${install.command}`);
    } else {
      log(`Installing local TypeScript/Oxc packages with ${install.command}`);
      const result = runPackageManager(manager, args, root);
      if (result.error || result.status !== 0) {
        throw new Error(`${install.command} failed with exit code ${result.status ?? "unknown"}`);
      }
    }
  }

  const after = missingOxcBinaries(root);
  if (after.length && !dryRun) {
    const paths = after.map(expectedLocalPath).join(", ");
    throw new Error(
      `Local tool installation did not provide the expected local path(s): ${paths}`,
    );
  }

  const editors = configure
    ? configureEditors(root, pluginRoot, { dryRun, log })
    : { written: 0, files: [] };
  for (const name of OXC_PACKAGES) {
    const path = expectedLocalPath(name);
    log(`${name}: ${dryRun && after.includes(name) ? `will verify ${path}` : `verified ${path}`}`);
  }
  return {
    packageManager: manager,
    installed: before.length === 0 || !dryRun,
    missingBefore: before,
    missingAfter: after,
    install,
    editors,
  };
}

function flagValue(argv, name, fallback = null) {
  const index = argv.indexOf(name);
  return index !== -1 && argv[index + 1] && !argv[index + 1].startsWith("-")
    ? argv[index + 1]
    : fallback;
}

function printHelp() {
  console.log(`
 JavaScript/TypeScript project setup — install local TypeScript/Oxlint/Oxfmt and configure editors

Usage:
  bun <plugin>/bin/oxc-setup.mjs [options]

Options:
  --project <path>             Project root (default: current directory)
  --package-manager <name>     Override detection: bun, npm, pnpm or yarn
  --no-editors                 Install and verify local tools without writing IDE settings
  --dry-run                    Print the install and write actions without changing files
  -h, --help                   Show this help

Zed's vtsls and the Oxc extension still have to be installed or enabled once in the editor. This
 command configures Oxfmt as the formatter and Oxlint as the interactive diagnostic provider; it
does not enable type-aware linting or a second TypeScript server.
`);
}

const argv = process.argv.slice(2);
const invokedDirectly =
  process.argv[1] && pathToFileURL(resolve(process.argv[1])).href === import.meta.url;
if (invokedDirectly) {
  if (argv.includes("-h") || argv.includes("--help")) {
    printHelp();
    process.exit(0);
  }
  try {
    const result = setupOxc({
      projectDir: flagValue(argv, "--project", process.cwd()),
      packageManager: flagValue(argv, "--package-manager"),
      configure: !argv.includes("--no-editors"),
      dryRun: argv.includes("--dry-run"),
    });
    console.log(
      result.missingBefore.length
        ? result.missingAfter.length
          ? "Oxc setup planned; run without --dry-run to install the packages."
          : "Oxc packages installed and editor settings configured."
        : "Oxc packages already installed and editor settings configured.",
    );
  } catch (error) {
    console.error(`Oxc setup failed: ${error.message}`);
    process.exit(1);
  }
}
