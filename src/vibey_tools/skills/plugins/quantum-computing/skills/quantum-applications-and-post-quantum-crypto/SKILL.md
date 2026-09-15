---
name: quantum-applications-and-post-quantum-crypto
description: "Use when evaluating quantum applications or planning a post-quantum migration. Covers quantum chemistry and materials as the strongest case, optimization, quantum machine learning, finance and everything else, quantum networking (QKD, repeaters) and sensing, and post-quantum cryptography — the harvest-now-decrypt-later threat, the NIST standards (ML-KEM, ML-DSA, SLH-DSA), the now-binding migration deadlines, and how to migrate (inventory, hybrid modes, prioritization)."
---

# Quantum Computing: Applications, Networking and Sensing, and Post-Quantum Cryptography

> **Part 4 of 5** of the *Quantum Computing* reference (plugin `quantum-computing`), covering §11–§13. Sibling skills: `quantum-foundations-and-algorithms` (§0–§3), `quantum-noise-error-correction-and-hardware` (§4–§7), `quantum-software-and-resource-estimation` (§8–§10), `quantum-reference` (§14–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    binding dates. §13 is the section with real deadlines attached.

---

## §11. Applications

### 11.1 Quantum chemistry and materials — the strongest case

**[DURABLE]** Simulating molecules and materials is the application where the exponential
advantage is least disputed, because the problem *is* a quantum system. Targets: catalysis
(nitrogen fixation is the canonical example), battery chemistry, superconductors, drug
binding affinities. **Near-term**: VQE on small molecules (⚠️ heuristic, barren plateaus,
§4.4 → `quantum-noise-error-correction-and-hardware`). **Fault-tolerant**: quantum phase estimation on industrially relevant systems —
which requires §5 → `quantum-noise-error-correction-and-hardware`-scale hardware.

**⚠️ Reality check**: classical computational chemistry (DFT, coupled cluster, DMRG,
quantum Monte Carlo) is very good and improving, and the quantum-advantage crossover point
for industrially relevant molecules is genuinely uncertain.

### 11.2 Optimization

Portfolio optimization, routing, scheduling, supply chain — the most-marketed application
and the **weakest technical case**. QAOA and quantum annealing are heuristics with no proven
advantage, and **classical solvers (Gurobi, CPLEX, specialized heuristics, and simulated
annealing) frequently match or beat quantum approaches** on the same problems. **[CONTESTED]
§16.4 → `quantum-reference`.**

### 11.3 Quantum machine learning

**⚠️ The most oversold area.** Two structural problems: **the data-loading bottleneck** —
there is no efficient way to load a large classical dataset into a quantum state, and QRAM
remains theoretical — and **dequantization** (§10.3 → `quantum-software-and-resource-estimation`), which removed the claimed speedup from
a whole family of QML algorithms. Add barren plateaus (§4.4 → `quantum-noise-error-correction-and-hardware`) and the result that **provable
absence of barren plateaus may imply classical simulability**, and the honest position is
that QML's advantage case is currently weak. **The plausible exception: machine learning on
data that is *natively quantum*** (from quantum sensors or quantum simulations), where the
loading problem doesn't arise.

### 11.4 Finance, and everything else

Derivative pricing via amplitude estimation (quadratic — see §9.3 → `quantum-software-and-resource-estimation` for why that may not
survive), risk analysis, fraud detection. Real bank R&D programs exist; **no production
quantum advantage has been demonstrated in finance.** The reasonable framing for enterprises
is capability-building and option value, not near-term ROI.

---

## §12. Quantum Networking and Sensing

**[DURABLE] These are separate fields from quantum computing and are commercially closer.**

**Quantum sensing** is the most mature quantum technology commercially: atomic clocks,
magnetometry (SQUIDs, NV centers), gravimetry, inertial navigation. **Real products, real
revenue, today** — and often ignored because it isn't a computer.

**Quantum networking / repeaters** — entanglement distribution, quantum memories, the
long-term "quantum internet" vision, and near-term links between quantum processors (which
is how trapped-ion and photonic architectures plan to scale).

**QKD (quantum key distribution)** — **[CONTESTED, and the disagreement is unusually
sharp]**. *For*: information-theoretic security grounded in physics rather than
computational assumptions. *Against*: **NSA, NCSC, and ANSSI all recommend post-quantum
cryptography over QKD** for national security systems, citing the requirement for
special-purpose hardware, the inability to provide authentication (QKD needs a classical
authenticated channel anyway), distance limitations and trusted-relay requirements,
denial-of-service exposure, and side-channel attacks on real implementations. **CNSA 2.0
explicitly rejects QKD for NSS.** **The practical guidance: PQC (§13) is the answer for
essentially all organizations; QKD is a niche with specific physical-layer requirements.**

---

## §13. Post-Quantum Cryptography

**[DURABLE] This is the part of quantum computing with the most immediate, concrete
consequences for ordinary organizations — and it does not depend on when quantum computers
arrive.**

### 13.1 The threat

**Shor's algorithm breaks RSA, Diffie-Hellman, and elliptic-curve cryptography.** Grover
halves the effective security of symmetric ciphers, so **AES-256 remains fine** and
SHA-384/512 are recommended.

**⚠️ "Harvest now, decrypt later" (HNDL) is why the timeline argument is a distraction.**
An adversary recording encrypted traffic today can decrypt it whenever a
cryptographically-relevant quantum computer exists. **If your data must stay confidential
for 10+ years, it is already exposed.** This applies to health records, state secrets,
long-lived financial data, and anything with a legal retention requirement.

### 13.2 The standards

**[VERSIONED]** NIST finalized three standards on **13 August 2024** after an eight-year
competition:

| FIPS | Algorithm | Purpose | Basis |
|---|---|---|---|
| **FIPS 203** | **ML-KEM** (CRYSTALS-Kyber) | Key encapsulation | Lattice |
| **FIPS 204** | **ML-DSA** (CRYSTALS-Dilithium) | Digital signatures | Lattice |
| **FIPS 205** | **SLH-DSA** (SPHINCS+) | Signatures | Hash-based — conservative backup |

**NIST also selected HQC in March 2025** as a fifth algorithm and additional KEM.
**HQC is code-based rather than lattice-based, providing a mathematically different backup
to ML-KEM** in case lattice assumptions fall — **its standard is still being drafted**, so
it is not yet deployable. **Use the FIPS names in procurement documents and specs.**

**⚠️ Use the FIPS versions, not the competition versions** — parameters changed during
standardization. And **prefer hybrid (classical + PQC) constructions** during transition:
ETSI and the EU explicitly encourage hybrids, and they protect you if a PQC algorithm is
broken (which has happened to competition candidates — SIKE and Rainbow were both broken
classically during the process).

### 13.3 The deadlines — now binding, not advisory

**[VERSIONED — verify against the current text; this is the highest-consequence table in
the document.]**

**NIST (IR 8547 transition roadmap):** quantum-vulnerable algorithms including **RSA and
ECC are deprecated after 2030 and disallowed after 2035**. Algorithms at the **112-bit
security level are deprecated after 2030 and disallowed after 2035** regardless.

**US federal civilian — this became obligation in 2026:**
- **EO 14412 ("Securing the Nation Against Advanced Cryptographic Attacks," June 2026)**
  mandates accelerated government-wide PQC migration, sets binding deadlines for high-value
  assets, and **directs the Federal Acquisition Regulatory Council to require contractor
  compliance** with NIST PQC standards.
- **OMB M-26-15** sets the phased schedule: agencies named a PQC migration lead by late
  July 2026 and owed a full migration plan by late October 2026; **inventories and planning
  through 2027, pilots through 2028, key establishment migrated by 31 December 2030,
  digital signatures by 31 December 2031, remaining systems by 2035.** It directs agencies
  to fold PQC into cloud migrations and hardware refresh cycles rather than run it
  standalone, and requires identification of systems that cannot support PQC or hybrid.
- **EO 14144** requires **TLS 1.3 (or successor) across federal systems by 2 January 2030.**

**US national security systems (NSA CNSA 2.0)** — excluded from the OMB track and moving
faster, with **ML-KEM-1024 and ML-DSA-87** specified alongside AES-256 and SHA-384/512:
software and firmware signing leads (**exclusive CNSA 2.0 use from 1 January 2027**),
**all new NSS acquisitions CNSA 2.0 compliant from 1 January 2027**, networking equipment
**by 2030**, operating systems / custom applications / cloud services **by 2033**, and
**full quantum resistance across all NSS by 2035**. ⚠️ **These extend across the defense
supply chain**, affecting contractors and vendors.

**EU** — the NIS Cooperation Group roadmap (June 2025): **initial national roadmaps and
awareness by 31 December 2026; high-risk use cases addressed by 31 December 2030; full
transition by 31 December 2035**, with a focus on standardized, tested hybrid solutions.

**UK NCSC** — three-phase guidance to 2035. **Australia (ASD)** is more aggressive,
advising elimination of classical public-key cryptography **by 2030**.

### 13.4 How to migrate

**[DURABLE]** In order: **(1) inventory your cryptography** — this is the hard part and
where every program stalls; you cannot migrate what you can't find, and it lives in TLS
configs, code signing, VPNs, HSMs, embedded firmware, third-party libraries, and vendor
products. **(2) Prioritize by data lifetime and HNDL exposure.** **(3) Build crypto-agility**
so the *next* migration is cheaper. **(4) Push vendors** — much of your exposure is in
products you don't control. **(5) Deploy hybrid first.** **(6) Watch the embedded and IoT
long tail**, where devices have 15-year lifetimes and no update path.

**Realistic enterprise timeline: 42–54 months from start to compliance.** The practical
dates arrive years before the printed ones, because hardware refresh cycles and vendor
readiness gate you.
