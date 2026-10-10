"""Bounded, read-only readiness checks for explicitly configured profiles.

This is an availability probe only. Paperclip remains responsible for native
agent sessions, task state, scheduling, retries, and handoff execution.
"""

import json
import os
import re
import subprocess


SENTINEL = "AIF_PROVIDER_READY"
MAX_OUTPUT_BYTES = 64 * 1024
_MODEL = re.compile(r"[A-Za-z0-9._-]+/[A-Za-z0-9._:-]+\Z")


def _text_response(stdout):
    """Return true only for a JSONL text event containing the exact sentinel."""
    if isinstance(stdout, bytes):
        if len(stdout) > MAX_OUTPUT_BYTES:
            return False, "output_too_large"
        try:
            stdout = stdout.decode("utf-8")
        except UnicodeDecodeError:
            return False, "invalid_output"
    elif isinstance(stdout, str):
        if len(stdout.encode("utf-8")) > MAX_OUTPUT_BYTES:
            return False, "output_too_large"
    else:
        return False, "invalid_output"

    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            continue
        part = event.get("part") if isinstance(event, dict) else None
        if (isinstance(event, dict) and event.get("type") == "text"
                and isinstance(part, dict) and part.get("type") == "text"
                and part.get("text") == SENTINEL):
            return True, "available"
    return False, "sentinel_missing"


def _native_config():
    return json.dumps({
        "permission": {"*": "deny"},
        "agent": {
            "aif-readiness": {
                "description": "Readiness probe with no tools",
                "mode": "primary",
                "steps": 2,
                "permission": {"*": "deny"},
            }
        },
    }, separators=(",", ":"))


def _probe(model, runner):
    env = os.environ.copy()
    env["OPENCODE_CONFIG_CONTENT"] = _native_config()
    try:
        result = runner(
            ["opencode", "run", "--pure", "--format", "json", "--model", model,
             "--dir", "/tmp", "--agent", "aif-readiness"],
            input="Respond exactly AIF_PROVIDER_READY. Use no tools.",
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return "timeout"
    except (OSError, subprocess.SubprocessError):
        return "unavailable"

    stdout = getattr(result, "stdout", None)
    # Check both streams' sizes, but never parse, return, or log stderr.
    stderr = getattr(result, "stderr", None)
    for stream in (stdout, stderr):
        if isinstance(stream, bytes) and len(stream) > MAX_OUTPUT_BYTES:
            return "output_too_large"
        if isinstance(stream, str) and len(stream.encode("utf-8")) > MAX_OUTPUT_BYTES:
            return "output_too_large"
    if getattr(result, "returncode", 1) != 0:
        return "unavailable"
    matched, category = _text_response(stdout)
    return "available" if matched else category


def qualify_available(profiles, runner=subprocess.run):
    """Return ready profiles and sanitized receipts, without changing profiles.

    Qualified subscription profiles without an availability probe are treated
    as previously operator-qualified. Explicit OpenCode probes are tried in a
    stable free-first/profile-id order and stop after the first success.
    """
    if not isinstance(profiles, (list, tuple)):
        return [], [{"category": "invalid_profiles"}]

    available = []
    receipts = []
    candidates = []
    for profile in profiles:
        if not isinstance(profile, dict) or profile.get("qualified") is not True:
            continue
        profile_id = profile.get("id")
        safe_id = profile_id if isinstance(profile_id, str) and len(profile_id) <= 128 else None
        if profile.get("tier") == "subscription" and not profile.get("availabilityProbe"):
            available.append(profile)
            receipts.append({"profileId": safe_id,
                             "qualification": "priorQualificationNotFreshInference"})
            continue
        if profile.get("availabilityProbe") != "opencode_no_tools":
            continue
        model = profile.get("model")
        if (profile.get("adapterType") != "opencode_local"
                or not isinstance(model, str) or len(model) > 256
                or not _MODEL.fullmatch(model)):
            receipts.append({"profileId": safe_id, "category": "invalid_profile"})
            continue
        tier_order = {"free": 0, "subscription": 1, "paid": 2}
        candidates.append((tier_order.get(profile.get("tier"), 3),
                           safe_id or "", profile, model, safe_id))

    candidates.sort(key=lambda row: (row[0], row[1]))
    for _, _, profile, model, safe_id in candidates:
        category = _probe(model, runner)
        receipts.append({"profileId": safe_id, "category": category})
        if category == "available":
            available.append(profile)
            break
    return available, receipts
