# agyloop

[![PyPI](https://img.shields.io/pypi/v/agyloop)](https://pypi.org/project/agyloop/)
[![PyPI downloads](https://img.shields.io/pypi/dm/agyloop)](https://pypi.org/project/agyloop/)
[![Python versions](https://img.shields.io/pypi/pyversions/agyloop)](https://pypi.org/project/agyloop/)
[![CI](https://github.com/adammatthewsteinberger/agyloop/actions/workflows/ci.yml/badge.svg)](https://github.com/adammatthewsteinberger/agyloop/actions/workflows/ci.yml)
[![Docs](https://github.com/adammatthewsteinberger/agyloop/actions/workflows/docs.yml/badge.svg)](https://adammatthewsteinberger.github.io/agyloop/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/adammatthewsteinberger/agyloop/blob/develop/LICENSE)

**Onion-architected, autonomous Google Antigravity / Gemini session runner
and generated Gemini REST CLI** — never blocks on a human, never treats
billing or daily-quota exhaustion as a short waitable RPM blip, and resumes
safely across usage windows.

## What problem this solves

Antigravity / Gemini sessions hit usage limits. A single turn ending doesn't
tell you whether the *task* finished or just that *turn* did. And a
`429 RESOURCE_EXHAUSTED` doesn't tell you whether waiting will help: an
RPM / TPM window resets in a minute; an RPD window waits until the next
Pacific midnight; a spend cap or exhausted credits never grows a reset
timestamp, no matter how long you wait.

`agyloop` exists to get all of those distinctions right, automatically, so
you can hand it a plan and walk away — including noticing a top-up on the
next probe rather than at some fixed deadline.

It is a deliberate transplant of the [claudeloop](https://github.com/adammatthewsteinberger/claudeloop)
design — same state machine, same ports, same run-directory layout —
retargeted onto the `google-antigravity` SDK, with a live `agy` CLI as an
optional second gateway. There is **no Anthropic dependency**.

## Install

Requires **Python 3.12+** and **macOS or Linux**. Auth is **either**
`GOOGLE_API_KEY` (Gemini Developer API) **or** Application Default
Credentials with a Vertex / Enterprise flag — `agyloop doctor` reports which
lane is active; it never guesses
([ADR 0011](https://adammatthewsteinberger.github.io/agyloop/architecture/decisions/0011-doctor-never-guesses-auth-lane/)).
Windows is not a supported target.

```bash
pipx install agyloop
agyloop doctor
```

See the [installation guide](https://adammatthewsteinberger.github.io/agyloop/getting-started/installation/)
for a from-source setup and the TestPyPI dry-run.

## Quickstart

```bash
agyloop doctor                  # pre-flight: auth lane, no interactive hooks
agyloop run handoff.md          # seed a session from a plan and run unattended
agyloop resume --last           # resume the most recent .agyloop/ run
agyloop resume --conversation <id>
agyloop sessions                # local .agyloop/runs registry only
agyloop api --help              # any Gemini REST endpoint (generated; --lane vertex for the Vertex subset)

# Mid-run control (second terminal, same cwd):
agyloop status
agyloop logs
agyloop prompt --now "Also cover the error path"   # or --at-break
agyloop preset high             # low | medium | high (model + effort)
agyloop model medium            # alias or raw Gemini model id
agyloop attach ./notes.md
agyloop watch --stream          # Textual token stream; --replay for history
agyloop snapshot
agyloop stop                    # soft-stop the active run
agyloop savepoints
agyloop unwind --to 1           # git save-point restore (refuses while a run is active)
```

Pace cold Enterprise runs with `--ramp N`. Drive a live `agy` binary with
`--gateway cli`. Bound a run with `--max-turns`, `--max-wait`, `--max-tokens`
or a labeled `--max-dollars` estimate
([ADR 0009](https://adammatthewsteinberger.github.io/agyloop/architecture/decisions/0009-budgets-are-token-denominated/)).

## Why it's different from just retrying on 429

| | Naive retry | `agyloop` |
|---|---|---|
| Sees `429 RESOURCE_EXHAUSTED` | Sleeps a fixed duration, retries | Classifies *which* exhaustion: RPM / TPM / IPM window (short probe cadence), RPD window (next Pacific midnight, not a short sleep), credits / spend / billing cap (no clock reset — probe until a human tops up), or auth failure (abort) |
| Credits exhausted | Sleeps forever, no reset time exists | `CreditsExhausted` has no `resets_at`. Probes on a bounded backoff and tells you it needs you |
| Daily quota | Guesses a sleep, or hammers a dead window | `--no-probe` waits only to computed quota boundaries and issues zero probe requests |
| Turn ends vs. task ends | A marker string, easily confused with a truncated limit message | Structured completion via Antigravity, done marker (`AGYLOOP_TASK_FULLY_COMPLETE`) as fallback. A capacity rejection always outranks a completion claim |
| Model asks a clarifying question | Hangs waiting on stdin, or fabricates an answer | `ask_question` is denied with guidance so the model proceeds on a stated, auditable assumption; interactive SDK hooks are never registered ([ADR 0007](https://adammatthewsteinberger.github.io/agyloop/architecture/decisions/0007-deny-ask-question-with-guidance/)) |
| Sandbox vs. skip-permissions | `--sandbox --dangerously-skip-permissions` silently neuters the sandbox | Never emitted together; `--unsafe-skip-permissions` is a CLI-adapter-only opt-in that refuses root and non-git cwds ([ADR 0008](https://adammatthewsteinberger.github.io/agyloop/architecture/decisions/0008-never-skip-permissions-with-sandbox/), [antigravity-cli#36](https://github.com/google-antigravity/antigravity-cli/issues/36)) |

See [rate limits vs. credits](https://adammatthewsteinberger.github.io/agyloop/guides/rate-limits-and-credits/)
and [never blocking on a human](https://adammatthewsteinberger.github.io/agyloop/guides/never-blocking/)
for the full reasoning.

## Documentation

Full docs (built with MkDocs Material) live at
**https://adammatthewsteinberger.github.io/agyloop/**. The same content
is in the [`docs/`](https://github.com/adammatthewsteinberger/agyloop/tree/develop/docs) directory on GitHub.

| | |
|---|---|
| [Getting started](https://adammatthewsteinberger.github.io/agyloop/getting-started/installation/) | Install, quickstart, configuration |
| [Usage](https://adammatthewsteinberger.github.io/agyloop/usage/) | Operator reference: capacity model, permissions, flags |
| [Guides](https://adammatthewsteinberger.github.io/agyloop/guides/rate-limits-and-credits/) | Rate limits vs. credits, never blocking, [the generated REST surface](https://adammatthewsteinberger.github.io/agyloop/guides/rest-api-surface/) |
| [Decision records](https://adammatthewsteinberger.github.io/agyloop/architecture/decisions/0001-onion-architecture/) | Why each hard call was made — onion, five-member `CapacityState`, quota-aware probes, generated REST with a drift gate |
| [Contributing](https://adammatthewsteinberger.github.io/agyloop/contributing/development/) | Development setup, [release process](https://adammatthewsteinberger.github.io/agyloop/contributing/release-process/) |
| [Plans](https://github.com/adammatthewsteinberger/agyloop/tree/develop/docs/plans) | Design record, vendor research notes, and the shared transplant outline (GitHub tree; not in the site nav) |
| [Changelog](https://github.com/adammatthewsteinberger/agyloop/blob/develop/CHANGELOG.md) | Release notes, maintained by release-please |

## Project status

Pre-1.0, but functional through milestone **M5**: pure domain core,
autonomous runner, adaptive waiting for Gemini quotas, `agy` CLI gateway,
git savepoints, ops CLI, and a generated Developer + Vertex REST CLI with a
drift gate ([ADR 0015](https://adammatthewsteinberger.github.io/agyloop/architecture/decisions/0015-generated-gemini-rest-with-drift-gate/)).
Coverage floor is **100%** on every layer — domain, application,
infrastructure, and CLI. `pytest -m system` runs a scripted agent against
real FS / git / control with no Google account.

| Item | Value |
|---|---|
| Env prefix | `AGYLOOP_*` |
| Auth | `GOOGLE_API_KEY` **or** ADC + Vertex / Enterprise flag |
| State dir | `.agyloop/runs/<run_id>/` |
| Done marker | `AGYLOOP_TASK_FULLY_COMPLETE` |
| Effort levels | `low` / `medium` / `high` / `xhigh` / `max`; presets `low` / `medium` / `high` map to `gemini-flash-lite-latest` / `gemini-2.5-flash` / `gemini-2.5-pro` |

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](https://github.com/adammatthewsteinberger/agyloop/blob/develop/CONTRIBUTING.md) for the
gitflow branch model, Conventional Commits requirement, and how to run every
quality gate locally.

The GitHub default branch is **`develop`**. Open feature PRs into `develop`,
not `main`. By contributing you agree that your work is licensed under the
same MIT License as the rest of this repository, and that you will follow
the [Code of Conduct](https://github.com/adammatthewsteinberger/agyloop/blob/develop/CODE_OF_CONDUCT.md).

Agent guidance is mirrored across:

- [CLAUDE.md](https://github.com/adammatthewsteinberger/agyloop/blob/develop/CLAUDE.md) + [`.claude/skills/`](https://github.com/adammatthewsteinberger/agyloop/tree/develop/.claude/skills/) (Claude Code)
- [`.cursor/rules/`](https://github.com/adammatthewsteinberger/agyloop/tree/develop/.cursor/rules/) (Cursor)
- [AGENTS.md](https://github.com/adammatthewsteinberger/agyloop/blob/develop/AGENTS.md) + [`.agents/skills/`](https://github.com/adammatthewsteinberger/agyloop/tree/develop/.agents/skills/) (Codex)
- [GEMINI.md](https://github.com/adammatthewsteinberger/agyloop/blob/develop/GEMINI.md) + [`.agent/rules/`](https://github.com/adammatthewsteinberger/agyloop/tree/develop/.agent/rules/) (Antigravity)

## Getting help

| I want to... | Go here |
|---|---|
| Read the docs | https://adammatthewsteinberger.github.io/agyloop/ |
| Ask a question | [Discussions](https://github.com/adammatthewsteinberger/agyloop/discussions) |
| Report a bug or request a feature | [Issues](https://github.com/adammatthewsteinberger/agyloop/issues) (use the templates) |
| Report a vulnerability | [SECURITY.md](https://github.com/adammatthewsteinberger/agyloop/blob/develop/SECURITY.md) (private) |

See [SUPPORT.md](https://github.com/adammatthewsteinberger/agyloop/blob/develop/SUPPORT.md)
for the same map.

## Security

This tool grants tool autonomy by default (`allow_all()` + workspace scope +
destructive-command denies; `--safe` narrows, `--yolo` widens), never
registers interactive SDK hooks, and handles Google credentials. See
[SECURITY.md](https://github.com/adammatthewsteinberger/agyloop/blob/develop/SECURITY.md)
for the threat model, the sandbox + skip-permissions footgun, and how to
report a vulnerability.

## Related projects

Same contract, different vendor. The four `*loop` runners share one domain
state machine, one set of application ports, and one `.<name>loop/runs/<id>/`
layout — pick the one that matches the agent you pay for:

| Runner | Drives | Install |
|---|---|---|
| [claudeloop](https://github.com/adammatthewsteinberger/claudeloop) | Claude Code (Anthropic) | `pipx install claudeloop` |
| [codexloop](https://github.com/adammatthewsteinberger/codexloop) | OpenAI Codex / GPT | `pipx install codexloop` |
| [cursorloop](https://github.com/adammatthewsteinberger/cursorloop) | Cursor Agent (Composer-first; Grok as a model profile) | `pipx install cursorloop` |
| **agyloop** (this repo) | Google Antigravity / Gemini | `pipx install agyloop` |

Around them:

- [vibey](https://github.com/adammatthewsteinberger/vibey) — queue-based, six-phase conductor (spec interview → design → build → review → deploy) that drives the four runners as interchangeable engines. PostgreSQL-backed.
- [vibey-bootstrap](https://github.com/adammatthewsteinberger/vibey-bootstrap) — Azure Functions cross-cutting layer: App Config + Key Vault + App Insights bootstrap, Service Bus plumbing, scaffold CLI.
- [vibey-skills](https://github.com/adammatthewsteinberger/vibey-skills) — versioned Agent Skills marketplace and deterministic context-packet engine.
- [homebrew-tap](https://github.com/adammatthewsteinberger/homebrew-tap) — `brew tap adammatthewsteinberger/tap`.

## License

MIT — see [LICENSE](https://github.com/adammatthewsteinberger/agyloop/blob/develop/LICENSE).

---

Built by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com) · [more open source](https://vibewithadam.matthewsteinberger.com/open-source)
