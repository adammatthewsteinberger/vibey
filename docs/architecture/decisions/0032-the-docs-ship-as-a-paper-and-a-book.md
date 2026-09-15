# 0032 — The documentation ships as a research paper and a book, findable everywhere and built to outlive the site

**Status:** accepted · **Date:** 2026-09-15 · **Extends:** ADR-0018, ADR-0028 · **Canon:** doctrines 5 (the document arc), 6 (the research paper) and 7 (the never-lost reader)

## Context

Doctrine 6 says every repository produces a journal-grade research paper, Markdown to
LaTeX to PDF; doctrine 5 orders the documentation from a zero-code beginner to
scholarly theory; doctrine 7 says no reader is ever lost. `vibey-gh` already builds
both end results on every release: `vibey-gh paper` renders `docs/paper.md` as an
IEEEtran document compiled with a pinned, checksummed Tectonic, and `vibey-gh book`
exports the built site, in navigation order, as an EPUB, a print-ready HTML and — when
the runner has Chromium — a 6×9 PDF interior. `release-surfaces.yml` publishes them at
the root of each documentation channel.

On 2026-09-15 both existed and nobody could find them. No page, no README, no release,
no package index and no citation metadata linked the paper or the book; a reader had
to know the file names. The site root is a channel chooser that linked neither. The
paper's byline read "the-vibey-project" because no author was configured. Four of the
reference pages and the paper itself were not in the navigation, so they were not in
the book either, and a navigation title containing a colon was silently dropped from
it. And nothing guaranteed a copy would survive a rebuilt or moved site: GitHub
Releases had stopped at v0.1.2.

## Decision

**The paper and the book are first-class release artifacts, linked from every surface
a person or a machine reads, and kept in more than one durable place.**

- **Single sources.** The paper is `docs/paper.md`, in the constrained Markdown the
  renderer converts. The book is the `properdocs.yml` navigation, in order: home,
  guides, reference, architecture decisions, research paper. A navigation edit is a
  book edit, and navigation titles carry no colon.
- **Stable addresses.** Production: `https://the-vibey-project.github.io/vibey/main/`
  `paper/`, `paper.pdf`, `book.pdf`, `book.epub`, `book-print.html`. Preview: the same
  paths under `/develop/`.
- **Linked from everywhere, only when produced.** Every documentation page's navigation
  and footer, the channel chooser and `llms.txt` link whatever the deploy actually
  built — rendered from file presence, never from configuration (PR #147). The README
  (and therefore the PyPI description), the docs landing page, the agent routers,
  SUPPORT, CONTRIBUTING and CHANGELOG link them in prose; `pyproject.toml`
  `[project.urls]` puts them in PyPI's sidebar; `CITATION.cff` makes the paper the
  repository's preferred citation.
- **A permanent copy per version.** On the release channel, the `attach` job uploads
  `paper.pdf`, `book.epub`, `book.pdf` and `book-print.html` to that version's GitHub
  Release, which `github-release.yml` now creates for every promotion (PR #147).
  `workflow_dispatch` of that workflow must prove its target is on `main` with a
  successful release run and never executes the target's code.
- **Named authorship.** `[documentation] author` is set, so the paper's byline, the
  book's Dublin Core metadata and every page's metadata name the author.

## Consequences

**Good.** A reader who lands anywhere — GitHub, PyPI, the docs site, a release, a
citation manager, an LLM crawler — is one link from the paper and the book, and the
link is never dead because it is only rendered for files that exist. Every release
leaves a versioned copy that does not depend on GitHub Pages.

**Bad.** The documentation deploy does more work (a TeX compile and a headless
Chromium print per channel), and the `attach` job waits up to ten minutes for the
GitHub Release. Links in prose duplicate the stable addresses in several files; the
addresses are therefore part of the site's contract and must not move.

**"Forever" needs the operator, and is recorded here so it is not forgotten.** GitHub
Release assets last as long as the repository. Stronger guarantees need accounts and
consent that automation does not hold:

1. **A DOI.** Enable the repository in Zenodo's GitHub integration; every GitHub
   Release is then archived with a versioned DOI and a concept DOI, which goes into
   `CITATION.cff`.
2. **A preprint server.** Submit the paper to arXiv (cs.SE), which needs an endorsed
   submitter account; the arXiv identifier then goes into `CITATION.cff` and the paper.
3. **An independent snapshot.** Save each release's asset URLs to the Internet
   Archive, which can be automated once the operator accepts that dependency (10.a).
4. **A print edition.** The book's PDF interior is already KDP-shaped; a listing is an
   operator decision about a commercial counterparty (10.b).

**Rule status.** The standing rule — the documentation's end results are linked from
every surface and kept durably — is doctrines 6 and 7 applied; this ADR is the
mechanism and owes no new sub-doctrine.

## Alternatives rejected

- **Publish only on a release page.** A reader of the docs site should download the
  book from the documentation it mirrors, not hunt a release page (the vibey-gh
  design note that put them on the site).
- **Link the files from configuration flags.** A flag on and a failed Chromium print
  would render a link to a PDF that does not exist; links follow file presence.
- **Commit the PDFs to the repository.** Binary churn on every documentation change,
  and a second source of truth beside the Markdown.
- **A separate book repository or site.** Moves the book away from the documentation
  it is built from, which is exactly the drift the export exists to prevent.
