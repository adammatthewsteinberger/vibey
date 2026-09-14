# Model profiles

Composer-first: the default profile targets Cursor's Composer lane, and every
other model — Grok included — is a *profile*, not a separate product with
separate plumbing. Pick one per run:

```bash
cursorloop models                 # what the account can use
cursorloop run --plan plan.md --model MODEL_ID
export CURSORLOOP_MODEL=MODEL_ID  # or set it for every run
```

A profile carries the model id plus the loop's expectations for it (how its
rate-limit and billing messages read — see
[rate limits and credits](rate-limits-and-credits.md)), so switching models
never means editing the loop.
