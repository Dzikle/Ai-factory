"""Quiesced local backup, disposable DB/storage restore, and artifact verification.

Uses the existing controller and PostgreSQL images. Restored agents remain
paused and the test controller exposes no host port. Private backups are retained
under .milestone0; only resources created by this invocation are removed.
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import secrets
import subprocess
import tarfile
import time
from urllib.parse import urlsplit
from uuid import UUID, uuid4

from milestone2.scripts.rotate_local_paperclip_database import (
    CONTROLLER, DATABASE, POSTGRES, TABLES, docker, health, sha256,
)


def artifact_manifest(rows):
    if not isinstance(rows, list) or not rows:
        raise ValueError("At least one persisted enriched run is required")
    result = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str):
            raise ValueError("Invalid enriched run identity")
        run_id = str(UUID(row["id"]))
        enrichment = row.get("enrichment")
        if not isinstance(enrichment, dict) or enrichment.get("version") != 1:
            raise ValueError("Missing persisted enrichment")
        entries = enrichment.get("entries")
        if not isinstance(entries, list) or not 1 <= len(entries) <= 4:
            raise ValueError("Invalid persisted enrichment entries")
        for entry in entries:
            artifact = entry.get("artifact") if isinstance(entry, dict) else None
            ref = artifact.get("ref") if isinstance(artifact, dict) else None
            expected_ref = f"file:///paperclip/milestone1-context/{run_id}.json"
            if (ref != expected_ref or not isinstance(artifact.get("sha256"), str)
                    or not re.fullmatch(r"[a-f0-9]{64}", artifact["sha256"])
                    or type(artifact.get("byteSize")) is not int or not 0 <= artifact["byteSize"] <= 100_000):
                raise ValueError("Unsupported or invalid context artifact")
            result.append({"runId": run_id, "ref": ref, "path": ref.removeprefix("file://"),
                           "sha256": artifact["sha256"], "byteSize": artifact["byteSize"]})
    return result


def sql_db(query, database=DATABASE, postgres=POSTGRES):
    if database != DATABASE and not re.fullmatch(r"aif_m4_restore_[a-f0-9]{12}", database):
        raise ValueError("Unexpected database target")
    if postgres != POSTGRES and not re.fullmatch(r"aif-m4-restore-postgres-[a-f0-9]{12}", postgres):
        raise ValueError("Unexpected PostgreSQL container")
    return docker("exec", "-i", postgres, "psql", "-X", "-v", "ON_ERROR_STOP=1", "-U", "paperclip",
                  "-d", database, "-At", stdin=query.encode()).stdout.decode().strip()


def snapshot(database=DATABASE, postgres=POSTGRES):
    records = {}
    for table in TABLES:
        count, checksum = sql_db(
            f"SELECT count(*), md5(coalesce(string_agg(to_jsonb(t)::text, '' ORDER BY id), '')) FROM {table} t;",
            database, postgres,
        ).split("|")
        records[table] = {"count": int(count), "rows_md5": checksum}
    records["schema"] = sql_db("SELECT count(*) || '|' || max(created_at) FROM drizzle.__drizzle_migrations;", database, postgres)
    return records


def assert_quiescent(database=DATABASE, postgres=POSTGRES):
    if int(sql_db("SELECT count(*) FROM heartbeat_runs WHERE status IN ('queued','running');", database, postgres)):
        raise RuntimeError("Queued/running work prevents a consistent restore drill")
    if int(sql_db("SELECT count(*) FROM agents WHERE status NOT IN ('paused','terminated');", database, postgres)):
        raise RuntimeError("Pause all agents before the restore drill")


def run(backup, image_ref, revision, run_ids):
    root = Path(__file__).resolve().parents[1]
    backup = Path(backup).resolve()
    if not backup.is_relative_to(root / ".milestone0") or backup == root / ".milestone0" or backup.exists():
        raise ValueError("Use a new named backup directory inside ignored .milestone0")
    if not re.fullmatch(r"ghcr\.io/dzikle/paperclip@sha256:[a-f0-9]{64}", image_ref):
        raise ValueError("An immutable owner image digest is required")
    if not re.fullmatch(r"[a-f0-9]{40}", revision):
        raise ValueError("An exact source revision is required")
    run_ids = [str(UUID(value)) for value in run_ids]
    if not 1 <= len(run_ids) <= 8 or len(set(run_ids)) != len(run_ids):
        raise ValueError("Select one to eight distinct enriched runs")
    controller = json.loads(docker("inspect", CONTROLLER).stdout)[0]
    postgres = json.loads(docker("inspect", POSTGRES).stdout)[0]
    image = json.loads(docker("image", "inspect", image_ref).stdout)[0]
    if (controller["Image"] != image["Id"]
            or image["Config"]["Labels"].get("org.opencontainers.image.revision") != revision):
        raise ValueError("Active image and source revision do not match the requested pin")
    mounts = [mount for mount in controller["Mounts"] if mount["Destination"] == "/paperclip"]
    if len(mounts) != 1 or mounts[0].get("Name") != "aif-m0-fork-restore-data":
        raise ValueError("Unexpected authoritative Paperclip storage volume")
    source_environment = dict(item.split("=", 1) for item in controller["Config"]["Env"])
    database_url = urlsplit(source_environment["DATABASE_URL"])
    if database_url.hostname != POSTGRES or database_url.username != "paperclip" or database_url.path != "/" + DATABASE:
        raise ValueError("Unexpected authoritative database URL")
    health(CONTROLLER)
    assert_quiescent()
    backup.mkdir(parents=True)
    suffix = uuid4().hex[:12]
    restore_db = "aif_m4_restore_" + suffix
    restore_volume = "aif-m4-restore-storage-" + suffix
    restore_controller = "aif-m4-restore-controller-" + suffix
    restore_postgres = "aif-m4-restore-postgres-" + suffix
    restore_network = "aif-m4-restore-net-" + suffix
    dump_remote = "/tmp/aif-m4-restore-" + suffix + ".dump"
    started = time.monotonic()
    stopped = pg_created = network_created = volume_created = container_created = False
    receipt = None
    private_env = backup / "restore.env"
    private_pg_env = backup / "restore-postgres.env"
    try:
        docker("stop", "--time", "20", CONTROLLER)
        stopped = True
        before = snapshot()
        selected = ",".join("'" + value + "'" for value in run_ids)
        rows = json.loads(sql_db("SELECT coalesce(jsonb_agg(jsonb_build_object('id', id, 'enrichment', "
                                "context_snapshot->'paperclipRunContextEnrichment') ORDER BY id), '[]'::jsonb) "
                                f"FROM heartbeat_runs WHERE id IN ({selected});"))
        if {row["id"] for row in rows} != set(run_ids):
            raise ValueError("A selected run is missing")
        artifacts = artifact_manifest(rows)
        docker("exec", POSTGRES, "pg_dump", "-U", "paperclip", "-d", DATABASE, "-Fc", "-f", dump_remote)
        docker("cp", f"{POSTGRES}:{dump_remote}", str(backup / "paperclip.dump"))
        docker("run", "--rm", "--network", "none", "--user", "0:0",
               "--mount", "type=volume,source=aif-m0-fork-restore-data,target=/data,readonly",
               "--mount", f"type=bind,source={backup},target=/backup", "--entrypoint", "tar", image_ref,
               "-czf", "/backup/paperclip-storage.tar.gz", "-C", "/data", ".", timeout=300)
        docker("start", CONTROLLER)
        stopped = False
        health(CONTROLLER)
        docker("network", "create", "--internal", "--label", "ai-factory.drill=milestone4", restore_network)
        network_created = True
        restore_password = secrets.token_hex(32)
        private_pg_env.write_text(f"POSTGRES_USER=paperclip\nPOSTGRES_DB={restore_db}\nPOSTGRES_PASSWORD={restore_password}\n", encoding="utf-8")
        docker("run", "-d", "--name", restore_postgres, "--network", restore_network,
               "--env-file", str(private_pg_env), "--tmpfs", "/var/lib/postgresql/data:rw,size=768m",
               "--health-cmd", f"pg_isready -U paperclip -d {restore_db}",
               "--health-interval", "2s", "--health-timeout", "5s", "--health-retries", "30",
               "--label", "ai-factory.drill=milestone4", postgres["Image"])
        pg_created = True
        health(restore_postgres)
        docker("cp", str(backup / "paperclip.dump"), f"{restore_postgres}:/tmp/restore.dump")
        docker("exec", restore_postgres, "pg_restore", "--exit-on-error", "-U", "paperclip", "-d", restore_db,
               "/tmp/restore.dump", timeout=300)
        if snapshot(restore_db, restore_postgres) != before:
            raise RuntimeError("Restored authority rows or schema differ from the captured source")
        assert_quiescent(restore_db, restore_postgres)
        docker("volume", "create", "--label", "ai-factory.drill=milestone4", restore_volume)
        volume_created = True
        docker("run", "--rm", "--network", "none", "--user", "0:0",
               "--mount", f"type=volume,source={restore_volume},target=/data",
               "--mount", f"type=bind,source={backup},target=/backup,readonly", "--entrypoint", "tar", image_ref,
               "-xzf", "/backup/paperclip-storage.tar.gz", "-C", "/data", timeout=300)
        necessary = {"BETTER_AUTH_SECRET", "PAPERCLIP_AGENT_JWT_SECRET", "PAPERCLIP_SECRETS_MASTER_KEY",
                     "PAPERCLIP_SECRETS_STRICT_MODE", "PAPERCLIP_MIGRATION_AUTO_APPLY",
                     "PAPERCLIP_DEPLOYMENT_MODE", "PAPERCLIP_DEPLOYMENT_EXPOSURE", "PORT",
                     "PAPERCLIP_BIND", "PAPERCLIP_BIND_HOST"}
        environment = {key: value for key, value in source_environment.items() if key in necessary}
        environment.update(DATABASE_URL=f"postgresql://paperclip:{restore_password}@{restore_postgres}:5432/{restore_db}",
                           PAPERCLIP_API_URL=f"http://{restore_controller}:3100",
                           PAPERCLIP_PUBLIC_URL="http://localhost:3100",
                           PAPERCLIP_ALLOWED_HOSTNAMES=f"localhost,127.0.0.1,{restore_controller}")
        if any("\n" in key + value or "\r" in key + value for key, value in environment.items()):
            raise ValueError("Unsupported newline in private restore environment")
        private_env.write_text("\n".join(key + "=" + value for key, value in environment.items()) + "\n", encoding="utf-8")
        docker("run", "-d", "--name", restore_controller, "--network", restore_network,
               "--env-file", str(private_env), "--mount", f"type=volume,source={restore_volume},target=/paperclip",
               "--health-cmd", "curl --fail --silent http://127.0.0.1:3100/api/health",
               "--health-interval", "5s", "--health-timeout", "5s", "--health-retries", "20",
               "--health-start-period", "20s",
               "--label", "ai-factory.drill=milestone4", image_ref)
        container_created = True
        health(restore_controller)
        assert_quiescent(restore_db, restore_postgres)
        if snapshot(restore_db, restore_postgres) != before:
            raise RuntimeError("Restored controller changed authority-table evidence")
        for artifact in artifacts:
            actual = docker("exec", restore_controller, "sha256sum", artifact["path"]).stdout.decode().split()[0]
            size = int(docker("exec", restore_controller, "stat", "-c", "%s", artifact["path"]).stdout)
            if actual != artifact["sha256"] or size != artifact["byteSize"]:
                raise RuntimeError("Restored artifact bytes do not match the durable run snapshot")
        with tarfile.open(backup / "paperclip-storage.tar.gz") as archive:
            members = len(archive.getmembers())
        receipt = {"status": "PASS", "observedAt": datetime.now(timezone.utc).isoformat(),
                   "image": image_ref, "revision": revision, "records": before,
                   "sourceControllerHealthy": True, "restoredControllerHealthy": True,
                   "restoreNetworkInternal": True, "restoreDatabaseSeparate": True,
                   "postgresImageId": postgres["Image"],
                   "agentsRemainPaused": True, "restoredArtifacts": artifacts,
                   "databaseBackupSha256": sha256(backup / "paperclip.dump"),
                   "storageBackupSha256": sha256(backup / "paperclip-storage.tar.gz"),
                   "storageArchiveEntries": members, "elapsedSeconds": round(time.monotonic() - started, 1)}
    finally:
        cleanup = [(stopped, ("start", CONTROLLER)),
                   (container_created, ("rm", "-f", restore_controller)),
                   (pg_created, ("rm", "-f", restore_postgres)),
                   (volume_created, ("volume", "rm", restore_volume)),
                   (network_created, ("network", "rm", restore_network)),
                   (True, ("exec", POSTGRES, "rm", "-f", dump_remote))]
        errors = []
        for enabled, command in cleanup:
            if enabled:
                try:
                    docker(*command)
                except (RuntimeError, OSError, subprocess.TimeoutExpired):
                    errors.append(command[0])
        private_env.unlink(missing_ok=True)
        private_pg_env.unlink(missing_ok=True)
        if errors:
            raise RuntimeError("Disposable restore cleanup requires attention")
    if receipt is None:
        raise RuntimeError("Restore drill ended without verification evidence")
    (backup / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backup-dir", type=Path, required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--run", action="append", required=True, help="persisted enriched run UUID; may repeat")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(run(args.backup_dir, args.image, args.revision, args.run)))
        return 0
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, AttributeError, subprocess.TimeoutExpired):
        print("Restore drill did not pass. Private backups are preserved; inspect local state before retrying.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
