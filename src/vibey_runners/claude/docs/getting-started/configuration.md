# Configuration reference

Configuration precedence, highest wins: **CLI flags > environment variables
> config file > built-in defaults** — see `infrastructure/config.py`'s
`load_config()`. Every field lives on `RunnerConfig`; not every field has a
CLI flag yet (noted below).

| Setting | CLI flag | Env var | Default | Backed by |
|---|---|---|---|---|
| Max turns per run | `--max-turns` (`run`, `resume`) | `CLAUDELOOP_MAX_TURNS` | unset (unbounded) | `domain.budget.Budget.max_turns` |
| Max dollars per run | `--max-dollars` (`run`, `resume`) | `CLAUDELOOP_MAX_DOLLARS` | unset (unbounded) | `domain.budget.Budget.max_dollars` |
| Max attempts per run | config file/env only | `CLAUDELOOP_MAX_ATTEMPTS` | unset (unbounded) | `domain.budget.Budget.max_attempts` |
| Max total wait time | `--max-wait` (`run`, `resume`) | `CLAUDELOOP_MAX_WAIT_SECONDS` | unset (unbounded) | `domain.waiting.WaitPolicyConfig.max_wait` |
| Model id / alias | `--model` (`run`, `resume`) | `CLAUDELOOP_MODEL` | alias `low` → `claude-sonnet-4-5` | `ClaudeAgentOptions.model` via profile resolve |
| Effort | `--effort` (`run`, `resume`) | `CLAUDELOOP_EFFORT` | `medium` | `ClaudeAgentOptions.effort` |
| Preset | `--preset` (`run`, `resume`) | `CLAUDELOOP_PRESET` | unset | sets model+effort (`low`/`medium`/`high`); flags override |
| Model alias `low` | config/env | `CLAUDELOOP_MODEL_LOW` | `claude-sonnet-4-5` | preset/alias table |
| Model alias `medium` | config/env | `CLAUDELOOP_MODEL_MEDIUM` | `claude-opus-4-6` | preset/alias table |
| Model alias `high` | config/env | `CLAUDELOOP_MODEL_HIGH` | `claude-fable-5` | preset/alias table |
| Auto model policy | `--auto-model/--no-auto-model` | `CLAUDELOOP_AUTO_MODEL` | on | escalate stuck / downgrade on progress+budget |
| Log chatter | `--log-chatter` | `CLAUDELOOP_LOG_CHATTER` | `summary` (or `full` at DEBUG) | `chatter.*` events |
| Stream UI | `--stream-ui` | `CLAUDELOOP_STREAM_UI` | off | Textual multi-pane; disables human console |
| Continue prompt | `--continue-prompt` (`run`, `resume`) | `CLAUDELOOP_CONTINUE_PROMPT` | short continue text | runner continue prompt |
| Credits probe interval | config file/env only | `CLAUDELOOP_CREDITS_PROBE_INTERVAL_SECONDS` | 120s | `WaitPolicyConfig.credits_probe_interval` |
| Credits probe ceiling | config file/env only | `CLAUDELOOP_CREDITS_PROBE_CEILING_SECONDS` | 600s | `WaitPolicyConfig.credits_probe_ceiling` |
| Window probe interval | config file/env only | `CLAUDELOOP_WINDOW_PROBE_INTERVAL_SECONDS` | 600s | `WaitPolicyConfig.window_probe_interval` |
| Reset-time grace period | config file/env only | `CLAUDELOOP_RESET_GRACE_SECONDS` | 60s | `WaitPolicyConfig.reset_grace` |
| Done-marker fallback string | `--done-marker` (`run`, `resume`) | `CLAUDELOOP_DONE_MARKER` | `CLAUDELOOP_TASK_FULLY_COMPLETE` | `domain.completion.DEFAULT_DONE_MARKER` |
| Agent SDK JSON buffer | `--max-buffer-size` (`run`) | `CLAUDELOOP_MAX_BUFFER_SIZE` | `52428800` (50 MiB) | `ClaudeAgentOptions.max_buffer_size` |
| Permission mode | `--permission-mode` (`run`) | `CLAUDELOOP_PERMISSION_MODE` | `bypass` | `ClaudeAgentOptions.permission_mode` (always start bypass-capable) |
| Tool approval timeout | config/env | `CLAUDELOOP_TOOL_APPROVAL_TIMEOUT_SECONDS` | 30s | Manual mode auto-deny |
| Web search | `--web-search` (`run`) | `CLAUDELOOP_WEB_SEARCH` | off | allowed tools / resource flag |
| Deep research | `--deep-research` (`run`) | `CLAUDELOOP_DEEP_RESEARCH` | off | Local research job under `resources/research/` (not a fake Anthropic deep-research product API) |
| Log level | `--log-level` (`run`, `resume`) | `CLAUDELOOP_LOG_LEVEL` | `INFO` | dual console + optional file (see [logging guide](../guides/logging-and-observability.md)) |
| Structlog file | `--log-file` (`run`, `resume`) | `CLAUDELOOP_LOG_FILE` | unset | optional JSON file transport — never the audit JSONL path |
| Use Claude Code's built-in retry watchdog instead of probing | config file/env only | `CLAUDELOOP_RETRY_WATCHDOG` | off | see [ADR 0005](../architecture/decisions/0005-retry-watchdog-off-by-default.md) |

Per-run **audit** and **events** always live under
`.claudeloop/runs/<run_id>/` (`audit.jsonl`, `events.jsonl`, `snapshots/`) and
are separate from `--log-file` / structlog. Console logging always emits
**both** a human stderr stream and a JSON stderr stream (`transport=console_json`).

Every numeric setting above corresponds directly to a field on
`WaitPolicyConfig` or `Budget` in `src/claudeloop/domain/`, both of which
validate their own values in `__post_init__` (e.g. a negative or zero
interval raises `ValueError` immediately, rather than producing a wait
policy that silently never probes). See `tests/domain/test_waiting.py` and
`tests/domain/test_budget.py` for the exact validated boundaries, and
`tests/infrastructure/test_config.py` for the precedence order itself.

## Config file

`claudeloop.toml` in the working directory, or
`~/.config/claudeloop/config.toml` (the former overrides the latter). Plain
TOML, keys match the "Backed by" field names in snake_case:

```toml
max_turns = 50
log_level = "DEBUG"
credits_probe_interval_seconds = 60
```

## Adding a CLI flag for the config-file/env-only settings

`run`/`resume` currently expose only the highest-traffic flags. Any
`RunnerConfig` field can be exposed as a flag by adding a `typer.Option(...)`
parameter to the relevant command in `src/claudeloop/cli/commands/` and
threading it into that command's `cli_overrides` dict passed to
`load_config()` — see `cli/commands/run.py` for the existing pattern.
