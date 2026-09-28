"""Explicit local-service smoke; serial writer, no task dispatch or automatic retry."""

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import time

from milestone2.task import read_object
from .cli import connect_memory, external_verifier, search_client
from .memory import digest, git_source_is_current, project, recall


def main():
    import os
    state = os.environ.get("AIF_PAPERCLIP_STATE")
    fixture = read_object(Path(__file__).parent / "fixtures/pinned-tests-lesson.json")
    verify = external_verifier(state)
    assert verify is not None
    assert all(git_source_is_current(".", s) if s["source_system"] == "git" else verify(s)
               for s in fixture["record"]["source_refs"])
    store = connect_memory(writable=True)
    reader, writer = search_client("READER"), search_client("WRITER")
    started = time.monotonic()
    try:
        # This is the earlier, incomplete wording of the same reviewed experience,
        # retained only to characterize real supersession and stale projection.
        previous = deepcopy(fixture)
        previous["record"].update(memory_id="lesson-python-test-dependencies-v1", supersedes=[])
        previous["content"] = "AIF-47 full-suite import failures exposed missing jsonschema. Verify current Git and the pinned test environment before diagnosing application defects. This earlier wording does not cover the later PyYAML failure."
        sha = digest(previous["content"].encode())
        previous["record"].update(content_sha256=sha, content_ref="sha256:" + sha)
        # Do not replay capture after supersession: get the source-filtered earlier
        # record and its logical parent ID, including MemPalace chunk handling.
        found = store.call("mempalace_search", {"query": "test environment", "limit": 10,
                           "wing": "ai-factory", "room": "engineering-lessons",
                           "source_file": "memory:lesson-python-test-dependencies-v1", "max_distance": 0})
        old_id = next((r.get("parent_drawer_id", r["drawer_id"]) for r in found.get("results", [])), None)
        if old_id is None:
            old_id = store.remember(previous)
        store.get(old_id)
        # Deliberately leave the old ACTIVE projection behind, even on replay.
        project(writer, old_id, previous)
        new_id = store.remember(fixture)
        assert store.remember(fixture) == new_id
        project(writer, new_id, fixture)
        updated = store.supersede(old_id, new_id)
        assert store.supersede(old_id, new_id) == updated
        assert updated["record"]["status"] == "superseded"
        search = store.call("mempalace_search", {"query": "Python test dependencies jsonschema PyYAML",
                           "limit": 3, "wing": "ai-factory", "room": "engineering-lessons",
                           "source_file": "memory:lesson-python-test-dependencies-v2", "max_distance": 0})
        assert search.get("results")
        options = dict(cwd=".", project_id="ai-factory", role="developer", query="Python test dependencies",
                       verify_external=verify, now=datetime.now(timezone.utc))
        used = recall(store, reader, **options)
        assert used["status"] == "used" and used["memories"][0]["drawer_id"] == new_id
        assert recall(store, reader, **{**options, "role": "reviewer"})["prompt"] == ""
        assert recall(store, reader, **{**options, "project_id": "other-project"})["prompt"] == ""
        class OnlyPrevious:
            def request(self, method, path, body):
                body = deepcopy(body)
                body["query"]["bool"]["filter"].append({"term": {"source_id": "lesson-python-test-dependencies-v1"}})
                return reader.request(method, path, body)
        assert recall(store, OnlyPrevious(), **{**options, "query": "v1"})["prompt"] == ""
        assert recall(store, reader, **{**options, "max_bytes": 100})["prompt"] == ""
        print(json.dumps({"status": "passed", "old_drawer_id": old_id, "drawer_id": new_id,
                          "supersession": "idempotent; stale active projection not used",
                          "semantic_search_results": len(search["results"]), "recall": used,
                          "elapsed_seconds": round(time.monotonic() - started, 3)}, indent=2))
        return 0
    finally:
        store.client.close()


if __name__ == "__main__":
    raise SystemExit(main())
