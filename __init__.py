"""Hermes native plugin for Graph Powers.

Registers skills and agent contracts from this checkout. Adds no tools and no
hooks: Hermes does not run Claude ``hooks/hooks.json``. Git rails stay with the
parent (SOUL + approvals), same class as Zed in AGENT_SETUP.md.

Discovery is the directory tree, not a hand list: a skill folder that gains a
SKILL.md is registered on the next Hermes start.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PLUGIN_ROOT = Path(__file__).resolve().parent
AGENT_NAME_PREFIX = "agent-"


def _frontmatter_description(path: Path, fallback: str) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return fallback
    close = text.find("\n---", 3)
    if close < 0:
        return fallback
    for line in text[3:close].splitlines():
        stripped = line.strip()
        if stripped.startswith("description:"):
            value = stripped.split(":", 1)[1].strip().strip("\"'")
            return value or fallback
    return fallback


def planned_registrations(root: Path | None = None) -> list[tuple[str, Path, str]]:
    """Return ``(name, path, description)`` for every file this plugin ships."""
    base = PLUGIN_ROOT if root is None else root
    planned: list[tuple[str, Path, str]] = []

    hermes_skills = base / "hermes" / "skills"
    if hermes_skills.is_dir():
        for folder in sorted(hermes_skills.iterdir()):
            skill = folder / "SKILL.md"
            if folder.is_dir() and skill.is_file():
                planned.append((folder.name, skill, _frontmatter_description(skill, folder.name)))

    skills_root = base / "skills"
    if skills_root.is_dir():
        for folder in sorted(skills_root.iterdir()):
            skill = folder / "SKILL.md"
            if folder.is_dir() and skill.is_file():
                planned.append((folder.name, skill, _frontmatter_description(skill, folder.name)))

    agents_root = base / "agents"
    if agents_root.is_dir():
        for agent in sorted(agents_root.glob("*.md")):
            if agent.name.upper() == "AGENTS.MD":
                continue
            slug = agent.stem
            planned.append(
                (
                    f"{AGENT_NAME_PREFIX}{slug}",
                    agent,
                    _frontmatter_description(agent, slug),
                )
            )
    return planned


def register(ctx: Any) -> None:
    """Register skills and agent contracts. No tools, no hooks."""
    registered = 0
    for name, path, description in planned_registrations():
        if not path.is_file():
            logger.warning("graph-powers: skipping '%s' — no file at %s", name, path)
            continue
        ctx.register_skill(name, path, description)
        registered += 1
    logger.debug("graph-powers: registered %d skills from %s", registered, PLUGIN_ROOT)
