---
name: arm-reference
description: "Use when correcting an ARM misconception, looking up a register, exception level, cache, extension or performance figure, finding the sources, or needing a quick-reference picker — plus the current state of Arm's business model and its actual market position. Companion to the other ARM skills."
---

# ARM: What's Live, Misconceptions, Numbers, and Sources

> **Part 6 of 6** of the *ARM: A Deep Dive* reference (plugin `arm-architecture-deep-dive`), covering §26–§31. Sibling skills: `arm-what-arm-is-licensing-families-and-isa-generations` (§0–§4), `arm-aarch64-exception-levels-memory-model-and-mmu` (§5–§9), `arm-vectors-atomics-numerics-and-security-architecture` (§10–§15), `arm-system-architecture-boot-and-virtualization` (§16–§20), `arm-cortex-m-toolchain-porting-and-performance` (§21–§25). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The architecture is documented and stable. Two things moved decisively. See §26 for Arm's business model, and its actual market position.

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

## §26. What's Live — checked August 2026

### 26.1 ⚠️ Arm started making chips — a 35-year break from the model
**⚠️ §2 → `arm-what-arm-is-licensing-families-and-isa-generations`'s licensing model changing at its foundation, and this is the most significant
strategic shift in the company's history.**

- **⚠️ WHAT HAPPENED.** ⚠️ **In March 2026, at its Arm Everywhere event, Arm announced
  Arm-designed SILICON PRODUCTS for the first time — the Arm AGI CPU, a data centre
  processor for agentic AI infrastructure.** ⚠️ **Arm's own framing is that it is extending
  its platform "beyond IP and Compute Subsystems (CSS) to include Arm-designed silicon
  products."** ⚠️ **One outlet notes the company had never done this in 35 years.**
- **⚠️ THE CHIP, as reported**: ⚠️ **136 Neoverse V3 cores per CPU at 3.7 GHz, TSMC 3nm,
  300 W TDP.** ⚠️ **A high-density air-cooled rack is claimed to deliver over 8,000 cores at
  36 kW with twice the performance of an equivalent x86 configuration at the same power;
  liquid-cooled configurations are claimed to scale past 45,000 cores per rack.**
  ⚠️ **Meta is the lead partner and co-developer, with other customers and ODMs reported.**
  ⚠️ **Development reportedly began in 2023.**
- **⚠️ THE PATH THERE WAS GRADUAL, and §2 → `arm-what-arm-is-licensing-families-and-isa-generations`'s CSS is the middle step.** ⚠️ **CSS are
  pre-integrated blueprints rather than bare cores; Arm reported 19 CSS licences with 11
  companies and five customers already shipping CSS-based chips, and claims first-generation
  CSS delivers double the royalty of ARMv9.** ⚠️ **Arm has also described CSS saving
  customers "80 engineering years."**
- **⚠️ THE ROYALTY LOGIC underneath all of this.** ⚠️ **ARMv9 is reported to command roughly
  double the royalty rate of ARMv8, and Arm reported v9 contributing over 50% of royalty
  revenue in late 2025.** ⚠️ **Moving from core IP → subsystem → chiplet → whole chip
  captures progressively more value per unit of silicon.**

> **⚠️ GOTCHA — this puts Arm in partial competition with its own licensees, and that
> tension is real.** ⚠️ **Analyst commentary notes the turnkey CPU directly substitutes for
> services design houses have traditionally provided, forcing them to reposition toward
> chiplet and 3D-integration work.**
> ⚠️ **It also changes Arm's risk profile fundamentally: ⚠️ core licensing carried no
> supply-chain responsibility, while subsystems and silicon demand coordination with
> foundries, packaging houses and firmware partners.** **⚠️ A company with 97% gross margins
> selling IP is a different business from one shipping chips.**
> **⚠️ And note the naming: "AGI CPU" is Arm's product name for agentic AI infrastructure —
> one outlet glosses it as "Artificial General Intelligence," which is marketing, not a
> technical claim.**

**⚠️ Sourcing note: the announcement and specifications come from Arm's own newsroom and
from trade press reporting the launch event.** ⚠️ **The performance claims — 2× per rack
versus x86 — are Arm's, made by the CEO, and are not independently verified here.**
⚠️ **A large share of the surrounding commentary is investment analysis with obvious
positions, and I have kept to the announcement facts.**

### 26.2 ⚠️ Where ARM actually is in the datacentre — and why the numbers disagree
**⚠️ §3 → `arm-what-arm-is-licensing-families-and-isa-generations`'s Neoverse story, with a measurement caveat that matters.**

- **⚠️ THE DEPLOYMENT PICTURE IS UNAMBIGUOUS.** ⚠️ **Arm reported in February 2026 that
  Neoverse CPUs had surpassed ONE BILLION CORES DEPLOYED.** ⚠️ **Every major hyperscaler has
  custom Arm silicon: AWS Graviton, Google Axion, Microsoft Cobalt, NVIDIA Grace/Vera —
  and Arm reported data centre royalty revenue more than doubling year on year for several
  consecutive quarters.**
- **⚠️ AWS is the proof case.** ⚠️ **Graviton is reported serving nearly 100,000 cloud
  customers and driving over half of AWS's CPU demand — Arm's own materials say Graviton
  powers over 50% of AWS's recent capacity.**

> **⚠️ GOTCHA — the market-share figures differ by a factor of two or three depending on
> what is being counted, and this is the thing to get right.**
> ⚠️ **IDC data reported in June 2026 put Arm-based machines at well over 45% of server
> market REVENUE.** ⚠️ **A separate analysis puts Arm at 15–23% of server CPU SHIPMENTS in
> 2025, up from around 5% in 2020.**
> **⚠️ Both can be true. Revenue share is inflated by AI servers, where an Arm CPU sits
> alongside expensive accelerators and the whole system counts** — ⚠️ **the same reporting
> notes accelerated servers were around 70.6% of all server revenue in Q1 2026.**
> ⚠️ **A third datum keeps it grounded: one report cites an analyst noting Arm's roughly
> $2 billion in AGI CPU sales are still not enough to reach 5% of overall market share.**
> **⚠️ When you see an ARM server share figure, ask: revenue or units, shipments or
> installed base, and does it count the CPU or the whole system.**

**⚠️ The driver is power, not performance** (see a computer-hardware reference §26.1):
⚠️ **cloud operators adopt Arm to lower cost per request and free campus power capacity for
AI racks.** ⚠️ **One market analysis puts it plainly — the shift has less to do with chip
performance than with energy economics under power-constrained AI scaling.**
**⚠️ The remaining constraint is software readiness**, ⚠️ **and one analyst's framing is
honest: a processor can look efficient on paper, but enterprise planners need container
support and database tuning before moving production workloads** (§23 → `arm-cortex-m-toolchain-porting-and-performance`).
**⚠️ Sourcing caution: several sources here are market-research firms selling forecast
reports, whose absolute figures I would not rely on.** ⚠️ **The billion-cores milestone and
the hyperscaler adoption are from Arm and are consistent with independent reporting; the
share figures are exactly where I would expect motivated numbers, hence the gotcha.**

---

## §27. Misconceptions

| Misconception | Correction |
|---|---|
| ARM is inherently more efficient than x86 | ⚠️ **Efficiency is an implementation property. The ISA isn't the barrier** (§1 → `arm-what-arm-is-licensing-families-and-isa-generations`, §25 → `arm-cortex-m-toolchain-porting-and-performance`) |
| "ARM performance" is a meaningful phrase | ⚠️ **Cortex-M0 and an Apple core share almost nothing** (§1 → `arm-what-arm-is-licensing-families-and-isa-generations`) |
| ARM is RISC and therefore simple | ⚠️ **AArch64 has ~1000 instructions. RISC/CISC is historical** (§6 → `arm-aarch64-exception-levels-memory-model-and-mmu`) |
| ARMv9 replaced ARMv8 | ⚠️ **It's built on ARMv8.5** (§4 → `arm-what-arm-is-licensing-families-and-isa-generations`) |
| Architecture version tells you the features | ⚠️ **Most are OPTIONAL. Check ID registers** (§4 → `arm-what-arm-is-licensing-families-and-isa-generations`) |
| AArch64 extends the 32-bit ISA | ⚠️ **It's a new instruction set. Different encoding** (§5 → `arm-aarch64-exception-levels-memory-model-and-mmu`) |
| ARM has conditional execution everywhere | ⚠️ **Dropped in AArch64. CSEL replaced it** (§5 → `arm-aarch64-exception-levels-memory-model-and-mmu`) |
| x86-correct concurrent code works on ARM | ⚠️ **Weak ordering. Silently broken, intermittently** (§8 → `arm-aarch64-exception-levels-memory-model-and-mmu`, §23 → `arm-cortex-m-toolchain-porting-and-performance`) |
| Use DMB for ordering | ⚠️ **LDAR/STLR are usually faster and clearer** (§8 → `arm-aarch64-exception-levels-memory-model-and-mmu`) |
| Atomics perform the same everywhere | ⚠️ **Without LSE you get exclusive retry loops** (§11 → `arm-vectors-atomics-numerics-and-security-architecture`) |
| A JIT works the same as on x86 | ⚠️ **I-cache and D-cache aren't coherent. Explicit maintenance** (§8 → `arm-aarch64-exception-levels-memory-model-and-mmu`, §23 → `arm-cortex-m-toolchain-porting-and-performance`) |
| Pages are 4 KB | ⚠️ **4/16/64 KB. Apple uses 16 KB** (§9 → `arm-aarch64-exception-levels-memory-model-and-mmu`) |
| SVE is just a wider NEON | ⚠️ **Vector-length agnostic — one binary, any width** (§10 → `arm-vectors-atomics-numerics-and-security-architecture`) |
| TrustZone makes a device secure | ⚠️ **TEEs have had serious vulnerabilities, and it's also a lock-down tool** (§13 → `arm-vectors-atomics-numerics-and-security-architecture`) |
| MTE catches every memory bug | ⚠️ **Probabilistic — 4-bit tags, 1-in-16 collisions** (§14 → `arm-vectors-atomics-numerics-and-security-architecture`) |
| Pointer authentication is unbreakable | ⚠️ **Signing gadgets and short MACs are real limits** (§14 → `arm-vectors-atomics-numerics-and-security-architecture`) |
| ARM boots like a PC | ⚠️ **No architectural BIOS. SystemReady certification is why servers do** (§19 → `arm-system-architecture-boot-and-virtualization`) |
| Cortex-M is a small Cortex-A | ⚠️ **Thumb-2 only, no MMU, hardware register stacking** (§21 → `arm-cortex-m-toolchain-porting-and-performance`) |
| ISRs need an assembly wrapper | ⚠️ **Not on Cortex-M. The NVIC stacks in hardware** (§21 → `arm-cortex-m-toolchain-porting-and-performance`) |
| char is signed | ⚠️ **Unsigned by default on ARM. Compiles silently** (§23 → `arm-cortex-m-toolchain-porting-and-performance`) |
| Porting is mostly recompiling | ⚠️ **True for app code; low-level code is where it bites** (§23 → `arm-cortex-m-toolchain-porting-and-performance`) |
| Arm only licenses IP | ⚠️ **It ships its own silicon as of March 2026** (§26.1) |
| Arm has 45% of the server market | ⚠️ **Of REVENUE. Units are 15-23%. Ask which** (§26.2) |
| Hyperscalers moved to Arm for speed | ⚠️ **Power, and freeing capacity for AI racks** (§26.2) |

---

## §28. Numbers

```
⚠️ AArch64 registers  ⚠️ 31 GP + zero register (vs 16 on x86-64)
⚠️ Instruction length  ⚠️ fixed 32-bit (AArch64) · 16/32 (Thumb-2)
⚠️ Exception levels  EL0-EL3 · ⚠️ × security state (2, or 3 with CCA)
⚠️ Page granules  ⚠️ 4 KB / 16 KB / 64 KB
⚠️ NEON  fixed 128-bit
⚠️ SVE  ⚠️ 128-2048 bit, implementation-defined, VL-agnostic
⚠️ MTE tags  ⚠️ 4-bit → 1-in-16 random collision
⚠️ AAPCS64  ⚠️ X0-X7 args · X29 FP · X30 LR · 16-byte stack align
⚠️ ⚠️ ARM AGI CPU (Mar 2026)  ⚠️ 136 Neoverse V3 cores · 3.7 GHz ·
   TSMC 3nm · 300 W TDP · >8,000 cores/rack at 36 kW air-cooled ·
   >45,000 liquid-cooled (⚠️ Arm's claims)
⚠️ Neoverse deployed  ⚠️ >1 billion cores (Arm, Feb 2026)
⚠️ Graviton  ⚠️ >50% of AWS recent capacity · ~100k customers
⚠️ ⚠️ Arm server share  ⚠️ >45% REVENUE (IDC) vs 15-23% UNITS —
   ⚠️ not the same question
⚠️ CSS licences  ⚠️ 19 with 11 companies; 5 shipping (Arm)
⚠️ ARMv9 royalty  ⚠️ ~2× ARMv8 rate (reported)
```

---

## §29. Sources

| Source | Why |
|---|---|
| **Arm Architecture Reference Manual (ARM ARM)** | ⚠️ **The authority. Free, enormous, and definitive** |
| **Arm Cortex/Neoverse Technical Reference Manuals** | ⚠️ **Per-core detail the ARM ARM doesn't give** |
| **Arm Developer documentation and learning paths** | Accessible entry point |
| **Sorin, Hill & Wood, *Memory Consistency and Cache Coherence*** | ⚠️ **§8 → `arm-aarch64-exception-levels-memory-model-and-mmu`. Free** |
| **"A Tutorial Introduction to ARM and POWER Relaxed Memory Models"** | ⚠️ **§8 → `arm-aarch64-exception-levels-memory-model-and-mmu` — the weak model made comprehensible** |
| **Trusted Firmware-A documentation** | ⚠️ **§19 → `arm-system-architecture-boot-and-virtualization`, and the code is readable** |
| **Arm SystemReady / SBSA / BSA specifications** | ⚠️ **§19 → `arm-system-architecture-boot-and-virtualization`** |
| **Yiu, *The Definitive Guide to Arm Cortex-M*** | ⚠️ **§21 → `arm-cortex-m-toolchain-porting-and-performance`** |
| **Pyeatt & Ughetta, *Modern Assembly Language Programming with the ARM Processor*** | §5–§6 → `arm-aarch64-exception-levels-memory-model-and-mmu` |
| **Arm's quarterly shareholder letters** | ⚠️ **§26 — primary, and read as an interested party** |
| **Linux kernel `Documentation/arch/arm64/`** | ⚠️ **Practical, current, and honest about quirks** |

---

## §30. Quick Reference

### 30.1 Picker
| Question | Where |
|---|---|
| Which ARM is this? | ⚠️ **Architecture, core, product — three questions** (§1 → `arm-what-arm-is-licensing-families-and-isa-generations`, §3 → `arm-what-arm-is-licensing-families-and-isa-generations`) |
| Can I use feature X? | ⚠️ **Check ID registers. Optional ≠ present** (§4 → `arm-what-arm-is-licensing-families-and-isa-generations`) |
| Why does my lock-free code fail? | ⚠️ **Weak memory ordering** (§8 → `arm-aarch64-exception-levels-memory-model-and-mmu`, §23 → `arm-cortex-m-toolchain-porting-and-performance`) |
| Which barrier do I need? | ⚠️ **Probably none — use LDAR/STLR** (§8 → `arm-aarch64-exception-levels-memory-model-and-mmu`) |
| Atomics are slow | ⚠️ **Check LSE is enabled in your build** (§11 → `arm-vectors-atomics-numerics-and-security-architecture`) |
| My JIT crashes | ⚠️ **Cache maintenance between I and D** (§8 → `arm-aarch64-exception-levels-memory-model-and-mmu`, §23 → `arm-cortex-m-toolchain-porting-and-performance`) |
| SVE or NEON? | ⚠️ **NEON for compatibility, SVE if the target has it** (§10 → `arm-vectors-atomics-numerics-and-security-architecture`) |
| How do I harden this? | ⚠️ **PAC + BTI + MTE, if silicon supports them** (§14 → `arm-vectors-atomics-numerics-and-security-architecture`) |
| Why won't this board boot a generic OS? | ⚠️ **No SystemReady certification** (§19 → `arm-system-architecture-boot-and-virtualization`) |
| Writing an ISR on Cortex-M | ⚠️ **Plain C function. Hardware stacks for you** (§21 → `arm-cortex-m-toolchain-porting-and-performance`) |
| Porting from x86 — what breaks? | ⚠️ **Memory ordering, intrinsics, char signedness** (§23 → `arm-cortex-m-toolchain-porting-and-performance`) |
| Is ARM taking over servers? | ⚠️ **Depends entirely on revenue vs units** (§26.2) |

### 30.2 Porting checklist
- [ ] ⚠️ **All synchronization uses language atomics, not `volatile`** (§8 → `arm-aarch64-exception-levels-memory-model-and-mmu`, §23 → `arm-cortex-m-toolchain-porting-and-performance`)
- [ ] ⚠️ **Lock-free code reviewed against the WEAK model** (§8 → `arm-aarch64-exception-levels-memory-model-and-mmu`)
- [ ] ⚠️ **Tested under load on real ARM hardware, not just emulation** (§23 → `arm-cortex-m-toolchain-porting-and-performance`)
- [ ] x86 intrinsics replaced or abstracted (§10 → `arm-vectors-atomics-numerics-and-security-architecture`, §23 → `arm-cortex-m-toolchain-porting-and-performance`)
- [ ] ⚠️ **`char` signedness assumptions found and fixed** (§23 → `arm-cortex-m-toolchain-porting-and-performance`)
- [ ] Page size not hardcoded to 4 KB (§9 → `arm-aarch64-exception-levels-memory-model-and-mmu`, §23 → `arm-cortex-m-toolchain-porting-and-performance`)
- [ ] ⚠️ **JIT or self-modifying code does cache maintenance** (§8 → `arm-aarch64-exception-levels-memory-model-and-mmu`)
- [ ] Unaligned access assumptions checked, especially in drivers (§23 → `arm-cortex-m-toolchain-porting-and-performance`)
- [ ] Floating-point exact-comparison tests reviewed (§12 → `arm-vectors-atomics-numerics-and-security-architecture`)
- [ ] ⚠️ **Build targets the right `-mcpu`/`-march` — LSE enabled** (§11 → `arm-vectors-atomics-numerics-and-security-architecture`, §22 → `arm-cortex-m-toolchain-porting-and-performance`)
- [ ] ⚠️ **Verified which optional features the target actually has** (§4 → `arm-what-arm-is-licensing-families-and-isa-generations`)
- [ ] Container images and dependencies available for arm64 (§23 → `arm-cortex-m-toolchain-porting-and-performance`)

---

## §31. Method

**§1–§25 → `arm-what-arm-is-licensing-families-and-isa-generations`, `arm-aarch64-exception-levels-memory-model-and-mmu`, `arm-vectors-atomics-numerics-and-security-architecture`, `arm-system-architecture-boot-and-virtualization`, `arm-cortex-m-toolchain-porting-and-performance` rests on published architecture** — **the ARM ARM specifies the exception model,
the memory model, translation regimes, the vector extensions and the security features, and
none of it needed verification.** ⚠️ **Where I have described a feature as optional or
version-gated, that is from the architecture's own feature-discovery model (§4 → `arm-what-arm-is-licensing-families-and-isa-generations`), which is
the single most practically important thing to internalize about ARM.**

**Two searches were run in August 2026**, on **Arm's business model** and **its datacentre
position** — ⚠️ **the first because §2 → `arm-what-arm-is-licensing-families-and-isa-generations`'s licensing model, which shaped the architecture
itself, has just changed at its foundation, and the second because ARM server share is
quoted constantly and the numbers in circulation are not measuring the same thing.**

**Confidence.** **High** in §8 → `arm-aarch64-exception-levels-memory-model-and-mmu` and §5 → `arm-aarch64-exception-levels-memory-model-and-mmu`, which are the sections I'd most want read.
⚠️ **The weak memory model is the difference that actually breaks things: x86-TSO hides
missing synchronization, ARM exposes it, and the resulting bugs are intermittent and
load-dependent — which is why §23 → `arm-cortex-m-toolchain-porting-and-performance` puts it first and says test on real hardware under load.**
⚠️ **§5 → `arm-aarch64-exception-levels-memory-model-and-mmu`'s account of what AArch64 deliberately REMOVED is the most instructive part of the
ISA: dropping universal predication and the PC-as-general-register were both giving up
elegant features because they obstruct out-of-order implementation, and that trade tells
you what a modern ISA is actually optimizing for.**
**⚠️ §21 → `arm-cortex-m-toolchain-porting-and-performance`'s hardware register stacking is the small delightful detail — it is why a Cortex-M
interrupt handler can be an ordinary C function.**

**High** on §26.1's core facts, which come from Arm's own newsroom: ⚠️ **the March 2026
announcement of Arm-designed silicon, the AGI CPU's core count and process node, and Meta as
lead partner.** ⚠️ **The performance claims are Arm's own and I have attributed them rather
than stating them.** **⚠️ The point I would most want carried is the structural one: core
licensing carried no supply-chain responsibility, and shipping silicon does — this changes
what kind of company Arm is, and it puts them in partial competition with licensees.**

**Moderate** on §26.2's share figures, and the gotcha IS the finding. ⚠️ **IDC reporting
puts Arm above 45% of server REVENUE while another analysis puts it at 15–23% of server CPU
SHIPMENTS, and both are defensible because AI servers inflate revenue share — the same
reporting has accelerated servers at around 70% of all server revenue.**
⚠️ **A third figure keeps it honest: an analyst noting Arm's roughly $2bn in AGI CPU sales
is under 5% of the overall market.** **⚠️ The billion-cores milestone and hyperscaler
adoption are solid; the percentage claims are exactly where motivated numbers live, and
several of my sources are market-research firms selling forecasts.**
