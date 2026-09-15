# 0017 — If the family already does it, the family does it here

**Status:** accepted · **Date:** 2026-09-15

**Canon:** sub-doctrine 10.e — *the family first*, filed under doctrine 10 — No guarantees (ADR-0020). It is law from the operator's ratifying merge of the change that carries it.

## Context

This organisation ships a conductor, five session runners, a GitHub automation
package, a skills marketplace with a retrieval engine, and a cross-cutting layer
with retry, dead-letter routing, correlation-scoped structured logging, secret
masking, counters, health probes, heartbeats, soft-fail, fail-close helpers,
token verification, rate limiting and ten log transports.

Measured on this branch, `src/vibey` imports **none of them**. Zero import sites
for `vibey_bootstrap`, `vibey_skills`, `vibey_gh` or `vibey_runners`. The runners
are driven as subprocesses, vibey-gh is CI tooling, and vibey-skills is reached
by `python -m vibey_skills.cli` — so the conductor consumes its own family only
across process boundaries, and never as code.

Meanwhile the conductor carries its own retry and backoff logic across 17 files,
its own logging adapter, and its own health service. Some of that is genuinely
different. Some of it is a second implementation of something this organisation
already ships, tested to a 100% floor, and published.

That is the wrong way round. A project whose product is autonomous software
delivery, and which does not use its own delivery tooling, is making a claim it
has not tested. Every seam where we choose something else over our own package is
a seam where nobody finds the bug until a user does.

## Decision

**If a capability exists inside this family, use it. Do not reimplement it, and
do not reach for a third-party equivalent.**

The bar is not "is ours better". The bar is "does ours do this at all". Between
using `vibey_bootstrap`'s retry and writing a retry loop, use
`vibey_bootstrap`'s. Between its dead-letter routing and a hand-rolled failure
path, use its. Between its correlation scope and threading a request id by hand,
use its. When the choice is between using a family feature and not using it,
**always prefer using it.**

This is deliberately stronger than "prefer". A new implementation of something
the family already ships needs a written reason at the call site, and the reason
has to be a capability gap — not taste, not "it was quicker", and not "ours is
only a few lines". If ours is missing something, the fix is to add it to ours.

### Where it applies, and how

The layer rules are not relaxed by this, and two of them shape how dogfooding is
actually done:

- **`domain/` gains a caveat rather than an exemption.** The rule was "stdlib
  only, no third-party imports". A family package is not third-party, so the rule
  now reads: **stdlib, and any family package that is itself dependency-free.**
  `vibey-gh`, `vibey-skills` and `vibey-runners-common` all declare
  `dependencies = []` — importing one adds nothing to the graph that stdlib-only
  did not already allow, and the purity the rule exists to protect is untouched.

  `vibey_bootstrap` is the exception, and for a stated reason rather than by
  category: it carries the Azure SDK and OpenTelemetry, so importing it in
  `domain/` would pull a third-party graph in transitively and break the
  invariant by the back door. It stays forbidden there, named explicitly in
  `.importlinter` so the reason is visible at the point of enforcement. Use it
  from `infrastructure/`, behind a port, like every other dependency.

  What has *not* changed is the rest of the rule: no I/O, no async, no clock, no
  network — enforced by `tests/domain/test_domain_purity.py`, which walks the AST
  rather than trusting the import list. A dependency-free family package that
  opened a file would still be unusable in `domain/`, and that test is what says
  so.
- **`application/` dogfoods behind a port.** It declares what it needs as a
  Protocol in `application/interfaces/`, exactly as ADR-0016 requires of every
  class, and the adapter that satisfies it with a family package lives in
  `infrastructure/`.
- **`infrastructure/` is where family packages are imported.** It is already the
  only layer permitted third-party imports, and a family package is one.

So the shape of every dogfooding change is the same: a port, an adapter, and a
line in `bootstrap.py`. That is the shape this codebase already uses for
everything else, which is the point — dogfooding is not a new pattern here, it is
the existing one applied to ourselves.

### Across process boundaries too

Dogfooding is not only in-process. Where the family already publishes a tool for
a job, use it rather than a hand-rolled script or a third-party action:
`vibey-gh` for provenance, versioning, release and merge automation in every
repository; `vibey-skills` for the context a model is given; the `*loop` runners
for driving a session. "We use our own thing here" applies to CI and to
operations as much as to imports.

## Consequences

**There is a parity backlog, and it is now visible instead of implicit.** The
measured starting point is zero in-process use. The named candidates, in the
order their seams already exist:

| Where | Today | Should be |
|---|---|---|
| `infrastructure/` retry and backoff | hand-rolled, 4 files | `vibey_bootstrap.retry` behind a port |
| `infrastructure/logging.py` | structlog, own redactor | `vibey_bootstrap.logging` — correlation scope, secret and control-character masking, `ExtraFieldsFormatter` |
| failed-job handling | own path | `vibey_bootstrap`'s dead-letter routing vocabulary |
| `application/engine_health_service.py` | own | `vibey_bootstrap.health` probes behind a port |
| counters and metrics | own, 7 files | `vibey_bootstrap.counters` / `.metrics` |
| `infrastructure/skills_context.py` | subprocess only, and **CI never installs the extra**, so the seam is exercised only against a fake | the real package, installed and tested |

**The cost is real and is accepted.** `vibey_bootstrap` carries the Azure SDK and
OpenTelemetry. Adopting it in `infrastructure/` puts those in the conductor's
dependency graph, and a container image that did not carry them will. That is a
price, and it is worth paying, because the alternative is maintaining a second
implementation of everything it does and discovering its bugs in production
rather than in our own use. Where a dependency's weight is genuinely intolerable
for a given surface, the answer is an optional extra — not a reimplementation.

**Adoption is incremental and ordinary.** Each item above is a normal change:
port, adapter, composition-root line, tests. None is a precondition for anything
else, and none should be bundled with unrelated work. What is *not* optional is
the direction — a new hand-rolled retry loop does not merge.

**It raises the cost of a gap in our own packages, on purpose.** If
`vibey_bootstrap`'s retry does not do what a caller needs, the change is to
`vibey_bootstrap`. That is the mechanism by which dogfooding improves the
product rather than just consuming it, and it is why this is worth a rule rather
than a preference.
