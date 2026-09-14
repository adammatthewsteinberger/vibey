# Quickstart

You want an agent to work through a plan unattended without you babysitting a
terminal. Two commands get you there:

```bash
export CURSOR_API_KEY=sk-...
cursorloop doctor          # proves auth + config before anything runs
cursorloop run --plan plan.md --max-dollars 5 --max-turns 40
```

`doctor` refuses to guess: it reports exactly which auth lane and settings it
can prove. `run` then loops until the plan completes, a bound trips, or you
stop it. While it runs, from another terminal:

```bash
cursorloop status          # state, capacity verdict, budget position
cursorloop watch           # live state transitions
cursorloop stop            # clean stop (or wind-down to finish the turn first)
```

Next: [configuration](configuration.md) for every bound, and
[autonomous runs](../guides/autonomous-runs.md) for how the loop decides to
run, wait, or stop.
