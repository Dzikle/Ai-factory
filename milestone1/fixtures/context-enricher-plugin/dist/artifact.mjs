import { randomUUID } from "node:crypto";
import { link, mkdir, readFile, unlink, writeFile } from "node:fs/promises";
import path from "node:path";

export async function publishArtifact(dir, runId, bytes) {
  if (!/^[a-zA-Z0-9-]{1,100}$/.test(runId) || !Buffer.isBuffer(bytes)) {
    throw new Error("invalid context artifact input");
  }
  await mkdir(dir, { recursive: true });
  const final = path.join(dir, `${runId}.json`);
  const temporary = path.join(dir, `.${runId}.${randomUUID()}.tmp`);
  await writeFile(temporary, bytes, { flag: "wx" });
  try {
    try {
      await link(temporary, final);
    } catch (error) {
      if (error?.code !== "EEXIST") throw error;
      const existing = await readFile(final);
      if (!existing.equals(bytes)) throw new Error("same run already has a different artifact");
    }
  } finally {
    await unlink(temporary);
  }
  return `file://${final.replaceAll("\\", "/")}`;
}
