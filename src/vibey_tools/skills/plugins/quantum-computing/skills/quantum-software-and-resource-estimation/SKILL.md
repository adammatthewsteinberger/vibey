---
name: quantum-software-and-resource-estimation
description: "Use when programming a quantum computer or assessing a quantum claim: the software layers, the frameworks (Qiskit, Cirq, PennyLane, CUDA-Q, OpenQASM, transpilers), what programming quantum computers is actually like, resource estimation from algorithm to logical to physical qubits, the canonical RSA-2048 example, why quadratic speedups often evaporate, the advantage vocabulary, the verification problem, dequantization as the pattern to watch for, and the 2026 state of the quantum-advantage debate."
---

# Quantum Computing: The Software Stack, Resource Estimation, and Evaluating Advantage Claims

> **Part 3 of 5** of the *Quantum Computing* reference (plugin `quantum-computing`), covering §8–§10. Sibling skills: `quantum-foundations-and-algorithms` (§0–§3), `quantum-noise-error-correction-and-hardware` (§4–§7), `quantum-applications-and-post-quantum-crypto` (§11–§13), `quantum-reference` (§14–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §8. The Software Stack

### 8.1 The layers

```
Application / domain library   (chemistry, finance, optimization)
  ↓
Algorithm / modeling layer     (Qmod, high-level synthesis)
  ↓
High-level SDK                 (Qiskit, Cirq, PennyLane, Q#, CUDA-Q)  ← most people live here
  ↓
Compilation / transpilation    (Qiskit transpiler, PyTKET) — routing, gate synthesis,
                                optimization, error-mitigation insertion
  ↓
Instruction-set language       (OpenQASM 3, Quil)
  ↓
Pulse-level control            (microsecond-timescale hardware control)
  ↓
Physical hardware
```

### 8.2 The frameworks

| Framework | Owner | Best at |
|---|---|---|
| **Qiskit** | IBM | The most feature-rich and most-taught. Circuits, noise modeling, dynamic circuits, native OpenQASM 3. **Start here if you want the biggest tutorial ecosystem** |
| **Cirq** | Google-affiliated | More explicit about hardware; rewards wanting to understand what the device does |
| **PennyLane** | Xanadu | **Quantum machine learning and autodiff.** Integrates with JAX, PyTorch, TensorFlow; broad plugin support across hardware |
| **CUDA-Q** | NVIDIA | Hybrid quantum-classical across GPUs, CPUs, and QPUs. The HPC-integration play |
| **Q#** | Microsoft | A dedicated language; teaches algorithm structure cleanly |
| **Braket** | AWS | Managed multi-vendor cloud access |
| **PyTKET** | Quantinuum | Compilation and optimization; often the best transpiler |
| **Ocean** | D-Wave | Annealing / QUBO |
| **Stim**, **Mitiq**, **Qualtran** | Community | Stabilizer simulation (fast QEC simulation), error mitigation, resource estimation |

**[DURABLE] Transpilation is where the practical difficulty lives.** Your abstract circuit
must be mapped onto real hardware with limited connectivity — inserting SWAP networks,
decomposing into native gates, and optimizing depth. **On a nearest-neighbour device, SWAP
insertion can multiply your gate count several-fold**, and this is invisible in the code
you wrote. Always look at the transpiled circuit, not the one you authored.

### 8.3 What programming quantum computers is actually like

**[DURABLE] Closer to embedded systems or FPGA design than to normal software
engineering**: severe resource constraints (tens to a few hundred qubits, strict depth
limits before errors dominate), no debugger in any conventional sense (measurement destroys
the state), **statistical rather than deterministic validation** (you check error rates,
not outputs), and algorithms usually verified mathematically *before* they're tested.

Practical workflow: **write it, simulate it small (≤~30 qubits on a laptop, ~40–50 on a
cluster), verify against a classical reference, then run on hardware and expect it to look
worse.** Simulators are where nearly all learning happens.

---

## §9. Resource Estimation

**[DURABLE] "How many qubits do I need?" is the question that separates serious evaluation
from hype, and the answer is almost always much larger than the headline suggests.**

### 9.1 The chain

```
abstract algorithm
  → gate count and depth (in T gates and Cliffords — count T gates specifically)
    → logical qubit count and logical circuit volume
      → CHOOSE A CODE and a target logical error rate
        → code distance d (set by how long the computation runs)
          → physical qubits per logical qubit (surface code ≈ 2d² per logical qubit)
            → + MAGIC STATE FACTORIES (often the majority of the footprint, §5.4)
              → total physical qubits, and wall-clock runtime
```

### 9.2 The canonical example: breaking RSA-2048

**[DURABLE as a structure; the specific numbers are [VERSIONED] and have fallen
substantially over the last decade as the algorithms improved.]** Published estimates have
ranged from roughly **20 million noisy physical qubits over ~8 hours** (Gidney–Ekerå 2019,
the most-cited figure) downward as factoring circuits and codes have improved. Current
hardware is in the **hundreds** of physical qubits.

**⚠️ Do not quote a single number as settled.** The estimates depend on assumed physical
error rate, code choice, cycle time, and the specific factoring circuit — and they have
been revised downward repeatedly. **The direction of travel matters more than any point
estimate**, and it is downward.

### 9.3 Why quadratic speedups often evaporate

**[DURABLE, and this is the most under-appreciated result in practical quantum computing.]**
Grover-type quadratic speedups must overcome:
- **Error-correction overhead** — every logical operation costs many physical ones.
- **Slow logical clock rates** — a logical gate takes many physical cycles (microseconds to
  milliseconds effective).
- **No parallelism advantage** — you can't parallelize Grover the way you parallelize a
  classical search across a datacenter.

The consequence: **for many realistic problem sizes, a classical cluster beats a
fault-tolerant quantum computer running a quadratically-faster algorithm.** Quadratic
speedups need enormous problem instances before they pay. **Exponential speedups are the
ones that survive the overhead**, which is why §3 → `quantum-foundations-and-algorithms`'s split between proven-exponential and
heuristic matters so much commercially.

---

## §10. Evaluating Quantum Advantage Claims

### 10.1 The vocabulary

- **Quantum supremacy / advantage** — outperforming the best classical approach on *some*
  well-defined task, useful or not.
- **Quantum utility** — practical usefulness; the emphasis shifts from beating classical
  to delivering value.
- **Verifiable advantage** — advantage where the answer's correctness can actually be
  checked. **[DURABLE]** This is the crux (§10.2).

### 10.2 The verification problem

**[DURABLE] This is the field's deepest methodological difficulty**: if no classical
computer can perform the calculation, how do you know the quantum answer is right? The
approaches:
- **Simulate smaller instances** and extrapolate — indirect, and the basis of most early
  claims.
- **Complexity-theoretic hardness arguments** plus a device-dependent fidelity certificate.
- **Peaked circuits** — circuits whose output concentrates on a single known bitstring, so
  correctness is checkable by comparison.
- **Structural verification** — problems where checking is easier than solving.

There is a serious argument, made in the applications literature, that **verifiability is a
necessary (though insufficient) condition for a quantum algorithm to be useful** — which
would rule out advantage claims based purely on sampling from a scrambled quantum state.
The reasoning: if you can efficiently spoof the output with no detectable performance
change, spoofing is easier than building the computer.

### 10.3 Dequantization — the pattern to watch for

**[DURABLE] Multiple proposed quantum advantages have been eliminated by improved classical
algorithms**, and this has happened often enough to be the default hypothesis rather than a
surprise. The history: **Google's 2019 Sycamore supremacy claim** (200 seconds vs. an
estimated 10,000 classical years) was followed by **years of improved classical simulation
partially closing the gap**; boson-sampling claims from USTC and Xanadu met the same
tug-of-war. **Ewin Tang's dequantization results** removed the claimed exponential speedup
from a family of quantum recommendation and machine-learning algorithms outright.

**A 2026 example of the pattern in real time**: a heuristic quantum advantage claim using
**peaked circuits on Quantinuum's 56-qubit H2** (October 2025, with estimated classical
runtimes of years for the largest instances) was followed in **April 2026 by an IBM Quantum
paper demonstrating efficient classical simulation of those same circuits**. The claim and
the refutation came from within the field, six months apart.

**⚠️ The checklist for any advantage claim:**
1. **Is the task useful, or contrived for the demonstration?**
2. **Is the result verifiable, and how?**
3. **What is it compared against — the best classical algorithm, or a convenient one?**
4. **Have classical researchers had time to attempt a match?** (Give it 6–18 months.)
5. **Peer-reviewed, or a press release timed to an earnings call?**
6. **Does the claim survive if you use a GPU cluster and a good tensor-network method?**

### 10.4 The 2026 state of the debate

**[VERSIONED and [CONTESTED].]** On **30 July 2026, IBM coordinated three announcements**
around arXiv preprints, presenting them collectively as evidence that quantum computing had
entered "the quantum advantage era," with IBM Research director Jay Gambetta using that
phrase. The three results addressed the same problem — how to trust output no classical
machine can check — from different directions, and **critically, they do not carry equal
evidentiary weight**: the IBM/University of Chicago paper makes an explicit advantage claim
backed by complexity-theoretic hardness arguments and a device-dependent fidelity
certificate, while the Qedma and Algorithmiq papers make **more empirical claims about
regimes where tested classical methods become unreliable**. One result ran an encoded
circuit using **70 logical qubits through thousands of logical operations with a logical
error rate roughly 10× lower than the underlying physical rate**, finishing in about 15
minutes.

**The fair reading**: the verification advances are real and substantive. Whether three
results at three different evidentiary levels justify declaring an era is a separate
question, and reasonable people in the field answer it differently. **The broader 2026
consensus is roughly: advantage on contrived tasks has likely been achieved; the live
argument is over whether usefulness should be a requirement for the term at all.**
