"""Bounded, non-atomic Paperclip readback, not a task or telemetry authority."""

from datetime import datetime, timezone
import json
import math
from uuid import UUID


def number(value, *, integer=False):
    if type(value) not in (int, float) or not 0 <= value <= 10**15 or not math.isfinite(value):
        return None
    if integer and value != int(value):
        return None
    return int(value) if integer else value


def identity(value):
    try:
        return str(UUID(value))
    except (ValueError, TypeError, AttributeError) as error:
        raise ValueError("Invalid Paperclip identity in scorecard readback") from error


def timestamp(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo is not None else None
    except (AttributeError, TypeError, ValueError):
        return None


def quality(issue, runs, activity):
    policy, state = issue.get("executionPolicy") or {}, issue.get("executionState") or {}
    if not isinstance(policy, dict) or not isinstance(state, dict):
        raise ValueError("Malformed native execution policy/state")
    stages, completed = policy.get("stages") or [], state.get("completedStageIds") or []
    if (not isinstance(stages, list) or not isinstance(completed, list)
            or any(not isinstance(s, dict) for s in stages)
            or any(not isinstance(s.get("id"), str) for s in stages)
            or any(not isinstance(s, str) for s in completed)):
        raise ValueError("Malformed native quality stages")
    stage_ids = [s["id"] for s in stages]
    complete = bool(stages) and len(set(stage_ids)) == len(stages) and set(stage_ids) == set(completed)
    participants = [s.get("participants") or [] for s in stages]
    if any(not isinstance(p, list) or any(not isinstance(a, dict) for a in p) for p in participants):
        raise ValueError("Malformed native quality participants")
    reviewer_ids = [a.get("agentId") for s, group in zip(stages, participants)
                    if s.get("type") == "review" for a in group if a.get("type") == "agent"]
    # Recovery can change returnAssignee. Use run-linked first-stage requests instead.
    run_agents = {r["id"]: r.get("agentId") for r in runs}
    developers = set()
    for event in activity:
        details = event.get("details") or {}
        if not isinstance(details, dict):
            continue
        snapshot, previous = details.get("executionState"), details.get("_previous")
        if (event.get("action") == "issue.updated" and event.get("actorType") == "agent"
                and event.get("actorId") and event.get("actorId") == run_agents.get(event.get("runId"))
                and isinstance(snapshot, dict) and isinstance(previous, dict)
                and "executionState" in previous and previous["executionState"] is None and stages
                and type(snapshot.get("currentStageIndex")) is int and snapshot["currentStageIndex"] == 0
                and snapshot.get("currentStageId") == stage_ids[0] and snapshot.get("completedStageIds") == []):
            developers.add(event["actorId"])
    distinct = (len(reviewer_ids) >= 2 and all(isinstance(a, str) and a for a in reviewer_ids)
                and len(set(reviewer_ids)) == len(reviewer_ids))
    independent = bool(distinct and developers.isdisjoint(reviewer_ids)) if developers else None
    owner = (complete and issue.get("status") == "done" and stages[-1].get("type") == "approval"
             and any(a.get("type") == "user" and a.get("userId") for a in participants[-1])
             and bool(state.get("lastDecisionId")) and state.get("lastDecisionOutcome") == "approved")
    return {"ownerAccepted": bool(owner), "independentParticipants": independent,
            "independenceBasis": "declared_review_participants_vs_run_linked_first_stage_request_actors; not_execution_proof",
            "completedStages": len(set(completed)), "totalStages": len(stages),
            "changesRequestedRounds": number(state.get("changesRequestedCount"), integer=True),
            "correctness": "not_inferred_from_status; requires_validation_review_and_QA_evidence"}


def collect(client, issue, company_id):
    if not isinstance(issue, dict) or issue.get("companyId") != company_id:
        raise ValueError("Issue does not belong to the configured company")
    issue_id = identity(issue.get("id"))
    _, rows = client.request("GET", f"/api/issues/{issue_id}/runs")
    if not isinstance(rows, list) or len(rows) > 50 or any(not isinstance(r, dict) for r in rows):
        raise ValueError("Scorecard supports at most 50 native task runs")
    ids = [identity(r.get("runId")) for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("Native run list contains duplicate identities")
    runs = []
    for row, run_id in zip(rows, ids):
        _, run = client.request("GET", f"/api/heartbeat-runs/{run_id}")
        if (not isinstance(run, dict) or run.get("id") != run_id or run.get("companyId") != company_id
                or run.get("agentId") != row.get("agentId")
                or not isinstance(run.get("contextSnapshot") or {}, dict)
                or (run.get("contextSnapshot") or {}).get("issueId") not in (None, issue_id)):
            raise ValueError("Native run scope/identity mismatch")
        runs.append(run)
    _, ledger = client.request("GET", f"/api/issues/{issue_id}/cost-summary")
    if not isinstance(ledger, dict) or ledger.get("issueId") != issue_id:
        raise ValueError("Native cost summary scope mismatch")
    if type(ledger.get("issueCount")) is not int or ledger["issueCount"] != 1:
        raise ValueError("Cannot attribute a descendant cost summary to one task")
    _, activity = client.request("GET", f"/api/issues/{issue_id}/activity")
    if not isinstance(activity, list) or len(activity) > 1000:
        raise ValueError("Scorecard supports at most 1000 native task activity records")
    if any(not isinstance(e, dict) or e.get("companyId") != company_id
           or e.get("entityId") != issue_id or e.get("entityType") != "issue" for e in activity):
        raise ValueError("Native activity scope mismatch")

    native_quality = quality(issue, runs, activity)
    timings, token_records, costs = [], [], []
    for run in runs:
        start, end = timestamp(run.get("startedAt")), timestamp(run.get("finishedAt"))
        if start is not None and end is not None and end >= start:
            timings.append((start, end))
        usage = run.get("usageJson")
        if not isinstance(usage, dict):
            continue
        tokens = [number(usage.get(k), integer=True) for k in ("inputTokens", "cachedInputTokens", "outputTokens")]
        if all(t is not None for t in tokens):
            token_records.append(tokens)
        cost = number(usage.get("costUsd"))
        if cost is not None and usage.get("costStatus") == "reported":
            costs.append(cost)
    count = len(runs)
    settled = bool(runs) and all(r.get("status") in {"succeeded", "failed", "cancelled", "timed_out", "skipped"}
                                 for r in runs)
    started_count = sum(timestamp(r.get("startedAt")) is not None for r in runs)
    consistent_count = number(ledger.get("runCount"), integer=True) == started_count
    covered = settled and consistent_count
    token_totals = [sum(t[index] for t in token_records) for index in range(3)]
    known_cost = math.fsum(costs)
    reported_cost = known_cost if covered and len(costs) == count else None
    runtime = math.fsum((end - start).total_seconds() * 1000 for start, end in timings)
    final_timing = covered and len(timings) == count
    return {
        "schemaVersion": 1, "sourceSystem": "paperclip", "issueId": issue_id,
        "identifier": issue.get("identifier"), "status": issue.get("status"),
        "observedAt": datetime.now(timezone.utc).isoformat(), "consistency": "non_atomic_GETs",
        "quality": native_quality, "runCount": count,
        "failedRuns": sum(r.get("status") in {"failed", "timed_out"} for r in runs),
        "handoffCancellations": sum(r.get("status") == "cancelled" and r.get("errorCode") == "issue_reassigned" for r in runs),
        "recordedRetries": sum(bool(r.get("retryOfRunId")) for r in runs),
        "timing": {"coveredRuns": len(timings), "knownRuntimeMs": round(runtime, 3),
                   "runtimeMs": round(runtime, 3) if final_timing else None,
                   "executionWindowMs": round((max(t[1] for t in timings) - min(t[0] for t in timings)).total_seconds() * 1000, 3)
                   if final_timing else None},
        "usage": {"coveredRuns": len(token_records), "costCoveredRuns": len(costs),
                  "knownInputTokens": token_totals[0], "knownCachedInputTokens": token_totals[1],
                  "knownOutputTokens": token_totals[2], "knownReportedCostUsd": known_cost,
                  "inputTokens": token_totals[0] if covered and len(token_records) == count else None,
                  "cachedInputTokens": token_totals[1] if covered and len(token_records) == count else None,
                  "outputTokens": token_totals[2] if covered and len(token_records) == count else None,
                  "reportedCostUsd": reported_cost,
                  "reportedCostPerOwnerAcceptedTaskUsd": reported_cost if native_quality["ownerAccepted"] else None,
                  "costBasis": "native_reported_USD_not_invoice; missing_is_unknown"},
        "nativeLedger": {k: number(ledger.get(k)) for k in
                         ("costCents", "inputTokens", "cachedInputTokens", "outputTokens", "runCount", "runtimeMs")},
        "runs": [{"id": r["id"], "agentId": r.get("agentId"), "status": r.get("status")} for r in runs],
    }


def format_scorecard(report):
    """Readable task scorecard; reads whitelisted fields without mutating report."""
    quality = report.get("quality") or {}
    timing = report.get("timing") or {}
    usage = report.get("usage") or {}

    def count(value):
        return "unknown" if value is None else str(value)

    def seconds(value):
        if value is None or isinstance(value, bool) or not isinstance(value, (int, float)):
            return "unknown"
        return f"{value / 1000:.3f}"

    def usd(value):
        if value is None or isinstance(value, bool) or not isinstance(value, (int, float)):
            return "unknown"
        return f"{value:.6f}"

    def tokens(value):
        return "unknown" if value is None else str(value)

    identifier = report.get("identifier") or report.get("issueId") or "unknown"
    status = report.get("status") or "unknown"
    independent = quality.get("independentParticipants")
    independent_text = "yes" if independent is True else "no" if independent is False else "unknown"
    run_count = report.get("runCount")

    lines = [
        f"Task: {identifier} ({status})",
        f"Owner accepted: {'yes' if quality.get('ownerAccepted') is True else 'no'}",
        f"Independent participants: {independent_text}",
        f"Gates: {count(quality.get('completedStages'))}/{count(quality.get('totalStages'))}",
        f"Runs: {count(run_count)}; failed: {count(report.get('failedRuns'))}; "
        f"retries: {count(report.get('recordedRetries'))}; "
        f"handoff cancellations: {count(report.get('handoffCancellations'))}",
        f"Runtime: {seconds(timing.get('runtimeMs'))} s; "
        f"coverage: {count(timing.get('coveredRuns'))}/{count(run_count)}",
        f"Execution window: {seconds(timing.get('executionWindowMs'))} s",
        f"Known runtime subtotal: {seconds(timing.get('knownRuntimeMs'))} s",
        f"Tokens: input {tokens(usage.get('inputTokens'))}; "
        f"cached {tokens(usage.get('cachedInputTokens'))}; "
        f"output {tokens(usage.get('outputTokens'))}; "
        f"coverage: {count(usage.get('coveredRuns'))}/{count(run_count)}",
        f"Reported cost: {usd(usage.get('reportedCostUsd'))} USD; "
        f"coverage: {count(usage.get('costCoveredRuns'))}/{count(run_count)}",
        f"Known subtotal: input {count(usage.get('knownInputTokens'))}; "
        f"cached {count(usage.get('knownCachedInputTokens'))}; "
        f"output {count(usage.get('knownOutputTokens'))}; "
        f"reported {usd(usage.get('knownReportedCostUsd'))} USD",
        f"Reported cost per owner-accepted task: "
        f"{usd(usage.get('reportedCostPerOwnerAcceptedTaskUsd'))} USD",
        "Caution: non-atomic readback; declared participant separation is not execution proof; "
        "native reported cost is not invoice evidence; "
        "correctness requires independent validation/review/QA.",
    ]
    return "\n".join(lines)
