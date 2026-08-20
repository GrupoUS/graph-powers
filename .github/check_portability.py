#!/usr/bin/env python3
"""The plugin runs on Linux, macOS and Windows. This is what keeps that true.

Nothing here is theoretical. Every pattern below was a live defect in this repository, found by
reading the whole tree once:

- `smart_bash_approver.py` classified commands with POSIX regexes only, so on a machine whose Bash
  tool maps to PowerShell the destructive floor did not exist — `Remove-Item -Recurse -Force C:\\`
  was treated as an unknown command and, under `autonomous`, allowed.
- `codex/lib.mjs` matched frontmatter with `^---\\n`, which does not match `---\\r\\n`. A clone on
  Windows produced an install with zero agents and zero command-skills, and reported success.
- `codex/install.mjs` guarded a recursive delete with `(^|/)`, so on Windows the guard never fired
  and `~/.agents/skills` — every other tool's skills included — was in scope for `rmSync`.
- `graph_guardrails.py` compared a native-separator path against a lease written with `/`, denying
  every legitimate write during exactly the parallel wave it exists to protect.
- Commands told the agent to run `awk`, `find | wc -l`, `date +%F` and `ls -lh … | sort | head`.

What they have in common is that none of them raised. They returned the wrong answer quietly, which
is why a gate is worth more here than a rule in a document.

    python3 .github/check_portability.py

Two categories, and the second is the one that catches the subtle ones:

    SHELL   a POSIX-only binary or construct in a block an agent is told to execute
    PATH    a path compared or built as a string with `/`, where the platform yields `\\`
"""

from __future__ import annotations

import glob
import os
import re
import sys

# Binaries that simply are not there on a Windows shell. `git`, `node`, `python`/`python3` and the
# project's own package manager are absent from this list on purpose — they are cross-platform, and
# a gate that flags them is a gate somebody disables.
POSIX_BINARIES = (
    "rm", "chmod", "chown", "ln", "touch", "mkdir", "ls", "cat", "head", "tail",
    "grep", "sed", "awk", "cut", "sort", "uniq", "wc", "find", "which", "xargs",
    "tr", "df", "du", "ps", "kill", "killall", "pbcopy", "osascript", "sudo", "jq", "time",
)

SHELL_CONSTRUCTS = {
    "command substitution `$(…)` is POSIX; cmd.exe passes it through literally":
        re.compile(r"\$\([a-z]"),
    "`/dev/null` does not exist on Windows":
        re.compile(r"/dev/null"),
    "`/tmp` does not exist on Windows — use tempfile.gettempdir()":
        re.compile(r"(?<![\w`.\"<])/tmp\b"),
    "`~` is not expanded by cmd.exe or PowerShell":
        re.compile(r"(?<![\w`])~/"),
    "`export VAR=` is POSIX; PowerShell uses $env:, cmd uses set":
        re.compile(r"^\s*export\s+[A-Z]"),
    "inline `VAR=value command` is POSIX-only shell syntax":
        re.compile(r"^\s*[A-Z][A-Z0-9_]*=\S+\s+[a-z$]"),
    "trailing `\\` is a line continuation only in POSIX shells":
        re.compile(r"[^\\`]\\$"),
}

# Files whose whole point is to document a platform difference, and the scanner's own source.
EXEMPT_FILES = {
    ".github/check_portability.py",
    "references/shared/110-guardrails-index.md",   # documents all three shell forms, by design
    "skills/astro/references/troubleshooting.md",  # has an explicit PowerShell branch
    "CHANGELOG.md",
}

FENCE_START = re.compile(r"^```(bash|sh|shell|console)?\s*$")


def executable_lines(path: str):
    """Yield (line number, text) for lines an agent is told to run.

    A fenced block with no language, or tagged `bash`/`sh`/`shell`/`console`, is treated as
    executable. Anything else — `typescript`, `json`, `text`, a table, prose — is not, because the
    cost of a false positive here is somebody switching the gate off.
    """
    open_fence = False       # inside any fenced block
    executable = False       # ...and that block is one an agent runs
    with open(path, encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh, 1):
            if line.startswith("```"):
                # Track "am I in a fence" separately from "is this fence executable". Conflating
                # them meant a ```json block reset the state and its closing fence re-opened the
                # scanner as if bash had begun — which reported prose as if it were a command.
                if open_fence:
                    open_fence, executable = False, False
                else:
                    open_fence, executable = True, bool(FENCE_START.match(line))
                continue
            if not (open_fence and executable):
                continue
            code = line.split("#", 1)[0] if not line.lstrip().startswith("#") else ""
            if code.strip():
                yield i, code.rstrip("\n")


def scan_markdown() -> list[str]:
    problems: list[str] = []
    binaries = re.compile(r"^\s*(" + "|".join(POSIX_BINARIES) + r")\b")
    roots = ["commands", "skills", "references", "templates", "agents", "workflows"]
    for root in roots:
        for path in sorted(glob.glob(f"{root}/**/*.md", recursive=True)):
            if path.replace(os.sep, "/") in EXEMPT_FILES:
                continue
            for lineno, line in executable_lines(path):
                m = binaries.match(line)
                if m:
                    problems.append(
                        f"SHELL {path}:{lineno}: `{m.group(1)}` is not on a Windows shell — "
                        f"use the agent's own tool, or one line of Python"
                    )
                for why, pattern in SHELL_CONSTRUCTS.items():
                    if pattern.search(line):
                        problems.append(f"SHELL {path}:{lineno}: {why}")
    return problems


def scan_python() -> list[str]:
    """String comparison against a path. The silent half of this whole class."""
    problems: list[str] = []
    checks = (
        (re.compile(r'\.startswith\(\s*[\'"](?!https?://|file://)[^\'"]*/'),
         "startswith() on a path — glob yields the platform separator; use os.path.dirname"),
        (re.compile(r'\.split\(\s*[\'"]/[\'"]\s*\)'),
         "split('/') on a path — use PurePath(...).parts or as_posix() first"),
        (re.compile(r'os\.environ\.get\(\s*[\'"]HOME[\'"]\s*\)(?!\s*or)'),
         "HOME is not set on Windows — fall back to USERPROFILE, or use Path.home()"),
        (re.compile(r'\bselect\.select\('),
         "select.select accepts only sockets on Windows — read stdin on a thread"),
        (re.compile(r'subprocess\.run\((?![^)]*encoding=)[^)]*text=True'),
         "text=True without encoding decodes with the locale code page — pass encoding='utf-8'"),
        (re.compile(r'shlex\.split\((?![^\n]*posix=)'),
         "shlex.split defaults to POSIX mode and eats Windows backslashes — pass posix="),
        # `strip` takes a SET OF CHARACTERS, not a prefix or a suffix, and this repository has paid
        # for that twice. `protect_files.py` used `.lstrip("./")`, which deletes the leading dot of
        # every declared dotfile, so `.env` stopped being protected. `fetch_logs.py` used
        # `.rstrip(".git")`, which turns `owner/my-agent.git` into `owner/my-agen` and sends every
        # log lookup to a repository that does not exist. Neither raised.
        #
        # Only a literal shaped like a suffix or a prefix is flagged: `"\n"` and `"> "` are genuine
        # character sets and a gate that reports them is a gate somebody switches off.
        (re.compile(r'''\.[lr]?strip\(\s*['"](?:[./]{2,}|[./]?[A-Za-z0-9]{2,})['"]\s*\)'''),
         "strip() takes a character set, not an affix — use removeprefix()/removesuffix()"),
    )
    for path in sorted(glob.glob("hooks/*.py") + glob.glob(".github/*.py")
                       + glob.glob("skills/**/*.py", recursive=True)):
        if path.replace(os.sep, "/") in EXEMPT_FILES:
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            source = fh.read()
        lines = source.splitlines()
        for i, line in enumerate(lines, 1):
            if line.lstrip().startswith("#"):
                continue
            for pattern, why in checks:
                if pattern.search(line):
                    problems.append(f"PATH  {path}:{i}: {why}")
        problems += scan_calls(path, source)
    return problems


# `subprocess.run(...)` is routinely written across four lines, and every check above reads one
# line at a time. Three real instances sat in the tree while the gate reported zero — the opening
# paren on one line, `text=True` on the next, so nothing ever saw both at once. These checks read
# the whole call instead, so formatting stops deciding whether a defect is visible.
CALL_CHECKS = (
    ("subprocess.run", lambda a: "text=True" in a and "encoding=" not in a,
     "text=True without encoding decodes with the locale code page — pass encoding='utf-8'"),
    ("shlex.split", lambda a: "posix=" not in a,
     "shlex.split defaults to POSIX mode and eats Windows backslashes — pass posix="),
)


def scan_calls(path: str, source: str) -> list[str]:
    """Every call to a named function, read whole however many lines it spans."""
    problems: list[str] = []
    for name, is_bad, why in CALL_CHECKS:
        start = 0
        while True:
            at = source.find(f"{name}(", start)
            if at == -1:
                break
            start = at + 1
            line_no = source.count("\n", 0, at) + 1
            if source.splitlines()[line_no - 1].lstrip().startswith("#"):
                continue
            args = balanced(source, at + len(name))
            if args is None:
                continue
            # The single-line pass already reported anything that fits on one line; reporting it
            # twice would make the count wrong and the fix look incomplete.
            if "\n" in args and is_bad(args):
                problems.append(f"PATH  {path}:{line_no}: {why}")
    return problems


def balanced(source: str, open_paren: int) -> str | None:
    """The text between `(` at `open_paren` and its matching `)`, or None if unbalanced."""
    depth = 0
    for i in range(open_paren, len(source)):
        c = source[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return source[open_paren + 1:i]
    return None


def main() -> int:
    problems = scan_markdown() + scan_python()
    for p in problems:
        print(p)
    print(f"\n{len(problems)} portability problem(s)")
    if problems:
        print("::error::the plugin ships to Linux, macOS and Windows — this does not run on all three")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
