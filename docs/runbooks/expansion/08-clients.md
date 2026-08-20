# Runbook: clients — mobile, web, desktop, and a finished TUI

## Goal

Four first-class operator surfaces over one API: a React Native mobile
app, a Next.js web app, a desktop app (macOS, and Linux across
Ubuntu/Fedora/Arch and friends), and the existing Textual TUI completed —
with **every surface able to drill into ALL log levels, down to the
deepest layer** (ledger events, engine events.jsonl lines, raw subprocess
stderr).

## Current state (verified)

- TUI exists as a single dashboard (`src/vibey/tui/dashboard.py`, 5 tests)
  — a skeleton, not the finished product.
- No HTTP API exists; every surface today is the CLI talking straight to
  Postgres. Workstream 12's API server is therefore a hard dependency:
  clients speak to `vibey-server`, never to the DB.

## Design

- **Log depth contract (the load-bearing requirement):** one
  `GET /projects/{id}/logs` stream (SSE/WebSocket) with a `depth`
  parameter — `phase` (transitions/parks) → `job` (queue lifecycle) →
  `ledger` (all 19 event kinds) → `engine` (translated engine events) →
  `raw` (verbatim events.jsonl lines + captured stderr, straight from the
  run dirs / attachment store). Server-side filtering by level, kind,
  engine, work item; cursor-based backfill from the ledger so every
  surface can replay history, not just tail. The TUI proves the contract
  first; the other clients reuse it.
- **TUI completion**: screens for projects list, phase pipeline, queue
  (with lease ages), gates (answer inline, including `--raw` grammar),
  engines/health/rotation, budget, and the log drill-down view
  (depth selector + follow mode). Textual is already a dependency.
- **Next.js web app** (`clients/web/`): same screens, App Router + SSE;
  typed client generated from the OpenAPI schema (12); auth = the API
  token scheme from 12.
- **React Native app** (`clients/mobile/`, Expo): the on-call surface —
  push notification on parks (server publishes via the existing
  notify/publishers fan-out → APNs/FCM), answer gates from the phone,
  budget approvals, log viewer with depth control.
- **Desktop** (`clients/desktop/`): Tauri wrapping the web UI (one Rust
  shell, small binaries, native menus/tray). Targets: macOS dmg,
  Linux AppImage + deb + rpm (covers Ubuntu/Fedora/Arch derivatives;
  AUR package in workstream 09). Tray shows live phase; the keep-awake
  contract (10) integrates here for local-worker mode.
- Monorepo layout: `clients/` in the vibey repo with its own CI lane —
  the Python coverage gates do not apply to TS; clients get their own
  (vitest + playwright, RN testing library, cargo test).

## Work items

1. Log-depth endpoint + backfill cursors on the 12 API (server side).
2. TUI: the seven screens + log drill-down; keep 100% cli/tui-layer
   Python coverage.
3. OpenAPI → generated TS client package (`@vibey/sdk`, also feeds 12).
4. Next.js app: screens + SSE + auth + e2e (playwright vs a scripted-
   engine fixture server).
5. RN app: gates + notifications + logs; Expo EAS build profiles.
6. Tauri desktop: shell, tray, updater, dmg/AppImage/deb/rpm bundling.
7. Push relay publisher (APNs/FCM) behind the existing publisher seam.
8. Live: one full greeter conducted **entirely from each surface** —
   including answering a park and reading raw engine stderr from the UI.

## Verification

The four live conductions above, plus: a log-parity test asserting the
same run shows identical event counts at `raw` depth across CLI, TUI,
web, and mobile (no surface silently truncates).

## Needs from operator

Apple/Google dev accounts only when 07 submits the RN app; Expo account;
nothing else beyond Node + Rust toolchains.

## Risks

- Feature drift across four UIs — the generated SDK + one shared screen
  spec doc is the guard; surfaces render the same resource model.
- Raw-depth logs can leak secrets → the existing redaction pass
  (`infrastructure/ledger/redact.py`) runs server-side on the raw stream
  too, before transport.
