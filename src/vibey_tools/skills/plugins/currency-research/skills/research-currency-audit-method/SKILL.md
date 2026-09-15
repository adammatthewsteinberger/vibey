---
name: research-currency-audit-method
description: Use when auditing a reference document, skill or knowledge base for staleness — deciding whether new developments in a field warrant adding, modifying or deleting existing content. Triggers on currency audit, staleness check, "is this still true", refreshing documentation, scheduled research runs, "what changed since", and reviewing dated claims. Covers the durability tiers, the decision procedure, scoping a run, and why the default answer is no change.
---

# Currency Audit Method

How to check whether an evidence-grounded reference has gone stale, and decide what — if
anything — to do about it.

This is the entry point for the weekly currency audit. It answers *what to look for* and
*when a finding justifies an edit*. The companion skills cover the searching
(`research-search-and-source-quality`), the editing (`research-editing-a-reference-skill`)
and the pull request (`research-weekly-pull-request`).

---

## The default answer is "no change"

**Most of a good reference does not go stale.** The second law of thermodynamics, Clausewitz
on friction, wood movement across the grain, the no-cloning theorem, Little's Law — these
read the same every year. A currency audit that produces edits every week on every plugin is
not doing its job well; it is manufacturing churn.

So the burden of proof runs one way: **you are looking for a reason to change something, and
absent a specific, sourced, material development, you leave it alone.** A run that concludes
"nothing here needs changing" is a successful run, and it should say so plainly rather than
inventing a marginal edit to look productive.

⚠️ **The failure mode this guards against is real and has happened in this repository.** A
document once shipped a currency section labelled "verified" that had been written after two
web searches returned nothing — populated with specific figures, named tests and dated
regulatory changes, all reconstructed from training data and presented as verification. It
had to be rebuilt from scratch. **An empty or unhelpful search result is information: report
it. It is never a licence to write what the answer probably looks like.**

---

## The three durability tiers

References in this marketplace tag claims by how durable they are. The tier determines
whether a claim is even a candidate for the audit.

| Tier | What it is | Audit treatment |
|---|---|---|
| **Stable fundamentals** | Physical law, mathematics, settled mechanism, historical fact | **Do not audit.** If you think one changed, you have misread it or found a genuinely extraordinary result — treat with proportionate scepticism. |
| **Versioned specifics** | Standard versions, API surfaces, product tiers, regulatory thresholds, prices, market shares, adoption figures | **The main target.** These have a shelf life measured in months. |
| **Contested questions** | Live scientific or scholarly disputes, replication status, unsettled policy | **Audit the state of the dispute, not the answer.** The correct update is usually "the balance of evidence shifted" or "a major replication landed", not "the question is now settled". |

A plugin's `> **Currency:**` header line names the section holding its dated claims. That
line is the brief — it tells you what the author already knew would age first.

---

## What counts as a finding

Four outcomes, in rough order of frequency.

**1. No change.** The claim still holds, or nothing credible has moved. Most common. Record
what you checked so the next run does not repeat the same search blindly.

**2. Modify.** A dated claim has a new value: a version shipped, a threshold moved, a
deadline passed, a share shifted, a dispute resolved. This is the bread and butter.
Requirements: a source that post-dates the existing claim, and a specific replacement value.
"Roughly X now" without a figure is not a modification, it is a rumour.

**3. Add.** A genuinely new development that the reference does not cover and that a reader
of that section would be misled by not knowing. **The bar is higher than it looks** — a
reference is not a news feed, and adding every development produces bloat that makes the
durable material harder to find. Ask: would omitting this cause a reader to make a wrong
decision? If not, skip it.

**4. Delete.** Rare and requires the most care. Legitimate deletions:
- a product, standard or programme that has been formally discontinued and the text presents as current;
- a figure whose source has been retracted or corrected;
- a claim that has been directly falsified by subsequent work.

⚠️ **Deleting content because it is inconvenient, unfashionable, or merely old is not a
currency edit — it is damage.** Superseded material often belongs in the text with its status
marked ("withdrawn in 2026", "failed to replicate") rather than removed, because readers
arrive carrying the old claim and need to be told it is dead. Prefer marking to deleting.

---

## The decision procedure

For each dated claim in scope:

1. **Read the claim exactly.** Note what it actually asserts, how hedged it is, and what date
   or version it is pinned to. Many "stale" claims turn out to be correctly hedged already.
2. **Search for the current state.** See `research-search-and-source-quality`.
3. **Compare.** Does a credible source that post-dates the claim contradict it, supersede it,
   or materially extend it?
4. **Decide the smallest correct edit.** Change the figure, not the paragraph. Change the
   paragraph, not the section. Preserve the author's framing and hedging unless the framing
   itself is what is now wrong.
5. **Record the source** with enough detail that a reader can check it: publisher, title,
   date, and what it actually said.
6. **If uncertain, do not edit.** Report the uncertainty in the pull request instead and let
   a human decide. An unresolved question raised is more useful than a wrong edit made.

---

## Scoping a run

**Audit only the plugins the run was given.** The rotation exists so that each run is small
enough to do properly; widening it to "while I was in there" turns a reviewable pull request
into an unreviewable one.

Within a plugin, work outward from the currency anchor:

1. the section named in the `> **Currency:**` line — always;
2. any section whose text contains an explicit date, version number, price, percentage or
   "as of" — these are self-identifying;
3. sections covering fast-moving subject matter even when undated — regulation, product
   landscapes, adoption, tooling;
4. everything else — only if something in steps 1–3 turned up a contradiction that implicates it.

**A reasonable run touches one to three claims per plugin, and often none.** If you find
yourself proposing a dozen edits to one plugin, stop and ask whether the plugin was actually
stale or whether you have drifted into rewriting it to your own taste.

---

## What this audit is not

- **Not a rewrite.** Style, structure, section ordering and voice are out of scope.
- **Not a completeness review.** "This section could also mention X" is not a currency finding.
- **Not a fact-check of stable material.** Re-litigating settled mechanism wastes the run.
- **Not a link checker.** The repository has one (`tools/check_links.py`) and it runs in CI.
- **Not a place to add opinions.** These references are deliberately hedged and source-tagged;
  match that register or leave the text alone.
