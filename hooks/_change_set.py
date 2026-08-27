"""Complete, bounded-by-time Git changeset assessment for the Stop verifier."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO, cast

import _config as gp

STATUS_TIMEOUT_S = 10
FINGERPRINT_VERSION = "gp-precommit-v1"
FINGERPRINT_BUDGET_S = 15.0
GIT_METADATA_CAP = 8 * 1024 * 1024
STREAM_CHUNK = 1024 * 1024
CACHE_NAME = "precommit-verification.json"
CACHE_VERSION = 1
CACHE_MAX_BYTES = 32 * 1024
CACHE_MAX_ENTRIES = 5


@dataclass(frozen=True)
class ChangeSet:
    """The paths Git reports and whether the assessment itself completed."""

    paths: tuple[str, ...]
    assessed: bool
    project_dir: Path | None


def _parse_status(raw: str) -> tuple[str, ...]:
    """Parse porcelain-v1 -z records, including the second record of a rename."""
    records = raw.split("\0")
    paths: list[str] = []
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        if len(record) < 3 or record[2] != " ":
            raise ValueError("malformed git status record")
        status = record[:2]
        path = record[3:]
        if path:
            paths.append(path)
        if "R" in status or "C" in status:
            if index >= len(records) or not records[index]:
                raise ValueError("incomplete git rename record")
            paths.append(records[index])
            index += 1
    return tuple(paths)


def collect_change_set(payload: dict[str, Any] | None) -> ChangeSet:
    """Read every Git change for the project resolved from the hook payload.

    ``assessed`` is deliberately separate from ``paths``: an empty list after a failed Git call
    must not be mistaken for a clean tree by the Stop verifier.
    """
    try:
        project = gp.project_dir(payload)
    except Exception:
        return ChangeSet((), False, None)
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
            cwd=str(project),
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=STATUS_TIMEOUT_S,
            check=False,
        )
        if result.returncode != 0:
            return ChangeSet((), False, project)
        return ChangeSet(_parse_status(result.stdout or ""), True, project)
    except Exception:
        return ChangeSet((), False, project)


def _path_bytes(path: Path) -> bytes:
    resolved = path.resolve(strict=True)
    text = os.path.normcase(str(resolved)).replace("\\", "/")
    return unicodedata.normalize("NFC", text).encode("utf-8", "surrogatepass")


def _frame(hasher: hashlib._Hash, label: str, value: bytes) -> None:
    label_bytes = label.encode("utf-8", "surrogatepass")
    hasher.update(len(label_bytes).to_bytes(8, "big"))
    hasher.update(label_bytes)
    hasher.update(len(value).to_bytes(8, "big"))
    hasher.update(value)


def _frame_stream(hasher: hashlib._Hash, label: str, stream: BinaryIO, size: int,
                  deadline: float | None = None) -> bool:
    """Add a raw-byte frame from a bounded stream without retaining its contents."""
    label_bytes = label.encode("utf-8", "surrogatepass")
    hasher.update(len(label_bytes).to_bytes(8, "big"))
    hasher.update(label_bytes)
    hasher.update(size.to_bytes(8, "big"))
    total = 0
    while total < size:
        if deadline is not None and _remaining(deadline) <= 0:
            return False
        block = stream.read(min(STREAM_CHUNK, size - total))
        if not block:
            return False
        hasher.update(block)
        total += len(block)
    return total == size


@dataclass
class _GitCapture:
    path: Path
    stream: BinaryIO
    size: int

    def cleanup(self) -> None:
        try:
            self.stream.close()
        finally:
            try:
                self.path.unlink(missing_ok=True)
            except Exception:
                pass


def frame_digest(frames: list[tuple[str, bytes]]) -> str:
    """Hash length-framed values; exposed for tests of the ambiguity-resistant protocol."""
    digest = hashlib.sha256()
    for label, value in frames:
        _frame(digest, label, value)
    return digest.hexdigest()


def _remaining(deadline: float) -> float:
    return deadline - time.monotonic()


def _git_to_temp(project: Path, args: list[str], deadline: float,
                 metadata_total: list[int]) -> _GitCapture | None:
    temporary_path: Path | None = None
    stream: BinaryIO | None = None
    process: subprocess.Popen[bytes] | None = None
    reader: threading.Thread | None = None
    output: BinaryIO | None = None
    stop = threading.Event()
    state = {"size": 0, "overflow": False, "error": False, "timeout": False}

    def stop_process() -> None:
        if process is None:
            return
        try:
            process.kill()
        except Exception:
            try:
                process.terminate()
            except Exception:
                pass

    try:
        if _remaining(deadline) <= 0:
            return None
        if metadata_total[0] >= GIT_METADATA_CAP:
            return None
        fd, temporary = tempfile.mkstemp(prefix=".gp-precommit-", suffix=".tmp")
        temporary_path = Path(temporary)
        capture_stream = os.fdopen(fd, "w+b")
        stream = capture_stream
        process = subprocess.Popen(
            ["git", *args], cwd=str(project), stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )

        raw_output = process.stdout
        if raw_output is None:
            return None
        process_output = cast(BinaryIO, raw_output)
        output = process_output

        def drain_output() -> None:
            try:
                while not stop.is_set():
                    room = min(GIT_METADATA_CAP - state["size"],
                               GIT_METADATA_CAP - metadata_total[0])
                    if room <= 0:
                        if state["size"] >= GIT_METADATA_CAP:
                            probe = process_output.read(1)
                            if probe:
                                state["overflow"] = True
                        else:
                            state["overflow"] = True
                        break
                    block = process_output.read(STREAM_CHUNK)
                    if not block:
                        break
                    if stop.is_set():
                        break
                    if len(block) > room:
                        state["overflow"] = True
                        break
                    if capture_stream.write(block) != len(block):
                        state["error"] = True
                        break
                    state["size"] += len(block)
                    metadata_total[0] += len(block)
            except Exception:
                state["error"] = True
            finally:
                stop.set()

        reader = threading.Thread(target=drain_output, name="gp-precommit-capture", daemon=True)
        reader.start()
        while reader.is_alive():
            remaining = _remaining(deadline)
            if remaining <= 0:
                state["timeout"] = True
                stop.set()
                stop_process()
                break
            reader.join(min(remaining, 0.05))

        if state["overflow"]:
            stop.set()
            stop_process()
        if reader.is_alive():
            stop.set()
            stop_process()
            reader.join(1.0)
        if reader.is_alive():
            state["error"] = True

        remaining = _remaining(deadline)
        try:
            process.wait(timeout=max(remaining, 0.001))
        except subprocess.TimeoutExpired:
            state["timeout"] = True
            stop.set()
            stop_process()
            try:
                process.wait(timeout=1.0)
            except Exception:
                state["error"] = True

        if (state["overflow"] or state["error"] or state["timeout"] or
                reader.is_alive() or process.returncode != 0):
            return None
        capture_stream.flush()
        size = capture_stream.tell()
        if size != state["size"] or size > GIT_METADATA_CAP:
            return None
        stream.seek(0)
        capture = _GitCapture(temporary_path, capture_stream, size)
        stream = None
        temporary_path = None
        return capture
    except Exception:
        return None
    finally:
        stop.set()
        if process is not None:
            try:
                if process.poll() is None:
                    stop_process()
                process.wait(timeout=1.0)
            except Exception:
                pass
        if reader is not None and reader.is_alive():
            reader.join(1.0)
        if output is not None:
            try:
                output.close()
            except Exception:
                pass
        if stream is not None:
            try:
                stream.close()
            except Exception:
                pass
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except Exception:
                pass


def _add_file_content(hasher: hashlib._Hash, label: str, path: Path,
                      deadline: float | None = None) -> bool:
    try:
        info = path.lstat()
        if path.is_symlink():
            _frame(hasher, label + ":type", b"symlink")
            _frame(hasher, label + ":mode", str(info.st_mode & 0o7777).encode())
            _frame(hasher, label + ":target", os.readlink(path).encode("utf-8", "surrogatepass"))
            return True
        if not path.is_file():
            kind = b"directory" if path.is_dir() else b"other"
            _frame(hasher, label + ":type", kind)
            _frame(hasher, label + ":mode", str(info.st_mode & 0o7777).encode())
            return True
        _frame(hasher, label + ":type", b"file")
        _frame(hasher, label + ":mode", str(info.st_mode & 0o7777).encode())
        with path.open("rb") as stream:
            if not _frame_stream(hasher, label + ":bytes", stream, info.st_size, deadline):
                return False
        return path.stat().st_size == info.st_size
    except Exception:
        return False


def _untracked_paths(status: bytes) -> list[str] | None:
    try:
        records = status.split(b"\0")
        paths: list[str] = []
        index = 0
        while index < len(records):
            record = records[index]
            index += 1
            if not record:
                continue
            if len(record) < 4 or record[2:3] != b" ":
                return None
            if record[:2] == b"??":
                relative = record[3:].decode("utf-8", "surrogateescape")
                if _is_hook_cache_path(relative):
                    continue
                paths.append(relative)
            if record[:2].find(b"R") >= 0 or record[:2].find(b"C") >= 0:
                if index >= len(records) or not records[index]:
                    return None
                index += 1
        return paths
    except Exception:
        return None


def _is_hook_cache_path(relative: str) -> bool:
    """Identify only this hook's cache artifact and its temporary write files."""
    parts = PurePosixPath(relative.replace("\\", "/")).parts
    if len(parts) != 3 or parts[:2] != (".graph-powers", "cache"):
        return False
    name = parts[2]
    prefix = "." + CACHE_NAME + "."
    return name == CACHE_NAME or (
        name[:len(prefix)] == prefix and name[-4:] == ".tmp"
    )


def _without_cache_status(status: bytes) -> bytes:
    """Remove the hook's own untracked cache files from the worktree attestation."""
    records = status.split(b"\0")
    kept: list[bytes] = []
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        if record[:2] == b"??" and _is_hook_cache_path(
            record[3:].decode("utf-8", "surrogateescape")
        ):
            continue
        kept.append(record)
        if (
            (record[:2].find(b"R") >= 0 or record[:2].find(b"C") >= 0)
            and index < len(records)
            and records[index]
        ):
            kept.append(records[index])
            index += 1
    return b"\0".join(kept) + (b"\0" if kept else b"")


def _add_executable(hasher: hashlib._Hash, command: str,
                    deadline: float | None = None) -> bool:
    try:
        parts = shlex.split(command, posix=os.name != "nt")
        if not parts:
            return False
        first = parts[0].strip("\"'")
        executable = Path(first)
        if not executable.is_absolute():
            located = shutil.which(first)
            if not located:
                return False
            executable = Path(located)
        executable = executable.resolve(strict=True)
        info = executable.stat()
        if not executable.is_file():
            return False
        _frame(hasher, "executable:path", hashlib.sha256(_path_bytes(executable)).digest())
        _frame(hasher, "executable:mode", str(info.st_mode & 0o7777).encode())
        with executable.open("rb") as stream:
            if not _frame_stream(hasher, "executable:bytes", stream, info.st_size, deadline):
                return False
        return executable.stat().st_size == info.st_size
    except Exception:
        return False


def fingerprint_worktree(project: Path, gate_name: str, command: str,
                         *, deadline: float | None = None) -> str | None:
    """Return the bounded content identity used by the pre-commit success cache."""
    start = time.monotonic()
    limit = start + FINGERPRINT_BUDGET_S if deadline is None else min(
        deadline, start + FINGERPRINT_BUDGET_S
    )
    captures: list[_GitCapture] = []
    try:
        root = project.resolve(strict=True)
        config = gp.config_path(root)
        if config is None:
            return None
        config = config.resolve(strict=True)
        if not config.is_relative_to(root):
            return None
        config_info = config.stat()
        if config_info.st_size > GIT_METADATA_CAP:
            return None
        metadata_total = [0]
        for args in (
            ["status", "--porcelain=v1", "-z", "--untracked-files=all"],
            ["ls-files", "--stage", "-z"],
            ["diff", "--cached", "--binary", "--no-ext-diff"],
            ["diff", "--binary", "--no-ext-diff"],
            ["rev-parse", "HEAD"],
        ):
            capture = _git_to_temp(root, args, limit, metadata_total)
            if capture is None:
                return None
            captures.append(capture)
        status_capture = captures[0]
        status_capture.stream.seek(0)
        status = status_capture.stream.read()
        if len(status) != status_capture.size:
            return None
        stable_status = _without_cache_status(status or b"")
        paths = _untracked_paths(stable_status)
        if paths is None:
            return None
        digest = hashlib.sha256()
        _frame(digest, "version", FINGERPRINT_VERSION.encode())
        _frame(digest, "rootHash", hashlib.sha256(_path_bytes(root)).digest())
        _frame(digest, "configPathHash", hashlib.sha256(_path_bytes(config)).digest())
        with config.open("rb") as stream:
            if not _frame_stream(digest, "configBytes", stream, config_info.st_size, limit):
                return None
        if config.stat().st_size != config_info.st_size:
            return None
        status_capture.stream.seek(0)
        _frame(digest, "status", stable_status)
        for label, capture in zip(
            ("index", "stagedDiff", "unstagedDiff", "head"), captures[1:], strict=True
        ):
            capture.stream.seek(0)
            if not _frame_stream(digest, label, capture.stream, capture.size, limit):
                return None
        for relative in sorted(paths, key=lambda value: value.encode("utf-8", "surrogateescape")):
            _frame(digest, "untracked:path", relative.encode("utf-8", "surrogateescape"))
            if not _add_file_content(digest, "untracked:" + relative, root / relative, limit):
                return None
        _frame(digest, "scope", b"worktree")
        _frame(digest, "gate", gate_name.encode("utf-8"))
        _frame(digest, "command", command.encode("utf-8", "surrogatepass"))
        _frame(digest, "platform", platform.system().encode("utf-8"))
        _frame(digest, "architecture", platform.machine().encode("utf-8"))
        _frame(digest, "python", sys.version.encode("utf-8", "replace"))
        _frame(digest, "pathHash", hashlib.sha256(os.environ.get("PATH", "").encode(
            "utf-8", "surrogatepass"
        )).digest())
        if not _add_executable(digest, command, limit):
            return None
        if _remaining(limit) <= 0:
            return None
        return digest.hexdigest()
    except Exception:
        return None
    finally:
        for capture in captures:
            capture.cleanup()


def cache_path(project: Path) -> Path:
    return project / ".graph-powers" / "cache" / CACHE_NAME


def cache_lookup(project: Path, gate_name: str, fingerprint: str,
                 cache_seconds: int, *, now: float | None = None) -> bool:
    if cache_seconds <= 0:
        return False
    try:
        path = cache_path(project)
        if not path.is_file() or path.stat().st_size > CACHE_MAX_BYTES:
            return False
        value = __import__("json").loads(path.read_text(encoding="utf-8"))
        entries = value.get("entries") if isinstance(value, dict) else None
        if value.get("version") != CACHE_VERSION or not isinstance(entries, list):
            return False
        if len(entries) > CACHE_MAX_ENTRIES or any(
            not isinstance(entry, dict)
            or set(entry) != {"gate", "fingerprint", "completedAt"}
            or not isinstance(entry.get("gate"), str)
            or not isinstance(entry.get("fingerprint"), str)
            or len(entry["fingerprint"]) != 64
            or any(char not in "0123456789abcdef" for char in entry["fingerprint"])
            or isinstance(entry.get("completedAt"), bool)
            or not isinstance(entry.get("completedAt"), (int, float))
            for entry in entries
        ):
            return False
        current = time.time() if now is None else now
        return any(
            isinstance(entry, dict) and entry.get("gate") == gate_name
            and entry.get("fingerprint") == fingerprint
            and isinstance(entry.get("completedAt"), (int, float))
            and current - float(entry["completedAt"]) <= cache_seconds
            for entry in entries
        )
    except Exception:
        return False


def cache_store(project: Path, gate_name: str, fingerprint: str,
                *, now: float | None = None) -> bool:
    try:
        path = cache_path(project)
        value: dict[str, Any] = {"version": CACHE_VERSION, "entries": []}
        if path.is_file() and path.stat().st_size <= CACHE_MAX_BYTES:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if (isinstance(loaded, dict) and loaded.get("version") == CACHE_VERSION
                    and isinstance(loaded.get("entries"), list)):
                value = loaded
        entries = [entry for entry in value["entries"]
                   if isinstance(entry, dict) and set(entry) == {"gate", "fingerprint", "completedAt"}
                   and isinstance(entry.get("gate"), str)
                   and isinstance(entry.get("fingerprint"), str)
                   and len(entry["fingerprint"]) == 64
                   and all(char in "0123456789abcdef" for char in entry["fingerprint"])
                   and isinstance(entry.get("completedAt"), (int, float))
                   and not isinstance(entry.get("completedAt"), bool)
                   and entry.get("gate") != gate_name]
        entries.append({"gate": gate_name, "fingerprint": fingerprint,
                        "completedAt": time.time() if now is None else now})
        value["entries"] = entries[-CACHE_MAX_ENTRIES:]
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(
            prefix="." + CACHE_NAME + ".", suffix=".tmp", dir=str(path.parent)
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
                json.dump(value, stream, sort_keys=True, separators=(",", ":"))
                stream.flush()
                os.fsync(stream.fileno())
            if temporary.stat().st_size > CACHE_MAX_BYTES:
                temporary.unlink(missing_ok=True)
                return False
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
        return True
    except Exception:
        return False
