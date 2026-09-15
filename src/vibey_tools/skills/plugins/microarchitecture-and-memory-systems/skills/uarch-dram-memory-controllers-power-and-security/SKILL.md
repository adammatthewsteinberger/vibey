---
name: uarch-dram-memory-controllers-power-and-security
description: "Use for the memory system and its side effects: DRAM internals with banks, rows, timings and refresh, memory controllers and scheduling, the emerging memory interfaces including CXL and high-bandwidth stacks, power and clocking with DVFS and thermal limits, and microarchitectural security — speculative execution attacks, side channels and Rowhammer-class problems."
---

# Microarchitecture and Memory: DRAM Internals, Memory Controllers, Emerging Memory Interfaces, Power and Clocking, and Microarchitectural Security

> **Part 4 of 6** of the *CPU, GPU, NPU and Memory Microarchitecture* reference (plugin `microarchitecture-and-memory-systems`), covering §15–§19. Sibling skills: `uarch-pipelining-out-of-order-branch-prediction-and-simd` (§0–§5), `uarch-caches-coherence-consistency-and-virtual-memory` (§6–§10), `uarch-gpu-npu-dataflow-and-numeric-formats` (§11–§14), `uarch-isa-simulation-measurement-roofline-and-specialization` (§20–§24), `uarch-reference` (§25–§30). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 2. **⚠️ MOVING DATA COSTS FAR MORE THAN COMPUTING ON IT** (§6 → `uarch-caches-coherence-consistency-and-virtual-memory`, §13 → `uarch-gpu-npu-dataflow-and-numeric-formats`, §23 → `uarch-isa-simulation-measurement-roofline-and-specialization`). **Energy per
>    arithmetic operation has fallen enormously; energy per byte moved has not. Modern
>    architecture is organized around minimizing data movement, and that single fact
>    explains caches, dataflow accelerators, quantization and HBM alike.**
> 3. **⚠️ PARALLELISM IS EXTRACTED AT EVERY LEVEL, AND EACH HAS A DIFFERENT LIMIT** (§3 → `uarch-pipelining-out-of-order-branch-prediction-and-simd`,
>    §11 → `uarch-gpu-npu-dataflow-and-numeric-formats`, §14 → `uarch-gpu-npu-dataflow-and-numeric-formats`). **ILP is limited by dependencies and branches, DLP by divergence and
>    memory, TLP by synchronization and coherence traffic. Knowing which one you're
>    hitting is the entire diagnostic skill.**

---

## §15. ⚠️ DRAM Internals

> **⚠️ The component whose behaviour is least understood by the people tuning it.**
```
⚠️ THE STRUCTURE  ⚠️ cell (one transistor + one capacitor) →
   row (page) → bank → bank group → rank → channel → DIMM
⚠️ ⚠️ ACCESS IS A THREE-STEP SEQUENCE, and this explains all the
   timing numbers
   ⚠️ 1. ACTIVATE  ⚠️ copy an entire ROW into the row buffer —
      ⚠️ this is DESTRUCTIVE (reading the capacitors drains them)
   ⚠️ 2. READ/WRITE from the row buffer — ⚠️ fast if the row is
      already open (ROW HIT), slow if not
   ⚠️ 3. PRECHARGE  ⚠️ write the row back and prepare for the next
⚠️ THE TIMINGS people quote  ⚠️ CL (CAS latency) · tRCD (activate
   to read) · tRP (precharge) · tRAS (minimum row active)
   ⚠️ THE HEADLINE "CL16" IS ONLY THE ROW-HIT CASE. ⚠️ A row miss
   costs tRP + tRCD + CL — roughly triple
⚠️ ⚠️ ACTUAL LATENCY IN NANOSECONDS = CL ÷ (data rate ÷ 2) × 1000.
   ⚠️ Higher-MT/s memory usually has higher CL, so real latency
   has barely improved across DDR generations — ⚠️ BANDWIDTH is
   what improved
⚠️ REFRESH  ⚠️ capacitors leak, so every row must be refreshed
   periodically (⚠️ typically every 64 ms). ⚠️ Refresh consumes
   bandwidth and blocks access, and the cost RISES with density
⚠️ BANK PARALLELISM  ⚠️ multiple banks let one activate overlap
   another's transfer — the memory controller's main lever (§16)
⚠️ ⚠️ ROWHAMMER  ⚠️ repeatedly activating a row disturbs charge in
   PHYSICALLY ADJACENT rows and can flip their bits — ⚠️ a
   reliability property that became a security vulnerability,
   and mitigations (TRR, on-die ECC) have repeatedly been bypassed
```

---

## §16. Memory Controllers

**⚠️ The controller is a scheduler**, ⚠️ **and its policies matter as much as the DRAM
timings.**
⚠️ **SCHEDULING: FR-FCFS (first-ready, first-come-first-served) prioritizes ROW HITS over
program order, which raises throughput and can starve latency-sensitive threads.**
**⚠️ Address mapping** determines how physical addresses distribute across channels, ranks,
banks and rows — ⚠️ **and a bad mapping for a given access pattern destroys bank
parallelism.**
**⚠️ Open-page versus closed-page policy** trades row-hit rate against precharge latency
for random access.
**⚠️ Refresh management, power-down states, and write-to-read turnaround** — ⚠️ **bus
turnaround is a real cost, so controllers batch reads and writes.**
**⚠️ ECC**: ⚠️ **SECDED at the module level; ⚠️ ON-DIE ECC in DDR5 exists to make the DRAM
manufacturable at density and does NOT replace system ECC — a distinction vendors blur.**

---

## §17. Emerging Memory Interfaces

**⚠️ HBM** (see a semiconductor reference §20): ⚠️ **stacked dies, TSVs, a very wide slow
interface — bandwidth through WIDTH rather than frequency, which is far more energy
efficient per bit.**
**⚠️ CXL** — ⚠️ **cache-coherent attach over PCIe, enabling memory EXPANSION, POOLING
across hosts, and tiering.** ⚠️ **The catch is latency: CXL memory is meaningfully slower
than direct-attached, so it is a tier, not a replacement.**
**⚠️ Processing-in-memory** — ⚠️ **real research and some commercial products, attacking
§13 → `uarch-gpu-npu-dataflow-and-numeric-formats`'s data movement cost directly.**
**⚠️ Persistent memory** — ⚠️ **Optane's discontinuation is a cautionary tale about a
technically interesting tier that couldn't find a durable economic niche between DRAM and
NAND.**
**⚠️ See §25.2 → `uarch-reference` for where standard DRAM interfaces are going.**

---

# PART IV — CROSS-CUTTING

## §18. Power and Clocking

**⚠️ Dynamic power ∝ C·V²·f, and the V² term is why voltage scaling was so powerful and its
end so consequential** (see a semiconductor reference §5).
**⚠️ Static/leakage power** now matters at idle and scales badly.
**⚠️ DVFS** — ⚠️ **and because power scales with V² while frequency scales roughly with V,
running slower saves power SUPERLINEARLY.**
**⚠️ Race-to-idle versus run-slow** is genuinely workload-dependent: ⚠️ **when static power
and fixed overheads dominate, finishing fast and sleeping deeply wins; when dynamic power
dominates, running slow wins.**
**⚠️ Clock and power gating; multiple voltage and clock domains; and thermal/current
throttling as the real limiter** (see a computer-hardware reference §8).
**⚠️ Energy per operation is the metric that matters** for accelerators (§13 → `uarch-gpu-npu-dataflow-and-numeric-formats`), ⚠️ **not
peak throughput.**

---

## §19. ⚠️ Microarchitectural Security

> **⚠️ The class of vulnerability created by §1 → `uarch-pipelining-out-of-order-branch-prediction-and-simd`'s leak: architectural state is restored on
> misspeculation, microarchitectural state is not.**
```
⚠️ THE MECHANISM  ⚠️ 1. Get the processor to speculatively perform
   an action it shouldn't. ⚠️ 2. That action leaves a trace in
   microarchitectural state — usually a cache line. ⚠️ 3. Recover
   the trace by timing (FLUSH+RELOAD, PRIME+PROBE)
⚠️ THE FAMILIES
   ⚠️ SPECTRE  ⚠️ mistrain the branch predictor (§4) so the victim
      speculatively accesses data it shouldn't. ⚠️ Crosses
      software boundaries; ⚠️ genuinely hard to fix in hardware
      because it exploits speculation itself
   ⚠️ MELTDOWN  ⚠️ speculative access across a PRIVILEGE boundary
      before the permission check retires. ⚠️ Fixable in hardware,
      and largely fixed
   ⚠️ MDS / microarchitectural data sampling  leakage from internal
      buffers
   ⚠️ Later variants have continued to appear, which is the point
⚠️ MITIGATIONS AND THEIR COST  ⚠️ KPTI page table isolation ·
   retpolines · IBRS/IBPB · flushing buffers on switch ·
   ⚠️ DISABLING SMT in the highest-security configurations
   ⚠️ THE COSTS ARE REAL — ⚠️ which means pre-2018 benchmark
   comparisons are not valid against patched systems
⚠️ ROWHAMMER (§15) is the memory-side analogue
⚠️ CONSTANT-TIME PROGRAMMING (see a cryptography reference §17)
   ⚠️ is the software-side response: no secret-dependent branches
   or memory addresses. ⚠️ And compilers can undo it, which is
   why crypto libraries fight their own toolchains
```
