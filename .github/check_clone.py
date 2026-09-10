"""What a clone must contain, checked against the checkout itself.

The clone includes canonical sources and a generated, self-contained Hermes package. Each has
its own byte budget; together they bound the complete tree, including untracked candidates.
"""

import os
import subprocess
import sys
from pathlib import PurePosixPath

REQUIRED = [
    "bin/graph-powers.mjs", "bin/oxc-setup.mjs", "bin/audit-settings.mjs",
    "bin/hook-client-verifier.mjs", "bin/verify-hook-clients.py",
    "codex/install.mjs", "codex/lib.mjs", "codex/model-policy.json", "codex/model-policy.mjs",
    "cursor/install.mjs",
    "grok/install.mjs",
    "hermes/install.mjs", "hermes/skills/graph-engineering/SKILL.md", "plugin.yaml", "__init__.py",
    "hooks/hooks.json", "hooks/_config.py", "hooks/test_hooks.py", "hooks/auto_update.py",
    ".github/check_oxc_policy.py", ".oxlintrc.json", ".oxfmtrc.json",
    "hooks/hooks-cursor.json",
    "schema/config.schema.json",
    ".claude-plugin/plugin.json", ".claude-plugin/marketplace.json",
    ".cursor-plugin/plugin.json",
    ".grok-plugin/plugin.json", ".grok-plugin/marketplace.json",
    ".codex-plugin/plugin.json", ".codex-plugin/marketplace.json",
    "codex/native-plugin.mjs", "codex/native-command-skills/verify/SKILL.md",
    "AGENT_SETUP.md", "README.md", "LICENSE", "NOTICE", "CHANGELOG.md",
    "DESIGN.md", "PRODUCT.md", "REVIEW.md", "AGENTS.md", "CONTRIBUTING.md",
    "templates/zed/settings.json", "templates/vscode/settings.json", "templates/vscode/extensions.json",
    "commands/setup.md", "references/shared/130-typescript7-oxc-gates.md",
    "docs/ARCHITECTURE.md", "docs/AUDIENCE.md",
]
REQUIRED_DIRS = [
    "agents", "skills", "commands", "references", "templates", "examples", "workflows",
    "hermes", "codex/native-agents", "codex/native-command-skills",
]
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_HERMES_BYTES = 2 * 1024 * 1024

missing = [f for f in REQUIRED if not os.path.exists(f)]
missing += [d + "/" for d in REQUIRED_DIRS if not os.path.isdir(d) or not os.listdir(d)]

try:
    inventory = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        capture_output=True, check=False,
    )
except OSError:
    print("::error::cannot enumerate clone candidates: Git is unavailable")
    sys.exit(1)
if inventory.returncode != 0:
    print(f"::error::cannot enumerate clone candidates: Git exited {inventory.returncode}")
    sys.exit(1)
candidates = sorted({os.fsdecode(name) for name in inventory.stdout.split(b"\0") if name})

# Compiled Python is gitignored, but an ignore rule is not proof that nothing was committed before
# the rule existed.
junk = [f for f in candidates if "__pycache__" in f or f.endswith(".pyc")]

source_size = 0
hermes_size = 0
for name in candidates:
    if os.path.exists(name):
        if PurePosixPath("hermes/package") in PurePosixPath(name).parents:
            hermes_size += os.path.getsize(name)
        else:
            source_size += os.path.getsize(name)
total_size = source_size + hermes_size

for m in missing:
    print(f"MISSING: {m}")
for j in junk:
    print(f"CANDIDATE JUNK: {j}")
print(f"{len(candidates)} candidate files (tracked and untracked, excluding ignored untracked files)")
print(f"Source: {source_size} bytes ({source_size / 1024:.2f} KiB) / {MAX_SOURCE_BYTES} bytes")
print(f"Hermes package: {hermes_size} bytes ({hermes_size / 1024:.2f} KiB) / {MAX_HERMES_BYTES} bytes")
print(f"Total: {total_size} bytes ({total_size / 1024:.2f} KiB) / {MAX_SOURCE_BYTES + MAX_HERMES_BYTES} bytes (source + Hermes)")

if source_size > MAX_SOURCE_BYTES:
    print("::error::the source grew past 4 MiB — check what got vendored back in")
if hermes_size > MAX_HERMES_BYTES:
    print("::error::the Hermes package grew past 2 MiB — check its generated dependency closure")
if missing:
    print("::error::a clone would not contain everything the installer needs")

sys.exit(1 if missing or junk or source_size > MAX_SOURCE_BYTES or hermes_size > MAX_HERMES_BYTES else 0)
