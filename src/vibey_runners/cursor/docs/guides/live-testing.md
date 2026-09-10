# Live testing

Most of the suite is deterministic and free; the part that talks to real
Cursor accounts is opt-in, so CI never burns credits by accident:

```bash
pytest                    # unit + integration, no network
pytest -m system          # deterministic end-to-end harness, still no vendor calls
pytest -m live            # real account, real spend — needs CURSOR_API_KEY
```

`-m live` is for release verification and vendor-behavior changes (a new
rate-limit phrasing, a changed completion format). Run it with a bounded
budget in the environment (`CURSORLOOP_MAX_DOLLARS`) so a broken test cannot
spend more than pocket change.
