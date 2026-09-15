---
name: hw-reference
description: "Use when correcting a hardware or data centre misconception, looking up a power, thermal, bandwidth, latency or efficiency figure, finding the sources, or needing a quick-reference picker — plus the current state of grid power as the binding constraint and high-voltage DC rack distribution. Companion to the other computer hardware and data centres skills."
---

# Computer Hardware and Data Centres: What's Live, Misconceptions, Numbers, and Sources

> **Part 6 of 6** of the *Computer Hardware Engineering, Custom Rigs and Data Centres* reference (plugin `computer-hardware-and-data-centers`), covering §26–§31. Sibling skills: `hw-bottlenecks-cpu-memory-gpu-and-storage` (§0–§5), `hw-interconnect-power-thermals-and-networking` (§6–§9), `hw-specifying-assembly-firmware-tuning-and-benchmarking` (§10–§15), `hw-datacentre-facility-power-cooling-and-efficiency` (§16–§20), `hw-datacentre-network-storage-failure-and-operations` (§21–§25). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The architecture is stable. Two areas moved decisively. See §26 for grid power as the binding constraint, and the shift to high-voltage DC rack distribution.

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
> 1. **⚠️ THE BOTTLENECK IS ALMOST NEVER WHERE YOU THINK** (§1 → `hw-bottlenecks-cpu-memory-gpu-and-storage`, §3 → `hw-bottlenecks-cpu-memory-gpu-and-storage`, §26.1). **It moves.
>    It has gone from clock speed to memory to packaging to — currently — the electrical
>    substation. Optimizing the wrong layer is the standard mistake at every scale.**
> 2. **⚠️ MEMORY, NOT COMPUTE, GOVERNS REAL PERFORMANCE** (§3 → `hw-bottlenecks-cpu-memory-gpu-and-storage`). **The gap between
>    processor speed and memory latency is the single most important fact in computer
>    architecture, and most "slow" systems are memory-bound.**
> 3. **⚠️ POWER AND HEAT ARE THE SAME NUMBER** (§8 → `hw-interconnect-power-thermals-and-networking`, §18 → `hw-datacentre-facility-power-cooling-and-efficiency`). **Essentially all electrical
>    power into a computer leaves as heat. Every watt you draw is a watt you must remove,
>    and at scale that equivalence dominates the entire building.**

---

## §26. What's Live — checked August 2026

### 26.1 ⚠️ The bottleneck moved to the substation
**⚠️ §1 → `hw-bottlenecks-cpu-memory-gpu-and-storage`'s migration completing its latest step — and this is now the primary constraint on
whether AI infrastructure gets built at all.**

- **⚠️ THE SHIFT.** ⚠️ **Through 2023–24 the constraint was chips and packaging (see a
  semiconductor reference §27.2). Reporting through 2026 is consistent that GPU
  availability has improved measurably while the grid has not caught up — power capacity is
  now the more pressing constraint for new deployments.**
- **⚠️ THE QUEUE.** ⚠️ **US interconnection queues reportedly contained around 2,600 GW of
  proposed generation and storage in early 2026, with wait times of five years or more.**
  ⚠️ **Lawrence Berkeley National Laboratory research is cited finding interconnection wait
  times have more than doubled over fifteen years, averaging around five years.** ⚠️ **One
  analysis notes only about a quarter of active queue capacity nationally has an executed
  or draft interconnection agreement — meaning most has no confirmed timeline at all.**
  ⚠️ **In ERCOT, a reported 410 GW large-load queue is 87% data centres.**
- **⚠️ EQUIPMENT IS THE SECOND WALL, and it is physical rather than procedural.**
  ⚠️ **Wood Mackenzie is cited reporting power and distribution transformer supply
  shortfalls of 30% and 10% respectively in 2025, with large power transformer lead times
  averaging 128 weeks in Q2 2025 and generator step-up transformers 144 weeks.**
  ⚠️ **Substations, switchgear and transmission are named alongside.**
- **⚠️ THE DEMAND PICTURE.** ⚠️ **The IEA is cited projecting global data centre electricity
  consumption rising from 415 TWh in 2024 toward 945 TWh by 2030; Goldman Sachs Research is
  cited forecasting US data centre demand from 31 GW in 2025 to 66 GW by 2027.**
  ⚠️ **NERC has warned that roughly half of the continental US faces elevated reliability
  risk as early as 2026 from capacity shortfalls and delayed transmission.**

> **⚠️ GOTCHA — the timescale mismatch is the whole problem, and no amount of capital fixes
> it directly.** ⚠️ **IT hardware supply chains can scale in 12–24 months; grid upgrades and
> heavy electrical equipment run on multi-year to decadal cycles.** **⚠️ So money arriving
> faster does not make transformers arrive faster.**
> ⚠️ **The observed responses are telling: developers advancing projects with ON-SITE
> natural gas generation (the IEA reported this in April 2026), operators becoming de facto
> energy companies, relocation to regions with surplus capacity even where fibre is less
> mature, and regulatory attention — the DOE reportedly directed FERC to expedite large-load
> interconnection by 30 April 2026.**
> **⚠️ One genuinely interesting mitigation: DNV's study of the Dutch network suggests
> INTERRUPTIBLE "emergency lane" connections — accepting occasional planned curtailment —
> could unlock 5–15% additional capacity in congested areas without compromising system
> security.** ⚠️ **Demand flexibility is cheaper than new transmission and is
> underexploited.**

**⚠️ Sourcing caution: much of this comes from data centre developers, consultancies and
infrastructure investors who benefit from the scarcity narrative.** ⚠️ **I anchored on IEA,
LBNL, NERC and Wood Mackenzie figures as cited, and note that the demand projections in
particular have a poor forecasting track record in this sector.**

### 26.2 ⚠️ Rack power density and the move to 800 VDC
**⚠️ §17 → `hw-datacentre-facility-power-cooling-and-efficiency`'s distribution chain being redesigned — and it is a direct application of the
I²R physics in an electromagnetism reference.**

- **⚠️ THE DENSITY TRAJECTORY.** ⚠️ **Conventional racks draw perhaps 5–10 kW.**
  ⚠️ **Reported figures: Hopper-era AI racks around 40 kW; GB200 NVL72 at 120–130 kW;
  GB300 NVL72 at 132–142 kW; Vera Rubin VR200 NVL72 at roughly 190–230 kW; and the 2027
  Rubin Ultra "Kyber" rack specified at around 600 kW, with 1 MW-class behind it.**
- **⚠️ WHY 48 V BREAKS — and this is straightforward physics, not a vendor argument.**
  ⚠️ **Delivering 120 kW at 48 V requires currents exceeding 2.5 kA; one analysis puts the
  NVL72 busbar at more than 3.8 kA at peak.** ⚠️ **NVIDIA states that using 54 VDC for a
  1 MW rack would require up to 200 kg of copper busbar per rack — and up to 200,000 kg of
  rack busbar copper in a single gigawatt facility.**
  ⚠️ **Space is the other limit: NVIDIA notes 54 VDC distribution at megawatt scale would
  consume up to 64U of power shelves, leaving no room for compute.**
- **⚠️ THE ANSWER IS HIGHER VOLTAGE, LOWER CURRENT.** ⚠️ **800 VDC distribution to the rack,
  with AC/DC conversion moved OUT of the IT rack into an adjacent "SIDECAR" cabinet.**
  ⚠️ **That returns the 8–16 rack units power conversion previously consumed, and lets
  power capacity be managed independently of compute capacity.**
- **⚠️ The ecosystem is broad and real**: ⚠️ **ABB, Eaton, GE Vernova, Hitachi Energy,
  Mitsubishi Electric, Schneider Electric, Siemens, Vertiv, TI, Infineon, Navitas and ST
  are all named developing 800 VDC hardware — and note the power semiconductors involved
  are wide-bandgap GaN and SiC parts** (see an electromagnetism reference §26.2).
  ⚠️ **Vertiv's 800 VDC portfolio was reported planned for H2 2026.**

> **⚠️ GOTCHA — 800 VDC is NOT YET REQUIRED, and the honest analysis says so.** ⚠️ **One
> assessment notes the chip generations ramping in late 2026 and 2027 top out around
> 180–220 kW per rack, which three-phase AC can still deliver without hitting conductor
> sizing limits — making early adoption "voluntary future-proofing, not a forced response
> to a hardware constraint."**
> ⚠️ **The forcing function arrives at 400 kW and above.** **⚠️ Expect a retrofit era first,
> layering HVDC power racks onto existing white space without replacing transformers, UPS
> or switchgear.**
> **⚠️ And note the safety consequence: 800 VDC to the IT rack raises insulation, creepage
> and clearance requirements beyond three-phase AC practice, and DC arcs are harder to
> extinguish than AC** (see an electromagnetism reference §23). ⚠️ **There are also
> competing 800 VDC standards, unipolar and bipolar, which differ in exactly these
> respects.**

**⚠️ The cooling consequence is not optional either**: ⚠️ **air handles roughly 30–40 kW per
rack with optimized design; direct-to-chip liquid extends to 60–120 kW; and GB200 NVL72
class needs over 120 kW of cooling capacity.** ⚠️ **Above that, all-liquid is mandatory —
which is why §18 → `hw-datacentre-facility-power-cooling-and-efficiency`'s liquid section is now the default rather than the exception.**
**⚠️ Sourcing note: nearly all of this comes from NVIDIA and its power-infrastructure
partners, who are selling the transition.** ⚠️ **The PHYSICS (I²R, copper mass, rack unit
consumption) is checkable and solid; the density roadmap figures are vendor projections and
I have marked them as reported.**

---

## §27. Misconceptions

| Misconception | Correction |
|---|---|
| More GHz means faster | ⚠️ **Instructions × CPI × cycle time. Three levers** (§2 → `hw-bottlenecks-cpu-memory-gpu-and-storage`) |
| The CPU is usually the bottleneck | ⚠️ **Most "slow" is memory-bound** (§3 → `hw-bottlenecks-cpu-memory-gpu-and-storage`) |
| Faster RAM is a big upgrade | ⚠️ **Capacity matters; speed is usually single-digit %** (§3 → `hw-bottlenecks-cpu-memory-gpu-and-storage`) |
| RAM runs at its advertised speed | ⚠️ **Not until you enable XMP/EXPO** (§12 → `hw-specifying-assembly-firmware-tuning-and-benchmarking`) |
| RAM slot choice doesn't matter | ⚠️ **Wrong slots silently halve bandwidth** (§11 → `hw-specifying-assembly-firmware-tuning-and-benchmarking`) |
| GPU TOPS figures are comparable | ⚠️ **Check the precision they're quoted at** (§4 → `hw-bottlenecks-cpu-memory-gpu-and-storage`) |
| GPUs are compute-limited | ⚠️ **Most real kernels are bandwidth-bound** (§4 → `hw-bottlenecks-cpu-memory-gpu-and-storage`) |
| RAID is a backup | ⚠️ **It survives drive failure, not deletion or ransomware** (§5 → `hw-bottlenecks-cpu-memory-gpu-and-storage`) |
| SSD benchmarks reflect sustained speed | ⚠️ **SLC cache exhaustion changes everything** (§5 → `hw-bottlenecks-cpu-memory-gpu-and-storage`) |
| Buy double the PSU wattage | ⚠️ **Efficiency peaks mid-load; transients matter more** (§7 → `hw-interconnect-power-thermals-and-networking`) |
| PSU cables are interchangeable | ⚠️ **Modular pinouts are NOT standardized** (§7 → `hw-interconnect-power-thermals-and-networking`) |
| Liquid cooling creates cooling | ⚠️ **It moves heat. The radiator still rejects to air** (§8 → `hw-interconnect-power-thermals-and-networking`) |
| Throttling means something is wrong | ⚠️ **It's the design. Better cooling IS performance** (§8 → `hw-interconnect-power-thermals-and-networking`) |
| Overclocking is free performance | ⚠️ **It consumes rated device lifetime** (§13 → `hw-specifying-assembly-firmware-tuning-and-benchmarking`, §23 → `hw-datacentre-network-storage-failure-and-operations`) |
| Average FPS describes the experience | ⚠️ **1% and 0.1% lows are what you feel** (§15 → `hw-specifying-assembly-firmware-tuning-and-benchmarking`) |
| Mean latency describes a service | ⚠️ **p99 is what users notice** (§15 → `hw-specifying-assembly-firmware-tuning-and-benchmarking`) |
| Tier III means certified | ⚠️ **Usually claimed, rarely certified. Ask** (§16 → `hw-datacentre-facility-power-cooling-and-efficiency`) |
| Redundancy means maintainable | ⚠️ **Different properties. N+1 ≠ concurrently maintainable** (§17 → `hw-datacentre-facility-power-cooling-and-efficiency`) |
| Outages come from hardware failure | ⚠️ **Mostly power transfer, software and change** (§17 → `hw-datacentre-facility-power-cooling-and-efficiency`, §23 → `hw-datacentre-network-storage-failure-and-operations`) |
| Low PUE means efficient | ⚠️ **Worse IT efficiency IMPROVES PUE. It's gameable** (§19 → `hw-datacentre-facility-power-cooling-and-efficiency`) |
| Data centres should run cold | ⚠️ **ASHRAE ranges are wider than assumed; over-cooling is costly** (§18 → `hw-datacentre-facility-power-cooling-and-efficiency`) |
| Eleven nines means your data is safe | ⚠️ **Models drive failure, not operator error** (§22 → `hw-datacentre-network-storage-failure-and-operations`) |
| Failures are independent | ⚠️ **Same batch, firmware, rack, feed. They correlate** (§23 → `hw-datacentre-network-storage-failure-and-operations`) |
| GPUs are the AI constraint now | ⚠️ **Grid power and interconnection are** (§26.1) |
| Money can accelerate power delivery | ⚠️ **Transformer lead times are ~128 weeks** (§26.1) |
| 800 VDC is needed today | ⚠️ **Not until ~400 kW racks. Currently future-proofing** (§26.2) |
| Higher rack voltage is just efficiency | ⚠️ **It's copper mass and rack space — 200 kg of busbar** (§26.2) |

---

## §28. Numbers

```
⚠️ Latency ladder  ⚠️ L1 ~4 cyc · L3 ~40 · DRAM ~200-300 ·
                   NVMe ~100,000+ cycles
⚠️ Cache line  typically 64 bytes
⚠️ PSU efficiency peak  ⚠️ ~40-60% load
⚠️ Rack unit  1U = 44.45 mm · common 42U/48U
⚠️ PUE  1.0 ideal; hyperscale approaches it, legacy far worse
⚠️ Air cooling limit  ⚠️ ~30-40 kW/rack optimized
⚠️ Direct-to-chip liquid  ⚠️ ~60-120 kW/rack
⚠️ Conventional rack  5-10 kW
⚠️ Rack density (reported)  ⚠️ Hopper ~40 kW · GB200 NVL72 120-130 ·
   GB300 NVL72 132-142 · VR200 ~190-230 · Kyber ~600 · then ~1 MW
⚠️ 120 kW at 48 V  ⚠️ >2.5 kA · NVL72 busbar >3.8 kA peak
⚠️ 1 MW rack at 54 VDC  ⚠️ up to 200 kg copper busbar
⚠️ Sidecar recovers  ⚠️ 8-16U previously used by power conversion
⚠️ US interconnection queue  ⚠️ ~2,600 GW; ~5 yr average wait
⚠️ ERCOT large-load queue  ⚠️ 410 GW, 87% data centres
⚠️ Transformer lead times  ⚠️ ~128 weeks (LPT), ~144 (GSU), Q2 2025
⚠️ Data centre electricity  ⚠️ 415 TWh (2024) → ~945 TWh (2030), IEA
⚠️ US DC demand  ⚠️ 31 GW (2025) → 66 GW (2027), Goldman Sachs
```

---

## §29. Sources

| Source | Why |
|---|---|
| **Hennessy & Patterson, *Computer Architecture*** | ⚠️ **The standard. §2–§4 → `hw-bottlenecks-cpu-memory-gpu-and-storage`** |
| **Patterson & Hennessy, *Computer Organization and Design*** | The accessible entry |
| **Drepper, "What Every Programmer Should Know About Memory"** | ⚠️ **§3 → `hw-bottlenecks-cpu-memory-gpu-and-storage`, free and excellent** |
| **Bryant & O'Hallaron, *Computer Systems: A Programmer's Perspective*** | Bridges hardware and software |
| **ASHRAE TC 9.9 Thermal Guidelines** | ⚠️ **§18 → `hw-datacentre-facility-power-cooling-and-efficiency`, the authority** |
| **Uptime Institute Tier Standard and outage reports** | ⚠️ **§16 → `hw-datacentre-facility-power-cooling-and-efficiency`, §23 → `hw-datacentre-network-storage-failure-and-operations` — the outage data is genuinely useful** |
| **Open Compute Project specifications** | ⚠️ **§20 → `hw-datacentre-facility-power-cooling-and-efficiency`, free and detailed** |
| **Barroso, Hölzle & Ranganathan, *The Datacenter as a Computer*** | ⚠️ **§16–§25 → `hw-datacentre-facility-power-cooling-and-efficiency`, `hw-datacentre-network-storage-failure-and-operations`. Free online** |
| **Google SRE Book** | ⚠️ **§23–§24 → `hw-datacentre-network-storage-failure-and-operations`, free** |
| **LBNL and IEA energy analyses** | ⚠️ **§26.1 — the disinterested sources** |
| **ServeTheHome, SemiAnalysis, DCD** | ⚠️ **Current practice; read as interested** |

---

## §30. Quick Reference

### 30.1 Picker
| Question | Where |
|---|---|
| What should I upgrade? | ⚠️ **Measure first. Find the actual bottleneck** (§1 → `hw-bottlenecks-cpu-memory-gpu-and-storage`, §15 → `hw-specifying-assembly-firmware-tuning-and-benchmarking`) |
| Why is my code slow? | ⚠️ **Suspect memory access patterns** (§3 → `hw-bottlenecks-cpu-memory-gpu-and-storage`) |
| How much RAM do I need? | ⚠️ **Enough. Beyond that, capacity beats speed** (§3 → `hw-bottlenecks-cpu-memory-gpu-and-storage`) |
| How big a PSU? | ⚠️ **Not double. Check transient handling** (§7 → `hw-interconnect-power-thermals-and-networking`) |
| Is my system throttling? | ⚠️ **Monitor under sustained load** (§8 → `hw-interconnect-power-thermals-and-networking`, §14 → `hw-specifying-assembly-firmware-tuning-and-benchmarking`) |
| Random crashes | ⚠️ **PSU transients, RAM (test overnight), XMP** (§14 → `hw-specifying-assembly-firmware-tuning-and-benchmarking`) |
| Build won't POST | ⚠️ **CPU 8-pin, reseat RAM, debug LEDs** (§14 → `hw-specifying-assembly-firmware-tuning-and-benchmarking`) |
| Is this benchmark trustworthy? | ⚠️ **Check lows, duration, config, repeats** (§15 → `hw-specifying-assembly-firmware-tuning-and-benchmarking`) |
| How do I size a facility? | ⚠️ **Power first — it runs out first** (§17 → `hw-datacentre-facility-power-cooling-and-efficiency`, §24 → `hw-datacentre-network-storage-failure-and-operations`, §26.1) |
| Is a low PUE good? | ⚠️ **Only alongside work per watt** (§19 → `hw-datacentre-facility-power-cooling-and-efficiency`) |
| Can this rack take an AI node? | ⚠️ **Power AND cooling AND floor loading** (§20 → `hw-datacentre-facility-power-cooling-and-efficiency`, §26.2) |
| Why did the data centre go down? | ⚠️ **Statistically: power transfer, or a change** (§17 → `hw-datacentre-facility-power-cooling-and-efficiency`, §23 → `hw-datacentre-network-storage-failure-and-operations`) |
| Why can't we just build more? | ⚠️ **Interconnection queue and transformers** (§26.1) |

### 30.2 Build and deployment checks
- [ ] ⚠️ **Workload identified and the likely bottleneck named** (§1 → `hw-bottlenecks-cpu-memory-gpu-and-storage`, §10 → `hw-specifying-assembly-firmware-tuning-and-benchmarking`)
- [ ] ⚠️ **Components balanced — no starved GPU, no starved CPU** (§10 → `hw-specifying-assembly-firmware-tuning-and-benchmarking`)
- [ ] ⚠️ **PSU sized on transients, not just continuous rating** (§7 → `hw-interconnect-power-thermals-and-networking`)
- [ ] ⚠️ **RAM in correct slots; XMP/EXPO enabled and verified** (§11 → `hw-specifying-assembly-firmware-tuning-and-benchmarking`, §12 → `hw-specifying-assembly-firmware-tuning-and-benchmarking`)
- [ ] Every power connector fully seated (§7 → `hw-interconnect-power-thermals-and-networking`, §11 → `hw-specifying-assembly-firmware-tuning-and-benchmarking`)
- [ ] ⚠️ **Sustained-load thermal test, not just idle** (§8 → `hw-interconnect-power-thermals-and-networking`, §14 → `hw-specifying-assembly-firmware-tuning-and-benchmarking`)
- [ ] Memory tested overnight before trusting the system (§14 → `hw-specifying-assembly-firmware-tuning-and-benchmarking`)
- [ ] ⚠️ **Backups exist and a restore has been TESTED** (§5 → `hw-bottlenecks-cpu-memory-gpu-and-storage`)
- [ ] **At facility scale, additionally:**
- [ ] ⚠️ **Power availability confirmed with a real timeline** (§26.1)
- [ ] ⚠️ **Cooling capacity matched to rack density, with liquid path planned** (§18 → `hw-datacentre-facility-power-cooling-and-efficiency`, §26.2)
- [ ] ⚠️ **Redundancy AND concurrent maintainability distinguished** (§17 → `hw-datacentre-facility-power-cooling-and-efficiency`)
- [ ] ⚠️ **Generator and battery testing scheduled and actually done** (§17 → `hw-datacentre-facility-power-cooling-and-efficiency`)
- [ ] ⚠️ **Fault domains and correlated-failure assumptions examined** (§23 → `hw-datacentre-network-storage-failure-and-operations`)
- [ ] ⚠️ **Change management treated as a reliability control** (§23 → `hw-datacentre-network-storage-failure-and-operations`)

---

## §31. Method

**§1–§25 → `hw-bottlenecks-cpu-memory-gpu-and-storage`, `hw-interconnect-power-thermals-and-networking`, `hw-specifying-assembly-firmware-tuning-and-benchmarking`, `hw-datacentre-facility-power-cooling-and-efficiency`, `hw-datacentre-network-storage-failure-and-operations` rests on settled computer architecture and mature facility practice** — **the
memory hierarchy, Amdahl's law, thermal paths, UPS topologies, Tier definitions, leaf-spine
networking and the failure literature.** ⚠️ **None needed verification; the processor-memory
gap has been the central architectural fact for thirty years.**

**Two searches were run in August 2026**, on **data centre power constraints** and **rack
power architecture** — ⚠️ **the first because §1 → `hw-bottlenecks-cpu-memory-gpu-and-storage`'s bottleneck migration reached a new step
that changes what can be built at all, the second because §17 → `hw-datacentre-facility-power-cooling-and-efficiency`'s distribution chain is being
redesigned in a way that directly applies an electromagnetism reference's I²R physics.**

**Confidence.** **High** in §3 → `hw-bottlenecks-cpu-memory-gpu-and-storage` and §8 → `hw-interconnect-power-thermals-and-networking`, which are the sections I'd most want read.
⚠️ **The latency ladder is the single most useful thing here — a main memory access costs
hundreds of cycles, during which a core could have executed hundreds of instructions, and
that fact explains most real-world performance behaviour.** ⚠️ **§8 → `hw-interconnect-power-thermals-and-networking`'s identity between power
draw and cooling requirement is the second, because it scales unchanged from a desk fan to
a hundred-megawatt facility and it is why §26.1 and §26.2 are the same story viewed at
different points in the chain.** **§7 → `hw-interconnect-power-thermals-and-networking`'s transient-response point is the practical one that
saves the most grief in custom builds.**

**Moderate-to-high** on §26.1. ⚠️ **The structural claim — that grid interconnection and
heavy electrical equipment have displaced chips as the binding constraint — is consistent
across every source and is corroborated by the equipment lead-time data, which is a
physical fact rather than a forecast.** ⚠️ **The specific figures (2,600 GW queue, 410 GW
ERCOT, 128/144-week transformer lead times) are cited to LBNL, Wood Mackenzie and grid
operators through secondary reporting and I've attributed them.** **⚠️ I'd treat the demand
PROJECTIONS with more scepticism than the constraint data — this sector's forecasts have
been revised repeatedly, and most of the commentary comes from developers and investors who
benefit from a scarcity narrative.**

**High** on §26.2's physics, which is checkable arithmetic: ⚠️ **120 kW at 48 V is over
2.5 kA, and NVIDIA's own figures of up to 200 kg of copper busbar per megawatt rack and 64U
of power shelves at 54 VDC are the reason the architecture must change.**
⚠️ **The density roadmap figures are vendor projections and I've marked them reported.**
**⚠️ The most useful corrective in that section is the analysis noting 800 VDC is NOT yet
required — the 2026–27 generations at 180–220 kW remain within three-phase AC's reach, so
current adoption is voluntary future-proofing rather than a forced response.** ⚠️ **Nearly
every source here sells the transition, which is exactly why that dissenting point is worth
carrying.**
