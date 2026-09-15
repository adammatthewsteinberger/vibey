---
name: scraping-tooling-extraction-and-blocking
description: "Use when building the scraper: how the modern web actually serves data (server-rendered, client-rendered, and the internal JSON API behind the page — the single most valuable technique here), the structured data sites give you for free, pagination and state, the tool ladder from requests and curl_cffi through Scrapy and Playwright to managed services, parsing and extraction including LLM versus deterministic selectors, and why you are getting blocked — TLS and HTTP fingerprinting, headless detection, and the honest guidance."
---

# Web Scraping: How the Web Serves Data, the Tool Ladder, Parsing, and Blocking

> **Part 2 of 5** of the *Web Scraping* reference (plugin `web-scraping`), covering §4–§7. Sibling skills: `scraping-legal-landscape-and-permissions` (§0–§3), `scraping-scale-reliability-and-data-quality` (§8–§10), `scraping-ethics-ai-corpora-and-site-defense` (§11–§13), `scraping-reference` (§14–§19). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    wrong data is the characteristic failure of this field** (§9 → `scraping-scale-reliability-and-data-quality`), and it's worse than
>    a crash because nobody notices.

---

## §4. How the Web Serves Data

**[DURABLE] Understanding this determines your tool choice (§5) and saves enormous effort.**

### 4.1 The three shapes

| Shape | How to tell | What to use |
|---|---|---|
| **Server-rendered HTML** | Data is in "View Source" | **HTTP client + parser.** Fastest, cheapest |
| **Client-rendered (SPA)** | View Source is a near-empty shell; data appears after JS runs | §4.2 — check for an API first |
| **Hybrid / progressive** | Some in HTML, more loaded on scroll or interaction | Usually §4.2 |

### 4.2 The single most valuable technique in scraping

**[DURABLE] Open DevTools → Network → XHR/Fetch, and reload the page.**

If content loads via JavaScript, **it is almost always coming from an API endpoint
returning JSON** — and calling that endpoint directly is **dramatically faster, more
stable, and less resource-intensive for both parties** than driving a browser. You get
clean structured data instead of parsing markup, and the JSON schema changes far less often
than the CSS does.

**⚠️ This is the technique that most distinguishes people who find scraping easy from
people who find it hard.** Before reaching for a headless browser, always check whether
there's a JSON endpoint behind the page. Also check the **`__NEXT_DATA__`**,
`window.__INITIAL_STATE__`, or equivalent embedded-JSON blobs many frameworks leave in the
HTML — the full dataset is frequently sitting there already serialized.

### 4.3 The structured data sites give you for free

**Sitemaps** (`/sitemap.xml`, often listed in robots.txt) enumerate URLs — **use these
instead of crawling links**. **JSON-LD / schema.org markup** in `<script type="application/
ld+json">` gives you clean product, article, and organization data because sites publish it
for search engines. **OpenGraph and meta tags**, **RSS/Atom feeds**, **microdata**.
**⚠️ Checking for these first regularly turns a two-day scraper into a two-hour one.**

### 4.4 Pagination and state

Offset (`?page=2`), cursor-based (more reliable, and **immune to the shifting-window
problem** where new items push results across page boundaries mid-crawl), infinite scroll
(usually an API call — §4.2), and **POST-based search with hidden state tokens** (the
awkward case, requiring session handling).

---

## §5. The Tool Ladder

**[DURABLE] Climb only as far as you need. Each rung costs an order of magnitude more in
resources, complexity, and fragility.**

```
1. requests / httpx        static HTML. Fastest, simplest, cheapest
2. curl_cffi / httpmorph   same speed, but presents a realistic TLS fingerprint (§7.2)
3. Scrapy                  many URLs, one site — concurrency, retries, pipelines,
                           throttling, dedup, all built in
4. Playwright              JavaScript rendering genuinely required
5. Managed service         when the above is more work than it's worth
```

### 5.1 The tools

| Tool | Notes |
|---|---|
| **requests / httpx** | The baseline. `httpx` adds async and HTTP/2 |
| **curl_cffi** | HTTP client that impersonates real browser TLS fingerprints — **same speed as `requests`, far less trivially detectable** |
| **Beautiful Soup** | Forgiving HTML parser. Slow but pleasant |
| **lxml / selectolax** | **Much faster** parsing; use when volume matters |
| **Scrapy** | **The framework for crawling at scale.** Built-in concurrency, `AutoThrottle`, retries, middleware, item pipelines, dedup, and `robots.txt` obedience by default |
| **Playwright** | **[VERSIONED] The default browser-automation choice for new projects in 2026.** Chromium, Firefox, and WebKit; auto-waiting; multiple language bindings; parallel browser contexts |
| **Puppeteer** | Chrome-only. Fine to maintain, little reason to start new work with it |
| **Selenium** | Widely deployed, weakest on stealth (the WebDriver flag and navigator properties are trivially detectable) |
| **Managed / API services** | ScrapingBee, ScraperAPI, Bright Data, Apify, Browserless, Zyte, Scrapfly, Firecrawl — they handle browsers, proxies, and retries. **Usually cheaper than your engineering time** at moderate scale |

**Non-Python**: **Colly** (Go — very fast), **Crawlee** (Node/Python — batteries-included),
**Cheerio** (Node parsing), **Nokogiri** (Ruby), **jsoup** (Java).

### 5.2 Choosing

```
Does the page need JavaScript to render the data you want?
├─ NO  → 100+ URLs from one site? → Scrapy
│        Otherwise → requests/httpx (+ curl_cffi if blocked on fingerprint)
└─ YES → Did you check DevTools for a JSON endpoint first? (§4.2)  ← DO THIS
         ├─ Endpoint exists → go back to the NO branch. You just saved 10× the cost
         └─ Genuinely needs a browser → Playwright
                                        → too much operational burden? Managed service
```

**[DURABLE] Headless browsers cost roughly 10–100× more CPU, memory, and time per page
than an HTTP request.** At any real volume that's the dominant cost line, and it's also
the dominant load you're putting on the target. **Use one only when you've confirmed you
need it.**

---

## §6. Parsing and Extraction

**Selectors**: **CSS selectors** for most work (readable, sufficient), **XPath** when you
need axes CSS can't express (`following-sibling`, `ancestor`, text-content matching).

**[DURABLE] Selector stability is what determines your maintenance burden**, and it's worth
deliberate thought:
```
✓ STABLE    semantic ids, data-* attributes, ARIA roles, schema.org markup,
            structural relationships to stable text labels
⚠️ FRAGILE  auto-generated class names (`css-1x7f2k9` — these change every build),
            deep positional paths (`div > div > div:nth-child(3)`),
            anything tied to visual layout
```
**Prefer anchoring to meaning rather than to position.** "The `<dd>` following the `<dt>`
containing 'Price'" survives a redesign that "the fourth div" does not.

**Always extract defensively**: assume any field may be missing, return `None` rather than
raising, **and record that it was missing** (§9 → `scraping-scale-reliability-and-data-quality`). And **normalize at extraction time** —
strip whitespace, parse dates into datetimes with timezones, convert prices to numbers
*with their currency*, resolve relative URLs against the base.

**[VERSIONED] LLM-assisted extraction** is now practical for messy or highly variable
pages, and tools like Firecrawl and various "AI scraping" products build on it. **⚠️ The
trade-offs are real**: cost per page, latency, non-determinism, and **hallucinated fields
that look plausible** — which is §9 → `scraping-scale-reliability-and-data-quality`'s failure mode with a new cause. **The defensible
pattern is LLM-assisted *selector generation* (deterministic at runtime) rather than
LLM-in-the-loop extraction**, plus validation on everything.

---

## §7. Why You're Getting Blocked

**[DURABLE] Understand detection so you can be a better-behaved client — and so you can
recognize when a site is clearly telling you to stop.** That second reading matters
legally now (§1.4 → `scraping-legal-landscape-and-permissions`).

### 7.1 What sites look at

| Signal | What it means |
|---|---|
| **Rate and volume** | The most common trigger, and **the one that's your fault** |
| **IP reputation** | Datacenter ranges are trivially identifiable; residential and mobile less so |
| **TLS/JA3/JA4 fingerprint** | ⚠️ Your HTTP library's TLS handshake **does not look like a browser's**, regardless of what User-Agent you set — this is why `curl_cffi` exists |
| **HTTP/2 fingerprint** | Frame ordering and settings differ between clients |
| **Headers** | Missing, inconsistent, or implausible header sets — especially **`Sec-CH-UA` and friends that headless browsers omit by default** |
| **Browser fingerprint** | Canvas, WebGL, fonts, screen, timezone, and automation-framework artifacts |
| **Behaviour** | Perfectly-timed requests, no mouse movement, impossible navigation speed, no asset loading |
| **Honeypots** | Links invisible to humans that only a crawler would follow |

**Commercial systems** (Cloudflare, DataDome, Akamai, PerimeterX/HUMAN, Imperva) combine
these with machine learning at network scale. **[VERSIONED] Cloudflare's "AI Labyrinth"**
and similar tarpit approaches now actively feed crawlers generated content rather than
simply blocking — **which means "my scraper is working" is no longer proof that your data
is real** (§9 → `scraping-scale-reliability-and-data-quality`).

### 7.2 The honest guidance

**[DURABLE] Most blocking is a rate problem, and the fix is to slow down.** Before anything
else: reduce concurrency, add delays, cache aggressively, use conditional requests, and
crawl off-peak (§11 → `scraping-ethics-ai-corpora-and-site-defense`). This resolves a large share of blocks and is what you should have
been doing anyway.

**Legitimate technical fixes**: send a **complete, coherent, honest header set** (a
descriptive User-Agent with contact info — **not** a spoofed Chrome string); use
`curl_cffi` so your TLS fingerprint matches the client you claim to be; handle cookies and
sessions properly; respect `Retry-After` and back off exponentially on 429/503.

> **⚠️ GOTCHA — the line you need to think about before crossing.** There is a meaningful
> difference between **"my client is being misidentified as malicious, so I'll make it
> present itself accurately and slow down"** and **"this site has deployed measures to stop
> automated collection, so I'll defeat them."**
>
> **The second is what DMCA §1201 claims target** (§1.4 → `scraping-legal-landscape-and-permissions`). Reddit's theory against
> Perplexity is precisely that rate limits and anti-bot systems are technological
> protection measures and defeating them is circumvention. **Solving CAPTCHAs at scale,
> rotating residential proxies specifically to evade IP-based blocking, and reverse-
> engineering anti-bot challenges sit on the wrong side of that line** — regardless of
> whether the underlying data is public.
>
> **A hard block, delivered consistently after you've slowed down and identified yourself,
> is the site's answer.** The professional response is to seek permission, license the
> data, use an official API, or walk away — not to escalate.
