# vibey — Phase E1: live engines, rotation, full worker, two-mode harness

You are working unattended in a disposable git worktree of `vibey`
(`~/git/vibey`), on branch `chore/e1-live-engines`. This is the single most
important slice of the whole fleet program: it's what turns vibey from "a
set of 100%-tested handlers nothing wires together" into something that
actually drives real `claudeloop`/`agyloop`/`codexloop`/`cursorloop`
processes end to end.

Read first, in order: `README.md`, `docs/plans/architecture-and-roadmap.md`,
`docs/plans/implementation-plan.md` (M5-M10 milestone table — this task
spans parts of M6, and is a prerequisite the plan didn't originally call
out by name), `docs/plans/domain-model.md`, `docs/plans/rotation-and-engines.md`,
`docs/plans/phase-protocols.md`, and the relevant ADRs in
`docs/architecture/decisions/` (0005 smooth-weighted-round-robin, 0007
rotate-at-boundaries, 0008 worktree-isolation). Ground rules from
`docs/plans/implementation-plan.md` are not optional: test-first, 100%
branch coverage on every layer (all four, not just domain+application —
that floor is already enforced in CI today), the 7-gate sweep, Conventional
Commits, real Postgres for anything touching `infrastructure/db/` (never
mocked — `VIBEY_TEST_DATABASE_URL` is already set up in this environment).

**Protected tests — do not modify these without flagging it loudly in your
final summary and stopping short of merging:** `tests/infrastructure/db/
test_chaos.py`, any `tests/domain/test_noloss*.py` / `test_briefing.py`
(the no-loss property suite), `tests/system/test_delivery_stage_set.py`.
If your work requires touching one of them, make the change, explain
precisely why in your summary, and do not claim
`VIBEY_TASK_FULLY_COMPLETE` — leave the PR for a human instead.

## Where things actually stand (measured, not from stale docs)

- Bootstrap (`bootstrap.py`) wires only DESIGN + VISUAL. Fourteen fully
  implemented, 100%-covered BUILD/REVIEW/DEPLOY handlers exist
  (`application/build_*.py`, `application/review_*.py`,
  `application/deploy_*.py`) but nothing outside tests ever constructs them.
- `domain/rotation.py::select()` — the actual nginx-style smooth-weighted
  round-robin selection logic — has **zero production callers**. Only
  `tests/domain/test_rotation.py` imports it.
- The only `EngineAdapter` implementation anywhere in `src/` is
  `infrastructure/engines/scripted.py::ScriptedEngine`, and its only
  production construction site is an unused helper. The DESIGN-only
  `infrastructure/engines/claudeloop_process.py::ClaudeLoopProcess` is a
  one-shot `communicate()` subprocess wrapper reachable only via
  `vibey work --provider claudeloop` — it is not an `EngineAdapter` (no
  `tail`/`stop`/`snapshot`) and only serves DESIGN.
- `infrastructure/engines/tailer.py::translate_event` does `EventKind(event.kind)`
  and raises `UnknownEventKind` on anything not in vibey's own 24-member
  vocabulary (`domain/ledger.py`). Real claudeloop/agyloop/codexloop/
  cursorloop `events.jsonl` files use an `event_type` field with dotted
  values (`chatter.assistant`, `sdk.message`, `RateLimitEvent`, ...) — none
  of them are `EventKind` members. It fails even earlier than that:
  `ScriptedEngine.tail` does `raw["kind"]`, and a real run line has no
  `"kind"` key at all, so it `KeyError`s before `translate_event` is ever
  reached.
- `vibey watch` renders a frozen one-shot snapshot — the CLI never passes a
  `state_fetcher` into `VibeyDashboardApp`, so the refresh timer never
  installs (`cli/main.py:383`, `tui/dashboard.py:273`).
- No `pytest -m live` marker exists (only `integration`, `slow`, `system`
  are declared). No `tests/live/`. Nothing in the whole test suite shells
  out to a real loop binary — every subprocess call in tests is
  monkeypatched.
- All four loop binaries (`claudeloop`, `agyloop`, `codexloop`, `cursorloop`)
  are installed on PATH as editable uv tools from their local `develop`
  checkouts under `~/git/`, so `shutil.which("claudeloop")` etc. will
  succeed in this environment. Only `claudeloop` and `agyloop` have live
  model credentials configured (`claude` is logged in;
  `GOOGLE_API_KEY`/`GEMINI_API_KEY` are set) — codexloop/cursorloop should
  be exercised in their **scripted/offline test-agent mode**
  (`CLAUDELOOP_ALLOW_TEST_AGENT=1`-style env gates — each loop has its own
  prefix, check `infrastructure/agent/scripted.py` in each repo for the
  exact variable names) until real credentials are available.

## Deliverables

### 1. Real event translation (`infrastructure/engines/loop_events.py`)

Build `LOOP_EVENT_MAP`: a per-engine mapping from the real dotted
`event_type` values each loop actually writes to `events.jsonl` to vibey's
`domain.ledger.EventKind` vocabulary. Get real event shapes by running each
installed binary in its **scripted/offline mode** against a trivial plan and
inspecting the resulting `events.jsonl` — don't guess field names. Capture
one representative run-dir per engine under
`tests/fixtures/rundirs/<engine>/` (small, hand-curated, not a raw dump) so
tests don't need a live process. Fix:
- `infrastructure/engines/tailer.py::translate_event` to go through
  `LOOP_EVENT_MAP` instead of a direct `EventKind(event.kind)` cast, and to
  degrade explicitly (a typed "unrecognized event, skip and log" path) for
  event types no engine version documents yet — a live run should never
  crash vibey just because a runner emitted something new.
- `infrastructure/engines/scripted.py::ScriptedEngine.tail` reads
  `raw["kind"]` — this needs to survive the real event shape too, or the
  new adapter (below) needs to bypass `ScriptedEngine.tail` entirely for
  real runs. Decide and document which; don't leave both code paths
  half-right.

### 2. One real engine adapter (`infrastructure/engines/loop_process_adapter.py`)

A single `LoopProcessAdapter(descriptor: EngineDescriptor)` implementing
`application/interfaces/engines.py`'s `EngineAdapter` protocol in full —
`preflight`, `start`, `tail` (a genuine stream, not `communicate()`),
`stop`, `snapshot` — parameterized over all four descriptors in
`infrastructure/engines/descriptors.py`, not four separate classes. Build
its argv via the existing `infrastructure/engines/argv.py::build_argv` +
descriptor data (already correct and golden-file tested — reuse it, don't
duplicate). Detect completion via `descriptor.done_marker` in the real
output stream (not the `_looks_structured()` JSON heuristic
`ClaudeLoopProcess` currently uses, which was always a placeholder).
Recognize exit code 75 (wind-down, once Phase B lands in each loop — until
then, treat a nonzero-but-not-crash exit conservatively) as a distinct
`WindDown` outcome, never `Failure`. Classify capacity states via
`infrastructure/engines/classify.py`, replacing its currently-synthesized
fixture payloads with real captured ones from your scripted-mode runs where
you can (documented honestly wherever you can't).

This adapter supersedes `ClaudeLoopProcess` for BUILD/REVIEW work; leave
`ClaudeLoopProcess` in place for DESIGN's existing narrower use unless you
find it's trivially subsumed — don't do a bigger refactor than this task
needs.

### 3. Rotation wiring (finally giving `domain/rotation.select()` a caller)

- `infrastructure/db/rotation_cursor_repository.py` — the `rotation_cursor`
  table already exists in migrations; write the repository over it.
- `application/engine_selector.py` — the **first production caller** of
  `domain/rotation.py::select()`. Feed it live `EngineHealthRecord`s (via a
  new `application/engine_health_service.py` over the existing
  `PostgresEngineHealthRepository`) and each descriptor's `Capability` set +
  `affinity_factor` (`domain/rotation.py:111-119`) — wiring this in gets
  §2.2 (engine specialization) essentially for free, since both primitives
  already exist and are 100% tested, just unused.
- `application/rotation_handoff.py` — on a wind-down, settle the work item
  as `Success` (never `Failure`, which would burn the escalation ladder and
  open a circuit on a perfectly healthy engine; never `Defer`, which would
  just re-run it on the same exhausted engine), build the no-loss handoff
  brief, and hand off to the next selected engine. Bound livelock: at most
  3 wind-downs per work item, then stop rotating and surface it as a
  human-gate ("needs attention", not a silent failure).

### 4. `bootstrap.py` — wire the rest of the app

Currently constructs only DESIGN+VISUAL adapters. Add: the 14 BUILD/REVIEW/
DEPLOY handlers, `WorktreeManager`, `IntegrationBranch`, `GateRunner`,
`SubprocessAutomatedReviewRunner`, `NotificationService` (wire the already-
correct, currently-unwired `infrastructure/notify/webhook.py` — it's
HMAC-signed and 100% covered, just never imported outside its own package —
plus `DesktopNotifier`), `PostgresJobReadyNotifier`, and the rotation
pieces from (3). Leave Azure adapter wiring behind an explicit opt-in flag
if you get to it, but it's lower priority than the rest of this list — do
not let it block the engine/rotation work.

New CLI surface in `cli/main.py`:
- `vibey worker [--engines claudeloop,agyloop,...] [--parallelism N]` — a
  long-running process: `LISTEN vibey_job_ready` via the existing
  `PostgresJobReadyNotifier` (already implemented, never called from
  production code today) instead of polling, dispatching across every
  phase's `WorkerLoop`.
- `vibey doctor [--conformance]` — runs `application/conformance.py::
  run_conformance` (the existing 9-check suite) against every installed
  runner found on PATH. This is a named item in the implementation plan's
  "Definition of done for v1" checklist — it doesn't exist yet.
- Fix `vibey watch`: pass a real `state_fetcher` into `VibeyDashboardApp`
  (currently omitted entirely, `cli/main.py:383`) so the refresh timer
  actually installs, and add a `ChatPanel` that tails the active engine via
  the new adapter's `tail`.

### 5. Two-mode test harness (`tests/live/`)

- Add `pytest` markers `live` and `paid` to `pyproject.toml` (alongside the
  existing `integration`, `slow`, `system`).
- `tests/live/` — vibey ①→②→③→(④→⑤→⑥) against the **real installed loop
  binaries**, two modes:
  - **faked** (default, runs in CI eventually — not this task's job to wire
    CI, just make the tests exist and pass locally): each loop's own
    scripted/offline env gate (`<LOOP>_ALLOW_TEST_AGENT=1` +
    `<LOOP>_TEST_AGENT_SCRIPT=...`). agyloop doesn't ship a `scripted.py`
    today (only claudeloop/codexloop/cursorloop do) — if you need it for
    agyloop coverage here and it's a small, well-scoped addition, add
    `infrastructure/agent/scripted.py` to agyloop mirroring its three
    siblings; if it's bigger than that, note the gap and skip agyloop in
    faked-mode live tests rather than scope-creep into a parallel repo.
  - **live**: gated by `VIBEY_LIVE_ENGINES=claudeloop,agyloop` (comma-list,
    empty/unset = skip live tests entirely) + a `--max-dollars`-equivalent
    cap threaded through; real models, real (small) spend. Mark these
    `@pytest.mark.paid` so they're trivially excludable.
- A forced-rotation scenario: start work on engine A (faked mode is fine),
  force a wind-down/capacity-exhaustion, verify the no-loss gate produces a
  brief whose closable ids are verbatim present in engine B's first seed
  prompt — this mirrors the existing (protected, do-not-touch)
  `tests/infrastructure/db/test_end_to_end_forced_rotation.py` but through
  the real `LoopProcessAdapter` + `EngineSelector` instead of
  `ScriptedEngine` directly.
- Unwind-ledger / residue check: after a `tests/live/` run, assert no writes
  landed outside the run's worktree, no orphaned worktrees/branches remain,
  no stray `.vibey`/`.claudeloop` litter in the vibey repo itself.
- `tests/contracts/test_*_contract.py`: for each repository port that has
  both a fake and a Postgres implementation, one parameterized test class
  run against `[fake, postgres]`, proving `FakeX.method` behaves like
  `PostgresX.method` for the same inputs. Start with `JobRepository` (the
  most behaviorally complex — `enqueue/claim/heartbeat/ack/nack/park/reap`)
  since a broken fake there would make every faked-mode test meaningless.
- Consolidate the ~60 inline `class Fake...` declarations currently
  duplicated across 26 test files into `tests/fakes/` (one module per port,
  reused everywhere) + `tests/fakes/test_port_parity.py` asserting
  `isinstance(FakeX(), PortX)` for every one of the 34 declared Protocols.
  Copy the structure of `~/git/codexloop/tests/application/test_ports.py`
  (a parametrized table of `(name, fake, Protocol)` triples with per-case
  ids) rather than inventing a new shape.

### 6. Fix the false advertising

`README.md` line ~23 advertises a done marker `VIBEY_TASK_FULLY_COMPLETE`
that exists nowhere in the code. Either implement it (a completion contract
for `vibey worker` analogous to what each loop already does for itself) or
correct the README to not claim it. Prefer implementing it if it's a small
addition given the CLI work above; otherwise fix the doc and note the gap.

## Definition of done

- `pytest -m live` green in faked mode for all engines you got working (at
  minimum claudeloop, codexloop, cursorloop; agyloop if scripted.py was in
  scope per above), and in live mode for claudeloop + agyloop specifically
  (small `--max-dollars` cap, real spend, real value as a smoke test).
- `vibey doctor --conformance` passes on every installed runner.
- A real project goes ①→③→DONE(local) via `vibey worker`, with **at least
  one forced rotation** actually exercised end to end.
- All four layers (domain/application/infrastructure/cli) still at 100%
  branch coverage. Full 7-gate sweep green:
  `ruff check`, `ruff format --check`, `mypy --strict src/vibey`, the four
  `pytest --cov=vibey.<layer> --cov-branch --cov-fail-under=100` runs,
  `lint-imports`, `bandit -q -r src/vibey`, `pip-audit`. Re-run the full
  suite `for i in 1 2 3 4 5; do uv run pytest -q; done` before trusting it.
  Also run once with `HOME=$(mktemp -d)` — a config/credential lookup that
  only works because of files on this machine is the single most common
  false-green in this fleet.

## Done

When every item above is genuinely satisfied — not aspirationally — commit
with Conventional Commits and end your final message with
**CLAUDELOOP_TASK_FULLY_COMPLETE**. If you touched a protected test file,
say so explicitly and do not claim completion; leave the PR for a human
instead. If a gate can't be made to pass, stop and explain why rather than
weakening it.
