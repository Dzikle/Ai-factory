"""Bounded provider-neutral evidence packs."""

import unittest

from milestone3.context import EvidenceUnavailable, SourceAdapter, build_evidence_pack


class FakeSource:
    def __init__(self, fresh=True):
        self.fresh = fresh

    def query(self, *, text, filters, max_hits, max_bytes):
        kind = "current" if self.fresh else "recalled"
        return [
            {"id": f"{kind}-1", "body": f"{kind} guidance " * 10},
            {"id": f"{kind}-2", "body": f"{kind} detail " * 10},
        ][:max_hits]

    def verify(self, item):
        body = item["body"]
        import hashlib

        return {
            "source": "fake",
            "source_system": "fake",
            "source_id": item["id"],
            "source_version": "v1",
            "content_sha256": hashlib.sha256(body.encode()).hexdigest(),
            "project_id": "ai-factory",
            "text": body,
            "citation": f"fake:{item['id']}",
            "source_uri": f"fake://docs/{item['id']}",
            "authority": "canonical" if self.fresh else "historical",
            "freshness": "fresh" if self.fresh else "stale",
        }


class BrokenSource:
    def query(self, *, text, filters, max_hits, max_bytes):
        raise RuntimeError("source is down")

    def verify(self, item):
        raise AssertionError("verify must not run when query fails")


def sample_request(max_bytes=900, max_tokens=225, required=("git-docs",), optional=("memory",)):
    queries = [
        {"source": source, "text": f"evidence about {source}", "filters": {"project_id": "ai-factory"},
         "max_hits": 2, "max_bytes": max_bytes, "required": True}
        for source in required
    ]
    queries += [
        {"source": source, "text": f"evidence about {source}", "filters": {"project_id": "ai-factory"},
         "max_hits": 2, "max_bytes": max_bytes, "required": False}
        for source in optional
    ]
    return {"project_id": "ai-factory", "total_budget": {"max_bytes": max_bytes, "max_tokens": max_tokens},
            "queries": queries}


class EvidencePackTests(unittest.TestCase):
    def test_pack_preserves_freshness_citations_and_total_budget(self):
        request = sample_request(max_bytes=900, max_tokens=225)
        pack = build_evidence_pack(request, {"git-docs": FakeSource(fresh=True), "memory": FakeSource(fresh=False)})
        self.assertLessEqual(pack["total_bytes"], 900)
        self.assertLessEqual(pack["estimated_tokens"], 225)
        self.assertTrue(all(item["citation"] and item["source_uri"] for item in pack["items"]))
        self.assertEqual("historical", pack["items"][-1]["authority"])
        self.assertEqual(64, len(pack["sha256"]))

    def test_required_source_failure_blocks_but_optional_failure_is_visible(self):
        with self.assertRaisesRegex(EvidenceUnavailable, "git-docs"):
            build_evidence_pack(sample_request(required=["git-docs"]), {"git-docs": BrokenSource()})
        pack = build_evidence_pack(sample_request(required=[], optional=["memory"]), {"memory": BrokenSource()})
        self.assertEqual([{"source": "memory", "status": "unavailable"}], pack["degraded_sources"])

    def test_pack_rejects_cross_project_results_and_deduplicates(self):
        class ForeignSource(FakeSource):
            def verify(self, item):
                row = super().verify(item)
                row["project_id"] = "another-project"
                return row

        pack = build_evidence_pack(sample_request(), {"git-docs": ForeignSource(), "memory": FakeSource()})
        self.assertTrue(all(item["project_id"] == "ai-factory" for item in pack["items"]))

        seen = pack["items"]
        again = build_evidence_pack(sample_request(), {"git-docs": FakeSource(), "memory": FakeSource()})
        keys = [(i["source_system"], i["source_id"], i["source_version"], i["content_sha256"]) for i in again["items"]]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertTrue(seen)


if __name__ == "__main__":
    unittest.main()
