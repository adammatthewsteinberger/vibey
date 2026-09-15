---
name: algo-core-algorithms
description: "Use when implementing or choosing a core algorithm: sorting as libraries actually implement it (introsort, Timsort, pdqsort, radix) and how to choose, searching and indexing, graph algorithms (traversal, shortest paths, topological sort, flow, union-find), string and text algorithms (substring search, edit distance, suffix structures), and dynamic programming, greedy, divide and conquer, and amortized analysis."
---

# Algorithms Deep Dive: Sorting, Searching, Graphs, Strings, and Dynamic Programming

> **Part 3 of 5** of the *Algorithms Deep Dive* reference (plugin `algorithms-deep-dive`), covering §7–§11. Sibling skills: `algo-foundations-and-machine-model` (§0–§2), `algo-data-structures` (§3–§6), `algo-probabilistic-concurrency-and-measurement` (§12–§14), `algo-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    **If your algorithm is complicated, your data layout is probably wrong** (§3–§7 → `algo-data-structures`).
> 2. **Asymptotic analysis models the wrong machine.** It assumes uniform-cost memory
>    access, which stopped being true in the 1990s. **A cache miss is ~100× an arithmetic
>    op, and a branch mispredict ~15–20 cycles** — so an O(n) scan over an array routinely
>    beats an O(log n) walk over a pointer structure (§2 → `algo-foundations-and-machine-model`). Asymptotics tell you how
>    something scales; they do not tell you which is faster at your n.
> 3. **You will almost never write these.** You will *choose* them. The valuable skill is
>    knowing what your standard library actually does, what its failure modes are, and
>    when its default is wrong for your data — not reimplementing quicksort (§13 → `algo-probabilistic-concurrency-and-measurement`).

---

## §7. Sorting

### 7.1 What your library actually does

**[DURABLE] Nobody ships a textbook sort.** Every serious standard library uses a hybrid,
and knowing which one tells you its behaviour.

| Family | Where |
|---|---|
| **Introsort** — quicksort + heapsort fallback + insertion sort for small runs | C++ `std::sort`, historically |
| **pdqsort** (pattern-defeating quicksort) | Adds **branchless partitioning**, pattern detection, and adversarial-input handling. Widely adopted |
| **Timsort** — adaptive natural mergesort | Python `sorted`, Java objects, **stable**, exploits existing runs |
| **Powersort** — Timsort with provably near-optimal merge policy | Adopted in CPython |
| **Radix / counting sort** — non-comparison, O(n·k) | Fixed-width keys; ⚠️ genuinely faster when applicable |

**[VERSIONED] The current state of the art is worth knowing as a concrete example of §2 → `algo-foundations-and-machine-model` in
action.** Rust's standard library replaced its sorts in 2024 with **driftsort** (stable,
derived from glidesort) and **ipnsort** (unstable). Reported gains: **ipnsort up to ~2.4×
faster on random inputs**; **driftsort up to ~17× faster on low-cardinality patterns**.

**⚠️ The design choices are the instructive part**: both **prefer instruction-level
parallelism over SIMD** — because ILP generalizes across architectures and data types while
SIMD depends on specific vector instruction sets — and both are **optimized to minimize
i-cache misses**, a factor automated instruction-count analysis doesn't capture. Rust's
`sort_unstable` documents that ipnsort **achieves linear time on fully sorted and reversed
inputs**, and **O(n log k) on inputs with k distinct elements**.

### 7.2 Choosing

```
Need stability?          → stable sort (Timsort/driftsort/std::stable_sort)
Fixed-width integer keys → radix sort can beat comparison sorting outright
Nearly sorted data       → adaptive sorts (Timsort family) approach O(n)
Small n (< ~20)          → insertion sort. This is what hybrids do internally
Top-k only               → heap, O(n log k). Don't sort (§6)
k-th element only        → quickselect, O(n) average (introselect for worst case)
Larger than memory       → external merge sort
Sort key expensive       → decorate-sort-undecorate (Schwartzian transform)
```

**[DURABLE] The comparison lower bound is Ω(n log n)** — and **radix sort doesn't violate
it**, because it isn't comparison-based. That distinction is worth being precise about.

**⚠️ Comparator correctness is a real production bug source.** Your comparator must define
a **strict weak ordering** — irreflexive, antisymmetric, transitive, with transitive
incomparability. Violating it is undefined behaviour and **can crash or corrupt memory in
C++**; Rust's `sort_unstable` documents that it "may panic if `Ord` does not implement a
total order." **NaN in a float comparator is the classic trigger.**

---

## §8. Searching and Indexing

**Binary search** — O(log n), and **⚠️ notoriously easy to get wrong** (the overflow in
`(lo+hi)/2` shipped in the JDK for years). **Use the library.** The variants that matter
are `lower_bound`/`upper_bound` — "first element ≥ x" is more often what you want than
"is x present."

**⚠️ Interpolation search** is O(log log n) on uniform data and O(n) on skewed data.
**Branchless / Eytzinger-layout binary search** rearranges the array in BFS order for
better cache behaviour — a real win for repeated searches on a static array.

**Inverted indexes** — the core of full-text search: term → posting list, with
skip pointers, compression (delta + varint/PFOR), and scoring (BM25). **If you're building
search, you're building this or using Lucene.**

**Bitmap indexes** — **Roaring bitmaps** are the practical standard: hybrid
array/bitmap/run containers, and **the right answer for large set intersection**,
which is what filtered search reduces to.

**Spatial indexes** — R-trees (rectangles, the standard in spatial DBs), k-d trees
(⚠️ **degrade badly above ~20 dimensions** — the curse of dimensionality), quadtrees /
octrees, **geohash and S2/H3** for lat-long. Which is why high-dimensional similarity
needs an entirely different approach (§13.4 → `algo-probabilistic-concurrency-and-measurement`).

---

## §9. Graphs

**[DURABLE] Representation is the first decision and it's usually adjacency lists** —
adjacency matrices cost O(V²) space and only win for genuinely dense graphs or when you
need O(1) edge existence checks. **CSR (compressed sparse row)** is the cache-friendly
static form and is what serious graph processing uses.

**The traversals**: **BFS** (shortest path in *unweighted* graphs, level order),
**DFS** (cycle detection, topological sort, SCC, backtracking — ⚠️ **use an explicit stack
in production**; recursion depth on a large graph is a stack overflow).

**Shortest paths, and picking the right one:**

| Algorithm | Use | Complexity |
|---|---|---|
| **BFS** | Unweighted | O(V+E) |
| **Dijkstra** | Non-negative weights | O((V+E) log V) with a heap |
| **A\*** | Single target with a good heuristic | Dijkstra + admissible heuristic |
| **Bellman-Ford** | ⚠️ **Negative weights**; detects negative cycles | O(VE) |
| **Floyd-Warshall** | All pairs, small dense graphs | O(V³) |
| **Bidirectional search** | Point-to-point on large graphs | Often dramatically better |

**⚠️ Dijkstra silently gives wrong answers with negative edges.** It doesn't error; it
returns a plausible wrong path. Know which one you need.

**Also**: **topological sort** (build systems, task scheduling, dependency resolution —
and cycle detection is the same algorithm), **union-find** for connectivity and Kruskal's,
**Prim's** for MST, **max-flow/min-cut** (Dinic's in practice; the reduction target for a
surprising number of assignment and matching problems), **bipartite matching**,
**PageRank** and centrality, and **community detection**.

**[DURABLE] Recognizing that your problem is a graph problem is most of the work.**
Dependency resolution, permissions inheritance, routing, scheduling, deduplication,
recommendation, and data lineage are all graph problems wearing business costumes.

---

## §10. Strings and Text

**Exact search**: **Boyer-Moore** and variants skip ahead and are sublinear in practice;
**KMP** is linear with no worst case; **Rabin-Karp** uses rolling hashes and generalizes
to multiple patterns; **Aho-Corasick** matches many patterns in one pass and is **the right
answer for keyword/blocklist scanning**. **⚠️ In practice, `memmem`/`std::string::find`
with SIMD beats naive implementations of all of these** — measure before implementing.

**Structures**: **suffix arrays** (+ LCP) — practical, compact, and the usual choice over
**suffix trees** (asymptotically nice, memory-hungry). **FM-index / BWT** for compressed
full-text search (the basis of genomic aligners). **Tries and ARTs** (§5.3 → `algo-data-structures`).

**Edit distance and similarity**: Levenshtein is O(mn) DP — **and §9 of a
theory-of-computation reference explains why that's conditionally optimal under SETH, so
don't try to beat it asymptotically**. Practical answers: bound the edit distance
(banded DP), use **Myers' bit-parallel algorithm**, or switch measures — **SimHash/MinHash
for near-duplicate detection at scale**, n-gram similarity, or trigram indexes.

**⚠️ Unicode will hurt you.** Normalization forms (NFC/NFD/NFKC/NFKD), grapheme clusters vs.
code points vs. bytes, case folding that isn't symmetric, collation that's
locale-dependent. **"Reverse a string" and "uppercase a string" are not simple operations**
and treating them as such is a recurring source of bugs in international products.

---

## §11. Dynamic Programming, Greedy, and Amortization

### 11.1 Dynamic programming

**[DURABLE] The recognition test: optimal substructure plus overlapping subproblems.**
If a problem's optimal solution is built from optimal solutions to subproblems, and those
subproblems repeat, it's DP.

**Top-down (memoization)** is easier to write and follows the recursion naturally;
**bottom-up (tabulation)** avoids recursion overhead and enables **space optimization** —
**⚠️ most DP tables only need the last row or two, turning O(n·m) space into O(m)**, which
is frequently the difference between fitting in cache and not.

**The classic patterns worth recognizing**: knapsack, LCS/edit distance, longest increasing
subsequence (**⚠️ the O(n log n) patience-sorting version, not the O(n²) one**), matrix
chain, interval scheduling, coin change, and DP over subsets/bitmasks (2ⁿ·n — fine for
n ≤ 20).

### 11.2 Greedy

Works when the **greedy choice property** holds — a locally optimal choice is globally
safe. **⚠️ Greedy is right far less often than it looks right, and the failure is silent:**
you get a plausible suboptimal answer, not an error. **Either prove the exchange argument
or test against brute force on small inputs.**

### 11.3 Divide and conquer
Mergesort, quicksort, FFT, Karatsuba, Strassen, closest pair. **The Master Theorem** gives
the complexity for the standard recurrence shapes.

### 11.4 Amortized analysis

**[DURABLE] Amortized O(1) means "cheap on average across a sequence," not "cheap every
time."** Dynamic array growth, hash table resize, union-find with path compression, and
splay trees are all amortized.

**⚠️ This is a latency-tail issue, and it's the most under-appreciated point here.**
Amortized-cheap structures have **occasional expensive operations**, and if you have a p99
latency budget, that occasional O(n) resize is exactly what shows up there. **For strict
latency bounds, prefer structures with good worst-case behaviour, or pre-size to avoid the
resize entirely.**
