---
name: social-feed-graph-ranking-and-notifications
description: "Use when building the core of a social system: feed and timeline architecture including fan-out on write versus read and the celebrity problem, the social graph and its storage and traversal, ranking and recommendation (signals, candidate generation, engagement objectives and their failure modes), and notifications and real-time delivery including push, batching, digesting and WebSocket fan-out."
---

# Social Media Engineering: Feed Architecture, the Social Graph, Ranking, and Notifications

> **Part 2 of 5** of the *Social Media Engineering* reference (plugin `social-media-engineering`), covering §3–§6. Sibling skills: `social-platform-apis-and-open-protocols` (§0–§2), `social-moderation-abuse-and-regulation` (§7–§9), `social-media-analytics-privacy-and-presence` (§10–§13), `social-reference` (§14–§19). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §16 → `social-reference` for the currency snapshot and what goes stale first.

> **How to read this.** The title spans two things and this document covers both, weighted
> toward the first: **§1–§12 → `social-platform-apis-and-open-protocols`, `social-moderation-abuse-and-regulation`, `social-media-analytics-privacy-and-presence` are about building and integrating with social systems;
> §13 → `social-media-analytics-privacy-and-presence` is about your own presence as a developer.** Skip to §13 → `social-media-analytics-privacy-and-presence` if that's what you came for.
>
> Three markers:
> - **[DURABLE]** — architecture, ranking, moderation, and abuse dynamics. Most of §2–§10 → `social-platform-apis-and-open-protocols`, `social-moderation-abuse-and-regulation`, `social-media-analytics-privacy-and-presence`.
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

## §3. Feed and Timeline Architecture

**[DURABLE] The canonical distributed-systems problem in this domain, and the trade-off is
stable.**

```
FAN-OUT ON WRITE (push)          FAN-OUT ON READ (pull)
Write to every follower's        Query followers' posts at read time
timeline at post time
✓ Reads are fast and cheap       ✓ Writes are cheap
✗ ⚠️ A 50M-follower account      ✗ Reads are expensive and hard to cache
  means 50M writes
✗ Storage amplification          ✗ Latency scales with following count
```

**[DURABLE] Every real system is hybrid**: **fan-out on write for normal accounts,
fan-out on read for high-follower accounts, merged at read time.** ⚠️ **The threshold is a
tuning parameter, and "celebrity accounts" are a distinct architectural case you must plan
for rather than discover.**

**The implementation vocabulary**: **timeline as a materialized list of post IDs**
(⚠️ **store IDs, hydrate content at read — content changes, deletions, and blocks all
become tractable**), **Redis or a purpose-built store** for the timeline itself,
**async fan-out through a queue**, **cursor-based pagination** (⚠️ **never offset — new
posts shift the window and you get duplicates and gaps**), and **backfill and repair jobs**
because fan-out will drop things.

**⚠️ The details that bite**: **deletion and edit propagation** through already-fanned-out
timelines; **block and mute enforcement** at read time (⚠️ **applying blocks at write time
means a later block doesn't retroactively clean the timeline**); **the "new follower
backfill" question** (do they see history?); **and the cold-start empty feed**, which is a
product problem disguised as an engineering one.

---

## §4. The Social Graph

**[DURABLE]** **Directed** (follow: Twitter, Instagram) vs **undirected** (friend:
Facebook) — ⚠️ **and the choice cascades into privacy, feeds, and moderation in ways that
are painful to reverse.**

**Storage**: adjacency lists in a KV store, a relational table with careful indexing,
a graph database (Neo4j, or Meta's TAO-style approach), or **an adjacency-list service
with heavy caching** — ⚠️ **which is what most large systems actually build, because a
general graph database is usually the wrong tool for a workload that is 99% "get followers
of X."**

**⚠️ The operations that hurt**: **follower counts on celebrity accounts** (⚠️ **counting
is expensive — cache approximately, and accept eventual consistency**), **"do these two
users follow each other"** at scale, **mutual-follow and friends-of-friends** queries, and
**the fact that graph traversal depth explodes combinatorially** — two hops from a
well-connected node is most of the network.

**Privacy is a graph problem**: blocks must be bidirectional in effect; **⚠️ private
accounts mean visibility checks on every read path, and getting one path wrong is a data
leak** rather than a bug.

---

## §5. Ranking and Recommendation

**[DURABLE] The structure is stable even as the models change.**

```
CANDIDATE GENERATION  → thousands of candidates from many sources (follows,
                        engagement-based, embedding-similarity, trending, ads)
     ↓
RANKING               → a model scores each; predicted engagement, dwell, quality
     ↓
RE-RANKING / POLICY   → diversity, freshness, source variety, safety filters,
                        author-frequency caps, business rules
     ↓
BLENDING              → merge organic, ads, recommendations
```

**⚠️ The problems that are genuinely hard and remain so**: **the feedback loop** — you
train on what you showed, so the model learns your past choices as much as user preference;
**engagement ≠ satisfaction**, and optimizing for the former reliably degrades the latter
(⚠️ **outrage, cliffhangers, and low-quality-but-clickable content all win on engagement
metrics**); **cold start** for new users and new content; **filter bubbles and diversity**,
which need explicit objectives because they never emerge from engagement optimization;
and **⚠️ explainability**, which is now partly a regulatory requirement (§9 → `social-moderation-abuse-and-regulation`).

**[DURABLE] The design lesson that matters most: what you measure becomes what you build.**
Choosing your objective function is a product-values decision wearing an engineering
costume, and **"we just show people what they engage with" is a choice, not a neutrality.**

---

## §6. Notifications and Real-Time

**Delivery**: WebSocket or SSE for in-app, **APNs/FCM** for push, email and SMS for
fallback. **⚠️ Push tokens expire and rotate — handle invalidation or you leak delivery
failures forever.**

**[DURABLE] The engineering that separates good from awful**: **batching and digest**
(⚠️ **notification fatigue causes permission revocation, and a revoked push permission is
very hard to win back**), **deduplication and collapsing** ("5 people liked your post", not
five notifications), **per-user preferences at real granularity**, **quiet hours and
timezone awareness**, **and read-state sync across devices.**

**⚠️ The ethics are load-bearing here.** Notifications are the most direct attention lever
you have, and **engagement-maximizing notification strategy is where product pressure most
often produces something the team wouldn't defend out loud.** Design the default you'd want
applied to you.

**Real-time presence** (typing indicators, online status) is expensive and
⚠️ **a privacy surface people underestimate** — "last seen" reveals more than users expect.
