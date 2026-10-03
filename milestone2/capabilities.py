"""Capability health aggregation and admission decisions.

Paperclip remains the runtime authority. This module only aggregates
externally supplied component health probes against the Git-owned provider
manifests and reports ready/degraded/blocked. It never prints credentials,
never calls paid model providers, and never grants runtime authority.
"""

import argparse
import json
import sys
from pathlib import Path

import yaml


DEFAULT_MANIFESTS = Path(__file__).resolve().parents[1] / "autonomy" / "capabilities" / "providers.v1.yaml"


def load_manifests(path):
    try:
        value = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"Cannot read capability manifests from {path}") from error
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError(f"Expected a list of capability manifests in {path}")
    return value


def _healthy(manifest, health):
    return manifest["status"] == "active" and health.get(manifest["health_probe"]) == "healthy"


def assess(required, optional, manifests, health):
    """Aggregate health into ready/degraded/blocked without side effects.

    Unknown capabilities raise instead of falling back to prompt permission;
    disabled manifests are never admitted even when their probe is healthy.
    """
    catalog = {item["capability"]: item for item in manifests}
    unknown = (set(required) | set(optional)) - set(catalog)
    if unknown:
        raise ValueError(f"unknown capability: {sorted(unknown)}")
    unavailable_required = sorted(c for c in required if not _healthy(catalog[c], health))
    unavailable_optional = sorted(c for c in optional if not _healthy(catalog[c], health))
    status = "blocked" if unavailable_required else "degraded" if unavailable_optional else "ready"
    return {
        "schemaVersion": 1,
        "status": status,
        "unavailable_required": unavailable_required,
        "unavailable_optional": unavailable_optional,
        "providers": sorted({catalog[c]["provider"] for c in required + optional}),
    }


def read_probes(path, manifests):
    """Read component-owned probe results, keeping only known probe names.

    Only validated status tokens enter the result; unknown keys and
    non-status values never propagate, so credentials in the probe file
    cannot leak into aggregates or text views.
    """
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as error:
        raise ValueError(f"Cannot read probe results from {path}") from error
    if isinstance(value, dict) and isinstance(value.get("probes"), dict):
        value = value["probes"]
    if not isinstance(value, dict):
        raise ValueError(f"Expected a probe mapping in {path}")
    known = {item["health_probe"] for item in manifests}
    health = {}
    for name in sorted(known):
        if name in value:
            status = value[name]
            if not isinstance(status, str) or not status.strip():
                raise ValueError(f"probe {name} has no readable status")
            health[name] = status.strip()
    return health


def diagnose(required, optional, manifests, health):
    """Aggregate health plus normalized per-probe statuses for reporting."""
    assessment = assess(required, optional, manifests, health)
    probes = {
        name: ("healthy" if health.get(name) == "healthy" else "unhealthy")
        for name in sorted({item["health_probe"] for item in manifests})
    }
    return {"probes": probes, "assessment": assessment}


def format_text(report):
    assessment = report["assessment"]
    lines = [f"capability health: {assessment['status']}"]
    lines.append(f"providers: {', '.join(assessment['providers']) or '(none)'}")
    lines.append(f"required unavailable: {', '.join(assessment['unavailable_required']) or '(none)'}")
    lines.append(f"optional unavailable: {', '.join(assessment['unavailable_optional']) or '(none)'}")
    for name, status in report["probes"].items():
        lines.append(f"{name}: {status}")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifests", default=str(DEFAULT_MANIFESTS), help="Git-owned provider manifests")
    commands = parser.add_subparsers(dest="command", required=True)
    doctor = commands.add_parser("doctor", help="aggregate component probe results into one diagnostic view")
    doctor.add_argument("--probes", required=True, help="JSON probe results file or stdin marker '-'; {'probes': {...}} or a bare mapping")
    doctor.add_argument("--required", action="append", default=[], help="required capability (repeatable)")
    doctor.add_argument("--optional", action="append", default=[], help="optional capability (repeatable)")
    doctor.add_argument("--output", default=None, help="write the machine-readable aggregate JSON here")
    args = parser.parse_args(argv)
    try:
        manifests = load_manifests(args.manifests)
        if args.probes == "-":
            raw = sys.stdin.read()
            try:
                value = json.loads(raw)
            except ValueError as error:
                raise ValueError("Cannot read probe results from stdin") from error
            known = {item["health_probe"] for item in manifests}
            health = {n: v.strip() for n, v in value.get("probes", value).items()
                      if n in known and isinstance(v, str) and v.strip()}
        else:
            health = read_probes(args.probes, manifests)
        required = list(args.required) or [item["capability"] for item in manifests if item["status"] == "active"]
        report = diagnose(required, list(args.optional), manifests, health)
        if args.output:
            Path(args.output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        else:
            print(json.dumps(report, indent=2))
        print(format_text(report), end="")
        return 0
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
