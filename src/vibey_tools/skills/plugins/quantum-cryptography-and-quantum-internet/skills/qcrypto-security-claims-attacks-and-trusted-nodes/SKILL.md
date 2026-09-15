---
name: qcrypto-security-claims-attacks-and-trusted-nodes
description: "Use when assessing a QKD security claim: what unconditional or information-theoretic security actually claims and the assumptions it depends on, the attacks that work against real systems including detector blinding and side channels, device-independent and measurement-device-independent approaches that close part of the gap, and the trusted-node problem that undermines most deployed networks."
---

# Quantum Cryptography: What Unconditional Security Actually Claims, Attacks on Real QKD Systems, Closing the Device Gap, and Trusted Nodes

> **Part 3 of 6** of the *Quantum Cryptography, Quantum Encryption and the Quantum Internet* reference (plugin `quantum-cryptography-and-quantum-internet`), covering §10–§13. Sibling skills: `qcrypto-two-different-things-qubits-no-cloning-and-entanglement` (§0–§5), `qcrypto-bb84-entanglement-based-cv-qkd-and-key-distillation` (§6–§9), `qcrypto-repeaters-memory-entanglement-distribution-and-satellite` (§14–§19), `qcrypto-official-position-qrng-quantum-threat-and-choosing` (§20–§23), `qcrypto-reference` (§24–§29). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    (§10). **It secures a key exchange against an eavesdropper on the channel. It does not
>    authenticate, does not protect endpoints, and cannot bootstrap trust from nothing.**
> 2. **⚠️ THE THEORY-IMPLEMENTATION GAP is the whole story** (§11). **Every deployed QKD
>    system that has been attacked was attacked through its hardware, not its protocol —
>    the security proofs assume devices the engineers cannot actually build.**
> 3. **⚠️ QUANTUM REPEATERS ARE THE BOTTLENECK** (§14 → `qcrypto-repeaters-memory-entanglement-distribution-and-satellite`, §24.1 → `qcrypto-reference`). **Without them, quantum
>    networks are point-to-point links chained through trusted nodes, which reintroduces
>    exactly the trust QKD was supposed to eliminate.**

---

## §10. ⚠️ What "Unconditional Security" Actually Claims

> **⚠️ The most oversold phrase in the field. It has a precise technical meaning that is
> much narrower than the marketing implies.**
```
⚠️ WHAT IT MEANS  ⚠️ security does not depend on assumptions about
   the ADVERSARY'S COMPUTATIONAL POWER. That's genuinely different
   from classical crypto and it is a real result
⚠️ WHAT IT STILL ASSUMES — and every one of these has failed somewhere
   ⚠️ The devices behave as the model says (§11 — they don't)
   ⚠️ The labs are secure and not leaking side channels
   ⚠️ ⚠️ THE CLASSICAL CHANNEL IS AUTHENTICATED
   ⚠️ The random number generators are sound
   ⚠️ Quantum mechanics is correct (fine) and the specific
      model of the source and detector is accurate (often not)
```
> **⚠️ GOTCHA — THE AUTHENTICATION BOOTSTRAP IS THE STRUCTURAL PROBLEM, and it is why
> agencies object** (§20 → `qcrypto-official-position-qrng-quantum-threat-and-choosing`). ⚠️ **QKD cannot authenticate. Without authentication, an
> attacker simply runs a machine-in-the-middle: separate QKD sessions with each party, and
> the physics detects nothing because each link is genuinely undisturbed.**
> **⚠️ So QKD requires either (a) classical public-key authentication — reintroducing
> exactly the classical dependency it was meant to remove — or (b) a PRE-SHARED SYMMETRIC
> KEY.**
> ⚠️ **And if you already have a pre-shared symmetric key, you could have used it directly
> with a symmetric algorithm. ⚠️ QKD's honest claim is that it EXPANDS a small pre-shared
> key into a large one, which is a real service and a much more modest one than "unhackable
> communication."**

---

## §11. ⚠️ Attacks on Real QKD Systems

**⚠️ Every publicly demonstrated break of a QKD system attacked the HARDWARE, not the
protocol. The gap between the security proof's idealized devices and real components is
where the vulnerabilities live.**
```
⚠️ DETECTOR BLINDING  ⚠️ the most damaging class. Bright illumination
   drives avalanche photodiodes out of Geiger mode into linear
   mode, where they respond to CLASSICAL light. ⚠️ The attacker
   then controls exactly which detector fires, learns the whole
   key, and the error rate stays low. ⚠️ Demonstrated against
   commercial systems
⚠️ TIME-SHIFT and EFFICIENCY MISMATCH  detectors whose efficiency
   differs over time lets an attacker bias which one fires
⚠️ PHOTON NUMBER SPLITTING  multi-photon pulses (§6) — decoy
   states are the fix
⚠️ TROJAN HORSE  ⚠️ inject light INTO Alice's device and read the
   reflection to learn her basis settings. ⚠️ Requires optical
   isolators and monitoring to defend
⚠️ LASER SEEDING / injection locking  manipulating the source
⚠️ LASER DAMAGE  ⚠️ permanently altering a component's behaviour
   with high power, then exploiting the modified device
⚠️ SIDE CHANNELS  timing, wavelength, spatial mode leakage
```
**⚠️ The honest reading**: ⚠️ **this is not a scandal — it is normal security engineering,
and the classical world has the same problem (see a cryptography reference on side
channels).** ⚠️ **But it directly undercuts the marketing claim, because "secure by the
laws of physics" is a statement about the protocol and the attacks are on the apparatus.**
**⚠️ It also means QKD needs the same thing everything else needs: certification, testing,
patching and a security update process — for hardware.**

---

## §12. Closing the Device Gap

**⚠️ MEASUREMENT-DEVICE-INDEPENDENT QKD (MDI-QKD)**: ⚠️ **both parties send to an untrusted
central node that performs a Bell measurement.** ⚠️ **Removes ALL detector side channels
(§11's worst class) at the cost of rate.** **⚠️ Practical and deployed in testbeds.**
**⚠️ TWIN-FIELD QKD** extends range substantially — ⚠️ **it scales with the square root of
channel transmittance rather than linearly, which lets it beat the repeaterless bound
(§5 → `qcrypto-two-different-things-qubits-no-cloning-and-entanglement`) without quantum memory.**
**⚠️ DEVICE-INDEPENDENT QKD (DI-QKD)**: ⚠️ **the theoretical ideal — security derived from
observed Bell violation alone, treating the devices as black boxes.** ⚠️ **Requires
extremely high detection efficiency and loophole-free operation, which is why it has been
a laboratory curiosity rather than a technology — until recently** (§24.1 → `qcrypto-reference`).
**⚠️ Note what remains assumed even in DI-QKD**: ⚠️ **the labs don't leak, the random
choices are free, and the devices don't communicate with the adversary.**

---

## §13. ⚠️ Trusted Nodes

> **⚠️ The awkward compromise at the heart of every deployed QKD network today.**
⚠️ **Because there are no working quantum repeaters (§14 → `qcrypto-repeaters-memory-entanglement-distribution-and-satellite`), long links are built by
chaining short QKD links through intermediate nodes.** ⚠️ **Each node DECRYPTS and
RE-ENCRYPTS the key.**
**⚠️ Therefore every intermediate node has the key in the clear and must be physically and
operationally trusted.**
> **⚠️ GOTCHA — this reintroduces exactly the trust model QKD was sold as eliminating.**
> ⚠️ **A "quantum-secured" national backbone with trusted relays is, from a trust
> standpoint, a chain of secure rooms — which is a perfectly reasonable engineering
> approach and is not "security guaranteed by physics" end to end.**
> **⚠️ When evaluating any deployed QKD network, the first question is: how many trusted
> nodes, and who operates them?**

---

# PART III — QUANTUM NETWORKS
