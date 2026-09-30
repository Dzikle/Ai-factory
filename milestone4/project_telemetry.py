"""One-shot native scorecard projection; Paperclip remains the only ledger."""

import argparse
import json
import os
from pathlib import Path
import re

from milestone0.scripts.paperclip_admission import Client
from milestone1.opensearch_projection import DOCS_READ_ALIAS, DOCS_WRITE_ALIAS, HttpClient
from milestone2.scorecard import collect
from milestone2.task import read_object, uuid
from milestone3.memory import digest, encoded


def collect_documents(client, state, roster):
    if (not isinstance(roster, dict) or roster.get("schemaVersion") != 1
            or not isinstance(roster.get("issues"), list) or not 1 <= len(roster["issues"]) <= 32
            or len(set(roster["issues"])) != len(roster["issues"])
            or not all(isinstance(item, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9]*-\d+", item)
                       for item in roster["issues"])
            or not all(isinstance(roster.get(key), str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", roster[key])
                       for key in ("projectId", "repositoryId"))):
        raise ValueError("Invalid bounded telemetry roster")
    native_project = uuid(roster.get("paperclipProjectId"), "paperclipProjectId")
    company = uuid(state.get("companyId"), "companyId")
    docs = []
    for identifier in roster["issues"]:
        _, issue = client.request("GET", "/api/issues/" + identifier)
        if (not isinstance(issue, dict) or issue.get("companyId") != company
                or issue.get("projectId") != native_project or issue.get("identifier") != identifier):
            raise ValueError("Native telemetry issue escapes the configured project")
        report = collect(client, issue, company)
        report.pop("observedAt", None)  # observation clock must not manufacture replay changes
        payload = encoded(report)
        if len(payload) > 32_000:
            raise ValueError("Native telemetry snapshot exceeds its byte bound")
        issue_id = uuid(issue["id"], "issueId")
        checksum = digest(payload)
        docs.append({"schema_version": 1, "id": digest((company + "\0telemetry\0" + issue_id).encode()),
                     "type": "paperclip_task_scorecard", "project_id": roster["projectId"],
                     "repository_id": roster["repositoryId"], "path": "telemetry/" + identifier,
                     "scope": "project", "status": "observed", "canonical": False,
                     "source_system": "paperclip", "source_id": issue_id,
                     "source_uri": "paperclip://" + company + "/issues/" + issue_id,
                     "source_version": checksum, "authority": "operational_projection",
                     "content_sha256": checksum, "observed_at": issue["updatedAt"],
                     "title": identifier + " native task scorecard", "content": payload.decode()})
    return sorted(docs, key=lambda doc: doc["id"])


def project(reader, writer, docs):
    if not docs or len(docs) > 32 or len({doc["id"] for doc in docs}) != len(docs):
        raise ValueError("Invalid telemetry inventory")
    response = reader.request("POST", f"/{DOCS_READ_ALIAS}/_search", {
        "size": len(docs), "query": {"ids": {"values": [doc["id"] for doc in docs]}},
    })
    hits = response.get("hits", {}).get("hits")
    if not isinstance(hits, list) or len(hits) > len(docs):
        raise ValueError("Malformed telemetry projection readback")
    existing = {hit["_id"]: hit["_source"] for hit in hits}
    changes = [doc for doc in docs if existing.get(doc["id"]) != doc]
    if not changes:
        return 0
    lines = []
    for doc in changes:
        lines.extend((json.dumps({"index": {"_index": DOCS_WRITE_ALIAS, "_id": doc["id"]}}), json.dumps(doc)))
    result = writer.request("POST", "/_bulk?refresh=wait_for", "\n".join(lines) + "\n",
                            content_type="application/x-ndjson")
    items = result.get("items")
    if (result.get("errors") or not isinstance(items, list) or len(items) != len(changes)
            or any(item.get("index", {}).get("status") not in (200, 201) for item in items)):
        raise RuntimeError("Telemetry projection failed; native Paperclip records remain authoritative")
    return len(changes)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True, help="private board state")
    parser.add_argument("--roster", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        state = read_object(args.state)
        docs = collect_documents(Client(state["baseUrl"], state["boardApiKey"]), state, read_object(args.roster))
        env = os.environ
        users = [env["AIF_DOCS_READER_USER"], env["AIF_DOCS_WRITER_USER"]]
        if users[0] == users[1] or any(user.lower() == "admin" for user in users):
            raise ValueError("Distinct non-admin projector principals are required")
        clients = [HttpClient(env["AIF_DOCS_URL"], user, env[f"AIF_DOCS_{mode}_PASSWORD"],
                              insecure_localhost=env.get("AIF_DOCS_LOCAL_TEST") == "1")
                   for user, mode in zip(users, ("READER", "WRITER"))]
        writes = project(*clients, docs)
        print(json.dumps({"status": "PASS", "documents": len(docs), "writes": writes,
                          "sourceDigest": digest(encoded(docs)), "authority": "paperclip"}))
        return 0
    except Exception:
        print(json.dumps({"status": "failed", "message": "Inspect the scoped native source and projector configuration privately."}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
