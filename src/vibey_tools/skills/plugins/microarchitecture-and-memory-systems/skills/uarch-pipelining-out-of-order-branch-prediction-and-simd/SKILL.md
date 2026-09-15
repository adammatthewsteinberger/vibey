---
name: uarch-pipelining-out-of-order-branch-prediction-and-simd
description: "Use for the core execution engine: the distinction between architecture and microarchitecture and why it governs what is portable, pipelining and hazards, out-of-order execution with register renaming, the reorder buffer and speculation, branch prediction and the cost of a misprediction, and execution units and SIMD. Includes the router for the whole microarchitecture reference."
---

# Microarchitecture and Memory: Architecture Versus Microarchitecture, Pipelining, Out-of-Order Execution, Branch Prediction, and Execution Units and SIMD

> **Part 1 of 6** of the *CPU, GPU, NPU and Memory Microarchitecture* reference (plugin `microarchitecture-and-memory-systems`), covering §0–§5. Sibling skills: `uarch-caches-coherence-consistency-and-virtual-memory` (§6–§10), `uarch-gpu-npu-dataflow-and-numeric-formats` (§11–§14), `uarch-dram-memory-controllers-power-and-security` (§15–§19), `uarch-isa-simulation-measurement-roofline-and-specialization` (§20–§24), `uarch-reference` (§25–§30). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 1. **⚠️ THE PROCESSOR LIES TO YOU, DELIBERATELY** (§2–§4). **Instructions do not execute
>    in program order, memory operations do not become visible in program order, and the
>    architecture works hard to maintain the illusion that they do. Every performance
>    surprise and several security disasters live in the gap.**
> 2. **⚠️ MOVING DATA COSTS FAR MORE THAN COMPUTING ON IT** (§6 → `uarch-caches-coherence-consistency-and-virtual-memory`, §13 → `uarch-gpu-npu-dataflow-and-numeric-formats`, §23 → `uarch-isa-simulation-measurement-roofline-and-specialization`). **Energy per
>    arithmetic operation has fallen enormously; energy per byte moved has not. Modern
>    architecture is organized around minimizing data movement, and that single fact
>    explains caches, dataflow accelerators, quantization and HBM alike.**
> 3. **⚠️ PARALLELISM IS EXTRACTED AT EVERY LEVEL, AND EACH HAS A DIFFERENT LIMIT** (§3,
>    §11 → `uarch-gpu-npu-dataflow-and-numeric-formats`, §14 → `uarch-gpu-npu-dataflow-and-numeric-formats`). **ILP is limited by dependencies and branches, DLP by divergence and
>    memory, TLP by synchronization and coherence traffic. Knowing which one you're
>    hitting is the entire diagnostic skill.**

---

## §0. Routing

| You want... | Go to |
|---|---|
| Architecture vs microarchitecture | §1 |
| Pipelining | §2 |
| **⚠️ Out-of-order internals** | **§3** |
| **⚠️ Branch prediction** | **§4** |
| Execution units and SIMD | §5 |
| **Cache organization** | **§6 → `uarch-caches-coherence-consistency-and-virtual-memory`** |
| **⚠️ Coherence** | **§7 → `uarch-caches-coherence-consistency-and-virtual-memory`** |
| **⚠️ Consistency models** | **§8 → `uarch-caches-coherence-consistency-and-virtual-memory`** |
| Virtual memory and TLBs | §9 → `uarch-caches-coherence-consistency-and-virtual-memory` |
| Prefetching | §10 → `uarch-caches-coherence-consistency-and-virtual-memory` |
| **GPU microarchitecture** | **§11 → `uarch-gpu-npu-dataflow-and-numeric-formats`** |
| GPU memory | §12 → `uarch-gpu-npu-dataflow-and-numeric-formats` |
| **⚠️ NPU and dataflow** | **§13 → `uarch-gpu-npu-dataflow-and-numeric-formats`** |
| **⚠️ Numeric formats** | **§14 → `uarch-gpu-npu-dataflow-and-numeric-formats`** |
| **⚠️ DRAM internals** | **§15 → `uarch-dram-memory-controllers-power-and-security`** |
| Memory controllers | §16 → `uarch-dram-memory-controllers-power-and-security` |
| Emerging memory interfaces | §17 → `uarch-dram-memory-controllers-power-and-security` |
| Power and DVFS | §18 → `uarch-dram-memory-controllers-power-and-security` |
| **⚠️ Microarchitectural security** | **§19 → `uarch-dram-memory-controllers-power-and-security`** |
| ISA design | §20 → `uarch-isa-simulation-measurement-roofline-and-specialization` |
| Simulation and modelling | §21 → `uarch-isa-simulation-measurement-roofline-and-specialization` |
| **⚠️ Performance measurement** | **§22 → `uarch-isa-simulation-measurement-roofline-and-specialization`** |
| Roofline and bounds | §23 → `uarch-isa-simulation-measurement-roofline-and-specialization` |
| Specialization | §24 → `uarch-isa-simulation-measurement-roofline-and-specialization` |
| **What's live** | **§25 → `uarch-reference`** |
| Misconceptions, numbers | §26–§27 → `uarch-reference` |
| Books, quick ref, method | §28–§30 → `uarch-reference` |

---

## §1. Architecture versus Microarchitecture

```
⚠️ ARCHITECTURE (ISA)  ⚠️ the CONTRACT — instructions, registers,
   memory model, exceptions. ⚠️ What software may rely on
⚠️ MICROARCHITECTURE  ⚠️ the IMPLEMENTATION — pipelines, caches,
   predictors, buffers. ⚠️ Invisible to correctness, decisive for
   performance
⚠️ THE SAME ISA can be implemented by wildly different
   microarchitectures — an in-order embedded core and a
   twelve-wide out-of-order server core run identical binaries
⚠️ ⚠️ THE LEAK: the contract covers CORRECTNESS, not TIMING.
   ⚠️ Microarchitectural state is observable through timing, and
   that is the entire basis of §19's attack class — a distinction
   the industry assumed was safe for forty years and wasn't
```
**⚠️ The design axes**: ⚠️ **frequency versus IPC versus power; ⚠️ latency-optimized
(CPU) versus throughput-optimized (GPU); general versus specialized** (§24 → `uarch-isa-simulation-measurement-roofline-and-specialization`).

---

# PART I — CPU MICROARCHITECTURE

## §2. Pipelining

**⚠️ Overlap instruction execution by splitting it into stages** — ⚠️ **throughput rises to
one instruction per cycle in the ideal case while LATENCY per instruction rises slightly.**
```
⚠️ THE HAZARDS
   ⚠️ STRUCTURAL  two instructions want the same resource
   ⚠️ DATA  ⚠️ RAW (true dependency — the real one) · WAR and WAW
      (⚠️ FALSE dependencies caused by reusing register NAMES —
      and register renaming eliminates them entirely, §3)
   ⚠️ CONTROL  branches (§4)
⚠️ FORWARDING/BYPASSING  route a result directly from one stage to
   another rather than waiting for writeback
⚠️ DEEPER PIPELINES  higher clock, ⚠️ and a far larger mispredict
   penalty. ⚠️ The Pentium 4 is the canonical lesson in taking
   this too far
⚠️ MODERN DEPTHS  roughly 14–20 stages, with the mispredict
   penalty in the same order of magnitude
```

---

## §3. ⚠️ Out-of-Order Execution

> **⚠️ The heart of modern high-performance CPUs, and the mechanism whose details matter
> most for both performance and §19 → `uarch-dram-memory-controllers-power-and-security`'s security.**
```
⚠️ THE PRINCIPLE  ⚠️ execute instructions when their OPERANDS are
   ready rather than in program order — then RETIRE them in
   program order so the architectural state stays correct
⚠️ THE STRUCTURES
   ⚠️ REGISTER RENAMING  ⚠️ map architectural registers to a much
      larger physical register file. ⚠️ ELIMINATES WAR and WAW
      hazards entirely, which is why "there are only 16 registers"
      is not the constraint people assume
   ⚠️ REORDER BUFFER (ROB)  ⚠️ holds instructions in program order
      until retirement. ⚠️ ROB SIZE bounds how far ahead the core
      can look — the "instruction window"
   ⚠️ RESERVATION STATIONS / scheduler  hold instructions waiting
      for operands, wake them when ready
   ⚠️ LOAD-STORE QUEUE  ⚠️ tracks memory ordering, does STORE-TO-LOAD
      FORWARDING, and handles memory DISAMBIGUATION — deciding
      whether a load may pass an earlier store whose address isn't
      known yet. ⚠️ Speculating wrongly here costs a replay
⚠️ ⚠️ WHY IT MATTERS: the core needs a deep window to hide a
   ~200-cycle memory latency. ⚠️ But it must also be able to
   UNDO everything speculative — and the fact that it undoes
   architectural state while leaving MICROARCHITECTURAL traces
   is precisely §19
⚠️ THE LIMITS  ⚠️ ILP in real code is finite; window size, rename
   width and scheduler complexity all scale badly in power and
   area, which is why cores stopped getting dramatically wider
```

---

## §4. ⚠️ Branch Prediction

**⚠️ A pipeline must guess where control flow goes, many cycles before it knows.**
```
⚠️ THE STAKES  ⚠️ roughly one in five instructions is a branch, and
   a mispredict costs the full pipeline depth. ⚠️ At 95% accuracy
   a wide deep core loses a large fraction of its throughput —
   which is why modern predictors target 99%+
⚠️ THE PROGRESSION  static → 2-bit saturating counters → ⚠️ TWO-LEVEL
   (global and local history) → tournament/hybrid →
   ⚠️ TAGE (geometric history lengths, the current state of the
   art class) → ⚠️ PERCEPTRON predictors, which are genuinely
   neural and shipping in real silicon
⚠️ ALSO PREDICTED  ⚠️ branch TARGET (BTB), ⚠️ RETURN addresses (a
   dedicated return stack buffer, because returns are highly
   predictable but not by history), and indirect branch targets
   (⚠️ the hardest case — virtual calls and jump tables)
⚠️ THE ALIASING PROBLEM  ⚠️ predictor tables are indexed by hashed
   PC and history, so unrelated branches COLLIDE. ⚠️ This is both
   a performance issue and an attack surface (§19)
```
> **⚠️ GOTCHA — branchless code is not automatically faster.** ⚠️ **A well-predicted branch
> is nearly free, while a conditional move creates a genuine data dependency that always
> costs.** **⚠️ Branchless wins on UNPREDICTABLE branches and loses on predictable ones —
> and which you have is an empirical question, not a stylistic one.**

---

## §5. Execution Units and SIMD

**⚠️ Superscalar width** — ⚠️ **the number of instructions issued per cycle, and the
practical limit is not the units but the RENAME and SCHEDULER width plus available ILP.**
**⚠️ Functional unit mix and latencies** — ⚠️ **integer ALU 1 cycle, multiply 3–5, FP add
and multiply 3–5, divide and square root far longer and often not pipelined.**
**⚠️ FMA (fused multiply-add)** — ⚠️ **one rounding instead of two, so it is both faster AND
more accurate; ⚠️ note it can change results versus separate operations, which matters for
reproducibility.**
**⚠️ SIMD** (AVX-512, NEON, SVE, RVV): ⚠️ **wide registers operating element-wise.**
⚠️ **The practical obstacles are ALIGNMENT, the need for contiguous data, tail handling,
and — for the widest units — DOWNCLOCKING under heavy vector load on some
implementations, which can make a vectorized kernel slow down neighbouring code.**
**⚠️ Predication and masking** let SIMD handle conditionals without branching, ⚠️ **and
scalable vector ISAs (SVE, RVV) express length-agnostic code so binaries survive width
changes.**
