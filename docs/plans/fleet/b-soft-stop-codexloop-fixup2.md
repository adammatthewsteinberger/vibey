# codexloop — Phase B fixup round 2: the wind-down interrupt's effect on the main loop is untested

You are continuing work on branch `chore/b-soft-stop` (PR #26). Round 1 got
`cli` to genuinely 100% and improved `application` from 98.89% to 99.21% —
progress, but not there. **One real gap remains, and it's on the flagship
functionality of this whole task**, not a nit:

```
$ uv run pytest -q -p no:cacheprovider --cov=codexloop.application --cov-report=term-missing --cov-fail-under=100
src/codexloop/application/runner.py   345    2    116    3    99%   245, 248, 547->544
FAIL Required test coverage of 100% not reached. Total coverage: 99.21%
```

Read `application/runner.py` around lines 230-250: inside the `run()`
method's main `case WaitUntil() | BackoffUntil():` branch, after
`interrupt = await self._sleep_interruptible(until)`, there are two
branches never exercised together with the surrounding loop:

```python
if interrupt == "stop":
    # Stop immediately - drain will handle on next poll
    pass
elif interrupt == "wind_down":
    # Wind-down requested - continue to next poll to process it
    pass
```

`tests/application/test_runner_wind_down_coverage.py` already tests
`_sleep_interruptible` **in isolation** (calling it directly and asserting
its return value) — that's real and fine, keep it. What's missing is a test
that drives the **actual `run()` loop** through a capacity wait
(`WaitUntil`/`BackoffUntil`) and verifies both interrupt outcomes are
actually reached from inside the loop, not just that the helper function
returns the right string in a vacuum. Look at how other `run()`-level tests
in this file (or `tests/application/test_waiting_runner.py`) construct a
scripted decision sequence / fake probe that yields a `WaitUntil` outcome,
and a fake control queue that delivers a `Stop` or `WindDownCommand` while
the loop is "waiting" — reuse that scaffolding rather than building new
plumbing.

The third gap, `547->544`, is a partial branch inside
`_sleep_interruptible`'s own control-polling loop (`for cmd in controls:`)
— it wants a case where the poll returns **more than one command in a
single batch**, and the first one isn't `Stop`/`WindDownCommand`, so the
loop actually continues to the next item rather than returning on the
first iteration. Add that case to whichever existing
`test_sleep_interruptible*` test is closest to it.

**Before you report done this time:** run the exact command above yourself
and confirm it prints `Required test coverage of 100% reached`, then run
all four layers, then the rest of the 7-gate sweep. Two previous rounds on
this exact task (the original attempt and round 1 of this fixup) both
claimed "all gates green" while genuinely failing — verify for real, don't
estimate, and don't trust your own memory of what you already checked
earlier in this session.

```bash
for L in domain application infrastructure cli; do
  uv run pytest -q --cov="codexloop.$L" --cov-fail-under=100
done
uv run ruff check . && uv run ruff format --check .
uv run mypy --strict src/codexloop
uv run lint-imports
uv run bandit -q -r src/codexloop
uv run pip-audit
```

Commit on the same branch and push.

Done: **CODEXLOOP_TASK_FULLY_COMPLETE** — only after you've personally seen
every gate's real output say pass/100%.
