#!/usr/bin/env python3
"""
Skill Initializer - Creates a new skill from template

Usage:
    init_skill.py <skill-name> --path <parent-directory>

Examples:
    init_skill.py my-new-skill --path skills
    init_skill.py my-api-helper --path .claude/skills

The scaffold is a starting point: every TODO is meant to be replaced, and the frontmatter it writes
already has the shape the validator accepts — a quoted single-line description with no colon-space
and no brackets — so that copying its shape does not reproduce the one YAML mistake that once left
four command files unregistered without anything noticing.
"""

import re
import sys
from pathlib import Path


def is_valid_kebab_case(name):
    if not re.match(r"^[a-z0-9-]+$", name):
        return (
            False,
            f"Name '{name}' must contain only lowercase letters, digits, and hyphens",
        )
    if name.startswith("-") or name.endswith("-") or "--" in name:
        return (
            False,
            f"Name '{name}' cannot start/end with hyphen or contain consecutive hyphens",
        )
    return True, None


SKILL_TEMPLATE = """---
name: {skill_name}
description: "TODO Write a trigger-oriented description that starts with Use when, naming the conditions and the phrases users actually type. Keep it a quoted single line under 1024 characters, with no colon-space, no angle brackets and no square brackets. Replace this whole value before shipping."
---

# {skill_title}

## Overview

[TODO: 1-2 sentences explaining what this skill enables]

## When to Use

[TODO: List specific scenarios, file types, or tasks that trigger this skill]

## Core Pattern

[TODO: Show the main pattern or workflow this skill provides]

## Implementation

[TODO: Add detailed implementation guidance, code examples, or step-by-step instructions]

## Resources

This skill may include example resource directories:

### scripts/
Optional executable code (Python/Bash/etc.). Delete if not needed.

### references/
Optional documentation to load into context. Delete if not needed.

### assets/
Optional files for output (templates, images, etc.). Delete if not needed.

---

Delete any unneeded directories. This is a starting point, not a complete skill.
"""

EXAMPLE_SCRIPT = '''#!/usr/bin/env python3
"""Example script for {skill_name}. Delete if not needed."""

def main():
    print("Example script for {skill_name}")
    # TODO: Add actual script logic here

if __name__ == "__main__":
    main()
'''

EXAMPLE_REFERENCE = """# Reference for {skill_title}

Delete this file if not needed. Use for detailed documentation too lengthy for SKILL.md.
"""

EXAMPLE_ASSET = """# Placeholder for {skill_name} assets

Delete this file if not needed. Add templates, images, fonts, or other files here.
"""

# One positive and one negative case, in the shape `run_evals.py` reads. Both are placeholders:
# the runner scores them, so a skill shipped with these untouched fails its own trigger gate.
EXAMPLE_EVALS = """{{
  "skill_name": "{skill_name}",
  "notes": "TODO at least 3 positive and 3 negative cases; negatives at the border with the real competitor.",
  "evals": [
    {{
      "id": "pos-TODO",
      "polarity": "positive",
      "prompt": "TODO a prompt a real user would type that must fire this skill",
      "expected_output": "TODO what success looks like",
      "assertions": [
        {{ "id": "A01", "description": "The skill fires.", "check": "regex: (?i){skill_name}\\\\b", "critical": true }}
      ]
    }},
    {{
      "id": "neg-TODO",
      "polarity": "negative",
      "prompt": "TODO a near-miss prompt that shares words with this skill and must route elsewhere",
      "expected_output": "TODO where it routes instead",
      "assertions": [
        {{ "id": "A01", "description": "Routes to the competitor, stated positively.", "check": "regex: (?i)TODO-competitor-name", "critical": true }}
      ]
    }}
  ]
}}
"""

EXAMPLE_LEARNING = """# learning.md — round history for `{skill_name}`

One entry per round: hypothesis, change, measurement, verdict. A round with no measured number is a
hunch with markdown around it. A round that changed nothing still gets an entry saying so.

## Round 1 — YYYY-MM-DD · TODO one-line subject

**Hypothesis:** TODO what you expected before looking.
**Change:** TODO what you did.
**Measurement:** TODO command output, quoted. Numbers, not adjectives.
**Verdict:** TODO kept, refuted, or partial — and what the evidence killed.
"""


def title_case_skill_name(skill_name):
    """Convert hyphenated skill name to Title Case for display."""
    return " ".join(word.capitalize() for word in skill_name.split("-"))


def init_skill(skill_name, path):
    """
    Initialize a new skill directory with template SKILL.md.

    Args:
        skill_name: Name of the skill
        path: Path where the skill directory should be created

    Returns:
        Path to created skill directory, or None if error
    """
    # Validate skill name is kebab-case
    valid, error = is_valid_kebab_case(skill_name)
    if not valid:
        print(f"❌ Error: {error}")
        return None

    # Determine skill directory path
    skill_dir = Path(path).resolve() / skill_name

    # Check if directory already exists
    if skill_dir.exists():
        print(f"❌ Error: Skill directory already exists: {skill_dir}")
        return None

    # Create skill directory
    try:
        skill_dir.mkdir(parents=True, exist_ok=False)
        print(f"✅ Created skill directory: {skill_dir}")
    except Exception as e:
        print(f"❌ Error creating directory: {e}")
        return None

    # Create SKILL.md from template
    skill_title = title_case_skill_name(skill_name)
    skill_content = SKILL_TEMPLATE.format(
        skill_name=skill_name, skill_title=skill_title
    )

    skill_md_path = skill_dir / "SKILL.md"
    try:
        # Explicit encoding everywhere: without it `write_text` uses the locale code page, and a
        # scaffold written on Windows carries the em dashes below as mojibake.
        skill_md_path.write_text(skill_content, encoding="utf-8")
        print("✅ Created SKILL.md")
    except Exception as e:
        print(f"❌ Error creating SKILL.md: {e}")
        return None

    # The two files the anatomy calls for in any skill in regular use, then the optional
    # resource directories with one example each.
    try:
        evals_dir = skill_dir / "evals"
        evals_dir.mkdir(exist_ok=True)
        (evals_dir / "evals.json").write_text(EXAMPLE_EVALS.format(skill_name=skill_name), encoding="utf-8")
        print("✅ Created evals/evals.json")

        (skill_dir / "learning.md").write_text(EXAMPLE_LEARNING.format(skill_name=skill_name), encoding="utf-8")
        print("✅ Created learning.md")

        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        example_script = scripts_dir / "example.py"
        example_script.write_text(EXAMPLE_SCRIPT.format(skill_name=skill_name), encoding="utf-8")
        example_script.chmod(0o755)
        print("✅ Created scripts/example.py")

        references_dir = skill_dir / "references"
        references_dir.mkdir(exist_ok=True)
        example_reference = references_dir / "api_reference.md"
        example_reference.write_text(EXAMPLE_REFERENCE.format(skill_title=skill_title), encoding="utf-8")
        print("✅ Created references/api_reference.md")

        assets_dir = skill_dir / "assets"
        assets_dir.mkdir(exist_ok=True)
        example_asset = assets_dir / "example_asset.txt"
        example_asset.write_text(EXAMPLE_ASSET.format(skill_name=skill_name), encoding="utf-8")
        print("✅ Created assets/example_asset.txt")
    except Exception as e:
        print(f"❌ Error creating resource files: {e}")
        return None

    # Print next steps
    print(f"\n✅ Skill '{skill_name}' initialized successfully at {skill_dir}")
    print("\nNext steps:")
    print("1. Edit SKILL.md to complete the TODO items and replace the description")
    print("2. Write the real cases in evals/evals.json; the placeholders fail the trigger gate on purpose")
    print("3. Customize or delete the example files in scripts/, references/, and assets/")
    print("4. Run quick_validate.py, then run_evals.py --response-dir, before shipping")

    return skill_dir


def main():
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) < 4 or sys.argv[2] != "--path":
        print("Usage: init_skill.py <skill-name> --path <parent-directory>")
        print("\nSkill name requirements:")
        print("  - Hyphen-case identifier (e.g., 'data-analyzer')")
        print("  - Lowercase letters, digits, and hyphens only")
        print("  - Max 40 characters")
        print("  - Must match directory name exactly")
        print("\nExamples:")
        print("  init_skill.py my-new-skill --path skills")
        print("  init_skill.py my-api-helper --path .claude/skills")
        sys.exit(1)

    skill_name = sys.argv[1]
    path = sys.argv[3]

    print(f"🚀 Initializing skill: {skill_name}")
    print(f"   Location: {path}")
    print()

    result = init_skill(skill_name, path)

    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
