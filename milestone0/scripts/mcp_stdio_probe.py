#!/usr/bin/env python3
"""Minimal stdio MCP admission probe for a process command after ``--``."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys


def parse_call(value: str) -> tuple[str, dict]:
    name, separator, raw = value.partition("=")
    if not separator or not name:
        raise argparse.ArgumentTypeError("calls must be NAME={JSON_OBJECT}")
    arguments = json.loads(raw)
    if not isinstance(arguments, dict):
        raise argparse.ArgumentTypeError("call arguments must be a JSON object")
    return name, arguments


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--call", action="append", default=[], type=parse_call)
    parser.add_argument("--include-schemas", action="store_true")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("a process command is required after --")

    requests: list[dict] = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "ai-factory-milestone0", "version": "1"},
            },
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    ]
    for request_id, (name, arguments) in enumerate(args.call, start=3):
        requests.append(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            }
        )
    payload = "".join(json.dumps(request, separators=(",", ":")) + "\n" for request in requests)

    try:
        completed = subprocess.run(
            command,
            input=payload,
            text=True,
            capture_output=True,
            timeout=args.timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"stdio MCP process exceeded {args.timeout}s") from exc

    responses = []
    noise = []
    for line in completed.stdout.splitlines():
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            noise.append(line)
            continue
        if isinstance(parsed, dict) and parsed.get("jsonrpc") == "2.0":
            responses.append(parsed)
        else:
            noise.append(line)
    by_id = {response.get("id"): response for response in responses if "id" in response}
    tools = by_id.get(2, {}).get("result", {}).get("tools", [])
    report = {
        "command": command,
        "exitCode": completed.returncode,
        "server": by_id.get(1, {}).get("result", {}).get("serverInfo"),
        "protocolVersion": by_id.get(1, {}).get("result", {}).get("protocolVersion"),
        "tools": [tool.get("name") for tool in tools],
        "toolSchemas": (
            {tool.get("name"): tool.get("inputSchema") for tool in tools}
            if args.include_schemas
            else None
        ),
        "calls": [by_id.get(request_id) for request_id in range(3, 3 + len(args.call))],
        "stdoutNoise": noise[-10:],
        "stderrTail": completed.stderr.splitlines()[-20:],
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if completed.returncode != 0 or any(response is None for response in report["calls"]):
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"error": str(exc), "type": type(exc).__name__}, sort_keys=True))
        raise SystemExit(1)
