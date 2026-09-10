# Live testing against a real Claude account (and the system harness)

`tests/live/` exercises real surfaces — not fakes in the default unit suite.
It is **opt-in and tiered** so it never runs by accident.

## Three tiers

| Tier | Markers | Tokens? | Invocation |
|---|---|---|---|
| **System** | `system` | No | `pytest -m system` |
| **Free live** | `live` (not `paid`) | No | `pytest -m live` |
| **Paid smoke** | `live` and `paid` | Yes | `pytest -m "live and paid" --run-paid-live` |

Default `addopts` is `-m "not live and not system"`, so bare `pytest` and CI
skip all three.

## System tier (deterministic, no tokens)

Real filesystem / git / CLI wiring with a **test-only scripted agent**:

```bash
pytest -m system
```

Layout:

- `tests/live/system/test_matrix_inprocess.py` — exhaustive happy paths and
  edges using real `RunDirectory`, `FileRunControl`, `GitSavePointStore`,
  events/bus/audit/redaction, plus a scripted agent and `FakeClock`/`FakeSleeper`
- `tests/live/system/test_subprocess_smoke.py` — thin real-CLI smoke via the
  env-gated test agent
- `tests/live/fixtures/agent_scripts/*.json` — turn/probe scripts

### Test-only agent gate (not a user feature)

Both environment variables are required:

```bash
export CLAUDELOOP_ALLOW_TEST_AGENT=1
export CLAUDELOOP_TEST_AGENT_SCRIPT=/absolute/path/to/script.json
```

If the script path is set without the allow flag, bootstrap fails loudly.
Never document this gate as something operators should use for production
runs — it exists so system tests can prove the control plane without spending
tokens.

## Free tier — no token spend

```bash
pytest -m live tests/live/test_free_tier.py
```

Covers: wheel install + console script version/help (including ops commands),
`run --help` documenting `--max-buffer-size`, `doctor`, and read-only
`sessions`.

## Paid tier — spends real tokens

```bash
pytest -m "live and paid" --run-paid-live tests/live/
```

A plain `pytest -m live` skips every paid test. Paid tests pin a cheap model,
tight `--max-turns` / `--max-dollars`, and a sandbox git repo. Includes
run/resume/never-block smokes plus one mid-run `status`/`logs`/`stop` path
against a real Claude session.

## Isolation

Every live/system test that touches a session or worktree uses a fresh
temporary git repository (`sandbox_repo` / `git_sandbox`) — never a real
project directory.
