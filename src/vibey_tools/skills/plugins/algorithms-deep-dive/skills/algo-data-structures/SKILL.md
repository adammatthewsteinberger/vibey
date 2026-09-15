---
name: algo-data-structures
description: "Use when picking or debugging a concrete data structure: arrays and sequences and their memory layout, hash tables (collision resolution, open addressing and modern probing, load factor, iteration order, hash flooding, the 2025 theory result), trees and ordered structures (balanced in-memory trees, B-trees and the B-tree/LSM storage divide, tries and specialized trees), and heaps and priority queues."
---

# Algorithms Deep Dive: Arrays, Hash Tables, Trees, and Heaps

> **Part 2 of 5** of the *Algorithms Deep Dive* reference (plugin `algorithms-deep-dive`), covering §3–§6. Sibling skills: `algo-foundations-and-machine-model` (§0–§2), `algo-core-algorithms` (§7–§11), `algo-probabilistic-concurrency-and-measurement` (§12–§14), `algo-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 → `algo-reference` for the currency snapshot and what goes stale first.

> **How to read this.** Reference, not a course, and deliberately complementary to a
> theory-of-computation reference: **that** answers "is this solvable and how hard is it";
> **this** answers "which structure, which algorithm, and why is it slower than the
> analysis said."
>
> Three markers:
> - **[DURABLE]** — established algorithms, structures, and engineering practice. Most of
>   this document.
> - **[VERSIONED]** — library implementations, hardware behaviour, recent results.
> - **[CONTESTED]** — genuine disagreement.
>
> **⚠️ GOTCHA** boxes mark the places where the textbook answer and the production answer
> diverge.
>
> **The three framings that organize everything below:**
> 1. **Data structure choice is algorithm choice.** Most "algorithm problems" in real
>    systems are solved by picking the right structure and letting the algorithm fall out.
>    **If your algorithm is complicated, your data layout is probably wrong** (§3–§7 → `algo-core-algorithms`).
> 2. **Asymptotic analysis models the wrong machine.** It assumes uniform-cost memory
>    access, which stopped being true in the 1990s. **A cache miss is ~100× an arithmetic
>    op, and a branch mispredict ~15–20 cycles** — so an O(n) scan over an array routinely
>    beats an O(log n) walk over a pointer structure (§2 → `algo-foundations-and-machine-model`). Asymptotics tell you how
>    something scales; they do not tell you which is faster at your n.
> 3. **You will almost never write these.** You will *choose* them. The valuable skill is
>    knowing what your standard library actually does, what its failure modes are, and
>    when its default is wrong for your data — not reimplementing quicksort (§13 → `algo-probabilistic-concurrency-and-measurement`).

---

## §3. Arrays and Sequences

**[DURABLE] The dynamic array (vector, `ArrayList`, `Vec`, slice) is the correct default
for sequences, and it is under-used relative to how often it's the right answer.**
Amortized O(1) append via geometric growth, O(1) indexing, and — decisively — **perfect
cache behaviour**.

| Structure | Real trade-off |
|---|---|
| **Dynamic array** | ⚠️ O(n) insert/delete in the middle — **but with a tiny constant**, so it wins over a list up to surprisingly large n |
| **Linked list** | O(1) splice **if you already hold the node**. ⚠️ Otherwise almost always the wrong choice — one cache miss per node, high per-element overhead. **Its main legitimate uses are intrusive lists and LRU chains where you hold node pointers** |
| **Deque** | O(1) both ends; usually a ring buffer or a chunked array. **The right answer for queues** |
| **Ring buffer** | Fixed capacity, contiguous, no allocation. **Excellent for streaming, audio, and bounded queues** |
| **Rope / gap buffer** | Text editing. Gap buffer for a single cursor, rope for concurrent/large edits |
| **Small-vector optimization** | Inline storage for the first N elements, heap after. **Large real win** for many-small-collections workloads |

**⚠️ Growth factor matters**: doubling is common; some implementations use 1.5× to allow
reuse of freed blocks. **Reserve capacity when you know the size** — repeated reallocation
and copying is a common invisible cost.

---

## §4. Hash Tables

**[DURABLE] The most important data structure in practice**, and the one whose
implementation details most affect real performance.

### 4.1 Collision resolution

**Separate chaining** — buckets hold lists. Simple, degrades gracefully, ⚠️ **one pointer
chase per probe.**
**Open addressing** — everything in one array. **Far better cache behaviour**, and the
modern default. Variants: **linear probing** (best locality; suffers clustering),
**quadratic probing**, **double hashing**, **Robin Hood** (steal from the rich — bounds
variance in probe length), **hopscotch**, **cuckoo** (worst-case O(1) lookup, expensive
inserts).

**[VERSIONED] Swiss tables** (Google's `absl::flat_hash_map`, and the basis of Rust's
`HashMap` via `hashbrown`) are the current practical state of the art: **open addressing
plus a separate array of one-byte control values, scanned with SIMD** so one instruction
checks 16 slots. **If your language's hash map is modern, this is probably what it does.**

### 4.2 The things that actually bite

> **⚠️ GOTCHA — the hash table failure modes, roughly in order of how often they hurt:**
> - **Load factor.** Performance degrades sharply as the table fills; most implementations
>   resize around 0.7–0.9. **Resizing is an O(n) rehash — a latency spike.** Pre-size when
>   you can.
> - **Bad hash functions.** A hash that doesn't distribute causes clustering that looks
>   like an algorithmic problem. **Never use `hash(x) % n` with a weak hash and a power-of-2
>   n** — you're using only the low bits.
> - **⚠️ Hash-flooding DoS.** If keys come from untrusted input, an attacker who can predict
>   your hash can force every key into one bucket, turning O(1) into O(n). **This is why
>   SipHash and randomized seeds are the default in Python, Rust, and others** — and why
>   swapping in a "faster" non-cryptographic hash on user-controlled keys is a security
>   decision, not a performance one.
> - **Iteration order.** Unordered by definition, and **deliberately randomized in some
>   languages.** Depending on it is a bug that surfaces after an upgrade.
> - **Mutating a key after insertion.** Corrupts the table silently.
> - **Equality and hashing must agree.** `a == b` ⟹ `hash(a) == hash(b)`. Violating this
>   produces lookups that fail for keys that are present.

**Ordered variants**: `LinkedHashMap`, Python's dict (insertion-ordered since 3.7),
Rust's `IndexMap` — an array of entries plus a hash index. **Cheap, and worth defaulting to
when determinism helps debugging.**

### 4.3 The 2025 theory result, and its honest weight

**[VERSIONED]** In **January 2025**, Farach-Colton, Krapivin, and Kuszmaul published
*"Optimal Bounds for Open Addressing Without Reordering"*, which **disproved the central
conjecture from Andrew Yao's 1985 "Uniform Hashing is Optimal."** The result got wide
attention partly because Krapivin was an undergraduate who found it while tinkering,
unaware of the conjecture.

Two constructions: **funnel hashing** (greedy) achieves **O(log² δ⁻¹)** worst-case expected
probe complexity — where δ is the empty fraction — **disproving Yao's claim that Ω(δ⁻¹) was
optimal for greedy schemes**; and **elastic hashing** (non-greedy) achieves **O(1) amortized
expected** and **O(log δ⁻¹) worst-case expected** probes **without reordering**.
**All results come with matching lower bounds** — they didn't just refute the conjecture,
they settled the question.

> **⚠️ GOTCHA — read this correctly, because the popular coverage oversold it.** CACM's own
> reporting notes the caveats: **it disproved Yao's conjectures but not Ullman's**; **some
> non-open-addressing designs (e.g. Iceberg tables) are faster** than Krapivin's structure;
> and **the construction handles insertions only, not deletions** — where the earlier Tiny
> Pointers work covered both. The authors themselves "take a lower-key view."
>
> **The engineering translation: this is a genuine and beautiful theoretical result that
> settles a 40-year question. It is not a reason to replace your hash map.** Its practical
> relevance is to very-high-load-factor regimes; your Swiss table at 0.75 load is
> unaffected.

---

## §5. Trees and Ordered Structures

### 5.1 In-memory trees

**[DURABLE] Use a tree when you need order** — range queries, successor/predecessor,
min/max, sorted iteration. **If you only need point lookup, use a hash map** (§4); a tree
is strictly worse for that.

**Balanced BSTs**: red-black (the usual standard-library choice — `std::map`,
`TreeMap`), AVL (more strictly balanced, faster lookup, slower update), **B-trees**
(§5.2 — increasingly used *in memory* too, because of §2 → `algo-foundations-and-machine-model`), **splay** (self-adjusting,
excellent for skewed access, ⚠️ **mutates on read**, which is a concurrency landmine),
**treaps** and **skip lists** (randomized, much simpler to implement, and skip lists are
notably easier to make concurrent).

**⚠️ The modern caveat**: **binary trees have poor cache behaviour** — one node per cache
line, one miss per level. **This is why B-trees with fanout tuned to the cache line
(B+ trees, or "cache-conscious" layouts) increasingly beat binary trees in memory**, and
why Rust's `BTreeMap` is a B-tree rather than a red-black tree.

### 5.2 B-trees and the storage divide

**[DURABLE] B-trees are the correct structure for block-addressed storage**, and
essentially every relational database index is one. High fanout (hundreds of keys per
node), so a billion rows is 3–4 levels deep and the upper levels stay cached. **B+ trees**
put all data in leaves and link them — which is what makes range scans fast.

**LSM trees** are the other half of the storage world (LevelDB, RocksDB, Cassandra,
ScyllaDB, and most modern write-heavy stores). **Buffer writes in memory, flush sorted
runs to disk, compact in the background.**

**[DURABLE] The trade-off is the clearest example of RUM in practice** (§16.1 → `algo-reference`):

| | **B-tree** | **LSM tree** |
|---|---|---|
| Writes | In-place, random I/O | **Sequential, much faster** |
| Reads | One path, predictable | May check several levels; **needs Bloom filters** (§12 → `algo-probabilistic-concurrency-and-measurement`) |
| Space | Fragmentation | ⚠️ **Space amplification** until compaction |
| Latency | Predictable | ⚠️ **Compaction causes spikes** |
| Best for | Read-heavy, range-heavy | **Write-heavy ingest** |

**⚠️ Know the three amplification factors** — read, write, and space — because a storage
engine choice is choosing which one to pay. Tuning an LSM is largely compaction tuning, and
**compaction stalls are the characteristic production surprise.**

### 5.3 Specialized trees
**Tries / radix trees** — string keys with shared prefixes; prefix and autocomplete
queries. **Adaptive Radix Tree (ART)** is the cache-efficient modern version.
**Segment trees / Fenwick (BIT)** — range queries with updates; Fenwick is smaller and
faster for prefix sums. **Interval trees** — overlap queries. **Merkle trees** —
verification and diffing, everywhere in distributed systems and version control.
**Union-Find (disjoint set)** — connectivity, Kruskal's, and **near-constant time with
path compression + union by rank**. ⚠️ **Under-known relative to how often it's exactly
the right tool.**

---

## §6. Heaps and Priority Queues

**[DURABLE] The binary heap is one of the best cost/benefit structures in computing**:
an implicit tree in a flat array, so no pointers and good locality. O(log n) push/pop,
**O(1) peek**, and **O(n) heapify** (not O(n log n) — a common misconception).

**Uses**: scheduling, Dijkstra and A\*, top-k, merging sorted streams, timer wheels,
event simulation.

**Variants worth knowing**: **d-ary heaps** (shallower, better cache, faster decrease-key —
often a real win for Dijkstra), **pairing heaps** (good practical decrease-key),
**Fibonacci heaps** (⚠️ **theoretically superior and practically slower** — the canonical
example of an algorithm whose constants defeat its asymptotics), **binomial** and
**leftist heaps** for mergeability.

**⚠️ For top-k, a bounded min-heap of size k is O(n log k)** and usually beats sorting.
And for a **fixed small range of priorities, a bucket queue is O(1)** and beats any
comparison heap.
