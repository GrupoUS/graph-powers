#!/usr/bin/env python3
"""Every name an artefact routes to has to resolve.

The existing dangling gate checks file paths, and that is the easy half. What it never saw is the
routing itself — the agent a command spawns, the workflow it invokes, the skill it loads, the
section of another file it tells the reader to apply. Those are the references that break silently:
the model reads the instruction, finds nothing, and carries on with less than it thinks it has.

The audit that motivated this found ten of them in a repository whose CI was already green,
including an agent that has never existed and three phases of `/verify` that were never written.

Five checks, and each one exists because a real reference was wrong in exactly that way:

    subagent_type   an agent the plugin does not ship
    Workflow(name)  a workflow the plugin does not ship
    Skill(name)     a skill the plugin does not ship
    § N / Phase N   a section of another file that is not in it
    ${rulesDir}/x   a rule template the plugin does not ship

The hard part of a gate like this is not finding misses, it is not crying wolf: a gate with false
positives gets `|| true` appended to it within a week. So every check is deliberately narrow, every
external namespace is skipped rather than guessed at, and anything ambiguous is left alone.
"""

from __future__ import annotations

import glob
import os
import re
import sys

# Namespaced references belong to somebody else's plugin. `superpowers:brainstorming` is a real
# dependency, declared in the README, and this repository cannot check it — nor should it try.
OWN_NAMESPACE = "graph-powers"

# Names that are roles in prose, not routing targets. Each one was checked by hand once; the
# rubric at references/rubrics/skill-improver-rubric.md warns about exactly this class.
ROLE_LABELS = {
    "code archaeologist", "regression hunter", "evidence collector",
    "db state inspector", "db-state-inspector", "main",
}

SCAN = ["agents", "commands", "skills", "references", "templates", "hooks", "workflows"]


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
                continue                      # another plugin's agent, not ours to verify
            checked += 1
            if bare not in agents:
                problems.append(f"{path}:{lineno(text, m.start())}: subagent_type \"{name}\" — no agents/{bare}.md")

        for m in skill_re.finditer(text):
            name = m.group(1).strip()
            bare = name.split(":", 1)[1] if name.startswith(OWN_NAMESPACE + ":") else name
            if ":" in bare or "$" in bare or "<" in bare:
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

    for p in problems:
        print(f"WIRING: {p}")
    print(f"\n{checked} routing references checked, {len(problems)} unresolved")
    if problems:
        print("::error::a routing reference does not resolve — the model reads it, finds nothing, and continues")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
