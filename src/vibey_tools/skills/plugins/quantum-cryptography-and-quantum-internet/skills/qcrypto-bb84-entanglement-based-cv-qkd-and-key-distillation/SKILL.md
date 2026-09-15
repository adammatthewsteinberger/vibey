---
name: qcrypto-bb84-entanglement-based-cv-qkd-and-key-distillation
description: "Use for the protocols themselves: BB84 step by step, entanglement-based QKD, continuous-variable QKD and how it differs in hardware and reach, and the post-processing that turns raw detections into a usable key — sifting, error correction and privacy amplification, which is where most of the practical difficulty lives."
---

# Quantum Cryptography: BB84, Entanglement-Based QKD, Continuous-Variable QKD, and From Raw Detections to a Usable Key

> **Part 2 of 6** of the *Quantum Cryptography, Quantum Encryption and the Quantum Internet* reference (plugin `quantum-cryptography-and-quantum-internet`), covering §6–§9. Sibling skills: `qcrypto-two-different-things-qubits-no-cloning-and-entanglement` (§0–§5), `qcrypto-security-claims-attacks-and-trusted-nodes` (§10–§13), `qcrypto-repeaters-memory-entanglement-distribution-and-satellite` (§14–§19), `qcrypto-official-position-qrng-quantum-threat-and-choosing` (§20–§23), `qcrypto-reference` (§24–§29). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 3. **⚠️ QUANTUM REPEATERS ARE THE BOTTLENECK** (§14 → `qcrypto-repeaters-memory-entanglement-distribution-and-satellite`, §24.1 → `qcrypto-reference`). **Without them, quantum
>    networks are point-to-point links chained through trusted nodes, which reintroduces
>    exactly the trust QKD was supposed to eliminate.**

---

## §6. BB84

**⚠️ Bennett and Brassard, 1984 — still the reference protocol.**
```
⚠️ THE PROTOCOL
   1. Alice sends photons, each encoded in a RANDOMLY chosen basis
      with a RANDOMLY chosen bit value
   2. Bob measures each in a RANDOMLY chosen basis
   3. ⚠️ SIFTING — over a public classical channel they compare
      BASES ONLY (never values) and discard where they differ.
      ⚠️ About half survive
   4. They sacrifice a sample of the remaining bits to estimate
      the ERROR RATE
   ⚠️ 5. IF THE ERROR RATE IS TOO HIGH, THEY ABORT — an eavesdropper
      measuring in the wrong basis (§2) injects errors
   6. Error correction and privacy amplification (§9)
⚠️ THE SECURITY INTUITION  ⚠️ eavesdropping is not PREVENTED,
   it is DETECTED. ⚠️ QKD does not stop interception; it stops you
   USING a key that was intercepted
```
**⚠️ Variants**: **B92 (simpler, two states), SARG04, and six-state protocols.**
> **⚠️ GOTCHA — real systems don't have single-photon sources, and this created a real
> attack.** ⚠️ **Attenuated lasers emit a Poissonian number of photons, so some pulses
> contain two or more — and an eavesdropper can split off the extra photon and keep it,
> learning the bit without disturbing what Bob receives.** **That is the PHOTON NUMBER
> SPLITTING attack.**
> ⚠️ **The fix — DECOY STATES, where the sender randomly varies pulse intensity so that
> splitting produces detectable statistical anomalies — is now standard and essentially
> mandatory. A QKD system without decoy states is not secure with realistic sources.**

---

## §7. Entanglement-Based QKD

**⚠️ E91 (Ekert, 1991)** uses entangled pairs: ⚠️ **a source distributes one photon to each
party, and correlated measurements produce the key.** **⚠️ Security comes from BELL
INEQUALITY VIOLATION — if the correlations are strong enough to violate Bell, monogamy
(§4 → `qcrypto-two-different-things-qubits-no-cloning-and-entanglement`) bounds what any eavesdropper can know.**
**⚠️ BBM92** is the practical entangled-source variant.
**⚠️ Advantages**: ⚠️ **the source can sit in the middle and need not be trusted in some
formulations; and no key exists anywhere until measurement, so there is nothing to steal
in advance.**
**⚠️ Disadvantages**: ⚠️ **entangled sources are harder, and rates are lower.**

---

## §8. Continuous-Variable QKD

**⚠️ Encodes in the quadratures of the light field rather than in discrete photon states**
— ⚠️ **and uses HOMODYNE DETECTION, which works with standard telecom photodiodes rather
than single-photon detectors.**
**⚠️ Advantages**: ⚠️ **cheaper, room-temperature detectors, better compatibility with
existing telecom equipment and wavelength multiplexing.**
**⚠️ Disadvantages**: ⚠️ **shorter range, more demanding error correction at low
signal-to-noise, and security proofs that historically lagged discrete-variable ones.**

---

## §9. ⚠️ From Raw Detections to a Usable Key

> **⚠️ The part popular accounts skip entirely, and it is where most of the actual
> engineering lives.**
```
⚠️ 1. SIFTING  discard basis mismatches (§6)
⚠️ 2. PARAMETER ESTIMATION  measure the QBER (quantum bit error
   rate). ⚠️ ALL errors must be attributed to the eavesdropper,
   because you cannot distinguish an attacker from a noisy fibre
⚠️ 3. ERROR RECONCILIATION  ⚠️ classical error correction over the
   public channel (Cascade, LDPC). ⚠️ This LEAKS information, and
   the leak must be accounted for in step 4
⚠️ 4. ⚠️ PRIVACY AMPLIFICATION  compress the corrected key with a
   universal hash so that the eavesdropper's partial knowledge is
   reduced to negligible. ⚠️ You throw away bits to buy secrecy
⚠️ 5. ⚠️ AUTHENTICATION of the classical channel — ⚠️ SEE §10
⚠️ THE RESULT  ⚠️ the final secret key is much shorter than the raw
   detections. ⚠️ Quoted "key rates" should always be SECRET key
   rate after all of this, and marketing sometimes quotes raw
```
**⚠️ Finite-key effects matter**: ⚠️ **asymptotic security proofs assume infinitely long
keys; real finite blocks require a stricter analysis and yield less key.** ⚠️ **A system
quoting asymptotic rates is quoting an upper bound it never achieves.**
