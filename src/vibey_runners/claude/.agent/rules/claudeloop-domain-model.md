# claudeloop-domain-model (Antigravity mirror of `.claude/skills/claudeloop-domain-model/SKILL.md`)


# claudeloop domain model

Everything in `src/claudeloop/domain/` is frozen dataclass, zero
third-party imports, 100% test coverage.

## CapacityState (capacity.py)

```python
CapacityState = Available | WindowExhausted | CreditsExhausted | AuthenticationFailed
```

**Most important fact**: `CreditsExhausted` has NO `resets_at` field — not
`None`, the type doesn't carry one. Waiting cannot fix an empty balance.
`WindowExhausted` carries `resets_at: datetime | None`.

## classify.py — TurnSignals → CapacityState

Reads three SDK signals. **Ordering is load-bearing**, in this sequence:

1. `assistant_error == "authentication_failed"` → `AuthenticationFailed`
2. `rate_limit_status == "allowed_warning"` → `Available` (NOT a rejection)
3. Credit signals (`credits_required`, `out_of_credits`,
   `overage_disabled_reason`) win over stray `resets_at` → `CreditsExhausted`
4. Anything else rejected → `WindowExhausted`

Preserve order. Re-run `tests/domain/test_classify.py`.

## CompletionVerdict (completion.py)

```python
CompletionVerdict = Done | Continue | Blocked
```

Primary: `StructuredVerdict` from `output_format`. `blocked_on` outranks
`complete`, terminates run. Fallback: substring-match
`CLAUDELOOP_TASK_FULLY_COMPLETE`.

## waiting.py — next_probe_instant()

Returns **instant to probe**, never a duration.

- `CreditsExhausted` — exponential backoff, clamp BEFORE constructing
  `timedelta` (overflow at realistic probe counts).
- `WindowExhausted(resets_at=X)` — `min(X + reset_grace, now +
  window_probe_interval)`.

See `docs/architecture/domain-model.md`.
