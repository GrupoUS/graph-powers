#!/usr/bin/env python3
"""Every name an artefact routes to has to resolve.

The existing dangling gate checks file paths, and that is the easy half. What it never saw is the
routing itself — the agent a command spawns, the workflow it invokes, the skill it loads, the
section of another file it tells the reader to apply. Those are the references that break silently:
the model reads the instruction, finds nothing, and carries on with less than it thinks it has.

The audit that motivated this found ten of them in a repository whose CI was already green,
including an agent that has never existed and three phases of `/verify` that were never written.

Six checks, and each one exists because a real reference was wrong in exactly that way:

    subagent_type   an agent the plugin does not ship
    Workflow(name)  a workflow the plugin does not ship
    Skill(name)     a skill the plugin does not ship
    § N / Phase N   a section of another file that is not in it
    ${rulesDir}/x   a rule template the plugin does not ship
    plugin:name     an artefact of ANOTHER plugin that nobody declared — the one class this gate
                    used to skip on principle, until eleven citations of `codex:rescue` proved
                    that "cannot verify" had been read as "do not look"

The hard part of a gate like this is not finding misses, it is not crying wolf: a gate with false
positives gets `|| true` appended to it within a week. So every check is deliberately narrow, every
external namespace is skipped rather than guessed at, and anything ambiguous is left alone.
"""

from __future__ import annotations

import glob
import os
import re
import sys

# Namespaced references belong to somebody else's plugin. This repository cannot open that plugin's
# tree in CI — but "cannot verify" was read as "do not look", and a name nobody looked at stayed
# wrong for two releases: eleven citations of `codex:rescue`, in the escalation path of `/debug` and
# `/implement`, naming an agent that does not exist. The plugin ships `codex-rescue`, so the address
# is `codex:codex-rescue`; `codex:rescue` resolved to nothing and the escalation silently did not
# happen.
#
# So the rule is not "verify the other plugin", it is **declare the dependency**. A name in this set
# was checked by hand against the plugin that ships it, with the evidence in the comment. A
# namespaced name that is NOT in this set fails the gate — not because it is wrong, but because
# nobody has said it is right.
OWN_NAMESPACE = "graph-powers"

EXTERNAL_ROUTES = {
    # openai-codex, agents/codex-rescue.md — the agent, addressed <plugin>:<agent>.
    "codex:codex-rescue",
    # openai-codex, skills/: codex-cli-runtime, codex-result-handling, gpt-5-4-prompting.
    "codex:codex-cli-runtime",
    "codex:codex-result-handling",
    "codex:gpt-5-4-prompting",
    # superpowers — the method layer this harness bootstraps from. Declared in README.md.
    # Each one checked against superpowers 6.3.0 `skills/`. Four more were nearly added here from
    # memory — condition-based-waiting, defense-in-depth, root-cause-tracing, webapp-testing — and
    # none of the four exists in that tree. That is the whole point of the set: a declaration is
    # only worth anything if somebody opened the other plugin before writing the line.
    "superpowers:using-superpowers", "superpowers:brainstorming",
    "superpowers:systematic-debugging", "superpowers:test-driven-development",
    "superpowers:verification-before-completion", "superpowers:dispatching-parallel-agents",
    "superpowers:requesting-code-review", "superpowers:receiving-code-review",
    "superpowers:writing-plans", "superpowers:subagent-driven-development",
    "superpowers:executing-plans", "superpowers:using-git-worktrees",
    "superpowers:writing-skills",
    # code-review — bundled with the CLI, best-effort by design (`/pr-review § 3C`).
    "code-review:code-review",
}

# `plugin:skill` is the shape itself, written out in prose that explains the shape. It is not a
# route and there is nothing to declare.
PLACEHOLDER_ROUTES = {"plugin:skill", "plugin:agent", "plugin:command"}

# Names that are roles in prose, not routing targets. Each one was checked by hand once; the
# rubric at references/rubrics/skill-improver-rubric.md warns about exactly this class.
ROLE_LABELS = {
    "code archaeologist", "regression hunter", "evidence collector",
    "db state inspector", "db-state-inspector", "main",
}

SCAN = ["agents", "commands", "skills", "references", "templates", "hooks", "workflows"]


def external_problem(path: str, line: int, name: str, kind: str) -> str:
    return (f"{path}:{line}: routes to `{name}`, a {kind} of another plugin that is not declared "
            f"in EXTERNAL_ROUTES — check the name against that plugin's tree and add it there, or "
            f"fix the spelling")


def scan_files() -> list[str]:
    out: list[str] = []
    for root in SCAN:
        for ext in ("md", "py", "js", "mjs"):
            out += glob.glob(f"{root}/**/*.{ext}", recursive=True)
    out += [f for f in ("AGENTS.md", "AGENT_SETUP.md", "README.md", "CONTRIBUTING.md",
                        "DESIGN.md", "PRODUCT.md", "REVIEW.md") if os.path.exists(f)]
    return sorted(set(out))


def read(path: str) -> str:
    return open(path, encoding="utf-8", errors="replace").read()


def lineno(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def have_agents() -> set[str]:
    return {os.path.basename(f)[:-3] for f in glob.glob("agents/*.md")}


def have_skills() -> set[str]:
    return {os.path.basename(os.path.dirname(f)) for f in glob.glob("skills/*/SKILL.md")}


def have_workflows() -> set[str]:
    return {os.path.basename(f)[:-3] for f in glob.glob("workflows/*.js")}


def have_rule_templates() -> set[str]:
    return {os.path.basename(f) for f in glob.glob("templates/rules/*.md")}


def sections_of(path: str) -> set[str]:
    """Every section id a file can be cited by.

    Both spellings are collected, because both are used: `## Section 11.5: Code graph` in
    shared-context.md, and `## 4.2 N+1 scan` in a command. A `## Phase 3` heading answers a
    `Phase 3` citation.
    """
    ids: set[str] = set()
    for line in read(path).splitlines():
        if not line.startswith("#"):
            continue
        head = line.lstrip("#").strip()
        # Three spellings are all in use and all cited: `## Section 11.5:`, `## §1 —`, `## 4.2 `.
        m = re.match(r"(?:Section|Phase|Step|FF-)?\s*§?\s*([0-9]+(?:\.[0-9]+)*[a-z]?)\b", head)
        if m:
            ids.add(m.group(1))
        m2 = re.match(r"(?:FF|D|R|N|T|W)-?([0-9]+[a-z]?)\b", head)
        if m2:
            ids.add(m2.group(0))
    return ids


def resolve(cited: str, base: str) -> str | None:
    """A cited path, resolved the way every other gate in this repository resolves one."""
    for candidate in (cited, os.path.join(base, cited),
                      os.path.join(base, "..", cited), os.path.join(base, "../..", cited)):
        if os.path.exists(candidate):
            return os.path.normpath(candidate)
    # Cited by bare filename — accept it only when the name is unambiguous in the tree.
    if "/" not in cited:
        hits = glob.glob(f"**/{cited}", recursive=True)
        hits = [h for h in hits if "node_modules" not in h]
        if len(hits) == 1:
            return hits[0]
    return None


def agent_frontmatter() -> list[str]:
    """The frontmatter contract from `.claude/rules/artifacts.md`, checked rather than trusted.

    The name that must match the filename, the `tools:` field without which an agent silently
    inherits `Write` and `Edit` whatever its body promises, and `disallowedTools` in the inline
    comma-separated shape the plugin reference documents.

    On that last one, an honest note. It was introduced believing a YAML block sequence there kept
    `security-reviewer` and `skill-improver` out of the registry for two releases. That was wrong:
    the CLI listed both while they still carried the block form, and what did not list them was a
    third-party `PreToolUse` hook whose allowlist predated them. The check stays because the
    documented shape is the inline one and uniformity across twelve files is worth holding — but it
    enforces a convention, not a known failure, and the difference matters if it ever has to be
    argued with.
    """
    problems: list[str] = []
    for path in sorted(glob.glob("agents/*.md")):
        stem = os.path.basename(path)[:-3]
        text = read(path)
        parts = text.split("---")
        if len(parts) < 3:
            problems.append(f"{path}: no frontmatter block")
            continue
        block = parts[1]
        for key in ("tools", "disallowedTools"):
            m = re.search(rf"^{key}:[ \t]*$", block, re.MULTILINE)
            if m and key == "disallowedTools":
                problems.append(
                    f"{path}: `disallowedTools` is a YAML block sequence — write it inline "
                    f"(`disallowedTools: Write, Edit`) or the agent never registers"
                )
        name = re.search(r"^name:\s*(\S+)", block, re.MULTILINE)
        if not name or name.group(1).strip("\"'") != stem:
            got = name.group(1) if name else "(absent)"
            problems.append(f"{path}: frontmatter name is {got}, the file is {stem}.md")
        if not re.search(r"^tools:", block, re.MULTILINE):
            problems.append(
                f"{path}: no `tools:` field — the agent inherits every tool, `Write` and `Edit` included"
            )
    return problems


def namespaced_spawns() -> list[str]:
    """A prescribed `subagent_type` names this plugin's agent the way the registry does.

    The agents ship inside the plugin, so the registry knows them as `graph-powers:<agent>`. Until
    1.3.1 every command and skill prescribed the bare name, copied from the assignment matrix, and
    the spawn failed with

        Agent type 'explorer' not found. Available agents: ... graph-powers:explorer ...

    an error that named the working string in its own list. `check_wiring.py` did not catch it
    because the file `agents/explorer.md` exists and the reference resolved — the path was right
    and the name was wrong, which is the combination a path check cannot see.

    A name that is not one of ours passes through untouched: a project may route to its own agent.
    """
    problems: list[str] = []
    ours = have_agents()
    if not ours:
        return problems
    literal = re.compile(r"""subagent_type\s*[:=]\s*["']?(?!graph-powers:)("""
                         + "|".join(sorted(ours)) + r""")\b""")
    # A backticked bare name in a routing file is a dispatch instruction too, and it is the shape
    # the literal check above cannot see: an audit found 129 of them across fifteen files —
    # role labels in fenced blocks, table cells, and prose reading "spawn `explorer`". They hand
    # the reader the form that does not resolve.
    backticked = re.compile(r"`(?!graph-powers:)(" + "|".join(sorted(ours)) + r")`")
    for path in scan_files():
        if os.path.dirname(path) == "agents":
            continue          # an agent describing itself is not prescribing a spawn
        text = read(path)
        for m in literal.finditer(text):
            problems.append(
                f"{path}:{lineno(text, m.start())}: prescribes `subagent_type: {m.group(1)}` — "
                f"the registry knows it as `graph-powers:{m.group(1)}`, and the bare name does not resolve"
            )
        # Where a bare name is the artefact's own name rather than a dispatch: the root specs
        # describe the host project, the rubrics describe what an auditor checks, the
        # prompt-engineering references discuss how agents are written, and `workflows/*.js` holds
        # bare names in `PLUGIN_AGENTS` precisely so `AG()` can add the namespace.
        rel = path.replace(os.sep, "/")
        if (rel in ("REVIEW.md", "DESIGN.md", "PRODUCT.md", "AGENTS.md")
                or rel.startswith(("references/rubrics/", "skills/senior-prompt-engineer/",
                                   "workflows/"))):
            continue
        for m in backticked.finditer(text):
            line = text[text.rfind("\n", 0, m.start()) + 1:text.find("\n", m.start())]
            # A quoted CLI error message has to keep the bare name it actually prints.
            if "not found" in line or "Valid:" in line or "Unknown subagent_type" in line:
                continue
            problems.append(
                f"{path}:{lineno(text, m.start())}: names the agent `{m.group(1)}` without its "
                f"namespace — write `graph-powers:{m.group(1)}`"
            )
    return problems


def external_routes() -> list[str]:
    """A `<plugin>:<name>` written in prose is an address, and it has to be one that exists.

    The `Skill()` and `subagent_type` checks only see call syntax. Every one of the eleven
    `codex:rescue` citations was ordinary prose — "escalate to `codex:codex-rescue`", a table cell,
    a mode list — so nothing looked at them, and the escalation path of `/debug` and `/implement`
    pointed at an agent no plugin ships. The correct address is `codex:codex-rescue`.

    Anchored on the namespaces this repository has declared, not on the shape `<word>:<word>`. The
    shape alone matches `path:line`, `file:line`, `client:visible`, `main:main` and `skipped:true`,
    all of which are ordinary notation here — 68 of them on the first run, which is how a gate
    ends up with `|| true` after it. The cost of the narrower rule is that a typo in the namespace
    itself (`codexx:rescue`) reads as a plugin nobody declared and passes; the name half, which is
    where the real defect was, is checked.
    """
    problems: list[str] = []
    namespaces = {n.split(":", 1)[0] for n in EXTERNAL_ROUTES}
    if not namespaces:
        return problems
    ref = re.compile(r"`(" + "|".join(sorted(map(re.escape, namespaces)))
                     + r"):([a-z0-9][a-z0-9-]*)`")
    for path in scan_files():
        text = read(path)
        for m in ref.finditer(text):
            name = f"{m.group(1)}:{m.group(2)}"
            if name in EXTERNAL_ROUTES or name in PLACEHOLDER_ROUTES:
                continue
            problems.append(external_problem(path, lineno(text, m.start()), name, "route"))
    return problems


def main() -> int:
    agents, skills, workflows, rules = have_agents(), have_skills(), have_workflows(), have_rule_templates()
    problems: list[str] = []
    checked = 0

    # A cited section is only checkable when the citation names the file: `§ 11.5` alone could be a
    # section of anything, so it is skipped rather than guessed.
    #
    # Two patterns, and the split is what keeps the gate quiet. `§` is this repository's deliberate
    # marker for "that section of that file", so it tolerates a short gap. `Phase` and `Step` are
    # ordinary English and constantly refer to a step of the CURRENT file while a filename happens
    # to sit nearby — a table row reading "`layer-map.md` cross-check (Step 3)" means Step 3 of the
    # file you are reading. So those two only count when they are glued to the filename.
    section_re = re.compile(r"([A-Za-z0-9._/-]+\.md)`?[^\n]{0,24}?§\s*([0-9]+(?:\.[0-9]+)*[a-z]?)\b")
    phase_re = re.compile(r"([A-Za-z0-9._/-]+\.md)`?\s{0,2}(?:Phase|Step)\s*([0-9]+(?:\.[0-9]+)*[a-z]?)\b")

    # The three root specs describe what the HOST project's file must contain. A citation of
    # `DESIGN.md § 15` is about the host's design authority, which this repository does not have
    # and cannot check. Verifying it against our own spec would report a defect that does not exist.
    HOST_SPECS = {"DESIGN.md", "PRODUCT.md", "REVIEW.md"}
    subagent_re = re.compile(r"""subagent_type["']?\s*[:=]\s*["']([^"']+)["']""")
    skill_re = re.compile(r"""Skill\(\s*["']([^"']+)["']""")
    workflow_re = re.compile(r"""Workflow\(\s*\{[^}]*?name:\s*["']([^"']+)["']""")
    rules_re = re.compile(r"\$\{rulesDir\}/([A-Za-z0-9._-]+\.md)")

    for path in scan_files():
        text = read(path)
        base = os.path.dirname(path)

        for m in subagent_re.finditer(text):
            name = m.group(1).strip()
            if name.lower() in ROLE_LABELS or "$" in name or "<" in name:
                continue
            bare = name.split(":", 1)[1] if name.startswith(OWN_NAMESPACE + ":") else name
            if ":" in bare:
                checked += 1
                if name not in EXTERNAL_ROUTES and name not in PLACEHOLDER_ROUTES:
                    problems.append(external_problem(path, lineno(text, m.start()), name, "agent"))
                continue
            checked += 1
            if bare not in agents:
                problems.append(f"{path}:{lineno(text, m.start())}: subagent_type \"{name}\" — no agents/{bare}.md")

        for m in skill_re.finditer(text):
            name = m.group(1).strip()
            bare = name.split(":", 1)[1] if name.startswith(OWN_NAMESPACE + ":") else name
            if "$" in bare or "<" in bare:
                continue
            if ":" in bare:
                checked += 1
                if name not in EXTERNAL_ROUTES and name not in PLACEHOLDER_ROUTES:
                    problems.append(external_problem(path, lineno(text, m.start()), name, "skill"))
                continue
            checked += 1
            if bare not in skills:
                problems.append(f"{path}:{lineno(text, m.start())}: Skill(\"{name}\") — no skills/{bare}/SKILL.md")

        for m in workflow_re.finditer(text):
            name = m.group(1).strip()
            if "$" in name or "<" in name:
                continue
            bare = name.split(":", 1)[1] if name.startswith(OWN_NAMESPACE + ":") else name
            if ":" in bare:
                continue
            checked += 1
            if bare not in workflows:
                problems.append(f"{path}:{lineno(text, m.start())}: Workflow({{name:'{name}'}}) — no workflows/{bare}.js")
            elif not name.startswith(OWN_NAMESPACE + ":"):
                problems.append(
                    f"{path}:{lineno(text, m.start())}: Workflow({{name:'{name}'}}) — a plugin workflow "
                    f"is namespaced; use '{OWN_NAMESPACE}:{bare}' or the name will not resolve"
                )

        for m in rules_re.finditer(text):
            name = m.group(1)
            # `${rulesDir}` resolves inside the HOST project, which is free to keep rules this
            # plugin never ships — `routing-supplements.md` is explicitly optional. So a name the
            # plugin does not have is not a defect. What IS a defect is citing a template the
            # plugin ships under a different case: on a case-sensitive filesystem that never
            # resolves, and it reads as correct in every review.
            if name in rules:
                continue
            lower = {r.lower(): r for r in rules}
            if name.lower() in lower:
                checked += 1
                problems.append(
                    f"{path}:{lineno(text, m.start())}: ${{rulesDir}}/{name} — the shipped template is "
                    f"`{lower[name.lower()]}`. On a case-sensitive filesystem this never resolves."
                )

        for m in list(section_re.finditer(text)) + list(phase_re.finditer(text)):
            target, sec = m.group(1), m.group(2)
            if os.path.basename(target) in HOST_SPECS:
                continue
            resolved = resolve(target, base)
            if resolved is None or not resolved.endswith(".md"):
                continue                      # the path gate owns missing files; do not double-report
            if os.path.normpath(resolved) == os.path.normpath(path):
                continue                      # a file citing its own section — the reader is already there
            checked += 1
            if sec not in sections_of(resolved):
                problems.append(
                    f"{path}:{lineno(text, m.start())}: cites {target} § {sec}, which has no such section"
                )

    problems += external_routes()
    frontmatter = agent_frontmatter() + namespaced_spawns()
    for p in frontmatter:
        print(f"AGENT:   {p}")
    for p in problems:
        print(f"WIRING: {p}")
    print(f"\n{checked} routing references checked, {len(problems)} unresolved; "
          f"{len(glob.glob('agents/*.md'))} agents checked, {len(frontmatter)} that would not register")
    problems += frontmatter
    if problems:
        print("::error::a routing reference does not resolve — the model reads it, finds nothing, and continues")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
