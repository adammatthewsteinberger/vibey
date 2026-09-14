# Ports and adapters

`application/` and `infrastructure/` are fully implemented (milestone M2).
This page documents the actual port shapes and their concrete adapters —
for the design rationale behind choosing this pattern, see
[`../plans/architecture-and-roadmap.md`](../plans/architecture-and-roadmap.md)
and [ADR 0001](decisions/0001-onion-architecture-with-import-linter.md).

## Why ports are `Protocol`, not `ABC`

`application/ports.py` defines every port as a `typing.Protocol`, not an
abstract base class. Two reasons:

1. **Structural typing keeps `application/` free of any import from
   `infrastructure/`.** A `Protocol` describes a shape; nothing has to
   inherit from it. `import-linter`'s "infrastructure only reachable from
   bootstrap" contract would reject an ABC-based design the moment a
   concrete adapter needed to `from claudeloop.application.ports import
   AgentGatewayBase` — with `Protocol`, the adapter simply implements the
   right methods and duck-types into place.
2. **Fakes for tests are trivial.** `FakeAgentGateway` and friends in
   `tests/application/fakes.py` don't inherit from anything either; they
   just need the right method signatures, which `mypy --strict` verifies
   against the `Protocol` at type-check time — see `test_runner.py` for the
   fakes exercising the real `AutonomousRunner`, including the
   credit-top-up scenario end to end.

## Ports (`application/ports.py`) and their adapters

| Port | Responsibility | Real adapter | Fake (`tests/application/fakes.py`) |
|---|---|---|---|
| `AgentGateway` | Drive a live `ClaudeSDKClient` session — never `query()`, which raises after an error result and exits the process (see [ADR 0002](decisions/0002-agent-sdk-over-subprocess.md)) | `infrastructure/agent/gateway.py::ClaudeAgentGateway` (production); `infrastructure/agent/scripted.py::ScriptedAgentGateway` (test-only, via bootstrap env gate) | `FakeAgentGateway` — replays a scripted list of `TurnOutcome`s |
| `CapacityProbe` | Run the cheap, throwaway turn used while waiting | `infrastructure/agent/gateway.py::ClaudeCapacityProbe` | `FakeCapacityProbe` — replays scripted `TurnSignals` |
| `SessionCatalog` | List/resolve sessions via the SDK's `list_sessions()` | `infrastructure/agent/catalog.py::SdkSessionCatalog` | a plain stub class in `tests/application/test_usecases.py` |
| `ApiGateway` | Invoke a generated REST command against `anthropic.Anthropic()` | `infrastructure/api/gateway.py::AnthropicApiGateway` | — |
| `Clock` | `now()` | `infrastructure/clock.py::SystemClock` | `FakeClock` — settable, doesn't advance on its own |
| `Sleeper` | `await sleep_until(instant)` | `infrastructure/clock.py::AnyioSleeper` | `FakeSleeper` — advances the paired `FakeClock` instantly, records what it was asked to wait for |
| `ProgressReporter` | Human-readable progress to the console | `infrastructure/progress.py::ConsoleProgressReporter` | `FakeProgressReporter` — records calls |
| `AuditLog` | Append-only JSONL of every recorded event | `infrastructure/audit.py::JsonlAuditLog` | `FakeAuditLog` — in-memory list |
| `Notifier` | Tell a human something needs attention | `infrastructure/notify.py::StderrNotifier` | `FakeNotifier` in `tests/application/fakes.py` |
| `RunStateStore` | Persist run state so a killed run is resumable | `infrastructure/state.py::FileRunStateStore` | `FakeStateStore` |
| `SessionLock` | Advisory file lock preventing two runners driving one session | `infrastructure/lock.py::FileSessionLock` | `FakeSessionLock` |
| `RunControl` | Poll mid-run operator commands (stop / prompt / permission / resources / …) | `infrastructure/control.py::FileRunControl` | `FakeRunControl` |
| `RunEventSink` | Realtime redacted event stream | `infrastructure/events.py::JsonlRunEventSink` | `FakeEventSink` |
| `SavePointStore` | Git save points + unwind | `infrastructure/git_savepoints.py::GitSavePointStore` | `FakeSavePointStore` |
| `RunResources` | Run-scoped attachments / skills / folders / memories applied mid-run | `infrastructure/resources/adapter.py::ResourcePortAdapter` over `RunResourceStore` | `_NullRunResources` / test fakes |
| `StateBus` | Publish phase/status for external pollers | `infrastructure/state_bus.py::FileStateBus` | `_NullStateBus` |
| `StreamUi` | Optional Textual token stream | `infrastructure/stream_ui/` | `_NullStreamUi` / `BufferingStreamUi` |
| `Logger` | Structured application logging | `infrastructure/logging.py::StructlogAppLogger` | `FakeLogger` |

`RunStateStore`, `SessionLock`, and `Notifier` are wired into
`AutonomousRunner` via `bootstrap.build_runner`. Mid-run operator commands
resolve the active run under `.claudeloop/runs/<run_id>/` (see also
`bootstrap_ops.py` for CLI-side enqueue helpers).

There's also a narrower `DoctorEnvironment` protocol, local to
`application/usecases/doctor.py` rather than `ports.py`, since `doctor` is
deliberately cheap to run and shouldn't need a full `AgentGateway`. Its real
adapter is `infrastructure/doctor_env.py::RealDoctorEnvironment`, which
shells out to `claude auth status` and `claude mcp list` — the authoritative
sources, rather than re-parsing config files whose format the docs warn
changes between releases.

## Why `FakeClock`/`FakeSleeper`, not `unittest.mock` or real sleeping

The waiting policy in `domain/waiting.py` is designed around instants, not
durations, precisely so the application-layer tests never need to sleep for
real. `FakeClock` holds a settable "now"; `FakeSleeper.sleep_until(instant)`
jumps the paired clock straight to `instant` instead of blocking. This is
what lets `tests/application/test_runner.py` exercise a full credit-top-up
sequence — several failed probes, then a resumed run — in milliseconds of
real wall-clock test time. See
[`../contributing/testing.md`](../contributing/testing.md) for why
`unittest.mock.patch("time.sleep")` was rejected in favor of this (a real
port + fake beats patching a stdlib call every test file has to remember to
do consistently).

## The composition root (`bootstrap.py`)

`bootstrap.py` is the **only** module permitted to import from every layer
at once. Its actual wiring functions:

```python
def build_runner(*, cwd: Path, config: RunnerConfig, ...) -> RunnerContext:
    """Wires ClaudeAgentGateway, ClaudeCapacityProbe, SystemClock, AnyioSleeper,
    JsonlAuditLog, and ConsoleProgressReporter into an AutonomousRunner."""

def build_session_catalog() -> SdkSessionCatalog: ...
def build_doctor_environment() -> DoctorEnvironment: ...
```

`cli/` commands call into these functions and then drive the returned
objects — they never construct an
`infrastructure.agent.gateway.ClaudeAgentGateway` directly. This is the seam
that makes it possible to swap an adapter (say, a different `Notifier`
backend) without touching `application/` or `cli/` at all.
