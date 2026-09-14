# Autonomous runs

An unattended run has to answer for itself: what is it doing, what may it
spend, and when is it done? `cursorloop run --plan plan.md` seeds a session
from the plan and loops turn by turn until one of three things happens:

1. **Done** — the completion evidence in
   [completion detection](completion-detection.md) all agrees;
2. **a bound trips** — turns (`--max-turns`), dollars (`--max-dollars`),
   a hung turn (`--turn-timeout`), or silence (`--stall-timeout`);
3. **an operator stop** — `cursorloop stop` now, or `cursorloop wind-down`
   after the current turn.

A worked overnight run:

```bash
cursorloop run --plan plan.md --max-dollars 10 --max-turns 80 \
    --turn-timeout 600 --stall-timeout 120
```

Every turn is recorded under `.cursorloop/runs/<id>/` and each meaningful
step gets a git savepoint, so the morning after starts with
`cursorloop runs`, `cursorloop logs`, and — if needed —
`cursorloop unwind` back to any savepoint.
