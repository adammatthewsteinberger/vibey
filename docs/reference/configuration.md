# Configuration reference: `vibey.toml`

`vibey.toml` is validated by
[`src/vibey/domain/config.py`](../../src/vibey/domain/config.py) — a pure,
stdlib-only module with no filesystem access of its own (reading the file
is an infrastructure concern). Every table below is optional; omit any of
them and the listed defaults apply. An unknown engine name anywhere, or
`qwenloop` referenced before `features.qwenloop = true`, fails validation
with a `ConfigError` naming the offending path.

Every project also accepts overrides via CLI flags (`vibey new --max-cycle-dollars`,
etc. — see the [CLI reference](cli.md)) and via `VIBEY_`-prefixed environment
variables. CLI flags and environment variables win over `vibey.toml`.

## `[project]`

| Field | Type | Default | Notes |
|---|---|---|---|
| `name` | string | *required* | Project name. |
| `repo` | string | `"."` | Path to the repository this project builds against. |
| `max_cycles` | integer | `10` | Cap on delivery cycles. |
| `strict_loopback` | boolean | `false` | When true, tightens review-loopback routing (ADR-0010). |

## `[isolation]`

| Field | Type | Default | Notes |
|---|---|---|---|
| `level` | string | `"worktree"` | One of `worktree`, `container`, `vm`. |
| `allow_push` | boolean | `false` | Whether a worktree may push to a remote. |
| `egress` | array of strings | `[]` | Allowed egress destinations when network isolation is otherwise closed. |

See [ADR-0008](../architecture/decisions/0008-worktree-isolation.md) and
[SECURITY.md](../../SECURITY.md) for what each isolation level enforces at
runtime (container hardening flags, network defaults, etc.).

## `[budget]`

| Field | Type | Default | Notes |
|---|---|---|---|
| `max_dollars_per_cycle` | float or unset | unset (no cap) | Tripping it parks a `budget_exhausted` gate. |
| `max_dollars_total` | float or unset | unset (no cap) | Total spend cap across the project's lifetime. |
| `max_turns_per_item` | integer or unset | unset (no cap) | Per-work-item engine-turn cap. |

Every cap is summed live from the ledger's own `TurnCompleted` and
`BudgetSpent` events — never estimated ahead of time. `vibey cost` shows
current spend against these caps.

## `[engines]`

| Field | Type | Default | Notes |
|---|---|---|---|
| `enabled` | array of strings | `["claudeloop", "codexloop", "cursorloop", "agyloop"]` | Must be a subset of the known engines below. |
| `weights` | table of string→int | `{}` | Per-engine weight for smooth weighted round robin ([ADR-0005](../architecture/decisions/0005-smooth-weighted-round-robin.md)). |

Known engine ids: `claudeloop`, `codexloop`, `cursorloop`, `agyloop`, and
`qwenloop` (only valid once `features.qwenloop = true`).

## `[phases.design]`, `[phases.build]`, `[phases.review]`

Each phase table accepts the same three fields:

| Field | Type | Default (per phase) | Notes |
|---|---|---|---|
| `effort` | string | `design` = `high`, `build` = `low`, `review` = `high` | One of `trivial`, `low`, `standard`, `high`, `max`. |
| `engines` | array of strings or unset | unset (falls back to `[engines].enabled`) | Restrict this phase to a subset of engines. |
| `parallelism` | integer or unset | unset | Per-phase worker concurrency override. |

```toml
[phases.build]
effort = "standard"
engines = ["claudeloop", "agyloop"]
parallelism = 4
```

## `[provision]`

| Field | Type | Default | Notes |
|---|---|---|---|
| `plugins` | array of strings | `[]` | Agent-surface provisioning plugins applied by `infrastructure/provision/agent_surface.py` ([ADR-0011](../architecture/decisions/0011-agent-surface-provisioning.md)). |

## `[deploy]`

| Field | Type | Default | Notes |
|---|---|---|---|
| `enabled` | boolean | `false` | Opts the project into the DEPLOY_DESIGN / DEPLOY_EXECUTE / DEPLOY_REVIEW stage set. |
| `target` | string | `"azure"` | Deployment target. Azure is the only implemented target today. |
| `iac` | string | `"bicep"` | Infrastructure-as-code format used by the deploy adapters. |

## `[features]`

| Field | Type | Default | Notes |
|---|---|---|---|
| `qwenloop` | boolean | `false` | Must be `true` before `qwenloop` can appear in `[engines].enabled` or any `[phases.*].engines` list. |

## `[qwenloop]`

Only meaningful when `features.qwenloop = true`. `qwenloop` is a local,
default-off standby engine considered only when enabled and no eligible
paid engine has capacity ([ADR-0015](../architecture/decisions/0015-qwenloop-standby.md)).

| Field | Type | Default | Notes |
|---|---|---|---|
| `backend` | string | `"auto"` | One of `auto`, `llama.cpp`, `vllm`. |
| `portable_profile` | string | `"qwen2.5-coder-14b-q5-k-m"` | Model profile used on the portable (CPU/quantized) backend path. |
| `nvidia_profile` | string | `"qwen2.5-coder-14b-bf16"` | Model profile used when an NVIDIA GPU backend is selected. |
| `idle_timeout_seconds` | integer | `900` | Must be non-negative; how long an idle local model stays warm. |
| `startup_timeout_seconds` | integer | `180` | Must be positive. |
| `context_window` | integer | `32768` | Must be positive. |

## `[skills_context]`

Set via `vibey new --skills-context-mode` / `--skills-context-budget`
rather than as a static `vibey.toml` table (see the
[CLI reference](cli.md#vibey-new-name)); the values are recorded into the
project's own config at creation time.

| Field | Type | Default | Notes |
|---|---|---|---|
| `mode` | string | `"off"` | `off`, `shadow` (measure only, never changes prompts), or `inject` (append successful packets to BUILD prompts). |
| `budget` | integer | `6000` | Token budget for retrieval (1,000–32,000). |

## Full example

```toml
[project]
name = "my-app"
repo = "."
max_cycles = 15

[isolation]
level = "container"
allow_push = false

[budget]
max_dollars_per_cycle = 15.0
max_dollars_total = 250.0

[engines]
enabled = ["claudeloop", "agyloop"]
weights = { claudeloop = 3, agyloop = 1 }

[phases.design]
effort = "high"

[phases.build]
effort = "low"
parallelism = 2

[phases.review]
effort = "high"

[deploy]
enabled = true
target = "azure"
iac = "bicep"

[features]
qwenloop = true

[qwenloop]
backend = "auto"
idle_timeout_seconds = 600
```
