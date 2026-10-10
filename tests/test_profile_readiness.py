import json
import subprocess
import unittest
from types import SimpleNamespace

from milestone2.scripts.profile_readiness import qualify_available


def profile(profile_id="free-a", **changes):
    value = {"id": profile_id, "qualified": True, "tier": "free",
             "adapterType": "opencode_local", "model": "opencode/example-model",
             "availabilityProbe": "opencode_no_tools"}
    value.update(changes)
    return value


class ProfileReadinessTests(unittest.TestCase):
    def test_native_text_sentinel_qualifies_profile_and_uses_strict_arguments(self):
        calls = []

        def runner(args, **kwargs):
            calls.append((args, kwargs))
            return SimpleNamespace(returncode=0, stdout=json.dumps({
                "type": "text", "part": {"type": "text", "text": "AIF_PROVIDER_READY"}
            }) + "\n", stderr="")

        target = profile()
        available, receipts = qualify_available([target], runner)
        self.assertEqual([target], available)
        self.assertEqual([{"profileId": "free-a", "category": "available"}], receipts)
        args, kwargs = calls[0]
        self.assertEqual(["opencode", "run", "--pure", "--format", "json", "--model",
                          "opencode/example-model", "--dir", "/tmp", "--agent", "aif-readiness"], args)
        self.assertEqual(30, kwargs["timeout"])
        self.assertEqual("Respond exactly AIF_PROVIDER_READY. Use no tools.", kwargs["input"])
        native = json.loads(kwargs["env"]["OPENCODE_CONFIG_CONTENT"])
        self.assertEqual({"*": "deny"}, native["permission"])
        agent = native["agent"]["aif-readiness"]
        self.assertEqual("primary", agent["mode"])
        self.assertEqual(2, agent["steps"])
        self.assertEqual({"*": "deny"}, agent["permission"])

    def test_requires_exact_text_event_and_nonzero_exit_is_unavailable(self):
        events = [
            json.dumps({"type": "tool_use", "part": {"text": "AIF_PROVIDER_READY"}}),
            json.dumps({"type": "text", "part": {"type": "text", "text": "prefix AIF_PROVIDER_READY"}}),
        ]
        for stdout in events:
            with self.subTest(stdout=stdout):
                available, receipts = qualify_available(
                    [profile()], lambda *_args, **_kwargs: SimpleNamespace(
                        returncode=0, stdout=stdout, stderr=""))
                self.assertEqual([], available)
                self.assertEqual("sentinel_missing", receipts[0]["category"])
        available, receipts = qualify_available(
            [profile()], lambda *_args, **_kwargs: SimpleNamespace(
                returncode=1, stdout="", stderr="credential=PRIVATE"))
        self.assertEqual([], available)
        self.assertEqual("unavailable", receipts[0]["category"])
        self.assertNotIn("PRIVATE", repr(receipts))

    def test_timeout_and_oversized_output_are_sanitized(self):
        def timeout(*_args, **_kwargs):
            raise subprocess.TimeoutExpired("opencode", 30, stderr="secret=PRIVATE")

        available, receipts = qualify_available([profile()], timeout)
        self.assertEqual([], available)
        self.assertEqual("timeout", receipts[0]["category"])
        self.assertNotIn("PRIVATE", repr(receipts))

        available, receipts = qualify_available(
            [profile()], lambda *_args, **_kwargs: SimpleNamespace(
                returncode=0, stdout="x" * (64 * 1024 + 1), stderr=""))
        self.assertEqual([], available)
        self.assertEqual("output_too_large", receipts[0]["category"])

    def test_free_first_stops_after_first_success_and_preserves_prequalified_subscription(self):
        subscription = {"id": "sub", "qualified": True, "tier": "subscription",
                        "model": "provider/model", "apiKey": "PRIVATE"}
        first = profile("free-z")
        next_free = profile("free-a")
        calls = []

        def runner(args, **kwargs):
            calls.append(args)
            return SimpleNamespace(returncode=0, stdout=json.dumps({
                "type": "text", "part": {"type": "text", "text": "AIF_PROVIDER_READY"}
            }), stderr="")

        available, receipts = qualify_available([next_free, subscription, first], runner)
        self.assertEqual([subscription, next_free], available)
        self.assertEqual(1, len(calls))
        self.assertEqual("free-a", receipts[-1]["profileId"])
        self.assertEqual("priorQualificationNotFreshInference", receipts[0]["qualification"])
        self.assertNotIn("PRIVATE", json.dumps(receipts))

    def test_unqualified_unknown_and_malformed_probe_profiles_are_skipped_safely(self):
        invalid = profile("bad", model="not-qualified")
        available, receipts = qualify_available([
            {"id": "unqualified", "qualified": False, "apiKey": "PRIVATE"},
            {"id": "unknown", "qualified": True, "tier": "paid"}, invalid,
        ], lambda *_args, **_kwargs: self.fail("invalid profiles must not run"))
        self.assertEqual([], available)
        self.assertEqual([{"profileId": "bad", "category": "invalid_profile"}], receipts)
        self.assertNotIn("PRIVATE", json.dumps(receipts))


if __name__ == "__main__":
    unittest.main()
