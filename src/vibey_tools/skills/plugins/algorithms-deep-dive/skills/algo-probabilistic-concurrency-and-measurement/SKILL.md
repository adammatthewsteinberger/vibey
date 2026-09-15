---
name: algo-probabilistic-concurrency-and-measurement
description: "Use when working with approximate or concurrent structures, or when measuring performance: Bloom filters, HyperLogLog, count-min sketch and streaming structures, benchmarking and profiling discipline, vector and similarity search (HNSW, IVF, approximate nearest neighbour recall), and concurrent data structures — locks, lock-free and wait-free designs, memory ordering, and the ABA problem."
---

# Algorithms Deep Dive: Probabilistic Structures, Measurement, and Concurrency

> **Part 4 of 5** of the *Algorithms Deep Dive* reference (plugin `algorithms-deep-dive`), covering §12–§14. Sibling skills: `algo-foundations-and-machine-model` (§0–§2), `algo-data-structures` (§3–§6), `algo-core-algorithms` (§7–§11), `algo-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    beats an O(log n) walk over a pointer structure (§2 → `algo-foundations-and-machine-model`). Asymptotics tell you how
>    something scales; they do not tell you which is faster at your n.
> 3. **You will almost never write these.** You will *choose* them. The valuable skill is
>    knowing what your standard library actually does, what its failure modes are, and
>    when its default is wrong for your data — not reimplementing quicksort (§13).

---

## §12. Probabilistic and Streaming Structures

**[DURABLE] These trade a bounded, quantified error for enormous savings in space or time,
and they are dramatically under-used relative to how often they fit.**

| Structure | Answers | Trades |
|---|---|---|
| **Bloom filter** | "Definitely not present" / "probably present" | ⚠️ **False positives, never false negatives.** No deletion |
| **Counting / Cuckoo filter** | Same, with deletion | More space; cuckoo also gives better locality |
| **HyperLogLog** | Approximate cardinality | ~2% error in **kilobytes** for billions of items. Mergeable |
| **Count-Min Sketch** | Approximate frequency | Overestimates only; heavy-hitters |
| **t-digest / DDSketch** | Approximate quantiles | ⚠️ **What your metrics system uses for p99** |
| **MinHash / SimHash** | Set/document similarity | Near-duplicate detection at scale |
| **Reservoir sampling** | Uniform sample from a stream of unknown length | One pass, O(k) space |

**[DURABLE] The canonical use**: **Bloom filters in front of LSM-tree reads** (§5.2 → `algo-data-structures`), so a
lookup skips levels that definitely don't contain the key. That single application is why
write-optimized stores can also read acceptably.

**⚠️ Know the error model before deploying.** "2% error" on a cardinality estimate is fine
for a dashboard and unacceptable for billing. **The question is always: what does being
wrong cost here?**

---

## §13. Measurement

**[DURABLE] The discipline that separates real optimization from folklore**, and the part
most engineers skip.

**Profile first.** Intuition about where time goes is unreliable, and the hot spot is
usually not where you'd guess. **Amdahl's law**: optimizing 10% of runtime by 10× gains
you 9%.

**Benchmarking correctly:**
- **Realistic data, realistic distribution, realistic size** — and **benchmark across
  sizes**, because §2.1 → `algo-foundations-and-machine-model`'s cache cliffs make single-size benchmarks actively misleading.
- **Warm up** (JIT, caches, branch predictors), then **measure many iterations**.
- **⚠️ Prevent dead-code elimination** — the compiler will delete your benchmark if the
  result is unused. Use the black-box/`std::hint::black_box` facility your language
  provides.
- **Report distributions, not means.** p50/p95/p99 and variance. **A mean hides the tail
  that your users experience.**
- **Control the environment**: pin CPUs, disable turbo/frequency scaling if you can, and
  run enough samples to see the noise floor.
- **Use a real harness** — Criterion, JMH, `google/benchmark`, `pytest-benchmark`,
  `hyperfine`. Hand-rolled timing loops get all of the above wrong.
- **Measure hardware counters** when it matters: `perf stat` gives cache misses, branch
  mispredicts, and IPC, which turns "it's slow" into "it's memory-bound."

### 13.4 Vector and similarity search

**[VERSIONED] Worth its own subsection because it went from research to standard
infrastructure in about four years**, driven by embeddings and RAG.

**The problem**: nearest-neighbour in high dimensions, where **k-d trees fail** (§8 → `algo-core-algorithms`) and
exact search is a linear scan. **The answer is approximate (ANN), trading recall for
speed.**

| Approach | Notes |
|---|---|
| **HNSW** | Hierarchical navigable small world graphs. **The in-memory default.** Excellent recall/QPS; ⚠️ **memory-hungry — the whole index in RAM** |
| **IVF** | Partition via k-means, search `nprobe` nearest cells. Scales better to billions; needs `nlist`/`nprobe` tuning |
| **DiskANN (Vamana)** | **Index and full-precision vectors on SSD, PQ-compressed vectors in RAM** for routing, then rerank. Indexes 1B+ vectors on a single machine with ~64 GB RAM |
| **ScaNN** | Anisotropic quantization — optimizes directional accuracy rather than reconstruction error; strong for inner-product search |
| **CAGRA** | GPU-oriented graph index |

**Quantization is the other axis**: **PQ** (product quantization — typically 16–32× smaller),
**scalar**, **binary**, and **RaBitQ**. **⚠️ Nearly all production deployments quantize and
rerank**, because storing full-precision vectors in RAM at scale is the dominant cost.

> **⚠️ GOTCHA — filtered search is where naive implementations fall over, and it's what
> real applications need.** "Find similar documents *where tenant = X and date > Y*" breaks
> the graph assumptions. **Post-filtering** either loses results or requires
> over-fetching; **pre-filtering** needs a mask that grows linearly with the dataset. And
> **when too many vectors are filtered out, an HNSW graph becomes disconnected and recall
> collapses** — the "recall cliff." This drove a whole line of work (Filtered-DiskANN,
> ACORN, and vendor-specific filterable-HNSW designs) and **it is the first thing to test
> when evaluating a vector store**, because benchmark numbers are almost always unfiltered.

**[DURABLE] Benchmark on your own data.** ANN performance is extremely dataset-dependent —
dimensionality, intrinsic dimension, and clustering all matter more than the published
QPS-vs-recall curve. **ANN-Benchmarks** and **VIBE** are the standard harnesses; use them
as method, not as an answer.

---

## §14. Concurrent Data Structures

**[DURABLE] Concurrency changes every answer in this document**, and the ordering of the
options below is the recommended order of preference.

```
1. DON'T SHARE           Partition the data. Thread-local, sharded, actor-per-key.
                         ⚠️ Almost always the right answer and the least explored one
2. IMMUTABLE / PERSISTENT  Structural sharing; readers never block. Great for read-heavy
3. COARSE LOCK           A single mutex. Boring, correct, and fast enough far more often
                         than people assume. START HERE and measure
4. FINE-GRAINED LOCKS    Striped/sharded locks. ⚠️ Deadlock risk; establish a lock order
5. RW LOCKS              Only when reads massively dominate; ⚠️ writer starvation
6. LOCK-FREE             CAS-based. Hard to get right, harder to debug
7. WAIT-FREE             Bounded steps per operation. Rare, and usually not worth it
```

**Key structures**: **concurrent hash maps** (striped or lock-free — `ConcurrentHashMap`,
`DashMap`), **MPMC/SPSC queues** (⚠️ **SPSC ring buffers are dramatically faster** — use the
most restrictive queue that fits), **the Disruptor** pattern (ring buffer + sequence
barriers; the reference design for low-latency pipelines), **RCU** (read-copy-update —
readers pay nothing), **hazard pointers** and **epoch-based reclamation** for the
memory-reclamation problem, and **CRDTs** for eventually-consistent replicated state.

> **⚠️ GOTCHA — the concurrency-specific failure modes:**
> - **The ABA problem.** A CAS succeeds because the value returned to A, but the structure
>   changed underneath. **The reason hazard pointers and epochs exist.**
> - **Memory reclamation is the hard part of lock-free programming**, not the algorithm.
>   You can't free a node while another thread might read it.
> - **⚠️ False sharing.** Two threads writing *different* variables on the **same cache
>   line** ping-pong that line between cores. **Can cost an order of magnitude, and it is
>   invisible in the source.** Pad to cache-line boundaries.
> - **Memory ordering.** Acquire/release/seq_cst are not decoration. **Getting this wrong
>   produces bugs that appear only on weakly-ordered architectures (ARM) after passing all
>   tests on x86.**
> - **Lock-free ≠ faster.** Under contention it often *is*; under low contention a mutex
>   frequently wins on simplicity and cache behaviour. **Measure.**
