# agyloop — SDK harness still fails its stdio handshake even with permissions fixed

Not yet launched as a dogfooded run — written up for queueing, since a lot
of real investigation already went into this today and it deserves a fresh,
focused session rather than continuing to spend live-API budget on it
ad hoc. Launch with:

```bash
scripts/fleet/run.sh agyloop c3-harness-handshake claudeloop
```

## What's already fixed (do not redo)

`docs/plans/fleet/c2-harness-fix-agyloop.md` (PR #25, merged) added loud
diagnostics for harness-startup failure instead of a raw traceback, and
fixed the `--gateway cli --scoped` false-success bug.

Separately, just fixed today (PR #27 on agyloop, merged):
`overwrite_site_packages_harness()` in `src/agyloop/infrastructure/agent/
harness_retarget.py` wrote the patched stock binary and its backup via
`Path.write_bytes()`, which creates the backup as a brand-new file with
default (non-executable) permissions — losing the stock harness binary's
executable bit on the machine's `site-packages` copy. Confirmed
deterministically with a regression test
(`test_site_packages_overwrite_preserves_executable_bit`) and independently
verified end-to-end: a real `agyloop run` no longer flips the stock
binary from `-rwxr-xr-x` to `-rw-r--r--`.

## What's still broken

With permissions now provably intact, a real `agyloop run` (with a
concrete, trivially-completable prompt — see
`docs/plans/fleet/e1-conformance-timeout-vibey.md`, PR #23, also merged
today, which fixed vibey's own prompt-vagueness bug in
`run_conformance()`) still fails with:

```
AgentConfigError: the local Antigravity harness failed to start. This is a
harness problem, not a capacity problem.
  ...
  Underlying error: Failed to read length from stdout. Stderr:
```

This is the exact symptom `c2-harness-fix-agyloop.md` originally reported
as Bug 1 and believed fixed. It is not fixed — it was previously masked by
the permission bug from being reachable in a clean state (the harness never
even got a chance to attempt the handshake before hitting `PermissionError`
first), and now reproduces cleanly with permissions confirmed correct.

Reproduce directly, bypassing vibey entirely (cheaper to iterate on, and
isolates vibey's own code from this investigation):

```bash
rm -rf /tmp/agyloop-repro && mkdir -p /tmp/agyloop-repro/.vibey/plans
cd /tmp/agyloop-repro && git init -q && git -c user.email=x@x -c user.name=x commit --allow-empty -q -m init
echo "Create a file at test.txt containing the text OK, then finish." > .vibey/plans/test.md
agyloop run .vibey/plans/test.md --cwd /tmp/agyloop-repro --run-id repro-1 --preset low --effort low
```

`smoke_check_harness()` in `harness_retarget.py` is supposed to catch a
copy that can't start (`Failed to read length from stdout` is explicitly
named in that function's own docstring as the failure mode a missing
sibling resource causes) and fall back to the site-packages-overwrite
layer instead of adopting a broken copy. Read that function and
`copy_harness_siblings()` closely: either the smoke check itself is
passing when it shouldn't (a false negative — the copy looks alive during
the 3-second smoke window but still fails the real handshake moments
later under `AntigravityAgentGateway`), or the sibling-copying logic is
missing something the smoke check doesn't exercise but a real turn does
(model config, a socket/port collision, a missing env var forwarded into
`LocalAgentConfig.env`).

Don't guess. Instrument first: add temporary logging (or run manually with
`AGYLOOP_SKIP_HARNESS_SMOKE=1` unset, comparing against a run with it set,
to isolate whether the smoke check itself is the gap) to see exactly what
the harness subprocess's stdout/stderr contain at the moment the SDK gives
up — right now nothing in the failure path surfaces that. Cross-reference
against `~/.cache/agyloop/localharness/` for missing siblings the stock
`bin/` directory has that didn't get copied.

## Budget discipline

Same as `e1-conformance-timeout-vibey.md`: reproduce carefully, form one
real hypothesis backed by evidence, fix it, verify once for real. If the
root cause isn't clear after a genuinely careful pass, stop and write up
what was ruled out rather than continuing to spend the budget on guesses.

## Gates

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy --strict src/agyloop
uv run lint-imports
uv run bandit -q -r src/agyloop
uv run pip-audit
for L in domain application infrastructure cli; do
  uv run pytest -q -p no:cacheprovider tests --cov="agyloop.$L" --cov-branch --cov-fail-under=100
done
```

Done only after a real (non-scripted) `agyloop run` against a fresh
scratch directory actually completes and writes `events.jsonl`/
`meta.json`/`snapshots/latest.json` — not merely after the gates above
pass.
