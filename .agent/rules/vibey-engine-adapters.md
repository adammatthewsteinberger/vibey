# vibey-engine-adapters (Antigravity mirror of `.claude/skills/vibey-engine-adapters/SKILL.md`)

description: How vibey drives claudeloop, codexloop, cursorloop, and agyloop — the engine adapter pattern, argv building, and the conformance suite.
alwaysApply: false
> **Cursor rule mirror** of `.claude/skills/vibey-engine-adapters/SKILL.md`. When this guidance changes, update Claude, Cursor, Codex, and Antigravity in the same PR.

# vibey engine adapters

Vibey orchestrates four autonomous session runners: `claudeloop`, `codexloop`,
`cursorloop`, `agyloop`. Each has its own CLI surface, effort vocabulary,
state directory, and done marker. Vibey abstracts these differences via
`EngineAdapter` (a Protocol in `application/ports.py`) and concrete
implementations in `infrastructure/engines/`.

## The adapter pattern

Every engine adapter implements:
- `build_argv(spec: RunSpec) -> tuple[str, ...]` — constructs the command line
- `classify_capacity(error: dict) -> CapacityState` — maps vendor errors to
  vibey's capacity ADT
- `tail_run_dir(run_dir: Path) -> AsyncIterator[EngineEvent]` — reads events
  from the engine's state directory
- `doctor() -> PreflightResult` — checks installation, auth, and version

See `application/ports.py::EngineAdapter` and
`infrastructure/engines/scripted.py::ScriptedEngine` (the fake runner used in
tests).

## Engine descriptors

`infrastructure/engines/descriptors.py` defines `CLAUDELOOP`, `CODEXLOOP`,
`CURSORLOOP`, `AGYLOOP` — one `EngineDescriptor` per engine.

Each descriptor declares:
- `binary` — the executable name (e.g., `"claudeloop"`)
- `state_dir` — where runs are stored (e.g., `".claudeloop/"`)
- `done_marker` — the text signaling completion (e.g., `"CLAUDELOOP_TASK_FULLY_COMPLETE"`)
- `capabilities` — which features it supports (`savepoints`, `unwind`, etc.)
- `effort_projection` — how vibey's 5-level ladder (`TRIVIAL, LOW, STANDARD, HIGH, MAX`)
  maps to the engine's native flags

**Effort projection example:**

```python
effort_projection={
    Effort.TRIVIAL: EngineInvocation(argv=("--preset", "low", "--effort", "low"), achieved=Effort.TRIVIAL),
    Effort.LOW: EngineInvocation(argv=("--preset", "standard", "--effort", "low"), achieved=Effort.LOW),
    Effort.STANDARD: EngineInvocation(argv=("--preset", "standard", "--effort", "standard"), achieved=Effort.STANDARD),
    Effort.HIGH: EngineInvocation(argv=("--preset", "high", "--effort", "high"), achieved=Effort.HIGH),
    Effort.MAX: EngineInvocation(argv=("--preset", "high", "--effort", "max"), achieved=Effort.MAX),
}
```

If an engine **saturates** (e.g., codexloop has no `MAX` tier), the descriptor
sets `achieved` to the highest tier it can actually deliver. The rotator
applies a `fidelity_penalty` to engines that saturate below the requested
effort.

See ADR-0006 (normalized effort ladder).

## argv building

`infrastructure/engines/argv.py::build_argv()` takes a `RunSpec` (the work to
be done) and an `EngineDescriptor`, and produces the command line:

```python
RunSpec(
    brief="Fix the bug in payment.py",
    effort=Effort.HIGH,
    run_id=UUID("..."),
    worktree=Path("/vibey/worktrees/c3-item-042"),
    isolation=IsolationLevel.CONTAINER,
)
```

→

```bash
claudeloop run \
  --prompt "Fix the bug in payment.py" \
  --preset high \
  --effort high \
  --run-id "..." \
  --cwd "/vibey/worktrees/c3-item-042" \
  --permission-mode container
```

20 golden files under `tests/infrastructure/engines/golden/` (4 engines × 5
efforts) capture the expected argv for each combination.

## Capacity classification

`infrastructure/engines/classify.py::classify_capacity()` maps vendor-specific
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

`application/conformance.py::run_conformance()` asserts, per engine:
- The state directory exists where the descriptor says.
- `run --help` exposes the flags the descriptor claims.
- A trivial scripted plan produces a run directory with `meta.json`,
  `events.jsonl`, and a snapshot at the documented paths.
- Capacity classification maps to vibey's ADT.
- The done marker matches.

A failing conformance check marks that engine **ineligible** rather than
letting it fail mid-cycle.

```bash
vibey doctor --conformance
```

See ADR-0001 (orchestrate, do not reimplement).

## When to read this skill

Before:
- Adding a new engine.
- Changing effort mappings.
- Debugging why rotation is skipping an engine.
- Updating capacity classification patterns after a vendor API change.
