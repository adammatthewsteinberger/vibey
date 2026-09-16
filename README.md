# vibey

[![PyPI](https://img.shields.io/pypi/v/vibey)](https://pypi.org/project/vibey/)
[![PyPI downloads](https://img.shields.io/pypi/dm/vibey)](https://pypi.org/project/vibey/)
[![Python versions](https://img.shields.io/pypi/pyversions/vibey)](https://pypi.org/project/vibey/)
[![CI](https://github.com/the-vibey-project/vibey/actions/workflows/ci.yml/badge.svg)](https://github.com/the-vibey-project/vibey/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/the-vibey-project/vibey/blob/develop/LICENSE)
[![Docs](https://img.shields.io/badge/docs-read-blue.svg)](https://the-vibey-project.github.io/vibey/main/)
[![Research paper](https://img.shields.io/badge/paper-PDF%20%7C%20HTML-6f42c1.svg)](https://the-vibey-project.github.io/vibey/main/paper.pdf)
[![Book](https://img.shields.io/badge/book-PDF%20%7C%20EPUB-0a7ea4.svg)](https://the-vibey-project.github.io/vibey/main/book.pdf)

**Read it first:** the design is a research paper — [PDF](https://the-vibey-project.github.io/vibey/main/paper.pdf) · [HTML](https://the-vibey-project.github.io/vibey/main/paper/) —
and the whole documentation is a book — [PDF](https://the-vibey-project.github.io/vibey/main/book.pdf) · [EPUB](https://the-vibey-project.github.io/vibey/main/book.epub) · [print](https://the-vibey-project.github.io/vibey/main/book-print.html).

**You've used an AI coding agent. Then you babysat it** — re-prompting when it
lost the thread, re-explaining everything after a crash, copying results
between tools, watching a run die at 2am because one vendor's credits ran out.
The agent was autonomous; the *delivery* was you.

**Vibey is the layer that does the babysitting.** It's an orchestrator that
wraps AI coding agents so you're not managing sessions or threads by hand: you
describe what you want, it interviews you until the spec is sharp, builds
unattended across a pool of engines, brings you back only for the decisions
that are genuinely yours, and survives crashes and credit exhaustion without
losing a single open question.

**Never written code?** You can still read this. *Code* is text files of
instructions computers run; an *AI coding agent* is a program that writes and
edits that code from plain-English requests; *deploying* means putting the
finished software somewhere people can use it. Vibey's job is to manage a
team of those agents from your first description to deployed software, the
way a project manager runs a team — asking you questions up front, checking
the work, and only interrupting you when a decision is truly yours.

For the precise version: a queue-based, six-phase conductor for autonomous
software delivery — with an optional visual-design interstitial and opt-in
Azure deployment — built on top of the [`*loop` autonomous session
runners](src/vibey_runners/), which live in this repository as uv
workspace members (ADR-0021).

## What problem this solves

An autonomous coding session is not autonomous software delivery. A single
`claudeloop` run can finish a task, but it cannot interview you until the spec
is sharp, split the work into parallel items, verify each one against gates it
cannot game, survive its own credit exhaustion by handing off to a different
vendor's engine *without losing a single open question*, or know that a review
finding should reopen design rather than vanish into a transcript.

Vibey conducts all of that. You describe what you want; it interviews you until
the spec is sharp, builds unattended across a pool of engines with real budget
caps, reviews the result with you, and (only if you opt in) deploys. Every
choice, finding, and handoff lives in an append-only PostgreSQL ledger — never
in one vendor's chat session.

| | |
|---|---|
| Runs on | macOS / Linux, local. No cloud control plane required. |
| Language | Python 3.12+ |
| Queue | PostgreSQL (`FOR UPDATE SKIP LOCKED`) |
| Engines | [`claudeloop`](https://pypi.org/project/claudeloop/), [`codexloop`](https://pypi.org/project/codexloop/), [`cursorloop`](https://pypi.org/project/cursorloop/), [`agyloop`](https://pypi.org/project/agyloop/), plus the opt-in [`qwenloop`](https://pypi.org/project/qwenloop/) — a local standby engine and sovereign DESIGN provider (ADR-0015, ADR-0027). Sources: [`src/vibey_runners/`](src/vibey_runners/). |
| State dir | `.vibey/` |
| Env prefix | `VIBEY_` |
| Done marker | Each loop's own marker (`CLAUDELOOP_TASK_FULLY_COMPLETE`, `QWENLOOP_TASK_FULLY_COMPLETE`, etc.) |

## Install

Requires **Python 3.12+**, **PostgreSQL**, and at least one `*loop` engine on
PATH. Windows is not a supported target. Every database-backed command reads
the connection string from `VIBEY_PG_URL`; vibey never guesses a database and
exits with `VIBEY_PG_URL is not set` when it is missing.

```bash
uv tool install vibey          # or: pipx install vibey / pip install vibey
uv tool install claudeloop     # at least one engine; add codexloop, cursorloop, agyloop for rotation
export VIBEY_PG_URL=postgresql://user@localhost:5432/vibey
vibey doctor                   # pre-flight: engines installed, versions, auth
```

`vibey doctor` alone checks only the engines. `--record` also writes the result
to the database for a project, and `--cluster` runs the in-cluster preflight
(DSN, workspace, secrets, database, migrations) instead.

`qwenloop` is opt-in (`uv tool install qwenloop`). With
`VIBEY_FEATURE_QWENLOOP=1` set, the worker adds it as the standby engine and
`vibey doctor` lists it; `vibey doctor` also honours `[features] qwenloop = true`
in a `./vibey.toml`. Separately, `vibey worker --provider qwenloop` (or
`vibey work --provider qwenloop`) uses it for the DESIGN interview; BUILD
decomposition under that provider stays scripted.

To add deterministic, budgeted context packets from the independently versioned
`vibey-skills` marketplace, install the optional extra and enable it per project:

```bash
uv tool install 'vibey[skills]'
vibey new my-app --repo ~/src/my-app \
  --skills-context-mode shadow --skills-context-budget 6000
```

`shadow` builds and records packet provenance without changing agent prompts.
After observing results, switch the project config to `inject` to append successful
packets to BUILD prompts. Missing tools, timeouts, low-confidence retrieval, and
insufficient budgets all fall back to the original prompt. The feature is off by
default, and wind-down prompts are never modified (ADR-0031).

The same tree is a Claude Code plugin marketplace — every plugin in the family, the 127
skills plugins and vibey-gh's four, from one address and nothing else:

```text
/plugin marketplace add the-vibey-project/vibey
/plugin install security-principles@vibey
/plugin                                    # browse all 131
```

The root manifest is rendered from the workspace members by `vibey-gh marketplace` and
held to them by `vibey-gh check` (ADR-0034); it is never edited by hand. The PyPI package
`vibey-skills` still ships its own marketplace under the name `vibey-skills`, so both can
be registered side by side.

## Quickstart

```bash
export VIBEY_PG_URL=postgresql://user@localhost:5432/vibey
vibey new my-app --repo ~/src/my-app \
  --max-cycle-dollars 15                     # real budget brake, enforced from the ledger
vibey doctor --conformance --record          # verify each engine's contract, persist health for the latest project
vibey worker --provider claudeloop \
  --engines claudeloop,agyloop -j 2          # live DESIGN provider; unattended build across the pool

# When vibey parks for your input (design gates, review, budget grants):
vibey answer <gate-id> --defaults            # accept the interview defaults, or:
vibey answer <gate-id> --raw '{"max_dollars": 25}'   # raise a tripped budget cap
vibey design accept <project-id> --no-visual
vibey answer <gate-id> --verdict accept      # review demo
vibey answer <gate-id> --choice local_only   # decline deployment → DONE (local)
```

`vibey doctor --record` needs a project to record against, so run it after
`vibey new`. `vibey worker` defaults to `--provider scripted`, a test double;
pass `--provider claudeloop` for a live DESIGN interview and BUILD
decomposition (`qwenloop` gives a live, local DESIGN interview only). No
command prints open gate ids yet; read them from the `human_gate` table:

```bash
psql "$VIBEY_PG_URL" -c "SELECT gate_id, kind, prompt FROM human_gate
  WHERE project_id = '<project-id>' AND answered_at IS NULL ORDER BY raised_at"
```

The [greeter live-demo runbook](docs/guides/greeter-live-demo.md) walks a full
paid run end to end, including the zero-touch contracts.

## Command reference

Every command's flags and defaults are in the
[CLI reference](docs/reference/cli.md). The most common ones:

| Command | What it does |
|---|---|
| `vibey doctor` | Pre-flight: engine install state, versions, auth; `--conformance` runs the 9-check suite, `--record` persists health, `--cluster` runs the in-cluster preflight. |
| `vibey new` | Create a project and enqueue its first DESIGN interview. |
| `vibey worker` | Long-running worker: dispatches jobs across every phase (`--provider scripted\|claudeloop\|qwenloop`, `--engines`, `-j`, `--azure memory\|az`). |
| `vibey work` | Process one ready DESIGN or VISUAL_DESIGN job for a project (foreground, capped). |
| `vibey answer` | Answer a parked human gate. |
| `vibey design resume/accept` / `vibey visual accept/waive` | Resume or accept DESIGN; accept or waive VISUAL_DESIGN. |
| `vibey watch` / `vibey status` | Live dashboard, or one-shot status (`--json` for scripting). |
| `vibey engines` / `vibey cost` / `vibey ledger show` | Engine health, budget spend, and event-ledger inspection. |
| `vibey deploy status/inspect/plan/cancel/rollback` | Inspect and control Phases ④–⑥. |
| `vibey recover` | Recover jobs stuck under a dead worker's lease. |
| `vibey operator` | Run the Kubernetes operator (`pip install 'vibey[operator]'`; ADR-0025). |

## Configuration

`vibey.toml`'s schema — `[project]`, `[isolation]`, `[budget]`, `[engines]`,
`[phases.design/build/review]`, `[provision]`, `[deploy]`, `[features]`,
`[qwenloop]` — is fully implemented and unit-tested in
`domain/config.py`/`infrastructure/config_loader.py`, with defaults and an
example file in the [configuration reference](docs/reference/configuration.md).
**Only one key is read at runtime today:** `[features] qwenloop = true`.
`vibey doctor` reads it from `./vibey.toml` in the current directory, and the
worker reads the same key from the project's stored config (which no CLI flag
sets yet); `VIBEY_FEATURE_QWENLOOP` overrides both. No other table is read by
`cli/`, `bootstrap.py`, the worker, or the operator —
`infrastructure/config_loader.py` is exercised only by its tests — so setting
any other key has no effect. Treat the rest the same as
`infrastructure/notify/` and `infrastructure/otel.py` below:
implemented-and-tested, not yet an active runtime path.

What does configure a project today is a handful of `vibey new` CLI flags
(`--max-cycles`, `--max-cycle-dollars`, `--max-cycle-turns`,
`--skills-context-mode`, `--skills-context-budget`) recorded directly into
that project's stored config at creation time — see the
[CLI reference](docs/reference/cli.md).

## Notifications

`infrastructure/notify/` implements a `NotificationService` that dispatches
desktop alerts and HMAC-SHA256-signed webhooks (`X-Vibey-Signature`, see
[SECURITY.md](SECURITY.md#6-webhook-payload-integrity--implemented-and-unit-tested-not-yet-an-active-runtime-path)), and it is covered
by tests. It is **not yet wired into `bootstrap.py`, the worker, or the
CLI** — no flag or `vibey.toml` key constructs it today. Treat it as
implemented-and-tested, not yet an active runtime path.

## Telemetry

`infrastructure/otel.py` implements `TelemetryTracer` (span tracing for
jobs, turns, and handoffs) and `TelemetryMetrics` (engine-selection,
queue-latency, phase-duration, handoff-failure, and cost-spend counters),
plus `calculate_rotation_fairness()` for measuring rotation fairness against
declared engine weights. It is covered by unit tests. Like `notify/`, it is
**not constructed by `bootstrap.py`** and has no CLI flag or `vibey.toml`
key wiring it into a running worker — treat it as implemented-and-tested,
not yet an active runtime path.

## The shape of it

```
  DELIVERY STAGE SET
  INTAKE → ① DESIGN ──┬─ no ───────────────→ ② BUILD ⇄ ③ REVIEW
             ▲        │                       autonomous / interactive
             │        └─ yes → [VISUAL DESIGN]
             │                  interactive, media generation + confirmation
             │                            │ visual-ready
             │                            └──────────────→ ② BUILD
             │
             └─ loop-back from ② BUILD or ③ REVIEW: a finding needs clarification

  ③ REVIEW ── no deployment ─────────────────────────────→ DONE (local)
       │ opt in
       ▼
  DEPLOYMENT STAGE SET
  ④ DEPLOY DESIGN → ⑤ DEPLOY EXECUTE → ⑥ DEPLOY REVIEW → DONE (deployed)
       interactive       autonomous          interactive
             ▲                 ▲                    │
             └─────────────────┴────────────────────┘
                  ⑥ can also route a defect back to ①, ②, or ③
```

**The six phases** — ① Design · ② Build · ③ Review · ④ Deploy Design ·
⑤ Deploy Execute · ⑥ Deploy Review. The circled numbers above are these;
**bold** below means the phase talks to you.

**① Design** → ② Build → **③ Review** → **④ Deploy Design** → ⑤ Deploy Execute → **⑥ Deploy Review**

Phases 1, 3, 4, and 6 talk to you. The optional Visual Design stage also talks to
you and cannot hand work to BUILD until every planned visual is accepted or you
explicitly waive the stage. Phases 2 and 5 run unattended, survive rate-limit
windows and credit exhaustion, and rotate eligible engines/providers when one
runs dry. Phase 3 asks whether to deploy; "no" is a successful local completion.
Phase 6 accepts a successful deployment, requests changed deployment details in
Phase 4, retries an unambiguous deployment in Phase 5, or routes an application
defect back to the appropriate delivery phase.

## Why it isn't just another agent framework

The hard part is not calling an LLM in a loop — `claudeloop` and its siblings
already solve that, including the distinction between a waitable rate-limit
window and exhausted credits that no amount of waiting will fix. Vibey adds the
things those runners deliberately do not do:

1. **A phase machine with loop-backs**, so a review finding becomes a new design
   conversation rather than a lost note.
2. **Round-robin engine rotation with lossless handoff** — the conversation is an
   append-only event ledger, not a chat transcript locked inside one vendor's
   session, so any engine can pick up where any other left off. A handoff that
   would lose an open question, decision, assumption, or finding is rejected by
   a pure, deterministic no-loss gate — never silently accepted.
3. **A durable queue**, so work survives a laptop lid closing, a crash, or a
   provider outage, and so multiple work items build in parallel in isolated
   git worktrees.
4. **Real money brakes** — per-cycle dollar and turn caps summed from the
   ledger's own cost events, with parks that tell you the exact command to
   grant more.

## Documentation

| Document | What's in it |
|---|---|
| [Architecture map](docs/project.mmd) | Comprehensive Mermaid diagram: every layer, the six phases, the ledger/handoff data flow, the security boundary, and the release channels |
| [Research paper](https://the-vibey-project.github.io/vibey/main/paper/) · [PDF](https://the-vibey-project.github.io/vibey/main/paper.pdf) | *Ledger-Mediated Orchestration: Vendor-Independent Autonomous Software Delivery over a Pool of Coding Agents* — the ledger invariant, queue semantics, gate soundness, and vendor independence, stated formally |
| [The book](https://the-vibey-project.github.io/vibey/main/book.pdf) · [EPUB](https://the-vibey-project.github.io/vibey/main/book.epub) · [print HTML](https://the-vibey-project.github.io/vibey/main/book-print.html) | Every page of the documentation site, in reading order, as one downloadable book |
| [CLI reference](docs/reference/cli.md) | Every command, subcommand, flag, and default |
| [Configuration reference](docs/reference/configuration.md) | The full `vibey.toml` schema, with defaults and an example file |
| [Kubernetes guide](docs/guides/kubernetes.md) | Container, Helm chart, KEDA autoscaling, and its own troubleshooting section |
| [Greeter live-demo runbook](docs/guides/greeter-live-demo.md) | A full paid run, end to end, with the zero-touch contracts |
| [Expansion runbooks](docs/runbooks/expansion/) | 21 workstreams: JIRA, more clouds, Kubernetes server mode, clients, store submissions, … |
| [Architecture & roadmap](docs/plans/architecture-and-roadmap.md) | The master design: context, containers, layers, phases, risks, milestones |
| [Domain model](docs/plans/domain-model.md) | Every value object, ADT, and invariant in `domain/` |
| [Data model](docs/plans/data-model.md) | Full PostgreSQL DDL, queue semantics, indices |
| [Handoff protocol](docs/plans/handoff-protocol.md) | The event ledger, the envelope, and the no-loss gate |
| [Rotation & engines](docs/plans/rotation-and-engines.md) | Capability matrix, effort normalization, smooth weighted round robin |
| [Phase protocols](docs/plans/phase-protocols.md) | What all six phases do, turn by turn |
| [Implementation plan](docs/plans/implementation-plan.md) | Milestone-by-milestone, test-first task breakdown |
| [CLAUDE.md](CLAUDE.md) | The short facts file every coding agent working on vibey loads first: non-negotiables, layer map, gate commands |
| [Decision records](docs/architecture/decisions/) | Why each hard call was made (34 ADRs) |

## Status

**Live-validated.** The full pipeline has conducted real paid deliveries end to
end: multi-worker builds (`-j 2`) with cross-engine rotation (claudeloop
implements, agyloop verifies), the bounded verify-repair ladder, budget caps
tripping and being granted live, and fully zero-touch DESIGN phases answered
with nothing but `--defaults`. The validation campaign's findings — a blind
budget brake, a repair-loop livelock, terminal gate-command failures — were
each fixed and re-validated live.

Every architectural layer (`domain`, `application`, `infrastructure`, `cli`)
holds a **100% branch-coverage floor**, enforced as four separate CI gates
(ADR-0023); the absorbed runner and tool packages keep their own gates (ADR-0022).
`domain/` is pure stdlib, enforced by import-linter and an AST-walking purity
test — the no-loss handoff gate is deterministic code, not a model's opinion.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `vibey doctor` reports an engine `NOT INSTALLED` | The `*loop` binary isn't on `PATH`. | `uv tool install claudeloop` (or codexloop/cursorloop/agyloop/qwenloop), then re-run `vibey doctor`. |
| `VIBEY_PG_URL is not set` | No database connection string in the environment. | `export VIBEY_PG_URL=postgresql://user@localhost:5432/vibey`, pointing at a database you own. |
| `vibey doctor` reports `auth FAIL` | The engine's own vendor credentials aren't configured. | Run that engine's own login/auth flow, then re-run `vibey doctor --conformance`. |
| `vibey worker` logs `no recorded conformance for ...` | `vibey doctor --conformance --record` has never passed for that engine on this project. | Run it before starting the worker; engine-driven jobs won't select an unrecorded engine. |
| A project is parked and nothing progresses | A human gate (interview, review verdict, budget cap) is waiting. | `vibey status <project-id>` shows an `AWAITING_HUMAN` count in the queue depth, but no command prints the gate id or prompt yet. Read them with `psql "$VIBEY_PG_URL" -c "SELECT gate_id, kind, prompt FROM human_gate WHERE project_id = '<project-id>' AND answered_at IS NULL ORDER BY raised_at"`, then `vibey answer <gate-id> ...`. |
| Jobs sit `leased` after a worker crash | The lease hasn't expired yet, or nothing has reclaimed it. | `vibey recover --project <id>` (or `--all`) sets them back to `ready`. |
| Budget cap trips mid-cycle | The project's `max_cycle_dollars` / `max_cycle_turns` cap (set by `vibey new --max-cycle-dollars` / `--max-cycle-turns`) was exceeded — by design. | `vibey answer <gate-id> --raw '{"max_dollars": 25}'` (or `{"max_turns": N}`) to grant more, or accept the park. |
| Kubernetes-specific issues | — | See the [Kubernetes guide's Troubleshooting section](docs/guides/kubernetes.md#troubleshooting). |

## Upgrading

Vibey is pre-1.0: minor versions may change `vibey.toml` fields, ledger
event shapes, or CLI flags. Before upgrading:

1. Read [CHANGELOG.md](CHANGELOG.md) for the versions between your current
   version and the target.
2. Re-run `vibey doctor --conformance --record` afterward — engine
   contracts and conformance checks can gain new checks between releases.
3. The database schema migrates automatically
   (`infrastructure/db/migrator.py`); no manual migration step is needed.

Every push to `develop` publishes a uniquely versioned dev build (`X.Y.Z.devN`)
to TestPyPI as `vibey-dev`; every push to `main` publishes `vibey` to PyPI.
After a successful `main` release, `github-release.yml` tags that exact commit
and creates the matching GitHub Release. Versioning and release are owned by
the in-tree `vibey-gh`; release-please is retired (ADR-0028). `uv tool install
vibey` (or `pipx install vibey` / `pip install vibey`) tracks stable releases.

## Formal notes

For the reader who wants the theory under the phases. Work items form a queue
$Q$ in PostgreSQL; workers claim with `SELECT ... FOR UPDATE SKIP LOCKED`, so
claims serialize per item without global locks: for any item $w$, at most one
worker holds $w$ at any instant, while throughput scales with
$\min(|Q|, \text{workers})$. The conductor is a six-phase state machine
$\Sigma = \langle D, B, R, D_d, D_e, D_r \rangle$ (design, build, review,
deploy-design, deploy-execute, deploy-review) with human gates exactly at
$\{D, R, D_d, D_r\}$ — interactive phases are the fixed points where the
ledger's open questions must drain to zero before the transition fires.
Crash recovery follows from two invariants: every decision, finding, and
handoff is a row in an append-only ledger *before* it takes effect
(write-ahead intent), and engine handoff re-derives session context from the
ledger alone — so vendor credit exhaustion is a scheduling event, not a loss
of state: $\text{state}(t) = f(\text{ledger}_{\leq t})$, independent of any
vendor session. The full treatment — with the queue-fairness argument and the gate-soundness
proof sketch — is the research paper, *Ledger-Mediated Orchestration: Vendor-Independent Autonomous Software Delivery over a Pool of Coding Agents*:
[read it online](https://the-vibey-project.github.io/vibey/main/paper/) or [download the PDF](https://the-vibey-project.github.io/vibey/main/paper.pdf)
(source: [`docs/paper.md`](docs/paper.md)). The complete documentation is also a book:
[PDF](https://the-vibey-project.github.io/vibey/main/book.pdf) · [EPUB](https://the-vibey-project.github.io/vibey/main/book.epub) · [print HTML](https://the-vibey-project.github.io/vibey/main/book-print.html).

## Project links

| | |
|---|---|
| Contributing | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Security policy | [SECURITY.md](SECURITY.md) |
| Getting help | [SUPPORT.md](SUPPORT.md) |
| Code of Conduct | [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) |
| Changelog | [CHANGELOG.md](CHANGELOG.md) |

## Related projects

These packages live in this repository as uv workspace members
(`src/vibey_runners/*`, `src/vibey_tools/*`; ADR-0021) and are published to
PyPI under their own names. Their former standalone GitHub repositories no
longer exist.

| Project | Source | What it is |
|---|---|---|
| [claudeloop](https://pypi.org/project/claudeloop/) | [`src/vibey_runners/claude`](src/vibey_runners/claude) | Autonomous Claude Code session runner — the design the family transplants |
| [codexloop](https://pypi.org/project/codexloop/) | [`src/vibey_runners/codex`](src/vibey_runners/codex) | The same design retargeted onto OpenAI Codex |
| [cursorloop](https://pypi.org/project/cursorloop/) | [`src/vibey_runners/cursor`](src/vibey_runners/cursor) | The same design retargeted onto Cursor |
| [agyloop](https://pypi.org/project/agyloop/) | [`src/vibey_runners/agy`](src/vibey_runners/agy) | The same design retargeted onto Google Antigravity / Gemini |
| [qwenloop](https://pypi.org/project/qwenloop/) | [`src/vibey_runners/qwen`](src/vibey_runners/qwen) | The same design on a local Qwen 2.5 Coder model (llama.cpp or vLLM) — the opt-in standby engine and sovereign DESIGN provider |
| [vibey-skills](https://pypi.org/project/vibey-skills/) | [`src/vibey_tools/skills`](src/vibey_tools/skills) | The Agent Skills marketplace (a Claude Code plugin marketplace) behind `vibey[skills]` and its context packets |
| [vibey-gh](https://pypi.org/project/vibey-gh/) | [`src/vibey_tools/gh`](src/vibey_tools/gh) | Provenance fingerprints, derived version bumps, a merge train, and branch realignment; it owns vibey's own release (ADR-0028) |
| [vibey-bootstrap](https://pypi.org/project/vibey-bootstrap/) | [`src/vibey_tools/bootstrap`](src/vibey_tools/bootstrap) | Azure bootstrap library for App Configuration, Key Vault, and App Insights integration |

## License

[MIT](LICENSE) © [Adam Matthew Steinberger](https://github.com/adammatthewsteinberger)

---

**The short version, again**: agents can code, but delivery still meant
babysitting them — Vibey is the layer that does the babysitting, from sharp
spec to deployed software, without losing a single open question.

**Your next step**: install it and let it interview you —

```bash
uv tool install vibey && uv tool install claudeloop && vibey doctor
```

**Prefer to read first?** The design is a [research paper](https://the-vibey-project.github.io/vibey/main/paper/)
([PDF](https://the-vibey-project.github.io/vibey/main/paper.pdf)), and the whole documentation is a [book](https://the-vibey-project.github.io/vibey/main/book.pdf)
([EPUB](https://the-vibey-project.github.io/vibey/main/book.epub)).
