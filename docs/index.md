# vibey

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

For the precise version: a queue-based, six-phase conductor for autonomous
software delivery — with an optional visual-design interstitial and opt-in
Azure deployment — built on top of the [`*loop` autonomous session
runners](https://github.com/adammatthewsteinberger/claudeloop).

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
| Engines | [`claudeloop`](https://github.com/adammatthewsteinberger/claudeloop), [`codexloop`](https://github.com/adammatthewsteinberger/codexloop), [`cursorloop`](https://github.com/adammatthewsteinberger/cursorloop), [`agyloop`](https://github.com/adammatthewsteinberger/agyloop) |
| State dir | `.vibey/` |
| Env prefix | `VIBEY_` |
| Done marker | Each loop's own marker (CLAUDELOOP_TASK_FULLY_COMPLETE, etc.) |

## Install

Requires **Python 3.12+**, **PostgreSQL**, and at least one `*loop` engine on
PATH. Windows is not a supported target.

```bash
uv tool install vibey          # or: pipx install vibey / pip install vibey
uv tool install claudeloop     # at least one engine; add codexloop, cursorloop, agyloop for rotation
vibey doctor                   # pre-flight: database, engines, auth
```

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
default, and wind-down prompts are never modified.

## Quickstart

```bash
vibey doctor --conformance --record          # verify each engine's contract, persist health
vibey new my-app --repo ~/src/my-app \
  --max-cycle-dollars 15                     # real budget brake, enforced from the ledger
vibey worker --engines claudeloop,agyloop -j 2   # unattended build across the pool

# When vibey parks for your input (design gates, review, budget grants):
vibey answer <gate-id> --defaults            # accept the interview defaults, or:
vibey answer <gate-id> --raw '{"max_dollars": 25}'   # raise a tripped budget cap
vibey design accept <project-id> --no-visual
vibey answer <gate-id> --verdict accept      # review demo
vibey answer <gate-id> --choice local_only   # decline deployment → DONE (local)
```

The [greeter live-demo runbook](guides/greeter-live-demo.md) walks a full
paid run end to end, including the zero-touch contracts.

## Command reference

Every command's flags and defaults are in the
[CLI reference](reference/cli.md). The most common ones:

| Command | What it does |
|---|---|
| `vibey doctor` | Pre-flight: engine auth, versions, optional conformance suite. |
| `vibey new` | Create a project and enqueue its first DESIGN interview. |
| `vibey worker` | Long-running worker: dispatches jobs across every phase. |
| `vibey work` | Process one ready DESIGN job (foreground, capped). |
| `vibey answer` | Answer a parked human gate. |
| `vibey design` / `vibey visual` | Resume/accept DESIGN; accept/waive VISUAL_DESIGN. |
| `vibey watch` / `vibey status` | Live dashboard, or one-shot status (`--json` for scripting). |
| `vibey engines` / `vibey cost` / `vibey ledger show` | Engine health, budget spend, and event-ledger inspection. |
| `vibey deploy status/inspect/plan/cancel/rollback` | Inspect and control Phases ④–⑥. |
| `vibey recover` | Recover jobs stuck under a dead worker's lease. |
| `vibey operator` | Run the Kubernetes operator (`pip install 'vibey[operator]'`). |

## Configuration

`vibey.toml`'s schema — `[project]`, `[isolation]`, `[budget]`, `[engines]`,
`[phases.design/build/review]`, `[provision]`, `[deploy]`, `[features]`,
`[qwenloop]` — is fully implemented and unit-tested in
`domain/config.py`/`infrastructure/config_loader.py`, with defaults and an
example file in the [configuration reference](reference/configuration.md).
**It is not yet wired into any command** — no code path in `cli/`,
`bootstrap.py`, the worker, or the operator ever reads a `vibey.toml` file
from disk, so writing one today has no effect. Treat it the same as
`infrastructure/notify/` below: implemented-and-tested, not yet an active
runtime path.

What does configure a project today is a handful of `vibey new` CLI flags
(`--max-cycles`, `--max-cycle-dollars`, `--max-cycle-turns`,
`--skills-context-mode`, `--skills-context-budget`) recorded directly into
that project's stored config at creation time — see the
[CLI reference](reference/cli.md).

## Notifications

`infrastructure/notify/` implements a `NotificationService` that dispatches
desktop alerts and HMAC-SHA256-signed webhooks (`X-Vibey-Signature`, see
[SECURITY.md](https://github.com/adammatthewsteinberger/vibey/blob/main/SECURITY.md#6-webhook-payload-integrity)),
and it is covered by tests. It is **not yet wired into `bootstrap.py`, the
worker, or the CLI** — no flag or `vibey.toml` key constructs it today.
Treat it as implemented-and-tested, not yet an active runtime path.

## The shape of it

```
  DELIVERY STAGE SET
  INTAKE → ① DESIGN ──┬─ no ───────────────→ ② BUILD ⇄ ③ REVIEW
                      │                       autonomous / interactive
                      └─ yes → [VISUAL DESIGN]
                                interactive, media generation + confirmation
                                          │ visual-ready
                                          └──────────────→ ② BUILD

  ③ REVIEW ── no deployment ─────────────────────────────→ DONE (local)
       │ opt in
       ▼
  DEPLOYMENT STAGE SET
  ④ DEPLOY DESIGN ⇄ ⑤ DEPLOY EXECUTE ⇄ ⑥ DEPLOY REVIEW → DONE (deployed)
       interactive       autonomous          interactive
             ▲                 │                    │
             └─────────────────┴────────────────────┘
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
| [Architecture map](https://github.com/adammatthewsteinberger/vibey/blob/main/docs/project.mmd) | Comprehensive Mermaid diagram: every layer, the six phases, the ledger/handoff data flow, the security boundary, and the release channels |
| [CLI reference](reference/cli.md) | Every command, subcommand, flag, and default |
| [Configuration reference](reference/configuration.md) | The full `vibey.toml` schema, with defaults and an example file |
| [Kubernetes guide](guides/kubernetes.md) | Container, Helm chart, KEDA autoscaling, and its own troubleshooting section |
| [Greeter live-demo runbook](guides/greeter-live-demo.md) | A full paid run, end to end, with the zero-touch contracts |
| [Expansion runbooks](https://github.com/adammatthewsteinberger/vibey/blob/main/docs/runbooks/expansion/) | 21 workstreams: JIRA, more clouds, Kubernetes server mode, clients, store submissions, … |
| [Architecture & roadmap](https://github.com/adammatthewsteinberger/vibey/blob/main/docs/plans/architecture-and-roadmap.md) | The master design: context, containers, layers, phases, risks, milestones |
| [Domain model](https://github.com/adammatthewsteinberger/vibey/blob/main/docs/plans/domain-model.md) | Every value object, ADT, and invariant in `domain/` |
| [Data model](https://github.com/adammatthewsteinberger/vibey/blob/main/docs/plans/data-model.md) | Full PostgreSQL DDL, queue semantics, indices |
| [Handoff protocol](https://github.com/adammatthewsteinberger/vibey/blob/main/docs/plans/handoff-protocol.md) | The event ledger, the envelope, and the no-loss gate |
| [Rotation & engines](https://github.com/adammatthewsteinberger/vibey/blob/main/docs/plans/rotation-and-engines.md) | Capability matrix, effort normalization, smooth weighted round robin |
| [Phase protocols](https://github.com/adammatthewsteinberger/vibey/blob/main/docs/plans/phase-protocols.md) | What all six phases do, turn by turn |
| [Implementation plan](https://github.com/adammatthewsteinberger/vibey/blob/main/docs/plans/implementation-plan.md) | Milestone-by-milestone, test-first task breakdown |
| [Decision records](https://github.com/adammatthewsteinberger/vibey/blob/main/docs/architecture/decisions/) | Why each hard call was made (15 ADRs) |

## Status

**Live-validated.** The full pipeline has conducted real paid deliveries end to
end: multi-worker builds (`-j 2`) with cross-engine rotation (claudeloop
implements, agyloop verifies), the bounded verify-repair ladder, budget caps
tripping and being granted live, and fully zero-touch DESIGN phases answered
with nothing but `--defaults`. The validation campaign's findings — a blind
budget brake, a repair-loop livelock, terminal gate-command failures — were
each fixed and re-validated live.

Every architectural layer (`domain`, `application`, `infrastructure`, `cli`)
holds a **100% branch-coverage floor**, enforced as four separate CI gates.
`domain/` is pure stdlib, enforced by import-linter and an AST-walking purity
test — the no-loss handoff gate is deterministic code, not a model's opinion.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `vibey doctor` reports an engine `NOT INSTALLED` | The `*loop` binary isn't on `PATH`. | `uv tool install claudeloop` (or codexloop/cursorloop/agyloop), then re-run `vibey doctor`. |
| `vibey doctor` reports `auth FAIL` | The engine's own vendor credentials aren't configured. | Run that engine's own login/auth flow, then re-run `vibey doctor --conformance`. |
| `vibey worker` logs `no recorded conformance for ...` | `vibey doctor --conformance --record` has never passed for that engine on this project. | Run it before starting the worker; engine-driven jobs won't select an unrecorded engine. |
| A project is parked and nothing progresses | A human gate (interview, review verdict, budget cap) is waiting. | `vibey status <project-id>` to see the park reason; `vibey answer <gate-id> ...` to clear it. |
| Jobs sit `leased` after a worker crash | The lease hasn't expired yet, or nothing has reclaimed it. | `vibey recover --project <id>` (or `--all`) sets them back to `ready`. |
| Budget cap trips mid-cycle | `max_dollars_per_cycle` / `max_dollars_total` was exceeded — by design. | `vibey answer <gate-id> --raw '{"max_dollars": 25}'` to grant more, or accept the park. |
| Kubernetes-specific issues | — | See the [Kubernetes guide's Troubleshooting section](guides/kubernetes.md#troubleshooting). |

## Upgrading

Vibey is pre-1.0: minor versions may change `vibey.toml` fields, ledger
event shapes, or CLI flags. Before upgrading:

1. Read the [changelog](https://github.com/adammatthewsteinberger/vibey/blob/main/CHANGELOG.md)
   for the versions between your current version and the target.
2. Re-run `vibey doctor --conformance --record` afterward — engine
   contracts and conformance checks can gain new checks between releases.
3. The database schema migrates automatically
   (`infrastructure/db/migrator.py`); no manual migration step is needed.

`develop` publishes dev builds to TestPyPI as `vibey-dev`; `main` publishes
tagged releases to PyPI as `vibey`. `uv tool install vibey` (or `pipx
install vibey` / `pip install vibey`) tracks stable releases.

## Project links

| | |
|---|---|
| Contributing | [CONTRIBUTING.md](https://github.com/adammatthewsteinberger/vibey/blob/main/CONTRIBUTING.md) |
| Security policy | [SECURITY.md](https://github.com/adammatthewsteinberger/vibey/blob/main/SECURITY.md) |
| Getting help | [SUPPORT.md](https://github.com/adammatthewsteinberger/vibey/blob/main/SUPPORT.md) |
| Code of Conduct | [CODE_OF_CONDUCT.md](https://github.com/adammatthewsteinberger/vibey/blob/main/CODE_OF_CONDUCT.md) |
| Changelog | [CHANGELOG.md](https://github.com/adammatthewsteinberger/vibey/blob/main/CHANGELOG.md) |

## Related projects

| Project | What it is |
|---|---|
| [claudeloop](https://github.com/adammatthewsteinberger/claudeloop) | Autonomous Claude Code session runner — the design the family transplants |
| [codexloop](https://github.com/adammatthewsteinberger/codexloop) | The same design retargeted onto OpenAI Codex |
| [cursorloop](https://github.com/adammatthewsteinberger/cursorloop) | The same design retargeted onto Cursor |
| [agyloop](https://github.com/adammatthewsteinberger/agyloop) | The same design retargeted onto Google Antigravity / Gemini |

## License

[MIT](LICENSE) © [Adam Matthew Steinberger](https://github.com/adammatthewsteinberger)
