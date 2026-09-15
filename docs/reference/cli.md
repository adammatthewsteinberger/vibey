# CLI reference

Every `vibey` command and subcommand, written by hand against
[`src/vibey/cli/main.py`](https://github.com/the-vibey-project/vibey/blob/main/src/vibey/cli/main.py)
and checked against it as of 2026-09-15. Nothing generates this page. If it
and the code disagree, the code wins. `vibey <command> --help` prints the
code's own help text, which is shorter than this page and in places less
complete (for example, `vibey work --help` does not list `qwenloop`).

Top-level commands, in `vibey --help` order: `new`, `answer`, `work`,
`watch`, `recover`, `status`, `engines`, `cost`, `doctor`, `operator`,
`worker`, and the command groups `design`, `visual`, `deploy`, `ledger`.
Bare `vibey`, and each bare command group, prints help.

Commands that read or write project state need `VIBEY_PG_URL` (see
[Environment variables](#environment-variables)). `doctor` needs it only
with `--record` or `--cluster`.

## Global options

These apply to every command; they must come before the subcommand name.

| Option | Default | What it does |
|---|---|---|
| `--version` | — | Print `vibey <version>` and exit. |
| `--verbose` / `-v` (repeatable) | `0` | `-v` debug, `-vv` also third-party libraries, `-vvv` full payloads. |
| `--quiet` / `-q` | off | Warnings and errors only. |
| `--log-level LEVEL` | unset | `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL` (case-insensitive). Overrides the level `-v` or `-q` would pick. |
| `--log-file PATH` | unset | Also write redacted JSON lines to this file. |
| `--install-completion` | — | Install shell completion for the current shell. |
| `--show-completion` | — | Print the completion script for the current shell. |
| `--help` | — | Show help and exit. |

`-v` and `-q` are mutually exclusive: together they print
`Error: --quiet and --verbose are mutually exclusive` and exit 2. An unknown
`--log-level` exits 2 with `Error: invalid log level ...`. `--log-level`
fixes the level, but the `-v` count still widens scope, so
`--log-level WARNING -vvv` means warnings from third-party libraries too,
with payloads.

## Exit codes and errors

| Code | Meaning |
|---|---|
| `0` | Success. Also a guarded command whose reader closed the pipe early. |
| `1` | Nothing to act on, or a check failed: no project exists (``no projects found; create one with `vibey new` first``); an explicit `PROJECT_ID` is unknown in `watch`, `cost`, or `deploy *`; `recover` without `--project` or `--all`; `doctor --engine` with an unknown name; `doctor --conformance` with a failing engine; `doctor --cluster` with a failing check; `operator` without the `operator` extra; `worker --azure az` without a logged-in Azure CLI. |
| `2` | Usage error: a bad global flag (see above); typer's own validation (missing argument, malformed UUID, a value outside an option's minimum or maximum, unknown option); `new --skills-context-mode` outside `off`/`shadow`/`inject`; `answer` mode conflicts or a `--raw` value that is not a JSON object; `worker` with an unknown `--engines` id, `--provider`, or `--azure` value. |
| `3` | Blocked by a domain rule, in a guarded command. Prints `Error: <message>` on stderr, plus a next-step hint for some error types. |
| `130` | Interrupted with Ctrl-C, in a guarded command (prints `Interrupted.`). |

### Guarded and unguarded commands

Seven commands run inside `vibey.cli.errors.guard()`: `new`,
`design resume`, `design accept`, `work`, `visual accept`, `visual waive`,
and `worker`. For these, any `VibeyError` — an unknown project or provider,
a wrong phase, an invalid spec, no eligible engine, a rejected handoff, an
unset `VIBEY_PG_URL` — becomes the one-line `Error:` message and exit 3.
Ctrl-C exits 130 and a closed pipe exits 0. Exceptions that are not
`VibeyError` keep their Python traceback.

The other commands (`answer`, `watch`, `recover`, `status`, `engines`,
`cost`, `ledger show`, every `deploy` subcommand, `doctor`, `operator`) are
not guarded. Their own checks exit 1 or 2 as listed above; any other error,
including an unset `VIBEY_PG_URL`, surfaces as a Python traceback.

Known gaps in unknown-project handling:

- `status <unknown-id>` raises `ValueError: unknown project ...` as a traceback.
- `engines <unknown-id>` prints `no engines recorded for project` and exits 0.
- `ledger show <unknown-id>` prints nothing and exits 0.

### Next-step hints

`guard()` appends a hint for these error types. Two hints name a command
that does not exist, and one gives guidance that does not work today; the
right-hand column says what to do instead.

| Error | Hint printed | What actually works |
|---|---|---|
| `NoEligibleEngine` | Every engine is excluded, circuit-open, or missing a capability; run `vibey engines` or `vibey doctor`. | As printed. |
| `BudgetExceeded` | Raise the cap in `vibey.toml` under `[budget]`, or run `vibey cost`. | Nothing in `src/vibey` raises this error, and no runtime code reads `[budget]` from `vibey.toml`. A tripped per-cycle cap parks a `budget_exhausted` gate; raise it with `vibey answer GATE_ID --raw '{"max_dollars": N}'` (or `"max_turns"`). |
| `EscalationExhausted` | `vibey gates` lists the human gate it raised. | There is no `vibey gates` command, and no command lists gates. See [Finding a gate id](#finding-a-gate-id), then `vibey answer` it. |
| `HandoffRejected` | `vibey gates` shows what the no-loss gate could not carry over. | Same: see [Finding a gate id](#finding-a-gate-id); the gate's `prompt` says what could not be carried over. |
| `IllegalTransitionError` | The project is not in a phase this command applies to; `vibey status` shows the phase. | As printed. |
| `InvalidSpecError` | Run `vibey design` to finish the spec before building. | As printed. |
| `InvalidPhaseError` | Likely a bug in vibey rather than the project. | As printed. |

## `vibey new NAME`

Create a project and enqueue its first DESIGN interview.

| Option | Default | What it does |
|---|---|---|
| `--repo PATH` | `.` | Repository the project builds against. |
| `--max-cycles N` | `10` | Cap on delivery cycles before the project stops (min 1). |
| `--max-cycle-dollars F` | unset | Per-cycle dollar cap (min 0.01), stored as `max_cycle_dollars` in project config. Tripping it parks a `budget_exhausted` gate instead of starting more sessions (ADR-0024). Unset means no dollar cap. |
| `--max-cycle-turns N` | unset | Per-cycle engine-turn cap (min 1), stored as `max_cycle_turns`. |
| `--skills-context-mode {off,shadow,inject}` | `off` | `vibey-skills` retrieval mode (ADR-0031) — see [Configuration reference](configuration.md#skills_context). Any other value exits 2. |
| `--skills-context-budget N` | `6000` | Token budget for skills retrieval (1,000–32,000). Stored only when the mode is not `off`. |

Prints `project <id>` and `design job <id>`. The project id is the
`PROJECT_ID` the other commands take.

## `vibey answer GATE_ID [QUESTION_ID=ANSWER ...]`

Answer a parked human gate. Exactly one of the following modes is required
(or `--defaults` alone for interview gates):

| Form | Used for |
|---|---|
| `QUESTION_ID=ANSWER [QUESTION_ID=ANSWER ...]` | Interview gates, answered per question. Combine with `--defaults` to fill in every other question's default; the explicit pairs win. |
| `--defaults` | Interview gates: accept every question's default. Question keys are model-minted per run, so this needs none. |
| `--choice VALUE` | Deployment and triage gates: sends `{"choice": VALUE}`. |
| `--verdict VALUE` | Review gates: sends `{"verdict": VALUE}` — `accept`, `changes`, `cancel`, `approve`, or `request_changes`. |
| `--raw JSON` | Any other gate shape, e.g. raising a tripped budget cap: `--raw '{"max_dollars": 25}'` or `--raw '{"max_turns": 50}'`. |

Prints `answered <gate_id>`. These exit 2 with a one-line message:
combining `--defaults` with `--choice`, `--verdict`, or `--raw`; giving no
mode or more than one; `--raw` that is not valid JSON or not a JSON object.
A positional item without `=` (`InvalidAnswer`) and an unknown gate id
(`LookupError`) currently surface as tracebacks, because `answer` is not
guarded.

### Finding a gate id

No `vibey` command lists open gates today. Gates live in the `human_gate`
table; the worker also sends `NOTIFY vibey_gate_raised` with the gate id when
one is raised. To list open gates:

```sql
SELECT gate_id, project_id, kind, prompt, options, default_answer, raised_at
FROM human_gate
WHERE answered_at IS NULL
ORDER BY raised_at;
```

## `vibey work PROJECT_ID`

Process one ready DESIGN job, or, when the project is in VISUAL_DESIGN, one
visual-inventory job. Live engine use is explicit and capped. Prints
`processed one job` or `no ready job`.

| Option | Default | What it does |
|---|---|---|
| `--provider {scripted,claudeloop,qwenloop}` | `scripted` | `scripted` needs no live engine. `claudeloop` runs a real, paid session capped by `--max-turns` and `--max-dollars`; its spend is recorded as `budget_spent` ledger events so the budget brake counts it. `qwenloop` runs the sovereign local DESIGN provider (ADR-0015, ADR-0027) and reads research material from `$VIBEY_EVIDENCE_DIR`; with that unset, research refuses rather than inventing a source, and DESIGN stops there. Any other value exits 3 with `Error: provider must be 'scripted', 'claudeloop', or 'qwenloop'`. |
| `--max-turns N` | `1` | Turn cap for this one job (min 1). |
| `--max-dollars F` | `0.25` | Dollar cap for this one job (0.01–10). |

In VISUAL_DESIGN only `--provider scripted` works; any other provider exits
3 with `Error: no live VisualInventoryProducer is implemented yet; use --provider scripted`.
An unknown `PROJECT_ID` exits 3.

## `vibey design`

Bare `vibey design` prints help. Subcommands:

| Subcommand | What it does |
|---|---|
| `design resume PROJECT_ID` | Enqueue or resume the project's DESIGN interview. Prints `design job <id>`. |
| `design accept PROJECT_ID [--spec-json PATH] [--visual/--no-visual]` | Accept the synthesized spec (optionally importing JSON first) and choose whether to enter the VISUAL_DESIGN interstitial. Defaults to `--no-visual`; the choice is never implicit. Prints `accepted design for <id>; entered <phase>; context under <repo_path>`. |

`--spec-json` expects a JSON object with:

- `objective` and `walking_skeleton` — required strings;
- `criteria` — required list of objects with `criterion_id`, `given`, `when`, `then`, `fit`;
- `constraints` — optional list of `{"text": ..., "kind": "hard" | "soft"}`;
- `non_goals` — optional list of strings;
- `nfrs` — optional list of objects with `nfr_id`, `attribute`, `scale`, `meter`, `must`, `wish` (string or `null`), `fit_criterion`.

The shapes are the dataclasses in `src/vibey/domain/spec.py`. A missing
required key or an unreadable file currently surfaces as a traceback,
because `guard()` renders only `VibeyError`.

## `vibey visual`

Bare `vibey visual` prints help. Subcommands:

| Subcommand | What it does |
|---|---|
| `visual accept PROJECT_ID` | Accept the reviewed visual plan and enter BUILD. Prints `accepted visual design for <id>; entered <phase>`. |
| `visual waive PROJECT_ID` | Explicitly waive the visual plan (the inventory must still be complete) and enter BUILD. Prints `waived visual design for <id>; entered <phase>`. |

## `vibey watch [PROJECT_ID]`

Live TUI dashboard: current phase, queue, engine circuits, active worktrees,
and a ledger tail. Defaults to the most recently created project; an unknown
id prints `unknown project <id>` and exits 1.

| Option | Default | What it does |
|---|---|---|
| `--replay` | off | Replay the project's historical ledger events instead of following live state. |
| `--speed F` | `1.0` | Replay rate in ledger states per second while playing (`--speed 4` advances four states per second). `0` or a negative value disables auto-advance. The option's `--help` text calls it a "multiplier"; it is a rate. |

Replay starts paused. Keys: Space play/pause, Right or `n` next step, Left or
`p` previous step, `q` quit.

## `vibey recover`

Recover stuck leased jobs (e.g. after a worker crash): every job in state
`leased` is set back to `ready`, and its lease owner, lease expiry, and
assigned engine are cleared.

| Option | Default | What it does |
|---|---|---|
| `--project ID` | unset | Recover jobs for one project. |
| `--all` | off | Recover jobs for every project. Wins if `--project` is also given. |

One of `--project` or `--all` is required; with neither, it prints
`Must specify either --project <id> or --all` and exits 1.

The printed `Recovered N stuck job(s).` count is currently always `0`, even
when rows were reset (the status-string regex in `main.py` never matches).
Check the queue depth in `vibey status` to confirm the result.

## `vibey status [PROJECT_ID]`

Show the project's name, phase, cycle, visual and deployment decisions,
repository path, queue depth per job state, and engine circuits (circuit
state, consecutive failures, cycle cost). Defaults to the most recently
created project.

| Option | Default | What it does |
|---|---|---|
| `--json` | off | Emit JSON instead: `project_id`, `name`, `phase`, `cycle`, `max_cycles`, `repo_path`, `visual_decision`, `deployment_decision`, `queue_depth`, `circuits` (each with `engine_id`, `installed`, `version`, `conformance_ok`, `circuit`, `capacity_state`, `consecutive_fail`, `cost_usd_cycle`, `selected_count`), and `active_worktrees`. |

## `vibey engines [PROJECT_ID]`

Show recorded engine health for a project as a table: engine, version,
circuit-breaker state, consecutive failures, selection count, and cycle
cost. Rows exist only for engines that `vibey doctor --record` or a worker's
startup preflight has recorded; with none it prints
`no engines recorded for project`. Defaults to the most recently created
project.

## `vibey cost [PROJECT_ID]`

Show per-engine spend for the current cycle, read from `engine_health`, with
a total and two budget caps. The `(N turns)` figure after each engine is its
selection count, not a turn count. Defaults to the most recently created
project.

The caps come from a `budget` table in the project's stored config
(`max_dollars_per_cycle`, `max_dollars_total`), with fallbacks of $40.00 and
$250.00. No code path writes that table today — not `vibey new`, not the
Kubernetes operator, and no runtime code reads `[budget]` from `vibey.toml` — so the command
prints the $40.00 / $250.00 placeholders. The cap that is enforced is
`--max-cycle-dollars` / `--max-cycle-turns` from `vibey new`, applied by the
worker's budget brake; `vibey cost` does not print it.

## `vibey ledger`

Bare `vibey ledger` prints help. Subcommand:

| Subcommand | Option | Default | What it does |
|---|---|---|---|
| `ledger show [PROJECT_ID]` | `--limit N` / `-n` | `50` | Show the most recent N events (min 1). |
| | `--phase PHASE` | unset | Filter to one phase, by name or value, case-insensitive (`BUILD`, `deploy_design`). |
| | `--kind KIND` | unset | Filter to one event kind, by name or value, case-insensitive. |

Prints one line per event, oldest first:
`#<seq> <YYYY-MM-DD HH:MM:SS> [<PHASE>] <kind> [<engine>]`. Filters apply
before `--limit`. Defaults to the most recently created project.

## `vibey deploy`

Phases ④–⑥. Bare `vibey deploy` prints help. Each subcommand takes an
optional `PROJECT_ID`, defaulting to the latest project; an unknown id
prints `unknown project <id>` and exits 1.

| Subcommand | What it does |
|---|---|
| `deploy status` | Prints the project name, its current phase, cycle, and the endpoint recorded by the most recent `deployment_verification` artifact (`(none)` if there is none). |
| `deploy inspect` | Prints spec id, scope digest, and monthly budget from the most recent `deployment_spec_accepted` decision. When no spec has been accepted it prints the placeholders `default` / `none` / `$100.00`. |
| `deploy plan` | Placeholder, not yet implemented: prints `Status: NOT EVALUATED` with every check marked "not checked". Reads no IaC changeset and evaluates no budget. |
| `deploy cancel` | Placeholder, not yet implemented: prints a notice and cancels nothing. No cloud resource, ledger event, or job or phase state is touched. |
| `deploy rollback` | Placeholder, not yet implemented: prints a notice and performs no rollback. |

Only `deploy status` and `deploy inspect` read real state today; the other
three reserve the command surface. Deployments themselves run through
`vibey worker` (see `--azure`) after an explicit opt-in at REVIEW.

## `vibey doctor`

Check engine installs and auth; optionally run the conformance suite, or run
the in-cluster preflight instead.

| Option | Default | What it does |
|---|---|---|
| `--conformance` | off | Run the 9-check conformance suite against each checked engine that is installed. |
| `--engine ENGINE` | unset | Check one engine: `claudeloop`, `codexloop`, `cursorloop`, `agyloop`, or `qwenloop`. An unknown name prints `Unknown engine: <name>` and exits 1. |
| `--record` | off | Persist preflight (and conformance, with `--conformance`) results to `engine_health`. Exits 1 if no project exists. |
| `--project ID` | latest | Project to record health for, with `--record`. |
| `--cluster` | off | Run the in-cluster preflight instead of the engine checks — see [Kubernetes guide](../guides/kubernetes.md). |

With `--engine` unset, doctor checks the four paid engines (`claudeloop`,
`codexloop`, `cursorloop`, `agyloop`) whether or not they are installed —
missing ones print `NOT INSTALLED` — and adds `qwenloop` when
`VIBEY_FEATURE_QWENLOOP` is truthy or, if that variable is unset,
`./vibey.toml` in the current directory has `[features] qwenloop = true`.
`--engine qwenloop` works regardless of the flag.

Each engine line shows install state, version, and auth. Auth is the exit
status of `<binary> doctor`; if that command cannot run, doctor falls back
to the engine's API-key variable (see
[Environment variables](#environment-variables)).

With `--conformance`, the command exits 1 if any engine fails a check. The
worker does not select an engine for engine-driven jobs until a
`doctor --conformance --record` run has passed for it.

`--cluster` ignores the other options, runs up to six checks, and exits 1 if
any fails: the DSN host resolves beyond its own namespace, the process is not
root, the workspace (current directory) is writable, every installed paid
engine binary has an API key in the environment, the database accepts a
connection, and no migrations are pending. The migrations check is skipped
when the database connection fails.

## `vibey operator`

Run the Kubernetes operator, reconciling `VibeyProject` custom resources
(ADR-0025). Requires the optional extra, `pip install 'vibey[operator]'`;
without it the command prints
`operator support is not installed: pip install 'vibey[operator]'` and exits 1.

| Option | Default | What it does |
|---|---|---|
| `--namespace NS` | unset (cluster-wide) | Watch a single namespace instead of the whole cluster. |

## `vibey worker`

Long-running worker: listens on `vibey_job_ready` and dispatches jobs across
every phase for one project.

| Option | Default | What it does |
|---|---|---|
| `--engines LIST` | the four paid engines | Comma-separated allowlist of engine ids (`claudeloop`, `codexloop`, `cursorloop`, `agyloop`, `qwenloop`) for engine-driven jobs. An unknown id prints `Invalid engine: ...` and exits 2. `qwenloop` joins the pool only when `VIBEY_FEATURE_QWENLOOP` is on (see below). |
| `--parallelism N` / `-j N` | `1` | Concurrent job loops, 1–16. The effective count is clamped to twice the number of allowed paid engines and to the CPU count, and is never below 1. |
| `--once` | off | Process one job and exit (`processed one job` or `no ready job`), instead of running forever. |
| `--provider {scripted,claudeloop,qwenloop}` | `scripted` | DESIGN and decomposition providers. `scripted` is fully offline. `claudeloop` uses a live session for both DESIGN and decomposition, capped by `--max-turns` / `--max-dollars`. `qwenloop` uses the sovereign local DESIGN provider (reads `$VIBEY_EVIDENCE_DIR`) with scripted decomposition. Any other value exits 2. |
| `--max-turns N` | `25` | Turn cap per claudeloop DESIGN or decomposition session (min 1). |
| `--max-dollars F` | `2.0` | Dollar cap per claudeloop DESIGN or decomposition session (0.01–10). |
| `--project ID` | latest | Project to work on. |
| `--wait-for-project SECONDS` | unset (min 1.0) | Poll every N seconds for a project instead of exiting 1 when none exists yet — for long-lived deployments, where exiting means a restart loop. |
| `--azure {memory,az}` | `memory` | Azure client for the deploy stage set. `memory` is an in-memory adapter that touches no real infrastructure. `az` uses the real Azure CLI and mutates real resources on consented deploys; the worker runs `az account show` first and exits 1 if you are not logged in. Any other value exits 2. |

The VISUAL_DESIGN stage always uses the scripted visual provider.

On start the worker preflights every allowed engine. Engines with no passing
recorded conformance produce
``warning: no recorded conformance for <names> -- engine-driven jobs will not select them until `vibey doctor --conformance --record` passes``.
It then prints
`worker started: project=<name> engines=<list or all> parallelism=<n> provider=<p>`.

qwenloop as a standby engine (ADR-0015): the worker enables it only when
`VIBEY_FEATURE_QWENLOOP` is truthy. Unlike `doctor`, the worker does not
read `[features] qwenloop` from `vibey.toml`; it falls back to a `features`
table in the project's stored config, which no creation path writes today.
In practice the environment variable is the only switch for the worker.

Shutdown (ADR-0026): SIGTERM drains the worker — it finishes the job in
hand, claims no more, and exits. A SIGTERM that arrives during startup,
before the handler is installed, is latched at import time and honoured as
soon as the event loop starts. Ctrl-C aborts immediately with exit 130. The
worker writes diagnostic lines to stderr (`sigterm handler registered`,
`drive[<i>] iter=...`); they are temporary instrumentation, not errors.

## Environment variables

Variables read by code under `src/vibey`:

| Variable | Read by | Effect |
|---|---|---|
| `VIBEY_PG_URL` | every command that opens the database; `recover`; `doctor --record`; `doctor --cluster` | PostgreSQL DSN. There is no default: when unset, vibey refuses with `VIBEY_PG_URL is not set. vibey will not guess a database.` (exit 3 from guarded commands, a traceback from the others). |
| `VIBEY_EVIDENCE_DIR` | `work --provider qwenloop`, `worker --provider qwenloop` | Directory of reading material for the qwenloop DESIGN provider's research stage. Unset means research refuses and DESIGN stops there. |
| `VIBEY_FEATURE_QWENLOOP` | `doctor`, `worker` | `1`, `true`, `yes`, or `on` (case-insensitive) enables qwenloop; any other set value disables it. When set it overrides config. When unset, `doctor` falls back to `[features] qwenloop` in `./vibey.toml` and `worker` falls back to the project's stored config. |
| `ANTHROPIC_API_KEY` | `doctor` auth fallback; `doctor --cluster` (which also accepts `ANTHROPIC_AUTH_TOKEN`) | claudeloop credentials. |
| `OPENAI_API_KEY` | `doctor` auth fallback; `doctor --cluster` (which also accepts `AZURE_OPENAI_API_KEY`, `CODEX_API_KEY`) | codexloop credentials. |
| `CURSOR_API_KEY` | `doctor` auth fallback; `doctor --cluster` | cursorloop credentials. |
| `GOOGLE_API_KEY` | `doctor` auth fallback; `doctor --cluster` (which also accepts `GEMINI_API_KEY`, `GOOGLE_APPLICATION_CREDENTIALS`) | agyloop credentials. |
| `VIRTUAL_ENV` | engine session launch | Removed, together with `VIRTUAL_ENV_PROMPT`, `PYTHONHOME`, `PYTHONPATH`, and the matching `PATH` entries, from the environment passed to engine sessions, so an engine does not install into or run vibey's own interpreter. |

Engine sessions otherwise inherit the caller's environment. Build-gate and
git subprocesses inherit it minus every `GIT_*` variable. The engine CLIs
read further variables of their own; see each runner under
`src/vibey_runners/`.
