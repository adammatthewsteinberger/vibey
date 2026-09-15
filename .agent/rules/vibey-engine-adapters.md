# vibey-engine-adapters (Antigravity mirror of `.claude/skills/vibey-engine-adapters/SKILL.md`)

# vibey engine adapters

Vibey drives five autonomous session runners: `claudeloop`, `codexloop`,
`cursorloop`, `agyloop` (the paid pool, `DEFAULT_DESCRIPTORS`) and `qwenloop`
(a local model; opt-in via `[features] qwenloop = true` or
`VIBEY_FEATURE_QWENLOOP`, ADR-0015). qwenloop is also the sovereign DESIGN
provider (`infrastructure/engines/qwenloop_design.py`, selected with
`vibey worker --provider qwenloop`, ADR-0027; sub-doctrine 8.a makes the sovereign
path the preference, not the fallback). The runners' source lives in this
repository under `src/vibey_runners/{claude,codex,cursor,agy,qwen,common}`
(ADR-0021); vibey drives the installed binaries, not those packages' Python
APIs. Each has its own CLI surface, effort vocabulary,
state directory, and done marker. Vibey abstracts these differences via
`EngineAdapter`, a `Protocol` defined in `application/interfaces/engines.py`
and re-exported from `application/ports.py`.

## The adapter pattern

`EngineAdapter` (read the real definition before relying on this summary —
it's short):
- `descriptor: EngineDescriptor` — a property, the engine's static facts
- `async def preflight() -> PreflightResult` — runs `<engine> doctor`;
  classifies auth + availability
- `async def start(spec: RunSpec) -> RunHandle` — builds argv from
  `descriptor.effort_projection` + isolation flags, spawns the runner,
  returns a handle over its run directory
- `def tail(handle: RunHandle) -> AsyncIterator[EngineEvent]` — streams the
  runner's `events.jsonl`, translated into vibey's own event vocabulary
- `async def send_prompt(handle, text, *, now: bool) -> None` — writes the
  runner's control-plane inbox
- `async def stop(handle: RunHandle) -> StopSummary` — soft-stops the run;
  collects `stop-summary.md` and the final snapshot
- `async def snapshot(handle: RunHandle) -> SnapshotRef | None`
- `def classify(raw: Mapping[str, object]) -> CapacityState` — maps a raw vendor
  error shape to `Available | WindowExhausted | CreditsExhausted | AuthenticationFailed`
- `def attribute(exit_code: int, tail: str) -> FailureClass` — attributes a dead
  process to a `FailureClass` (`capacity`, `engine`, `work`, `vibey`)

`start()` internally calls `infrastructure/engines/argv.py::build_argv()` —
that's a plain function, not an adapter method; it takes both the descriptor
and the `RunSpec` (`build_argv(descriptor, spec)`), not just the spec.

See `application/interfaces/engines.py::EngineAdapter` and
`infrastructure/engines/scripted.py::ScriptedEngine` (the fake runner used in
tests). `infrastructure/engines/loop_process_adapter.py::LoopProcessAdapter`
is the production adapter (it supersedes `ClaudeLoopProcess`): it spawns the
loop process, streams `events.jsonl`, detects `done_marker`, treats exit code 75
as wind-down, and classifies capacity through `classify.py` — one class driven
by descriptors, not one class per engine.

Engine choice for engine-driven BUILD jobs goes through
`SelectingEngineProvider → application/engine_selector.py::EngineSelector`
(SWRR over `domain/rotation.py`), wired in `bootstrap.py`. Selection requires
populated `engine_health` rows, so an engine with no recorded conformance is
never selected.

Before `build.implement` seeds a fresh run, it can ask the `vibey-skills` CLI for
a skills-context packet (`infrastructure/skills_context.py::VibeySkillsContextCompiler`,
modes `off`/`shadow`/`inject`, budget 1,000–32,000 with a 6,000 default;
ADR-0031). The packet is recorded as a `vibey_skills_context_packet` artifact.

## Engine descriptors

`infrastructure/engines/descriptors.py` defines `CLAUDELOOP`, `CODEXLOOP`,
`CURSORLOOP`, `AGYLOOP`, `QWENLOOP` — one `EngineDescriptor` per engine.
`DEFAULT_DESCRIPTORS` is the paid four, `ALL_DESCRIPTORS` adds qwenloop, and
`BY_ENGINE_ID` maps every `EngineId`. The worker adds a `LoopProcessAdapter` for
qwenloop only when the feature flag is on.

Each descriptor (`domain/engine.py::EngineDescriptor`) declares:
- `engine_id`, `binary` — the executable name (e.g., `"claudeloop"`), `min_version`
- `state_dir` — where runs are stored (e.g., `".claudeloop/"`)
- `done_marker` — the text signaling completion (e.g., `"CLAUDELOOP_TASK_FULLY_COMPLETE"`)
- `capabilities` — which features it supports (`savepoints`, `unwind`, etc.)
- `effort_projection` — how vibey's 5-level ladder (`TRIVIAL, LOW, STANDARD, HIGH, MAX`)
  maps to the engine's native flags
- `auth_env` — environment variables that must be set (empty for qwenloop)
- `session_verb`, `isolation_flags` (per `IsolationLevel`)
- `cost_per_mtok_in`/`cost_per_mtok_out`, `context_window`, `base_weight` (rotation weight)
- `supports_cwd_flag` (default `True`; codexloop: `False`) and `plan_flag`
  (default `None` = positional plan path; cursorloop: `"--plan"`)

**Effort projection example** (claudeloop, as in `descriptors.py`):

```python
effort_projection={
    Effort.TRIVIAL: EngineInvocation(("--preset", "low", "--effort", "low"), achieved=Effort.TRIVIAL),
    Effort.LOW: EngineInvocation(("--preset", "low", "--effort", "medium"), achieved=Effort.LOW),
    Effort.STANDARD: EngineInvocation(("--preset", "medium", "--effort", "high"), achieved=Effort.STANDARD),
    Effort.HIGH: EngineInvocation(("--preset", "high", "--effort", "high"), achieved=Effort.HIGH),
    Effort.MAX: EngineInvocation(("--preset", "high", "--effort", "max"), achieved=Effort.MAX),
}
```

qwenloop projects effort onto `--max-turns` (8, 16, 40, 64, 96).

If an engine **saturates**, the descriptor sets `achieved` to the tier it
actually delivers. codexloop is the extreme case: its `run` has no effort flag,
so every level projects to empty argv with `achieved=Effort.STANDARD`.
`domain/rotation.py::fidelity_factor(descriptor, requested)` computes the
`Candidate.fidelity_factor` that scales the effective weight of engines that
saturate below the requested effort; `application/engine_selector.py` applies
it.

See ADR-0006 (normalized effort ladder).

## argv building

`infrastructure/engines/argv.py::build_argv(descriptor, spec)` takes an
`EngineDescriptor` and a `RunSpec` (fields: `run_id`, `worktree_path`,
`prompt`, `effort`, `isolation`, optional `session_id` to resume) and
produces the command line — read the real function, it is short. As of
2026-09-15 it emits, in order:

1. `<binary> run`, or `<binary> resume <session_id>` when `spec.session_id` is set.
2. For `run` only: the plan path `<worktree>/.vibey/plans/<run_id>.md`, prefixed
   by `descriptor.plan_flag` when the engine wants a flag (cursorloop: `--plan`),
   then `--run-id <run_id>` (so the adapter finds the run directory the process
   writes to).
3. `descriptor.invoke(effort).argv`.
4. `descriptor.isolation_flags.get(isolation, ())`.
5. `--cwd <worktree_path>`, only when `descriptor.supports_cwd_flag` (codexloop:
   `False`).

25 golden files under `tests/infrastructure/engines/golden/` (5 engines × 5
efforts; `test_argv.py` parametrizes over `ALL_DESCRIPTORS`) capture the
expected argv for each combination — the source of truth for the exact current
shape.

## Capacity classification

`infrastructure/engines/classify.py::classify_capacity(engine_id, raw)` dispatches
to one private classifier per engine (all five) and maps vendor-specific
error shapes to vibey's `CapacityState`:

```python
Available | WindowExhausted | CreditsExhausted | AuthenticationFailed
```

**The critical distinction:** `WindowExhausted` has a `resets_at` deadline;
`CreditsExhausted` does not. A window exhaustion is waitable; credits
exhaustion requires a human top-up.

Each engine's classifier pattern is versioned in `CREDITS_FIXTURES`,
`WINDOW_FIXTURES`, `AUTH_FIXTURES`, and `AVAILABLE_FIXTURES` — shared between
the classifier's own tests and the conformance suite.

**Note:** these are synthesized fixture payloads, not captured real vendor
errors. If you get access to real `*loop` binaries or real captured error
payloads, this is the first thing to replace.

## The conformance suite

`application/conformance.py::run_conformance()` runs 9 named checks per
engine (grep the file for the check-name strings if this list drifts):
`binary` (installed + version), `flags` (`run --help` exposes what the
descriptor claims), `state_dir`, `run_dir_shape` (a real run produces
`meta.json`/`events.jsonl`/`snapshots/latest.json` — this one races a real
subprocess's own startup time, not just an instant file check; read the
function if you're touching it), `snapshot_schema`, `capacity_map`,
`done_marker`, `control_plane`, `structured_verdict`.

A failing conformance check marks that engine **ineligible** rather than
letting it fail mid-cycle.

```bash
vibey doctor --conformance --record
```

`--record` persists the preflight and conformance result to `engine_health`.
Without a recorded pass the worker warns and never selects the engine for
engine-driven jobs.

Live runs of the suite are split in two modes (ADR-0030): `tests/live/` with
`@pytest.mark.live` runs conformance and rotation against `ScriptedEngine`
and scripted stand-in binaries, with no model calls; `@pytest.mark.paid` spawns real binaries
against real models and is excluded by default.

See ADR-0001 (orchestrate, do not reimplement).

## When to read this skill

Before:
- Adding a new engine.
- Changing effort mappings.
- Debugging why rotation is skipping an engine.
- Updating capacity classification patterns after a vendor API change.
