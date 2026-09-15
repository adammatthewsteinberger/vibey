---
name: scraping-reference
description: "Use when checking a scraping anti-pattern, weighing a contested question (is scraping public data ethical, does robots.txt bind you, should sites block AI crawlers, is pay-per-crawl the right model, LLM extraction versus deterministic selectors, managed service versus building it yourself), confirming whether a legal or tooling claim is still current (snapshot verified August 2026), finding the primary documentation and books, or needing the before-you-write-code checklist, the operating rules, and a triage list. Companion to the other web-scraping skills."
---

# Web Scraping: Anti-Patterns, Contested Questions, Currency, and Canon

> **Part 5 of 5** of the *Web Scraping* reference (plugin `web-scraping`), covering §14–§19. Sibling skills: `scraping-legal-landscape-and-permissions` (§0–§3), `scraping-tooling-extraction-and-blocking` (§4–§7), `scraping-scale-reliability-and-data-quality` (§8–§10), `scraping-ethics-ai-corpora-and-site-defense` (§11–§13). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §16 below for the currency snapshot and what goes stale first.

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
>    wrong data is the characteristic failure of this field** (§9 → `scraping-scale-reliability-and-data-quality`), and it's worse than
>    a crash because nobody notices.

---

## §14. Anti-Patterns

| Anti-pattern | Why |
|---|---|
| Asking "is scraping legal" as one question | It's four questions with different answers (§1.1 → `scraping-legal-landscape-and-permissions`) |
| Scraping a service you hold an account with, against its terms | **The single highest-risk configuration** — hiQ won on CFAA and lost on contract for $500K (§1.3 → `scraping-legal-landscape-and-permissions`) |
| Treating hiQ as blanket permission | It covers **logged-out public access under the CFAA**. Nothing else |
| Assuming public = free to use for any purpose | Copyright, database rights, and GDPR all say otherwise (§1.5 → `scraping-legal-landscape-and-permissions`) |
| Assuming public personal data is outside GDPR | **The Clearview cases turned on legal basis and transparency, not publicness** (§1.5 → `scraping-legal-landscape-and-permissions`) |
| Buying a pre-scraped dataset to avoid the compliance problem | EDPB guidelines cover acquirers too (§1.6 → `scraping-legal-landscape-and-permissions`) |
| Defeating anti-bot measures | **DMCA §1201 theories now target exactly this** (§1.4 → `scraping-legal-landscape-and-permissions`, §7.2 → `scraping-tooling-extraction-and-blocking`) |
| Ignoring a consistent hard block | It's the site's answer. Escalating is the risk (§7.2 → `scraping-tooling-extraction-and-blocking`) |
| Scraping before checking for an API, dataset, feed, or licence | Cheaper, more stable, no legal layer (§2 → `scraping-legal-landscape-and-permissions`) |
| Not opening DevTools to look for a JSON endpoint | **The single highest-leverage 60 seconds in this domain** (§4.2 → `scraping-tooling-extraction-and-blocking`) |
| Reaching for a headless browser by default | 10–100× the cost per page, for you and for them (§5.2 → `scraping-tooling-extraction-and-blocking`) |
| Ignoring sitemaps and crawling links instead | They enumerated the URLs for you (§4.3 → `scraping-tooling-extraction-and-blocking`) |
| Selectors bound to generated class names or `nth-child` | Breaks on the next deploy (§6 → `scraping-tooling-extraction-and-blocking`) |
| Spoofing a Chrome User-Agent while sending a Python TLS fingerprint | Inconsistent, and detected on the mismatch (§7.1 → `scraping-tooling-extraction-and-blocking`) |
| Blaming the site when the real problem is your request rate | Most blocking is a rate problem (§7.2 → `scraping-tooling-extraction-and-blocking`) |
| Not storing raw responses | You'll re-crawl history you already have (§8 → `scraping-scale-reliability-and-data-quality`) |
| Global rate limit instead of per-domain | Hammers one host while idling on others |
| Retrying 404s and 403s | Extra load, zero chance of success |
| A scraper that returns `None` instead of failing | **Silent wrong data is worse than a crash** (§9 → `scraping-scale-reliability-and-data-quality`) |
| No null-rate baseline per field | The most effective breakage detector, and it's cheap (§9 → `scraping-scale-reliability-and-data-quality`) |
| Never manually spot-checking records | Ten minutes catches what nothing else will |
| Assuming everything you collected is real content | Tarpits now serve generated filler (§7.1 → `scraping-tooling-extraction-and-blocking`, §9 → `scraping-scale-reliability-and-data-quality`) |
| No contact information in the User-Agent | You get banned instead of emailed (§11 → `scraping-ethics-ai-corpora-and-site-defense`) |
| Same crawl rate for a major platform and a hobbyist blog | Scale courtesy to their infrastructure (§11 → `scraping-ethics-ai-corpora-and-site-defense`) |
| Treating AI-training scraping like ordinary scraping | Materially different legal regime (§12 → `scraping-ethics-ai-corpora-and-site-defense`) |
| Toggling "block AI bots" without reading the mixed-use rule | **You may have blocked Googlebot** (§3.2 → `scraping-legal-landscape-and-permissions`, §13 → `scraping-ethics-ai-corpora-and-site-defense`) |
| No documented legal basis or provenance per source | Exactly what a regulator asks for, and unreconstructable later (§10 → `scraping-scale-reliability-and-data-quality`) |
| No deletion capability for personal data | Rights are not optional, and models can't easily forget (§1.6 → `scraping-legal-landscape-and-permissions`, §10 → `scraping-scale-reliability-and-data-quality`) |

---

## §15. Contested Questions

**15.1 Is scraping public data ethical?** *For*: information wants to be accessible, public
data supports research, journalism, price transparency, and competition, and the hiQ court
warned specifically about **"information monopolies that would disserve the public
interest."** *Against*: users posted to a platform, not to the world's data brokers; scale
changes the character of the act; and site operators bear real infrastructure cost. **Both
positions are seriously held and the answer plainly depends on the data and the use.**

**15.2 Does robots.txt bind you?** Technically voluntary and legally not an access control
— **but ignoring it evidences bad faith, and machine-readable opt-outs now carry copyright
weight under the EU AI Act.** The "it's just a suggestion" position has weakened
considerably.

**15.3 Should sites block AI crawlers?** §13 → `scraping-ethics-ai-corpora-and-site-defense`. The historic bargain (content for traffic)
has demonstrably broken — crawl-to-referral ratios in the hundreds-to-thousands support
that — but blocking forfeits AI-answer visibility, and nobody yet knows what that's worth.

**15.4 Is pay-per-crawl the right model?** *For*: it prices an externality and compensates
creators. *Against*: it concentrates enormous gatekeeping power in one CDN, disadvantages
smaller AI developers and researchers, and **the "web as open commons" framing is genuinely
lost if crawling requires payment rails.**

**15.5 Should the CFAA/§1201 line move?** *For scrapers*: hiQ's monopoly reasoning, and
§1201 was written for DRM, not rate limiters. *For platforms*: they bear the cost, and
users didn't consent to bulk collection. **Reddit v. Perplexity may substantially determine
this.**

**15.6 LLM extraction vs. deterministic selectors.** §6 → `scraping-tooling-extraction-and-blocking`. Robustness and speed of
development against cost, non-determinism, and **hallucinated fields that pass validation**.

**15.7 Managed service vs. build it yourself.** *Service*: faster, handles the operational
layer, often cheaper than engineering time. *Against*: cost at scale, vendor lock-in, less
control, and **you inherit their collection practices and their legal posture** — which,
given §1 → `scraping-legal-landscape-and-permissions`, is not a minor consideration.

---

## §16. Currency Snapshot — verified August 2026

| Thing | Status as of Aug 2026 | Decay risk |
|---|---|---|
| **CFAA line** | **Van Buren (2021)** narrowed "exceeds authorized access." **hiQ v. LinkedIn (9th Cir., April 2022)**: scraping publicly accessible data doesn't violate the CFAA. **Meta v. Bright Data (N.D. Cal., Jan 2024)**: Judge Chen dismissed Meta's CFAA claim over **logged-out** public Facebook/Instagram scraping. **Logged-out public scraping is defensible** | Low |
| **The contract counterweight** | ⚠️ **hiQ lost on breach of LinkedIn's User Agreement (accepted by creating accounts)** — **$500,000, permanent injunction, destruction of the scraped corpus.** In *Meta v. Bright Data* the contract claim **partially survived only for the period of an active contractual relationship**; general browsewrap ToS was treated as a **weaker basis** | Low |
| **⚠️ The §1201 shift** | **Reddit sued Perplexity AI and data-collection providers in late 2025**, claiming **DMCA §1201 circumvention of rate limits and anti-bot systems** for AI training. **Reframes the question from "was it public?" to "did you defeat a protection?"** Pending as of early 2026. Similar theories in creator suits over YouTube scraping | **High** |
| **EDPB Guidelines 03/2026** | ⚠️ **Adopted at the July 2026 plenary** (published 7 July, adopted 8 July) — **first pan-EU framework on web scraping for generative AI**, confirming **GDPR applies in full with no AI carve-out.** Reported positions: **consent unlikely to be a valid basis**; **legitimate interest requires a documented three-part test per deployment**; **data minimisation before scraping**; **near-prohibition on sensitive data**; **personal data can't easily be deleted from a trained model.** Covers **acquirers of pre-scraped datasets**, not just scrapers. Companion anonymisation guidelines set a three-criterion test. **Draft — consultation open to 30 October 2026** | **High** |
| **EU AI Act** | In force 1 Aug 2024; GPAI obligations from **2 Aug 2025**; ⚠️ **enforcement teeth from 2 August 2026** — GPAI fines up to **€15M or 3% of turnover**. GPAI providers must **publish a training-data summary** and **respect machine-readable copyright opt-outs**, giving robots.txt and TDM reservations legal weight. **Bans untargeted scraping of facial images** for FR databases (targeted collection distinguished) | Medium |
| **Clearview line** | **€30.5M (Dutch DPA, 2024)**, actions from the Italian Garante and CNIL, **$75M+ cumulative across US/UK/EU**. **UK Upper Tribunal held Clearview within UK GDPR scope** despite being wholly outside the UK, rejecting the law-enforcement exemption for a private company — a potential **£7.5M ICO fine**. ⚠️ **These cases turned on legal basis and transparency, not on whether the data was public** | Low |
| **Cloudflare: the enforcement layer** | **July 2025 "Content Independence Day"**: one-click Block AI Bots + **Pay Per Crawl** private beta reviving **HTTP 402**, Cloudflare as merchant of record. **1 July 2026**: replaced by **three categories — Search, Agent, Training** — each with allow / block-on-ad-pages / block-everywhere, **free tier included**. ⚠️ **15 September 2026: Training and Agent blocked by default on ad-serving pages** for new domains, new sites of existing customers, and **all existing free-tier customers**; Search allowed by default. **Pay Per Crawl evolving toward "Pay Per Use"** | **High** |
| **⚠️ The mixed-use trap** | **If a zone blocks Training, multi-purpose crawlers including Googlebot, Applebot and BingBot are blocked too**, even where Search is allowed — applying only to zones that actively enabled Training blocking. **Opt out via Security settings before 15 September 2026** to preserve current behaviour | **High** |
| **Content Signals / standards** | Cloudflare's **Content Signals** gained a **`use` parameter**: **Immediate** (no storage/reuse), **Reference** (index, excerpt, link back), **Full** (summarize/reproduce). Not enforceable by robots.txt; compliance reported via BotBase. Competing efforts: **IETF AIPREF** (Content-Usage header, standards-track milestone targeted Aug 2026), **RSL**, **ai.txt**, **TDMRep**. **No winner** | **High** |
| **Crawler economics** | Cloudflare-network analysis (Q1 2026): **89.4% of AI crawler traffic serves training or mixed purposes rather than search**; GPTBot the most-blocked AI crawler. Crawl-to-referral ratios tracked in the hundreds-to-thousands per referral, **improving through 2026** (one series reported Anthropic's falling 3,386:1 → 1,917:1 June→July; OpenAI 647:1 → 251:1) | **High** |
| **Tooling** | **Playwright is the default browser-automation choice for new 2026 projects** (Chromium/Firefox/WebKit, auto-waiting, multi-language). Puppeteer maintenance-mode-ish for new work; **Selenium weakest on stealth** (WebDriver flag trivially detected). **`curl_cffi` / `httpmorph`** for realistic TLS fingerprints at HTTP-client speed. **Scrapy** remains the scale framework. ⚠️ **Cloudflare's "AI Labyrinth"** and similar tarpits serve generated content rather than blocking | Medium |

**Goes stale fastest:** the Cloudflare defaults and the standards contest; the EDPB
guidelines as they move from draft to final; Reddit v. Perplexity. **Essentially never
stale:** §4 → `scraping-tooling-extraction-and-blocking` (how pages serve data), §6 → `scraping-tooling-extraction-and-blocking` (selector stability), §8 → `scraping-scale-reliability-and-data-quality` (architecture), §9 → `scraping-scale-reliability-and-data-quality` (data
quality), §11 → `scraping-ethics-ai-corpora-and-site-defense` (ethics), §14.

---

## §17. The Canon

### 17.1 Primary documentation
**RFC 9309** (Robots Exclusion Protocol), **Scrapy docs** (genuinely excellent — read the
architecture overview even if you use something else), **Playwright docs**,
**MDN** on HTTP semantics, caching, and conditional requests, **schema.org**,
**Cloudflare's AI Crawl Control docs** and the Content Independence Day posts (§3.2 → `scraping-legal-landscape-and-permissions`),
**EDPB** guidelines and **EUR-Lex** for the AI Act text, and **Common Crawl** documentation
(both as a data source and as a model of how large-scale crawling is done responsibly).

### 17.2 Books and long-form
| Author | Work | Why |
|---|---|---|
| **Ryan Mitchell** | ***Web Scraping with Python*** (O'Reilly) | The standard book; strong on ethics as well as technique |
| **Seppe vanden Broucke & Bart Baesens** | *Practical Web Scraping for Data Science* | Good on the pipeline, not just the fetch |
| **Manning / Packt Scrapy titles** | — | Useful if you're committing to Scrapy |
| **Julia Angwin / The Markup** | Investigative work built on scraping | **The best demonstration of why this matters** — public-interest journalism that would be impossible otherwise |
| **Bellingcat's Online Investigation Toolkit** | — | OSINT methodology, and unusually thoughtful on ethics |

### 17.3 Sites and people
**ScrapFly**, **ScrapingBee**, **Oxylabs**, **Bright Data**, and **Apify** blogs are
technically strong and **commercially motivated — read them for technique, discount the
buy-our-product conclusion.** **Cloudflare Radar** and the Cloudflare blog for the crawler
economics data. **`r/webscraping`** for practitioner reality. **Zyte's** engineering
writing (they maintain Scrapy). **EFF** and **Public Knowledge** on the CFAA/§1201 policy
debate. **IAPP** for the privacy layer. Follow the **Reddit v. Perplexity** docket if you
do anything at scale.

---

## §18. Quick Reference

### 18.1 Before you write any code
- [ ] Is there an API, dataset, feed, or licence? (§2 → `scraping-legal-landscape-and-permissions`)
- [ ] **Have you opened DevTools → Network → XHR to look for a JSON endpoint?** (§4.2 → `scraping-tooling-extraction-and-blocking`)
- [ ] Is there a sitemap or schema.org markup? (§4.3 → `scraping-tooling-extraction-and-blocking`)
- [ ] Read `robots.txt`
- [ ] Read the Terms of Service — **and do you hold an account there?** (§1.3 → `scraping-legal-landscape-and-permissions`)
- [ ] Does the data include personal data? If so, what's your legal basis? (§1.5 → `scraping-legal-landscape-and-permissions`)
- [ ] Is this for AI training? Different regime (§12 → `scraping-ethics-ai-corpora-and-site-defense`)
- [ ] Documented: source, purpose, legal basis, retention (§10 → `scraping-scale-reliability-and-data-quality`)

### 18.2 Operating rules
- [ ] Descriptive User-Agent **with contact info**
- [ ] Per-domain rate limiting, conservative to start
- [ ] Conditional requests and caching
- [ ] Exponential backoff with jitter; honour `Retry-After`
- [ ] **Raw responses stored** so you can re-parse without re-crawling
- [ ] Per-field null-rate baseline with alerting
- [ ] Batch-level validation on count, distribution, and duplicates
- [ ] Provenance on every record
- [ ] Manual spot-check after every change
- [ ] A consistent hard block is respected, not escalated (§7.2 → `scraping-tooling-extraction-and-blocking`)

### 18.3 Triage
| Symptom | First look |
|---|---|
| 403 / CAPTCHA immediately | TLS fingerprint (try `curl_cffi`), header set, IP reputation (§7.1 → `scraping-tooling-extraction-and-blocking`) |
| Worked, then started failing | Rate — slow down first, before anything else (§7.2 → `scraping-tooling-extraction-and-blocking`) |
| Empty results, no error | **Selector broke.** Check null rates; this is the dangerous one (§9 → `scraping-scale-reliability-and-data-quality`) |
| Page loads in browser, empty from script | JavaScript rendering — **look for the JSON endpoint before reaching for a browser** (§4.2 → `scraping-tooling-extraction-and-blocking`) |
| Data looks plausible but is subtly wrong | Tarpit/generated content, or a partially-broken parser (§7.1 → `scraping-tooling-extraction-and-blocking`, §9 → `scraping-scale-reliability-and-data-quality`) |
| Works locally, blocked in production | Datacenter IP reputation |
| Slow and expensive | You're using a browser where an HTTP request would do (§5.2 → `scraping-tooling-extraction-and-blocking`) |
| Duplicates across runs | Non-idempotent writes; offset pagination with a shifting window (§4.4 → `scraping-tooling-extraction-and-blocking`, §8 → `scraping-scale-reliability-and-data-quality`) |
| Site owner sends an angry email | **Good — you were contactable.** Respond, slow down, negotiate (§11 → `scraping-ethics-ai-corpora-and-site-defense`) |

---

## §19. Sources and Method

**Method.** Narrative (not systematic) review. The durable material — §4 → `scraping-tooling-extraction-and-blocking` (how pages serve
data), §5–§6 → `scraping-tooling-extraction-and-blocking` (tooling and extraction), §8 → `scraping-scale-reliability-and-data-quality` (architecture), §9 → `scraping-scale-reliability-and-data-quality` (data quality), §10 → `scraping-scale-reliability-and-data-quality`, §11 → `scraping-ethics-ai-corpora-and-site-defense`
(ethics), §14 — rests on HTTP standards, long-stable engineering practice, and failure
modes reported consistently by practitioners. Every **time-sensitive** claim — and in this
domain the **legal layer is moving faster than the technical layer** — was verified against
a primary or near-primary source in **August 2026** and is flagged in §16 with a decay-risk
rating. §7 → `scraping-tooling-extraction-and-blocking` describes detection mechanisms at the conceptual level for the purpose of
diagnosing blocks and behaving better; **it deliberately does not provide evasion
techniques for specific commercial anti-bot products**, both because §1.4 → `scraping-legal-landscape-and-permissions` makes that
legally live and because the professional answer to a deliberate block is to seek
permission rather than escalate.

**Search log** (August 2026): web scraping case law (hiQ, Van Buren, Meta v. Bright Data,
Reddit v. Perplexity) · Cloudflare AI crawler controls, Pay Per Crawl, and the robots.txt
standards landscape · Playwright/Scrapy/tooling comparison and bot detection · GDPR
scraping enforcement, EDPB guidelines, and the EU AI Act.

**Primary and near-primary sources consulted (selected):**
- **Cloudflare's own blog and docs** — "Content Independence Day" (July 2025 and the
  July 2026 "Your site, your rules" post), AI Crawl Control documentation, and the
  Pay Per Crawl changelog; **Help Net Security** on the content-use levels and the
  mixed-use crawler rule
- **EDPB** Guidelines 03/2026 on web scraping for generative AI, via **Sidley's Data
  Matters** analysis and contemporaneous reporting; **EU AI Act** GPAI obligations and
  timelines
- **Gowling WLG** and **URM Consulting** on the UK Upper Tribunal's Clearview decision;
  **FPF** on the AI Act's targeted/untargeted facial-scraping distinction; Dutch DPA and
  other DPA enforcement reporting
- Case-law summaries of **Van Buren**, **hiQ v. LinkedIn** (including the December 2022
  settlement terms), and **Meta v. Bright Data** from multiple independent legal and
  industry analyses; contemporaneous reporting on **Reddit v. Perplexity**'s §1201 theory
- Tooling comparisons from **Browserless**, **ScrapingBee**, **ScrapFly**, **Oxylabs**,
  and independent practitioner write-ups

**Confidence statement.** **High confidence** in §4–§11 → `scraping-tooling-extraction-and-blocking`, `scraping-scale-reliability-and-data-quality`, `scraping-ethics-ai-corpora-and-site-defense` and §18 — HTTP semantics,
extraction practice, and pipeline engineering are stable and consistently described.
**High confidence** in the Cloudflare mechanics and dates, which come from Cloudflare's own
announcements and documentation. **Moderate confidence on the legal material in §1 → `scraping-legal-landscape-and-permissions`**, and
the caveats matter: **case summaries came largely from law-firm and industry analyses
rather than from the opinions themselves**; **US case law is circuit-specific and hiQ is a
Ninth Circuit holding**; **Reddit v. Perplexity was pending and its outcome is genuinely
unknown**; and **the EDPB guidelines were in draft with consultation open to 30 October
2026**, so the positions summarized in §1.6 → `scraping-legal-landscape-and-permissions` may change before adoption. **Lower confidence
on the crawl-to-referral ratio figures** in §16 — they come from a single analytics
provider's network view, methodology varies, and the numbers moved substantially within
2026. **This is not legal advice**; §1 → `scraping-legal-landscape-and-permissions` maps frameworks and identifies the questions to put
to counsel, and the answer for any specific operation depends on jurisdiction, data type,
data subject, and purpose in ways no general document can resolve.
