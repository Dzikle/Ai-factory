import { execFileSync } from "node:child_process";

// Run inside the Paperclip image with: docker exec -i <controller> node - <home> <expected...>
// Feed this file on stdin. Never print the Codex catalog: it contains bearer tokens.
const [home, ...expectedNames] = process.argv.slice(2);
if (!home || expectedNames.length === 0) {
  throw new Error("usage: node - <codex-home> <expected-server-name>...");
}

const catalog = JSON.parse(execFileSync("codex", ["mcp", "list", "--json"], {
  encoding: "utf8",
  env: { ...process.env, CODEX_HOME: home },
  timeout: 30_000,
}));
if (!Array.isArray(catalog)) throw new Error("Codex returned a non-array MCP catalog");

const actualNames = catalog.map((entry) => entry.name).sort();
const expected = [...expectedNames].sort();
if (JSON.stringify(actualNames) !== JSON.stringify(expected)) {
  throw new Error(`MCP server names differ: expected ${expected.join(",")}; actual ${actualNames.join(",")}`);
}
for (const entry of catalog) {
  const authorization = entry.transport?.http_headers?.Authorization;
  if (typeof authorization !== "string" || !authorization.startsWith("Bearer ")) {
    throw new Error(`Codex did not load the governed Authorization header for ${entry.name}`);
  }
}
console.log(`PASS: Codex loaded ${catalog.length} expected governed MCP servers with bearer headers`);
