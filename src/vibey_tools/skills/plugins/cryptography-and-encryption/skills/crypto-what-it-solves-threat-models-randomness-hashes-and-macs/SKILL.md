---
name: crypto-what-it-solves-threat-models-randomness-hashes-and-macs
description: "Use before choosing any primitive: what cryptography does and does not solve and the problems people wrongly expect it to fix, threat models and what you are actually defending against, randomness and why CSPRNG choice and seeding is a common silent failure, hash functions and their security properties, and MACs and authentication. Includes the router for the whole cryptography reference."
---

# Cryptography: What Cryptography Does and Doesn't Solve, Threat Models, Randomness, Hash Functions, and MACs

> **Part 1 of 6** of the *Cryptography and Encryption* reference (plugin `cryptography-and-encryption`), covering §0–§5. Sibling skills: `crypto-symmetric-aead-public-key-and-signatures` (§6–§10), `crypto-passwords-tls-pki-messaging-and-disk-encryption` (§11–§16), `crypto-implementation-failures-key-management-and-agility` (§17–§19), `crypto-advanced-constructions-blockchain-and-policy` (§20–§22), `crypto-reference` (§23–§28). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §0. Routing

| You want... | Go to |
|---|---|
| **⚠️ What crypto does and doesn't solve** | **§1** |
| Threat models | §2 |
| **⚠️ Randomness** | **§3** |
| Hash functions | §4 |
| MACs | §5 |
| Symmetric ciphers and modes | §6 → `crypto-symmetric-aead-public-key-and-signatures` |
| **⚠️ AEAD** | **§7 → `crypto-symmetric-aead-public-key-and-signatures`** |
| Public key | §8 → `crypto-symmetric-aead-public-key-and-signatures` |
| Key exchange and forward secrecy | §9 → `crypto-symmetric-aead-public-key-and-signatures` |
| Signatures | §10 → `crypto-symmetric-aead-public-key-and-signatures` |
| **⚠️ Password storage** | **§11 → `crypto-passwords-tls-pki-messaging-and-disk-encryption`** |
| **TLS** | **§12 → `crypto-passwords-tls-pki-messaging-and-disk-encryption`** |
| PKI and certificates | §13 → `crypto-passwords-tls-pki-messaging-and-disk-encryption` |
| End-to-end messaging | §14 → `crypto-passwords-tls-pki-messaging-and-disk-encryption` |
| Disk and file encryption | §15 → `crypto-passwords-tls-pki-messaging-and-disk-encryption` |
| Other protocols | §16 → `crypto-passwords-tls-pki-messaging-and-disk-encryption` |
| **⚠️ Implementation failures** | **§17 → `crypto-implementation-failures-key-management-and-agility`** |
| **⚠️ Key management** | **§18 → `crypto-implementation-failures-key-management-and-agility`** |
| Crypto agility | §19 → `crypto-implementation-failures-key-management-and-agility` |
| Advanced constructions | §20 → `crypto-advanced-constructions-blockchain-and-policy` |
| Blockchain crypto | §21 → `crypto-advanced-constructions-blockchain-and-policy` |
| Law and policy | §22 → `crypto-advanced-constructions-blockchain-and-policy` |
| **What's live** | **§23 → `crypto-reference`** |
| Misconceptions, numbers | §24–§25 → `crypto-reference` |
| Books, quick ref, method | §26–§28 → `crypto-reference` |

---

## §1. ⚠️ What Cryptography Does and Doesn't Solve

```
⚠️ THE FOUR GOALS
   ⚠️ CONFIDENTIALITY  nobody else can read it
   ⚠️ INTEGRITY  it hasn't been altered
   ⚠️ AUTHENTICITY  it's from who you think
   ⚠️ NON-REPUDIATION  they can't later deny sending it
   ⚠️ These are DIFFERENT and require DIFFERENT mechanisms.
   ⚠️ Confusing them is the root of many design errors
⚠️ WHAT CRYPTO CANNOT DO
   ⚠️ Protect against a compromised ENDPOINT. ⚠️ If the attacker is
      on the device, encryption in transit is irrelevant
   ⚠️ Hide METADATA — ⚠️ who talked to whom, when, how often and how
      much. ⚠️ Metadata is frequently more revealing than content
   ⚠️ Fix a bad trust model. ⚠️ Encryption to the wrong party is
      perfectly secure and completely useless
   ⚠️ Solve authorization, availability, or insider abuse
   ⚠️ Compensate for users who will click through any warning
```
> **⚠️ GOTCHA — "don't roll your own crypto" is often misunderstood as being about
> ALGORITHMS. It's mostly about PROTOCOLS AND IMPLEMENTATIONS.** ⚠️ **Nobody sensible
> designs a new block cipher; plenty of teams compose existing primitives into a novel
> protocol, and that is where the failures come from.**
> **⚠️ The practical version: use libsodium/NaCl, Tink, the platform's crypto API, or an
> equivalent — at the highest level that solves your problem. ⚠️ If your code contains a
> mode of operation, an IV, or a padding decision, you are already lower-level than you
> probably need to be.**

---

## §2. Threat Models

**⚠️ KERCKHOFFS'S PRINCIPLE**: ⚠️ **the system should be secure even if everything about it
except the key is public knowledge.** **⚠️ "Security through obscurity" fails because
obscurity is not a secret you can rotate.**
```
⚠️ ADVERSARY MODELS, in ascending strength
   PASSIVE / eavesdropper · ⚠️ ACTIVE / can modify, inject, replay ·
   ⚠️ CHOSEN-PLAINTEXT and CHOSEN-CIPHERTEXT · ⚠️ ADAPTIVE ·
   ⚠️ PHYSICAL ACCESS (side channels, §17) · ⚠️ INSIDER
⚠️ THE QUESTIONS THAT DEFINE A DESIGN
   ⚠️ Who is the adversary and what can they DO?
   ⚠️ What must stay secret, and FOR HOW LONG? (§23.1)
   ⚠️ What is the trusted computing base?
   ⚠️ What happens when a key is compromised? (§9, §18)
```
**⚠️ Security proofs are conditional**: ⚠️ **"provably secure" means "reduces to a problem
we believe is hard, in a stated model, assuming the implementation is correct."** **⚠️ All
three qualifiers have failed in practice.**

---

# PART I — PRIMITIVES

## §3. ⚠️ Randomness

> **⚠️ The most under-appreciated failure point, and it breaks everything above it
> silently. Bad randomness produces output that LOOKS fine.**
```
⚠️ USE THE OPERATING SYSTEM CSPRNG. Always.
   ⚠️ /dev/urandom, getrandom(), BCryptGenRandom, SecRandomCopyBytes
   ⚠️ NEVER a language's default rand()/Math.random() — those are
      statistical PRNGs, deliberately fast and entirely predictable
⚠️ WHERE IT HAS GONE WRONG IN REALITY
   ⚠️ Insufficient entropy at BOOT on embedded devices and VMs —
      ⚠️ producing duplicate keys across many devices
   ⚠️ VM cloning replaying the same RNG state
   ⚠️ A distribution patch that reduced the effective keyspace
      of every key generated for years
   ⚠️ Deterministic nonce generation from a predictable counter (§17)
⚠️ THE /dev/random vs /dev/urandom DEBATE IS SETTLED on modern
   systems: ⚠️ once seeded, urandom is fine and blocking is not a
   security benefit
```

---

## §4. Hash Functions

**⚠️ Properties**: ⚠️ **preimage resistance, second preimage resistance, and COLLISION
resistance — and collision resistance is the weakest of the three and the first to fall.**
```
⚠️ STATUS
   ⚠️ MD5  BROKEN. Collisions are trivial. ⚠️ Not for anything security-related
   ⚠️ SHA-1  BROKEN for collisions (chosen-prefix collisions demonstrated).
      ⚠️ Deprecated everywhere that matters
   ⚠️ SHA-2 (SHA-256/384/512)  ⚠️ the current workhorse. Fine
   ⚠️ SHA-3 / Keccak  different internal structure (sponge) — ⚠️ a
      structural hedge rather than a replacement
   ⚠️ BLAKE2/BLAKE3  fast, secure, good choices
⚠️ LENGTH EXTENSION  ⚠️ SHA-2 (Merkle-Damgård) is vulnerable: knowing
   H(m) lets you compute H(m ‖ padding ‖ extra) without knowing m.
   ⚠️ THIS IS WHY H(key ‖ message) IS NOT A MAC (§5)
   ⚠️ SHA-3 and BLAKE are not vulnerable
```
> **⚠️ GOTCHA — collision resistance matters when an ATTACKER CONTROLS BOTH INPUTS
> (certificates, signed documents, code signing).** ⚠️ **It matters much less for HMAC or
> for a random-input use.** **⚠️ This is why SHA-1 was catastrophic for certificates and
> merely undesirable inside HMAC — but migrate anyway, because arguing about it costs more
> than replacing it.**
**⚠️ Do NOT use general-purpose hashes for passwords** (§11 → `crypto-passwords-tls-pki-messaging-and-disk-encryption`) — ⚠️ **their speed is the
problem.**

---

## §5. MACs

**⚠️ A MAC provides integrity and authenticity with a SHARED key.**
⚠️ **HMAC is the standard construction and is specifically designed to resist §4's length
extension.** ⚠️ **Poly1305 and KMAC are also good.**
**⚠️ CRITICAL PROPERTIES**:
⚠️ **verify in CONSTANT TIME (§17 → `crypto-implementation-failures-key-management-and-agility`) — a naive byte-by-byte comparison leaks the correct
value through timing, one byte at a time; and use a SEPARATE key from encryption, or
better, use AEAD (§7 → `crypto-symmetric-aead-public-key-and-signatures`) which handles it.**
**⚠️ A MAC is NOT a signature** — ⚠️ **both parties hold the same key, so a MAC cannot prove
to a third party who created it.** **No non-repudiation** (§1).
