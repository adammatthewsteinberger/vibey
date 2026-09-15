# 0026 — tini is PID 1, and the SIGTERM latch is armed before the first import

**Status:** accepted · **Date:** 2026-09-15 · **Extends:** ADR-0025

## Context

ADR-0025's scale-in contract depends on the worker receiving SIGTERM. The minikube drain contract kept failing, and it was not flaky. `kubectl describe` gave the timeline: container started 12:23:04, delete issued 12:23:04.22. Linux treats PID 1 specially — a signal whose disposition is still `SIG_DFL` is **discarded, not queued**. SIGTERM arrived while Python was still booting, before any handler existed, and was thrown away permanently; the worker then sat out its entire 7200-second grace period claiming jobs nobody wanted, while `kubectl delete --timeout=5m` gave up long before.

Three fixes landed in sequence, each moving the handler earlier, and the first two were not enough:

1. Register the asyncio handler as the first statement in the event loop, before any I/O (2e8e48ad). Closes the window down to interpreter start, imports and argument parsing — which is where the signal was landing.
2. Arm a deliberately tiny handler at import time, above the `typer` import, whose only job is to remember (44c1c21a). This is the earliest point *the CLI* controls. It still lost: a pod deleted 0.6s after container start showed clean five-second iterations for 56 seconds after the delete. Exec, loading the interpreter, site initialisation and the import machinery are hundreds of milliseconds on a cold container, and all of it is before the first Python statement.

That race is not winnable from inside Python.

## Decision

**`tini` runs as PID 1; `vibey` runs as its child.** `ENTRYPOINT ["/usr/bin/tini", "-g", "--", "vibey"]`. tini installs its handlers in microseconds and forwards, which turns an unwinnable race into an ordinary one. `-g` signals the whole process group, so an engine subprocess the worker started is stopped too rather than orphaned onto init.

**The latch stays, and is not redundant.** `vibey.cli.early_signals.SIGTERM_LATCH.arm()` is the first statement of `cli/main.py`, above every other import — the one per-file E402 exception in the tree, with its reason beside it, because the placement *is* the fix. With tini above it, a SIGTERM in the window between interpreter start and the asyncio handler would otherwise end the process on the default disposition, part-way through connecting to the database; the latch converts that into a clean drain. `arm()` reports rather than raises when it cannot install (importing the CLI from a worker thread is legitimate), and `release()` hands the disposition back once the real handler owns it.

The resulting behaviour: SIGTERM during boot terminates a worker that has claimed nothing — correct and prompt; SIGTERM after boot drains gracefully.

## Consequences

**Good.** The drain contract passes, and CI now echoes the container's start time beside the delete so a future failure can be classified as startup race or broken drain from the log alone. The unit test for the latch proves the bug by hanging when the check is disabled — a worker that never learns to drain never stops.

**Bad.** One more binary in the runtime image, and a lint exception that every future reader of `cli/main.py` must understand before "fixing" the import order. Both are documented at the site.

**Rule status.** Mechanism; does not pass ADR-0020's test.

## Alternatives rejected

- **Handler first in the event loop only.** Loses to a delete inside interpreter start.
- **Import-time latch only.** Loses to a delete inside exec and site initialisation; measured, not assumed.
- **A preStop hook.** Cannot tell the claim loop to stop (ADR-0025).
- **A shorter grace period.** Makes the symptom shorter, not absent, and throws away paid session work.
- **`--init` / the runtime's own init.** Kubernetes does not expose Docker's `--init`; shipping tini in the image is the portable form of the same idea.
- **Remove the latch now that tini exists.** Rejected: it is what makes a boot-window SIGTERM a drain instead of a kill.
