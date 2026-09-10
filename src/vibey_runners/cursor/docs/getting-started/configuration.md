# Configuration

Every knob has a flag, an environment variable, and a config-file key — and they
resolve in that order (CLI over `CURSORLOOP_*` env over file over defaults), so a
one-off flag never has to fight your shell profile. `cursorloop config`-style
inspection lives in `cursorloop doctor`, which reports every setting it observed
and where it came from.

## Environment variables

| Variable | Type | Maps to | What it bounds |
|---|---|---|---|
| `CURSOR_API_KEY` | string | `api_key` | Cursor API authentication (the only non-`CURSORLOOP_*` variable read). |
| `CURSORLOOP_MAX_WAIT` | seconds (float) | `max_wait_seconds` | Longest single wait on a rate-limit window before the run gives up waiting. |
| `CURSORLOOP_MAX_TURNS` | int | `max_turns` | Hard cap on agent turns for the run. |
| `CURSORLOOP_MAX_DOLLARS` | float | `max_dollars` | Budget ledger cap; the run stops before exceeding it. |
| `CURSORLOOP_TURN_TIMEOUT` | seconds (float) | `turn_timeout_seconds` | Watchdog for one turn; a hung turn is failed, not waited on. |
| `CURSORLOOP_STALL_TIMEOUT` | seconds (float) | `stall_timeout_seconds` | How long output may stay silent before the run is declared stalled. |
| `CURSORLOOP_LOG_LEVEL` | string | `log_level` | Log verbosity (`INFO` default). |
| `CURSORLOOP_LOG_FILE` | path | `log_file` | Optional log destination beside the JSONL audit trail. |
| `CURSORLOOP_MODEL` | string | `model` | Model override for the session. |
| `CURSORLOOP_BILLING_LEXICON` | comma list | `billing_terms` | Phrases classified as billing/credit exhaustion (not waitable). |
| `CURSORLOOP_RATE_LIMIT_LEXICON` | comma list | `rate_limit_terms` | Phrases classified as rate-limit windows (waitable with a bounded probe). |
| `CURSORLOOP_MANAGED_HOOKS` | bool-ish (`0/false/no/off` disable) | `managed_hooks` | Whether cursorloop installs its non-blocking hook preamble. |

## Flags

`cursorloop run` accepts the same knobs per-invocation: `--max-turns`,
`--max-dollars`, `--max-wait`, `--turn-timeout`, `--stall-timeout`, `--model`,
`--log-level`, and `--managed-hooks/--no-managed-hooks`. A flag always wins over
the environment.

## Worked example

```bash
export CURSOR_API_KEY=sk-...
export CURSORLOOP_MAX_DOLLARS=5
cursorloop run --plan plan.md --max-turns 40 --turn-timeout 300
```

The run stops at whichever bound arrives first: the plan completing, 40 turns,
$5, or a 300-second hung turn.
