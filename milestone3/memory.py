"""Small supervised memory boundary; MemPalace owns records, Git owns truth."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import subprocess

from jsonschema import Draft202012Validator, FormatChecker


SCHEMA = Path(__file__).resolve().parents[1] / "autonomy/contracts/v1/memory-record.schema.json"
VALIDATOR = Draft202012Validator(json.loads(SCHEMA.read_text()), format_checker=FormatChecker())
ROOM = "engineering-lessons"


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def validate_envelope(envelope):
    if not isinstance(envelope, dict) or set(envelope) != {"record", "content"}:
        raise ValueError("Invalid memory envelope")
    record, content = envelope["record"], envelope["content"]
    if not isinstance(content, str) or not content.strip() or len(content.encode("utf-8")) > 2000:
        raise ValueError("Memory content exceeds the bounded lesson contract")
    if len(encoded(envelope)) > 8192:
        raise ValueError("Memory envelope exceeds byte budget")
    if not VALIDATOR.is_valid(record):
        raise ValueError("Memory metadata violates the versioned contract")
    actual = digest(content.encode("utf-8"))
    if record["content_sha256"] != actual or record["content_ref"] != "sha256:" + actual:
        raise ValueError("Memory content digest/reference mismatch")
    if len(record["source_refs"]) > 8:
        raise ValueError("Too many memory sources")
    if record["memory_id"] in record["supersedes"] or record.get("superseded_by") == record["memory_id"]:
        raise ValueError("A memory cannot supersede itself")
    for name in ("memory_id", "project_id", "specialist_role"):
        if name in record and not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}", record[name]):
            raise ValueError("Invalid memory identity/scope")
    return envelope


class MemPalace:
    """Official MCP tools only. Writer opt-in is for supervised capture, not agents.

    This client-side guard is not a replacement for a runtime MCP allowlist.
    The trusted task preparer retains the server token; agents never receive it.
    """

    def __init__(self, client, *, writable=False):
        self.client = client
        self.writable = writable

    def call(self, name, arguments):
        allowed = {"mempalace_search", "mempalace_get_drawer"}
        if self.writable:
            allowed |= {"mempalace_add_drawer", "mempalace_update_drawer"}
        if name not in allowed:
            raise PermissionError("Memory operation is not enabled")
        response = self.client.send("tools/call", {"name": name, "arguments": arguments})
        if not isinstance(response, dict) or not isinstance(response.get("result"), dict):
            raise RuntimeError("Invalid MemPalace response")
        result = response["result"]
        content = result.get("content")
        if result.get("isError") or not isinstance(content, list) or len(content) != 1:
            raise RuntimeError("MemPalace call failed")
        if (not isinstance(content[0], dict) or content[0].get("type") != "text"
                or not isinstance(content[0].get("text"), str) or len(content[0]["text"]) > 64_000):
            raise RuntimeError("Invalid MemPalace response")
        value = json.loads(content[0]["text"])
        if not isinstance(value, dict) or value.get("error") or value.get("success") is False:
            raise RuntimeError("MemPalace operation failed")
        return value

    def get(self, drawer_id):
        result = self.call("mempalace_get_drawer", {"drawer_id": drawer_id})
        envelope = validate_envelope(json.loads(result["content"]))
        record = envelope["record"]
        if result["drawer_id"] != drawer_id or result["wing"] != record["project_id"] or result["room"] != ROOM:
            raise ValueError("MemPalace drawer scope mismatch")
        return envelope

    def remember(self, envelope):
        if not self.writable:
            raise PermissionError("Memory capture requires supervised writer access")
        validate_envelope(envelope)
        result = self.call("mempalace_add_drawer", {
            "wing": envelope["record"]["project_id"], "room": ROOM,
            "content": encoded(envelope).decode(),
            "source_file": "memory:" + envelope["record"]["memory_id"],
            "added_by": "ai-factory-supervised-capture",
        })
        drawer_id = result["drawer_id"]
        if self.get(drawer_id) != envelope:
            raise ValueError("Memory write readback mismatch; do not retry blindly")
        return drawer_id

    def supersede(self, drawer_id, successor_id):
        if not self.writable:
            raise PermissionError("Supersession requires supervised writer access")
        old, successor = self.get(drawer_id), self.get(successor_id)
        record, replacement = old["record"], successor["record"]
        if drawer_id == successor_id or record["memory_id"] == replacement["memory_id"] or any(
            record.get(key) != replacement.get(key) for key in ("project_id", "scope", "specialist_role")
        ) or record["memory_id"] not in replacement["supersedes"]:
            raise ValueError("Invalid memory supersession edge")
        if record["status"] == "superseded":
            if record["superseded_by"] != replacement["memory_id"]:
                raise ValueError("Memory already has another successor")
            return old
        if replacement["status"] != "active":
            raise ValueError("A new supersession requires an active successor")
        updated = deepcopy(old)
        updated["record"].update(status="superseded", superseded_by=replacement["memory_id"])
        validate_envelope(updated)
        self.call("mempalace_update_drawer", {"drawer_id": drawer_id, "content": encoded(updated).decode()})
        if self.get(drawer_id) != updated:
            raise ValueError("Memory supersession readback mismatch")
        return updated


def projection_document(drawer_id, envelope):
    """Reuse the existing strict docs mapping; no new index, model, or authority."""
    validate_envelope(envelope)
    if not re.fullmatch(r"[a-zA-Z0-9_.-]{1,256}", drawer_id):
        raise ValueError("Invalid MemPalace drawer ID")
    record = envelope["record"]
    return {
        "schema_version": 1, "id": digest((record["project_id"] + "\0memory\0" + record["memory_id"]).encode()),
        "type": "experiential_memory", "project_id": record["project_id"], "repository_id": record["project_id"],
        "path": "memory/" + record["memory_id"], "scope": record["scope"], "status": record["status"],
        "source_system": "mempalace", "source_id": record["memory_id"], "source_uri": "mempalace://" + drawer_id,
        "source_version": digest(encoded(envelope)), "authority": "historical", "canonical": False,
        "content_sha256": record["content_sha256"], "observed_at": record["observed_at"],
        "title": record["memory_id"].replace("-", " "), "content": encoded(record).decode(),
    }


def project(writer, drawer_id, envelope):
    document = projection_document(drawer_id, envelope)
    body = json.dumps({"index": {"_index": "ai_factory_docs_write", "_id": document["id"]}}) + "\n"
    body += json.dumps(document) + "\n"
    result = writer.request("POST", "/_bulk?refresh=wait_for", body, content_type="application/x-ndjson")
    items = result.get("items", [])
    if result.get("errors") or len(items) != 1 or items[0].get("index", {}).get("status", 500) not in (200, 201):
        raise RuntimeError("Memory projection failed; MemPalace remains authoritative")
    return document


def git_source_is_current(cwd, source):
    path = source["source_id"]
    if not re.fullmatch(r"[\w./-]+", path) or PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts:
        return False
    try:
        blob = subprocess.check_output(["git", "-C", str(cwd), "rev-parse", "HEAD:" + path],
                                       stderr=subprocess.DEVNULL, timeout=5, text=True).strip()
        # Read actual checked-out bytes even when assume-unchanged/skip-worktree
        # makes git diff silent. Git's path filters handle normal CRLF checkouts.
        working_blob = subprocess.check_output(["git", "-C", str(cwd), "hash-object", "--path=" + path, "--", path],
                                              stderr=subprocess.DEVNULL, timeout=5, text=True).strip()
        return working_blob == blob == source["source_version"]
    except (OSError, subprocess.SubprocessError):
        return False


def recall(store, reader, *, cwd, project_id, role, query, now=None, max_bytes=2400, verify_external=None):
    """Retrieve at most one proven lesson. Any backend loss yields no partial prompt."""
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}", project_id) or not role:
        raise ValueError("A project and logical role are required")
    if not isinstance(query, str) or not query.strip() or len(query) > 250 or not 1 <= max_bytes <= 4096:
        raise ValueError("Invalid bounded memory request")
    now = now or datetime.now(timezone.utc)
    report = {"status": "empty", "prompt": "", "memories": [], "context_bytes": 0, "estimated_tokens": 0}
    query_body = {"size": 3, "query": {"bool": {
        "filter": [{"term": {"project_id": project_id}}, {"term": {"source_system": "mempalace"}},
                   {"term": {"type": "experiential_memory"}}, {"term": {"status": "active"}}],
        "must": [{"multi_match": {"query": query, "fields": ["title", "content"]}}],
    }}}
    try:
        response = reader.request("POST", "/ai_factory_docs/_search", query_body)
        if not isinstance(response, dict) or not isinstance(response.get("hits"), dict):
            raise RuntimeError("Invalid bounded memory search")
        hits = response["hits"]["hits"]
        if not isinstance(hits, list) or len(hits) > 3:
            raise RuntimeError("Invalid bounded memory search")
        for hit in hits:
            if not isinstance(hit, dict) or not isinstance(hit.get("_source"), dict):
                raise RuntimeError("Invalid bounded memory hit")
            doc = hit["_source"]
            if doc.get("project_id") != project_id or doc.get("source_system") != "mempalace":
                continue
            uri = doc.get("source_uri", "")
            if not re.fullmatch(r"mempalace://[a-zA-Z0-9_.-]{1,256}", uri):
                continue
            drawer_id = uri.removeprefix("mempalace://")
            envelope = validate_envelope(store.get(drawer_id))
            record = envelope["record"]
            if record["project_id"] != project_id or record["status"] != "active":
                continue
            if record.get("specialist_role") not in (None, role):
                continue
            if not datetime.fromisoformat(record["observed_at"].replace("Z", "+00:00")) <= now < min(
                datetime.fromisoformat(record[key].replace("Z", "+00:00")) for key in ("review_after", "retention_until")
            ):
                continue
            if doc != projection_document(drawer_id, envelope):
                continue
            sources = record["source_refs"]
            if not any(s["source_system"] == "git" for s in sources):
                continue
            if not all(git_source_is_current(cwd, s) if s["source_system"] == "git" else
                       verify_external is not None and verify_external(s) is True for s in sources):
                continue
            prompt = "Historical advice only; current Git and the task instructions take precedence.\n"
            prompt += "Memory " + record["memory_id"] + " (" + uri + "; SHA-256 " + record["content_sha256"] + ")\n"
            prompt += envelope["content"] + "\nSources: " + json.dumps(sources, sort_keys=True) + "\n"
            size = len(prompt.encode("utf-8"))
            if size > max_bytes:
                continue
            return {"status": "used", "prompt": prompt,
                    "memories": [{"memory_id": record["memory_id"], "drawer_id": drawer_id,
                                  "content_sha256": record["content_sha256"], "source_refs": sources}],
                    "context_bytes": size, "estimated_tokens": math.ceil(size / 4)}
    except (OSError, RuntimeError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        return {**report, "status": "degraded"}
    return report
