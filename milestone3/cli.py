"""Supervised capture/projection/recall; no scheduler or automatic task dispatch."""

import argparse
import json
import os
from urllib.parse import urlsplit

from milestone0.scripts.mcp_http_probe import McpHttpClient
from milestone0.scripts.paperclip_admission import Client
from milestone1.opensearch_projection import HttpClient
from milestone2.task import read_object
from .memory import MemPalace, git_source_is_current, project, recall, validate_envelope


def connect_memory(*, writable=False):
    url = os.environ.get("AIF_MEMORY_URL", "http://127.0.0.1:18767/mcp")
    parsed = urlsplit(url)
    if parsed.username or parsed.password or parsed.fragment or parsed.scheme not in ("http", "https"):
        raise ValueError("Invalid memory URL")
    if parsed.scheme == "http" and parsed.hostname not in ("127.0.0.1", "localhost", "::1"):
        raise ValueError("Memory credentials require HTTPS or local loopback HTTP")
    token = os.environ.get("AIF_MEMORY_TOKEN")
    if not token:
        raise ValueError("Set AIF_MEMORY_TOKEN in the trusted preparer's environment")
    client = McpHttpClient(url, token, 15)
    try:
        client.send("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                  "clientInfo": {"name": "aif-supervised-memory", "version": "1"}})
        client.send("notifications/initialized", notification=True)
    except Exception:
        client.close()
        raise
    return MemPalace(client, writable=writable)


def search_client(mode):
    return HttpClient(os.environ["AIF_DOCS_URL"], os.environ[f"AIF_DOCS_{mode}_USER"],
                      os.environ[f"AIF_DOCS_{mode}_PASSWORD"],
                      insecure_localhost=os.environ.get("AIF_DOCS_LOCAL_TEST") == "1")


def external_verifier(state_path):
    if not state_path:
        return None
    state = read_object(state_path)
    client = Client(state["baseUrl"], state["boardApiKey"])

    def verify(source):
        if source["source_system"] != "paperclip":
            return False
        # Only the configured company and completed owner-approved task qualify.
        _, issue = client.request("GET", "/api/issues/" + source["source_id"])
        execution = issue.get("executionState") or {}
        return (issue.get("companyId") == state["companyId"] and issue.get("status") == "done"
                and execution.get("status") == "completed" and execution.get("lastDecisionOutcome") == "approved"
                and execution.get("lastDecisionId") == source["source_version"])

    return verify


def attach_context(task, report):
    """Paperclip stores the task and run snapshots; this function stores nothing."""
    if report["status"] != "used":
        return dict(task)
    return {**task, "description": task["description"] + "\n\n" + report["prompt"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", default=os.environ.get("AIF_PAPERCLIP_STATE"), help="private board state, for source verification only")
    commands = parser.add_subparsers(dest="command", required=True)
    capture = commands.add_parser("capture", help="store one reviewed lesson in MemPalace")
    capture.add_argument("--lesson", required=True)
    capture.add_argument("--cwd", default=".")
    projection = commands.add_parser("project", help="copy only authoritative metadata into the existing docs index")
    projection.add_argument("--drawer", required=True)
    supersession = commands.add_parser("supersede", help="mark an old drawer superseded after its successor exists")
    supersession.add_argument("--drawer", required=True)
    supersession.add_argument("--successor", required=True)
    retrieval = commands.add_parser("recall", help="produce bounded historical advice; backend loss yields no advice")
    retrieval.add_argument("--query", required=True)
    retrieval.add_argument("--project", required=True)
    retrieval.add_argument("--role", required=True)
    retrieval.add_argument("--cwd", default=".")
    retrieval.add_argument("--task", help="optionally emit a task with advice attached; does not submit it")
    args = parser.parse_args(argv)
    store = None
    try:
        if args.command == "recall":
            try:
                store = connect_memory()
                report = recall(store, search_client("READER"), cwd=args.cwd, project_id=args.project,
                                role=args.role, query=args.query, verify_external=external_verifier(args.state))
            except Exception:
                report = {"status": "degraded", "prompt": "", "memories": [], "context_bytes": 0, "estimated_tokens": 0}
            if args.task:
                report = {"memory": report, "task": attach_context(read_object(args.task), report)}
            print(json.dumps(report, indent=2))
            return 0
        store = connect_memory(writable=args.command in ("capture", "supersede"))
        if args.command == "capture":
            envelope = validate_envelope(read_object(args.lesson))
            verify = external_verifier(args.state)
            sources = envelope["record"]["source_refs"]
            if not any(s["source_system"] == "git" for s in sources) or not all(
                git_source_is_current(args.cwd, s) if s["source_system"] == "git" else
                verify is not None and verify(s) is True for s in sources
            ):
                raise ValueError("Lesson sources are not verified")
            report = {"drawer_id": store.remember(envelope)}
        elif args.command == "project":
            doc = project(search_client("WRITER"), args.drawer, store.get(args.drawer))
            report = {"projected_id": doc["id"], "source_uri": doc["source_uri"], "status": doc["status"]}
        else:
            result = store.supersede(args.drawer, args.successor)
            report = {"drawer_id": args.drawer, "status": result["record"]["status"],
                      "superseded_by": result["record"]["superseded_by"]}
        print(json.dumps(report))
        return 0
    except Exception:
        # Neither privileged backend messages nor credentials enter public output.
        print(json.dumps({"status": "failed", "operation": args.command,
                          "message": "Memory operation failed; inspect private configuration/source state before retrying."}))
        return 1
    finally:
        if store:
            store.client.close()


if __name__ == "__main__":
    raise SystemExit(main())
