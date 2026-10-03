"""Verify saved native script-discovery evidence; read-only, no agent dispatch."""

import argparse
import json
import re
import sys

from milestone2.task import read_object


EXPECTED = {"publicationModule": "milestone2.publish", "guide": "milestone2/PUBLISH.md",
            "preflightSubcommand": "preflight", "publicationSubcommand": "publish",
            "testModule": "milestone3.check", "developerMayPublish": False,
            "reviewerMayPublish": False, "ownerApprovalRequired": True,
            "preflightHelpExecuted": True}


def evaluate(run, log, revision):
    workspace = (run.get("contextSnapshot") or {}).get("paperclipWorkspace") or {}
    dispatch = (run.get("runnerProfileJson") or {}).get("adapterDispatch") or {}
    if (log.get("runId") != run.get("id") or not re.fullmatch(r"[0-9a-f]{40}", revision) or run.get("status") != "succeeded"
            or (workspace.get("gitHead") or workspace.get("repoRef")) != revision
            or dispatch.get("adapterType") != "opencode_local"):
        raise ValueError("Native success/adapter/revision identity does not match the discovery check")
    summary = (run.get("resultJson") or {}).get("summary") or run.get("summary")
    if not isinstance(summary, str) or len(summary.encode()) > 8000:
        raise ValueError("Missing or unbounded native discovery answer")
    match = re.search(r"(\{[^{}]*\})\s*$", summary)
    value = json.loads(match[1]) if match else None
    if (not isinstance(value, dict) or set(value) != set(EXPECTED)
            or any(type(value[k]) is not type(v) or value[k] != v for k, v in EXPECTED.items())):
        raise ValueError("Discovery answer confuses command identity or role/approval restrictions")
    content = log.get("content")
    if not isinstance(content, str) or len(content.encode()) > 1_048_576:
        raise ValueError("Missing or unbounded native execution log")
    chunks = []
    for line in content.splitlines():
        row = json.loads(line)
        if row.get("stream") == "stdout" and isinstance(row.get("chunk"), str):
            chunks.append(row["chunk"])
    for line in "".join(chunks).splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        part = event.get("part") or {}
        state = part.get("state") or {}
        command = (state.get("input") or {}).get("command")
        output = state.get("output", "")
        if (event.get("type") == "tool_use" and part.get("tool") == "bash"
                and state.get("status") == "completed" and isinstance(command, str)
                and re.fullmatch(r"python(?:3(?:\.\d+)?)? -m milestone2\.publish preflight --help", command.strip())
                and isinstance(output, str) and output.startswith("usage: publish.py preflight")
                and "--repo" in output and "--plan" in output):
            return {"status": "PASS", "runId": run.get("id"), "revision": revision,
                    "answers": value, "observedCommand": command.strip(),
                    "scope": "native_read_only_discovery_not_publication_or_access_enforcement"}
    raise ValueError("Native command execution proof is missing; model assertion alone is insufficient")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, help="saved native run JSON")
    parser.add_argument("--log", required=True, help="saved native log API JSON")
    parser.add_argument("--revision", required=True, help="exact source revision used in that run")
    args = parser.parse_args(argv)
    try:
        result = evaluate(read_object(args.run), read_object(args.log), args.revision)
        print(json.dumps(result))
        return 0
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        print("Discovery proof failed: inspect native identity, answer and command execution evidence", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
