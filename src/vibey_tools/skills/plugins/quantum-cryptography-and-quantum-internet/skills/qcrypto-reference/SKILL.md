---
name: qcrypto-reference
description: "Use when correcting a quantum cryptography misconception, looking up a key rate, distance, loss, fidelity or detector figure, finding the sources, or needing a quick-reference picker — plus the current state of quantum repeater demonstrations and the government position on QKD. Companion to the other quantum cryptography skills."
---

# Quantum Cryptography: What's Live, Misconceptions, Numbers, and Sources

> **Part 6 of 6** of the *Quantum Cryptography, Quantum Encryption and the Quantum Internet* reference (plugin `quantum-cryptography-and-quantum-internet`), covering §24–§29. Sibling skills: `qcrypto-two-different-things-qubits-no-cloning-and-entanglement` (§0–§5), `qcrypto-bb84-entanglement-based-cv-qkd-and-key-distillation` (§6–§9), `qcrypto-security-claims-attacks-and-trusted-nodes` (§10–§13), `qcrypto-repeaters-memory-entanglement-distribution-and-satellite` (§14–§19), `qcrypto-official-position-qrng-quantum-threat-and-choosing` (§20–§23). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The protocols date to the 1980s and 90s. Two areas moved recently. See §24 for quantum repeater demonstrations, and the government position on QKD.

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
> 3. **⚠️ QUANTUM REPEATERS ARE THE BOTTLENECK** (§14 → `qcrypto-repeaters-memory-entanglement-distribution-and-satellite`, §24.1). **Without them, quantum
>    networks are point-to-point links chained through trusted nodes, which reintroduces
>    exactly the trust QKD was supposed to eliminate.**

---

## §24. What's Live — checked August 2026

### 24.1 ⚠️ Quantum repeaters crossed a real threshold
**⚠️ §14 → `qcrypto-repeaters-memory-entanglement-distribution-and-satellite`'s bottleneck moved in early 2026, and this is the development the NCSC named as
most likely to change its assessment** (§20 → `qcrypto-official-position-qrng-quantum-threat-and-choosing`).

- **⚠️ THE USTC RESULT.** ⚠️ **A team led by Jian-Wei Pan and Qiang Zhang, published in
  Nature in February 2026, demonstrated remote memory-memory entanglement between trapped
  calcium-40 ions connected by 10 km of spooled telecom fibre — achieving a coherence time
  of 550 ± 36 ms against an average entanglement generation time of 450 ms.**
- **⚠️ WHY THAT SPECIFIC COMPARISON IS THE WHOLE POINT** (§14 → `qcrypto-repeaters-memory-entanglement-distribution-and-satellite`, §15 → `qcrypto-repeaters-memory-entanglement-distribution-and-satellite`): ⚠️ **entanglement now
  SURVIVES LONGER THAN IT TAKES TO CREATE, which is the threshold that lets neighbouring
  segments be connected reliably and makes multi-stage repeaters physically possible.**
  ⚠️ **Coverage describes it as "what the field has been waiting for."**
- **⚠️ The same architecture produced a DI-QKD result** (§12 → `qcrypto-security-claims-attacks-and-trusted-nodes`): ⚠️ **1,917 secret key bits
  over 10 km with finite-size security analysis, and a positive asymptotic key rate over
  101 km — reported as extending achievable DI-QKD distance by more than two orders of
  magnitude.** ⚠️ **DI-QKD bases security on measurable quantum correlations rather than
  assumptions about trusted hardware, which directly addresses §11 → `qcrypto-security-claims-attacks-and-trusted-nodes`'s entire attack class.**
- **⚠️ Other 2026 milestones worth knowing:**
```
⚠️ Metropolitan multiplexed repeater with BELL NONLOCALITY certified —
   heralded entanglement between solid-state memories over 14.5 km,
   fidelity 78.6% ± 2.0%, CHSH violation by 3.7σ.
   ⚠️ Reported as the FIRST Bell nonlocality certification at
   metropolitan scale, combining single-photon heralding rates
   with two-photon phase robustness (§16)
⚠️ Multimode storage — entanglement between a telecom photon through
   25.3 km fibre and a stored photon, across 16,340 temporal modes
   (§15's multiplexing requirement)
⚠️ 420 km memory-memory entanglement reported to beat the
   repeaterless channel capacity (§5's bound)
⚠️ New York City — entanglement swapping across three nodes on
   ALREADY-DEPLOYED commercial telecom fibre (NYU, Qunnect, Cisco)
⚠️ Earlier Delft work: heralded entanglement between independently
   operated nodes 10 km apart via 25 km of deployed fibre
```
> **⚠️ GOTCHA — "physics validated" is not "product available," and the sources are
> explicit about this.** ⚠️ **One assessment notes the quantum link efficiency exceeds the
> deterministic threshold and the entanglement fidelity, while above classical bounds, is
> modest.** ⚠️ **Another states plainly that no commercial quantum repeater exists, and that
> programme planning should NOT assume availability on PQC migration timescales of roughly
> 2026–2033.**
> **⚠️ So the correct reading is: a genuine scientific threshold was crossed, the
> engineering runway to a deployable device remains long, and nothing about your
> cryptographic migration plan should change because of it.**

### 24.2 ⚠️ The QKD split: agencies against, Europe investing
**⚠️ The most useful thing to understand before reading any QKD claim, because the
disagreement is real and partly non-technical.**

- **⚠️ THE SCEPTIC CAMP is consistent and hardening** (§20 → `qcrypto-official-position-qrng-quantum-threat-and-choosing`). ⚠️ **NSA concludes
  quantum-resistant cryptography is "more cost effective and easily maintained" than QKD
  and does "not anticipate certifying or approving any QKD" products for national security
  use unless the limitations are overcome.** ⚠️ **NCSC took a 2025 position mirroring it.**
  ⚠️ **ANSSI and BSI reach similar conclusions on maturity and cost.** ⚠️ **CNSA 2.0
  explicitly rejects QKD for NSS, and reporting indicates a DoD memorandum banned it in DoD
  systems outright while setting a 31 December 2030 PQC deadline.**
- **⚠️ EUROPE IS SIMULTANEOUSLY INVESTING**, ⚠️ **treating QKD deployment as a strategic
  priority — which is why the EuroQCI programme and national quantum networks exist
  alongside ANSSI's and BSI's technical scepticism.** ⚠️ **China has invested at
  substantially greater scale** (§17 → `qcrypto-repeaters-memory-entanglement-distribution-and-satellite`, §24.1).
- ⚠️ **These positions are not straightforwardly contradictory. A government can
  simultaneously judge that QKD is not currently the right way to secure its own classified
  traffic AND that it wants domestic capability in a strategically significant technology.**
  **⚠️ Sovereignty, industrial policy and research capacity are legitimate reasons that are
  not security-per-euro arguments — and conflating them is how the debate gets confused.**

> **⚠️ GOTCHA — the criticism most worth internalizing is the DENIAL-OF-SERVICE one,
> because it is structural rather than an implementation flaw** (§20 → `qcrypto-official-position-qrng-quantum-threat-and-choosing`). ⚠️ **QKD's security
> mechanism is refusing to produce key when disturbance is detected — so an attacker who
> injects light to saturate the single-photon detectors cannot read anything AND leaves
> the parties unable to communicate.**
> **⚠️ A security property that converts a confidentiality attack into an availability
> attack is a real trade, not a pure gain.**

**⚠️ How I'd advise reading vendor claims in this space.** ⚠️ **"Unhackable" and "secured by
the laws of physics" are not supportable as stated** (§10 → `qcrypto-security-claims-attacks-and-trusted-nodes`, §11 → `qcrypto-security-claims-attacks-and-trusted-nodes`). ⚠️ **Ask: how is the
classical channel authenticated; how many trusted nodes; decoy states implemented; what
countermeasures against detector blinding and Trojan-horse attacks; is the quoted rate
SECRET key rate with finite-key analysis; and is this offered as defence in depth alongside
PQC or as a replacement for it?** **⚠️ A vendor with good answers to all six is selling
something real and narrower than the brochure.**

---

## §25. Misconceptions

| Misconception | Correction |
|---|---|
| Quantum cryptography and PQC are the same | ⚠️ **Nearly opposites. PQC is what's deployed** (§1 → `qcrypto-two-different-things-qubits-no-cloning-and-entanglement`) |
| QKD protects against quantum computers | ⚠️ **It addresses key distribution; the threat is to public-key crypto** (§1 → `qcrypto-two-different-things-qubits-no-cloning-and-entanglement`, §22 → `qcrypto-official-position-qrng-quantum-threat-and-choosing`) |
| QKD is unhackable | ⚠️ **Real systems have been broken via hardware** (§11 → `qcrypto-security-claims-attacks-and-trusted-nodes`) |
| "Unconditional security" means no assumptions | ⚠️ **It means no COMPUTATIONAL assumptions. Others remain** (§10 → `qcrypto-security-claims-attacks-and-trusted-nodes`) |
| QKD removes the need for classical crypto | ⚠️ **It cannot authenticate. It relocates the dependency** (§10 → `qcrypto-security-claims-attacks-and-trusted-nodes`, §20 → `qcrypto-official-position-qrng-quantum-threat-and-choosing`) |
| QKD prevents eavesdropping | ⚠️ **It DETECTS it. You abort rather than use the key** (§6 → `qcrypto-bb84-entanglement-based-cv-qkd-and-key-distillation`) |
| An eavesdropper is stopped | ⚠️ **They can still deny service by disturbing the channel** (§20 → `qcrypto-official-position-qrng-quantum-threat-and-choosing`) |
| Quantum signals can be amplified like classical ones | ⚠️ **No-cloning forbids it. Hence repeaters** (§3 → `qcrypto-two-different-things-qubits-no-cloning-and-entanglement`, §14 → `qcrypto-repeaters-memory-entanglement-distribution-and-satellite`) |
| Entanglement allows faster-than-light signalling | ⚠️ **It doesn't. A classical channel is always needed** (§4 → `qcrypto-two-different-things-qubits-no-cloning-and-entanglement`) |
| A national QKD backbone is end-to-end physics-secured | ⚠️ **Trusted nodes hold the key in the clear** (§13 → `qcrypto-security-claims-attacks-and-trusted-nodes`) |
| Single photons are used in practice | ⚠️ **Attenuated lasers. Hence decoy states** (§6 → `qcrypto-bb84-entanglement-based-cv-qkd-and-key-distillation`) |
| Advertised key rates are what you get | ⚠️ **Ask for SECRET key rate with finite-key analysis** (§9 → `qcrypto-bb84-entanglement-based-cv-qkd-and-key-distillation`) |
| Satellite QKD is untrusted end-to-end | ⚠️ **The satellite is typically a trusted node** (§17 → `qcrypto-repeaters-memory-entanglement-distribution-and-satellite`) |
| Quantum internet exists | ⚠️ **Deployed networks are stage 1 of six** (§18 → `qcrypto-repeaters-memory-entanglement-distribution-and-satellite`) |
| Quantum repeaters are available | ⚠️ **No commercial repeater exists** (§24.1) |
| The 2026 repeater results change migration plans | ⚠️ **They don't. Long engineering runway** (§24.1) |
| Europe investing means agencies were wrong | ⚠️ **Sovereignty and security-per-euro are different arguments** (§24.2) |
| QRNG is required for good randomness | ⚠️ **Any properly certified RNG is acceptable** (§21 → `qcrypto-official-position-qrng-quantum-threat-and-choosing`) |
| Grover's algorithm breaks AES | ⚠️ **Halves effective strength. AES-256 is fine** (§22 → `qcrypto-official-position-qrng-quantum-threat-and-choosing`) |

---

## §26. Numbers

```
⚠️ Fibre loss  ⚠️ ~0.2 dB/km at 1550 nm — ⚠️ EXPONENTIAL, no amplification
⚠️ BB84 sifting  ⚠️ ~half of detections survive basis comparison
⚠️ Micius  satellite-ground QKD; ⚠️ ~1,200 km entanglement distribution
⚠️ USTC repeater (Feb 2026, Nature)
   ⚠️ 10 km fibre · ⚠️ coherence 550 ± 36 ms vs generation 450 ms
   ⚠️ Coherence EXCEEDS generation time — the enabling threshold
⚠️ USTC DI-QKD  ⚠️ 1,917 secret key bits over 10 km (finite-size);
   ⚠️ positive asymptotic rate at 101 km — ⚠️ ~2 orders of magnitude
   further than prior DI-QKD
⚠️ Metropolitan multiplexed repeater  ⚠️ 14.5 km · fidelity 78.6% ± 2.0%
   · ⚠️ CHSH violation 3.7σ — first Bell nonlocality at metro scale
⚠️ Multimode storage  ⚠️ 16,340 temporal modes; 25.3 km fibre
⚠️ Delft  ⚠️ nodes 10 km apart via 25 km deployed fibre
⚠️ Quantum internet stages  ⚠️ 6 · ⚠️ deployed networks are at STAGE 1
⚠️ NSA limitations on QKD  ⚠️ 5
⚠️ DoD PQC deadline  ⚠️ reported 31 December 2030, with QKD banned
```

---

## §27. Sources

| Source | Why |
|---|---|
| **NSA, "QKD and Quantum Cryptography (QC)"** | ⚠️ **§20 → `qcrypto-official-position-qrng-quantum-threat-and-choosing`, primary. Read the five limitations yourself** |
| **NCSC, "Quantum networking technologies"** | ⚠️ **§20 → `qcrypto-official-position-qrng-quantum-threat-and-choosing`, primary and unusually clear** |
| **ANSSI and BSI position papers on QKD** | ⚠️ **§20 → `qcrypto-official-position-qrng-quantum-threat-and-choosing` — the European technical view** |
| **"The debate over QKD: A rebuttal to the NSA's objections"** | ⚠️ **The other side, seriously argued** |
| **Nielsen & Chuang** | ⚠️ **The standard quantum information text** |
| **Gisin et al., "Quantum cryptography" (Rev. Mod. Phys.)** | ⚠️ **The foundational review** |
| **Wehner, Elkouss & Hanson, "Quantum internet: a vision for the road ahead"** | ⚠️ **§18 → `qcrypto-repeaters-memory-entanglement-distribution-and-satellite`'s staged roadmap** |
| **Scarani et al., "The security of practical QKD"** | ⚠️ **§9–§11 → `qcrypto-bb84-entanglement-based-cv-qkd-and-key-distillation`, `qcrypto-security-claims-attacks-and-trusted-nodes`** |
| **ETSI QKD standards group** | Interoperability and certification |
| **NIST FIPS 203/204/205** | ⚠️ **§1 → `qcrypto-two-different-things-qubits-no-cloning-and-entanglement`'s alternative, and what to actually deploy** |

---

## §28. Quick Reference

### 28.1 Picker
| Question | Where |
|---|---|
| Should we deploy QKD? | ⚠️ **Almost certainly PQC instead** (§23 → `qcrypto-official-position-qrng-quantum-threat-and-choosing`) |
| Is QKD unhackable? | ⚠️ **No. Hardware attacks are demonstrated** (§11 → `qcrypto-security-claims-attacks-and-trusted-nodes`) |
| Does QKD replace classical crypto? | ⚠️ **No — it can't authenticate** (§10 → `qcrypto-security-claims-attacks-and-trusted-nodes`) |
| What does "unconditional" mean? | ⚠️ **No computational assumptions. Others remain** (§10 → `qcrypto-security-claims-attacks-and-trusted-nodes`) |
| Vendor claims physics-level security | ⚠️ **Ask the six questions in §24.2** |
| How far can QKD go? | ⚠️ **Limited by exponential loss; trusted nodes extend it** (§5 → `qcrypto-two-different-things-qubits-no-cloning-and-entanglement`, §13 → `qcrypto-security-claims-attacks-and-trusted-nodes`) |
| Are quantum repeaters here? | ⚠️ **Threshold crossed in the lab; no product** (§24.1) |
| Does the 2026 news change my plans? | ⚠️ **No** (§24.1) |
| Why is Europe building QKD then? | ⚠️ **Sovereignty is a different argument** (§24.2) |
| Do I need a QRNG? | ⚠️ **A certified RNG is acceptable** (§21 → `qcrypto-official-position-qrng-quantum-threat-and-choosing`) |
| What actually breaks my crypto? | ⚠️ **Shor's, against public-key. See a crypto reference** (§22 → `qcrypto-official-position-qrng-quantum-threat-and-choosing`) |

### 28.2 Evaluating a QKD proposal
- [ ] ⚠️ **How is the classical channel authenticated — PQC or pre-shared key?** (§10 → `qcrypto-security-claims-attacks-and-trusted-nodes`)
- [ ] ⚠️ **How many trusted nodes are in the path, and who operates them?** (§13 → `qcrypto-security-claims-attacks-and-trusted-nodes`)
- [ ] ⚠️ **Decoy states implemented?** (§6 → `qcrypto-bb84-entanglement-based-cv-qkd-and-key-distillation`)
- [ ] ⚠️ **Countermeasures for detector blinding and Trojan-horse attacks?** (§11 → `qcrypto-security-claims-attacks-and-trusted-nodes`)
- [ ] ⚠️ **Is the quoted rate SECRET key rate with finite-key analysis?** (§9 → `qcrypto-bb84-entanglement-based-cv-qkd-and-key-distillation`)
- [ ] ⚠️ **Offered ALONGSIDE PQC, or as a replacement?** (§23 → `qcrypto-official-position-qrng-quantum-threat-and-choosing`)
- [ ] Independent certification, and against what scheme? (§11 → `qcrypto-security-claims-attacks-and-trusted-nodes`)
- [ ] ⚠️ **What is the denial-of-service posture?** (§20 → `qcrypto-official-position-qrng-quantum-threat-and-choosing`)
- [ ] ⚠️ **Total cost against a pre-shared-key or PQC alternative** (§23 → `qcrypto-official-position-qrng-quantum-threat-and-choosing`)

---

## §29. Method

**§1–§23 → `qcrypto-two-different-things-qubits-no-cloning-and-entanglement`, `qcrypto-bb84-entanglement-based-cv-qkd-and-key-distillation`, `qcrypto-security-claims-attacks-and-trusted-nodes`, `qcrypto-repeaters-memory-entanglement-distribution-and-satellite`, `qcrypto-official-position-qrng-quantum-threat-and-choosing` rests on settled quantum information theory and a well-documented attack
literature** — **no-cloning, BB84, privacy amplification, the photon-number-splitting and
detector-blinding attacks, and the repeater architecture.** ⚠️ **None of it needed
verification; BB84 is from 1984 and the no-cloning theorem from 1982.**

**Two searches were run in August 2026**, on **agency positions on QKD** and **quantum
repeater and network milestones** — ⚠️ **the first because I was going to assert a strong
claim about official scepticism and wanted it verified rather than remembered, the second
because §14 → `qcrypto-repeaters-memory-entanglement-distribution-and-satellite`'s bottleneck is exactly where a genuine change would show up.**

**Confidence.** **High** in §1 → `qcrypto-two-different-things-qubits-no-cloning-and-entanglement`, §10 → `qcrypto-security-claims-attacks-and-trusted-nodes` and §11 → `qcrypto-security-claims-attacks-and-trusted-nodes`, which are the sections I'd most want read.
⚠️ **The QKD/PQC distinction is the single most useful thing here because the conflation is
near-universal in popular coverage.** ⚠️ **§10 → `qcrypto-security-claims-attacks-and-trusted-nodes`'s authentication bootstrap is the structural
argument that decides the practical question: QKD cannot authenticate, so it needs either
classical public-key crypto or a pre-shared symmetric key — and in the second case you
could have used the symmetric key directly.** **⚠️ §11 → `qcrypto-security-claims-attacks-and-trusted-nodes` matters because "secure by physics"
is a claim about the protocol while every real break has been against the apparatus.**

**High** on §20 → `qcrypto-official-position-qrng-quantum-threat-and-choosing`, which traces to NCSC's own publication and to NSA's stated position as
reported consistently across many independent sources: ⚠️ **the NCSC will not support QKD
for government or military applications and states plainly that QKD does not provide
authentication; NSA does not recommend it for NSS; ANSSI calls it niche and not
sufficiently mature; CNSA 2.0 rejects it.**
⚠️ **I have deliberately included the published rebuttal, because this is a genuine
technical disagreement and the rebuttal's framing — that the assessment depends on which
technological epoch you assume — is a fair point that §24.1 partially vindicates.**
⚠️ **The DoD ban and the 2030 deadline come via secondary reporting rather than the
memorandum itself and are marked as reported.**

**High** on §24.1's headline result, which was published in Nature and is reported
consistently: ⚠️ **550 ± 36 ms coherence against 450 ms generation time over 10 km of
trapped-ion-linked fibre, plus the DI-QKD figures.**
⚠️ **The significance framing — that coherence exceeding generation time is the threshold
enabling multi-stage repeaters — is the sources' own and is the part worth carrying.**
⚠️ **I have been careful to pair it with the explicit statement that no commercial repeater
exists and that migration planning should not assume one, because the temptation to read a
Nature result as a deployment signal is exactly the error this section should prevent.**
**⚠️ Sourcing caution: several supporting items come from quantum-industry outlets with an
interest in the field appearing to advance, so I anchored on the primary journal reports
where possible and marked the rest.**
