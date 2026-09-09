"""Generated Hermes registrations; no tools, hooks or runtime source generation."""

import json
from pathlib import Path, PurePosixPath

PLUGIN_ROOT = Path(__file__).resolve().parent


def planned_registrations(root=None):
    base = (PLUGIN_ROOT if root is None else Path(root)).resolve()
    plan = json.loads((base / "PROVENANCE.json").read_text(encoding="utf-8"))
    planned = []
    names = set()
    paths = set()
    for row in plan["registrations"]:
        name, relative = row["name"], PurePosixPath(row["path"])
        if (not isinstance(name, str) or not name or name.casefold() in names
                or relative.is_absolute() or ".." in relative.parts
                or "\\" in row["path"] or relative.parent != PurePosixPath("skills")):
            raise ValueError("invalid or duplicate Hermes registration")
        path = (base / relative).resolve()
        if not path.is_relative_to(base / "skills") or not path.is_file() or path in paths:
            raise ValueError("missing or escaping Hermes registration source")
        names.add(name.casefold())
        paths.add(path)
        planned.append((name, path, row["description"]))
    return planned


def register(ctx):
    for name, path, description in planned_registrations():
        ctx.register_skill(name, path, description)
