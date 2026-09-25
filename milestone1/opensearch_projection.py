"""OpenSearch document projection boundary; never a source of task or Git truth."""

from __future__ import annotations

import base64
import json
import ssl
import urllib.error
import urllib.request
from urllib.parse import urlsplit

from .git_projection import document_id, plan_reconciliation


DOCS_INDEX = "ai_factory_docs_v1"
DOCS_READ_ALIAS = "ai_factory_docs"
DOCS_WRITE_ALIAS = "ai_factory_docs_write"


class HttpClient:
    """Small authenticated transport; insecure TLS is limited to loopback tests."""

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        *,
        cafile: str | None = None,
        insecure_localhost: bool = False,
    ) -> None:
        parsed = urlsplit(base_url)
        loopback = parsed.hostname in ("127.0.0.1", "::1", "localhost")
        if parsed.username or parsed.password or parsed.path not in ("", "/") or parsed.query or parsed.fragment:
            raise ValueError("OpenSearch URL must contain only scheme and host")
        if parsed.scheme not in ("https", "http") or (parsed.scheme == "http" and not loopback):
            raise ValueError("OpenSearch credentials require HTTPS or loopback test HTTP")
        if parsed.scheme == "http" and not insecure_localhost:
            raise ValueError("loopback HTTP requires explicit test opt-in")
        if insecure_localhost and not loopback:
            raise ValueError("insecure transport is restricted to loopback")
        if not username or not password:
            raise ValueError("OpenSearch credentials are required")
        self.base_url = base_url.rstrip("/")
        self.authorization = "Basic " + base64.b64encode(f"{username}:{password}".encode()).decode()
        self.context = (
            ssl._create_unverified_context()
            if insecure_localhost and parsed.scheme == "https"
            else ssl.create_default_context(cafile=cafile)
        )

    def request(
        self,
        method: str,
        path: str,
        body=None,
        *,
        content_type: str = "application/json",
        expected: tuple[int, ...] = (200, 201),
    ) -> dict:
        if not path.startswith("/") or path.startswith("//"):
            raise ValueError("OpenSearch request path must be relative to the configured host")
        payload = None
        if body is not None:
            payload = body.encode("utf-8") if isinstance(body, str) else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path,
            data=payload,
            method=method,
            headers={"Authorization": self.authorization, "Content-Type": content_type},
        )
        try:
            with urllib.request.urlopen(request, context=self.context, timeout=20) as response:
                status = response.status
                raw = response.read()
        except urllib.error.HTTPError as error:
            status = error.code
            raw = error.read()
        if status not in expected:
            raise RuntimeError(f"OpenSearch {method} {path} returned HTTP {status}")
        return json.loads(raw) if raw else {}


def docs_index_definition() -> dict:
    """Versioned mapping with stable read/write aliases and filterable provenance."""
    keywords = (
        "id", "type", "project_id", "repository_id", "path", "scope", "status",
        "source_system", "source_id", "source_uri", "source_version",
        "source_revision", "authority", "content_sha256",
    )
    properties = {field: {"type": "keyword"} for field in keywords}
    properties.update(
        {
            "schema_version": {"type": "integer"},
            "canonical": {"type": "boolean"},
            "observed_at": {"type": "date"},
            "title": {"type": "text"},
            "content": {"type": "text"},
        }
    )
    return {
        "mappings": {"dynamic": "strict", "properties": properties},
        "aliases": {DOCS_READ_ALIAS: {}, DOCS_WRITE_ALIAS: {"is_write_index": True}},
    }


def install_docs_index(admin) -> None:
    """Create the versioned index once, then verify its contract on every run."""
    definition = docs_index_definition()
    result = admin.request("PUT", f"/{DOCS_INDEX}", definition, expected=(200, 400))
    error = result.get("error")
    if error and error.get("type") != "resource_already_exists_exception":
        raise RuntimeError(f"OpenSearch rejected docs index creation: {error.get('type')}")
    mapping = admin.request("GET", f"/{DOCS_INDEX}/_mapping")
    aliases = admin.request("GET", f"/{DOCS_INDEX}/_alias")
    try:
        actual = mapping[DOCS_INDEX]["mappings"]
        actual_aliases = aliases[DOCS_INDEX]["aliases"]
    except KeyError as error:
        raise RuntimeError("OpenSearch docs index disappeared during install") from error
    if (
        actual.get("dynamic") != definition["mappings"]["dynamic"]
        or actual.get("properties") != definition["mappings"]["properties"]
        or actual_aliases != definition["aliases"]
    ):
        raise RuntimeError("incompatible existing OpenSearch docs index or aliases")
    for alias in (DOCS_READ_ALIAS, DOCS_WRITE_ALIAS):
        targets = admin.request("GET", f"/_alias/{alias}")
        if set(targets) != {DOCS_INDEX}:
            raise RuntimeError(f"OpenSearch {alias} points at another physical index")


def reconcile_documents(
    reader,
    writer,
    desired: list[dict],
    project_id: str,
    repository_id: str,
    revision: str,
) -> int:
    """Reconcile one repository snapshot using separate read and write clients.

    A failed bulk raises; a later invocation retries from Git and OpenSearch.
    Neither the caller nor this function persists a second cursor or task state.
    """
    if not project_id or not repository_id or not revision:
        raise ValueError("project, repository and revision are required")
    for document in desired:
        path = document.get("path")
        if (
            document.get("project_id") != project_id
            or document.get("repository_id") != repository_id
            or document.get("source_system") != "git"
            or not isinstance(path, str)
            or document.get("source_id") != f"{repository_id}:{path}"
            or document.get("id") != document_id(project_id, repository_id, path)
        ):
            raise ValueError("Git projection document identity escapes its repository scope")

    existing: list[dict] = []
    cursor = None
    while True:
        query: dict = {
            "size": 500,
            "sort": [{"id": "asc"}],
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"project_id": project_id}},
                        {"term": {"repository_id": repository_id}},
                        {"term": {"source_system": "git"}},
                    ]
                }
            },
        }
        if cursor is not None:
            query["search_after"] = cursor
        response = reader.request("POST", f"/{DOCS_READ_ALIAS}/_search", query)
        hits = response.get("hits", {}).get("hits")
        if not isinstance(hits, list):
            raise RuntimeError("malformed OpenSearch search response")
        existing.extend(hit["_source"] for hit in hits)
        if len(hits) < 500:
            break
        cursor = hits[-1]["sort"]

    actions = plan_reconciliation(desired, existing, revision=revision)
    if not actions:
        return 0
    lines: list[str] = []
    for action in actions:
        document = action["document"]
        lines.append(json.dumps({"index": {"_index": DOCS_WRITE_ALIAS, "_id": document["id"]}}))
        lines.append(json.dumps(document, ensure_ascii=False))
    result = writer.request(
        "POST", "/_bulk?refresh=wait_for", "\n".join(lines) + "\n",
        content_type="application/x-ndjson",
    )
    if result.get("errors"):
        failures = [
            item.get("index", {}).get("_id", "unknown")
            for item in result.get("items", [])
            if item.get("index", {}).get("status", 500) >= 300
        ]
        raise RuntimeError(f"OpenSearch document projection failed for: {', '.join(failures) or 'unknown items'}")
    return len(actions)
