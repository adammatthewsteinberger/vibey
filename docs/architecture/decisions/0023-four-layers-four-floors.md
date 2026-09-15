# 0023 — Four layers, four floors: 100% branch coverage per layer, each its own gate

**Status:** accepted · **Date:** 2026-08-15 (recorded 2026-09-15)

## Context

The M0 scaffold gated `domain/` at 100% and the whole package at 90%. A single aggregate number hides where the missing 10% lives: the pure phase machine can be perfect while the queue's crash paths — the code that only runs when a worker dies mid-lease — go untested, and the aggregate still passes. In a system whose design *is* the failure paths (leases expire, workers are killed, engines reject on capacity), an untested branch is by construction one of those paths.

PR #3 (2026-08-15) brought `application/`, `infrastructure/` and `cli/` to 100% branch coverage and, rather than one gate at 100%, made four. PR #70 later unified the test run (one `pytest --cov` under xdist against a template database) and kept the four `coverage report` gates over the single data file.

## Decision

**Every architectural layer — `domain/`, `application/`, `infrastructure/`, `cli/` — carries a 100% *branch* coverage floor, enforced in CI as a separate gate per layer.** One test run produces the data; four `coverage report --include='src/vibey/<layer>/*' --fail-under=100` commands judge it.

- **Branch, not line.** A line is covered when any path through it runs; a branch is covered only when both outcomes run. The untested `else` is where the reaper, the capacity rejection and the replay guard live.
- **Per layer, not aggregate.** A layer that drops below the floor names itself in the failing gate; an aggregate names nothing.
- **Suppressions are part of the bar.** A `# pragma: no cover`, `noqa`, `nosec` or `type: ignore` without a written reason at the site is the bar moving in the dark (runbook 18's suppression census). The preferred answer to "this branch is hard to test" is to test it — PR #76 tested the `kopf.run` delegation and the missing-extra `ImportError` rather than pragma them.
- **`tui/` is outside the floor.** It is the one layer with no gate today. This is recorded here as an exemption rather than an oversight; lifting it is a change to this ADR.

## Consequences

**Good.** "Is the failure path tested?" is answered by the build, per layer, on every push. The floor has held through the worker, the operator, the deployment stage set and the absorption, and repeatedly found real bugs while being reached (PR #3 fixed rotation weights that had never matched ADR-0005; the `BrokenPipeError` branch that closed stderr).

**Bad.** Every new branch costs a test before it can merge, and a mechanical refactor of the tree is expensive precisely because it cannot lower the number (ADR-0016 accepts this cost explicitly). Test-suite time is the pressure valve: PR #70 bought parallelism rather than lowering the floor, and PR #117 moved the suite off the commit hook rather than shrinking it.

**Rule status.** Binds every future change, survives any rewrite, and is about how this project treats its own work: it passes ADR-0020's test and owes a sub-doctrine, not yet proposed; the parent doctrine and the wording are the operator's to ratify.

## Alternatives rejected

- **One aggregate floor at 90% or 95%.** The M0 state. Hides which layer is short and lets the crash paths be the missing fraction.
- **Line coverage at 100%.** Cheaper to reach and misses exactly the `else` branches this system is made of.
- **A ratchet (never lower than last run).** Allows a permanently sub-100% layer as long as it does not get worse; the failure paths stay untested forever.
- **Per-file floors.** Finer than a layer but noisier; the layer is the unit the onion contract already draws, so the gates and the import-linter contracts speak the same vocabulary.
