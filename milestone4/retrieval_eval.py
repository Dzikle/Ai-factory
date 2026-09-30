"""Read-only judged retrieval checks for the existing Git-documents projection."""

import argparse
import json
import math
import os
from pathlib import Path
import re
import sys

from milestone1.opensearch_projection import HttpClient


FIELDS = ["path", "project_id", "repository_id", "source_system", "status",
          "canonical", "source_revision", "source_id", "content_sha256"]


def _path(value):
    return (isinstance(value, str) and 1 <= len(value) <= 512 and "\\" not in value
            and ":" not in value and all(part not in {"", ".", ".."} for part in value.split("/")))


def _validate(suite, expected_revision, k):
    if (not isinstance(expected_revision, str) or not re.fullmatch(r"[a-f0-9]{40}", expected_revision)
            or type(k) is not int or not 1 <= k <= 10):
        raise ValueError("Expected revision and top-k bound are required")
    if not isinstance(suite, dict) or type(suite.get("schemaVersion")) is not int or suite["schemaVersion"] != 1:
        raise ValueError("Invalid retrieval suite")
    project, repository, cases = (suite.get("projectId"), suite.get("repositoryId"),
                                  suite.get("cases"))
    if not all(isinstance(item, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", item)
               for item in (project, repository)) or not isinstance(cases, list) or not 1 <= len(cases) <= 32:
        raise ValueError("Invalid retrieval scope or case count")
    seen = set()
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str) or not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", case["id"]
        ) or case["id"] in seen:
            raise ValueError("Invalid or duplicate retrieval case")
        seen.add(case["id"])
        query, relevant = case.get("query"), case.get("relevantPaths")
        if not isinstance(query, str) or not query.strip() or len(query) > 240:
            raise ValueError("Invalid bounded retrieval query")
        if (not isinstance(relevant, list) or not 1 <= len(relevant) <= 8
                or not all(_path(path) for path in relevant) or len(set(relevant)) != len(relevant)):
            raise ValueError("Each case requires distinct relevant paths")
    thresholds = suite.get("thresholds")
    if thresholds is not None and (
        not isinstance(thresholds, dict) or set(thresholds) != {"recallAtK", "meanReciprocalRank", "staleRelevantHits"}
        or any(type(thresholds.get(name)) not in (int, float) or not math.isfinite(thresholds[name])
               or not 0 <= thresholds[name] <= 1 for name in ("recallAtK", "meanReciprocalRank"))
        or type(thresholds.get("staleRelevantHits")) is not int or not 0 <= thresholds["staleRelevantHits"] <= 320
    ):
        raise ValueError("Invalid retrieval promotion thresholds")
    return project, repository, cases, thresholds


def evaluate(reader, suite, *, expected_revision, k=5):
    """Compare judged paths with filtered results; no contents or credentials leave the report."""
    project, repository, cases, thresholds = _validate(suite, expected_revision, k)
    reports = []
    total_relevant = total_found = reciprocal_rank = stale_relevant = 0
    for case in cases:
        body = {"size": k, "_source": FIELDS, "query": {"bool": {
            "filter": [{"term": {"project_id": project}}, {"term": {"repository_id": repository}},
                       {"term": {"source_system": "git"}}, {"term": {"status": "canonical"}},
                       {"term": {"canonical": True}}],
            "must": [{"multi_match": {"query": case["query"], "fields": ["title^3", "content"]}}],
        }}}
        response = reader.request("POST", "/ai_factory_docs/_search", body)
        container = response.get("hits") if isinstance(response, dict) else None
        hits = container.get("hits") if isinstance(container, dict) else None
        if not isinstance(hits, list) or len(hits) > k:
            raise ValueError("Malformed or unbounded retrieval response")
        found, seen, first_rank, stale = set(), set(), None, 0
        for rank, hit in enumerate(hits, 1):
            doc = hit.get("_source") if isinstance(hit, dict) else None
            if (not isinstance(doc, dict) or not _path(doc.get("path"))
                    or doc.get("project_id") != project or doc.get("repository_id") != repository
                    or doc.get("source_system") != "git" or doc.get("status") != "canonical"
                    or doc.get("canonical") is not True):
                raise ValueError("Retrieval result violates source scope")
            path = doc["path"]
            if path in seen:
                raise ValueError("Retrieval returned duplicate paths")
            seen.add(path)
            if (doc.get("source_id") != repository + ":" + path
                    or not isinstance(doc.get("source_revision"), str)
                    or not re.fullmatch(r"[a-f0-9]{40}", doc["source_revision"])
                    or not isinstance(doc.get("content_sha256"), str)
                    or not re.fullmatch(r"[a-f0-9]{64}", doc["content_sha256"])):
                raise ValueError("Retrieval result has invalid provenance")
            if path in case["relevantPaths"]:
                found.add(path)
                first_rank = rank if first_rank is None else first_rank
                stale += doc["source_revision"] != expected_revision
        total_relevant += len(case["relevantPaths"])
        total_found += len(found)
        reciprocal_rank += 1 / first_rank if first_rank is not None else 0
        stale_relevant += stale
        reports.append({"id": case["id"], "relevantFound": len(found),
                        "relevantExpected": len(case["relevantPaths"]),
                        "firstRelevantRank": first_rank, "staleRelevantHits": stale,
                        "returnedPaths": [hit["_source"]["path"] for hit in hits]})
    recall, mrr = total_found / total_relevant, reciprocal_rank / len(cases)
    passed = (recall >= thresholds["recallAtK"] and mrr >= thresholds["meanReciprocalRank"]
              and stale_relevant <= thresholds["staleRelevantHits"]) if thresholds is not None else None
    return {"schemaVersion": 1, "projectId": project, "repositoryId": repository,
            "expectedRevision": expected_revision, "k": k, "casesEvaluated": len(cases),
            "recallAtK": recall, "meanReciprocalRank": mrr,
            "staleRelevantHits": stale_relevant, "passesThresholds": passed, "cases": reports}


def run(suite_path, expected_revision, *, environ, k=5, insecure_localhost=False):
    """Use one non-admin reader; credentials never enter the result or suite."""
    required = ("AIF_DOCS_URL", "AIF_DOCS_READER_USER", "AIF_DOCS_READER_PASSWORD")
    if any(not environ.get(name) for name in required):
        raise ValueError("OpenSearch reader credentials are required")
    if environ["AIF_DOCS_READER_USER"].lower() == "admin":
        raise ValueError("Retrieval evaluation requires a non-admin reader")
    path = Path(suite_path)
    if path.stat().st_size > 64_000:
        raise ValueError("Retrieval suite exceeds its byte bound")
    suite = json.loads(path.read_text(encoding="utf-8"))
    reader = HttpClient(environ["AIF_DOCS_URL"], environ["AIF_DOCS_READER_USER"],
                        environ["AIF_DOCS_READER_PASSWORD"], insecure_localhost=insecure_localhost)
    return evaluate(reader, suite, expected_revision=expected_revision, k=k)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--expect-revision", required=True, help="full committed Git revision")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--insecure-localhost", action="store_true", help="self-signed local test cluster only")
    args = parser.parse_args(argv)
    try:
        result = run(args.suite, args.expect_revision, environ=os.environ,
                     k=args.top_k, insecure_localhost=args.insecure_localhost)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["passesThresholds"] is not False else 2
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError):
        print("Retrieval evaluation failed; check suite, reader scope and index privately.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
