---
name: crypto-reference
description: "Use when correcting a cryptography misconception, looking up a key size, security level, hash output or KDF parameter, finding the books and references, or needing a quick-reference picker — plus the current state of the post-quantum migration and TLS certificate lifetimes. Companion to the other cryptography skills."
---

# Cryptography: What's Live, Misconceptions, Numbers, and Books

> **Part 6 of 6** of the *Cryptography and Encryption* reference (plugin `cryptography-and-encryption`), covering §23–§28. Sibling skills: `crypto-what-it-solves-threat-models-randomness-hashes-and-macs` (§0–§5), `crypto-symmetric-aead-public-key-and-signatures` (§6–§10), `crypto-passwords-tls-pki-messaging-and-disk-encryption` (§11–§16), `crypto-implementation-failures-key-management-and-agility` (§17–§19), `crypto-advanced-constructions-blockchain-and-policy` (§20–§22). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The primitives are stable. Two migrations are actively underway. See §23 for post-quantum cryptography, and TLS certificate lifetimes.

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
> 3. **⚠️ AGILITY IS A DESIGN REQUIREMENT** (§19 → `crypto-implementation-failures-key-management-and-agility`, §23). **Every algorithm eventually
>    weakens. Systems that hardcoded their primitives are the ones in pain right now.**

---

## §23. What's Live — checked August 2026

> **⚠️ Two migrations are underway simultaneously, and both are §19 → `crypto-implementation-failures-key-management-and-agility`'s lesson arriving as
> a deadline. Verify current status — these have specific dates that are moving through.**

### 23.1 ⚠️ Post-quantum cryptography: standards settled, deadlines now real
**⚠️ The largest cryptographic transition in the history of deployed systems, and the
algorithm question is closed — only sequencing and timing remain open.**

- **⚠️ THE STANDARDS, finalized August 2024 after an eight-year process:**
```
⚠️ ML-KEM (FIPS 203)  ⚠️ from CRYSTALS-Kyber. Module-lattice KEM,
   IND-CCA2. ⚠️ Replaces RSA and ECDH KEY EXCHANGE
   ⚠️ Public keys ~800–1568 bytes, ciphertexts ~768–1568 bytes
⚠️ ML-DSA (FIPS 204)  ⚠️ from CRYSTALS-Dilithium. Lattice signatures
   ⚠️ ~2420–4595 bytes — replaces ECDSA and RSA signing
⚠️ SLH-DSA (FIPS 205)  ⚠️ from SPHINCS+. Hash-based, ⚠️ security
   resting SOLELY on hash properties — a structural hedge against
   lattice cryptanalysis. ⚠️ Signatures ~7856–49856 bytes
⚠️ HQC selected March 2025 as a code-based BACKUP KEM;
   a Falcon-based signature standard is expected
```
- **⚠️ THE DEADLINES.** ⚠️ **NIST IR 8547 (initial public draft, November 2024) schedules
  RSA-2048 and ECC P-256 — the ~112-bit-security algorithms — DEPRECATED BY 2030 and
  DISALLOWED AFTER 2035.** ⚠️ **Reporting indicates a June 2026 executive order (14412)
  treats the 2030 date as a compliance deadline for federal high-value assets, with OMB
  guidance directing alignment to IR 8547 and 2035 for full migration.**
  ⚠️ **NSA CNSA 2.0 requires national security systems to migrate by 2030–2035, specifying
  ML-KEM-1024 and ML-DSA-87 alongside AES-256 and SHA-384/512.** ⚠️ **The EU published a
  coordinated roadmap in June 2025 with national strategies and cryptographic inventories
  expected by end-2026 and critical infrastructure high-risk transition by 2030.**
- **⚠️ AES-256 DOES NOT NEED REPLACING.** ⚠️ **PQC migration is about PUBLIC-KEY
  cryptography, where Shor's algorithm applies.** **⚠️ Symmetric algorithms face Grover's
  algorithm, which roughly halves effective key strength — and AES-256 already accommodates
  that.** ⚠️ **This is the single most common misunderstanding of the whole transition.**

> **⚠️ GOTCHA — "HARVEST NOW, DECRYPT LATER" is why this is urgent despite no quantum
> computer existing.** ⚠️ **An adversary recording encrypted traffic today can decrypt it
> retrospectively once a cryptographically relevant quantum computer exists.**
> **⚠️ Therefore: any data encrypted today with RSA or ECC that must stay confidential for
> more than roughly 5–10 years is ALREADY exposed.** ⚠️ **The relevant question is not
> "when will quantum computers arrive" but "how long must this stay secret, plus how long
> will migration take" — and if that sum exceeds the arrival date, you are already late.**

**⚠️ Why HYBRID deployment is the norm, and this is the nuance that gets lost.**
⚠️ **In TLS, ML-KEM is deployed combined with classical ECDH — X25519MLKEM768 — providing
security against both classical and quantum adversaries simultaneously.** ⚠️ **NIST
explicitly endorses hybrids during the transition, and the reason is honest caution: the
PQC candidates represent a comparatively young attack surface.**
⚠️ **The cautionary evidence is concrete: SIKE and Rainbow were BROKEN DURING the NIST
evaluation — SIKE by a polynomial-time attack in 2022 — demonstrating that absence of known
attacks differs fundamentally from proof of hardness.** ⚠️ **And implementations have proven
fragile, with side-channel attacks reported recovering ML-KEM and Dilithium keys from both
masked and unmasked implementations** (§17 → `crypto-implementation-failures-key-management-and-agility`).
**⚠️ The practical obstacles are §19 → `crypto-implementation-failures-key-management-and-agility`'s**: ⚠️ **larger keys and signatures break size
assumptions in protocols and constrained hardware, and the cryptographic INVENTORY problem
is the real blocker — organizations cannot migrate what they have not found.**

### 23.2 ⚠️ TLS certificate lifetimes are collapsing toward 47 days
**⚠️ §13 → `crypto-passwords-tls-pki-messaging-and-disk-encryption`'s unsolved revocation problem being addressed by making certificates expire fast
instead — and it is forcing automation across the entire web.**

- **⚠️ CA/Browser Forum Ballot SC-081v3, proposed by Apple and passed 11 April 2025** —
  ⚠️ **reportedly 29 votes in favour, none opposed, with five abstentions.**
- **⚠️ THE SCHEDULE:**
```
⚠️ Until 15 March 2026   398 days (DCV reuse 398 days)
⚠️ From 15 March 2026    200 days (DCV reuse 200 days)
⚠️ From 15 March 2027    100 days
⚠️ From 15 March 2029    ⚠️ 47 days, ⚠️ DCV reuse 10 DAYS
```
- **⚠️ The DCV reuse collapse is the part that actually forces the change.** ⚠️ **At 47-day
  validity with 10-day domain-control-validation reuse, domain ownership must be re-proved
  roughly 35 times per year per domain.** ⚠️ **Email-based validation and manual HTTP file
  placement are not viable at that frequency — ACME automation via DNS-01 or HTTP-01
  becomes effectively the only practical method.**
- **⚠️ The stated rationale** is §13 → `crypto-passwords-tls-pki-messaging-and-disk-encryption`'s: ⚠️ **shorter lifetimes reduce the window in which a
  certificate remains valid after its information is no longer accurate, and the ballot
  explicitly treats revocation's limitations as given and uses expiry as the workaround.**

> **⚠️ GOTCHA — a practical detail that catches people: the ballot numbers are NOT what CAs
> issue.** ⚠️ **DigiCert, for instance, moved to a 199-day maximum from 24 February 2026
> rather than 200 — validity limits are precise to the second, so CAs issue just under the
> cap.** **⚠️ Don't build automation that assumes exactly 200.**
> **⚠️ Scope limit worth knowing: this covers PUBLICLY TRUSTED TLS certificates only.**
> ⚠️ **Private/internal PKI is unaffected and can still issue multi-year certificates; code
> signing and S/MIME operate under different rules.**

**⚠️ The honest criticism, which is worth recording.** ⚠️ **The change is not universally
regarded as pure security benefit: critics note that CAs and certificate lifecycle
management vendors profit from the acceleration, and that using short expiry as a substitute
for working revocation may be pragmatic engineering or may be accumulating technical debt —
that question is genuinely open.**
⚠️ **Note also that much of the available commentary comes from CAs and CLM vendors selling
the solution, which I have weighted accordingly.**
**⚠️ The operational advice is unambiguous regardless**: ⚠️ **inventory every publicly
trusted certificate and its renewal method now; identify infrastructure without ACME
support, because that is where the risk concentrates; and treat the 2026 step as the forcing
function rather than waiting for 2029.** ⚠️ **A separate ballot (SC-085v2) requiring CAs to
validate DNSSEC took effect on the same March 2026 date.**

---

## §24. Misconceptions

| Misconception | Correction |
|---|---|
| Encryption makes data secure | ⚠️ **It solves four specific problems and not others** (§1 → `crypto-what-it-solves-threat-models-randomness-hashes-and-macs`) |
| Encrypted means private | ⚠️ **Metadata is often more revealing than content** (§1 → `crypto-what-it-solves-threat-models-randomness-hashes-and-macs`) |
| Don't roll your own crypto means algorithms | ⚠️ **Mostly protocols and implementations** (§1 → `crypto-what-it-solves-threat-models-randomness-hashes-and-macs`) |
| Secret algorithms are safer | ⚠️ **Kerckhoffs. You can't rotate obscurity** (§2 → `crypto-what-it-solves-threat-models-randomness-hashes-and-macs`) |
| Any random number will do | ⚠️ **OS CSPRNG only. rand() is predictable** (§3 → `crypto-what-it-solves-threat-models-randomness-hashes-and-macs`) |
| SHA-256 of a password is fine | ⚠️ **Its speed is the problem. Use Argon2id** (§4 → `crypto-what-it-solves-threat-models-randomness-hashes-and-macs`, §11 → `crypto-passwords-tls-pki-messaging-and-disk-encryption`) |
| HMAC is just hashing the key with the message | ⚠️ **H(key‖msg) breaks via length extension** (§4 → `crypto-what-it-solves-threat-models-randomness-hashes-and-macs`, §5 → `crypto-what-it-solves-threat-models-randomness-hashes-and-macs`) |
| A MAC is a signature | ⚠️ **Shared key — no non-repudiation** (§5 → `crypto-what-it-solves-threat-models-randomness-hashes-and-macs`) |
| ECB is fine for small data | ⚠️ **It leaks structure. Never** (§6 → `crypto-symmetric-aead-public-key-and-signatures`) |
| Encryption alone protects the message | ⚠️ **Unauthenticated ciphertext is malleable. Use AEAD** (§7 → `crypto-symmetric-aead-public-key-and-signatures`) |
| MAC-then-encrypt is fine | ⚠️ **Encrypt-then-MAC — or just use AEAD** (§7 → `crypto-symmetric-aead-public-key-and-signatures`) |
| RSA without padding still works | ⚠️ **Textbook RSA is insecure. OAEP/PSS** (§8 → `crypto-symmetric-aead-public-key-and-signatures`) |
| Bigger RSA keys are always better | ⚠️ **EC gives equivalent strength far smaller** (§8 → `crypto-symmetric-aead-public-key-and-signatures`) |
| TLS means forward secrecy | ⚠️ **Only with ephemeral key exchange** (§9 → `crypto-symmetric-aead-public-key-and-signatures`) |
| Reusing a signature nonce is sloppy | ⚠️ **It reveals the private key outright** (§10 → `crypto-symmetric-aead-public-key-and-signatures`) |
| Salting is enough for passwords | ⚠️ **Salt defeats rainbow tables, not GPUs** (§11 → `crypto-passwords-tls-pki-messaging-and-disk-encryption`) |
| Force password rotation every 90 days | ⚠️ **Modern guidance inverted this** (§11 → `crypto-passwords-tls-pki-messaging-and-disk-encryption`) |
| A valid certificate means you're safe | ⚠️ **Any of hundreds of CAs can issue for any domain** (§13 → `crypto-passwords-tls-pki-messaging-and-disk-encryption`) |
| Revocation works | ⚠️ **Browsers frequently fail open** (§13 → `crypto-passwords-tls-pki-messaging-and-disk-encryption`, §23.2) |
| E2EE protects me completely | ⚠️ **Not against a compromised endpoint, or unverified keys** (§14 → `crypto-passwords-tls-pki-messaging-and-disk-encryption`) |
| Full disk encryption protects a running machine | ⚠️ **It protects data at rest** (§15 → `crypto-passwords-tls-pki-messaging-and-disk-encryption`) |
| Nonce reuse is a minor bug | ⚠️ **Catastrophic — can reveal the auth key in GCM** (§17 → `crypto-implementation-failures-key-management-and-agility`) |
| Timing differences are too small to exploit | ⚠️ **They're a demonstrated attack class** (§17 → `crypto-implementation-failures-key-management-and-agility`) |
| Environment variables are secure storage | ⚠️ **They leak into logs and dumps** (§18 → `crypto-implementation-failures-key-management-and-agility`) |
| Deleting the commit removes the secret | ⚠️ **Rotate it. It's public** (§18 → `crypto-implementation-failures-key-management-and-agility`) |
| Blockchain makes data true | ⚠️ **Tamper-evident once recorded. Not correct** (§21 → `crypto-advanced-constructions-blockchain-and-policy`) |
| Quantum computers break AES | ⚠️ **AES-256 is already adequate. It's public-key that breaks** (§23.1) |
| No quantum computer, so no urgency | ⚠️ **Harvest now, decrypt later** (§23.1) |
| PQC algorithms are proven safe | ⚠️ **SIKE and Rainbow broke during evaluation. Hence hybrids** (§23.1) |
| I can keep buying 1-year certificates | ⚠️ **200 days now, 47 by 2029** (§23.2) |

---

## §25. Numbers

```
⚠️ AES  128/192/256 · ⚠️ AES-256 already quantum-adequate
⚠️ RSA  ⚠️ ≥2048, prefer 3072+ · ⚠️ EC ~256-bit ≈ RSA ~3072-bit
⚠️ Broken hashes  ⚠️ MD5 (collisions trivial) · SHA-1 (chosen-prefix)
⚠️ Nonce  ⚠️ NEVER reuse (key, nonce). GCM: 96-bit standard
⚠️ Password hashing  ⚠️ Argon2id preferred · never a fast hash
⚠️ ML-KEM (FIPS 203)  ⚠️ pubkeys ~800–1568 B · ciphertexts ~768–1568 B
⚠️ ML-DSA (FIPS 204)  ⚠️ signatures ~2420–4595 B
⚠️ SLH-DSA (FIPS 205)  ⚠️ signatures ~7856–49856 B
⚠️ PQC security levels  L1≈AES-128 · L3≈AES-192 · L5≈AES-256
⚠️ NIST IR 8547  ⚠️ RSA-2048/ECC-256 deprecated 2030, disallowed 2035
⚠️ NSA CNSA 2.0  ⚠️ ML-KEM-1024, ML-DSA-87; NSS migration by 2030–2035
⚠️ TLS hybrid KEX  ⚠️ X25519MLKEM768
⚠️ Cert lifetimes  ⚠️ 398 → 200 (Mar 2026) → 100 (Mar 2027) → 47 (Mar 2029)
⚠️ DCV reuse  ⚠️ 398 → 200 → ... → 10 days (2029), ~35 revalidations/yr
⚠️ SC-081v3 vote  ⚠️ 29 for, 0 against, 5 abstentions (11 Apr 2025)
```

---

## §26. Books and References

| Source | Why |
|---|---|
| **Aumasson, *Serious Cryptography*** | ⚠️ **The best modern practitioner introduction. Start here** |
| **Ferguson, Schneier & Kohno, *Cryptography Engineering*** | ⚠️ **On building systems, not just primitives** |
| **Katz & Lindell, *Introduction to Modern Cryptography*** | ⚠️ **The rigorous academic standard** |
| **Boneh & Shoup, *A Graduate Course in Applied Cryptography*** | ⚠️ **Free online, comprehensive** |
| **Cryptopals challenges** | ⚠️ **Learn the attacks by implementing them. Genuinely excellent** |
| **libsodium / Tink documentation** | ⚠️ **§1 → `crypto-what-it-solves-threat-models-randomness-hashes-and-macs`'s recommendation, in practice** |
| **Latacora's "Cryptographic Right Answers"** | ⚠️ **Opinionated, current, correct defaults** |
| **NIST FIPS 203/204/205 and IR 8547** | ⚠️ **§23.1, primary** |
| **CA/Browser Forum Baseline Requirements** | ⚠️ **§13 → `crypto-passwords-tls-pki-messaging-and-disk-encryption`, §23.2, primary** |
| **Signal protocol specifications** | ⚠️ **§14 → `crypto-passwords-tls-pki-messaging-and-disk-encryption`, well documented and readable** |
| **RFC 8446 (TLS 1.3), RFC 5869 (HKDF), RFC 6979** | Primary protocol sources |

---

## §27. Quick Reference

### 27.1 Picker
| Need | Answer |
|---|---|
| Encrypt data | ⚠️ **AEAD — AES-GCM or ChaCha20-Poly1305** (§7 → `crypto-symmetric-aead-public-key-and-signatures`) |
| Encrypt with a password | ⚠️ **Argon2id to derive, then AEAD** (§7 → `crypto-symmetric-aead-public-key-and-signatures`, §11 → `crypto-passwords-tls-pki-messaging-and-disk-encryption`) |
| Store passwords | ⚠️ **Argon2id, unique salt. Never a fast hash** (§11 → `crypto-passwords-tls-pki-messaging-and-disk-encryption`) |
| Verify integrity with a shared key | ⚠️ **HMAC, constant-time compare** (§5 → `crypto-what-it-solves-threat-models-randomness-hashes-and-macs`) |
| Prove authorship to third parties | ⚠️ **Ed25519 signature** (§10 → `crypto-symmetric-aead-public-key-and-signatures`) |
| Agree a key over a public channel | ⚠️ **X25519 ECDHE — ephemeral for forward secrecy** (§9 → `crypto-symmetric-aead-public-key-and-signatures`) |
| Derive several keys from one secret | ⚠️ **HKDF. Never reuse one key for two purposes** (§11 → `crypto-passwords-tls-pki-messaging-and-disk-encryption`) |
| Generate randomness | ⚠️ **OS CSPRNG** (§3 → `crypto-what-it-solves-threat-models-randomness-hashes-and-macs`) |
| Secure a web service | ⚠️ **TLS 1.3, complete chain, ACME automation** (§12 → `crypto-passwords-tls-pki-messaging-and-disk-encryption`, §23.2) |
| Store a key | ⚠️ **HSM > KMS > secrets manager. Never in source** (§18 → `crypto-implementation-failures-key-management-and-agility`) |
| Compare two secrets | ⚠️ **Constant-time comparison** (§5 → `crypto-what-it-solves-threat-models-randomness-hashes-and-macs`, §17 → `crypto-implementation-failures-key-management-and-agility`) |
| Protect data for 10+ years | ⚠️ **Plan PQC now — harvest now, decrypt later** (§23.1) |
| Pick a curve | ⚠️ **Curve25519/Ed25519 unless compliance dictates otherwise** (§8 → `crypto-symmetric-aead-public-key-and-signatures`) |

### 27.2 Design review checklist
- [ ] ⚠️ **Using a vetted library at the highest useful level** (§1 → `crypto-what-it-solves-threat-models-randomness-hashes-and-macs`)
- [ ] ⚠️ **Threat model written down — who, capabilities, secrecy duration** (§2 → `crypto-what-it-solves-threat-models-randomness-hashes-and-macs`)
- [ ] ⚠️ **All randomness from the OS CSPRNG** (§3 → `crypto-what-it-solves-threat-models-randomness-hashes-and-macs`)
- [ ] ⚠️ **AEAD everywhere; no unauthenticated ciphertext** (§7 → `crypto-symmetric-aead-public-key-and-signatures`)
- [ ] ⚠️ **Nonce uniqueness guaranteed across reboots, restores and instances** (§17 → `crypto-implementation-failures-key-management-and-agility`)
- [ ] Constant-time comparison for all secret-dependent checks (§5 → `crypto-what-it-solves-threat-models-randomness-hashes-and-macs`, §17 → `crypto-implementation-failures-key-management-and-agility`)
- [ ] ⚠️ **Passwords via Argon2id/scrypt/bcrypt, salted** (§11 → `crypto-passwords-tls-pki-messaging-and-disk-encryption`)
- [ ] Separate keys per purpose, derived via HKDF (§11 → `crypto-passwords-tls-pki-messaging-and-disk-encryption`, §18 → `crypto-implementation-failures-key-management-and-agility`)
- [ ] ⚠️ **Forward secrecy for anything transported** (§9 → `crypto-symmetric-aead-public-key-and-signatures`)
- [ ] ⚠️ **No secrets in source, env vars, logs or error messages** (§17 → `crypto-implementation-failures-key-management-and-agility`, §18 → `crypto-implementation-failures-key-management-and-agility`)
- [ ] ⚠️ **Rotation and compromise-recovery paths exist AND have been tested** (§18 → `crypto-implementation-failures-key-management-and-agility`)
- [ ] ⚠️ **Algorithms are versioned and replaceable** (§19 → `crypto-implementation-failures-key-management-and-agility`)
- [ ] ⚠️ **Cryptographic inventory exists for the PQC migration** (§19 → `crypto-implementation-failures-key-management-and-agility`, §23.1)
- [ ] ⚠️ **Certificate renewal automated via ACME** (§23.2)

---

## §28. Method

**§1–§22 → `crypto-what-it-solves-threat-models-randomness-hashes-and-macs`, `crypto-symmetric-aead-public-key-and-signatures`, `crypto-passwords-tls-pki-messaging-and-disk-encryption`, `crypto-implementation-failures-key-management-and-agility`, `crypto-advanced-constructions-blockchain-and-policy` rests on settled cryptography and long-established engineering practice** —
**the primitives, the AEAD recommendation, the failure-mode catalogue, and key management
discipline.** ⚠️ **None of it needed verification; nonce reuse has been catastrophic for
decades and Kerckhoffs published in 1883.**

**Two searches were run in August 2026**, on **post-quantum migration** and **TLS
certificate lifetimes** — ⚠️ **both chosen because they are §19 → `crypto-implementation-failures-key-management-and-agility`'s crypto-agility lesson
arriving as hard deadlines, and both change what you should be building today rather than
being interesting background.**

**Confidence.** **High** in §7 → `crypto-symmetric-aead-public-key-and-signatures`, §17 → `crypto-implementation-failures-key-management-and-agility` and §18 → `crypto-implementation-failures-key-management-and-agility`, which are the sections I'd most want read.
⚠️ **"Encryption without authentication is broken" is the single most actionable rule here,
and the malleability of unauthenticated ciphertext is the thing people who have only read
about "encryption" reliably don't know.** ⚠️ **§17 → `crypto-implementation-failures-key-management-and-agility`'s nonce reuse entry is the specific
failure I'd flag hardest — it is catastrophic, it is easy to do accidentally via counters
that reset, and in GCM it can expose the authentication key entirely.** **§18 → `crypto-implementation-failures-key-management-and-agility` is the honest
answer to where systems actually fail.**

**High** on §23.1's standards and dates, which trace to NIST's own publications and are
consistent across academic and industry sources: ⚠️ **FIPS 203/204/205 finalized August
2024, IR 8547's 2030 deprecation and 2035 disallowance, CNSA 2.0's algorithm selections, and
the key sizes.** ⚠️ **The June 2026 executive order and OMB memo details come via secondary
reporting rather than the primary documents and I've attributed them as such.** ⚠️ **The
point I'd most want carried is the AES-256 clarification — PQC migration is a public-key
problem, and the widespread belief that quantum computers break symmetric encryption is
simply wrong.** **⚠️ The SIKE/Rainbow breaks during evaluation are the honest reason hybrid
deployment is standard, and I've included them because the marketing around PQC rarely
mentions that two candidates fell mid-competition.**

**High** on §23.2's schedule, which comes from the ballot itself and is reported identically
across many CAs: ⚠️ **SC-081v3 passed 11 April 2025; 200 days from March 2026, 100 from
March 2027, 47 from March 2029, with DCV reuse falling to 10 days.**
⚠️ **The vote tally and the DigiCert 199-day detail are single-source and marked as
reported.** ⚠️ **Sourcing caution stated in-section: nearly all commentary here comes from
certificate authorities and certificate-lifecycle-management vendors who sell the automation
this creates demand for — which is why I've included the criticism that short expiry may be
substituting for fixing revocation, and that the beneficiaries voted for it.**
