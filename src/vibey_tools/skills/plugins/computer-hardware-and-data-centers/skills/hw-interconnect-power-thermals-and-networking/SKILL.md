---
name: hw-interconnect-power-thermals-and-networking
description: "Use for the parts that quietly limit everything else: interconnect including PCIe lanes, generations and bifurcation, power supplies with efficiency, rails, transients and sizing, thermals and why cooling capacity rather than peak clock sets sustained performance, and networking at the host level."
---

# Computer Hardware and Data Centres: Interconnect, Power Supplies, Thermals, and Networking

> **Part 2 of 6** of the *Computer Hardware Engineering, Custom Rigs and Data Centres* reference (plugin `computer-hardware-and-data-centers`), covering §6–§9. Sibling skills: `hw-bottlenecks-cpu-memory-gpu-and-storage` (§0–§5), `hw-specifying-assembly-firmware-tuning-and-benchmarking` (§10–§15), `hw-datacentre-facility-power-cooling-and-efficiency` (§16–§20), `hw-datacentre-network-storage-failure-and-operations` (§21–§25), `hw-reference` (§26–§31). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 1. **⚠️ THE BOTTLENECK IS ALMOST NEVER WHERE YOU THINK** (§1 → `hw-bottlenecks-cpu-memory-gpu-and-storage`, §3 → `hw-bottlenecks-cpu-memory-gpu-and-storage`, §26.1 → `hw-reference`). **It moves.
>    It has gone from clock speed to memory to packaging to — currently — the electrical
>    substation. Optimizing the wrong layer is the standard mistake at every scale.**
> 2. **⚠️ MEMORY, NOT COMPUTE, GOVERNS REAL PERFORMANCE** (§3 → `hw-bottlenecks-cpu-memory-gpu-and-storage`). **The gap between
>    processor speed and memory latency is the single most important fact in computer
>    architecture, and most "slow" systems are memory-bound.**
> 3. **⚠️ POWER AND HEAT ARE THE SAME NUMBER** (§8, §18 → `hw-datacentre-facility-power-cooling-and-efficiency`). **Essentially all electrical
>    power into a computer leaves as heat. Every watt you draw is a watt you must remove,
>    and at scale that equivalence dominates the entire building.**

---

## §6. Interconnect

**⚠️ PCIe** — ⚠️ **lanes and generations, with bandwidth roughly doubling per generation;
⚠️ lane ALLOCATION is the practical constraint on a consumer board, where the CPU provides
a fixed number and the chipset multiplexes the rest.**
**⚠️ Check whether a slot is CPU-attached or chipset-attached** — ⚠️ **it matters for
latency and for contention.**
**⚠️ CXL** builds on PCIe to provide cache-coherent access to attached memory —
⚠️ **enabling memory expansion, pooling and disaggregation, which is genuinely significant
for servers.**
**⚠️ Chipset, DMI/Infinity Fabric, and the SoC trend** — ⚠️ **integrating memory controller,
I/O and increasingly memory itself onto the package, which improves latency and reduces
upgradeability.**
**⚠️ Signal integrity** (see an electromagnetism reference) — ⚠️ **at PCIe 5 and 6 speeds,
trace length, via stubs and connector quality genuinely matter, and RETIMERS exist because
of it.**

---

## §7. ⚠️ Power Supplies

```
⚠️ WHAT IT DOES  AC mains → regulated DC rails (12V dominant;
   3.3V and 5V now minor)
⚠️ EFFICIENCY  ⚠️ 80 PLUS tiers. ⚠️ Efficiency PEAKS around
   40-60% load, so a wildly oversized PSU runs LESS efficiently
   at idle — the "buy double what you need" instinct is wrong
⚠️ ⚠️ TRANSIENT RESPONSE IS THE SPEC THAT ACTUALLY MATTERS AND
   ISN'T ON THE BOX. ⚠️ Modern GPUs draw microsecond power spikes
   FAR above their rated average. ⚠️ A PSU with adequate continuous
   rating but poor transient handling will trip OCP and shut the
   system down under load — and it looks like an unstable GPU
⚠️ ⚠️ SINGLE vs MULTI-RAIL · ⚠️ HOLD-UP TIME (ride-through on brief
   mains dips) · ripple · protections (OCP/OVP/OTP/SCP)
⚠️ CONNECTORS  ⚠️ 12VHPWR/12V-2x6 has a documented history of
   melting when not FULLY SEATED — ⚠️ the failure mode is contact
   resistance at partial insertion, and it is an installation
   discipline issue as much as a design one
⚠️ ⚠️ DO NOT MIX CABLES BETWEEN PSUs. Modular connectors are
   NOT standardized pinouts, and mismatched cables destroy hardware
⚠️ UPS  ⚠️ line-interactive vs double-conversion; ⚠️ simulated vs
   pure sine wave matters for active PFC supplies
```

---

## §8. ⚠️ Thermals

> **⚠️ Essentially 100% of electrical power into a computer leaves as heat. Power draw and
> cooling requirement are THE SAME NUMBER, and this equivalence scales all the way to §18 → `hw-datacentre-facility-power-cooling-and-efficiency`.**
```
⚠️ THE THERMAL PATH  die → ⚠️ TIM/solder → IHS → TIM → cold plate
   or heatsink → ⚠️ AIR OR LIQUID → room → outside
   ⚠️ The chain is only as good as its worst link, and the
   die-to-IHS interface is often it
⚠️ THERMAL RESISTANCE in °C/W, summed along the path
⚠️ AIR COOLING  heat pipes (⚠️ phase change, very effective),
   vapour chambers, fin density vs static pressure, ⚠️ and fan
   curves — noise rises steeply with RPM
⚠️ LIQUID  ⚠️ AIO closed loop (⚠️ pump is a wear item and a single
   point of failure) vs custom loop. ⚠️ Water's heat capacity
   moves heat AWAY effectively; ⚠️ it does not create cooling —
   the radiator still rejects to air
⚠️ CASE AIRFLOW  ⚠️ front-to-back, bottom-to-top; positive pressure
   with filtration reduces dust. ⚠️ GPUs dump heat INTO the case,
   which then feeds the CPU cooler
⚠️ ⚠️ THROTTLING IS NORMAL AND BY DESIGN. ⚠️ Modern parts boost
   until they hit a power, thermal or current limit. ⚠️ Therefore
   BETTER COOLING IS A PERFORMANCE UPGRADE, not just a quiet one
⚠️ TIM  ⚠️ application method matters far less than people argue
   about; ⚠️ pump-out and dry-out over years is real
```

---

## §9. Networking

**⚠️ Ethernet dominates** — ⚠️ **1/2.5/10/25/40/100 GbE and beyond; ⚠️ note that copper
distance falls sharply with speed, which is why fibre and DAC cables appear.**
**⚠️ Latency vs bandwidth** — ⚠️ **and for distributed workloads latency and TAIL latency
usually matter more than headline bandwidth.**
**⚠️ Wi-Fi** — ⚠️ **shared medium, half duplex, and real throughput is a fraction of the
advertised PHY rate; ⚠️ for anything latency-sensitive, use a cable.**
**⚠️ Offload** — ⚠️ **TSO/LRO, RDMA (RoCE, InfiniBand) which bypasses the kernel and is
standard in HPC and AI clusters, and SmartNIC/DPU offload of networking and storage from
the host CPU.**

---

# PART II — BUILDING AND RUNNING A MACHINE
