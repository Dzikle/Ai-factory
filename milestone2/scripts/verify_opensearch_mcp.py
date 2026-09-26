#!/usr/bin/env python3
"""Verify the supervised, least-privilege OpenSearch MCP deployment."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "milestone0" / "scripts"))
from mcp_http_probe import McpHttpClient  # noqa: E402


CONTAINER = "aif-m2-opensearch-mcp-opensearch-mcp-1"
TOOLS = {"ListIndexTool", "IndexMappingTool", "SearchIndexTool", "MsearchTool"}
INTERNAL_URL = "http://opensearch-mcp:9900/mcp"


def docker(*args: str) -> str:
    return subprocess.check_output(["docker", *args], text=True, stderr=subprocess.STDOUT).strip()


def inspect() -> dict:
    return json.loads(docker("inspect", CONTAINER))[0]


def verify_distinct_reader_secret(mcp: dict) -> None:
    cluster = json.loads(docker("inspect", "aif-m0-opensearch-opensearch-1"))[0]
    mcp_env = dict(item.split("=", 1) for item in mcp["Config"]["Env"] if "=" in item)
    cluster_env = dict(item.split("=", 1) for item in cluster["Config"]["Env"] if "=" in item)
    assert mcp_env.get("OPENSEARCH_USERNAME") == "aif_agent"
    assert mcp_env.get("OPENSEARCH_PASSWORD"), "MCP reader password is unset"
    assert mcp_env["OPENSEARCH_PASSWORD"] != cluster_env.get("OPENSEARCH_INITIAL_ADMIN_PASSWORD"), (
        "MCP reader and cluster admin must not share a secret"
    )


def probe(url: str) -> None:
    client = McpHttpClient(url, None, 10)
    try:
        client.send("initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "aif-m2-supervision-probe", "version": "1"},
        })
        client.send("notifications/initialized", notification=True)
        listed = client.send("tools/list", {}) or {}
        actual = {tool["name"] for tool in listed["result"]["tools"]}
        assert actual == TOOLS, f"MCP catalog is not deny-default: {sorted(actual)}"
        for index in ("aif_docs_current", "ai_factory_docs"):
            search = client.send("tools/call", {
                "name": "SearchIndexTool",
                "arguments": {
                    "index": index,
                    "query_dsl": {"query": {"match_all": {}}},
                    "size": 1,
                },
            }) or {}
            assert not search.get("result", {}).get("isError"), f"search failed for {index}: {search}"
    finally:
        client.close()


def await_probe(url: str, timeout: float = 90) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            probe(url)
            return
        except (OSError, RuntimeError, AssertionError):
            time.sleep(2)
    raise RuntimeError("MCP did not present its exact catalog and live search before deadline")


def verify_paperclip(state_path: Path, connection_id: str, agent_ids: list[str]) -> None:
    state = json.loads(state_path.read_text(encoding="utf-8"))
    base = state["baseUrl"].rstrip("/")
    headers = {"Authorization": f"Bearer {state['boardApiKey']}", "Origin": "http://localhost:3100"}

    def get(path: str) -> dict:
        with urlopen(Request(f"{base}{path}", headers=headers), timeout=15) as response:
            return json.load(response)

    connection = get(f"/api/tool-connections/{connection_id}")
    assert connection["config"]["url"] == INTERNAL_URL
    assert connection["transportConfig"]["url"] == INTERNAL_URL
    catalog = get(f"/api/tool-connections/{connection_id}/catalog")
    names = {item["toolName"] for item in catalog["catalog"]}
    assert names == TOOLS, f"Paperclip cached catalog is not exact: {sorted(names)}"
    for agent_id in agent_ids:
        effective = get(f"/api/companies/{state['companyId']}/tools/profiles/effective/agents/{agent_id}")
        assert effective["allowedToolNames"] == ["SearchIndexTool"], (
            f"agent {agent_id} has unexpected effective tools: {effective['allowedToolNames']}"
        )
        installed = {item["id"] for item in effective["installedConnections"]}
        assert installed == {connection_id}, f"agent {agent_id} has unexpected connections: {sorted(installed)}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:19902/mcp")
    parser.add_argument("--fault-inject", action="store_true", help="SIGKILL the MCP child process and verify restart")
    parser.add_argument("--paperclip-state", type=Path, help="ignored local board API state file")
    parser.add_argument("--connection-id", help="Paperclip connection to verify; defaults to the admission state file")
    parser.add_argument("--agent-id", action="append", default=[], help="agent whose effective catalog must be search-only")
    args = parser.parse_args()

    before = inspect()
    assert before["State"]["Running"], "MCP container is not running"
    assert before["HostConfig"]["RestartPolicy"]["Name"] == "unless-stopped"
    verify_distinct_reader_secret(before)
    await_probe(args.url)
    if args.paperclip_state:
        state = json.loads(args.paperclip_state.read_text(encoding="utf-8"))
        verify_paperclip(args.paperclip_state, args.connection_id or state["connectionId"], args.agent_id)
    if args.fault_inject:
        started = before["State"]["StartedAt"]
        # Docker treats `docker kill` as an operator stop. The init process is
        # PID 1; killing its MCP child models an unexpected application crash.
        killer = (
            "import os, signal; "
            "children=open('/proc/1/task/1/children').read().split(); "
            "targets=[int(p) for p in children if b'mcp_server_opensearch' "
            "in open('/proc/'+p+'/cmdline','rb').read()]; "
            "assert len(targets)==1, targets; os.kill(targets[0], signal.SIGKILL)"
        )
        subprocess.run(["docker", "exec", CONTAINER, "python", "-c", killer], check=True)
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            time.sleep(2)
            after = inspect()
            if after["State"]["Running"] and after["State"]["StartedAt"] != started:
                try:
                    probe(args.url)
                    if args.paperclip_state:
                        verify_paperclip(args.paperclip_state, args.connection_id or state["connectionId"], args.agent_id)
                    print(json.dumps({"status": "PASS", "catalog": sorted(TOOLS), "restart": True}))
                    return
                except (OSError, RuntimeError, AssertionError):
                    pass
        raise RuntimeError("MCP did not recover with exact catalog and live search after SIGKILL")
    print(json.dumps({"status": "PASS", "catalog": sorted(TOOLS), "restart": False}))


if __name__ == "__main__":
    main()
