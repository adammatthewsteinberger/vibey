---
name: hw-datacentre-network-storage-failure-and-operations
description: "Use for data centre systems and running them: network architecture including leaf-spine and oversubscription, storage at scale, failure at scale and why component failure becomes a design assumption rather than an incident, operations and maintenance practice, and what AI infrastructure changes about power density, networking and cooling."
---

# Computer Hardware and Data Centres: Network Architecture, Storage at Scale, Failure at Scale, Operations, and AI Infrastructure Specifics

> **Part 5 of 6** of the *Computer Hardware Engineering, Custom Rigs and Data Centres* reference (plugin `computer-hardware-and-data-centers`), covering §21–§25. Sibling skills: `hw-bottlenecks-cpu-memory-gpu-and-storage` (§0–§5), `hw-interconnect-power-thermals-and-networking` (§6–§9), `hw-specifying-assembly-firmware-tuning-and-benchmarking` (§10–§15), `hw-datacentre-facility-power-cooling-and-efficiency` (§16–§20), `hw-reference` (§26–§31). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 3. **⚠️ POWER AND HEAT ARE THE SAME NUMBER** (§8 → `hw-interconnect-power-thermals-and-networking`, §18 → `hw-datacentre-facility-power-cooling-and-efficiency`). **Essentially all electrical
>    power into a computer leaves as heat. Every watt you draw is a watt you must remove,
>    and at scale that equivalence dominates the entire building.**

---

## §21. Network Architecture

**⚠️ The topology shift**: ⚠️ **traditional three-tier (access/aggregation/core) was
designed for north-south traffic; ⚠️ modern LEAF-SPINE (Clos) topologies exist because
EAST-WEST traffic between servers now dominates.**
**⚠️ Oversubscription ratio** is the key design number — ⚠️ **how much aggregate access
bandwidth is contending for uplink capacity.**
**⚠️ For AI clusters specifically**: ⚠️ **collective operations (all-reduce) make the
network part of the compute path, so RDMA, lossless fabrics and congestion control matter
enormously; InfiniBand and increasingly Ethernet with RoCE; and ⚠️ RAIL-OPTIMIZED
topologies designed around GPU communication patterns.**
**⚠️ Optics**: ⚠️ **pluggable transceivers dominate, and CO-PACKAGED OPTICS is emerging to
cut the power cost of moving bits — networking power is a growing share of the total.**

---

## §22. Storage at Scale

**⚠️ The tiers**: ⚠️ **NVMe for hot, SSD for warm, HDD for capacity, tape for archive
(⚠️ tape is very much alive for cost per terabyte and for offline ransomware resistance).**
**⚠️ Distributed storage**: ⚠️ **replication versus ERASURE CODING (⚠️ far better storage
efficiency for the same durability, at the cost of rebuild bandwidth and CPU).**
**⚠️ The CAP theorem** frames the fundamental trade in distributed systems, ⚠️ **and in
practice the choice is between consistency and availability during a partition.**
**⚠️ Durability claims** ("eleven nines") are ⚠️ **modelled figures about drive failure, and
they do not cover operator error, software bugs or correlated failures — which are the
things that actually destroy data** (§23).

---

## §23. ⚠️ Failure at Scale

> **⚠️ At scale, rare events are constant. A failure rate that is negligible for one machine
> is a daily occurrence across a hundred thousand.**
```
⚠️ WHAT ACTUALLY FAILS  ⚠️ drives (predictably, at known rates) ·
   ⚠️ DRAM (⚠️ correctable and uncorrectable errors are far more
   common than most people assume — which is why ECC is not
   optional at scale, and soft errors are physics, not defects) ·
   PSUs · fans · optics and cables (⚠️ a large share of "network"
   problems) · ⚠️ and SOFTWARE and HUMAN ERROR, which dominate
   real outage causes
⚠️ CORRELATED FAILURE IS THE KILLER  ⚠️ same batch, same firmware
   bug, same rack, same power feed, same cooling loop.
   ⚠️ Independence is an ASSUMPTION and it is often false
⚠️ DESIGN RESPONSES  ⚠️ design for failure rather than against it ·
   fault domains and availability zones · ⚠️ blast radius
   limitation · graceful degradation · ⚠️ CHAOS ENGINEERING
⚠️ THE HONEST OBSERVATION  ⚠️ most large outages are triggered by
   a CHANGE — a deployment, a config push, a maintenance action —
   not by spontaneous hardware failure. ⚠️ Which means change
   management is reliability engineering
```

---

## §24. Operations

**⚠️ DCIM and monitoring**: ⚠️ **power, thermal, capacity and asset tracking; ⚠️ and the
useful principle is to monitor what you'd act on rather than everything you can collect.**
**⚠️ Capacity planning across four dimensions** — ⚠️ **space, power, cooling and network —
and ⚠️ POWER is normally the one that runs out first** (§26.1 → `hw-reference`).
**⚠️ Maintenance**: ⚠️ **battery testing, generator load banks, thermal imaging of
connections, filter changes, and cleanliness.**
**⚠️ Change management** (§23) and ⚠️ **runbooks that have actually been tested.**
**⚠️ Decommissioning and e-waste**: ⚠️ **secure data destruction, and component recovery —
which links to a resource-extraction reference, since recycling skips mining entirely.**

---

## §25. AI Infrastructure Specifics

**⚠️ AI training clusters break several assumptions that ordinary data centre design
relies on:**
⚠️ **the load is SYNCHRONIZED and near-constant rather than diverse and averaging out —
thousands of GPUs stepping together produce power swings that stress the electrical
system; ⚠️ power density per rack is an order of magnitude above conventional (§26.2 → `hw-reference`);
⚠️ the network is part of the compute path (§21); ⚠️ a single failed node can stall an
entire training job, so checkpointing and fast recovery are architectural requirements;
and ⚠️ utilization is expected to be extremely high, so there is no diversity factor to
exploit.**
**⚠️ Inference has a different profile** — ⚠️ **more variable, more latency-sensitive, more
amenable to scaling and to cheaper hardware.**
**⚠️ The stranded-asset risk is real**: ⚠️ **a facility built for one generation's density
may not physically support the next, and the accelerator refresh cadence is now faster
than the building's depreciation schedule.**
