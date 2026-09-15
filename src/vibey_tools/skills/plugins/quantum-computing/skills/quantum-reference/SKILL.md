---
name: quantum-reference
description: "Use when learning quantum computing from scratch, debunking myths and anti-patterns, weighing contested questions (when a cryptographically-relevant quantum computer arrives, whether advantage has been achieved, whether NISQ is a dead end, annealing and optimization, topological qubits, whether the field is overinvested, whether your organization should act now), checking whether a hardware or roadmap claim is still current (snapshot verified August 2026), finding the books, papers, and people, or needing the numbers, the checklist for evaluating any quantum claim, and what to actually do. Companion to the other quantum-computing skills."
---

# Quantum Computing: Learning It, Myths, Contested Questions, Currency, and Canon

> **Part 5 of 5** of the *Quantum Computing* reference (plugin `quantum-computing`), covering §14–§20. Sibling skills: `quantum-foundations-and-algorithms` (§0–§3), `quantum-noise-error-correction-and-hardware` (§4–§7), `quantum-software-and-resource-estimation` (§8–§10), `quantum-applications-and-post-quantum-crypto` (§11–§13). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 below for the currency snapshot and what goes stale first.

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

## §14. Learning It

**[DURABLE] Prerequisites, honestly:** **linear algebra is essential and non-negotiable**
(complex vector spaces, unitary and Hermitian matrices, tensor products, eigendecomposition
— tensor products in particular are where most people stall). Probability, and comfort with
complex numbers. **Physics background is helpful but genuinely not required** for the
computing side. Programming: Python.

**The path**: linear algebra → qubits and single-qubit gates → multi-qubit gates and
entanglement → the standard algorithms (Deutsch–Jozsa → Bernstein–Vazirani → Grover →
Shor) → noise → error correction → whichever application domain you care about.

**⚠️ The failure mode is skipping the linear algebra.** Every popular-science analogy
(the coin that's both heads and tails, "trying all answers at once") actively obstructs
understanding, and you will have to unlearn them. **Work through Nielsen & Chuang's early
chapters or Qiskit's textbook with the math in front of you**, and run everything on a
simulator as you go.

---

## §15. Myths and Anti-Patterns

| Claim / behaviour | Reality |
|---|---|
| "Tries all possibilities in parallel" | Measurement returns one outcome. **Interference is the mechanism** (§1.2 → `quantum-foundations-and-algorithms`, §1.4 → `quantum-foundations-and-algorithms`) |
| "Solves NP-complete problems efficiently" | **BQP is not believed to contain NP** (§2.1 → `quantum-foundations-and-algorithms`). Grover is quadratic and provably optimal |
| "Exponentially more storage" | 2ⁿ amplitudes exist; **you get n bits out**. No efficient classical-data loading (§1.4 → `quantum-foundations-and-algorithms`, §11.3 → `quantum-applications-and-post-quantum-crypto`) |
| "N qubits" without saying which kind | **Physical ≠ logical.** ~49 physical per logical at distance 7 (§0 → `quantum-foundations-and-algorithms`, §5.3 → `quantum-noise-error-correction-and-hardware`) |
| "Will replace classical computers" | Co-processors for specific subroutines. Everything else stays classical |
| "Quantum computers are just faster" | Different computational model with narrow advantages |
| Comparing a quantum result to a naive classical baseline | Compare against the **best** classical method, on a GPU cluster, with tensor networks (§10.3 → `quantum-software-and-resource-estimation`) |
| Treating a supremacy claim as permanent | **Multiple claims have been dequantized** (§10.3 → `quantum-software-and-resource-estimation`). Wait 6–18 months |
| Quoting Willow as "fault tolerance achieved" | It demonstrated **below-threshold scaling**, not fault tolerance at useful scale (§5.3 → `quantum-noise-error-correction-and-hardware`) |
| Quoting one RSA-breaking qubit number as settled | Estimates vary with assumptions and have fallen repeatedly (§9.2 → `quantum-software-and-resource-estimation`) |
| Assuming quadratic speedups translate to real advantage | **Error-correction overhead and slow logical clocks often eat them** (§9.3 → `quantum-software-and-resource-estimation`) |
| Building a business case on QAOA/VQE advantage | Heuristics with **no proven speedup**; classical often wins (§3 → `quantum-foundations-and-algorithms`, §11.2 → `quantum-applications-and-post-quantum-crypto`) |
| Investing in QML without addressing data loading | The bottleneck that invalidates most proposals (§11.3 → `quantum-applications-and-post-quantum-crypto`) |
| Believing vendor-defined single-number metrics | Ask what it measures and who defined it (§4.3 → `quantum-noise-error-correction-and-hardware`) |
| Ignoring the transpiled circuit | SWAP insertion can multiply gate count several-fold (§8.2 → `quantum-software-and-resource-estimation`) |
| Confusing error mitigation with error correction | Mitigation costs exponential shots and doesn't scale (§4.2 → `quantum-noise-error-correction-and-hardware`) |
| Deploying QKD instead of PQC | **NSA, NCSC, and ANSSI all recommend PQC over QKD** (§12 → `quantum-applications-and-post-quantum-crypto`) |
| Using competition-version PQC parameters | Use the **FIPS** versions; parameters changed (§13.2 → `quantum-applications-and-post-quantum-crypto`) |
| Deferring PQC because "quantum computers don't exist yet" | **HNDL** + **binding regulatory deadlines** (§13.1 → `quantum-applications-and-post-quantum-crypto`, §13.3 → `quantum-applications-and-post-quantum-crypto`) |
| Starting PQC migration with algorithm selection | **Start with the inventory.** That's where programs stall (§13.4 → `quantum-applications-and-post-quantum-crypto`) |
| Learning from analogies instead of linear algebra | You'll have to unlearn them (§14) |

---

## §16. Contested Questions

**16.1 When does a cryptographically-relevant quantum computer arrive?** Expert estimates
cluster around **2030–2035** with enormous error bars, and the security-community central
estimate has been roughly **2033–2035**. **[VERSIONED, and important]: NCSC, NSA, and NIST
did not revise that estimate upward in response to Willow, Nighthawk, or Majorana 1, and
no standards body changed its deprecation schedule as a direct result.** What changed was
**the credibility of the estimate**, not the date: Willow removed the "maybe error
correction is physically impossible" objection, and four architecturally distinct programmes
hitting milestones simultaneously reduces the risk that one technical obstacle blocks the
whole field. **Note the asymmetry in the decision: you must migrate on the pessimistic
timeline regardless (§13.1 → `quantum-applications-and-post-quantum-crypto`).**

**16.2 Has quantum advantage been achieved?** §10.4 → `quantum-software-and-resource-estimation`. The 2026 position is roughly:
*probably yes on contrived tasks*, with the live argument being whether usefulness and
verifiability should be requirements for the term. Skepticism persists because benchmark
tasks are contrived, verification relies on indirect proxies, and early experiments were
partially matched by later classical simulation.

**16.3 Is NISQ a dead end?** *For NISQ*: real hardware today, learning value, possible
niche wins, and it builds the engineering base for fault tolerance. *Against*: **no proven
advantage from any NISQ algorithm**, barren plateaus, mitigation costs that scale
exponentially, and the result that provably-trainable circuits may be classically
simulable. **A growing view is that useful quantum computing requires fault tolerance, full
stop, and NISQ was an interesting detour.** Held seriously by serious people on both sides.

**16.4 Quantum annealing and optimization.** D-Wave has thousands of qubits and real
commercial deployments; it is also **not a universal quantum computer**, and its claimed
advantages have been repeatedly matched by classical methods. **[CONTESTED]** whether
annealing offers any asymptotic advantage at all.

**16.5 Topological qubits.** Microsoft's Majorana-based approach promises error protection
built into the physics. **It is the most scientifically contested modality** — a
high-profile Majorana paper was retracted in 2021, and subsequent claims have drawn
substantial expert skepticism. **Genuinely unresolved.**

**16.6 Is the field overinvested?** *For the bubble case*: no commercial advantage yet,
valuations disconnected from revenue, repeated timeline slippage, and dequantization
history. *Against*: the physics is proven, error correction crossed a real threshold in
2024–2026, the cryptographic threat alone justifies national investment, and the downside
of being late is severe. **[VERSIONED]** The US **EO 14413 (June 2026)** established a
national effort toward a science-enabling quantum computer, directed an update to the
National Quantum Strategy, and mandated domestic quantum workforce institutes and supply
chain strategies — so the state-level bet is being *increased*, whatever one thinks of the
private valuations.

**16.7 Should my organization do anything now?** **The clear answer for PQC is yes,
immediately** (§13 → `quantum-applications-and-post-quantum-crypto`) — that's regulatory and HNDL-driven, not hardware-driven. For quantum
*computing*, the honest answer for most organizations is **education and monitoring, not
deployment**: build literacy (which takes years), identify whether you have genuinely
quantum-suited problems (optimization, simulation, and sampling with real structural
bottlenecks), and avoid pilots whose main output is a press release.

---

## §17. Currency Snapshot — verified August 2026

| Thing | Status as of Aug 2026 | Decay risk |
|---|---|---|
| **Google Willow** | **105 superconducting qubits, announced 9 December 2024.** First **below-threshold** error correction on real hardware — surface code at **distance 3/5/7 on one chip**, logical error rate falling roughly by half per distance increase. Published in *Nature*. ⚠️ **Not fault tolerance at useful scale**; d=7 uses 49 physical qubits per logical qubit | Low (historical) |
| **Google roadmap** | Self-assessed at **Milestone 2** (~10² physical qubits, ~10⁻² logical error). Milestone 3: long-lived logical qubit (~10³ physical, 10⁻⁶). **Milestone 6: ~10⁶ physical qubits at 10⁻¹³** — presented as a destination, **not a near-term spec** | Medium |
| **IBM roadmap** | **Nighthawk**: 120 qubits, 218 tunable couplers, ~30% more circuit complexity than Heron; **~7,500 gates in 2026** (up to 3×120-qubit modules = 360 qubits), 10,000 in 2027, 15,000 in 2028. **Loon** (2025): c-couplers for qLDPC. **Kookaburra**: ~4,158 physical qubits, first qLDPC memory + logical processing unit. **Starling (2029): 200 logical qubits from ~10,000 physical, 100M operations. Blue Jay (2033): 2,000 logical qubits, 1B operations.** Real-time decoder prototype targeted 2026 | **High** |
| **Others** | **PsiQuantum**: million-qubit photonic on a similar horizon. **DARPA QBI** funds Atom Computing, Photonic Inc., **Oxford Ionics (now part of IonQ)** and others toward 2033. **Microsoft/Quantinuum** reported logical-qubit milestones on H-series. **Atom Computing** demonstrated 1000+ neutral-atom qubits | **High** |
| **Advantage claims** | ⚠️ **30 July 2026: IBM coordinated three announcements** (arXiv preprints, 27–28 July) presented as "the quantum advantage era." **They do not carry equal evidentiary weight** — the IBM/UChicago paper has complexity-theoretic hardness arguments plus a fidelity certificate; the Qedma and Algorithmiq papers are more empirical. One ran **70 logical qubits through thousands of logical operations, logical error ~10× below physical**, in ~15 minutes | **High** |
| **Dequantization, live** | An October 2025 **peaked-circuit advantage claim on Quantinuum's 56-qubit H2** was followed by an **April 2026 IBM Quantum paper demonstrating efficient classical simulation of those circuits.** The pattern continues | **High** |
| **QEC research volume** | Peer-reviewed QEC-code papers: **36 in 2024 → 120+ between January and October 2025** | Medium |
| **NIST PQC standards** | **FIPS 203 (ML-KEM), 204 (ML-DSA), 205 (SLH-DSA)** finalized **13 August 2024**. **HQC selected March 2025** as a code-based backup KEM — **standard still being drafted** | Low |
| **NIST transition** | **RSA and ECC deprecated after 2030, disallowed after 2035**; 112-bit security deprecated after 2030 (IR 8547) | Low |
| **US federal deadlines** | ⚠️ **EO 14412 (June 2026)** mandates accelerated migration and **FAR Council contractor compliance**. **OMB M-26-15**: migration lead named by late July 2026, plan by late October 2026; **key establishment by 31 Dec 2030, signatures by 31 Dec 2031, remainder by 2035**. **EO 14144: TLS 1.3 by 2 Jan 2030** | Medium |
| **CNSA 2.0 (NSS)** | **ML-KEM-1024 + ML-DSA-87**, AES-256, SHA-384/512. Software/firmware signing **exclusive by 1 Jan 2027**; **new NSS acquisitions compliant 1 Jan 2027**; networking **2030**; OS/apps/cloud **2033**; **all NSS by 2035**. Extends across the defense supply chain. **QKD explicitly rejected** | Medium |
| **EU / UK / AU** | **EU (NIS CG, June 2025)**: roadmaps by **31 Dec 2026**, high-risk cases by **2030**, full transition by **2035**. **UK NCSC**: three-phase to 2035. **Australia ASD**: eliminate classical public-key **by 2030** | Medium |
| **Q-Day estimates** | ⚠️ **NCSC, NSA, and NIST did not revise the ~2033–2035 central estimate upward** in response to Willow, Nighthawk, or Majorana 1, and **no standards body changed its deprecation schedule as a result** | Medium |
| **Software** | **Qiskit 2.x** (12-month release cycle since 1.0; native OpenQASM 3, primitives V2). **PennyLane 0.4x**. Cirq, Q#, **CUDA-Q**, PyTKET, Braket active. **OpenQASM 3** is the portable IR | Medium |
| **US policy** | **EO 14413 (June 2026)** — national effort toward a science-enabling quantum computer, National Quantum Strategy update, domestic workforce institutes, sensing/networking plans, supply-chain strategy | Medium |

**Goes stale fastest:** vendor roadmaps and hardware milestones; advantage claims and their
refutations; federal deadline implementation details. **Essentially never stale:** §1 → `quantum-foundations-and-algorithms`
(foundations), §2 → `quantum-foundations-and-algorithms` (complexity), §3 → `quantum-foundations-and-algorithms`'s speedup classification, §4.1 → `quantum-noise-error-correction-and-hardware`, §5.1 → `quantum-noise-error-correction-and-hardware`–5.2, §9.1 → `quantum-software-and-resource-estimation`, §10.2 → `quantum-software-and-resource-estimation`–10.3
(evaluation method), §13.1 → `quantum-applications-and-post-quantum-crypto` (HNDL logic), §15 (myths).

---

## §18. The Canon

### 18.1 Books

| Author | Work | Why |
|---|---|---|
| **Nielsen & Chuang** | ***Quantum Computation and Quantum Information*** ("Mike & Ike") | **The standard graduate text**, 25 years on. Still the reference |
| **Scott Aaronson** | ***Quantum Computing Since Democritus***; his blog **Shtetl-Optimized** | The best complexity-theoretic perspective, and **the most reliable public debunker of hype in the field** |
| **Kaye, Laflamme & Mosca** | *An Introduction to Quantum Computing* | Gentler, algorithm-focused |
| **Mermin** | *Quantum Computer Science* | Short and unusually clear for physicists |
| **Hidary** | *Quantum Computing: An Applied Approach* | Practical and code-oriented |
| **Sutor** | *Dancing with Qubits* | Builds the math from scratch; good for self-study |
| **Bernhardt** | *Quantum Computing for Everyone* | Genuinely rigorous popular treatment — rare |
| **Lidar & Brun (eds.)** | *Quantum Error Correction* | The reference for §5 → `quantum-noise-error-correction-and-hardware` |
| **Preskill** | Caltech Ph219 lecture notes (**free**) | The best free advanced treatment anywhere |

### 18.2 Papers to actually read
Feynman, *Simulating Physics with Computers* (1982) — the founding argument. Shor (1994)
and Grover (1996). **Preskill, "Quantum Computing in the NISQ Era and Beyond" (2018)** —
the paper that named the era and is more skeptical than its citations suggest.
**Gidney & Ekerå (2019)** on RSA resource estimation. **Google's Willow paper in *Nature*
(2024)** on below-threshold correction. **Ewin Tang's dequantization papers.**
**Aaronson & Zhang on peaked-circuit verifiable advantage.** The **"Grand Challenge of
Quantum Applications"** perspective piece for the verifiability argument in §10.2 → `quantum-software-and-resource-estimation`.

### 18.3 Online and people
**Qiskit Textbook / IBM Quantum Learning** (free, the best structured on-ramp),
**PennyLane's Codebook and demos** (excellent, especially for QML),
**Michael Nielsen's Quantum Country** (spaced-repetition essays — an unusually effective
format), **Quantum Computing Stack Exchange** (high signal), **Quantum Algorithm Zoo**
(Stephen Jordan's catalogue — the reference list of every known quantum algorithm),
**Error Correction Zoo**, **arXiv quant-ph**, and **qosf's awesome-quantum-software** for
tooling.

**People worth following**: **Scott Aaronson** (complexity, and hype control),
**John Preskill**, **Ewin Tang** (dequantization), **Craig Gidney** (resource estimation),
**Sergio Boixo**, **Michael Nielsen**, and the **Quantum Computing Report** /
**The Quantum Insider** for industry news — read the latter two knowing they cover an
industry that funds them.

---

## §19. Quick Reference

### 19.1 Numbers
- **n qubits → 2ⁿ amplitudes**, but **n classical bits out per measurement.**
- Surface code: **~2d² physical qubits per logical qubit**; **d=7 → 49 physical per logical.**
- Surface code threshold: **~1%** physical error rate.
- Current two-qubit gate errors: **~10⁻³–10⁻²**; single-qubit **~10⁻⁴–10⁻³**.
- **T2 ≤ 2·T1**, always.
- Classical simulation limit: **~30 qubits on a laptop, ~40–50 on a cluster.**
- RSA-2048: **millions of physical qubits** (estimates ~20M and falling).
- **IBM Starling 2029: 200 logical / ~10,000 physical / 100M operations.**
- **Google Milestone 6: ~10⁶ physical qubits.**
- PQC: **RSA/ECC deprecated after 2030, disallowed after 2035.**
- Enterprise PQC migration: **42–54 months.**

### 19.2 Evaluating any quantum claim
- [ ] Physical or logical qubits?
- [ ] Two-qubit gate fidelity, measured how?
- [ ] Is the task useful, or constructed for the demo?
- [ ] Is the result verifiable, and by what method?
- [ ] Compared against the **best** classical approach, or a convenient one?
- [ ] Peer-reviewed, preprint, or press release?
- [ ] Has 6–18 months passed for classical researchers to respond?
- [ ] Does the previous roadmap's promise for this year look accurate in hindsight?
- [ ] Proven speedup, or heuristic?
- [ ] If quadratic — does it survive error-correction overhead (§9.3 → `quantum-software-and-resource-estimation`)?

### 19.3 What to actually do
| If you are... | Do |
|---|---|
| Any organization | **Start PQC migration now** — inventory first (§13.4 → `quantum-applications-and-post-quantum-crypto`). This is regulatory and HNDL-driven |
| A US federal agency or contractor | Check **EO 14412 / OMB M-26-15** obligations and the **FAR** implications immediately |
| Evaluating a quantum vendor pilot | Run §19.2 on everything they show you; ask what the previous roadmap promised |
| Curious and technical | Linear algebra → Qiskit textbook → simulator. Skip the analogies (§14) |
| Looking for real quantum problems | **Simulation of quantum systems** is the defensible case (§11.1 → `quantum-applications-and-post-quantum-crypto`). Optimization and ML are not |
| In a domain with 10+ year data confidentiality | You are **already exposed** to HNDL (§13.1 → `quantum-applications-and-post-quantum-crypto`) |

---

## §20. Sources and Method

**Method.** Narrative (not systematic) review. The durable material — §1 → `quantum-foundations-and-algorithms` (foundations),
§2 → `quantum-foundations-and-algorithms` (complexity), §3 → `quantum-foundations-and-algorithms`'s classification of speedups, §4.1 → `quantum-noise-error-correction-and-hardware`, §5.1 → `quantum-noise-error-correction-and-hardware`–5.2, §9.1 → `quantum-software-and-resource-estimation`, §10.2 → `quantum-software-and-resource-estimation`–10.3,
§13.1 → `quantum-applications-and-post-quantum-crypto`'s HNDL logic, §14, §15 — rests on textbook physics, established complexity theory,
and results that have been stable for years to decades. Every **time-sensitive** claim
(hardware milestones, roadmaps, advantage claims, regulatory deadlines, software versions)
was verified against a primary or near-primary source in **August 2026** and is flagged in
§17 with a decay-risk rating. This field has an unusually high hype-to-substance ratio, so
where claims are contested I have said so explicitly rather than picking a side (§16), and
§10.3 → `quantum-software-and-resource-estimation` documents the dequantization pattern precisely because it recurs.

**Search log** (August 2026): quantum error correction, logical qubits, and vendor roadmaps ·
NIST PQC migration deadlines, CNSA 2.0, and HQC · quantum advantage claims, verifiability,
and dequantization · quantum SDKs and programming frameworks.

**Primary and near-primary sources consulted (selected):**
- **IBM Technology Atlas / IBM Quantum roadmap 2026** (`ibm.com/roadmaps/quantum/2026`) —
  Nighthawk, Loon, Kookaburra, Starling, Blue Jay, and the real-time decoder target
- **Google Quantum AI** roadmap and the Willow *Nature* result, plus the arXiv review of
  Google's milestone structure
- **NIST** — FIPS 203/204/205; Dustin Moody's "NIST PQC: The Road Ahead" (March 2025)
  transition tables; **NCCoE Migration to PQC** documentation (EO 14412, EO 14413, HQC)
- **NSA CNSA 2.0** requirements as documented across implementation guides;
  **OMB M-26-15** as reported by the **OpenSSL Corporation** analysis; **UK NCSC** PQC
  migration roadmap; **EU NIS Cooperation Group** PQC roadmap via PQShield
- **IEEE Spectrum** and **phys.org** on IBM's July 2026 verifiable-advantage papers
  (Martiel et al., arXiv 2607.25941); **postquantum.com**'s fact-check of the three claims;
  **Kremer & Dupuis (IBM Quantum, arXiv 2604.21908)** on classical simulation of peaked
  circuits, against **Gharibyan et al. (arXiv 2510.25838)**
- **Aaronson & Zhang**, "On verifiable quantum advantage with peaked circuit sampling"
  (arXiv 2404.14493); **"The Grand Challenge of Quantum Applications"** (arXiv 2511.09124)
  on verifiability as a necessary condition
- **Riverlane** on QEC publication volume; **The Quantum Insider** on migration timelines
  and the advantage debate; **IBM Quantum documentation** and **PennyLane docs** for the
  software stack

**Confidence statement.** **High confidence** in §1–§5 → `quantum-foundations-and-algorithms`, `quantum-noise-error-correction-and-hardware`'s physics, mathematics, and
complexity theory, and in §13.2 → `quantum-applications-and-post-quantum-crypto`'s standards — these are textbook material and published
federal standards. **High confidence** in the Willow result (peer-reviewed in *Nature*) and
in the IBM roadmap figures, which come from IBM's own published roadmap. **Moderate
confidence** in §7 → `quantum-noise-error-correction-and-hardware`'s broader vendor landscape and §17's competitor milestones: much of this
is drawn from press releases, preprints, and trade coverage rather than peer-reviewed work,
and **vendors have systematic incentives to present the most flattering framing** — the
qubit-count-versus-fidelity issue in §6 → `quantum-noise-error-correction-and-hardware` is exactly this problem. **Moderate confidence,
deliberately hedged, on §10.4 → `quantum-software-and-resource-estimation`'s advantage claims**: these are days-to-weeks-old preprints as
of writing, they have not been peer-reviewed, the field's own history (§10.3 → `quantum-software-and-resource-estimation`) says some
advantage claims are later matched classically, and I have reported both IBM's framing and
the documented criticism that the three papers carry unequal evidentiary weight. **Lower
confidence on §9.2 → `quantum-software-and-resource-estimation`'s specific RSA resource numbers** — these are model-dependent, have been
revised downward repeatedly, and I have deliberately given a range and a direction rather
than a point estimate. Regulatory deadlines in §13.3 → `quantum-applications-and-post-quantum-crypto` were verified against multiple
independent summaries and, where possible, primary documents, but **implementation details
change and you should verify against the current official text before making a compliance
decision.** Q-Day estimates (§16.1) are expert judgment, not measurement.
