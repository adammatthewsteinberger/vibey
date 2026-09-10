# Testing philosophy and layout

## Layout

```
tests/
├── domain/           # pure unit + Hypothesis; mirrors src/claudeloop/domain/
├── application/      # fakes for every port (fakes.py), zero real I/O
├── infrastructure/   # adapters (incl. scripted test agent unit tests)
├── cli/              # Typer / man-page / api surface
└── live/             # opt-in: system / free / paid (see guides/live-testing.md)
    └── system/       # marker: system — real FS/git/CLI + scripted agent
```

Run everything (skips live + system by default):

```bash
pytest
```

System harness (no tokens):

```bash
pytest -m system
```

Free / paid live tiers: see [`../guides/live-testing.md`](../guides/live-testing.md).

Run one module, with verbose failures:

```bash
pytest tests/domain/test_classify.py -v
```

Coverage report (already wired into `addopts` in `pyproject.toml`):

```bash
pytest --cov-report=term-missing
```
## Coverage gates are per-layer, not global

There is deliberately **no** single `--cov-fail-under` in `pyproject.toml`.
A single global number would either be trivially satisfied while the one
pure, fully-controllable layer regresses, or block every commit before
`application`/`infrastructure`/`cli` exist at all. Instead, CI runs coverage
separately per layer:

- `domain/` and `application/`: **100%** required. These
  layers have no I/O and no third-party dependencies — there is no excuse
  for an untested branch, and an untested branch here is the most
  consequential kind of bug, since this is the code deciding whether an
  unattended, potentially multi-day run keeps going, waits, or gives up.
- `infrastructure/` and `cli/`: a lower floor, since some paths (signal
  handlers, real SDK error translation) are inherently harder to exercise
  without a live process. See the `# pragma: no cover` policy below.

## Fakes over mocks

Every port in `application/ports.py` gets a **fake**
implementation in test code — a real class satisfying the same `Protocol`,
not a `unittest.mock.Mock` with stubbed return values. Two concrete reasons:

1. **`mypy --strict` checks a fake against the port's `Protocol` shape.** A
   `Mock` has no such check — a port method rename silently breaks nothing
   in test code until runtime, or worse, not at all.
2. **A fake can carry real (if simplified) behavior**, which is what makes
   `FakeClock`/`FakeSleeper` possible (see below) — a `Mock` can only record
   calls and return canned values, it can't coordinate state the way a real
   collaborator would.

## `FakeClock` / `FakeSleeper` — testing a multi-day wait in microseconds

`domain/waiting.py`'s policy is designed entirely around instants
(`next_probe_instant() -> datetime`), never durations, specifically so
application-layer tests never call `time.sleep()` for real. The
pattern:

```python
clock = FakeClock(start=NOW)
sleeper = FakeSleeper(clock)  # sleep_until(instant) jumps `clock` straight there

runner = AutonomousRunner(agent_gateway=fake_gateway, clock=clock, sleeper=sleeper, ...)
result = runner.run(plan)

assert result.success
assert sleeper.wait_log == [...]  # exactly which instants it was asked to wait until
```

This is what lets a test simulate a **seven-day rate-limit wait**, or the
**credit-top-up scenario** (several failed probes, then success — already
covered at the domain layer by
`test_credit_topup_sequence_resumes_after_several_failed_probes` in
`tests/domain/test_loop.py`), in a test that completes in milliseconds of
real wall-clock time. `unittest.mock.patch("time.sleep")` was considered and
rejected: a real port + fake pair is one thing to reason about, while
patching a stdlib call is something every test file touching timing would
need to remember to do, consistently, forever.

## Property tests, not just examples

Anything with a numeric or time-based invariant gets a Hypothesis property
test, not just hand-picked examples. This isn't a style preference — it
already found a real bug during development:
`test_property_credits_probe_never_in_the_past_and_never_exceeds_ceiling`
generated a `probe_count` of 29 with a backoff factor of 3.0 and triggered
`OverflowError: days=1588666142; must have magnitude <= 999999999` — an
unclamped `interval * factor**probe_count` overflowing `timedelta`'s maximum
magnitude, at a probe count well within what a real multi-day wait could
reach. No example-based test at any specific, hand-picked `probe_count`
would have caught this before it happened in production. See
[ADR 0004](../architecture/decisions/0004-adaptive-waiting-with-probes-not-sleep.md#consequences)
for the fix.

When adding a numeric config field (an interval, a ceiling, a factor, a
budget), ask: what invariant must hold for *every* valid input, not just the
ones I thought to write down? Then write that as a `@given(...)` test.

## Golden fixtures from real transcripts

A real Claude Code transcript captured during development contains a
genuine `credits_required` 429 rejection. Prefer capturing real observed
payloads like this as fixtures over inventing synthetic ones — the shape of
a real SDK error is rarely exactly what you'd guess it looks like.

## `# pragma: no cover` policy

Reserved for genuinely unreachable branches — and every use must carry an
inline comment explaining *why* it's unreachable, not just that it is. Two
real examples already in the codebase:

```python
if candidate < now:  # pragma: no cover — unreachable: all config intervals are
    candidate = now  # validated positive in __post_init__, so every branch above
    # already yields candidate >= now. Kept as a defensive invariant guard.
```

```python
# Precondition, not a security gate: CompletionVerdict is the closed union
# {Done, Blocked, Continue} and both other members are handled above, so this
# is exhaustive by construction — asserted here to fail loudly if a future
# variant is added to the union without a matching branch here.
assert isinstance(verdict, Continue)  # nosec B101
```

A `# pragma: no cover` with no reasoning attached will be rejected in
review — the point of the annotation is to make the *reason* for the gap
visible, not to make the coverage number look better.
