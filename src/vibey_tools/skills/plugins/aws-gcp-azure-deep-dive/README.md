# AWS, GCP and Azure Deep Dive Plugin

A comparative reference for the three major cloud providers, written to separate genuine architectural differences from marketing: an honest framing of what actually differs, shared responsibility, the identity and access models where the providers really do diverge, resource hierarchy, networking, compute, containers, serverless, storage, databases, analytics and AI services, observability, cost mechanics, reliability and SLAs, infrastructure as code, an honest account of lock-in and multi-cloud, migration, and a service equivalence mapping.

One reference, split into 5 skills along its section groups so a task loads only the part it needs. Section numbers (§N) are shared across the set and cross-references into a sibling skill are written as §N → `skill`. Reference, not tutorial: sections are independent, every claim is tagged by how durable it is (stable fundamentals vs. versioned specifics vs. genuinely contested questions), and a currency snapshot (verified August 2026) flags what goes stale first.

## Skills

- **hyperscaler-framing-responsibility-identity-and-hierarchy** — The Honest Framing, Shared Responsibility, Identity and Access, and Resource Hierarchy (§0–§4): Routing; The Honest Framing; Shared Responsibility; ⚠️ Identity and Access — Where They Genuinely Differ; Resource Hierarchy and Organization.
- **hyperscaler-networking-compute-containers-and-serverless** — Networking, Compute, Containers and Kubernetes, and Serverless (§5–§8): Networking; Compute; Containers and Kubernetes; Serverless.
- **hyperscaler-storage-databases-analytics-and-observability** — Storage, Databases, Analytics, AI/ML Services, and Observability (§9–§13): Storage; Databases; Analytics; AI/ML Services; Observability.
- **hyperscaler-cost-reliability-iac-lock-in-and-migration** — Cost Mechanics, Reliability and SLAs, Infrastructure as Code, Lock-In, and Migration (§14–§18): ⚠️ Cost Mechanics; Reliability, Regions and SLAs; Infrastructure as Code; ⚠️ Lock-In and Multi-Cloud, Honestly; Migration.
- **hyperscaler-reference** — Anti-Patterns, Service Equivalence, What Moved, and Numbers (§19–§26): Anti-Patterns; Service Equivalence; What Moved; Misconceptions; Numbers; Resources; Quick Reference; Method.
