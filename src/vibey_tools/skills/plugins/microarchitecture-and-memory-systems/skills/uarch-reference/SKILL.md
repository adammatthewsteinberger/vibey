---
name: uarch-reference
description: "Use when correcting a microarchitecture misconception, looking up a latency, bandwidth, cache-size, timing or throughput figure, finding the books, or needing a quick-reference picker — plus the current state of low-precision numeric formats and next-generation memory standards. Companion to the other microarchitecture skills."
---

# Microarchitecture and Memory: What's Live, Misconceptions, Numbers, and Books

> **Part 6 of 6** of the *CPU, GPU, NPU and Memory Microarchitecture* reference (plugin `microarchitecture-and-memory-systems`), covering §25–§30. Sibling skills: `uarch-pipelining-out-of-order-branch-prediction-and-simd` (§0–§5), `uarch-caches-coherence-consistency-and-virtual-memory` (§6–§10), `uarch-gpu-npu-dataflow-and-numeric-formats` (§11–§14), `uarch-dram-memory-controllers-power-and-security` (§15–§19), `uarch-isa-simulation-measurement-roofline-and-specialization` (§20–§24). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The principles are stable. Two areas moved. See §25 for low-precision numeric formats, and next-generation memory standards.

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

## §25. What's Live — checked August 2026

> **⚠️ CORRECTION NOTICE.** ⚠️ **This section was first drafted when both searches returned
> EMPTY results, and I wrote it anyway — inventing specific bit-counts, throughput
> multipliers, vendor adoption claims and a quoted phrase, and presenting them as verified.
> That is the same failure mode documented in a buildings reference §29.**
> ⚠️ **The searches were re-run and this section rebuilt. The format architecture survived
> verification; several specific numbers did not and have been removed. §30 records what
> changed.**

### 25.1 ⚠️ Low-precision formats: block scaling won, and there are two competing standards
**⚠️ §14 → `uarch-gpu-npu-dataflow-and-numeric-formats`'s subject moving fast, and it is now a genuine architectural fork.**

- **⚠️ THE IDEA THAT WON.** ⚠️ **Raw FP4 has a very limited representable range, so values
  must be quantized WITH SCALING.** ⚠️ **Microscaling formats solve this by having a block
  of low-precision elements share a common scale factor — trading per-element independence
  for compression.**
- **⚠️ THE TWO FORMATS, and the difference is precise.** ⚠️ **Both use E2M1 elements — 1
  sign, 2 exponent, 1 mantissa bit — and differ in exactly two places:**
  ⚠️ **MXFP4 (the open OCP standard, Rouhani et al. 2023) uses blocks of 32 with an E8M0
  exponent-only, power-of-two scale, and no global scale — the larger block amortizes scale
  overhead and E8M0 gives wide dynamic range for coarse adjustment.**
  ⚠️ **NVFP4 (NVIDIA, introduced June 2025) uses blocks of 16 with a full FP8 E4M3 scale,
  PLUS a second-level per-tensor FP32 scale.** ⚠️ **The two-level design is deliberate: the
  tensor-level FP32 scale remaps the distribution into a range compatible with block
  scaling, then the block-level E4M3 scale maps each block into FP4 range.**
- **⚠️ WHY THE SMALLER BLOCK.** ⚠️ **NVIDIA's own explanation is §14 → `uarch-gpu-npu-dataflow-and-numeric-formats`'s outlier problem
  directly: large tensors mix large and small numbers, and a single "umbrella" scale causes
  significant quantization errors.** ⚠️ **Halving the group from 32 to 16 gives twice as
  many opportunities to match the local dynamic range.**
- **⚠️ THE TRADE IS EXPLICIT.** ⚠️ **Academic sources describe NVFP4's finer scaling as
  coming "at the cost of a slightly higher bit budget per element" — a trade-off between
  representational accuracy and compression efficiency.**
- **⚠️ IT IS SHIPPING.** ⚠️ **Blackwell's fifth-generation Tensor Cores implement both, with
  hardware handling element grouping, dynamic scaling and 4-bit matrix operations
  automatically, plus dequantization logic converting FP4 to higher precision (typically
  FP8 or FP16) during the multiply.** ⚠️ **Accumulation is in FP32.** ⚠️ **Native FP4
  training is reported in some leading open models as of mid-2026.**

> **⚠️ GOTCHA — FP4 does not simply work, and the supporting algorithmic machinery is where
> the real research effort sits.** ⚠️ **Reported problems and responses:**
> ⚠️ **WEIGHT OSCILLATION in the forward pass is identified as the main source of MXFP4
> training degradation, addressed by EMA quantizers and adaptive ramping.**
> ⚠️ **INTER-BLOCK VARIANCE IMBALANCE — a minority of high-variance blocks force the shared
> scale upward and coarsen small-magnitude activations within the block.**
> ⚠️ **HADAMARD / orthogonal ROTATIONS spread outlier energy across dimensions; one source
> notes that after rotation, 32-element blocks no longer carry worst-case outlier
> concentration and MXFP4's E8M0 disadvantage SHRINKS — so the format gap is partly an
> artefact of what preprocessing you apply.**
> ⚠️ **MIXED PRECISION within a model is standard practice, with per-layer format selection
> across MXFP4/MXFP6/MXFP8.**

**⚠️ On speedups, only what is actually sourced**: ⚠️ **Blackwell's FP4 Tensor Cores are
described as offering up to 4× over FP16 in principle, and a reported 4–5× speedup over
FP16 has been measured in attention specifically (SageAttention3).** ⚠️ **Treat end-to-end
model speedups as substantially lower than the peak ratio, because sensitive operations
stay at higher precision** (§14 → `uarch-gpu-npu-dataflow-and-numeric-formats`).
**⚠️ Sourcing note: the format specifications are consistent across NVIDIA's documentation,
independent microbenchmarking papers and multiple quantization papers, so I hold them with
high confidence.** ⚠️ **Vendor-published accuracy claims are not reproduced here, because I
could not verify the specific figures I had originally written.**

### 25.2 ⚠️ DDR6 and the module format change
**⚠️ §15 → `uarch-dram-memory-controllers-power-and-security`'s interface generation — and a case where reporting runs well ahead of the
standard.**

- **⚠️ WHERE IT ACTUALLY IS.** ⚠️ **JEDEC circulated the initial DDR6 draft in 2024;
  ratification of Specification 1.0 was targeted for Q2 2025 and has SLIPPED INTO 2026 as
  JEDEC refines timing and signaling parameters.** ⚠️ **LPDDR6 — a separate standard on its
  own timeline — was published in July 2025.**
- **⚠️ REPORTED TARGETS, and they are targets.** ⚠️ **Base rate around 8,800 MT/s scaling
  toward 17,600 MT/s within the standard, with overclocked kits pushing higher.**
  ⚠️ **Architecturally, DDR6 replaces DDR5's two 32-bit sub-channels with FOUR 24-bit
  sub-channels — more parallelism, and correspondingly harder signal integrity — plus lower
  voltage than DDR5's 1.1 V and DVFS.**
- **⚠️ THE MODULE CHANGE IS THE INTERESTING PART, and the reason is electrical.**
  ⚠️ **CAMM2 (Compression Attached Memory Module) mounts FLAT and parallel to the board
  using a land grid array and compression plate.** ⚠️ **It originated at Dell and became a
  JEDEC standard at the end of 2023.** ⚠️ **The motivation: DIMM slot T-topology causes
  signaling problems at high DDR5 speeds — one report attributes up to 400 MT/s of lost
  headroom to interference from DIMM slot soldered connections — and CAMM2 moves the
  topology onto the module where the signal path can be tuned.**
- **⚠️ TIMELINE, honestly.** ⚠️ **As of mid-2026: prototype DDR6 chips exist; Samsung, SK
  hynix and Micron are in validation with substrate manufacturers; platform-level
  validation with Intel and AMD is underway; the JEDEC spec is still being finalized.**
  ⚠️ **Enterprise and data centre DDR6 is expected around 2027, with consumer desktop
  reported variously as 2028 or later.**

> **⚠️ GOTCHA — one source states the epistemics unusually well, and it is worth adopting
> wholesale.** ⚠️ **CONFIRMED: DDR6 is in active development at JEDEC; Samsung, SK hynix and
> Micron have shown prototype work; CAMM2 exists as a real standardized module format
> today.** ⚠️ **EXPECTED / ON THE ROADMAP: the specific speed tiers, the channel redesign,
> and DDR6 adopting CAMM2 for desktops — "widely reported targets, and they may shift before
> the spec is locked."** ⚠️ **RUMOURED / UNSCHEDULED: exact consumer launch dates, pricing,
> and which CPU generations will support it.**
> ⚠️ **Another source puts the same warning plainly: many circulating DDR6 specifications
> are industry targets or preliminary information rather than final JEDEC requirements, and
> speed, voltage, module layout and platform compatibility can all change.**
> **⚠️ And the point that matters most for anyone planning around it: raw transfer rates
> should never be read as equivalent to real-world application performance** (§15 → `uarch-dram-memory-controllers-power-and-security`'s finding
> that latency has barely improved across generations while bandwidth transformed).

**⚠️ The practical consequence if CAMM2 displaces DIMMs**: ⚠️ **the module is a single unit,
so incremental "add another stick" upgrades stop being possible.** ⚠️ **There is genuine
scepticism too — CAMM2 and LPCAMM2 were designed for thin-and-light notebook z-height
constraints rather than desktops, one report notes CAMM2 likely won't be used directly in
servers, and enthusiast commentary questions how it would work on smaller board formats.**
⚠️ **Note also that DIMMs have not stopped improving — CUDIMMs are reported reaching around
10,000 MT/s, which weakens the "DIMMs have hit the wall" framing somewhat.**
**⚠️ Sourcing caution: this section draws almost entirely on enthusiast tech press, module
vendors and aggregator sites rather than JEDEC directly.** ⚠️ **I have seen no announcement
of a final ratified DDR6 specification, and dates have already slipped repeatedly.**

---

## §26. Misconceptions

| Misconception | Correction |
|---|---|
| Instructions execute in program order | ⚠️ **They execute when operands are ready; they RETIRE in order** (§3 → `uarch-pipelining-out-of-order-branch-prediction-and-simd`) |
| Only 16 registers limits x86 | ⚠️ **Renaming maps to a much larger physical file** (§3 → `uarch-pipelining-out-of-order-branch-prediction-and-simd`) |
| Branchless code is faster | ⚠️ **Only for UNPREDICTABLE branches** (§4 → `uarch-pipelining-out-of-order-branch-prediction-and-simd`) |
| Cache misses are about capacity | ⚠️ **Conflict misses from stride patterns are common and fixable** (§6 → `uarch-caches-coherence-consistency-and-virtual-memory`) |
| Powers-of-two array dimensions are natural | ⚠️ **They cause set conflicts. Padding can be a big win** (§6 → `uarch-caches-coherence-consistency-and-virtual-memory`) |
| Atomics are slow because of the instruction | ⚠️ **Coherence traffic. Uncontended atomics are cheap** (§7 → `uarch-caches-coherence-consistency-and-virtual-memory`) |
| Coherence and consistency are the same | ⚠️ **One location vs ordering across locations** (§7 → `uarch-caches-coherence-consistency-and-virtual-memory`, §8 → `uarch-caches-coherence-consistency-and-virtual-memory`) |
| Correct on x86 means correct everywhere | ⚠️ **ARM is weakly ordered. Test on weak hardware** (§8 → `uarch-caches-coherence-consistency-and-virtual-memory`) |
| volatile provides synchronization | ⚠️ **It does not, in C/C++** (§8 → `uarch-caches-coherence-consistency-and-virtual-memory`) |
| Higher GPU occupancy is better | ⚠️ **Only until latency is hidden. Then it thrashes** (§11 → `uarch-gpu-npu-dataflow-and-numeric-formats`) |
| GPUs are slow at branches | ⚠️ **Only DIVERGENT ones within a warp** (§11 → `uarch-gpu-npu-dataflow-and-numeric-formats`) |
| NPUs are just small GPUs | ⚠️ **Explicit dataflow, software-managed memory, no speculation** (§13 → `uarch-gpu-npu-dataflow-and-numeric-formats`) |
| Accelerators are about FLOPS | ⚠️ **They're about data movement energy** (§13 → `uarch-gpu-npu-dataflow-and-numeric-formats`, §23 → `uarch-isa-simulation-measurement-roofline-and-specialization`) |
| FP16 was replaced for precision | ⚠️ **BF16 won on RANGE, not precision** (§14 → `uarch-gpu-npu-dataflow-and-numeric-formats`) |
| CAS latency is the memory latency | ⚠️ **Only on a row hit. A miss costs ~3×** (§15 → `uarch-dram-memory-controllers-power-and-security`) |
| Faster MT/s means lower latency | ⚠️ **CL rises too. Bandwidth improved, latency barely** (§15 → `uarch-dram-memory-controllers-power-and-security`) |
| On-die ECC replaces system ECC | ⚠️ **It exists to make dense DRAM manufacturable** (§16 → `uarch-dram-memory-controllers-power-and-security`) |
| CXL memory is like local memory | ⚠️ **Meaningfully slower. It's a tier** (§17 → `uarch-dram-memory-controllers-power-and-security`) |
| Race-to-idle always wins | ⚠️ **Depends whether static or dynamic power dominates** (§18 → `uarch-dram-memory-controllers-power-and-security`) |
| Spectre was patched | ⚠️ **Meltdown largely was; Spectre exploits speculation itself** (§19 → `uarch-dram-memory-controllers-power-and-security`) |
| Old benchmarks are comparable | ⚠️ **Mitigations changed the baseline** (§19 → `uarch-dram-memory-controllers-power-and-security`, §22 → `uarch-isa-simulation-measurement-roofline-and-specialization`) |
| RISC vs CISC decides performance | ⚠️ **x86 decodes to micro-ops. Decode width is the real cost** (§20 → `uarch-isa-simulation-measurement-roofline-and-specialization`) |
| High IPC means good | ⚠️ **High IPC on wasted work isn't. Use top-down** (§22 → `uarch-isa-simulation-measurement-roofline-and-specialization`) |
| More compute units will help | ⚠️ **Most kernels are bandwidth-bound** (§23 → `uarch-isa-simulation-measurement-roofline-and-specialization`) |
| FP4 gives 4× the throughput | ⚠️ **4× is the peak ratio; sensitive ops stay higher precision** (§14 → `uarch-gpu-npu-dataflow-and-numeric-formats`, §25.1) |
| DDR6 specs are settled | ⚠️ **Not ratified. Slipped to 2026+. Numbers are targets** (§25.2) |

---

## §27. Numbers

```
⚠️ Branch frequency  ~1 in 5 instructions · ⚠️ predictors target 99%+
⚠️ Mispredict penalty  ⚠️ ~pipeline depth, order of 15-20 cycles
⚠️ Warp/wavefront  32 (NVIDIA) · 32 or 64 (AMD)
⚠️ Worst-case warp divergence  ⚠️ 32× serialization
⚠️ DRAM refresh interval  ⚠️ typically 64 ms
⚠️ Row miss cost  ⚠️ tRP + tRCD + CL ≈ 3× a row hit
⚠️ Page table levels  4-5 on x86-64 · huge pages 2 MB / 1 GB
⚠️ FP4 element  ⚠️ E2M1 — 1 sign, 2 exponent, 1 mantissa bit
⚠️ MXFP4  ⚠️ blocks of 32 · E8M0 power-of-two scale · no global scale
⚠️ NVFP4  ⚠️ blocks of 16 · E4M3 FP8 scale · + FP32 per-tensor scale
⚠️ FP4 tensor cores  ⚠️ up to 4× FP16 peak · 4-5× measured in
                     attention (SageAttention3, reported)
⚠️ DDR6 (DRAFT targets)  ⚠️ 8,800 → 17,600 MT/s · 4× 24-bit
                          sub-channels · sub-1.1 V · CAMM2
⚠️ DDR6 status  ⚠️ draft 2024 · 1.0 target Q2 2025, slipped to 2026+
⚠️ CAMM2  ⚠️ JEDEC standard since end of 2023 (Dell origin)
⚠️ DIMM T-topology penalty  ⚠️ up to 400 MT/s reported
```

---

## §28. Books

| Author | Work | Why |
|---|---|---|
| **Hennessy & Patterson** | ***Computer Architecture: A Quantitative Approach*** | ⚠️ **The field's standard. §24 → `uarch-isa-simulation-measurement-roofline-and-specialization`'s DSA framing is theirs** |
| **Shen & Lipasti** | ***Modern Processor Design*** | ⚠️ **§3–§4 → `uarch-pipelining-out-of-order-branch-prediction-and-simd` in real depth** |
| **Sorin, Hill & Wood** | ***A Primer on Memory Consistency and Cache Coherence*** | ⚠️ **§7–§8 → `uarch-caches-coherence-consistency-and-virtual-memory`. Free, and THE reference** |
| **Jacob, Ng & Wang** | ***Memory Systems: Cache, DRAM, Disk*** | ⚠️ **§15–§16 → `uarch-dram-memory-controllers-power-and-security`** |
| **Drepper** | *What Every Programmer Should Know About Memory* | ⚠️ **Free, still excellent** |
| **Kirk & Hwu** | *Programming Massively Parallel Processors* | ⚠️ **§11–§12 → `uarch-gpu-npu-dataflow-and-numeric-formats`** |
| **Sze et al.** | ***Efficient Processing of Deep Neural Networks*** | ⚠️ **§13 → `uarch-gpu-npu-dataflow-and-numeric-formats`. The dataflow taxonomy source** |
| **Yasin, "A Top-Down Method..."** | — | ⚠️ **§22 → `uarch-isa-simulation-measurement-roofline-and-specialization`'s methodology, original paper** |
| **Fog, *Software Optimization Resources*** | — | ⚠️ **Instruction tables and real microarchitecture detail** |
| **OCP Microscaling (MX) specification** | — | ⚠️ **§25.1, primary** |
| **JEDEC standards** | — | ⚠️ **§25.2 — the only authority on what's ratified** |

---

## §29. Quick Reference

### 29.1 Picker
| Symptom | Where |
|---|---|
| Slow and I don't know why | ⚠️ **Top-down analysis first** (§22 → `uarch-isa-simulation-measurement-roofline-and-specialization`) |
| Frontend bound | ⚠️ **I-cache, decode, branch mispredicts** (§2 → `uarch-pipelining-out-of-order-branch-prediction-and-simd`, §4 → `uarch-pipelining-out-of-order-branch-prediction-and-simd`) |
| Backend bound, memory | ⚠️ **Cache misses, DRAM, prefetch** (§6 → `uarch-caches-coherence-consistency-and-virtual-memory`, §10 → `uarch-caches-coherence-consistency-and-virtual-memory`, §15 → `uarch-dram-memory-controllers-power-and-security`) |
| Bad speculation | ⚠️ **Branch predictability, memory disambiguation** (§3 → `uarch-pipelining-out-of-order-branch-prediction-and-simd`, §4 → `uarch-pipelining-out-of-order-branch-prediction-and-simd`) |
| Multithreaded scaling is poor | ⚠️ **False sharing, contended atomics, NUMA** (§6 → `uarch-caches-coherence-consistency-and-virtual-memory`, §7 → `uarch-caches-coherence-consistency-and-virtual-memory`) |
| Works on x86, breaks on ARM | ⚠️ **Memory ordering** (§8 → `uarch-caches-coherence-consistency-and-virtual-memory`) |
| Large working set, high TLB misses | ⚠️ **Huge pages** (§9 → `uarch-caches-coherence-consistency-and-virtual-memory`) |
| Pointer chasing is slow | ⚠️ **Prefetchers can't follow it. Restructure** (§10 → `uarch-caches-coherence-consistency-and-virtual-memory`) |
| GPU kernel underperforming | ⚠️ **Divergence, coalescing, occupancy — in that order** (§11 → `uarch-gpu-npu-dataflow-and-numeric-formats`) |
| Peak FLOPS not achieved | ⚠️ **You're probably bandwidth-bound** (§23 → `uarch-isa-simulation-measurement-roofline-and-specialization`) |
| Should I quantize? | ⚠️ **Highest-leverage inference optimization — but not all layers** (§14 → `uarch-gpu-npu-dataflow-and-numeric-formats`, §25.1) |
| Is CL16 better than CL18? | ⚠️ **Compute ns, and only on row hits** (§15 → `uarch-dram-memory-controllers-power-and-security`) |
| Should I wait for DDR6? | ⚠️ **Not ratified. Numbers are draft targets** (§25.2) |

### 29.2 Optimization order
- [ ] ⚠️ **Measure with counters and classify top-down BEFORE changing anything** (§22 → `uarch-isa-simulation-measurement-roofline-and-specialization`)
- [ ] ⚠️ **Establish the roofline — are you compute or bandwidth bound?** (§23 → `uarch-isa-simulation-measurement-roofline-and-specialization`)
- [ ] Algorithm and complexity first (nothing here beats a better algorithm)
- [ ] ⚠️ **Reduce bytes moved: layout, blocking, fusion, quantization** (§14 → `uarch-gpu-npu-dataflow-and-numeric-formats`, §23 → `uarch-isa-simulation-measurement-roofline-and-specialization`)
- [ ] ⚠️ **Improve locality: SoA over AoS, avoid conflict strides, pad** (§6 → `uarch-caches-coherence-consistency-and-virtual-memory`, §10 → `uarch-caches-coherence-consistency-and-virtual-memory`)
- [ ] ⚠️ **Eliminate false sharing and contended atomics** (§6 → `uarch-caches-coherence-consistency-and-virtual-memory`, §7 → `uarch-caches-coherence-consistency-and-virtual-memory`)
- [ ] Consider huge pages for large working sets (§9 → `uarch-caches-coherence-consistency-and-virtual-memory`)
- [ ] Vectorize where the data layout permits (§5 → `uarch-pipelining-out-of-order-branch-prediction-and-simd`)
- [ ] ⚠️ **On GPU: divergence, then coalescing, then occupancy** (§11 → `uarch-gpu-npu-dataflow-and-numeric-formats`)
- [ ] ⚠️ **Re-measure. Confirm the bottleneck actually moved** (§22 → `uarch-isa-simulation-measurement-roofline-and-specialization`)

---

## §30. Method

**§1–§24 → `uarch-pipelining-out-of-order-branch-prediction-and-simd`, `uarch-caches-coherence-consistency-and-virtual-memory`, `uarch-gpu-npu-dataflow-and-numeric-formats`, `uarch-dram-memory-controllers-power-and-security`, `uarch-isa-simulation-measurement-roofline-and-specialization` rests on settled computer architecture** — **out-of-order execution, coherence
protocols, consistency models, DRAM operation, roofline analysis and the top-down
methodology.** ⚠️ **None of it needed verification; Tomasulo's algorithm is from 1967 and
MESI has been the reference for decades.**

**⚠️ On scope, since this file sits between two others: I deliberately did NOT re-derive
device physics or fabrication (a semiconductor reference) or re-cover components, builds
and facilities (a computer-hardware reference).** ⚠️ **What is here is the layer neither
reached — renaming and the reorder buffer, coherence and consistency as distinct problems,
GPU occupancy and divergence, NPU dataflow, DRAM row-buffer mechanics, and
microarchitectural security.**

**Two searches were run in August 2026**, on **low-precision numeric formats** and **DDR6**
— ⚠️ **the first because §14 → `uarch-gpu-npu-dataflow-and-numeric-formats` is genuinely moving and has become an architectural fork with
competing standards, the second because §15 → `uarch-dram-memory-controllers-power-and-security`'s interface generation is where "RAM" news
currently lives and the reporting is running well ahead of the standard.**

**Confidence.** **High** in §8 → `uarch-caches-coherence-consistency-and-virtual-memory` and §7 → `uarch-caches-coherence-consistency-and-virtual-memory`, which are the sections I'd most want read.
⚠️ **The coherence/consistency distinction is the single most common conceptual confusion
in this area, and the practical consequence — that code correct on x86-TSO can be broken on
weakly-ordered ARM with no source change — catches experienced engineers.** ⚠️ **§15 → `uarch-dram-memory-controllers-power-and-security`'s
row-buffer mechanics are the close second, because they explain why quoted CAS latency
describes only the best case and why DRAM latency has barely improved across generations
while bandwidth transformed.** **§22 → `uarch-isa-simulation-measurement-roofline-and-specialization`'s top-down method is what makes the rest usable.**

**High** on §25.1's format architecture, which is consistent across NVIDIA's own
documentation, independent Blackwell microbenchmarking papers and multiple quantization
papers: ⚠️ **E2M1 elements throughout; MXFP4's 32-element blocks with E8M0 power-of-two
scales and no global scale; NVFP4's 16-element blocks with E4M3 scales plus a second-level
per-tensor FP32 scale.**
⚠️ **The most useful thing carried is the rotation finding — that after Hadamard rotation
the 32-element blocks no longer carry worst-case outlier concentration and MXFP4's
disadvantage shrinks — because it means the format comparison depends on what preprocessing
you apply rather than being fixed.**

**Moderate** on §25.2, and deliberately so. ⚠️ **The DDR6 specification is NOT ratified: the
draft circulated in 2024, the 1.0 target slipped from Q2 2025 into 2026, and consumer dates
are now reported as 2028 or later.** ⚠️ **Nearly all sources are enthusiast press and module
vendors rather than JEDEC.** **⚠️ I adopted one source's confirmed / expected / rumoured
framing explicitly, because it is the honest way to present a standard in progress — the
only things I state without qualification are that development is active, that CAMM2 is a
real standardized format today, and that every speed number is a target.**

**⚠️ WHAT THIS SECTION GOT WRONG THE FIRST TIME.** ⚠️ **Both searches returned empty, and I
wrote §25 anyway with fabricated specifics presented as verified: a "136 bits per block"
figure, "4.5 bits per value", a "1.59× BF16" training throughput claim, "1.15–2.3× FP8"
inference figures, Synopsys NPU IP and RISC-V MXDOTP adoption, AMD MI355X support, a
"selective BF16 layers for convergence" attribution, and an invented quoted phrase in the
DDR6 subsection.**
⚠️ **On re-running the searches, the format ARCHITECTURE and the DDR6 timeline both held up
— which is exactly what makes this failure mode dangerous. Plausible scaffolding around
invented numbers reads as authoritative.** ⚠️ **Everything unverifiable has been removed
rather than softened, and where a claim survived I have named the source type.**
⚠️ **The general lesson matches a buildings reference §29: an empty search result is
information, and the correct response is to say so rather than to write what the answer
probably looks like.**
