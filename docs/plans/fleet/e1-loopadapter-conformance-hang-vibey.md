# vibey — LoopProcessAdapter still can't observe a genuinely healthy agyloop run

Not yet launched. Written up for queueing after closing out
`c3-harness-handshake-agyloop.md` (agyloop PR #29, merged) — that fix is
real and independently verified multiple ways below. This is a *new*,
distinct, vibey-side finding uncovered while verifying it end-to-end.

## What's now proven healthy (do not re-litigate)

With agyloop PR #29 merged (code-signs the patched harness binary after
byte-patching it, since macOS SIGKILLs a process whose signature the patch
just invalidated — the actual root cause of "Failed to read length from
stdout"), all of the following succeed completely, repeatably:

1. `agyloop run <plan> --run-id X --preset low --effort low --cwd <dir>`
   run directly from an interactive shell.
2. The exact same argv reproduced via a bare `asyncio.create_subprocess_exec`
   Python script using `communicate()` to wait for completion.
3. The exact same argv AND spawn parameters `LoopProcessAdapter.start()`
   itself uses (`stdout=PIPE, stderr=PIPE, cwd=<dir>`, **never draining
   those pipes**, just polling `process.returncode`) via a standalone
   script that faithfully copies `start()`'s exact behavior.

All three write `test.txt`/`events.jsonl`/`meta.json`/`snapshots/latest.json`
and complete with `success: true` in well under 15 seconds.

## What's still broken

`vibey doctor --conformance --engine agyloop` (i.e. the real
`LoopProcessAdapter` + `run_conformance()` running inside an actual `uv run
vibey doctor` process) still fails `run_dir_shape`/`snapshot_schema`/
`done_marker`/`structured_verdict` with `events_file_missing` after the
full poll window (30s in `run_conformance()` + up to another 10s inside
`tail()`), even run back-to-back immediately after confirming (3) above
works. Not intermittent — reproduced on two consecutive invocations.

## What's already ruled out (do not redo this investigation)

- **Not the base_dir/worktree_path bug** (fixed in #21) — the logged
  `events_file_missing` path is correctly rooted under
  `spec.worktree_path`, not some other directory.
- **Not the harness handshake/code-signing bug** (fixed in #27, then
  confirmed further fixed in #29) — proven healthy by items 1-3 above,
  including a reproduction using `LoopProcessAdapter.start()`'s *exact*
  spawn parameters.
- **Not a classic stdout/stderr pipe deadlock** (the parent never draining
  `PIPE` pipes while the child writes a lot of output, which can fill the
  OS pipe buffer and block the child forever) — reproduction (3) above
  uses the identical `stdout=PIPE, stderr=PIPE`, never-read setup and
  completed fine well within the poll window.
- **Not a stdin/TTY difference** — reproduction (2) and (3) don't set
  `stdin` at all, matching `LoopProcessAdapter.start()` exactly, and both
  succeed.
- **Not the conformance scratch dir being a bare (non-git) directory**
  (fixed in #21).

## What hasn't been tried yet

The one variable none of the standalone reproductions share with the real
failure: running *through* `run_conformance()`'s actual call sequence
inside the actual `vibey` process (preflight → start → the concurrent
`tail()` polling loop that's *simultaneously* reading `events.jsonl` while
the subprocess is still writing it, plus `run_conformance()`'s own polling
of `meta.json`/`events.jsonl`/`snapshots/latest.json` existence). Candidates,
untested:

- `tail()` (`loop_process_adapter.py`) opens and re-reads `events.jsonl`
  in a loop while the file is actively being written. Check whether a
  partial/truncated read during a mid-write moment could raise an
  exception that gets swallowed somewhere upstream, silently ending the
  poll early without it showing up as `events_file_missing` per se, or
  whether repeated `Path.read_text()` calls against a growing file
  interact badly with the agyloop process's own I/O in some way.
- `agyloop run`'s own session-lock mechanism (`session.lock_acquired`/
  `session.lock_released` seen in every successful log) is presumably
  keyed by something under `--cwd`. `run_conformance()`'s default scratch
  dir (`/tmp/vibey-conformance`) is *shared* across every conformance
  check ever run against it (not randomized per invocation) — check
  whether running `vibey doctor --conformance` twice in a row without
  clearing that directory leaves stale lock/session state that a *second*
  real agyloop process collides with, even though each gets its own
  `run_id` subdirectory. Test by using a fresh, uniquely-named
  `trivial_worktree` per run instead of the shared default and see if
  that alone fixes it — cheap to test, would immediately confirm or rule
  out this specific hypothesis.
- Whether `vibey doctor`'s own asyncio event loop scheduling (running
  `preflight()`, `start()`, and `tail()`'s polling loop all as awaited
  coroutines within one process) somehow starves the child process of
  CPU/scheduling in a way an interactive shell invocation never would.

Reproduce by running `vibey doctor --conformance --engine agyloop` twice in
a row against a **freshly created, uniquely-named** scratch dir each time
(not the shared default) as the very first experiment — it's the cheapest
way to either confirm or rule out the shared-scratch-dir hypothesis before
going deeper.

## Budget discipline

Same as the other harness plans in this directory: reproduce carefully,
form one real hypothesis backed by evidence from the *actual* failure path
(not another simplified script that might not share the real bug), fix it,
verify with a real `vibey doctor --conformance --engine agyloop` run. Stop
and write up findings rather than guessing indefinitely if the cause isn't
clear after a genuinely careful pass.

## Gates

Standard vibey 7-gate sweep, all four layers at 100% branch coverage (see
`docs/plans/fleet/e1-conformance-timeout-vibey.md` for the exact commands).

Done only after `vibey doctor --conformance --engine agyloop`, run for
real against a fresh scratch directory, actually passes `run_dir_shape`,
`snapshot_schema`, `done_marker`, and `structured_verdict` — not merely
after the gates above pass.
