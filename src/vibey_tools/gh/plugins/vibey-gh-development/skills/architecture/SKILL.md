---
name: architecture
description: This skill should be used when designing or changing vibey-gh configuration, policy logic, adapters, CLI commands, templates, or cross-repository contracts.
---
# Architecture

Read `AGENTS.md`, `docs/architecture.md`, and `references/boundaries.md`. Keep policy
decisions deterministic and isolate subprocess/network mutation. Update template,
renderer, dogfood copy, docs, and contract tests as one change. Preserve Python 3.11 and
the dependency-free runtime.

## Resources
- `references/boundaries.md` documents layer and mutation boundaries.
