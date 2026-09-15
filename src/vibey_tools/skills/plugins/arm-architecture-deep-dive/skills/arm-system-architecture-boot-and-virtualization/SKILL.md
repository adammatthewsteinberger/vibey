---
name: arm-system-architecture-boot-and-virtualization
description: "Use for the system level around the core: big.LITTLE and DynamIQ heterogeneous topologies and their scheduling consequences, interrupts and timers with the GIC generations, interconnect and the AMBA protocol family with coherency, boot and firmware on ARM including the trusted firmware stages and how it differs from x86, and virtualization with stage-2 translation and the hypervisor exception level."
---

# ARM: big.LITTLE and DynamIQ, Interrupts and Timers, Interconnect, Boot and Firmware on ARM, and Virtualization

> **Part 4 of 6** of the *ARM: A Deep Dive* reference (plugin `arm-architecture-deep-dive`), covering §16–§20. Sibling skills: `arm-what-arm-is-licensing-families-and-isa-generations` (§0–§4), `arm-aarch64-exception-levels-memory-model-and-mmu` (§5–§9), `arm-vectors-atomics-numerics-and-security-architecture` (§10–§15), `arm-cortex-m-toolchain-porting-and-performance` (§21–§25), `arm-reference` (§26–§31). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The architecture is documented and stable. Two things moved decisively. See §26 → `arm-reference` for Arm's business model, and its actual market position.

> **⚠️ ARM is a business model as much as an instruction set, and you cannot understand the
> architecture without understanding that.** ⚠️ **The design choices — modularity, optional
> extensions, profiles, strict architectural compliance — exist because the ISA has to be
> implementable by dozens of independent companies at wildly different power and
> performance points.**
>
> **Builds on a microarchitecture reference (§20 ISA design, §8 → `arm-aarch64-exception-levels-memory-model-and-mmu` memory consistency) and a
> semiconductor reference. Complements a digital-logic reference for the boot chain and a
> computer-hardware reference for the datacentre context.**
>
> **⚠️ GOTCHA** boxes mark where ARM differs from x86 in ways that break assumptions.
>
> **The three ideas that organize this document:**
> 1. **⚠️ THE ARCHITECTURE IS A CONTRACT, NOT A CHIP** (§1 → `arm-what-arm-is-licensing-families-and-isa-generations`, §4 → `arm-what-arm-is-licensing-families-and-isa-generations`). **"ARM" names a
>    specification that Apple, Qualcomm, Amazon and a microcontroller vendor all implement
>    completely differently. Statements about "ARM performance" are usually category
>    errors.**
> 2. **⚠️ THE WEAK MEMORY MODEL IS THE MOST CONSEQUENTIAL DIFFERENCE FROM x86** (§8 → `arm-aarch64-exception-levels-memory-model-and-mmu`, §23 → `arm-cortex-m-toolchain-porting-and-performance`).
>    **Concurrent code that is correct on x86-TSO can be silently broken on ARM with no
>    source change. This is the single most common real porting failure and it produces
>    intermittent bugs.**
> 3. **⚠️ SECURITY IS ARCHITECTED, NOT BOLTED ON** (§13–§15 → `arm-vectors-atomics-numerics-and-security-architecture`). **TrustZone, pointer
>    authentication, BTI, MTE and CCA are architectural features with silicon support —
>    which is genuinely different from mitigation-by-software, and it is a large part of
>    why ARM won mobile.**

---

## §16. big.LITTLE and DynamIQ

**⚠️ Heterogeneous cores sharing one ISA** — ⚠️ **the property that makes it work is that
all cores are architecturally identical, so a thread can migrate mid-execution.**
> **⚠️ GOTCHA — and this is exactly what Intel's hybrid designs got wrong initially.**
> ⚠️ **If the big and little cores support DIFFERENT feature sets, a thread using a feature
> present only on one cannot migrate — which is why Intel disabled AVX-512 on its
> performance cores when the efficiency cores lacked it.** **⚠️ ARM's insistence on
> architectural uniformity across a DynamIQ cluster avoids the problem by construction.**

**⚠️ The scheduling problem is the hard part** — ⚠️ **the OS must decide placement, and
Energy Aware Scheduling uses a power model to do it.** ⚠️ **Getting this wrong produces the
classic symptom of a fast chip that feels slow.**
**⚠️ DynamIQ** replaced the original cluster arrangement, ⚠️ **allowing mixed core types in
one coherent cluster with shared L3 and per-core power control.**

---

## §17. Interrupts and Timers

**⚠️ The GIC (Generic Interrupt Controller)** — ⚠️ **GICv2, v3 and v4, with v3+ using system
registers rather than MMIO for the CPU interface, which is substantially faster.**
**⚠️ Interrupt types**: ⚠️ **SPI (shared peripheral), PPI (private per-core), SGI
(software-generated, for inter-processor interrupts), and LPI (message-signalled, via the
ITS — which is how MSI-X scales on ARM servers).**
**⚠️ Affinity routing and priority**, ⚠️ **and GICv4's direct injection of virtual
interrupts into guests without hypervisor involvement** (§20).
**⚠️ The Generic Timer** is architected — ⚠️ **a system counter plus per-core comparators,
with virtual timer offsets for guests, which is why timekeeping on ARM VMs is cleaner than
the x86 history of TSC problems.**

---

## §18. Interconnect

**⚠️ AMBA** is the family of bus specifications, ⚠️ **and it is as much a part of ARM's
ecosystem lock-in as the ISA — third-party IP is built to talk AMBA.**
⚠️ **AXI (high performance, channel-based, out-of-order), AHB and APB (simple, peripheral),
⚠️ ACE (adds cache coherency), and ⚠️ CHI (Coherent Hub Interface — the scalable
mesh-oriented protocol used in Neoverse-class designs).**
**⚠️ Coherent Mesh Networks** scale to very high core counts, ⚠️ **and interconnect design
is a large share of why two chips using the same cores perform differently.**
**⚠️ External coherency**: ⚠️ **CCIX historically, and now CXL** (see a microarchitecture
reference §17).
**⚠️ SMMU/IOMMU** for device address translation and DMA protection (§20).

---

## §19. ⚠️ Boot and Firmware on ARM

> **⚠️ Genuinely different from the x86 world, and a common source of confusion. See a
> digital-logic reference §21 for the general boot model.**
```
⚠️ ⚠️ THERE IS NO ARCHITECTURAL EQUIVALENT OF THE PC BIOS.
   ⚠️ x86 has decades of de-facto platform standardization; ARM
   platforms historically each booted their own way, which is
   why "just install Linux on it" is easy on a PC and hard on
   an ARM board
⚠️ THE STANDARD BOOT CHAIN  ⚠️ BL1 (ROM) → BL2 → ⚠️ BL31 (EL3
   RUNTIME — the secure monitor, stays resident) → BL32
   (optional TEE) → ⚠️ BL33 (the normal-world bootloader:
   U-Boot, EDK2/UEFI)
⚠️ ⚠️ TRUSTED FIRMWARE-A (TF-A) is the open reference
   implementation of the secure world and monitor, and it is
   what most platforms actually run
⚠️ ⚠️ PSCI (Power State Coordination Interface)  ⚠️ the
   standardized SMC-based interface by which the OS asks
   firmware to power cores on and off. ⚠️ This is how CPU
   hotplug and idle work portably
⚠️ ⚠️ THE STANDARDIZATION EFFORT THAT CHANGED THINGS
   ⚠️ SBSA/BSA (hardware requirements) and SBBR/BBR (firmware
   requirements), under SystemReady certification
   ⚠️ ⚠️ THIS IS WHY ARM SERVERS BOOT A GENERIC OS IMAGE THE WAY
   A PC DOES, AND MOST ARM SBCs AND PHONES DO NOT. ⚠️ The
   difference is certification, not architecture
⚠️ DEVICE TREE vs ACPI  ⚠️ embedded platforms use device tree;
   ⚠️ SystemReady servers use ACPI — and the split is a
   long-running ecosystem argument
```

---

## §20. Virtualization

**⚠️ EL2 is architected for it** (§7 → `arm-aarch64-exception-levels-memory-model-and-mmu`), ⚠️ **which is the structural advantage over x86's
retrofit.**
**⚠️ Stage 2 translation** (§9 → `arm-aarch64-exception-levels-memory-model-and-mmu`) gives guest-physical to host-physical translation in
hardware.
**⚠️ Trap and emulate** via HCR_EL2 bits — ⚠️ **the hypervisor chooses precisely which guest
operations trap.**
**⚠️ Virtual interrupts** through the GIC (§17), ⚠️ **and GICv4's direct injection removes
the hypervisor from the interrupt path entirely for many cases.**
**⚠️ VHE (Virtualization Host Extensions, ARMv8.1)** is the pragmatic addition: ⚠️ **it lets
a host kernel designed to run at EL1 run at EL2 with minimal changes, which is what made
KVM on ARM efficient rather than a split-mode compromise.**
**⚠️ SMMU** for device passthrough with DMA isolation.
**⚠️ Nested virtualization** is supported in later revisions and is much harder.
