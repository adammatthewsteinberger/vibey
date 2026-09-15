---
name: arm-what-arm-is-licensing-families-and-isa-generations
description: "Use when orienting on ARM or reading an ARM spec sheet: what the word ARM actually names across the company, the architecture and the cores, the licensing model and why it explains the ecosystem's shape, the Cortex-A, Cortex-R and Cortex-M product families and Neoverse, and the ISA generations from ARMv7 through ARMv9. Includes the router for the whole ARM reference."
---

# ARM: What "ARM" Actually Names, the Licensing Model, Product Families, and ISA Generations

> **Part 1 of 6** of the *ARM: A Deep Dive* reference (plugin `arm-architecture-deep-dive`), covering §0–§4. Sibling skills: `arm-aarch64-exception-levels-memory-model-and-mmu` (§5–§9), `arm-vectors-atomics-numerics-and-security-architecture` (§10–§15), `arm-system-architecture-boot-and-virtualization` (§16–§20), `arm-cortex-m-toolchain-porting-and-performance` (§21–§25), `arm-reference` (§26–§31). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 1. **⚠️ THE ARCHITECTURE IS A CONTRACT, NOT A CHIP** (§1, §4). **"ARM" names a
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

## §0. Routing

| You want... | Go to |
|---|---|
| What "ARM" means | §1 |
| **⚠️ The licensing model** | **§2** |
| Product families | §3 |
| ISA generations | §4 |
| **⚠️ AArch64** | **§5 → `arm-aarch64-exception-levels-memory-model-and-mmu`** |
| Instruction characteristics | §6 → `arm-aarch64-exception-levels-memory-model-and-mmu` |
| **⚠️ Exception levels** | **§7 → `arm-aarch64-exception-levels-memory-model-and-mmu`** |
| **⚠️ The memory model** | **§8 → `arm-aarch64-exception-levels-memory-model-and-mmu`** |
| MMU and translation | §9 → `arm-aarch64-exception-levels-memory-model-and-mmu` |
| **⚠️ NEON, SVE, SME** | **§10 → `arm-vectors-atomics-numerics-and-security-architecture`** |
| Atomics | §11 → `arm-vectors-atomics-numerics-and-security-architecture` |
| Floating point | §12 → `arm-vectors-atomics-numerics-and-security-architecture` |
| **⚠️ TrustZone** | **§13 → `arm-vectors-atomics-numerics-and-security-architecture`** |
| **⚠️ PAC, BTI, MTE** | **§14 → `arm-vectors-atomics-numerics-and-security-architecture`** |
| CCA and realms | §15 → `arm-vectors-atomics-numerics-and-security-architecture` |
| big.LITTLE and DynamIQ | §16 → `arm-system-architecture-boot-and-virtualization` |
| Interrupts and timers | §17 → `arm-system-architecture-boot-and-virtualization` |
| Interconnect | §18 → `arm-system-architecture-boot-and-virtualization` |
| **⚠️ Boot and firmware** | **§19 → `arm-system-architecture-boot-and-virtualization`** |
| Virtualization | §20 → `arm-system-architecture-boot-and-virtualization` |
| **⚠️ Cortex-M** | **§21 → `arm-cortex-m-toolchain-porting-and-performance`** |
| Toolchain and ABI | §22 → `arm-cortex-m-toolchain-porting-and-performance` |
| **⚠️ Porting from x86** | **§23 → `arm-cortex-m-toolchain-porting-and-performance`** |
| Performance analysis | §24 → `arm-cortex-m-toolchain-porting-and-performance` |
| The competition | §25 → `arm-cortex-m-toolchain-porting-and-performance` |
| **What's live** | **§26 → `arm-reference`** |
| Misconceptions, numbers | §27–§28 → `arm-reference` |
| Sources, quick ref, method | §29–§31 → `arm-reference` |

---

## §1. What "ARM" Actually Names

```
⚠️ THE LAYERS, and conflating them causes most confusion
   ⚠️ THE ARCHITECTURE  ⚠️ a specification — ARMv8-A, ARMv9-A.
      ⚠️ Defines instructions, registers, exception model, memory
      model. ⚠️ This is what "ARM" properly names
   ⚠️ THE MICROARCHITECTURE  ⚠️ an implementation — Cortex-X925,
      Neoverse V3, Apple's cores. ⚠️ Same contract, radically
      different execution
   ⚠️ THE PRODUCT  a chip integrating cores with everything else
⚠️ ⚠️ THEREFORE "ARM IS EFFICIENT" IS A CATEGORY ERROR. ⚠️ A
   Cortex-M0 and an Apple performance core share an ISA family
   and essentially nothing else. ⚠️ Efficiency is a property of
   implementations, targets and process nodes — see a
   microarchitecture reference §20, where the conclusion is that
   the ISA was never the barrier
⚠️ THE PROFILES  ⚠️ A (Application — MMU, rich OS) · R (Real-time
   — MPU, determinism) · ⚠️ M (Microcontroller — small, fast
   interrupts, §21)
⚠️ ARCHITECTURAL COMPLIANCE  ⚠️ Arm certifies that an
   implementation matches the spec, which is what makes the
   ecosystem work across dozens of vendors
```

---

# PART I — THE MODEL

## §2. ⚠️ The Licensing Model

```
⚠️ ⚠️ ARM DESIGNS AND LICENSES; IT HISTORICALLY DID NOT
   MANUFACTURE — ⚠️ and as of March 2026 that is no longer
   entirely true (§26.1)
⚠️ THE LICENCE TYPES
   ⚠️ CORE / IMPLEMENTATION LICENCE  ⚠️ use Arm's designed cores
      (Cortex, Neoverse). ⚠️ Most licensees
   ⚠️ ⚠️ ARCHITECTURE LICENCE  ⚠️ design your OWN core
      implementing the ISA. ⚠️ Rare, expensive, and the reason
      Apple, Qualcomm's Oryon and Amazon's designs can differ so
      much while running the same binaries
   ⚠️ ⚠️ CSS (Compute Subsystems)  ⚠️ pre-integrated, validated
      multi-IP blueprints rather than a bare core (§26.1)
⚠️ THE REVENUE STRUCTURE  ⚠️ UPFRONT LICENCE FEE + ⚠️ PER-CHIP
   ROYALTY. ⚠️ The royalty model means Arm's revenue tracks unit
   volume across the whole industry, which is why it appears in
   an enormous number of devices at very low revenue per device
⚠️ ⚠️ THE ARCHITECTURAL CONSEQUENCE  ⚠️ because licensees are
   competitors implementing one contract, the SPEC must be
   precise, extensions must be OPTIONAL and discoverable, and
   compliance must be testable. ⚠️ Compare RISC-V, where
   fragmentation is the standing concern (§25)
⚠️ SOFTBANK ownership, the failed NVIDIA acquisition, and the
   2023 IPO are the corporate context
```

---

## §3. Product Families

**⚠️ Cortex-A** — application processors. ⚠️ **The little/middle/big naming (A5xx / A7xx) and
the X-series as the maximum-performance line.**
**⚠️ Cortex-R** — real-time, ⚠️ **MPU rather than MMU, deterministic interrupt latency, used
in storage controllers, modems and automotive.**
**⚠️ Cortex-M** — microcontrollers (§21 → `arm-cortex-m-toolchain-porting-and-performance`), ⚠️ **the volume leader by unit count by an
enormous margin.**
**⚠️ NEOVERSE** — infrastructure: ⚠️ **V-series (maximum per-core performance), N-series
(balanced, throughput per watt), E-series (efficiency/edge).** ⚠️ **This is where the
datacentre story lives** (§26.2 → `arm-reference`).
**⚠️ Ethos** NPUs, **Mali/Immortalis** GPUs, ⚠️ **CoreLink and CoreSight** for interconnect
and debug.
**⚠️ The naming is genuinely confusing** — ⚠️ **architecture version (ARMv9), core name
(Cortex-A720), and product tier are three independent things, and a new core does not imply
a new architecture version.**

---

# PART II — THE ARCHITECTURE

## §4. ISA Generations

```
⚠️ THE HISTORY THAT STILL MATTERS
   ⚠️ ARMv7-A  32-bit, ⚠️ Thumb-2 (mixed 16/32-bit encoding for
      code density — ⚠️ a genuine advantage in embedded)
   ⚠️ ⚠️ ARMv8-A (2011)  ⚠️ THE BIG BREAK. Introduced AArch64 —
      ⚠️ a NEW 64-bit instruction set, not an extension of the
      32-bit one. ⚠️ AArch32 retained for compatibility
   ⚠️ ARMv8.1 through 8.9  ⚠️ incremental: LSE atomics, RCpc,
      pointer authentication, MTE, BTI — ⚠️ note that many
      "ARMv8" features people rely on arrived in these dot
      releases and are OPTIONAL
   ⚠️ ⚠️ ARMv9-A (2021)  ⚠️ SVE2 mandatory, ⚠️ CCA/Realms,
      enhanced MTE, and a marketing reset. ⚠️ Built ON ARMv8.5
      rather than replacing it
   ⚠️ ARMv9.x continues the dot-release cadence
⚠️ ⚠️ 32-BIT SUPPORT IS BEING DROPPED. ⚠️ Modern application
   cores are increasingly AArch64-only, Android has moved to
   64-bit-only requirements, and Apple dropped 32-bit years ago.
   ⚠️ AArch32 is legacy
⚠️ ⚠️ FEATURE DISCOVERY  ⚠️ ID registers (and HWCAP via the OS)
   tell you what the implementation supports. ⚠️ You CANNOT
   assume a feature from the architecture version — this is the
   practical consequence of everything being optional
```
