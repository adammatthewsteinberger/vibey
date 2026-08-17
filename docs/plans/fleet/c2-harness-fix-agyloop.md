# agyloop — Phase C2: fix the local-harness / CLI-gateway startup failures

You are working unattended in a disposable git worktree of `agyloop`
(`~/git/agyloop`), on branch `chore/c2-harness-fix`. Pass `--cwd`
explicitly wherever `agyloop` supports it (it has good `--cwd` coverage).

This is a real, mature codebase — 100% branch-covered on all four
architectural layers, CI-gated. Do not weaken any gate, delete a test, or
add a coverage exclusion to get to green.

## Why this task exists

Two real failures were hit trying to dogfood agyloop unattended, back to
back, in this exact environment. Both are genuine bugs, not environment
misconfiguration — fix the root cause, don't just document a workaround.

### Bug 1: the default SDK gateway's local harness fails to start

`agyloop run ... --gateway sdk --preset high --scoped --ramp 3` (agyloop's
own documented default invocation, per
`~/git/vibey/docs/plans/fleet-program-runbook.md`) fails immediately with:

```
RuntimeError: Failed to read length from stdout. Stderr:
AgentConfigError: the local Antigravity harness failed to start. This is a
harness problem, not a capacity problem.
```

Read `docs/contributing/harness-patch.md` first — it documents that agyloop
ships a runtime copy-patch of Google's `localharness` binary (a withdrawn
model-id string swap) into `~/.cache/agyloop/localharness` (or
`AGYLOOP_HARNESS_CACHE`), and that `agyloop doctor repair-harness` restores
a bundled backup. In this environment, a patched copy already exists at
`~/.cache/agyloop/localharness/localharness` (a valid `arm64` Mach-O
executable, so it's not simply corrupted at the file level) but the SDK
still can't complete its handshake with it — empty stdout, empty stderr,
immediate exit. Diagnose why: is the patch being applied at the wrong byte
offset for the currently-installed `google-antigravity` SDK version (check
`pyproject.toml`'s pinned version against what the patch logic assumes)?
Is `agyloop doctor repair-harness` actually restoring a working binary, or
also producing a broken one? Does the harness need an argument or stdin
handshake the copy-patch logic doesn't preserve? Reproduce with
`agyloop doctor` and/or a minimal direct invocation of the harness binary
before touching any patching code, so you're fixing a confirmed cause, not
guessing.

Fix so that `agyloop run --gateway sdk` (agyloop's own documented default)
works end to end in this environment, or — if the harness truly cannot be
made reliable here — make the SDK-gateway preflight probe **fail fast with
a clear, actionable error** rather than the current raw
`AgentConfigError`, and make `agyloop doctor` proactively detect this
condition (add a check if one doesn't already cover it) so a user finds out
before spending a run's turn budget on it.

### Bug 2: the CLI-gateway fallback silently does nothing and lies about completion (more urgent — this one produced a false success)

As a workaround for Bug 1, the fleet launcher switched to
`--gateway cli --scoped`. This did **not** fail — it completed "successfully"
in 3 turns and emitted `AGYLOOP_TASK_FULLY_COMPLETE` — but every turn's
entire output was:

```
jetski: no output produced — a tool required the "command" permission that
headless mode cannot prompt for, so it was auto-denied. Add an allow-rule
under permissions.allow in settings.json (e.g. command(<target>)).
Alternatively, re-run with --dangerously-skip-permissions to auto-approve
all tools.
```

**No file was ever read, no command ever ran, and the run still declared
victory.** This is the worse of the two bugs: it doesn't fail loudly, it
silently produces nothing and reports success. Root cause: the CLI gateway
(`infrastructure/agent/gateway_cli.py`) shells out to the separately
installed `agy` binary via `build_agy_argv` (`infrastructure/agent/cli_argv.py`),
which defaults to `--sandbox` + `proceed-in-sandbox` / `deny: unsandboxed`
(`cli_argv.py:129-130`). `--scoped` is agyloop's own posture flag, designed
for the SDK gateway's in-process policy engine
(`infrastructure/agent/policies.py`'s `allow_all`-named-policy convention)
— but it has **no corresponding effect on the CLI gateway's exported `agy`
settings**, so `agy` falls back to its own default sandboxed posture, which
cannot grant command-execution permission non-interactively, and every
tool call it needs is auto-denied.

Two things need fixing here, and both matter:

1. **`--scoped` must actually authorize command execution when using the
   CLI gateway**, equivalent in spirit to what it does for the SDK gateway:
   workspace-scoped writes allowed, destructive commands still denied, but
   ordinary build/test/lint commands inside the worktree must not be
   silently blocked. Figure out the right shape for this — likely writing
   an explicit `permissions.allow` rule set (scoped to the run's `cwd`) into
   the settings JSON `execute_agy` already exports
   (`invocation.settings` → `AGYLOOP_AGY_SETTINGS_FILE`), not a blanket
   `--dangerously-skip-permissions`/`--unsafe-skip-permissions` (that's a
   materially different, much broader posture and conflates two things
   that should stay distinct).
2. **A run whose every turn is entirely permission-denial noise must never
   be allowed to reach a "done" verdict.** This is the actual safety bug:
   completion detection (wherever `AGYLOOP_TASK_FULLY_COMPLETE` gets
   accepted as a verdict) needs a sanity check — if a turn produced zero
   tool executions, zero file changes, and its only content is a permission
   or capability error, that is not evidence of "nothing left to do"; it's
   evidence the run never got to do anything. Distinguish this from a
   legitimately trivial task (which is rare in this fleet's actual usage —
   every plan file is substantial) and fail the run with a clear
   diagnostic instead of a false `success=True`. This protects every other
   run in this fleet from the same silent-no-op failure mode.

## Tests

Test-first. For Bug 1: whatever the root cause turns out to be, add a
regression test that would have caught it (a fixture harness binary /
mocked subprocess that reproduces the exact "empty stdout, empty stderr"
condition, asserting the improved error message and/or the `doctor` check
catches it). For Bug 2: a test that a turn consisting only of a
permission-denial message from the underlying tool does **not** get
classified as a completion signal even when it's followed by a marker
string — and a test that `--scoped` under the CLI gateway actually produces
an `agy` settings payload that permits an in-worktree command to run (you
can test the settings-generation logic directly without needing a real
`agy` binary — check what's already mockable in `cli_argv.py`/
`gateway_cli.py`'s existing test suite and extend that pattern).

Keep all four layers at 100% branch coverage. Full 7-gate sweep: ruff
check/format, `mypy --strict src/agyloop`, the four
`pytest --cov=<layer> --cov-fail-under=100` runs, `lint-imports`, `bandit`,
`pip-audit`. Re-run the full suite 3-5 times before trusting green.

## Smoke test

After your fix, both of these must actually do real work (not just exit 0):

```bash
agyloop run <trivial-plan-that-reads-a-file-and-echoes-it> --cwd /tmp/smoke-sdk \
  --gateway sdk --preset high --scoped --run-id smoke-sdk
# must not raise AgentConfigError; must show real tool output, not silence

agyloop run <same-plan> --cwd /tmp/smoke-cli \
  --gateway cli --scoped --run-id smoke-cli
# must show the command/file-read tool actually executing, not "auto-denied"
```

If you genuinely cannot make Bug 1 (SDK harness) work in this environment
after real investigation, that's an acceptable outcome **as long as you
document exactly why** (with the specific evidence — offsets, versions,
handshake bytes) and Bug 2 is still fully fixed, since Bug 2 is the one
that produces silent false success and is the higher-priority fix of the
two.

## Done

Full gate sweep green, Conventional Commit, end your final message with
**AGYLOOP_TASK_FULLY_COMPLETE** — only when genuinely done, and only if a
completion-detection safeguard for Bug 2 is in place and tested. If a gate
can't be made to pass, stop and explain why instead of weakening it.
