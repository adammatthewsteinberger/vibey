---
name: agyloop-domain-model
description: CapacityState, TurnSignals, completion verdicts, waiting, and the run loop. Consult before editing domain/classify.py, waiting.py, completion.py, or loop.py.
allowed-tools: Read Grep Glob
---

# agyloop domain model

`src/agyloop/domain/` is stdlib-only. Frozen dataclasses / closed unions.

## CapacityState (ADR 0003 — five members)

```
Available | WindowExhausted | TransientThrottle | CreditsExhausted | AuthenticationFailed
```

`CreditsExhausted` has **no** `resets_at`. Never add one. Credits ≠ window.

`TransientThrottle` is a short waitable (503 / UNAVAILABLE / RetryInfo).

## classify.py

Ladder over `TurnSignals`. Operator cancel (exception type **or**
`context canceled` / `context cancelled` / `manage_task` in the message)
is Available **before** the throttle ladder. Do not match a bare
`canceled`. 404 / withdrawn-model is **not** a sixth state — the adapter
raises `AgentConfigError`.

## completion.py

Structured `{complete, remaining_work, blocked_on, summary}`. Capacity
rejection outranks a Done claim.

## loop.py

Pure state machine. No I/O. The runner only performs the Decision.
