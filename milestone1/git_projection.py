"""Deterministic, Git-backed document snapshots for the knowledge projection.

This module does not own Git data or OpenSearch state. It reads committed blobs
and produces replacement documents and retraction tombstones for a projector.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path, PurePosixPath
import re
import subprocess


DOCUMENT_SUFFIXES = {".md", ".yaml", ".yml", ".json"}


def document_id(project_id: str, repository_id: str, path: str) -> str:
    identity = f"{project_id}\x00{repository_id}\x00{path}".encode("utf-8")
    return hashlib.sha256(identity).hexdigest()


def _git(root: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, timeout=30
    ).stdout


def _valid_path(path: str) -> str:
    candidate = PurePosixPath(path)
    if (
        not path
        or path.startswith(("/", "-"))
        or "\\" in path
        or ":" in path
        or any(part in (".", "..") for part in path.split("/"))
        or any(character in path for character in "*?[]")
        or candidate.is_absolute()
    ):
        raise ValueError(f"invalid canonical Git path: {path!r}")
    return path


def _title(path: str, content: str) -> str:
    if path.endswith(".md"):
        heading = re.search(r"^#\s+(.+)$", content, flags=re.MULTILINE)
        if heading:
            return heading.group(1).strip()
    return PurePosixPath(path).name


def _status(content: str) -> str:
    match = re.search(r"^\*\*Status:\*\*\s*(.+)$", content[:4096], flags=re.MULTILINE | re.IGNORECASE)
    if match and "superseded" in match.group(1).lower():
        return "superseded"
    if match and "deprecated" in match.group(1).lower():
        return "deprecated"
    return "canonical"


def collect_snapshot(
    root: Path,
    *,
    project_id: str,
    repository_id: str,
    remote: str,
    canonical_paths: list[str],
    revision: str = "HEAD",
) -> list[dict]:
    """Read only committed, allowlisted text blobs at one resolved Git commit."""
    if not project_id or not repository_id or not remote:
        raise ValueError("project, repository and remote are required")
    if not revision or revision.startswith("-"):
        raise ValueError("invalid Git revision")
    paths = [_valid_path(path) for path in canonical_paths]
    if not paths:
        raise ValueError("at least one canonical path is required")
    commit = _git(root, "rev-parse", "--verify", f"{revision}^{{commit}}").decode().strip()
    committed_at = _git(root, "show", "-s", "--format=%cI", commit).decode().strip()
    tree = _git(root, "ls-tree", "-r", "-z", commit, "--", *paths)
    result: list[dict] = []
    for entry in tree.split(b"\x00"):
        if not entry:
            continue
        metadata, name = entry.split(b"\t", 1)
        mode, kind, blob_id = metadata.decode("ascii").split(" ")
        path = name.decode("utf-8")
        if kind != "blob" or mode not in ("100644", "100755"):
            continue
        if PurePosixPath(path).suffix.lower() not in DOCUMENT_SUFFIXES:
            continue
        raw = _git(root, "show", f"{commit}:{path}")
        if b"\x00" in raw:
            raise ValueError(f"binary content in canonical document: {path}")
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(f"non-UTF-8 canonical document: {path}") from error
        result.append(
            {
                "id": document_id(project_id, repository_id, path),
                "type": "git_document",
                "project_id": project_id,
                "repository_id": repository_id,
                "path": path,
                "scope": "project",
                "title": _title(path, content),
                "content": content,
                "schema_version": 1,
                "source_system": "git",
                "source_id": f"{repository_id}:{path}",
                "source_uri": f"git+{remote}@{commit}#{path}",
                "source_version": blob_id,
                "source_revision": commit,
                "observed_at": committed_at,
                "authority": "canonical",
                "status": _status(content),
                "canonical": True,
                "content_sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
    return sorted(result, key=lambda document: document["id"])


def plan_reconciliation(
    desired: list[dict], existing: list[dict], *, revision: str | None = None
) -> list[dict]:
    """Return only changed upserts and tombstones for removed committed paths."""
    wanted = {document["id"]: document for document in desired}
    current = {document["id"]: document for document in existing}
    actions = [
        {"op": "index", "document": document}
        for doc_id, document in wanted.items()
        if current.get(doc_id) != document
    ]
    removed = current.keys() - wanted.keys()
    if removed and not revision:
        raise ValueError("a deletion revision is required for Git tombstones")
    for doc_id in removed:
        previous = current[doc_id]
        if previous.get("status") == "stale":
            continue
        tombstone = {
            **previous,
            "content": "",
            "content_sha256": hashlib.sha256(b"").hexdigest(),
            "source_revision": revision,
            "source_version": revision,
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "status": "stale",
            "canonical": False,
        }
        actions.append({"op": "index", "document": tombstone})
    return sorted(actions, key=lambda action: action["document"]["id"])
