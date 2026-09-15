---
name: algo-foundations-and-machine-model
description: "Use when choosing an algorithm or data structure, or explaining why measured performance disagrees with the Big-O analysis: how to pick a structure, asymptotic notation and its limits, and the machine you are actually programming — the memory hierarchy and cache lines, branch prediction and mispredicts, allocation, pointer indirection and SIMD. Includes the router for the whole algorithms-deep-dive reference."
---

# Algorithms Deep Dive: Choosing, and the Machine You Are Actually Programming

> **Part 1 of 5** of the *Algorithms Deep Dive* reference (plugin `algorithms-deep-dive`), covering §0–§2. Sibling skills: `algo-data-structures` (§3–§6), `algo-core-algorithms` (§7–§11), `algo-probabilistic-concurrency-and-measurement` (§12–§14), `algo-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    **If your algorithm is complicated, your data layout is probably wrong** (§3–§7 → `algo-data-structures`, `algo-core-algorithms`).
> 2. **Asymptotic analysis models the wrong machine.** It assumes uniform-cost memory
>    access, which stopped being true in the 1990s. **A cache miss is ~100× an arithmetic
>    op, and a branch mispredict ~15–20 cycles** — so an O(n) scan over an array routinely
>    beats an O(log n) walk over a pointer structure (§2). Asymptotics tell you how
>    something scales; they do not tell you which is faster at your n.
> 3. **You will almost never write these.** You will *choose* them. The valuable skill is
>    knowing what your standard library actually does, what its failure modes are, and
>    when its default is wrong for your data — not reimplementing quicksort (§13 → `algo-probabilistic-concurrency-and-measurement`).

---

## §0. Routing

| Asked about... | Go to |
|---|---|
| How to choose — the decision method | §1 |
| **Why my O(log n) is slower than your O(n)** | **§2** |
| Arrays, lists, and the layout question | §3 → `algo-data-structures` |
| Hash tables | §4 → `algo-data-structures` |
| Trees, B-trees, LSM trees | §5 → `algo-data-structures` |
| Heaps and priority queues | §6 → `algo-data-structures` |
| Sorting | §7 → `algo-core-algorithms` |
| Searching, indexing, and range queries | §8 → `algo-core-algorithms` |
| Graphs | §9 → `algo-core-algorithms` |
| Strings and text | §10 → `algo-core-algorithms` |
| Dynamic programming and greedy | §11 → `algo-core-algorithms` |
| Probabilistic and streaming structures | §12 → `algo-probabilistic-concurrency-and-measurement` |
| Vector / similarity search | §13.4 → `algo-probabilistic-concurrency-and-measurement` |
| Concurrency and lock-free structures | §14 → `algo-probabilistic-concurrency-and-measurement` |
| Measurement and benchmarking discipline | §13 → `algo-probabilistic-concurrency-and-measurement` |
| "Don't do this" | §15 → `algo-reference` |
| "Which is better?" | §16 → `algo-reference` |
| "Is this still current?" | §17 → `algo-reference` |
| Books and resources | §18 → `algo-reference` |

---

## §1. Choosing

**[DURABLE] The questions that determine the answer, in order:**

1. **What operations, at what ratio?** A structure optimized for reads is usually bad at
   writes. **Write down the operation mix before choosing** — "we insert once and query a
   million times" and "we update constantly" have opposite answers.
2. **How much data, and where does it live?** L1 / L2 / L3 / RAM / SSD / network. **The
   answer changes completely at each boundary** (§2.1), and this is the question most
   often skipped.
3. **What does the data look like?** Sorted? Nearly sorted? Skewed? Many duplicates?
   Adversarial? **Real data has structure and the best algorithms exploit it** (§7.2 → `algo-core-algorithms`).
4. **What are the ordering and locality requirements?** Do you need range scans, or only
   point lookups? That single question decides hash vs. tree (§4 → `algo-data-structures` vs. §5 → `algo-data-structures`).
5. **What's the tolerance for approximation?** Exact answers are often far more expensive
   than 99%-accurate ones (§12 → `algo-probabilistic-concurrency-and-measurement`).
6. **Is it concurrent?** Changes everything (§14 → `algo-probabilistic-concurrency-and-measurement`).
7. **What's the worst case, and does it matter?** Amortized-good-worst-case-terrible is
   fine for a batch job and unacceptable for a p99 latency SLO (§11.4 → `algo-core-algorithms`).

**[DURABLE] The default answer is usually "an array or a hash map."** Reach for something
exotic only when profiling shows you need it, and be aware that most exotic structures
lose to a flat array below a few thousand elements because of §2.

---

## §2. The Machine You Are Actually Programming

**[DURABLE] This section explains most of the gap between predicted and measured
performance, and it is the single highest-value part of this document.**

### 2.1 The memory hierarchy

```
register       <1 ns      ~0 cycles
L1 cache        ~1 ns      ~4 cycles       32–64 KB
L2 cache        ~4 ns     ~12 cycles       256 KB – 2 MB
L3 cache       ~15 ns     ~40 cycles       8–64 MB, shared
DRAM           ~80 ns   ~200–300 cycles    ⚠️ THE CLIFF
NVMe SSD       ~50 µs                      ~100,000 cycles
network         ~1 ms+
```

**[DURABLE] The consequences that should change your defaults:**
- **The cache line is 64 bytes.** That's the unit of transfer. Touching one byte costs you
  a line.
- **Sequential access is prefetched; random access is not.** A hardware prefetcher can
  hide latency on a predictable stride and does nothing for pointer chasing.
- **⚠️ This is why a linked list loses to an array with identical asymptotics.** The array
  scan is ~64 bytes per miss, prefetched; the list is one miss per node, unprefetchable.
  **A "O(n) scan" on a contiguous array often beats an "O(log n) search" on a tree for
  n in the thousands** — and this is the most common surprise for people who learned
  complexity before they learned hardware.
- **Structure of Arrays beats Array of Structures** when you touch one field across many
  records. You stop loading the fields you don't need.
- **Working set size is a step function.** Performance is fine until your data stops
  fitting in a cache level, then falls off a cliff. **Benchmark across sizes, not at one
  size** (§13 → `algo-probabilistic-concurrency-and-measurement`).

### 2.2 Branches

**~15–20 cycles for a mispredict.** Predictable branches are nearly free; unpredictable
ones are catastrophic. **This is why branchless techniques exist**: conditional moves,
arithmetic masking, and the branchless partitioning that makes modern quicksort fast (§7 → `algo-core-algorithms`).

**⚠️ It's also why sorted input can make code *faster*** — the famous "why is processing a
sorted array faster" effect is entirely branch prediction, and it's a useful sanity check
on whether you understand your own profile.

### 2.3 Allocation, indirection, and the rest

**Allocation is expensive and often the real cost** in a structure that looks
algorithmically fine. Pre-allocate, pool, reuse, and prefer structures that allocate in
blocks over ones that allocate per element. **In GC languages, allocation is future GC
pressure**, and a GC pause is a latency spike attributed to the wrong place.

**Pointer indirection costs a potential cache miss each hop.** Every level of a pointer
structure is a chance to stall.

**SIMD** processes 4–16 elements per instruction. Autovectorization is real but fragile;
the structures that vectorize are flat, contiguous, and branch-light. **This is a data
layout question before it's an instruction-selection question.**

**[DURABLE] The synthesis: the constant factor is not a footnote in this domain — it
routinely spans two orders of magnitude, and it is determined mostly by memory layout.**
