# Runbook: JIRA integration

## Goal

A user can drive vibey entirely from Jira, and vibey can drive Jira back.
Both directions, fully comprehensive:

- **Inbound (Jira → vibey):** a new ticket in a watched project becomes a
  vibey project (INTAKE); a comment on a linked ticket answers a parked
  human gate; a status transition (e.g. "Approved") accepts a design or
  opts into deployment; an attachment becomes DESIGN input.
- **Outbound (vibey → Jira):** vibey creates the ticket hierarchy (epic per
  project, story per work item), comments progress (phase transitions,
  verify results, spend), transitions statuses as phases advance, posts
  park prompts as comments with the exact `vibey answer` contract, attaches
  artifacts (specs, demo output), and closes tickets on DONE.

## Current state (verified)

- No Jira code exists anywhere in the repo.
- Human gates already un-park via `gates.answer` +
  `NOTIFY vibey_job_ready` (`infrastructure/db/human_gate_repository.py`)
  — a Jira comment handler only has to call the same application service
  the CLI `vibey answer` uses. No queue changes needed.
- `infrastructure/notify/publishers.py` already fans events out to
  pluggable publishers — the outbound half slots in as one more publisher.

## Design

- `application/interfaces/tracker.py`: `IssueTrackerPort` Protocol —
  vendor-neutral (`create_issue`, `comment`, `transition`, `attach`,
  `watch_events`), so Linear/GitHub Issues can implement it later.
- `infrastructure/jira/client.py`: Jira Cloud REST v3 over httpx; auth via
  API token (email+token basic) first, OAuth 2.0 (3LO) as a follow-up.
- `infrastructure/jira/inbound.py`: two modes, both feeding the same
  translator —
  - **Webhook mode** (server deployments): FastAPI route registered with
    Jira webhooks (`jira:issue_created`, `comment_created`,
    `jira:issue_updated`).
  - **Poll mode** (MacBook, no public ingress): JQL poll
    `updated >= -2m ORDER BY updated` on a worker heartbeat.
- Translator maps Jira events → existing application calls:
  issue_created → `vibey new` equivalent; comment matching an open gate id
  → `gates.answer` (comment body supports the `--defaults` and `--raw`
  grammars verbatim); transition names mapped per-project in config.
- `infrastructure/jira/outbound.py`: a ledger-event publisher that mirrors
  PhaseTransitioned / FindingRaised / park events into comments and
  transitions. Idempotent: every mirrored event carries the ledger event
  id in a hidden Jira entity property, so replays never double-comment.
- State mapping stored in `project.config` (`jira_site`, `jira_project`,
  `jira_epic_id`, transition map).

## Work items (vibey decomposition seed)

1. `IssueTrackerPort` Protocol + in-memory fake + port-parity tests.
2. Jira REST client (fixture-tested at the HTTP boundary, respx).
3. Outbound publisher: epic/story creation + progress comments +
   transitions + attachments, idempotent via entity properties.
4. Inbound poll mode: JQL watcher job (`tracker.poll` job kind, serial).
5. Inbound comment → gate answer (full `--defaults`/`--raw` grammar).
6. Webhook mode: FastAPI ingress (server mode only) + HMAC verification.
7. CLI: `vibey jira link <project> --site --jira-project`, `vibey jira
   status`.
8. `tests/live/test_jira_live.py`: against a free Jira Cloud site, gated
   on `VIBEY_JIRA_LIVE=1` + credentials.

## Verification

- Fixture suites green across all layers (100% branch).
- Live: create ticket on the free site → vibey project appears → park a
  gate → answer it from a Jira comment → phase transition mirrored back
  to the ticket, all with zero CLI interaction.

## Needs from operator

Jira Cloud free site, an API token, and one watched project key.

## Risks

- Jira rate limits (poll mode: back off on 429, jitter).
- Comment-grammar injection: answers only accepted from configured
  accounts; everything else is recorded but ignored.
- Transition maps differ per Jira workflow — config, never hardcoded.
