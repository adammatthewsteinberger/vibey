# Package Manager Development Plugin

A deep technical reference for building and reasoning about package managers and registries: the anatomy of a package manager (manifest, resolver, lockfile, fetcher, linker, cache), version schemes and constraint syntax, dependency resolution algorithms, lockfile design and reproducibility, installation layouts, registry architecture and APIs, publishing and authentication, supply-chain attacks and defenses, caching and performance, monorepos and workspaces, lifecycle scripts, deprecation and yanking, governance, and a cross-ecosystem comparison of npm, pip/uv, Cargo, Go modules, Maven, NuGet, apt/dnf, Nix, and others.

One reference, split into 5 skills along its section groups so a task loads only the part it needs. Section numbers (§N) are shared across the set and cross-references into a sibling skill are written as §N → `skill`. Reference, not tutorial: sections are independent, every claim is tagged by how durable it is (stable fundamentals vs. versioned specifics vs. genuinely contested questions), and a currency snapshot (verified August 2026) flags what goes stale first.

## Skills

- **package-manager-versioning-and-resolution** — Versions, Manifests, Dependency Resolution, and Lockfiles (§0–§4): Routing; Versions and Constraints; The Manifest; Dependency Resolution — the hard part; Lockfiles.
- **package-manager-registries-and-installation** — Registry Design, Cache, Layout, and Linking, Publishing and Authentication (§5–§7): Registry Design; Cache, Layout, and Linking; Publishing and Authentication.
- **package-manager-supply-chain-and-workspaces** — Supply-Chain Security, Lifecycle Scripts, and Workspaces (§8–§10): Supply-Chain Security; Lifecycle Scripts and Building; Workspaces, Monorepos, and Overrides.
- **package-manager-ux-ecosystems-and-governance** — Performance, UX, the Ecosystem Comparison, and Governance (§11–§14): Performance; UX; The Ecosystem Comparison; Governance and Sustainability.
- **package-manager-reference** — Anti-Patterns, Contested Questions, Currency, and Canon (§15–§20): Anti-Patterns; Contested Questions; Currency Snapshot; The Canon; Quick Reference; Sources and Method.
