---
name: quantum-foundations-and-algorithms
description: "Use when explaining or learning how quantum computing works and what it can do: the qubit, superposition, entanglement, interference, and measurement, gates and circuits, the misconceptions up front, the complexity picture (BQP, what quantum computers cannot do), and the algorithm canon — Shor, Grover, HHL, VQE/QAOA, quantum simulation — with their honest speedup claims. Includes the router for the whole quantum-computing reference."
---

# Quantum Computing: Foundations, Capabilities and Limits, and the Algorithm Canon

> **Part 1 of 5** of the *Quantum Computing* reference (plugin `quantum-computing`), covering §0–§3. Sibling skills: `quantum-noise-error-correction-and-hardware` (§4–§7), `quantum-software-and-resource-estimation` (§8–§10), `quantum-applications-and-post-quantum-crypto` (§11–§13), `quantum-reference` (§14–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §0. Routing

### 0.1 The question router

| Asked about... | Go to |
|---|---|
| What a qubit actually is; the math | §1 |
| What quantum computers can/can't do | §2 |
| The algorithms and their real speedups | §3 |
| Noise, decoherence, error mitigation | §4 → `quantum-noise-error-correction-and-hardware` |
| Error correction and fault tolerance | §5 → `quantum-noise-error-correction-and-hardware` |
| Hardware modalities and trade-offs | §6 → `quantum-noise-error-correction-and-hardware` |
| Vendor roadmaps and current state | §7 → `quantum-noise-error-correction-and-hardware` |
| The software stack and how to program | §8 → `quantum-software-and-resource-estimation` |
| Resource estimation ("how many qubits do I need?") | §9 → `quantum-software-and-resource-estimation` |
| Quantum advantage claims and how to judge them | §10 → `quantum-software-and-resource-estimation` |
| Applications: chemistry, optimization, ML, finance | §11 → `quantum-applications-and-post-quantum-crypto` |
| Quantum networking, sensing, QKD | §12 → `quantum-applications-and-post-quantum-crypto` |
| Post-quantum cryptography and migration | §13 → `quantum-applications-and-post-quantum-crypto` |
| Getting started; learning path | §14 → `quantum-reference` |
| "Don't believe this" — myths and anti-patterns | §15 → `quantum-reference` |
| "Which side is right?" | §16 → `quantum-reference` (contested) |
| "Is this still current?" | §17 → `quantum-reference` |
| Books, papers, people | §18 → `quantum-reference` |

---

## §1. Foundations

### 1.1 The qubit

**[DURABLE]** A classical bit is 0 or 1. A qubit is a unit vector in a two-dimensional
complex Hilbert space:

```
|ψ⟩ = α|0⟩ + β|1⟩        where α, β ∈ ℂ  and  |α|² + |β|² = 1
```
`α` and `β` are **probability amplitudes**. On measurement in the computational basis you
get `0` with probability `|α|²` and `1` with probability `|β|²`, **and the state collapses**.

**n qubits require 2ⁿ complex amplitudes to describe.** 300 qubits is more amplitudes than
there are atoms in the observable universe. **This is the entire source of the hope** — and
also the source of the most persistent misconception (§1.4).

### 1.2 The four things that make it work

| Property | What it means | Why it matters |
|---|---|---|
| **Superposition** | A state can be a linear combination of basis states | You can act on many amplitudes at once |
| **Interference** | Amplitudes are complex and can cancel | **This is the actual mechanism.** Algorithms work by making wrong answers destructively interfere |
| **Entanglement** | Joint states not expressible as a product of individual states | Correlations with no classical analogue; the source of exponential state-space |
| **Measurement** | Probabilistic, and destroys superposition | **The bottleneck.** You get n bits out of a 2ⁿ-amplitude state |

**[DURABLE] Interference, not superposition, is the resource.** The naive story —
"it tries all answers in parallel" — is wrong (§1.4). A quantum algorithm works only if you
can arrange the amplitudes so that wrong answers cancel and right ones reinforce. **That
arrangement requires exploitable mathematical structure in the problem**, which is why
quantum speedups are rare and specific rather than general.

### 1.3 Gates and circuits

**Single-qubit gates** are 2×2 unitary matrices — rotations on the Bloch sphere:
- **X** (NOT), **Y**, **Z** — the Pauli gates.
- **H** (Hadamard) — creates superposition: `H|0⟩ = (|0⟩+|1⟩)/√2`. The workhorse.
- **S**, **T** — phase gates. **The T gate is the expensive one** (§5.4 → `quantum-noise-error-correction-and-hardware`, §9 → `quantum-software-and-resource-estimation`).
- **Rx(θ), Ry(θ), Rz(θ)** — arbitrary rotations.

**Two-qubit gates** create entanglement: **CNOT**, **CZ**, **iSWAP**, and the
hardware-native ones (**Mølmer–Sørensen** on ions). **[DURABLE] Two-qubit gates are
roughly an order of magnitude worse in fidelity than single-qubit gates on every
platform**, and they are what limits circuit depth.

**Universality**: `{H, T, CNOT}` is universal — any unitary can be approximated to
arbitrary precision. **Clifford gates alone (H, S, CNOT) are NOT universal and are
classically simulable in polynomial time (Gottesman–Knill).** This is why the T gate is
both essential and expensive: **it's precisely the non-classical part.**

**No-cloning theorem [DURABLE]**: an unknown quantum state cannot be copied. This forbids
naive error correction by redundancy (hence §5 → `quantum-noise-error-correction-and-hardware`), forbids "just measure and retry"
debugging, and underlies QKD's security argument (§12 → `quantum-applications-and-post-quantum-crypto`).

**Reversibility**: quantum gates are unitary and therefore reversible. Classical
irreversible operations must be embedded reversibly, which costs ancilla qubits — a real
factor in resource estimates.

### 1.4 The misconceptions, up front

> **⚠️ GOTCHA — "It tries all possibilities in parallel."** This is the single most
> damaging popular framing. You *can* put a register in superposition over all inputs, but
> **measurement gives you one random outcome.** Without interference engineering, that's
> just an expensive random number generator. Grover's quadratic (not exponential) speedup
> exists precisely because unstructured search offers no structure to interfere against —
> and **Grover's is provably optimal**, so no cleverness gets you further.

> **⚠️ GOTCHA — "Exponentially more storage."** 2ⁿ amplitudes exist in the mathematics, but
> **you cannot read them out.** n qubits yield n classical bits per measurement. Quantum
> computers are not memory devices, and **there is no efficient way to load a large
> classical dataset into a quantum state** — the QRAM problem, which quietly invalidates
> many proposed quantum machine-learning speedups (§11.3 → `quantum-applications-and-post-quantum-crypto`).

---

## §2. What Quantum Computers Can and Cannot Do

### 2.1 The complexity picture

**[DURABLE]** **BQP** (bounded-error quantum polynomial time) is the class of problems a
quantum computer solves efficiently. Known relationships:
- **P ⊆ BQP ⊆ PSPACE.** Quantum computers can do everything classical ones can.
- **BQP is not known to contain NP.** ⚠️ **Quantum computers are not believed to solve
  NP-complete problems efficiently.** This is the most consequential fact in the field and
  the most frequently misreported.
- **Factoring is in BQP** and is *not* believed NP-complete — it's in NP ∩ co-NP, suspected
  to be strictly between P and NP-complete. **Shor's algorithm exploits a specific
  structure (periodicity), not general search power.**
- Grover gives **quadratic** speedup on unstructured search — so for NP-complete problems
  you get √(2ⁿ) instead of 2ⁿ, which is a real but modest improvement that **does not make
  intractable problems tractable**.

**[DURABLE] The honest summary of where speedups live:**

| Speedup | Problems | Confidence |
|---|---|---|
| **Exponential** | Factoring, discrete log, **simulating quantum systems**, some hidden-subgroup and number-theoretic problems | High for these specific cases |
| **Polynomial (usually quadratic)** | Unstructured search, some optimization, Monte Carlo amplitude estimation | High, but the constant factors and error-correction overhead may eat it (§9.3 → `quantum-software-and-resource-estimation`) |
| **Claimed but contested** | Most optimization heuristics, most quantum machine learning | **Low.** Many have been "dequantized" (§10.3 → `quantum-software-and-resource-estimation`) |
| **None expected** | Databases, web serving, general software, most business computing | Very high |

**[DURABLE] The strongest and least-hyped case is quantum simulation.** Feynman's original
1982 motivation: simulating quantum systems on classical computers costs exponential
resources; a quantum computer simulates them natively. Chemistry and materials science
remain the most defensible application, and notably, **it's the one where the exponential
advantage isn't in doubt.**

---

## §3. The Algorithm Canon

| Algorithm | Does | Speedup | Reality check |
|---|---|---|---|
| **Deutsch–Jozsa** | Distinguishes constant vs. balanced functions | Exponential (oracle) | Pedagogical only — no use |
| **Bernstein–Vazirani**, **Simon's** | Hidden string / hidden period | Exponential (oracle) | Pedagogical; Simon's inspired Shor |
| **Shor's (1994)** | Factoring, discrete log | **Exponential** | ⚠️ **Breaks RSA, DH, ECC.** Needs millions of physical qubits (§9.2 → `quantum-software-and-resource-estimation`) |
| **Grover's (1996)** | Unstructured search | **Quadratic**, provably optimal | Halves effective symmetric key strength → AES-256 stays safe |
| **Quantum Phase Estimation** | Eigenvalues of a unitary | — | The subroutine underneath Shor and much of chemistry |
| **HHL (2009)** | Linear systems `Ax=b` | Exponential *with heavy caveats* | ⚠️ Sparse/well-conditioned A only; prepares `|x⟩`, doesn't give you x; needs QRAM. **Often dequantizable** |
| **Quantum simulation** (Trotter, qubitization, LCU) | Simulate quantum systems | **Exponential** | **The most defensible application** |
| **Amplitude estimation** | Monte Carlo | Quadratic | Finance interest; overheads are severe |
| **VQE** | Ground-state energies | **Heuristic — no proven speedup** | NISQ-era workhorse; ⚠️ barren plateaus (§4.4 → `quantum-noise-error-correction-and-hardware`) |
| **QAOA** | Combinatorial optimization | **Heuristic — no proven speedup** | Heavily studied; **classical algorithms often match or beat it** |
| **Quantum annealing** (D-Wave) | Ising/QUBO problems | **Disputed** | A different model entirely; not universal; §16.4 → `quantum-reference` |

**[DURABLE] Note the split.** The algorithms with *proven* exponential speedups all need
fault-tolerant hardware that doesn't exist yet. The algorithms that run on today's hardware
(VQE, QAOA) are **heuristics with no proven advantage**. That gap is the central honest
fact about the field's present moment, and most vendor messaging is designed to obscure it.
