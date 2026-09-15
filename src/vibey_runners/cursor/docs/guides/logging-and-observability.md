# Logging and observability

When an unattended run misbehaves, the question is always *what exactly
happened at 3:41 a.m.?* — so everything the loop does lands in two places:

- **structlog** console/file logs — level via `--log-level` or
  `CURSORLOOP_LOG_LEVEL`, optional file via `CURSORLOOP_LOG_FILE`;
- **a JSONL audit trail** under `.cursorloop/runs/<id>/` — every turn, state
  transition, capacity verdict, and spend entry as one line of JSON, with
  secrets redacted before write.

The working set:

```bash
cursorloop runs                     # list run ids
cursorloop logs                     # tail the active/last run
cursorloop watch                    # live state transitions
python3 -m json.tool < .cursorloop/runs/<id>/audit.jsonl | less   # post-mortem
```
