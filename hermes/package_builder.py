#!/usr/bin/env python3
"""Build-only static dependency closure; never import a plugin or run copied code.

Markdown links and concrete plugin paths are resolved before translation. Python local
imports and ESM relative imports are read as syntax. The two bundled scripts with computed
source-root reads declare those dependencies below; unknown dynamic imports fail closed.
Host-project examples and historical ledgers are recorded separately from package edges.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
import sys
from io import TextIOWrapper
from pathlib import Path, PurePosixPath

PLUGIN_TOKEN = "${CLAUDE_PLUGIN_ROOT}"
CONTENT = "skills/content/"
EXTENSIONS = r"(?:md|py|mjs|js|json|ya?ml|txt|toml)"
PATH_TOKEN = re.compile(
    rf"(?:\$\{{CLAUDE_PLUGIN_ROOT\}}/)?(?:\.\.?/)*"
    rf"(?:[.\w-]+/)*[.\w-]+\.{EXTENSIONS}(?![\w.])(?:#[\w-]+)?"
)
ROOTED = ("references/", "scripts/", "skills/", "agents/", "commands/", "schema/", "templates/")
HOST_NAMES = {
    "AGENTS.md", "CLAUDE.md", "GEMINI.md", "README.md", "DESIGN.md", "PRODUCT.md",
    "REVIEW.md", "PLAN.md", "HANDOFF.md", "SKILL.md", "package.json", "tsconfig.json",
    "settings.json", "config.json", "config.yaml", "pyproject.toml", "requirements.txt",
    "config.toml", "settings.local.json", "PROGRESS.md", "MEMORY.md", "spec.md",
    "task-reviews.md", "dispatches.json", "NNN-short-slug.md", "path-to-script.js",
    "llms.txt", "robots.txt", "Robots.txt", "tsserver.js", "Express.js",
}
HOST_PREFIXES = (".graph-powers/", ".claude/", ".codex/", ".agents/", ".zed/", "docs/",
                 "src/", "app/", "apps/", "packages/", "tests/", "test/", "dist/", "build/",
                 ".vercel/", "graft/.graph/")

# These are dependency edges, not a second public registration inventory. Both files compute
# their source root and read these paths at runtime; retain that topology in content/.
COMPUTED_INPUTS = {
    "skills/planning/scripts/sdd.py": {
        "paths": ["schema/config.schema.json"],
        "globs": ["agents/*.md", "skills/*/SKILL.md"],
        "reason": "SOURCE_PLUGIN_ROOT, PLUGIN_SCHEMA, AGENTS_DIR and SKILLS_DIR reads",
    },
    ".github/check_workflows.mjs": {
        "paths": ["schema/config.schema.json"],
        "globs": ["agents/*.md", "workflows/*.js"],
        "reason": "loadAgentModels, canonical workflow and configuration checks",
    },
}

# Hermes is a projection, not a second canonical source. These source-specific rewrites preserve
# the upstream rule while naming the equivalent Hermes boundary. Each expected source fragment is
# checked before projection so a canonical wording change cannot silently produce a stale adapter.
SEMANTIC_PROJECTIONS = {
    "commands/evolve.md": [(
        "Update the nearest applicable `AGENTS.md` only when the learning is a reusable project rule. If no suitable node exists or it exceeds its budget, load `skill_view(\"graph-powers:intent-layer\")` before adding a node. Otherwise append problem, cause and solution; do not duplicate guidance.",
        "When the learning is a reusable project rule, propose a diff for the nearest applicable `AGENTS.md` and request explicit approval before changing it. If no suitable node exists or it exceeds its budget, load `skill_view(\"graph-powers:intent-layer\")` to prepare that proposal. Do not automatically alter project instructions or configuration.",
    )],
    "schema/config.schema.json": [(
        "Keep refusing the operations git cannot undo, at any autonomy level: rm -rf on / or the home directory, mkfs, dd to a device, chmod -R 777 /, --no-preserve-root, DROP DATABASE, TRUNCATE, and force-pushing a protected branch. Deleting files inside a committed repository is not on this list — git restores those, so autonomous mode does it without asking. Set false to remove even this floor; nothing else in the harness will stop those commands.",
        "Keep refusing operations git cannot undo at any autonomy level: recursive deletion of the filesystem root or home directory, filesystem formatting or raw device writes, recursively opening permissions on the filesystem root, root-preservation bypasses, destructive database statements, and force-pushing a protected branch. Deleting files inside a committed repository is not on this list — git restores those, so autonomous mode does it without asking. Set false to remove even this floor; nothing else in the harness will stop those commands.",
    )],
    "skills/debugger/references/diagnose.md": [(
        "| **2** | **HTTP fixture** (curl) | `curl -sS -X POST ${project.stagingUrl}/api/<endpoint> -H \"authorization: Bearer $TOKEN\" -H \"content-type: application/json\" -d '<json>' \\| jq` | tRPC 500 / UNAUTHORIZED / payload edge case |",
        "| **2** | **HTTP fixture** (local test server) | deterministic synthetic request and response; no credential-like value in the command | tRPC 500 / UNAUTHORIZED / payload edge case |",
    ), (
        "**tRPC 500 repro:**\n```bash\n# Read the token with the Read tool and paste it in place of <token>. Never commit it; vault-only.\n# Not `curl … | jq`: in PowerShell `curl` is an alias of `Invoke-WebRequest`, which rejects `-s`,\n# and `jq` is not there at all — so on Windows this printed a parameter error, not a response body.\npython -X utf8 -c \"import json,urllib.request as u;r=u.Request('${project.stagingUrl}/api/<endpoint>',data=json.dumps({'0':{'json':{}}}).encode(),headers={'authorization':'Bearer <token>','content-type':'application/json'});print(json.dumps(json.load(u.urlopen(r)),indent=2))\"\n```",
        "**tRPC 500 repro:** First start the project's local test server with synthetic fixture data. Replace `8787` with its declared test port. This command contains no credential-like value. For a protected staging endpoint, authenticate only through an explicitly authorized host mechanism; otherwise record the missing authorization as the blocker.\n```bash\npython -X utf8 -c \"import json,urllib.request as u;r=u.Request('http://127.0.0.1:8787/api/<endpoint>',data=json.dumps({'0':{'json':{}}}).encode(),headers={'content-type':'application/json'});print(json.dumps(json.load(u.urlopen(r)),indent=2))\"\n```",
    ), (
        "**SSE leak / listener count probe:** hold the stream open and read it line by line, then disconnect\nand check the server's `listener.attach` / `listener.detach` pairs for that wid. Same reason as\nabove — a backgrounded `curl -N` is two POSIX-only constructs, the alias and the trailing `&`:\n```bash\npython -X utf8 -c \"import urllib.request as u;r=u.Request('${project.stagingUrl}/api/<stream-endpoint>',headers={'authorization':'Bearer <token>'});[print(l.decode('utf-8','replace').rstrip()) for l in u.urlopen(r)]\"\n```",
        "**SSE leak / listener count probe:** Start the project's local test server with synthetic stream events, then hold the stream open and read it line by line. Replace `8787` with its declared test port; disconnect and check the server's `listener.attach` / `listener.detach` pairs. For a protected staging stream, use only an explicitly authorized host authentication mechanism; otherwise stop with the authorization blocker.\n```bash\npython -X utf8 -c \"import urllib.request as u;[print(line.decode('utf-8','replace').rstrip()) for line in u.urlopen('http://127.0.0.1:8787/api/<stream-endpoint>')]\"\n```",
    )],
    "skills/debugger/references/turbo-dry-json-epipe.md": [(
        "**Validation:** `python3 https://github.com/GrupoUS/graph-powers/blob/main/hooks/test_hooks.py` — the deny cases for `--dry=json` and the\nallow cases for `bun run test` / `turbo run test --filter=…`. Script with no turbo\ninstalled: non-zero, stdout is not a JSON object.",
        "**Validation:** In an explicitly authorized Claude source checkout, run the Claude hook test for the deny cases for `--dry=json` and the allow cases for `bun run test` / `turbo run test --filter=…`. Hermes does not fetch or execute that external hook test. Its bundled script with no turbo installed exits non-zero and does not print a JSON object.",
    )],
    "skills/webapp-testing/references/browser-setup.md": [(
        "1. Read the host `.graph-powers/config.json`. Use `${project.stagingUrl}` as the target unless the\n   person supplies another URL in the current task. A missing target is a blocker. Never replace an\n   unavailable staging target with localhost without an explicit local-testing request.",
        "1. Read the host `.graph-powers/config.json`.\n   Target: `${project.stagingUrl}`.\n   Use that target unless the person supplies another URL in the current task. A missing target is a blocker. Never replace an unavailable staging target with localhost without an explicit local-testing request.",
    )],
    "references/shared/045-context-staging.md": [(
        "| Runtime / env | env vars, deploy config, runtime behaviour | the project's architecture notes if any, otherwise `skill_view(\"graph-powers:senior-architect\")` |",
        "| Runtime / environment | environment variables, deploy config, runtime behaviour | the project's architecture notes if any, otherwise `skill_view(\"graph-powers:senior-architect\")` |",
    )],
    "skills/planning/references/issue-triage.md": [(
        "(`auth|payment|PII|schema|env|ci|none`).",
        "(`auth`, `payment`, `PII`, `schema`, `env`, `ci`, or `none`).",
    ), (
        "RISK SURFACES: <auth|payment|PII|schema|env|ci|none>",
        "RISK SURFACES: <one of auth, payment, PII, schema, env, ci, none>",
    )],
}

HOOK_SOURCE_REASON = "external Claude hook source for inspection; Hermes never copies or executes hooks"
HOOK_SOURCE_URL = "https://github.com/GrupoUS/graph-powers/blob/main/"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_text(value) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


class PackageBuilder:
    def __init__(self, root: Path, request: dict):
        self.root = root.resolve()
        self.request = request
        self.sources: dict[str, bytes] = {}
        self.outputs: dict[str, str] = {}
        self.file_rows: list[dict] = []
        self.edges: list[dict] = []
        self.host_refs: list[dict] = []
        self.pending: list[str] = []
        self.names = {item["name"] for item in request["registrations"]}
        self.destinations: dict[str, str] = {}
        self.registration_by_source = {item["path"]: item["name"] for item in request["registrations"]}
        self.canonical_files = sorted(path.relative_to(self.root).as_posix()
            for directory in ("references", "skills", "agents", "commands", "hooks", "schema", "templates")
            for path in (self.root / directory).rglob("*") if path.is_file())

    def inside(self, path: Path) -> Path:
        try:
            path.resolve().relative_to(self.root)
        except ValueError:
            raise ValueError(f"source path escape: {path}") from None
        return path

    def read(self, source: str) -> bytes:
        path = self.inside(self.root / source)
        if not path.is_file():
            raise ValueError(f"required package source is missing: {source}")
        self.sources.setdefault(source, path.read_bytes())
        return self.sources[source]

    def enqueue(self, source: str) -> None:
        self.read(source)
        if source not in self.pending:
            self.pending.append(source)

    def edge(self, source: str, reference: str, target: str, kind="reference") -> None:
        self.edges.append({"from": source, "reference": reference, "to": target, "kind": kind})
        self.enqueue(target)

    def host(self, source: str, reference: str, reason: str) -> None:
        self.host_refs.append({"from": source, "reference": reference, "reason": reason})

    def resolve_reference(self, source: str, reference: str, *, required=False) -> str | None:
        explicit = reference.startswith(PLUGIN_TOKEN + "/")
        bare = reference.removeprefix(PLUGIN_TOKEN + "/").split("#", 1)[0]
        if explicit:
            candidates = [self.root / bare]
        elif bare.startswith(("./", "../")):
            candidates = [(self.root / source).parent / bare]
        else:
            owner = (self.root / source).parent
            candidates = [self.root / bare, owner / bare, owner.parent / bare, owner.parent.parent / bare]
        if explicit or bare.startswith(("./", "../")):
            for candidate in candidates:
                self.inside(candidate)
        else:
            candidates = [candidate for candidate in candidates if candidate.is_relative_to(self.root)]
            for candidate in candidates:
                self.inside(candidate)
        matches = {path.resolve().relative_to(self.root).as_posix()
                   for path in candidates if path.is_file()}
        if not matches and not explicit and not bare.startswith(("./", "../")):
            # The source often names a sibling script or shared reference by basename.
            # Prefer the skill's own namespace, then require a unique canonical suffix.
            suffix = "/" + bare
            suffixes = {item for item in self.canonical_files if item.endswith(suffix)}
            parts = PurePosixPath(source).parts
            if parts[0] == "skills" and len(parts) > 2:
                own = {item for item in suffixes if item.startswith(f"skills/{parts[1]}/")}
                suffixes = own or suffixes
            matches = suffixes
        if len(matches) > 1:
            raise ValueError(f"ambiguous package reference {reference} in {source}: {sorted(matches)}")
        if matches:
            return next(iter(matches))
        if required or explicit or bare.startswith(("./", "../", *ROOTED)):
            raise ValueError(f"unresolved required reference {reference} in {source}")
        return None

    def references(self, source: str, text: str) -> dict[int, tuple[str, str]]:
        resolved = {}
        # Real Markdown links have explicit file semantics. Backticks also contain command
        # examples, so only concrete plugin/relative paths there are required dependencies.
        link_targets = {match[0].strip("<>") for match in
                        re.findall(r"\]\(([^\s)]+)(?:\s+(['\"]).*?\2)?\)", text)}
        for match in PATH_TOKEN.finditer(text):
            reference = match.group()
            preceding = text[max(0, match.start() - 160):match.start()]
            token_prefix = re.split(r"[\s`\"'()<>]", preceding)[-1]
            if token_prefix and ("://" in token_prefix or token_prefix.endswith(":") or
                                 "${" in token_prefix or token_prefix.endswith(("/", "\\"))):
                self.host(source, reference, "external URL or caller-resolved host path")
                continue
            bare = reference.removeprefix(PLUGIN_TOKEN + "/").split("#", 1)[0]
            explicit = reference.startswith(PLUGIN_TOKEN + "/")
            required = reference in link_targets
            if not explicit and bare.startswith("-") and preceding.endswith(">"):
                self.host(source, reference, "suffix of a caller-supplied path placeholder")
                continue
            if source == "references/rubrics/skill-improver-rubric.md" and reference in {"plan_validator.py", "pre_write_guard.py"}:
                self.host(source, reference, "historical 2026-08-17 false-finding example, not an installed dependency")
                continue
            # Hooks belong to the Claude product boundary. Validate direct hooks/ references
            # before externalizing them, so a traversal-like spelling cannot become an exemption.
            if bare.startswith("hooks/"):
                try:
                    hook_target = self.resolve_reference(source, reference, required=True)
                except ValueError as error:
                    raise ValueError(f"invalid external hook source in {source}: {reference}") from error
                if hook_target is None or not hook_target.startswith("hooks/"):
                    raise ValueError(f"hook source escape in {source}: {reference}")
                self.host(source, reference, HOOK_SOURCE_REASON)
                resolved[match.start()] = (reference, HOOK_SOURCE_URL + hook_target)
                continue
            if source == "skills/senior-prompt-engineer/references/llm_evaluation_frameworks.md" and reference == "evals/README.md":
                self.host(source, reference, "documentation to create in the evaluated host project")
                continue
            if reference == "evals/evals.json" and source == "commands/evolve.md":
                for path in sorted((self.root / "skills").glob("*/evals/evals.json")):
                    self.edge(source, reference, path.relative_to(self.root).as_posix(), "selected-skill-evals")
                resolved[match.start()] = (reference, "skills/<selected-skill>/evals/evals.json")
                continue
            if source == "references/rubrics/skill-improver-rubric.md" and reference in {"evals/evals.json", "learning.md"}:
                self.host(source, reference, "rubric E1/E2: artifacts of the skill under audit")
                continue
            if (not explicit and not bare.startswith("templates/")
                    and PurePosixPath(bare).name in {"AGENTS.md", "CLAUDE.md"}):
                self.host(source, reference, "host-project instruction hierarchy, not installed plugin instructions")
                continue
            if not explicit and not required and (bare in HOST_NAMES or bare.startswith(HOST_PREFIXES)):
                self.host(source, reference, "host-project input or output, resolved by the caller")
                continue
            target = self.resolve_reference(source, reference, required=required)
            if target:
                if target.startswith("hooks/"):
                    self.host(source, reference, HOOK_SOURCE_REASON)
                    resolved[match.start()] = (reference, HOOK_SOURCE_URL + target)
                else:
                    resolved[match.start()] = (reference, target)
                    self.edge(source, reference, target)
            else:
                raise ValueError(f"unresolved reference {reference} in {source}; declare its concrete host boundary")
        return resolved

    def project(self, source: str, text: str) -> str:
        for expected, replacement in SEMANTIC_PROJECTIONS.get(source, []):
            if expected not in text:
                raise ValueError(f"stale Hermes semantic projection for {source}: expected source fragment is missing")
            text = text.replace(expected, replacement, 1)
        return text

    def script_dependencies(self, source: str, text: str) -> None:
        path = PurePosixPath(source)
        declaration = COMPUTED_INPUTS.get(source, {})
        for target in declaration.get("paths", []):
            self.edge(source, declaration["reason"], target, "computed-input")
        for pattern in declaration.get("globs", []):
            matches = sorted(self.root.glob(pattern))
            if not matches:
                raise ValueError(f"missing computed dependency {pattern} in {source}")
            for match in matches:
                self.edge(source, pattern, match.relative_to(self.root).as_posix(), "computed-input")
        if path.suffix == ".py":
            tree = ast.parse(text, filename=source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, (ast.Name, ast.Attribute)):
                    name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr
                    if name in {"__import__", "import_module", "spec_from_file_location"}:
                        if (name != "spec_from_file_location" and node.args
                                and isinstance(node.args[0], ast.Constant)
                                and isinstance(node.args[0].value, str)
                                and node.args[0].value.split(".")[0] in sys.stdlib_module_names):
                            continue
                        raise ValueError(f"unsupported dynamic Python import in {source}:{node.lineno}")
                if isinstance(node, ast.Import):
                    imports = [(alias.name, 0) for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    imports = [(node.module or "", node.level)]
                else:
                    continue
                for module, level in imports:
                    if not level and module.split(".")[0] in sys.stdlib_module_names:
                        continue
                    owner = self.root / path.parent
                    for _ in range(max(0, level - 1)):
                        owner = owner.parent
                    candidate = owner.joinpath(*module.split("."))
                    candidates = [candidate.with_suffix(".py"), candidate / "__init__.py"]
                    matches = [item for item in candidates if self.inside(item).is_file()]
                    if len(matches) != 1:
                        raise ValueError(f"unresolved Python dependency {module!r} in {source}:{node.lineno}")
                    self.edge(source, module, matches[0].relative_to(self.root).as_posix(), "python-import")
        elif path.suffix in {".mjs", ".js"}:
            for reference in re.findall(r"(?:from\s*|import\s*\(|new URL\()\s*['\"](\.[^'\"]+)['\"]", text):
                target = self.resolve_reference(source, reference, required=True)
                assert target is not None  # Required references resolve or raise.
                self.edge(source, reference, target, "javascript-import")
            if re.search(r"\b(?:require|import)\(\s*[^'\"\s]", text):
                raise ValueError(f"unsupported dynamic JavaScript import in {source}")

    def adapt(self, source: str, text: str, references: dict[int, tuple[str, str]]) -> str:
        # Rewrite original spans once: a later shorthand must not corrupt an already-rooted path.
        for start, (reference, target) in sorted(references.items(), reverse=True):
            fragment = "#" + reference.split("#", 1)[1] if "#" in reference else ""
            replacement = f"content/{target}{fragment}" if not target.startswith("https://") else target + fragment
            text = text[:start] + replacement + text[start + len(reference):]
        # Root placeholders in conceptual ownership rules name the installed content root.
        # Linked files are returned raw, so never emit another environment template here.
        text = text.replace(PLUGIN_TOKEN, "content")
        text = re.sub(r'Skill\(["\'](?:graph-powers:)?([\w-]+)["\']\)',
                      lambda m: f'skill_view("graph-powers:{m[1]}")', text)
        text = text.replace("Skill()", "skill_view()")
        text = text.replace("$ARGUMENTS", "the user-provided arguments")
        # Role names in prose remain contracts. Only concrete call syntax is projected.
        text = re.sub(r'Agent\(\{subagent_type:"graph-powers:([\w-]+)",\s*run_in_background:true\}\)',
                      lambda m: f'delegate_task(goal="<bounded task>", context="<loaded graph-powers:agent-{m[1]} contract and seven-section prompt>", background=true)', text)
        text = text.replace("Agent()", "delegate_task()")
        text = re.sub(r"run_in_background\s*:\s*true", "background=true", text)
        text = re.sub(r"subagent_type:\s*([\"'])graph-powers:([\w-]+)\1",
                      lambda m: f'contract: "graph-powers:agent-{m[2]}"', text)
        if source == "skills/debugger/references/pack-guides.md":
            text = text.replace("Read-only **by frontmatter,\nnever by instruction**",
                                "Read-only **requires actual host policy and an explicit child MUST NOT DO; frontmatter is not enforced by Hermes**")
        if source == "references/shared/070-parallel-agent-spawn.md":
            text = text.replace("Native `Agent` calls pass no override;", "Hermes delegation uses the parent's live host model configuration; source model labels do not select a Hermes model;")
        if source in self.registration_by_source:
            header = ('> Hermes: first load `skill_view("graph-powers:graph-engineering")` for native calls '
                      'and host-policy limits. `content/` paths are `file_path` values relative to the '
                      'common registered-document parent. Source tools/model frontmatter is not host enforcement.\n\n')
        else:
            header = ('> Hermes auxiliary: `content/` paths are `file_path` values relative to the '
                      'registered-document parent. Apply the loaded graph-engineering mapping and host policy; '
                      'this file is served without template expansion.\n\n')
        if source == "references/shared/110-guardrails-index.md":
            header += '> Hermes does not install or enforce the Claude hooks listed here. Each hook link leads to its external Claude source for inspection only; Hermes never fetches, copies, or executes hook code. The parent carries safety rules and approvals.\n\n'
        if source == "references/shared/130-workflow-authoring.md":
            header += '> Hermes has no native Workflow tool. This source-client authoring reference and its validator require an explicitly authorized external Claude workflow task. Do not invoke Workflow in Hermes; use the planning contract for native orchestration.\n\n'
        if text.startswith("---\n"):
            end = text.find("\n---", 4)
            if end >= 0:
                end += 4
                return text[:end] + "\n\n" + header + text[end:].lstrip("\n")
        return header + text

    def output(self, path: str, text: str, sources: list[str], kind: str) -> None:
        portable = PurePosixPath(path)
        if portable.is_absolute() or ".." in portable.parts or "\\" in path:
            raise ValueError(f"package destination escape: {path}")
        key = path.casefold()
        if key in self.destinations:
            raise ValueError(f"package destination collision: {self.destinations[key]} and {path}")
        self.destinations[key] = path
        text = text.replace("\r\n", "\n")
        self.outputs[path] = text
        self.file_rows.append({"path": path, "sha256": digest(text.encode()), "sources": sources, "kind": kind})

    def build(self) -> dict:
        registrations = []
        for item in self.request["registrations"]:
            source = item["path"]
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", item["name"]):
                raise ValueError(f"unsupported registration name: {item['name']}")
            registrations.append({**item, "source": source, "path": f"skills/{item['name']}.md"})
            self.enqueue(source)
        index = 0
        while index < len(self.pending):
            source = self.pending[index]
            index += 1
            raw = self.read(source).decode("utf-8").replace("\r\n", "\n")
            if source.endswith("/learning.md"):
                self.host(source, "historical ledger", "historical paths/calls are evidence, not operational dependencies")
                adapted = "> Historical evidence only. Load the current registered contract for operational instructions.\n\n" + raw
            elif source.endswith(".md"):
                adapted = self.project(source, self.adapt(source, raw, self.references(source, raw)))
            else:
                self.script_dependencies(source, raw)
                adapted = self.project(source, raw)
            self.output(CONTENT + source, adapted, [source], "content")
            if source in self.registration_by_source:
                self.output(f"skills/{self.registration_by_source[source]}.md", adapted, [source], "registration")
        self.output("plugin.yaml", self.request["manifest"], [".claude-plugin/plugin.json"], "manifest")
        self.read(".claude-plugin/plugin.json")
        # The runtime entrypoint consumes generated data; source discovery remains build-only.
        entrypoint = '''"""Generated Hermes registrations; no tools, hooks or runtime source generation."""

import json
from pathlib import Path, PurePosixPath

PLUGIN_ROOT = Path(__file__).resolve().parent


def planned_registrations(root=None):
    base = (PLUGIN_ROOT if root is None else Path(root)).resolve()
    plan = json.loads((base / "PROVENANCE.json").read_text(encoding="utf-8"))
    planned = []
    names = set()
    paths = set()
    for row in plan["registrations"]:
        name, relative = row["name"], PurePosixPath(row["path"])
        if (not isinstance(name, str) or not name or name.casefold() in names
                or relative.is_absolute() or ".." in relative.parts
                or "\\\\" in row["path"] or relative.parent != PurePosixPath("skills")):
            raise ValueError("invalid or duplicate Hermes registration")
        path = (base / relative).resolve()
        if not path.is_relative_to(base / "skills") or not path.is_file() or path in paths:
            raise ValueError("missing or escaping Hermes registration source")
        names.add(name.casefold())
        paths.add(path)
        planned.append((name, path, row["description"]))
    return planned


def register(ctx):
    for name, path, description in planned_registrations():
        ctx.register_skill(name, path, description)
'''
        entry_sources = ["hermes/package_builder.py"] if (self.root / "hermes/package_builder.py").is_file() else []
        self.output("__init__.py", entrypoint, entry_sources, "entrypoint")
        for name, kind in [("LICENSE", "license"), ("NOTICE", "notice")]:
            self.output(name, self.read(name).decode("utf-8"), [name], kind)
        # Skill-specific licenses follow only skills that are actually in the closure.
        owners = {PurePosixPath(source).parts[1] for source in self.pending
                  if source.startswith("skills/") and len(PurePosixPath(source).parts) > 2}
        for owner in sorted(owners):
            for path in sorted((self.root / "skills" / owner).glob("*LICENSE*")):
                source = path.relative_to(self.root).as_posix()
                if CONTENT + source not in self.outputs:
                    self.output(CONTENT + source, self.read(source).decode("utf-8"), [source], "license")
        for path in ["hermes/install.mjs", "hermes/package_builder.py", "codex/lib.mjs"]:
            if (self.root / path).is_file():
                self.read(path)
        head = subprocess.run(["git", "-C", str(self.root), "rev-parse", "--show-toplevel"],
                              capture_output=True, text=True, encoding="utf-8", check=False)
        base_revision = None
        if head.returncode == 0 and Path(head.stdout.strip()).resolve() == self.root:
            head = subprocess.run(["git", "-C", str(self.root), "rev-parse", "HEAD"],
                                  capture_output=True, text=True, encoding="utf-8", check=False)
            if head.returncode == 0:
                base_revision = head.stdout.strip()
        source_rows = []
        for path, data in sorted(self.sources.items()):
            base_hash = None
            if base_revision:
                original = subprocess.run(["git", "-C", str(self.root), "show", f"{base_revision}:{path}"],
                                          capture_output=True, check=False)
                if original.returncode == 0:
                    base_hash = digest(original.stdout)
            sha = digest(data)
            source_rows.append({"path": path, "sha256": sha, "base_sha256": base_hash, "dirty": sha != base_hash})
        def unique(rows):
            return sorted({json.dumps(row, sort_keys=True): row for row in rows}.values(),
                          key=lambda row: json.dumps(row, sort_keys=True))
        provenance = {
            "schema_version": 1, "generator": "hermes/install.mjs",
            "source": {"base_revision": base_revision, "version": self.request["version"],
                       "dirty": any(row["dirty"] for row in source_rows)},
            "registrations": sorted(registrations, key=lambda row: row["name"]),
            "sources": source_rows, "files": sorted(self.file_rows, key=lambda row: row["path"]),
            "closure": {"edges": unique(self.edges), "host_references": unique(self.host_refs)},
            "runtime": "UNVERIFIED",
        }
        self.outputs["PROVENANCE.json"] = json_text(provenance)
        return {"provenance": provenance, "files": dict(sorted(self.outputs.items()))}


if __name__ == "__main__":
    # The Bun/Python JSON protocol is UTF-8 regardless of the caller's console encoding.
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if isinstance(stream, TextIOWrapper):
            stream.reconfigure(encoding="utf-8")
    try:
        print(json.dumps(PackageBuilder(Path(sys.argv[1]), json.load(sys.stdin)).build(), ensure_ascii=False))
    except (ValueError, OSError, SyntaxError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from None
