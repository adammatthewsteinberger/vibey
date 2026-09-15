---
name: crypto-advanced-constructions-blockchain-and-policy
description: "Use for the frontier and the context around it: advanced constructions including zero-knowledge proofs, multiparty computation, homomorphic encryption and threshold schemes with honest notes on their maturity, the cryptography specific to blockchains, and the law and policy layer of export control, lawful access debates and compliance obligations."
---

# Cryptography: Advanced Constructions, Blockchain Cryptography, and Law and Policy

> **Part 5 of 6** of the *Cryptography and Encryption* reference (plugin `cryptography-and-encryption`), covering §20–§22. Sibling skills: `crypto-what-it-solves-threat-models-randomness-hashes-and-macs` (§0–§5), `crypto-symmetric-aead-public-key-and-signatures` (§6–§10), `crypto-passwords-tls-pki-messaging-and-disk-encryption` (§11–§16), `crypto-implementation-failures-key-management-and-agility` (§17–§19), `crypto-reference` (§23–§28). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The primitives are stable. Two migrations are actively underway. See §23 → `crypto-reference` for post-quantum cryptography, and TLS certificate lifetimes.

> **⚠️ Cryptography is the part of security that mostly WORKS. The primitives are rarely
> broken; the systems built from them fail constantly** (§17 → `crypto-implementation-failures-key-management-and-agility`). ⚠️ **Almost every real-world
> break is a key management failure, an implementation bug, a protocol composition error,
> or a human process — not a cryptanalytic result.**
>
> **⚠️ THE RULE THAT MATTERS MOST: don't build it yourself.** ⚠️ **Use a vetted,
> well-maintained library at the highest level of abstraction that solves your problem.
> This document is for UNDERSTANDING what those libraries do and evaluating designs —
> not a recipe for implementing primitives.**
>
> **Complements an electromagnetism reference (the physical layer), and security-focused
> material on threat modelling and application security.**
>
> **⚠️ GOTCHA** boxes mark the failure modes that have caused real breaches.
>
> **The three ideas that organize this document:**
> 1. **⚠️ ENCRYPTION WITHOUT AUTHENTICATION IS BROKEN** (§7 → `crypto-symmetric-aead-public-key-and-signatures`). **Confidentiality alone is
>    almost never what you want, and unauthenticated ciphertext is malleable. Use AEAD.**
> 2. **⚠️ KEY MANAGEMENT IS THE HARD PART** (§18 → `crypto-implementation-failures-key-management-and-agility`). **The algorithm choice is usually easy
>    and usually not where you lose. Where keys live, who can reach them, and how they
>    rotate is where systems actually fail.**
> 3. **⚠️ AGILITY IS A DESIGN REQUIREMENT** (§19 → `crypto-implementation-failures-key-management-and-agility`, §23 → `crypto-reference`). **Every algorithm eventually
>    weakens. Systems that hardcoded their primitives are the ones in pain right now.**

---

## §20. Advanced Constructions

**⚠️ Real, deployed, and frequently oversold — worth knowing what each actually gives you.**
**⚠️ ZERO-KNOWLEDGE PROOFS**: ⚠️ **prove a statement is true without revealing why.**
**zk-SNARKs (⚠️ succinct, often needing a trusted setup) and zk-STARKs (⚠️ no trusted setup,
larger proofs).** **Genuine uses in privacy and verifiable computation.**
**⚠️ MULTI-PARTY COMPUTATION**: ⚠️ **jointly compute a function over private inputs;
practical for specific problems (private set intersection, threshold operations) and still
expensive for general computation.**
**⚠️ HOMOMORPHIC ENCRYPTION**: ⚠️ **compute on ciphertext.** ⚠️ **Partially homomorphic
schemes are practical; FULLY homomorphic encryption is real, improving, and still orders of
magnitude slower than plaintext computation.** **⚠️ Treat "we use FHE" claims sceptically
and ask about the performance envelope.**
**⚠️ THRESHOLD AND SECRET SHARING**: ⚠️ **Shamir's scheme splits a secret so that k of n
shares reconstruct it — genuinely useful for root key custody.** ⚠️ **Threshold signatures
avoid ever reconstructing the key at all.**
**⚠️ Differential privacy** — ⚠️ **not cryptography, but frequently deployed alongside it;
it bounds what can be learned about any individual from aggregate release.**

---

## §21. Blockchain Cryptography

**⚠️ What it actually uses**: ⚠️ **hash functions for linking and proof-of-work, Merkle
trees for efficient inclusion proofs, ECDSA or Schnorr signatures for transaction
authorization.** **⚠️ The cryptography is standard; the novelty is the consensus mechanism
and the incentive design, not the primitives.**
**⚠️ Merkle trees** are independently useful — ⚠️ **certificate transparency (§13 → `crypto-passwords-tls-pki-messaging-and-disk-encryption`), git,
and file integrity systems all use them.**
> **⚠️ GOTCHA — "blockchain" is not a cryptographic property.** ⚠️ **It does not make data
> true, only tamper-evident once recorded, and it says nothing about whether the input was
> correct.** **⚠️ And "your keys, your coins" means key management (§18 → `crypto-implementation-failures-key-management-and-agility`) with no recovery
> path — which has resulted in permanent, irreversible loss at large scale.**

---

## §22. Law and Policy

**⚠️ Export controls**: ⚠️ **historically severe (the "crypto wars"), substantially
liberalized, and still present in some jurisdictions and for some categories.**
**⚠️ Lawful access and "exceptional access"** is a genuinely contested policy question
where I'd rather set out the positions than pick one:
⚠️ **the law enforcement argument is that end-to-end encryption creates spaces where lawful
warrants cannot reach, with real consequences for serious crime investigation.**
⚠️ **The technical community's near-consensus counter-argument is that any mechanism
permitting third-party access constitutes a deliberate vulnerability that cannot be limited
to authorized users, that key escrow at scale creates an extraordinarily valuable target,
and that the software is globally available regardless of any one country's rules.**
⚠️ **Client-side scanning has been proposed as a middle path and criticized on the grounds
that it relocates rather than resolves the trust problem.**
**⚠️ Also relevant**: ⚠️ **compelled key disclosure laws vary sharply by jurisdiction, data
protection regimes increasingly treat encryption as an expected safeguard, and
jurisdiction-specific rules can require specific algorithms.**
