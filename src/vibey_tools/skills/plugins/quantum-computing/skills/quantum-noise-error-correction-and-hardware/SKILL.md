---
name: quantum-noise-error-correction-and-hardware
description: "Use when reasoning about real quantum hardware: what goes wrong (decoherence, gate errors, crosstalk), error mitigation vs correction, benchmarking (quantum volume, randomized benchmarking), barren plateaus, the idea of quantum error correction, the surface code and qLDPC codes, the 2024–2026 below-threshold breakthrough, magic states as the hidden cost, the hardware modalities (superconducting, trapped ion, neutral atom, photonic, spin, topological), the vendor roadmaps, and how to read a roadmap."
---

# Quantum Computing: Noise and NISQ, Error Correction, and Hardware

> **Part 2 of 5** of the *Quantum Computing* reference (plugin `quantum-computing`), covering §4–§7. Sibling skills: `quantum-foundations-and-algorithms` (§0–§3), `quantum-software-and-resource-estimation` (§8–§10), `quantum-applications-and-post-quantum-crypto` (§11–§13), `quantum-reference` (§14–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 → `quantum-reference` for the currency snapshot and what goes stale first.

> **How to read this.** Reference, not tutorial. Sections are independent. Three markers:
> - **[DURABLE]** — physics, mathematics, or complexity theory. Does not expire.
> - **[VERSIONED]** — hardware state, roadmaps, software versions, regulatory deadlines.
>   Moving fast; verify before relying on it.
> - **[CONTESTED]** — genuine scientific or strategic disagreement, of which this field
>   has an unusual amount.
>
> **⚠️ GOTCHA** boxes mark the misconceptions that produce bad technical decisions and
> bad business decisions.
>
> **The three framings that organize everything below:**
> 1. **A quantum computer is not a faster computer. It is a different computer with a
>    narrow set of exponential advantages.** For the overwhelming majority of workloads
>    there is no quantum speedup, and none is expected. The interesting question is never
>    "how fast" — it's "does this specific problem have exploitable structure?"
> 2. **Nearly every headline conflates physical qubits with logical qubits.** A distance-7
>    surface code uses **49 physical qubits to make one logical qubit**; breaking RSA-2048
>    needs millions of physical qubits. Any number quoted without specifying which kind is
>    nearly meaningless.
> 3. **The cryptographic migration is urgent independently of when the hardware
>    arrives.** "Harvest now, decrypt later" makes today's encrypted traffic a future
>    liability, and regulators have stopped waiting for hardware predictions and published
>    binding dates. §13 → `quantum-applications-and-post-quantum-crypto` is the section with real deadlines attached.

---

## §4. Noise and the NISQ Era

### 4.1 What goes wrong

**[DURABLE]** Quantum states are fragile in ways classical bits are not:
- **Decoherence** — coupling to the environment destroys the state. **T1** (energy
  relaxation / amplitude damping) and **T2** (dephasing) are the two lifetimes, and
  **T2 ≤ 2·T1** always.
- **Gate errors** — imperfect control. Single-qubit errors ~10⁻⁴–10⁻³, two-qubit errors
  ~10⁻³–10⁻² on current hardware, depending heavily on platform.
- **Measurement/readout errors** — often the largest single error source, ~1%.
- **Crosstalk** — operating one qubit disturbs its neighbours.
- **Leakage** — the qubit escapes the computational subspace into a third level.
- **Correlated and non-Markovian noise** — the assumption-breaker for many error models,
  and a live research area.

**The core tension**: circuit depth × error rate must stay small. At 10⁻³ two-qubit error,
you get roughly 1000 gates before errors dominate. **Useful algorithms need millions to
billions.** That gap is the entire justification for §5.

### 4.2 Error mitigation (not correction)

**[DURABLE] Mitigation reduces bias in expectation values; it does not fix the
computation.** The distinction matters: correction (§5) makes arbitrarily long computations
possible, mitigation buys you a factor at exponentially growing sampling cost.

- **Zero-noise extrapolation (ZNE)** — run at amplified noise levels, extrapolate to zero.
- **Probabilistic error cancellation (PEC)** — invert the noise channel by sampling;
  **provably correct, exponentially costly in sampling overhead**.
- **Readout error mitigation** — cheap, effective, do it always.
- **Dynamical decoupling** — pulse sequences that echo away slow dephasing during idle time.
- **Symmetry verification / post-selection** — throw away runs that violate a known
  conserved quantity.
- **Twirling / randomized compiling** — turn coherent errors into stochastic ones, which
  are much better behaved.

**⚠️ Every mitigation technique costs exponentially more shots as circuits grow.** They
extend the NISQ regime; they do not scale to useful algorithms.

### 4.3 Benchmarking

Beyond raw qubit count: **randomized benchmarking** and **cycle benchmarking** for gate
fidelity, **quantum volume** (IBM's single-number metric, now widely seen as saturating),
**CLOPS** (speed), **algorithmic qubits** (IonQ's metric — ⚠️ vendor-defined), and
**application-level benchmarks**. **[DURABLE] Be suspicious of any single-number metric,
especially one the vendor invented.**

### 4.4 Barren plateaus

**[DURABLE, and it's the most important negative result of the NISQ era.]** For many
parameterized quantum circuits, gradients vanish **exponentially in the number of qubits**,
making variational training (VQE, QAOA, QML) infeasible at scale. Causes include circuit
expressiveness, entanglement, noise, and global cost functions. Mitigations (local cost
functions, shallow structured ansätze, smart initialization) exist — but **there is a
significant result showing that provable absence of barren plateaus may imply classical
simulability**, i.e. the circuits you can train may be exactly the ones you didn't need a
quantum computer for. That tension is unresolved and it is central to §16.3 → `quantum-reference`.

---

## §5. Error Correction and Fault Tolerance

### 5.1 The idea

**[DURABLE]** No-cloning forbids naive redundancy, but you can encode one **logical qubit**
into many **physical qubits** and measure *stabilizers* — operators that reveal error
syndromes **without measuring (and collapsing) the logical state**. Then correct.

**The threshold theorem [DURABLE, and it's why the field exists]:** if physical error rates
are below a threshold, arbitrarily long computations become possible with polylogarithmic
overhead. The surface-code threshold is around **~1%**, which is why the field spent two
decades pushing gate fidelities toward it.

### 5.2 Codes

| Code | Overhead | Notes |
|---|---|---|
| **Surface code** | High (~1000:1 for useful rates) | 2D nearest-neighbour connectivity, high threshold. **The default for superconducting** |
| **Color codes** | Similar | Transversal gates are easier; lower threshold |
| **qLDPC codes** | **Much lower** | Requires long-range connectivity. **The most important recent development** — the main hope for reducing overhead |
| **Bosonic codes** (cat, GKP) | Different trade-off | Encode in an oscillator's infinite-dimensional space; hardware-efficient |
| **Concatenated codes** | Historically first | Simple analysis, worse thresholds |

### 5.3 The 2024–2026 breakthrough

**[VERSIONED — this is what actually changed.]** **Google's Willow chip (105
superconducting qubits, announced 9 December 2024) demonstrated "below threshold" error
correction for the first time on real hardware**: running the surface code at **distance
3, 5, and 7 on the same chip**, the logical error rate fell **monotonically — roughly
halving with each increase in code distance**.

**Why that specific result mattered [DURABLE reasoning]:** before Willow, nobody had
publicly demonstrated that *adding more physical qubits actually lowered the logical error
rate*. Every prior scaling attempt had added more error than it corrected. Willow
eliminated the legitimate scientific objection that scalable error correction might be
physically impossible on superconducting hardware.

**⚠️ What it did not do:** demonstrate fault tolerance at useful scale. **A distance-7
surface code uses 49 physical qubits to produce one logical qubit**; Shor's on RSA-2048
requires millions of them. **The pathway is now credible. The pathway is still long.**

### 5.4 Magic states — the hidden cost

**[DURABLE]** Clifford gates can be done transversally and cheaply; **T gates cannot**.
The standard solution is **magic state distillation**: consume many noisy states to produce
one clean `|T⟩`. **This dominates the resource cost of fault-tolerant algorithms** — often
the majority of the qubits and time in a resource estimate (§9 → `quantum-software-and-resource-estimation`). Reducing or eliminating
distillation overhead (transversal T gates, better codes) is one of the two remaining
engineering problems, alongside raw physical qubit scaling.

---

## §6. Hardware Modalities

**[DURABLE] No modality has won, and each fails differently.** The trade-off structure is
stable even as the numbers move.

| Modality | Players | Strengths | Weaknesses |
|---|---|---|---|
| **Superconducting** | IBM, Google, Rigetti, IQM | Fast gates (ns), fab-compatible, most mature | Short coherence (µs), millikelvin dilution fridges, nearest-neighbour connectivity, crosstalk |
| **Trapped ion** | Quantinuum, IonQ | **Best gate fidelities**, all-to-all connectivity, identical qubits, long coherence | **Slow gates (µs–ms)**, scaling requires shuttling or photonic interconnects |
| **Neutral atom** | QuEra, Pasqal, Atom Computing | **Massive qubit counts** (1000+ demonstrated), reconfigurable geometry, room-temperature-ish optics | Slower operations, atom loss, younger |
| **Photonic** | PsiQuantum, Xanadu | Room temperature, natural networking, fast | Probabilistic gates, photon loss, needs enormous component counts |
| **Spin / silicon** | Intel, Diraq, academic | CMOS-compatible, tiny footprint, potential to leverage existing fabs | Least mature; variability between devices |
| **Topological** | Microsoft | Error protection built into the physics | ⚠️ **Most scientifically contested** (§16.5 → `quantum-reference`) |
| **Annealing** | D-Wave | Thousands of qubits *now*, real commercial deployments | **Not universal**; advantage disputed (§16.4 → `quantum-reference`) |

**[DURABLE] The comparison metric that matters is not qubit count.** It's the combination
of **two-qubit gate fidelity**, **connectivity**, **gate speed**, **coherence relative to
gate time**, and **whether the architecture has a credible scaling path**. A vendor quoting
only qubit count is telling you which number flatters them.

---

## §7. Where the Hardware Actually Is

**[VERSIONED — highest decay risk in this document. Verify everything here.]**

### 7.1 The roadmaps

**IBM** publishes the most specific named-deliverable roadmap in the industry:
- **Nighthawk** — 120-qubit processor with 218 next-generation tunable couplers in a square
  lattice; ~30% more circuit complexity than the Heron family. Targeted to run
  **~7,500 gates in 2026** with up to three 120-qubit modules (360 qubits), **10,000 gates
  in 2027**, **15,000 in 2028**.
- **Loon** — debuted 2025 with c-couplers linking qubits across the chip, the architecture
  needed for qLDPC codes.
- **Kookaburra** — the first module built around modular Quantum System Two, ~4,158 physical
  qubits across the connected cluster; **the first IBM module capable of storing information
  in qLDPC memory and processing it with an attached logical processing unit**.
- **Starling (2029)** — **200 logical qubits from roughly 10,000 physical qubits, running
  100 million operations.** The fault-tolerance target.
- **Blue Jay (2033)** — **2,000 logical qubits, 1 billion operations.**
- IBM states it will **prototype a real-time error-correction decoder in 2026**.

**Google** publishes a six-milestone roadmap. It places itself at **Milestone 2** (~100
physical qubits, logical error rate ~10⁻²) with Willow. Milestone 3 is a long-lived logical
qubit (~10³ physical qubits, 10⁻⁶ logical error). **Milestone 6 is the endpoint: ~10⁶
physical qubits with a 10⁻¹³ logical error rate.** ⚠️ **Google presents the million-qubit
figure as a destination, not a near-term specification** — and the gap from ~100-qubit
chips is enormous.

**Others**: **PsiQuantum** targets a million-qubit utility-scale photonic machine on a
similar horizon. **DARPA's Quantum Benchmarking Initiative** funds Atom Computing,
Photonic Inc., Oxford Ionics (now part of IonQ), and others on parallel fault-tolerance
tracks toward 2033 operational milestones. **Quantinuum** and **Microsoft** have reported
logical-qubit milestones on the H-series trapped-ion systems.

### 7.2 How to read a roadmap

**[DURABLE] Roadmaps are marketing documents with engineering inside them.** The questions
that separate signal from noise:
1. **Physical or logical qubits?** (§0 → `quantum-foundations-and-algorithms` framing 2)
2. **What two-qubit fidelity**, and measured how?
3. **Is the connectivity claim about the chip or about a hypothetical module?**
4. **Has the milestone been demonstrated, or is it a target year?**
5. **Peer-reviewed, preprint, or press release?**
6. **What did the previous roadmap promise for this year, and did it land?** — the single
   most informative question, and the one nobody asks.
