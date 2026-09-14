# claudeloop

**Onion-architected, autonomous Claude Code session runner and full Anthropic
SDK CLI** — never blocks on a human, distinguishes an exhausted rate-limit
window from exhausted credits, and resumes safely across usage windows.

## What problem this solves

Claude Code sessions hit usage limits. A `claude -p` invocation ending
doesn't tell you whether the *task* finished or just that *turn* did. And
when a rate limit rejects you, you can't tell from the outside whether
waiting will ever help — a five-hour window will reset on its own; an
exhausted credits balance never will, no matter how long you wait.

`claudeloop` exists to get all three of those distinctions right,
automatically, so you can hand it a plan and walk away — including handling
the case where you top up your account's credits while it's mid-wait.

## Where to go next

| I want to... | Read |
|---|---|
| Install it and run my first autonomous session | [Getting started](getting-started/installation.md) |
| Understand how rate limits and credits are told apart | [Rate limits vs. credits](guides/rate-limits-and-credits.md) |
| Understand why it can never get stuck waiting on me | [Never blocking](guides/never-blocking.md) |
| Operate mid-run (attachments, permissions, chat, …) | [Run resources and chat ops](guides/run-resources-and-chat-ops.md) |
| See the full system design | [Architecture overview](architecture/overview.md) |
| See *why* a specific hard call was made | [Architecture decision records](architecture/decisions/0001-onion-architecture-with-import-linter.md) |
| Contribute code | [Development guide](contributing/development.md) |
| See the original plans this project was built from | [Plans](plans/architecture-and-roadmap.md) |

## Project status

Pre-1.0. Milestones **M1–M5 are complete** (pure domain core, autonomous
runner, resilient waiting, generated REST surface, polish). An **ops
control plane** on top of that core provides mid-run stop/prompt/logs,
model/effort, permissions/cwd, run-scoped resources (attachments, skills,
MCP), memories/artifacts, chat metadata, and response actions. See
[architecture overview](architecture/overview.md) for the living status;
historical plans under [`plans/`](plans/architecture-and-roadmap.md) are
preserved design records.

## Supported platforms

**macOS and Linux.** Python 3.10–3.13. Windows is not a supported target —
see [installation](getting-started/installation.md#requirements).

## Getting help

| I want to... | Go here |
|---|---|
| Contribute code | [Development guide](contributing/development.md) and [CONTRIBUTING.md](https://github.com/adammatthewsteinberger/claudeloop/blob/develop/CONTRIBUTING.md) |
| Ask a question | [GitHub Discussions](https://github.com/adammatthewsteinberger/claudeloop/discussions) |
| Report a bug or request a feature | [Issues](https://github.com/adammatthewsteinberger/claudeloop/issues) (templated; blank issues are off) |
| Report a vulnerability | [SECURITY.md](https://github.com/adammatthewsteinberger/claudeloop/blob/develop/SECURITY.md) |
| Same map, shorter | [SUPPORT.md](https://github.com/adammatthewsteinberger/claudeloop/blob/develop/SUPPORT.md) |

## License

MIT. See [LICENSE](https://github.com/adammatthewsteinberger/claudeloop/blob/main/LICENSE).

Participation is governed by the
[Code of Conduct](https://github.com/adammatthewsteinberger/claudeloop/blob/develop/CODE_OF_CONDUCT.md).
