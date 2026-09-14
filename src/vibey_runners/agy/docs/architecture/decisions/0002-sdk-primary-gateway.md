# ADR 0002: google-antigravity SDK is the primary gateway

## Status

Accepted (2026-08-13).

## Context

Two transports exist: the preview SDK and the `agy` CLI.

## Decision

`AgentGateway` is the port. `--gateway sdk` (default) uses `google.antigravity.Agent`. `--gateway cli` is a secondary adapter behind the same port. Vendor types never leave infrastructure/.

## Consequences

Recorded in architecture §19. Changing this ADR requires a new numbered record, not a silent edit of the classifier or ports.
