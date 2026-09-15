---
name: hw-bottlenecks-cpu-memory-gpu-and-storage
description: "Use when choosing or diagnosing components: where the bottleneck actually lives and how to find it before spending money, CPU architecture and what core counts and clocks really buy, the memory hierarchy and why latency and bandwidth are different problems, GPUs and accelerators, and storage from NVMe queue depth to endurance. Includes the router for the whole computer hardware and data centres reference."
---

# Computer Hardware and Data Centres: Where the Bottleneck Actually Lives, CPU Architecture, the Memory Hierarchy, GPUs and Accelerators, and Storage

> **Part 1 of 6** of the *Computer Hardware Engineering, Custom Rigs and Data Centres* reference (plugin `computer-hardware-and-data-centers`), covering §0–§5. Sibling skills: `hw-interconnect-power-thermals-and-networking` (§6–§9), `hw-specifying-assembly-firmware-tuning-and-benchmarking` (§10–§15), `hw-datacentre-facility-power-cooling-and-efficiency` (§16–§20), `hw-datacentre-network-storage-failure-and-operations` (§21–§25), `hw-reference` (§26–§31). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The architecture is stable. Two areas moved decisively. See §26 → `hw-reference` for grid power as the binding constraint, and the shift to high-voltage DC rack distribution.

> **⚠️ The systems level above a semiconductor reference.** ⚠️ **That file covers how chips
> are made; this covers what happens when you have to power them, cool them, connect them
> and keep them running — at one desk or at a hundred megawatts.**
>
> **Complements an electromagnetism reference (power delivery, signal integrity, I²R
> losses), a refrigeration reference (cooling physics), a thermodynamics reference (heat
> rejection and exergy), and a resource-extraction reference (where the grid power comes
> from).**
>
> **⚠️ GOTCHA** boxes mark where spec sheets mislead and where builders waste money.
>
> **The three ideas that organize this document:**
> 1. **⚠️ THE BOTTLENECK IS ALMOST NEVER WHERE YOU THINK** (§1, §3, §26.1 → `hw-reference`). **It moves.
>    It has gone from clock speed to memory to packaging to — currently — the electrical
>    substation. Optimizing the wrong layer is the standard mistake at every scale.**
> 2. **⚠️ MEMORY, NOT COMPUTE, GOVERNS REAL PERFORMANCE** (§3). **The gap between
>    processor speed and memory latency is the single most important fact in computer
>    architecture, and most "slow" systems are memory-bound.**
> 3. **⚠️ POWER AND HEAT ARE THE SAME NUMBER** (§8 → `hw-interconnect-power-thermals-and-networking`, §18 → `hw-datacentre-facility-power-cooling-and-efficiency`). **Essentially all electrical
>    power into a computer leaves as heat. Every watt you draw is a watt you must remove,
>    and at scale that equivalence dominates the entire building.**

---

## §0. Routing

| You want... | Go to |
|---|---|
| Where bottlenecks live | §1 |
| CPU architecture | §2 |
| **⚠️ Memory hierarchy** | **§3** |
| GPUs and accelerators | §4 |
| Storage | §5 |
| Interconnect | §6 → `hw-interconnect-power-thermals-and-networking` |
| **⚠️ Power supplies** | **§7 → `hw-interconnect-power-thermals-and-networking`** |
| **⚠️ Thermals** | **§8 → `hw-interconnect-power-thermals-and-networking`** |
| Networking | §9 → `hw-interconnect-power-thermals-and-networking` |
| **Specifying a build** | **§10 → `hw-specifying-assembly-firmware-tuning-and-benchmarking`** |
| Assembly | §11 → `hw-specifying-assembly-firmware-tuning-and-benchmarking` |
| Firmware and boot | §12 → `hw-specifying-assembly-firmware-tuning-and-benchmarking` |
| Tuning and overclocking | §13 → `hw-specifying-assembly-firmware-tuning-and-benchmarking` |
| **⚠️ Troubleshooting** | **§14 → `hw-specifying-assembly-firmware-tuning-and-benchmarking`** |
| **⚠️ Benchmarking** | **§15 → `hw-specifying-assembly-firmware-tuning-and-benchmarking`** |
| Facility basics | §16 → `hw-datacentre-facility-power-cooling-and-efficiency` |
| **⚠️ Power distribution** | **§17 → `hw-datacentre-facility-power-cooling-and-efficiency`** |
| **⚠️ Cooling at scale** | **§18 → `hw-datacentre-facility-power-cooling-and-efficiency`** |
| Efficiency metrics | §19 → `hw-datacentre-facility-power-cooling-and-efficiency` |
| Racks and physical | §20 → `hw-datacentre-facility-power-cooling-and-efficiency` |
| Network architecture | §21 → `hw-datacentre-network-storage-failure-and-operations` |
| Storage at scale | §22 → `hw-datacentre-network-storage-failure-and-operations` |
| **⚠️ Failure at scale** | **§23 → `hw-datacentre-network-storage-failure-and-operations`** |
| Operations | §24 → `hw-datacentre-network-storage-failure-and-operations` |
| AI infrastructure | §25 → `hw-datacentre-network-storage-failure-and-operations` |
| **What's live** | **§26 → `hw-reference`** |
| Misconceptions, numbers | §27–§28 → `hw-reference` |
| Sources, quick ref, method | §29–§31 → `hw-reference` |

---

## §1. Where the Bottleneck Actually Lives

```
⚠️ THE HISTORICAL MIGRATION — and each shift invalidated the
   previous generation's optimization instincts
   ⚠️ 1990s   CPU clock speed
   ⚠️ 2000s   ⚠️ MEMORY LATENCY (§3) and then thermal/power limits
   ⚠️ 2010s   I/O and storage, until NVMe largely solved it
   ⚠️ Early 2020s  ⚠️ chip supply, then advanced PACKAGING and HBM
   ⚠️ NOW     ⚠️ GRID POWER AND INTERCONNECTION (§26.1)
⚠️ AMDAHL'S LAW  ⚠️ speedup is capped by the fraction you DIDN'T
   parallelize. ⚠️ Optimizing an already-fast component gains
   nothing — this is the formal version of the whole section
⚠️ THE DIAGNOSTIC DISCIPLINE  ⚠️ MEASURE before optimizing.
   ⚠️ Is it CPU-bound, memory-bound, I/O-bound, network-bound,
   or thermally throttled? (§14, §15). ⚠️ These have completely
   different fixes and people routinely guess wrong
```

---

# PART I — COMPONENTS

## §2. CPU Architecture

```
⚠️ THE PIPELINE  fetch → decode → execute → memory → writeback
⚠️ THE PERFORMANCE EQUATION  ⚠️ time = instructions × CPI × cycle
   time. ⚠️ THREE independent levers, which is why "GHz" alone
   tells you almost nothing across architectures
⚠️ ILP TECHNIQUES  superscalar (multiple instructions per cycle) ·
   out-of-order execution · ⚠️ BRANCH PREDICTION (⚠️ a mispredict
   flushes the pipeline and costs tens of cycles) · speculation ·
   SMT/hyperthreading
⚠️ SIMD  AVX, NEON, SVE — data parallelism within a core
⚠️ HETEROGENEOUS CORES  ⚠️ performance and efficiency cores, which
   makes SCHEDULING a first-order problem and is why OS scheduler
   quality now visibly affects benchmarks
⚠️ ISA  x86-64 · ⚠️ ARM (now genuinely competitive in servers and
   dominant in mobile) · RISC-V (open, growing)
⚠️ THE POWER REALITY (see a semiconductor reference §5)
   ⚠️ Frequency scaling stopped; ⚠️ boost behaviour is now
   thermally and power-limited, so SUSTAINED performance can
   differ enormously from peak
⚠️ SPECULATIVE EXECUTION SIDE CHANNELS  ⚠️ Spectre/Meltdown class —
   ⚠️ the mitigations cost real performance, which is why old
   benchmarks are not comparable to patched systems
```

---

## §3. ⚠️ The Memory Hierarchy

> **⚠️ The most important section for understanding real performance. The processor-memory
> gap is the defining problem of modern computer architecture.**
```
⚠️ THE LATENCY LADDER, in rough cycle counts — ⚠️ the ORDERS OF
   MAGNITUDE are the point, not the exact numbers
   ⚠️ Register        ~1 cycle
   ⚠️ L1 cache        ~4 cycles
   ⚠️ L2              ~12 cycles
   ⚠️ L3              ~40 cycles
   ⚠️ MAIN MEMORY     ⚠️ ~200-300 cycles
   ⚠️ NVMe SSD        ⚠️ ~100,000+ cycles
   ⚠️ Network/disk    millions
⚠️ ⚠️ A MAIN MEMORY ACCESS COSTS HUNDREDS OF CYCLES. A modern core
   can execute HUNDREDS OF INSTRUCTIONS in the time one cache miss
   takes. ⚠️ This is why cache behaviour dominates real performance
⚠️ WHY CACHES WORK  ⚠️ LOCALITY — temporal (reuse soon) and spatial
   (nearby addresses soon). ⚠️ Programs that violate locality get
   no benefit and run at memory speed
⚠️ CACHE LINES  ⚠️ typically 64 bytes — you always fetch a whole
   line. ⚠️ Hence FALSE SHARING, where two threads writing
   different variables in the SAME LINE destroy performance
   through cache coherence traffic
⚠️ DRAM  ⚠️ latency has improved remarkably little across
   generations; BANDWIDTH has improved enormously. ⚠️ DDR5 and
   channel count matter more than raw MT/s for many workloads
⚠️ NUMA  ⚠️ on multi-socket systems, memory attached to another
   socket is substantially slower. ⚠️ Ignoring NUMA placement is
   a classic and large performance loss
⚠️ VIRTUAL MEMORY and the TLB  ⚠️ TLB misses are their own penalty;
   huge pages exist to reduce them
```
> **⚠️ GOTCHA — "add more RAM" and "get faster RAM" solve different problems.** ⚠️ **Running
> out of capacity causes swapping and is catastrophic; once you have enough, more capacity
> does nothing.** **⚠️ Latency and bandwidth improvements are usually single-digit-percent
> gains outside specific workloads — and integrated GPUs, which share system memory, are
> the notable exception where bandwidth genuinely matters.**

---

## §4. GPUs and Accelerators

**⚠️ The architectural difference is throughput versus latency**: ⚠️ **a CPU minimizes the
latency of one thread; a GPU maximizes aggregate throughput by running enormous numbers of
threads and HIDING memory latency by switching between them.**
```
⚠️ SIMT execution · ⚠️ WARP/wavefront divergence (⚠️ branches within
   a warp serialize — the main GPU performance trap)
⚠️ MEMORY IS USUALLY THE LIMIT  ⚠️ GDDR or HBM bandwidth, and
   ⚠️ VRAM CAPACITY is the hard wall for AI work — a model that
   doesn't fit doesn't run, regardless of compute
⚠️ TENSOR/MATRIX UNITS  ⚠️ and reduced precision (FP16, BF16, FP8,
   INT8) is where the headline TOPS numbers come from —
   ⚠️ always check WHICH precision a quoted figure refers to
⚠️ ARITHMETIC INTENSITY and the ROOFLINE MODEL  ⚠️ FLOPs per byte
   moved determines whether you are compute-bound or
   memory-bandwidth-bound. ⚠️ Most real kernels are bandwidth-bound
⚠️ OTHER ACCELERATORS  NPUs · TPUs and custom ASICs · FPGAs
   (⚠️ reconfigurable, good for low latency and evolving protocols,
   hard to program) · DPUs/SmartNICs
```

---

## §5. Storage

```
⚠️ NAND SSD  (see a semiconductor reference §8) ⚠️ wear-out is
   intrinsic, hence TBW ratings and wear levelling
   ⚠️ SLC/TLC/QLC trade density against endurance and sustained
   write speed — ⚠️ note that consumer drives use an SLC CACHE
   and slow dramatically once it's exhausted, which is why
   short benchmarks flatter them
   ⚠️ DRAM cache vs DRAM-less · ⚠️ TRIM · write amplification
⚠️ INTERFACES  SATA → NVMe over PCIe. ⚠️ NVMe's real advantage is
   the queue model and latency, not just bandwidth
⚠️ HDD  ⚠️ still unbeaten on cost per terabyte at capacity, hence
   its persistence in bulk and archival tiers
⚠️ ⚠️ RAID IS NOT BACKUP. It protects against DRIVE failure, not
   against deletion, corruption, ransomware, fire or theft
   ⚠️ RAID 5 rebuild on large modern drives carries real risk of a
   second failure or unrecoverable read error during the rebuild
⚠️ THE 3-2-1 RULE  three copies, two media, one offsite
⚠️ FILESYSTEMS  ⚠️ ZFS and Btrfs checksum data and can detect and
   repair silent corruption; conventional filesystems cannot
```
