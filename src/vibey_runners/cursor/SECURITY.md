# Security policy

## Why this matters more than usual for this project

`cursorloop` is designed to drive a Cursor Agent **unattended, for
potentially multi-hour runs**, which means it:

- Merges an autonomy fragment into `.cursor/hooks.json` for the duration of a
  run and restores it afterward (hash-verified; a mid-run user edit wins;
  `cursorloop reset` recovers after a crash). A misconfigured or compromised
  run still has more latitude than an interactive session.
- Reads `CURSOR_API_KEY` and may surface credential-shaped strings in logs
  unless redaction holds (`infrastructure/redact.py` scrubs `crsr_…` keys
  and known secret fields). No `ANTHROPIC_*` or other foreign vendor env var
  is ever read or accepted as a fallback.
- Writes per-run `events.jsonl` / `audit.jsonl` under
  `.cursorloop/runs/<run_id>/` that can contain prompts, tool output, and
  error bodies. Treat run directories and log files as sensitive.
- Edits the working tree and runs tools without waiting on a human.

The env vars `CURSORLOOP_ALLOW_TEST_AGENT` / `CURSORLOOP_TEST_AGENT_SCRIPT`
activate a JSON-scripted agent for the system test harness only. They are
not a supported production control plane and must never be set on operator
machines running real work.

Treat any report touching these areas as high priority.

## Supported versions

Only the latest released version on PyPI receives security fixes. This
project is pre-1.0; there is no long-term-support branch.

## Reporting a vulnerability

**Do not open a public GitHub issue for a security vulnerability.**

Report privately via one of:

1. [GitHub Security Advisories](https://github.com/adammatthewsteinberger/cursorloop/security/advisories/new)
   for this repository (preferred — supports coordinated disclosure).
2. Email **adam@matthewsteinberger.com** with a clear description, steps to
   reproduce, and the version affected.

## What to expect

- **Acknowledgment** within 5 business days.
- **An initial assessment** (severity, affected versions) within 10
  business days.
- **Coordinated disclosure**: a fix is prepared and released before public
  details are shared, unless the reporter and maintainer agree on a
  different timeline (e.g. the issue is already public elsewhere).

## Threat model, briefly

**In scope:**

- Any way `cursorloop` could be induced to bypass its own "never block on a
  human" safety design in a way that causes *harmful* unattended action (as
  opposed to simply failing) — e.g. a prompt-injection path from tool output
  back into a decision the runner treats as authoritative.
- Hook restore failures that leave elevated autonomy in `.cursor/hooks.json`
  after a run ends or crashes.
- Credential handling — logging, redaction, or storage of `CURSOR_API_KEY`
  or other tokens in a way that leaks them (to logs, to disk, to a third
  party).
- The test-agent gate being reachable without **both** env vars set.
- Path traversal or command injection in anything derived from a plan file,
  agent content, or CLI arguments — the project's explicit design goal is
  "no `shell=True` anywhere."
- Any way the Cloud Agents surface (`cursorloop cloud ...`) could execute an
  unintended request against a live Cursor account.

**Out of scope:**

- Vulnerabilities in Cursor, the `cursor-sdk` package, or the Cursor bridge
  binary themselves — report those to Cursor directly.
- Issues requiring an attacker to already have arbitrary code execution on
  the machine running `cursorloop` (at that point, the OS has already been
  compromised).
- Rate limits or credit exhaustion on your own Cursor account — that's an
  account/billing concern, not a vulnerability in this tool.
