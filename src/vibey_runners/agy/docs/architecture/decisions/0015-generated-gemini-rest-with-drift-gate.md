# ADR 0015: Generated Gemini REST CLI with a drift gate

## Status

Accepted (2026-08-13). Supersedes [ADR 0006](0006-defer-genai-rest.md).

## Context

ADR 0006 deferred `agyloop api` because neither stability-criterion clause
held: the Gemini Developer discovery document is a daily-revision `v1beta`
inventory, and `google-antigravity` is still 0.1.x preview. An operator
override asked to ship the surface anyway.

Architecture §14 still applies: bind **discovery document A**, treat OpenAPI
**B as a cross-check**, model the Developer vs Vertex split, and make "no
gaps" real with a drift gate.

## Decision

Ship `agyloop api` generated from the committed Developer discovery baseline:

- Substrate: `https://generativelanguage.googleapis.com/$discovery/rest?version=v1beta`
- Committed snapshot: `src/agyloop/infrastructure/api/surface_baseline.json`
  (revision `20260812`, **84** methods)
- OpenAPI cross-check: the same revision lists **91** operations. The mismatch
  is recorded in the baseline (`openapi_operation_count`) so we do not silently
  switch substrates.
- Drift tests: discovered count equals the committed count; every method is
  registered on the Click tree; hiding one method from the registry is
  detectable.
- `--lane developer` (default) serves that tree. `--lane vertex` serves a
  disjoint Gemini subset of `aiplatform:v1` (revision `20260801`, **33**
  methods: generateContent / predict / countTokens / embedContent family).
  Developer command paths are refused on the Vertex lane and vice versa.
  Vertex auth is `GOOGLE_ACCESS_TOKEN` (or `CLOUDSDK_AUTH_ACCESS_TOKEN`).
- Invokes are raw HTTPS + `GOOGLE_API_KEY` (Developer). No `google-genai` SDK
  dependency. No Anthropic imports.

Regenerate the baseline by fetching the discovery document and rewriting
`surface_baseline.json`. CI must fail if the inventory drifts without that
commit.

## Consequences

- `agyloop api` is present. Help cites this ADR.
- The surface can rot when Google revises `v1beta`; the drift gate is the
  intended alarm, not a promise of a frozen API.
- Vertex remains a filtered Gemini subset of Vertex AI, not the full 1100+
  method aiplatform surface. Regen `vertex_baseline.json` from the v1
  discovery document and keep the filter in the drift tests.
