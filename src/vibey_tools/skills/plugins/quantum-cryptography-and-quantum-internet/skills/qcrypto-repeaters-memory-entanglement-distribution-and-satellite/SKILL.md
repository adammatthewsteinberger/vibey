---
name: qcrypto-repeaters-memory-entanglement-distribution-and-satellite
description: "Use for the network layer and its physical limits: quantum repeaters and why they are the blocking problem for terrestrial range, quantum memory, entanglement distribution and swapping, satellite QKD, the quantum internet roadmap and its realistic stages, and the other quantum network applications beyond key distribution."
---

# Quantum Cryptography: Quantum Repeaters, Quantum Memory, Entanglement Distribution, Satellite QKD, the Quantum Internet Roadmap, and Other Applications

> **Part 4 of 6** of the *Quantum Cryptography, Quantum Encryption and the Quantum Internet* reference (plugin `quantum-cryptography-and-quantum-internet`), covering §14–§19. Sibling skills: `qcrypto-two-different-things-qubits-no-cloning-and-entanglement` (§0–§5), `qcrypto-bb84-entanglement-based-cv-qkd-and-key-distillation` (§6–§9), `qcrypto-security-claims-attacks-and-trusted-nodes` (§10–§13), `qcrypto-official-position-qrng-quantum-threat-and-choosing` (§20–§23), `qcrypto-reference` (§24–§29). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The protocols date to the 1980s and 90s. Two areas moved recently. See §24 → `qcrypto-reference` for quantum repeater demonstrations, and the government position on QKD.

> **⚠️ FIRST, THE TERMINOLOGY DISASTER — because almost every popular article gets this
> wrong and the two things are nearly opposites** (§1 → `qcrypto-two-different-things-qubits-no-cloning-and-entanglement`).
> ⚠️ **POST-QUANTUM CRYPTOGRAPHY is classical mathematics running on ordinary computers,
> designed to resist quantum attack. It is what is actually being deployed** (see a
> cryptography reference).
> ⚠️ **QUANTUM CRYPTOGRAPHY / QKD uses quantum physics and special hardware to distribute
> keys. It is a niche technology that several major security agencies actively recommend
> AGAINST** (§20 → `qcrypto-official-position-qrng-quantum-threat-and-choosing`).
> **⚠️ "Quantum-safe" and "quantum-secure" are marketing terms that get applied to both.
> When someone uses them, ask which they mean.**
>
> **Companion to a cryptography reference, which covers the classical primitives, the
> protocols in production, and the PQC migration.**
>
> **⚠️ GOTCHA** boxes mark where physics claims and engineering reality diverge.
>
> **The three ideas that organize this document:**
> 1. **⚠️ QKD's security is real physics and its threat model is narrower than advertised**
>    (§10 → `qcrypto-security-claims-attacks-and-trusted-nodes`). **It secures a key exchange against an eavesdropper on the channel. It does not
>    authenticate, does not protect endpoints, and cannot bootstrap trust from nothing.**
> 2. **⚠️ THE THEORY-IMPLEMENTATION GAP is the whole story** (§11 → `qcrypto-security-claims-attacks-and-trusted-nodes`). **Every deployed QKD
>    system that has been attacked was attacked through its hardware, not its protocol —
>    the security proofs assume devices the engineers cannot actually build.**
> 3. **⚠️ QUANTUM REPEATERS ARE THE BOTTLENECK** (§14, §24.1 → `qcrypto-reference`). **Without them, quantum
>    networks are point-to-point links chained through trusted nodes, which reintroduces
>    exactly the trust QKD was supposed to eliminate.**

---

## §14. Quantum Repeaters

**⚠️ The technology the entire field is waiting for** — ⚠️ **and the NCSC has cited quantum
repeaters as the specific development that would most change its assessment of QKD** (§20 → `qcrypto-official-position-qrng-quantum-threat-and-choosing`).
```
⚠️ THE PROBLEM  no-cloning (§3) forbids amplification, and loss is
   exponential (§5)
⚠️ THE SOLUTION  ⚠️ divide the link into segments; establish
   entanglement across each segment; ⚠️ ENTANGLEMENT SWAPPING joins
   adjacent segments into one longer entangled pair;
   ⚠️ ENTANGLEMENT PURIFICATION/DISTILLATION upgrades several noisy
   pairs into fewer better ones
⚠️ WHY IT'S HARD  ⚠️ segments succeed PROBABILISTICALLY and at
   different times, so you must STORE entanglement while waiting
   for the neighbouring segment. ⚠️ THAT REQUIRES QUANTUM MEMORY
   (§15) with coherence time longer than the entanglement
   generation time — which is exactly the threshold recently
   crossed (§24.1)
⚠️ GENERATIONS  1st (heralding + purification, needs memory) →
   2nd (error correction on qubits) → 3rd (fully error-corrected,
   one-way, no waiting)
```

---

## §15. Quantum Memory

**⚠️ Storing a quantum state and retrieving it faithfully.**
**⚠️ Platforms**: ⚠️ **trapped ions (long coherence, good optical interface), neutral atoms
and atomic ensembles, rare-earth-doped crystals (⚠️ excellent MULTIMODE capacity — many
modes stored at once, which is how you get practical rates), NV centres in diamond, and
solid-state spin systems.**
**⚠️ The figures of merit that matter**: ⚠️ **coherence TIME, storage-and-retrieval
EFFICIENCY, FIDELITY, MULTIMODE capacity, and wavelength compatibility with telecom
fibre — which frequently requires QUANTUM FREQUENCY CONVERSION between the memory's
natural wavelength and 1550 nm.**
**⚠️ The binding requirement for repeaters**: ⚠️ **coherence time must exceed the time
needed to establish entanglement on the neighbouring segment, or the stored state decays
before it can be used.**

---

## §16. Entanglement Distribution

**⚠️ Heralding** is the key concept: ⚠️ **a classical signal announcing that entanglement
succeeded, so the parties know which attempts to keep.**
**⚠️ Single-photon interference schemes** give higher rates and are ⚠️ **phase-sensitive,
demanding active stabilization of the fibre;** **⚠️ two-photon interference schemes are
phase-robust and slower.** ⚠️ **Recent work combines them** (§24.1 → `qcrypto-reference`).
**⚠️ Multiplexing** — in time, frequency or spatial mode — ⚠️ **is how rates become
practical, because it lets many attempts proceed in parallel.**
**⚠️ Quantum teleportation** transfers a quantum state using shared entanglement plus
classical communication — ⚠️ **it destroys the original (consistent with no-cloning) and
transmits no information faster than light.**

---

## §17. Satellite QKD

**⚠️ Free-space loss scales with beam divergence rather than exponentially** (§5 → `qcrypto-two-different-things-qubits-no-cloning-and-entanglement`), ⚠️ **so
satellites bypass fibre's distance limit.**
**⚠️ China's Micius satellite** demonstrated satellite-to-ground QKD, entanglement
distribution over roughly 1,200 km between ground stations, and an intercontinental
quantum-secured video call.
**⚠️ The limitations are practical and severe**: ⚠️ **line of sight only, weather dependent,
mostly night operation because of daylight background, short pass windows, and ⚠️ THE
SATELLITE IS A TRUSTED NODE in the simplest architecture** (§13 → `qcrypto-security-claims-attacks-and-trusted-nodes`).
**⚠️ Several national and multinational satellite QKD programmes are in progress**,
⚠️ **and the strategic interest is at least as much about sovereignty and capability
demonstration as about a commercial need.**

---

## §18. The Quantum Internet Roadmap

**⚠️ The standard staged framing (Wehner, Elkouss and Hanson) is genuinely useful because
each stage unlocks different applications:**
```
⚠️ 1. TRUSTED REPEATER NETWORKS  ⚠️ QKD with trusted nodes (§13).
   ⚠️ This is where deployed networks are TODAY
⚠️ 2. PREPARE-AND-MEASURE  end-to-end QKD without trusting relays
⚠️ 3. ENTANGLEMENT DISTRIBUTION  ⚠️ device-independent protocols
   become possible (§12)
⚠️ 4. QUANTUM MEMORY NETWORKS  ⚠️ requires §15. Enables blind
   quantum computing and simple distributed protocols
⚠️ 5. FEW-QUBIT FAULT TOLERANT
⚠️ 6. QUANTUM COMPUTING NETWORK  ⚠️ distributed quantum computation
```
**⚠️ The honest status**: ⚠️ **deployed networks are stage 1; laboratory and testbed work is
around stages 3–4** (§24.1 → `qcrypto-reference`). **⚠️ Stages 5–6 are research.**

---

## §19. Other Quantum Network Applications

⚠️ **Beyond QKD, and arguably more interesting because they don't have a competing
classical solution:**
⚠️ **BLIND QUANTUM COMPUTING (run a computation on a remote quantum computer without
revealing the input, output or algorithm); DISTRIBUTED QUANTUM COMPUTING (linking
processors to exceed any single machine); CLOCK SYNCHRONIZATION beyond classical limits;
⚠️ ENTANGLED TELESCOPE ARRAYS for improved baseline interferometry; distributed quantum
sensing; and quantum position verification.**
**⚠️ Note the strategic argument**: ⚠️ **if quantum networks are built, it may be these
applications rather than QKD that justify them — QKD has a strong classical competitor
(§23 → `qcrypto-official-position-qrng-quantum-threat-and-choosing`) and these do not.**

---

# PART IV — REALITY CHECK
