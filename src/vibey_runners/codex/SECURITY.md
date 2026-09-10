# Security policy

## Why this matters more than usual for this project

`codexloop` is designed to drive OpenAI Codex **unattended, for potentially
multi-day runs**, which means it:

- Runs `codex exec` with `-c approval_policy="never"` so autonomous operation
  is possible — no approval prompt is ever shown, and the child is spawned
  with stdin closed. The default sandbox is `sandbox_mode="workspace-write"`,
  which keeps writes inside the workspace; `danger-full-access` is reachable
  only behind an explicit, loudly-audited opt-in that refuses to run as root
  or outside a git repository. A misconfigured or compromised run still has
  more latitude than an interactive session.
- Reads and handles OpenAI credentials — `OPENAI_API_KEY` in API-key mode, or
  the `codex login` OAuth material in `$CODEX_HOME/auth.json` in ChatGPT-plan
  mode. The two are never mixed; `codexloop doctor` reports which is active.
- Writes per-run `events.jsonl` / `audit.jsonl` under
  `.codexloop/runs/<run_id>/` that can contain prompts, tool output, and
  error bodies. Logs redact API keys and `auth.json` material, and the
  optional `--log-file` uses the same redactor. Treat run directories and log
  files as sensitive anyway.
- Never invokes bare `codex` (the interactive TUI) and never emits
  `--full-auto` (deprecated, then removed upstream). Both are forbidden in the
  argv builder.

The env vars `CODEXLOOP_ALLOW_TEST_AGENT` / `CODEXLOOP_TEST_AGENT_SCRIPT`
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

1. [GitHub Security Advisories](https://github.com/adammatthewsteinberger/codexloop/security/advisories/new)
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

- Any way `codexloop` could be induced to bypass its own "never block on a
  human" safety design in a way that causes *harmful* unattended action (as
  opposed to simply failing) — e.g. a prompt-injection path from tool output
  back into a decision the runner treats as authoritative.
- Any path that emits `danger-full-access` / drops the sandbox without the
  documented opt-in, or that reintroduces bare `codex` / `--full-auto`.
- Credential handling — logging, redaction, or storage of `OPENAI_API_KEY`,
  `CODEX_API_KEY`, or `auth.json` tokens in a way that leaks them (to logs,
  to disk, to a third party).
- Path traversal or command injection in anything derived from a plan file,
  thread content, or CLI arguments — the project's explicit design goal is
  "no `shell=True` anywhere," and any path that reintroduces that class of
  risk is a real finding.
- Any way the generated REST surface (`codexloop api ...`) could execute an
  unintended request against a live OpenAI account — destructive actions
  executed without a clear, deliberate invocation.

**Out of scope:**

- Vulnerabilities in the Codex CLI or the `openai` package themselves —
  report those to OpenAI directly.
- Issues requiring an attacker to already have arbitrary code execution on
  the machine running `codexloop` (at that point, the OS has already been
  compromised).
- Rate limits or quota exhaustion on your own OpenAI account — that's an
  account/billing concern, not a vulnerability in this tool.
