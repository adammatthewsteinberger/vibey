# codexloop — Phase B fixup: application and CLI layers are not actually at 100%

You are continuing work on branch `chore/b-soft-stop` (already pushed as
PR #26 against `develop`, currently **red**). Your prior turn on this
branch reported "All 889 tests pass, all gates green (ruff, mypy, bandit,
lint-imports)" and declared the task done. **That report did not check
coverage, and coverage is part of the gate.** Independent verification just
now found two of the four per-layer floors fail:

```
$ uv run pytest -q -p no:cacheprovider --cov=codexloop.application --cov-report=term-missing --cov-fail-under=100
src/codexloop/application/usecases/preflight.py       5 stmts, some missed
src/codexloop/application/usecases/resume_thread.py   6 stmts, some missed
src/codexloop/application/usecases/run_control.py     7 stmts, some missed
src/codexloop/application/usecases/run_plan.py        6 stmts, some missed
TOTAL   511 stmts, 3 missed, 118 branch, 4 partial
FAIL Required test coverage of 100% not reached. Total coverage: 98.89%

$ uv run pytest -q -p no:cacheprovider --cov=codexloop.cli --cov-report=term-missing --cov-fail-under=100
src/codexloop/cli/commands/wind_down_cmd.py    15    9    2    0    35%   26-34
TOTAL   449 stmts, 9 missed, 66 branch
FAIL Required test coverage of 100% not reached. Total coverage: 97.86%
```

`cli/commands/wind_down_cmd.py` (your new wind-down CLI command) is 65%
uncovered — lines 26-34, read them and add real tests for whatever branches
they cover. Re-run the term-missing command above to find exactly which
lines in the four `application/usecases/*.py` files are uncovered (the
output above only shows the file list, not the exact missing line numbers —
get those yourself) and add tests for those too.

**Before you report done this time:** run the full 7-gate sweep for real,
capture each command's actual final line, and only include the literal
`CODEXLOOP_TASK_FULLY_COMPLETE` marker if every one of them genuinely says
100%/pass. "All tests pass" is not the same claim as "coverage is 100%" —
check both, separately, for real.

```bash
uv run pytest -q --cov=codexloop.domain --cov-fail-under=100
uv run pytest -q --cov=codexloop.application --cov-fail-under=100
uv run pytest -q --cov=codexloop.infrastructure --cov-fail-under=100
uv run pytest -q --cov=codexloop.cli --cov-fail-under=100
uv run ruff check . && uv run ruff format --check .
uv run mypy --strict src/codexloop
uv run lint-imports
uv run bandit -q -r src/codexloop
uv run pip-audit
```

Commit the fix on the same branch and push. Don't touch anything else in
this task's original scope unless you find it's also actually broken.

Done: **CODEXLOOP_TASK_FULLY_COMPLETE** — only after you've personally seen
every gate's real output say pass/100%.
