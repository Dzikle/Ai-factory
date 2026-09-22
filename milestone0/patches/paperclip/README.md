# Paperclip Milestone 0B/0C upstream remediation

Temporary evaluation and upstream-contribution material only. These changes are
**not** an admitted production fork. Milestone 1 waits for supported upstream
acceptance/release, migration proof, and release-image re-admission.

## Milestone 0C submitted proposals

Both changes were independently rebased/adapted to upstream
`8326e33adad63e26c918edf6adf6db114997eced` and submitted:

| Proposal | Pull request | Exact head | Status at capture |
| --- | --- | --- | --- |
| SSH ephemeral host-workspace lease recovery | [#13772](https://github.com/paperclipai/paperclip/pull/13772) | `e319a7e8ddeba95274616d042d143c2343fc6031` | Open; CI passed |
| Optional durable pre-run run-context enrichment | [#13773](https://github.com/paperclipai/paperclip/pull/13773) | `de8b22d7fb1a29bf6fd9a1c3c8a4d823d37df428` | Open; new-head CI/review pending |

Upstream #13717 added local bookkeeping-lease cleanup while these proposals were
being prepared. The submitted lease contribution therefore reuses that behavior
and adds only the missing SSH driver retry/guard treatment plus stronger local
and SSH regression coverage. The enrichment proposal remains independent.

Focused validation: lease tests 58/58; enrichment, SDK, plugin-route authz, and
MCP policy tests 53/53 on the source-equivalent updated tree. Both proposals
passed monorepo typecheck and the normal production build. The updated
enrichment PR requires explicit instance-admin approval per plugin/company;
an ordinary settings row no longer enables the hook. The preceding enrichment
head had unrelated Runner Codex and chat-ordering CI failures; CI for the new
head is running. The historical 0B patches and bundle below preserve the exact
admission image evidence; the real PR heads
and GitHub diffs are the canonical 0C submission artifacts.

## Revisions and patch ownership

Upstream base: `e1f245a6607f3920d1618409ee0d5b90c822d81e`, MIT,
[merged PR #13515](https://github.com/paperclipai/paperclip/pull/13515).
Its lease sweep is reused; the superseded three PR-head patches are not carried.
Latest upstream inspected on 2026-09-22:
`8326e33adad63e26c918edf6adf6db114997eced`. It contains local-only logical
lease cleanup but no SSH equivalent or pre-run enrichment hook.

| Patch | Standalone commit / base | Scope |
| --- | --- | --- |
| `0001-feat-plugins-add-durable-pre-run-context-enrichment-.patch` | `939a02e96847282da5881a3a30f396c51659b32c` / `bd51f157e9aade37f2f4602eda238fe51405a0c2` | Optional SDK hook, worker RPC, explicit plugin capability, bounded durable same-run enrichment before existing dispatch; no adapter wrapper. |
| `0002-fix-server-recover-orphaned-local-and-SSH-workspace-.patch` | `0453a773a59403f57f978ecf68359282a025f7ef` / `e1f245a6607f3920d1618409ee0d5b90c822d81e` | Atomic logical release for recorded local/SSH ephemeral leases; capped pending repair; four PostgreSQL regression cases. |

Composite **tested revision**: `b75cbb5fa6ee408c516e04544365cdcd2ff1a383`;
tree: `8414940ca75347bd85f6b1be58af40697c82c03c`. It is upstream base plus
seam cherry-pick `d69a384ab1f8e2d68ec1bb16b4aa4874a720b054` plus host-lease fix.
`paperclip-m0b-test.bundle` preserves those exact temporary commits with the
upstream base as a prerequisite; it is an audit/reproduction artifact, not a
maintenance distribution. Fetch upstream/base first, then fetch the bundle's
`refs/heads/test/m0b-paperclip-upstream-lease-composite` into a test branch.

Alternatively `git am` patch 0001 then 0002 on the upstream base. Commit hashes
may differ with committer identity/time; require the exact tree above. The lease
patch also applies alone to upstream base; the seam applies after it. Keep the
changes as independent upstream proposals.

Applying lease alone then seam to official base was also verified in a clean
worktree: resulting commit `cb7e123208ccf3d92f2fc4cdf959030200134162` has the
identical test tree. File SHA-256 integrity receipts:

- seam patch: `381ede00b6bb308504ceed1035874ec642b3ba887c732a3bb05bb7417159e1a2`;
- lease patch: `6bec198cb0b16dfb846dc01e17e61781998d0c65a4bc6e97f8b425f5864f6e90`;
- test bundle: `76e3b45a43933d35f082e18deaa69209b8ea1ea60bdf4c28a3f7fc2e4717a5f3`.

Scoped Git attributes preserve these bytes across Windows checkouts. Patch
context lines deliberately contain the unified-diff space prefix; do not strip
them as prose trailing whitespace. Clean apply and tree/digest equality, rather
than nested-diff whitespace inspection, validate the patch artifacts.

## Compatibility and review notes

Lease correction adds no schema, endpoint, queue, provider contract, or task
writer. Built-in local/SSH release is already database-only; never delete their
shared host directories or invoke sandbox destruction. Classify by recorded
`metadata.driver` and ephemeral policy, not a potentially ambiguous provider
name. Sandbox shared-resource guards/teardown/retry budgets remain unchanged.
Unknown/legacy driver records require inspection, not a blanket teardown bypass.
Status compare-and-swap makes overlapping/repeated logical release idempotent;
existing release timestamps are preserved.

Enrichment is opt-in through `agent.run.enrich` and `onRunContextEnrich`, with
worker RPC `enrichRunContext`. Ready/company-enabled plugins receive the run's
existing governed MCP surface, not privileged knowledge credentials. They cannot
select another adapter or create a nested run. The host validates/persists
artifact identity and bounded prompt/metadata before the existing native/legacy
dispatch. Plugin failures fail that run before provider invocation. No schema
migration is required; older plugins without the hook are unchanged. An operator
installing this capability trusts the plugin with run-scoped credentials.

Existing events are asynchronous observation/job surfaces, not a durable
pre-dispatch response contract. Existing external adapters replace execution and
cannot transparently delegate to another registered adapter. The optional worker
RPC reuses the plugin runtime and leaves both dispatch paths in the host. These
were preferred over nested execution, a copied CLI adapter, or an event consumer
that races the provider invocation.

Bounds: at most eight enrichers; 64 KiB prompt and 16 KiB metadata per enricher;
artifact ref <=2,048 chars, SHA-256 required. The digest is a plugin assertion:
the host does not fetch/hash arbitrary artifact URIs. The POC independently
checks actual bytes. Plugins must write deterministic/idempotent artifacts and
avoid secrets in durable prompt/metadata; a crash before snapshot persistence
may repeat enrichment. Persisted snapshots prevent repeated same-run enrichment.
Cancellation, worker timeout, token expiry and provider invocation remain under
Paperclip's existing run machinery. This seam does not implement retrieval.

Focused test commands and real Docker/PostgreSQL receipts are in the existing
`docs/implementation/MILESTONE_0_DEPENDENCY_ADMISSION.md`. Full upstream CI and
a normal supported release build remain acceptance requirements, not claims made
by the admission-only `--noCheck` server image.
