"""Nonsecret admission mirror. Paperclip alone owns admission and inference."""
import hashlib
import json
import posixpath
import re

NATIVE_ADMITTED_ADAPTERS = {"cline_local", "commandcode_local", "claude_local"}
FIELDS = {"companyId", "agentId", "projectId", "cwd", "adapterType", "model", "provider",
          "accountRef", "runtimePin", "policyDigest", "mcpDigest", "instructionsDigest", "credentialVersionRef"}
DIGEST = re.compile(r"[a-f0-9]{64}\Z")


def _object(value):
    return value if isinstance(value, dict) else {}


def binding_fingerprint(binding):
    if not isinstance(binding, dict) or set(binding) != FIELDS:
        raise ValueError("native_binding_mismatch")
    for key, value in binding.items():
        if (not isinstance(value, str) or not value or value != value.strip() or len(value) > 4096
                or any(char in value for char in "\x00\r\n")):
            raise ValueError("native_binding_mismatch")
        if key.endswith("Digest") and not DIGEST.fullmatch(value):
            raise ValueError("native_binding_mismatch")
    cwd = binding["cwd"]
    if not cwd.startswith("/") or cwd.startswith("//") or posixpath.normpath(cwd) != cwd or "\\" in cwd:
        raise ValueError("native_binding_mismatch")
    encoded = json.dumps(binding, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def requires_admission(agent):
    metadata = _object(agent.get("metadata"))
    return agent.get("adapterType") in {"cline_local", "commandcode_local"} or bool(
        metadata.get("nativeProviderManaged") or metadata.get("nativeProviderAdmission") or metadata.get("nativeProviderQualification"))


def validate_profile_admission(profile, agent, project_id, cwd):
    admission = _object(_object(agent.get("metadata")).get("nativeProviderAdmission"))
    if not admission or not isinstance(admission.get("binding"), dict):
        raise ValueError("native_admission_missing")
    state = _object(agent.get("nativeAdmissionState"))
    availability = _object(admission.get("availability"))
    if (admission.get("schemaVersion") != 1 or isinstance(admission.get("schemaVersion"), bool)
            or availability.get("available") is not True or availability.get("invalidatedByRunId")
            or state.get("schemaVersion") != 1 or state.get("admitted") is not True):
        raise ValueError("native_admission_unavailable")
    identity = admission["binding"]
    fingerprint = binding_fingerprint(identity)
    if (fingerprint != admission.get("bindingFingerprint") or fingerprint != profile.get("bindingFingerprint")
            or state.get("admission") != admission or state.get("currentBinding") != identity):
        raise ValueError("native_binding_mismatch")
    config = _object(agent.get("adapterConfig"))
    if (identity["agentId"] != agent.get("id") or identity["companyId"] != agent.get("companyId")
            or identity["projectId"] != project_id or identity["cwd"] != cwd
            or identity["adapterType"] != agent.get("adapterType")
            or identity["adapterType"] not in NATIVE_ADMITTED_ADAPTERS
            or profile.get("tier") not in {"free", "subscription"}
            or config.get("nativeCostTier") != profile.get("tier") or config.get("maxPaidUsd") != 0):
        raise ValueError("native_binding_mismatch")
    for key in ("agentId", "adapterType", "model", "provider", "accountRef", "runtimePin", "credentialVersionRef"):
        if profile.get(key) != identity[key]:
            raise ValueError("native_binding_mismatch")
    for key in ("cwd", "model", "provider", "accountRef", "runtimePin", "credentialVersionRef"):
        if config.get(key) != identity[key]:
            raise ValueError("native_binding_mismatch")
    qualification = _object(admission.get("qualification"))
    required = {"runId", "issueId", "candidateTree", "testsRunId", "reviewerRunId", "capabilityRunId"}
    if (set(qualification) != required or any(not isinstance(qualification[key], str) or not qualification[key] for key in required)
            or not re.fullmatch(r"(?:[a-f0-9]{40}|[a-f0-9]{64})", qualification["candidateTree"])
            or profile.get("qualificationRunId") != qualification["runId"]):
        raise ValueError("native_admission_missing")
    return {"bindingFingerprint": fingerprint, "qualificationRunId": qualification["runId"],
            "testsRunId": qualification["testsRunId"], "reviewerRunId": qualification["reviewerRunId"],
            "capabilityRunId": qualification["capabilityRunId"], "availabilityRunId": availability.get("runId")}
