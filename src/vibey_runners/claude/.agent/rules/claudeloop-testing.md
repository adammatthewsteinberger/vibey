# claudeloop-testing (Antigravity mirror of `.claude/skills/claudeloop-testing/SKILL.md`)


# claudeloop testing

## Layout

```
tests/domain/           # pure unit + Hypothesis property tests
tests/application/      # fakes for every port, zero real I/O
tests/infrastructure/   # adapters (incl. scripted test-agent unit tests)
tests/cli/
tests/live/             # opt-in free + paid live tiers
tests/live/system/      # marker: system — real FS/git/CLI + scripted agent
```

Run: `pytest` (skips `live` and `system`).
System: `pytest -m system`.
Live: `pytest -m live`.

## Coverage per-layer

**100%** on `domain/` and `application/` — zero I/O, zero excuse for
untested branches. No blanket `--cov-fail-under` in `pyproject.toml`. CI
enforces separately per layer.

## Fakes over mocks

Every port gets a real class implementing the `Protocol`. No
`unittest.mock.Mock` for ports. `mypy --strict` checks the shape.

## FakeClock / FakeSleeper

Never `time.sleep()` in tests. `FakeClock` + `FakeSleeper` simulate
multi-day waits in milliseconds. See `tests/application/fakes.py`.

## Hypothesis property tests — mandatory

Not a nice-to-have. Numeric/time-based logic gets `@given(...)` tests
asserting invariants across the entire valid input space. Caught real bugs
during development (e.g., exponential backoff overflow at `probe_count=29`).

See `docs/guides/live-testing.md`.
