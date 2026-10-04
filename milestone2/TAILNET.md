# Private dashboard access

Use the existing host Tailscale client and **Serve**, not Funnel. No additional
container, image, router forwarding or public/LAN Docker bind is needed.
Paperclip remains authenticated; Tailscale identity headers do not grant a
Paperclip account or bypass its permissions.

On this installation, enable Tailscale on the accessing device and open:

`https://desktop-t58n2b9.tail14d8ec.ts.net/`

Local access remains `http://localhost:13101/`. The computer, Docker Desktop,
Paperclip and Tailscale must be running. Existing tailnet access rules apply;
other users do not automatically get access, and this setup does not edit those
rules. Serve is private to allowed tailnet devices, not publicly published.

## Existing configuration

`compose/paperclip-tailnet.yaml` appends only the exact device hostname and auth
origin/cookie settings to the admitted controller configuration. The pinned
image, database, volume, native MCP network and agent permissions remain
unchanged. The hostname is supplied by the ignored
`.milestone0/paperclip-tailnet.env`; no credential is stored in that file.

The normal Paperclip public URL is HTTPS. Native auth auto-base handling and
its existing HTTP-loopback cookie compatibility retain local access. Explicit
trusted origins include only the two existing local mapped-port origins;
Paperclip derives the exact HTTPS tailnet origin from the allowed hostname.

The host route was created with the installed Tailscale 1.102.2 CLI:

```powershell
tailscale serve --bg --https=443 http://127.0.0.1:13101
tailscale serve status
```

Do not overwrite an existing handler on port 443. This installation had no
Serve configuration before enabling the route. `--bg` persists the route across
Tailscale/device restarts; it does not start Docker or Paperclip.

For an intentional controller recreation, from the Factory repository root:

```powershell
docker compose --env-file .milestone0/m2-security-rotation-20260928/rotated.env --env-file .milestone0/paperclip-tailnet.env -f milestone0/compose/paperclip-fork-readmission.yaml -f milestone2/compose/paperclip-native-mcp.yaml -f milestone2/compose/paperclip-tailnet.yaml up -d --no-deps --no-build --pull never paperclip-fork
```

Use the current private credential file, not an older admission fixture. Check
no tasks are running before recreation, and validate the resolved image,
mounts/networks and unchanged credentials without printing them. Ordinary
`docker start` needs neither the credential files nor recreation.

## Verify and undo

Check the HTTPS root, `/api/health` and `/api/auth/get-session`; anonymous
session/board requests must not disclose a user or company. Login uses the
existing Paperclip account.
Confirm unrelated Host/Origin requests are still denied. Do not treat a health
check as proof of a remote device's grants or a successful owner login.

Disable only this handler with:

```powershell
tailscale serve --https=443 off
```

Do not use `serve reset` or change Funnel settings belonging to other services.
To restore the old Paperclip URL/configuration, recreate the controller with
only the first two Compose files, after checking it is idle. Preserve the same
database, volume and secrets. No application/database rollback is required.

Official references: [Serve](https://tailscale.com/docs/features/tailscale-serve)
and [Serve CLI](https://tailscale.com/docs/reference/tailscale-cli/serve).

## Applied verification — 2026-10-04

- Before change: the tailnet hostname and HTTPS dashboard returned HTTP 403.
- After change: local and HTTPS dashboard/health returned HTTP 200; controller
  health is healthy. Serve status reports **tailnet only**, with no Funnel route.
- Anonymous session lookup returned HTTP 401 (`Board authentication required`)
  and company listing HTTP 403 (`Board access required`) through both addresses.
- Well-formed login requests for a nonexistent `.invalid` account reached normal
  validation through both allowed origins: HTTP 401 `INVALID_EMAIL_OR_PASSWORD`.
  No user/session was created and no existing account password was used.
- The same well-formed request from an unrelated origin returned HTTP 403
  `INVALID_ORIGIN`; an unrelated Host also returned HTTP 403. An empty login body
  returns HTTP 400 before origin checks and is not evidence of origin denial.
- Compose preflight verified unchanged image pin, configured secrets, named data
  volume, both networks and `127.0.0.1:13101` binding. Recreation retained image
  digest `sha256:c0d8fe5a94d7cabd475f149b10d7d7444ce003740aeefc0b03e40a6a41199dbf`
  and volume `aif-m0-fork-restore-data`; no build/pull/schema change was requested.
- Zero queued/running runs and all 115 agents paused before and after the change.
- These probes used this host's Tailscale URL. A second device's access-policy
  grant and a successful existing-owner browser login were not tested.

## Mobile selector fix — 2026-10-04

The owner fork now serves image commit
`9570a362e7cd9f4b9f277806f308ecad0ae6aabb`, pinned in
`compose/paperclip-native-mcp.yaml`. The old mobile fixed-position override
collapsed Radix's popup wrapper to 10px, hiding project/assignee/model choices.
The fix restores normal content sizing and leaves positioning to Radix.
Nine browser regressions (including the real New Task dialog), 35 focused unit
tests and UI typecheck/build passed. Keyboard checks emulate viewports, not a
physical Android device. The broader UI suite/audit is not fully green; exact
failures and deployment evidence are in
[the result record](results/mobile-picker-fix-20261004.json).

Paired database/storage backups preceded the update. All seven authority-table
checksums and the schema were preserved, with the same credentials, volume,
networks and loopback binding. Local and tailnet pages serve the repaired CSS;
anonymous access remains denied. All agents remain paused. AIF-75 is still
unassigned and was not started. This is a layout fix, not a permission grant.

Refresh the phone page (or use Paperclip's update prompt, if shown), then reopen
New Task and its Project/Assignee/model selector. Physical-phone confirmation
is the remaining user check. Previous image/backup material is retained for
rollback; no unrelated Docker resources were removed.
