"""Bounded backup/restore proof for the pinned production MemPalace volume."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import time
from uuid import uuid4

from milestone2.scripts.rotate_local_paperclip_database import docker, sha256


def _digest(value):
    return hashlib.sha256(value).hexdigest()


def _encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


ROOT = Path(__file__).resolve().parents[1]
SOURCE = "aif-m0-mempalace-production-mempalace-1"
VOLUME = "aif-m0-mempalace-embeddinggemma-data"
IMAGE = "ghcr.io/mempalace/mempalace@sha256:65da0834ab5ddc2d8247de43aff611393a151eac2893108e66b64f077bf1f232"
WING = "ai-factory"
ROOM = "engineering-lessons"
PAGE_SIZE = 100
MAX_DRAWERS = 1000
READ_TOOLS = {"mempalace_search", "mempalace_get_drawer", "mempalace_list_drawers"}
READ_ONLY_TOOLS = READ_TOOLS | {
    "mempalace_artifact_get", "mempalace_check_duplicate", "mempalace_diary_read",
    "mempalace_event_list", "mempalace_event_wait", "mempalace_find_tunnels",
    "mempalace_follow_tunnels", "mempalace_get_aaak_spec", "mempalace_get_taxonomy",
    "mempalace_graph_stats", "mempalace_kg_query", "mempalace_kg_stats",
    "mempalace_kg_timeline", "mempalace_list_hallways", "mempalace_list_rooms",
    "mempalace_list_tunnels", "mempalace_list_wings", "mempalace_mesh_peers",
    "mempalace_reconnect", "mempalace_status", "mempalace_traverse",
}
SOURCE_COMMAND = ["serve", "--host", "0.0.0.0", "--port", "8765", "--backend", "sqlite_exact",
                  "--palace", "/data/palace_sqlite"]
SOURCE_ENV = {"MEMPALACE_BACKEND": "sqlite_exact", "MEMPALACE_EMBEDDING_MODEL": "embeddinggemma",
              "MEMPALACE_EMBEDDING_DEVICE": "cpu", "MEMPALACE_EMBEDDING_THREADS": "2",
              "MEMPALACE_MCP_IDLE_HOURS": "0", "MEMPALACE_PALACE_PATH": "/data/palace_sqlite",
              "HF_HUB_OFFLINE": "1"}


def validate_page(page, expected_offset):
    if not isinstance(page, dict) or set(("total", "count", "offset", "limit", "drawers")) - page.keys():
        raise ValueError("Invalid MemPalace list page")
    rows = page["drawers"]
    if (type(page["total"]) is not int or not 0 <= page["total"] <= MAX_DRAWERS
            or not isinstance(rows, list) or len(rows) > PAGE_SIZE
            or type(page["count"]) is not int or page["count"] != len(rows)
            or type(page["offset"]) is not int or page["offset"] != expected_offset
            or type(page["limit"]) is not int or page["limit"] != PAGE_SIZE
            or page["count"] > max(0, page["total"] - expected_offset)):
        raise ValueError("MemPalace page exceeded bounds or returned inconsistent pagination")
    return rows


def drawer_manifest(drawers):
    if not isinstance(drawers, list) or not drawers:
        raise ValueError("No scoped MemPalace drawers to verify")
    manifest = []
    seen = set()
    for row in drawers:
        if not isinstance(row, dict) or row.get("wing") != WING or row.get("room") != ROOM:
            raise ValueError("MemPalace drawer escaped the required scope")
        drawer_id, envelope = row.get("drawer_id"), row.get("envelope")
        if not isinstance(drawer_id, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,256}", drawer_id):
            raise ValueError("Invalid MemPalace drawer ID")
        if drawer_id in seen or not isinstance(envelope, dict):
            raise ValueError("Duplicate or incomplete MemPalace drawer")
        record = envelope.get("record")
        if (not isinstance(record, dict) or record.get("project_id") != WING
                or not isinstance(envelope.get("content"), str) or not envelope["content"]
                or record.get("content_sha256") != _digest(envelope["content"].encode("utf-8"))):
            raise ValueError("MemPalace drawer content or metadata is invalid")
        seen.add(drawer_id)
        manifest.append({"drawer_id": drawer_id, "status": record.get("status"),
                         "content_sha256": record["content_sha256"],
                         "envelope_sha256": _digest(_encoded(envelope))})
    return sorted(manifest, key=lambda item: item["drawer_id"])


def cleanup_plan(created):
    commands = {"container": ("rm", "-f"), "volume": ("volume", "rm"),
                "token_file": None}
    return [(name, commands[name]) for name, owned in created.items()
            if name in commands and owned]


def validate_tool_catalog(tools, *, require_readonly):
    if not isinstance(tools, list):
        raise ValueError("Invalid MemPalace tool catalog")
    names = {tool.get("name") for tool in tools if isinstance(tool, dict)}
    if not READ_TOOLS <= names or (require_readonly and not names <= READ_ONLY_TOOLS):
        raise ValueError("MemPalace tool catalog does not match its required access mode")
    return names


def server_write_denied(response):
    if not isinstance(response, dict):
        return False
    error = response.get("error")
    if isinstance(error, dict):
        native_refusal = (error.get("code") == -32003
                          and error.get("message") == "Server is in read-only mode; this tool is disabled"
                          and isinstance(error.get("data"), dict)
                          and error["data"].get("tool") == "mempalace_add_drawer")
        return native_refusal or error.get("code") == -32601 or "unknown tool" in str(error).lower()
    result = response.get("result", {})
    if not isinstance(result, dict) or not result.get("isError"):
        return False
    message = " ".join(item.get("text", "") for item in result.get("content", [])
                       if isinstance(item, dict)).lower()
    return "unknown tool" in message or "tool not found" in message


def validate_source_config(source, expected_image_id):
    if not source.get("State", {}).get("Running") or source.get("Image") != expected_image_id:
        raise ValueError("Production MemPalace container is stopped or uses another image")
    config = source.get("Config", {})
    environment = dict(item.split("=", 1) for item in config.get("Env", []) if "=" in item)
    if config.get("Cmd") != SOURCE_COMMAND or any(environment.get(key) != value
                                                   for key, value in SOURCE_ENV.items()):
        raise ValueError("Production MemPalace runtime does not match the pinned offline embedding configuration")
    if not environment.get("MEMPALACE_MCP_HTTP_TOKEN"):
        raise ValueError("Source MemPalace authentication is not configured")
    mounts = [item for item in source.get("Mounts", []) if item.get("Destination") == "/data"]
    if len(mounts) != 1 or mounts[0].get("Name") != VOLUME:
        raise ValueError("Unexpected production MemPalace data volume")
    return environment["MEMPALACE_MCP_HTTP_TOKEN"]


def _tool_result(client, name, arguments):
    response = client.send("tools/call", {"name": name, "arguments": arguments})
    result = (response or {}).get("result", {})
    content = result.get("content")
    if result.get("isError") or not isinstance(content, list) or len(content) != 1:
        raise RuntimeError("MemPalace tool call failed")
    value = json.loads(content[0]["text"])
    if not isinstance(value, dict) or value.get("error") or value.get("success") is False:
        raise RuntimeError("MemPalace returned an invalid tool result")
    return value


def _all_drawers(store, *, require_readonly=True):
    client = store.client
    tools = client.send("tools/list", {}).get("result", {}).get("tools", [])
    names = validate_tool_catalog(tools, require_readonly=require_readonly)
    rows, total, offset = [], None, 0
    while total is None or offset < total:
        page = _tool_result(client, "mempalace_list_drawers", {
            "wing": WING, "room": ROOM, "limit": PAGE_SIZE, "offset": offset})
        if total is None:
            total = page.get("total")
        elif page.get("total") != total:
            raise RuntimeError("MemPalace drawer set changed during pagination")
        current = validate_page(page, offset)
        rows.extend(current)
        if not current and offset < total:
            raise RuntimeError("MemPalace pagination ended before total")
        offset += len(current)
    if len(rows) != total:
        raise RuntimeError("MemPalace pagination did not cover the reported total")
    full = []
    for row in rows:
        drawer_id = row.get("drawer_id")
        envelope = store.get(drawer_id)
        full.append({"drawer_id": drawer_id, "wing": row.get("wing"), "room": row.get("room"),
                     "envelope": envelope})
    return drawer_manifest(full), names


def _ephemeral_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def _wait_memory(url, token, timeout=120, *, connect=None):
    if connect is None:
        from milestone3.cli import connect_memory
        connect = connect_memory
    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        store = None
        try:
            os.environ["AIF_MEMORY_URL"] = url
            os.environ["AIF_MEMORY_TOKEN"] = token
            store = connect()
            return store
        except (OSError, RuntimeError, ValueError) as error:
            last_error = error
            if store:
                store.client.close()
            time.sleep(2)
    raise RuntimeError("Restored MemPalace did not become ready") from last_error


def _wait_running(container, timeout=45):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        state = json.loads(docker("inspect", container).stdout)[0]["State"]
        if state.get("Running"):
            return
        if state.get("Status") in {"exited", "dead", "removing"}:
            raise RuntimeError("MemPalace container did not stay running")
        time.sleep(1)
    raise RuntimeError("MemPalace container start timed out")


def run(backup_dir):
    from milestone3.cli import connect_memory
    backup = Path(backup_dir).resolve()
    milestone0 = (ROOT / ".milestone0").resolve()
    if not backup.is_relative_to(milestone0) or backup == milestone0 or backup.exists():
        raise ValueError("Backup must be a new named child of ignored .milestone0")
    source = json.loads(docker("inspect", SOURCE).stdout)[0]
    if not source["State"].get("Running"):
        raise ValueError("The exact production MemPalace source must already be running")
    image = json.loads(docker("image", "inspect", IMAGE).stdout)[0]
    if source["Image"] != image["Id"]:
        raise ValueError("Production MemPalace image does not match the approved immutable digest")
    source_token = validate_source_config(source, image["Id"])

    suffix = uuid4().hex[:12]
    restore_container = "aif-m4-memory-restore-" + suffix
    restore_volume = "aif-m4-memory-volume-" + suffix
    token = secrets.token_urlsafe(32)
    token_file = backup / "restore.env"
    created = {"container": False, "volume": False, "token_file": False}
    source_stopped = False
    source_restart_verified = False
    started = time.monotonic()
    receipt = None
    original_url = os.environ.get("AIF_MEMORY_URL")
    original_token = os.environ.get("AIF_MEMORY_TOKEN")
    try:
        backup.mkdir(parents=True, exist_ok=False)
        os.environ["AIF_MEMORY_URL"] = "http://127.0.0.1:18767/mcp"
        os.environ["AIF_MEMORY_TOKEN"] = source_token
        source_store = connect_memory()
        try:
            before, source_tools = _all_drawers(source_store, require_readonly=False)
        finally:
            source_store.client.close()
        if len(before) != 2 or {row["status"] for row in before} != {"active", "superseded"}:
            raise RuntimeError("Expected exactly the active lesson and its superseded predecessor")

        docker("stop", "--time", "20", SOURCE)
        source_stopped = True
        docker("run", "--rm", "--network", "none", "--user", "0:0",
               "--mount", f"type=volume,source={VOLUME},target=/data,readonly",
               "--mount", f"type=bind,source={backup},target=/backup",
               "--entrypoint", "tar", IMAGE, "-czf", "/backup/mempalace-volume.tar.gz",
               "-C", "/data", ".", timeout=300)
        docker("volume", "create", "--label", "ai-factory.drill=milestone4-memory", restore_volume)
        created["volume"] = True
        docker("run", "--rm", "--network", "none", "--user", "0:0",
               "--mount", f"type=volume,source={restore_volume},target=/data",
               "--mount", f"type=bind,source={backup},target=/backup,readonly",
               "--entrypoint", "tar", IMAGE, "-xzf", "/backup/mempalace-volume.tar.gz",
               "-C", "/data", timeout=300)

        created["token_file"] = True
        token_file.write_text(f"MEMPALACE_MCP_HTTP_TOKEN={token}\n", encoding="utf-8")
        try:
            token_file.chmod(0o600)
        except OSError:
            pass
        port = _ephemeral_port()
        docker("run", "-d", "--name", restore_container, "-p", f"127.0.0.1:{port}:8765",
               "--env-file", str(token_file), "-e", "MEMPALACE_BACKEND=sqlite_exact",
               "-e", "MEMPALACE_EMBEDDING_MODEL=embeddinggemma", "-e", "MEMPALACE_EMBEDDING_DEVICE=cpu",
               "-e", "MEMPALACE_EMBEDDING_THREADS=2", "-e", "MEMPALACE_MCP_IDLE_HOURS=0",
               "-e", "MEMPALACE_PALACE_PATH=/data/palace_sqlite", "-e", "HF_HUB_OFFLINE=1",
               "--mount", f"type=volume,source={restore_volume},target=/data",
               "--label", "ai-factory.drill=milestone4-memory", IMAGE,
               "serve", "--host", "0.0.0.0", "--port", "8765", "--backend", "sqlite_exact",
               "--palace", "/data/palace_sqlite", "--read-only")
        created["container"] = True
        _wait_running(restore_container)
        restored_store = _wait_memory(f"http://127.0.0.1:{port}/mcp", token)
        try:
            after, restored_tools = _all_drawers(restored_store)
            if after != before:
                raise RuntimeError("Restored drawer metadata/content digests differ from source")
            denial = False
            try:
                restored_store.call("mempalace_add_drawer", {})
            except PermissionError:
                denial = True
            if not denial:
                raise RuntimeError("Read-only MemPalace adapter allowed a write")
            server_denied = False
            try:
                server_attempt = restored_store.client.send("tools/call", {
                    "name": "mempalace_add_drawer", "arguments": {
                    "wing": WING, "room": ROOM, "content": "{}",
                    "source_file": "memory:restore-drill-deny-check",
                    "added_by": "aif-milestone4-restore-drill"}})
            except RuntimeError as error:
                try:
                    error_body = json.loads(str(error))
                except json.JSONDecodeError:
                    raise
                if not server_write_denied({"error": error_body}):
                    raise
                server_denied = True
            else:
                server_denied = server_write_denied(server_attempt)
            if not server_denied:
                raise RuntimeError("MemPalace server accepted a write in read-only mode")
            post_denial, _ = _all_drawers(restored_store)
            if post_denial != after:
                raise RuntimeError("Restored drawer manifest changed during the denied write check")
            search = restored_store.call("mempalace_search", {
                "query": "Python test dependencies jsonschema PyYAML", "limit": 10,
                "wing": WING, "room": ROOM, "max_distance": 0})
            results = search.get("results")
            if not isinstance(results, list) or not results:
                raise RuntimeError("Restored offline semantic search returned no matching lesson")
            ids = {item.get("drawer_id") or item.get("parent_drawer_id") for item in results
                   if isinstance(item, dict)}
            if not ids.intersection({item["drawer_id"] for item in before}):
                raise RuntimeError("Semantic search results did not resolve to a restored drawer")
        finally:
            restored_store.client.close()

        receipt = {"status": "PASS", "observedAt": datetime.now(timezone.utc).isoformat(),
                   "image": IMAGE, "sourceContainer": SOURCE, "sourceVolume": VOLUME,
                   "restoredContainer": restore_container, "restoredVolume": restore_volume,
                   "sourceWasRestarted": False, "sourceMcpReady": False,
                   "sourceManifestPreserved": False, "loopbackOnly": True,
                   "sourceToolCount": len(source_tools),
                   "restoredReadOnlyToolCount": len(restored_tools), "writeDenied": True,
                   "postDenialManifestUnchanged": True, "drawers": before,
                   "semanticSearchResults": len(results), "offlineEmbedding": True,
                   "backupSha256": sha256(backup / "mempalace-volume.tar.gz"),
                   "elapsedSeconds": round(time.monotonic() - started, 1)}
    finally:
        errors = []
        for name, command in cleanup_plan(created):
            try:
                if command is None:
                    token_file.unlink(missing_ok=True)
                elif name == "container":
                    docker(*command, restore_container)
                elif name == "volume":
                    docker(*command, restore_volume)
            except (OSError, RuntimeError, subprocess.TimeoutExpired):
                errors.append(name)
        if source_stopped:
            try:
                docker("start", SOURCE)
                _wait_running(SOURCE)
                source_store = _wait_memory("http://127.0.0.1:18767/mcp", source_token)
                try:
                    restarted_manifest, _ = _all_drawers(source_store, require_readonly=False)
                    if restarted_manifest != before:
                        raise RuntimeError("Restarted source MemPalace manifest differs from captured source")
                finally:
                    source_store.client.close()
                source_restart_verified = True
                source_stopped = False
            except (OSError, RuntimeError, subprocess.TimeoutExpired):
                errors.append("source_restart")
        if original_url is None:
            os.environ.pop("AIF_MEMORY_URL", None)
        else:
            os.environ["AIF_MEMORY_URL"] = original_url
        if original_token is None:
            os.environ.pop("AIF_MEMORY_TOKEN", None)
        else:
            os.environ["AIF_MEMORY_TOKEN"] = original_token
        if errors:
            raise RuntimeError("Memory restore cleanup requires attention")
    if receipt is None:
        raise RuntimeError("Memory restore drill ended without a receipt")
    receipt["sourceWasRestarted"] = source_restart_verified
    receipt["sourceMcpReady"] = source_restart_verified
    receipt["sourceManifestPreserved"] = source_restart_verified
    (backup / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backup-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(run(args.backup_dir), indent=2))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired):
        print("Memory restore drill failed. Private backup is retained; inspect local state before retrying.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
