---
name: arm-aarch64-exception-levels-memory-model-and-mmu
description: "Use for the core architecture: AArch64 register and instruction design and how it differs from AArch32, the instruction set characteristics that matter to compilers and hand-written assembly, exception levels EL0 to EL3 and the privilege model, the weak memory model and the barriers and acquire-release semantics it forces, and the MMU with translation regimes, page table formats and TLB behaviour."
---

# ARM: AArch64, Instruction Set Characteristics, Exception Levels, the Memory Model, and MMU and Translation

> **Part 2 of 6** of the *ARM: A Deep Dive* reference (plugin `arm-architecture-deep-dive`), covering §5–§9. Sibling skills: `arm-what-arm-is-licensing-families-and-isa-generations` (§0–§4), `arm-vectors-atomics-numerics-and-security-architecture` (§10–§15), `arm-system-architecture-boot-and-virtualization` (§16–§20), `arm-cortex-m-toolchain-porting-and-performance` (§21–§25), `arm-reference` (§26–§31). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The architecture is documented and stable. Two things moved decisively. See §26 → `arm-reference` for Arm's business model, and its actual market position.

> **⚠️ ARM is a business model as much as an instruction set, and you cannot understand the
> architecture without understanding that.** ⚠️ **The design choices — modularity, optional
> extensions, profiles, strict architectural compliance — exist because the ISA has to be
> implementable by dozens of independent companies at wildly different power and
> performance points.**
>
> **Builds on a microarchitecture reference (§20 ISA design, §8 memory consistency) and a
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
> 2. **⚠️ THE WEAK MEMORY MODEL IS THE MOST CONSEQUENTIAL DIFFERENCE FROM x86** (§8, §23 → `arm-cortex-m-toolchain-porting-and-performance`).
>    **Concurrent code that is correct on x86-TSO can be silently broken on ARM with no
>    source change. This is the single most common real porting failure and it produces
>    intermittent bugs.**
> 3. **⚠️ SECURITY IS ARCHITECTED, NOT BOLTED ON** (§13–§15 → `arm-vectors-atomics-numerics-and-security-architecture`). **TrustZone, pointer
>    authentication, BTI, MTE and CCA are architectural features with silicon support —
>    which is genuinely different from mitigation-by-software, and it is a large part of
>    why ARM won mobile.**

---

## §5. ⚠️ AArch64

> **⚠️ A clean-sheet design, and its choices are instructive because they were made with
> forty years of hindsight.**
```
⚠️ REGISTERS  ⚠️ 31 general-purpose (X0-X30, or W0-W30 for
   32-bit views), ⚠️ plus a ZERO REGISTER (XZR/WZR) and a
   separate stack pointer
   ⚠️ COMPARE x86-64's 16 — ⚠️ more registers means less
   spilling, and it is one of the genuine ISA-level differences
⚠️ ⚠️ WHAT AArch64 DELIBERATELY REMOVED from AArch32
   ⚠️ CONDITIONAL EXECUTION on nearly every instruction —
      ⚠️ ARM's famous feature, dropped because it complicates
      out-of-order register renaming badly
   ⚠️ ⚠️ THE PC AS A GENERAL REGISTER — ⚠️ AArch32 let you write
      to r15 and branch. Elegant, and a nightmare for
      implementation and security
   ⚠️ Load/store multiple with arbitrary register lists
   ⚠️ The barrel shifter on every operand (⚠️ retained in
      reduced form)
⚠️ WHAT IT KEPT  ⚠️ FIXED 32-BIT INSTRUCTION LENGTH (⚠️ which
   makes parallel DECODE far easier than x86's variable
   length — see a microarchitecture reference §20) ·
   load/store architecture · condition flags (NZCV) ·
   ⚠️ conditional SELECT instructions (CSEL) replacing
   predication
⚠️ ADDRESSING MODES  base+offset, pre/post-indexed, scaled
   register, PC-relative — ⚠️ and PC-relative addressing plus
   ADRP is how position-independent code works efficiently
```

---

## §6. Instruction Set Characteristics

**⚠️ Load/store architecture** — ⚠️ **arithmetic operates on registers only, so memory
access is explicit; this makes the memory model (§8) analyzable.**
**⚠️ Load/store PAIR (LDP/STP)** — ⚠️ **two registers in one instruction, heavily used in
prologues and epilogues.**
**⚠️ CSEL and the conditional-select family** — ⚠️ **branchless selection without full
predication.**
**⚠️ Bitfield instructions** (UBFX, SBFX, BFI) — ⚠️ **single-instruction extract and insert,
notably better than the x86 equivalents.**
**⚠️ Encoding constraints**: ⚠️ **immediates are limited by the fixed 32-bit width, so large
constants need MOVZ/MOVK sequences or a literal pool — ⚠️ which is why disassembly shows
apparently redundant instruction pairs.**
**⚠️ System registers** are accessed via MRS/MSR, ⚠️ **and the naming convention
(`REG_ELx`) tells you which exception level owns it** (§7).
**⚠️ Code density**: ⚠️ **AArch64 is denser than fixed-32-bit RISC traditionally was but
less dense than Thumb-2 or x86 — a deliberate trade for decode simplicity.**

---

## §7. ⚠️ Exception Levels

> **⚠️ The privilege model, and it is cleaner than x86's rings.**
```
⚠️ THE LEVELS  ⚠️ EL0 (applications) · EL1 (OS kernel) ·
   ⚠️ EL2 (HYPERVISOR) · ⚠️ EL3 (SECURE MONITOR — the highest,
   and where the world switch happens, §13)
⚠️ ⚠️ EL2 EXISTING AS AN ARCHITECTED LEVEL is the key difference
   from x86, where virtualization was retrofitted. ⚠️ The
   hypervisor has its own level, its own registers and its own
   translation regime by design (§20)
⚠️ ⚠️ ORTHOGONAL TO THIS: SECURITY STATE (§13). ⚠️ Secure and
   Non-secure worlds each have their own EL0/EL1, so the
   privilege model is TWO-DIMENSIONAL. ⚠️ ARMv9's CCA adds a
   third dimension with Realm state (§15)
⚠️ EXCEPTION HANDLING  ⚠️ a VECTOR TABLE indexed by exception
   type AND by the level/state the exception came from ·
   ⚠️ ELR (return address), SPSR (saved state), ESR (⚠️ the
   syndrome register, which tells you WHY — enormously useful
   for debugging)
⚠️ ⚠️ EXCEPTIONS ROUTE UPWARD, and where they route is
   CONFIGURABLE via HCR_EL2 and SCR_EL3 — ⚠️ which is what lets
   a hypervisor trap and emulate specific guest operations
⚠️ SYNCHRONOUS vs asynchronous (IRQ, FIQ, SError) ·
   ⚠️ FIQ historically the fast interrupt, now largely used for
   secure-world interrupts
```

---

## §8. ⚠️ The Memory Model

> **⚠️ §1 → `arm-what-arm-is-licensing-families-and-isa-generations`'s second organizing idea, and the thing most likely to bite you. See a
> microarchitecture reference §8 for consistency models generally.**
```
⚠️ ⚠️ ARM IS WEAKLY ORDERED. ⚠️ Loads and stores can be reordered
   far more freely than on x86-TSO — ⚠️ store-store, load-load,
   load-store and store-load reordering are all permitted where
   no dependency exists
⚠️ ⚠️ THE PRACTICAL CONSEQUENCE: CONCURRENT CODE THAT IS CORRECT
   ON x86 CAN BE BROKEN ON ARM WITH NO SOURCE CHANGE. ⚠️ x86's
   stronger model HIDES missing synchronization. ⚠️ The bugs are
   intermittent, load-dependent and hard to reproduce
⚠️ THE BARRIERS
   ⚠️ DMB  data memory barrier — orders memory accesses
   ⚠️ DSB  data synchronization barrier — stronger, waits for
      completion
   ⚠️ ISB  instruction synchronization barrier — ⚠️ needed after
      changing system state that affects instruction fetch
   ⚠️ Each takes a SHAREABILITY DOMAIN and access-type qualifier
      (ISH, OSH, NSH; LD, ST) — ⚠️ using the weakest sufficient
      variant matters for performance
⚠️ ⚠️ ACQUIRE/RELEASE IS BUILT INTO THE INSTRUCTIONS
   ⚠️ LDAR (load-acquire) and STLR (store-release) — ⚠️ ordering
   semantics without a separate barrier, and generally FASTER
   than a full DMB. ⚠️ This is the idiom to use
⚠️ ⚠️ ADDRESS, DATA AND CONTROL DEPENDENCIES provide some
   ordering for free — ⚠️ and relying on them is subtle and
   compiler-hostile, because the compiler may optimize the
   dependency away
⚠️ MEMORY TYPES  ⚠️ NORMAL (cacheable, reorderable, speculatable)
   vs ⚠️ DEVICE (nGnRnE through nGRE — ⚠️ device memory
   attributes control gathering, reordering and early
   acknowledgement, and getting these wrong on MMIO causes
   baffling driver bugs)
⚠️ CACHE MAINTENANCE  ⚠️ ARM requires explicit cache maintenance
   in places x86 does not, particularly for ⚠️ SELF-MODIFYING
   CODE and JITs — ⚠️ instruction and data caches are not
   coherent, so a JIT must clean D-cache and invalidate I-cache
```

---

## §9. MMU and Translation

**⚠️ Translation regimes** are per exception level and per security state, ⚠️ **which is why
there are so many system registers.**
**⚠️ TTBR0 and TTBR1** — ⚠️ **two base registers split by address range, so user and kernel
mappings live in separate tables and a context switch changes only TTBR0.** ⚠️ **This is
architecturally cleaner than the x86 arrangement and made Meltdown-style page-table
isolation cheaper.**
**⚠️ Granule sizes** of 4 KB, 16 KB and 64 KB — ⚠️ **note that 16 KB is what Apple uses, and
it is a real source of porting friction for code that assumes 4 KB pages.**
**⚠️ Multi-level tables, up to 4 or 5 levels**, ⚠️ **with configurable address size (TCR).**
**⚠️ ASIDs and VMIDs** avoid TLB flushes on context and VM switch.
**⚠️ STAGE 2 TRANSLATION** is the virtualization feature (§20 → `arm-system-architecture-boot-and-virtualization`): ⚠️ **the guest's "physical"
address is translated again by the hypervisor's tables — architected, not emulated.**
**⚠️ TLB maintenance** is explicit and has broadcast variants, ⚠️ **and TLBI instructions
plus the required DSB/ISB sequencing are a classic source of subtle kernel bugs.**
