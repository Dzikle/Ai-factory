"""Deterministic outcome reports projected from authoritative records.

Reports accept only validated fields and render sections in one fixed order,
so the same records always reproduce the same Markdown. Nothing is inferred:
correctness comes from the linked verification digest and independent
review, and missing costs stay missing.
"""

import re


SECTIONS = ("Objective", "Candidate", "Changes", "Verification", "Independent Review",
            "External Evidence", "Authorization", "Knowledge Impact", "Deferred Findings",
            "Metrics", "Unresolved Items", "Rollback", "Next Disposition")

REPORT_KEYS = {"schemaVersion", "objective", "candidate", "changes", "verification", "review",
               "external_evidence", "authorization", "knowledge_impact", "deferred_findings",
               "metrics", "unresolved_items", "rollback", "next_disposition", "status"}
_SHA1_RE = re.compile(r"[0-9a-f]{40}\Z")
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")


def validate_candidate_lineage(report):
    """Every evidence record must name the same candidate commit."""
    expected = report["candidate"]["commit"]
    errors = []
    for label in ("verification", "review"):
        if report[label]["candidate_commit"] != expected:
            errors.append(f"{label} candidate mismatch")
    for row in report.get("external_evidence", []):
        if row["candidate_commit"] != expected:
            errors.append("external evidence candidate mismatch")
    return errors


def validate_outcome_report(report):
    """Accept only validated fields; raise on any problem, return [] when clean."""
    if not isinstance(report, dict):
        raise ValueError("outcome report must be a mapping")
    unknown = set(report) - REPORT_KEYS
    if unknown:
        raise ValueError(f"outcome report has unknown fields: {sorted(unknown)}")
    missing = REPORT_KEYS - set(report)
    if missing:
        raise ValueError(f"outcome report is missing fields: {sorted(missing)}")
    errors = []
    candidate = report["candidate"]
    if not _SHA1_RE.fullmatch(candidate.get("commit", "")) or not _SHA1_RE.fullmatch(candidate.get("tree", "")):
        errors.append("candidate needs 40-hex commit and tree")
    if report["knowledge_impact"] not in ("none", "verify", "update"):
        errors.append(f"knowledge_impact must be none, verify, or update, got {report['knowledge_impact']!r}")
    if report["status"] not in ("accepted", "blocked", "failed"):
        errors.append(f"status must be accepted, blocked, or failed, got {report['status']!r}")
    if report["review"].get("verdict") not in ("approve", "request_changes", "reject"):
        errors.append("review needs an approve, request_changes, or reject verdict")
    errors.extend(validate_candidate_lineage(report))
    if errors:
        raise ValueError(f"outcome report is invalid: {'; '.join(errors)}")
    return []


def _lines(title, body_lines):
    return [f"## {title}", ""] + list(body_lines) + [""]


def render_markdown(report):
    """Render validated report fields in the fixed canonical section order."""
    validate_outcome_report(report)
    candidate = report["candidate"]
    verification = report["verification"]
    review = report["review"]
    out = ["# Self-Enhancement Outcome Report", ""]
    out += _lines("Objective", [report["objective"]])
    out += _lines("Candidate", [f"commit: {candidate['commit']}", f"tree: {candidate['tree']}",
                                f"status: {report['status']}"])
    out += _lines("Changes", [f"- {row.get('path', '?')}: {row.get('summary', '')}"
                              for row in report["changes"]] or ["(no changes)"])
    out += _lines("Verification", [f"candidate: {verification['candidate_commit']}",
                                   f"status: {verification['status']}",
                                   f"failed: {', '.join(verification.get('failed_checks', [])) or '(none)'}",
                                   f"missing: {', '.join(verification.get('missing_checks', [])) or '(none)'}"])
    out += _lines("Independent Review", [f"candidate: {review['candidate_commit']}",
                                         f"verdict: {review['verdict']}",
                                         f"reviewer: {review.get('reviewer', 'unknown')}"])
    out += _lines("External Evidence", [
        f"- {row.get('kind', '?')}: {row.get('status', '?')} ({row.get('candidate_commit', '?')}) {row.get('uri', '')}"
        for row in report["external_evidence"]] or ["(none)"])
    authorization = report["authorization"]
    out += _lines("Authorization", [f"digest: {authorization.get('digest', 'unknown')}",
                                    f"scope: {authorization.get('scope', 'unknown')}"])
    out += _lines("Knowledge Impact", [report["knowledge_impact"]])
    out += _lines("Deferred Findings", [
        f"- {row.get('summary', '')} (severity: {row.get('severity', 'unknown')})"
        for row in report["deferred_findings"]] or ["(none)"])
    metrics = report["metrics"]
    out += _lines("Metrics", [f"{key}: {value}" for key, value in sorted(metrics.items())])
    out += _lines("Unresolved Items", [f"- {item}" if isinstance(item, str) else f"- {item.get('summary', item)}"
                                       for item in report["unresolved_items"]] or ["(none)"])
    out += _lines("Rollback", [report["rollback"]])
    out += _lines("Next Disposition", [report["next_disposition"]])
    return "\n".join(out)
