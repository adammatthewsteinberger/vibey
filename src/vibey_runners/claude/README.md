# claudeloop

> **Now part of the vibey monorepo.** `claudeloop` lives in [the-vibey-project/vibey](https://github.com/the-vibey-project/vibey) at [`src/vibey_runners/claude`](https://github.com/the-vibey-project/vibey/tree/develop/src/vibey_runners/claude) (vibey ADR-0021). It is still published on PyPI as [`claudeloop`](https://pypi.org/project/claudeloop/).

[![PyPI](https://img.shields.io/pypi/v/claudeloop)](https://pypi.org/project/claudeloop/)
[![PyPI downloads](https://img.shields.io/pypi/dm/claudeloop)](https://pypi.org/project/claudeloop/)
[![Python versions](https://img.shields.io/pypi/pyversions/claudeloop)](https://pypi.org/project/claudeloop/)
[![CI](https://github.com/the-vibey-project/vibey/actions/workflows/ci.yml/badge.svg)](https://github.com/the-vibey-project/vibey/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_runners/claude/LICENSE)

**Onion-architected, autonomous Claude Code session runner and full Anthropic
SDK CLI** — never blocks on a human, distinguishes an exhausted rate-limit
window from exhausted credits, and resumes safely across usage windows.

## What problem this solves

Claude Code sessions hit usage limits. A `claude -p` invocation ending
doesn't tell you whether the *task* finished or just that *turn* did. And
when a rate limit rejects you, you can't tell from the outside whether
waiting will ever help — a five-hour window resets on its own; an exhausted
credits balance never will, no matter how long you wait.

`claudeloop` exists to get all three of those distinctions right,
automatically, so you can hand it a plan and walk away — including handling
the case where you top up your account's credits while it's mid-wait, which
it notices on the next probe rather than at some fixed deadline.

This project began as [`legacy/claude_autoresume.py`](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_runners/claude/legacy/claude_autoresume.py),
a single-file script that did this by shelling out to `claude -p` and
regex-scraping its output. `claudeloop` replaces that with a tested,
typed, onion-architected package built on the official `claude-agent-sdk`.
See the [architecture decision records](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_runners/claude/docs/architecture/decisions/0001-onion-architecture-with-import-linter.md) for why
each specific change was made.

## Install

Requires **Python 3.10+**, **macOS or Linux**, and the
[Claude Code CLI](https://code.claude.com) installed and authenticated.
Windows is not a supported target.

```bash
pipx install claudeloop
```

See the [installation guide](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_runners/claude/docs/getting-started/installation.md)
for requirements and a from-source setup.

## Quickstart

```bash
claudeloop doctor                # pre-flight checks before a long unattended run
claudeloop run handoff.md        # seed a session from a plan file and run to completion
claudeloop resume                # resume whatever you were last working on
claudeloop resume --session-id <id>
claudeloop api models list       # any Anthropic SDK endpoint (generated; see docs)

# Mid-run control (second terminal, same cwd):
claudeloop status
claudeloop snapshot              # handoff JSON under .claudeloop/runs/<id>/snapshots/
claudeloop logs -f --chatter
claudeloop prompt --now "Also cover the error path"
claudeloop preset high           # or: model / effort (low|medium|high|xhigh|max)
claudeloop permission-mode plan  # mid-run; default at start is always bypass
claudeloop attach ./notes.md
claudeloop response retry
claudeloop watch --stream        # Textual live stream; --replay for history
claudeloop stop                  # soft-stop → stop-summary.md (exit 130)
claudeloop savepoints
claudeloop unwind --to 1         # after stop; git save-point restore
```

Ops surface (attachments, skills/MCP, memories, chat metadata, slash commands):
[run resources and chat ops](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_runners/claude/docs/guides/run-resources-and-chat-ops.md).

## Why it's different from just retrying on 429

| | Naive retry | `claudeloop` |
|---|---|---|
| Sees an HTTP 429 | Sleeps a fixed duration, retries | Classifies *why* — a waitable rate-limit window, or exhausted credits that only a human can fix |
| Credits exhausted | Sleeps forever, no reset time exists | Probes on a bounded backoff and tells you it needs you |
| A credit top-up arrives mid-wait | Not noticed until the fixed sleep ends | Noticed on the next scheduled probe |
| Turn ends vs. task ends | No structured signal — a marker string, easily confused with a truncated limit message | Structured per-turn JSON verdict, with the legacy marker kept only as a fallback |
| Asked a clarifying question | Hangs waiting for stdin, or fabricates an answer | Denies the tool call with guidance, so the model proceeds on a stated, auditable assumption |

See [rate limits vs. credits](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_runners/claude/docs/guides/rate-limits-and-credits.md)
and [never blocking on a human](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_runners/claude/docs/guides/never-blocking.md) for the
full reasoning.

## Documentation

Full docs (MkDocs Material sources) live in the
[`docs/`](https://github.com/the-vibey-project/vibey/tree/develop/src/vibey_runners/claude/docs) directory of the vibey monorepo, starting at
[`docs/index.md`](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_runners/claude/docs/index.md). The standalone `claudeloop` Pages site has been retired.

| | |
|---|---|
| [Getting started](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_runners/claude/docs/getting-started/installation.md) | Install, quickstart, configuration |
| [Guides](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_runners/claude/docs/guides/autonomous-runs.md) | How autonomous runs work, rate limits vs. credits, never blocking, completion detection, [logging](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_runners/claude/docs/guides/logging-and-observability.md), [run resources and chat ops](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_runners/claude/docs/guides/run-resources-and-chat-ops.md) |
| [Architecture](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_runners/claude/docs/architecture/overview.md) | The onion layers, the domain model, the run-loop state machine |
| [Decision records](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_runners/claude/docs/architecture/decisions/0001-onion-architecture-with-import-linter.md) | Why each hard call was made |
| [Contributing](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_runners/claude/docs/contributing/development.md) | Development setup, testing philosophy, release process |
| [Plans](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_runners/claude/docs/plans/architecture-and-roadmap.md) | The original approved plans this project was built from |
| [Changelog](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_runners/claude/CHANGELOG.md) | Release notes (entries up to 2026-08 were written by release-please, which vibey ADR-0028 retired) |

## Project status

Pre-1.0, but functional through milestone **M5**. The CLI above genuinely
works — `run`/`resume` drive Claude Code through `claude-agent-sdk`,
`sessions` and `doctor` run against your environment, and **`claudeloop api`**
exposes a generated 1:1 Anthropic SDK REST surface with a CI drift gate.
`domain`/`application` carry a CI-enforced 100% test-coverage gate, with a
live test suite (`tests/live/`) exercising the installed console script.
`run` / `resume` log to stderr twice — a human-readable stream and a JSON
line stream — controlled by `--log-level`; see
[logging and observability](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_runners/claude/docs/guides/logging-and-observability.md).
See the [architecture roadmap](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_runners/claude/docs/plans/architecture-and-roadmap.md).

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_runners/claude/CONTRIBUTING.md) for the
gitflow branch model, Conventional Commits requirement, and how to run every
quality gate locally.

The GitHub default branch is **`develop`**. Open feature PRs into `develop`,
not `main`. By contributing you agree that your work is licensed under the
same MIT License as the rest of this repository, and that you will follow
the [Code of Conduct](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_runners/claude/CODE_OF_CONDUCT.md).

Agent guidance is mirrored across:

- [CLAUDE.md](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_runners/claude/CLAUDE.md) + [`.claude/skills/`](https://github.com/the-vibey-project/vibey/tree/develop/src/vibey_runners/claude/.claude/skills/) (Claude Code)
- [`.cursor/rules/`](https://github.com/the-vibey-project/vibey/tree/develop/src/vibey_runners/claude/.cursor/rules/) (Cursor)
- [AGENTS.md](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_runners/claude/AGENTS.md) + [`.agents/skills/`](https://github.com/the-vibey-project/vibey/tree/develop/src/vibey_runners/claude/.agents/skills/) (Codex)
- [GEMINI.md](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_runners/claude/GEMINI.md) + [`.agent/rules/`](https://github.com/the-vibey-project/vibey/tree/develop/src/vibey_runners/claude/.agent/rules/) (Antigravity)

## Getting help

| I want to... | Go here |
|---|---|
| Read the docs | [`docs/`](https://github.com/the-vibey-project/vibey/tree/develop/src/vibey_runners/claude/docs) |
| Ask a question | [Discussions](https://github.com/the-vibey-project/vibey/discussions) |
| Report a bug or request a feature | [Issues](https://github.com/the-vibey-project/vibey/issues) (use the templates) |
| Report a vulnerability | [SECURITY.md](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_runners/claude/SECURITY.md) (private) |

See [SUPPORT.md](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_runners/claude/SUPPORT.md)
for the same map.

## Security

This tool bypasses Claude Code's interactive permission prompts by design
(that's what makes autonomous operation possible) and handles API
credentials. See [SECURITY.md](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_runners/claude/SECURITY.md) for the threat model and how
to report a vulnerability.

## Related projects

Same contract, different vendor. The four `*loop` runners share one domain
state machine, one set of application ports, and one `.<name>loop/runs/<id>/`
layout — pick the one that matches the agent you pay for:

| Runner | Drives | Install |
|---|---|---|
| **claudeloop** (this package) | Claude Code (Anthropic) | `pipx install claudeloop` |
| [codexloop](https://github.com/the-vibey-project/vibey/tree/develop/src/vibey_runners/codex) | OpenAI Codex / GPT | `pipx install codexloop` |
| [cursorloop](https://github.com/the-vibey-project/vibey/tree/develop/src/vibey_runners/cursor) | Cursor Agent (Composer-first; Grok as a model profile) | `pipx install cursorloop` |
| [agyloop](https://github.com/the-vibey-project/vibey/tree/develop/src/vibey_runners/agy) | Google Antigravity / Gemini | `pipx install agyloop` |

Around them:

- [vibey](https://github.com/the-vibey-project/vibey) — queue-based, six-phase conductor (spec interview → design → build → review → deploy) that drives these four runners as interchangeable engines, plus [qwenloop](https://github.com/the-vibey-project/vibey/tree/develop/src/vibey_runners/qwen) as an opt-in fifth (vibey ADR-0015). PostgreSQL-backed. Background reading: the [vibey research paper](https://the-vibey-project.github.io/vibey/main/paper/) ([PDF](https://the-vibey-project.github.io/vibey/main/paper.pdf)) and the vibey book ([PDF](https://the-vibey-project.github.io/vibey/main/book.pdf), [EPUB](https://the-vibey-project.github.io/vibey/main/book.epub), [print HTML](https://the-vibey-project.github.io/vibey/main/book-print.html)).
- [vibey-bootstrap](https://github.com/the-vibey-project/vibey/tree/develop/src/vibey_tools/bootstrap) — Azure Functions cross-cutting layer: App Config + Key Vault + App Insights bootstrap, Service Bus plumbing, scaffold CLI.
- [vibey-skills](https://github.com/the-vibey-project/vibey/tree/develop/src/vibey_tools/skills) — versioned Agent Skills marketplace and deterministic context-packet engine.
- [homebrew-tap](https://github.com/adammatthewsteinberger/homebrew-tap) — `brew tap adammatthewsteinberger/tap`.

## License

MIT — see [LICENSE](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_runners/claude/LICENSE).

---

Built by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com) · [more open source](https://vibewithadam.matthewsteinberger.com/open-source)
