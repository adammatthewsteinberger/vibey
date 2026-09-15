---
name: social-platform-apis-and-open-protocols
description: "Use when integrating with a social platform or evaluating a federated one: what happened to the platform API landscape and how to survive pricing and policy changes, the state of the X API in 2026 and the wider landscape (Meta, LinkedIn, Reddit, YouTube, Discord), and the open protocols — ActivityPub and the fediverse, the AT Protocol and Bluesky, what federation actually costs to run, and why the two do not interoperate. Includes the router for the whole social-media-engineering reference."
---

# Social Media Engineering: Platform APIs and the Open Protocols

> **Part 1 of 5** of the *Social Media Engineering* reference (plugin `social-media-engineering`), covering §0–§2. Sibling skills: `social-feed-graph-ranking-and-notifications` (§3–§6), `social-moderation-abuse-and-regulation` (§7–§9), `social-media-analytics-privacy-and-presence` (§10–§13), `social-reference` (§14–§19). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §16 → `social-reference` for the currency snapshot and what goes stale first.

> **How to read this.** The title spans two things and this document covers both, weighted
> toward the first: **§1–§12 → `social-feed-graph-ranking-and-notifications`, `social-moderation-abuse-and-regulation`, `social-media-analytics-privacy-and-presence` are about building and integrating with social systems;
> §13 → `social-media-analytics-privacy-and-presence` is about your own presence as a developer.** Skip to §13 → `social-media-analytics-privacy-and-presence` if that's what you came for.
>
> Three markers:
> - **[DURABLE]** — architecture, ranking, moderation, and abuse dynamics. Most of §2–§10 → `social-feed-graph-ranking-and-notifications`, `social-moderation-abuse-and-regulation`, `social-media-analytics-privacy-and-presence`.
> - **[VERSIONED]** — platform terms, pricing, protocols, regulation. ⚠️ **Verify all of
>   it; this is the fastest-moving material in the collection after AI.**
> - **[CONTESTED]** — genuine disagreement.
>
> **⚠️ GOTCHA** boxes mark what breaks, gets you banned, or gets you fined.
>
> **The three framings that organize everything below:**
> 1. **⚠️ Building on a platform API is building on rented land, and the rent changed.**
>    The 2023–2026 period established that platforms will reprice or withdraw access with
>    weeks of notice and no obligation. **Architect for that from day one** (§1).
> 2. **The hard problems are social, not technical.** Fan-out and ranking are solved
>    engineering; **moderation, abuse, and incentive design are not, and they scale
>    worse than your database does** (§7 → `social-moderation-abuse-and-regulation`, §8 → `social-moderation-abuse-and-regulation`).
> 3. **⚠️ Compliance is now an architecture input, not a legal afterthought.** Age
>    assurance, transparency reporting, and appeals mechanisms have to be designed in —
>    **and regulators have started saying explicitly that self-declaration is not
>    sufficient** (§9 → `social-moderation-abuse-and-regulation`).

---

## §0. Routing

| Asked about... | Go to |
|---|---|
| **Platform APIs — costs, terms, survival** | **§1** |
| Open protocols: ActivityPub, AT Protocol | §2 |
| Feed and timeline architecture | §3 → `social-feed-graph-ranking-and-notifications` |
| The social graph | §4 → `social-feed-graph-ranking-and-notifications` |
| Ranking and recommendation | §5 → `social-feed-graph-ranking-and-notifications` |
| Notifications, real-time, presence | §6 → `social-feed-graph-ranking-and-notifications` |
| **Moderation at scale** | **§7 → `social-moderation-abuse-and-regulation`** |
| Spam, bots, and abuse | §8 → `social-moderation-abuse-and-regulation` |
| **Regulation and compliance** | **§9 → `social-moderation-abuse-and-regulation`** |
| Media handling | §10 → `social-media-analytics-privacy-and-presence` |
| Analytics, metrics, experimentation | §11 → `social-media-analytics-privacy-and-presence` |
| Privacy, data, and deletion | §12 → `social-media-analytics-privacy-and-presence` |
| **Your own developer presence** | **§13 → `social-media-analytics-privacy-and-presence`** |
| "Don't do this" | §14 → `social-reference` |
| "Which side is right?" | §15 → `social-reference` |
| "Is this still current?" | §16 → `social-reference` |
| Resources | §17 → `social-reference` |

---

## §1. Platform APIs

**[VERSIONED — and the single most important practical section here.]**

### 1.1 What happened

**[DURABLE lesson, VERSIONED specifics] The 2023–2026 period ended the era of open social
APIs, and the pattern was consistent: reprice or restrict with short notice, and let
downstream developers absorb the consequences.**

**Twitter/X**: the free tier that had supported a decade of bots, research, and
third-party clients closed. ⚠️ **Developers on the free v1.1 API were given nine days to
migrate.**
**Reddit (July 2023)**: **$0.24 per 1,000 API calls** for commercial use with roughly
30 days' notice. **Apollo — the most-loved third-party client, 1.5M active users — shut
down** rather than absorb it, its developer having been told the cost would be
**~$20M/year**. ⚠️ **Pushshift, the academic Reddit archive, was terminated.** Reddit also
ended self-service access; **new applications require approval under a "Responsible
Builder Policy."**

**⚠️ The $20M figure became the defining anecdote for how API repricing redistributes risk
from the platform onto the downstream developer** — and it is the right thing to remember
before you build.

### 1.2 ⚠️ The X API in 2026

**[VERSIONED — verify before budgeting; this has changed repeatedly.]**

**As of February 2026, X moved new developers to pay-per-use and closed Basic and Pro to
new signups.** Legacy subscribers are grandfathered. Reported rates as of mid-2026:

| Action | Reported rate |
|---|---|
| Read your own posts/followers/lists | ~$0.001 per resource (cut sharply April 2026) |
| **Read a third-party post** | **~$0.005** — ⚠️ **the rate that dominates data projects** |
| User / follower / trends read | ~$0.010 |
| Create a plain post | ~$0.015 |
| ⚠️ **Create a post containing a URL** | **~$0.20** — **~13× a plain post** |

> **⚠️ GOTCHA — three structural traps beyond the per-call rates:**
> - **The 2,000,000 post-read monthly cap.** ⚠️ **At $0.005/read, hitting it means you've
>   spent ~$10,000 — and then you stop until the cycle resets or you move to Enterprise
>   (reported entry ~$42,000/month, custom contract, multi-week sales process).** There is
>   **no middle tier any more** — the $5,000 Pro plan that included full-archive search is
>   closed to new signups, creating a cliff between self-serve and Enterprise.
> - **⚠️ The URL surcharge lands hardest on exactly the automation people build**:
>   auto-posting newsletter links, blog posts, release announcements.
> - **⚠️ As of 20 April 2026, following, liking, and quote-posting were removed from
>   self-serve writes entirely** — withdrawn rather than repriced, Enterprise-only.
>   **If your product does social actions on a user's behalf, check this before designing.**
>
> **Also: your stated use case is contractually binding**, and materially changing it
> requires notifying X and getting approval.

**⚠️ The third-party reseller market exists and the price gap is enormous** — resellers
advertise reads at a small fraction of the official rate, and one comparison put the
official pay-per-use rate at roughly **33× a third-party's**. **But**: ⚠️ **scraping X
directly is explicitly prohibited by its terms**, resellers occupy a legally contested
position (see a web-scraping reference for why), and **you inherit their compliance
posture and their continuity risk.** **The common architecture that results: official API
for posting and authenticated actions, third party for reads at volume** — with the
trade-off understood and documented, not assumed away.

### 1.3 The wider landscape
**Meta Graph** — weeks of app review before permissions are granted; **LinkedIn** —
partnership agreements for anything beyond surface data; **TikTok** — formal application
process; **YouTube** — a quota ceiling rather than per-call pricing. **⚠️ The common shape:
approval gates rather than open signup, and apps that fail review lose endpoints they were
using in development.**

**[DURABLE] How to build so this doesn't kill you:**
- **⚠️ Abstract the platform behind your own interface** from day one. When terms change,
  you change one adapter.
- **Cache aggressively and store what you're permitted to store** — re-fetching is the
  cost centre.
- **Model your costs at projected volume, not current volume**, and know where the cliff
  is (§1.2).
- **⚠️ Have a fallback path** — a second provider, a degraded mode, or a plan to exit.
- **Don't make a single platform load-bearing** for your product's core value.
- **Read the terms, including the use-case obligation**, and re-read them at renewal.
- **⚠️ Assume the free tier will end.** It has, everywhere, repeatedly.

---

## §2. Open Protocols

**[VERSIONED — the structural alternative, and the two camps have not merged.]**

### 2.1 ActivityPub

**W3C standard since 2018**, powering **Mastodon, Pixelfed, PeerTube, Lemmy** and — notably
— **Meta's Threads**. **The model is server-to-server federation**: every user is an
**actor** with an **inbox** and an **outbox**; servers deliver activities to each other.
**Identity is tied to your instance** (`@you@server.social`), which is both the model's
simplicity and its central weakness.

**Scale**: **Mastodon around 10.5 million accounts**, with the **wider Fediverse around
11 million** including Pixelfed and others. ⚠️ **Decentralization makes accurate counts
genuinely hard, and the 2022 surge has been followed by a steady decline in active users
and servers.**

### 2.2 AT Protocol

**Bluesky's protocol**, launched 2023, general registration February 2024.
**Over 40 million registered users**, with third-party estimates putting **monthly actives
in the low tens of millions** by early 2026 — ⚠️ **and registered-versus-active is the
distinction that matters here.**

**The architectural difference is the point**: ATProto separates **Personal Data Servers**
(your repository), **Relays** (firehose aggregation), **App Views** (indexing and
presentation), and **Labelers** (moderation as a separate, subscribable service).
**⚠️ Account portability is the design goal ActivityPub doesn't achieve**: moving your
entire identity, follows, and post history to a different server **without the old
server's cooperation**, via **DIDs** rather than server-scoped handles. **Custom feed
algorithms are a first-class, third-party-buildable primitive**, which is genuinely
unusual.

**⚠️ The honest critique**: **the protocol is decentralized; the main application is still
largely centralized**, and running a full relay is expensive enough that few do.
**Bluesky's centralized onboarding is also why adoption outpaced Mastodon's** — the
trade-off is real in both directions.

### 2.3 ⚠️ They don't interoperate

**As of 2026, ActivityPub and AT Protocol do not natively interoperate**, and this is not
an oversight — ⚠️ **the data models differ enough that a clean bridge is genuinely hard.**
ActivityPub co-author **Evan Prodromou** argued Bluesky should simply implement
ActivityPub; **Bluesky's position was that ActivityPub couldn't deliver the account
portability they wanted**, and native ActivityPub support **is not on the Bluesky
roadmap.**

**Bridges exist** — **Bridgy Fed** is the main one, now under the **A New Social**
nonprofit — ⚠️ **and the EFF's own guidance is candid about the seams: you can edit posts
on Mastodon but not Bluesky, so a bridged edit doesn't propagate; replies can get lost;
and account ownership gets strange** when you federate from a website rather than a
conventional account.

**[DURABLE] If you're building on either**: **the firehose is the interesting primitive**
(both give you one), **moderation is your problem** (§7 → `social-moderation-abuse-and-regulation`) and neither protocol solves it for
you, **and instance-level blocking is a social mechanism with technical consequences** you
need to model.
