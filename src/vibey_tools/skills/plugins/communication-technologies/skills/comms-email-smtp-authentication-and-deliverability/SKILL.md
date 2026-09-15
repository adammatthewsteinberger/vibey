---
name: comms-email-smtp-authentication-and-deliverability
description: "Use for anything email: the federated versus proprietary divide that shapes the whole field, SMTP and email architecture, the retrieval protocols IMAP and POP, message format and MIME, SPF, DKIM and DMARC and how the three actually compose, deliverability and why legitimate mail lands in spam, and email encryption with S/MIME and PGP and why neither won. Includes the router for the whole communication technologies reference."
---

# Communication Technologies: The Federated / Proprietary Divide, SMTP and Email Architecture, Retrieval Protocols, Message Format, SPF, DKIM and DMARC, Deliverability, and Email Encryption

> **Part 1 of 6** of the *Communication Technologies* reference (plugin `communication-technologies`), covering §0–§7. Sibling skills: `comms-telephony-pstn-ss7-voip-and-caller-id` (§8–§12), `comms-sms-rcs-signal-protocol-and-messaging-apps` (§13–§18), `comms-webrtc-video-conferencing-team-platforms-and-push` (§19–§22), `comms-encryption-metadata-interoperability-and-policy` (§23–§27), `comms-reference` (§28–§33). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 1. **⚠️ FEDERATED VERSUS PROPRIETARY IS THE DEEPEST DIVIDE** (§1). **Email, SMS and the
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

## §0. Routing

| You want... | Go to |
|---|---|
| The federated/proprietary split | §1 |
| SMTP and email architecture | §2 |
| Retrieval protocols | §3 |
| Message format | §4 |
| **⚠️ SPF, DKIM, DMARC** | **§5** |
| **⚠️ Deliverability** | **§6** |
| Email encryption | §7 |
| PSTN | §8 → `comms-telephony-pstn-ss7-voip-and-caller-id` |
| **⚠️ SS7** | **§9 → `comms-telephony-pstn-ss7-voip-and-caller-id`** |
| VoIP and SIP | §10 → `comms-telephony-pstn-ss7-voip-and-caller-id` |
| VoLTE | §11 → `comms-telephony-pstn-ss7-voip-and-caller-id` |
| **⚠️ Caller ID and robocalls** | **§12 → `comms-telephony-pstn-ss7-voip-and-caller-id`** |
| **⚠️ SMS** | **§13 → `comms-sms-rcs-signal-protocol-and-messaging-apps`** |
| MMS | §14 → `comms-sms-rcs-signal-protocol-and-messaging-apps` |
| **⚠️ RCS** | **§15 → `comms-sms-rcs-signal-protocol-and-messaging-apps`** |
| **⚠️ The Signal protocol** | **§16 → `comms-sms-rcs-signal-protocol-and-messaging-apps`** |
| The messaging landscape | §17 → `comms-sms-rcs-signal-protocol-and-messaging-apps` |
| iMessage and FaceTime | §18 → `comms-sms-rcs-signal-protocol-and-messaging-apps` |
| **⚠️ WebRTC** | **§19 → `comms-webrtc-video-conferencing-team-platforms-and-push`** |
| Video conferencing | §20 → `comms-webrtc-video-conferencing-team-platforms-and-push` |
| Team platforms | §21 → `comms-webrtc-video-conferencing-team-platforms-and-push` |
| Push and notifications | §22 → `comms-webrtc-video-conferencing-team-platforms-and-push` |
| **⚠️ What E2EE protects** | **§23 → `comms-encryption-metadata-interoperability-and-policy`** |
| **⚠️ Metadata** | **§24 → `comms-encryption-metadata-interoperability-and-policy`** |
| Interoperability regulation | §25 → `comms-encryption-metadata-interoperability-and-policy` |
| **⚠️ The encryption debate** | **§26 → `comms-encryption-metadata-interoperability-and-policy`** |
| Emergency calling | §27 → `comms-encryption-metadata-interoperability-and-policy` |
| **What's live** | **§28 → `comms-reference`** |
| Misconceptions, numbers | §29–§30 → `comms-reference` |
| Sources, quick ref, method | §31–§33 → `comms-reference` |

---

## §1. The Federated / Proprietary Divide

```
⚠️ FEDERATED  ⚠️ email, SMS, the phone network, XMPP, Matrix
   ⚠️ ANYONE can participate · ⚠️ NOBODY can change it
   unilaterally · ⚠️ security is limited by the WEAKEST
   participant · ⚠️ evolution takes decades (§15, §28.1)
   ⚠️ AND THIS IS WHY EMAIL AND SMS ARE INSECURE — not
   incompetence, but the cost of universal reach
⚠️ PROPRIETARY  ⚠️ iMessage, Signal, WhatsApp, Slack, Discord
   ⚠️ Coherent security model · ⚠️ ships improvements in weeks ·
   ⚠️ walled garden · ⚠️ you depend on one company's continued
   existence and goodwill
⚠️ ⚠️ THE PATTERN THAT KEEPS REPEATING: a proprietary system
   demonstrates a capability, the federated standard adopts it
   years later, badly. ⚠️ RCS versus iMessage is the current
   instance and §28.1 is its resolution
⚠️ REGULATION IS NOW FORCING INTEROPERABILITY (§25) — ⚠️ an
   attempt to get federation's reach with proprietary security,
   and the jury is out
⚠️ ⚠️ THE HONEST TRADE  ⚠️ you cannot have universal reach,
   strong security, rapid evolution and no central authority
   simultaneously. ⚠️ Every system here picks three
```

---

# PART I — EMAIL

## §2. SMTP and Email Architecture

```
⚠️ THE COMPONENTS  ⚠️ MUA (your client) → MSA (submission) →
   MTA (transfer, possibly several) → MDA (delivery) → mailbox
⚠️ SMTP  ⚠️ from 1982, text-based, store-and-forward.
   ⚠️ Ports: 25 (MTA-to-MTA), 587 (⚠️ submission, authenticated),
   465 (implicit TLS)
⚠️ ⚠️ THE ENVELOPE IS NOT THE HEADER. ⚠️ MAIL FROM and RCPT TO
   are the SMTP envelope; the From: and To: you SEE are message
   headers. ⚠️ THEY NEED NOT MATCH — and that gap is the
   entire basis of email spoofing (§5)
⚠️ MX RECORDS in DNS route mail for a domain
⚠️ STARTTLS  ⚠️ opportunistic encryption — ⚠️ and "opportunistic"
   means STRIPPABLE by an active attacker unless MTA-STS or
   DANE is in place, which most domains lack
⚠️ ⚠️ SMTP HAD NO AUTHENTICATION AT ALL BY DESIGN. ⚠️ Everything
   in §5 is bolted on decades later, which is why it is a
   layered mess of DNS records rather than a protocol feature
⚠️ BOUNCES  ⚠️ hard vs soft · ⚠️ BACKSCATTER (bounces sent to a
   forged sender) is a consequence of accepting-then-bouncing
```

---

## §3. Retrieval Protocols

**⚠️ POP3** downloads and traditionally deletes — ⚠️ **a single-device model that predates
people having several.**
**⚠️ IMAP** keeps mail on the server with folders, flags and server-side search —
⚠️ **the model that matches how people actually use email, and it is complex enough that
implementations differ in maddening ways.**
**⚠️ JMAP** is the modern replacement: ⚠️ **JSON over HTTP, designed for mobile with
efficient synchronization and push, and it is genuinely better — with the usual federated
adoption problem** (§1).
**⚠️ Exchange/ActiveSync and Gmail's API** are the proprietary equivalents, ⚠️ **and the
calendar and contacts integration is a large part of why organizations stay on them.**
**⚠️ The practical consequence for users**: ⚠️ **IMAP means your mail lives on a server
someone else controls, which is the assumption §7 has to work around.**

---

## §4. Message Format

**⚠️ RFC 5322** defines headers and body; ⚠️ **MIME extends it to attachments, multiple
character sets and multipart bodies — because the original format was US-ASCII text only.**
**⚠️ Multipart/alternative** carries plain text and HTML versions of the same message,
⚠️ **and HTML email is where tracking pixels, remote-image beacons and rendering
inconsistency all live.**
**⚠️ Base64 and quoted-printable** encode binary into the 7-bit-safe channel SMTP assumes —
⚠️ **which is why attachments inflate roughly a third in transit.**
**⚠️ Message-ID, In-Reply-To and References** are what make threading work, ⚠️ **and clients
that ignore them produce the broken threads everyone recognizes.**
**⚠️ Internationalized email (EAI/SMTPUTF8)** allows non-ASCII addresses, ⚠️ **and support
remains patchy — a real equity issue for non-Latin-script users.**

---

## §5. ⚠️ SPF, DKIM, DMARC

> **⚠️ The three-layer patch over §2's missing authentication, and understanding what each
> actually checks is what makes email security legible.**
```
⚠️ ⚠️ SPF  ⚠️ a DNS record listing which IPs may send for a
   domain. ⚠️ CHECKS THE ENVELOPE SENDER (MAIL FROM), NOT the
   visible From: header
   ⚠️ THEREFORE SPF ALONE DOES NOT STOP SPOOFING of what the
   user sees. ⚠️ It also BREAKS ON FORWARDING, because the
   forwarder's IP is not in the original domain's record
⚠️ ⚠️ DKIM  ⚠️ a cryptographic SIGNATURE over selected headers
   and the body, with the public key in DNS.
   ⚠️ SURVIVES FORWARDING (as long as nothing modifies the
   signed parts) · ⚠️ BREAKS when a mailing list appends a
   footer or rewrites a subject
⚠️ ⚠️ DMARC  ⚠️ THE ONE THAT MATTERS. ⚠️ Requires SPF or DKIM to
   pass AND to be ALIGNED with the visible From: domain, and
   publishes a POLICY: none, quarantine, or reject
   ⚠️ Plus aggregate and forensic REPORTING, which is how you
   discover who is sending as you
⚠️ ⚠️ THE ALIGNMENT REQUIREMENT IS THE WHOLE POINT — it closes
   the envelope-versus-header gap of §2
⚠️ ARC  ⚠️ preserves authentication results across intermediaries
   (mailing lists, forwarders) so DMARC does not destroy them
⚠️ BIMI  displays a verified logo; ⚠️ requires DMARC enforcement
   and usually a paid mark certificate — ⚠️ arguably a
   compliance incentive dressed as a feature
⚠️ ⚠️ THE ROLLOUT TRAP  ⚠️ going straight to p=reject without
   reading reports first WILL silently drop legitimate mail from
   systems you forgot about — the ticketing system, the payroll
   provider, the marketing tool
```

---

## §6. ⚠️ Deliverability

**⚠️ Getting mail accepted is a different problem from sending it**, ⚠️ **and it is
governed by reputation rather than by rules.**
**⚠️ What actually determines it**: ⚠️ **sending IP and domain reputation, authentication
(§5), ⚠️ ENGAGEMENT SIGNALS (opens, replies, and especially deletions-without-reading),
complaint rate, spam-trap hits, list hygiene, and consistency of volume.**
> **⚠️ GOTCHA — complaint rate is the metric that kills you, and the thresholds are
> brutally low.** ⚠️ **Major providers publish complaint-rate targets in the region of a
> tenth of a percent — meaning a handful of "report spam" clicks per thousand messages is
> enough to damage a sending reputation.** **⚠️ One easy unsubscribe link prevents more
> deliverability damage than any amount of content tuning.**

**⚠️ Bulk sender requirements** now enforced by the large providers require ⚠️ **SPF, DKIM,
DMARC, one-click unsubscribe and complaint-rate limits — which formalized what was
previously informal.**
**⚠️ Shared versus dedicated IPs, warming, and subdomain separation** (⚠️ **transactional
mail on a different subdomain from marketing, so a bad campaign cannot take down your
password resets**).
**⚠️ The uncomfortable structural point**: ⚠️ **a handful of providers effectively decide
whose email is delivered, with no appeal — which is centralization arriving at a federated
system through the back door** (§1).

---

## §7. Email Encryption

**⚠️ Transport encryption (§2) protects the hop, not the message**, ⚠️ **and the provider
reads everything.**
**⚠️ PGP/GPG** — ⚠️ **decentralized web of trust, no forward secrecy, and famously unusable
for non-experts; ⚠️ the EFAIL research showed real vulnerabilities in how clients handled
it.**
**⚠️ S/MIME** — ⚠️ **certificate-authority based, better organizational tooling, and
therefore common in enterprise and government and rare elsewhere.**
> **⚠️ GOTCHA — neither encrypts the SUBJECT LINE or the metadata** (§24 → `comms-encryption-metadata-interoperability-and-policy`). ⚠️ **Who you
> emailed, when, and about what (per the subject) remains visible even with the body
> encrypted.**

**⚠️ Provider-based approaches** (Proton, Tutanota) ⚠️ **encrypt within their own systems and
fall back to links or plain mail outside — which is §1's trade in miniature.**
**⚠️ The honest assessment**: ⚠️ **email encryption has failed to achieve meaningful
adoption in thirty years, and if you need confidential messaging the practical answer is to
use something else** (§16 → `comms-sms-rcs-signal-protocol-and-messaging-apps`, §17 → `comms-sms-rcs-signal-protocol-and-messaging-apps`).

---

# PART II — TELEPHONY
