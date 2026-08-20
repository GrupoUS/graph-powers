/**
 * Syntax gate for `workflows/*.js`.
 *
 * `node --check` refuses these files, and correctly: they use a top-level `return`, which is legal
 * only because the workflow runtime wraps the body in an async function before evaluating it. So
 * the check has to wrap them the same way. Without this gate there is none at all — a stray
 * backtick inside one of the prompt template literals is invisible until a run starts and has
 * already spent agents.
 *
 * It also asserts the two things the runtime needs to find the workflow: an `export const meta`
 * with a `name`, and that the name matches the filename. A mismatch does not fail loudly at
 * startup; the workflow is simply registered under a name nobody calls.
 */
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { basename, join } from "node:path";

/**
 * A workflow spawns the plugin's agents by their namespaced name (`graph-powers:explorer`), and
 * keeps the set of plugin-owned names in a literal so a project's own agent passes through
 * unprefixed. That literal is a second copy of what `agents/` already says, and a second copy is
 * what this repository exists to prevent — so it is checked rather than trusted. A name here that
 * is not on disk loses its namespace silently and fails at spawn time; a name on disk that is
 * missing here gets no namespace and does the same.
 */
function checkAgentSet(path, source, onDisk) {
  const block = source.match(/const PLUGIN_AGENTS = new Set\(\[([\s\S]*?)\]\)/);
  if (!block) return []; // a workflow that spawns nothing needs no set
  const listed = new Set([...block[1].matchAll(/'([^']+)'/g)].map((m) => m[1]));
  const problems = [];
  for (const name of listed)
    if (!onDisk.has(name))
      problems.push(`AGENTS ${path}: PLUGIN_AGENTS lists "${name}", which is not in agents/`);
  for (const name of onDisk)
    if (!listed.has(name))
      problems.push(
        `AGENTS ${path}: agents/${name}.md exists but PLUGIN_AGENTS omits it — a spawn of it would go unnamespaced`,
      );
  return problems;
}

/**
 * Dry-run a workflow with every runtime hook stubbed.
 *
 * Parsing proves the file is syntactically legal. It does not prove the script RUNS: a typo in a
 * variable name, a helper used before it is defined, a destructure of something the schema never
 * returns — none of that shows up until a real run has already spent agents on it.
 *
 * So the body is executed against stubs. `agent()` returns a minimal object synthesised from the
 * schema it was given, so downstream code sees the shape it expects. Nothing is spawned, nothing
 * is read, nothing costs anything. A ReferenceError here is a bug that would otherwise surface
 * halfway through a paid run.
 *
 * What this does NOT prove: that the prompts are good, that the schema matches what a real agent
 * would return, or that the logic is correct. It proves the script survives its own control flow.
 */
function sampleFor(schema) {
  if (!schema || typeof schema !== "object") return {};
  if (schema.enum?.length) return schema.enum[0];
  switch (schema.type) {
    case "string":
      return "x";
    case "number":
    case "integer":
      return 1;
    case "boolean":
      return true;
    case "array":
      return [sampleFor(schema.items ?? {})];
    default: {
      const out = {};
      for (const [key, sub] of Object.entries(schema.properties ?? {})) out[key] = sampleFor(sub);
      return out;
    }
  }
}

// Executing the script IS the check: a workflow that parses but throws on the first `agent()` call
// is a workflow nobody can run, and only running it finds that. The cost is stated rather than
// hidden: `new Function` gives the body the ambient globals — `process`, `fetch`, dynamic `import`
// — and the scope below shadows six names rather than removing anything. `node:vm` would not change
// that; the Node documentation is explicit that it is not a security boundary. What bounds this is
// the CI job: `permissions: contents: read`, no secrets on a fork's pull request, and an ephemeral
// runner. Do not run this gate against a workflow directory you did not review.
async function dryRun(body, args) {
  const spawned = [];
  const scope = {
    args,
    budget: { total: null, spent: () => 0, remaining: () => Infinity },
    log: () => {},
    phase: () => {},
    agent: async (prompt, opts = {}) => {
      if (typeof prompt !== "string" || !prompt.trim())
        throw new Error(`empty prompt at ${spawned.length}`);
      spawned.push(opts.agentType ?? "(inherited)");
      return opts.schema ? sampleFor(opts.schema) : "ok";
    },
    parallel: async (thunks) => Promise.all(thunks.map((t) => t())),
    pipeline: async (items, ...stages) => {
      const out = [];
      for (const [i, item] of items.entries()) {
        let value = item;
        // Sequential on purpose: a stage consumes the previous stage's result, so awaiting inside
        // the loop is the contract the real runtime implements, not an accidental serialisation.
        // oxlint-disable-next-line no-await-in-loop
        for (const stage of stages) value = await stage(value, item, i);
        out.push(value);
      }
      return out;
    },
    workflow: async () => ({}),
  };
  const names = Object.keys(scope);
  const fn = new Function(...names, `return (async function(){\n${body}\n})()`);
  const result = await fn(...names.map((n) => scope[n]));
  return { result, spawned };
}

/**
 * Two modes, one check.
 *
 *   node .github/check_workflows.mjs                 the gate: every file in workflows/
 *   node .github/check_workflows.mjs <file> [...]    one script, before it is ever run
 *
 * The second mode exists because the failure this file was written to catch does not only happen
 * to workflows that ship. A script authored inline for a single run — the shape `Workflow({script})`
 * takes — reaches the runtime unparsed, and a stray backtick inside one of its prompt template
 * literals surfaces as `Unexpected token (156:63)` with a caret pointing at prose. By then the call
 * has failed and whatever the script was orchestrating has to be re-authored from scratch.
 *
 * The `Workflow` tool writes every inline script to a file and returns its `scriptPath`, so the
 * loop that avoids this is: write the script to a file, run it past this, then invoke it by path.
 *
 * Explicit-path mode drops the two checks that only make sense for a shipped workflow — the
 * filename/`meta.name` agreement and the refuses-empty-args guard — because a one-run script is not
 * registered under a name and has no contract to refuse. What it keeps is what actually breaks:
 * the parse, and the dry run.
 */
const EXPLICIT = process.argv.slice(2).filter((a) => !a.startsWith("-"));
const CHECKING_ONE_OFF = EXPLICIT.length > 0;

const DIR = "workflows";
if (!CHECKING_ONE_OFF && !existsSync(DIR)) {
  console.log("no workflows/ directory — nothing to check");
  process.exit(0);
}

const files = CHECKING_ONE_OFF
  ? EXPLICIT
  : readdirSync(DIR)
      .filter((f) => f.endsWith(".js"))
      .sort();
if (files.length === 0) {
  console.error(
    "workflows/ exists but is empty — a shipped directory with no content is a broken promise",
  );
  process.exit(1);
}

for (const f of files) {
  if (CHECKING_ONE_OFF && !existsSync(f)) {
    console.error(`MISSING ${f}: no such file`);
    process.exit(1);
  }
}

const agentsOnDisk = existsSync("agents")
  ? new Set(
      readdirSync("agents")
        .filter((f) => f.endsWith(".md"))
        .map((f) => basename(f, ".md")),
    )
  : new Set();

let failed = 0;
for (const file of files) {
  const path = CHECKING_ONE_OFF ? file : join(DIR, file);
  const source = readFileSync(path, "utf8");

  // Same wrapper the runtime applies: strip the ESM export (an `export` is illegal inside a
  // function body) and evaluate the rest as an async function body.
  const body = source.replace(/^export\s+const\s+meta\s*=/m, "const meta =");
  try {
    // Compiling it IS the check — the function is never called, so it is built without `new`.
    Function(`return (async function(){\n${body}\n})`);
  } catch (error) {
    console.error(`SYNTAX ${path}: ${error.message}`);
    failed++;
    continue;
  }

  const declared = source.match(/name:\s*['"]([^'"]+)['"]/);
  if (!declared) {
    console.error(
      `META   ${path}: no \`name\` in \`export const meta\` — the runtime has nothing to register`,
    );
    failed++;
    continue;
  }
  // A one-off script is invoked by `scriptPath`, never by name, so the filename it happens to sit
  // under carries no meaning and disagreeing with `meta.name` breaks nothing.
  const expected = basename(file, ".js");
  if (!CHECKING_ONE_OFF && declared[1] !== expected) {
    console.error(`NAME   ${path}: meta.name is "${declared[1]}" but the file is "${expected}.js"`);
    failed++;
    continue;
  }

  const agentProblems = checkAgentSet(path, source, agentsOnDisk);
  if (agentProblems.length) {
    for (const problem of agentProblems) console.error(problem);
    failed++;
    continue;
  }

  // Every workflow here takes a string first argument (a task, or a plan path). Passing one
  // exercises the real path; passing nothing exercises the guard that should reject it.
  let spawnCount = 0;
  try {
    // One workflow at a time, so a failure names the file it came from without interleaving.
    // oxlint-disable-next-line no-await-in-loop
    const { spawned } = await dryRun(body, "dry-run/plan.md");
    spawnCount = spawned.length;
    const unnamespaced = [...new Set(spawned)].filter(
      (a) => a !== "(inherited)" && !a.includes(":") && agentsOnDisk.has(a),
    );
    if (unnamespaced.length) {
      console.error(
        `SPAWN  ${path}: spawns ${unnamespaced.join(", ")} without the plugin namespace`,
      );
      failed++;
      continue;
    }
  } catch (error) {
    console.error(`RUN    ${path}: ${error.message}`);
    failed++;
    continue;
  }

  // A shipped workflow must refuse an empty invocation; a one-off script written for one known set
  // of arguments has no such contract, and demanding one would fail every correct ad-hoc script.
  if (!CHECKING_ONE_OFF) {
    try {
      // oxlint-disable-next-line no-await-in-loop
      await dryRun(body, undefined);
      console.error(
        `GUARD  ${path}: ran with no args instead of refusing — a missing plan path or task must throw before any spawn`,
      );
      failed++;
      continue;
    } catch {
      // Expected: the input guard fired.
    }
  }

  console.log(
    CHECKING_ONE_OFF
      ? `ok     ${path} (${declared[1]}) — parses, runs dry in ${spawnCount} stubbed spawns`
      : `ok     ${path} (${declared[1]}) — parses, runs dry in ${spawnCount} stubbed spawns, refuses empty args`,
  );
}

if (failed) {
  console.error(`\n${failed} workflow file(s) failed`);
  process.exit(1);
}
console.log(
  CHECKING_ONE_OFF
    ? `\n${files.length} script(s) parse and survive a dry run — safe to hand to Workflow`
    : `\n${files.length} workflow(s) parse, and every meta.name matches its file`,
);
