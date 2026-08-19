/**
 * Shared helpers for generating Codex CLI artefacts from the plugin's own files.
 *
 * The rule this module exists to hold: **there is one source of truth per artefact.**
 * Codex hooks are generated from `.claude-plugin/plugin.json`, Codex subagents from
 * `agents/*.md`, Codex skills from `skills/` and `commands/`. Nothing is maintained twice —
 * a second hand-written list is exactly the divergence this plugin was built to end.
 */

import { readFileSync, writeFileSync, mkdirSync, readdirSync, statSync, copyFileSync } from "node:fs";
import { dirname, join } from "node:path";

// ── frontmatter ──────────────────────────────────────────────────────────────

/**
 * Minimal YAML frontmatter reader. Handles the shapes this repository actually uses:
 * `key: value`, quoted values, and block sequences (`- item`). Deliberately not a YAML
 * parser — a dependency here would ship into every install, and the schema is ours.
 */
export function parseFrontmatter(text) {
  const m = /^---\n([\s\S]*?)\n---\n?/.exec(text);
  if (!m) return { data: {}, body: text };

  const data = {};
  let key = null;
  for (const raw of m[1].split("\n")) {
    if (!raw.trim() || raw.trimStart().startsWith("#")) continue;

    const item = /^\s+-\s+(.*)$/.exec(raw);
    if (item && key) {
      (data[key] ||= []).push(unquote(item[1].trim()));
      continue;
    }
    const pair = /^([A-Za-z_][\w-]*)\s*:\s*(.*)$/.exec(raw);
    if (!pair) continue;
    key = pair[1];
    const value = pair[2].trim();
    data[key] = value === "" ? [] : splitInline(key, value);
  }
  return { data, body: text.slice(m[0].length) };
}

function unquote(s) {
  const t = s.trim();
  if ((t.startsWith('"') && t.endsWith('"')) || (t.startsWith("'") && t.endsWith("'"))) {
    return t.slice(1, -1);
  }
  return t;
}

/**
 * `tools: Read, Glob, Grep` is a list. A description is not — and descriptions are full of
 * commas, which is the whole point of them.
 *
 * Splitting on the comma alone was wrong in the direction that matters: it turned every
 * multi-clause `description:` into an array, and the generated Codex skill then carried a
 * description that stopped at the first comma. A skill nobody can find is a skill that is not
 * installed. So the shape is decided by the key, from a list this repository controls, and
 * anything unknown stays a string.
 */
const LIST_KEYS = new Set([
  "tools", "allowed-tools", "allowedTools", "disallowedTools", "skills", "triggers", "keywords",
]);

function splitInline(key, value) {
  const v = unquote(value);
  if (!LIST_KEYS.has(key)) return v;
  if (value.startsWith('"') || value.startsWith("'")) return v;
  if (!v.includes(",")) return v;
  return v.split(",").map((s) => s.trim()).filter(Boolean);
}

export function asList(value) {
  if (value === undefined || value === null) return [];
  return Array.isArray(value) ? value : [value];
}

// ── TOML ─────────────────────────────────────────────────────────────────────

export function tomlString(value) {
  return `"${String(value).replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\n/g, "\\n")}"`;
}

/** Multi-line literal when the body allows it; escaped basic string otherwise. */
export function tomlBlock(value) {
  const body = String(value).replace(/\r\n/g, "\n").trimEnd();
  if (!body.includes("'''")) return `'''\n${body}\n'''`;
  return `"""\n${body.replace(/\\/g, "\\\\").replace(/"""/g, '\\"\\"\\"')}\n"""`;
}

// ── filesystem ───────────────────────────────────────────────────────────────

export function readJson(path, fallback = null) {
  try {
    return JSON.parse(readFileSync(path, "utf8"));
  } catch {
    return fallback;
  }
}

export function writeFile(path, contents) {
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, contents, "utf8");
}

/** Text files a `transform` is allowed to touch. Anything else is copied byte for byte. */
const TEXT_EXT = /\.(md|markdown|json|toml|ya?ml|txt|py|mjs|js|ts|sh)$/i;

/**
 * Copy a directory. `transform(contents, src)` rewrites text files on the way through.
 *
 * The transform exists for one reason: `${CLAUDE_PLUGIN_ROOT}` is a Claude Code variable, and
 * Codex never sets it. Copying skills across verbatim left every cross-reference pointing at a
 * literal that resolves to nothing — the reference reads as present and loads as empty.
 */
export function copyTree(from, to, skip = () => false, transform = null) {
  const written = [];
  for (const entry of readdirSync(from)) {
    const src = join(from, entry);
    const dst = join(to, entry);
    if (skip(src, entry)) continue;
    if (statSync(src).isDirectory()) {
      written.push(...copyTree(src, dst, skip, transform));
      continue;
    }
    mkdirSync(dirname(dst), { recursive: true });
    copyOne(src, dst, transform && TEXT_EXT.test(entry) ? transform : null);
    written.push(dst);
  }
  return written;
}

/** One file. A binary, or a text file that could not be read as text, is copied byte for byte. */
function copyOne(src, dst, transform) {
  if (transform) {
    try {
      writeFileSync(dst, transform(readFileSync(src, "utf8"), src), "utf8");
      return;
    } catch { /* not readable as text — fall through to the byte copy */ }
  }
  copyFileSync(src, dst);
}

/**
 * Resolve the Claude-only plugin-root variable to the paths Codex actually reads.
 *
 * Each subtree lands somewhere different on the Codex side, so one blanket substitution would be
 * wrong for two of the three: skills become `~/.agents/skills/`, shared references become
 * `~/.codex/graph-powers/`, and everything else still lives in the installed plugin directory.
 */
export function rewriteForCodex(text, { skillsRef, referencesRef, pluginRoot }) {
  return String(text)
    .replaceAll("${CLAUDE_PLUGIN_ROOT}/skills", skillsRef)
    .replaceAll("${CLAUDE_PLUGIN_ROOT}/references", referencesRef)
    .replaceAll("${CLAUDE_PLUGIN_ROOT}", pluginRoot);
}

export function listDirs(dir) {
  try {
    return readdirSync(dir).filter((f) => {
      try {
        return statSync(join(dir, f)).isDirectory();
      } catch {
        return false;
      }
    }).sort();
  } catch {
    return [];
  }
}

export function listMarkdown(dir) {
  try {
    return readdirSync(dir).filter((f) => f.endsWith(".md")).sort();
  } catch {
    return [];
  }
}
