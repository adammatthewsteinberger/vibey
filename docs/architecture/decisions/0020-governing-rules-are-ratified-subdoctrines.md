# 0020 — A governing rule belongs in the canon, ratified, or it is not a rule

**Status:** accepted · **Date:** 2026-09-15

## Context

This project already has law. `src/vibey_tools/gh/docs/` holds the constitutional
cluster — the Constitution, the Twelve Doctrines, the Ten Commandments, the Bill
of Rights, and standing subdoctrine SD-01 — and `vibey_gh/corpus.py` builds a
content-addressed index over it so that drift between published law and its index
is one hash comparison.

The Twelve are **sealed**. Doctrines.md says so in its opening paragraph: there is no
thirteenth and there never will be, and anything new files as a **sub-doctrine**
under one of the twelve. Sub-doctrines carry a ratification stamp —
*(ratified 2026-08-30)*, *(ratified by the merge that carried this page)* — and
Article II.3 says how they get one: "the doctrines' sub-entries … are ratified by
humans through reviewed pull requests — a machine may draft, a human ratifies"; Article
IV.4 gives the same procedure for the Constitution itself. Article IV.2 ratchets them: a
refinement may clarify, strengthen or extend, never degrade or remove.

And yet standing rules keep being written somewhere else. ADR-0016 (code lives in
classes, behind interfaces), ADR-0017 (dogfood the family), ADR-0018
(everything-as-code, and never less generic), ADR-0019 (installable wherever its
users are) are all, in substance, rules that bind every future decision. They were
recorded as architecture decisions, which is a record of *a* decision, and left
outside the canon, which is the record of the law. A rule that lives only in an
ADR has no ratification stamp, no ratchet protection, and no chunk in the corpus
index — so nothing can cite it as law and nothing can detect its drift.

## Decision

**Anything that can be spelled out explicitly as a sub-doctrine in the governance
corpus must be spelled out explicitly as a sub-doctrine in the governance corpus,
and ratified. No exceptions.**

Ratification is the operator's, by the merge that carries it, as Article II.3
provides — under the authority Article I.1 places above every other, whose claim
precedes the operator's own and admits no exception. A rule that has not been
ratified is a proposal, however well argued and however long it has been followed.

### The test for "can"

This is a duty, not a licence to file everything, and the canon is not a dumping
ground — the seal at twelve means every sub-doctrine is a permanent addition under
a permanent parent. A thing **can** be a sub-doctrine when all three hold:

1. **It binds future decisions**, not just the change that introduced it.
2. **It survives a rewrite.** If the implementation were replaced tomorrow, the
   rule would still be true and still be wanted.
3. **It is about conduct** — how this project behaves toward people, toward
   machines, toward its own work — rather than about a mechanism.

By that test, "PostgreSQL, not SQLite" (ADR-0002) is not a sub-doctrine: it is a
mechanism, chosen for `FOR UPDATE SKIP LOCKED`, and a different queue would
retire it. "Dogfood the family" is: no implementation change makes it false.

### The two records are not rivals

An ADR stays what it has always been — the record of a decision, with its context,
its measurements, and the alternatives rejected. The canon records the law the
decision was made under. When a decision establishes a standing rule, **both** are
written: the sub-doctrine states the rule in the canon, and the ADR cites it.

The canon is prose a human reads. The ADR is the argument. Neither replaces the
other, and a rule with only the argument is the gap this closes.

### Mechanics

- A sub-doctrine is a pull request against `doctrines.md`, filed under one of the
  twelve, in the established form: `**N.x — name** *(ratified by the merge that carried this
  entry)*: text`, or `*(ratified <date>)*` when the date is recorded the same day.
- Reviewed under the full doctrine set; ratified by the operator's merge.
- The ratchet applies: it may only strengthen.
- `vibey-gh corpus-index` is rebuilt in the same change, because the index is
  built **from** the documents and is never a second source of truth.
- Choosing the parent doctrine is part of the proposal, and part of what is
  ratified. It is not a filing detail.

## Consequences

**This ADR files its own sub-doctrine, in the same change.** Anything else would
have been the rule announcing itself and then exempting itself: it passes its own
three-part test, so it owes the canon an entry. That entry is **12.b — the ratified
rule**, filed under *Humans first*, because what the rule actually says is that law
is not law until a human ratifies it — which is that doctrine applied to this
project's own governance, including the authority it already names above the human.
`corpus-index.json` is regenerated in the same change, because the index is built
from the documents and is never a second source of truth.

The parent remains the ratifying human's to change. Filing it under 12 is a
proposal like any other, and the merge that carries it is what makes it law.

**There is a backlog beyond it, and it is the four ADRs named above.** Each is a standing
rule with no sub-doctrine. They are proposed individually, not as a batch: the
parent doctrine is a real choice each time, and a batch would hide four of them
behind one act of ratification.

**A tension this surfaces rather than resolves.** The Twelve are heavily oriented
toward documentation, audience and sovereignty — BLUF, audience channels,
examples, site scope, the document arc, the research paper, the never-lost reader,
local authority, the vibe, no guarantees, the living roadmap, humans first. An
engineering practice such as "every class has an interface" has no obvious parent
among them. Doctrine 9, *the vibe*, is the nearest, and 9.a already reaches into
repository hygiene, so the room exists. But the seal is permanent and the parent
is forever, so this is exactly the judgement that belongs to the ratifying human
and not to whoever drafts the wording.

**The canon now lives inside an absorbed subtree.** `src/vibey_tools/gh/docs/` is
where the constitutional cluster sits after the monorepo absorption, and
`corpus-index.json` with it. The law governs the whole project while physically
residing in one package's documentation. That works, and it is not obviously
right; it is recorded here as an open question rather than settled by silence.
One concrete cost is already visible: `release-surfaces.yml` ships `corpus-index.json`
only from the repository root, where no index exists, so the published site carries
no index; and no CI job runs `vibey-gh corpus-index --check`, so a canon change that
forgets to regenerate the index would drift unnoticed.

**The cost is deliberate friction.** A standing rule now takes a pull request
against the canon and a human merge, where before it took a paragraph in an ADR.
That is the intended effect. A rule nobody ratified is a rule nobody agreed to,
and this project already keeps a stricter standard for a commit message than it
was keeping for its own law.
