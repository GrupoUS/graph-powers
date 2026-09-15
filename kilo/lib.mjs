/**
 * Shared helpers for generating Kilo artefacts from the canonical Claude Code files.
 *
 * The rule this module exists to hold, same as `../codex/lib.mjs`: **one source of truth per
 * artefact.** Kilo agents are generated from `agents/*.md`, Kilo commands from `commands/*.md`,
 * Kilo skills from `skills/`. Nothing is maintained twice.
 *
 * Two things here are Kilo-specific and were proven against the installed CLI (7.6.2):
 *
 * 1. `~/.kilo/` is the directory Kilo actually reads for `agent/`, `command/`, `skills/` and
 *    `plugin/`. `~/.config/kilo/` holds the config file, not the artefacts. `~/.kilocode/` is the
 *    legacy twin of `~/.kilo/` and is scanned too. `kilo agent list` and `kilo debug skill` were
 *    the proof.
 * 2. Canonical prose carries client literals that resolve to nothing on Kilo — `graph-powers:<agent>`,
 *    `Skill("graph-powers:planning")`, `Workflow({...})`. Translating them is the difference between
 *    an installed command and a command that reads as installed and routes nowhere.
 */

import { readFileSync, statSync } from "node:fs";
import { homedir } from "node:os";
import { join, relative, sep } from "node:path";

export { copyTree, listDirs, listMarkdown, parseFrontmatter, readJson, writeFile } from "../codex/lib.mjs";

// ── locations ────────────────────────────────────────────────────────────────

/** The directory Kilo reads agents, commands, skills and plugins from. */
export function kiloHome() {
  return process.env.KILO_HOME ? process.env.KILO_HOME : join(homedir(), ".kilo");
}

/** The directory Kilo reads its global config file from. */
export function kiloConfigDir() {
  return process.env.KILO_CONFIG_DIR
    ? process.env.KILO_CONFIG_DIR
    : join(homedir(), ".config", "kilo");
}

/**
 * The global config files Kilo reads, in precedence order.
 *
 * Proven against 7.6.2 on a clean `HOME`: a `~/.config/kilo/kilo.jsonc` alone contributes nothing
 * to `kilo debug config`, while `~/.kilo/kilo.jsonc` does — and on an installed machine both are
 * read and merged, with the home file winning a conflicting key. The second entry exists for one
 * reason: a managed key defined there must be a conflict we refuse, not a value we silently
 * shadow. The first is the file an install writes.
 */
export function kiloConfigFiles() {
  const home = join(kiloHome(), "kilo.jsonc");
  const xdg = join(kiloConfigDir(), "kilo.jsonc");
  return [home, xdg].filter((path, index, all) => all.indexOf(path) === index);
}

/** The file Graph Powers writes managed keys to. */
export function kiloConfigFile() {
  return kiloConfigFiles()[0];
}

const MANIFEST_NAME = "graph-powers-installed.json";

export function kiloPaths(scope, projectDir, pluginRoot) {
  const home = kiloHome();
  const references = join(home, "graph-powers", "references");
  const referencesRelative = relative(homedir(), references);
  const underHome =
    referencesRelative &&
    referencesRelative !== ".." &&
    !referencesRelative.startsWith(`..${sep}`);
  return scope === "user"
    ? {
        agents: join(home, "agent"),
        commands: join(home, "command"),
        skills: join(home, "skills"),
        plugins: join(home, "plugin"),
        references,
        referencesRef: underHome ? `~/${referencesRelative.split(sep).join("/")}` : references,
        assets: join(home, "graph-powers"),
        config: kiloConfigFile(),
        manifest: join(home, MANIFEST_NAME),
        pluginRoot,
      }
    : {
        agents: join(projectDir, ".kilo", "agent"),
        commands: join(projectDir, ".kilo", "command"),
        skills: join(projectDir, ".kilo", "skills"),
        plugins: join(projectDir, ".kilo", "plugin"),
        references: join(projectDir, ".kilo", "graph-powers", "references"),
        referencesRef: ".kilo/graph-powers/references",
        assets: join(projectDir, ".kilo", "graph-powers"),
        config: join(projectDir, "kilo.jsonc"),
        manifest: join(projectDir, ".graph-powers", "installed-kilo.json"),
        pluginRoot,
      };
}

// ── prose translation ────────────────────────────────────────────────────────

const SKILL_CALL = /Skill\(\s*["']([^"']+)["']\s*\)/g;
/** Only `graph-powers:` bound to something — `graph-powers:agent`, `graph-powers:${name}`. A bare
 *  mention followed by a space ("there is no namespace") is prose and stays. */
const NAMESPACE = /graph-powers:(?=\S)/g;
/** The optional-group idiom in shipped Python (`^(?:graph-powers:)?…`) reads worse empty. */
const OPTIONAL_NAMESPACE = /\(\?:graph-powers:\)\?/g;
const WORKFLOW = /\bWorkflow\s*\(/g;

/** Replace a balanced `Workflow({ ... })` call, nested braces and all. */
function replaceWorkflowCalls(text, replacement) {
  let out = text;
  for (;;) {
    WORKFLOW.lastIndex = 0;
    const match = WORKFLOW.exec(out);
    if (!match) return out;
    const open = out.indexOf("(", match.index);
    let depth = 0;
    let end = -1;
    for (let i = open; i < out.length; i += 1) {
      const ch = out[i];
      if (ch === "(" || ch === "{" || ch === "[") depth += 1;
      else if (ch === ")" || ch === "}" || ch === "]") {
        depth -= 1;
        if (depth === 0) {
          end = i + 1;
          break;
        }
      }
    }
    if (end === -1) return out;
    out = `${out.slice(0, match.index)}${replacement}${out.slice(end)}`;
  }
}

/**
 * Resolve the Claude-only plugin-root variable and translate client literals.
 *
 * Order is load-bearing: the longest plugin-root prefixes resolve first, `Workflow` is replaced
 * before the namespaced name inside it is stripped, and `Skill(...)` is rewritten before the bare
 * namespace pass so the skill name survives as a name.
 */
export function rewriteForKilo(text, { skillsRef, referencesRef, commandsRef, agentsRef, pluginRoot }) {
  let out = String(text)
    .replaceAll("${CLAUDE_PLUGIN_ROOT}/skills", skillsRef)
    .replaceAll("${CLAUDE_PLUGIN_ROOT}/references", referencesRef)
    .replaceAll("${CLAUDE_PLUGIN_ROOT}/commands", commandsRef)
    .replaceAll("${CLAUDE_PLUGIN_ROOT}/agents", agentsRef)
    .replaceAll("${CLAUDE_PLUGIN_ROOT}", pluginRoot);

  out = out.replace(SKILL_CALL, (_match, name) => {
    const bare = name.replace(/^graph-powers:/, "");
    return `the \`${bare}\` skill`;
  });
  out = replaceWorkflowCalls(
    out,
    "the named Graph Powers workflow (unavailable on Kilo: there is no workflow runtime)",
  );
  out = out.replace(OPTIONAL_NAMESPACE, "");
  out = out.replace(NAMESPACE, "");
  return out;
}

// ── YAML frontmatter emission ────────────────────────────────────────────────

function yamlScalar(value) {
  if (typeof value === "boolean" || typeof value === "number") return String(value);
  const s = String(value);
  if (/^[A-Za-z0-9_][A-Za-z0-9_ .-]*$/.test(s) && !/^(true|false|null|yes|no|on|off)$/i.test(s)) {
    return s;
  }
  return `"${s.replace(/\\/g, "\\\\").replace(/"/g, '\\"')}"`;
}

/**
 * Emit deterministic YAML for the shapes a generated Kilo artefact uses: scalars, one nested map
 * (`permission`), a map of scalars (`permission.bash`, `tools`) and block sequences.
 *
 * A hand-rolled emitter rather than a dependency: the install ships into `~/.kilo/plugin/` next to
 * Kilo's own runtime, and a YAML library would be a second package resolution to get wrong.
 */
export function emitFrontmatter(data) {
  const lines = ["---"];
  for (const [key, value] of Object.entries(data)) {
    if (value === undefined || value === null) continue;
    if (Array.isArray(value)) {
      if (!value.length) continue;
      lines.push(`${key}:`);
      for (const item of value) lines.push(`  - ${yamlScalar(item)}`);
      continue;
    }
    if (typeof value === "object") {
      const entries = Object.entries(value).filter(([, v]) => v !== undefined && v !== null);
      if (!entries.length) continue;
      lines.push(`${key}:`);
      for (const [childKey, childValue] of entries) {
        if (childValue && typeof childValue === "object" && !Array.isArray(childValue)) {
          const nested = Object.entries(childValue);
          if (!nested.length) continue;
          lines.push(`  ${yamlScalar(childKey)}:`);
          for (const [nestedKey, nestedValue] of nested) {
            lines.push(`    ${yamlScalar(nestedKey)}: ${yamlScalar(nestedValue)}`);
          }
          continue;
        }
        lines.push(`  ${yamlScalar(childKey)}: ${yamlScalar(childValue)}`);
      }
      continue;
    }
    lines.push(`${key}: ${yamlScalar(value)}`);
  }
  lines.push("---");
  return lines.join("\n");
}

/** An artefact on disk: frontmatter object plus body, rendered deterministically. */
export function emitMarkdown(frontmatter, body) {
  const clean = String(body ?? "").replace(/\r\n/g, "\n").replace(/^\n+/, "").trimEnd();
  return `${emitFrontmatter(frontmatter)}\n\n${clean}\n`;
}

// ── JSONC ────────────────────────────────────────────────────────────────────

/** Remove `//` and block comments and trailing commas without touching string contents. */
export function stripJsonc(text) {
  let out = "";
  let i = 0;
  let inString = false;
  let quote = "";
  while (i < text.length) {
    const ch = text[i];
    const next = text[i + 1];
    if (inString) {
      out += ch;
      if (ch === "\\") {
        out += next ?? "";
        i += 2;
        continue;
      }
      if (ch === quote) inString = false;
      i += 1;
      continue;
    }
    if (ch === '"' || ch === "'") {
      inString = true;
      quote = ch;
      out += ch;
      i += 1;
      continue;
    }
    if (ch === "/" && next === "/") {
      while (i < text.length && text[i] !== "\n") i += 1;
      continue;
    }
    if (ch === "/" && next === "*") {
      i += 2;
      while (i < text.length && !(text[i] === "*" && text[i + 1] === "/")) i += 1;
      i += 2;
      continue;
    }
    out += ch;
    i += 1;
  }
  return out.replace(/,(\s*[}\]])/g, "$1");
}

export function parseJsonc(text) {
  if (!String(text).trim()) return {};
  const value = JSON.parse(stripJsonc(String(text)));
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("Kilo config must contain a JSON object");
  }
  return value;
}

/**
 * The character span of a top-level key — its name, and its value — so an update can replace
 * exactly that value and leave every comment, blank line and unrelated key byte-for-byte.
 */
export function topLevelKeySpan(text, key) {
  const needle = `"${key}"`;
  let i = 0;
  let depth = 0;
  let inString = false;
  let quote = "";
  let keyStart = -1;
  while (i < text.length) {
    const ch = text[i];
    const next = text[i + 1];
    if (inString) {
      if (ch === "\\") {
        i += 2;
        continue;
      }
      if (ch === quote) inString = false;
      i += 1;
      continue;
    }
    if (ch === "/" && next === "/") {
      while (i < text.length && text[i] !== "\n") i += 1;
      continue;
    }
    if (ch === "/" && next === "*") {
      i += 2;
      while (i < text.length && !(text[i] === "*" && text[i + 1] === "/")) i += 1;
      i += 2;
      continue;
    }
    if (ch === '"' || ch === "'") {
      if (depth === 1 && keyStart === -1 && text.startsWith(needle, i)) {
        keyStart = i;
      }
      inString = true;
      quote = ch;
      i += 1;
      continue;
    }
    if (ch === "{" || ch === "[") depth += 1;
    else if (ch === "}" || ch === "]") depth -= 1;
    else if (ch === ":" && depth === 1 && keyStart !== -1) {
      let j = i + 1;
      while (j < text.length && /\s/.test(text[j])) j += 1;
      const start = j;
      let nesting = 0;
      while (j < text.length) {
        const c = text[j];
        if (inString) {
          if (c === "\\") {
            j += 2;
            continue;
          }
          if (c === quote) inString = false;
          j += 1;
          continue;
        }
        if (c === '"' || c === "'") {
          inString = true;
          quote = c;
          j += 1;
          continue;
        }
        if (c === "/" && text[j + 1] === "/") {
          while (j < text.length && text[j] !== "\n") j += 1;
          continue;
        }
        if (c === "{" || c === "[") nesting += 1;
        else if (c === "}" || c === "]") {
          if (nesting === 0) break;
          nesting -= 1;
        } else if (c === "," && nesting === 0) break;
        j += 1;
      }
      return { keyStart, valueStart: start, valueEnd: j };
    }
    i += 1;
  }
  return null;
}

/** The value span alone, for callers that only replace a value. */
export function topLevelValueSpan(text, key) {
  const span = topLevelKeySpan(text, key);
  return span ? [span.valueStart, span.valueEnd] : null;
}

function renderValue(value, indent) {
  const rendered = JSON.stringify(value, null, 2);
  if (rendered === undefined) throw new Error("Kilo config value is not serialisable");
  return rendered.replace(/\n/g, `\n${indent}`);
}

/**
 * Insert or replace top-level managed keys while preserving comments.
 *
 * A key that already exists but is not recorded as ours is a conflict, never a silent overwrite:
 * `plugin`, `lsp` and `formatter` are keys a person configures, and taking one over because it has
 * a familiar name is exactly how a harness breaks an editor setup it did not create.
 */
export function upsertManagedKeys(text, updates, ownedKeys = []) {
  const owned = new Set(ownedKeys);
  const current = parseJsonc(text);
  const insertions = [];
  const replacements = [];
  const conflicts = [];
  for (const [key, value] of Object.entries(updates)) {
    const has = Object.hasOwn(current, key);
    if (has) {
      if (JSON.stringify(current[key]) === JSON.stringify(value)) continue;
      const span = topLevelValueSpan(text, key);
      if (!span) {
        conflicts.push(key);
        continue;
      }
      if (!owned.has(key)) {
        conflicts.push(key);
        continue;
      }
      replacements.push({ span, key, value });
      continue;
    }
    insertions.push({ key, value });
  }
  if (conflicts.length) return { text, changed: [], conflicts };

  let out = text;
  const changed = [];
  for (const { span, key, value } of replacements.sort((a, b) => b.span.valueStart - a.span.valueStart)) {
    out = `${out.slice(0, span.valueStart)}${renderValue(value, "  ")}${out.slice(span.valueEnd)}`;
    changed.push({ key, kind: "replace" });
  }
  // New keys are inserted in reverse so the final text lists them in `updates` order. Inserting
  // immediately after the opening brace — rather than before the closing one — is what keeps a
  // trailing `// note` on the last existing value intact: text is never placed inside a comment.
  for (const { key, value } of [...insertions].reverse()) {
    out = insertTopLevel(out, key, value);
    changed.push({ key, kind: "insert" });
  }
  return { text: out, changed, conflicts: [] };
}

/**
 * Merge the autonomous permission posture into a config, additively.
 *
 * `permission` is operator posture, not a key this installer owns. Kilo's own resolution is
 * last-match-wins, and a person tunes `permission.bash` and `permission.edit` per machine; a
 * harness that recognised the name and replaced the object is how somebody's approval workflow
 * gets deleted without a word. So every sub-key this writes is written only when the operator has
 * not declared it, a `permission` that is not an object is a conflict rather than a value to
 * replace, and the merged object is never recorded as ours — uninstall leaves it where the
 * operator can find it, the same rule Cursor's `permissions.json` follows.
 *
 * Returns the sub-keys actually added, so a caller can report which posture this run introduced
 * without claiming the operator's existing rules as its own.
 */
export function mergeConfigPermission(text, permission) {
  const current = parseJsonc(text);
  const existing = current.permission;
  if (
    existing !== undefined &&
    (existing === null || typeof existing !== "object" || Array.isArray(existing))
  ) {
    return { text, changed: [], conflicts: ["permission"] };
  }
  const base = existing ?? {};
  const additions = {};
  for (const [key, value] of Object.entries(permission)) {
    if (Object.hasOwn(base, key)) continue;
    additions[key] = value;
  }
  const added = Object.keys(additions);
  if (!added.length) return { text, changed: [], conflicts: [] };

  const merged = { ...base, ...additions };
  const span = topLevelValueSpan(text, "permission");
  if (!span) {
    const inserted = upsertManagedKeys(text, { permission: merged }, []);
    return { text: inserted.text, changed: added, conflicts: inserted.conflicts };
  }
  const out = `${text.slice(0, span[0])}${renderValue(merged, "  ")}${text.slice(span[1])}`;
  return { text: out, changed: added, conflicts: [] };
}

/** The offset of the object's opening `{`, ignoring comments and strings. */
export function objectOpen(text) {
  let i = 0;
  let inString = false;
  let quote = "";
  while (i < text.length) {
    const ch = text[i];
    const next = text[i + 1];
    if (inString) {
      if (ch === "\\") {
        i += 2;
        continue;
      }
      if (ch === quote) inString = false;
      i += 1;
      continue;
    }
    if (ch === "/" && next === "/") {
      while (i < text.length && text[i] !== "\n") i += 1;
      continue;
    }
    if (ch === "/" && next === "*") {
      i += 2;
      while (i < text.length && !(text[i] === "*" && text[i + 1] === "/")) i += 1;
      i += 2;
      continue;
    }
    if (ch === '"' || ch === "'") {
      inString = true;
      quote = ch;
      i += 1;
      continue;
    }
    if (ch === "{") return i;
    i += 1;
  }
  return -1;
}

function insertTopLevel(text, key, value) {
  const open = objectOpen(text);
  if (open === -1) throw new Error("Kilo config object has no opening brace");
  const indent = "  ";
  const rendered = `${indent}"${key}": ${renderValue(value, indent)}`;
  const rest = text.slice(open + 1);
  const isEmpty = stripJsonc(rest).trim() === "}";
  const body = isEmpty ? `\n${rendered}\n` : `\n${rendered},`;
  return `${text.slice(0, open + 1)}${body}${rest}`;
}

/**
 * Delete top-level managed keys, leaving comments and neighbouring keys intact.
 *
 * Used by uninstall: a rollback that removes the artefacts but leaves `formatter: false` in a
 * person's config is not a rollback — it is the harness still speaking after it was removed.
 */
export function removeManagedKeys(text, keys) {
  let out = text;
  for (const key of keys) {
    const span = topLevelKeySpan(out, key);
    if (!span) continue;
    // Prefer removing the key together with the comma that follows it. When it is the last key,
    // remove the comma before it instead. Falls back to the value alone for a single-key object.
    let start = span.keyStart;
    let end = span.valueEnd;
    const after = out.slice(end);
    const commaAfter = /^\s*,/.exec(after);
    if (commaAfter) {
      end += commaAfter[0].length;
    } else {
      const before = out.slice(0, start);
      const commaBefore = /,\s*(?:\/\/[^\n]*\n\s*|\/\*[\s\S]*?\*\/\s*)*$/.exec(before);
      if (commaBefore) start -= commaBefore[0].length;
    }
    out = `${out.slice(0, start)}${out.slice(end)}`;
  }
  return out;
}

export function readText(path) {
  try {
    return readFileSync(path, "utf8");
  } catch {
    return "";
  }
}

export function isFile(path) {
  try {
    return statSync(path).isFile();
  } catch {
    return false;
  }
}
