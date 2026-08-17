# claudeloop — Phase C fixup: CLI layer is not actually at 100%

You are continuing work on branch `chore/c-guardrails` (already pushed as
PR #29 against `develop`, currently **red**). Your prior turn on this
branch reported "All quality gates passed (100% coverage on domain/
application/infrastructure, 99.92% on CLI)" and declared the task done.
**That report was wrong, and 99.92% would not have been passing anyway —
the CI gate is `--cov-fail-under=100`, not 99.92%.** Independent
verification just now found the real number is **95.04%**, and the failing
module is almost entirely uncovered, not just short by a fraction:

```
$ uv run pytest -q -p no:cacheprovider tests/cli --cov=claudeloop.cli --cov-branch --cov-report=term-missing --cov-fail-under=100
src/claudeloop/cli/time_parse.py    34     29     18      0    10%   27-43, 62-82
TOTAL                              1052     39    138      2    95%
FAIL Required test coverage of 100% not reached. Total coverage: 95.04%
```

`cli/time_parse.py` — presumably the `--wind-down-at` parser you added — is
90% uncovered. Add real tests for it: both accepted formats (absolute
ISO-8601 and relative `+duration`), invalid input, and whatever edge cases
lines 27-43 and 62-82 actually contain (read them, don't guess). Then
re-run the exact command above yourself and confirm it prints
`Required test coverage of 100% reached` — not an estimate, not "should be
close now," the actual tool output.

**Before you report done this time:** run the full 7-gate sweep for real,
capture each command's actual final line, and only include the literal
`CLAUDELOOP_TASK_FULLY_COMPLETE` marker if every one of them says 100%/pass.
If you're not sure a gate passed, it didn't — go verify, don't estimate.

```bash
rm -f .coverage*
for L in domain application infrastructure cli; do
  uv run pytest -q -p no:cacheprovider "tests/$L" --cov="claudeloop.$L" --cov-branch --cov-fail-under=100
done
uv run ruff check . && uv run ruff format --check .
uv run mypy --strict src/claudeloop
uv run lint-imports
uv run bandit -q -r src/claudeloop
uv run pip-audit
```

Commit the fix (amend or a new commit on the same branch, whichever is
cleaner given what's already there) and push to `chore/c-guardrails`. Don't
touch anything else in this task's original scope unless you find it's
also actually broken (verify, don't assume the rest is fine just because
it wasn't flagged here — this check only looked at coverage, not
correctness).

Done: **CLAUDELOOP_TASK_FULLY_COMPLETE** — only after you've personally
seen every gate's real output say pass/100%.
