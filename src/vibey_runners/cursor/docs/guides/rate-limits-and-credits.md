# Rate limits and credits

Two very different "the model said no" cases, and the loop refuses to treat
them alike:

- **A rate-limit window is waitable.** The verdict enters WAITING/PROBING with
  a bounded probe: wait, re-test, and give up at `--max-wait` seconds. The
  phrases that classify as rate limits come from
  `CURSORLOOP_RATE_LIMIT_LEXICON`, so a vendor rewording is a config edit.
- **Credit exhaustion is not waitable-with-a-deadline.** No amount of waiting
  refills a balance, so the run fails fast with the reason in the audit trail.
  Classification phrases come from `CURSORLOOP_BILLING_LEXICON`.

Watch it happen live:

```bash
cursorloop watch     # shows WAITING/PROBING entries with their deadlines
cursorloop usage     # spend and turn counters for the window
```
