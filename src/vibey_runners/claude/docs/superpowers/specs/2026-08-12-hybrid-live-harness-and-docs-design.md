# Hybrid live harness + FOSS documentation deep-scan

**Date:** 2026-08-12
**Status:** Approved design (pending user review of this written spec)
**Repo:** claudeloop

## Problem

The control-plane / ops layer (stop, prompt inject, logs, status, runs,
savepoints, unwind, watch, state bus, 50MiB SDK buffer) is implemented and
covered by unit/application/infrastructure tests with fakes. That is not
enough to prove:

1. Real filesystem / git / CLI wiring works end-to-end for every happy path
   and major edge case.
2. Free and paid live tiers still reflect the shipped command surface.
3. Documentation across GitHub, github.io, Unix/`--help` man page, and
   PyPI / TestPyPI is complete and current for a developer with zero prior
   knowledge.

## Goals

1. **Hybrid live harness (Approach 1)** with three layers: system live
   (deterministic, no tokens), free live (no tokens), paid smoke (few real
   turns).
2. **Both** driving styles for system live: exhaustive **in-process** matrix
   (real adapters + scripted agent) **and** thin **subprocess** smoke
   (real `claudeloop` CLI + env-gated test agent).
3. After the harness is green: an **exhaustive documentation deep-scan** so
   every FOSS surface is idiot-proof and current.

## Non-goals

- Changing production Claude agent behavior except for a **test-only**
  bootstrap gate.
- Exhaustive paid coverage of every edge (paid stays smoke).
- Publishing releases to PyPI / TestPyPI (docs must be release-ready;
  publishing is a separate release task).
- Replacing existing domain/application unit tests or lowering coverage
  gates.

## Decisions already locked

| Decision | Choice |
|---|---|
| Overall approach | Hybrid A (system + free + paid) |
| System agent injection | Both: in-process + subprocess with env-gated test agent |
| Organization | Approach 1 — layered markers + production-shaped test agent |
| Docs timing | Milestone B after harness (Milestone A) is green |

---

## Milestone A — Hybrid live harness

### Layout

```
tests/live/
  conftest.py                 # markers, sandbox_repo, paid skip, shared helpers
  test_free_tier.py           # extended free checks
  test_paid_tier.py           # existing smoke + one mid-run ops path
  system/
    conftest.py               # composition helpers, script loaders
    test_matrix_inprocess.py  # exhaustive happy + edge matrix
    test_subprocess_smoke.py  # thin real-CLI smoke via test agent
  fixtures/agent_scripts/     # JSON turn scripts for subprocess / shared cases
```

### Markers and invocation

| Layer | Markers | Invocation | Tokens |
|---|---|---|---|
| Default unit/integration | (none / excluded) | `pytest` | no |
| System live | `system` | `pytest -m system` | no |
| Free live | `live` (not `paid`) | `pytest -m live` | no |
| Paid smoke | `live` and `paid` | `pytest -m "live and paid" --run-paid-live` | yes |

Default `addopts` in `pyproject.toml` must remain safe:

```text
-m "not live and not system"
```

so bare `pytest` and CI never run system or live suites by accident.

### Test-only scripted agent gate

**Environment contract (both required for subprocess path):**

- `CLAUDELOOP_ALLOW_TEST_AGENT=1`
- `CLAUDELOOP_TEST_AGENT_SCRIPT=/absolute/or/relative/path.json`

**Bootstrap behavior (`bootstrap.build_runner`):**

1. If the script path env is set **without** the allow flag → fail loudly
   (raise / exit with clear error). Never silently ignore.
2. If both are set → wire a scripted `AgentGateway` (+ matching capacity
   probe as needed) that replays the JSON script instead of
   `ClaudeAgentGateway`.
3. Otherwise → always the real Claude adapters (production default).

**Constraints:**

- Gate lives only in the composition root (`bootstrap.py` / a tiny helper
  it calls). Domain and application stay unaware of “test mode.”
- Documented as **test-only**, never as a user-facing feature in guides
  that teach operators how to run claudeloop day-to-day.
- Script format: ordered list of turns (signals, verdict, output_text,
  session_id, cost_usd) plus optional probe script — aligned with existing
  `FakeAgentGateway` / `ScriptedTurn` shapes so in-process and subprocess
  share semantics.

### In-process matrix (exhaustive)

Compose a runner using **real** infrastructure adapters:

- `RunDirectory` / run control inbox
- `JsonlRunEventSink` / `JsonlAuditLog`
- `GitSavePointStore`
- `FileStateBus` / `FileRunStateStore` / `FileSessionLock`
- recursive redaction on events

…with **scripted** agent + probe + `FakeClock` / `FakeSleeper` (or real
clock only where wall time is irrelevant).

**Happy paths (minimum):**

- Complete in one turn; multi-turn continue then done
- Save points created after turns; listed via use case / store
- Status + bus publications on phase changes
- Events written and redacted; logs readable
- Resume-shaped continuation prompt path (as applicable without Claude)

**Control paths (minimum):**

- Soft stop → terminal stopped (exit semantics 130 at CLI), `stop-summary.md`
- `prompt --now` replaces next continue prompt
- `prompt --at-break` applies only after a Continue verdict
- Stop during capacity wait interrupts sleep

**Edge cases (minimum):**

- Unwind refused while run still active
- Unwind `--to N` with backup ref after stop
- Stop outranks queued prompts
- Turn and dollar budget exhaustion
- Authentication failure is terminal (never retried)
- Credits exhausted vs window exhausted (wait policy distinction)
- Capacity rejection outranks completion claim on same turn
- Missing / unknown run id for ops commands
- Session lock contention / second acquire fails cleanly
- `--max-buffer-size` / config flows into agent options (assert 50MiB default
  and override)
- Secret-shaped keys / credential substrings redacted in events

### Subprocess smoke (thin)

Spawn the real `claudeloop` console script under a sandbox git repo with
the test-agent env set. Cover:

- `run` → complete with scripted done
- Concurrent second process: `stop`, `prompt`, `logs`, `status`, `runs`,
  `savepoints`
- After stop: `unwind --to N` succeeds; while “active” script still running,
  unwind refuses
- Root `--help` / man lists ops commands

### Free tier extensions

Extend `tests/live/test_free_tier.py` (no tokens):

- Help / man page lists all ops commands
- `run --help` documents `--max-buffer-size`
- Existing doctor / sessions / installed-wheel checks remain

### Paid smoke extensions

Keep existing cheap-model caps. Add **one** mid-run ops path against real
Claude:

- Start trivial plan in sandbox
- From a second process: `status` and/or `logs`
- Soft-stop **or** prompt inject
- Assert `.claudeloop/runs/<id>/` artifacts exist (`status.json`,
  `events.jsonl`, and stop-summary if stop was used)

Still requires `--run-paid-live`.

### Acceptance (Milestone A)

- `pytest` (default markers) green
- `pytest -m system` green locally
- `pytest -m live` (free) green in an environment with `claude` available
- Paid path documented; only runs with `--run-paid-live`
- Test-agent gate cannot activate without both env vars; fails loud if
  misconfigured
- `docs/guides/live-testing.md` and `docs/contributing/testing.md` describe
  the three layers and markers

---

## Milestone B — Documentation deep-scan

Runs **after** Milestone A is green.

### Surfaces

| Surface | Source of truth | Requirement |
|---|---|---|
| PyPI / TestPyPI | root `README.md` | Absolute github.io + GitHub URLs only; install + quickstart + ops overview |
| GitHub landing | same `README.md` | Same |
| Docs site | `docs/**` + `mkdocs.yml` | Full guides / reference / architecture; `mkdocs build --strict` clean |
| In-CLI man | `cli/man_page.py` | Exhaustive man(1)-style: commands, options, FILES, ENVIRONMENT, EXIT STATUS, EXAMPLES, SEE ALSO |
| Contributor | `CONTRIBUTING.md`, `docs/contributing/*`, skills | How to run system / free / paid harnesses |
| Security | `SECURITY.md` | Run-dir sensitivity, redaction, test-agent is not a user feature |

### Deep-scan checklist

1. Grep for stale command trees, missing ops commands, outdated Roadmap
   admonitions, missing buffer / env documentation.
2. Rewrite `docs/reference/cli.md` to match the real Typer tree (ops layer
   included).
3. Expand `cli/man_page.py` to idiot-proof depth (per-command synopsis,
   FILES under `.claudeloop/runs/<id>/`, ENVIRONMENT including production
   config vars; test-agent vars only in contributor/testing docs, not as
   recommended user knobs).
4. Update autonomous-runs, live-testing, getting-started, configuration,
   ports-and-adapters, testing, README, CLAUDE.md cross-links as needed.
5. Add or fold an operator mid-run control guide; document system-live
   harness how-to in live-testing.
6. Wire every new/updated page into `mkdocs.yml` nav; strict build passes.
7. Touch `claudeloop-testing` skill (and docs skill if needed) for new
   markers / philosophy.
8. Confirm cold-reader path: install → doctor → run → stop/prompt/logs/unwind
   works from man page **or** site alone.

### Acceptance (Milestone B)

- No shipped ops/buffer feature left behind a Roadmap admonition
- Man page and CLI reference list every public command and major flag
- README works on GitHub and as PyPI / TestPyPI long description (absolute
  links)
- `mkdocs build --strict` passes
- Live-testing guide documents system / free / paid accurately

---

## Architecture notes

- **Onion stays intact:** test agent selection is composition-root only.
- **Fakes over mocks:** in-process matrix reuses / extends
  `tests/application/fakes.py` patterns; real adapters for FS/git/control.
- **No real sleeps** in the in-process matrix for multi-day wait edges —
  use `FakeClock` / `FakeSleeper`.
- **Isolation:** every live/system test uses a fresh temp git sandbox, never
  a real project directory.

## Delivery order

1. Implement Milestone A (gate → in-process matrix → subprocess smoke →
   free/paid extensions → testing docs for markers).
2. Verify acceptance for A.
3. Implement Milestone B (deep-scan + rewrite).
4. Verify acceptance for B.

## Open implementation details (resolved preferences)

These are fixed by this spec (not left to invent later):

- Marker name: `system` (not `e2e` or `harness`).
- Suite location: under `tests/live/system/` (not a new top-level
  `tests/e2e/`).
- Subprocess gate: both allow flag and script path required.
- Docs: second milestone after harness green, not interleaved in the same
  “done” definition as A.
)
