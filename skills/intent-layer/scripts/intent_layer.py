#!/usr/bin/env python3
"""Report, measure and gate a project's AGENTS.md tree.

An intent layer is a set of AGENTS.md files: one at the root, one in every subtree large
enough to need its own map, each one linked from the node above it. The three questions the
setup playbook and /evolve keep asking about it — what is there, where a node is missing, does
the tree still hold — used to be answered by three shell scripts built on `find`, `wc`, `grep`,
`bc` and `$(…)`. None of that runs on the Windows shells a third of installs map the Bash tool
to, and none of it was a gate: a report that always exits 0 is advice.

`state` and `measure` are reads. `check` exits 1 on the first thing Codex, Cursor or Grok would
trip over — an orphan node no ancestor links to, a downlink to a file that is not there, a
`{{placeholder}}` the setup left behind, a node past the 4k-token cap, or a root-to-leaf chain
past the 32 KiB Codex stops reading at.

Tokens are bytes / 4. That is an estimate, and the output says so.
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import re
import subprocess
import sys
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path, PurePath, PurePosixPath

ROOT_NODE = "AGENTS.md"
CLAUDE_NODE = "CLAUDE.md"

# Directories no agent reads and no node should map. `.bak-` is the setup playbook's backup
# suffix: a backup of a node is a second copy of the node, and it would report as an orphan.
IGNORED = frozenset({
    "node_modules", ".git", "dist", "build", "out", "coverage", "__pycache__", ".venv", "venv",
    "target", "vendor", ".turbo", ".cache", ".next", ".nuxt", ".svelte-kit", ".output",
    ".parcel-cache", ".pytest_cache", ".mypy_cache", ".ruff_cache",
})

# What an agent reads when it works in a directory. Images, binaries and generated artefacts
# weigh nothing here because they weigh nothing in a context window.
COUNTED_EXT = frozenset({
    "ts", "tsx", "js", "jsx", "mjs", "cjs", "py", "go", "rs", "java", "kt", "swift", "rb", "php",
    "c", "cc", "cpp", "h", "hpp", "cs", "vue", "svelte", "astro", "md", "mdx", "json", "yaml",
    "yml", "toml", "sql", "graphql", "prisma", "css", "scss", "html",
})

# A lockfile is the one text file nobody reads and everybody has: 500 KB of JSON that would
# make every `packages/*` look like it needs a node.
LOCKFILES = frozenset({
    "package-lock.json", "npm-shrinkwrap.json", "bun.lock", "bun.lockb", "pnpm-lock.yaml",
    "yarn.lock", "Cargo.lock", "poetry.lock", "uv.lock", "Pipfile.lock", "Gemfile.lock",
    "composer.lock", "packages.lock.json", "pubspec.lock", "deno.lock", "flake.lock",
})

# A manifest below the root is a package boundary, and package boundaries are where nodes go.
MANIFESTS = frozenset({
    "package.json", "pyproject.toml", "Cargo.toml", "go.mod", "Gemfile", "composer.json",
    "pom.xml", "build.gradle",
})

# A downlink is any path ending in AGENTS.md. Four shapes are read, in this order, and each match
# is blanked before the next pattern runs so one token is never read twice:
#   1. an angle-bracketed markdown link target — `[api](<my docs/AGENTS.md>)` — the one shape
#      that admits a space;
#   2. a plain markdown link target — `[api](packages/api/AGENTS.md)`;
#   3. a backticked path with no whitespace inside — `app/(dashboard)/AGENTS.md`;
#   4. a bare token: no whitespace, no quote of either kind, no emphasis marker, no pipe, with
#      balanced `()` and `[]` allowed so a route group or a dynamic segment reads whole.
# Two adversarial rounds shaped this. The first found an ASCII-only charset truncating
# `módulos/AGENTS.md`; the second found a link earlier on the line swallowing the real path, the
# prose between two code spans read as one path, and curly quotes glued to the token. The tail
# keeps `AGENTS.mdx`, `AGENTS.md.bak`, `AGENTS.md~` and `AGENTS.md-old` from reading as a node.
_TAIL = r"AGENTS\.md(?![A-Za-z0-9_~]|[.-][A-Za-z0-9])"
DOWNLINK_TAIL_RE = re.compile(_TAIL)
_SEG = r"(?:[^\s()\[\]`\"'<>|“”«»‘’*]|\([^\s()]*\)|\[[^\s\[\]]*\])"
DOWNLINK_PATTERNS = (
    re.compile(r"\]\(<([^>\n]*?" + _TAIL + r")[^>\n]*>\)"),
    re.compile(r"\]\((" + _SEG + r"*?" + _TAIL + r")"),
    re.compile(r"`([^`\s]*?" + _TAIL + r")[^`\s]*`"),
    re.compile(r"(" + _SEG + r"*" + _TAIL + r")"),
)
# A token carrying one of these is prose about a convention — `packages/*/AGENTS.md`,
# `packages/<name>/AGENTS.md`, `${paths.backendRoot}/AGENTS.md` — not a path to a file.
NOT_A_PATH = ("*", "?", "<", ">", "{", "}", "$", "://")
PLACEHOLDER_RE = re.compile(r"\{\{.*?\}\}|\{\{\S*")
FENCE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
RULE_RE = re.compile(r"^(?:[-*_]\s*){3,}$")


def downlink_tokens(line: str) -> list[str]:
    """Every distinct downlink token on one line, in the order the shapes above find them."""
    # The bare-path pattern is intentionally expressive, but applying its leading repeated segment
    # to a long line with no viable suffix makes the regex engine retry from every character. Rule
    # out that overwhelmingly common case with a fixed-tail scan first. This also rejects suffixes
    # such as AGENTS.mdx before any of the path expressions can backtrack over the line.
    if DOWNLINK_TAIL_RE.search(line) is None:
        return []
    tokens: list[str] = []
    rest = line
    for pattern in DOWNLINK_PATTERNS:
        for match in pattern.finditer(rest):
            # `my\_pkg` is a markdown-escaped underscore before it is a Windows separator.
            token = match.group(1).replace("\\_", "_").replace("\\", "/").strip()
            if token and token not in tokens:
                tokens.append(token)
        rest = pattern.sub(" ", rest)
    return tokens


def prose_lines(text: str):
    """(line_no, line) for every line that is prose: outside a fenced block, outside an HTML comment.

    A fence closes only on its own marker at its own length or longer, so a ``` pair inside a
    ~~~ block does not end the block. A path inside either is an example, not a downlink, and a
    line inside either is not a purpose line.
    """
    fence: str | None = None
    in_comment = False
    for line_no, line in enumerate(text.splitlines(), 1):
        marker = FENCE_RE.match(line)
        if fence is None and marker:
            fence = marker.group(1)
            continue
        if fence is not None:
            if marker and marker.group(1)[0] == fence[0] and len(marker.group(1)) >= len(fence):
                fence = None
            continue
        if in_comment:
            if "-->" not in line:
                continue
            in_comment = False
            line = line.split("-->", 1)[1]
        while "<!--" in line:
            head, _, tail = line.partition("<!--")
            if "-->" in tail:
                line = head + " " + tail.split("-->", 1)[1]
            else:
                line = head
                in_comment = True
        yield line_no, line

DEPTH = 3
THRESHOLD = 20_000
SPLIT = 64_000
TOP = 25
MAX_NODE_TOKENS = 4_000
CODEX_CAP = 32_768


@dataclass
class Node:
    rel: str            # POSIX path relative to ROOT — the only form ever printed or compared
    path: Path
    size: int
    text: str | None    # None when the file could not be read; `error` says why
    error: str = ""
    links: set[str] = field(default_factory=set)
    dangling: list[tuple[int, str]] = field(default_factory=list)

    @property
    def tokens(self) -> int:
        # Rounded up: a 16,001-byte node is over a 4,000-token cap, and floor division said 4,000.
        return -(-self.size // 4)

    @property
    def directory(self) -> str:
        parent = PurePosixPath(self.rel).parent.as_posix()
        return "" if parent == "." else parent


@dataclass
class Layer:
    root_dir: Path
    label: str
    root: Node | None
    children: list[Node]
    claude_root: bool
    claude_subdirs: list[str]

    @property
    def nodes(self) -> list[Node]:
        return ([self.root] if self.root else []) + self.children

    def node_at(self, rel: str) -> Node | None:
        for node in self.nodes:
            if node.rel == rel:
                return node
        return None

    def ancestors(self, child: Node) -> list[Node]:
        """Every node in a parent directory of `child`, root first, nearest last."""
        parts = PurePosixPath(child.directory).parts if child.directory else ()
        found: list[Node] = []
        for i in range(len(parts)):
            prefix = "/".join(parts[:i])
            node = self.node_at(f"{prefix}/{ROOT_NODE}" if prefix else ROOT_NODE)
            if node is not None:
                found.append(node)
        return found

    def linked(self, child: Node) -> bool:
        return any(child.rel in a.links for a in self.ancestors(child))


# --- discovery ------------------------------------------------------------------------------


def posix_rel(path: str | Path, root: Path) -> str:
    return PurePath(os.path.relpath(str(path), str(root))).as_posix()


def fmt_k(tokens: int) -> str:
    # Floored to one decimal, never rounded: 19,999 tokens printed as `20.0k` beside a verdict of
    # `—` reads as the gate contradicting itself, and it did until this line was written.
    return f"{tokens // 100 / 10:.1f}k"


def skip_dir(name: str) -> bool:
    return name in IGNORED or name[:1] == "." or ".bak-" in name


def excluded(rel: str, patterns: list[str]) -> bool:
    """`--exclude templates` has to hide `templates/AGENTS.md`, so every parent is matched too."""
    if not patterns or rel in ("", "."):
        return False
    parts = PurePosixPath(rel).parts
    prefixes = ["/".join(parts[:i]) for i in range(1, len(parts) + 1)]
    for pat in patterns:
        if any(fnmatch.fnmatchcase(p, pat) for p in prefixes):
            _MATCHED.add(pat)
            return True
    return False


# The `--exclude` patterns that hid at least one path this run; `main` names the ones that did not.
_MATCHED: set[str] = set()


def walk_tree(root: Path, patterns: list[str], unreadable: list[str] | None = None):
    """One os.walk, pruned in place, yielding (posix rel dir or "", abs dir, sorted file names).

    A directory the walk cannot open is recorded rather than dropped: 100 KB that vanishes from a
    table with no line saying so is a `complete` verdict on a tree nobody measured.
    """
    def on_error(err: OSError) -> None:
        if unreadable is not None:
            unreadable.append(posix_rel(getattr(err, "filename", "") or str(root), root))

    for dirpath, dirnames, filenames in os.walk(str(root), onerror=on_error):
        rel = posix_rel(dirpath, root)
        rel_dir = "" if rel == "." else rel
        keep: list[str] = []
        for name in sorted(dirnames):
            if skip_dir(name):
                continue
            if excluded(f"{rel_dir}/{name}" if rel_dir else name, patterns):
                continue
            keep.append(name)
        dirnames[:] = keep
        yield rel_dir, dirpath, sorted(filenames)


def load_node(root: Path, rel: str) -> Node:
    """Read a node as UTF-8, and refuse to pretend about one that is not.

    PowerShell 5.1's `>` writes UTF-16. Decoded as UTF-8 with replacement that is NUL-interleaved
    text in which no `{{placeholder}}` and no downlink is visible, so the gate said OK on a root
    full of placeholders. NUL bytes in the head are the tell; the node is reported unreadable,
    with the reason, and `check` fails on it. `utf-8-sig` drops a BOM, which `str.strip` does
    not — a BOM in front of `#` turned a heading into a purpose line.
    """
    path = root / rel
    try:
        data = path.read_bytes()
    except OSError as err:
        return Node(rel, path, 0, None, error=str(err))
    if b"\x00" in data[:2048]:
        return Node(rel, path, len(data), None,
                    error="not UTF-8 text (NUL bytes — a UTF-16 file? agents read UTF-8)")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as err:
        # Latin-1 decoded with replacement is a node whose accented downlinks never resolve and
        # whose reader sees mojibake. Say which byte, and what to do.
        return Node(rel, path, len(data), None,
                    error=f"not UTF-8 text (undecodable byte at offset {err.start}; re-save as UTF-8)")
    return Node(rel, path, len(data), text)


def resolve_token(root: Path, node_dir: Path, token: str) -> str | None:
    """POSIX rel path of the file a downlink names — node-relative first — or None.

    `%20` is how an editor writes a space into a link target; the second spelling tried is the
    decoded one, so a directory with a space resolves either way.
    """
    spellings = [token]
    if "%" in token:
        spellings.append(urllib.parse.unquote(token))
    for spelling in spellings:
        for base in (node_dir, root):
            candidate = os.path.normpath(os.path.join(str(base), spelling))
            if os.path.isfile(candidate):
                return posix_rel(candidate, root)
    return None


def resolve_links(layer: Layer) -> None:
    known = {n.rel for n in layer.nodes}
    for node in layer.nodes:
        if node.text is None:
            continue
        # A path inside a fenced block or an HTML comment is an example — "add
        # `packages/new/AGENTS.md`" in a how-to — so it is neither a link nor a dangle.
        for line_no, line in prose_lines(node.text):
            for token in downlink_tokens(line):
                # An absolute path, a URL, a glob or a placeholder is prose about a node, not a
                # link to one.
                if token[:1] == "/" or any(mark in token for mark in NOT_A_PATH):
                    continue
                target = resolve_token(layer.root_dir, node.path.parent, token)
                if target is None:
                    if (line_no, token) not in node.dangling:
                        node.dangling.append((line_no, token))
                elif target != node.rel and target in known:
                    # "read its AGENTS.md first" resolves to the node itself, and a file that
                    # exists but is not a node (an excluded template, say) is neither a link nor
                    # a dangle.
                    node.links.add(target)


def discover(root: Path, label: str, patterns: list[str]) -> Layer:
    root_node: Node | None = None
    children: list[Node] = []
    claude_root = False
    claude_subdirs: list[str] = []
    for rel_dir, _dirpath, filenames in walk_tree(root, patterns, None):
        for name in filenames:
            if name not in (ROOT_NODE, CLAUDE_NODE):
                continue
            rel = f"{rel_dir}/{name}" if rel_dir else name
            if excluded(rel, patterns):
                continue
            if name == CLAUDE_NODE:
                if rel_dir:
                    claude_subdirs.append(rel)
                else:
                    claude_root = True
                continue
            node = load_node(root, rel)
            if rel_dir:
                children.append(node)
            else:
                root_node = node
    children.sort(key=lambda n: n.rel)
    layer = Layer(root, label, root_node, children, claude_root, sorted(claude_subdirs))
    resolve_links(layer)
    return layer


# --- measure ----------------------------------------------------------------------------------


def git_files(root: Path) -> list[str] | None:
    """Tracked plus untracked-not-ignored files, or None when git cannot answer for this root.

    Untracked files count because a package that was just scaffolded is exactly the one whose
    node is missing. An empty answer falls through to the walk: a directory that is inside a
    repository but tracked by nothing is still full of files an agent will read.
    """
    try:
        done = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=str(root), capture_output=True, encoding="utf-8", errors="replace",
            check=False, timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if done.returncode != 0:
        return None
    files = [f for f in done.stdout.split("\0") if f]
    return files or None


def walked_files(root: Path, patterns: list[str], unreadable: list[str]) -> list[str]:
    files: list[str] = []
    for rel_dir, _dirpath, filenames in walk_tree(root, patterns, unreadable):
        for name in filenames:
            rel = f"{rel_dir}/{name}" if rel_dir else name
            if not excluded(rel, patterns):
                files.append(rel)
    return files


def all_files(root: Path, patterns: list[str]) -> tuple[list[str], str, list[str]]:
    """(POSIX rel paths, source, unreadable directories).

    The same directory filter applies to both sources. What differs is `.gitignore`: the git
    source honours it and the walk cannot, so a generated directory counts in an unpacked tree and
    not in a clone. The footer names the source for that reason — the number is only comparable
    to another number measured from the same one.
    """
    unreadable: list[str] = []
    listed = git_files(root)
    source = "git" if listed is not None else "walk"
    if listed is None:
        listed = walked_files(root, patterns, unreadable)
    kept: list[str] = []
    for rel in listed:
        parts = PurePosixPath(rel).parts
        if any(skip_dir(p) for p in parts[:-1]) or excluded(rel, patterns):
            continue
        kept.append(rel)
    return kept, source, unreadable


@dataclass
class Row:
    directory: str
    files: int = 0
    size: int = 0

    @property
    def tokens(self) -> int:
        return -(-self.size // 4)


@dataclass
class Measure:
    total: Row
    rows: list[Row]          # depth 1..N, tokens desc
    boundaries: list[str]
    source: str
    unreadable: list[str]


def measure(root: Path, patterns: list[str], depth: int) -> Measure:
    files, source, unreadable = all_files(root, patterns)
    total = Row(".")
    rows: dict[str, Row] = {}
    boundaries: list[str] = []
    for rel in files:
        parts = PurePosixPath(rel).parts
        name = parts[-1]
        dir_depth = len(parts) - 1
        # `git ls-files` still lists a manifest deleted from the worktree; the size lookup below
        # is what proves the file exists, so the boundary is recorded only after it succeeds.
        is_boundary = name in MANIFESTS and 1 <= dir_depth <= depth
        ext = PurePosixPath(name).suffix[1:].lower()
        if not is_boundary and (ext not in COUNTED_EXT or name in LOCKFILES):
            continue
        try:
            size = os.path.getsize(str(root / rel))
        except OSError:
            unreadable.append(rel)
            continue
        if is_boundary:
            boundaries.append(rel)
            if ext not in COUNTED_EXT or name in LOCKFILES:
                continue
        total.files += 1
        total.size += size
        for i in range(1, min(depth, dir_depth) + 1):
            row = rows.setdefault("/".join(parts[:i]), Row("/".join(parts[:i])))
            row.files += 1
            row.size += size
    ordered = sorted(rows.values(), key=lambda r: (-r.tokens, r.directory))
    return Measure(total, ordered, sorted(boundaries), source, unreadable)


def verdict(tokens: int, has_node: bool, threshold: int, split: int) -> str:
    if has_node:
        return "SPLIT" if tokens >= split else "ok"
    if tokens >= split:
        return "NODE + SPLIT"
    if tokens >= threshold:
        return "NODE"
    return "—"


def candidates(layer: Layer, m: Measure, threshold: int, split: int) -> list[Row]:
    """Directories that earn a node and do not have one — the `.` row is `state`'s own business.

    Only the top-most of a nested run counts: `packages`, `packages/core` and `packages/core/src`
    over the line are one missing node, not three, and the count `state` prints should say so.
    The table in `measure` still shows every row, because the split decision needs them.
    """
    flagged: list[Row] = []
    for row in m.rows:
        has_node = layer.node_at(f"{row.directory}/{ROOT_NODE}") is not None
        if verdict(row.tokens, has_node, threshold, split) in ("NODE", "NODE + SPLIT"):
            flagged.append(row)
    return [r for r in flagged
            if not any(r.directory.startswith(o.directory + "/") for o in flagged)]


# --- subcommands ------------------------------------------------------------------------------


def placeholders(node: Node) -> list[tuple[int, str]]:
    if node.text is None:
        return []
    found: list[tuple[int, str]] = []
    for line_no, line in enumerate(node.text.splitlines(), 1):
        match = PLACEHOLDER_RE.search(line)
        if match:
            found.append((line_no, match.group(0)))
    return found


def has_purpose_line(node: Node) -> bool:
    """A subtree node opens with what the subtree owns, not with a heading and a table.

    Metadata is not purpose and is not counted against the five-line window: a YAML frontmatter
    block, an HTML comment and a fenced block are skipped whole. Within the window, a heading, a
    quote, a table row, a rule (`---`, `***`, `___`, `- - -`) and an indented code line do not
    count. Each of those passed as "the purpose line" in an earlier version, which is how a node
    made of headings and a table got through the gate.
    """
    if node.text is None:
        return False
    lines = node.text.splitlines()
    start = 0
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                start = i + 1
                break
    seen = 0
    for _line_no, line in prose_lines("\n".join(lines[start:])):
        seen += 1
        if seen > 5:
            return False
        stripped = line.strip()
        if not stripped or stripped[:1] in ("#", ">", "|") or RULE_RE.match(stripped):
            continue
        if line.startswith(("    ", "\t")):
            continue
        return True
    return False


def chains(layer: Layer) -> list[tuple[int, Node]]:
    """(bytes Codex reads before it reaches the leaf, leaf) for every child node."""
    out: list[tuple[int, Node]] = []
    for child in layer.children:
        on_path = [*layer.ancestors(child), child]
        out.append((sum(n.size for n in on_path), child))
    return out


def cmd_state(layer: Layer, args: argparse.Namespace) -> int:
    lines = [f"=== Intent layer: {layer.label} ==="]
    claude = "present" if layer.claude_root else "absent"
    if layer.root:
        lines.append(f"root: {ROOT_NODE} (~{fmt_k(layer.root.tokens)} tokens) | {CLAUDE_NODE}: {claude}")
    else:
        lines.append(f"root: none | {CLAUDE_NODE}: {claude}")

    lines.append(f"child nodes: {len(layer.children)}")
    orphans: list[Node] = []
    for child in layer.children:
        if layer.linked(child):
            lines.append(f"  linked  {child.rel}  (~{fmt_k(child.tokens)} tokens)")
        else:
            orphans.append(child)
            lines.append(f"  ORPHAN  {child.rel}  (~{fmt_k(child.tokens)} tokens)  "
                         f"no ancestor node links here")

    dangling = [(n, line_no, raw) for n in layer.nodes for line_no, raw in n.dangling]
    lines.append(f"dangling downlinks: {len(dangling)}")
    for node, line_no, raw in dangling:
        lines.append(f"  {node.rel}:{line_no} -> {raw}")

    m = measure(layer.root_dir, args.exclude, DEPTH)
    wanted = candidates(layer, m, THRESHOLD, SPLIT)
    lines.append(f"candidates: {len(wanted)} directories over ~{fmt_k(THRESHOLD)} tokens "
                 f"with no node (run measure)")
    lines.append("tokens = bytes / 4 (estimate)")
    if m.unreadable:
        lines.append(f"unreadable, not counted: {', '.join(m.unreadable)}")

    over_cap = [n for n in layer.nodes if n.tokens > MAX_NODE_TOKENS]
    with_placeholders = [n for n in layer.nodes if placeholders(n)]
    unreadable = [n for n in layer.nodes if n.text is None]

    if layer.root is None:
        state, action = "none", (f"write {ROOT_NODE} at the root (setup playbook step 4b), "
                                 f"then run state again")
    elif unreadable:
        state, action = "partial", f"{unreadable[0].rel} could not be read: {unreadable[0].error}"
    elif orphans:
        near = layer.ancestors(orphans[0])
        where = near[-1].rel if near else ROOT_NODE
        state, action = "partial", f"add a downlink to {orphans[0].rel} in {where}"
    elif dangling:
        node, line_no, raw = dangling[0]
        state, action = "partial", f"fix or remove the downlink {raw} at {node.rel}:{line_no}"
    elif over_cap:
        state, action = "partial", (f"{over_cap[0].rel} is ~{fmt_k(over_cap[0].tokens)} tokens — "
                                    f"split it or move detail to a reference")
    elif with_placeholders:
        line_no, token = placeholders(with_placeholders[0])[0]
        state, action = "partial", (f"resolve {token} at {with_placeholders[0].rel}:{line_no}")
    elif wanted:
        state, action = "partial", (f"run measure, then write {wanted[0].directory}/{ROOT_NODE} "
                                    f"(~{fmt_k(wanted[0].tokens)} tokens with no node)")
    else:
        state, action = "complete", "nothing — run check as the gate before handing off"

    lines.append(f"state: {state}")
    lines.append(f"action: {action}")
    print("\n".join(lines))
    return 0


def cmd_measure(layer: Layer, args: argparse.Namespace) -> int:
    m = measure(layer.root_dir, args.exclude, args.depth)
    shown = m.rows[: max(0, args.top)]
    width = max([len("directory"), len(".")] + [len(r.directory) for r in shown])
    lines = [f"{'directory':<{width}}  {'files':>6}  {'~tokens':>8}  {'node':<8}  verdict"]

    # The `.` row is the total. Splitting the root is not a verdict anyone can act on, so its
    # cell only ever says whether the root node exists.
    root_verdict = "—" if layer.root else "NODE"
    lines.append(f"{'.':<{width}}  {m.total.files:>6}  {fmt_k(m.total.tokens):>8}  "
                 f"{'present' if layer.root else '—':<8}  {root_verdict}")
    for row in shown:
        has_node = layer.node_at(f"{row.directory}/{ROOT_NODE}") is not None
        lines.append(f"{row.directory:<{width}}  {row.files:>6}  {fmt_k(row.tokens):>8}  "
                     f"{'present' if has_node else '—':<8}  "
                     f"{verdict(row.tokens, has_node, args.threshold, args.split)}")
    if len(m.rows) > len(shown):
        lines.append(f"… {len(m.rows) - len(shown)} more directories below --top {max(0, args.top)}")
    lines.append(f"thresholds: node >= {fmt_k(args.threshold)} · split >= {fmt_k(args.split)} "
                 f"· tokens = bytes / 4 (estimate) · files from {m.source}"
                 + (" (.gitignore honoured)" if m.source == "git" else " (.gitignore not read)"))
    lines.append(f"boundaries: {', '.join(m.boundaries) if m.boundaries else 'none'}")
    if m.unreadable:
        lines.append(f"unreadable, not counted: {', '.join(m.unreadable)}")
    print("\n".join(lines))
    return 0


def cmd_check(layer: Layer, args: argparse.Namespace) -> int:
    fails: list[str] = []
    warns: list[str] = []

    if layer.root is None:
        fails.append(f"{ROOT_NODE}: missing at the root — the intent layer has no root node")

    for node in layer.nodes:
        if node.text is None:
            fails.append(f"{node.rel}: could not be read ({node.error})")
            continue
        if node.tokens > args.max_node_tokens:
            fails.append(f"{node.rel}: ~{node.tokens:,} tokens, cap {args.max_node_tokens} — "
                         f"split it or move detail to the nearest reference")
        for line_no, token in placeholders(node):
            fails.append(f"{node.rel}:{line_no}: unresolved placeholder {token}")
        for line_no, raw in node.dangling:
            fails.append(f"{node.rel}:{line_no}: downlink {raw} does not resolve")

    for child in layer.children:
        if not layer.linked(child):
            near = layer.ancestors(child)
            where = near[-1].rel if near else ROOT_NODE
            fails.append(f"{child.rel}: no ancestor {ROOT_NODE} links here — add a downlink in {where}")
        if child.text is not None and not has_purpose_line(child):
            fails.append(f"{child.rel}: no purpose line in the first 5 lines — what this subtree "
                         f"owns goes before anything else")

    # One finding for the chain, on the leaf that ends it: every node on that path is under the
    # per-node cap by the check above, and the fix is still to shorten one of them.
    longest = max(chains(layer), key=lambda pair: pair[0], default=None)
    if longest is not None and longest[0] > args.codex_cap:
        total, leaf = longest
        fails.append(f"{leaf.rel}: root-to-leaf {ROOT_NODE} chain is {total:,} bytes, over the "
                     f"{args.codex_cap:,}-byte cap Codex stops reading at")

    for rel in layer.claude_subdirs:
        directory = PurePosixPath(rel).parent.as_posix()
        warns.append(f"{rel}: a Claude-only node; Codex, Cursor and Grok never read it — "
                     f"move its content to {directory}/{ROOT_NODE}")

    lines = [f"FAIL {f}" for f in fails] + [f"WARN {w}" for w in warns]
    lines.append(f"{len(layer.nodes)} nodes checked, {len(fails)} failures, {len(warns)} warnings")
    lines.append("intent layer: FAIL" if fails else "intent layer: OK")
    print("\n".join(lines))
    return 1 if fails else 0


# --- entry ------------------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Report (state), measure, or gate (check) a project's AGENTS.md tree.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p: argparse.ArgumentParser) -> None:
        p.add_argument("root", nargs="?", default=".", help="project root (default: .)")
        p.add_argument("--exclude", action="append", default=[], metavar="GLOB",
                       help="fnmatch glob against a POSIX relative path or any parent; repeatable. "
                            "Brackets are a character class: spell app/[slug] as app/[[]slug]")

    common(sub.add_parser("state", help="what the intent layer is today, and the next action"))

    p_measure = sub.add_parser("measure", help="which directories are heavy enough to need a node")
    common(p_measure)
    p_measure.add_argument("--depth", type=int, default=DEPTH)
    p_measure.add_argument("--threshold", type=int, default=THRESHOLD,
                           help="tokens at which a directory earns a node")
    p_measure.add_argument("--split", type=int, default=SPLIT,
                           help="tokens at which one node is no longer enough")
    p_measure.add_argument("--top", type=int, default=TOP)

    p_check = sub.add_parser("check", help="the gate: exit 1 on anything an agent would trip over")
    common(p_check)
    p_check.add_argument("--max-node-tokens", type=int, default=MAX_NODE_TOKENS)
    p_check.add_argument("--codex-cap", type=int, default=CODEX_CAP,
                         help="bytes of AGENTS.md Codex reads root-to-cwd before it stops")
    return parser


def main(argv: list[str] | None = None) -> int:
    # The table and the findings carry `—` and `·`. A console that cannot show them gets `?`,
    # not a traceback — a gate that crashes on its own output is the report nobody reads.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(errors="replace")
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    if not root.is_dir():
        sys.stderr.write(f"{args.root}: not a directory\n")
        return 2
    # `templates/`, `./templates`, `/templates`, `templates//` and `.\templates` are one intention,
    # and a spelling that matches nothing hides nothing without saying so.
    patterns: list[str] = []
    for raw in args.exclude:
        p = raw.replace("\\", "/")
        while "//" in p:
            p = p.replace("//", "/")
        p = p.removeprefix("./").removeprefix("/").removesuffix("/")
        if p:
            patterns.append(p)
    args.exclude = patterns
    if getattr(args, "threshold", 0) > getattr(args, "split", 0) and args.command == "measure":
        sys.stderr.write("--threshold must not exceed --split\n")
        return 2
    layer = discover(root, args.root, args.exclude)
    handler = {"state": cmd_state, "measure": cmd_measure, "check": cmd_check}[args.command]
    code = handler(layer, args)
    # A pattern that matched nothing hid nothing, and the person who typed it should know.
    for pattern in patterns:
        if pattern not in _MATCHED:
            print(f"note: --exclude {pattern} matched nothing")
    return code


if __name__ == "__main__":
    sys.exit(main())
