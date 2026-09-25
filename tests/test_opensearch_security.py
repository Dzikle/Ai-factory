"""The Git projection may not gain broader OpenSearch privileges by accident."""

import unittest

from milestone1.opensearch_security import docs_reader_role, docs_writer_role


class DocsProjectionSecurityTests(unittest.TestCase):
    def test_reader_role_is_limited_to_document_read_alias_and_index(self) -> None:
        role = docs_reader_role()
        self.assertEqual([], role["cluster_permissions"])
        self.assertEqual(1, len(role["index_permissions"]))
        permission = role["index_permissions"][0]
        self.assertEqual(["ai_factory_docs_v1", "ai_factory_docs"], permission["index_patterns"])
        self.assertEqual(
            ["indices:data/read/search"],
            permission["allowed_actions"],
        )
        self.assertEqual([], role["tenant_permissions"])

    def test_writer_role_cannot_read_or_administer_other_indexes(self) -> None:
        role = docs_writer_role()
        self.assertEqual(["indices:data/write/bulk"], role["cluster_permissions"])
        self.assertEqual(1, len(role["index_permissions"]))
        permission = role["index_permissions"][0]
        self.assertEqual(["ai_factory_docs_v1", "ai_factory_docs_write"], permission["index_patterns"])
        self.assertEqual(["indices:data/write/bulk*", "indices:data/write/index"], permission["allowed_actions"])
        self.assertEqual([], role["tenant_permissions"])


if __name__ == "__main__":
    unittest.main()
