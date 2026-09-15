---
name: algo-reference
description: "Use when checking an algorithm or data-structure anti-pattern, weighing a contested question, confirming whether a claim is still current (snapshot verified August 2026), finding the books and sources, or needing the structure selection table, the latency numbers worth keeping in your head, and the checklist to run before optimizing. Companion to the other algorithms-deep-dive skills."
---

# Algorithms Deep Dive: Anti-Patterns, Contested Questions, Currency, and Canon

> **Part 5 of 5** of the *Algorithms Deep Dive* reference (plugin `algorithms-deep-dive`), covering §15–§20. Sibling skills: `algo-foundations-and-machine-model` (§0–§2), `algo-data-structures` (§3–§6), `algo-core-algorithms` (§7–§11), `algo-probabilistic-concurrency-and-measurement` (§12–§14). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 below for the currency snapshot and what goes stale first.

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
>    beats an O(log n) walk over a pointer structure (§2 → `algo-foundations-and-machine-model`). Asymptotics tell you how
>    something scales; they do not tell you which is faster at your n.
> 3. **You will almost never write these.** You will *choose* them. The valuable skill is
>    knowing what your standard library actually does, what its failure modes are, and
>    when its default is wrong for your data — not reimplementing quicksort (§13 → `algo-probabilistic-concurrency-and-measurement`).

---

## §15. Anti-Patterns

| Anti-pattern | Why |
|---|---|
| Choosing by asymptotics alone | **The constant spans two orders of magnitude and is set by memory layout** (§2 → `algo-foundations-and-machine-model`) |
| Linked list as the default sequence | One cache miss per node; arrays win to surprisingly large n (§3 → `algo-data-structures`) |
| Optimizing without profiling | The hot spot is rarely where you think (§13 → `algo-probabilistic-concurrency-and-measurement`) |
| Benchmarking at one input size | ⚠️ **Cache cliffs make this actively misleading** (§2.1 → `algo-foundations-and-machine-model`, §13 → `algo-probabilistic-concurrency-and-measurement`) |
| Benchmarking without a black-box hint | The compiler deletes your benchmark (§13 → `algo-probabilistic-concurrency-and-measurement`) |
| Reporting mean latency | Hides the tail your users experience. p50/p95/p99 (§13 → `algo-probabilistic-concurrency-and-measurement`) |
| Hash map when you need ordered iteration or ranges | Wrong structure class (§4 → `algo-data-structures` vs §5 → `algo-data-structures`) |
| Tree when you only do point lookups | Strictly worse than a hash map (§5.1 → `algo-data-structures`) |
| Not pre-sizing a collection you can size | Repeated reallocation, and a resize latency spike (§3 → `algo-data-structures`, §4.2 → `algo-data-structures`) |
| Weak/predictable hash on untrusted keys | ⚠️ **Hash-flooding DoS** (§4.2 → `algo-data-structures`) |
| Depending on hash map iteration order | Unordered by definition, randomized in some languages (§4.2 → `algo-data-structures`) |
| Mutating a key after insertion | Silently corrupts the table (§4.2 → `algo-data-structures`) |
| Comparator that isn't a strict weak ordering | ⚠️ **UB — can crash or corrupt memory** (§7.2 → `algo-core-algorithms`) |
| Sorting to get the top k | Heap is O(n log k) (§6 → `algo-data-structures`) |
| Sorting to get one element | Quickselect is O(n) average (§7.2 → `algo-core-algorithms`) |
| Assuming Fibonacci heaps are faster | **The canonical constants-defeat-asymptotics case** (§6 → `algo-data-structures`) |
| Dijkstra with negative edges | ⚠️ **Silently wrong, not an error** (§9 → `algo-core-algorithms`) |
| Recursive DFS on a large graph | Stack overflow. Explicit stack (§9 → `algo-core-algorithms`) |
| Adjacency matrix for a sparse graph | O(V²) space for nothing (§9 → `algo-core-algorithms`) |
| Greedy without proving the exchange argument | ⚠️ Silently suboptimal (§11.2 → `algo-core-algorithms`) |
| DP table storing all rows when two suffice | Often the cache-fit difference (§11.1 → `algo-core-algorithms`) |
| Treating amortized O(1) as per-operation O(1) | ⚠️ **This is your p99** (§11.4 → `algo-core-algorithms`) |
| Exact counting when an estimate would do | HLL is kilobytes for billions (§12 → `algo-probabilistic-concurrency-and-measurement`) |
| Deploying a sketch without knowing the error model | Fine for a dashboard, not for billing (§12 → `algo-probabilistic-concurrency-and-measurement`) |
| Reimplementing binary search | ⚠️ The JDK shipped an overflow bug for years (§8 → `algo-core-algorithms`) |
| Hand-rolling string search | SIMD `memmem` beats naive KMP (§10 → `algo-core-algorithms`) |
| Treating strings as arrays of characters | Unicode: graphemes ≠ code points ≠ bytes (§10 → `algo-core-algorithms`) |
| k-d tree for high-dimensional similarity | ⚠️ Degrades above ~20 dims (§8 → `algo-core-algorithms`, §13.4 → `algo-probabilistic-concurrency-and-measurement`) |
| Evaluating a vector store on unfiltered benchmarks | **Filtered search is where they fall over** (§13.4 → `algo-probabilistic-concurrency-and-measurement`) |
| Reaching for lock-free first | Try not-sharing, then a mutex, then measure (§14 → `algo-probabilistic-concurrency-and-measurement`) |
| Ignoring false sharing | ⚠️ **Order-of-magnitude cost, invisible in source** (§14 → `algo-probabilistic-concurrency-and-measurement`) |
| Testing concurrent code only on x86 | Memory-ordering bugs surface on ARM (§14 → `algo-probabilistic-concurrency-and-measurement`) |
| Rewriting your hash map because of a 2025 paper | ⚠️ Insertions only, and not the bottleneck (§4.3 → `algo-data-structures`) |

---

## §16. Contested Questions

**16.1 Is there a universal "best" structure?** No, and the **RUM conjecture** names why:
you can optimize at most two of **R**ead overhead, **U**pdate overhead, and **M**emory
overhead. **The B-tree vs. LSM divide is RUM made concrete** (§5.2 → `algo-data-structures`). Treat any claim of
across-the-board superiority as a signal that the benchmark was narrow.

**16.2 How much should engineers implement vs. use?** *For implementing*: you understand
the failure modes, and standard libraries make general-purpose choices that may be wrong
for your data. *For using*: library implementations are extensively tested, tuned, and
maintained, and **your hand-rolled version will be slower and buggier.** **[CONTESTED] The
position here: implement once to learn, then use the library — and invest your effort in
knowing what the library does rather than in replacing it.**

**16.3 Do interview algorithm questions measure anything?** *For*: they test problem
decomposition, and knowing the toolkit genuinely helps. *Against*: they select for recent
practice on a narrow corpus, correlate poorly with the job, and reward memorization.
**Widely and legitimately contested.**

**16.4 Are learned indexes real?** Replacing index structures with models that predict
position. *For*: strong results on read-only sorted data, real memory savings. *Against*:
updates are hard, worst-case guarantees are weak, and adoption remains limited relative to
the attention. **Genuinely unsettled; treat production claims with skepticism.**

**16.5 Cache-oblivious vs. cache-aware?** Cache-oblivious algorithms achieve good behaviour
at every level of the hierarchy without knowing its parameters — elegant and theoretically
lovely. **Cache-aware tuning usually wins in practice when you know your target**, at the
cost of portability.

**16.6 SIMD vs. ILP?** ⚠️ **A live design question, not a settled one.** Rust's new sorts
deliberately **chose instruction-level parallelism over SIMD**, on the grounds that ILP
adapts across architectures and data types while SIMD depends on specific vector
instruction sets. Others take the opposite view for fixed workloads on known hardware.
**The trade-off is genuinely portability vs. peak.**

**16.7 Do theoretical hash-table results matter to practitioners?** §4.3 → `algo-data-structures`. **The honest
answer: rarely and indirectly** — but the reason to care is that "settled for 40 years"
turned out not to mean "settled."

---

## §17. Currency Snapshot — verified August 2026

**[DURABLE] Read this section knowing that most of this document does not move.** Quicksort
is 1961, B-trees 1970, Dijkstra 1959, Bloom filters 1970. What follows is what genuinely
changed.

| Thing | Status as of Aug 2026 | Decay risk |
|---|---|---|
| **⚠️ Optimal open addressing** | **January 2025: Farach-Colton, Krapivin & Kuszmaul, "Optimal Bounds for Open Addressing Without Reordering" (arXiv 2501.02305), disproving the central conjecture of Yao's "Uniform Hashing is Optimal" (1985).** **Funnel hashing** (greedy): **O(log² δ⁻¹)** worst-case expected probes, refuting Yao's Ω(δ⁻¹) claim. **Elastic hashing** (non-greedy): **O(1) amortized expected**, **O(log δ⁻¹) worst-case expected**, without reordering. **All results have matching lower bounds.** ⚠️ **CACM's caveats: disproves Yao's conjectures but not Ullman's; some non-open-addressing designs (Iceberg tables) are faster; the construction covers insertions only, not deletions.** Authors "take a lower-key view" than the coverage did | Low (theorem) |
| **Rust standard-library sorts** | **driftsort** (stable, from glidesort) and **ipnsort** (unstable) merged 2024. Reported: **ipnsort up to ~2.4× faster on random inputs**; **driftsort up to ~17× on low-cardinality patterns (random_d20)**. ⚠️ Both **prefer ILP over SIMD** for cross-architecture adaptability, and both minimize **i-cache misses** — a factor instruction-count analysis misses. `sort_unstable` documents **linear time on sorted and reversed inputs**, **O(n log k)** for k distinct elements | Medium |
| **Sorting landscape generally** | **pdqsort** is the widely-adopted branchless-partitioning baseline (Rust, and ported into other ecosystems including a Dart `package:collection` proposal). **fluxsort/crumsort** ideas were adopted into crumsort-rs, glidesort, ipnsort, driftsort. **Powersort** (provably near-optimal merge policy) adopted in CPython | Medium |
| **Swiss tables** | `absl::flat_hash_map` and Rust's `hashbrown`-backed `HashMap` — SIMD-scanned control bytes over open addressing. Current practical state of the art | Low |
| **Vector search: indexes** | **HNSW** the in-memory default; **IVF** for billion-scale partitioning; **DiskANN/Vamana** — SSD-resident index + PQ vectors in RAM, indexing **1B+ vectors on one machine with ~64 GB RAM**, ~95%+ recall@1 at sub-5ms on SIFT-1B; **ScaNN** (anisotropic quantization); **CAGRA** (GPU). Reported 2026 scaling: **DiskANN to ~4.8B vectors on a single server** with GPU-accelerated build via NVIDIA cuVS | **High** |
| **Vector search: quantization** | **PQ (typically 16–32× compression), scalar, binary, RaBitQ.** Quantize-then-rerank is the standard production pattern. Binary quantization reported in Elasticsearch with large cost/indexing-speed gains | **High** |
| **⚠️ Filtered ANN** | **The live problem.** Post-filtering loses results or over-fetches; pre-filtering needs a linearly-growing mask; **heavy filtering disconnects the HNSW graph → recall cliff.** Active line of work: **Filtered-DiskANN** (reported order-of-magnitude gains over IVF/HNSW/NHQ/Milvus baselines, recall near 100% at specificity down to 10⁻⁴–10⁻⁶), **ACORN**, **CAPS**, vendor filterable-HNSW designs. **Benchmarks are usually unfiltered — test this yourself** | **High** |
| **ANN benchmarking** | **ANN-Benchmarks** remains the standard containerized harness; **VIBE** (2025) added an embeddings-focused benchmark; **big-ann-benchmarks** covers filtered tracks | Medium |
| **Learned indexes** | Still research-forward; adoption limited relative to attention (§16.4) | Medium |

**Goes stale fastest:** everything in §13.4 → `algo-probabilistic-concurrency-and-measurement` — vector search is moving quarterly.
**Essentially never stale:** §1–§3 → `algo-foundations-and-machine-model`, `algo-data-structures`, §5–§12 → `algo-data-structures`, `algo-core-algorithms`, `algo-probabilistic-concurrency-and-measurement`, §14 → `algo-probabilistic-concurrency-and-measurement`'s principles, §15.

---

## §18. The Canon

### 18.1 Books

| Author | Work | Why |
|---|---|---|
| **Cormen, Leiserson, Rivest & Stein** | ***Introduction to Algorithms*** (CLRS) | The reference. Comprehensive, rigorous, not a tutorial |
| **Sedgewick & Wayne** | ***Algorithms***, 4th ed. | **The best learning book** — implementations you can read, excellent site and course |
| **Kleinberg & Tardos** | *Algorithm Design* | **The best on *recognizing* which technique applies** — the actual skill |
| **Skiena** | ***The Algorithm Design Manual*** | ⚠️ **The most practical of the lot.** Part 2 is a catalogue: "I have this problem, what do I use?" |
| **Bentley** | ***Programming Pearls*** | Short, old, and still the best writing on algorithm engineering and measurement |
| **Knuth** | *TAOCP* | Monumental. A reference to consult, not to read through |
| **Demaine / Erik & Martin** | *Advanced Data Structures* (MIT OCW) | For the exotic structures |
| **Fog, Agner** | *Optimization manuals* (free) | §2 → `algo-foundations-and-machine-model` in exhaustive detail. **The reference for what the hardware does** |
| **Herlihy & Shavit** | ***The Art of Multiprocessor Programming*** | §14 → `algo-probabilistic-concurrency-and-measurement`, and the standard |
| **Kleppmann** | *Designing Data-Intensive Applications* | ⚠️ **The best treatment of §5.2 → `algo-data-structures`'s B-tree/LSM trade-off in context** |
| **Petrov** | *Database Internals* | Storage structures in depth |
| **Roughgarden** | *Algorithms Illuminated* (4 vols) | Clear, well-paced, with a good companion course |
| **Okasaki** | *Purely Functional Data Structures* | Persistent/immutable structures; underlies §14 → `algo-probabilistic-concurrency-and-measurement`'s option 2 |

### 18.2 People and sources
**Sedgewick** and **Roughgarden** (courses), **Erik Demaine** (MIT 6.006/6.851 lectures —
outstanding), **Daniel Lemire** (SIMD, fast parsing, `simdjson` — **the best public writing
on measured algorithm engineering**), **Andrei Alexandrescu** ("Speed Is Found In The
Minds of People"), **Chandler Carruth** (CppCon talks on data structures and hardware),
**Martin Thompson** (mechanical sympathy, the Disruptor), **Orson Peters** (pdqsort,
glidesort), **Lukas Bergdoll** (`sort-research-rs` — genuinely rigorous sort benchmarking),
**Martín Farach-Colton** and **William Kuszmaul** (§4.3 → `algo-data-structures`), **Quanta Magazine** for
accessible coverage of results like §4.3 → `algo-data-structures`'s.

**Practical**: **`sort-research-rs`** (the benchmark suite behind §7.1 → `algo-core-algorithms`), **ANN-Benchmarks**
and **VIBE** (§13.4 → `algo-probabilistic-concurrency-and-measurement`), **Google Benchmark / Criterion / JMH / hyperfine**, **`perf`** and
**Godbolt**, **Big-O Cheat Sheet** (with §2 → `algo-foundations-and-machine-model`'s caveat firmly in mind), and **VisuAlgo** for
building intuition.

---

## §19. Quick Reference

### 19.1 The selection table

| Need | Use |
|---|---|
| Sequence, index access | **Dynamic array.** Default (§3 → `algo-data-structures`) |
| Queue / both ends | Deque or ring buffer (§3 → `algo-data-structures`) |
| Point lookup by key | **Hash map.** Default (§4 → `algo-data-structures`) |
| Ordered keys, ranges, successor | B-tree / balanced BST (§5 → `algo-data-structures`) |
| Keys on disk, read-heavy | **B+ tree** (§5.2 → `algo-data-structures`) |
| Keys on disk, write-heavy | **LSM tree** (+ Bloom filters) (§5.2 → `algo-data-structures`) |
| String keys with shared prefixes | Trie / ART (§5.3 → `algo-data-structures`) |
| Repeated min/max | Binary heap (§6 → `algo-data-structures`) |
| Top k of n | **Bounded heap, O(n log k)** (§6 → `algo-data-structures`) |
| k-th element | **Quickselect, O(n) avg** (§7.2 → `algo-core-algorithms`) |
| Connectivity / grouping | **Union-Find** (§5.3 → `algo-data-structures`) |
| Shortest path, unweighted | BFS (§9 → `algo-core-algorithms`) |
| Shortest path, non-negative | Dijkstra (§9 → `algo-core-algorithms`) |
| **Negative edge weights** | **Bellman-Ford** — Dijkstra is silently wrong (§9 → `algo-core-algorithms`) |
| Dependency order / cycle detection | Topological sort (§9 → `algo-core-algorithms`) |
| Many patterns, one pass | Aho-Corasick (§10 → `algo-core-algorithms`) |
| "Have I seen this?" at scale | Bloom / cuckoo filter (§12 → `algo-probabilistic-concurrency-and-measurement`) |
| "How many distinct?" at scale | **HyperLogLog** (§12 → `algo-probabilistic-concurrency-and-measurement`) |
| Percentiles over a stream | t-digest / DDSketch (§12 → `algo-probabilistic-concurrency-and-measurement`) |
| Near-duplicate detection | MinHash / SimHash (§10 → `algo-core-algorithms`, §12 → `algo-probabilistic-concurrency-and-measurement`) |
| Large set intersection | **Roaring bitmaps** (§8 → `algo-core-algorithms`) |
| High-dimensional similarity | **HNSW / DiskANN + quantization** (§13.4 → `algo-probabilistic-concurrency-and-measurement`) |
| Geospatial | R-tree, S2/H3 (§8 → `algo-core-algorithms`) |
| Shared mutable state | **Try not sharing first**, then a mutex (§14 → `algo-probabilistic-concurrency-and-measurement`) |

### 19.2 Numbers to keep in your head
- **Cache line: 64 bytes.** L1 ~4 cycles, DRAM ~200–300. **The cliff is DRAM.**
- **Branch mispredict: ~15–20 cycles.**
- **Heapify is O(n)**, not O(n log n).
- **Comparison sorting is Ω(n log n)**; radix isn't comparison-based.
- **Hash maps resize around 0.7–0.9 load** — and that's an O(n) latency spike.
- **k-d trees degrade above ~20 dimensions.**
- **HLL: ~2% error, kilobytes, billions of items, mergeable.**
- **Amortized O(1) is your p99 problem, not your average-case win.**

### 19.3 Before optimizing
- [ ] Have I profiled, or am I guessing? (§13 → `algo-probabilistic-concurrency-and-measurement`)
- [ ] What fraction of runtime is this? (Amdahl)
- [ ] Is the problem the algorithm, or the memory layout? (§2 → `algo-foundations-and-machine-model`)
- [ ] Am I benchmarking across input sizes? (§2.1 → `algo-foundations-and-machine-model`)
- [ ] Realistic data and distribution?
- [ ] Reporting the distribution, not the mean?
- [ ] Would a different structure make the algorithm trivial? (§1 → `algo-foundations-and-machine-model`)
- [ ] Would approximation be acceptable? (§12 → `algo-probabilistic-concurrency-and-measurement`)
- [ ] Is the standard library's default actually wrong for my data, or do I just assume so?

---

## §20. Sources and Method

**Method.** Narrative review, written as **selection and engineering guidance** rather than
as a course, and deliberately complementary to a theory-of-computation reference — this
document assumes the question "is it tractable" is settled and addresses "which one, and
why is it slow." **The great majority of the material is textbook-stable**: the structures
and algorithms in §3–§12 → `algo-data-structures`, `algo-core-algorithms`, `algo-probabilistic-concurrency-and-measurement` date from the 1950s–1990s and the trade-offs among them have not
changed. §2 → `algo-foundations-and-machine-model`'s hardware model reflects behaviour that has been broadly stable since roughly
2010; the specific cycle counts are order-of-magnitude figures that vary by
microarchitecture and should be treated as such. Three targeted searches were run in
**August 2026** on the areas where movement was plausible — theoretical hashing results,
modern sort implementations, and vector search. **The rest was not "verified" against web
sources because CLRS, Skiena, Sedgewick, and the primary literature are the authority and
they are stable.**

**Search log** (August 2026): Krapivin/Farach-Colton/Kuszmaul open-addressing result and
its reception · Rust driftsort/ipnsort and the modern sorting landscape · HNSW/DiskANN,
quantization, and filtered ANN search.

**Primary and near-primary sources consulted (selected):**
- **arXiv 2501.02305**, *"Optimal Bounds for Open Addressing Without Reordering"*
  (Farach-Colton, Krapivin, Kuszmaul), read directly for the bounds and the scope of the
  claim; **CACM's "Speeding Up Hash Tables"** for the expert caveats (Ullman's conjecture,
  Iceberg tables, insertions-only); **Quanta** for the accessible account
- **`Voultapher/sort-research-rs`** — the driftsort and ipnsort design write-ups, which are
  the primary source for the ILP-over-SIMD and i-cache reasoning; **Rust standard library
  documentation** for the documented complexity guarantees
- **Vector search**: the **DiskANN/Vamana** line (Subramanya et al., NeurIPS 2019) and
  **Filtered-DiskANN** (WWW 2023) for the filtered-search results; **ANN-Benchmarks**
  (Aumüller, Bernhardsson, Faithfull) and **VIBE** (2025) as the benchmark harnesses;
  **Qdrant's** benchmark documentation for the pre/post-filtering failure analysis; 2026
  survey and systems papers on filtered ANN and quantization

**Confidence statement.** **Very high confidence** in §1–§12 → `algo-foundations-and-machine-model`, `algo-data-structures`, `algo-core-algorithms`, `algo-probabilistic-concurrency-and-measurement` and §14 → `algo-probabilistic-concurrency-and-measurement`'s principles — these
rest on the standard literature and decades of consistent engineering practice, not on
anything I searched. **High confidence** in §4.3 → `algo-data-structures`'s bounds and §7.1 → `algo-core-algorithms`'s Rust design rationale,
both read from primary sources. **Moderate confidence** in the specific performance
multipliers quoted in §17 — the sort speedups are the implementers' own benchmark figures
on their chosen patterns and hardware, and **speedup claims of this kind are always
workload-specific**; treat them as directional. **Lower confidence in §13.4 → `algo-probabilistic-concurrency-and-measurement`'s vector-search
landscape**, which is the fastest-moving material here: several figures come from vendor
blogs and single-system papers with obvious incentives, benchmark methodology varies
enormously across sources, and the field is moving quarterly — **which is exactly why the
section's actual advice is "benchmark on your own data with your own filters" rather than
any ranking.** §2 → `algo-foundations-and-machine-model`'s cycle counts are approximations for reasoning, not measurements for
your machine.
