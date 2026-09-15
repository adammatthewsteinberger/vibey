---
name: comms-reference
description: "Use when correcting a communications misconception, looking up a protocol port, latency, codec, deliverability or adoption figure, finding the sources, or needing a quick-reference picker — plus the current state of cross-platform encrypted RCS and the legal status of message scanning. Companion to the other communication technologies skills."
---

# Communication Technologies: What's Live, Misconceptions, Numbers and Dates, and Sources

> **Part 6 of 6** of the *Communication Technologies* reference (plugin `communication-technologies`), covering §28–§33. Sibling skills: `comms-email-smtp-authentication-and-deliverability` (§0–§7), `comms-telephony-pstn-ss7-voip-and-caller-id` (§8–§12), `comms-sms-rcs-signal-protocol-and-messaging-apps` (§13–§18), `comms-webrtc-video-conferencing-team-platforms-and-push` (§19–§22), `comms-encryption-metadata-interoperability-and-policy` (§23–§27). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The protocols are old and stable. Two things moved. See §28 for cross-platform encrypted RCS, and the legal status of message scanning.

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

## §28. What's Live — checked August 2026

### 28.1 ⚠️ Cross-platform encrypted RCS finally shipped
**⚠️ §15 → `comms-sms-rcs-signal-protocol-and-messaging-apps`'s gap closing, and §1 → `comms-email-smtp-authentication-and-deliverability`'s federated-versus-proprietary trade playing out over eight
years.**

- **⚠️ WHAT HAPPENED.** ⚠️ **The GSMA published RCS Universal Profile 3.0 in March 2025, the
  first version to formally define end-to-end encryption for person-to-person RCS, using
  MLS** (§16 → `comms-sms-rcs-signal-protocol-and-messaging-apps`). ⚠️ **The GSMA's technical director framed it as making RCS the first
  large-scale messaging service to support interoperable E2EE between client
  implementations from different providers.**
- **⚠️ IT WENT LIVE 11 MAY 2026**, ⚠️ **in beta with iOS 26.5 and current Google Messages —
  the first time iPhone-to-Android messages could be end-to-end encrypted.** ⚠️ **Encryption
  is on by default where supported, with a lock icon indicating coverage.**
- **⚠️ THE EFF called it a victory**, noting ⚠️ **neither Google, Apple, nor the cellular
  carriers have access to message contents.**
- **⚠️ THE STANDARDIZATION LAG IS THE STORY.** ⚠️ **UP 3.0 was specified in March 2025 and
  took roughly a year to reach a first beta — and one industry commentary notes the GSMA
  had already reached UP 5.0 by then.** ⚠️ **That is §1 → `comms-email-smtp-authentication-and-deliverability`'s federated cost, measured.**

> **⚠️ GOTCHA — three separate caveats, and coverage tends to state only the headline.**
> ⚠️ **FIRST, CARRIER SUPPORT IS REQUIRED ON BOTH ENDS.** ⚠️ **Apple has shipped its side,
> but whether a given conversation is actually encrypted depends on network infrastructure
> Apple neither controls nor publishes a support list for.**
> ⚠️ **SECOND, BUSINESS MESSAGING IS EXCLUDED AND WILL STAY EXCLUDED.** ⚠️ **A2P RCS uses
> transport-layer security, not MLS — and this is architectural rather than an oversight:
> carrier-side compliance filtering, spam detection and regulatory logging require readable
> content** (§15 → `comms-sms-rcs-signal-protocol-and-messaging-apps`, §21 → `comms-webrtc-video-conferencing-team-platforms-and-push`'s same tension).
> ⚠️ **THIRD, METADATA AND BACKUPS REMAIN.** ⚠️ **The EFF's own assessment notes metadata is
> likely still collected, and cloud backups may store conversations unencrypted unless
> Advanced Data Protection is enabled — with Google Messages reportedly encrypting message
> text but not media in backups.** **⚠️ This is §23 → `comms-encryption-metadata-interoperability-and-policy`'s list, arriving on schedule.**

**⚠️ The honest summary**: ⚠️ **a real and large improvement for personal messaging between
platforms, achieved through standardization rather than regulation (§25 → `comms-encryption-metadata-interoperability-and-policy`) — and Signal
remains the stronger choice where metadata matters, which the EFF says explicitly.**

### 28.2 ⚠️ The legal status of message scanning
**⚠️ §26 → `comms-encryption-metadata-interoperability-and-policy`'s debate moving from principle to statute — and the 2026 position is genuinely
tangled.**

- **⚠️ TWO DIFFERENT THINGS SHARE THE NICKNAME, and conflating them is the main source of
  confusion.**
  ⚠️ **"CHAT CONTROL 1.0" is Regulation (EU) 2021/1232 — a temporary derogation from
  ePrivacy PERMITTING (not requiring) providers to voluntarily scan for CSAM. It applies to
  unencrypted services.**
  ⚠️ **"CHAT CONTROL 2.0" is the permanent CSA Regulation proposed in May 2022, which is
  where mandatory detection and client-side scanning have been debated.**
- **⚠️ THE 2026 SEQUENCE ON 1.0.** ⚠️ **Parliament rejected a further extension in March
  2026 and the derogation lapsed on 4 April 2026.** ⚠️ **On 9 July 2026 it was reinstated
  via a fast-tracked Council text, in force until 2028.**
- ⚠️ **The vote mechanics are worth stating precisely, because the headline "Parliament
  passed it" is misleading: 314 MEPs voted to reject and 276 in favour with 17 abstentions,
  but rejection required an ABSOLUTE MAJORITY of 361 — so it passed despite a majority of
  those voting opposing it.** ⚠️ **Reporting indicates an exemption for end-to-end encrypted
  services was adopted.**
- ⚠️ **Notably, Google, Meta, Microsoft and Snap reportedly continued scanning during the
  April–July gap when no legal basis existed.**
- **⚠️ ON 2.0, the permanent regulation**: ⚠️ **the Council dropped the original mandatory
  client-side scanning requirement but retained a permanent voluntary framework,
  age-verification obligations extending to encrypted services, broad risk-mitigation
  obligations, and detection orders for known CSAM via hash-matching on unencrypted
  platforms.** ⚠️ **Trilogue negotiations began December 2025 and the file returns in
  September 2026.**

> **⚠️ GOTCHA — the technical point is independent of the politics and worth stating
> plainly.** ⚠️ **Client-side scanning does not break end-to-end encryption; it inspects
> content on the device BEFORE encryption is applied.** **⚠️ As the Max Planck Society puts
> it, the encryption remains in place but is fundamentally circumvented.**
> ⚠️ **The corresponding point about email is also worth knowing: most email is NOT
> end-to-end encrypted (§7 → `comms-email-smtp-authentication-and-deliverability`), so providers can and already do scan it server-side — which is
> why the debate is specifically about messaging.**
> **⚠️ The industry objection to "voluntary" framings is that risk-mitigation obligations
> can become regulatory pressure to scan, and that a detection-order precedent against E2EE
> services could later be expanded without new primary legislation.**

**⚠️ Elsewhere**: ⚠️ **the UK Online Safety Act gives Ofcom powers that reporting describes
as demanding scanning no encrypted service can satisfy while remaining encrypted — and the
observed provider response has been to WITHDRAW FEATURES from the UK rather than weaken them
globally, which is itself evidence about whether "compliant but still encrypted" is
achievable.**
**⚠️ Sourcing warning, and it is significant.** ⚠️ **Much of the available coverage comes
from campaigning organizations on one side and is written accordingly; the Max Planck
Society and Euronews are the closest to neutral among my sources, and the vote arithmetic is
consistently reported across otherwise-opposed outlets.** ⚠️ **I have described mechanisms
and positions rather than taking one — the technical statement that CSS circumvents rather
than breaks E2EE is a factual claim, not a political one, and both sides accept it.**

---

## §29. Misconceptions

| Misconception | Correction |
|---|---|
| Email From: is verified | ⚠️ **Envelope and header differ. That gap IS spoofing** (§2 → `comms-email-smtp-authentication-and-deliverability`, §5 → `comms-email-smtp-authentication-and-deliverability`) |
| SPF stops spoofing | ⚠️ **It checks the envelope, not what you see. DMARC aligns them** (§5 → `comms-email-smtp-authentication-and-deliverability`) |
| STARTTLS secures email | ⚠️ **Opportunistic and strippable without MTA-STS/DANE** (§2 → `comms-email-smtp-authentication-and-deliverability`) |
| Set DMARC to p=reject immediately | ⚠️ **Read reports first or you'll drop real mail** (§5 → `comms-email-smtp-authentication-and-deliverability`) |
| Deliverability is about content | ⚠️ **Reputation, engagement, complaint rate** (§6 → `comms-email-smtp-authentication-and-deliverability`) |
| PGP encrypts your email | ⚠️ **Not the subject line, not the metadata** (§7 → `comms-email-smtp-authentication-and-deliverability`) |
| SS7 is a legacy curiosity | ⚠️ **Still routes roaming and SMS. No authentication** (§9 → `comms-telephony-pstn-ss7-voip-and-caller-id`) |
| Caller ID shows who's calling | ⚠️ **Asserted by the originator. Trivially forged** (§12 → `comms-telephony-pstn-ss7-voip-and-caller-id`) |
| STIR/SHAKEN proves a call is legitimate | ⚠️ **It attests a carrier's claim about the number** (§12 → `comms-telephony-pstn-ss7-voip-and-caller-id`) |
| 160 characters was a design decision | ⚠️ **It's what fitted in spare signalling capacity** (§13 → `comms-sms-rcs-signal-protocol-and-messaging-apps`) |
| SMS 2FA is fine | ⚠️ **Weakest common factor — SS7, SIM swap. Still beats none** (§9 → `comms-telephony-pstn-ss7-voip-and-caller-id`, §13 → `comms-sms-rcs-signal-protocol-and-messaging-apps`) |
| Non-Latin SMS costs the same | ⚠️ **UCS-2 cuts the limit to 70 chars per segment** (§13 → `comms-sms-rcs-signal-protocol-and-messaging-apps`) |
| MMS is SMS with pictures | ⚠️ **Different system — needs mobile data, recompresses hard** (§14 → `comms-sms-rcs-signal-protocol-and-messaging-apps`) |
| RCS is a carrier standard | ⚠️ **Substantially operated by Google via Jibe** (§15 → `comms-sms-rcs-signal-protocol-and-messaging-apps`) |
| RCS was already encrypted | ⚠️ **Google-to-Google only. The standard had none until UP 3.0** (§15 → `comms-sms-rcs-signal-protocol-and-messaging-apps`, §28.1) |
| Telegram is an encrypted messenger | ⚠️ **NOT E2EE by default. Only Secret Chats** (§17 → `comms-sms-rcs-signal-protocol-and-messaging-apps`) |
| WhatsApp backups are encrypted | ⚠️ **Only if you enable it** (§17 → `comms-sms-rcs-signal-protocol-and-messaging-apps`, §23 → `comms-encryption-metadata-interoperability-and-policy`) |
| E2EE protects your conversation | ⚠️ **Not endpoints, backups, metadata or the other party** (§23 → `comms-encryption-metadata-interoperability-and-policy`) |
| Zoom was end-to-end encrypted | ⚠️ **The 2020 claim described transport encryption. FTC settlement** (§20 → `comms-webrtc-video-conferencing-team-platforms-and-push`) |
| Conferencing could easily be E2EE | ⚠️ **Recording, transcription and effects need the content** (§20 → `comms-webrtc-video-conferencing-team-platforms-and-push`) |
| Slack and Teams are private | ⚠️ **Search, retention and eDiscovery require readable content** (§21 → `comms-webrtc-video-conferencing-team-platforms-and-push`) |
| Push notifications are private | ⚠️ **APNs/FCM see the metadata for every app** (§22 → `comms-webrtc-video-conferencing-team-platforms-and-push`) |
| Metadata is less sensitive | ⚠️ **Often more revealing, and usually less legally protected** (§24 → `comms-encryption-metadata-interoperability-and-policy`) |
| Interop mandates improve security | ⚠️ **Bridging can mean the weakest party sets the level** (§25 → `comms-encryption-metadata-interoperability-and-policy`) |
| Client-side scanning breaks encryption | ⚠️ **It circumvents it — reads before the envelope closes** (§26 → `comms-encryption-metadata-interoperability-and-policy`, §28.2) |
| VoIP phones work in a blackout | ⚠️ **Copper powered the handset. IP doesn't** (§27 → `comms-encryption-metadata-interoperability-and-policy`) |
| Encrypted RCS works everywhere now | ⚠️ **Both carriers must support UP 3.0** (§28.1) |
| The EU banned/mandated scanning | ⚠️ **Two separate files. Check which is meant** (§28.2) |

---

## §30. Numbers and Dates

```
⚠️ SMTP  RFC 821 (1982) · ports 25 / 587 / 465
⚠️ SMS  ⚠️ 160 chars GSM-7 · ⚠️ 70 chars UCS-2
⚠️ PSTN voice  ⚠️ 8 kHz, 8-bit companded = 64 kbit/s · 300-3400 Hz
⚠️ VoIP one-way latency  ⚠️ interactivity degrades above ~150 ms
⚠️ Complaint rate threshold  ⚠️ order of 0.1% (bulk sender rules)
⚠️ STIR/SHAKEN attestation  ⚠️ A (full) · B (partial) · C (gateway)
⚠️ SFU  ⚠️ forwards without decoding — the standard topology
⚠️ MLS  ⚠️ RFC 9420 — designed for large groups AND interop
⚠️ ⚠️ RCS UP 3.0 published  ⚠️ March 2025 (GSMA)
⚠️ ⚠️ Cross-platform E2EE RCS live  ⚠️ 11 May 2026, iOS 26.5 beta
⚠️ Standardization lag  ⚠️ ~1 year spec → first beta; GSMA at UP 5.0
⚠️ ⚠️ Chat Control 1.0  ⚠️ Reg (EU) 2021/1232 — VOLUNTARY,
   unencrypted services · lapsed 4 Apr 2026 ·
   ⚠️ reinstated 9 Jul 2026, in force to 2028
⚠️ ⚠️ The 9 July vote  ⚠️ 314 to reject, 276 for, 17 abstain —
   ⚠️ needed 361 (absolute majority) to reject
⚠️ CSA Regulation (2.0)  ⚠️ proposed May 2022 · trilogue from
   Dec 2025 · ⚠️ returns September 2026
```

---

## §31. Sources

| Source | Why |
|---|---|
| **RFCs — 5321/5322 (email), 3261 (SIP), 9420 (MLS)** | ⚠️ **Primary, free, authoritative** |
| **M3AAWG best practice documents** | ⚠️ **§5–§6 → `comms-email-smtp-authentication-and-deliverability`, the operational reality of email** |
| **Signal protocol documentation and specifications** | ⚠️ **§16 → `comms-sms-rcs-signal-protocol-and-messaging-apps` — unusually well documented** |
| **GSMA RCS Universal Profile specifications** | ⚠️ **§15 → `comms-sms-rcs-signal-protocol-and-messaging-apps`, §28.1, primary** |
| **EFF Deeplinks and Surveillance Self-Defense** | ⚠️ **§23–§26 → `comms-encryption-metadata-interoperability-and-policy` — advocacy, but technically careful** |
| **webrtcforthecurious.com** | ⚠️ **§19 → `comms-webrtc-video-conferencing-team-platforms-and-push`, free and excellent** |
| **Rosenberg/Johnston on SIP; *WebRTC* (Loreto & Romano)** | §10 → `comms-telephony-pstn-ss7-voip-and-caller-id`, §19 → `comms-webrtc-video-conferencing-team-platforms-and-push` |
| **Karsten Nohl's SS7 research** | ⚠️ **§9 → `comms-telephony-pstn-ss7-voip-and-caller-id` — the work that made it public** |
| **NIST SP 800-63B on authenticators** | ⚠️ **§13 → `comms-sms-rcs-signal-protocol-and-messaging-apps`, on SMS as a factor** |
| **"Bugs in our Pockets" (Abelson, Anderson, Rivest et al.)** | ⚠️ **§26 → `comms-encryption-metadata-interoperability-and-policy` — the technical case against CSS** |
| **Euronews, Max Planck Society on Chat Control** | ⚠️ **§28.2 — nearest to neutral available** |

---

## §32. Quick Reference

### 32.1 Picker
| Question | Where |
|---|---|
| Why does my mail go to spam? | ⚠️ **Authentication, then reputation and complaints** (§5 → `comms-email-smtp-authentication-and-deliverability`, §6 → `comms-email-smtp-authentication-and-deliverability`) |
| Someone is spoofing my domain | ⚠️ **DMARC with reporting. Read before enforcing** (§5 → `comms-email-smtp-authentication-and-deliverability`) |
| Is this messenger actually secure? | ⚠️ **Ask the new-device test** (§23 → `comms-encryption-metadata-interoperability-and-policy`) |
| Is SMS 2FA good enough? | ⚠️ **Better than nothing, worse than TOTP or a key** (§13 → `comms-sms-rcs-signal-protocol-and-messaging-apps`) |
| Why do spam calls look local? | ⚠️ **Neighbour spoofing. Caller ID isn't authenticated** (§12 → `comms-telephony-pstn-ss7-voip-and-caller-id`) |
| Why is my video call bad? | ⚠️ **Latency, jitter, loss — and echo means get a headset** (§10 → `comms-telephony-pstn-ss7-voip-and-caller-id`, §20 → `comms-webrtc-video-conferencing-team-platforms-and-push`) |
| Can my employer read my Slack? | ⚠️ **Yes. It's a product feature** (§21 → `comms-webrtc-video-conferencing-team-platforms-and-push`) |
| Is my group chat end-to-end encrypted? | ⚠️ **Check the platform, and check backups separately** (§23 → `comms-encryption-metadata-interoperability-and-policy`) |
| Does encryption hide who I talk to? | ⚠️ **No. Metadata survives** (§24 → `comms-encryption-metadata-interoperability-and-policy`) |
| Is iPhone-to-Android encrypted now? | ⚠️ **If both carriers support UP 3.0** (§28.1) |
| Are business RCS messages encrypted? | ⚠️ **Transport only, and by design** (§15 → `comms-sms-rcs-signal-protocol-and-messaging-apps`, §28.1) |
| Will my phone work in a power cut? | ⚠️ **Not on all-IP without battery backup** (§27 → `comms-encryption-metadata-interoperability-and-policy`) |

### 32.2 Choosing a channel
- [ ] ⚠️ **What must be confidential — content, or the fact of contact?** (§23 → `comms-encryption-metadata-interoperability-and-policy`, §24 → `comms-encryption-metadata-interoperability-and-policy`)
- [ ] ⚠️ **Who must be able to reach you? Reach vs security is the trade** (§1 → `comms-email-smtp-authentication-and-deliverability`)
- [ ] ⚠️ **Are backups covered, or is the archive the weak point?** (§23 → `comms-encryption-metadata-interoperability-and-policy`)
- [ ] Is the other party's endpoint trustworthy? (§23 → `comms-encryption-metadata-interoperability-and-policy`)
- [ ] ⚠️ **Does the org need search, retention or eDiscovery? Then not E2EE** (§21 → `comms-webrtc-video-conferencing-team-platforms-and-push`)
- [ ] Does it need to work with no internet or no app? (§13 → `comms-sms-rcs-signal-protocol-and-messaging-apps`)
- [ ] ⚠️ **Emergency and accessibility requirements met?** (§27 → `comms-encryption-metadata-interoperability-and-policy`)
- [ ] **If sending bulk email, additionally:**
- [ ] ⚠️ **SPF, DKIM and DMARC aligned; reports monitored** (§5 → `comms-email-smtp-authentication-and-deliverability`)
- [ ] ⚠️ **One-click unsubscribe, and complaint rate watched** (§6 → `comms-email-smtp-authentication-and-deliverability`)
- [ ] Transactional separated from marketing by subdomain (§6 → `comms-email-smtp-authentication-and-deliverability`)

---

## §33. Method

**§1–§27 → `comms-email-smtp-authentication-and-deliverability`, `comms-telephony-pstn-ss7-voip-and-caller-id`, `comms-sms-rcs-signal-protocol-and-messaging-apps`, `comms-webrtc-video-conferencing-team-platforms-and-push`, `comms-encryption-metadata-interoperability-and-policy` rests on published protocols and long-documented practice** — **SMTP, SIP, the
Signal protocol, MLS, SFU architecture, the SS7 vulnerability literature, and the four-way
distinction in what "encrypted" means.** ⚠️ **None needed verification; RFC 821 is from 1982
and the Signal double ratchet has been publicly specified and independently analyzed for a
decade.**

**Two searches were run in August 2026**, on **encrypted RCS** and **message-scanning law**
— ⚠️ **the first because §15 → `comms-sms-rcs-signal-protocol-and-messaging-apps`'s gap was the largest open hole in mainstream messaging
security and it just closed, the second because §26 → `comms-encryption-metadata-interoperability-and-policy`'s debate has moved from principle into
statute and the current position is widely misreported in both directions.**

**Confidence.** **High** in §23 → `comms-encryption-metadata-interoperability-and-policy` and §1 → `comms-email-smtp-authentication-and-deliverability`, which are the sections I'd most want read.
⚠️ **The four-way distinction between transport encryption, encryption at rest, E2EE and
E2EE-with-verified-keys is the thing that makes marketing claims readable — and the
practical test is worth memorizing: if a provider can show you old messages on a new device
with only a password, it is not end-to-end encrypted.**
⚠️ **§1 → `comms-email-smtp-authentication-and-deliverability`'s federated-versus-proprietary trade is the frame that explains why email and SMS
are insecure and why fixing them takes decades: it is the price of universal reach, not
incompetence.** **⚠️ §24 → `comms-encryption-metadata-interoperability-and-policy`'s point that metadata is often more revealing and less legally
protected than content is the one most people have not internalized.**

**High** on §28.1, anchored on the GSMA's own specification announcement and the EFF's
assessment: ⚠️ **UP 3.0 published March 2025 defining MLS-based E2EE, cross-platform
encrypted RCS live 11 May 2026 in beta.** ⚠️ **The three caveats are the part worth
carrying — carrier support required on both ends, business messaging excluded
architecturally, and metadata and backups untouched — because coverage reliably states the
headline and omits them.**

**Moderate** on §28.2, and deliberately careful. ⚠️ **The vote arithmetic on 9 July 2026 —
314 to reject against a required absolute majority of 361 — is consistently reported across
outlets with opposed editorial positions, which is why I state it precisely: describing this
as "Parliament passed it" is technically true and substantively misleading.**
⚠️ **Much of the available coverage is from campaigning organizations, and I have leaned on
Euronews and the Max Planck Society where possible and flagged the rest.**
**⚠️ I have described mechanisms and positions rather than adopting one.** ⚠️ **The single
technical claim I state flatly — that client-side scanning circumvents rather than breaks
end-to-end encryption — is accepted by advocates on both sides and is the distinction that
makes the rest of the argument legible.**
