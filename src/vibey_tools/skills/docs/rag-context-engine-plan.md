# Vibey Skills Context Engine

## Objective

Build a local-first retrieval and context-compilation engine for `vibey-skills` that reduces
the total cost per accepted Vibey work item without weakening mandatory instructions,
verification, provenance, or reproducibility.

The product is a **skill router and context compiler**, not a generic chatbot and not merely
a vector database. It must select the most relevant plugin, skill, and Markdown sections for
a work item; preserve every mandatory rule from activated skills; enforce a configurable
token budget; and produce an immutable, auditable context packet that Vibey can inject into
an engine plan.

## Why now

The marketplace currently contains 127 plugins, 644 long-form skills, approximately 1.29
million words, 9.2 MB of Markdown, and 3,661 second-level sections. The corpus is large enough
that installing or reading skills indiscriminately creates unnecessary context pressure, yet
small enough that a local SQLite index can serve it without a distributed retrieval service.

Native Agent Skills already provide progressive disclosure at the skill level. This project
must complement that mechanism rather than replace it. The expected benefit is not based on
the false premise that every run currently loads the entire corpus. Savings should come from:

- activating fewer irrelevant skills;
- retrieving only pertinent sections from long skills;
- deduplicating passages across turns;
- reducing exploratory tool calls and context reconstruction;
- avoiding failed attempts and repair loops caused by missing domain guidance; and
- enabling cheaper models when retrieval has supplied sufficient task knowledge.

The primary economic metric is **cost per accepted work item**, not retrieval precision in
isolation and not raw prompt-token reduction.

## Product principles

1. **Mandatory rules are never similarity-ranked away.** Safety, destructive-action,
   verification, architecture, licensing, provenance, and repository-hygiene rules must be
   supplied deterministically whenever their skill is activated.
2. **Deterministic routing precedes semantic retrieval.** Exact repository signals such as
   paths, dependencies, commands, languages, frameworks, phase, and error class are stronger
   evidence than embedding similarity.
3. **Lexical retrieval is the baseline.** SQLite FTS5 must be implemented and measured before
   embeddings are introduced.
4. **Embeddings are an optional reranking enhancement.** The engine must work offline without
   an API key or network access.
5. **Every passage is attributable.** A packet must identify the exact release, plugin, skill,
   heading path, source file, line range, and content hash for every included passage.
6. **Indexes are content-addressed and reproducible.** The same corpus and configuration must
   yield the same manifest, chunks, rankings, and packet in deterministic mode.
7. **No hidden quality trade.** A cost reduction is accepted only if task success,
   verification, safety, and mandatory-rule recall do not regress.
8. **Keep the package lightweight.** The existing runtime has no dependencies. The walking
   skeleton should use the Python standard library and SQLite FTS5; optional embedding support
   must not make the base CLI depend on a hosted service.

## Scope

### In scope

- Heading-aware parsing of all `plugins/*/skills/*/SKILL.md` files.
- An optional, backward-compatible retrieval metadata schema in skill frontmatter.
- A content-addressed corpus manifest.
- A local SQLite metadata and FTS5 index.
- Hierarchical plugin, skill, and section routing.
- Deterministic repository-signal and work-item-signal extraction from a JSON request.
- Hybrid-ready ranking interfaces with lexical retrieval implemented first.
- Mandatory/procedure/reference/example/source content classes.
- Token-budgeted context-packet compilation.
- Exact provenance, retrieval reasons, scores, and hashes in a packet manifest.
- CLI commands for index construction, inspection, search, and packet generation.
- Shadow-mode evaluation against replayable Vibey work items.
- A versioned integration contract that Vibey can consume without importing infrastructure
  internals from this package.
- Documentation, tests, security analysis, and benchmarks.

### Deferred until lexical baseline evidence exists

- Remote vector databases.
- A hosted multi-tenant retrieval service.
- Learning-to-rank from production outcomes.
- Automatic mutation of skill metadata based on agent behavior.
- Replacing native Agent Skills activation.
- Sending private repository content to an embedding provider.
- Vector embeddings in the default, offline installation.

### Explicitly out of scope

- Training or fine-tuning a language model.
- A general-purpose question-answering UI.
- Silently summarizing or rewriting authoritative skill content.
- Relaxing the requirement to read a complete `SKILL.md` when an agent platform or governing
  instruction explicitly requires it.
- Treating generated text as an authoritative replacement for source-cited passages.

## Architecture

The pipeline is hierarchical:

```text
work item + acceptance criteria + repository signals + prior failure
                              |
                              v
                    deterministic filters
        phase, paths, dependencies, commands, language, framework
                              |
                              v
                         plugin routing
                              |
                              v
                          skill routing
                              |
                              v
                  heading-aware lexical search
                              |
                              v
                  optional semantic reranking
                              |
                              v
                 mandatory-rule reconciliation
                              |
                              v
                  bounded context compilation
                              |
                              v
                immutable packet + provenance
```

### Ownership boundary

`vibey-skills` owns:

- source documents and optional retrieval metadata;
- Markdown parsing and chunk boundaries;
- corpus/index formats and versioning;
- local search and packet compilation;
- retrieval evaluation fixtures; and
- stable CLI and JSON contracts.

Vibey owns:

- extraction of live work-item and repository signals;
- phase-specific budgets and policy;
- injection of packets into engine plans;
- per-run cost, turn, retry, and outcome telemetry; and
- A/B rollout controls.

The integration must be process/JSON based initially so the packages remain independently
versioned and neither imports the other's infrastructure.

## Data model

### Corpus manifest

The generated manifest must include:

```json
{
  "schema_version": 1,
  "skills_release": "<package version>",
  "corpus_sha256": "<digest>",
  "generated_at": "<informational timestamp excluded from deterministic digest>",
  "skills": [],
  "chunks": []
}
```

Each skill record includes plugin, name, description, version, category, source path, source
hash, headings, optional retrieval metadata, and mandatory-section declarations.

Each chunk includes:

- stable chunk ID derived from source hash and heading path;
- plugin and skill;
- skill version;
- heading path;
- source-relative path and line range;
- content hash;
- content class: `mandatory`, `procedure`, `reference`, `example`, or `source`;
- normalized text for search; and
- optional tags, phase, languages, technologies, paths, dependencies, and commands.

### Optional frontmatter extension

Existing skills with only `name` and `description` must remain valid. A skill may add:

```yaml
domains:
  - database
phases:
  - build
  - verify
languages:
  - python
technologies:
  - postgresql
  - asyncpg
signals:
  paths:
    - "tests/**"
    - "**/db/**"
  dependencies:
    - asyncpg
  commands:
    - pytest
    - psql
mandatory_sections:
  - Safety and data isolation
  - Verification requirements
retrieval_version: 1
```

The validator must reject unknown types, nonexistent mandatory headings, absolute/private
paths, and metadata that conflicts with the skill directory or manifest.

### Query request

Packet generation accepts a versioned JSON object containing:

- work-item title and objective;
- requirements and acceptance criteria;
- phase and job kind;
- repository languages, dependencies, paths, and commands;
- target or changed files when known;
- prior failure class and a bounded error summary;
- excluded or required plugins/skills;
- maximum context tokens; and
- deterministic or hybrid ranking mode.

Unknown fields must be rejected in strict mode and ignored only under an explicitly versioned
forward-compatibility mode.

### Context packet

The output contains Markdown for the agent plus a JSON manifest containing:

- schema and index version;
- query hash;
- deterministic input signals;
- selected plugins and skills;
- included chunks, scores, reasons, hashes, and token estimates;
- mandatory and retrieved token totals;
- omissions caused by the token budget;
- retrieval latency; and
- fallback or low-confidence decisions.

## Ranking and compilation policy

### Candidate generation

1. Apply explicit required/excluded filters.
2. Score plugin and skill metadata using exact and FTS matches.
3. Add deterministic boosts for phase, path, dependency, command, language, framework, and
   prior-error signals.
4. Search section text only within the resulting candidate skills.
5. Diversify results so adjacent or duplicate sections cannot consume the packet.

### Mandatory reconciliation

After selecting a skill, include all declared mandatory sections before discretionary chunks.
If mandatory content alone exceeds the budget, return a structured `budget_insufficient`
result. Never truncate mandatory text silently.

### Budgeting

- Default packet target: 6,000 estimated tokens.
- Configurable range: 1,000 to 32,000 tokens.
- Reserve space for packet headings and provenance.
- Deduplicate identical content hashes.
- Prefer complete heading sections over arbitrary mid-paragraph truncation.
- Report every relevant chunk omitted for budget reasons.
- Use a deterministic, documented tokenizer approximation in the zero-dependency baseline;
  allow an optional exact tokenizer adapter later.

### Confidence and fallback

Return a low-confidence signal when no candidate clears a measured threshold. The consuming
Vibey integration must then fall back to native full-skill activation or request a broader
packet. Low confidence must never be represented as an empty but successful packet.

## CLI walking skeleton

Implement these stable commands:

```bash
vibey-skills index build --output .vibey-skills/index
vibey-skills index inspect .vibey-skills/index --json
vibey-skills search "pytest xdist postgres template database" --json
vibey-skills packet --request task.json --budget 6000 --output packet.md \
  --manifest packet.json
```

All commands must support source checkouts and installed wheels. Generated index and packet
artifacts must not be committed by default; add appropriate ignore rules if the default path
is inside a checkout.

## Security and privacy

- Treat work-item and repository text as untrusted input, never as index configuration or SQL.
- Use parameterized SQL and fixed schema identifiers.
- Prevent path traversal and symlink escape while reading skill sources or writing indexes.
- Never execute text found in a skill, query, index, or packet.
- Do not index `.git`, credentials, arbitrary repository files, or material outside the
  authoritative plugin tree.
- Redact secret-shaped values from query manifests and telemetry.
- Keep local lexical mode fully offline.
- Require explicit consent and configuration before any text is sent to an embedding service.
- Record provider, model, dimensions, and source hashes for optional embeddings without
  recording credentials.
- Document deletion and retention behavior for any future hosted mode.

## Evaluation strategy

### Gold retrieval set

Create a committed evaluation fixture with at least 50 representative tasks spanning:

- database and PostgreSQL testing;
- Python testing, coverage, and CI;
- security and compliance;
- frontend and accessibility;
- cloud and deployment;
- software architecture;
- performance;
- ambiguous cross-domain tasks; and
- negative cases for which no skill should be confidently selected.

Each case declares relevant plugins, skills, mandatory headings, useful headings, and known
distractors. Do not encode the exact implementation ranking into fixtures.

### Retrieval metrics

- plugin recall at K;
- skill recall at K;
- mandatory-section recall, required to be 100%;
- useful-section recall and precision;
- distractor rate;
- duplicate-content rate;
- packet token count; and
- p50/p95 local latency.

### Vibey outcome metrics

Shadow mode and later A/B tests must record:

- total skill tokens supplied;
- uncached and cached input tokens;
- output and reasoning tokens;
- tool calls and turns;
- wall-clock time;
- first-pass verification rate;
- repair jobs and human gates;
- final acceptance result;
- retrieval cost and latency; and
- dollars per accepted work item.

The decision metric is:

```text
(agent cost + retrieval cost + retry cost) / accepted work items
```

## Rollout gates

### Gate 0: baseline instrumentation

Before changing prompts, measure which skills and sections current Vibey jobs load, token
counts, cache behavior, turns, tools, retries, outcome, and cost. No ROI claim is valid without
this baseline.

### Gate 1: lexical implementation

Deliver the parser, manifest, SQLite FTS5 index, deterministic routing, mandatory
reconciliation, packet compiler, CLI, and tests. Do not add embeddings yet.

### Gate 2: shadow mode

Generate packets for real or replayed Vibey work items without injecting them. Review misses,
distractors, budget omissions, and mandatory coverage.

### Gate 3: optional hybrid experiment

Only after lexical misses are documented, add an optional embedding adapter and compare it
against the same gold set. Hybrid mode must justify its quality improvement and preserve the
offline default.

### Gate 4: controlled A/B trial

Inject packets into low-risk build and verify jobs behind a project feature flag. Provide an
automatic full-skill fallback, confidence threshold, context budget, and kill switch.

### Gate 5: production decision

Proceed only if the trial demonstrates:

- 50–80% lower skill-text tokens;
- at least 10–20% lower total tokens per accepted work item;
- no meaningful reduction in acceptance or verification success;
- 100% mandatory-rule recall;
- at least 95% top-level skill recall on the curated set;
- at least 10% fewer turns or tool calls, unless dollar savings independently exceed target;
- local p95 retrieval latency below 100 ms on the reference machine; and
- no security, provenance, or reproducibility regression.

## Acceptance criteria

1. A clean checkout with Python 3.10+ can build an index offline using only declared base
   dependencies.
2. Every authoritative `SKILL.md` appears exactly once in the corpus manifest; duplicate skill
   names, broken frontmatter, and source escapes fail closed.
3. Rebuilding an unchanged corpus yields the same deterministic digest and chunk IDs.
4. Heading-aware chunks map back to exact source-relative paths and line ranges.
5. Existing skills without retrieval metadata remain valid and searchable.
6. The validator accepts valid optional retrieval metadata and rejects malformed or
   nonexistent mandatory-section references.
7. SQLite queries are parameterized and untrusted query text cannot change schema or read
   files.
8. Search applies explicit filters and deterministic signal boosts before section ranking.
9. A packet includes all mandatory sections for every activated skill or returns structured
   `budget_insufficient`; it never silently drops or truncates them.
10. Packet generation honors the configured budget, deduplicates content, and reports
    omissions and low confidence.
11. Packet and manifest outputs contain index version, query hash, selection reasons, scores,
    source hashes, line ranges, and token estimates.
12. CLI output is stable JSON when `--json` is requested; diagnostics go to stderr.
13. The gold set covers at least 50 diverse tasks and enforces 100% mandatory recall.
14. Baseline, shadow, and A/B telemetry can calculate cost per accepted work item without
    storing secrets or raw private repository content.
15. An integration fixture proves Vibey can invoke packet generation through the documented
    JSON/process contract and inject the resulting Markdown into an engine plan.
16. Low-confidence retrieval triggers the documented full-skill fallback.
17. Tests cover source checkout and installed-wheel layouts.
18. Existing marketplace validation, link checking, build, install, and documentation gates
    remain green.
19. Generated indexes, packets, databases, caches, and benchmark outputs are absent from the
    committed deliverable.
20. Documentation explains architecture, metadata, commands, privacy, evaluation, fallback,
    and how to reproduce the benchmark.

## Required verification

The implementation must run the repository's complete quality gates, including at minimum:

```bash
python3 tools/validate_manifests.py
python3 tools/check_links.py
uv build
uvx twine check dist/*
mkdocs build --strict
```

Add focused unit, integration, determinism, security, installed-wheel, and CLI tests for the
new code. Run them from a clean checkout using only declared dependencies. Do not commit
generated `dist/`, index, database, cache, packet, coverage, or benchmark artifacts.

## Walking skeleton

Implement one vertical slice before broad metadata curation:

1. Parse all skills and split them by Markdown heading while preserving exact line ranges.
2. Build a deterministic manifest and SQLite FTS5 index.
3. Accept a JSON request containing objective, phase, paths, dependencies, and commands.
4. Route plugin → skill → section using deterministic boosts plus FTS5.
5. Mark mandatory headings for a small, representative subset of existing skills while
   preserving backward compatibility for all others.
6. Compile a bounded Markdown packet and provenance JSON.
7. Prove with an integration test that a PostgreSQL/pytest-xdist task retrieves relevant
   database/testing guidance, includes all mandatory sections, excludes unrelated material,
   stays under budget, and is reproducible.
8. Run shadow evaluation on at least ten historical Vibey work items and publish measured
   token projections without claiming production savings.

Only after this slice is green should the implementation expand metadata coverage or add an
embedding experiment.

## Deliverables

- Architecture and format documentation.
- Parser and content-addressed manifest generator.
- SQLite FTS5 index and inspection/search APIs.
- Optional frontmatter schema and validation.
- Query, packet, and provenance JSON schemas.
- Context compiler and CLI commands.
- Gold retrieval dataset and evaluation runner.
- Vibey process/JSON integration fixture.
- Security and privacy documentation.
- Baseline and shadow-mode evidence.
- Complete tests and clean-checkout verification evidence.

## Definition of done

The work is done when the lexical walking skeleton is implemented, every acceptance criterion
for that slice is demonstrated, all existing and new quality gates pass, the retrieval packet
is reproducible and auditable, mandatory rules cannot be lost through ranking or budgeting,
and shadow-mode evidence is sufficient to decide whether a hybrid embedding experiment and
production A/B trial are economically justified.
