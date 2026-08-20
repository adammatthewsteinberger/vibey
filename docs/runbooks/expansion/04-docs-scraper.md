# Runbook: integration docs scraper — self-maintaining adapters

## Goal

A watcher that monitors the documentation of every external surface vibey
integrates with, detects drift, and turns each change into work vibey
executes on itself: raise a finding → open a vibey project (or Jira
ticket, post-01) → an engine session updates the affected adapter → gates
prove it → PR.

## Watched surfaces (initial registry)

| Surface | Source of truth |
|---|---|
| claudeloop/codexloop/cursorloop/agyloop | their repos' docs + `--help` output |
| GitHub Copilot CLI | github.blog changelog feed + `copilot --help` |
| Jira Cloud REST v3 | developer.atlassian.com changelog |
| az / aws / gcloud CLIs | release notes feeds + `<cli> version` |
| App Store Connect / Play Developer APIs | Apple/Google release notes |
| KEDA / kopf / Helm | GitHub releases |
| OpenClaw skill format / Moltbook API | docs.openclaw.ai, moltbook docs |
| Anthropic/OpenAI/Google LLM APIs | provider changelogs |

## Design

- `infrastructure/docwatch/registry.py`: declarative registry — each entry
  has a fetcher (RSS/Atom, GitHub releases API, HTML page + CSS selector,
  or local `--help` capture), a canonicalizer (strip dates/ads →
  normalized markdown), and an `owner_paths` list mapping the surface to
  the adapter files it governs.
- `docwatch.scan` job kind (serial, scheduled): fetch → canonicalize →
  SHA-256 → compare against the stored digest in a `doc_snapshot` table
  (append-only, like everything else). On change: store the new snapshot,
  diff the two normalized texts, and record a `FindingRaised` ledger event
  scoped to the owning adapter.
- **Change triage is a model call, upgrades are engine sessions**: the
  finding's payload carries the diff; a `docwatch.triage` job asks an
  engine (TRIVIAL effort) "does this diff affect `owner_paths`? breaking /
  additive / cosmetic?". Breaking/additive → seed a vibey project on the
  owning repo with the diff + affected files as DESIGN input. Cosmetic →
  resolve the finding with the classification recorded.
- Local `--help` capture is the cheapest, most truthful watcher for CLIs
  — the flags conformance check (#33) already proved help output catches
  real drift. Reuse it.
- Everything idempotent: digest-keyed snapshots, finding ids derived from
  (surface, digest-pair).

## Work items

1. `doc_snapshot` table + migration + repository (append-only).
2. Registry + three fetcher kinds (feed, releases-API, help-capture) with
   fixture tests; HTML fetcher with a strict allowlist.
3. `docwatch.scan` handler + scheduling (worker heartbeat or cron job row).
4. Canonicalizer + differ (pure, `domain/` if truly pure).
5. `docwatch.triage` handler → finding resolution or project seeding.
6. CLI: `vibey docwatch list|scan|status`.
7. Live: point at the real Copilot changelog feed, replay a known past
   change, prove a project gets seeded with the right owner_paths.

## Verification

Fixture gates green. Replay test: feed two archived versions of a real
changelog through the pipeline and assert the seeded project's DESIGN
input contains the diff and owner paths. One real scheduled scan runs
overnight without raising false positives on unchanged docs.

## Needs from operator

Nothing (public feeds). Optional: a GitHub token to raise API rate limits.

## Risks

- False positives from page chrome → canonicalizer strips aggressively;
  cosmetic classification is the safety valve.
- Watching too much too often → scans are daily by default, per-surface
  overrides, ETag/If-None-Match caching.
- A scraped page is untrusted input: diffs are data for triage, never
  instructions executed verbatim (prompt-shield already exists,
  `domain/prompt_shield.py` — reuse it on scraped content).
