---
name: uarch-caches-coherence-consistency-and-virtual-memory
description: "Use when memory behaviour is the performance story: cache organization with associativity, line size and replacement, cache coherence and the MESI-family protocols, memory consistency models and what the hardware may reorder underneath your code, virtual memory, TLBs and page-table walks, and prefetching including what hardware prefetchers can and cannot detect."
---

# Microarchitecture and Memory: Cache Organization, Cache Coherence, Memory Consistency Models, Virtual Memory and Translation, and Prefetching

> **Part 2 of 6** of the *CPU, GPU, NPU and Memory Microarchitecture* reference (plugin `microarchitecture-and-memory-systems`), covering §6–§10. Sibling skills: `uarch-pipelining-out-of-order-branch-prediction-and-simd` (§0–§5), `uarch-gpu-npu-dataflow-and-numeric-formats` (§11–§14), `uarch-dram-memory-controllers-power-and-security` (§15–§19), `uarch-isa-simulation-measurement-roofline-and-specialization` (§20–§24), `uarch-reference` (§25–§30). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The principles are stable. Two areas moved. See §25 → `uarch-reference` for low-precision numeric formats, and next-generation memory standards.

> **⚠️ SCOPE, because this sits between two neighbours.** ⚠️ **A semiconductor reference
> covers device physics and fabrication — how a transistor works and how it's made. A
> computer-hardware reference covers system integration — components, builds, facilities.**
> **⚠️ THIS file is the layer in between: how billions of transistors are ORGANIZED into
> something that executes instructions fast, and why memory systems are the hard part.**
> ⚠️ **It assumes the other two rather than repeating them.**
>
> **⚠️ GOTCHA** boxes mark where architectural intuition is wrong and where the
> abstraction leaks.
>
> **The three ideas that organize this document:**
> 1. **⚠️ THE PROCESSOR LIES TO YOU, DELIBERATELY** (§2–§4 → `uarch-pipelining-out-of-order-branch-prediction-and-simd`). **Instructions do not execute
>    in program order, memory operations do not become visible in program order, and the
>    architecture works hard to maintain the illusion that they do. Every performance
>    surprise and several security disasters live in the gap.**
> 2. **⚠️ MOVING DATA COSTS FAR MORE THAN COMPUTING ON IT** (§6, §13 → `uarch-gpu-npu-dataflow-and-numeric-formats`, §23 → `uarch-isa-simulation-measurement-roofline-and-specialization`). **Energy per
>    arithmetic operation has fallen enormously; energy per byte moved has not. Modern
>    architecture is organized around minimizing data movement, and that single fact
>    explains caches, dataflow accelerators, quantization and HBM alike.**
> 3. **⚠️ PARALLELISM IS EXTRACTED AT EVERY LEVEL, AND EACH HAS A DIFFERENT LIMIT** (§3 → `uarch-pipelining-out-of-order-branch-prediction-and-simd`,
>    §11 → `uarch-gpu-npu-dataflow-and-numeric-formats`, §14 → `uarch-gpu-npu-dataflow-and-numeric-formats`). **ILP is limited by dependencies and branches, DLP by divergence and
>    memory, TLP by synchronization and coherence traffic. Knowing which one you're
>    hitting is the entire diagnostic skill.**

---

## §6. Cache Organization

**⚠️ See a computer-hardware reference for the latency ladder. Here, the mechanism.**
```
⚠️ THE STRUCTURE  address splits into TAG / INDEX / OFFSET
   ⚠️ Direct-mapped (fast, conflict-prone) · fully associative
   (no conflicts, impractical) · ⚠️ N-WAY SET ASSOCIATIVE (the
   real answer, typically 8–16 way at L2/L3)
⚠️ THE THREE Cs of misses  ⚠️ COMPULSORY (first touch) ·
   CAPACITY (working set too big) · ⚠️ CONFLICT (set collisions —
   fixable by associativity or by changing the access stride)
   ⚠️ Plus COHERENCE misses in multiprocessors (§7)
⚠️ REPLACEMENT  LRU is the reference; ⚠️ real caches use
   approximations (pseudo-LRU, RRIP) because true LRU is
   expensive at high associativity
⚠️ WRITE POLICY  write-through vs ⚠️ WRITE-BACK (dominant) ·
   write-allocate vs no-write-allocate · ⚠️ WRITE COMBINING buffers
⚠️ INCLUSIVE vs EXCLUSIVE vs NINE hierarchies — ⚠️ affects
   effective capacity and coherence probe cost
⚠️ ⚠️ THE PATHOLOGIES WORTH KNOWING BY NAME
   ⚠️ FALSE SHARING  two threads writing different variables in
      the SAME LINE — coherence traffic destroys performance
      with no logical sharing at all
   ⚠️ CACHE THRASHING from a stride that maps everything to one set
      (⚠️ powers-of-two array dimensions are the classic cause —
      which is why padding arrays can produce large speedups)
   ⚠️ 4K ALIASING between loads and stores
```

---

## §7. ⚠️ Cache Coherence

> **⚠️ How multiple caches maintain a consistent view of memory — and the source of
> multicore scaling limits.**
```
⚠️ MESI and relatives  each line is Modified / Exclusive / Shared /
   Invalid. ⚠️ MOESI adds Owned; MESIF adds Forward
   ⚠️ THE INVARIANT: one writer OR many readers, never both
⚠️ PROTOCOL FAMILIES  ⚠️ SNOOPING (every cache watches a shared
   bus — simple, doesn't scale) vs ⚠️ DIRECTORY-BASED (a directory
   tracks who holds each line — scales, adds latency and storage)
⚠️ ⚠️ THE COST  a write to a SHARED line requires INVALIDATING every
   other copy and waiting. ⚠️ A contended line ping-ponging between
   cores can be orders of magnitude slower than uncontended access
⚠️ THEREFORE  ⚠️ atomics and locks are expensive not because of the
   instruction but because of the COHERENCE TRAFFIC. ⚠️ An
   uncontended atomic is cheap; a contended one is not, and the
   difference is enormous
⚠️ SCALABLE SYNCHRONIZATION  ⚠️ MCS and ticket locks queue waiters
   to avoid all-cores-spinning-on-one-line; ⚠️ RCU and per-CPU
   data avoid sharing altogether — which is the real answer
⚠️ NUMA  ⚠️ coherence across sockets is far more expensive again
```

---

## §8. ⚠️ Memory Consistency Models

> **⚠️ The most conceptually difficult topic here, and the one most often misunderstood.
> COHERENCE (§7) is about a single location; CONSISTENCY is about the ORDER of operations
> across different locations.**
```
⚠️ SEQUENTIAL CONSISTENCY  ⚠️ the intuitive model — as if all
   operations from all threads interleaved in some global order
   consistent with each program's order. ⚠️ NO REAL HARDWARE
   PROVIDES THIS, because it forbids too many optimizations
⚠️ ⚠️ WHAT REAL HARDWARE DOES
   ⚠️ x86-TSO  ⚠️ relatively strong: stores are buffered, so a
      LOAD MAY BE REORDERED BEFORE AN EARLIER STORE to a
      different address. ⚠️ That one relaxation is enough to break
      naive Dekker-style algorithms
   ⚠️ ARM and RISC-V  ⚠️ WEAKLY ORDERED — loads and stores can be
      reordered much more freely. ⚠️ Code that is correct on x86
      can be BROKEN on ARM with no source change, and this
      surprises people porting between them
⚠️ FENCES / BARRIERS  ⚠️ explicitly constrain reordering; acquire,
   release, and full barriers
⚠️ LANGUAGE MEMORY MODELS  ⚠️ C++11 and Java define their own
   models so portable concurrent code is possible at all.
   ⚠️ memory_order_relaxed / acquire / release / seq_cst map onto
   whatever the hardware needs
⚠️ ⚠️ THE COMPILER REORDERS TOO. ⚠️ A hardware fence without a
   compiler barrier is not enough, and "volatile" is NOT a
   synchronization primitive in C/C++
```
**⚠️ The practical guidance**: ⚠️ **use the language's atomics and locks rather than
hand-rolled fences; ⚠️ if you write lock-free code, TEST ON WEAK HARDWARE, because x86
hides bugs that ARM exposes.**

---

## §9. Virtual Memory and Translation

**⚠️ Multi-level page tables** (⚠️ four or five levels on x86-64), ⚠️ **so a TLB miss can
cost several memory accesses — a "page walk."**
**⚠️ The TLB** caches translations, ⚠️ **and TLB reach — entries × page size — is frequently
the hidden limit on large working sets.**
**⚠️ HUGE PAGES** (2 MB, 1 GB) ⚠️ **multiply TLB reach and are one of the highest-value and
least-used tunings for memory-intensive server workloads;** ⚠️ **the costs are internal
fragmentation and allocation difficulty.**
**⚠️ Cache indexing interaction**: ⚠️ **VIPT (virtually indexed, physically tagged) caches
let translation and lookup proceed in parallel, which constrains L1 size to page size ×
associativity — a genuine architectural reason L1 caches are small.**
**⚠️ ASIDs/PCIDs** avoid flushing the whole TLB on context switch, ⚠️ **which became much
more important after §19 → `uarch-dram-memory-controllers-power-and-security`'s mitigations increased switching costs.**

---

## §10. Prefetching

**⚠️ Fetch data before it's requested, to hide latency.**
⚠️ **Hardware prefetchers detect sequential streams and constant strides, and increasingly
more complex patterns; ⚠️ they cannot follow pointer chasing, which is why linked lists
and trees perform so badly relative to arrays.**
**⚠️ Software prefetch instructions** exist and ⚠️ **are difficult to use well — too early
and the line is evicted, too late and you gained nothing.**
**⚠️ The costs**: ⚠️ **useless prefetches consume bandwidth and can EVICT useful data, so an
aggressive prefetcher can make a bandwidth-bound workload slower.**
**⚠️ The design implication**: ⚠️ **data structures with predictable access patterns are
fast almost for free; ⚠️ this is a large part of why structure-of-arrays beats array-of-
structures in performance-critical code.**

---

# PART II — THROUGHPUT ARCHITECTURES
