# ARM: A Deep Dive Plugin

ARM in depth, from the licensing business that shapes the product families through to porting real software onto it. What "ARM" actually names, the licensing model, and the ISA generations; AArch64 register and instruction design, exception levels, the weak memory model, translation regimes, the vector extensions and atomics; the security architecture — TrustZone, pointer authentication, BTI, MTE and CCA; system architecture with GIC, AMBA, boot, firmware and virtualization; Cortex-M and embedded; and the practical business of toolchains, ABIs, porting from x86 and performance analysis.

One reference, split into 6 skills along its section groups so a task loads only the part it needs. Section numbers (§N) are shared across the set and cross-references into a sibling skill are written as §N → `skill`. Reference, not tutorial: sections are independent, every claim is tagged by how durable it is (stable fundamentals vs. versioned specifics vs. genuinely contested questions), and a currency snapshot (checked August 2026) flags what goes stale first.

## Skills

- **arm-what-arm-is-licensing-families-and-isa-generations** — What "ARM" Actually Names, the Licensing Model, Product Families, and ISA Generations (§0–§4): Routing; What "ARM" Actually Names; ⚠️ The Licensing Model; Product Families; ISA Generations.
- **arm-aarch64-exception-levels-memory-model-and-mmu** — AArch64, Instruction Set Characteristics, Exception Levels, the Memory Model, and MMU and Translation (§5–§9): ⚠️ AArch64; Instruction Set Characteristics; ⚠️ Exception Levels; ⚠️ The Memory Model; MMU and Translation.
- **arm-vectors-atomics-numerics-and-security-architecture** — Vector Extensions, Atomics and Synchronization, Floating Point and Numerics, TrustZone, Pointer Authentication, BTI and MTE, and CCA (§10–§15): ⚠️ Vector Extensions; Atomics and Synchronization; Floating Point and Numerics; ⚠️ TrustZone; ⚠️ Pointer Authentication, BTI and MTE; CCA and Realms.
- **arm-system-architecture-boot-and-virtualization** — big.LITTLE and DynamIQ, Interrupts and Timers, Interconnect, Boot and Firmware on ARM, and Virtualization (§16–§20): big.LITTLE and DynamIQ; Interrupts and Timers; Interconnect; ⚠️ Boot and Firmware on ARM; Virtualization.
- **arm-cortex-m-toolchain-porting-and-performance** — Cortex-M and Embedded, Toolchain and ABI, Porting from x86, Performance Analysis, and the Competitive Landscape (§21–§25): ⚠️ Cortex-M and Embedded; Toolchain and ABI; ⚠️ Porting from x86; Performance Analysis on ARM; The Competitive Landscape.
- **arm-reference** — What's Live, Misconceptions, Numbers, and Sources (§26–§31): What's Live; Misconceptions; Numbers; Sources; Quick Reference; Method.
