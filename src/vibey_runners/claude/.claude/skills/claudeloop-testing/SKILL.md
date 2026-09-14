---
name: claudeloop-testing
description: Explains claudeloop's testing philosophy and pytest layout — fakes over mocks for every port, FakeClock/FakeSleeper for simulating multi-day waits without real sleeping, mandatory Hypothesis property tests for numeric/time-based invariants, per-layer coverage gates (100% for domain and application), and the documented # pragma no cover policy. Use this whenever writing or modifying any test under tests/, whenever the user asks how to test something in this codebase, mentions coverage, Hypothesis, property-based testing, or asks why a coverage gate failed. Make sure to consult this before adding a mock (this codebase uses fakes implementing real Protocols instead), before adding a numeric or time-based config field without a property test, and before adding a # pragma no cover without a stated reason — all three are enforced review expectations here, not suggestions.
allowed-tools: Read Grep Glob Bash(pytest *)
---

# claudeloop testing philosophy

## Layout

```
tests/domain/           # pure unit + Hypothesis property tests
tests/application/      # fakes for every port (fakes.py), zero real I/O
tests/infrastructure/   # adapters (incl. scripted test-agent unit tests)
tests/cli/
tests/live/             # opt-in free + paid live tiers
tests/live/system/      # marker: system — real FS/git/CLI + scripted agent
```

Run: `pytest` (skips `live` and `system` via addopts).
System harness: `pytest -m system`.
Live free: `pytest -m live`. Paid: `pytest -m "live and paid" --run-paid-live`.
See `docs/guides/live-testing.md`.

Coverage: `pytest --cov-report=term-missing` (already the default via
`addopts` in `pyproject.toml`).

Test-only agent gate (composition root only; not a user feature):
`CLAUDELOOP_ALLOW_TEST_AGENT=1` + `CLAUDELOOP_TEST_AGENT_SCRIPT=<json>`.

## Coverage is per-layer, not global — and why

There is deliberately **no** blanket `--cov-fail-under` in `pyproject.toml`.
CI enforces coverage separately per layer: **100%** on `domain/` and
`application/` (zero I/O, zero third-party deps — no excuse for an untested
branch, and this is the code deciding whether an unattended multi-day run
keeps going, waits, or gives up), a lower floor on `infrastructure/`/`cli/`.
When adding domain code, run coverage scoped to it and treat anything less
than 100% as a defect, not a number to negotiate down.

## Fakes, never `unittest.mock.Mock`, for ports

Every port in `application/ports.py` gets a real class
implementing the same `Protocol` — checked by `mypy --strict` against the
port shape. A `Mock` has no such check; a port method rename silently
breaks nothing in test code, possibly not even at runtime. If you're
tempted to `from unittest.mock import Mock` for a port, write a small
`FakeXxx` class instead.

## `FakeClock` / `FakeSleeper` — never sleep for real in a test

`domain/waiting.py` is designed entirely around instants
(`next_probe_instant() -> datetime`), never durations, specifically so
tests never call real `time.sleep()`. Pattern (tests/application/fakes.py):

```python
clock = FakeClock(start=NOW)
sleeper = FakeSleeper(clock)  # sleep_until(instant) jumps clock straight there, no real delay
```

This is what lets a test simulate a **seven-day rate-limit wait** or the
**credit-top-up scenario** (already covered at the domain layer —
`test_credit_topup_sequence_resumes_after_several_failed_probes` in
`tests/domain/test_loop.py`) in milliseconds. Do not use
`unittest.mock.patch("time.sleep")` — a real fake port is one thing to
reason about; a patched stdlib call is something every test touching timing
has to remember to apply consistently.

## Hypothesis property tests are mandatory for numeric/time-based logic

Not a nice-to-have. `test_property_credits_probe_never_in_the_past_and_never_exceeds_ceiling`
in `tests/domain/test_waiting.py` caught a real production-shaped bug during
development: `probe_count=29, factor=3.0` overflowed `timedelta`'s max
magnitude via unclamped exponential backoff — an example-based test at any
hand-picked `probe_count` would never have found this. When you add a
numeric config field (an interval, ceiling, factor, budget cap), write a
`@given(...)` test asserting the invariant holds across the *entire* valid
input space, not a handful of examples. Two existing property tests to use
as templates: the one above, and
`test_property_never_proposes_instant_beyond_max_wait`.

## Golden fixtures from real transcripts

Prefer capturing real observed SDK/API payloads as test fixtures over
inventing synthetic ones — a real `credits_required` 429 rejection from a
development transcript is already used this way; the shape of a real error
payload is rarely exactly what you'd guess.

## `# pragma: no cover` — reserved, and always justified inline

Every use must carry a comment explaining *why* the branch is unreachable,
not just that it is. Two real examples already in the codebase:

```python
if candidate < now:  # pragma: no cover — unreachable: all config intervals are
    candidate = now  # validated positive in __post_init__, so every branch above
    # already yields candidate >= now. Kept as a defensive invariant guard.
```

A bare `# pragma: no cover` with no reasoning will be rejected in review —
grep the codebase for the pattern above before adding a new one, and match
that level of specificity.

## Full reference

`docs/contributing/testing.md`.
