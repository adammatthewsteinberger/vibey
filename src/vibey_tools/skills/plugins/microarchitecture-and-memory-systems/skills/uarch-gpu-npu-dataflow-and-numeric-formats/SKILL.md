---
name: uarch-gpu-npu-dataflow-and-numeric-formats
description: "Use for accelerators: GPU microarchitecture including warps, occupancy and divergence, GPU memory systems with coalescing and the bandwidth hierarchy, NPUs and dataflow architectures such as systolic arrays and why they suit tensor workloads, and numeric formats from FP32 down to FP8 and the block-scaled formats with their accuracy and throughput trade-offs."
---

# Microarchitecture and Memory: GPU Microarchitecture, GPU Memory Systems, NPUs and Dataflow Architectures, and Numeric Formats

> **Part 3 of 6** of the *CPU, GPU, NPU and Memory Microarchitecture* reference (plugin `microarchitecture-and-memory-systems`), covering §11–§14. Sibling skills: `uarch-pipelining-out-of-order-branch-prediction-and-simd` (§0–§5), `uarch-caches-coherence-consistency-and-virtual-memory` (§6–§10), `uarch-dram-memory-controllers-power-and-security` (§15–§19), `uarch-isa-simulation-measurement-roofline-and-specialization` (§20–§24), `uarch-reference` (§25–§30). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 2. **⚠️ MOVING DATA COSTS FAR MORE THAN COMPUTING ON IT** (§6 → `uarch-caches-coherence-consistency-and-virtual-memory`, §13, §23 → `uarch-isa-simulation-measurement-roofline-and-specialization`). **Energy per
>    arithmetic operation has fallen enormously; energy per byte moved has not. Modern
>    architecture is organized around minimizing data movement, and that single fact
>    explains caches, dataflow accelerators, quantization and HBM alike.**
> 3. **⚠️ PARALLELISM IS EXTRACTED AT EVERY LEVEL, AND EACH HAS A DIFFERENT LIMIT** (§3 → `uarch-pipelining-out-of-order-branch-prediction-and-simd`,
>    §11, §14). **ILP is limited by dependencies and branches, DLP by divergence and
>    memory, TLP by synchronization and coherence traffic. Knowing which one you're
>    hitting is the entire diagnostic skill.**

---

## §11. GPU Microarchitecture

```
⚠️ THE ORGANIZING PRINCIPLE  ⚠️ hide latency with PARALLELISM
   rather than with caches and speculation. ⚠️ When a warp stalls
   on memory, the scheduler switches to another — so latency is
   tolerated rather than reduced
⚠️ THE HIERARCHY  ⚠️ SM / CU containing warp schedulers, register
   file, SIMD lanes, ⚠️ SHARED MEMORY / LDS (⚠️ software-managed
   scratchpad — the key GPU-specific resource), L1, tensor units
⚠️ SIMT  ⚠️ threads grouped into warps (32) or wavefronts (32/64)
   executing in lockstep
   ⚠️ WARP DIVERGENCE — ⚠️ if threads in a warp take different
   branch paths, the hardware SERIALIZES them. ⚠️ Worst case a
   32-way divergent branch costs 32× — the single biggest GPU
   performance trap
⚠️ ⚠️ OCCUPANCY  active warps per SM, limited by ⚠️ REGISTERS PER
   THREAD, ⚠️ SHARED MEMORY PER BLOCK, and block size.
   ⚠️ GOTCHA: higher occupancy is NOT automatically better —
   beyond the point where latency is hidden, more warps just
   thrash cache. ⚠️ Register-heavy kernels with low occupancy
   frequently outperform "optimized" high-occupancy versions
⚠️ MEMORY COALESCING  ⚠️ consecutive threads accessing consecutive
   addresses combine into one transaction; ⚠️ scattered access
   multiplies the transaction count and is the second big trap
⚠️ BANK CONFLICTS in shared memory ⚠️ serialize access
⚠️ THE REGISTER FILE IS HUGE  ⚠️ larger than the L1 cache — because
   thousands of resident threads each need private state
```

---

## §12. GPU Memory Systems

**⚠️ GDDR versus HBM**: ⚠️ **GDDR is cheaper with fewer, faster pins; ⚠️ HBM uses stacked
dies and an extremely wide interface (§15 → `uarch-dram-memory-controllers-power-and-security`, and see a semiconductor reference §20) for
far higher bandwidth per watt at much higher cost.**
**⚠️ Bandwidth is the design centre**: ⚠️ **GPUs are usually bandwidth-bound (§23 → `uarch-isa-simulation-measurement-roofline-and-specialization`), so
arithmetic intensity determines whether you can use the compute at all.**
**⚠️ Caches on GPUs behave differently**: ⚠️ **smaller per thread, and used more for
coalescing and reuse across warps than for latency reduction.**
**⚠️ Unified/managed memory** simplifies programming and ⚠️ **can hide expensive migration
— convenience that costs performance silently.**
**⚠️ Multi-GPU**: ⚠️ **NVLink and Infinity Fabric provide far higher bandwidth than PCIe,
and collective operations make the interconnect part of the compute path** (see a
computer-hardware reference §21).

---

## §13. ⚠️ NPUs and Dataflow Architectures

> **⚠️ The least-covered area elsewhere, and the design logic is genuinely different from
> both CPU and GPU.**
```
⚠️ THE PREMISE  ⚠️ neural network inference and training are
   dominated by MATRIX MULTIPLY, which has enormous, REGULAR,
   STATICALLY KNOWN parallelism. ⚠️ You do not need speculation,
   branch prediction or coherence — so remove them and spend
   the area on arithmetic and local memory
⚠️ ⚠️ THE ENERGY ARGUMENT IS THE REAL ONE  ⚠️ a multiply-accumulate
   costs far less energy than fetching its operands from DRAM.
   ⚠️ Therefore the architecture is designed around DATA REUSE,
   not around arithmetic throughput
⚠️ SYSTOLIC ARRAYS  ⚠️ a grid of MAC units where data flows
   rhythmically between neighbours — ⚠️ each value fetched once
   and reused across the array. Google's TPU is the canonical
   modern example
⚠️ DATAFLOW TAXONOMY  ⚠️ weight-stationary (keep weights in place,
   stream activations) · output-stationary (accumulate in place) ·
   row-stationary. ⚠️ The choice depends on layer shape, and
   flexible accelerators support several
⚠️ THE MEMORY HIERARCHY IS EXPLICIT AND SOFTWARE-MANAGED —
   ⚠️ no transparent caches. ⚠️ TILING and scheduling are the
   compiler's job, and the compiler is most of the product
⚠️ SPARSITY  ⚠️ structured (e.g. 2:4) is hardware-exploitable;
   unstructured sparsity is much harder to convert into speedup
⚠️ COMPUTE-IN-MEMORY  research direction — do the MAC where the
   data lives, attacking the movement cost directly
⚠️ EDGE NPUs  ⚠️ optimized for INT8 and now INT4/FP4 (§25.1),
   with fixed function blocks and very tight power budgets
```

---

## §14. ⚠️ Numeric Formats

**⚠️ Precision is an architectural parameter now, not a given.**
```
⚠️ IEEE 754  FP64, FP32, ⚠️ FP16 (5 exponent bits — limited RANGE,
   which causes training overflow)
⚠️ BF16  ⚠️ FP32's 8 exponent bits with fewer mantissa bits —
   ⚠️ same RANGE as FP32, less precision. ⚠️ This is why BF16
   largely displaced FP16 for training: range mattered more
   than mantissa
⚠️ FP8  E4M3 (more precision) and E5M2 (more range) — typically
   used together for forward and backward passes
⚠️ INTEGER  INT8, INT4 — with quantization scale and zero-point
⚠️ ⚠️ BLOCK FLOATING POINT / MICROSCALING  ⚠️ the key modern idea:
   a group of low-precision values SHARES a higher-precision
   scale factor, recovering dynamic range at almost no bit cost
   (§25.1)
⚠️ THE TRADE  ⚠️ halving bit width roughly halves memory, memory
   BANDWIDTH and energy, and can more than double throughput —
   ⚠️ which is why quantization is the highest-leverage
   optimization available for inference
⚠️ WHAT BREAKS  ⚠️ ACTIVATION OUTLIERS — a few very large values
   force a scale that crushes everything else. ⚠️ Hence
   per-channel and per-block scaling, and Hadamard rotations
   that spread outlier energy across dimensions
⚠️ ⚠️ NOT EVERYTHING QUANTIZES  softmax, layer norm and
   accumulation are typically kept at higher precision
```

---

# PART III — MEMORY SYSTEMS
