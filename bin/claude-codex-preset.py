"""Apply the plugin's Codex model policy to Claude Code's global model aliases."""

import argparse
import json
import os
import sys
from pathlib import Path


def apply_preset(settings_path: Path, *, apply: bool) -> None:
    root = Path(__file__).resolve().parents[1]
    policy = json.loads((root / "codex/model-policy.json").read_text(encoding="utf-8"))
    models = {
        "ANTHROPIC_DEFAULT_SONNET_MODEL": policy["agentDefaults"]["evaluator"]["model"],
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": policy["profiles"]["scout"]["model"],
    }
    if any(not isinstance(model, str) or not model.strip() for model in models.values()):
        raise ValueError("Codex policy must declare non-empty model IDs")
    settings = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
    if not isinstance(settings, dict) or not isinstance(settings.get("env", {}), dict):
        raise ValueError("Claude settings and env must be JSON objects")
    env = settings.get("env", {})
    force = "CLAUDE_CODE_SUBAGENT_MODEL_FORCE"
    if any(str(value).lower() not in {"", "0", "false"} for value in [
        env.get(force, ""), os.environ.get(force, ""),
    ]):
        raise ValueError(f"{force} prevents per-agent routing; no settings were changed")
    changed = any(env.get(key) != value for key, value in models.items())
    if apply and changed:
        settings["env"] = {**env, **models}
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    state = "applied" if apply and changed else "current" if not changed else "preview"
    print(f"Claude Codex preset: {state} ({settings_path})")
    for alias, model in models.items():
        print(f"{alias} -> {model}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write aliases; without this, only preview")
    home = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    parser.add_argument("--settings", type=Path, default=home / "settings.json")
    args = parser.parse_args()
    try:
        apply_preset(args.settings.expanduser(), apply=args.apply)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Claude Codex preset failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
