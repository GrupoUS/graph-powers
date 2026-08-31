"""What a clone must contain, checked against the checkout itself.

There is no package step and no tarball: whatever `git clone` produces is what runs on somebody
else's machine. So the assertions are about the tracked tree, not about an archive.
"""

import os
import subprocess
import sys

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
    "codex/native-plugin.mjs",
    "AGENT_SETUP.md", "README.md", "LICENSE", "NOTICE", "CHANGELOG.md",
    "DESIGN.md", "PRODUCT.md", "REVIEW.md", "AGENTS.md", "CONTRIBUTING.md",
    "templates/zed/settings.json", "templates/vscode/settings.json", "templates/vscode/extensions.json",
    "commands/setup.md", "references/shared/130-typescript7-oxc-gates.md",
    "docs/ARCHITECTURE.md", "docs/AUDIENCE.md",
]
REQUIRED_DIRS = ["agents", "skills", "commands", "references", "templates", "examples", "workflows", "hermes", "codex/native-agents"]
MAX_BYTES = 4 * 1024 * 1024

missing = [f for f in REQUIRED if not os.path.exists(f)]
missing += [d + "/" for d in REQUIRED_DIRS if not os.path.isdir(d) or not os.listdir(d)]

tracked = subprocess.run(
    ["git", "ls-files"], capture_output=True,
    encoding="utf-8", errors="replace", check=False
).stdout.splitlines()

# Compiled Python is gitignored, but an ignore rule is not proof that nothing was committed before
# the rule existed.
junk = [f for f in tracked if "__pycache__" in f or f.endswith(".pyc")]

size = sum(os.path.getsize(f) for f in tracked if os.path.exists(f))

for m in missing:
    print(f"MISSING: {m}")
for j in junk:
    print(f"TRACKED JUNK: {j}")
print(f"{len(tracked)} tracked files, {size // 1024} KB")

if size > MAX_BYTES:
    print("::error::the clone grew past 4 MB — check what got vendored back in")
if missing:
    print("::error::a clone would not contain everything the installer needs")

sys.exit(1 if missing or junk or size > MAX_BYTES else 0)
