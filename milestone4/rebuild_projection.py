"""Supervised loss/rebuild drill for the existing local docs projection.

Committed Git, complete scoped MemPalace drawers and selected native Paperclip
scorecards supply rebuilt data; no projection is used to reconstruct a source.
The fixed disposable index is replaced; roles, aliases and authority stay put.
Administrative credentials belong to this operator, never to agents/projectors.
"""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess

from milestone1.git_projection import collect_snapshot
from milestone1.opensearch_projection import DOCS_INDEX, HttpClient, install_docs_index
from milestone1.project_git_docs import _committed_overlay
from milestone3.cli import connect_memory
from milestone3.memory import ROOM, digest, encoded, projection_document
from .restore_drill import assert_quiescent
from .retrieval_eval import evaluate
from .project_telemetry import collect_documents
from milestone0.scripts.paperclip_admission import Client
from milestone2.task import read_object


def memory_snapshot(store, project_id, *, maximum=200):
    """Enumerate the primary store, not its possibly stale search projection."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", project_id):
        raise ValueError("Invalid memory project scope")
    documents, seen, total = [], set(), None
    offset = 0
    while True:
        response = store.client.send("tools/call", {"name": "mempalace_list_drawers", "arguments": {
            "wing": project_id, "room": ROOM, "limit": 100, "offset": offset,
        }})
        result = response.get("result") if isinstance(response, dict) else None
        content = result.get("content") if isinstance(result, dict) else None
        if (not isinstance(content, list) or len(content) != 1 or result.get("isError")
                or not isinstance(content[0], dict) or content[0].get("type") != "text"
                or not isinstance(content[0].get("text"), str) or len(content[0]["text"]) > 128_000):
            raise ValueError("Malformed memory enumeration")
        page = json.loads(content[0]["text"])
        if (not isinstance(page, dict) or type(page.get("total")) is not int
                or not 0 <= page["total"] <= maximum or page.get("offset") != offset
                or not isinstance(page.get("drawers"), list) or len(page["drawers"]) > 100
                or page.get("count") != len(page["drawers"])
                or (total is not None and page["total"] != total)):
            raise ValueError("Unbounded or changing memory enumeration")
        total = page["total"]
        for drawer in page["drawers"]:
            drawer_id = drawer.get("drawer_id") if isinstance(drawer, dict) else None
            if (not isinstance(drawer_id, str) or drawer_id in seen
                    or drawer.get("wing") != project_id or drawer.get("room") != ROOM):
                raise ValueError("Duplicate or cross-scope memory drawer")
            seen.add(drawer_id)
            envelope = store.get(drawer_id)
            if envelope["record"]["project_id"] != project_id:
                raise ValueError("Memory primary scope mismatch")
            documents.append(projection_document(drawer_id, envelope))
        offset += len(page["drawers"])
        if offset == total:
            break
        if offset > total or not page["drawers"]:
            raise ValueError("Incomplete memory enumeration")
    identities = [doc["id"] for doc in documents]
    if len(set(identities)) != len(identities):
        raise ValueError("Duplicate primary memory identities")
    return sorted(documents, key=lambda doc: doc["id"])


def index_snapshot(client, path=f"/{DOCS_INDEX}"):
    result = client.request("POST", path + "/_search", {
        "size": 1000, "track_total_hits": True, "query": {"match_all": {}},
    })
    hits = result.get("hits") if isinstance(result, dict) else None
    total = hits.get("total") if isinstance(hits, dict) else None
    rows = hits.get("hits") if isinstance(hits, dict) else None
    if (not isinstance(total, dict) or total.get("relation") != "eq"
            or not isinstance(rows, list) or total.get("value") != len(rows) or len(rows) > 1000):
        raise ValueError("Projection inventory exceeds the supervised drill bound")
    docs = []
    for row in rows:
        doc = row.get("_source") if isinstance(row, dict) else None
        if not isinstance(doc, dict) or not isinstance(doc.get("id"), str) or row.get("_id") != doc["id"]:
            raise ValueError("Malformed projection inventory")
        docs.append(doc)
    if len({doc["id"] for doc in docs}) != len(docs):
        raise ValueError("Duplicate projection identities")
    return sorted(docs, key=lambda doc: doc["id"])


def replace(admin, reader, desired, *, project_id, repository_id, verify_sources):
    """One destructive operator action, retryable from sources without a cursor."""
    if not desired or len(desired) > 1000 or len({doc["id"] for doc in desired}) != len(desired):
        raise ValueError("Invalid or oversized rebuild inventory")
    allowed_sources = {doc.get("source_system") for doc in desired}
    if not allowed_sources <= {"git", "mempalace", "paperclip"}:
        raise ValueError("Unknown primary source")
    for doc in desired:
        if (doc.get("project_id") != project_id or doc.get("repository_id") != repository_id
                or doc.get("source_system") not in allowed_sources):
            raise ValueError("Rebuild sources escape scope")
    expected = sorted(desired, key=lambda doc: doc["id"])
    existing = index_snapshot(admin)
    for doc in existing:
        if (doc.get("project_id") != project_id or doc.get("repository_id") != repository_id
                or doc.get("source_system") not in allowed_sources):
            raise ValueError("Another source/project exists; cannot replace this index")
    # Also verifies exact mapping and single alias targets before removing anything.
    install_docs_index(admin)
    if verify_sources() is not True:
        raise ValueError("Primary sources changed before rebuild")
    admin.request("DELETE", f"/{DOCS_INDEX}")
    lines = []
    for doc in expected:
        lines.extend((json.dumps({"index": {"_index": DOCS_INDEX, "_id": doc["id"]}}),
                      json.dumps(doc, ensure_ascii=False)))

    def restore():
        install_docs_index(admin)
        result = admin.request("POST", "/_bulk?refresh=wait_for", "\n".join(lines) + "\n",
                               content_type="application/x-ndjson")
        items = result.get("items")
        if (result.get("errors") or not isinstance(items, list) or len(items) != len(expected)
                or any(item.get("index", {}).get("status") not in (200, 201) for item in items)):
            raise RuntimeError("Rebuild bulk failed")
        if index_snapshot(reader, "/ai_factory_docs") != expected or verify_sources() is not True:
            raise RuntimeError("Rebuilt index differs from primary sources")

    try:
        loss = reader.request("POST", "/ai_factory_docs/_search",
                              {"size": 0, "query": {"match_all": {}}}, expected=(404,))
        if loss.get("error", {}).get("type") != "index_not_found_exception":
            raise RuntimeError("Missing-index loss was not proven")
        restore()
    except (RuntimeError, OSError, ValueError, KeyError, TypeError, AttributeError):
        # One idempotent recovery attempt only; never delete again on retry.
        try:
            restore()
        except (RuntimeError, OSError, ValueError, KeyError, TypeError, AttributeError):
            raise RuntimeError("Projection unavailable/incomplete: restore from primaries after operator repair") from None
        raise RuntimeError("Drill failed but projection recovered; inspect failure before retrying") from None
    return {"documentsBefore": len(existing), "documentsAfter": len(expected),
            "sourceDigest": digest(encoded(expected)), "dependencyLossObserved": True,
            "exactPrimaryReadback": True, "index": DOCS_INDEX,
            "sources": {name: sum(doc["source_system"] == name for doc in expected)
                        for name in sorted(allowed_sources)}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--overlay", default="autonomy/projects/examples/ai-factory.v1.yaml")
    parser.add_argument("--repository", default="ai-factory")
    parser.add_argument("--expect-revision", required=True)
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--telemetry-roster", type=Path)
    parser.add_argument("--paperclip-state", type=Path, help="private board state for native telemetry sources")
    parser.add_argument("--confirm-rebuild-ai-factory-docs-v1", action="store_true")
    args = parser.parse_args(argv)
    store = None
    try:
        if not args.confirm_rebuild_ai_factory_docs_v1:
            raise ValueError("Explicit fixed-index loss/rebuild confirmation is required")
        assert_quiescent()
        env = os.environ
        reader = HttpClient(env["AIF_DOCS_URL"], env["AIF_DOCS_READER_USER"],
                            env["AIF_DOCS_READER_PASSWORD"], insecure_localhost=True)
        if env["AIF_DOCS_READER_USER"].lower() == "admin":
            raise ValueError("An independent non-admin reader is required")
        admin = HttpClient(env["AIF_DOCS_URL"], env["AIF_DOCS_OPERATOR_USER"],
                           env["AIF_DOCS_OPERATOR_PASSWORD"], insecure_localhost=True)
        overlay, revision = _committed_overlay(args.repo_root, args.overlay)
        if revision != args.expect_revision:
            raise ValueError("Git revision does not match the expected commit")
        repositories = [repo for repo in overlay["repositories"] if repo["id"] == args.repository]
        if len(repositories) != 1:
            raise ValueError("Repository must occur exactly once")
        repo = repositories[0]
        docs = collect_snapshot(args.repo_root, project_id=overlay["project_id"], repository_id=args.repository,
                                remote=repo["remote"], canonical_paths=repo["canonical_paths"], revision=revision)
        if not docs:
            raise ValueError("Empty Git snapshot")
        store = connect_memory()
        memories = memory_snapshot(store, overlay["project_id"])
        native_docs, native_client, native_state, roster = [], None, None, None
        if args.telemetry_roster:
            if not args.paperclip_state:
                raise ValueError("Native telemetry rebuild requires private board state")
            roster = read_object(args.telemetry_roster)
            if roster["projectId"] != overlay["project_id"] or roster["repositoryId"] != args.repository:
                raise ValueError("Telemetry roster escapes the rebuilt project")
            native_state = read_object(args.paperclip_state)
            native_client = Client(native_state["baseUrl"], native_state["boardApiKey"])
            native_docs = collect_documents(native_client, native_state, roster)

        def unchanged():
            assert_quiescent()
            head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=args.repo_root,
                                           text=True, timeout=10).strip()
            return (head == revision and memory_snapshot(store, overlay["project_id"]) == memories
                    and (native_client is None or (read_object(args.telemetry_roster) == roster
                         and collect_documents(native_client, native_state, roster) == native_docs)))

        receipt = replace(admin, reader, docs + memories + native_docs, project_id=overlay["project_id"],
                          repository_id=args.repository, verify_sources=unchanged)
        receipt["revision"] = revision
        receipt["retrieval"] = evaluate(reader, json.loads(args.suite.read_text(encoding="utf-8")),
                                         expected_revision=revision)
        if receipt["retrieval"]["passesThresholds"] is not True:
            raise RuntimeError("Rebuilt retrieval failed promotion thresholds")
        print(json.dumps(receipt, sort_keys=True))
        return 0
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, AttributeError, subprocess.SubprocessError):
        print(json.dumps({"status": "failed", "message": "Inspect sources and operator configuration privately; do not use the old projection as authority."}))
        return 1
    finally:
        if store:
            store.client.close()


if __name__ == "__main__":
    raise SystemExit(main())
