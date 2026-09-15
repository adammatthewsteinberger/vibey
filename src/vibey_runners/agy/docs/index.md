# agyloop

**Onion-architected, autonomous Google Antigravity / Gemini session runner** —
never blocks on a human, and never treats billing or daily-quota exhaustion as
a short waitable RPM blip.

## What problem this solves

Antigravity / Gemini sessions hit usage limits. A single turn ending does not
tell you whether the *task* finished. A `429 RESOURCE_EXHAUSTED` does not tell
you whether waiting will help: an RPM window resets; an RPD window waits until
the next Pacific midnight; a spend / credits cap never grows a reset timestamp.

`agyloop` exists to get those distinctions right, automatically, so you can
hand it a plan and walk away.

## Where to go next

| I want to... | Read |
|---|---|
| Install it and run the first session | [Installation](getting-started/installation.md) |
| See a short end-to-end | [Quickstart](getting-started/quickstart.md) |
| Set auth, env, and flags | [Configuration](getting-started/configuration.md) |
| Operator reference | [Usage](usage.md) |
| Understand RPM vs RPD vs credits | [Rate limits vs credits](guides/rate-limits-and-credits.md) |
| Understand why it never waits on stdin | [Never blocking](guides/never-blocking.md) |
| Call Gemini REST 1:1 | [Generated REST surface](guides/rest-api-surface.md) |
| See why a hard call was made | [ADR 0015](architecture/decisions/0015-generated-gemini-rest-with-drift-gate.md) |

## Project status

Public **0.2.0**. Install from [PyPI](https://pypi.org/project/agyloop/).
The core loop, resilient waiting, CLI gateway, git savepoints, generated
Developer REST CLI, and this documentation site ship in that release.

## License

MIT. See [Contributing](contributing/development.md) to work on the code.
