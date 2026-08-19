/**
 * Shared helpers for generating Codex CLI artefacts from the plugin's own files.
 *
 * The rule this module exists to hold: **there is one source of truth per artefact.**
 * Codex hooks are generated from `.claude-plugin/plugin.json`, Codex subagents from
 * `agents/*.md`, Codex skills from `skills/` and `commands/`. Nothing is maintained twice —
 * a second hand-written list is exactly the divergence this plugin was built to end.
 */

import { readFileSync, writeFileSync, mkdirSync, readdirSync, statSync, copyFileSync } from "node:fs";
import { dirname, join, relative } from "node:path";

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
    data[key] = value === "" ? [] : splitInline(value);
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

// `tools: Read, Glob, Grep` is a list; `description: "a, b"` is not.
function splitInline(value) {
  const v = unquote(value);
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

export function copyTree(from, to, skip = () => false) {
  const written = [];
  for (const entry of readdirSync(from)) {
    const src = join(from, entry);
    const dst = join(to, entry);
    if (skip(src, entry)) continue;
    if (statSync(src).isDirectory()) {
      written.push(...copyTree(src, dst, skip));
    } else {
      mkdirSync(dirname(dst), { recursive: true });
      copyFileSync(src, dst);
      written.push(dst);
    }
  }
  return written;
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

export function rel(root, path) {
  const r = relative(root, path);
  return r.startsWith("..") ? path : r;
}
