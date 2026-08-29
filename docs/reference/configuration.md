# Configuration reference: `vibey.toml`

**Not yet an active runtime input.** The schema below is fully implemented
and unit-tested in
[`src/vibey/domain/config.py`](../../src/vibey/domain/config.py)
(`VibeyConfig`, `parse_config`, `parse_toml_string`) and
[`src/vibey/infrastructure/config_loader.py`](../../src/vibey/infrastructure/config_loader.py)
(`load_config_from_path`), but **no command actually reads a `vibey.toml`
file from disk today** — `load_config_from_path` has no caller anywhere in
`cli/`, `bootstrap.py`, the worker, or the Kubernetes operator, only its own
unit test. Writing a `vibey.toml` into your repo currently has *no effect*
on a running project. Treat this page as a designed-and-tested schema, the
same "implemented and tested, not yet an active runtime path" status the
README gives `infrastructure/notify/` and `infrastructure/otel.py`.

What actually configures a project today is a small, separate set of CLI
flags on `vibey new` — `--max-cycles`, `--max-cycle-dollars`,
`--max-cycle-turns`, `--skills-context-mode`, `--skills-context-budget` (see
the [CLI reference](cli.md)) — which are recorded directly into that
project's own stored config record at creation time. They never pass
through `parse_config`, and no `vibey.toml` file is written or read to
produce them. `VIBEY_`-prefixed environment variables are read only inside
`load_config_from_path` itself (e.g. `VIBEY_FEATURE_QWENLOOP`), so they too
have no effect until that function is wired into a live command.

`domain/config.py` is a pure, stdlib-only module with no filesystem access
of its own (reading the file is an infrastructure concern). Every table
below is optional; omit any of them and the listed defaults apply, as
validated by `parse_config`. An unknown engine name anywhere, or `qwenloop`
referenced before `features.qwenloop = true`, fails validation with a
`ConfigError` naming the offending path — again, only when something calls
`load_config_from_path`/`parse_config`, which nothing in this codebase does
yet outside tests.

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

`worktree` isolation is the one active runtime behavior today: every job
and phase runs in an isolated ephemeral git worktree. `container` and `vm`
are schema-valid values, and the container hardening path
(`infrastructure/container/config.py`'s `ContainerConfig`,
`infrastructure/container/runtime.py`'s `OciContainerExecutor`) is
implemented and unit-tested, but — like the rest of this page — it is never
constructed by `bootstrap.py` or anything else outside its own test file,
and (per the note above) `[isolation]` itself is never read from a real
`vibey.toml`. Setting `level = "container"` has no effect today; see
[SECURITY.md](../../SECURITY.md#1-worktree--container-isolation-runtime-adr-0008-task-91)
for the same disclosure.

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

This file illustrates the full schema that `parse_config` validates today —
not a file any command currently reads from disk (see the disclosure at the
top of this page).

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
