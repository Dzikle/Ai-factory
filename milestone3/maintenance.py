"""Deferred findings, exact knowledge patches, and recoverable cleanup.

Knowledge maintenance is separate from accepting a code candidate. Patches
require current source hashes and stay inside the assigned workspace;
cleanup only quarantines expired, unreferenced, factory-owned resources and
never recursively deletes.
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def finding_fingerprint(finding):
    """Stable identity for equivalent normalized finding evidence."""
    value = {key: finding[key] for key in ("project_id", "affected_components", "summary")}
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def deduplicate_findings(findings):
    """Collapse equivalent findings while preserving every origin task ID."""
    merged = {}
    for finding in findings:
        digest = finding_fingerprint(finding)
        if digest not in merged:
            merged[digest] = dict(finding, origin_task_ids=list(finding.get("origin_task_ids") or []),
                                  fingerprint=digest)
        else:
            known = set(merged[digest]["origin_task_ids"])
            for task_id in finding.get("origin_task_ids") or []:
                if task_id not in known:
                    merged[digest]["origin_task_ids"].append(task_id)
                    known.add(task_id)
    return list(merged.values())


def _validated_patch(patch):
    if not isinstance(patch, dict):
        raise ValueError("knowledge patch must be a mapping")
    path = patch.get("path")
    if not isinstance(path, str) or not path or path.startswith("/"):
        raise ValueError(f"patch path must be a relative path, got {path!r}")
    expected = patch.get("expected_sha256")
    if not isinstance(expected, str) or len(expected) != 64:
        raise ValueError("patch expected_sha256 must be a SHA-256 hex digest")
    for field in ("old_text", "new_text"):
        if not isinstance(patch.get(field), str) or not patch[field]:
            raise ValueError(f"patch {field} must be nonempty text")
    return patch


def preview_patch(root, patch):
    """Dry-run a knowledge patch without writing; reject stale or escaped targets."""
    patch = _validated_patch(patch)
    base = Path(root).resolve(strict=True)
    target = (base / patch["path"]).resolve()
    if target != base and base not in target.parents:
        raise ValueError("patch target is outside assigned root")
    try:
        original = target.read_bytes()
    except OSError as exc:
        raise ValueError(f"knowledge source unreadable: {patch['path']}") from exc
    if hashlib.sha256(original).hexdigest() != patch["expected_sha256"]:
        raise ValueError("knowledge source changed")
    text = original.decode("utf-8")
    if text.count(patch["old_text"]) != 1:
        raise ValueError("patch anchor must match exactly once")
    updated = text.replace(patch["old_text"], patch["new_text"], 1)
    return {"path": patch["path"], "before_sha256": patch["expected_sha256"],
            "after_sha256": hashlib.sha256(updated.encode()).hexdigest(), "updated_text": updated}


def apply_patch(root, patch, preview):
    """Apply a previously previewed patch; write only inside the workspace.

    The preview must still match current source state, otherwise the caller
    must re-preview. This never commits, publishes, or reindexes.
    """
    patch = _validated_patch(patch)
    base = Path(root).resolve(strict=True)
    target = (base / patch["path"]).resolve()
    if target != base and base not in target.parents:
        raise ValueError("patch target is outside assigned root")
    try:
        current = target.read_bytes()
    except OSError as exc:
        raise ValueError(f"knowledge source unreadable: {patch['path']}") from exc
    if hashlib.sha256(current).hexdigest() != preview.get("before_sha256"):
        raise ValueError("source changed since preview; re-preview before applying")
    fresh = preview_patch(root, patch)
    if fresh["after_sha256"] != preview.get("after_sha256"):
        raise ValueError("preview does not match current source; re-preview before applying")
    target.write_text(preview["updated_text"], encoding="utf-8")
    return {"path": patch["path"], "before_sha256": preview["before_sha256"],
            "after_sha256": preview["after_sha256"],
            "bytes_written": len(preview["updated_text"].encode("utf-8"))}


def _expires_at(value):
    try:
        moment = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"resource has an invalid expires_at: {value!r}") from exc
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment


def plan_reclamation(resources, *, now, owned_root):
    """Split factory-owned resources into quarantine candidates and retained rows.

    A resource is reclaimable only when it resolves below the declared
    factory-owned root and is expired, reproducible or recoverable,
    unreferenced, and not protected. Unknown ownership and live references
    are always retained with an explicit reason.
    """
    base = Path(owned_root).resolve(strict=True)
    quarantine, retained = [], []
    for record in resources:
        path = (base / record["path"]).resolve() if not str(record.get("path", "")).startswith("/") else Path(record["path"])
        if path != base and base not in path.parents:
            retained.append({**record, "retain_reason": "foreign"})
            continue
        if _expires_at(record["expires_at"]) > now:
            retained.append({**record, "retain_reason": "active"})
            continue
        if record.get("referenced"):
            retained.append({**record, "retain_reason": "referenced"})
            continue
        if record.get("protected"):
            retained.append({**record, "retain_reason": "protected"})
            continue
        if not (record.get("reproducible") or record.get("recoverable")):
            retained.append({**record, "retain_reason": "irreproducible"})
            continue
        quarantine.append(record)
    return {"quarantine": quarantine, "retained": retained}


def quarantine_resources(owned_root, records):
    """Atomically rename approved paths into quarantine; never delete."""
    base = Path(owned_root).resolve(strict=True)
    digest = hashlib.sha256(json.dumps(sorted(r["id"] for r in records),
                                       separators=(",", ":")).encode()).hexdigest()[:16]
    yard = base / "quarantine" / digest
    yard.mkdir(parents=True, exist_ok=True)
    moved = []
    for record in records:
        source = (base / record["path"]).resolve()
        if source != base and base not in source.parents:
            raise ValueError(f"quarantine target is outside owned root: {record['id']}")
        if not source.exists():
            raise ValueError(f"quarantine target is missing: {record['id']}")
        destination = yard / record["id"]
        if destination.exists():
            raise ValueError(f"quarantine target already exists: {record['id']}")
        os.replace(source, destination)
        moved.append({"id": record["id"], "from": record["path"], "to": destination.relative_to(base).as_posix()})
    (yard / "manifest.json").write_text(json.dumps({"digest": digest, "moved": moved}, indent=2) + "\n",
                                         encoding="utf-8")
    return {"digest": digest, "directory": str(yard), "moved": moved}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    preview = commands.add_parser("maintenance-preview",
                                  help="dry-run a knowledge patch without writing anything")
    preview.add_argument("--root", required=True, help="assigned workspace root the patch must stay inside")
    preview.add_argument("--patch", required=True, help="patch JSON with path, expected_sha256, old_text, new_text")
    args = parser.parse_args(argv)
    try:
        patch = json.loads(Path(args.patch).read_text(encoding="utf-8-sig"))
        print(json.dumps(preview_patch(args.root, patch), indent=2))
        return 0
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
