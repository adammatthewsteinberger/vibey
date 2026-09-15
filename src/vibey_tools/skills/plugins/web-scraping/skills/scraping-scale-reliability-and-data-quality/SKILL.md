---
name: scraping-scale-reliability-and-data-quality
description: "Use when a scraper has to run reliably and produce trustworthy data: scale and reliability engineering (concurrency, rate limiting, retries and backoff, proxies, scheduling), data quality and validation against the silent breakage that produces plausible-looking wrong data for months, and storage, pipelines and operations including deduplication, change detection and monitoring."
---

# Web Scraping: Scale and Reliability, Data Quality, and Storage and Operations

> **Part 3 of 5** of the *Web Scraping* reference (plugin `web-scraping`), covering §8–§10. Sibling skills: `scraping-legal-landscape-and-permissions` (§0–§3), `scraping-tooling-extraction-and-blocking` (§4–§7), `scraping-ethics-ai-corpora-and-site-defense` (§11–§13), `scraping-reference` (§14–§19). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    happens to be what keeps you unblocked (§11 → `scraping-ethics-ai-corpora-and-site-defense`).
> 3. **Scrapers rot.** A scraper is a hard dependency on someone else's HTML, which they
>    will change without telling you. **Silent breakage that produces plausible-looking
>    wrong data is the characteristic failure of this field** (§9), and it's worse than
>    a crash because nobody notices.

---

## §8. Scale and Reliability

**[DURABLE] The architecture that survives contact with reality:**

```
URL frontier (queue, deduplicated, prioritized)
   → fetcher pool (rate-limited PER DOMAIN, retries with backoff)
     → response cache (raw HTML stored — see below)
       → parser (pure function: HTML → structured record)
         → validator (§9)
           → storage + change detection
```

**[DURABLE] Store the raw response, not just the parsed output.** This is the single most
valuable architectural decision in a scraping system: when your parser turns out to have
been wrong for three weeks, **you can re-parse history instead of re-crawling** — which is
cheaper for you and, more importantly, costs the target site nothing.

**Rate limiting is per-domain, not global.** A token bucket per host, with concurrency
caps. Scrapy's `AutoThrottle` adapts to observed latency, which is both polite and
effective.

**Retries**: exponential backoff **with jitter**, only on transient failures (429, 5xx,
timeouts), with a cap. **⚠️ Retrying a 404 or a 403 is just extra load** — classify errors
before retrying.

**Also**: **conditional requests** (`If-Modified-Since`, `If-None-Match` → 304 responses
cost the server almost nothing), **incremental crawling** (only fetch what changed —
sitemaps with `lastmod` help), **checkpointing** so a crash doesn't restart from zero,
**idempotent writes** so a re-run doesn't duplicate, and **distributed queues** (Redis,
SQS) when one machine isn't enough.

**Proxies**: legitimate uses exist — geographic content variation, avoiding
single-IP saturation, and reliability. **⚠️ But note that "rotating residential proxies to
evade blocking" is the use case §7.2 → `scraping-tooling-extraction-and-blocking` flags**, and separately, **residential proxy networks
have documented supply-chain ethics problems** around how consumer bandwidth is sourced and
whether those users understood what they consented to. That's worth knowing before you buy.

---

## §9. Data Quality

**[DURABLE] This is the section that separates a scraper from a data pipeline, and it is
the one people skip.**

> **⚠️ GOTCHA — silent breakage is the characteristic failure of this field.** A site
> redesigns. Your selector no longer matches. Your extractor returns empty strings.
> **Your pipeline runs green, your dashboard shows data, and every number is wrong.**
> Nobody notices for weeks because nothing crashed.
>
> **A scraper that crashes is a good scraper. A scraper that silently returns `None` for
> the price field is a liability.**

**Validate every record**: required fields present; types correct; **values within
plausible ranges** (a price of 0 or 10,000,000 is a parser bug, not a bargain); enums in
their expected set; dates sane.

**Validate every batch — this is where breakage actually surfaces**: record count within
expected bounds, **null rate per field compared against the historical baseline** (the
single most effective breakage detector), value distributions not suddenly shifted,
duplicate rate stable. **Alert on the delta, not on absolute failure.**

**Cross-check** against a second source, an official API, or a manual spot-check on a
sample. **[DURABLE] Manually verify a handful of records at the start and after every
change** — it takes ten minutes and catches the class of error nothing else will.

**Also track provenance**: source URL, fetch timestamp, parser version, and raw-response
reference on every record. When you find a problem you need to know exactly which records
are affected.

**⚠️ And in 2026, add one more check**: with tarpit and content-poisoning defences now
deployed (§7.1 → `scraping-tooling-extraction-and-blocking`), **verify that what you're collecting is real content**, not generated
filler served to something the site classified as a bot.

---

## §10. Storage and Operations

**Format by purpose**: JSON/JSONL for raw and semi-structured; **Parquet** for analytics
(columnar, compressed, and far faster to query); a relational database for
relationships and deduplication; object storage for raw HTML archives; a vector store only
if you're doing retrieval (§12 → `scraping-ethics-ai-corpora-and-site-defense`).

**[DURABLE] Design for change detection, not just snapshots.** Most scraping value comes
from *what changed* — price movements, new listings, removed items. That means either
storing versions with valid-from/valid-to, or storing a content hash per record and
recording transitions.

**Schema evolution**: sites add and remove fields, so store the raw payload alongside the
parsed record and **make your schema additive**.

**Operational monitoring**: success rate by domain, latency, block/CAPTCHA rate,
records-per-run against baseline, **field-level null rates** (§9), cost per record, and
queue depth. **Alert on trends, not just failures** — a slow decline in fields extracted
is the signal that matters.

**Legal and ethical hygiene at the data layer**: know your **retention period** and
enforce it; **be able to delete a person's data on request** if you hold personal data
(GDPR/CCPA rights are not optional and "it's in a training set" is not an answer — §1.6 → `scraping-legal-landscape-and-permissions`);
document **provenance and legal basis per source**, because that documentation is what a
regulator will ask for and it is very hard to reconstruct retroactively.
