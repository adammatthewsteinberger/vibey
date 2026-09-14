# Quickstart

```bash
agyloop doctor                  # pre-flight: auth lane, no interactive hooks
agyloop run handoff.md          # seed a session from a plan and run unattended
agyloop resume --last           # resume the most recent .agyloop/ run
agyloop sessions                # local .agyloop/runs registry only

# Mid-run (second terminal, same cwd):
agyloop prompt --now "Also cover the error path"
agyloop prompt --at-break "Then write tests"
agyloop stop                    # soft-stop the active run

# After a run:
agyloop snapshot
agyloop savepoints
agyloop unwind --to 1           # refuses while the run is still active
```

The plan file is copied under `.agyloop/runs/<run-id>/plan.md`. Completion is
a structured verdict with fallback marker `AGYLOOP_TASK_FULLY_COMPLETE`.

Default transport is the Antigravity SDK (`--gateway sdk`). To drive a live
`agy` binary instead:

```bash
agyloop run handoff.md --gateway cli
agyloop run handoff.md --gateway cli --unsafe-skip-permissions
```

Pace the first N turns on the Enterprise lane (acceleration limits):

```bash
agyloop run handoff.md --ramp 5
```

Generated REST:

```bash
agyloop api models generate-content --json '{"model":"models/gemini-2.5-pro"}'
```

See [Usage](../usage.md) for the full operator surface.
