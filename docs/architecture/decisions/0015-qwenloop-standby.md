# ADR-0015: qwenloop is an opt-in standby tier

## Decision

Vibey recognizes the independent `qwenloop` runner, but the feature is off by
default. `[features] qwenloop = true` adds it to the effective engine pool.
`VIBEY_FEATURE_QWENLOOP` may override that switch for deployments.

Qwenloop is selected only when no otherwise-eligible paid engine exists, or
when a phase explicitly allows only qwenloop. This prevents a zero-dollar
local descriptor from crowding paid engines out of smooth weighted rotation.
Activation and `doctor` never download model weights. Model installation is an
explicit qwenloop operation.

The runner uses `.qwenloop/runs/<run-id>`, the
`QWENLOOP_TASK_FULLY_COMPLETE` marker, and the shared graceful wind-down exit
code 75. Local resource/configuration failures are not provider-credit
exhaustion.
