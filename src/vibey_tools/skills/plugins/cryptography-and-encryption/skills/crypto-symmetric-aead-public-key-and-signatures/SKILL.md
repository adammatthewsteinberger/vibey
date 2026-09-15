---
name: crypto-symmetric-aead-public-key-and-signatures
description: "Use when selecting primitives: symmetric encryption with modes and the nonce rules that must not be broken, AEAD as the default you should almost always reach for, public key cryptography including RSA and elliptic curves, key exchange and forward secrecy, and digital signatures with their algorithms and the malleability and verification pitfalls."
---

# Cryptography: Symmetric Encryption, AEAD, Public Key Cryptography, Key Exchange and Forward Secrecy, and Digital Signatures

> **Part 2 of 6** of the *Cryptography and Encryption* reference (plugin `cryptography-and-encryption`), covering §6–§10. Sibling skills: `crypto-what-it-solves-threat-models-randomness-hashes-and-macs` (§0–§5), `crypto-passwords-tls-pki-messaging-and-disk-encryption` (§11–§16), `crypto-implementation-failures-key-management-and-agility` (§17–§19), `crypto-advanced-constructions-blockchain-and-policy` (§20–§22), `crypto-reference` (§23–§28). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 1. **⚠️ ENCRYPTION WITHOUT AUTHENTICATION IS BROKEN** (§7). **Confidentiality alone is
>    almost never what you want, and unauthenticated ciphertext is malleable. Use AEAD.**
> 2. **⚠️ KEY MANAGEMENT IS THE HARD PART** (§18 → `crypto-implementation-failures-key-management-and-agility`). **The algorithm choice is usually easy
>    and usually not where you lose. Where keys live, who can reach them, and how they
>    rotate is where systems actually fail.**
> 3. **⚠️ AGILITY IS A DESIGN REQUIREMENT** (§19 → `crypto-implementation-failures-key-management-and-agility`, §23 → `crypto-reference`). **Every algorithm eventually
>    weakens. Systems that hardcoded their primitives are the ones in pain right now.**

---

## §6. Symmetric Encryption

**⚠️ AES is the standard** (128/192/256-bit keys), ⚠️ **with hardware acceleration
essentially universal.** **⚠️ ChaCha20 is the good software-only alternative and is faster
without AES instructions.**
```
⚠️ MODES OF OPERATION — where block ciphers actually get used
   ⚠️ ECB  ⚠️ NEVER. Identical plaintext blocks produce identical
      ciphertext blocks — the famous encrypted-penguin image is
      still visible. ⚠️ ECB leaks structure
   ⚠️ CBC  needs a RANDOM, UNPREDICTABLE IV, and ⚠️ needs padding,
      which creates PADDING ORACLE exposure (§17)
   ⚠️ CTR  turns a block cipher into a stream cipher.
      ⚠️ NEVER REUSE A (key, nonce) PAIR — see §17
   ⚠️ GCM / ChaCha20-Poly1305  ⚠️ AEAD. Use these (§7)
⚠️ KEY SIZE  ⚠️ AES-128 remains secure against classical attack;
   AES-256 is the conservative choice and is already
   quantum-adequate (§23.1)
```
**⚠️ Stream ciphers**: ⚠️ **RC4 is broken and must not be used.** **⚠️ The general stream
cipher hazard is keystream reuse, which is catastrophic and easy to do accidentally.**

---

## §7. ⚠️ AEAD

> **⚠️ The single most important practical recommendation in this document: use
> AUTHENTICATED encryption with associated data, and don't compose encryption and
> authentication yourself.**
```
⚠️ WHY  ⚠️ unauthenticated ciphertext is MALLEABLE. An attacker can
   flip bits in ciphertext and produce predictable changes in the
   decrypted plaintext WITHOUT knowing the key. ⚠️ CTR-mode bit
   flips map one-to-one onto plaintext bits
⚠️ THE ORDER MATTERS IF YOU DO IT MANUALLY
   ⚠️ ENCRYPT-THEN-MAC is the correct construction
   ⚠️ MAC-then-encrypt and encrypt-and-MAC have both produced
      real vulnerabilities
   ⚠️ So don't do it manually — use AEAD
⚠️ USE  ⚠️ AES-GCM · ChaCha20-Poly1305 · AES-GCM-SIV (⚠️ nonce-misuse
   resistant — degrades gracefully rather than catastrophically) ·
   XChaCha20-Poly1305 (⚠️ large nonce, so random nonces are safe)
⚠️ ASSOCIATED DATA  authenticated but NOT encrypted — for headers
   and routing information that must be visible but not forgeable
⚠️ AND  ⚠️ DO NOT ACT ON DECRYPTED DATA BEFORE VERIFYING THE TAG.
   Release of unverified plaintext is its own vulnerability class
```

---

## §8. Public Key Cryptography

```
⚠️ RSA  based on factoring difficulty
   ⚠️ Use ≥2048-bit, preferably 3072+. ⚠️ RSA-1024 is not adequate
   ⚠️ PADDING IS MANDATORY AND SPECIFIC: OAEP for encryption,
      PSS for signatures. ⚠️ "Textbook RSA" (no padding) is
      completely insecure, and PKCS#1 v1.5 encryption padding has
      a long history of oracle attacks (Bleichenbacher, and it
      keeps coming back)
⚠️ ELLIPTIC CURVE  ⚠️ much smaller keys for equivalent strength —
   ~256-bit EC ≈ ~3072-bit RSA
   ⚠️ Curve25519/X25519 and Ed25519 are the modern defaults —
      designed to be MISUSE-RESISTANT, which matters more than
      marginal performance
   ⚠️ NIST P-curves are widely deployed and required in some
      compliance contexts; ⚠️ they are harder to implement safely
      (point validation, invalid curve attacks)
⚠️ ASYMMETRIC CRYPTO IS SLOW  ⚠️ so it is used to establish or wrap
   a SYMMETRIC key, not to encrypt bulk data. This is hybrid
   encryption and it is what essentially every real system does
```

---

## §9. Key Exchange and Forward Secrecy

**⚠️ Diffie-Hellman** lets two parties derive a shared secret over a public channel —
⚠️ **and unauthenticated DH is vulnerable to machine-in-the-middle, so it must be combined
with authentication** (§10, §13 → `crypto-passwords-tls-pki-messaging-and-disk-encryption`).
> **⚠️ GOTCHA — FORWARD SECRECY is the property to insist on, and it is defined by what
> happens AFTER a compromise.** ⚠️ **With ephemeral keys (ECDHE), compromising the
> long-term private key does NOT let an attacker decrypt previously recorded sessions.**
> **⚠️ Without it — as in RSA key transport — one key compromise retroactively exposes
> everything ever recorded.**
> ⚠️ **This is exactly why "harvest now, decrypt later" is a real strategy and why §23.1 → `crypto-reference`'s
> timeline matters: recorded traffic is a stored liability.**

**⚠️ Post-compromise security / self-healing** is the complementary property — ⚠️ **the
ability to RECOVER security after a compromise, which ratcheting protocols provide** (§14 → `crypto-passwords-tls-pki-messaging-and-disk-encryption`).

---

## §10. Digital Signatures

**⚠️ Sign with the PRIVATE key, verify with the PUBLIC key** — ⚠️ **the inverse of
encryption, and the confusion is common.**
```
⚠️ ALGORITHMS  ⚠️ Ed25519 (fast, deterministic, misuse-resistant —
   the modern default) · ECDSA (widely deployed) · RSA-PSS
⚠️ ECDSA'S NONCE HAZARD  ⚠️ ECDSA requires a per-signature random
   value k. ⚠️ REUSING k ACROSS TWO SIGNATURES REVEALS THE PRIVATE
   KEY through simple algebra. ⚠️ This has broken real systems,
   including a well-known games console. ⚠️ Even BIASED k leaks
   the key over many signatures
   ⚠️ Deterministic nonce generation (RFC 6979) or Ed25519 removes
   this entire class of failure
⚠️ SIGN THE RIGHT THING  ⚠️ sign a hash of a canonical encoding;
   ⚠️ ambiguity in what was signed is a real attack surface
⚠️ DOMAIN SEPARATION  ⚠️ include context so a signature valid in one
   protocol cannot be replayed as valid in another
```
