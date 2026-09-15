---
name: qcrypto-official-position-qrng-quantum-threat-and-choosing
description: "Use when making an actual decision: the official position of the national security agencies on QKD and why they recommend against it for most purposes, quantum random number generation and where it genuinely helps, the quantum computing threat to existing cryptography and realistic timelines, and a direct guide to choosing between QKD, QRNG and post-quantum cryptography for a given problem."
---

# Quantum Cryptography: The Official Position, Quantum Random Number Generation, the Quantum Computing Threat, and Choosing

> **Part 5 of 6** of the *Quantum Cryptography, Quantum Encryption and the Quantum Internet* reference (plugin `quantum-cryptography-and-quantum-internet`), covering §20–§23. Sibling skills: `qcrypto-two-different-things-qubits-no-cloning-and-entanglement` (§0–§5), `qcrypto-bb84-entanglement-based-cv-qkd-and-key-distillation` (§6–§9), `qcrypto-security-claims-attacks-and-trusted-nodes` (§10–§13), `qcrypto-repeaters-memory-entanglement-distribution-and-satellite` (§14–§19), `qcrypto-reference` (§24–§29). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The protocols date to the 1980s and 90s. Two areas moved recently. See §24 → `qcrypto-reference` for quantum repeater demonstrations, and the government position on QKD.

> **⚠️ FIRST, THE TERMINOLOGY DISASTER — because almost every popular article gets this
> wrong and the two things are nearly opposites** (§1 → `qcrypto-two-different-things-qubits-no-cloning-and-entanglement`).
> ⚠️ **POST-QUANTUM CRYPTOGRAPHY is classical mathematics running on ordinary computers,
> designed to resist quantum attack. It is what is actually being deployed** (see a
> cryptography reference).
> ⚠️ **QUANTUM CRYPTOGRAPHY / QKD uses quantum physics and special hardware to distribute
> keys. It is a niche technology that several major security agencies actively recommend
> AGAINST** (§20).
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

## §20. ⚠️ The Official Position

> **⚠️ The most important section for anyone evaluating a QKD procurement, and it is
> strikingly consistent across the anglophone agencies while Europe diverges** (§24.2 → `qcrypto-reference`).
**⚠️ The NSA's published position** identifies five limitations and concludes it does not
recommend QKD for national security systems.
```
⚠️ THE FIVE NSA LIMITATIONS, in substance
   ⚠️ 1. ⚠️ PARTIAL SOLUTION — QKD supplies keying material for
      confidentiality but ⚠️ CANNOT AUTHENTICATE ITS OWN
      TRANSMISSION SOURCE, so authentication requires asymmetric
      cryptography or pre-placed keys anyway (§10)
   ⚠️ 2. SPECIAL-PURPOSE EQUIPMENT — dedicated fibre or managed
      free-space transmitters; cannot be a software upgrade
   ⚠️ 3. Significant infrastructure and maintenance cost
   ⚠️ 4. ⚠️ IMPLEMENTATION SECURITY — the theory-device gap (§11)
   ⚠️ 5. ⚠️ DENIAL OF SERVICE — the quantum channel is trivially
      disruptable, and detecting an "eavesdropper" means REFUSING
      TO PRODUCE KEY, so an attacker who cannot read can still
      stop you communicating
```
**⚠️ The UK NCSC is equally direct**: ⚠️ **it "will not support the use of QKD for
government or military applications," endorses PQC as the best mitigation, and makes the
structural point plainly — QKD does not provide authentication, nor do any other quantum
techniques, so it must be combined with other cryptographic services and "should not be
relied on as a mechanism that provides substantial security value."** ⚠️ **For other
sectors it recommends QKD should not be solely relied upon.**
**⚠️ France's ANSSI** concludes QKD is usable "only in some niche use cases," is "not yet
sufficiently mature from a security perspective," and that the clear priorities should be
migration to PQC and/or adoption of symmetric keying. ⚠️ **Germany's BSI has published in
similar terms, with cost cited as a primary barrier.**
**⚠️ In the US this has hardened into policy**: ⚠️ **CNSA 2.0 explicitly rejects QKD for
national security systems, NSA advises agencies not to invest in or deploy QKD without
direct consultation, and reporting indicates a DoD PQC migration memorandum explicitly
BANNED QKD in DoD systems.**
> **⚠️ GOTCHA — read this as a genuine technical disagreement, not a settled fact, because
> the QKD community has responded substantively.** ⚠️ **A published rebuttal by Swiss
> researchers argues some NSA objections don't hold and others are expected to be resolved
> as cheaper optics and quantum repeaters arrive — explicitly framing the assessment as
> depending on which technological epoch you assume.**
> ⚠️ **And the NCSC's non-endorsement is reportedly not framed as permanent, with quantum
> repeaters cited as the development that would most change the assessment** (§14 → `qcrypto-repeaters-memory-entanglement-distribution-and-satellite`, §24.1 → `qcrypto-reference`).
> **⚠️ Verify current wording against the source documents rather than any paraphrase —
> including mine.**

---

## §21. Quantum Random Number Generation

**⚠️ The quantum security technology that is uncontroversially useful, and it deserves
separating from QKD.**
⚠️ **Measurement outcomes on a quantum superposition are fundamentally, not merely
practically, unpredictable — which makes a genuine entropy source.**
**⚠️ Implementations**: **photon path splitting, vacuum fluctuation measurement, phase
noise in lasers.**
**⚠️ The sober framing**: ⚠️ **NSA's position is that any RNG certified by appropriate
standards is acceptable if correctly implemented — so QRNG is fine, and is not
categorically required.** **⚠️ In practice a well-implemented OS CSPRNG seeded properly
(see a cryptography reference) is sufficient for almost all purposes, and QRNG's real value
is as a high-quality entropy source for seeding, and where certification demands it.**
⚠️ **Note that a QRNG still needs post-processing and health testing — a raw quantum source
with a device bias is just a biased source.**

---

## §22. The Quantum Computing Threat

**⚠️ Brief, because a cryptography reference covers the migration.**
⚠️ **SHOR'S ALGORITHM breaks RSA, Diffie-Hellman and elliptic curve cryptography — the
public-key foundations.** ⚠️ **GROVER'S ALGORITHM gives a quadratic speedup on brute-force
search, which effectively halves symmetric key strength and is why AES-256 remains
adequate.**
**⚠️ Requires a CRYPTOGRAPHICALLY RELEVANT quantum computer** — ⚠️ **millions of
high-quality error-corrected logical qubits, which is far beyond current hardware.**
**⚠️ Timeline estimates vary enormously and should be treated with suspicion in both
directions** — ⚠️ **vendors and national programmes both have incentives.**
**⚠️ HARVEST NOW, DECRYPT LATER is why the timeline is less important than people think**:
⚠️ **recorded traffic is a stored liability, so the relevant question is secrecy lifetime
plus migration time.**

---

## §23. ⚠️ Choosing

```
⚠️ FOR ESSENTIALLY EVERY ORGANIZATION: ⚠️ PQC
   ⚠️ Software upgrade · works end to end at any distance ·
   provides authentication · standardized · endorsed by every
   major agency · no new physical infrastructure
⚠️ QKD MIGHT MAKE SENSE WHEN, ALL AT ONCE
   ⚠️ You control dedicated fibre between two fixed points
   ⚠️ The distance is short, or you accept trusted nodes (§13)
   ⚠️ You already have pre-shared symmetric keys for
      authentication (§10)
   ⚠️ The cost is acceptable for a small number of links
   ⚠️ You want defence in depth rather than a replacement
   ⚠️ Or you have a sovereignty/strategic reason distinct from
      the technical case
⚠️ THE DEFENSIBLE HYBRID POSITION  ⚠️ QKD-derived key XORed or
   combined with a PQC-derived key, so security holds if EITHER
   holds. ⚠️ This is the architecture serious QKD deployments use,
   and it is an honest answer to §20's objections
⚠️ ALSO GENUINELY AVAILABLE  ⚠️ pre-shared symmetric keys with
   AES-256. ⚠️ Unglamorous, quantum-resistant, and adequate for
   the fixed-point-to-point case QKD targets
```
**⚠️ The question to ask any QKD vendor**: ⚠️ **"how do you authenticate the classical
channel, and how many trusted nodes are in this path?"** ⚠️ **The answers locate the actual
trust boundary.**
