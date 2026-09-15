---
name: crypto-passwords-tls-pki-messaging-and-disk-encryption
description: "Use for applied protocols: password storage and KDFs including Argon2, scrypt and bcrypt and the parameter choices that matter, TLS and its handshake and configuration, PKI, certificates and chain validation, end-to-end encrypted messaging with ratchets and metadata limits, disk and file encryption and what it protects against, and the other protocols worth knowing."
---

# Cryptography: Password Storage and KDFs, TLS, PKI and Certificates, End-to-End Encrypted Messaging, Disk and File Encryption, and Other Protocols

> **Part 3 of 6** of the *Cryptography and Encryption* reference (plugin `cryptography-and-encryption`), covering §11–§16. Sibling skills: `crypto-what-it-solves-threat-models-randomness-hashes-and-macs` (§0–§5), `crypto-symmetric-aead-public-key-and-signatures` (§6–§10), `crypto-implementation-failures-key-management-and-agility` (§17–§19), `crypto-advanced-constructions-blockchain-and-policy` (§20–§22), `crypto-reference` (§23–§28). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §11. ⚠️ Password Storage and KDFs

> **⚠️ Passwords need a fundamentally different treatment from everything else here,
> because they are LOW ENTROPY. The design goal is to make guessing expensive.**
```
⚠️ USE A PASSWORD HASHING FUNCTION, NOT A HASH
   ⚠️ Argon2id — the current recommendation
   ⚠️ scrypt · bcrypt (⚠️ note its input length limit) · PBKDF2
      (⚠️ acceptable where required for compliance, weakest of these)
⚠️ WHY  ⚠️ these are deliberately SLOW and MEMORY-HARD.
   ⚠️ Memory hardness specifically resists GPU and ASIC attack,
   which is where the economics of cracking live
⚠️ SALT  ⚠️ unique per user, stored alongside. Defeats rainbow
   tables and stops identical passwords hashing identically
⚠️ PEPPER  a secret held separately from the database — ⚠️ useful
   defence in depth against database-only compromise
⚠️ NEVER  ⚠️ MD5, SHA-256 or any fast hash, salted or not.
   ⚠️ A GPU does billions of SHA-256 per second
⚠️ KDFs FOR KEY DERIVATION (different job)  ⚠️ HKDF for deriving
   multiple keys from one high-entropy secret. ⚠️ Do not reuse a
   single key for multiple purposes — derive separate ones
```
**⚠️ The modern guidance on password POLICY has inverted**: ⚠️ **length over composition
rules, no forced periodic rotation without evidence of compromise, and screening against
known-breached password lists.**

---

# PART II — PROTOCOLS

## §12. TLS

**⚠️ TLS 1.3 is a substantial improvement and largely a simplification**: ⚠️ **removed
static RSA key transport (so forward secrecy is mandatory), removed CBC and RC4, removed
compression, reduced the handshake to one round trip, and encrypted more of the handshake.**
**⚠️ Deprecated and to be disabled**: ⚠️ **SSLv2, SSLv3, TLS 1.0, TLS 1.1.**
**⚠️ The handshake in outline**: ⚠️ **negotiate parameters → key exchange (ECDHE) →
authenticate the server via certificate (§13) → derive keys → encrypted application data.**
**⚠️ 0-RTT is a genuine trade-off**: ⚠️ **it saves a round trip and is REPLAYABLE by design,
so it must only carry idempotent requests.**
**⚠️ Configuration is where most TLS problems live**: ⚠️ **certificate chain completeness
(⚠️ a missing intermediate is the classic "works in my browser, fails elsewhere" bug),
cipher suite selection, protocol versions, HSTS, and OCSP stapling.**

---

## §13. PKI and Certificates

**⚠️ The trust model is the weak point, and it is worth stating plainly.**
```
⚠️ HOW IT WORKS  a CA vouches that a public key belongs to a name;
   your OS/browser ships a ROOT STORE of trusted CAs; chains
   validate up to a root
⚠️ THE STRUCTURAL PROBLEM  ⚠️ ANY trusted CA can issue for ANY
   domain. ⚠️ Trust is the UNION of hundreds of organizations
   across many jurisdictions, and it is only as strong as the
   weakest one. ⚠️ Real CAs have been compromised or have
   misissued, more than once
⚠️ MITIGATIONS
   ⚠️ CERTIFICATE TRANSPARENCY  ⚠️ public append-only logs of issued
      certificates, so misissuance is DETECTABLE. ⚠️ The most
      effective structural fix deployed
   ⚠️ CAA records  restrict which CAs may issue for your domain
   ⚠️ Pinning  ⚠️ powerful and dangerous — HPKP was deprecated
      because it enabled permanent self-inflicted denial of service
⚠️ REVOCATION IS THE UNSOLVED PROBLEM  ⚠️ CRLs are large, OCSP is
   a privacy leak and a latency cost, and ⚠️ browsers commonly
   FAIL OPEN when the check is unavailable — meaning revocation
   often doesn't work. ⚠️ This is precisely why §23.2 is happening
```
**⚠️ Private PKI** for internal services is a different problem — ⚠️ **you control the root,
so you control policy, and CA/Browser Forum rules do not apply.**

---

## §14. End-to-End Encrypted Messaging

**⚠️ The Signal protocol** is the reference design and is used far beyond Signal itself.
```
⚠️ X3DH  initial key agreement that works when the recipient is OFFLINE
⚠️ DOUBLE RATCHET  ⚠️ the key idea. Keys advance with every message
   ⚠️ FORWARD SECRECY — old messages stay safe if a key leaks
   ⚠️ POST-COMPROMISE SECURITY — the session HEALS after a
      compromise, once a fresh DH ratchet step occurs
⚠️ SEALED SENDER  reduces metadata exposure to the server
⚠️ THE REMAINING HARD PROBLEMS
   ⚠️ 1. KEY VERIFICATION — ⚠️ E2EE without verifying the other
      party's key only protects against the SERVER lying if you
      check. Safety numbers exist and almost nobody compares them
   ⚠️ 2. METADATA (§1) — who and when is still largely visible
   ⚠️ 3. ⚠️ ENDPOINT SECURITY — E2EE is irrelevant against a
      compromised device, and backups are frequently the weak link
   ⚠️ 4. Multi-device and group messaging complicate everything
```
**⚠️ "End-to-end encrypted" is a claim to interrogate, not accept**: ⚠️ **ask who controls
the key directory, whether backups are encrypted with a key the provider holds, and whether
the client is verifiable.**

---

## §15. Disk and File Encryption

**⚠️ Full disk encryption** (BitLocker, FileVault, LUKS, dm-crypt) ⚠️ **protects data AT
REST — meaning a powered-off, lost or stolen device.** **⚠️ It provides essentially nothing
against malware on a running, unlocked system, which is the misconception that matters.**
**⚠️ Key hierarchy**: ⚠️ **a volume key wrapped by a key derived from the user's password
(§11) and/or sealed to a TPM/Secure Enclave — which is what makes hardware-bound
protections and rate limiting possible.**
**⚠️ Threat-model caveats**: ⚠️ **cold boot attacks against keys in RAM, DMA attacks,
evil-maid attacks against unencrypted boot components (⚠️ Secure Boot addresses part of
this), and the fact that "encrypted at rest" in cloud storage usually means the PROVIDER
holds the keys.**
**⚠️ Deniable encryption and hidden volumes** — ⚠️ **the cryptography works and the threat
model usually doesn't, because their existence is often inferable and legal compulsion
doesn't require proof.**

---

## §16. Other Protocols

**⚠️ SSH**: ⚠️ **host key trust-on-first-use — ⚠️ and blindly accepting the fingerprint
defeats the whole model; prefer key-based authentication over passwords; certificate-based
SSH scales far better than distributing authorized_keys.**
**⚠️ PGP/GPG**: ⚠️ **historically important and widely criticized — no forward secrecy,
complex and error-prone UX, long-lived keys, and a web of trust that never achieved
usability.** **⚠️ For messaging, modern alternatives (§14) are better; it persists for
package and release signing where its properties fit.**
**⚠️ VPNs**: ⚠️ **WireGuard is the modern design — small, opinionated, auditable, with a
deliberately fixed cipher suite (which is the anti-agility choice, and defensible for its
purpose).** ⚠️ **Note that a commercial VPN moves trust from your ISP to the VPN operator;
it does not create anonymity.**
**⚠️ Kerberos, OAuth/OIDC, JWT** — ⚠️ **and JWT specifically has a long list of
implementation traps: the `alg: none` acceptance bug, algorithm confusion between HMAC and
RSA verification, and unverified signature paths.** **⚠️ Prefer a vetted library and
explicitly pin the expected algorithm.**

---

# PART III — WHERE IT ACTUALLY BREAKS
