# Assembly Programming Plugin

A deep technical reference for assembly-language programming: when assembly is and isn't the right tool, the major ISAs (x86-64, AArch64/ARM64, RISC-V, plus embedded and historical), machine-level fundamentals, calling conventions and ABIs, assembler syntax and toolchains, SIMD and vector programming, performance engineering on out-of-order superscalar hardware, inline assembly and intrinsics, systems-level and cryptographic/constant-time assembly, and reading disassembly.

One reference, split into 4 skills along its section groups so a task loads only the part it needs. Section numbers (§N) are shared across the set and cross-references into a sibling skill are written as §N → `skill`. Reference, not tutorial: sections are independent, every claim is tagged by how durable it is (stable fundamentals vs. versioned specifics vs. genuinely contested questions), and a currency snapshot (verified August 2026) flags what goes stale first.

## Skills

- **assembly-fundamentals-and-isas** — Fundamentals and ISAs (§0–§5): Routing; The Machine Model; x86-64; AArch64 (ARM64); RISC-V; Other ISAs Worth Knowing.
- **assembly-toolchain-performance-and-simd** — ABIs, Toolchain, Disassembly, Performance, and SIMD (§6–§10): Calling Conventions and ABIs; Assemblers and Toolchain; Reading Disassembly; Performance; SIMD and Vector.
- **assembly-systems-crypto-and-inline** — Systems, Constant-Time, Inline Assembly, and Debugging (§11–§14): Systems Assembly; Cryptographic and Constant-Time Assembly; Inline Assembly and Intrinsics; Debugging, Testing, and Verification.
- **assembly-reference** — Anti-Patterns, Contested Questions, Currency, and Canon (§15–§20): Anti-Patterns; Contested Questions; Currency Snapshot; The Canon; Quick Reference; Sources and Method.
