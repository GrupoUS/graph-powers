#!/usr/bin/env node
/**
 * Generate the Cursor side of Graph Powers from the Claude Code artefacts.
 *
 *   node cursor/install.mjs [--plugin <dir>] [--emit] [--emit-only] [--dry-run] [--guarded]
 *
 * Cursor is the third harness. Cardinal 7 still holds: nothing here is a second list. The
 * thirteen Python guardrails stay the source; this file only translates the wiring into the
 * shape Cursor actually loads.
 *
 *   .cursor-plugin/plugin.json   <- .claude-plugin/plugin.json   (manifest, plus Cursor paths)
 *   hooks/hooks-cursor.json      <- hooks/hooks.json             (event + matcher + flatten)
 *   ~/.cursor/permissions.json   <- autonomy.level               (IDE Run Mode / Auto-review)
 *   ~/.cursor/cli-config.json    <- the same posture for `cursor-agent`
 *
 * Cursor does not support PermissionRequest or Notification. Those registrations are skipped,
 * not rewritten: inventing a Cursor event for them would be a second owner for a decision
 * that already has one. preToolUse still runs the git gates and smart_bash_approver, which is
 * the half that stops a confirmation flood.
 *
 * User files are merged, never replaced. A permission list is somebody's decision.
 */

import { existsSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { readJson, writeFile } from "../codex/lib.mjs";

const HERE = resolve(dirname(fileURLToPath(import.meta.url)), "..");

const EVENT_MAP = {
  PreToolUse: "preToolUse",
  PostToolUse: "postToolUse",
  SessionStart: "sessionStart",
  SessionEnd: "sessionEnd",
  Stop: "stop",
  SubagentStop: "subagentStop",
  PreCompact: "preCompact",
  UserPromptSubmit: "beforeSubmitPrompt",
};

const SKIP_EVENTS = new Set(["PermissionRequest", "Notification"]);

const MATCHER_MAP = {
  Bash: "Shell",
  "Edit|Write|NotebookEdit": "Write|StrReplace|EditNotebook",
  "Edit|Write": "Write|StrReplace",
};

function mapMatcher(matcher) {
  if (matcher === undefined || matcher === "*") return undefined;
  return MATCHER_MAP[matcher] ?? matcher;
}

function pluginRootFromArgv(argv) {
  const i = argv.indexOf("--plugin");
  if (i !== -1 && argv[i + 1] && !argv[i + 1].startsWith("-")) return resolve(argv[i + 1]);
  return HERE;
}

function commandForCursor(command) {
  return String(command)
    .replaceAll("${CLAUDE_PLUGIN_ROOT}/", "")
    .replaceAll("${CLAUDE_PLUGIN_ROOT}", ".");
}

/**
 * Flatten one Claude Code matcher-group into Cursor's array-of-commands shape.
 *
 * Cursor's native hook is `{ command, matcher?, timeout? }`. Claude Code nests
 * `{ matcher, hooks: [{ type, command, timeout }] }`. Each inner command becomes its own
 * Cursor entry so a matcher with five gates is five hooks, not one command that Cursor
 * cannot parse.
 */
export function buildCursorHooks(hookManifest) {
  const out = {};
  const skipped = [];
  for (const [event, groups] of Object.entries(hookManifest?.hooks ?? {})) {
    if (SKIP_EVENTS.has(event)) {
      skipped.push(event);
      continue;
    }
    const mapped = EVENT_MAP[event];
    if (!mapped) {
      skipped.push(event);
      continue;
    }
    const entries = [];
    for (const group of groups ?? []) {
      const matcher = mapMatcher(group.matcher);
      for (const hook of group.hooks ?? []) {
        if (hook.type && hook.type !== "command") continue;
        const entry = { command: commandForCursor(hook.command) };
        if (matcher) entry.matcher = matcher;
        if (hook.timeout) entry.timeout = hook.timeout;
        entries.push(entry);
      }
    }
    if (entries.length) out[mapped] = [...(out[mapped] ?? []), ...entries];
  }
  return { version: 1, hooks: out, skipped };
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
    keywords: [...new Set([...(claudeManifest.keywords ?? []), "cursor"])],
    skills: "./skills/",
    agents: "./agents/",
    commands: "./commands/",
    hooks: "./hooks/hooks-cursor.json",
  };
}

function autonomousPermissions() {
  return {
    approvalMode: "unrestricted",
    mcpAllowlist: ["*:*"],
    terminalAllowlist: ["*"],
    autoRun: {
      allow_instructions: [
        "Allow routine shell: git reads and reversible git, the project's package manager, linters, type-checks, tests, python3 and node scripts inside the repository.",
        "Allow file reads, edits, searches, fetches, and MCP tools. Graph Powers still refuses what git cannot undo.",
      ],
      block_instructions: [
        "Block force-push, git reset --hard, git clean -f, DROP DATABASE, rm -rf of a home or root path, and writes to .env or secrets.",
      ],
    },
  };
}

/**
 * Merge the operator's Cursor IDE permissions. `approvalMode: unrestricted` is what
 * Settings → Agents → Approvals & Execution calls Run Everything. Without this file the
 * IDE stays on Auto-review / Allowlist even when `~/.cursor/cli-config.json` is already
 * unrestricted — they are two products, and the confirmation flood lives in the IDE one.
 *
 * Never overwrite a mode the operator already set to unrestricted. Never replace an
 * allowlist they extended; append ours.
 */
export function mergePermissions(current, { autonomous }) {
  if (!autonomous) return { next: current, changed: [] };
  const wanted = autonomousPermissions();
  const next = { ...(current && typeof current === "object" ? current : {}) };
  const changed = [];
  const mode = next.approvalMode;
  if (mode !== "unrestricted") {
    next.approvalMode = "unrestricted";
    changed.push("approvalMode");
  }
  const mcp = new Set(next.mcpAllowlist ?? []);
  for (const entry of wanted.mcpAllowlist) {
    if (!mcp.has(entry)) {
      mcp.add(entry);
      changed.push("mcpAllowlist");
    }
  }
  next.mcpAllowlist = [...mcp];
  const terminal = new Set(next.terminalAllowlist ?? []);
  for (const entry of wanted.terminalAllowlist) {
    if (!terminal.has(entry)) {
      terminal.add(entry);
      changed.push("terminalAllowlist");
    }
  }
  next.terminalAllowlist = [...terminal];
  const allow = new Set(next.autoRun?.allow_instructions ?? []);
  let autoRunTouched = false;
  for (const entry of wanted.autoRun.allow_instructions) {
    if (!allow.has(entry)) {
      allow.add(entry);
      autoRunTouched = true;
    }
  }
  const block = new Set(next.autoRun?.block_instructions ?? []);
  for (const entry of wanted.autoRun.block_instructions) {
    if (!block.has(entry)) {
      block.add(entry);
      autoRunTouched = true;
    }
  }
  if (autoRunTouched) {
    next.autoRun = { allow_instructions: [...allow], block_instructions: [...block] };
    changed.push("autoRun");
  }
  return { next, changed: [...new Set(changed)] };
}

export function mergeCliConfig(current, { autonomous }) {
  const next = { ...(current && typeof current === "object" ? current : { version: 1 }) };
  const changed = [];
  if (autonomous && next.approvalMode !== "unrestricted") {
    next.approvalMode = "unrestricted";
    changed.push("approvalMode");
  }
  if (autonomous && next.autoAcceptWebSearch !== true) {
    next.autoAcceptWebSearch = true;
    changed.push("autoAcceptWebSearch");
  }
  const allow = new Set(next.permissions?.allow ?? []);
  const wanted = ["Shell(*)", "Write(*)", "Read(*)", "WebFetch(*)", "WebSearch", "Mcp(*)"];
  let allowTouched = false;
  if (autonomous) {
    for (const entry of wanted) {
      if (!allow.has(entry)) {
        allow.add(entry);
        allowTouched = true;
      }
    }
  }
  if (allowTouched) {
    next.permissions = {
      ...next.permissions,
      allow: [...allow],
      deny: next.permissions?.deny ?? [],
    };
    changed.push("permissions.allow");
  }
  return { next, changed };
}

export function install({
  pluginRoot = HERE,
  dryRun = false,
  autonomous = true,
  emit = false,
  emitOnly = false,
  log = () => {},
} = {}) {
  const written = [];
  const claudeManifest = readJson(join(pluginRoot, ".claude-plugin/plugin.json"), {});
  const hookManifest = readJson(join(pluginRoot, "hooks/hooks.json"), { hooks: {} });
  const cursorHooks = buildCursorHooks(hookManifest);
  const pluginManifest = buildPluginManifest(claudeManifest);
  const { skipped, ...hooksFile } = cursorHooks;

  if (emit) {
    const hooksPath = join(pluginRoot, "hooks/hooks-cursor.json");
    const manifestPath = join(pluginRoot, ".cursor-plugin/plugin.json");
    if (dryRun) {
      log(`(dry-run) would emit ${hooksPath}`);
      log(`(dry-run) would emit ${manifestPath}`);
    } else {
      writeFile(hooksPath, `${JSON.stringify(hooksFile, null, 2)}\n`);
      writeFile(manifestPath, `${JSON.stringify(pluginManifest, null, 2)}\n`);
      written.push(hooksPath, manifestPath);
    }
    if (skipped.length) log(`cursor skips unsupported events: ${skipped.join(", ")}`);
  }

  if (emitOnly) return { written, skipped, permChanged: [], cliChanged: [] };

  const home = homedir();
  const permFile = join(home, ".cursor/permissions.json");
  const cliFile = join(home, ".cursor/cli-config.json");
  const { next: perms, changed: permChanged } = mergePermissions(
    existsSync(permFile) ? readJson(permFile, {}) : {},
    { autonomous },
  );
  const { next: cli, changed: cliChanged } = mergeCliConfig(
    existsSync(cliFile) ? readJson(cliFile, {}) : {},
    { autonomous },
  );

  if (permChanged.length) {
    if (dryRun) log(`(dry-run) would write ${permFile}: ${permChanged.join(", ")}`);
    else {
      writeFile(permFile, `${JSON.stringify(perms, null, 2)}\n`);
      written.push(permFile);
    }
  } else {
    log("Cursor IDE permissions already match autonomous posture");
  }
  if (cliChanged.length) {
    if (dryRun) log(`(dry-run) would write ${cliFile}: ${cliChanged.join(", ")}`);
    else {
      writeFile(cliFile, `${JSON.stringify(cli, null, 2)}\n`);
      written.push(cliFile);
    }
  } else {
    log("Cursor CLI config already matches autonomous posture");
  }
  return { written, skipped, permChanged, cliChanged };
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
    log: (m) => console.log(`  ${m}`),
  });
  if (!dryRun && result.written.length) {
    console.log(`cursor: ${result.written.length} path(s) written`);
  }
}

const invoked = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invoked) main();
