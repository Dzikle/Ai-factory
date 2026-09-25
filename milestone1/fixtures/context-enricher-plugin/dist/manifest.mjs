export default {
  id: "ai-factory.milestone1-git-context",
  apiVersion: 1,
  version: "0.1.0",
  displayName: "Verified Git context",
  description: "Provides one bounded, source-verified Git document excerpt before a run.",
  author: "AI Factory",
  categories: ["automation"],
  capabilities: ["agent.run.enrich"],
  entrypoints: { worker: "./dist/worker.mjs" },
};
