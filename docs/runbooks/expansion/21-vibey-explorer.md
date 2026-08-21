# Runbook: vibey-explorer — find work in the open, build it, ship it

## Goal

A new repo, `vibey-explorer`, submoduled into the umbrella (runbook 19).
Daily, it looks for open-source work worth doing — features people are
asking for, bugs people are hitting — picks the ones this system is
genuinely capable of finishing, builds them, and ships:

- to an **existing project**, as a pull request;
- or, where no implementation exists, as a **new repository** on the
  operator's account, announced back wherever the need was found.

## The two constraints that decide whether this works

Everything else in this runbook is mechanics. These two are the design.

### 1. Capability-first selection, not popularity-first

The temptation is to rank by attention and work down the list. That
produces contributions to trending Rust GPU projects this system cannot
finish. **The primary filter is "can we take this to a full-gate,
mergeable standard", and attention is the tiebreaker among things that
pass it.** An abandoned half-fix is worse than no fix: it costs a
maintainer a review and leaves nothing behind.

Concretely, score candidates on:

- **Fit** — Python/typed, test-suited, onion-friendly, CLI/API/library
  shaped, reproducible locally, dependencies installable. This system's
  demonstrated strengths, not its aspirations.
- **Boundedness** — a clear definition of done. "Add a `--json` flag" is
  a candidate; "improve performance" is not.
- **Verifiability** — a failing test can be written first. If success
  cannot be demonstrated mechanically, the PR is an opinion.
- **Attention** — issue reactions, stars velocity, HN/Reddit/Lobsters
  discussion, download trend. Real, and last.

Fit gates; attention ranks. A candidate that fails fit is not rescued by
being popular.

### 2. An unsolicited PR spends someone else's time

A PR to a project nobody asked for costs a maintainer a review whether or
not they wanted it, and machine-authored contributions have made that
cost worse across open source generally. That is not a reason to refuse
the work — a genuinely good, tested, scoped fix is welcome almost
everywhere — but it is a reason for the bot to behave better than the
median contributor rather than worse. Non-negotiable:

- **Respect the project's stated policy.** Read `CONTRIBUTING.md`, the
  issue templates, and any AI-contribution policy *before* building. A
  project that declines machine-generated contributions is skipped, and
  that skip is recorded so it is never re-evaluated by accident.
- **Disclose.** Every PR says plainly that it was machine-authored, via
  the provenance line from runbook 18. A maintainer should never have to
  work that out.
- **Prefer the issue over the PR.** Where a project's norm is to discuss
  first, open the issue with the diagnosis and offer the patch — do not
  arrive with 800 lines nobody asked for.
- **Cap the rate, hard.** A small number of PRs per day across all of
  open source, and **at most one open PR per project at a time.** Volume
  is what turns a helpful bot into a nuisance.
- **Close what goes stale.** An unreviewed PR after N days is withdrawn,
  not bumped.
- **Never re-open a rejected idea.** A closed PR is a signal; ignoring it
  is how a bot gets an account banned.

The new-repo path carries none of this burden, which makes it the
preferred outlet when no upstream exists.

## Design

1. **Discovery** — pluggable sources (GitHub search and trending, issue
   labels like `help wanted` / `good first issue` / `bug`, HN, Reddit,
   Lobsters, package registries). Each yields candidates with a source
   link so provenance is never lost.
2. **Scoring** — fit gate first, then rank. The scorer is a pure,
   testable function over candidate features, so its judgement can be
   inspected and property-tested rather than being a prompt with a mood.
3. **Policy check** — the constraint list above, evaluated before any
   build work is done. Building first and checking policy after wastes
   real money.
4. **Build as a vibey project** — same queue, same six phases, same
   gates, same budget caps. The output must clear runbook 18's bar:
   100% coverage, linted, scanned, documented, attributed. Anything less
   should not be sent to a stranger.
5. **Ship** — PR to upstream, or a new repo published to the operator's
   account and announced back to the source thread. Both paths record the
   destination in the ledger.
6. **Learn from outcomes** — merged, closed, ignored, and *why* feed back
   into scoring. A discovery bot that never learns which of its
   contributions landed will keep making the same unwelcome ones.

## Work items

1. Repo scaffold matching family conventions.
2. Discovery source adapters behind one Protocol, fixture-tested.
3. Pure scorer: fit gate + attention ranking, property-tested.
4. Policy reader (CONTRIBUTING, templates, AI policy) + skip registry.
5. Build pipeline wiring into vibey's phases with per-candidate budgets.
6. Upstream PR publisher with disclosure, rate caps, staleness withdrawal.
7. New-repo publisher + announce-back to source.
8. Outcome tracking feeding the scorer.
9. Daily schedule; Job/CronJob chart per runbook 16.

## Verification

- **The quiet bar:** a day with no candidate passing the fit gate ships
  nothing. A bot that must produce output will produce bad output.
- A project whose CONTRIBUTING declines AI contributions is skipped
  before any build spend, and lands in the skip registry.
- Rate caps hold under a deliberately large candidate set; never two open
  PRs to one project.
- Every shipped artifact clears runbook 18's full bar and carries the
  provenance line.
- A merged PR and a closed PR both move the scorer measurably.
- A stale PR is withdrawn on schedule without a human.
- End to end: one real merged upstream PR, and one new repo published and
  announced, both traceable in the ledger to the source that prompted
  them.

## Needs from operator

- GitHub account(s) and publish rights for new repos.
- The daily PR cap, and the staleness withdrawal window.
- Any accounts or ecosystems to exclude outright.
- API access for whichever discovery sources are wanted.

## Risks

- **Reputational, and it compounds.** Bad unsolicited PRs damage the
  operator's name, not the bot's. Rate caps, the fit gate, and full gates
  on output are the mitigation; start with a cap far below what feels
  useful.
- **Chasing attention over capability.** The fit gate exists precisely to
  stop this, and it must stay a gate rather than becoming a weight.
- **Burning budget on candidates that never ship.** Per-candidate caps
  and policy-check-before-build.
- **Account suspension** from volume or ignoring rejections. The rate cap
  and the never-re-open rule are load-bearing, not politeness.
- **Duplicating work already in flight.** Check for existing PRs and
  linked branches before building; arriving second is pure waste.
