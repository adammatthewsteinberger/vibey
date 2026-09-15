---
name: pr-repair
description: This skill should be used when diagnosing or repairing failed pull-request scans without weakening their checks.
---
# PR repair

Aggregate all current-head checks, distinguish actionable code failures from operational
blocks, inspect logs, find root cause, and make the smallest correct edit. Never execute
untrusted PR code in a privileged job. Push at most one guarded commit per attempt.
