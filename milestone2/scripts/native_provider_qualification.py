"""Owner-only bounded proof submission. Default preflight does GETs, not inference."""
import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from milestone0.scripts.paperclip_admission import Client, ApiError
from milestone2 import task
from milestone2.scripts.native_profile_contract import binding_fingerprint

FIELDS = {"schemaVersion","profileId","phase","companyId","projectId","agentId","validatorAgentId",
          "reviewerAgentId","ownerUserId","model","provider","accountRef","runtimePin","bindingFingerprint",
          "cwd","requestKey","permissionPolicy","budget"}


class NativeProofError(ValueError):
    def __init__(self, category, issue_id):
        super().__init__(category)
        self.category, self.issue_id = category, issue_id


def _get(client, path):
    return client.request("GET",path)[1]


def _validate(request):
    if not isinstance(request,dict) or set(request) != FIELDS or request.get("schemaVersion") != 1:
        raise ValueError("native_request_invalid")
    if request["phase"] not in {"capabilities","availability","coding"}: raise ValueError("native_request_invalid")
    for key in ("companyId","projectId","agentId","validatorAgentId","reviewerAgentId"): task.uuid(request[key],key)
    if len({request[key] for key in ("agentId","validatorAgentId","reviewerAgentId")}) != 3: raise ValueError("native_witness_not_independent")
    for key in ("profileId","ownerUserId","model","provider","accountRef","runtimePin","cwd","requestKey","bindingFingerprint"):
        value = task.text(request[key],key,4096 if key != "requestKey" else 255)
        if value != request[key] or any(char in value for char in "\x00\r\n"): raise ValueError("native_request_invalid")
    budget = request["budget"]
    expected_timeout = 600 if request["phase"] == "coding" else 120
    if (not isinstance(budget,dict) or set(budget) != {"tier","maxPaidCents","timeoutSec","maxCanaryAttempts"}
            or budget.get("tier") not in {"free","subscription"} or type(budget.get("maxPaidCents")) is not int
            or budget["maxPaidCents"] != 0 or type(budget.get("timeoutSec")) is not int or budget["timeoutSec"] != expected_timeout
            or type(budget.get("maxCanaryAttempts")) is not int or budget["maxCanaryAttempts"] != 2
            or request["permissionPolicy"] != ("coding_canary" if request["phase"] == "coding" else "no_tools")):
        raise ValueError("native_budget_or_policy_invalid")


def _prepared(client, request, *, require_idle=True):
    _validate(request)
    company, aid, project = request["companyId"],request["agentId"],request["projectId"]
    agent = _get(client,f"/api/agents/{aid}")
    if not isinstance(agent,dict) or agent.get("id") != aid or agent.get("companyId") != company or (require_idle and agent.get("status") != "idle"): raise ValueError("native_agent_not_idle")
    if agent.get("adapterType") not in {"cline_local","commandcode_local"}: raise ValueError("native_qualification_unsupported")
    state = _get(client,f"/api/agents/{aid}/native-provider-admission?projectId={project}")
    binding = state.get("currentBinding") if isinstance(state,dict) else None
    if not binding or binding_fingerprint(binding) != request["bindingFingerprint"]: raise ValueError("native_binding_unverified")
    for key in ("companyId","agentId","projectId","model","provider","accountRef","runtimePin","cwd"):
        if binding.get(key) != request[key]: raise ValueError("native_binding_mismatch")
    config = agent.get("adapterConfig") or {}
    if config.get("nativeCostTier") != request["budget"]["tier"] or config.get("maxPaidUsd") != 0: raise ValueError("native_paid_disallowed")
    timeout = config.get("timeoutSec",600)
    if request["phase"] == "coding" and (type(timeout) is not int or not 0 < timeout <= request["budget"]["timeoutSec"]):
        raise ValueError("native_timeout_not_authorized")
    if require_idle and request["phase"] == "coding" and state.get("codingSourceReady") is not True:
        raise ValueError("native_canary_source_unprepared")
    workflow = dict(projectId=project,developerAgentId=aid,validatorAgentId=request["validatorAgentId"],reviewerAgentId=request["reviewerAgentId"])
    if request["phase"] == "coding":
        fixture = json.loads((Path(__file__).resolve().parents[1]/"fixtures/native-provider-canary.json").read_text(encoding="utf-8"))
        description = fixture["description"]
    else:
        description = "Verify native ACP controls and exact model with zero inference." if request["phase"] == "capabilities" else "Respond exactly AIF_PROVIDER_READY. Use no tools. One no-tool prompt only."
    payload = task.build_payload(dict(userId=request["ownerUserId"]),workflow,
        dict(title=f"Native qualification: {request['profileId']} {request['phase']}",description=description,requestKey=request["requestKey"]),start=False)
    task.preflight(client,company,payload,start=False)
    if request["phase"] != "coding": payload["executionPolicy"] = None
    runs = _get(client,f"/api/companies/{company}/heartbeat-runs?agentId={aid}&limit=1000")
    if not isinstance(runs,list) or len(runs) >= 1000: raise ValueError("native_run_lineage_incomplete")
    if any(not isinstance(run,dict) or run.get("companyId") != company or run.get("agentId") != aid for run in runs): raise ValueError("native_run_lineage_invalid")
    matching = [run for run in runs if (run.get("contextSnapshot") or {}).get("nativeProviderProof",{}).get("baseBindingFingerprint") == request["bindingFingerprint"]
                and (run.get("contextSnapshot") or {}).get("nativeProviderProof",{}).get("phase") == request["phase"]]
    return agent,state,payload,matching


def preflight(client, request):
    _,_,_,runs = _prepared(client,request)
    if len(runs) >= 2: raise ValueError("native_canary_attempts_exhausted")
    return dict(schemaVersion=1,profileId=request["profileId"],phase=request["phase"],bindingFingerprint=request["bindingFingerprint"],attempts=len(runs),mutations=False)


def submit_qualification(client, request, *, authorized=False):
    if authorized is not True: raise ValueError("live_qualification_not_authorized")
    agent,_,payload,runs = _prepared(client,request)
    if len(runs) >= 2: raise ValueError("native_canary_attempts_exhausted")
    # Existing durable issue idempotency, no second queue or local recovery state.
    _,issue = client.request("POST",f"/api/companies/{request['companyId']}/issues",payload,expected=(200,201))
    if not isinstance(issue,dict) or issue.get("companyId") != request["companyId"] or any(issue.get(key) != payload[key] for key in ("projectId","assigneeAgentId","title","executionPolicy")):
        raise ValueError("native_proof_issue_conflict")
    issue_id = task.uuid(issue.get("id"),"proof issueId")
    if issue.get("status") != "backlog":
        return dict(schemaVersion=1,issueId=issue_id,phase=request["phase"],status="existing_started_or_terminal",mutations=False)
    # Same original issue never receives another prompt on recovery.
    if any((run.get("contextSnapshot") or {}).get("nativeProviderProof",{}).get("issueId") == issue_id for run in runs): raise ValueError("native_proof_already_attempted")
    scope = dict(schemaVersion=1,bindingFingerprint=request["bindingFingerprint"],issueIds=[issue_id],phase=request["phase"],
                 expiresAt=(datetime.now(timezone.utc)+timedelta(minutes=20)).isoformat(timespec="milliseconds").replace("+00:00","Z"),maxAttempts=2)
    try:
        _,updated = client.request("PATCH",f"/api/agents/{request['agentId']}",dict(metadata=dict(nativeProviderQualification=scope)))
        if (updated.get("metadata") or {}).get("nativeProviderQualification") != scope: raise ValueError("unconfirmed")
    except Exception:
        raise NativeProofError("native_grant_not_confirmed",issue_id) from None
    # Fresh GET-only preflight before starting; controller also rechecks at dispatch.
    _prepared(client,request)
    _,started = client.request("PATCH",f"/api/issues/{issue_id}",dict(status="todo",expectedStatusVersion=issue.get("statusVersion",0)))
    if started.get("status") != "todo": raise NativeProofError("native_start_not_confirmed",issue_id)
    return dict(schemaVersion=1,issueId=issue_id,phase=request["phase"],bindingFingerprint=request["bindingFingerprint"],status="submitted",mutations=True)


def collect_evidence(client, request):
    agent,state,_,runs = _prepared(client,request,require_idle=False)
    admission = (agent.get("metadata") or {}).get("nativeProviderAdmission") or {}
    return dict(schemaVersion=1,profileId=request["profileId"],source="integrated",installed="artifact_verified",
                authenticated="unverified",lastVerifiedAvailable=(admission.get("availability") or {}).get("verifiedAt"),
                codingQualified=bool(admission.get("qualification")),projectAdmitted=state.get("admitted") is True,
                bindingFingerprint=request["bindingFingerprint"],runs=[dict(runId=run.get("id"),status=run.get("status")) for run in runs],mutations=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",nargs="?",choices=("preflight","submit","report"),default="preflight")
    parser.add_argument("--state",required=True,help="private owner board state filename")
    parser.add_argument("--request",required=True,help="private proof request filename, no secret values")
    parser.add_argument("--authorize-live-qualification",action="store_true")
    args = parser.parse_args(argv)
    try:
        state,request = task.read_object(args.state),task.read_object(args.request)
        if state.get("companyId") != request.get("companyId") or state.get("userId") != request.get("ownerUserId"): raise ValueError("native_owner_state_mismatch")
        client = Client(task.text(state.get("baseUrl"),"baseUrl",2048),task.text(state.get("boardApiKey"),"boardApiKey",4096))
        result = submit_qualification(client,request,authorized=args.authorize_live_qualification) if args.command == "submit" else (collect_evidence if args.command == "report" else preflight)(client,request)
        print(json.dumps(result,separators=(",",":"),allow_nan=False)); return 0
    except NativeProofError as error:
        print(json.dumps(dict(status="failed",category=error.category,issueId=error.issue_id,retry="inspect Paperclip and reuse the same requestKey"),separators=(",",":")))
        return 1
    except (ApiError,ValueError,OSError):
        print("native_qualification_failed; no automatic retry; inspect the existing requestKey in Paperclip")
        return 1
if __name__ == "__main__": raise SystemExit(main())
