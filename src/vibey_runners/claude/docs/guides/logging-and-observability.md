# Logging and observability

`claudeloop` uses **multiple independent transports**. They are not alternatives
to each other — a normal `run` / `resume` emits several of them at once.

## Transport matrix

| Transport | Where | Format | When |
|---|---|---|---|
| **Human console** | stderr | Colored / key=value (structlog `ConsoleRenderer`) | After logging is configured (off when `--stream-ui` owns the TTY) |
| **JSON console** | stderr | One JSON object per line (`"transport": "console_json"`) | Always (same events as human) |
| **Structlog file** | `--log-file` / `CLAUDELOOP_LOG_FILE` | JSON lines (`"transport": "file"`) | Optional |
| **Events** | `.claudeloop/runs/<run_id>/events.jsonl` | Redacted JSONL (SDK + control + chatter) | Every run; includes `trace_id` / `turn_id` |
| **Audit** | `.claudeloop/runs/<run_id>/audit.jsonl` | Redacted JSONL (phase trail) | Every run |
| **Progress banners** | stdout-style prints via `ConsoleProgressReporter` | Short `=== attempt N ===` / Done/Failed | Every run |
| **Status / bus** | `status.json`, `bus.jsonl` | Snapshots for poll/subscribe | Every run |
| **Handoff snapshots** | `snapshots/latest.json`, `snapshots/<ts>-<reason>.json` | Control-plane handoff (+ optional bundles / Claude transcript) | Start / wait / stop / finish / persist / `claudeloop snapshot` |
| **Stream UI** | full-screen Textual | Live / follow / replay panes | `--stream-ui` or `watch --stream` / `--replay` |

Level for the structlog console (+ optional file) transports is controlled by
`--log-level` / `CLAUDELOOP_LOG_LEVEL` (default `INFO`). Use `DEBUG` for
per-SDK-message and decision-detail noise.

## What gets logged (structured)

Among others:

- `run.started` / `run.finished` / `run.stopped` / `run.exception`
- `preflight.completed`, `turn.starting`, `turn.completed`
- `waiting.scheduled`, `probe.completed`, `capacity.restored`
- `control.stop`, `control.prompt_now`, deferred prompt queue/apply
- `savepoint.created`, `session.lock_acquired` / `session.lock_released`
- `gateway.connect`, `gateway.send_turn.*`, `probe.*`
- `ops.stop_enqueued`, `ops.prompt_enqueued`, `ops.unwind`
- `runner.config` (non-secret fields only)
- `test_agent.active` / `test_agent.loading` (test-only gate)
- `chatter.prompt` / `chatter.assistant` / `chatter.tool` / `chatter.delta` / `chatter.thinking`
- `model.profile_queued` / `model.profile_changed` / `model.auto_policy` / `model.auto_downgrade_budget`

## Trace and turn ids

Every run gets a `trace_id` (UUID) bound into structlog context and every
`events.jsonl` row. Each turn gets a `turn_id`. Use these to correlate console
JSON lines with the per-run event log.

## Chatter verbosity

`--log-chatter` / `CLAUDELOOP_LOG_CHATTER`:

| Mode | Behavior |
|---|---|
| `summary` (default at INFO) | Console shows short previews; `events.jsonl` still stores full `text` (256 KiB safety cap) so `--stream-ui` never crops prompts |
| `full` (default when `--log-level DEBUG`, unless chatter is `off`) | Full bodies everywhere (256 KiB cap per field) |
| `off` | No `chatter.*` events |

`claudeloop logs --chatter` filters the event stream to `chatter.*` only.

## Token stream UI

- `claudeloop run|resume --stream-ui` — full-screen Textual panes (header /
  continuous AI chat log on the left / tools on the right / footer). The left
  pane appends prompts and streamed tokens in realtime and does not wipe or
  crop prompts between turns. Requires a TTY; human console renderer is
  disabled; JSON console stays on stderr.
- `claudeloop watch --stream [--run-id]` — follow live `events.jsonl` deltas.
- `claudeloop watch --stream --replay [--speed N]` — replay historical
  `chatter.delta` / turn chatter from disk (`--speed 0` = as fast as possible).
  Non-TTY replay dumps a plain transcript.

## Redaction

All structlog transports and the per-run events/audit sinks run payloads
through recursive redaction (`infrastructure/redact.py`) — secret-shaped keys
and credential-looking substrings become `***REDACTED***`. See `SECURITY.md` at the repository root.

## Separating streams

Human and JSON console lines both go to **stderr**. Machine consumers should
parse only lines that start with `{` and check `"transport": "console_json"`.
Progress banners and Typer user messages may still appear on stdout.

`--log-file` never shares a path with `audit.jsonl` / `events.jsonl`.

## Related

- CLI flags: [`../reference/cli.md`](../reference/cli.md)
- Config / env: [`../getting-started/configuration.md`](../getting-started/configuration.md)
- Mid-run ops + run dir layout: [`autonomous-runs.md`](autonomous-runs.md)
- System harness (scripted agent): [`live-testing.md`](live-testing.md)
