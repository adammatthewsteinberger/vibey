---
name: arm-vectors-atomics-numerics-and-security-architecture
description: "Use for the extensions and the security architecture: the vector extensions NEON, SVE, SVE2 and SME and the vector-length-agnostic model, atomics and synchronization including the large system extensions, floating point and numerics, TrustZone and secure world separation, pointer authentication, branch target identification and memory tagging, and Confidential Compute Architecture with realms."
---

# ARM: Vector Extensions, Atomics and Synchronization, Floating Point and Numerics, TrustZone, Pointer Authentication, BTI and MTE, and CCA

> **Part 3 of 6** of the *ARM: A Deep Dive* reference (plugin `arm-architecture-deep-dive`), covering §10–§15. Sibling skills: `arm-what-arm-is-licensing-families-and-isa-generations` (§0–§4), `arm-aarch64-exception-levels-memory-model-and-mmu` (§5–§9), `arm-system-architecture-boot-and-virtualization` (§16–§20), `arm-cortex-m-toolchain-porting-and-performance` (§21–§25), `arm-reference` (§26–§31). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 3. **⚠️ SECURITY IS ARCHITECTED, NOT BOLTED ON** (§13–§15). **TrustZone, pointer
>    authentication, BTI, MTE and CCA are architectural features with silicon support —
>    which is genuinely different from mitigation-by-software, and it is a large part of
>    why ARM won mobile.**

---

## §10. ⚠️ Vector Extensions

```
⚠️ NEON (Advanced SIMD)  ⚠️ fixed 128-bit registers, widely
   supported, mandatory on most application cores. ⚠️ The safe
   baseline
⚠️ ⚠️ SVE (Scalable Vector Extension)  ⚠️ THE INTERESTING IDEA:
   ⚠️ VECTOR LENGTH AGNOSTIC. ⚠️ The register width is
   implementation-defined between 128 and 2048 bits, and
   ⚠️ THE SAME BINARY RUNS CORRECTLY ON ANY WIDTH
   ⚠️ HOW: ⚠️ predicate registers plus a loop idiom
   (WHILELT and INCB) that adapts to the hardware width at
   runtime. ⚠️ No re-compilation, no width-specific code paths,
   ⚠️ AND NO TAIL LOOP — predication handles the remainder
   ⚠️ COMPARE x86's approach of a new instruction set per width
   (SSE → AVX → AVX-512), each needing separate code paths
⚠️ SVE2  ⚠️ extends SVE to general-purpose and DSP-style
   workloads rather than just HPC. ⚠️ MANDATORY in ARMv9-A,
   which is what makes it targetable
⚠️ ⚠️ SME (Scalable Matrix Extension)  ⚠️ outer-product and
   matrix operations with a dedicated ZA tile storage array,
   plus ⚠️ STREAMING SVE MODE — a distinct processor mode with
   its own vector length. ⚠️ Aimed squarely at the ML workloads
   in a microarchitecture reference §13
⚠️ ⚠️ THE PRACTICAL CAVEAT  ⚠️ SVE's elegance is real and
   adoption has been gradual; ⚠️ NEON remains the compatibility
   baseline, and much shipping code still targets it. ⚠️ Check
   what your target actually implements (§4)
```

---

## §11. Atomics and Synchronization

**⚠️ The original mechanism is LOAD-EXCLUSIVE / STORE-EXCLUSIVE (LDXR/STXR)** —
⚠️ **an optimistic pair with a retry loop, which is flexible and scales badly under
contention because every failure means another round trip.**
**⚠️ LSE (Large System Extensions, ARMv8.1)** added ⚠️ **true single-instruction atomics —
LDADD, SWP, CAS and relatives — which perform far better under high core counts, and are
frequently done at the interconnect or cache rather than by the core.**
> **⚠️ GOTCHA — this is a real and measurable performance cliff.** ⚠️ **Code compiled without
> LSE enabled falls back to exclusive loops, and on a high-core-count server the difference
> under contention is substantial.** **⚠️ Check your compiler flags (`-moutline-atomics` or
> an explicit `-march`), because the default may target the oldest baseline.**

**⚠️ WFE/WFI and SEV** — ⚠️ **wait-for-event and send-event, which let a spinning core sleep
until something changes rather than burning power.**
**⚠️ Combine with §8 → `arm-aarch64-exception-levels-memory-model-and-mmu`'s acquire/release forms** — ⚠️ **LDADDAL and friends carry ordering
semantics in the instruction.**

---

## §12. Floating Point and Numerics

**⚠️ IEEE 754 compliance**, with FPCR and FPSR controlling rounding mode and reporting
exceptions.
**⚠️ Half precision (FP16)** as both a storage and an arithmetic format; ⚠️ **BF16 and
INT8 dot-product instructions (SDOT/UDOT) for ML** (see a microarchitecture reference §14).
**⚠️ FMA** as a single-rounding fused operation.
> **⚠️ GOTCHA — ARM's default flush-to-zero and denormal handling can differ from x86**,
> ⚠️ **and floating-point results can therefore differ in the last bits between
> architectures.** **⚠️ For anything requiring bit-exact reproducibility across platforms
> this is a real porting issue, and it surfaces in test suites that compare floating-point
> output exactly** (§23 → `arm-cortex-m-toolchain-porting-and-performance`).

---

# PART III — SECURITY ARCHITECTURE

## §13. ⚠️ TrustZone

```
⚠️ ⚠️ THE IDEA  ⚠️ split the system into a SECURE WORLD and a
   NON-SECURE WORLD, with the split enforced in HARDWARE
   throughout — ⚠️ not just in the CPU, but propagated across
   the interconnect as an extra address bit (the NS bit), so
   peripherals and memory regions are partitioned too
⚠️ THE MONITOR at EL3 handles world switches via SMC calls
⚠️ WHAT RUNS IN THE SECURE WORLD  ⚠️ a Trusted Execution
   Environment — key storage, DRM, biometric matching, secure
   payment, mobile device attestation
⚠️ ⚠️ THE HONEST CRITIQUES
   ⚠️ TEE implementations are large, proprietary, and have had
      SERIOUS VULNERABILITIES — ⚠️ and a compromise there is
      more privileged than the kernel
   ⚠️ ⚠️ TrustZone protects against the NORMAL world, not
      against the secure world's own bugs or against physical
      attack
   ⚠️ ⚠️ IT IS ALSO A LOCK-DOWN MECHANISM. ⚠️ The same feature
      that protects your keys enforces DRM and can prevent the
      device owner from controlling their own hardware — the
      security benefit and the control question are inseparable
⚠️ CORTEX-M has TrustZone-M — ⚠️ a different, lighter design
   with fast state transitions rather than a monitor (§21)
```

---

## §14. ⚠️ Pointer Authentication, BTI and MTE

> **⚠️ Three architectural mitigations for classes of memory-safety bug, and they are a good
> example of what silicon support buys over software mitigation.**
```
⚠️ ⚠️ POINTER AUTHENTICATION (PAC, ARMv8.3)
   ⚠️ ⚠️ THE INSIGHT: 64-bit pointers do not use all 64 bits.
   ⚠️ The unused top bits hold a cryptographic MAC of the
   pointer value plus a context (usually the stack pointer),
   keyed by a register the attacker cannot read
   ⚠️ PACIASP on function entry, AUTIASP on return — ⚠️ a
   corrupted return address fails authentication and faults
   ⚠️ ⚠️ THIS BREAKS ROP/JOP AT LOW COST because it needs no
   shadow stack and no extra memory
   ⚠️ LIMITS  ⚠️ signing gadget reuse, ⚠️ the MAC is short so
   brute force is conceivable in some threat models, and
   ⚠️ pointer-substitution attacks within the same context
⚠️ ⚠️ BTI (Branch Target Identification, ARMv8.5)  ⚠️ indirect
   branches may only land on a BTI landing-pad instruction —
   ⚠️ dramatically shrinking the gadget space for JOP
⚠️ ⚠️ MTE (Memory Tagging Extension, ARMv8.5)  ⚠️ THE MOST
   INTERESTING ONE
   ⚠️ 4-bit tags in pointer top bits AND in memory tag storage;
   ⚠️ the hardware checks they match on every access
   ⚠️ ⚠️ CATCHES USE-AFTER-FREE AND BUFFER OVERFLOW
   PROBABILISTICALLY (⚠️ 1-in-16 chance of a random collision)
   at low enough overhead to run in PRODUCTION, not just in
   testing — ⚠️ which is the qualitative difference from
   ASAN-style tooling
   ⚠️ SYNC mode (precise, slower) vs ASYNC (faster, imprecise)
⚠️ ⚠️ ALL THREE ARE OPTIONAL FEATURES (§4). ⚠️ Availability
   varies by silicon, and MTE deployment in particular has been
   slower than the architecture's availability
```

---

## §15. CCA and Realms

**⚠️ Confidential Compute Architecture (ARMv9)** adds a ⚠️ **REALM world alongside Secure and
Non-secure — a fourth security state.**
**⚠️ The goal is confidential computing**: ⚠️ **a workload whose memory and state the
HYPERVISOR and host OS cannot read, so a cloud tenant need not trust the cloud operator's
software stack.**
**⚠️ The Realm Management Monitor (RMM)** at a new level manages realms; ⚠️ **the hypervisor
still schedules and allocates resources but cannot inspect realm memory — the separation of
management from access is the architectural trick.**
**⚠️ Attestation** lets a remote party verify what is running inside a realm (see a
digital-logic reference §22 on measured boot).
**⚠️ The comparison** is with Intel TDX and AMD SEV-SNP — ⚠️ **same problem, different
architecture, and none of them defends against a compromised root of trust or physical
attack.**
**⚠️ Maturity**: ⚠️ **the architecture is specified and silicon and software support are
still arriving; treat deployment claims sceptically.**

---

# PART IV — SYSTEM ARCHITECTURE
