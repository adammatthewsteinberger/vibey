---
name: hw-datacentre-facility-power-cooling-and-efficiency
description: "Use for data centre facilities: facility basics and tier models, power distribution from utility feed through UPS and PDU to the rack with redundancy topologies, cooling at scale including air containment, liquid and direct-to-chip, efficiency metrics such as PUE and what they hide, and racks and the physical infrastructure that constrains everything else."
---

# Computer Hardware and Data Centres: Facility Basics, Power Distribution, Cooling at Scale, Efficiency Metrics, and Racks and Physical Infrastructure

> **Part 4 of 6** of the *Computer Hardware Engineering, Custom Rigs and Data Centres* reference (plugin `computer-hardware-and-data-centers`), covering §16–§20. Sibling skills: `hw-bottlenecks-cpu-memory-gpu-and-storage` (§0–§5), `hw-interconnect-power-thermals-and-networking` (§6–§9), `hw-specifying-assembly-firmware-tuning-and-benchmarking` (§10–§15), `hw-datacentre-network-storage-failure-and-operations` (§21–§25), `hw-reference` (§26–§31). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 3. **⚠️ POWER AND HEAT ARE THE SAME NUMBER** (§8 → `hw-interconnect-power-thermals-and-networking`, §18). **Essentially all electrical
>    power into a computer leaves as heat. Every watt you draw is a watt you must remove,
>    and at scale that equivalence dominates the entire building.**

---

## §16. Facility Basics

```
⚠️ WHAT A DATA CENTRE ACTUALLY IS  ⚠️ a building that converts
   electricity into computation and heat, reliably. ⚠️ Everything
   else is in service of that
⚠️ THE MAJOR SYSTEMS  ⚠️ POWER (§17) · ⚠️ COOLING (§18) · space
   and structure · network · fire suppression · security ·
   monitoring
⚠️ TIER CLASSIFICATION (Uptime Institute)  ⚠️ I basic · II
   redundant components · ⚠️ III CONCURRENTLY MAINTAINABLE (you
   can service anything without shutting down) · ⚠️ IV FAULT
   TOLERANT (survives a single failure anywhere)
   ⚠️ Note "Tier III" is frequently claimed and rarely certified —
   ask whether the CERTIFICATION exists or just the aspiration
⚠️ TYPES  hyperscale · colocation (retail and wholesale) ·
   enterprise · ⚠️ EDGE (small, distributed, latency-driven)
⚠️ SITE SELECTION  ⚠️ POWER AVAILABILITY FIRST (§26.1) · fibre
   routes · water · climate (free cooling hours) · land ·
   natural hazard exposure · latency to users · tax and politics
```

---

## §17. ⚠️ Power Distribution

> **⚠️ The dominant capital cost, the dominant design constraint, and increasingly the
> reason a facility can or cannot be built at all** (§26 → `hw-reference`).
```
⚠️ THE CHAIN  utility medium voltage → transformer → switchgear →
   ⚠️ UPS → PDU → rack busbar/PDU → server PSU → VRM → chip
   ⚠️ EVERY CONVERSION LOSES ENERGY, and the losses compound (§19)
⚠️ REDUNDANCY NOTATION  ⚠️ N (no redundancy) · N+1 (one spare) ·
   ⚠️ 2N (fully duplicated) · 2N+1
   ⚠️ THE KEY DISTINCTION: redundancy protects against COMPONENT
   failure; ⚠️ CONCURRENT MAINTAINABILITY means you can also
   service it without downtime, and those are different properties
⚠️ UPS TYPES  ⚠️ double-conversion (cleanest, least efficient) ·
   line-interactive · ⚠️ ECO/multi-mode which trades a little
   protection for meaningful efficiency · flywheel · lithium
   batteries increasingly displacing VRLA
⚠️ GENERATORS  ⚠️ diesel standby, with the UPS covering only the
   seconds until they start and stabilize. ⚠️ FUEL CONTRACTS and
   ⚠️ REGULAR LOAD-BANK TESTING are what make them real — an
   untested generator is a decoration
⚠️ ⚠️ THE FAILURE PATTERN: most data centre outages trace to POWER,
   and disproportionately to the TRANSFER between sources —
   ATS failures, batteries that had degraded silently, and
   generators that didn't start
⚠️ AT RACK LEVEL  ⚠️ 208/415V AC three-phase or 48 VDC, and now
   ⚠️ 800 VDC (§26.2)
```

---

## §18. ⚠️ Cooling at Scale

**⚠️ Every watt in becomes a watt of heat out** (§8 → `hw-interconnect-power-thermals-and-networking`) — ⚠️ **so a 100 MW facility is a 100 MW
heat source.** **See a refrigeration reference for the underlying physics.**
```
⚠️ AIR-BASED  ⚠️ hot aisle / cold aisle containment (⚠️ the single
   highest-value retrofit in legacy facilities) · CRAC/CRAH ·
   raised floor or overhead delivery
   ⚠️ AIR RUNS OUT OF CAPACITY around 30-40 kW per rack even
   with optimized design (§26.2)
⚠️ ECONOMIZATION  ⚠️ air-side (⚠️ outside air directly, subject to
   humidity and contamination) and water-side (cooling towers)
   ⚠️ FREE COOLING HOURS drive site selection
⚠️ LIQUID  ⚠️ rear-door heat exchangers (⚠️ easiest retrofit) →
   ⚠️ DIRECT-TO-CHIP cold plates with a CDU → immersion
   (single or two-phase)
   ⚠️ Liquid is now MANDATORY, not optional, above roughly
   50-100 kW per rack (§26.2)
⚠️ WATER  ⚠️ evaporative cooling consumes water and trades it
   against electricity. ⚠️ WUE is a real metric and a real siting
   constraint in stressed regions
⚠️ ⚠️ ASHRAE THERMAL GUIDELINES  ⚠️ and the important finding is
   that the allowable ranges are WIDER than operators historically
   assumed — running warmer saves substantial cooling energy at
   little reliability cost, and over-cooling is a widespread and
   expensive habit
⚠️ HEAT REUSE  district heating from data centre waste heat is
   real where the geography permits, and limited by the LOW
   TEMPERATURE of the rejected heat (see a thermodynamics
   reference on exergy)
```

---

## §19. Efficiency Metrics

**⚠️ PUE = total facility energy ÷ IT equipment energy.** ⚠️ **1.0 is the theoretical
ideal; hyperscale facilities operate close to it and legacy enterprise rooms are far
worse.**
> **⚠️ GOTCHA — PUE IS EASILY GAMED AND FREQUENTLY MISUSED.** ⚠️ **It measures
> INFRASTRUCTURE overhead, not useful work.** **⚠️ Making the IT equipment less efficient
> IMPROVES PUE, because it increases the denominator.** ⚠️ **A facility with excellent PUE
> running idle servers is wasting more energy than a worse-PUE facility doing useful work.**
> **⚠️ Also check the measurement boundary, the averaging period, and whether it's
> annualized or a favourable-day figure.**

**⚠️ Complementary metrics**: ⚠️ **WUE (water), CUE (carbon), and — the ones that actually
matter — WORK PER WATT: transactions, queries or tokens per joule.**
**⚠️ The largest efficiency wins are usually not in the facility at all**: ⚠️ **server
utilization (⚠️ idle servers draw a large fraction of peak power for zero output),
virtualization and consolidation, decommissioning zombie servers, and software
efficiency.**

---

## §20. Racks and Physical Infrastructure

**⚠️ The 19-inch rack, measured in U (1U = 1.75 inches / 44.45 mm)**, ⚠️ **with 42U and 48U
common and depth mattering more than people expect.**
**⚠️ OCP (Open Compute Project)** — ⚠️ **21-inch racks, DC busbar distribution, PSUs moved
out of the server, and a genuinely different mechanical standard now widely adopted by
hyperscalers.**
**⚠️ Weight and floor loading are real constraints** — ⚠️ **a fully populated high-density
rack is very heavy, and liquid cooling adds more.**
**⚠️ Cable management, structured cabling, and labelling** — ⚠️ **unglamorous and the
difference between a maintainable facility and an unmaintainable one.**
**⚠️ Physical security**: **layered access, mantraps, CCTV, cage-level separation in colo.**
