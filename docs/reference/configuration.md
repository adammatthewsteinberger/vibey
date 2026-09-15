# Configuration reference: `vibey.toml`

**Mostly not an active runtime input.** The schema below is fully implemented
and unit-tested in
[`src/vibey/domain/config.py`](https://github.com/the-vibey-project/vibey/blob/main/src/vibey/domain/config.py)
(`VibeyConfig`, `parse_config`, `parse_toml_string`) and
[`src/vibey/infrastructure/config_loader.py`](https://github.com/the-vibey-project/vibey/blob/main/src/vibey/infrastructure/config_loader.py)
(`load_config_from_path`), but `load_config_from_path` has no caller outside
its own unit test, so the full schema is never loaded at runtime — not by
`cli/`, `bootstrap.py`, the worker, or the Kubernetes operator. Treat this page
as a designed-and-tested schema, the same "implemented and tested, not yet an
active runtime path" status the README gives `infrastructure/notify/` and
`infrastructure/otel.py`.

## What is read at runtime today

| Input | Read by | What it controls |
|---|---|---|
| `./vibey.toml`, key `[features].qwenloop` only | `vibey doctor` (`cli/main.py` `_qwenloop_feature_enabled`) | Whether `qwenloop` is added to the health sweep. The file is read from the current directory with `parse_toml_string`, never validated by `parse_config`; a missing or malformed file counts as `qwenloop = false`. Every other table on this page is ignored. |
| The project's stored record (the `project` row: `max_cycles` column and `config` JSON) | `vibey worker` and every job handler | Cycle cap, per-cycle spend and turn caps, skills-context policy, and (in principle) `features.qwenloop` — see below. |
| Environment variables | See [Environment variables](#environment-variables) | Database DSN, the qwenloop switch, the sovereign DESIGN provider's evidence directory. |

The project record is written once, at creation, by one of two paths:

- **`vibey new`** (see the [CLI reference](cli.md)): `--max-cycles` is stored
  in the `project.max_cycles` column; `--max-cycle-dollars`,
  `--max-cycle-turns`, `--skills-context-mode` and `--skills-context-budget`
  are stored in the `config` JSON as `max_cycle_dollars`, `max_cycle_turns`
  and `skills_context` (the last only when the mode is not `off`).
- **The Kubernetes operator** ([ADR-0025](../architecture/decisions/0025-kubernetes-operator-crd-keda.md)):
  a `VibeyProject` spec's `maxCycles` sets the column (default `10`);
  `repo`, `maxCycleDollars`, `maxCycleTurns` and `skillsContext` are stored in
  the `config` JSON. `spec.engines` is stored as a flat `engines` list that
  nothing reads back yet.

Neither path passes through `parse_config`, and neither writes or reads a
`vibey.toml`. No command updates these values on an existing project.

Neither path writes a `features` key either, so the worker's check of the
stored `features.qwenloop` is always false for projects created today:
**`VIBEY_FEATURE_QWENLOOP` is the switch that reaches the worker.**

## Environment variables

| Variable | Read by | Effect |
|---|---|---|
| `VIBEY_PG_URL` | `bootstrap.database_url()` (every command that opens the queue) | PostgreSQL DSN. Required; there is no default — `vibey` exits with `DatabaseNotConfigured` if it is unset. |
| `VIBEY_FEATURE_QWENLOOP` | `vibey worker` (`bootstrap._qwenloop_enabled`), `vibey doctor` (`cli/main.py` `_qwenloop_feature_enabled`), and `load_config_from_path` | Overrides `features.qwenloop`. `1`, `true`, `yes`, `on` (case-insensitive, surrounding whitespace ignored) enable; any other value disables. When set it wins over both the stored project record and `./vibey.toml`. Only `load_config_from_path` rejects a non-boolean value. For the worker, enabling it adds a qwenloop adapter and makes qwenloop the standby engine for BUILD rotation. |
| `VIBEY_EVIDENCE_DIR` | `vibey work --provider qwenloop`, `vibey worker --provider qwenloop` | Directory of reading that the sovereign DESIGN provider's research stage draws from ([ADR-0027](../architecture/decisions/0027-sovereign-design-provider.md)). Unset, research refuses rather than inventing a source, and the phase stops there. |

## Schema semantics

`domain/config.py` is a pure, stdlib-only module with no filesystem access
of its own (reading the file is an infrastructure concern). Every table
below is optional; omit any of them and the listed defaults apply.

Validation is partial. The Type column is the intended shape. `parse_config`
type-checks every key except `[budget].*`, `[phases.*].engines` (not even
checked to be a list — a bare string is split into single-character engine
ids), `[phases.*].parallelism`, the elements of `[isolation].egress` and
`[provision].plugins`, and the values of `[engines].weights`; those are stored
as written. No numeric range is checked outside `[qwenloop]`
(`idle_timeout_seconds ≥ 0`, `startup_timeout_seconds > 0`,
`context_window > 0`), booleans pass integer checks (`max_cycles = true` is
accepted), and `[deploy].target` / `[deploy].iac` accept any string.

Engine names: an unknown engine name in `[engines].enabled` or as a key of
`[engines].weights` fails validation with a `ConfigError` naming the offending
path, as does `qwenloop` in `[engines].enabled` or any `[phases.*].engines`
list before `features.qwenloop = true`. `[phases.*].engines` entries are
otherwise not validated — unknown names and engines outside
`[engines].enabled` are accepted as written — and `[engines].weights` may name
`qwenloop` without the feature flag. Unknown tables (for example
`[skills_context]`) are silently ignored. All of this applies only when
something calls `load_config_from_path`/`parse_config`, which nothing in this
codebase does outside tests.

## `[project]`

| Field | Type | Default | Notes |
|---|---|---|---|
| `name` | string | *required* | Project name. |
| `repo` | string | `"."` | Path to the repository this project builds against. |
| `max_cycles` | integer | `10` | Cap on delivery cycles. Not range-checked. The live value is the `project.max_cycles` column set by `vibey new --max-cycles` or `spec.maxCycles`. |
| `strict_loopback` | boolean | `false` | When true, tightens review-loopback routing ([ADR-0010](../architecture/decisions/0010-review-loopback-routing.md)). |

## `[isolation]`

| Field | Type | Default | Notes |
|---|---|---|---|
| `level` | string | `"worktree"` | One of `worktree`, `container`, `vm`. |
| `allow_push` | boolean | `false` | Whether a worktree may push to a remote. |
| `egress` | array of strings | `[]` | Allowed egress destinations when network isolation is otherwise closed. Element types are not validated. |

`worktree` isolation is the one active runtime behavior today: every job
and phase runs in an isolated ephemeral git worktree. `container` and `vm`
are schema-valid values, and the container hardening path
(`infrastructure/container/config.py`'s `ContainerConfig`,
`infrastructure/container/runtime.py`'s `OciContainerExecutor`) is
implemented and unit-tested, but it is never constructed by `bootstrap.py`
or anything else outside `infrastructure/container/` and its tests, and
`[isolation]` itself is never read from a real `vibey.toml`. Setting
`level = "container"` has no effect today; see
[SECURITY.md](https://github.com/the-vibey-project/vibey/blob/main/SECURITY.md#1-worktree--container-isolation-runtime-adr-0008-task-91)
for the same disclosure.

## `[budget]`

| Field | Type | Default | Notes |
|---|---|---|---|
| `max_dollars_per_cycle` | float or unset | unset (no cap) | Intended per-cycle spend cap. Not validated. |
| `max_dollars_total` | float or unset | unset (no cap) | Intended total spend cap across the project's lifetime. Not validated. |
| `max_turns_per_item` | integer or unset | unset (no cap) | Intended per-work-item turn cap; the implemented cap (`max_cycle_turns`) is per cycle. Not validated. |

None of these keys is read at runtime. The live brake is the project's stored
`max_cycle_dollars` / `max_cycle_turns` (set by `vibey new --max-cycle-dollars`
/ `--max-cycle-turns`, or the operator's `spec.maxCycleDollars` /
`spec.maxCycleTurns`). `LedgerBudgetSource` sums them live from the current
cycle's `TurnCompleted` and `BudgetSpent` ledger events — never estimated
ahead of time — and tripping either parks a `budget_exhausted` gate. With
neither set, spend is uncapped.

`vibey cost` prints caps from a `budget` key in the stored project config
(`max_dollars_per_cycle`, `max_dollars_total`) that nothing writes, so it
currently shows the fallbacks $40.00 (cycle) and $250.00 (total) rather than
the real cap.

## `[engines]`

| Field | Type | Default | Notes |
|---|---|---|---|
| `enabled` | array of strings | `["claudeloop", "codexloop", "cursorloop", "agyloop"]` | Must be a subset of the known engines below. If omitted while `features.qwenloop = true`, `qwenloop` is appended to the default automatically; an explicit list is never extended. |
| `weights` | table of string→int | `{}` | Per-engine weight for smooth weighted round robin ([ADR-0005](../architecture/decisions/0005-smooth-weighted-round-robin.md)). Keys must be known engines; values are not validated. |

Known engine ids: `claudeloop`, `codexloop`, `cursorloop`, `agyloop`, and
`qwenloop` (valid in `enabled` and `[phases.*].engines` only once
`features.qwenloop = true`).

## `[phases.design]`, `[phases.build]`, `[phases.review]`

Each phase table accepts the same three fields:

| Field | Type | Default (per phase) | Notes |
|---|---|---|---|
| `effort` | string | `design` = `high`, `build` = `low`, `review` = `high` | One of `trivial`, `low`, `standard`, `high`, `max`. |
| `engines` | array of strings or unset | unset (falls back to `[engines].enabled`) | Engine ids this phase may use. Not validated against known engines or `[engines].enabled`, and not checked to be a list. |
| `parallelism` | integer or unset | unset | Per-phase worker concurrency override. Not validated. |

```toml
[phases.build]
effort = "standard"
engines = ["claudeloop", "agyloop"]
parallelism = 4
```

## `[provision]`

| Field | Type | Default | Notes |
|---|---|---|---|
| `plugins` | array of strings | `[]` | Reserved for agent-surface provisioning plugins ([ADR-0011](../architecture/decisions/0011-agent-surface-provisioning.md)). Parsed and stored only; `infrastructure/provision/agent_surface.py` does not read it today. |

## `[deploy]`

| Field | Type | Default | Notes |
|---|---|---|---|
| `enabled` | boolean | `false` | Opts the project into the DEPLOY_DESIGN / DEPLOY_EXECUTE / DEPLOY_REVIEW stage set. |
| `target` | string | `"azure"` | Deployment target. Azure is the only implemented target today; other strings are accepted by `parse_config`. |
| `iac` | string | `"bicep"` | Infrastructure-as-code format used by the deploy adapters; other strings are accepted by `parse_config`. |

## `[features]`

| Field | Type | Default | Notes |
|---|---|---|---|
| `qwenloop` | boolean | `false` | Must be `true` before `qwenloop` can appear in `[engines].enabled` or any `[phases.*].engines` list. |

Runtime: `vibey doctor` reads this key from `./vibey.toml`. `vibey worker`
reads it from the project's stored config record, which `vibey new` and the
operator never write, so for the worker `VIBEY_FEATURE_QWENLOOP=1` is
currently the only way to enable qwenloop. The environment variable overrides
both. Without it, the worker's default adapter set has no qwenloop adapter.

## `[qwenloop]`

Only meaningful when `features.qwenloop = true`. In engine-driven BUILD
rotation qwenloop is a standby tier — selected only when no paid engine is
eligible ([ADR-0015](../architecture/decisions/0015-qwenloop-standby.md)).
It is also the sovereign DESIGN provider, selected explicitly with
`vibey work --provider qwenloop` or `vibey worker --provider qwenloop`
([ADR-0027](../architecture/decisions/0027-sovereign-design-provider.md)).
These keys mirror the runner's own `QwenConfig`
(`src/vibey_runners/qwen/src/qwenloop/domain/config.py`, which additionally
has `max_turns`, default `40`, must be positive); `parse_config` validates
them into `VibeyConfig`, but nothing passes them to the runner.

| Field | Type | Default | Notes |
|---|---|---|---|
| `backend` | string | `"auto"` | One of `auto`, `llama.cpp`, `vllm`. |
| `portable_profile` | string | `"qwen2.5-coder-14b-q5-k-m"` | Model profile used on the portable (CPU/quantized) backend path. |
| `nvidia_profile` | string | `"qwen2.5-coder-14b-bf16"` | Model profile used when an NVIDIA GPU backend is selected. |
| `idle_timeout_seconds` | integer | `900` | Must be non-negative; how long an idle local model stays warm. |
| `startup_timeout_seconds` | integer | `180` | Must be positive. |
| `context_window` | integer | `32768` | Must be positive. |

## Skills context (project config record — not a `vibey.toml` table) { #skills_context }

`VibeyConfig` has no `skills_context` field; a `[skills_context]` table in
`vibey.toml` is silently ignored by `parse_config`. The values live in the
project's stored config record and are written by
`vibey new --skills-context-mode` / `--skills-context-budget` (only when the
mode is not `off`; see the [CLI reference](cli.md#vibey-new-name)) or by the
operator's `spec.skillsContext` object (copied verbatim).
`compiler_from_config` (`infrastructure/skills_context.py`) reads them when
`bootstrap.build_full_worker` builds the worker ([ADR-0031](../architecture/decisions/0031-skills-context-packets-over-a-process-boundary.md)).

| Field | Type | Default | Notes |
|---|---|---|---|
| `mode` | string | `"off"` | `off`, `shadow` (measure only, never changes prompts), or `inject` (append successful packets to BUILD prompts). Any other value raises when the worker is built. |
| `budget` | integer | `6000` | Token budget for retrieval, 1,000–32,000 (enforced by the `vibey new` flag, the operator CRD, and `VibeySkillsContextCompiler`). |
| `timeout_seconds` | number | `120.0` | Skills compile timeout; must be positive. Settable only through `spec.skillsContext`. |
| `command` | array of non-empty strings | unset (`<python> -m vibey_skills.cli`) | Override for the `vibey-skills` command. Read by `compiler_from_config` but not declared in the `VibeyProject` CRD schema, so neither creation path sets it today. |
| `index_path` | string | `.vibey/skills-context/index` under the repo | Path to the skills index; relative paths resolve under the repo. Read by `compiler_from_config` but not declared in the CRD schema, so neither creation path sets it today. |

## Full example

This is a valid file exercising most of the schema that `parse_config`
validates — not a file any command reads from disk (apart from `vibey doctor`
honouring its `[features].qwenloop`; see the top of this page).

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
