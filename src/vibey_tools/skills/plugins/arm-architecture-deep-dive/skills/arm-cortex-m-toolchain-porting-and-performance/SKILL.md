---
name: arm-cortex-m-toolchain-porting-and-performance
description: "Use when actually building or moving software onto ARM: Cortex-M and the embedded profile with its interrupt model and memory protection, the toolchain and ABI including calling conventions and the AAPCS, porting from x86 and the memory-ordering, intrinsics and undefined-behaviour traps that bite, performance analysis with PMU counters and the ARM-specific pitfalls, and the competitive landscape against x86 and RISC-V."
---

# ARM: Cortex-M and Embedded, Toolchain and ABI, Porting from x86, Performance Analysis, and the Competitive Landscape

> **Part 5 of 6** of the *ARM: A Deep Dive* reference (plugin `arm-architecture-deep-dive`), covering §21–§25. Sibling skills: `arm-what-arm-is-licensing-families-and-isa-generations` (§0–§4), `arm-aarch64-exception-levels-memory-model-and-mmu` (§5–§9), `arm-vectors-atomics-numerics-and-security-architecture` (§10–§15), `arm-system-architecture-boot-and-virtualization` (§16–§20), `arm-reference` (§26–§31). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 2. **⚠️ THE WEAK MEMORY MODEL IS THE MOST CONSEQUENTIAL DIFFERENCE FROM x86** (§8 → `arm-aarch64-exception-levels-memory-model-and-mmu`, §23).
>    **Concurrent code that is correct on x86-TSO can be silently broken on ARM with no
>    source change. This is the single most common real porting failure and it produces
>    intermittent bugs.**
> 3. **⚠️ SECURITY IS ARCHITECTED, NOT BOLTED ON** (§13–§15 → `arm-vectors-atomics-numerics-and-security-architecture`). **TrustZone, pointer
>    authentication, BTI, MTE and CCA are architectural features with silicon support —
>    which is genuinely different from mitigation-by-software, and it is a large part of
>    why ARM won mobile.**

---

## §21. ⚠️ Cortex-M and Embedded

> **⚠️ By unit volume this is the ARM most chips actually are, and it is a genuinely
> different architecture — not a small Cortex-A.**
```
⚠️ ⚠️ THUMB-2 ONLY. ⚠️ No AArch64, no ARM 32-bit encoding —
   ⚠️ a mixed 16/32-bit instruction set chosen for CODE DENSITY,
   which matters enormously when flash is the cost driver
⚠️ ⚠️ NO MMU. ⚠️ An optional MPU gives region-based protection
   without translation. ⚠️ This means no virtual memory, no
   fork(), and a flat physical address space
⚠️ ⚠️ THE INTERRUPT DESIGN IS THE STANDOUT FEATURE
   ⚠️ NVIC with ⚠️ AUTOMATIC REGISTER STACKING IN HARDWARE on
   exception entry — ⚠️ so an ISR can be a plain C function with
   no assembly wrapper
   ⚠️ ⚠️ TAIL-CHAINING  back-to-back interrupts skip the
   unstack/restack entirely
   ⚠️ Deterministic, low, documented interrupt latency —
   ⚠️ which is the whole point for real-time work
⚠️ ⚠️ EXC_RETURN  a magic value in LR on exception entry that
   encodes which stack and mode to return to — ⚠️ startling the
   first time you see it in a debugger
⚠️ THE FAMILY  ⚠️ M0/M0+ (smallest) · M3 · M4 (DSP) · M7
   (cache, higher performance) · ⚠️ M23/M33 (TrustZone-M) ·
   M55/M85 (⚠️ Helium/MVE — SIMD for ML at the edge)
⚠️ ⚠️ CMSIS  the standard HAL and register-definition layer,
   which is what makes vendor peripherals tractable
⚠️ MEMORY MAP is architecturally defined — ⚠️ code, SRAM,
   peripheral and system regions at fixed addresses, plus
   ⚠️ BIT-BANDING on some parts for atomic single-bit access
```

---

# PART V — WORKING WITH IT

## §22. Toolchain and ABI

**⚠️ The AAPCS64 calling convention**: ⚠️ **X0–X7 for arguments and return, X8 for indirect
result, X9–X15 caller-saved, X19–X28 callee-saved, X29 frame pointer, X30 link register.**
**⚠️ The LINK REGISTER is the key difference from x86** — ⚠️ **a call puts the return address
in X30 rather than pushing it, so LEAF FUNCTIONS need not touch the stack at all.** ⚠️ **It
also means the return address is in a register where PAC can sign it** (§14 → `arm-vectors-atomics-numerics-and-security-architecture`).
**⚠️ Stack alignment to 16 bytes**, ⚠️ **and it is enforced — misalignment faults rather than
degrading.**
**⚠️ Compilers**: ⚠️ **GCC, LLVM/Clang and Arm's own toolchain; ⚠️ `-mcpu` and `-march`
selection matters more than on x86 because of feature optionality (§4 → `arm-what-arm-is-licensing-families-and-isa-generations`, §11 → `arm-vectors-atomics-numerics-and-security-architecture`).**
**⚠️ Debug**: ⚠️ **CoreSight for trace, ETM/ITM, gdb and OpenOCD, and SWD as the two-wire
debug interface on Cortex-M.**

---

## §23. ⚠️ Porting from x86

```
⚠️ ⚠️ IN ORDER OF HOW MUCH TROUBLE THEY CAUSE
   ⚠️ 1. MEMORY ORDERING (§8)  ⚠️ THE BIG ONE. ⚠️ Lock-free
      code, hand-rolled synchronization and anything using
      `volatile` as a synchronization primitive can be silently
      broken. ⚠️ Use the language's atomics; ⚠️ and TEST UNDER
      LOAD ON REAL ARM HARDWARE — the bugs are probabilistic
   ⚠️ 2. ⚠️ INTRINSICS AND INLINE ASSEMBLY  ⚠️ SSE/AVX intrinsics
      do not exist. ⚠️ Options: portable libraries, SIMDe-style
      translation headers, or NEON/SVE rewrites (§10)
   ⚠️ 3. ⚠️ char IS UNSIGNED BY DEFAULT ON ARM. ⚠️ Code assuming
      signed char has real behaviour differences, and it
      compiles silently
   ⚠️ 4. ⚠️ PAGE SIZE ASSUMPTIONS — ⚠️ 4 KB is not guaranteed
      (§9); Apple uses 16 KB
   ⚠️ 5. ⚠️ UNALIGNED ACCESS  ⚠️ generally supported on normal
      memory in AArch64, ⚠️ but NOT on device memory and not for
      exclusives — and this catches driver code
   ⚠️ 6. FLOATING POINT last-bit differences (§12)
   ⚠️ 7. ⚠️ SELF-MODIFYING CODE AND JITs  ⚠️ require explicit
      cache maintenance (§8), and this is a hard-crash-level bug
   ⚠️ 8. Build system, dependencies, and containers built for
      one architecture
⚠️ ⚠️ WHAT IS USUALLY EASY  ⚠️ ordinary application code in a
   memory-safe or well-behaved language recompiles and runs.
   ⚠️ The horror stories are concentrated in low-level code
⚠️ EMULATION  ⚠️ Rosetta 2 and Windows Prism translate x86
   binaries — ⚠️ and note the memory model problem AGAIN: Apple
   silicon implements an optional TSO MODE specifically so
   translated x86 code gets the ordering it assumes
```

---

## §24. Performance Analysis on ARM

**⚠️ PMU counters** exist and are architected, ⚠️ **though the specific events available vary
by implementation — check the core's technical reference manual, not a generic list.**
**⚠️ Tools**: ⚠️ **`perf` works, Arm Streamline and Arm Forge for deeper analysis, and
vendor tools for specific silicon.**
**⚠️ SPE (Statistical Profiling Extension)** — ⚠️ **hardware sampling with instruction-level
attribution including memory latency, which is genuinely better than software sampling for
finding memory stalls.**
**⚠️ The top-down method applies** (see a microarchitecture reference §22), ⚠️ **with
vendor-specific implementations.**
**⚠️ ARM-specific things to look for**: ⚠️ **atomics falling back to exclusive loops (§11 → `arm-vectors-atomics-numerics-and-security-architecture`);
big.LITTLE scheduling putting your thread on the wrong core (§16 → `arm-system-architecture-boot-and-virtualization`); missing SVE/NEON
vectorization; barrier overuse where acquire/release would do (§8 → `arm-aarch64-exception-levels-memory-model-and-mmu`); and cache maintenance
in hot paths.**

---

## §25. The Competitive Landscape

**⚠️ Against x86**: ⚠️ **the honest position is that the ISA is not the differentiator (see a
microarchitecture reference §20) — ⚠️ implementation, process node, memory system and the
economics of custom silicon are.** ⚠️ **AMD's strongest argument remains software
compatibility: moving enterprise workloads off x86 requires recompilation and sometimes
real refactoring** (§23).
**⚠️ Against RISC-V**: ⚠️ **RISC-V's advantage is no licence fee and full freedom to extend;
its disadvantages are ecosystem maturity and fragmentation risk, which ARM's architectural
compliance regime (§2 → `arm-what-arm-is-licensing-families-and-isa-generations`) specifically prevents.** ⚠️ **RISC-V is winning first in
deeply-embedded and controller roles where the ecosystem burden is lightest.**
**⚠️ Apple silicon** is the demonstration case: ⚠️ **an architecture licence plus vertical
integration plus a very wide, low-clocked microarchitecture plus unified memory — and the
lesson is about implementation and integration, not about ARM per se.**
**⚠️ Windows on ARM** — ⚠️ **its history is one of repeated attempts, and the persistent
constraint has been application compatibility rather than silicon.**
