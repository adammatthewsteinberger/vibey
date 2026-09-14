# Ports and adapters

Protocols in `application/ports.py` define what the use cases need; concrete
implementations live only under `infrastructure/`:

| Port | Adapter | Talks to |
|---|---|---|
| agent transport | `infrastructure/agent` | the Cursor agent CLI session |
| cloud API | `infrastructure/api` (generated, drift-gated) | Cursor Cloud Agents REST |
| savepoints | `infrastructure/git_savepoints` | git |
| control | `infrastructure/control`, `run_control`, `lock` | the `.cursorloop/` control plane |
| observability | `infrastructure/events`, `state_bus`, `stream_ui`, `logging`, `audit`, `redact` | structlog + JSONL under `.cursorloop/runs/<id>/` |
| environment | `infrastructure/config`, `doctor_env`, `clock` | env/file/system |

The REST client is generated from Cursor's published surface and guarded by a
drift gate: if the vendor's API changes shape, CI fails loudly instead of the
loop failing quietly at 3 a.m.
