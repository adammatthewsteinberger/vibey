# CLI reference

One binary, `cursorloop`, drives the whole loop: start and steer unattended
runs, inspect what they did, and talk to Cursor's Cloud Agents API directly.
Every command below exists in `src/cursorloop/cli` — this page is generated
against that registry, not aspiration.

## Running

| Command | What it does |
|---|---|
| `cursorloop run --plan plan.md` | Seed a session from a plan file and loop until Done, a budget bound, or an operator stop. Accepts `--max-turns`, `--max-dollars`, `--max-wait`, `--turn-timeout`, `--stall-timeout`, `--model`, `--log-level`, `--run-id`, `--cwd`. |
| `cursorloop resume` | Re-attach to an interrupted run and continue it. |
| `cursorloop stop` | Stop the active run cleanly. |
| `cursorloop wind-down` | Finish the current turn, then stop — softer than `stop`. |
| `cursorloop prompt` | Inject a one-off operator prompt into the running session. |

## Observing

| Command | What it does |
|---|---|
| `cursorloop status` | Current run state, capacity verdict, and budget position. |
| `cursorloop logs` | Tail the structured logs for the active or last run. |
| `cursorloop watch` | Live view of the run loop's state transitions. |
| `cursorloop runs` | List past runs recorded under `.cursorloop/runs/`. |
| `cursorloop usage` | Spend and turn counters for the current accounting window. |

## State and recovery

| Command | What it does |
|---|---|
| `cursorloop savepoints` | List git savepoints the loop created. |
| `cursorloop snapshot` | Record a savepoint of the working tree now. |
| `cursorloop unwind` | Roll the working tree back to a savepoint (refuses while a run is active). |
| `cursorloop reset` | Wipe the local `.cursorloop/` control plane. |

## Environment

| Command | What it does |
|---|---|
| `cursorloop doctor` | Prove what auth and config the environment actually provides. |
| `cursorloop whoami` | The authenticated Cursor identity. |
| `cursorloop models` | Models the account can use. |
| `cursorloop agents` | Local agent transports available. |
| `cursorloop hooks` | Show the managed non-blocking hook state. |

## Cloud Agents (`cursorloop cloud ...`)

Direct access to Cursor's Cloud Agents API — the same surface the loop uses:

```bash
cursorloop cloud me                 # the authenticated account
cursorloop cloud models             # models the Cloud Agents API offers
cursorloop cloud create --help      # launch a cloud agent
cursorloop cloud get AGENT_ID       # inspect one agent
cursorloop cloud status             # service reachability
cursorloop cloud cancel AGENT_ID    # stop a cloud agent
```
