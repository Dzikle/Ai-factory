#!/usr/bin/env python3
"""Minimal Streamable HTTP MCP admission probe using only the standard library."""

from __future__ import annotations

import argparse
import http.client
import json
import os
import sys
from urllib.parse import urlparse


class McpHttpClient:
    def __init__(self, url: str, token: str | None, timeout: float) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("MCP URL must be http(s)://host[:port]/path")
        connection_type = (
            http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
        )
        self.connection = connection_type(parsed.hostname, parsed.port, timeout=timeout)
        self.path = parsed.path or "/mcp"
        if parsed.query:
            self.path += f"?{parsed.query}"
        self.token = token
        self.session_id: str | None = None
        self.next_id = 1

    def close(self) -> None:
        self.connection.close()

    def _headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        return headers

    @staticmethod
    def _parse_body(content_type: str, body: str) -> dict | None:
        if not body.strip():
            return None
        if "text/event-stream" in content_type:
            payloads = []
            for line in body.splitlines():
                if line.startswith("data:"):
                    payloads.append(line[5:].strip())
            if not payloads:
                raise RuntimeError(f"SSE response did not contain a data event: {body[:500]}")
            return json.loads(payloads[-1])
        return json.loads(body)

    def send(self, method: str, params: dict | None = None, *, notification: bool = False) -> dict | None:
        payload: dict[str, object] = {"jsonrpc": "2.0", "method": method}
        if not notification:
            payload["id"] = self.next_id
            self.next_id += 1
        if params is not None:
            payload["params"] = params
        self.connection.request(
            "POST",
            self.path,
            body=json.dumps(payload).encode("utf-8"),
            headers=self._headers(),
        )
        response = self.connection.getresponse()
        body = response.read().decode("utf-8", errors="replace")
        session_id = response.getheader("Mcp-Session-Id")
        if session_id:
            self.session_id = session_id
        if response.status >= 400:
            raise RuntimeError(f"HTTP {response.status}: {body[:1000]}")
        parsed = self._parse_body(response.getheader("Content-Type", ""), body)
        if parsed and parsed.get("error"):
            raise RuntimeError(json.dumps(parsed["error"], sort_keys=True))
        return parsed


def parse_call(value: str) -> tuple[str, dict]:
    name, separator, raw = value.partition("=")
    if not separator or not name:
        raise argparse.ArgumentTypeError("calls must be NAME={JSON_OBJECT}")
    arguments = json.loads(raw)
    if not isinstance(arguments, dict):
        raise argparse.ArgumentTypeError("call arguments must be a JSON object")
    return name, arguments


def compact(value: object, limit: int) -> object:
    encoded = json.dumps(value, sort_keys=True, default=str)
    if len(encoded) <= limit:
        return value
    return {"truncated": True, "characters": len(encoded), "prefix": encoded[:limit]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--token-env")
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--call", action="append", default=[], type=parse_call)
    parser.add_argument("--include-schemas", action="store_true")
    parser.add_argument("--output-limit", type=int, default=5000)
    args = parser.parse_args()

    token = os.environ.get(args.token_env) if args.token_env else None
    if args.token_env and not token:
        raise RuntimeError(f"required token environment variable is unset: {args.token_env}")

    client = McpHttpClient(args.url, token, args.timeout)
    report: dict[str, object] = {"url": args.url, "calls": []}
    try:
        initialized = client.send(
            "initialize",
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "ai-factory-milestone0", "version": "1"},
            },
        )
        client.send("notifications/initialized", notification=True)
        tools_response = client.send("tools/list", {}) or {}
        tools = tools_response.get("result", {}).get("tools", [])
        report["server"] = (initialized or {}).get("result", {}).get("serverInfo")
        report["protocolVersion"] = (initialized or {}).get("result", {}).get("protocolVersion")
        report["session"] = bool(client.session_id)
        report["tools"] = [tool.get("name") for tool in tools]
        if args.include_schemas:
            report["toolSchemas"] = {
                tool.get("name"): tool.get("inputSchema") for tool in tools
            }
        for name, arguments in args.call:
            response = client.send("tools/call", {"name": name, "arguments": arguments})
            report["calls"].append(
                {"name": name, "result": compact((response or {}).get("result"), args.output_limit)}
            )
    finally:
        client.close()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"error": str(exc), "type": type(exc).__name__}, sort_keys=True))
        raise SystemExit(1)
