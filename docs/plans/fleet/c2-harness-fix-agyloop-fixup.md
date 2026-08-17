# agyloop — Phase C2 fixup: the test suite doesn't even collect

You are continuing work on branch `chore/c2-harness-fix` (already pushed as
PR #25 against `develop`, currently **red**). Your prior turn reported "All
7 quality gates pass, commit created." **That report was false in the
worst possible way — the change you committed breaks `import` for the
whole package, so nothing can even run, let alone pass:**

```
$ uv run pytest -q -p no:cacheprovider tests/test_bootstrap.py
ImportError while importing test module 'tests/test_bootstrap.py'.
tests/test_bootstrap.py:9: in <module>
    from agyloop.bootstrap import build_runner, parse_gateway
src/agyloop/bootstrap.py:55: in <module>
    from agyloop.infrastructure.doctor_env import RealDoctorEnvironment, developer_api_key
src/agyloop/infrastructure/doctor_env.py:11: in <module>
    from agyloop.application.interfaces import AuthResolution, HarnessStatus
E   ImportError: cannot import name 'HarnessStatus' from 'agyloop.application.interfaces'
```

Every single test file that transitively imports `agyloop.bootstrap` fails
to collect (7 files failed collection in the sweep that found this — not
just `test_bootstrap.py`). Find wherever you referenced `HarnessStatus` in
`infrastructure/doctor_env.py` (part of your Bug-1 diagnostics work) and
either define it properly in `agyloop.application.interfaces` and export it
from that package's `__init__.py` (check how the sibling `AuthResolution`
on the same import line is defined and exported, and mirror that exactly),
or remove the reference if it turns out to be unnecessary. This is not a
coverage shortfall, it's a broken commit — first priority above everything
else.

**After fixing the import, run the actual test suite and confirm it
collects and passes, then check coverage for real** — you have not yet
verified either of these, since collection failed before either could be
measured:

```bash
rm -f .coverage*
for L in domain application infrastructure cli; do
  uv run pytest -q -p no:cacheprovider tests --cov="agyloop.$L" --cov-fail-under=100
done
uv run ruff check . && uv run ruff format --check .
uv run mypy --strict src/agyloop
uv run lint-imports
uv run bandit -q -r src/agyloop
uv run pip-audit
```

Also re-read the original task
(`docs/plans/fleet/c2-harness-fix-agyloop.md`) — both bugs it describes
(the SDK harness startup failure, and the CLI-gateway `--scoped` posture
silently auto-denying tool calls while reporting false success) are real
and still need fixing if your prior turn's fix was incomplete. Verify your
fix for Bug 2 actually works by reproducing the original failure mode
(a headless `--gateway cli --scoped` run that needs to execute a command)
and confirming it now either succeeds for real or fails loudly — not
silently succeeds having done nothing, which was the original bug.

**Before you report done this time:** every gate above must show its
actual real output, seen by you, not estimated. Given what just happened —
a previous "all gates pass" claim on this exact branch was false because
the package didn't even import — treat your own confidence as unreliable
here and re-verify everything from scratch rather than trusting partial
memory of what you already checked.

Commit the fix on the same branch and push.

Done: **AGYLOOP_TASK_FULLY_COMPLETE** — only after you've personally seen
every gate's real output say pass/100%, starting with confirming the test
suite collects at all.
