#!/usr/bin/env python3
"""Machine-local approval for commands declared by a project config.

The repository config is the authority for *what* a hook may run. This module owns the separate
operator decision for *whether this exact config* may run it on this machine. Only hashes are
stored, so the registry cannot become a project inventory or a second command configuration.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
import time
import unicodedata
from pathlib import Path
from typing import Any

import _config as gp

REGISTRY_VERSION = 1
MAX_PROJECTS = 256
REGISTRY_NAME = "command-trust.json"


def _home(home: Path | None = None) -> Path | None:
    if home is not None:
        return home
    try:
        return Path.home()
    except Exception:
        return None


def registry_path(home: Path | None = None) -> Path | None:
    base = _home(home)
    return base / ".graph-powers" / REGISTRY_NAME if base is not None else None


def _path_bytes(path: Path) -> bytes:
    """Return the exact cross-platform bytes used for canonical path hashes."""
    resolved = path.resolve(strict=True)
    text = os.path.normcase(str(resolved)).replace("\\", "/")
    return unicodedata.normalize("NFC", text).encode("utf-8", "surrogatepass")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _root(project: Path) -> Path | None:
    try:
        if not project.is_dir():
            return None
        resolved = project.resolve(strict=True)
        git_root = gp._git_root(resolved)
        return git_root.resolve(strict=True) if git_root is not None else resolved
    except Exception:
        return None


def _identity(project: Path) -> tuple[str, str, str] | None:
    """Return ``(root hash, config hash, raw config digest)`` or no trusted identity."""
    try:
        root = _root(project)
        if root is None:
            return None
        config = gp.config_path(root)
        if config is None:
            return None
        canonical_config = config.resolve(strict=True)
        if not canonical_config.is_file() or not canonical_config.is_relative_to(root):
            return None
        raw = canonical_config.read_bytes()
        return (_sha256(_path_bytes(root)), _sha256(_path_bytes(canonical_config)), _sha256(raw))
    except Exception:
        return None


def _empty_registry() -> dict[str, Any]:
    return {"version": REGISTRY_VERSION, "projects": {}}


def _valid_entry(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"configPathHash", "configSha256", "approvedAt"}
        and isinstance(value.get("configPathHash"), str)
        and len(value["configPathHash"]) == 64
        and all(char in "0123456789abcdef" for char in value["configPathHash"])
        and isinstance(value.get("configSha256"), str)
        and len(value["configSha256"]) == 64
        and all(char in "0123456789abcdef" for char in value["configSha256"])
        and isinstance(value.get("approvedAt"), (int, float))
        and not isinstance(value.get("approvedAt"), bool)
        and math.isfinite(value["approvedAt"])
    )


def _read_registry(home: Path | None = None) -> dict[str, Any] | None:
    path = registry_path(home)
    if path is None:
        return None
    try:
        if not path.is_file():
            return None
        value = json.loads(path.read_text(encoding="utf-8"))
        projects = value.get("projects") if isinstance(value, dict) else None
        if (
            not isinstance(value, dict)
            or set(value) != {"version", "projects"}
            or value.get("version") != REGISTRY_VERSION
            or not isinstance(projects, dict)
        ):
            return None
        if len(projects) > MAX_PROJECTS or any(
            not isinstance(key, str) or len(key) != 64 or
            any(char not in "0123456789abcdef" for char in key) or
            not _valid_entry(entry)
            for key, entry in projects.items()
        ):
            return None
        return value
    except Exception:
        return None


def _write_registry(value: dict[str, Any], home: Path | None = None) -> bool:
    path = registry_path(home)
    if path is None:
        return False
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
                json.dump(value, stream, sort_keys=True, separators=(",", ":"))
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            if os.name != "nt":
                os.chmod(temporary, 0o600)
            os.replace(temporary, path)
            if os.name != "nt":
                os.chmod(path, 0o600)
            return True
        finally:
            try:
                Path(temporary).unlink(missing_ok=True)
            except Exception:
                pass
    except Exception:
        return False


def is_trusted(project: Path, *, home: Path | None = None) -> bool:
    identity = _identity(Path(project))
    registry = _read_registry(home)
    if identity is None or registry is None:
        return False
    root_hash, config_hash, digest = identity
    entry = registry["projects"].get(root_hash)
    return bool(
        isinstance(entry, dict)
        and entry.get("configPathHash") == config_hash
        and entry.get("configSha256") == digest
    )


def approve(project: Path, *, home: Path | None = None) -> bool:
    identity = _identity(Path(project))
    if identity is None:
        return False
    path = registry_path(home)
    if path is None:
        return False
    registry = _read_registry(home)
    # A missing registry is the normal first approval. A malformed registry is not trusted, but an
    # explicit human approval may repair it by replacing the unusable local state.
    if registry is None and path.exists():
        registry = _empty_registry()
    registry = registry or _empty_registry()
    root_hash, config_hash, digest = identity
    registry["projects"][root_hash] = {
        "configPathHash": config_hash,
        "configSha256": digest,
        "approvedAt": time.time(),
    }
    while len(registry["projects"]) > MAX_PROJECTS:
        oldest = min(
            registry["projects"],
            key=lambda key: (registry["projects"][key].get("approvedAt", 0), key),
        )
        del registry["projects"][oldest]
    return _write_registry(registry, home)


def revoke(project: Path, *, home: Path | None = None) -> bool:
    root = _root(Path(project))
    registry = _read_registry(home)
    if root is None or registry is None:
        return False
    try:
        root_hash = _sha256(_path_bytes(root))
        if root_hash not in registry["projects"]:
            return False
        del registry["projects"][root_hash]
        return _write_registry(registry, home)
    except Exception:
        return False


def status(project: Path, *, home: Path | None = None) -> dict[str, Any]:
    """Return a safe status object for the approval CLI and tests."""
    identity = _identity(Path(project))
    trusted = is_trusted(Path(project), home=home)
    return {
        "trusted": trusted,
        "configSha256": identity[2][:12] if identity is not None else None,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Approve project-configured Graph Powers commands")
    parser.add_argument("action", choices=("approve", "status", "revoke"))
    parser.add_argument("project", nargs="?", default=".")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        project = Path(args.project)
        if args.action == "approve":
            ok = approve(project)
            print(json.dumps({"approved": ok}, separators=(",", ":")))
            return 0 if ok else 1
        if args.action == "revoke":
            ok = revoke(project)
            print(json.dumps({"revoked": ok}, separators=(",", ":")))
            return 0 if ok else 1
        print(json.dumps(status(project), separators=(",", ":")))
        return 0
    except Exception:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
