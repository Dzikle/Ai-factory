"""No live calls: qualification operator state transitions use fixture API only."""
import unittest
from copy import deepcopy
from uuid import uuid4
from milestone2.scripts.native_provider_qualification import preflight, submit_qualification, collect_evidence
from milestone2.scripts.native_profile_contract import binding_fingerprint
from tests.test_native_profile_contract import fixture


class FakeClient:
    def __init__(self):
        profile, self.agent = fixture()
        self.company, self.project, self.aid, self.tests, self.reviewer = [str(uuid4()) for _ in range(5)]
        binding = self.agent["metadata"]["nativeProviderAdmission"]["binding"]
        binding.update(companyId=self.company, projectId=self.project, agentId=self.aid)
        self.agent.update(id=self.aid, companyId=self.company)
        self.agent["nativeAdmissionState"]["admitted"] = False
        self.writes, self.runs = [], []
        self.issue = None
        self.fail_grant = False
        self.request = dict(schemaVersion=1,profileId="cline",phase="availability",companyId=self.company,
            projectId=self.project,agentId=self.aid,validatorAgentId=self.tests,reviewerAgentId=self.reviewer,
            ownerUserId="owner",model=binding["model"],provider=binding["provider"],accountRef=binding["accountRef"],
            runtimePin=binding["runtimePin"],bindingFingerprint=binding_fingerprint(binding),cwd=binding["cwd"],
            requestKey="native-proof-one",permissionPolicy="no_tools",budget=dict(tier="subscription",maxPaidCents=0,timeoutSec=120,maxCanaryAttempts=2))
    def request_api(self, method, path, body=None, **kwargs):
        if method == "GET":
            if "/native-provider-admission?" in path: return 200,deepcopy(self.agent["nativeAdmissionState"])
            if path.endswith("/heartbeat-runs?agentId="+self.aid+"&limit=1000"): return 200,deepcopy(self.runs)
            if path == "/api/projects/"+self.project: return 200,dict(id=self.project,companyId=self.company,workspaces=[dict(cwd=self.request["cwd"])])
            if path == "/api/agents/"+self.aid: return 200,deepcopy(self.agent)
            if path.startswith("/api/agents/"): return 200,dict(id=path.rsplit("/",1)[1],companyId=self.company,status="idle")
            raise AssertionError(path)
        self.writes.append((method,path,deepcopy(body)))
        if method == "POST" and path.endswith("/issues"):
            if self.issue is None: self.issue = dict(id=str(uuid4()),companyId=self.company,**deepcopy(body))
            return 200,deepcopy(self.issue)
        if method == "PATCH" and path.startswith("/api/agents/"):
            if self.fail_grant: raise ValueError("fixture grant refused")
            self.agent.setdefault("metadata",{}).update(body["metadata"])
            return 200,deepcopy(self.agent)
        if method == "PATCH" and path.startswith("/api/issues/"):
            self.issue.update(body); return 200,deepcopy(self.issue)
        raise AssertionError(path)


class NativeQualificationTests(unittest.TestCase):
    def setUp(self):
        self.f = FakeClient()
        self.client = type("FixtureAPI",(),{"request": lambda _,*args,**kwargs:self.f.request_api(*args,**kwargs)})()
    def test_preflight_read_only_and_explicit_authority(self):
        self.assertFalse(preflight(self.client,self.f.request)["mutations"])
        self.assertEqual([],self.f.writes)
        with self.assertRaisesRegex(ValueError,"live_qualification_not_authorized"):
            submit_qualification(self.client,self.f.request)
        self.assertEqual([],self.f.writes)
    def test_backlog_grant_start_and_idempotent_replay(self):
        first = submit_qualification(self.client,self.f.request,authorized=True)
        self.assertEqual(["POST","PATCH","PATCH"],[row[0] for row in self.f.writes])
        self.assertEqual("backlog",self.f.writes[0][2]["status"])
        self.assertIsNone(self.f.writes[0][2]["executionPolicy"])
        self.assertEqual("todo",self.f.issue["status"])
        self.assertEqual(first["issueId"],submit_qualification(self.client,self.f.request,authorized=True)["issueId"])
        self.assertEqual(4,len(self.f.writes)) # replay lookup via existing idempotent POST, no new grant/start
    def test_failed_grant_never_starts_and_same_request_recovers(self):
        self.f.fail_grant = True
        with self.assertRaisesRegex(ValueError,"native_grant_not_confirmed"):
            submit_qualification(self.client,self.f.request,authorized=True)
        self.assertEqual("backlog",self.f.issue["status"])
        issue_id = self.f.issue["id"]
        self.f.fail_grant = False
        self.assertEqual(issue_id,submit_qualification(self.client,self.f.request,authorized=True)["issueId"])
    def test_third_attempt_and_paid_are_refused_before_writes(self):
        self.f.runs = [dict(companyId=self.f.company,agentId=self.f.aid,contextSnapshot=dict(nativeProviderProof=dict(baseBindingFingerprint=self.f.request["bindingFingerprint"],phase="availability"))) for _ in range(2)]
        with self.assertRaisesRegex(ValueError,"native_canary_attempts_exhausted"):
            submit_qualification(self.client,self.f.request,authorized=True)
        self.assertEqual([],self.f.writes)
        self.f.request["budget"]["maxPaidCents"] = 1
        with self.assertRaises(ValueError): preflight(self.client,self.f.request)
    def test_missing_refs_busy_or_foreign_proof(self):
        for patch in ({"model":None},{"bindingFingerprint":"0"*64},{"permissionPolicy":"allow_all"}):
            with self.subTest(patch=patch),self.assertRaises(ValueError): preflight(self.client,{**self.f.request,**patch})
        self.f.agent["status"] = "running"
        with self.assertRaises(ValueError): preflight(self.client,self.f.request)
        self.f.agent["status"] = "idle"
        self.f.runs = [dict(companyId="other",agentId=self.f.aid)]
        with self.assertRaises(ValueError): preflight(self.client,self.f.request)
        self.assertEqual([],self.f.writes)
    def test_report_truthful_and_bounded(self):
        report = collect_evidence(self.client,self.f.request)
        self.assertEqual("unverified",report["authenticated"])
        self.assertFalse(report["projectAdmitted"])
        self.assertEqual([],self.f.writes)
    def test_coding_timeout_must_match_authorized_envelope(self):
        self.f.request.update(phase="coding",permissionPolicy="coding_canary")
        self.f.request["budget"]["timeoutSec"] = 600
        self.f.agent["adapterConfig"]["timeoutSec"] = 3600
        with self.assertRaisesRegex(ValueError,"native_timeout_not_authorized"):
            preflight(self.client,self.f.request)
        self.assertEqual([],self.f.writes)
    def test_paused_report_is_read_only(self):
        self.f.agent["status"] = "paused"
        self.assertFalse(collect_evidence(self.client,self.f.request)["mutations"])
        self.assertEqual([],self.f.writes)
