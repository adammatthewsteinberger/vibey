---
name: assembly-reference
description: "Use when reviewing assembly for known anti-patterns, weighing contested questions (hand-written asm vs compilers, CISC vs RISC, fixed-width SIMD vs scalable vectors, AVX-512's design, whether and which ISA to learn first), checking whether an ISA or microarchitecture claim is still current (snapshot verified August 2026), finding the authoritative vendor manuals, performance references, books, and people, or needing the quick-reference numbers, first moves, and hand-written-assembly review checklist. Companion to the other assembly-programming skills."
---

# Assembly Programming: Anti-Patterns, Contested Questions, Currency, and Canon

> **Part 4 of 4** of the *Assembly Programming* reference (plugin `assembly-programming`), covering §15–§20. Sibling skills: `assembly-fundamentals-and-isas` (§0–§5), `assembly-toolchain-performance-and-simd` (§6–§10), `assembly-systems-crypto-and-inline` (§11–§14). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 below for the currency snapshot and what goes stale first.

> **How to read this.** Reference, not tutorial. Sections are independent. Three markers:
> - **[DURABLE]** — machine organization, algorithms, or a lesson that has held since the
>   1970s. Does not expire.
> - **[ISA]** — specific to x86-64, AArch64, RISC-V, or a particular microarchitecture.
>   Verify against the vendor's current manual.
> - **[CONTESTED]** — practitioners genuinely disagree, usually about how much hand-written
>   assembly is justified.
>
> **⚠️ GOTCHA** boxes mark the mistakes that produce silent corruption, ABI violations,
> or code that is slower than the C you replaced.
>
> **The three framings that organize everything below:**
> 1. **The instruction set is an interface, not the machine.** The CPU you're actually
>    programming is out-of-order, superscalar, speculative, and cached. Your instructions
>    are decoded into µops, reordered, and executed in parallel. Reasoning about assembly
>    as "the CPU does this, then this" is wrong in ways that make your optimizations wrong.
> 2. **Reading assembly is a hundred times more common than writing it, and more
>    valuable.** Most of the return here comes from understanding compiler output,
>    debugging an optimized crash, or reverse-engineering a binary.
> 3. **When you write assembly, you are taking on the compiler's job permanently.** No
>    retargeting, no auto-vectorization, no new-CPU tuning, and no help from the next
>    twenty years of compiler improvements. That's the real cost, and it's paid in
>    maintenance rather than in the initial write.

---

## §15. Anti-Patterns

| Anti-pattern | Why | Instead |
|---|---|---|
| Writing assembly before profiling | You'll optimize code that doesn't matter | Profile; then §0.1 → `assembly-fundamentals-and-isas`'s ladder |
| Hand-written asm where intrinsics would do | You give up register allocation, scheduling, inlining | Intrinsics (§13.1 → `assembly-systems-crypto-and-inline`) |
| Optimizing instruction count | Cache misses and mispredicts dominate by 100× | Optimize the dependency chain and memory (§9.1 → `assembly-toolchain-performance-and-simd`) |
| Clobbering a callee-saved register | Corruption surfaces in the caller, arbitrarily later | Know the ABI (§6 → `assembly-toolchain-performance-and-simd`); test with poison values (§14 → `assembly-systems-crypto-and-inline`) |
| Misaligning the stack | Faults inside unrelated library code | 16-byte alignment at every call |
| Assuming System V on Windows | Different arg registers, shadow space, xmm6–15 saved | Per-platform code paths |
| Assuming AArch64 saves all of v8–v15 | **Only the low 64 bits are callee-saved** | Save the full registers yourself |
| Using the red zone in kernel/interrupt code | It doesn't exist there | `-mno-red-zone`, explicit stack |
| Omitting CFI directives | No backtraces, broken unwinding, misattributed profiles | `.cfi_*` on every function (§7.2 → `assembly-toolchain-performance-and-simd`) |
| Writing to `ax`/`al` instead of `eax` | Partial-register merge stall | 32-bit ops zero-extend for free (§2.1 → `assembly-fundamentals-and-isas`) |
| `loop`, or branch-hint prefixes on x86 | Slower / ignored for two decades | `dec`/`jnz`; nothing |
| Reusing one accumulator in a reduction | Serializes on latency | Multiple accumulators (§9.2 → `assembly-toolchain-performance-and-simd`) |
| Forgetting `vzeroupper` | AVX↔SSE transition penalties | Emit it before returning |
| Assuming AVX-512 / SVE2 / SME are present | Wildly uneven deployment | Runtime dispatch via CPUID/HWCAP |
| Porting concurrent code from x86 without adding barriers | TSO hid the missing barrier; ARM/RISC-V won't | Understand the memory model (§1.4 → `assembly-fundamentals-and-isas`) |
| JIT: writing bytes without I-cache invalidation | Works on x86 (coherent I-cache), breaks on ARM/RISC-V | `dc cvau`/`ic ivau`/`isb`, or `fence.i` (§11 → `assembly-systems-crypto-and-inline`) |
| Inline asm without `"memory"`/`"cc"`/`&`/`volatile` | Works at `-O0`, fails at `-O2` | Get the clobbers right (§13.2 → `assembly-systems-crypto-and-inline`) |
| Branching or table-indexing on secret data | Timing side channel | Constant-time discipline (§12 → `assembly-systems-crypto-and-inline`) |
| Assuming constant-time arithmetic by default on modern Intel | **Not guaranteed by default on Ice Lake / Gracemont and later** | Understand DOIT/DIT/Zkt (§12.2 → `assembly-systems-crypto-and-inline`) |
| Optimizing from a 20-year-old guide | Half of it was Pentium 4 lore | Agner Fog / uops.info, and measure |
| No differential test against a C reference | Assembly bugs are subtle and data-dependent | Random differential testing (§14 → `assembly-systems-crypto-and-inline`) |
| Hand-writing crypto assembly with no verification story | The stakes are maximal and the failure is silent | Jasmin / HACL\* / fiat-crypto (§12.3 → `assembly-systems-crypto-and-inline`) |

---

## §16. Contested Questions

**16.1 Does hand-written assembly still beat compilers?** *For*: in narrow kernels —
crypto, codecs, string/parsing primitives — with a knowledgeable author on a known
microarchitecture, yes, and measurably. *Against*: the gap closed enormously, compilers
retarget for free, and most claimed wins evaporate under proper benchmarking or on the
next CPU generation. **The synthesis practitioners actually apply: intrinsics for almost
everything, assembly for the last few percent on the few kernels that justify permanent
maintenance.**

**16.2 CISC vs. RISC.** Largely a resolved non-question — both decode to internal µops and
the ISA-level distinction matters far less than it did. What survives is real: **decode
complexity and code density** (x86 pays for the first, gains on the second), and the
argument that a clean ISA is cheaper to implement and verify.

**16.3 Fixed-width SIMD vs. scalable vectors.** *For scalable*: one binary across vector
widths, no epilogue, future-proof. *Against*: harder to reason about, harder to
hand-schedule, less mature tooling, and you can't see the register width you're working
with. The industry is split — x86 doubled down on fixed-width with AVX10, while ARM and
RISC-V both chose scalable.

**16.4 AVX-512's ISA design.** *For*: mask registers and 32 registers are genuinely
excellent, and it's the most capable SIMD ISA. *Against*: Linus Torvalds' well-known
criticism — fragmentation, downclocking, and die area spent on benchmarks rather than real
code. **AVX10 is Intel conceding the fragmentation half of that argument.**

**16.5 Should you learn assembly at all?** *For*: it's the only way to understand what your
machine and your compiler actually do, and it's indispensable for debugging optimized code,
security work, and systems programming. *Against*: as a *writing* skill it's applicable to
a shrinking share of work. **The consensus is to learn to read fluently and write rarely.**

**16.6 Which ISA to learn first.** **RISC-V** is the best-designed teaching target and the
easiest to hold in your head. **AArch64** is the best balance of clean design and real-world
ubiquity. **x86-64** is the ugliest and the one whose disassembly you're most likely to have
to read. Learning any one makes the next much easier.

---

## §17. Currency Snapshot — verified August 2026

| Thing | Status as of Aug 2026 | Decay risk |
|---|---|---|
| **Intel APX** | Doubles GPRs to **32**, adds a **unique destination register** for integer instructions (i.e. non-destructive three-operand x86), and extends predication. Intel reports **~10% fewer loads and ~20% fewer stores** in compiled code. Described as the most significant x86 ISA update since the move to 64 bits | Medium |
| **AVX10** | The convergence effort to clean up AVX-512: one ISA across P-cores and E-cores, with mask registers and 256-bit as the common denominator. **From AVX10.2 spec rev 4.0, Intel declared AVX10/512 will be used across all product lines, supporting 128/256/512 in all lines** — dropping the earlier AVX10/256-only plan (LLVM/Clang 22 correspondingly dropped the 256-bit-only options) | Medium |
| **Nova Lake** | ⚠️ Intel's **Instruction Set Extensions and Future Features manual rev 060 (November 2025)** confirms Nova Lake supports **AVX10.1, AVX10.2, APX**, plus SM4 (EVEX), MOVRS and PREFETCHRST2 — ending months of rumours it would ship without them. Launching as Core Ultra 400, **second half of 2026** | **High** |
| **RISC-V RVA23** | **Ratified 21 October 2024.** ⚠️ **The V (vector) extension is now MANDATORY** (optional in RVA22). Also newly mandatory: Zvfhmin, Zvbb, **Zvkt**, Zihintntl, Zicond, Zimop, Zcmop, Zcb, Zfa, Supm. **Baseline for the Android RISC-V ABI.** Scalar crypto Zkn/Zks **removed as options** — the goal is to move the ecosystem to vector crypto. Ratified specs are frozen and never revised | Low |
| **RVV** | v1.0 ratified 2021. VLA model; 32 vector registers; shipping **VLEN from 128 to 16384 bits**; SEW and LMUL set dynamically by `vsetvli` | Low |
| **Arm SVE2 / SME** | SVE2 mandatory in Armv9-A. **SME was added to the Arm ARM for A-profile on 20 March 2024.** ⚠️ **Apple M4 was the first consumer-grade silicon supporting both SVE2 and SME** (Apple's LLVM contribution specifies **Armv9.2-A** for M4 and confirms SME and SME2). Arm's **Lumex** cores bring SME2 to Android; some custom cores shipped SME1+SVE2 first. **Deployment remains uneven — runtime-detect** | **High** |
| **Intel DOIT** | Constant-time guarantees held **by default only before Ice Lake (Core) and Gracemont (Atom)**. On those and later they must be **explicitly enabled** via `IA32_UARCH_MISC_CTL` bit 0. **Intel does not recommend enabling globally.** **Kernel-only (MSR).** Explicitly covers data-dependent prefetchers | Medium |
| **Arm DIT** | `PSTATE.DIT`, Armv8.4+. **Unprivileged and cheap to set** from user space. Linux enabled it for arm64 in **v6.2 — kernel only**; user space must opt in. ⚠️ Guarantee is scoped to the registers an instruction explicitly uses, and makes **no statement about DMPs** | Medium |
| **RISC-V constant-time** | **Zkt** (scalar) and **Zvkt** (vector) attest data-independent execution latency for their instruction subsets. **Zvkt is mandatory in RVA23** — arguably the cleanest of the three vendors' approaches | Low |
| **LLVM constant-time intrinsics** | In development as of late 2025; lowers to `CSEL` on AArch64, masked arithmetic elsewhere. Rust Crypto, BearSSL, and PuTTY maintainers interested in **replacing inline-assembly workarounds** | **High** |

**Goes stale fastest:** Nova Lake / APX / AVX10 shipping status; SME deployment across
vendors; LLVM constant-time intrinsics. **Essentially never stale:** §1 → `assembly-fundamentals-and-isas` (machine model),
§6 → `assembly-toolchain-performance-and-simd` (ABIs), §8 → `assembly-toolchain-performance-and-simd` (reading disassembly), §9 → `assembly-toolchain-performance-and-simd` (performance fundamentals), §12.1 → `assembly-systems-crypto-and-inline` (the three
constant-time rules), §15 (anti-patterns).

---

## §18. The Canon

### 18.1 The vendor manuals — and here they genuinely are the field

- **Intel® 64 and IA-32 Architectures Software Developer's Manuals** — Volume 2 is the
  instruction reference; Volume 3 is systems programming. Also the **Optimization Reference
  Manual** and the **Instruction Set Extensions and Future Features** manual (where APX and
  AVX10 live).
- **AMD64 Architecture Programmer's Manual** + the **Software Optimization Guide** per
  family. **Read both vendors' manuals** — they differ on details that matter.
- **Arm Architecture Reference Manual (Arm ARM)** for A-profile, and the **Software
  Optimization Guides** per core (Neoverse, Cortex-X/A). Arm's **Developer** site and the
  **Learn the Architecture** series are unusually good.
- **RISC-V ISA specifications** (unprivileged and privileged) and the **Ratified
  Specifications Library** at `docs.riscv.org`, plus **riscv/riscv-profiles** on GitHub for
  RVA23.
- **System V ABI: AMD64 Architecture Processor Supplement**, **AAPCS64**, and the
  **RISC-V psABI** — the calling-convention documents in §6 → `assembly-toolchain-performance-and-simd`.

### 18.2 The performance references

- **Agner Fog's manuals** (`agner.org/optimize`) — five volumes, free, and the
  **instruction tables** are the canonical latency/throughput/port reference for every x86
  microarchitecture. **If you optimize x86, this is not optional.**
- **uops.info** — automated, exhaustive, machine-measured instruction data.
- **Intel intrinsics guide** (`intel.com/content/www/us/en/docs/intrinsics-guide`) and
  **Arm's Neon/SVE intrinsics references**.
- **Brendan Gregg**, *Systems Performance* — for the layer above.
- **Ulrich Drepper**, "What Every Programmer Should Know About Memory" — dated in specifics,
  still the best explanation of why §9.3 → `assembly-toolchain-performance-and-simd` is the section that matters.

### 18.3 Books

| Author | Work | Why |
|---|---|---|
| **Bryant & O'Hallaron** | ***Computer Systems: A Programmer's Perspective*** (CS:APP) | **The best book for learning assembly in context.** Teaches x86-64 as part of understanding the whole machine |
| **Patterson & Hennessy** | *Computer Organization and Design* (**RISC-V edition**) | The undergraduate standard, now RISC-V-based |
| **Hennessy & Patterson** | *Computer Architecture: A Quantitative Approach* | The graduate one — why microarchitecture is what it is |
| **Randall Hyde** | *The Art of Assembly Language* | Comprehensive, opinionated, good on fundamentals |
| **Daniel Kusswurm** | *Modern X86 Assembly Language Programming*; *Modern Arm Assembly* | The most current practical SIMD-focused books |
| **Ray Seyfarth** | *Introduction to 64 Bit Assembly Programming* | Clean, modern, Linux-focused |
| **Pyeatt & Ughetta** | *ARM 64-Bit Assembly Language* | Solid AArch64 treatment |
| **Waterman & Asanović** | *The RISC-V Reader* | Short, excellent, by the architects |
| **Eldad Eilam** | *Reversing: Secrets of Reverse Engineering* | The reading-assembly discipline |
| **Dennis Andriesse** | *Practical Binary Analysis* | Modern, tool-focused |
| **Chris Kaspersky** | *Code Optimization: Effective Memory Usage* | Dated but instructive |
| **Warren** | ***Hacker's Delight*** | Bit-twiddling algorithms — the raw material of good assembly |
| **Abrash** | *Graphics Programming Black Book* | Historically important, and the best writing about the *craft* of optimization ever published. **Read it for the method, not the numbers** |

### 18.4 Online and people
**Compiler Explorer** (godbolt.org — Matt Godbolt) is the single best tool; his talks on
"what has my compiler done for me lately" are the best introduction to reading assembly.
**Agner Fog**, **Daniel Lemire** (SIMD parsing, `simdjson`), **Wojciech Muła**
(`0x80.pl` — SIMD algorithms), **Travis Downs** (performance archaeology),
**Peter Cordes** (his Stack Overflow x86 answers are a reference work in their own right,
and the **x86 tag wiki** he maintains is genuinely excellent), **Fabian Giesen** (`ryg`),
**Anger's forum**, **stuffedcow.net** (Henry Wong, branch prediction), and the
**highload.fun** / **Algorithmica** (`en.algorithmica.org/hpc`) performance material.

---

## §19. Quick Reference

### 19.1 Numbers to memorize
- **Cache line: 64 bytes.**
- Latency: **L1 ~4, L2 ~12, L3 ~40, DRAM ~200–300+ cycles.**
- Branch mispredict: **~15–20 cycles.**
- Integer divide: **20–100 cycles** (strength-reduce it).
- Stack alignment at a call: **16 bytes** on x86-64 SysV, AArch64, and RISC-V.
- x86-64 GPRs: **16** (32 with APX). AArch64: **31 + zero**. RISC-V: **32** (x0 = zero).
- x86 instruction length: **1–15 bytes.** AArch64 and RV: **fixed 32-bit** (RV `C`: 16).
- System V red zone: **128 bytes**. Windows shadow space: **32 bytes**.

### 19.2 First moves
| Task | Do this |
|---|---|
| Understand what the compiler did | **godbolt.org**, `-O2 -masm=intel` |
| Find the hot instruction | `perf record` → `perf annotate` |
| Look up latency/throughput | Agner Fog's tables; uops.info |
| Analyze a loop statically | `llvm-mca`, uiCA |
| Check ABI compliance | Poison callee-saved registers and verify after the call |
| Debug at instruction level | `gdb`: `layout asm`, `si`, `info registers` |
| Verify a hand-written routine | Random differential test vs. a C reference |
| Check for a CPU feature | CPUID (x86) / `getauxval(AT_HWCAP)` (Linux ARM/RV) |

### 19.3 Hand-written assembly review checklist
- [ ] Correct ABI: arg registers, return register, callee-saved preserved
- [ ] Stack 16-byte aligned at every call; no red-zone use in kernel/interrupt context
- [ ] CFI directives present, and `.type`/`.size` set
- [ ] Tail/remainder path tested (this is where SIMD bugs live)
- [ ] Unaligned and zero-length inputs tested
- [ ] Memory barriers correct for the *weakest* target, not just x86
- [ ] `vzeroupper` before returning from AVX code
- [ ] Runtime feature detection, with a fallback path
- [ ] For crypto: no secret-dependent branches, no secret-dependent addresses, no
      variable-latency ops on secrets — and a DIT/DOIT/Zkt story
- [ ] Differential-tested against a reference implementation
- [ ] Benchmarked on more than one microarchitecture

---

## §20. Sources and Method

**Method.** Narrative (not systematic) review. The durable material — §1 → `assembly-fundamentals-and-isas` (machine model),
§6 → `assembly-toolchain-performance-and-simd` (ABIs), §8 → `assembly-toolchain-performance-and-simd` (reading disassembly), §9 → `assembly-toolchain-performance-and-simd` (performance fundamentals), §10.4 → `assembly-toolchain-performance-and-simd`, §11 → `assembly-systems-crypto-and-inline`, §12.1 → `assembly-systems-crypto-and-inline`,
§13.2 → `assembly-systems-crypto-and-inline`, §14 → `assembly-systems-crypto-and-inline`, §15 — is synthesized from the vendor architecture manuals, the optimization
references in §18, and long-established practice. Every **time-sensitive** claim (ISA
extension status, profile contents, constant-time guarantees, silicon deployment) was
verified against a primary or near-primary source in **August 2026** and is flagged in
§17 with a decay-risk rating. Where practitioners genuinely disagree — mostly about how
much hand-written assembly is justified — §16 presents both cases.

**Search log** (August 2026): Intel APX and AVX10/AVX10.2 status and Nova Lake support ·
RISC-V RVA23 profile ratification and mandatory extensions · constant-time programming,
Intel DOIT and Arm DIT · Armv9, SVE2, SME/SME2 and Apple Silicon deployment.

**Primary and near-primary sources consulted (selected):**
- **Intel** — *Architecture Instruction Set Extensions and Future Features* programming
  reference (rev 060, November 2025), the AVX10 architecture specification, and the
  *Data Operand Independent Timing ISA Guidance* and timing-side-channel guidance articles
- **RISC-V International** — RVA23 ratification announcement (21 Oct 2024), the **Ratified
  Specifications Library** (`docs.riscv.org/reference/rva23`), and **riscv/riscv-profiles**
  `rva23-profile.adoc` for the mandatory/optional extension lists
- **Arm** — the Armv9-A architecture page; DIT register documentation
- **TechInsights** on APX's register and load/store impact; **Phoronix**, **TechPowerUp**,
  **VideoCardz**, and **igor'sLAB** on the Nova Lake ISA confirmation; the LKVM/KVM
  AVX10.2 CPUID patch series for the AVX10/512 policy change
- **Academic and practitioner security work** — "Let's DOIT: Using Intel's Extended HW/SW
  Contract for Secure Compilation of Crypto Code" (TCHES 2025), "Constant-Time Code: The
  Pessimist Case" (IACR ePrint 2025/435), "Constant-Time Wasmtime, for Real This Time",
  **LWN.net**'s "Constant-time instructions and processor optimizations", and the oss-sec
  thread on data-operand-dependent timing
- **Trail of Bits** on LLVM constant-time intrinsics; academic SME benchmarking work on
  Apple M4 confirming Armv9.2-A, SME and SME2

**Confidence statement.** **High confidence** in §1–§14 → `assembly-fundamentals-and-isas`, `assembly-systems-crypto-and-inline` and §19 — these rest on vendor
architecture manuals, ABI specifications, and long-established optimization literature.
**High confidence** in §17's RISC-V RVA23 contents and the DOIT/DIT descriptions, which
come from the ratified specification and vendor documentation respectively. **Moderate
confidence** in the Nova Lake and AVX10/APX shipping details: they come from Intel's own
ISA reference manual (a primary source) but describe **unreleased hardware**, and this
specific question had contradictory reporting through late 2025 before the manual settled
it — treat ship dates and final feature lists as subject to change. **Moderate confidence**
in §10.3 → `assembly-toolchain-performance-and-simd`'s SME deployment picture, which is assembled from vendor announcements,
academic benchmarking, and trade reporting rather than a single authoritative source;
the direction (uneven, runtime-detect) is reliable, the per-vendor specifics less so.
Cycle-count figures throughout §9 → `assembly-toolchain-performance-and-simd` and §19.1 are **order-of-magnitude guidance across
typical modern cores**, not measurements for any specific microarchitecture — use Agner
Fog's tables or uops.info for real numbers.
