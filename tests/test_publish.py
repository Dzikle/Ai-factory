"""Publication contract: real Git repositories, fake only the Paperclip HTTP boundary."""

import copy
from contextlib import redirect_stderr, redirect_stdout
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from threading import Thread
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
COMPANY = "00000000-0000-0000-0000-000000000010"
ISSUE = "00000000-0000-0000-0000-000000000030"
DECISION = "00000000-0000-0000-0000-000000000040"
APPROVAL = "00000000-0000-0000-0000-000000000050"


class PublishTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.repo = self.directory / "checkout"
        self.remote = self.directory / "remote.git"
        self.repo.mkdir()
        self.git("init", "-b", "work")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")
        subprocess.run(["git", "init", "--bare", str(self.remote)], check=True, capture_output=True)
        self.git("remote", "add", "origin", str(self.remote))
        (self.repo / "approved.txt").write_text("before\n", encoding="utf-8", newline="\n")
        (self.repo / "unrelated.txt").write_text("unrelated\n", encoding="utf-8", newline="\n")
        self.git("add", ".")
        self.git("commit", "-m", "base")
        self.base = self.git("rev-parse", "HEAD")
        self.git("push", "origin", "HEAD:refs/heads/main")
        # An unrelated intermediate commit must not be published with the candidate.
        (self.repo / "unrelated.txt").write_text("intermediate\n", encoding="utf-8", newline="\n")
        self.git("commit", "-am", "unrelated intermediate history")
        self.unrelated_commit = self.git("rev-parse", "HEAD")
        (self.repo / "unrelated.txt").write_text("unrelated\n", encoding="utf-8", newline="\n")
        (self.repo / "approved.txt").write_text("reviewed\n", encoding="utf-8", newline="\n")
        self.git("commit", "-am", "reviewed candidate")
        self.candidate = self.git("rev-parse", "HEAD")
        self.tree = self.git("rev-parse", "HEAD^{tree}")
        self.plan = {"schemaVersion": 1, "issueId": ISSUE, "decisionId": DECISION,
                     "remoteUrl": str(self.remote), "baseBranch": "main", "baseCommit": self.base,
                     "candidateCommit": self.candidate, "branch": "fix/aif-58-example",
                     "allowedPaths": ["approved.txt"]}
        self.receipt = self.directory / "receipt.json"
        self.issue = {"id": ISSUE, "companyId": COMPANY, "status": "done",
                      "executionPolicy": {"stages": [
                          {"id": "tests", "type": "review", "participants": [{"type": "agent", "agentId": "validator"}]},
                          {"id": "review", "type": "review", "participants": [{"type": "agent", "agentId": "reviewer"}]},
                          {"id": "owner", "type": "approval", "participants": [{"type": "user", "userId": "owner-1"}]}]},
                      "executionState": {"status": "completed", "lastDecisionId": DECISION,
                                         "lastDecisionOutcome": "approved",
                                         "completedStageIds": ["tests", "review", "owner"]}}
        self.comments = []
        self.posts = 0
        self.post_status = 201
        self.drop_post_response = False
        self.redirect_issue = False
        test = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def respond(self, status, body):
                raw = json.dumps(body).encode()
                self.send_response(status)
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def do_GET(self):
                if self.headers.get("Authorization") != "Bearer PRIVATE_TOKEN_SENTINEL":
                    self.respond(401, {"error": "PRIVATE_ERROR_SENTINEL"})
                elif self.path == f"/api/issues/{ISSUE}":
                    if test.redirect_issue:
                        self.send_response(302)
                        self.send_header("Location", test.redirect_url)
                        self.end_headers()
                    else:
                        self.respond(200, test.issue)
                elif self.path == f"/api/issues/{ISSUE}/comments/{APPROVAL}":
                    self.respond(200, test.approval)
                elif self.path.startswith(f"/api/issues/{ISSUE}/comments?"):
                    self.respond(200, test.comments)
                else:
                    self.respond(404, {})

            def do_POST(self):
                test.posts += 1
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                if self.path != f"/api/issues/{ISSUE}/comments":
                    self.respond(404, {})
                elif test.post_status != 201:
                    self.respond(test.post_status, {"error": "PRIVATE_ERROR_SENTINEL"})
                else:
                    comment = {**body, "id": "00000000-0000-0000-0000-000000000060",
                               "issueId": ISSUE, "companyId": COMPANY,
                               "authorUserId": "owner-1", "authorAgentId": None}
                    test.comments.append(comment)
                    if test.drop_post_response:
                        self.close_connection = True
                    else:
                        self.respond(201, comment)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        Thread(target=self.server.serve_forever, kwargs={"poll_interval": .05}, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.state = {"baseUrl": f"http://127.0.0.1:{self.server.server_port}", "companyId": COMPANY,
                      "userId": "owner-1", "boardApiKey": "PRIVATE_TOKEN_SENTINEL"}
        self.approval = {"id": APPROVAL, "issueId": ISSUE, "companyId": COMPANY,
                         "authorUserId": "owner-1", "authorAgentId": None,
                         "body": "Approved publication plan sha256:" + self.digest()}

    def digest(self):
        return hashlib.sha256(json.dumps(self.plan, sort_keys=True, separators=(",", ":"),
                                         ensure_ascii=True).encode()).hexdigest()

    def git(self, *args):
        return subprocess.run(["git", "-c", "core.autocrlf=false", *args], cwd=self.repo,
                              check=True, capture_output=True, text=True).stdout.strip()

    def arguments(self, command="publish"):
        for name, value in (("plan", self.plan), ("state", self.state)):
            (self.directory / f"{name}.json").write_text(json.dumps(value), encoding="utf-8")
        arguments = [command, "--repo", str(self.repo), "--plan", str(self.directory / "plan.json")]
        if command == "publish":
            arguments += ["--state", str(self.directory / "state.json"),
                          "--approval-comment", APPROVAL, "--receipt", str(self.receipt)]
        return arguments

    def cli(self, command="publish"):
        return subprocess.run([sys.executable, "-m", "milestone2.publish", *self.arguments(command)],
                              cwd=ROOT, capture_output=True, text=True, timeout=20)

    def remote_head(self):
        result = self.git("ls-remote", str(self.remote), f"refs/heads/{self.plan['branch']}")
        return result.split()[0] if result else None

    def test_preflight_is_read_only_and_emits_exact_approval_binding(self):
        before = self.git("status", "--porcelain")
        result = self.cli("preflight")
        self.assertEqual(0, result.returncode, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(self.digest(), report["planSha256"])
        self.assertEqual(self.tree, report["tree"])
        self.assertEqual(["approved.txt"], report["changedPaths"])
        self.assertEqual(self.approval["body"], report["approvalText"])
        self.assertIsNone(self.remote_head())
        self.assertFalse(self.receipt.exists())
        self.assertEqual(before, self.git("status", "--porcelain"))

    def test_preflight_does_not_refresh_index_bytes(self):
        self.git("status", "--porcelain")
        index = self.repo / self.git("rev-parse", "--git-path", "index")
        before = index.read_bytes()
        tracked = self.repo / "approved.txt"
        stat = tracked.stat()
        os.utime(tracked, (stat.st_atime, stat.st_mtime + 100))
        result = self.cli("preflight")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(before, index.read_bytes(), "Even index stat-cache refresh is forbidden")

    def test_git_replacement_refs_cannot_substitute_the_approved_tree(self):
        (self.repo / "approved.txt").write_text("SUBSTITUTED\n", encoding="utf-8", newline="\n")
        self.git("commit", "--amend", "-am", "replacement candidate")
        replacement = self.git("rev-parse", "HEAD")
        self.git("replace", self.candidate, replacement)
        result = self.cli("preflight")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(self.tree, json.loads(result.stdout)["tree"])

    def test_ignored_submodule_configuration_cannot_hide_out_of_scope_gitlink(self):
        self.git("update-index", "--add", "--cacheinfo", "160000", self.base, "libs/example")
        self.git("commit", "-m", "base with gitlink")
        new_base = self.git("rev-parse", "HEAD")
        (self.repo / "approved.txt").write_text("new reviewed change\n", encoding="utf-8", newline="\n")
        self.git("add", "approved.txt")
        self.git("update-index", "--cacheinfo", "160000", self.candidate, "libs/example")
        self.git("commit", "-m", "unapproved gitlink with approved text")
        self.plan.update(baseCommit=new_base, candidateCommit=self.git("rev-parse", "HEAD"))
        self.git("config", "diff.ignoreSubmodules", "all")
        result = self.cli("preflight")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("scope", result.stderr.lower())

    def test_unknown_empty_receipt_is_not_overwritten(self):
        self.receipt.write_text("{}", encoding="utf-8")
        result = self.cli()
        self.assertNotEqual(0, result.returncode)
        self.assertIsNone(self.remote_head())
        self.assertEqual("{}", self.receipt.read_text())

    def test_publication_keeps_exact_tree_without_unrelated_history_or_edits(self):
        (self.repo / "unrelated.txt").write_text("LOCAL WORK\n", encoding="utf-8")
        self.git("add", "unrelated.txt")
        (self.repo / "new-user-file.txt").write_text("UNTRACKED\n", encoding="utf-8")
        before = self.git("status", "--porcelain")
        head = self.git("rev-parse", "HEAD")
        result = self.cli()
        self.assertEqual(0, result.returncode, result.stderr)
        receipt = json.loads(self.receipt.read_text())
        published = self.remote_head()
        self.assertEqual(published, receipt["publishedCommit"])
        self.assertEqual(self.tree, self.git("rev-parse", published + "^{tree}"))
        self.assertEqual(self.base, self.git("rev-parse", published + "^"))
        self.assertEqual("reviewed", self.git("show", published + ":approved.txt"))
        self.assertEqual("unrelated", self.git("show", published + ":unrelated.txt"))
        self.assertNotEqual(self.candidate, published)
        self.assertEqual("recorded", receipt["status"])
        self.assertEqual(self.digest(), receipt["planSha256"])
        patch_bytes = subprocess.run(["git", "diff", "--binary", "--full-index", self.base, self.candidate],
                                     cwd=self.repo, capture_output=True, check=True).stdout
        self.assertEqual(hashlib.sha256(patch_bytes).hexdigest(), receipt["patchSha256"])
        self.assertEqual(before, self.git("status", "--porcelain"))
        self.assertEqual(head, self.git("rev-parse", "HEAD"))
        self.assertEqual(False, self.comments[0]["reopen"])
        self.assertEqual(False, self.comments[0]["resume"])
        self.assertEqual(False, self.comments[0]["interrupt"])
        self.assertNotIn("PRIVATE_", result.stdout + result.stderr + self.receipt.read_text())

    def test_replay_does_not_push_another_commit_or_add_another_comment(self):
        first = self.cli()
        self.assertEqual(0, first.returncode, first.stderr)
        published = self.remote_head()
        second = self.cli()
        self.assertEqual(0, second.returncode, second.stderr)
        self.assertEqual(published, self.remote_head())
        self.assertEqual(1, self.posts)

    def test_wrong_remote_is_rejected_before_push(self):
        self.git("remote", "set-url", "--push", "origin", str(self.directory / "wrong.git"))
        result = self.cli()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("remote", result.stderr.lower())
        self.assertIsNone(self.remote_head())

    def test_denies_stale_decision_missing_stages_or_unapproved_issue(self):
        original = copy.deepcopy(self.issue)
        mutations = [("status", "in_review"), ("lastDecisionId", APPROVAL),
                     ("lastDecisionOutcome", "changes_requested"), ("completedStageIds", ["tests"])]
        for key, value in mutations:
            with self.subTest(key=key):
                self.issue = copy.deepcopy(original)
                target = self.issue if key == "status" else self.issue["executionState"]
                target[key] = value
                result = self.cli()
                self.assertNotEqual(0, result.returncode)
                self.assertIn("approval", result.stderr.lower())
                self.assertIsNone(self.remote_head())
                self.assertEqual(0, self.posts)

    def test_denies_forged_deleted_or_wrong_candidate_approval(self):
        original = copy.deepcopy(self.approval)
        for key, value in [("authorUserId", "someone-else"), ("authorAgentId", "agent"),
                           ("deletedAt", "2026-10-03"), ("body", "Approved a different candidate")]:
            with self.subTest(key=key):
                self.approval = {**original, key: value}
                result = self.cli()
                self.assertNotEqual(0, result.returncode)
                self.assertIn("approval", result.stderr.lower())
                self.assertIsNone(self.remote_head())

    def test_protected_branch_and_out_of_scope_diff_are_rejected(self):
        for key, value in [("branch", "main"), ("branch", "stage"), ("branch", "fix/../main"),
                           ("allowedPaths", ["unrelated.txt"])]:
            with self.subTest(key=key, value=value):
                previous = self.plan[key]
                self.plan[key] = value
                result = self.cli()
                self.assertNotEqual(0, result.returncode)
                self.assertIn("branch" if key == "branch" else "scope", result.stderr.lower())
                self.plan[key] = previous
                self.assertIsNone(self.remote_head())

    def test_remote_conflict_is_not_overwritten(self):
        self.git("push", "origin", self.base + ":refs/heads/" + self.plan["branch"])
        result = self.cli()
        self.assertNotEqual(0, result.returncode)
        self.assertEqual(self.base, self.remote_head())
        self.assertEqual(0, self.posts)

    def test_branch_created_during_push_is_not_fast_forwarded_by_this_script(self):
        from milestone2.publish import main
        run = subprocess.run

        def create_competing_branch(argv, **kwargs):
            if "push" in argv:
                run(["git", "--git-dir=" + str(self.remote), "update-ref",
                     "refs/heads/" + self.plan["branch"], self.base], check=True, capture_output=True)
            return run(argv, **kwargs)

        with patch("milestone2.publish.subprocess.run", side_effect=create_competing_branch):
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                result = main(self.arguments())
        self.assertNotEqual(0, result)
        self.assertEqual(self.base, self.remote_head())
        self.assertEqual(0, self.posts)

    def test_comment_failure_keeps_truthful_pending_receipt_and_can_resume(self):
        self.post_status = 503
        result = self.cli()
        self.assertNotEqual(0, result.returncode)
        receipt = json.loads(self.receipt.read_text())
        self.assertEqual("pushed_receipt_pending", receipt["status"])
        self.assertEqual(self.remote_head(), receipt["publishedCommit"])
        self.assertNotIn("PRIVATE_", result.stdout + result.stderr)
        self.assertEqual(1, self.posts)
        self.post_status = 201
        result = self.cli()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(receipt["publishedCommit"], self.remote_head())
        self.assertEqual("recorded", json.loads(self.receipt.read_text())["status"])

    def test_lost_comment_response_is_reconciled_without_duplicate_post(self):
        self.drop_post_response = True
        result = self.cli()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("recorded", json.loads(self.receipt.read_text())["status"])
        self.assertEqual(1, self.posts)

    def test_lost_push_response_is_reconciled_by_exact_remote_commit(self):
        from milestone2.publish import main
        run = subprocess.run

        def lose_push_response(argv, **kwargs):
            result = run(argv, **kwargs)
            if "push" in argv and result.returncode == 0:
                return subprocess.CompletedProcess(argv, 1, b"", b"PRIVATE_PUSH_ERROR_SENTINEL")
            return result

        with patch("milestone2.publish.subprocess.run", side_effect=lose_push_response):
            with redirect_stdout(io.StringIO()):
                result = main(self.arguments())
        self.assertEqual(0, result)
        self.assertEqual(self.remote_head(), json.loads(self.receipt.read_text())["publishedCommit"])
        self.assertEqual(1, self.posts)

    def test_unreachable_paperclip_fails_before_git_publication(self):
        self.server.shutdown()
        self.server.server_close()
        result = self.cli()
        self.assertNotEqual(0, result.returncode)
        self.assertIsNone(self.remote_head())
        self.assertFalse(self.receipt.exists())

    def test_api_redirect_cannot_forward_board_credentials(self):
        received = []

        class Sink(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_GET(self):
                received.append(self.headers.get("Authorization"))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"{}")

        sink = ThreadingHTTPServer(("127.0.0.1", 0), Sink)
        Thread(target=sink.serve_forever, kwargs={"poll_interval": .05}, daemon=True).start()
        self.addCleanup(sink.server_close)
        self.addCleanup(sink.shutdown)
        self.redirect_issue = True
        self.redirect_url = f"http://127.0.0.1:{sink.server_port}/sink"
        result = self.cli()
        self.assertNotEqual(0, result.returncode)
        self.assertEqual([], received, "Board token must never reach a redirected endpoint")
        self.assertIsNone(self.remote_head())

    def test_stale_remote_base_is_rejected_before_publication(self):
        self.git("push", "origin", self.candidate + ":refs/heads/main")
        result = self.cli()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("base", result.stderr.lower())
        self.assertIsNone(self.remote_head())

    def test_missing_push_with_uncertain_receipt_is_not_blindly_retried(self):
        from milestone2.publish import main
        run = subprocess.run

        def no_push(argv, **kwargs):
            if "push" in argv:
                return subprocess.CompletedProcess(argv, 1, b"", b"PRIVATE_PUSH_ERROR_SENTINEL")
            return run(argv, **kwargs)

        with patch("milestone2.publish.subprocess.run", side_effect=no_push):
            with redirect_stderr(io.StringIO()):
                result = main(self.arguments())
        self.assertNotEqual(0, result)
        self.assertEqual("push_uncertain", json.loads(self.receipt.read_text())["status"])
        result = self.cli()
        self.assertNotEqual(0, result.returncode)
        self.assertIsNone(self.remote_head())
        self.assertEqual(0, self.posts)

    def test_receipt_for_different_plan_is_not_overwritten(self):
        first = self.cli()
        self.assertEqual(0, first.returncode, first.stderr)
        before = self.receipt.read_bytes()
        self.plan["branch"] = "fix/aif-58-different"
        self.approval["body"] = "Approved publication plan sha256:" + self.digest()
        result = self.cli()
        self.assertNotEqual(0, result.returncode)
        self.assertEqual(before, self.receipt.read_bytes())
        self.assertIsNone(self.remote_head())

    def test_github_account_is_checked_without_pushing_or_printing_credentials(self):
        from milestone2.publish import main
        for remote in ["https://github.com/Dzikle/example.git", "git@github-private:Dzikle/example.git"]:
            with self.subTest(remote=remote):
                self.git("remote", "set-url", "origin", remote)
                self.plan["remoteUrl"] = remote
                self.plan["githubAccount"] = "Dzikle"
                run = subprocess.run

                def wrong_account(argv, **kwargs):
                    if argv[0] == "gh":
                        return subprocess.CompletedProcess(argv, 0, b"someone-else\n", b"PRIVATE_AUTH_SENTINEL")
                    return run(argv, **kwargs)

                output = io.StringIO()
                with patch("milestone2.publish.subprocess.run", side_effect=wrong_account):
                    with redirect_stderr(output):
                        result = main(self.arguments("preflight"))
                self.assertNotEqual(0, result)
                self.assertIn("account", output.getvalue().lower())
                self.assertNotIn("PRIVATE_", output.getvalue())


if __name__ == "__main__":
    unittest.main()
