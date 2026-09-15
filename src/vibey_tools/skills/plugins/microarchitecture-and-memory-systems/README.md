# CPU, GPU, NPU and Memory Microarchitecture Plugin

How processors and memory systems actually execute code, and why performance so rarely matches the naive model. Architecture versus microarchitecture, pipelining, out-of-order execution, branch prediction and SIMD; cache organization, coherence, memory consistency models, virtual memory and prefetching; GPU microarchitecture and memory systems, NPUs and dataflow architectures, and numeric formats; DRAM internals, memory controllers, emerging interfaces, power and clocking, and microarchitectural security; then ISA design, simulation, how to measure any of it honestly, roofline and the fundamental limits, and specialization.

One reference, split into 6 skills along its section groups so a task loads only the part it needs. Section numbers (§N) are shared across the set and cross-references into a sibling skill are written as §N → `skill`. Reference, not tutorial: sections are independent, every claim is tagged by how durable it is (stable fundamentals vs. versioned specifics vs. genuinely contested questions), and a currency snapshot (checked August 2026) flags what goes stale first.

## Skills

- **uarch-pipelining-out-of-order-branch-prediction-and-simd** — Architecture Versus Microarchitecture, Pipelining, Out-of-Order Execution, Branch Prediction, and Execution Units and SIMD (§0–§5): Routing; Architecture versus Microarchitecture; Pipelining; ⚠️ Out-of-Order Execution; ⚠️ Branch Prediction; Execution Units and SIMD.
- **uarch-caches-coherence-consistency-and-virtual-memory** — Cache Organization, Cache Coherence, Memory Consistency Models, Virtual Memory and Translation, and Prefetching (§6–§10): Cache Organization; ⚠️ Cache Coherence; ⚠️ Memory Consistency Models; Virtual Memory and Translation; Prefetching.
- **uarch-gpu-npu-dataflow-and-numeric-formats** — GPU Microarchitecture, GPU Memory Systems, NPUs and Dataflow Architectures, and Numeric Formats (§11–§14): GPU Microarchitecture; GPU Memory Systems; ⚠️ NPUs and Dataflow Architectures; ⚠️ Numeric Formats.
- **uarch-dram-memory-controllers-power-and-security** — DRAM Internals, Memory Controllers, Emerging Memory Interfaces, Power and Clocking, and Microarchitectural Security (§15–§19): ⚠️ DRAM Internals; Memory Controllers; Emerging Memory Interfaces; Power and Clocking; ⚠️ Microarchitectural Security.
- **uarch-isa-simulation-measurement-roofline-and-specialization** — ISA Design, Simulation and Modelling, Measuring It, Roofline and Fundamental Limits, and Specialization (§20–§24): ISA Design; Simulation and Modelling; ⚠️ Measuring It; Roofline and Fundamental Limits; Specialization.
- **uarch-reference** — What's Live, Misconceptions, Numbers, and Books (§25–§30): What's Live; Misconceptions; Numbers; Books; Quick Reference; Method.
