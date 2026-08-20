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
 *
 * That second assertion used to be `source.match(/name:\s*['"]([^'"]+)['"]/)` over the whole file,
 * which asserts something else entirely: that SOME `name: '<stem>'` literal exists somewhere in the
 * text. A `meta` with no `name` at all passed as long as any later object — an agent schema, a
 * phase, a prompt — happened to carry one. `readMeta` below reads the `meta` literal itself.
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
 * The end of the string literal that opens at `start`, or -1 if it never closes.
 *
 * Brace counting that does not know about strings is brace counting that is wrong here: two of the
 * three shipped workflows carry `Pass { planPath, config }` inside `meta.whenToUse`, and one carries
 * an escaped quote (`the project\'s plan directory`). Both would end the literal early.
 */
function endOfString(text, start) {
  const quote = text[start];
  for (let i = start + 1; i < text.length; i++) {
    if (text[i] === "\\") {
      i++;
      continue;
    }
    if (text[i] === quote) return i;
  }
  return -1;
}

/**
 * The index of the `}` that closes the object opening at `open`, or -1.
 *
 * Bounded on purpose: this is not a JavaScript parser, it is a brace matcher that knows about
 * strings and comments. `.claude/rules/artifacts.md` requires `meta` to be a pure literal — "no
 * variable, call, spread or interpolation" — which is exactly the grammar this can read, and
 * anything outside it is refused below rather than guessed at.
 */
function closingBrace(text, open) {
  let depth = 0;
  for (let i = open; i < text.length; i++) {
    const c = text[i];
    if (c === "'" || c === '"' || c === "`") {
      const end = endOfString(text, i);
      if (end === -1) return -1;
      i = end;
      continue;
    }
    if (c === "/" && text[i + 1] === "/") {
      const nl = text.indexOf("\n", i);
      if (nl === -1) return -1;
      i = nl;
      continue;
    }
    if (c === "/" && text[i + 1] === "*") {
      const end = text.indexOf("*/", i + 2);
      if (end === -1) return -1;
      i = end + 1;
      continue;
    }
    if (c === "{" || c === "[") depth++;
    else if (c === "}" || c === "]") {
      depth--;
      if (depth === 0) return i;
    }
  }
  return -1;
}

/**
 * `meta.name`, read from the `meta` literal and from nowhere else.
 *
 * Only a TOP-LEVEL `name` counts. `meta.phases` is an array of objects and a phase is free to be
 * called anything; the whole-file regex this replaces would happily have registered a workflow
 * under a phase's title, or under a `name` field of an agent output schema three hundred lines
 * down. Depth tracking is what makes the difference.
 *
 * A computed `meta` FAILS rather than being skipped. The runtime reads `meta` before the body runs,
 * so a spread, a variable or a call there does not register under a different name — it does not
 * register at all, and a gate that stays quiet about it is worse than no gate.
 */
function readMeta(source) {
  // `\s*` and not `[ \t]*`: a CRLF checkout puts a `\r` everywhere this pattern would otherwise
  // have to stop, and the whole file's docstring is about matches that anchor to `\n` and then
  // never fire on Windows.
  const decl = /(?:^|\n)\s*(?:export\s+)?const\s+meta\s*=\s*/.exec(source);
  if (!decl) return { error: "no `export const meta` — the runtime has nothing to register" };
  const open = decl.index + decl[0].length;
  if (source[open] !== "{")
    return {
      error:
        "`meta` is not an object literal — the runtime reads it before the body runs, so a variable, a call or a spread never resolves and the workflow registers under nothing",
    };
  const close = closingBrace(source, open);
  if (close === -1) return { error: "the `meta` object literal is never closed" };
  const literal = source.slice(open, close + 1);
  if (literal.includes("..."))
    return {
      error:
        "`meta` spreads another object — it has to be a pure literal, because the runtime reads it before anything exists to spread from",
    };

  let depth = 0;
  for (let i = 0; i < literal.length; i++) {
    if (depth === 1 && !/[\w$]/.test(literal[i - 1] ?? "")) {
      const key = /^(['"]?)name\1\s*:\s*/.exec(literal.slice(i));
      if (key) {
        const at = i + key[0].length;
        const quote = literal[at];
        if (quote !== "'" && quote !== '"' && quote !== "`")
          return {
            error:
              "`meta.name` is not a string literal — the runtime reads `meta` before the body runs, so a variable, a call or an expression there resolves to nothing",
          };
        const end = endOfString(literal, at);
        if (end === -1) return { error: "the `meta.name` string is never closed" };
        const value = literal.slice(at + 1, end);
        if (quote === "`" && value.includes("${"))
          return {
            error:
              "`meta.name` interpolates — nothing is in scope when the runtime reads `meta`, so the name it registers is not the name you wrote",
          };
        return { name: value };
      }
    }
    const c = literal[i];
    if (c === "'" || c === '"' || c === "`") {
      const end = endOfString(literal, i);
      if (end === -1) return { error: "an unterminated string inside `meta`" };
      i = end;
    } else if (c === "/" && literal[i + 1] === "/") {
      const nl = literal.indexOf("\n", i);
      if (nl === -1) break;
      i = nl;
    } else if (c === "/" && literal[i + 1] === "*") {
      const end = literal.indexOf("*/", i + 2);
      if (end === -1) break;
      i = end + 1;
    } else if (c === "{" || c === "[") depth++;
    else if (c === "}" || c === "]") depth--;
  }
  return { error: "`meta` has no top-level `name` — the runtime has nothing to register" };
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
// — and the scope below shadows eight names rather than removing anything. `node:vm` would not
// change that; the Node documentation is explicit that it is not a security boundary. So the
// simulator is strictly MORE privileged than the thing it simulates: the real workflow runtime has
// no `fs` and no `require` (`.claude/rules/artifacts.md § Workflow scripts`), while here `require`
// is indeed undefined but `await import('node:fs')` returns the module and writes to disk —
// measured, not assumed.
//
// The boundary, for both modes, because naming only one of them was the defect:
//
//   DIRECTORY mode runs it, and the files are the repository's own — reviewed, versioned, and in
//   CI bounded further by `permissions: contents: read`, no secrets on a fork's pull request and an
//   ephemeral runner. Do not point this mode at a workflows/ directory you did not review.
//
//   EXPLICIT-PATH mode does NOT run it unless `--run` is passed. That mode's whole purpose is "one
//   script, before it is ever run" — a body nobody has vouched for yet, frequently one a model just
//   wrote — and executing it to prove it is safe to execute is the question begging its own answer.
//   Parse-only is the default there; `--run` is the operator saying they read the file.
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
 *   node .github/check_workflows.mjs <file> [...]    one script, before it is ever run — PARSE ONLY
 *   node .github/check_workflows.mjs <file> --run    ...and execute its body against the stubs
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
 * registered under a name and has no contract to refuse.
 *
 * It also does not EXECUTE the body unless `--run` says so, and that is not caution for its own
 * sake. The dry run is `new Function` with the ambient globals (see `dryRun`), and this mode is
 * pointed at exactly the file nobody has vouched for yet — the one a model wrote a minute ago, the
 * one whose contents are the open question. "Check this before it runs" cannot be implemented by
 * running it. So the default here is the parse, which catches the failure this mode was built for
 * (the stray backtick), and `--run` is the operator stating they read the file and want the rest:
 * a helper used before it is defined, a destructure of a field the schema never returns, a typo in
 * a variable name.
 */
const EXPLICIT = process.argv.slice(2).filter((a) => !a.startsWith("-"));
const CHECKING_ONE_OFF = EXPLICIT.length > 0;
const RUN_REQUESTED = process.argv.slice(2).includes("--run");
// Directory mode always executes: those files are in the repository and reviewed, and the dry run
// is the check they exist for.
const WILL_EXECUTE = !CHECKING_ONE_OFF || RUN_REQUESTED;

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

if (CHECKING_ONE_OFF && RUN_REQUESTED)
  console.log(
    "--run: the body of each file below is EXECUTED in this process. The stubs replace the workflow runtime, not the platform — `process`, `fetch`, `globalThis` and `await import('node:fs')` all stay reachable, and the real runtime has none of them. Pass this only for a file you have read.",
  );

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

  const meta = readMeta(source);
  if (meta.error) {
    console.error(`META   ${path}: ${meta.error}`);
    failed++;
    continue;
  }
  // A one-off script is invoked by `scriptPath`, never by name, so the filename it happens to sit
  // under carries no meaning and disagreeing with `meta.name` breaks nothing.
  const expected = basename(file, ".js");
  if (!CHECKING_ONE_OFF && meta.name !== expected) {
    console.error(`NAME   ${path}: meta.name is "${meta.name}" but the file is "${expected}.js"`);
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
  if (WILL_EXECUTE) {
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

  if (!CHECKING_ONE_OFF)
    console.log(
      `ok     ${path} (${meta.name}) — parses, runs dry in ${spawnCount} stubbed spawns, refuses empty args`,
    );
  else if (WILL_EXECUTE)
    console.log(`ok     ${path} (${meta.name}) — parses, runs dry in ${spawnCount} stubbed spawns`);
  else
    console.log(
      `ok     ${path} (${meta.name}) — parses. The body was NOT executed; add --run to dry-run it, which executes this file's code here.`,
    );
}

if (failed) {
  console.error(`\n${failed} workflow file(s) failed`);
  process.exit(1);
}
if (!CHECKING_ONE_OFF)
  console.log(`\n${files.length} workflow(s) parse, and every meta.name matches its file`);
else if (WILL_EXECUTE)
  console.log(`\n${files.length} script(s) parse and survive a dry run — safe to hand to Workflow`);
else
  console.log(
    `\n${files.length} script(s) parse — which is what catches the stray backtick. Nothing was executed: add --run, for a file you have read, to also exercise the control flow.`,
  );
