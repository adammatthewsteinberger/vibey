# Runbook: keep-awake — desktops never sleep mid-run

## Goal

When vibey is conducting on a desktop/laptop, the machine must not idle-
sleep or hibernate out from under a 2-hour engine session. The screen may
turn off and the session may lock — only system sleep is forbidden.
Automatic, scoped to active work, and released the moment work drains.

## Design

- `application/interfaces/power.py`: `SleepInhibitorPort` —
  `acquire(reason) -> handle`, `release(handle)`; a null adapter for
  servers/CI (k8s mode never needs it).
- Platform adapters in `infrastructure/power/`:
  - **macOS**: spawn `caffeinate -is` bound to the worker's lifetime
    (child process dies with us = inhibition auto-released; crash-safe by
    construction). `-i` blocks idle sleep, `-s` blocks system sleep on AC;
    display sleep stays allowed — exactly the contract.
  - **Linux**: `systemd-inhibit --what=sleep:idle --who=vibey
    --why="<reason>" --mode=block` wrapping a sentinel child, same
    lifetime binding; logind covers Ubuntu/Fedora/Arch alike. No D-Bus
    library needed.
  - **Windows (desktop app later)**: `SetThreadExecutionState(ES_CONTINUOUS
    | ES_SYSTEM_REQUIRED)` without `ES_DISPLAY_REQUIRED`.
- **Scoping policy (application layer, pure):** inhibition is held while
  the worker has ≥1 leased job or a due ready job, plus a short grace
  (5 min) to cover inter-job gaps; released when the queue drains. The
  policy is a pure decision (`domain/` if it stays IO-free) driven by the
  worker loop's claim/settle callbacks.
- Wired in `bootstrap.py` for `vibey worker` (opt-out flag
  `--no-keep-awake`); the Tauri desktop app (08) acquires through its own
  API call when running an embedded worker.
- The reason string names the project + job so `pmset -g assertions` /
  `systemd-inhibit --list` show *why* the machine is awake.

## Work items

1. Port + null adapter + policy (both-sides tests: acquires on lease,
   releases on drain, grace window honored).
2. macOS caffeinate adapter (subprocess-boundary fixture tests + child-
   lifetime binding test).
3. Linux systemd-inhibit adapter (same shape).
4. Worker wiring + `--no-keep-awake` + doctor line showing inhibitor
   state.
5. Windows adapter (deferred until the desktop app ships there).
6. Live proof on this MacBook.

## Verification

- Live: start a worker with a long implement, set system sleep to 2 min,
  walk away — session completes; `pmset -g assertions` shows the vibey
  assertion during the run and its absence after drain. Display sleeps;
  machine doesn't.
- Kill -9 the worker mid-run: assertion is gone immediately (child died)
  — no leaked inhibition.
- Linux: same script in a Fedora VM using `systemd-inhibit --list`.

## Needs from operator

Nothing. (macOS may show the assertion in battery UI — expected.)

## Risks

- On battery, macOS can still force-sleep on lid close — document that
  lid-open or AC is required for long runs; hibernation on critical
  battery is OS-mandated and out of scope.
- Grace-window flapping on bursty queues — hysteresis (instant acquire,
  lazy release) is the policy default.
