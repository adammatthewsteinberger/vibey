# Security policy

## Supported versions

The latest production release is supported. Security fixes may be backported only when
the maintainer explicitly announces support for an older line.

## Reporting a vulnerability

Do not open a public issue. Use GitHub private vulnerability reporting when available or
email `adam@matthewsteinberger.com` with impact, reproduction, affected versions, and any
suggested mitigation. Expect acknowledgement within seven days. Coordinated disclosure
timing will be agreed with the reporter.

## Trust boundaries

Pull-request content, workflow logs, model output, retrieved content, and generated files
are untrusted. Privileged automation must not execute contributor-controlled code. Tokens
use least privilege; third-party Actions are immutable; permanent branches are never
deleted or force-pushed. See `docs/security.md` and `docs/threat-model.md`.
