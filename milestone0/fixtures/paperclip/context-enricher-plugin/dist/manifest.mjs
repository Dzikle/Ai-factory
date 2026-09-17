const manifest = {
  id: "ai-factory.milestone0-context-enricher",
  apiVersion: 1,
  version: "0.0.0-admission",
  displayName: "Milestone 0 Context Enricher",
  description: "Admission-only deterministic pre-run enrichment fixture.",
  author: "AI Factory",
  categories: ["automation"],
  capabilities: ["agent.run.enrich"],
  entrypoints: {
    worker: "./dist/worker.mjs"
  }
};

export default manifest;
