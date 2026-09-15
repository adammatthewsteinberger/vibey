---
name: hw-specifying-assembly-firmware-tuning-and-benchmarking
description: "Use when building or fixing a machine: specifying a build from the workload backwards, assembly practice, firmware and boot including UEFI and the settings that actually matter, tuning and overclocking assessed honestly against the risk, troubleshooting method for intermittent and hard faults, and benchmarking that measures the thing you care about rather than a number."
---

# Computer Hardware and Data Centres: Specifying a Build, Assembly, Firmware and Boot, Tuning and Overclocking, Troubleshooting, and Benchmarking

> **Part 3 of 6** of the *Computer Hardware Engineering, Custom Rigs and Data Centres* reference (plugin `computer-hardware-and-data-centers`), covering §10–§15. Sibling skills: `hw-bottlenecks-cpu-memory-gpu-and-storage` (§0–§5), `hw-interconnect-power-thermals-and-networking` (§6–§9), `hw-datacentre-facility-power-cooling-and-efficiency` (§16–§20), `hw-datacentre-network-storage-failure-and-operations` (§21–§25), `hw-reference` (§26–§31). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §10. Specifying a Build

> **⚠️ Start from the WORKLOAD, not from a parts list. Almost every wasted pound in a
> custom build comes from balancing the machine wrong.**
```
⚠️ MATCH THE COMPONENT TO THE BOTTLENECK (§1)
   ⚠️ Gaming  ⚠️ GPU-dominant; CPU matters at high frame rates and
      low resolution; ⚠️ VRAM capacity increasingly binding
   ⚠️ Content creation  cores, RAM CAPACITY, fast storage
   ⚠️ Software development  ⚠️ single-thread speed for many tools,
      cores for compilation, RAM for containers and VMs
   ⚠️ ML  ⚠️ VRAM CAPACITY FIRST — a model that doesn't fit doesn't
      run — then bandwidth, then compute
   ⚠️ Workstation/CAD  certified drivers, ECC where correctness matters
   ⚠️ Home server/NAS  ⚠️ reliability, ECC, drive bays, low idle power
⚠️ THE BALANCE PRINCIPLE  ⚠️ a top GPU with an inadequate CPU or
   insufficient RAM wastes most of what you paid for
⚠️ WHERE MONEY IS USUALLY WASTED  ⚠️ oversized PSU (§7) · RGB ·
   marginal RAM speed · exotic cooling for a part that isn't
   thermally limited · high-end board features you'll never use
⚠️ WHERE IT IS USUALLY WELL SPENT  ⚠️ a good PSU · adequate RAM
   capacity · a decent monitor (⚠️ which outlasts the whole build)
   · quiet cooling · a case you can work in
```

---

## §11. Assembly

**⚠️ ESD precautions** (see a cryptography-adjacent electronics reference on static —
⚠️ **high voltage, tiny energy, harmless to you and destructive to semiconductors**): work
on a hard surface, ground yourself, handle boards by the edges.
**⚠️ The order that saves rework**: ⚠️ **CPU, cooler backplate, RAM and M.2 into the board
BEFORE it goes in the case; then PSU; then board; then GPU last.**
**⚠️ The specific care points**: ⚠️ **CPU socket orientation and never touching LGA pins;
⚠️ RAM in the correct slots for dual channel — usually A2/B2, and getting this wrong
halves memory bandwidth silently; ⚠️ standoffs correct and no extras shorting the board;
⚠️ every power connector FULLY seated (§7 → `hw-interconnect-power-thermals-and-networking`); and cable management for airflow.**
**⚠️ Test outside the case first** if anything is uncertain — ⚠️ **it takes minutes and
saves a full disassembly.**

---

## §12. Firmware and Boot

**⚠️ UEFI replaced BIOS** — ⚠️ **GPT partitioning, larger disks, faster boot, and Secure
Boot.**
**⚠️ POST and the boot chain**: ⚠️ **firmware → bootloader → kernel → init, and knowing this
sequence is what lets you diagnose where a boot failure occurs.**
**⚠️ Settings that actually matter**: ⚠️ **XMP/EXPO to run memory at its rated speed
(⚠️ memory ships at JEDEC defaults and does NOT run at advertised speed until you enable
it — an extremely common oversight), resizable BAR, virtualization extensions, fan curves,
and boot order.**
**⚠️ Firmware updates** fix real bugs including microcode and stability issues — ⚠️ **and a
failed flash can brick a board, so use the vendor's recovery mechanism where available and
don't update without reason.**
**⚠️ Secure Boot and TPM** underpin measured boot and disk encryption (see a cryptography
reference §15).

---

## §13. Tuning and Overclocking, Honestly

**⚠️ The modern reality**: ⚠️ **parts already boost to their limits automatically, so
headroom is far smaller than a decade ago and manual overclocking often loses to the
stock algorithm.**
**⚠️ What actually pays**: ⚠️ **UNDERVOLTING (⚠️ frequently gives equal performance at lower
temperature and noise — the best-value tuning available), memory timing tuning on some
platforms, fan curve tuning, and improving cooling** (§8 → `hw-interconnect-power-thermals-and-networking`).
**⚠️ Stability testing must be workload-diverse** — ⚠️ **a system stable under one stress
test can fail under another, and instability manifests as silent data corruption, not
just crashes.**
**⚠️ The honest costs** (see a semiconductor reference §23): ⚠️ **higher voltage and
temperature consume rated device lifetime through electromigration and TDDB, warranties
may be affected, and the performance gain is usually single-digit percent.**

---

## §14. ⚠️ Troubleshooting

```
⚠️ THE METHOD  ⚠️ change ONE thing at a time · bisect · reduce to
   minimum configuration · swap known-good parts · ⚠️ and READ
   THE ACTUAL ERROR before theorizing
⚠️ NO POST  ⚠️ power connectors (especially the CPU 8-pin, the
   most commonly forgotten) · RAM reseat and try ONE stick ·
   standoff short · ⚠️ CMOS clear · debug LEDs or POST codes
   (⚠️ these tell you the stage — use them)
⚠️ RANDOM CRASHES  ⚠️ this is the hardest class. ⚠️ Suspect, in
   rough order: PSU transients (§7) · RAM (⚠️ run MemTest86
   OVERNIGHT — a short pass proves little) · thermals · unstable
   XMP · drivers · storage errors
⚠️ THERMAL THROTTLING  monitor under sustained load, not at idle
⚠️ POOR PERFORMANCE  ⚠️ check XMP enabled · dual channel populated ·
   GPU in the CPU-attached x16 slot · power plan · background load ·
   ⚠️ and confirm which resource is actually saturated (§15)
⚠️ INTERMITTENT  ⚠️ the worst. Log everything; check event logs;
   suspect connections, thermal cycling and marginal power
⚠️ ⚠️ THE PRINCIPLE: SUSPECT WHAT YOU CHANGED, and prefer
   measurement over replacement
```

---

## §15. ⚠️ Benchmarking

> **⚠️ Most published comparisons are misleading, and the errors are systematic rather than
> random.**
**⚠️ Synthetic vs real workload**: ⚠️ **synthetics are repeatable and frequently don't
predict your application; run YOUR workload if you can.**
**⚠️ The methodology errors that matter**: ⚠️ **testing only average FPS while ignoring
1% and 0.1% LOWS (⚠️ which is what actually feels bad); short runs that miss thermal
steady state; run-to-run variance reported without repeats; comparing across different
driver, firmware and OS versions; and ⚠️ CPU tests run at resolutions where the GPU is the
limit, which flattens all CPUs into a meaningless tie.**
**⚠️ Vendor benchmarks** are selected, not falsified — ⚠️ **and the selection is the whole
effect.**
**⚠️ For servers**: ⚠️ **measure TAIL latency (p99, p99.9) rather than mean, because mean
latency hides exactly the behaviour users notice.**
**⚠️ The discipline**: ⚠️ **state the configuration completely, repeat, report variance,
and change one variable at a time** (§14).

---

# PART III — DATA CENTRES
