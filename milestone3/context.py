"""Bounded provider-neutral evidence-pack composition.

Git and other canonical sources remain authoritative; OpenSearch is a
rebuildable retrieval projection and MemPalace is historical memory. Packs
carry freshness and authority labels, citations, budgets, explicit unknowns,
and a digest, and never fabricate evidence for unavailable sources.
"""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Protocol


_AUTHORITY_RANK = {"canonical": 0, "operational": 1, "projection": 2, "historical": 3}


class SourceAdapter(Protocol):
    def query(self, *, text: str, filters: dict, max_hits: int, max_bytes: int) -> list[dict]:
        """Return raw candidate rows without exceeding the per-query budget."""
        ...

    def verify(self, item: dict) -> dict:
        """Re-verify a row against its source; attach citation and freshness."""
        ...


class EvidenceUnavailable(RuntimeError):
    pass


def _request(request):
    if not isinstance(request, dict):
        raise ValueError("evidence request must be a mapping")
    project_id = request.get("project_id")
    if not isinstance(project_id, str) or not project_id.strip():
        raise ValueError("evidence request needs a nonempty project_id")
    budget = request.get("total_budget")
    if (
        not isinstance(budget, dict)
        or not isinstance(budget.get("max_bytes"), int)
        or budget["max_bytes"] < 1
        or not isinstance(budget.get("max_tokens"), int)
        or budget["max_tokens"] < 1
    ):
        raise ValueError("evidence request needs a positive total_budget")
    queries = request.get("queries")
    if not isinstance(queries, list) or not queries:
        raise ValueError("evidence request needs a nonempty queries list")
    for query in queries:
        if not isinstance(query, dict):
            raise ValueError("each evidence query must be a mapping")
        for field in ("source", "text"):
            if not isinstance(query.get(field), str) or not query[field].strip():
                raise ValueError(f"evidence query needs a nonempty {field}")
        if not isinstance(query.get("filters"), dict):
            raise ValueError("evidence query needs a filters mapping")
        for field in ("max_hits", "max_bytes"):
            if not isinstance(query.get(field), int) or query[field] < 1:
                raise ValueError(f"evidence query needs a positive {field}")
        if not isinstance(query.get("required"), bool):
            raise ValueError("evidence query needs a boolean required flag")
    return project_id, budget, queries


def build_evidence_pack(request, adapters):
    """Compose one budgeted pack across adapters without fabricating rows.

    Required-source failures raise EvidenceUnavailable; optional-source
    failures are recorded visibly in degraded_sources. Cross-project rows
    are rejected before budgeting, duplicates collapse on their provenance
    key, and canonical/current evidence is preferred over historical memory
    when the total budget binds.
    """
    project_id, budget, queries = _request(request)
    selected, degraded, seen = [], [], set()
    for query in queries:
        adapter = adapters.get(query["source"])
        if adapter is None:
            if query["required"]:
                raise EvidenceUnavailable(query["source"])
            degraded.append({"source": query["source"], "status": "unavailable"})
            continue
        try:
            rows = adapter.query(text=query["text"], filters=query["filters"],
                                 max_hits=query["max_hits"], max_bytes=query["max_bytes"])
        except Exception as exc:
            if query["required"]:
                raise EvidenceUnavailable(query["source"]) from exc
            degraded.append({"source": query["source"], "status": "unavailable"})
            continue
        used = 0
        for row in rows[: query["max_hits"]]:
            verified = adapter.verify(row)
            if verified.get("project_id") != project_id:
                continue
            key = (verified.get("source_system"), verified.get("source_id"),
                   verified.get("source_version"), verified.get("content_sha256"))
            if key in seen:
                continue
            seen.add(key)
            size = len(verified.get("text", "").encode("utf-8"))
            if used + size > query["max_bytes"]:
                break
            used += size
            selected.append(verified)
    selected.sort(key=lambda item: (_AUTHORITY_RANK.get(item.get("authority"), 99),))
    budgeted, used = [], 0
    for item in selected:
        size = len(item.get("text", "").encode("utf-8"))
        if used + size > budget["max_bytes"]:
            break
        budgeted.append(item)
        used += size
    canonical = json.dumps(budgeted, sort_keys=True, separators=(",", ":")).encode()
    return {
        "schemaVersion": 1,
        "items": budgeted,
        "degraded_sources": degraded,
        "total_bytes": used,
        "estimated_tokens": (used + 3) // 4,
        "sha256": hashlib.sha256(canonical).hexdigest(),
    }


class GitFileAdapter:
    """Bounded evidence adapter over one local Git checkout (canonical source).

    No network, no credentials. Files are ranked deterministically: filename
    matches first, then content matches, both in sorted path order.
    ``verify`` re-reads the file so a new run re-verifies current Git.
    """

    def __init__(self, root, *, project_id="ai-factory", revision=None):
        self.root = Path(root)
        self.project_id = project_id
        self.revision = revision or self._head_revision()

    def _head_revision(self):
        try:
            completed = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.root,
                                       capture_output=True, text=True, timeout=30, check=True)
        except (OSError, subprocess.SubprocessError) as exc:
            raise EvidenceUnavailable("git checkout has no readable HEAD") from exc
        return completed.stdout.strip()

    def query(self, *, text, filters, max_hits, max_bytes):
        prefixes = filters.get("path_prefix", [])
        if isinstance(prefixes, str):
            prefixes = [prefixes]
        suffixes = filters.get("suffix", [])
        if isinstance(suffixes, str):
            suffixes = [suffixes]
        words = [word.lower() for word in text.split() if len(word) > 2]
        ranked = []
        for path in sorted(self.root.rglob("*")):
            if not path.is_file():
                continue
            try:
                relative = path.relative_to(self.root).as_posix()
            except ValueError:
                continue
            if prefixes and not any(relative == prefix or relative.startswith(prefix.rstrip("/") + "/")
                                    for prefix in prefixes):
                continue
            if suffixes and not any(relative.endswith(suffix) for suffix in suffixes):
                continue
            try:
                body = path.read_bytes()
                content = body.decode("utf-8")
            except (OSError, ValueError):
                continue
            lowered_name, lowered_body = relative.lower(), content.lower()
            score = sum(2 for word in words if word in lowered_name) + sum(1 for word in words if word in lowered_body)
            ranked.append((score, relative, body))
        ranked.sort(key=lambda row: (-row[0], row[1]))
        rows, used = [], 0
        for _, relative, body in ranked[:max_hits]:
            if used + len(body) > max_bytes:
                continue
            used += len(body)
            rows.append({"path": relative, "body": body})
            if len(rows) >= max_hits:
                break
        return rows

    def verify(self, item):
        target = self.root / item["path"]
        try:
            body = target.read_bytes()
            content = body.decode("utf-8")
        except (OSError, ValueError) as exc:
            raise EvidenceUnavailable(f"git file is unreadable: {item.get('path')}") from exc
        digest = hashlib.sha256(body).hexdigest()
        try:
            current = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.root,
                                     capture_output=True, text=True, timeout=30, check=True).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            current = self.revision
        return {
            "source": "git",
            "source_system": "git",
            "source_id": item["path"],
            "source_version": current,
            "content_sha256": digest,
            "project_id": self.project_id,
            "text": content,
            "citation": f"git:{current[:12]}:{item['path']}",
            "source_uri": f"git://ai-factory/{current}/{item['path']}",
            "authority": "canonical",
            "freshness": "fresh" if current == self.revision else "stale",
        }


def default_wave_request(program, wave, *, project_id="ai-factory"):
    """Bounded local-Git evidence request for one program wave."""
    budget = wave["context_budget"]
    return {
        "project_id": project_id,
        "total_budget": {"max_bytes": budget["max_bytes"], "max_tokens": budget["max_tokens"]},
        "queries": [
            {"source": "git", "text": f"{wave['id']} self-enhancement lifecycle",
             "filters": {"path_prefix": ["docs/superpowers/", "autonomy/"]},
             "max_hits": 8, "max_bytes": min(budget["max_bytes"], 48000), "required": True},
        ],
    }
