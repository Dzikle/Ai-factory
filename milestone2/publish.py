"""Preflight and publish one owner-approved Git tree; Paperclip remains task authority."""

import argparse
import hashlib
from http.client import HTTPException
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
from urllib.error import URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import build_opener, HTTPRedirectHandler
import uuid as uuids

from milestone0.scripts.paperclip_admission import ApiError, Client
from milestone2.task import read_object, text, uuid


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def environment():
    # Do not inherit an agent's temporary index or redirected repository.
    result = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    result.update(GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0", GCM_INTERACTIVE="Never")
    return result


def command(argv, *, cwd, env=None, check=True):
    try:
        result = subprocess.run(argv, cwd=cwd, env=env or environment(), capture_output=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ValueError("Command unavailable or timed out; reconcile the remote before retrying publication") from error
    if check and result.returncode:
        # Git/gh stderr may contain credentials or private server responses.
        raise ValueError("Git/GitHub command failed; no automatic write retry")
    return result


def git(repo, *args, env=None, check=True):
    return command(["git", "--no-replace-objects", "-c", f"core.hooksPath={os.devnull}", "-c", "core.fsmonitor=false",
                    "-c", "push.followTags=false", *args], cwd=repo, env=env, check=check)


def git_text(repo, *args):
    return git(repo, *args).stdout.decode("utf-8").strip()


def check_plan(plan, repo):
    keys = {"schemaVersion", "issueId", "decisionId", "remoteUrl", "baseCommit", "candidateCommit",
            "branch", "baseBranch", "allowedPaths"}
    if not isinstance(plan, dict) or set(plan) not in (keys, keys | {"githubAccount"}):
        raise ValueError("Plan must contain only the documented publication fields")
    if plan["schemaVersion"] != 1:
        raise ValueError("Unsupported publication plan schema")
    for key in ("issueId", "decisionId"):
        if uuid(plan[key], key) != plan[key]:
            raise ValueError(f"{key} must be a canonical UUID")
    for key in ("baseCommit", "candidateCommit"):
        if not isinstance(plan[key], str) or not re.fullmatch(r"[0-9a-f]{40}", plan[key]):
            raise ValueError(f"{key} must be an exact SHA-1 Git commit, not a branch/ref")
    branch = plan["branch"]
    if not isinstance(branch, str) or not re.fullmatch(r"(?:fix|feat|chore|docs|test)/[A-Za-z0-9][A-Za-z0-9._/-]{1,160}", branch):
        raise ValueError("Publication branch must be a feature branch, not a deployment branch")
    if git(repo, "check-ref-format", "refs/heads/" + branch, check=False).returncode:
        raise ValueError("Invalid publication branch")
    base_branch = text(plan["baseBranch"], "baseBranch", 200)
    if git(repo, "check-ref-format", "refs/heads/" + base_branch, check=False).returncode:
        raise ValueError("Invalid base branch")
    if base_branch == branch:
        raise ValueError("Publication branch must not replace its base branch")
    paths = plan["allowedPaths"]
    if not isinstance(paths, list) or not 0 < len(paths) <= 200 or len(set(map(str, paths))) != len(paths):
        raise ValueError("Scope must be a nonempty list of unique exact repository paths")
    for path in paths:
        if (not isinstance(path, str) or not path or len(path) > 1024 or "\\" in path
                or any(ord(c) < 32 for c in path) or PurePosixPath(path).is_absolute()
                or any(p in {"", ".", "..", ".git"} for p in path.split("/"))):
            raise ValueError("Scope contains an invalid repository path")
    remote = text(plan["remoteUrl"], "remoteUrl", 2048)
    if remote != plan["remoteUrl"] or any(ord(c) < 32 for c in remote):
        raise ValueError("Invalid remote URL")
    github = re.fullmatch(r"(?:https://github\.com/|git@(?:github\.com|github-private):)([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?", remote)
    if github:
        account = plan.get("githubAccount")
        if not isinstance(account, str) or not re.fullmatch(r"[A-Za-z0-9-]{1,39}", account):
            raise ValueError("GitHub remote requires an explicit githubAccount")
        login = command(["gh", "api", "--hostname", "github.com", "user", "--jq", ".login"], cwd=repo).stdout.decode().strip()
        if login.casefold() != account.casefold():
            raise ValueError("GitHub account mismatch; select the approved account without changing the plan")
    else:
        # A local bare remote is useful for offline verification. No arbitrary
        # transports or credential-bearing HTTPS URLs are accepted.
        local = Path(remote)
        if "githubAccount" in plan or not local.is_absolute() or not local.is_dir():
            raise ValueError("Remote must be credential-free GitHub URL or absolute local bare repository")
        if git_text(local, "rev-parse", "--is-bare-repository") != "true":
            raise ValueError("Local remote must be a bare Git repository")
    if git_text(repo, "remote", "get-url", "--push", "--all", "origin") != remote:
        raise ValueError("Configured origin push remote does not exactly match the approved plan")


def preflight(plan, repo):
    repo = Path(repo).resolve(strict=True)
    if Path(git_text(repo, "rev-parse", "--show-toplevel")).resolve() != repo:
        raise ValueError("Use the Git repository root")
    check_plan(plan, repo)
    for key in ("baseCommit", "candidateCommit"):
        if git_text(repo, "rev-parse", "--verify", plan[key] + "^{commit}") != plan[key]:
            raise ValueError("Commit identity mismatch")
    if git(repo, "merge-base", "--is-ancestor", plan["baseCommit"], plan["candidateCommit"], check=False).returncode:
        raise ValueError("Approved base must be an ancestor of the candidate")
    diff_args = ["--no-ext-diff", "--no-textconv", "--no-renames", "--ignore-submodules=none",
                 plan["baseCommit"], plan["candidateCommit"]]
    changed = git(repo, "diff", "--name-only", "-z", *diff_args).stdout.decode("utf-8").split("\0")[:-1]
    if not changed or not set(changed).issubset(plan["allowedPaths"]):
        raise ValueError("Candidate diff is empty or outside the approved path scope")
    if git(repo, "diff", "--check", *diff_args, check=False).returncode:
        raise ValueError("Candidate diff fails Git whitespace validation")
    patch = git(repo, "diff", "--binary", "--full-index", *diff_args).stdout
    digest = hashlib.sha256(canonical(plan)).hexdigest()
    return {"planSha256": digest, "tree": git_text(repo, "rev-parse", plan["candidateCommit"] + "^{tree}"),
            "changedPaths": changed, "patchSha256": hashlib.sha256(patch).hexdigest(),
            "dirtyCheckout": bool(git(repo, "status", "--porcelain", "-z").stdout),
            "approvalText": "Approved publication plan sha256:" + digest}


def approval(client, state, plan, comment_id, report):
    _, issue = client.request("GET", f"/api/issues/{plan['issueId']}")
    stages = (issue.get("executionPolicy") or {}).get("stages") or []
    execution = issue.get("executionState") or {}
    stage_ids = [s.get("id") for s in stages]
    if (issue.get("id") != plan["issueId"] or issue.get("companyId") != state["companyId"]
            or issue.get("status") != "done" or execution.get("status") != "completed"
            or execution.get("lastDecisionId") != plan["decisionId"]
            or execution.get("lastDecisionOutcome") != "approved" or not stages
            or not all(stage_ids) or len(set(stage_ids)) != len(stage_ids)
            or execution.get("completedStageIds") != stage_ids or stages[-1].get("type") != "approval"
            or {"type": "user", "userId": state["userId"]} not in stages[-1].get("participants", [])):
        raise ValueError("Paperclip owner approval is missing, incomplete or stale")
    _, comment = client.request("GET", f"/api/issues/{plan['issueId']}/comments/{comment_id}")
    if (comment.get("id") != comment_id or comment.get("issueId") != plan["issueId"]
            or comment.get("companyId") != state["companyId"] or comment.get("authorUserId") != state["userId"]
            or comment.get("authorAgentId") or comment.get("deletedAt")
            or report["approvalText"] not in str(comment.get("body", "")).splitlines()):
        raise ValueError("Exact publication plan requires a live owner-authored Paperclip approval comment")


def remote_head(plan, repo):
    result = git_text(repo, "ls-remote", "--refs", plan["remoteUrl"], "refs/heads/" + plan["branch"])
    if not result:
        return None
    rows = result.splitlines()
    if len(rows) != 1 or rows[0].split()[1] != "refs/heads/" + plan["branch"]:
        raise ValueError("Unexpected remote ref response")
    return rows[0].split()[0]


def check_remote_base(plan, repo):
    if remote_head({**plan, "branch": plan["baseBranch"]}, repo) != plan["baseCommit"]:
        raise ValueError("Remote base changed or is absent; re-review the base instead of publishing stale work")


def write_receipt(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False, suffix=".tmp") as output:
        temporary = Path(output.name)
        output.write(canonical(value) + b"\n")
        output.flush()
        os.fsync(output.fileno())
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def find_receipt(client, state, plan, request_id, body):
    after = None
    for _ in range(5):
        query = {"order": "asc", "limit": 100}
        if after:
            query["after"] = after
        _, comments = client.request("GET", f"/api/issues/{plan['issueId']}/comments?" + urlencode(query))
        if not isinstance(comments, list) or len(comments) > 100:
            raise ValueError("Unexpected Paperclip receipt catalog")
        for comment in comments:
            if comment.get("clientRequestId") == request_id:
                if (comment.get("body") != body or comment.get("authorUserId") != state["userId"]
                        or comment.get("authorAgentId") or comment.get("deletedAt")
                        or comment.get("issueId") != plan["issueId"] or comment.get("companyId") != state["companyId"]):
                    raise ValueError("Existing Paperclip publication receipt conflicts with this plan")
                return uuid(comment.get("id"), "receipt comment")
        if len(comments) < 100:
            return None
        after = uuid(comments[-1].get("id"), "comment cursor")
    raise ValueError("Receipt lookup exceeded 500 comments; reconcile explicitly instead of posting blindly")


def publish(plan, repo, state, comment_id, path, report):
    uuid(state.get("companyId"), "companyId")
    text(state.get("userId"), "owner userId", 255)
    base_url = text(state.get("baseUrl"), "baseUrl", 2048)
    url = urlsplit(base_url)
    if (url.username or url.password or url.query or url.fragment or url.path not in {"", "/"}
            or not (url.scheme == "https" or url.scheme == "http" and url.hostname in {"localhost", "127.0.0.1", "::1"})):
        raise ValueError("Paperclip URL must be HTTPS or loopback HTTP, without embedded credentials")
    client = Client(base_url, text(state.get("boardApiKey"), "boardApiKey", 4096))
    client.opener = build_opener(NoRedirect())
    approval(client, state, plan, comment_id, report)
    path = Path(path).resolve()
    try:
        path.relative_to(Path(repo).resolve())
    except ValueError:
        pass
    else:
        if git(repo, "check-ignore", "-q", str(path), check=False).returncode:
            raise ValueError("Receipt must be outside the checkout or in a Git-ignored directory")
    timestamp = git_text(repo, "show", "-s", "--format=%ct", plan["candidateCommit"])
    env = environment()
    env.update(GIT_AUTHOR_NAME="AI Factory", GIT_AUTHOR_EMAIL="ai-factory@example.invalid",
               GIT_COMMITTER_NAME="AI Factory", GIT_COMMITTER_EMAIL="ai-factory@example.invalid",
               GIT_AUTHOR_DATE=f"@{timestamp} +0000", GIT_COMMITTER_DATE=f"@{timestamp} +0000")
    # Flatten history, not file bytes. Unreviewed intermediate commits and the
    # caller's index never become part of this approved publication.
    message = f"Publish approved task {plan['issueId']}\n\nPlan sha256:{report['planSha256']}\nCandidate:{plan['candidateCommit']}"
    published = git(repo, "commit-tree", report["tree"], "-p", plan["baseCommit"], "-m", message, env=env).stdout.decode().strip()
    evidence = {"schemaVersion": 1, "issueId": plan["issueId"], "decisionId": plan["decisionId"],
                "approvalCommentId": comment_id, "planSha256": report["planSha256"], "branch": plan["branch"],
                "baseCommit": plan["baseCommit"], "candidateCommit": plan["candidateCommit"],
                "publishedCommit": published, "tree": report["tree"], "changedPaths": report["changedPaths"],
                "patchSha256": report["patchSha256"]}
    previous = read_object(path) if path.exists() else None
    if previous is not None and ({k: previous.get(k) for k in evidence} != evidence
                     or set(previous) - set(evidence) - {"status", "receiptCommentId"}):
        raise ValueError("Existing receipt belongs to a different publication; it was not overwritten")
    actual = remote_head(plan, repo)
    if actual is not None and actual != published:
        raise ValueError("Remote branch already contains a different commit; no overwrite")
    if actual is None:
        if previous is not None:
            raise ValueError("Prior publication is absent on remote; reconcile explicitly, no automatic repush")
        # Recheck immediately before the external write. Cross-system approval
        # revocation cannot be atomic with Git; this is the trusted-local profile.
        approval(client, state, plan, comment_id, report)
        check_remote_base(plan, repo)
        write_receipt(path, {**evidence, "status": "push_uncertain"})
        try:
            # Empty expected ref is a Git-native creation-only CAS. Even a
            # concurrent branch pointing at our base must not be fast-forwarded.
            # No existing ref is ever force-updated; no '+' refspec is used.
            git(repo, "push", "--porcelain", "--no-verify",
                f"--force-with-lease=refs/heads/{plan['branch']}:", plan["remoteUrl"],
                f"{published}:refs/heads/{plan['branch']}", check=False)
        except ValueError:
            pass
        if remote_head(plan, repo) != published:
            raise ValueError("Push not confirmed; saved uncertain receipt. Reconcile remote, do not blindly retry")
    write_receipt(path, {**evidence, "status": "pushed_receipt_pending"})
    request_id = str(uuids.uuid5(uuids.NAMESPACE_URL, "ai-factory-publication:" + report["planSha256"]))
    body = "AI Factory publication receipt\n\n```json\n" + canonical(evidence).decode() + "\n```"
    found = find_receipt(client, state, plan, request_id, body)
    if not found:
        try:
            client.request("POST", f"/api/issues/{plan['issueId']}/comments",
                           {"body": body, "clientRequestId": request_id, "reopen": False,
                            "resume": False, "interrupt": False}, expected=(200, 201))
        except (ApiError, URLError, HTTPException, OSError):
            pass
        found = find_receipt(client, state, plan, request_id, body)
        if not found:
            raise ValueError("Git push confirmed; Paperclip receipt pending. Rerun same plan after checking Paperclip")
    result = {**evidence, "status": "recorded", "receiptCommentId": found}
    write_receipt(path, result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("preflight", "publish"):
        child = commands.add_parser(name)
        child.add_argument("--repo", required=True, help="target repository root; never modifies checkout/index")
        child.add_argument("--plan", required=True, help="exact commits, branch, scope and Paperclip decision JSON")
        if name == "publish":
            child.add_argument("--state", default=os.environ.get("AIF_PAPERCLIP_STATE"), help="existing private board state JSON")
            child.add_argument("--approval-comment", required=True, help="owner-authored Paperclip comment containing preflight approvalText")
            child.add_argument("--receipt", required=True, help="public evidence JSON, outside checkout or Git-ignored")
    args = parser.parse_args(argv)
    try:
        plan = read_object(args.plan)
        report = preflight(plan, args.repo)
        if args.command == "publish":
            if not args.state:
                raise ValueError("Set AIF_PAPERCLIP_STATE or pass --state")
            report = publish(plan, args.repo, read_object(args.state),
                             uuid(args.approval_comment, "approval comment"), args.receipt, report)
        print(json.dumps(report, allow_nan=False))
        return 0
    except ApiError as error:
        print(f"Paperclip API returned {error.status}; check the saved receipt before retrying", file=sys.stderr)
    except (URLError, HTTPException, OSError):
        print("Paperclip or local evidence unavailable; check the saved receipt and remote before retrying", file=sys.stderr)
    except (ValueError, TypeError, KeyError, AttributeError, UnicodeError) as error:
        print(str(error) if isinstance(error, ValueError) else "Invalid publication input or API response", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
