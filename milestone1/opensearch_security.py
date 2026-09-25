"""Least-privilege OpenSearch Security role templates for Git documents.

An administrator applies these roles and binds separate runtime principals.
The projector itself receives only the resulting reader/writer credentials.
"""

from __future__ import annotations

from .opensearch_projection import DOCS_INDEX, DOCS_READ_ALIAS, DOCS_WRITE_ALIAS


def docs_reader_role() -> dict:
    return {
        "cluster_permissions": [],
        "index_permissions": [{
            # OpenSearch resolves aliases to the physical index for action checks.
            "index_patterns": [DOCS_INDEX, DOCS_READ_ALIAS],
            "allowed_actions": ["indices:data/read/search"],
        }],
        "tenant_permissions": [],
    }


def docs_writer_role() -> dict:
    return {
        # The cluster bulk action is required for the _bulk entry point;
        # per-item permissions remain scoped to the docs index below.
        "cluster_permissions": ["indices:data/write/bulk"],
        "index_permissions": [{
            "index_patterns": [DOCS_INDEX, DOCS_WRITE_ALIAS],
            "allowed_actions": ["indices:data/write/bulk*", "indices:data/write/index"],
        }],
        "tenant_permissions": [],
    }
