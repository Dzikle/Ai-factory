"""Safe verification-contract execution and compact digest generation.

Raw stdout/stderr stay available as artifacts with the caller; the digest
carries only hashes and bounded excerpts so compact digests can enter model
context. Execution rejects shell strings, absolute or escaping per-check
working directories, duplicate check IDs, over-long timeouts, and
environment values outside an explicit allowlist.
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ENV_ALLOWLIST = ("PYTHONPATH",)
CHECK_KEYS = {"id", "argv", "timeoutSeconds", "required", "cwd", "env"}
CONTRACT_KEYS = {"profile", "candidate_commit", "checks"}
_SHA1_RE = re.compile(r"[0-9a-f]{40}\Z")
_DOC_SUFFIXES = (".md", ".rst", ".txt")


def load_profiles(path):
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as error:
        raise ValueError(f"Cannot read verification profiles from {path}") from error
    profiles = value.get("profiles") if isinstance(value, dict) else None
    if not isinstance(profiles, dict) or not profiles:
        raise ValueError(f"Expected a profiles mapping in {path}")
    return profiles


def resolve_profile(profiles, name, *, changed_paths):
    """Select a profile, enforcing reduced-check eligibility.

    Reduced verification is valid only when every changed path is
    documentation and the wave explicitly selects the docs profile.
    """
    try:
        profile = profiles[name]
    except (KeyError, TypeError) as exc:
        raise ValueError(f"unknown verification profile: {name!r}") from exc
    if name == "ai-factory-docs":
        offenders = [path for path in changed_paths
                     if not (path.startswith("docs/") or path.endswith(_DOC_SUFFIXES))]
        if offenders:
            raise ValueError(f"ai-factory-docs requires documentation-only changes; saw {offenders}")
    return profile


def validate_contract(contract):
    """Reject unsafe or malformed contracts before anything executes."""
    if not isinstance(contract, dict) or set(contract) != CONTRACT_KEYS:
        raise ValueError("verification contract needs exactly profile, candidate_commit, and checks")
    if not isinstance(contract["profile"], str) or not contract["profile"]:
        raise ValueError("verification contract needs a nonempty profile name")
    if not isinstance(contract["candidate_commit"], str) or not _SHA1_RE.fullmatch(contract["candidate_commit"]):
        raise ValueError("verification contract needs a 40-hex candidate_commit")
    checks = contract["checks"]
    if not isinstance(checks, list) or not checks:
        raise ValueError("verification contract needs a nonempty checks list")
    seen = set()
    for check in checks:
        if not isinstance(check, dict) or set(check) - CHECK_KEYS or "id" not in check or "argv" not in check:
            raise ValueError(f"verification check needs id/argv with optional {sorted(CHECK_KEYS)}")
        if check["id"] in seen:
            raise ValueError(f"duplicate verification check ID: {check['id']!r}")
        seen.add(check["id"])
        argv = check["argv"]
        if isinstance(argv, str) or not isinstance(argv, list) or not argv:
            raise ValueError(f"check {check['id']}: argv must be a list, never a shell string")
        if any(not isinstance(part, str) or not part or len(part) > 1024 for part in argv):
            raise ValueError(f"check {check['id']}: argv parts must be bounded nonempty strings")
        timeout = check.get("timeoutSeconds", 300)
        if not isinstance(timeout, int) or isinstance(timeout, bool) or not 1 <= timeout <= 1800:
            raise ValueError(f"check {check['id']}: timeoutSeconds must be an integer of 1..1800")
        if not isinstance(check.get("required", True), bool):
            raise ValueError(f"check {check['id']}: required must be boolean")
        cwd = check.get("cwd")
        if cwd is not None:
            if not isinstance(cwd, str) or cwd.startswith("/") or cwd.startswith("\\"):
                raise ValueError(f"check {check['id']}: cwd must be relative, got {cwd!r}")
            if ".." in Path(cwd).parts:
                raise ValueError(f"check {check['id']}: cwd must not escape, got {cwd!r}")
        env = check.get("env")
        if env is not None:
            if not isinstance(env, dict):
                raise ValueError(f"check {check['id']}: env must be a mapping")
            for key, value in env.items():
                if key not in ENV_ALLOWLIST or not isinstance(value, str) or len(value) > 4096:
                    raise ValueError(f"check {check['id']}: env value is not in the explicit allowlist")
    return contract


def run_contract(contract, root, *, runner=subprocess.run):
    """Execute a validated contract and return a compact digest."""
    validate_contract(contract)
    base = Path(root)
    if not base.is_dir():
        raise ValueError(f"verification root is not a directory: {root!r}")
    results, failed, missing = [], [], []
    for check in contract["checks"]:
        target = base / check["cwd"] if check.get("cwd") else base
        try:
            completed = runner(check["argv"], cwd=target, capture_output=True,
                               timeout=check.get("timeoutSeconds", 300), shell=False)
        except (KeyError, LookupError) as exc:
            missing.append(check["id"])
            results.append({"id": check["id"], "exit_code": None, "missing": True,
                            "detail": f"no result from runner: {exc!r}"[:200]})
            continue
        except subprocess.TimeoutExpired:
            failed.append(check["id"])
            results.append({"id": check["id"], "exit_code": None, "timeout": True,
                            "stdout_sha256": hashlib.sha256(b"").hexdigest(),
                            "stderr_sha256": hashlib.sha256(b"timeout").hexdigest(),
                            "stdout_excerpt": "", "stderr_excerpt": "timeout expired"})
            continue
        stdout = bytes(completed.stdout or b"")
        stderr = bytes(completed.stderr or b"")
        code = completed.returncode
        results.append({"id": check["id"], "exit_code": code,
                        "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
                        "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
                        "stdout_excerpt": stdout.decode("utf-8", errors="replace")[:500],
                        "stderr_excerpt": stderr.decode("utf-8", errors="replace")[:500]})
        if code != 0 and check.get("required", True):
            failed.append(check["id"])
    return {"schemaVersion": 1, "profile": contract["profile"],
            "candidate_commit": contract["candidate_commit"],
            "status": "failed" if failed else "passed",
            "failed_checks": failed, "missing_checks": missing, "results": results}


def detect_divergence(contract, digest):
    """List check-ID mismatches between the requested contract and a digest."""
    expected = [check["id"] for check in contract.get("checks", [])]
    actual = [row.get("id") for row in digest.get("results", [])]
    errors = []
    for check_id in expected:
        if check_id not in actual:
            errors.append(f"contract check {check_id} has no digest result")
    for check_id in actual:
        if check_id not in expected:
            errors.append(f"digest result {check_id} is not in the contract")
    return errors


def digest_acceptance(digest):
    """Blockers that prevent a digest from authorizing progression."""
    errors = []
    for check_id in digest.get("failed_checks", []):
        errors.append(f"failed check: {check_id}")
    for check_id in digest.get("missing_checks", []):
        errors.append(f"missing check: {check_id}")
    if digest.get("status") == "divergent":
        errors.append("divergent verification digest")
    return errors


def check_progression(wave_ids, digests_by_wave):
    """A failed or divergent digest blocks its wave and every later wave."""
    errors = []
    for wave_id in wave_ids:
        digest = digests_by_wave.get(wave_id)
        if digest is None:
            errors.append(f"wave {wave_id} has no verification digest; progression blocked")
            break
        blockers = digest_acceptance(digest)
        if blockers:
            errors.append(f"wave {wave_id} cannot progress: {'; '.join(blockers)}")
            break
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    verify = commands.add_parser("verify", help="execute a validated contract and print the compact digest")
    verify.add_argument("--contract", required=True, help="verification contract JSON file")
    verify.add_argument("--root", default=".", help="working-tree root the checks run in")
    verify.add_argument("--output", default=None, help="write the digest JSON here instead of stdout")
    args = parser.parse_args(argv)
    try:
        contract = json.loads(Path(args.contract).read_text(encoding="utf-8-sig"))
        digest = run_contract(contract, args.root)
        if args.output:
            Path(args.output).write_text(json.dumps(digest, indent=2) + "\n", encoding="utf-8")
        else:
            print(json.dumps(digest, indent=2))
        return 0 if not digest_acceptance(digest) else 2
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
