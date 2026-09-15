# codexloop

[![PyPI](https://img.shields.io/pypi/v/codexloop)](https://pypi.org/project/codexloop/)
[![PyPI downloads](https://img.shields.io/pypi/dm/codexloop)](https://pypi.org/project/codexloop/)
[![Python versions](https://img.shields.io/pypi/pyversions/codexloop)](https://pypi.org/project/codexloop/)
[![CI](https://github.com/adammatthewsteinberger/codexloop/actions/workflows/ci.yml/badge.svg)](https://github.com/adammatthewsteinberger/codexloop/actions/workflows/ci.yml)
[![Docs](https://github.com/adammatthewsteinberger/codexloop/actions/workflows/docs.yml/badge.svg)](https://adammatthewsteinberger.github.io/codexloop/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/adammatthewsteinberger/codexloop/blob/develop/LICENSE)

**Onion-architected, autonomous OpenAI Codex / GPT session runner and
generated OpenAI SDK CLI** — never blocks on a human, never treats
`insufficient_quota` as a waitable `rate_limit_exceeded` window, and resumes
safely across usage windows.

## What problem this solves

Codex sessions hit usage limits. A `codex exec` process exiting doesn't
tell you whether the *task* finished or just that *turn* did. And an HTTP
429 from OpenAI is two different failures behind one status code:
`rate_limit_exceeded` / `usage_limit_reached` are windows that reset on
their own; `insufficient_quota` / `credit_balance_exhausted` are billing
walls that never will, no matter how long you wait. OpenAI's own guidance
is not to retry the second kind.

`codexloop` exists to get all three of those distinctions right,
automatically, so you can hand it a plan and walk away — including noticing
a top-up or a plan-window reset on the next probe rather than at some fixed
deadline.

It is a deliberate transplant of the [claudeloop](https://github.com/adammatthewsteinberger/claudeloop)
design — same state machine, same ports, same run-directory layout —
retargeted at the OpenAI stack. The primary transport is `codex exec --json`
as a subprocess, which is exactly what the official TypeScript Codex SDK does
under the hood ([ADR 0002](https://adammatthewsteinberger.github.io/codexloop/architecture/adr/0002-subprocess-codex-exec/)).
There is **no Anthropic dependency**.

## Install

Requires **Python 3.12+**, **macOS or Linux**, and the
[Codex CLI](https://github.com/openai/codex) (`codex` ≥ 0.40 on `PATH`)
signed in via `codex login` **or** an `OPENAI_API_KEY`. Windows is not a
supported target.

```bash
pipx install codexloop
codexloop doctor      # reports which auth mode is active; it never guesses
```

See the [getting-started guide](https://adammatthewsteinberger.github.io/codexloop/getting-started/)
for a from-source setup.

## Quickstart

```bash
codexloop doctor                        # codex version, login status, probe strategies, MCP OAuth
codexloop capacity                      # ChatGPT plan windows when known; says so honestly when not
codexloop run plan.md --max-turns 20    # seed a run from a markdown plan and drive it to completion
codexloop run plan.md --network-access  # trusted task that needs PostgreSQL/HTTP access
codexloop resume --last                 # or: codexloop resume <thread-id>
codexloop threads                       # this product's run registry (not vendor Codex sessions)
codexloop api models list               # any OpenAI SDK endpoint (generated; see docs)

# Mid-run control (second terminal, same cwd):
codexloop status
codexloop logs
codexloop prompt --now "Also cover the error path"   # or --next-turn
codexloop model <model>                              # queued for the next control boundary
codexloop effort high                                # low | medium | high
codexloop approval never                             # approval policy
codexloop sandbox workspace-write                    # sandbox mode
codexloop watch --follow                             # or --replay for the Textual stream UI
codexloop stop                                       # graceful stop at the next control boundary
codexloop wind-down --reason "capacity exhausted"    # finish the turn, write a handoff, exit
codexloop savepoints
codexloop unwind 1                                   # git save-point restore (refuses while live)
```

`--transport app-server` opts into the experimental Codex app-server protocol
and falls back to `exec` when it is unavailable
([ADR 0009](https://adammatthewsteinberger.github.io/codexloop/architecture/adr/0009-optional-app-server/)).

Network access remains off by default in the `workspace-write` sandbox. Enable
it per invocation with `--network-access`, per process with
`CODEXLOOP_NETWORK_ACCESS=true`, or in `codexloop.toml` with
`network_access = true`. This permits outbound command networking generally; it
is not a localhost- or PostgreSQL-only allowlist. Use it only for trusted tasks.
Runs record the effective `sandbox_mode` and `network_access` values in
`.codexloop/runs/<run_id>/meta.json`. Because the app-server transport cannot
currently express this setting, CodexLoop uses the exec transport whenever it
is enabled.

## Why it's different from just retrying on 429

| | Naive retry | `codexloop` |
|---|---|---|
| Sees an HTTP 429 | Sleeps a fixed duration, retries | Classifies **body-first** — `error.code` / `error.type` before the status: `rate_limit_exceeded` and `slow_down` are short throttles, `usage_limit_reached` is a plan window, `insufficient_quota` / `credit_balance_exhausted` / `usage_not_included` are billing walls |
| Credits exhausted | Sleeps forever, no reset time exists | `CreditsExhausted` structurally has no `resets_at` field. Probes on a bounded backoff and tells you it needs you |
| Plan window (5-hour / weekly) | Guesses a sleep | Reads `Retry-After` / plan-window resets when the vendor supplies them; degrades to a bounded probe under `--max-wait`, never a blind sleep |
| Turn ends vs. task ends | A marker string, easily confused with a truncated limit message | Structured verdict via `codex exec --output-schema`, done marker (`CODEXLOOP_TASK_FULLY_COMPLETE`) as fallback, and *no signal is never completion* |
| Approval prompts | Hangs, or you reach for `--full-auto` (deprecated, then removed) | `-c approval_policy=never` **plus** `-c sandbox_mode=workspace-write` — non-blocking *and* confined; `danger-full-access` only behind a loud opt-in |
| Bare `codex` TUI | Waits on a TTY | Never invoked; the argv builder forbids it and the child is spawned with stdin closed |

See the [architecture overview](https://adammatthewsteinberger.github.io/codexloop/architecture/)
and [ADR 0003 — credits exhausted](https://adammatthewsteinberger.github.io/codexloop/architecture/adr/0003-credits-exhausted/)
for the full reasoning.

## Documentation

Full docs (built with MkDocs Material) live at
**https://adammatthewsteinberger.github.io/codexloop/**. The same content
is in the [`docs/`](https://github.com/adammatthewsteinberger/codexloop/tree/develop/docs) directory on GitHub.

| | |
|---|---|
| [Getting started](https://adammatthewsteinberger.github.io/codexloop/getting-started/) | Install, preflight, first run, transports |
| [Generated REST surface](https://adammatthewsteinberger.github.io/codexloop/guides/rest-api-surface/) | `codexloop api …` — 1:1 over the `openai` SDK resource tree, `--provider openai\|azure\|custom`, drift gate |
| [Architecture](https://adammatthewsteinberger.github.io/codexloop/architecture/) | The onion layers and the twelve [decision records](https://adammatthewsteinberger.github.io/codexloop/architecture/adr/) |
| [CLI reference](https://adammatthewsteinberger.github.io/codexloop/reference/cli/) | Command index |
| [Contributing](https://adammatthewsteinberger.github.io/codexloop/contributing/) / [Publishing](https://adammatthewsteinberger.github.io/codexloop/publishing/) | Setup, tests, coverage floors, TestPyPI → PyPI Trusted Publishing |
| [Plans](https://github.com/adammatthewsteinberger/codexloop/tree/develop/docs/plans) | Design record, vendor research notes, and the shared transplant outline (GitHub tree; not in the site nav) |
| [Changelog](https://github.com/adammatthewsteinberger/codexloop/blob/develop/CHANGELOG.md) | Release notes, maintained by release-please |

## Project status

Pre-1.0, but functional through milestone **M5**: onion core, `codex exec`
gateway, layered capacity probe (exec floor + optional app-server + rollout
tail), control plane, generated OpenAI REST CLI with a drift gate, and the
optional app-server transport with exec fallback. Later releases added the
`-v`/`-q` verbosity ladder, `--run-id`, wind-down, and capacity forecasting
(measurement only, off by default). Coverage floor is **100%** for the whole
package. `pytest -m system` runs a scripted agent with no OpenAI account;
`pytest -m live` is opt-in.

| Item | Value |
|---|---|
| Env prefix | `CODEXLOOP_*` |
| State dir | `.codexloop/runs/<run_id>/` |
| Auth | `OPENAI_API_KEY` **or** `codex login` (`$CODEX_HOME/auth.json`) — never mixed |
| Done marker | `CODEXLOOP_TASK_FULLY_COMPLETE` |
| Effort levels | `low` / `medium` / `high` (Codex `model_reasoning_effort`) |

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](https://github.com/adammatthewsteinberger/codexloop/blob/develop/CONTRIBUTING.md) for the
gitflow branch model, Conventional Commits requirement, and how to run every
quality gate locally.

The GitHub default branch is **`develop`**. Open feature PRs into `develop`,
not `main`. By contributing you agree that your work is licensed under the
same MIT License as the rest of this repository, and that you will follow
the [Code of Conduct](https://github.com/adammatthewsteinberger/codexloop/blob/develop/CODE_OF_CONDUCT.md).

Agent guidance is mirrored across:

- [CLAUDE.md](https://github.com/adammatthewsteinberger/codexloop/blob/develop/CLAUDE.md) + [`.claude/skills/`](https://github.com/adammatthewsteinberger/codexloop/tree/develop/.claude/skills/) (Claude Code)
- [`.cursor/rules/`](https://github.com/adammatthewsteinberger/codexloop/tree/develop/.cursor/rules/) (Cursor)
- [AGENTS.md](https://github.com/adammatthewsteinberger/codexloop/blob/develop/AGENTS.md) + [`.agents/skills/`](https://github.com/adammatthewsteinberger/codexloop/tree/develop/.agents/skills/) (Codex)
- [GEMINI.md](https://github.com/adammatthewsteinberger/codexloop/blob/develop/GEMINI.md) + [`.agent/rules/`](https://github.com/adammatthewsteinberger/codexloop/tree/develop/.agent/rules/) (Antigravity)

## Getting help

| I want to... | Go here |
|---|---|
| Read the docs | https://adammatthewsteinberger.github.io/codexloop/ |
| Ask a question | [Discussions](https://github.com/adammatthewsteinberger/codexloop/discussions) |
| Report a bug or request a feature | [Issues](https://github.com/adammatthewsteinberger/codexloop/issues) (use the templates) |
| Report a vulnerability | [SECURITY.md](https://github.com/adammatthewsteinberger/codexloop/blob/develop/SECURITY.md) (private) |

See [SUPPORT.md](https://github.com/adammatthewsteinberger/codexloop/blob/develop/SUPPORT.md)
for the same map.

## Security

This tool runs Codex with `approval_policy=never` by design (that's what
makes autonomous operation possible), confines it to `sandbox_mode=workspace-write`
by default, and handles OpenAI credentials. See
[SECURITY.md](https://github.com/adammatthewsteinberger/codexloop/blob/develop/SECURITY.md)
for the threat model and how to report a vulnerability.

## Related projects

Same contract, different vendor. The four `*loop` runners share one domain
state machine, one set of application ports, and one `.<name>loop/runs/<id>/`
layout — pick the one that matches the agent you pay for:

| Runner | Drives | Install |
|---|---|---|
| [claudeloop](https://github.com/adammatthewsteinberger/claudeloop) | Claude Code (Anthropic) | `pipx install claudeloop` |
| **codexloop** (this repo) | OpenAI Codex / GPT | `pipx install codexloop` |
| [cursorloop](https://github.com/adammatthewsteinberger/cursorloop) | Cursor Agent (Composer-first; Grok as a model profile) | `pipx install cursorloop` |
| [agyloop](https://github.com/adammatthewsteinberger/agyloop) | Google Antigravity / Gemini | `pipx install agyloop` |

Around them:

- [vibey](https://github.com/adammatthewsteinberger/vibey) — queue-based, six-phase conductor (spec interview → design → build → review → deploy) that drives the four runners as interchangeable engines. PostgreSQL-backed.
- [vibey-bootstrap](https://github.com/adammatthewsteinberger/vibey-bootstrap) — Azure Functions cross-cutting layer: App Config + Key Vault + App Insights bootstrap, Service Bus plumbing, scaffold CLI.
- [vibey-skills](https://github.com/adammatthewsteinberger/vibey-skills) — versioned Agent Skills marketplace and deterministic context-packet engine.
- [homebrew-tap](https://github.com/adammatthewsteinberger/homebrew-tap) — `brew tap adammatthewsteinberger/tap`.

## License

MIT — see [LICENSE](https://github.com/adammatthewsteinberger/codexloop/blob/develop/LICENSE).

---

Built by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com) · [more open source](https://vibewithadam.matthewsteinberger.com/open-source)
