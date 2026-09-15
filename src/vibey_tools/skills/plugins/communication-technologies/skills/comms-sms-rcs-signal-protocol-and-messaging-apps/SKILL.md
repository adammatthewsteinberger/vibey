---
name: comms-sms-rcs-signal-protocol-and-messaging-apps
description: "Use for messaging: SMS and why it is neither private nor reliable enough for authentication, MMS, RCS and its carrier and Universal Profile history, the Signal protocol with the double ratchet and forward secrecy, the messaging landscape and what each app actually encrypts, and iMessage and FaceTime including their key transparency and fallback behaviour."
---

# Communication Technologies: SMS, MMS, RCS, the Signal Protocol, the Messaging Landscape, and iMessage and FaceTime

> **Part 3 of 6** of the *Communication Technologies* reference (plugin `communication-technologies`), covering §13–§18. Sibling skills: `comms-email-smtp-authentication-and-deliverability` (§0–§7), `comms-telephony-pstn-ss7-voip-and-caller-id` (§8–§12), `comms-webrtc-video-conferencing-team-platforms-and-push` (§19–§22), `comms-encryption-metadata-interoperability-and-policy` (§23–§27), `comms-reference` (§28–§33). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The protocols are old and stable. Two things moved. See §28 → `comms-reference` for cross-platform encrypted RCS, and the legal status of message scanning.

> **⚠️ The most-used software category on earth, built on protocols mostly designed before
> the threats they now face existed.**
>
> **Builds on a cryptography reference (key exchange, forward secrecy, authentication), a
> wireless reference (cellular and Bluetooth layers), and a computer-hardware reference
> (networking). Complements a speaking-and-influence reference for the human side.**
>
> **⚠️ GOTCHA** boxes mark where the security or reliability property people assume is not
> the one the system actually provides.
>
> **The three ideas that organize this document:**
> 1. **⚠️ FEDERATED VERSUS PROPRIETARY IS THE DEEPEST DIVIDE** (§1 → `comms-email-smtp-authentication-and-deliverability`). **Email, SMS and the
>    phone network are federated — anyone can join, anyone can reach anyone, and nobody can
>    fix them unilaterally. Signal, iMessage and Slack are proprietary — coherent, secure,
>    improvable, and walled. Almost every frustration in this domain traces to that trade.**
> 2. **⚠️ "ENCRYPTED" IS FOUR DIFFERENT CLAIMS** (§23 → `comms-encryption-metadata-interoperability-and-policy`). **Transport encryption,
>    encryption at rest, end-to-end encryption, and end-to-end encryption with verified
>    keys are wildly different guarantees, and marketing conflates them constantly.**
> 3. **⚠️ METADATA IS USUALLY THE POINT** (§24 → `comms-encryption-metadata-interoperability-and-policy`). **Who talked to whom, when, how often and
>    from where survives content encryption — and for most surveillance purposes it is more
>    valuable than content. A system can be perfectly end-to-end encrypted and still
>    surveillable.**

---

## §13. ⚠️ SMS

```
⚠️ ⚠️ THE ORIGIN IS THE EXPLANATION  ⚠️ SMS was built into spare
   capacity in GSM's SIGNALLING channel. ⚠️ THAT is why messages
   are 160 characters — it was what fitted, not a design choice
   about human communication
⚠️ ENCODING  ⚠️ GSM 7-bit (160 chars) · 8-bit · ⚠️ UCS-2 for
   non-Latin scripts, which cuts the limit to 70
   ⚠️ THIS IS AN EQUITY ISSUE — the same message costs more
   segments in Arabic, Chinese or Hindi than in English
⚠️ CONCATENATION  longer messages are split with a header,
   reassembled on the handset, ⚠️ and billed per segment
⚠️ STORE AND FORWARD via the SMSC, ⚠️ with best-effort delivery
   and no guarantee of ordering or timeliness
⚠️ ⚠️ SMS IS NOT SECURE. ⚠️ Not end-to-end encrypted, visible to
   carriers, ⚠️ interceptable via SS7 (§9), and vulnerable to
   SIM SWAP at the account level
   ⚠️ ⚠️ THEREFORE SMS 2FA IS THE WEAKEST COMMON SECOND FACTOR —
   ⚠️ and it is still far better than no second factor, which is
   the nuance security advice often loses. ⚠️ NIST has
   discouraged it for years; app-based TOTP or hardware keys are
   materially stronger
⚠️ A2P messaging  ⚠️ the business channel, with registration
   regimes, sender IDs and per-country rules (see a wireless
   reference §13)
⚠️ ⚠️ WHY SMS PERSISTS DESPITE ALL THIS: ⚠️ universal reach.
   ⚠️ Every phone, every network, no app, no account, no
   internet connection. §1's trade, exactly
```

---

## §14. MMS

**⚠️ A different system wearing SMS's clothes**: ⚠️ **an SMS control message points the
handset at a WAP gateway, and the actual content is fetched over the data connection.**
**⚠️ This is why MMS needs mobile data**, ⚠️ **why it fails on Wi-Fi-only, and why it
behaves so differently across carriers.**
**⚠️ Aggressive recompression** is the notorious characteristic — ⚠️ **carriers shrink media
to fit size limits, which is the real reason cross-platform photos looked terrible for
years, and the specific problem RCS was meant to fix** (§15).
**⚠️ MMS is being retired** as RCS takes over, ⚠️ **though group messaging fallback keeps it
alive.**

---

## §15. ⚠️ RCS

```
⚠️ WHAT IT IS  ⚠️ the GSMA's IP-based successor to SMS/MMS —
   ⚠️ read receipts, typing indicators, high-quality media,
   proper group chats, and rich business messaging
⚠️ ⚠️ UNIVERSAL PROFILE is the interoperability specification,
   because the early years produced incompatible carrier
   implementations that could not talk to each other
⚠️ ⚠️ THE GOOGLE COMPLICATION  ⚠️ carrier rollout was so slow
   that Google effectively took over, running the Jibe backend
   for many operators and shipping Google Messages as the
   client. ⚠️ So a "carrier standard" is substantially operated
   by one company — ⚠️ which is §1's federated model quietly
   centralizing
⚠️ APPLE  ⚠️ adopted RCS in iOS 18 (2024), at Universal Profile
   2.4 — ⚠️ WITHOUT encryption, which is why cross-platform
   chats remained materially less protected than iMessage
   (§28.1 resolves this)
⚠️ ⚠️ THE PERSISTENT CONFUSION: "RCS IS ENCRYPTED" WAS HALF
   TRUE. ⚠️ Google Messages had PROPRIETARY E2EE between Google
   Messages users; the STANDARD had none, so anything
   cross-platform or cross-client was not end-to-end encrypted
   (§23, §28.1)
⚠️ ⚠️ BUSINESS MESSAGING (A2P) IS ARCHITECTURALLY DIFFERENT and
   remains so — ⚠️ transport-encrypted, not end-to-end, because
   carrier-side compliance filtering, spam detection and
   regulatory logging require readable content (§28.1)
```

---

## §16. ⚠️ The Signal Protocol

> **⚠️ The most consequential piece of applied cryptography in consumer software, and it is
> worth understanding because it underpins WhatsApp and others too.**
```
⚠️ ⚠️ X3DH (extended triple Diffie-Hellman)  ⚠️ ASYNCHRONOUS key
   agreement — ⚠️ you can establish a shared secret with someone
   who is OFFLINE, using prekeys they published in advance.
   ⚠️ This is the thing that made E2EE work for mobile messaging
   at all
⚠️ ⚠️ THE DOUBLE RATCHET  ⚠️ two ratchets combined
   ⚠️ A DH ratchet: new key material each time the conversation
      changes direction
   ⚠️ A symmetric ratchet: a new key for every single message
   ⚠️ ⚠️ FORWARD SECRECY  ⚠️ compromising today's key does not
      decrypt yesterday's messages
   ⚠️ ⚠️ POST-COMPROMISE SECURITY (self-healing) ⚠️ — the
      genuinely remarkable property: if an attacker steals your
      keys, the conversation RECOVERS security once a message
      is exchanged in each direction. ⚠️ Very few systems offer
      this
⚠️ SEALED SENDER hides the sender from the server — ⚠️ a real
   metadata reduction (§24), though not a complete one
⚠️ PQXDH  ⚠️ post-quantum key agreement added to X3DH — Signal
   shipped this ahead of most of the industry (see a
   cryptography reference §26)
⚠️ ⚠️ MLS (Messaging Layer Security, RFC 9420)  ⚠️ THE OTHER
   IMPORTANT PROTOCOL. ⚠️ Designed for EFFICIENT LARGE GROUPS —
   Signal's pairwise approach scales poorly past a few hundred —
   and for INTEROPERABILITY between different implementations.
   ⚠️ This is what RCS adopted (§28.1)
⚠️ ⚠️ THE HARD PART IS NOT THE CRYPTOGRAPHY, IT IS KEY
   VERIFICATION (§23). ⚠️ Safety numbers exist; almost nobody
   checks them
```

---

## §17. The Messaging Landscape

**⚠️ Signal** — ⚠️ **nonprofit foundation, open source, minimal metadata retention, and the
reference implementation for what good looks like.** ⚠️ **Requires a phone number, which is
a genuine and much-debated privacy limitation.**
**⚠️ WhatsApp** — ⚠️ **uses the Signal protocol for content, at enormous scale; ⚠️ the
questions concern metadata, Meta ownership, and cloud backups (⚠️ which are separately
encrypted only if you enable it).**
**⚠️ Telegram** — ⚠️ **⚠️ NOT end-to-end encrypted by default. Only "Secret Chats" are, and
they are one-to-one and device-bound. ⚠️ Its custom MTProto has drawn cryptographer
criticism.** ⚠️ **This is the single most widespread misconception in consumer messaging
security.**
**⚠️ Matrix** — ⚠️ **federated and open, with E2EE; ⚠️ the trade is complexity and a
metadata model that replicates room state across homeservers.**
**⚠️ The regional giants** — ⚠️ **WeChat, LINE, KakaoTalk, Viber — where the platform is
often the whole internet for its users, and the surveillance posture varies enormously by
jurisdiction.**

---

## §18. iMessage and FaceTime

**⚠️ End-to-end encrypted since launch**, ⚠️ **with device-specific keys and Apple
distributing the key directory — ⚠️ which is the trust assumption: Apple could in principle
add a device to your account, and Contact Key Verification exists to detect exactly that.**
**⚠️ PQ3** added post-quantum ratcheting, ⚠️ **making it one of the first large-scale
deployments** (see a cryptography reference).
**⚠️ The backup gotcha** (§23 → `comms-encryption-metadata-interoperability-and-policy`): ⚠️ **iCloud Backup historically included message keys, so
messages were recoverable by Apple — Advanced Data Protection changes this and is
opt-in.**
**⚠️ FaceTime** is E2EE peer-to-peer or via relays; ⚠️ **the blue/green bubble distinction is
a real security distinction and also a famously effective lock-in mechanism, which is a
large part of why RCS and §25 → `comms-encryption-metadata-interoperability-and-policy` exist.**

---

# PART IV — REAL-TIME AND COLLABORATION
