# 0030 — The live harness has two modes: faked by default, paid by explicit choice

**Status:** accepted · **Date:** 2026-08-17 (recorded 2026-09-15) · **Extends:** ADR-0001, ADR-0002

## Context

vibey's correctness is mostly about what happens at the edges of a subprocess it does not own: an engine's run directory shape, its event vocabulary, its verdict payload, its exit codes, how long its `doctor` takes. Unit tests with hand-written fakes had already shipped fabricated event maps for three of four engines (#32, #34) — the fakes encoded what we believed, not what the binaries did. At the other extreme, every real-engine test costs money and needs credentials, so a suite made only of those never runs.

Postgres is the one dependency this project refuses to fake at all: the queue's semantics *are* `FOR UPDATE SKIP LOCKED`, and a mock cannot have them.

## Decision

**`tests/live/` runs in two modes, chosen by marker, and only one of them runs by default.**

- **Faked mode** (`@pytest.mark.live`): `ScriptedEngine` — real run-directory shapes, real event files, real exit codes, no subprocess — parametrized over every engine descriptor so a descriptor cannot drift from the shape the adapter reads.
- **Paid mode** (`@pytest.mark.paid`): real engine binaries against real models through the production dispatch stack — rotation-selected engine, real worktree, real subprocess, ledger events recorded. `addopts = "-m 'not paid'"` deselects it everywhere unless asked for. Each paid test is scoped to one trivial LOW-effort item so the spend is bounded, and adding one is a human decision, not an agent's.
- **Scripted-binary conformance** sits between them: a real subprocess running a scripted stand-in, which is what found the `--run-id` and run-dir bugs no in-process fake could (#36).
- **`tests/contracts/`** proves every implementation of a port (Postgres and in-memory) satisfies the same contract, so a fake that passes is a fake that behaves.
- **Postgres is never mocked.** Integration tests run against a real instance (`VIBEY_TEST_DATABASE_URL`, a template database per worker under xdist).

## Consequences

**Good.** The default suite is free, offline and deterministic, and still exercises every engine's on-disk contract. The paid path exists and is run deliberately; its first run caught a 30-second preflight timeout that made every authenticated claudeloop report `auth_ok=False`, and a `success`/`complete` verdict mismatch that failed a finished item — neither visible to any fake.

**Bad.** Faked mode is only as honest as `ScriptedEngine`; a change to a real engine's output shape is caught only by the conformance recording or a paid run. Paid tests rot when nobody has credentials.

**Rule status.** "Paid is opt-in, never a default" is conduct about money and matches doctrine 8.a and 10.b; it passes ADR-0020's test in that clause and owes a sub-doctrine, not yet proposed. The harness layout is mechanism.

## Alternatives rejected

- **Mock the engines in-process only.** Produced the fabricated event maps.
- **Paid tests in the default run.** Never green without keys; a suite that needs money to pass is a suite that does not run.
- **A single 'live' mode switched by environment variable.** A silent switch is how a paid session runs on a laptop that had a key in its shell.
- **Mock Postgres for speed.** The queue's guarantees are the database's; PR #70 bought speed with a template database and xdist instead.
