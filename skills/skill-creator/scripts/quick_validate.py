#!/usr/bin/env python3
"""
Quick validation script for skills - minimal version
"""

import sys
import os
import re
from pathlib import Path


def validate_skill(skill_path):
    """Basic validation of a skill"""
    skill_path = Path(skill_path)

    # Check SKILL.md exists
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return False, "SKILL.md not found"

    # Read and validate frontmatter
    content = skill_md.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return False, "No YAML frontmatter found"

    # Extract frontmatter
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return False, "Invalid frontmatter format"

    frontmatter = match.group(1)

    # Check required fields
    if "name:" not in frontmatter:
        return False, "Missing 'name' in frontmatter"
    if "description:" not in frontmatter:
        return False, "Missing 'description' in frontmatter"

    # Extract name for validation
    name = None
    name_match = re.search(r"name:\s*(.+)", frontmatter)
    if name_match:
        name = name_match.group(1).strip()
        # Check naming convention (hyphen-case: lowercase with hyphens)
        if not re.match(r"^[a-z0-9-]+$", name):
            return (
                False,
                f"Name '{name}' should be hyphen-case (lowercase letters, digits, and hyphens only)",
            )
        if name.startswith("-") or name.endswith("-") or "--" in name:
            return (
                False,
                f"Name '{name}' cannot start/end with hyphen or contain consecutive hyphens",
            )

        # Rule 3: Directory-name alignment check
        dir_name = skill_path.name
        if name != dir_name:
            return (
                False,
                f"Frontmatter name '{name}' must match directory name '{dir_name}'",
            )

    # Extract and validate description
    description = None
    desc_match = re.search(r"description:\s*(.+)", frontmatter)
    if desc_match:
        description = desc_match.group(1).strip()
        # Check for angle brackets
        if "<" in description or ">" in description:
            return False, "Description cannot contain angle brackets (< or >)"

        # Rule 1: Description length check (<= 1024 characters)
        if len(description) > 1024:
            return (
                False,
                f"Description exceeds 1024 characters (current: {len(description)})",
            )

        # Rule 4: Trigger phrase check (warning only, not failure)
        trigger_phrases = ["use when", "use for", "use to", "help with"]
        desc_lower = description.lower()
        if not any(desc_lower.startswith(phrase) for phrase in trigger_phrases):
            print(
                f"WARNING: Description should start with one of: {trigger_phrases}",
                file=sys.stderr,
            )

    # Rule 2: Line count check (<= 500 lines after frontmatter)
    # Find where frontmatter ends and calculate body line count
    frontmatter_end_match = re.match(r"^---\n.*?\n---", content, re.DOTALL)
    if frontmatter_end_match:
        body_content = content[frontmatter_end_match.end() :]
        body_lines = body_content.split("\n")
        # Count non-empty lines (excluding the trailing newline)
        body_line_count = len([line for line in body_lines if line.strip()])
        if body_line_count > 500:
            return (
                False,
                f"SKILL.md body exceeds 500 lines (current: {body_line_count})",
            )

    return True, "Skill is valid!"


def find_all_skills(parent_dir):
    """Find all skill directories (containing SKILL.md) under parent_dir"""
    parent_path = Path(parent_dir)
    skills = []

    if not parent_path.exists():
        return skills

    # Scan immediate subdirectories for SKILL.md
    for item in parent_path.iterdir():
        if item.is_dir() and (item / "SKILL.md").exists():
            skills.append(item)

    return sorted(skills, key=lambda x: x.name)


def batch_validate(parent_dir):
    """Run validation on all skills under parent_dir"""
    skills = find_all_skills(parent_dir)

    if not skills:
        print(f"No skills found in {parent_dir}")
        return 1

    print(f"Scanning {parent_dir}...")
    print(f"Found {len(skills)} skills\n")

    passed = 0
    failed = 0
    failed_skills = []

    for skill in skills:
        valid, message = validate_skill(skill)

        if valid:
            print(f"PASS: {skill.name}")
            passed += 1
        else:
            print(f"FAIL: {skill.name} - {message}")
            failed += 1
            failed_skills.append((skill.name, message))

    # Summary
    print(f"\nSummary: {passed} passed, {failed} failed")

    if failed > 0:
        print(f"Exit code: 1 (if any failures)")
        return 1

    return 0


if __name__ == "__main__":
    # Parse arguments
    if "--all" in sys.argv:
        # Batch mode
        sys.argv.remove("--all")

        if len(sys.argv) != 2:
            print("Usage: python quick_validate.py --all <skills_parent_directory>")
            sys.exit(1)

        exit_code = batch_validate(sys.argv[1])
        sys.exit(exit_code)
    else:
        # Single skill mode (original behavior)
        if len(sys.argv) != 2:
            print("Usage: python quick_validate.py <skill_directory>")
            print("       python quick_validate.py --all <skills_parent_directory>")
            sys.exit(1)

        valid, message = validate_skill(sys.argv[1])
        print(message)
        sys.exit(0 if valid else 1)
