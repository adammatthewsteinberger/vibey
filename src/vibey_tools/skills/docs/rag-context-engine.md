# Retrieval context engine

The `vibey-skills` context engine builds a deterministic, local SQLite FTS5 index over the
authoritative `plugins/*/skills/*/SKILL.md` corpus. It retrieves complete Markdown heading
sections and compiles a bounded context packet with exact source provenance. The default path
is standard-library-only and makes no network calls.

This is a lexical baseline, not a claim that retrieval has already reduced production cost.
Measure **cost per accepted work item** before enabling packet injection. The design and
rollout rationale is in the [implementation plan](rag-context-engine-plan.md).

## Architecture and formats

Indexing parses frontmatter and Markdown headings, records exact source-relative paths and
line ranges, hashes source and section content, and creates stable chunk IDs. An index
directory contains:

- `manifest.json`, the content-addressed skills and chunk manifest; and
- `index.sqlite3`, metadata plus an FTS5 table queried only with bound parameters.

A packet request is a versioned JSON object. Useful fields include `title`, `objective`,
`requirements`, `acceptance_criteria`, `phase`, `job_kind`, `languages`, `dependencies`,
`paths`, `commands`, `required_plugins`, `excluded_plugins`, `required_skills`,
`excluded_skills`, and `maximum_context_tokens`. Strict mode rejects unknown fields.

Packet Markdown contains complete selected sections. Its JSON manifest records the corpus and
query hashes, deterministic input signals, selected plugins and skills, scores, selection
reasons, source hashes, line ranges, token estimates, omissions, fallback status, and packet
hash. `low_confidence` directs the caller to activate native full skills. If mandatory content
cannot fit, `budget_insufficient` is returned instead of truncating rules.

## Optional retrieval metadata

Existing skill frontmatter remains valid. Skills may add list-valued `domains`, `phases`,
`languages`, `technologies`, and `mandatory_sections`, plus `retrieval_version: 1`.
`mandatory_sections` values must exactly match headings in that skill. The standard manifest
validator rejects unsupported versions, malformed list values, duplicate names, source
escapes, and missing mandatory headings.

```yaml
domains:
  - testing
phases:
  - build
  - verify
languages:
  - python
technologies:
  - postgresql
mandatory_sections:
  - Verification requirements
retrieval_version: 1
```

## Commands

```bash
vibey-skills index build --output .vibey-skills/index
vibey-skills index inspect .vibey-skills/index --json
vibey-skills search "pytest xdist postgres" --index .vibey-skills/index --json
vibey-skills packet --request task.json --index .vibey-skills/index \
  --budget 6000 --output packet.md --manifest packet.json
vibey-skills evaluate --index .vibey-skills/index \
  --cases tests/fixtures/rag_gold.json --top-k 10
```

JSON result data is written to stdout; errors and diagnostics are written to stderr. Generated
indexes and common packet filenames are ignored by Git.

## Vibey process contract

Vibey should invoke the CLI as a subprocess rather than import package internals. It supplies
the request as a JSON file, checks the exit code, parses the packet manifest, and injects the
Markdown only when `status` is `ok`. Exit code `2` means a structured non-success such as
`low_confidence` or `budget_insufficient`; the caller must use the manifest's fallback or
adjust the budget. Exit code `1` means invalid input or an invalid index.

## Security and privacy

Only authoritative skill files are indexed. Symlinked skill sources and symlinked index
boundaries fail closed. Search text is always a SQLite value parameter and the database is
opened read-only. Query provenance redacts labelled credentials and common provider-token
shapes. The engine never executes skill or query text and never reads arbitrary repository
files. Do not send corpus or repository text to an embedding provider; semantic retrieval is
outside this offline baseline.

## Evaluation and benchmark reproduction

The committed 50-case set covers testing, RAG, cost control, cloud resilience, Kubernetes,
frontend performance, cryptography, mobile development, and Linux operations. Evaluation
reports skill recall and mandatory-section recall without persisting raw query text.

For shadow measurements, create request JSON from at least ten historical work items, generate
packets without injecting them, and record baseline skill tokens, projected packet tokens,
latency, turns, retries, verification result, and agent cost. Do not record secrets or raw
private repository content. Compare:

```text
(agent cost + retrieval cost + retry cost) / accepted work items
```

Proceed to an embedding experiment or production A/B test only after the lexical baseline
shows 100% mandatory recall and enough evidence to detect a quality regression. Generated
benchmark results are local artifacts and must not be committed.
