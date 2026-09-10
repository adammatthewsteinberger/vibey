# Rate limits vs credits

A `429 RESOURCE_EXHAUSTED` is not one thing:

| State | Meaning | Waiting helps? |
|---|---|---|
| RPM / TPM / IPM window | Per-minute throttle | Yes — short probe cadence |
| RPD window | Daily quota | Yes — next Pacific midnight, not a short sleep |
| Credits / spend / billing cap | No balance, spend cap | **No clock reset.** Probe until a human tops up |
| Auth failure | Bad or revoked credentials | Never — abort |

`--no-probe` waits only to computed quota boundaries and issues zero probe
requests. `--max-turns`, `--max-wait`, and `--max-tokens` bound a run.

`--ramp N` paces the first N turns (sleep `attempt` seconds before each) so a
cold Enterprise run is less likely to hit acceleration limits inside quota.

RPM ≠ RPD ≠ credits. A billing wall does not grow a reset timestamp.
