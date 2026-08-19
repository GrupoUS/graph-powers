#!/usr/bin/env node
/**
 * audit-settings — compares the project's `.claude/settings.json` against what the plugin already
 * provides.
 *
 *   node <plugin>/bin/audit-settings.mjs [--json]
 *
 * Why it exists: hooks **accumulate** across levels instead of overriding. A hook declared in the
 * project and an equivalent one in the plugin both run — same event, same call. Nothing breaks
 * immediately, which is exactly why it goes unnoticed: the cost shows up as latency per tool call
 * and as two denial messages for one reason.
 *
 * What it does: reads both sides, points out duplicates, points out what is exclusive to the
 * project and has to stay, and suggests the `permissions` the plugin's guardrails expect.
 * **It writes nothing.** Removing a local hook is a decision for whoever knows the project; this
 * script only shows what is there.
 *
 * Runs under node and bun. Exits 0 whenever it could read; an audit is not a gate.
 */

import { existsSync, readFileSync } from "node:fs";
import { basename, dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const PLUGIN_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const CWD = process.cwd();
const asJson = process.argv.includes("--json");

const color = process.stdout.isTTY && !process.env.NO_COLOR && !asJson;
const paint = (c, s) => (color ? `[${c}m${s}[0m` : s);
const bold = (s) => paint("1", s);
const dim = (s) => paint("2", s);
const green = (s) => paint("32", s);
const yellow = (s) => paint("33", s);

function readJson(p) {
  try {
    return JSON.parse(readFileSync(p, "utf8"));
  } catch {
    return null;
  }
}

/** A hook's identity for duplicate purposes: event + matcher + the file that runs.
 *  The full path differs between project and plugin by construction; the filename is what says
 *  whether the two do the same thing. */
function hookKey(event, matcher, command) {
  const file = basename(String(command).replace(/["']/g, "").split(/\s+/).pop() ?? "");
  return `${event}::${matcher || "*"}::${file}`;
}

function collectHooks(settings) {
  const out = [];
  for (const [event, arr] of Object.entries(settings?.hooks ?? {})) {
    if (!Array.isArray(arr)) continue;
    for (const group of arr) {
      for (const h of group?.hooks ?? []) {
        out.push({
          event,
          matcher: group.matcher ?? "*",
          command: h.command ?? "",
          key: hookKey(event, group.matcher, h.command),
        });
      }
    }
  }
  return out;
}

const projectSettings = readJson(join(CWD, ".claude", "settings.json"));
const pluginManifest = readJson(join(PLUGIN_ROOT, ".claude-plugin", "plugin.json"));

if (!pluginManifest) {
  console.error("could not read the plugin manifest at", PLUGIN_ROOT);
  process.exit(1);
}

const pluginHooks = collectHooks(pluginManifest);
const projectHooks = collectHooks(projectSettings);
const pluginKeys = new Set(pluginHooks.map((h) => h.key));
// Same event, same file, different matcher. The dangerous category: it looks exclusive,
// but both fire on the matcher intersection. Measured: a project with `Edit|Write` against the
// plugin's `Edit|Write|NotebookEdit` runs both on every edit.
const pluginByFile = new Map(pluginHooks.map((h) => [`${h.event}::${h.key.split("::").pop()}`, h]));

const duplicated = projectHooks.filter((h) => pluginKeys.has(h.key));
const overlapping = projectHooks.filter(
  (h) => !pluginKeys.has(h.key) && pluginByFile.has(`${h.event}::${h.key.split("::").pop()}`),
);
const exclusive = projectHooks.filter(
  (h) => !pluginKeys.has(h.key) && !pluginByFile.has(`${h.event}::${h.key.split("::").pop()}`),
);

// Permissions the guardrails assume exist so they do not prompt on every call.
const SUGGESTED_ALLOW = ["Bash(git status:*)", "Bash(git diff:*)", "Bash(git log:*)", "Bash(python3 *)"];
const currentAllow = new Set(projectSettings?.permissions?.allow ?? []);
const missingAllow = SUGGESTED_ALLOW.filter((p) => !currentAllow.has(p));

if (asJson) {
  console.log(
    JSON.stringify(
      {
        projectSettingsFound: Boolean(projectSettings),
        pluginHooks: pluginHooks.length,
        projectHooks: projectHooks.length,
        duplicated,
        overlapping,
        exclusive,
        missingAllow,
      },
      null,
      2,
    ),
  );
  process.exit(0);
}

console.log(`\n${bold("audit-settings")} ${dim(`— ${CWD}`)}\n`);

if (!projectSettings) {
  console.log(`  ${green("✔")} this project has no .claude/settings.json.`);
  console.log(`    ${dim("Nothing to merge: the plugin provides the hooks and you lose nothing.")}\n`);
} else {
  console.log(`${bold("Hooks")}  ${dim(`plugin: ${pluginHooks.length} · project: ${projectHooks.length}`)}\n`);

  if (duplicated.length) {
    console.log(`  ${yellow("!")} ${bold(`${duplicated.length} duplicated`)} — the plugin already provides an equivalent:\n`);
    for (const h of duplicated) {
      console.log(`      ${h.event} ${dim(`[${h.matcher}]`)}  ${basename(h.command.split(/\s+/).pop() ?? "")}`);
    }
    console.log(
      `\n    ${dim("Hooks accumulate across levels: both run, on the same event. Remove the")}\n` +
        `    ${dim("project copy IF it does nothing the plugin's does not — diff them first.")}\n`,
    );
  } else {
    console.log(`  ${green("✔")} no duplicated hooks.\n`);
  }

  if (overlapping.length) {
    console.log(`  ${yellow("!")} ${bold(`${overlapping.length} overlapping`)} — same file, different matcher:\n`);
    for (const h of overlapping) {
      const file = h.key.split("::").pop();
      const mine = pluginByFile.get(`${h.event}::${file}`);
      console.log(`      ${h.event}  ${file}`);
      console.log(`        ${dim(`project: ${h.matcher}`)}`);
      console.log(`        ${dim(`plugin:  ${mine?.matcher}`)}`);
    }
    console.log(
      `\n    ${dim("Both fire on the matcher intersection. If the plugin's covers everything yours")}\n` +
        `    ${dim("covers, the local one is redundant — check the matcher before deciding.")}\n`,
    );
  }

  if (exclusive.length) {
    console.log(`  ${bold(`${exclusive.length} exclusive to the project`)} — keep them:\n`);
    for (const h of exclusive) {
      console.log(`      ${h.event} ${dim(`[${h.matcher}]`)}  ${basename(h.command.split(/\s+/).pop() ?? "")}`);
    }
    console.log("");
  }

  const keys = Object.keys(projectSettings).filter((k) => k !== "hooks");
  if (keys.length) {
    console.log(`  ${bold("Other keys")} ${dim("(the plugin touches none of them):")} ${keys.join(", ")}\n`);
  }
}

if (missingAllow.length) {
  console.log(`${bold("Suggested permissions")} ${dim("— they avoid one prompt per gate call:")}\n`);
  console.log(dim(`      "permissions": { "allow": [${missingAllow.map((p) => `"${p}"`).join(", ")}] }\n`));
  console.log(`  ${dim("A suggestion, not a requirement. Append to what exists; never replace the list.")}\n`);
}

console.log(
  `${dim("This script wrote nothing. Back up before editing:")} ` +
    `${dim("cp .claude/settings.json .claude/settings.json.bak")}\n`,
);
