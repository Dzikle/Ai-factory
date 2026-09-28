#!/usr/bin/env python3
"""Owner-approved local credential rotation/cutover; no credentials in output.

Preserves databases and storage. Requires a published immutable owner image,
paused agents and zero queued/running work. Recovery material stays Git-ignored.
This is an operator procedure, not an agent tool or a second state engine.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import subprocess
import tarfile
import time
from pathlib import Path
from urllib.parse import unquote, urlsplit

CONTROLLER = "aif-m0-paperclip-fork-paperclip-fork-1"
POSTGRES = "aif-m0-paperclip-postgres-1"
DATABASE = "paperclip_fork_m0"
TABLES = ("companies", "agents", "issues", "heartbeat_runs", "project_workspaces",
          "execution_workspaces", "environment_leases")


def docker(*args: str, stdin: bytes | None = None, timeout: int = 180) -> subprocess.CompletedProcess:
    result = subprocess.run(["docker", *args], input=stdin, capture_output=True, timeout=timeout)
    if result.returncode:
        # Neither stdout/stderr nor CalledProcessError may disclose config/SQL.
        raise RuntimeError(f"Docker operation failed: {args[0]} (exit {result.returncode})")
    return result


def sql(query: str) -> str:
    return docker("exec", "-i", POSTGRES, "psql", "-X", "-v", "ON_ERROR_STOP=1", "-U", "paperclip",
                  "-d", DATABASE, "-At", stdin=query.encode()).stdout.decode().strip()


def authority_snapshot() -> dict:
    result = {}
    for table in TABLES:
        # Includes durable context snapshots and complete lease receipts, but
        # publishes only counts and checksums, never raw rows/logs/credentials.
        count, digest = sql(f"SELECT count(*), md5(coalesce(string_agg(to_jsonb(t)::text, '' ORDER BY id), '')) FROM {table} t;").split("|")
        result[table] = {"count": int(count), "rows_md5": digest}
    result["schema"] = sql("SELECT count(*) || '|' || max(created_at) FROM drizzle.__drizzle_migrations;")
    return result


def tcp_auth(password: str) -> bool:
    # initdb trusts both Unix sockets and loopback. Use the Docker service
    # address so this exercises the same SCRAM rule as the controller.
    result = subprocess.run(["docker", "exec", "-i", POSTGRES, "sh", "-c",
        f"IFS= read -r PGPASSWORD; export PGPASSWORD; exec psql -X -h {POSTGRES} -U paperclip -d paperclip_fork_m0 -At -c 'SELECT 1'"],
        input=(password + "\n").encode(), capture_output=True, timeout=20)
    return result.returncode == 0 and result.stdout.strip() == b"1"


def sha256(file: Path) -> str:
    with file.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def health(container: str) -> None:
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        state = json.loads(docker("inspect", container).stdout)[0]["State"]
        if state.get("Health", {}).get("Status") == "healthy":
            return
        if not state.get("Running"):
            raise RuntimeError(f"Container did not stay running: {container}")
        time.sleep(2)
    raise RuntimeError(f"Health timeout: {container}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--backup-dir", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"ghcr\.io/dzikle/paperclip@sha256:[a-f0-9]{64}", args.image):
        raise ValueError("An immutable owner-fork registry digest is required")
    if not re.fullmatch(r"[a-f0-9]{40}", args.revision):
        raise ValueError("Exact source revision is required")
    root = Path(__file__).resolve().parents[2]
    backup = args.backup_dir.resolve()
    if not backup.is_relative_to(root / ".milestone0") or backup == root / ".milestone0":
        raise ValueError("Backup must be a named child of the ignored .milestone0 directory")
    env_path = root / ".milestone0/admission.env"
    original = env_path.read_text(encoding="utf-8-sig")
    matches = re.findall(r"^AIF_M0_POSTGRES_PASSWORD=(.*)$", original, re.MULTILINE)
    if len(matches) != 1:
        raise ValueError("Expected exactly one database password assignment")
    old_password = matches[0].strip()
    controller = json.loads(docker("inspect", CONTROLLER).stdout)[0]
    controller_env = dict(item.split("=", 1) for item in controller["Config"]["Env"])
    url = urlsplit(controller_env["DATABASE_URL"])
    if url.hostname != POSTGRES or url.username != "paperclip" or url.path != "/" + DATABASE or unquote(url.password or "") != old_password:
        raise ValueError("Environment file does not match the exact active database target")
    if int(sql("SELECT count(*) FROM heartbeat_runs WHERE status IN ('running', 'queued');")):
        raise RuntimeError("Active/queued runs must finish before cutover")
    if int(sql("SELECT count(*) FROM agents WHERE status NOT IN ('paused', 'terminated');")):
        raise RuntimeError("All agents must be paused before cutover")
    if not tcp_auth(old_password) or tcp_auth(secrets.token_hex(32)):
        raise RuntimeError("Expected password-enforced TCP authentication before rotation")
    data = [m for m in controller["Mounts"] if m["Destination"] == "/paperclip"]
    if len(data) != 1 or data[0].get("Name") != "aif-m0-fork-restore-data":
        raise ValueError("Unexpected Paperclip storage volume")
    docker("pull", args.image, timeout=900)
    image = json.loads(docker("image", "inspect", args.image).stdout)[0]
    if image["Config"]["Labels"].get("org.opencontainers.image.revision") != args.revision:
        raise ValueError("Registry image revision does not match requested source")
    compose = root / "milestone2/compose/paperclip-native-mcp.yaml"
    if args.image not in compose.read_text():
        raise ValueError("Rollout Compose file must pin the requested image")
    if not args.apply:
        print(json.dumps({"ready": True, "mutations": False, "image": args.image, "revision": args.revision}))
        return
    backup.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    docker("stop", "--time", "20", CONTROLLER)
    before = authority_snapshot()
    dump_remote = "/tmp/aif-pre-credential-rotation.dump"
    docker("exec", POSTGRES, "pg_dump", "-U", "paperclip", "-d", DATABASE, "-Fc", "-f", dump_remote)
    docker("cp", f"{POSTGRES}:{dump_remote}", str(backup / "paperclip.dump"))
    entries = docker("exec", POSTGRES, "pg_restore", "-l", dump_remote).stdout.decode().splitlines()
    docker("run", "--rm", "--network", "none", "--mount", "type=volume,source=aif-m0-fork-restore-data,target=/data,readonly",
           "--mount", f"type=bind,source={backup},target=/backup", "--entrypoint", "tar", args.image,
           "-czf", "/backup/paperclip-storage.tar.gz", "-C", "/data", ".", timeout=300)
    with tarfile.open(backup / "paperclip-storage.tar.gz") as archive:
        storage_entries = len(archive.getmembers())
    (backup / "before.json").write_text(json.dumps(before, indent=2) + "\n")
    # Protected local recovery material only; never print it or add it to Git.
    (backup / "previous.env").write_text(original)
    new_password = secrets.token_hex(32)
    updated = re.sub(r"^AIF_M0_POSTGRES_PASSWORD=.*$", "AIF_M0_POSTGRES_PASSWORD=" + new_password, original, flags=re.MULTILINE)
    pending = backup / "rotated.env"
    pending.write_text(updated)
    sql("SET log_statement='none'; SET log_min_error_statement='panic'; "
        f"ALTER ROLE paperclip WITH PASSWORD '{new_password}';")
    if tcp_auth(old_password) or not tcp_auth(new_password):
        raise RuntimeError("Rotation authentication assertions failed; controller remains stopped, recovery material preserved")
    replacement = env_path.with_suffix(".env.pending")
    replacement.write_text(updated)
    os.replace(replacement, env_path)
    base = ["compose", "--env-file", str(env_path)]
    docker(*base, "-f", str(root / "milestone0/compose/paperclip.yaml"), "up", "-d", "--no-deps", "postgres")
    health(POSTGRES)
    docker(*base, "-f", str(root / "milestone0/compose/paperclip-fork-readmission.yaml"), "-f", str(compose),
           "up", "-d", "--no-deps", "paperclip-fork")
    health(CONTROLLER)
    after = authority_snapshot()
    if before != after:
        (backup / "after.json").write_text(json.dumps(after, indent=2) + "\n")
        raise RuntimeError("Authority snapshot changed; inspect checksums before enabling agents")
    if tcp_auth(old_password) or not tcp_auth(new_password):
        raise RuntimeError("Post-restart password assertions failed")
    receipt = {"status": "PASS", "image": args.image, "revision": args.revision,
        "data_preserved": before == after, "old_tcp_auth": False, "new_tcp_auth": True,
        "auth_endpoint": f"{POSTGRES}:5432 (Docker service address, not trusted loopback)",
        "schema": after["schema"], "records": after,
        "database_backup_sha256": sha256(backup / "paperclip.dump"),
        "storage_backup_sha256": sha256(backup / "paperclip-storage.tar.gz"),
        "dump_entries": len(entries), "storage_entries": storage_entries,
        "controller_downtime_seconds": round(time.monotonic() - started, 1), "agents_remain_paused": True}
    (backup / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError) as error:
        print(f"STOP: {error}. Agents remain paused; protected recovery material is preserved.")
        raise SystemExit(1)
    except (OSError, subprocess.TimeoutExpired):
        # Avoid tracebacks with subprocess/config reprs containing credentials.
        print("STOP: cutover did not complete; agents remain paused. Inspect protected local recovery state before retrying.")
        raise SystemExit(1)
