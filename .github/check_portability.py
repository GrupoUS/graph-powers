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
    # `expanduser` and `os.homedir()` are the fix for this, so a line that calls one and then
    # writes `~/` as its argument is the corrected form being reported as the defect. The gate
    # said so four times against instructions that had just been rewritten to be portable, which
    # is the fastest way to teach somebody to stop reading it.
    "`~` is not expanded by cmd.exe or PowerShell":
        re.compile(r"(?<![\w`])~/(?<!expanduser\(\"~/)(?<!expanduser\('~/)"),
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
    "CHANGELOG.md",                                # a record of what happened, not an instruction
    # Prose for a person, not a block an agent executes — which is the line this gate draws in its
    # own docstring. Somebody reading the README on a Mac types `~/.claude`, and rewriting that as
    # a Python one-liner would make the documentation worse to serve a rule about agent execution.
    # `AGENT_SETUP.md` is deliberately NOT here: the agent follows it, it ships, and it carried
    # twenty-six POSIX-only lines for as long as the root went unscanned.
    "README.md",
    "CONTRIBUTING.md",
}

FENCE_START = re.compile(r"^```(bash|sh|shell|console)?\s*$")

# A POSIX binary is a defect wherever the shell would START it, not only where the line starts.
# The pattern here was `^\s*(…)` read with `.match()`, so everything after the first word of a line
# was invisible: `git ls-files | wc -l` sits in this repository's own list of gates, twenty-five
# lines below the paragraph that bans `wc`, and this gate reported zero problems. Every other check
# in the file already used `.search()`; the binary list was the one that did not.
#
# The shell's command separators. Split a line on them and the first word of each piece is a
# command — which is the only position where one of these names means the binary rather than a word.
COMMAND_SEPARATORS = re.compile(r"[|;&`]|\$\(")

# `xargs` runs what follows it, so what follows it is in command position too. Rewriting it as a
# separator (while leaving `xargs` itself in place to be reported on its own account) is what makes
# `find . -type f | xargs rm -f` report `find`, `xargs` AND `rm` instead of stopping at the pipe.
XARGS_RUNS_NEXT = re.compile(r"\bxargs\b((?:\s+-\S+)*)\s+")

# The first word of a segment, if it has one. A segment starting with `-` or a quote has no command.
FIRST_WORD = re.compile(r"^\s*([A-Za-z_][\w-]*)")

# ...and what proves the first word is NOT a command, however much it looks like one. `;` is also
# Python's statement separator, so `python -X utf8 -c "import time; time.sleep(1)"` would otherwise
# report `time`. An attribute, a call, a subscript or an assignment is never a shell command.
NOT_A_COMMAND = (".", "(", "[", "=")


def posix_binaries_in(line: str) -> list[str]:
    """Every POSIX-only binary this line puts in command position, in the order they appear."""
    hits: list[str] = []
    for segment in COMMAND_SEPARATORS.split(XARGS_RUNS_NEXT.sub(r"xargs\1 ; ", line)):
        m = FIRST_WORD.match(segment)
        if m and m.group(1) in POSIX_BINARIES and segment[m.end(1):m.end(1) + 1] not in NOT_A_COMMAND:
            hits.append(m.group(1))
    return hits


def executable_blocks(path: str) -> list[tuple[str, list[tuple[int, str]]]]:
    """The same lines, grouped by the fenced block they came from, with the block's raw text.

    Some constructs are only a defect in isolation. A block that shows `export VAR=` under a
    `# bash / zsh` heading and `$env:VAR =` under a `# PowerShell` heading is documenting both
    platforms, which is the thing the gate wants — read one line at a time it looks like the
    thing the gate refuses.
    """
    blocks: list[tuple[str, list[tuple[int, str]]]] = []
    current: list[tuple[int, str]] = []
    open_fence = False
    executable = False
    with open(path, encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh, 1):
            if line.startswith("```"):
                if open_fence:
                    if current:
                        blocks.append(("\n".join(c for _, c in current), current))
                        current = []
                    open_fence, executable = False, False
                else:
                    open_fence, executable = True, bool(FENCE_START.match(line))
                continue
            if not (open_fence and executable):
                continue
            code = line.split("#", 1)[0] if not line.lstrip().startswith("#") else ""
            if code.strip():
                current.append((i, code.rstrip("\n")))
    if current:
        blocks.append(("\n".join(c for _, c in current), current))
    return blocks


def scan_markdown() -> list[str]:
    problems: list[str] = []
    roots = ["commands", "skills", "references", "templates", "agents", "workflows"]
    # The repository root was missing, and it is where the file a new installer reads first lives.
    # `AGENT_SETUP.md` ships (`check_version_bump.SHIPPED` lists it), it is the longest set of
    # copy-paste commands the plugin publishes, and none of it was ever scanned — seven POSIX-only
    # lines sat in it while this gate reported clean. `glob` with no recursion is deliberate: the
    # roots above already cover every subdirectory that matters, and `**` from `.` would walk
    # `node_modules` on a machine that has one.
    paths = [p for root in roots for p in glob.glob(f"{root}/**/*.md", recursive=True)]
    paths += glob.glob("*.md")
    for path in sorted(set(paths)):
        if path.replace(os.sep, "/") in EXEMPT_FILES:
            continue
        for raw, lines in executable_blocks(path):
            # One exemption, and it is conditional on the block doing the work: a POSIX spelling
            # beside its PowerShell counterpart is coverage, not a gap.
            both_shells = "$env:" in raw
            for lineno, line in lines:
                # Every occurrence, not the first: `find . | wc -l` is two defects on one line, and
                # reporting one of them makes the second survive the fix that answered the report.
                for name in posix_binaries_in(line):
                    problems.append(
                        f"SHELL {path}:{lineno}: `{name}` is not on a Windows shell — "
                        f"use the agent's own tool, or one line of Python"
                    )
                for why, pattern in SHELL_CONSTRUCTS.items():
                    if both_shells and why.startswith("`export VAR=`"):
                        continue
                    if pattern.search(line):
                        problems.append(f"SHELL {path}:{lineno}: {why}")
    return problems


# The same class of defect, in the language the installers are written in. Two of the five defects
# this file's own docstring cites live in `codex/lib.mjs` and `codex/install.mjs`, and neither was
# ever scanned — the gate named them as its motivation and could not have caught a regression of
# either. Every pattern below is a defect this repository actually shipped, generalised one step.
JS_CHECKS = (
    (re.compile(r"\(\^\|/\)"),
     r"`(^|/)` misses the Windows separator — use `(^|[\\/])`"),
    (re.compile(r"""\.split\(\s*['"]/['"]\s*\)"""),
     "split('/') on a path — use path.sep, or normalise to posix form first"),
    (re.compile(r"process\.env\.HOME(?!\s*\|\|)"),
     "HOME is not set on Windows — fall back to USERPROFILE, or use os.homedir()"),
    (re.compile(r"""['"]/tmp/"""),
     "`/tmp` does not exist on Windows — use os.tmpdir()"),
)


CRLF_NORMALISE = re.compile(r"""replace\(\s*/\\r\\n/g""")
LF_ANCHOR = re.compile(r"""/\^---\\n""")


def scan_js() -> list[str]:
    """The installers. Same defect class as `scan_python`, different runtime."""
    problems: list[str] = []
    roots = ("bin/*.mjs", "bin/*.js", "codex/*.mjs", "codex/*.js",
             ".github/*.mjs", ".github/*.js", "workflows/*.js", "workflows/*.mjs")
    for path in sorted({p for root in roots for p in glob.glob(root)}):
        if path.replace(os.sep, "/") in EXEMPT_FILES:
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            source = fh.read()
        # Anchoring a match to `\n` is only a defect against text that may still carry `\r\n`.
        # `codex/lib.mjs` normalises first and then anchors, which is correct and is what the
        # repair looked like — so the condition is the absence of the normalisation, not the
        # presence of the anchor. Checking it per file rather than per line is the whole point:
        # the fix and the defect sit on different lines.
        normalises_crlf = CRLF_NORMALISE.search(source) is not None
        for i, line in enumerate(source.splitlines(), 1):
            stripped = line.lstrip()
            if stripped.startswith("//") or stripped.startswith("*"):
                continue
            if not normalises_crlf and LF_ANCHOR.search(line):
                problems.append(
                    f"PATH  {path}:{i}: a match anchored to \\n never fires on a CRLF checkout, "
                    f"and this file never normalises — allow \\r?\\n, or normalise first"
                )
            for pattern, why in JS_CHECKS:
                if pattern.search(line):
                    problems.append(f"PATH  {path}:{i}: {why}")
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
    problems = scan_markdown() + scan_python() + scan_js()
    for p in problems:
        print(p)
    print(f"\n{len(problems)} portability problem(s)")
    if problems:
        print("::error::the plugin ships to Linux, macOS and Windows — this does not run on all three")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
