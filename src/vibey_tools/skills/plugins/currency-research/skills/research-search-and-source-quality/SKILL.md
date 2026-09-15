---
name: research-search-and-source-quality
description: Use when researching whether a factual claim is still current — constructing web searches, judging source quality, dating a claim, distinguishing primary from secondary sources, and recording provenance. Triggers on web search research, fact-checking a claim, "find a source for", verifying a statistic, source tiers, primary sources, and any task where an answer must be grounded in something citable rather than recalled. Covers the fabrication failure mode and what to do when the search comes back empty.
---

# Search and Source Quality

How to find out what is actually true right now, and how to know whether what you found is
worth writing down.

---

## The one rule that matters most

⚠️ **Never present recalled knowledge as a search result.** The single worst outcome of a
research task is a confident, specific, well-formatted claim that was reconstructed from
training data and labelled "verified". It is worse than no answer, because it is
indistinguishable from a real one until someone tries to use it.

Concretely:

- If a search returns nothing useful, **say the search returned nothing useful.**
- If you can only find secondary coverage, **say it is secondary.**
- If a figure is approximate or disputed, **carry the approximation or the dispute into the text.**
- If your recollection disagrees with the sources you found, **the sources win** — or the
  question goes in the pull request as unresolved.

The tell for this failure mode is plausible scaffolding around invented specifics: real
organisation names, a real-sounding report title, a precise number, and no retrievable
source. If your draft has that shape, delete the specifics.

---

## Constructing the search

**Start from the claim, not the topic.** "Is X still 12%?" searches better than "X overview".
The claim gives you the entity, the quantity and the implicit date.

Useful moves, roughly in order:

- **Name the authority.** Standards bodies, regulators and vendors publish the thing itself;
  search for the specification, the register, the changelog, the docs — not commentary on them.
- **Date-bound the query.** Add the current or previous year when a claim is time-sensitive.
  Be aware that this biases toward recently *published* pages, which is not the same as
  recently *true*.
- **Search for the change, not the state.** "deprecated", "sunset", "withdrawn", "superseded",
  "end of life", "replaced by", "revision" find transitions that a state-of-the-world query misses.
- **Search for the contradiction.** If the reference says X, search for "not X" as well. A
  source that disagrees is more informative than the tenth that agrees.
- **Go to the primary document** whenever a secondary source cites one. Press coverage of a
  standard routinely garbles version numbers, dates and scope.

⚠️ **One search is not research.** A single query that appears to confirm the existing text is
the weakest possible evidence, because you have only sampled the part of the web that agrees.
Two or three angles, including one adversarial, before concluding "unchanged".

---

## Source tiers

Judge a source by what it is, not by how confident it sounds.

| Tier | Examples | Use for |
|---|---|---|
| **Primary / authoritative** | The standard, the statute, the regulator's register, the vendor's own docs and pricing, the filed report, the dataset | Anything you state as fact. Prefer always. |
| **Peer-reviewed / systematic** | Journal articles, systematic reviews, meta-analyses, official statistics | Scientific and quantitative claims. Check retraction status for older work. |
| **Reputable secondary** | Established trade and technical press, industry analysts, standards-body summaries | Orientation, and finding the primary source. Cite the primary. |
| **Weak** | Vendor marketing, press releases about intentions, blog posts without sources, forum consensus, LLM output, undated pages | Leads only. **Never the sole basis for an edit.** |

Specific traps:

- **A press release announcing a plan is not evidence the plan happened.** Check for the follow-through.
- **Analyst market-share figures vary wildly by methodology.** If you cite one, name the source and
  the method, and prefer reporting a range across sources over a single false-precise number.
- **Wikipedia is a finding aid, not a citation.** Follow its references.
- **A vendor's own docs are authoritative about that vendor's product** and about nothing else,
  least of all competitors.
- **Beware circular sourcing** — three outlets repeating one unsourced claim is still one
  unsourced claim.

---

## Dating a claim

Currency work lives and dies on dates, and pages are bad at them.

- Distinguish **publication date**, **last-revised date** and **the date the content is about**.
  A page revised this month may describe last year's state.
- Undated pages are close to useless for currency work. Look for a version number, a changelog
  entry, or an archived copy that pins the date.
- **A superseded document is still evidence** — of what was true then. Use it to establish the
  before-state when you are describing a change.
- When you cannot establish a date, **say the date is unestablished** rather than assuming
  the page is current.

---

## Recording provenance

Every proposed edit must carry enough provenance for a reviewer to check it without repeating
your research. Record, in the pull request:

- **who** published it (the organisation, not just the site);
- **what** it is (specification, report, register entry, article);
- **when** it is dated;
- **what it actually said** — the specific figure or statement, in your own words;
- **how well it supports the edit** — direct statement, inference, or single-source.

Match the confidence of the wording to the strength of the source. The references in this
marketplace already hedge carefully — "reported", "estimates place", "sources disagree",
"n=753" — and an edit that drops the hedging to sound cleaner has made the document worse
even if the number is right.

---

## When the evidence is thin

Thin evidence is a normal outcome, not a failure. Options, in order of preference:

1. **Leave the text alone** and note in the pull request what you looked for and did not find.
2. **Weaken the claim to match the evidence** — turn a flat assertion into a hedged one, or
   add the disagreement between sources. This is often the most honest edit available.
3. **Mark the uncertainty in the text** where the reference already uses that device
   (a confidence marker, a "sources disagree" note).
4. **Raise it as a question** in the pull request for a human to resolve.

⚠️ **Never resolve thin evidence by picking the most quotable number.** If two credible
sources disagree, the disagreement *is* the finding, and the reference should say so.
