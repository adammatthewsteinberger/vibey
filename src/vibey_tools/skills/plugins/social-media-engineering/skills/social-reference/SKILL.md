---
name: social-reference
description: "Use when checking a social-systems anti-pattern, weighing a contested question, confirming whether a platform API, pricing or regulatory claim is still current (snapshot verified August 2026), finding the engineering, trust-and-safety and regulation resources, or needing the architecture picker and the checklists to run before building on a platform API or launching anything social. Companion to the other social-media-engineering skills."
---

# Social Media Engineering: Anti-Patterns, Contested Questions, Currency, and Resources

> **Part 5 of 5** of the *Social Media Engineering* reference (plugin `social-media-engineering`), covering §14–§19. Sibling skills: `social-platform-apis-and-open-protocols` (§0–§2), `social-feed-graph-ranking-and-notifications` (§3–§6), `social-moderation-abuse-and-regulation` (§7–§9), `social-media-analytics-privacy-and-presence` (§10–§13). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §16 below for the currency snapshot and what goes stale first.

> **How to read this.** The title spans two things and this document covers both, weighted
> toward the first: **§1–§12 → `social-platform-apis-and-open-protocols`, `social-feed-graph-ranking-and-notifications`, `social-moderation-abuse-and-regulation`, `social-media-analytics-privacy-and-presence` are about building and integrating with social systems;
> §13 → `social-media-analytics-privacy-and-presence` is about your own presence as a developer.** Skip to §13 → `social-media-analytics-privacy-and-presence` if that's what you came for.
>
> Three markers:
> - **[DURABLE]** — architecture, ranking, moderation, and abuse dynamics. Most of §2–§10 → `social-platform-apis-and-open-protocols`, `social-feed-graph-ranking-and-notifications`, `social-moderation-abuse-and-regulation`, `social-media-analytics-privacy-and-presence`.
> - **[VERSIONED]** — platform terms, pricing, protocols, regulation. ⚠️ **Verify all of
>   it; this is the fastest-moving material in the collection after AI.**
> - **[CONTESTED]** — genuine disagreement.
>
> **⚠️ GOTCHA** boxes mark what breaks, gets you banned, or gets you fined.
>
> **The three framings that organize everything below:**
> 1. **⚠️ Building on a platform API is building on rented land, and the rent changed.**
>    The 2023–2026 period established that platforms will reprice or withdraw access with
>    weeks of notice and no obligation. **Architect for that from day one** (§1 → `social-platform-apis-and-open-protocols`).
> 2. **The hard problems are social, not technical.** Fan-out and ranking are solved
>    engineering; **moderation, abuse, and incentive design are not, and they scale
>    worse than your database does** (§7 → `social-moderation-abuse-and-regulation`, §8 → `social-moderation-abuse-and-regulation`).
> 3. **⚠️ Compliance is now an architecture input, not a legal afterthought.** Age
>    assurance, transparency reporting, and appeals mechanisms have to be designed in —
>    **and regulators have started saying explicitly that self-declaration is not
>    sufficient** (§9 → `social-moderation-abuse-and-regulation`).

---

## §14. Anti-Patterns

| Anti-pattern | Why |
|---|---|
| Building a product whose core value depends on one platform's API | ⚠️ **Apollo. Nine days' notice. $20M/year** (§1.1 → `social-platform-apis-and-open-protocols`) |
| No abstraction layer over platform APIs | Terms change; you want to change one adapter (§1.3 → `social-platform-apis-and-open-protocols`) |
| Budgeting on current volume | ⚠️ **The X read cap is a $10k cliff, then Enterprise** (§1.2 → `social-platform-apis-and-open-protocols`) |
| Auto-posting links without checking the URL surcharge | ⚠️ **~13× a plain post on X** (§1.2 → `social-platform-apis-and-open-protocols`) |
| Designing follow/like features without checking write availability | ⚠️ **Removed from X self-serve, April 2026** (§1.2 → `social-platform-apis-and-open-protocols`) |
| Assuming the free tier persists | It hasn't, anywhere (§1.1 → `social-platform-apis-and-open-protocols`) |
| Scraping a platform that prohibits it in its terms | Contractual exposure (§1.2 → `social-platform-apis-and-open-protocols`) |
| Treating ActivityPub and ATProto as interchangeable | ⚠️ **They don't natively interoperate and won't soon** (§2.3 → `social-platform-apis-and-open-protocols`) |
| Assuming a bridge is transparent | Edits don't propagate; replies get lost (§2.3 → `social-platform-apis-and-open-protocols`) |
| Quoting Bluesky's registered users as active users | Registered ≠ MAU (§2.2 → `social-platform-apis-and-open-protocols`) |
| Pure fan-out on write | ⚠️ **A 50M-follower account is 50M writes** (§3 → `social-feed-graph-ranking-and-notifications`) |
| Pure fan-out on read | Latency scales with following count (§3 → `social-feed-graph-ranking-and-notifications`) |
| Storing hydrated content in timelines | Deletions and edits become unfixable (§3 → `social-feed-graph-ranking-and-notifications`) |
| Offset pagination on a live feed | Duplicates and gaps (§3 → `social-feed-graph-ranking-and-notifications`) |
| Applying blocks only at write time | Later blocks don't clean history (§3 → `social-feed-graph-ranking-and-notifications`) |
| Exact follower counts at celebrity scale | Cache approximately; accept eventual consistency (§4 → `social-feed-graph-ranking-and-notifications`) |
| A general graph database for "get followers of X" | Usually the wrong tool (§4 → `social-feed-graph-ranking-and-notifications`) |
| Visibility checks on some read paths | ⚠️ **One missed path is a data leak** (§4 → `social-feed-graph-ranking-and-notifications`) |
| Optimizing purely for engagement | ⚠️ **Reliably degrades the product; outrage wins** (§5 → `social-feed-graph-ranking-and-notifications`, §11 → `social-media-analytics-privacy-and-presence`) |
| Notification strategy tuned for reach | Fatigue → permission revocation → unrecoverable (§6 → `social-feed-graph-ranking-and-notifications`) |
| "We're too small to need moderation" | ⚠️ **False the moment you're worth abusing** (§7 → `social-moderation-abuse-and-regulation`) |
| Automated moderation with no human escalation | Context is what classifiers lack (§7 → `social-moderation-abuse-and-regulation`) |
| Moderation tooling with no reviewer welfare provision | ⚠️ **Documented psychological harm; a duty of care** (§7 → `social-moderation-abuse-and-regulation`) |
| English-only classifiers on a global product | Where the worst real-world harms have happened (§7 → `social-moderation-abuse-and-regulation`) |
| Content-based spam detection only | ⚠️ **Behaviour and graph structure are harder to fake** (§8 → `social-moderation-abuse-and-regulation`) |
| Detection heuristics based on "looks human-written" | Generated content is cheap now (§8 → `social-moderation-abuse-and-regulation`) |
| **Age gate by self-declaration** | ⚠️ **Reddit fined £14.5M; explicitly deemed insufficient** (§9.2 → `social-moderation-abuse-and-regulation`) |
| Assuming non-EU headquarters exempts you from the DSA | ⚠️ **"Substantial connection" is the test** (§9.1 → `social-moderation-abuse-and-regulation`) |
| Storing ID documents to prove age | ⚠️ **You created a worse liability. Take a token** (§9.3 → `social-moderation-abuse-and-regulation`) |
| No appeals mechanism | Legally required in the EU (§9.1 → `social-moderation-abuse-and-regulation`) |
| Retrofitting transparency reporting | ⚠️ **You can't reconstruct data you didn't collect** (§9.3 → `social-moderation-abuse-and-regulation`) |
| Trusting client-supplied content type on upload | Sniff the bytes (§10 → `social-media-analytics-privacy-and-presence`) |
| Serving user-supplied SVG from your origin | ⚠️ **Script execution** (§10 → `social-media-analytics-privacy-and-presence`) |
| Decoding uploads before capping dimensions | Decompression bombs (§10 → `social-media-analytics-privacy-and-presence`) |
| Not stripping EXIF | ⚠️ **GPS coordinates. A recurring real incident** (§10 → `social-media-analytics-privacy-and-presence`) |
| "Deleting" content only from the primary store | Timelines, caches, CDN, search, backups, warehouse (§12 → `social-media-analytics-privacy-and-presence`) |
| A/B testing a social feature without cluster randomization | ⚠️ **Network effects break independence** (§11 → `social-media-analytics-privacy-and-presence`) |
| Treating the social graph as non-sensitive | ⚠️ **It reveals what users never disclosed** (§12 → `social-media-analytics-privacy-and-presence`) |
| Building a personal brand as a career strategy | ⚠️ **Serendipity is the real mechanism, and it's slow** (§13 → `social-media-analytics-privacy-and-presence`) |
| Advice that ignores who pays the harassment cost | It isn't evenly distributed (§13 → `social-media-analytics-privacy-and-presence`) |

---

## §15. Contested Questions

**15.1 Is building on platform APIs ever wise?** *For*: the data and reach exist nowhere
else, and real businesses run on them. *Against*: ⚠️ **the 2023–26 record is unambiguous —
you have no protection and short notice.** **[The defensible position: build on them for
capability, never for your core value proposition, and keep an exit path costed.]**

**15.2 ActivityPub or AT Protocol?** *ActivityPub*: a W3C standard, a real multi-project
ecosystem, Threads participating, genuine server diversity. *ATProto*: better account
portability, algorithmic choice as a primitive, far larger user base, ⚠️ **and a
centralization critique that its own community makes.** **[CONTESTED and unresolved. If
you're building, the honest answer is that you may need both, and bridging is imperfect.]**

**15.3 Should feeds be algorithmic or chronological?** *Algorithmic*: with any real
following count, chronological is unusable, and ranking genuinely surfaces value.
*Chronological*: predictable, uncoupled from engagement optimization, and not
manipulable by the platform. **⚠️ ATProto's answer — make the algorithm a user-selectable,
third-party-buildable component — is the most interesting structural response anyone has
shipped**, and whether it works at scale is still open.

**15.4 Is age verification good policy?** *For*: the harms to minors are documented and
self-declaration demonstrably fails. *Against*: ⚠️ **it requires identifying users, which
is in direct tension with privacy and anonymity, and anonymity protects vulnerable people
too.** **The technical middle ground — zero-knowledge age tokens, OS-level attestation
(§9.3 → `social-moderation-abuse-and-regulation`) — is genuinely promising and not yet deployed at scale.** **[Live, and the
engineering choice materially affects which side you land on.]**

**15.5 Can moderation be solved?** ⚠️ **No, and treating it as a solvable engineering
problem is itself an error.** It's a values problem with an engineering component; every
policy is contested by someone; and **the realistic goal is legitimacy and consistency,
not correctness.**

**15.6 Do developers need a social presence?** §13 → `social-media-analytics-privacy-and-presence`. **[CONTESTED, and I've taken a
position: no, and the alternatives are underrated.]** The counter-case is real —
visibility does generate opportunity, and for people outside traditional networks it can
be genuinely levelling.

---

## §16. Currency Snapshot — verified August 2026

⚠️ **This is among the fastest-decaying documents in the collection.** §3–§8 → `social-feed-graph-ranking-and-notifications`, `social-moderation-abuse-and-regulation`, §10 → `social-media-analytics-privacy-and-presence` and §12 → `social-media-analytics-privacy-and-presence`
are durable architecture; §1 → `social-platform-apis-and-open-protocols`, §2 → `social-platform-apis-and-open-protocols` and §9 → `social-moderation-abuse-and-regulation` are not.

| Thing | Status as of Aug 2026 | Decay risk |
|---|---|---|
| **⚠️ X API** | **February 2026: pay-per-use became default for new developers; Basic ($200/mo) and Pro ($5,000/mo) closed to new signups** (grandfathered for existing). Reported rates: **owned reads ~$0.001** (cut April 2026), **third-party post read ~$0.005**, **user/follower/trends ~$0.010**, **plain post ~$0.015**, ⚠️ **post with a URL ~$0.20**. **2,000,000 post-read monthly hard cap** — hitting it costs ~$10,000, then **Enterprise (~$42,000+/mo, custom, multi-week sales)**. ⚠️ **20 April 2026: following, liking and quote-posting withdrawn from all self-serve tiers.** Stated use case is contractually binding | **High** |
| **X third-party resellers** | Advertise reads at a small fraction of official rates; one comparison put official pay-per-use at **~33×** a third party. ⚠️ **Direct scraping is prohibited by X's terms**; resellers' legal position is contested | **High** |
| **Reddit** | **$0.24 per 1,000 API calls** commercial (since July 2023, ~30 days' notice). **Apollo (1.5M users) shut down** — quoted **~$20M/year**. **Pushshift terminated.** Self-service ended; new apps need approval under a **"Responsible Builder Policy"** | Medium |
| **Other platforms** | **Meta**: weeks of app review. **LinkedIn**: partnership agreements beyond surface data. **TikTok**: formal application. **YouTube**: quota ceiling. ⚠️ **Apps failing review lose endpoints used during development** | Medium |
| **Fediverse scale** | **Mastodon ~10.5M accounts; wider Fediverse ~11M** including Pixelfed and others. ⚠️ **Counts are genuinely hard; the 2022 surge has been followed by steady decline in active users and servers** | Medium |
| **Bluesky / ATProto** | **40M+ registered users** (crossed late 2025); third-party estimates put **MAU in the low tens of millions** early 2026. **Centralized onboarding drove faster adoption than Mastodon.** ⚠️ **Protocol decentralized, main application still largely centralized** — a critique from within its own community | Medium |
| **⚠️ Protocol interop** | **ActivityPub and AT Protocol do not natively interoperate as of 2026** — data models differ enough that a clean bridge is hard. **Native ActivityPub support is not on Bluesky's roadmap.** **Bridgy Fed** (now under the **A New Social** nonprofit) is the main bridge; ⚠️ **EFF documents real seams — Mastodon edits don't propagate to Bluesky, replies can get lost** | Medium |
| **⚠️ UK Online Safety Act** | **"Highly effective age assurance" in force since July 2025.** **Ofcom accepts** photo-ID matching, facial age estimation, Open Banking, digital identity services, MNO checks — ⚠️ **self-declaration alone is not sufficient.** Fines **up to 10% of global turnover**. **ICO fined Reddit £14.5M in early 2026** for inadequate children's-data protection and reliance on self-declaration; **Ofcom has fined adult sites** | **High** |
| **⚠️ DSA enforcement** | Applies on a **"substantial connection"** test — non-EU HQ is no exemption; non-EU providers must nominate a legal representative. **Commission enforces for VLOPs; national Digital Services Coordinators for others.** **April 2026: Commission preliminarily found Meta in breach** over under-13s on Facebook; **preliminary findings against TikTok** over minors' account safety; **Snapchat's self-declaration deemed insufficient.** Obligations: illegal-content reporting tools, no targeted ads to minors, statements of reasons, internal appeals, annual transparency reports | **High** |
| **Age assurance direction** | **EU Digital Identity Wallet required operational by 31 Dec 2026**; Commission building an interim age-verification solution. ⚠️ **OS-level age signalling under consideration (e.g. Colorado)** — would restructure the integration problem. **US: no federal law; 12+ states enacted. Australia: penalties to AUD $49.5M** | **High** |

**Goes stale fastest:** §1 → `social-platform-apis-and-open-protocols`, §9 → `social-moderation-abuse-and-regulation`, and every figure in the table above. **Essentially never
stale:** §3 → `social-feed-graph-ranking-and-notifications`, §4 → `social-feed-graph-ranking-and-notifications`, §5 → `social-feed-graph-ranking-and-notifications`'s structure, §7 → `social-moderation-abuse-and-regulation`, §8 → `social-moderation-abuse-and-regulation`, §10 → `social-media-analytics-privacy-and-presence`, §12 → `social-media-analytics-privacy-and-presence`, §14.

---

## §17. Resources

### 17.1 Engineering
**Kleppmann, *Designing Data-Intensive Applications*** (⚠️ **§3 → `social-feed-graph-ranking-and-notifications`'s fan-out problem is
literally the book's opening example**); **the Twitter/X, Instagram, Discord, and Slack
engineering blogs** (⚠️ **Discord's writing on scaling message storage and Instagram's on
feed architecture are unusually candid**); **Bluesky's ATProto documentation and
specifications** (⚠️ **genuinely good technical writing, and the clearest available
explanation of the PDS/relay/AppView/labeler split**); **the ActivityPub W3C spec** and
**SocialHub** for the community; **Meta's TAO paper** for graph storage at scale;
**the RecSys** conference for §5 → `social-feed-graph-ranking-and-notifications`.

### 17.2 Moderation, trust and safety
**the Trust & Safety Professional Association** and its curriculum; **Sarah T. Roberts,
*Behind the Screen*** (⚠️ **on the human cost of commercial content moderation — the book
to read before you build a review queue**); **Tarleton Gillespie, *Custodians of the
Internet***; **evelyn douek** and **Daphne Keller** (⚠️ **the two most reliable academic
commentators on platform regulation**); **the Oversight Board's** published decisions;
**Techdirt** and **Platformer** for ongoing coverage; **the EFF** on the open social web
and on the privacy costs of age verification.

### 17.3 Regulation
⚠️ **Go to primary sources here — summaries age badly.** **The European Commission's DSA
pages** and enforcement announcements; **Ofcom's OSA implementation roadmap and guidance**;
**the ICO** for UK children's-data enforcement; **Future of Privacy Forum** and
**Inside Privacy** for readable analysis. **This document is not legal advice.**

---

## §18. Quick Reference

### 18.1 Architecture picker
| Need | Approach |
|---|---|
| Timeline for normal accounts | **Fan-out on write**, store IDs (§3 → `social-feed-graph-ranking-and-notifications`) |
| Timeline including celebrity follows | **Hybrid — merge pulled high-follower posts at read** (§3 → `social-feed-graph-ranking-and-notifications`) |
| Feed pagination | **Cursor, never offset** (§3 → `social-feed-graph-ranking-and-notifications`) |
| Follower lists at scale | Adjacency lists + heavy caching, not a graph DB (§4 → `social-feed-graph-ranking-and-notifications`) |
| Follower counts on huge accounts | Approximate and cached (§4 → `social-feed-graph-ranking-and-notifications`) |
| Ranking | Candidate generation → rank → re-rank → blend (§5 → `social-feed-graph-ranking-and-notifications`) |
| Notifications | Batch, dedupe, collapse, respect quiet hours (§6 → `social-feed-graph-ranking-and-notifications`) |
| Known-violating media | Hash matching before publication (§7 → `social-moderation-abuse-and-regulation`) |
| Coordinated inauthentic behaviour | ⚠️ **Graph and timing analysis, not content** (§8 → `social-moderation-abuse-and-regulation`) |
| Age assurance | ⚠️ **Token + audit ID. Never store the document** (§9.3 → `social-moderation-abuse-and-regulation`) |
| Uploads | Sniff bytes, cap dimensions, transcode, strip EXIF (§10 → `social-media-analytics-privacy-and-presence`) |
| Testing a social feature | Cluster/ego-network randomization (§11 → `social-media-analytics-privacy-and-presence`) |
| Reaching developers yourself | ⚠️ **Own the writing; syndicate second** (§13 → `social-media-analytics-privacy-and-presence`) |

### 18.2 Before you build on a platform API
- [ ] Modelled cost at **projected** volume, and located the cliff? (§1.2 → `social-platform-apis-and-open-protocols`)
- [ ] Read the current terms, including the use-case obligation? (§1.2 → `social-platform-apis-and-open-protocols`)
- [ ] Are the specific endpoints you need still on self-serve? (§1.2 → `social-platform-apis-and-open-protocols`)
- [ ] Abstraction layer, so a terms change is one adapter? (§1.3 → `social-platform-apis-and-open-protocols`)
- [ ] Fallback path and exit plan costed? (§1.3 → `social-platform-apis-and-open-protocols`)
- [ ] Is the platform load-bearing for your core value? ⚠️ **If yes, reconsider** (§1 → `social-platform-apis-and-open-protocols`)

### 18.3 Before you launch anything social
- [ ] Moderation pipeline, including human escalation and appeals (§7 → `social-moderation-abuse-and-regulation`, §9 → `social-moderation-abuse-and-regulation`)
- [ ] Reviewer welfare provisions if humans will see reports (§7 → `social-moderation-abuse-and-regulation`)
- [ ] Rate limits and signup friction (§8 → `social-moderation-abuse-and-regulation`)
- [ ] Age assurance appropriate to your jurisdictions — ⚠️ **not self-declaration** (§9 → `social-moderation-abuse-and-regulation`)
- [ ] Transparency-reporting data collection **from day one** (§9.3 → `social-moderation-abuse-and-regulation`)
- [ ] Statements of reasons on enforcement actions (§9.1 → `social-moderation-abuse-and-regulation`)
- [ ] Upload validation, EXIF stripping, hash matching (§10 → `social-media-analytics-privacy-and-presence`)
- [ ] Deletion that propagates everywhere (§12 → `social-media-analytics-privacy-and-presence`)
- [ ] Block/mute enforced on **every** read path (§4 → `social-feed-graph-ranking-and-notifications`)
- [ ] Counter-metrics alongside engagement metrics (§11 → `social-media-analytics-privacy-and-presence`)

---

## §19. Sources and Method

**Method.** Narrative review, deliberately covering both readings of the title — **the
engineering of social systems (§1–§12 → `social-platform-apis-and-open-protocols`, `social-feed-graph-ranking-and-notifications`, `social-moderation-abuse-and-regulation`, `social-media-analytics-privacy-and-presence`) and the developer's own presence (§13 → `social-media-analytics-privacy-and-presence`)** — weighted
toward the former, since that's where the transferable technical content is. **§3–§8 → `social-feed-graph-ranking-and-notifications`, `social-moderation-abuse-and-regulation`, §10 → `social-media-analytics-privacy-and-presence`,
§11 → `social-media-analytics-privacy-and-presence` and §12 → `social-media-analytics-privacy-and-presence` rest on long-stable distributed-systems and trust-and-safety practice** and on
the platform engineering literature rather than on anything searched; the fan-out trade-off,
the moderation pipeline, and the adversarial dynamics have been consistently described for
a decade. **§1 → `social-platform-apis-and-open-protocols`, §2 → `social-platform-apis-and-open-protocols` and §9 → `social-moderation-abuse-and-regulation` move fast** and were verified in **August 2026** with three
targeted searches; every claim there is flagged **[VERSIONED]** with a decay rating in §16.

**Search log** (August 2026): X and Reddit API pricing and access terms · Bluesky/AT
Protocol and Mastodon/ActivityPub state and interoperability · DSA, Online Safety Act and
age-verification enforcement.

**Primary and near-primary sources consulted (selected):**
- **API pricing**: multiple independent 2026 breakdowns of X's pay-per-use model,
  cross-checked against each other for the per-resource rates, the 2M cap, and the April
  2026 endpoint withdrawals; contemporaneous reporting (via TechCrunch) of Christian
  Selig's Apollo/Reddit figures; Reddit's own $0.24/1K announcement as widely reported
- **Protocols**: **Bluesky's own atproto GitHub discussion** on ActivityPub
  interoperability (including Evan Prodromou's position and Bluesky's response); **the
  EFF's** 2026 guidance on bridging for the practical seams; **Nieman Lab** and
  **TechCrunch** on Fediverse adoption trends and Bridgy Fed/A New Social
- **Regulation**: **the European Commission's DSA pages** and enforcement announcements;
  **Future of Privacy Forum** on the Commission's age-verification approach and the Meta
  preliminary finding; multiple 2026 compliance guides for the Ofcom-accepted methods and
  the Reddit ICO fine; **Yoti** and **Inside Privacy** for the DSA obligation set

**Confidence statement.** **High confidence** in §3–§8 → `social-feed-graph-ranking-and-notifications`, `social-moderation-abuse-and-regulation`, §10 → `social-media-analytics-privacy-and-presence`, §11 → `social-media-analytics-privacy-and-presence`, §12 → `social-media-analytics-privacy-and-presence` and §14 — these are
architectural patterns and adversarial dynamics, consistently described across the platform
engineering and trust-and-safety literature. **High confidence in the protocol
architecture** in §2 → `social-platform-apis-and-open-protocols`, which comes substantially from Bluesky's own documentation and the
W3C spec, and in the interoperability position, which is stated directly by the projects
themselves.

⚠️ **Lower confidence, deliberately, on the API pricing in §1.2 → `social-platform-apis-and-open-protocols`.** **Almost every source
for these figures is a company selling an alternative to the official API**, which is a
clear incentive to present official pricing unfavourably. I cross-checked the rates across
several such sources and they agree closely — but ⚠️ **the framing is not disinterested,
X has changed this pricing repeatedly (including twice in 2026 alone), and you should
verify at developer.x.com before budgeting anything.** ⚠️ **Similarly, several age-assurance
sources are vendors selling verification services**, which is an incentive to present the
regulatory obligation as broader and more urgent than it is; **I have relied on the
Commission's and Ofcom's own positions for the substance and used vendor material only for
corroborating detail.** The **fine and enforcement facts** (Reddit's £14.5M, the Meta and
TikTok preliminary findings) are reported consistently across independent sources but
**I read reporting, not the decisions themselves.** **§9 → `social-moderation-abuse-and-regulation` is not legal advice**, the
regulatory position differs by jurisdiction and surface, and §15 is opinion labelled as
such — including §15.6, where I have taken a position that reasonable people dispute.
