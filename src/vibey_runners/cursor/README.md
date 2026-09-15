# cursorloop

[![PyPI](https://img.shields.io/pypi/v/cursorloop)](https://pypi.org/project/cursorloop/)
[![PyPI downloads](https://img.shields.io/pypi/dm/cursorloop)](https://pypi.org/project/cursorloop/)
[![Python versions](https://img.shields.io/pypi/pyversions/cursorloop)](https://pypi.org/project/cursorloop/)
[![CI](https://github.com/adammatthewsteinberger/cursorloop/actions/workflows/ci.yml/badge.svg)](https://github.com/adammatthewsteinberger/cursorloop/actions/workflows/ci.yml)
[![Docs](https://github.com/adammatthewsteinberger/cursorloop/actions/workflows/release-surfaces.yml/badge.svg)](https://adammatthewsteinberger.github.io/cursorloop/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/adammatthewsteinberger/cursorloop/blob/develop/LICENSE)

**Onion-architected, autonomous Cursor Agent session runner** — Composer-first
(`composer-2.5`; Grok is a secondary model profile, not a product). Never
blocks on a human, distinguishes a waitable rate-limit window from
non-waitable exhausted credits, and resumes safely across usage windows.

## What problem this solves

Cursor Agent sessions hit usage limits. A single agent turn ending doesn't
tell you whether the *task* finished or just that *turn* did. And when
Cursor rejects you, you can't tell from the outside whether waiting will
ever help — a rate-limit window resets on its own; an exhausted credits
balance never will, no matter how long you wait. Cursor does not publish a
stable credits discriminator on its `RateLimitError`, so cursorloop keeps a
configurable billing lexicon and, when a signal is ambiguous, **biases toward
`CreditsExhausted`** — the failure mode is a spurious "top up" notification,
never a hang past a fabricated reset.

`cursorloop` exists to get all three of those distinctions right,
automatically, so you can hand it a plan and walk away.

It is a deliberate transplant of the [claudeloop](https://github.com/adammatthewsteinberger/claudeloop)
design — same state machine, same ports, same run-directory layout —
retargeted onto the Cursor Agent SDK (`cursor-sdk`). There is **no Anthropic
dependency** and no foreign vendor auth env fallback.

## Install

Requires **Python 3.12+**, **macOS or Linux**, and a Cursor account with
`CURSOR_API_KEY` set for live runs. Windows is not a supported target.

```bash
pipx install cursorloop
cursorloop doctor            # --offline skips the live me / models calls
```

See the [installation guide](https://adammatthewsteinberger.github.io/cursorloop/getting-started/installation/)
for a from-source setup.

## Quickstart

```bash
cursorloop doctor                          # fail-fast preflight before a multi-hour unattended run
cursorloop run --plan plan.md              # seed a Cursor Agent from a plan and run to completion
cursorloop resume --agent-id <id>          # continue an existing agent
cursorloop models                          # composer-fast → composer → grok-4.5 → grok → grok-xhigh, plus router-* aliases
cursorloop agents                          # local agents for a workspace (needs a live client)
cursorloop whoami                          # authenticated Cursor account

# Mid-run control (second terminal, same cwd):
cursorloop status
cursorloop logs
cursorloop prompt "Also cover the error path"   # queued for the next turn
cursorloop watch                                # plain-text tail; --ui opens the Textual view
cursorloop hooks status                         # install | restore | diff the autonomy fragment
cursorloop stop                                 # soft stop
cursorloop wind-down                            # finish the turn, write a handoff marker, exit 75
cursorloop savepoints
cursorloop unwind --to <sha-or-ref>
cursorloop reset                                # restore managed hooks after a crashed run
```

`cursorloop cloud me|models|create|get|cancel` is a **partial** Cloud Agents
REST surface ([ADR-0006](https://adammatthewsteinberger.github.io/cursorloop/architecture/decisions/0006-cloud-agents-rest-surface/));
full generation waits on a digest-stable published OpenAPI document.

## Why it's different from just retrying on 429

| | Naive retry | `cursorloop` |
|---|---|---|
| Sees a rate-limit error | Sleeps a fixed duration, retries | Classifies *why* — a waitable window (bounded probe under `--max-wait`) or exhausted credits that only a human can fix; ambiguity resolves toward credits ([ADR-0005](https://adammatthewsteinberger.github.io/cursorloop/architecture/decisions/0005-ambiguity-biases-credits/)) |
| Credits exhausted | Sleeps forever, no reset time exists | `CreditsExhausted` has no `resets_at`. Probes on a bounded backoff and tells you it needs you |
| Vendor changes an error string | Silent misclassification | Configurable billing lexicon; unmatched terminal errors land in the audit log; `doctor --explain-error <payload>` classifies them offline ([ADR-0004](https://adammatthewsteinberger.github.io/cursorloop/architecture/decisions/0004-billing-lexicon-configurable/)) |
| Turn ends vs. task ends | A marker string, easily confused with a truncated limit message | Four-tier verdict: a `cursorloop-verdict` fenced block, done marker (`CURSORLOOP_TASK_FULLY_COMPLETE`), empty-turn soft-fail, plan-checkbox reconciliation. A capacity rejection outranks any completion claim |
| Agent asks a question | Hangs — Cursor has no `can_use_tool` callback | Managed `.cursor/hooks.json` autonomy fragment + preamble + `local.force` + a stall watchdog. Hooks are hash-verified and restored afterward; a mid-run user edit wins ([ADR-0008](https://adammatthewsteinberger.github.io/cursorloop/architecture/decisions/0008-hash-verified-hooks-restore/)) |

See [rate limits and credits](https://adammatthewsteinberger.github.io/cursorloop/guides/rate-limits-and-credits/)
and [never blocking](https://adammatthewsteinberger.github.io/cursorloop/guides/never-blocking/)
for the full reasoning.

## Documentation

Full docs (built with MkDocs Material) live at
**https://adammatthewsteinberger.github.io/cursorloop/**. The same content
is in the [`docs/`](https://github.com/adammatthewsteinberger/cursorloop/tree/develop/docs) directory on GitHub.

| | |
|---|---|
| [Getting started](https://adammatthewsteinberger.github.io/cursorloop/getting-started/installation/) | Install, quickstart, configuration |
| [Guides](https://adammatthewsteinberger.github.io/cursorloop/guides/autonomous-runs/) | Autonomous runs, rate limits and credits, never blocking, completion detection, [model profiles](https://adammatthewsteinberger.github.io/cursorloop/guides/model-profiles/), [logging](https://adammatthewsteinberger.github.io/cursorloop/guides/logging-and-observability/), [cloud agents](https://adammatthewsteinberger.github.io/cursorloop/guides/cloud-agents/) |
| [Architecture](https://adammatthewsteinberger.github.io/cursorloop/architecture/overview/) | The onion layers, the domain model, the run-loop state machine, and ten [decision records](https://adammatthewsteinberger.github.io/cursorloop/architecture/decisions/0001-onion-architecture/) |
| [CLI reference](https://adammatthewsteinberger.github.io/cursorloop/reference/cli/) | `cursorloop --help` and `cursorloop --man` |
| [Contributing](https://adammatthewsteinberger.github.io/cursorloop/contributing/development/) | Development setup, testing, docs, [release](https://adammatthewsteinberger.github.io/cursorloop/contributing/release/) |
| [Plans](https://github.com/adammatthewsteinberger/cursorloop/tree/develop/docs/plans) | Design record, vendor research notes, and the shared transplant outline (GitHub tree; not in the site nav) |
| [Changelog](https://github.com/adammatthewsteinberger/cursorloop/blob/develop/CHANGELOG.md) | Release notes, versions derived and published by vibey-gh at promotion |

## Project status

Pre-1.0, but functional through the M5 milestone: Typer CLI (`run` /
`resume` / `doctor` / mid-run control), bootstrap that auto-launches
`CursorClient.launch_bridge`, a full offline-capable doctor checklist, a
deterministic `pytest -m system` harness (scripted agent, no Cursor account),
a partial-but-live Cloud Agents surface, a CLI-fallback gateway, and mirrored
agent skills. Later releases added the `-v`/`-q` verbosity ladder, `--run-id`,
wind-down, and capacity forecasting (measurement only, off by default).
Coverage floor is **100%** on every layer — domain, application,
infrastructure, and CLI.

| Item | Value |
|---|---|
| Env prefix | `CURSORLOOP_*` |
| Auth | `CURSOR_API_KEY` (never an `ANTHROPIC_*` fallback) |
| State dir | `.cursorloop/runs/<run_id>/` |
| Done marker | `CURSORLOOP_TASK_FULLY_COMPLETE` |
| Model ladder | `composer-fast → composer → grok-4.5 → grok → grok-xhigh` (or `router-cost → router-balanced → router-intelligence`); default `composer-2.5` |
| Test-agent gate | `CURSORLOOP_ALLOW_TEST_AGENT=1` **and** `CURSORLOOP_TEST_AGENT_SCRIPT=<path>` |

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](https://github.com/adammatthewsteinberger/cursorloop/blob/develop/CONTRIBUTING.md) for the
gitflow branch model, Conventional Commits requirement, and how to run every
quality gate locally.

The GitHub default branch is **`develop`**. Open feature PRs into `develop`.
By contributing you agree that your work is licensed under the same MIT
License as the rest of this repository, and that you will follow the
[Code of Conduct](https://github.com/adammatthewsteinberger/cursorloop/blob/develop/CODE_OF_CONDUCT.md).

Agent guidance is mirrored across:

- [CLAUDE.md](https://github.com/adammatthewsteinberger/cursorloop/blob/develop/CLAUDE.md) + [`.claude/skills/`](https://github.com/adammatthewsteinberger/cursorloop/tree/develop/.claude/skills/) (Claude Code)
- [CURSOR.md](https://github.com/adammatthewsteinberger/cursorloop/blob/develop/CURSOR.md) + [`.cursor/rules/`](https://github.com/adammatthewsteinberger/cursorloop/tree/develop/.cursor/rules/) (Cursor)
- [AGENTS.md](https://github.com/adammatthewsteinberger/cursorloop/blob/develop/AGENTS.md) + [`.agents/skills/`](https://github.com/adammatthewsteinberger/cursorloop/tree/develop/.agents/skills/) (Codex)
- [GEMINI.md](https://github.com/adammatthewsteinberger/cursorloop/blob/develop/GEMINI.md) + [`.agent/rules/`](https://github.com/adammatthewsteinberger/cursorloop/tree/develop/.agent/rules/) (Antigravity)

## Getting help

| I want to... | Go here |
|---|---|
| Read the docs | https://adammatthewsteinberger.github.io/cursorloop/ |
| Ask a question | [Discussions](https://github.com/adammatthewsteinberger/cursorloop/discussions) |
| Report a bug or request a feature | [Issues](https://github.com/adammatthewsteinberger/cursorloop/issues) (use the templates) |
| Report a vulnerability | [SECURITY.md](https://github.com/adammatthewsteinberger/cursorloop/blob/develop/SECURITY.md) (private) |

See [SUPPORT.md](https://github.com/adammatthewsteinberger/cursorloop/blob/develop/SUPPORT.md)
for the same map.

## Security

This tool merges an autonomy fragment into `.cursor/hooks.json` for the
duration of a run (restored afterward, hash-verified), edits the working tree
without waiting on a human, and handles `CURSOR_API_KEY`. See
[SECURITY.md](https://github.com/adammatthewsteinberger/cursorloop/blob/develop/SECURITY.md)
for the threat model and how to report a vulnerability.

## Related projects

Same contract, different vendor. The four `*loop` runners share one domain
state machine, one set of application ports, and one `.<name>loop/runs/<id>/`
layout — pick the one that matches the agent you pay for:

| Runner | Drives | Install |
|---|---|---|
| [claudeloop](https://github.com/adammatthewsteinberger/claudeloop) | Claude Code (Anthropic) | `pipx install claudeloop` |
| [codexloop](https://github.com/adammatthewsteinberger/codexloop) | OpenAI Codex / GPT | `pipx install codexloop` |
| **cursorloop** (this repo) | Cursor Agent (Composer-first; Grok as a model profile) | `pipx install cursorloop` |
| [agyloop](https://github.com/adammatthewsteinberger/agyloop) | Google Antigravity / Gemini | `pipx install agyloop` |

Around them:

- [vibey](https://github.com/adammatthewsteinberger/vibey) — queue-based, six-phase conductor (spec interview → design → build → review → deploy) that drives the four runners as interchangeable engines. PostgreSQL-backed.
- [vibey-bootstrap](https://github.com/adammatthewsteinberger/vibey-bootstrap) — Azure Functions cross-cutting layer: App Config + Key Vault + App Insights bootstrap, Service Bus plumbing, scaffold CLI.
- [vibey-skills](https://github.com/adammatthewsteinberger/vibey-skills) — versioned Agent Skills marketplace and deterministic context-packet engine.
- [homebrew-tap](https://github.com/adammatthewsteinberger/homebrew-tap) — `brew tap adammatthewsteinberger/tap`.

## License

MIT — see [LICENSE](https://github.com/adammatthewsteinberger/cursorloop/blob/develop/LICENSE).

---

Built by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com) · [more open source](https://vibewithadam.matthewsteinberger.com/open-source)
