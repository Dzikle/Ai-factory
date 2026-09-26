"""One-shot projection of committed project documents into an existing index.

The project overlay and documents are read at the same Git commit. OpenSearch
remains a rebuildable projection; this command never creates indexes or roles.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys

import yaml

from .git_projection import collect_snapshot
from .opensearch_projection import HttpClient, reconcile_documents


def _committed_overlay(root: Path, overlay_path: str) -> tuple[dict, str]:
    path = PurePosixPath(overlay_path)
    if (
        not overlay_path
        or path.is_absolute()
        or "\\" in overlay_path
        or ":" in overlay_path
        or any(part in ("", ".", "..") for part in overlay_path.split("/"))
        or path.suffix not in (".yaml", ".yml")
    ):
        raise ValueError("overlay must be a relative committed YAML path")
    revision = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD^{commit}"],
        cwd=root, check=True, capture_output=True, text=True, timeout=30,
    ).stdout.strip()
    raw = subprocess.run(
        ["git", "show", f"{revision}:{overlay_path}"],
        cwd=root, check=True, capture_output=True, text=True, timeout=30,
    ).stdout
    overlay = yaml.safe_load(raw)
    if not isinstance(overlay, dict) or overlay.get("schema_version") != 1:
        raise ValueError("invalid project overlay schema version")
    if not isinstance(overlay.get("project_id"), str) or not overlay["project_id"]:
        raise ValueError("project overlay requires project_id")
    if not isinstance(overlay.get("repositories"), list):
        raise ValueError("project overlay requires repositories")
    return overlay, revision


def project_once(root: Path, overlay_path: str, repository_id: str, reader, writer) -> dict:
    """Reconcile one repository snapshot; return an evidence-friendly summary."""
    if not repository_id:
        raise ValueError("repository id is required")
    overlay, revision = _committed_overlay(root, overlay_path)
    repositories = [
        item for item in overlay["repositories"]
        if isinstance(item, dict) and item.get("id") == repository_id
    ]
    if len(repositories) != 1:
        raise ValueError("repository must occur exactly once in the committed overlay")
    repository = repositories[0]
    if (
        not isinstance(repository.get("remote"), str)
        or not repository["remote"]
        or not isinstance(repository.get("canonical_paths"), list)
        or not repository["canonical_paths"]
        or not all(isinstance(path, str) for path in repository["canonical_paths"])
    ):
        raise ValueError("repository requires remote and canonical_paths")
    documents = collect_snapshot(
        root,
        project_id=overlay["project_id"],
        repository_id=repository_id,
        remote=repository["remote"],
        canonical_paths=repository["canonical_paths"],
        revision=revision,
    )
    document_paths = {document["path"] for document in documents}
    missing_paths = [
        canonical_path
        for canonical_path in repository["canonical_paths"]
        if not any(
            document_path == canonical_path.rstrip("/")
            or document_path.startswith(canonical_path.rstrip("/") + "/")
            for document_path in document_paths
        )
    ]
    if missing_paths:
        raise ValueError(
            "canonical paths contain no eligible committed document: "
            + ", ".join(repr(path) for path in missing_paths)
        )
    writes = reconcile_documents(
        reader, writer, documents, overlay["project_id"], repository_id, revision
    )
    return {
        "project_id": overlay["project_id"],
        "repository_id": repository_id,
        "revision": revision,
        "documents": len(documents),
        "writes": writes,
    }


def run(argv: list[str] | None = None, environ: dict[str, str] | None = None) -> dict:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--overlay", required=True, help="committed path relative to repo root")
    parser.add_argument("--repository", required=True, help="repository id in the overlay")
    parser.add_argument("--ca-file")
    parser.add_argument("--insecure-localhost", action="store_true", help="local test cluster only")
    args = parser.parse_args(argv)
    env = os.environ if environ is None else environ
    required = (
        "AIF_DOCS_URL", "AIF_DOCS_READER_USER", "AIF_DOCS_READER_PASSWORD",
        "AIF_DOCS_WRITER_USER", "AIF_DOCS_WRITER_PASSWORD",
    )
    if any(not env.get(name) for name in required):
        raise ValueError("separate OpenSearch reader/writer credentials are required")
    reader_user = env["AIF_DOCS_READER_USER"]
    writer_user = env["AIF_DOCS_WRITER_USER"]
    if reader_user == writer_user or any(user.lower() == "admin" for user in (reader_user, writer_user)):
        raise ValueError("reader and writer must be distinct non-admin principals")
    options = {"cafile": args.ca_file, "insecure_localhost": args.insecure_localhost}
    reader = HttpClient(env["AIF_DOCS_URL"], reader_user, env["AIF_DOCS_READER_PASSWORD"], **options)
    writer = HttpClient(env["AIF_DOCS_URL"], writer_user, env["AIF_DOCS_WRITER_PASSWORD"], **options)
    return project_once(args.repo_root, args.overlay, args.repository, reader, writer)


def main() -> int:
    try:
        print(json.dumps(run()))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError, yaml.YAMLError) as error:
        print(f"Git document projection failed: {type(error).__name__}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
