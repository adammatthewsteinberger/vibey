# Security policy

`vibey-bootstrap` handles App Configuration connection strings, Key Vault
secrets, and Application Insights credentials at process startup, and its
optional extras touch webhooks, HMAC tokens, attachment ingress, and Service
Bus. Treat any report in those areas as high priority.

## Supported versions

Only the latest 3.x minor on PyPI receives security fixes. v1 and v2 lines
receive none — upgrade (the v2 → v3 path is additive; see
[MIGRATING-TO-V3.md](MIGRATING-TO-V3.md)).

## Reporting a vulnerability

**Do not open a public GitHub issue for a security vulnerability.**

Report privately via one of:

1. [GitHub Security Advisories](https://github.com/adammatthewsteinberger/vibey-bootstrap/security/advisories/new)
   for this repository (preferred — supports coordinated disclosure).
2. Email **adam@matthewsteinberger.com** with a description, steps to
   reproduce, and the affected version.

## What to expect

- Acknowledgment within a few business days.
- An initial assessment (severity, affected versions) within 10 business days.
- Coordinated disclosure: a fix is released before details are published,
  unless the reporter and maintainer agree otherwise.

## Out of scope

- Vulnerabilities in the Azure SDKs themselves — report those to Microsoft
  via [MSRC](https://msrc.microsoft.com/report).
- Issues that require an attacker to already have code execution on the host
  running your Function App.
