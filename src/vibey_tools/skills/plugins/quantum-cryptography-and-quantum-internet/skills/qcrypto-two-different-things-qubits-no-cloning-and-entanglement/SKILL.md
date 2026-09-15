---
name: qcrypto-two-different-things-qubits-no-cloning-and-entanglement
description: "Use first, because it prevents the most common category error in this area: why quantum key distribution and post-quantum cryptography are completely different things, qubits and measurement, the no-cloning theorem that the whole field rests on, entanglement and Bell inequalities, and quantum channels and loss. Includes the router for the whole quantum cryptography reference."
---

# Quantum Cryptography: Two Completely Different Things, Qubits and Measurement, the No-Cloning Theorem, Entanglement and Bell Inequalities, and Quantum Channels

> **Part 1 of 6** of the *Quantum Cryptography, Quantum Encryption and the Quantum Internet* reference (plugin `quantum-cryptography-and-quantum-internet`), covering §0–§5. Sibling skills: `qcrypto-bb84-entanglement-based-cv-qkd-and-key-distillation` (§6–§9), `qcrypto-security-claims-attacks-and-trusted-nodes` (§10–§13), `qcrypto-repeaters-memory-entanglement-distribution-and-satellite` (§14–§19), `qcrypto-official-position-qrng-quantum-threat-and-choosing` (§20–§23), `qcrypto-reference` (§24–§29). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The protocols date to the 1980s and 90s. Two areas moved recently. See §24 → `qcrypto-reference` for quantum repeater demonstrations, and the government position on QKD.

> **⚠️ FIRST, THE TERMINOLOGY DISASTER — because almost every popular article gets this
> wrong and the two things are nearly opposites** (§1).
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
> 3. **⚠️ QUANTUM REPEATERS ARE THE BOTTLENECK** (§14 → `qcrypto-repeaters-memory-entanglement-distribution-and-satellite`, §24.1 → `qcrypto-reference`). **Without them, quantum
>    networks are point-to-point links chained through trusted nodes, which reintroduces
>    exactly the trust QKD was supposed to eliminate.**

---

## §0. Routing

| You want... | Go to |
|---|---|
| **⚠️ QKD vs PQC** | **§1** |
| Qubits and measurement | §2 |
| **⚠️ No-cloning** | **§3** |
| Entanglement and Bell | §4 |
| Channels and loss | §5 |
| **BB84** | **§6 → `qcrypto-bb84-entanglement-based-cv-qkd-and-key-distillation`** |
| Entanglement-based QKD | §7 → `qcrypto-bb84-entanglement-based-cv-qkd-and-key-distillation` |
| Continuous variable | §8 → `qcrypto-bb84-entanglement-based-cv-qkd-and-key-distillation` |
| **⚠️ Raw key to secret key** | **§9 → `qcrypto-bb84-entanglement-based-cv-qkd-and-key-distillation`** |
| **⚠️ What "unconditional" means** | **§10 → `qcrypto-security-claims-attacks-and-trusted-nodes`** |
| **⚠️ Attacks on real systems** | **§11 → `qcrypto-security-claims-attacks-and-trusted-nodes`** |
| MDI and device-independent | §12 → `qcrypto-security-claims-attacks-and-trusted-nodes` |
| **⚠️ Trusted nodes** | **§13 → `qcrypto-security-claims-attacks-and-trusted-nodes`** |
| **Quantum repeaters** | **§14 → `qcrypto-repeaters-memory-entanglement-distribution-and-satellite`** |
| Quantum memory | §15 → `qcrypto-repeaters-memory-entanglement-distribution-and-satellite` |
| Entanglement distribution | §16 → `qcrypto-repeaters-memory-entanglement-distribution-and-satellite` |
| Satellites | §17 → `qcrypto-repeaters-memory-entanglement-distribution-and-satellite` |
| Quantum internet roadmap | §18 → `qcrypto-repeaters-memory-entanglement-distribution-and-satellite` |
| Other applications | §19 → `qcrypto-repeaters-memory-entanglement-distribution-and-satellite` |
| **⚠️ The official position** | **§20 → `qcrypto-official-position-qrng-quantum-threat-and-choosing`** |
| QRNG | §21 → `qcrypto-official-position-qrng-quantum-threat-and-choosing` |
| The quantum computing threat | §22 → `qcrypto-official-position-qrng-quantum-threat-and-choosing` |
| **⚠️ Choosing** | **§23 → `qcrypto-official-position-qrng-quantum-threat-and-choosing`** |
| **What's live** | **§24 → `qcrypto-reference`** |
| Misconceptions, numbers | §25–§26 → `qcrypto-reference` |
| Sources, quick ref, method | §27–§29 → `qcrypto-reference` |

---

## §1. ⚠️ Two Completely Different Things

```
⚠️ POST-QUANTUM CRYPTOGRAPHY (PQC)
   ⚠️ Classical maths, ordinary computers, software upgrade
   ⚠️ Lattice/hash/code-based problems believed hard for quantum
   ⚠️ Works over the existing internet, end to end, at any distance
   ⚠️ Provides KEY EXCHANGE *AND* SIGNATURES/AUTHENTICATION
   ⚠️ Standardized (FIPS 203/204/205) and being deployed NOW
   ⚠️ THIS IS WHAT EVERY MAJOR AGENCY RECOMMENDS

⚠️ QUANTUM KEY DISTRIBUTION (QKD)
   ⚠️ Physics, special hardware, dedicated fibre or line of sight
   ⚠️ Security from quantum mechanics, not computational hardness
   ⚠️ Distance-limited; needs trusted nodes or repeaters (§13, §14)
   ⚠️ Provides KEY DISTRIBUTION ONLY — ⚠️ NO AUTHENTICATION
   ⚠️ Niche deployment; ⚠️ several agencies recommend against (§20)
```
> **⚠️ GOTCHA — the deepest confusion is that QKD does NOT protect against quantum
> computers in the way people assume.** ⚠️ **The quantum computing threat is to classical
> PUBLIC-KEY cryptography (§22 → `qcrypto-official-position-qrng-quantum-threat-and-choosing`). QKD addresses key distribution — and because it needs
> authentication it cannot supply, it must be combined with classical cryptography anyway
> (§10 → `qcrypto-security-claims-attacks-and-trusted-nodes`).** **⚠️ So QKD does not remove the classical dependency; it relocates it.**
> ⚠️ **This is not a fringe criticism — it is the central structural objection made by
> national agencies** (§20 → `qcrypto-official-position-qrng-quantum-threat-and-choosing`).

---

# PART I — THE PHYSICS

## §2. Qubits and Measurement

**⚠️ A qubit can be in SUPERPOSITION** — ⚠️ **α|0⟩ + β|1⟩ — and the coefficients are
amplitudes, not probabilities, which is why interference is possible.**
```
⚠️ MEASUREMENT IS DESTRUCTIVE AND BASIS-DEPENDENT
   ⚠️ Measuring collapses the state to an eigenstate of the
      measured observable
   ⚠️ ⚠️ MEASURING IN THE WRONG BASIS gives a RANDOM result AND
      destroys the original information. This is the mechanism
      QKD exploits (§6)
⚠️ CONJUGATE BASES  ⚠️ rectilinear {|0⟩,|1⟩} and diagonal
   {|+⟩,|−⟩} are mutually unbiased — a state definite in one is
   maximally uncertain in the other
⚠️ PHYSICAL ENCODINGS  polarization · time-bin (⚠️ robust in fibre) ·
   phase · frequency · ⚠️ continuous variables (§8)
```
**⚠️ The uncertainty principle is the deeper statement**: ⚠️ **not "measurement disturbs"
as a practical limitation, but that conjugate properties do not simultaneously have
definite values.**

---

## §3. ⚠️ The No-Cloning Theorem

> **⚠️ The single result that makes quantum cryptography possible.**
⚠️ **An unknown quantum state CANNOT be copied. There is no operation that takes |ψ⟩ to
|ψ⟩|ψ⟩ for arbitrary unknown |ψ⟩.** **⚠️ It follows directly from the linearity of quantum
mechanics, which makes it about as fundamental as results get.**
**⚠️ Why it matters**: ⚠️ **classical eavesdropping is passive and undetectable — light in a
fibre can be split and copied with no trace.** ⚠️ **An eavesdropper on a quantum channel
cannot copy the state, so must measure it — and measurement in the wrong basis (§2)
introduces detectable errors.**
> **⚠️ GOTCHA — no-cloning also creates the central ENGINEERING problem** (§14 → `qcrypto-repeaters-memory-entanglement-distribution-and-satellite`).
> ⚠️ **You cannot amplify a quantum signal, because amplification is copying.** **⚠️ So the
> classical solution to loss — put a repeater every 80 km — is unavailable, and this is
> precisely why quantum networks are hard and why the field needs quantum repeaters.**
> **⚠️ The property that provides the security is the same property that blocks the
> engineering.**

---

## §4. Entanglement and Bell Inequalities

**⚠️ Entangled particles have correlated measurement outcomes that cannot be explained by
any shared classical information determined in advance.**
**⚠️ Bell's theorem** made this experimentally testable: ⚠️ **any local hidden variable
theory obeys an inequality that quantum mechanics violates.** **⚠️ Loophole-free Bell tests
have confirmed the violation, and the 2022 Nobel Prize recognized this work.**
**⚠️ MONOGAMY OF ENTANGLEMENT is the security-relevant property**: ⚠️ **if two parties share
maximal entanglement, no third party can be correlated with them.** **⚠️ This is what
entanglement-based QKD (§7 → `qcrypto-bb84-entanglement-based-cv-qkd-and-key-distillation`) and device-independent protocols (§12 → `qcrypto-security-claims-attacks-and-trusted-nodes`) exploit.**
**⚠️ Entanglement does NOT permit faster-than-light signalling** — ⚠️ **correlations are only
visible when the parties compare results over a classical channel, which is limited by
light speed.** **⚠️ Every quantum protocol here requires a classical channel alongside the
quantum one.**

---

## §5. Quantum Channels and Loss

```
⚠️ FIBRE LOSS is EXPONENTIAL in distance — ⚠️ roughly 0.2 dB/km at
   the 1550 nm telecom minimum. ⚠️ Over 100 km that is ~20 dB, so
   about 1% of photons survive; over 500 km, essentially none
⚠️ AND YOU CANNOT AMPLIFY (§3)
⚠️ THEREFORE  ⚠️ key rate falls exponentially with distance, and
   there is a fundamental bound on repeaterless key rate as a
   function of channel transmittance (the PLOB/repeaterless bound).
   ⚠️ Beating it is the definition of a working repeater (§14)
⚠️ OTHER PROBLEMS  detector dark counts (⚠️ which set a noise floor
   and therefore a maximum distance) · dispersion · polarization
   drift in deployed fibre · ⚠️ thermal and mechanical phase noise
⚠️ FREE SPACE  loss scales with beam divergence rather than
   exponentially — ⚠️ which is exactly why satellites help (§17)
```

---

# PART II — QUANTUM KEY DISTRIBUTION
