# Runbook: integration surfaces — MCP, API, webhooks, skills, SDKs (all repos)

## Goal

Every repo in the family — vibey and each loop runner — exposes the full
modern integration stack: an MCP server, a public HTTP API, webhooks in
and out, packaged skills/plugins for the major agent products, and typed
SDKs. One coherent surface, generated from one schema, never five
hand-drifted ones.

## Design

### The API is the root artifact (`vibey-server`)

- FastAPI app in `infrastructure/api/` (new `vibey server` CLI entry;
  the same app the k8s chart (05) deploys and the clients (08) consume).
- Resources mirror the application layer 1:1: projects, jobs, gates
  (answer endpoint = the same service `vibey answer` calls — single choke
  point), ledger (cursor-paginated), engines/health, handoffs, budget,
  and the depth-parameterized log stream (08's contract).
- AuthN: bearer tokens (hashed at rest) with scopes (`read`, `answer`,
  `conduct`, `admin`); localhost-no-auth dev mode.
- OpenAPI schema is CI-checked: schema drift without a version bump fails
  the build. **Everything else below is generated or derived from it.**

### MCP servers

- `vibey-mcp`: stdio + streamable-HTTP MCP server exposing tools that
  wrap the API — `vibey_new_project`, `vibey_status`, `vibey_answer_gate`,
  `vibey_logs`, `vibey_engines`, `vibey_budget` — plus resources for specs
  and park prompts. Tool inputs/outputs derive from the OpenAPI
  components; a parity test asserts every MCP tool maps to a documented
  API operation.
- Each loop runner gets a thin `<runner>-mcp` (run, status, tail,
  wind-down, doctor) built from a shared template package so five servers
  stay one implementation effort.

### Webhooks

- **Outbound**: a `webhook` notify-publisher (same seam as Jira/Moltbook):
  operator registers URLs + event filters; deliveries are HMAC-SHA256
  signed (`X-Vibey-Signature`), retried with backoff, dead-lettered into
  the ledger after N failures. Park events, phase transitions, DONE, and
  budget trips are the marquee payloads.
- **Inbound**: `/webhooks/{source}` routes with per-source verification —
  the generic entry point 01 (Jira), GitHub (PR events → review phase
  input), and future sources plug into.

### Skills/plugins

- Claude Code skill, Cursor rules, Codex/Antigravity trees already exist
  in-repo for *developing* vibey; this workstream adds **operator-facing**
  skills for *using* vibey (conduct/answer/monitor) across: Claude Code
  plugin (marketplace layout), OpenClaw AgentSkill (11), and a ChatGPT/
  Gemini-compatible action manifest derived from the OpenAPI schema.

### SDKs

- `@vibey/sdk` (TypeScript, generated + hand-polished wrapper) — feeds
  08's clients and npm (09).
- `vibey-sdk` (Python, typed httpx client generated from the schema) —
  for scripting conductors (the scratchpad drivers this validation used
  become 5-line SDK scripts).
- Runner repos: each publishes a small typed client for its local state
  dir + control plane (read runs, tail events, wind-down).

## Work items

1. FastAPI server + auth + the resource routes + OpenAPI freeze test.
2. Log-depth stream endpoint (SSE) + redaction.
3. Outbound webhook publisher + signing + retries + dead-letter.
4. Inbound webhook router + per-source verification.
5. vibey-mcp (stdio + HTTP) + parity tests + `vibey mcp serve`.
6. Runner MCP template + five instantiations.
7. TS + Python SDK generation in the release pipeline (09 publishes).
8. Operator skills: Claude Code plugin + action manifests.
9. Live: Claude Code conducts a full scripted greeter **through
   vibey-mcp only**; a webhook consumer receives signed park + DONE
   events; both SDKs drive a project end-to-end in their test suites.

## Verification

The three live proofs in item 9, plus CI: OpenAPI freeze, MCP↔API parity,
SDK round-trip tests, webhook signature verification vectors.

## Needs from operator

Nothing new (accounts from 09 cover publishing).

## Risks

- Five surfaces drifting — the OpenAPI-as-root rule and parity tests are
  the whole defense; hand-written surface code is a review flag.
- The API is a second write path to the queue — every mutating route
  must call the same application services the CLI does (enforced by a
  convention test, like `application/interfaces` has today).
- Webhook receivers are untrusted input: verification before parsing,
  prompt-shield on any content that reaches an engine prompt.
