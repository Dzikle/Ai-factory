#!/usr/bin/env python3
"""Provision and verify the disposable Milestone 0 OpenSearch security fixture."""

from __future__ import annotations

import argparse
import base64
import json
import os
import ssl
import urllib.error
import urllib.request


DOCS = [
    {
        "id": "adr-current",
        "project_id": "ai-factory",
        "status": "current",
        "kind": "architecture_decision",
        "title": "OpenSearch is a rebuildable projection",
        "body": "Git and operational systems remain canonical.",
        "source_revision": "71b5a5d",
    },
    {
        "id": "adr-superseded",
        "project_id": "ai-factory",
        "status": "superseded",
        "kind": "architecture_decision",
        "title": "Earlier task-state proposal",
        "body": "This decision was superseded by Paperclip admission work.",
        "source_revision": "pre-spike",
    },
    {
        "id": "other-project",
        "project_id": "fixture-other",
        "status": "current",
        "kind": "run_summary",
        "title": "Unrelated fixture",
        "body": "Project filters must exclude this document.",
        "source_revision": "fixture",
    },
]

# More than the configured MCP search result cap so the live probe can prove
# bounded retrieval rather than merely inspect configuration.
DOCS.extend(
    {
        "id": f"run-{number:02d}",
        "project_id": "ai-factory",
        "status": "current",
        "kind": "run_summary",
        "title": f"Admission run {number:02d}",
        "body": "Deterministic bounded retrieval fixture.",
        "source_revision": "71b5a5d",
    }
    for number in range(1, 10)
)


class Client:
    def __init__(self, base_url: str, username: str, password: str) -> None:
        self.base_url = base_url.rstrip("/")
        token = base64.b64encode(f"{username}:{password}".encode()).decode()
        self.authorization = f"Basic {token}"
        self.context = ssl._create_unverified_context()

    def request(
        self,
        method: str,
        path: str,
        body: object | str | None = None,
        *,
        content_type: str = "application/json",
        expected: tuple[int, ...] = (200,),
    ) -> tuple[int, object]:
        data = None
        if body is not None:
            data = body.encode() if isinstance(body, str) else json.dumps(body).encode()
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            method=method,
            headers={"Authorization": self.authorization, "Content-Type": content_type},
        )
        try:
            with urllib.request.urlopen(request, context=self.context, timeout=20) as response:
                raw = response.read().decode(errors="replace")
                status = response.status
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode(errors="replace")
            status = exc.code
        try:
            parsed: object = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = raw
        if status not in expected:
            raise RuntimeError(f"{method} {path}: expected {expected}, got {status}: {str(parsed)[:800]}")
        return status, parsed


def bulk_body(index: str) -> str:
    lines: list[str] = []
    for doc in DOCS:
        lines.append(json.dumps({"index": {"_index": index, "_id": doc["id"]}}))
        lines.append(json.dumps(doc))
    return "\n".join(lines) + "\n"


def create_index(client: Client, index: str) -> None:
    client.request(
        "PUT",
        f"/{index}",
        {
            "mappings": {
                "properties": {
                    "project_id": {"type": "keyword"},
                    "status": {"type": "keyword"},
                    "kind": {"type": "keyword"},
                    "title": {"type": "text"},
                    "body": {"type": "text"},
                    "source_revision": {"type": "keyword"},
                }
            }
        },
        expected=(200, 400),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="https://127.0.0.1:19200")
    parser.add_argument("--password-env", default="AIF_M0_OPENSEARCH_ADMIN_PASSWORD")
    args = parser.parse_args()
    password = os.environ.get(args.password_env)
    if not password:
        raise RuntimeError(f"required environment variable is unset: {args.password_env}")

    admin = Client(args.url, "admin", password)
    agent = Client(args.url, "aif_agent", password)
    projector = Client(args.url, "aif_projector", password)
    report: dict[str, object] = {}

    _, root = admin.request("GET", "/")
    report["version"] = root.get("version", {}).get("number")

    admin.request(
        "PUT",
        "/_plugins/_security/api/roles/aif_agent_reader",
        {
            "cluster_permissions": ["cluster_monitor", "cluster_composite_ops_ro"],
            "index_permissions": [
                {
                    "index_patterns": ["aif_docs_v*", "aif_docs_current"],
                    "allowed_actions": [
                        "read",
                        "indices:admin/mappings/get",
                        "indices:admin/aliases/get",
                    ],
                }
            ],
            "tenant_permissions": [],
        },
        expected=(200, 201),
    )
    admin.request(
        "PUT",
        "/_plugins/_security/api/roles/aif_projector_writer",
        {
            "cluster_permissions": ["indices:data/write/bulk"],
            "index_permissions": [
                {"index_patterns": ["aif_docs_v*"], "allowed_actions": ["write"]}
            ],
            "tenant_permissions": [],
        },
        expected=(200, 201),
    )
    for username, role in (
        ("aif_agent", "aif_agent_reader"),
        ("aif_projector", "aif_projector_writer"),
    ):
        admin.request(
            "PUT",
            f"/_plugins/_security/api/internalusers/{username}",
            {"password": password, "backend_roles": [], "opendistro_security_roles": [role]},
            expected=(200, 201),
        )

    for index in ("aif_docs_v1", "aif_docs_v2"):
        admin.request("DELETE", f"/{index}", expected=(200, 404))
    create_index(admin, "aif_docs_v1")
    _, bulk = projector.request(
        "POST", "/_bulk?refresh=true", bulk_body("aif_docs_v1"), content_type="application/x-ndjson"
    )
    if bulk.get("errors"):
        raise RuntimeError(f"projector bulk write failed: {bulk}")
    admin.request(
        "POST",
        "/_aliases",
        {"actions": [{"add": {"index": "aif_docs_v1", "alias": "aif_docs_current"}}]},
    )

    query = {
        "size": 5,
        "query": {
            "bool": {
                "must": [{"match": {"body": "canonical"}}],
                "filter": [
                    {"term": {"project_id": "ai-factory"}},
                    {"term": {"status": "current"}},
                ],
            }
        },
    }
    _, search = agent.request("POST", "/aif_docs_current/_search", query)
    report["filtered_search_hits"] = search["hits"]["total"]["value"]

    msearch_lines = [
        json.dumps({"index": "aif_docs_current"}),
        json.dumps({"size": 1, "query": {"term": {"status": "current"}}}),
        json.dumps({"index": "aif_docs_current"}),
        json.dumps({"size": 1, "query": {"term": {"status": "superseded"}}}),
    ]
    _, msearch = agent.request(
        "POST", "/_msearch", "\n".join(msearch_lines) + "\n", content_type="application/x-ndjson"
    )
    report["msearch_hit_counts"] = [
        response["hits"]["total"]["value"] for response in msearch["responses"]
    ]

    report["agent_write_status"] = agent.request(
        "PUT", "/aif_docs_v1/_doc/forbidden", {"title": "must fail"}, expected=(403,)
    )[0]
    report["projector_read_status"] = projector.request(
        "GET", "/aif_docs_v1/_search", expected=(403,)
    )[0]

    create_index(admin, "aif_docs_v2")
    _, rebuilt_bulk = projector.request(
        "POST", "/_bulk?refresh=true", bulk_body("aif_docs_v2"), content_type="application/x-ndjson"
    )
    if rebuilt_bulk.get("errors"):
        raise RuntimeError(f"rebuild bulk write failed: {rebuilt_bulk}")
    admin.request(
        "POST",
        "/_aliases",
        {
            "actions": [
                {"remove": {"index": "aif_docs_v1", "alias": "aif_docs_current"}},
                {"add": {"index": "aif_docs_v2", "alias": "aif_docs_current"}},
            ]
        },
    )
    admin.request("DELETE", "/aif_docs_v1")
    _, count = agent.request("GET", "/aif_docs_current/_count")
    report["rebuild_count"] = count["count"]
    report["alias_target"] = "aif_docs_v2"
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
