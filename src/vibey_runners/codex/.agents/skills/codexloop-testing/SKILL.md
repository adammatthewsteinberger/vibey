---
name: codexloop-testing
description: Fakes over mocks, FakeClock/FakeSleeper, Hypothesis, pytest markers, per-layer 100% coverage. Consult before adding tests or mocks.
allowed-tools: Read Grep Glob Bash(pytest *)
---

# codexloop testing

```
tests/domain/            # pure unit + Hypothesis
tests/application/       # fakes for every port (application/interfaces/)
tests/infrastructure/    # adapters
tests/shim/              # fake_codex.py + fake_appserver.py — executable fakes
tests/live/              # marker: live — real OpenAI account, opt-in
```

```bash
pytest                 # skips live (default -m "not live and not system")
pytest -m system       # real FS/git + scripted agent
pytest -m live         # needs OPENAI_API_KEY
```

- **Fakes over mocks.** Implement the `Protocol`; `mypy --strict` checks it.
- **Executable shims.** `fake_codex.py` and `fake_appserver.py` in
  `tests/shim/` are genuine executables driven by env vars — the only such
  fakes in the fleet. They let you script exact output sequences without
  touching the OpenAI SDK.
- **No `time.sleep` in tests.** `FakeClock` / `FakeSleeper`.
- Hypothesis for numeric / time-based invariants.
- `# pragma: no cover` needs a reason.
- **100% branch coverage per layer**, enforced by gate:
  ```bash
  pytest -q --cov=codexloop.domain --cov-fail-under=100
  pytest -q --cov=codexloop.application --cov-fail-under=100
  pytest -q --cov=codexloop.infrastructure --cov-fail-under=100
  pytest -q --cov=codexloop.cli --cov-fail-under=100
  ```
