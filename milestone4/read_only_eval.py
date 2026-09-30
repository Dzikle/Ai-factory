"""Supervised, free-model native read-only evaluation; not a coding workflow.

Paperclip creates/owns every run. This operator prepares prompts and observes
results; it never wraps the native harness, approves integration or retries a
provider call. Results measure these read-only calls, not interrupted coding
handoffs or general model improvement.
"""

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import subprocess
import time
from uuid import uuid4

from milestone0.scripts.paperclip_admission import Client
from milestone2.task import read_object
from milestone1.git_projection import collect_snapshot
from milestone1.opensearch_projection import HttpClient
from milestone2.scripts.rotate_local_paperclip_database import CONTROLLER, docker
import os
from milestone3.memory import digest, encoded
from .restore_drill import assert_quiescent


MODELS = {"opencode/muse-spark-1.3-contributor-free", "opencode/mimo-v2.6-flash-free"}
EXPECTED = {"taskStateOwner": "Paperclip", "currentProjectTruth": "Git",
            "memoryPrimary": "MemPalace", "searchIsRebuildableProjection": True,
            "memoryCanOverrideGit": False, "codeGraphEnabled": False,
            "nativeHarnessThroughLiteLLM": False, "autonomousCanonicalMutation": False}
CONTRACT = """Read-only project-policy evaluation. Do not write files, create commits,
update issues, call provider APIs directly, inspect credentials/environment, or
perform coordination. Do not read .milestone0 or private state. You may read the
current canonical repository documents to resolve the question. Complete the
native provider normally by returning one JSON object, no markdown or prose.
For the current AI Factory V1, answer these fields: taskStateOwner (component
name), currentProjectTruth (system name), memoryPrimary (component name),
searchIsRebuildableProjection (boolean), memoryCanOverrideGit (boolean),
codeGraphEnabled (boolean), nativeHarnessThroughLiteLLM (boolean), and
autonomousCanonicalMutation (boolean)."""


def verified_context(root, reader, revision):
    paths = ["docs/decisions/V1_ADOPTION_ARCHITECTURE.md", "docs/decisions/adr/006-memory-mempalace.md",
             "docs/architecture/STATE_AND_STORAGE.md"]
    docs = collect_snapshot(Path(root), project_id="ai-factory", repository_id="ai-factory",
                            remote="https://github.com/Dzikle/Ai-factory.git", canonical_paths=paths, revision=revision)
    if len(docs) != len(paths):
        raise ValueError("Canonical evaluation source missing")
    response = reader.request("POST", "/ai_factory_docs/_search", {
        "size": len(docs), "query": {"ids": {"values": [doc["id"] for doc in docs]}},
    })
    hits = response.get("hits", {}).get("hits")
    if not isinstance(hits, list) or len(hits) != len(docs):
        raise ValueError("Canonical context retrieval incomplete")
    actual = {hit["_source"]["id"]: hit["_source"] for hit in hits}
    for doc in docs:
        # Remote text can differ after Git changed remotes; verify all truth-bearing fields.
        if any(actual.get(doc["id"], {}).get(key) != doc[key] for key in (
            "id", "project_id", "repository_id", "path", "content", "source_system", "source_id",
            "source_revision", "source_version", "content_sha256", "canonical", "status",
        )):
            raise ValueError("Retrieved context differs from canonical Git")
    fragments = []
    for doc in docs:
        lines = doc["content"].splitlines()
        selected = [line for line in lines if re.search(
            r"Paperclip|MemPalace|CodeGraph|LiteLLM|canonical|autonomous.*mutat|rebuildable", line, re.I)]
        excerpt = "\n".join(selected)[:1500]
        fragments.append(doc["path"] + " @ " + doc["source_revision"] + "; SHA-256 "
                         + doc["content_sha256"] + "\n" + excerpt)
    return "\n\n".join(fragments)


def answer(result):
    if not isinstance(result, str) or len(result.encode()) > 8000:
        raise ValueError("Missing or unbounded native answer")
    result = result.strip()
    if result.startswith("```json\n") and result.endswith("\n```"):
        result = result[8:-4]
    try:
        value = json.loads(result)
    except json.JSONDecodeError:
        # Native OpenCode summary joins earlier text parts with the final one.
        # Require the final complete JSON object, not a substring in a tool log.
        candidates = []
        for offset, character in enumerate(result):
            if character != "{":
                continue
            try:
                candidate, end = json.JSONDecoder().raw_decode(result[offset:])
            except json.JSONDecodeError:
                continue
            if isinstance(candidate, dict) and not result[offset + end:].strip():
                candidates.append(candidate)
        if len(candidates) != 1:
            raise ValueError("No unique final native JSON answer") from None
        value = candidates[0]
    if not isinstance(value, dict) or set(value) != set(EXPECTED):
        raise ValueError("Native answer violates the fixed evaluation contract")
    if any(type(value[key]) is not type(expected) for key, expected in EXPECTED.items()):
        raise ValueError("Native answer has invalid field types")
    return value


def measurement(run):
    usage = run.get("usageJson")
    if run.get("status") != "succeeded" or not isinstance(usage, dict):
        raise ValueError("Only a settled native success supplies complete evaluation usage")
    if usage.get("usageCompleteness", "complete") != "complete":
        raise ValueError("Partial usage cannot satisfy the evaluation gate")
    fields = ("inputTokens", "cachedInputTokens", "outputTokens", "costUsd")
    values = {key: usage.get(key) for key in fields}
    if any(type(value) not in (int, float) or not math.isfinite(value) or value < 0 for value in values.values()):
        raise ValueError("Native usage or cost is unknown")
    if any(int(values[key]) != values[key] for key in fields[:-1]):
        raise ValueError("Invalid native token counts")
    start = datetime.fromisoformat(run["startedAt"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(run["finishedAt"].replace("Z", "+00:00"))
    if start.tzinfo is None or end.tzinfo is None or end < start:
        raise ValueError("Invalid native run timing")
    value = answer((run.get("resultJson") or {}).get("result")
                   or (run.get("resultJson") or {}).get("summary") or run.get("summary"))
    return {"runId": run["id"], "agentId": run["agentId"], "status": run["status"],
            "usage": values, "runtimeMs": round((end - start).total_seconds() * 1000, 3),
            "answers": value, "checksPassed": sum(value[key] == expected for key, expected in EXPECTED.items()),
            "checksExpected": len(EXPECTED), "nativeResultDigest": digest(encoded(value))}


def wait_run(client, run_id, company, agent_id, issue_id, timeout=240):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        _, run = client.request("GET", "/api/heartbeat-runs/" + run_id)
        if run.get("companyId") != company or run.get("agentId") != agent_id or run.get("id") != run_id:
            raise ValueError("Native evaluation run identity/scope mismatch")
        if (run.get("contextSnapshot") or {}).get("issueId") != issue_id:
            raise ValueError("Native evaluation run belongs to another issue")
        if run["status"] not in {"queued", "running"}:
            return run
        time.sleep(3)
    raise RuntimeError("Native evaluation timed out; inspect the exact run before another call")


def run(state_path, output_dir, reader, actor_id, baseline_run_id=None, expected_revision=None):
    root = Path(__file__).resolve().parents[1]
    output = Path(output_dir).resolve()
    if not output.is_relative_to(root / ".milestone0") or output == root / ".milestone0" or output.exists():
        raise ValueError("Use a new named private evidence directory inside .milestone0")
    assert_quiescent()
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True, timeout=10).strip()
    if expected_revision is not None and expected_revision != revision:
        raise ValueError("Expected immutable evaluation commit differs from HEAD")
    context = verified_context(root, reader, revision)
    if not context.strip() or len(context.encode()) > 6000:
        raise ValueError("Canonical evaluation context exceeds its byte bound")
    docker("exec", "--user", "0", CONTROLLER, "git", "-c", "safe.directory=/paperclip/m1-first-task-source",
           "-C", "/paperclip/m1-first-task-source", "merge-base", "--is-ancestor", revision, "milestone1-contracts")
    state = read_object(state_path)
    client = Client(state["baseUrl"], state["boardApiKey"])
    company, suffix = state["companyId"], uuid4().hex[:12]
    _, actor = client.request("GET", "/api/agents/" + actor_id)
    if (actor.get("companyId") != company or actor.get("status") != "paused"
            or actor.get("adapterType") != "opencode_local"):
        raise ValueError("Reuse only an explicitly selected paused native smoke actor")
    _, effective = client.request("GET", f"/api/companies/{company}/tools/profiles/effective/agents/{actor_id}")
    if effective.get("allowedToolNames") != ["SearchIndexTool"]:
        raise ValueError("Read-only evaluation requires the existing exact governed search-only MCP profile")
    original_config = actor["adapterConfig"]
    original_runtime = actor["runtimeConfig"]
    if any(key not in {"XDG_DATA_HOME", "HOME", "XDG_CONFIG_HOME"} for key in original_config.get("env", {})):
        raise ValueError("Use a smoke actor with only nonsecret home/config environment bindings")
    output.mkdir(parents=True)
    results = []
    config = {"cwd": "/paperclip/m1-first-task-source", "model": "opencode/muse-spark-1.3-contributor-free",
              "promptTemplate": CONTRACT, "timeoutSec": 180,
              "dangerouslySkipPermissions": original_config.get("dangerouslySkipPermissions", False),
              "env": {"XDG_DATA_HOME": {"type": "plain", "value": "/paperclip/m4-readonly-" + suffix}},
              "desiredSkills": []}
    try:
        client.request("PATCH", "/api/agents/" + actor_id, {
            "runtimeConfig": {**original_runtime, "heartbeat": {
                "enabled": False, "wakeOnDemand": True, "wakeOnAssignment": False, "maxConcurrentRuns": 1}},
        })
        client.request("POST", "/api/agents/" + actor_id + "/resume", {})
        for label, model, addition in [
            ("baseline", "opencode/muse-spark-1.3-contributor-free", ""),
            ("context", "opencode/muse-spark-1.3-contributor-free", context),
            ("model-substitution", "opencode/mimo-v2.6-flash-free", context),
        ]:
            if model not in MODELS:
                raise ValueError("Only the specifically allowed free models may execute")
            prompt = CONTRACT + ("\n\nGit-verified canonical context:\n" + addition if addition else "")
            if label == "baseline" and baseline_run_id:
                _, native = client.request("GET", "/api/heartbeat-runs/" + baseline_run_id)
                snapshot = native.get("contextSnapshot") or {}
                dispatch = (native.get("runnerProfileJson") or {}).get("adapterDispatch") or {}
                if (native.get("companyId") != company or native.get("agentId") != actor_id
                        or (snapshot.get("paperclipWorkspace") or {}).get("repoRef") != revision
                        or dispatch.get("adapterType") != "opencode_local"
                        or (native.get("usageJson") or {}).get("model") != model):
                    raise ValueError("Prior baseline does not match the exact native experiment binding")
                _, issue = client.request("GET", "/api/issues/" + snapshot["issueId"])
                if issue.get("description") != CONTRACT or issue.get("companyId") != company:
                    raise ValueError("Prior baseline task does not match the frozen question contract")
                observed = measurement(native)
                observed.update(label=label, model=model, configuredPromptBytes=len(prompt.encode()),
                                configuredPromptSha256=digest(prompt.encode()), addedContextBytes=0,
                                issueId=issue["id"], identifier=issue["identifier"])
                results.append(observed)
                continue
            _, _ = client.request("PATCH", "/api/agents/" + actor_id, {
                "adapterConfig": {**config, "model": model, "promptTemplate": prompt}, "replaceAdapterConfig": True,
            })
            _, issue = client.request("POST", f"/api/companies/{company}/issues", {
                "title": "M4 read-only policy evaluation " + label + " " + suffix,
                "description": CONTRACT, "status": "backlog", "assigneeAgentId": actor_id,
                "projectId": "856c35c2-b55a-4284-aa91-e7a627c1fe08",
                "executionWorkspaceSettings": {"mode": "isolated_workspace",
                    "workspaceStrategy": {"type": "git_worktree", "baseRef": revision}},
                "idempotencyKey": "m4-readonly-" + suffix + "-" + label,
                "executionPolicy": {"mode": "normal", "commentRequired": True, "stages": [
                    {"type": "approval", "participants": [{"type": "user", "userId": state["userId"]}]}]},
            }, expected=(200, 201))
            _, wake = client.request("POST", "/api/agents/" + actor_id + "/wakeup", {
                "source": "on_demand", "triggerDetail": "manual", "reason": "m4_read_only_evaluation",
                "forceFreshSession": True, "idempotencyKey": "m4-readonly-" + suffix + "-" + label,
                "payload": {"issueId": issue["id"], "taskKey": "m4-readonly-" + suffix + "-" + label},
            }, expected=(200, 201, 202))
            (output / (label + "-run.json")).write_text(json.dumps({
                "issueId": issue["id"], "identifier": issue["identifier"], "runId": wake["id"],
                "model": model, "revision": revision, "promptSha256": digest(prompt.encode()),
            }) + "\n", encoding="utf-8")
            native = wait_run(client, wake["id"], company, actor_id, issue["id"])
            observed = measurement(native)
            observed.update(label=label, model=model, configuredPromptBytes=len(prompt.encode()),
                            configuredPromptSha256=digest(prompt.encode()), addedContextBytes=len(addition.encode()),
                            issueId=issue["id"], identifier=issue["identifier"])
            results.append(observed)
            # Publish a supervised pending owner disposition only after native
            # provider settlement; this is not approval or a coding-stage relay.
            client.request("PATCH", "/api/issues/" + issue["id"], {
                "status": "in_review", "comment": "Native read-only evaluation settled. Exact result and usage retained in run "
                    + native["id"] + ". Owner evaluation review pending; no integration or performance approval implied.",
            })
            (output / "observations.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
            print(json.dumps({"phase": label, "runId": native["id"], "status": native["status"],
                              "checksPassed": observed["checksPassed"], "usageComplete": True}), flush=True)
    finally:
        errors = []
        for method, path, body in [
            ("POST", "/api/agents/" + actor_id + "/pause", {}),
            ("PATCH", "/api/agents/" + actor_id, {
                "adapterConfig": original_config, "runtimeConfig": original_runtime, "replaceAdapterConfig": True}),
        ]:
            try:
                client.request(method, path, body)
            except Exception:
                errors.append("actor_cleanup")
        try:
            assert_quiescent()
        except Exception:
            errors.append("quiescence")
        if errors:
            raise RuntimeError("Evaluation actor cleanup/quiescence requires attention") from None
    receipt = {"status": "PASS" if all(row["checksPassed"] == len(EXPECTED) for row in results) else "QUALITY_FAILED",
               "observedAt": datetime.now(timezone.utc).isoformat(), "adapterType": "opencode_local",
               "logicalAgentId": actor["id"], "externalMcpGrants": ["SearchIndexTool"], "actorPaused": True,
               "scope": "read_only_policy_question_evaluation_not_coding_task_cost_or_owner_integration",
               "contextSha256": digest(context.encode()), "results": results,
               "limitations": ["one_serial_pair_not_randomized", "free_reported_cost_not_invoice",
                               "context_supplied_not_proof_of_causal_use", "no_interrupted_coding_handoff_cost_claim"]}
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expect-revision", required=True)
    parser.add_argument("--insecure-localhost", action="store_true")
    parser.add_argument("--smoke-agent", required=True, help="existing paused native smoke actor with exact search-only MCP grants")
    parser.add_argument("--baseline-run", help="reobserve an existing exact successful baseline; never reexecutes it")
    args = parser.parse_args(argv)
    try:
        if os.environ["AIF_DOCS_READER_USER"].lower() == "admin":
            raise ValueError("Canonical context requires a non-admin reader")
        reader = HttpClient(os.environ["AIF_DOCS_URL"], os.environ["AIF_DOCS_READER_USER"],
                            os.environ["AIF_DOCS_READER_PASSWORD"], insecure_localhost=args.insecure_localhost)
        print(json.dumps(run(args.state, args.output_dir, reader, args.smoke_agent, args.baseline_run, args.expect_revision)))
        return 0
    except Exception:
        print(json.dumps({"status": "failed", "message": "Inspect exact native run and private evidence before retrying; no automatic provider retry."}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
