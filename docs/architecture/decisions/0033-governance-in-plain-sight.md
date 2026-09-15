# 0033 — Governance in plain sight: the law is as easy to find and as visible as possible, on every human-readable surface

**Status:** accepted · **Date:** 2026-09-15 · **Extends:** ADR-0020, ADR-0032 · **Canon:** proposed as sub-doctrine 7.b — *governance in plain sight*, under doctrine 7 (the never-lost reader), PR #157, for the operator's ratification

## Context

This project governs itself by written law. The Constitution orders authority and the
ratchet; the Twelve Doctrines and their sub-doctrines state how the project behaves;
the Ten Commandments bind every agent, human and machine; the Bill of Rights recognises
what every engineer is owed; standing subdoctrine SD-01 governs counterparties, trust
and verification. ADR-0020 made the canon the only place a standing rule becomes law,
and the decision records argue the rules it holds.

A rule binds the people it governs fairly only if they can find it. Measured on
2026-09-15, they mostly could not:

- The canon lives in `src/vibey_tools/gh/docs/`, inside one absorbed package's
  documentation (ADR-0020 recorded this as an open question). It is not on the
  project's documentation site, not in the book, and not in the research paper.
- Of the 92 human-readable top-level documents in the tree — READMEs, contributor,
  support and security guides, agent routers, changelogs and landing pages — only
  `CLAUDE.md` links any of it, and only in prose aimed at an agent. The README, which
  is also the PyPI page, does not mention that the project has a constitution.
- The absorbed runners and tools, each still published under its own name, link none
  of it.
- Its address on `main` returns 404 until a promotion carries the absorbed tools
  there, so even a correct link would currently be dead on the release branch.

Visibility had been treated as something that follows from the law existing. It does
not; it has to be decided and then built, like any other surface.

## Decision

**All governance documents are as easy to find and as visible as possible to every
human reader, on every human-readable surface of the entire codebase, forever, no
matter what, with no exceptions.**

**What counts as governance.** The Constitution, the Twelve Doctrines and every
ratified sub-doctrine, the Ten Commandments, the Bill of Rights, every standing
subdoctrine (SD-01 and its successors), and the architecture decision records that
argue the rules. When the corpus grows, the new document is governance from the day it
is ratified.

**What counts as a human-readable surface.** Every README, landing page, documentation
page and its navigation, the book, the research paper, the channel chooser, every
package's page on every registry it is published to, every GitHub Release, every
contributor, support, security and conduct guide, every agent router and skill, issue
and pull-request templates, and the command line's own help where it describes the
project. The rule covers the whole tree: the conductor and every absorbed package.

**What "as easy to find as possible" requires.**

1. **One link away, everywhere.** Every surface carries a direct path to the
   governance, and it is never more than one link from wherever a person is reading.
   A surface that cannot carry a link names where the governance lives in words.
2. **Published in every form the documentation takes.** The governance documents are
   pages on the documentation site with their own navigation section, chapters of the
   book, and are cited from the research paper — not only Markdown files a reader must
   know to open in a repository browser.
3. **Stable, public, plain.** Each document has a stable address, readable without an
   account, a paywall, a search, a login or a machine-only format, in plain words
   first. Links follow what is actually published and are never rendered dead.
4. **Visible, not just present.** Placement is part of the rule: near the top of a
   README or landing page, in the site's primary navigation, in every page footer — not
   only at the bottom of a long table.
5. **Kept true.** A change to the corpus's location, or a new document in it, updates
   every surface in the same change, and a check fails when a surface loses its link.

## Consequences

**Good.** Anyone the law governs — a contributor, a user, an adopter, an agent's
operator, a government reading the order of authority — can find and read it from
wherever they already are, which is the precondition for the law being cited, held to,
or challenged fairly. Machine readers benefit second, as doctrine 7 orders.

**Bad, and accepted.** Every surface carries one more block to keep correct, and the
documentation build grows: the canon must be published into a site whose sources are
under `docs/` while the canon lives under `src/vibey_tools/gh/docs/`, which needs a
build step that publishes the canon from its single source rather than a copy. A
stated rule with no enforcement drifts, so a check is part of the work, not an extra.

**Implementation backlog, in order.** None of it is done by this record; each item is
an ordinary pull request.

1. A **Governance** block near the top of the root README and the docs landing page,
   and a **Governance** row in the documentation tables, the agent routers, CONTRIBUTING,
   SUPPORT, SECURITY and CODE_OF_CONDUCT, linking each governance document.
2. The same block in every absorbed package's README, CONTRIBUTING and SUPPORT, so the
   PyPI pages of all ten distributions carry it.
3. Publishing the canon on the documentation site — a **Governance** navigation
   section built from `src/vibey_tools/gh/docs/` at release time — so it is also in the
   book; a **Governance** link in every page footer and on the channel chooser (the
   vibey-gh release theme, configurable per adopter under ADR-0018); and
   `corpus-index.json` shipped beside it (ADR-0020's recorded gap).
4. A citation of the governance corpus in the research paper, and a governance line in
   GitHub Release notes and `CITATION.cff`.
5. A repository-introspecting test that fails when a human-readable surface in the tree
   no longer links the governance.
6. Until a promotion carries the absorbed tools to `main`, links point at the `develop`
   copy; the promotion switches them to `main`.

**Rule status.** A standing rule — it binds every future surface, survives any rewrite
of the documentation tooling, and is about conduct toward people — so under ADR-0020 it
is written in the canon as well. It is proposed as sub-doctrine 7.b and is law from the
operator's ratifying merge.

## Alternatives rejected

- **Leave visibility to the documentation that already exists.** The measurement above
  is what that produced: one agent-facing file out of 92.
- **Link the canon from the README only.** A reader who arrives on a package page, a
  release, the book or a runner's documentation is still lost; doctrine 7 admits no
  such reader.
- **Copy the canon into `docs/`.** Two copies of the law, one of which the corpus index
  does not cover and which can drift silently; publishing must read the single source.
- **Move the canon out of `src/vibey_tools/gh/docs/` first.** That is ADR-0020's open
  question and a separate decision; visibility does not wait on it, because a link and
  a publishing step work from wherever the canon lives.
- **Treat governance as contributor-only material.** The law governs users, adopters
  and every agent too, and the Constitution places persons above the project's own
  humans; it belongs where every reader is.
