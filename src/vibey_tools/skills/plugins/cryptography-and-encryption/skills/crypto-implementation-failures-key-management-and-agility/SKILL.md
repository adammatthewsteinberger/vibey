---
name: crypto-implementation-failures-key-management-and-agility
description: "Use when reviewing or hardening a real system, where most breaks actually happen: implementation failure modes including timing and side channels, nonce reuse, padding oracles and misuse of primitives, key management covering generation, storage, rotation, escrow and HSMs, and crypto agility — designing so an algorithm can be replaced without redesigning the system."
---

# Cryptography: Implementation Failure Modes, Key Management, and Crypto Agility

> **Part 4 of 6** of the *Cryptography and Encryption* reference (plugin `cryptography-and-encryption`), covering §17–§19. Sibling skills: `crypto-what-it-solves-threat-models-randomness-hashes-and-macs` (§0–§5), `crypto-symmetric-aead-public-key-and-signatures` (§6–§10), `crypto-passwords-tls-pki-messaging-and-disk-encryption` (§11–§16), `crypto-advanced-constructions-blockchain-and-policy` (§20–§22), `crypto-reference` (§23–§28). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The primitives are stable. Two migrations are actively underway. See §23 → `crypto-reference` for post-quantum cryptography, and TLS certificate lifetimes.

> **⚠️ Cryptography is the part of security that mostly WORKS. The primitives are rarely
> broken; the systems built from them fail constantly** (§17). ⚠️ **Almost every real-world
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
> 2. **⚠️ KEY MANAGEMENT IS THE HARD PART** (§18). **The algorithm choice is usually easy
>    and usually not where you lose. Where keys live, who can reach them, and how they
>    rotate is where systems actually fail.**
> 3. **⚠️ AGILITY IS A DESIGN REQUIREMENT** (§19, §23 → `crypto-reference`). **Every algorithm eventually
>    weakens. Systems that hardcoded their primitives are the ones in pain right now.**

---

## §17. ⚠️ Implementation Failure Modes

> **⚠️ This is where cryptography fails in the real world. The maths holds; the code
> doesn't.**
```
⚠️ NONCE / IV REUSE  ⚠️ THE most catastrophic and most common
   ⚠️ In CTR/GCM, reusing a (key, nonce) pair XORs two plaintexts
      together and, in GCM, ⚠️ can reveal the authentication key,
      allowing forgery
   ⚠️ Counters that reset on reboot, VM restore, or across
      instances are the usual cause. ⚠️ Use random 96+-bit nonces
      or a construction that tolerates misuse (AES-GCM-SIV)
⚠️ TIMING SIDE CHANNELS  ⚠️ comparison, table lookups, branches on
   secret data. ⚠️ Use constant-time comparison; ⚠️ note the
   compiler may optimize your careful code away
⚠️ PADDING ORACLES  ⚠️ distinguishing "bad padding" from "bad MAC"
   in an error message or timing lets an attacker decrypt.
   ⚠️ AEAD (§7) removes the class
⚠️ POWER/EM/ACOUSTIC side channels — physical access
⚠️ FAULT INJECTION  ⚠️ inducing an error during RSA-CRT signing
   can leak the private key from ONE faulty signature
⚠️ ERROR MESSAGES  ⚠️ any distinguishable failure is an oracle
⚠️ MEMORY  ⚠️ keys in swap, core dumps, logs, or freed-but-not-zeroed
   buffers. ⚠️ Garbage-collected languages make zeroization hard
⚠️ DOWNGRADE / VERSION NEGOTIATION  ⚠️ an attacker forcing the
   weakest mutually supported option. ⚠️ Remove weak options
⚠️ SPECULATIVE EXECUTION  Spectre/Meltdown-class leakage
```
**⚠️ The pattern worth internalizing**: ⚠️ **almost all of these are about the system
leaking information through a channel the mathematical model didn't include.**

---

## §18. ⚠️ Key Management

> **⚠️ The hard part, and the part that gets least attention in tutorials.**
```
⚠️ THE LIFECYCLE  generate (§3) → distribute → store → use →
   rotate → revoke → destroy. ⚠️ Every stage has failure modes
⚠️ STORAGE, best to worst
   ⚠️ HSM or secure element (⚠️ key never leaves the hardware)
   ⚠️ Cloud KMS / platform keystore
   ⚠️ Secrets manager with access control and audit
   ⚠️ Environment variables (⚠️ leak into logs, crash dumps and
      child processes)
   ⚠️ HARDCODED IN SOURCE — ⚠️ and therefore in git history forever.
      ⚠️ Still one of the most common real-world findings
⚠️ PRINCIPLES
   ⚠️ SEPARATE KEYS FOR SEPARATE PURPOSES — derive with HKDF (§11)
   ⚠️ Least privilege on key access; audit every use
   ⚠️ ⚠️ PLAN FOR COMPROMISE. Rotation is not a formality —
      it is the thing you'll need under pressure
   ⚠️ Key escrow and recovery are a genuine trade-off: losing the
      key means losing the data, and escrow creates a target
   ⚠️ ⚠️ Test the recovery path. An untested restore is not a backup
```
**⚠️ Secret scanning in CI and git history** is high-value and cheap. ⚠️ **Assume anything
committed once is permanently public and rotate it rather than deleting the commit.**

---

## §19. Crypto Agility

**⚠️ Every algorithm eventually weakens** — ⚠️ **MD5, SHA-1, RC4, DES, RSA-1024 were all
once fine.** **⚠️ Systems that hardcoded them are the ones in pain now, and §23.1 → `crypto-reference` is about
to repeat the lesson at unprecedented scale.**
```
⚠️ DESIGN FOR REPLACEMENT
   ⚠️ VERSION your ciphertexts and message formats from day one
   ⚠️ Negotiate algorithms rather than assuming
   ⚠️ ⚠️ Maintain a CRYPTOGRAPHIC INVENTORY — you cannot migrate
      what you cannot find, and this is the single biggest
      practical obstacle to §23.1
   ⚠️ Abstract crypto behind an interface
   ⚠️ Plan for LARGER keys and signatures (§23.1 breaks size
      assumptions in many protocols and hardware)
⚠️ THE TENSION  ⚠️ agility ADDS complexity and negotiation, which is
   itself an attack surface (downgrade attacks, §17).
   ⚠️ WireGuard deliberately chose the opposite — fixed suites,
   replace the protocol version instead. Both positions are defensible
```
