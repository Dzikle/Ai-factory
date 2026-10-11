"""Offline mirror tests; no provider, board, Docker, or private state access."""
import unittest
from copy import deepcopy
from milestone2.scripts.native_profile_contract import binding_fingerprint, validate_profile_admission


def fixture(adapter="cline_local"):
    binding = dict(companyId="company", agentId="agent", projectId="project", cwd="/paperclip/source",
                   adapterType=adapter, model="exact/model", provider="fixture", accountRef="account-ёж",
                   runtimePin="fixture@1", policyDigest="a" * 64, mcpDigest="b" * 64,
                   instructionsDigest="c" * 64, credentialVersionRef="secret-ref:v1")
    fingerprint = binding_fingerprint(binding)
    admission = dict(schemaVersion=1, binding=binding, bindingFingerprint=fingerprint,
                     qualification=dict(runId="coding", issueId="issue", candidateTree="d" * 40,
                                        testsRunId="tests", reviewerRunId="reviewer", capabilityRunId="capability"),
                     availability=dict(runId="availability", verifiedAt="2026-10-11T12:00:00.000Z", available=True))
    profile = dict(id="native", agentId="agent", adapterType=adapter, model="exact/model", tier="subscription",
                   qualified=True, enabled=True, bindingFingerprint=fingerprint, qualificationRunId="coding",
                   **{key: binding[key] for key in ("provider", "accountRef", "runtimePin", "credentialVersionRef")})
    agent = dict(id="agent", companyId="company", adapterType=adapter, status="idle",
                 adapterConfig={key: binding[key] for key in ("cwd", "model", "provider", "accountRef", "runtimePin", "credentialVersionRef")},
                 metadata=dict(nativeProviderAdmission=admission),
                 nativeAdmissionState=dict(schemaVersion=1, admitted=True, currentBinding=binding, admission=admission))
    agent["adapterConfig"].update(nativeCostTier="subscription", maxPaidUsd=0)
    return profile, agent


class NativeProfileContractTests(unittest.TestCase):
    def test_fixed_typescript_utf8_fixture(self):
        self.assertEqual("7fc6460695a311b513165695c1b944429030db8e0476557dc3573f05be9c09a6", fixture()[0]["bindingFingerprint"])
    def test_missing_metadata(self):
        profile, agent = fixture()
        agent["metadata"] = None
        with self.assertRaisesRegex(ValueError, "native_admission_missing"):
            validate_profile_admission(profile, agent, "project", "/paperclip/source")

    def test_exact_both_adapters_and_controller_readiness(self):
        for adapter in ("cline_local", "commandcode_local"):
            profile, agent = fixture(adapter)
            evidence = validate_profile_admission(profile, agent, "project", "/paperclip/source")
            self.assertEqual(profile["bindingFingerprint"], evidence["bindingFingerprint"])
            agent["nativeAdmissionState"]["admitted"] = False
            with self.assertRaisesRegex(ValueError, "native_admission_unavailable"):
                validate_profile_admission(profile, agent, "project", "/paperclip/source")

    def test_every_current_identity_and_retained_registry_reference(self):
        profile, original = fixture()
        for key in original["nativeAdmissionState"]["currentBinding"]:
            agent = deepcopy(original)
            agent["nativeAdmissionState"]["currentBinding"][key] = "f" * 64 if key.endswith("Digest") else "/changed"
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_profile_admission(profile, agent, "project", "/paperclip/source")
        for key in ("model", "provider", "accountRef", "runtimePin", "credentialVersionRef", "bindingFingerprint", "tier"):
            row = {**profile, key: "wrong"}
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_profile_admission(row, original, "project", "/paperclip/source")

    def test_revoke_and_unbounded_or_secret_shaped_identity(self):
        profile, agent = fixture()
        agent["metadata"]["nativeProviderAdmission"]["availability"]["available"] = False
        with self.assertRaisesRegex(ValueError, "native_admission_unavailable"):
            validate_profile_admission(profile, agent, "project", "/paperclip/source")
        for patch in ({"apiKey": "do-not-output"}, {"accountRef": "a\nsecret"}, {"model": "x" * 4097}, {"cwd": "/tmp/../source"}):
            identity = {**fixture()[1]["nativeAdmissionState"]["currentBinding"], **patch}
            with self.assertRaisesRegex(ValueError, "native_binding_mismatch"):
                binding_fingerprint(identity)
