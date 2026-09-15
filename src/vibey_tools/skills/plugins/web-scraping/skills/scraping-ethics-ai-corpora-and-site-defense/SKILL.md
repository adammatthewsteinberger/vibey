---
name: scraping-ethics-ai-corpora-and-site-defense
description: "Use when weighing the operational ethics of collection, building a corpus for AI or RAG, or configuring and defending a site: rate limits and being a good guest on someone else's infrastructure, provenance, opt-out signals and legal basis per source for AI training, and running a site that handles crawlers well — robots.txt tokens including Google-Extended, the mixed-use blocking trap, pay-per-crawl, and the structured data that makes you legible to agents."
---

# Web Scraping: Operational Ethics, Scraping for AI and RAG, and If You Run a Site

> **Part 4 of 5** of the *Web Scraping* reference (plugin `web-scraping`), covering §11–§13. Sibling skills: `scraping-legal-landscape-and-permissions` (§0–§3), `scraping-tooling-extraction-and-blocking` (§4–§7), `scraping-scale-reliability-and-data-quality` (§8–§10), `scraping-reference` (§14–§19). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §16 → `scraping-reference` for the currency snapshot and what goes stale first.

> **How to read this.** Reference, not tutorial. Three markers:
> - **[DURABLE]** — how HTTP and the web work, engineering practice, or ethics. Doesn't expire.
> - **[VERSIONED]** — case law, regulation, tooling, platform behaviour. **This domain's
>   legal layer is moving faster than its technical layer right now.** Verify.
> - **[CONTESTED]** — genuine disagreement.
>
> **⚠️ GOTCHA** boxes mark the mistakes that get you blocked, sued, or quietly producing
> wrong data for months.
>
> **This is not legal advice.** §1 → `scraping-legal-landscape-and-permissions` is a map of the frameworks that apply and the questions
> to put to counsel, not an answer for your jurisdiction or your use case. **The legal
> position depends heavily on what data, from where, about whom, and for what purpose** —
> and those four variables move the answer more than any technical choice you make.
>
> **The three framings that organize everything below:**
> 1. **The legal question is not "is scraping legal." It is four separate questions** —
>    *how did you access it* (computer-access law), *what did you agree to* (contract),
>    *what is the data* (copyright, personal data), and *what will you do with it*
>    (privacy, AI training, resale). **They have different answers and you need all four**
>    (§1 → `scraping-legal-landscape-and-permissions`).
> 2. **You are a guest on someone else's infrastructure, and they're paying for it.**
>    Nearly every operational rule in this document — rate limiting, caching, conditional
>    requests, off-peak scheduling — follows from taking that seriously, and doing so also
>    happens to be what keeps you unblocked (§11).
> 3. **Scrapers rot.** A scraper is a hard dependency on someone else's HTML, which they
>    will change without telling you. **Silent breakage that produces plausible-looking
>    wrong data is the characteristic failure of this field** (§9 → `scraping-scale-reliability-and-data-quality`), and it's worse than
>    a crash because nobody notices.

---

## §11. Operational Ethics

**[DURABLE] Almost every rule here also happens to keep you unblocked, which is a useful
alignment.**

- **Identify yourself.** A descriptive User-Agent with a contact URL. **The cost of being
  contactable is zero; the benefit is that a site owner emails you instead of banning your
  infrastructure.**
- **Respect robots.txt** (§3.1 → `scraping-legal-landscape-and-permissions`).
- **Rate-limit conservatively.** Start slow, watch response times, back off if the site
  slows. **⚠️ Nights and weekends are not free** — that's when their batch jobs run.
- **Cache aggressively and use conditional requests.** A 304 costs them almost nothing.
- **Don't scrape what you don't need.** Every field you don't use is load you shouldn't
  have generated.
- **Honour `Retry-After` and 429s.** They are literally telling you the answer.
- **Respect a hard block** (§7.2 → `scraping-tooling-extraction-and-blocking`).
- **Consider the target's size.** The same request rate is trivial to a major platform and
  a genuine cost to a hobbyist's blog or a small nonprofit. **Scale your courtesy to their
  infrastructure, not to your appetite.**
- **Attribute where appropriate**, and **don't republish wholesale** — derive, aggregate,
  analyze.
- **Don't build a competing product from a scrape of someone's entire catalogue** and
  expect goodwill.

**[DURABLE] The test worth applying: would you be comfortable if the site owner read your
crawl logs, and could you explain your rate, your purpose, and your data handling without
wincing?** If not, that's information.

---

## §12. Scraping for AI and RAG

**[VERSIONED — the highest-risk use case, and where §1.6 → `scraping-legal-landscape-and-permissions` concentrates.]**

**Technical differences from classic scraping**: you want **clean readable text** rather
than fields (boilerplate stripping, main-content extraction, markdown conversion),
**chunking** that respects document structure, **metadata and provenance per chunk** (so a
retrieval system can cite), and **freshness** management.

**⚠️ The legal picture is materially different from ordinary scraping**, and conflating
them is how teams get into trouble:
- **EDPB Guidelines 03/2026** apply to both direct scrapers and **organizations acquiring
  pre-scraped datasets from brokers** — buying the corpus does not transfer the problem
  away (§1.6 → `scraping-legal-landscape-and-permissions`).
- **Personal data cannot easily be removed from a trained model**, so the compliance
  decision has to be made **upstream, before training**.
- **EU AI Act GPAI obligations** require publishing a training-data summary and respecting
  machine-readable opt-outs, with enforcement from **2 August 2026**.
- **DMCA §1201 circumvention theories** are being tested specifically in the
  AI-training context (§1.4 → `scraping-legal-landscape-and-permissions`).
- **Copyright**: reproducing creative work for training is genuinely unsettled and heavily
  litigated; **the EU TDM exception is opt-out-dependent** (§3.2 → `scraping-legal-landscape-and-permissions`).

**[DURABLE] The practical governance minimum**: maintain a **source inventory with legal
basis per source**, **respect opt-out signals and log that you did**, exclude sensitive
categories at collection, keep provenance through to the training set, and get review
before training or reselling. **This is dull and it is the actual work.**

---

## §13. If You Run a Site

**[DURABLE] Worth understanding from both sides, and increasingly a live product decision.**

**Publish your preferences clearly**: robots.txt with the AI-crawler tokens you care about
(**note that `Google-Extended` is a control token Googlebot reads, not a separate crawler —
disallowing it stops Gemini training use without touching search indexing**), a sitemap,
and consider Content Signals / TDM reservations if AI use matters to you (§3.2 → `scraping-legal-landscape-and-permissions`).

**⚠️ Understand the mixed-use trap before you toggle anything** — blocking Training can
block multi-purpose crawlers including Googlebot, Applebot and Bingbot (§3.2 → `scraping-legal-landscape-and-permissions`). **Check what
your configuration actually does rather than what you assumed it does.**

**Decide the strategic question**, because it's genuinely contested: **block AI crawlers
to protect content, allow them for AI-answer visibility, or charge via a pay-per-crawl
scheme.** These are real trade-offs with revenue implications either way, and the honest
position is that nobody knows yet how AI-referral traffic will develop.

**And the counterintuitive one**: **if you want to be cited by AI systems and found by
agents, clean machine-readable structured data is what makes you legible.** Schema.org
markup, a stable catalogue API, and accurate feeds serve search, marketplaces, agents, and
your own consumers simultaneously — **the same work pays off across all of them.**

**Technically**: rate-limit rather than hard-block where you can, offer an API so people
have a sanctioned path, serve conditional requests properly, and remember that **an
aggressive block is also blocking legitimate researchers, accessibility tools, and
archives.**
