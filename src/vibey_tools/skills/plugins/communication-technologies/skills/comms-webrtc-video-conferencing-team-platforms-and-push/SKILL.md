---
name: comms-webrtc-video-conferencing-team-platforms-and-push
description: "Use for real-time and collaboration: WebRTC including ICE, STUN, TURN and the signalling you have to build yourself, video conferencing architecture across mesh, SFU and MCU topologies and the bandwidth and quality trade-offs, team platforms, and push and notification delivery and what the push infrastructure can see."
---

# Communication Technologies: WebRTC, Video Conferencing Architecture, Team Platforms, and Push and Notifications

> **Part 4 of 6** of the *Communication Technologies* reference (plugin `communication-technologies`), covering §19–§22. Sibling skills: `comms-email-smtp-authentication-and-deliverability` (§0–§7), `comms-telephony-pstn-ss7-voip-and-caller-id` (§8–§12), `comms-sms-rcs-signal-protocol-and-messaging-apps` (§13–§18), `comms-encryption-metadata-interoperability-and-policy` (§23–§27), `comms-reference` (§28–§33). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §19. ⚠️ WebRTC

**⚠️ Real-time audio, video and data in the browser with no plugin** — ⚠️ **and it is the
foundation of most modern conferencing, including products that do not advertise it.**
**⚠️ The pieces**: ⚠️ **getUserMedia for capture, RTCPeerConnection for transport,
RTCDataChannel for arbitrary data (⚠️ over SCTP, giving optionally-reliable
optionally-ordered delivery).**
**⚠️ Signalling is deliberately NOT specified** — ⚠️ **you bring your own, which is why every
WebRTC application needs a server before two browsers can talk.**
**⚠️ ICE, STUN and TURN** (§10 → `comms-telephony-pstn-ss7-voip-and-caller-id`) — ⚠️ **and TURN relaying is the expensive fallback that a
meaningful fraction of connections need.**
> **⚠️ GOTCHA — WebRTC leaks your local and public IP addresses to the page by design**,
> ⚠️ **because ICE candidate gathering requires it.** **⚠️ This has been used for
> de-anonymization and VPN leak detection, and browsers have added mitigations that are
> partial.**

**⚠️ SRTP with DTLS key exchange** means media is always encrypted in transit — ⚠️ **which
is not the same as end-to-end encrypted once an SFU is involved** (§20).

---

## §20. Video Conferencing Architecture

```
⚠️ THE THREE TOPOLOGIES, and the choice explains everything
   ⚠️ MESH  ⚠️ everyone sends to everyone. ⚠️ No server cost,
      and upstream bandwidth explodes past 3-4 participants
   ⚠️ ⚠️ SFU (Selective Forwarding Unit)  ⚠️ THE STANDARD ANSWER.
      Each client sends once; the server FORWARDS streams
      without decoding. ⚠️ Cheap server-side, and the client
      receives many streams
   ⚠️ MCU  ⚠️ the server decodes and composites into one stream.
      ⚠️ Expensive in CPU, and the only option for very weak
      clients
⚠️ SIMULCAST and SVC  ⚠️ send multiple qualities so the SFU can
   forward the appropriate one per receiver — ⚠️ this is what
   makes a gallery view of thirty people work at all
⚠️ ⚠️ THE E2EE PROBLEM  ⚠️ an SFU only forwards, so it CAN work
   with E2EE (insertable streams) — ⚠️ but any server-side
   feature that needs the content (recording, transcription,
   noise suppression, virtual backgrounds computed server-side)
   becomes impossible. ⚠️ THIS TENSION IS WHY MOST CONFERENCING
   IS NOT E2EE BY DEFAULT
   ⚠️ Zoom's 2020 "end-to-end encrypted" marketing was found to
   describe transport encryption, resulting in an FTC
   settlement — ⚠️ the canonical example of §23's confusion
   being commercially convenient
⚠️ THE ACTUAL QUALITY WORK  ⚠️ echo cancellation (⚠️ genuinely
   hard, and why headsets help), noise suppression, automatic
   gain, jitter buffering, loss concealment, bandwidth
   estimation and congestion control
```

---

## §21. Team Platforms

**⚠️ Slack** — ⚠️ **channel-based, strong integration model, and the search-and-history
product is arguably what people actually pay for.**
**⚠️ Microsoft Teams** — ⚠️ **wins on bundling rather than on product, and the deep
Office/Graph integration is the genuine differentiator.** ⚠️ **The EU competition case over
bundling with Office led to unbundling commitments.**
**⚠️ Discord** — ⚠️ **built for gaming latency, and its persistent-voice-channel model turns
out to suit communities better than meeting-based tools do.**
**⚠️ The common architecture**: ⚠️ **WebSocket for real-time, an event/message bus, presence
services, and search over history — with the hard engineering in fan-out at scale and in
notification routing** (§22).
> **⚠️ GOTCHA — none of these are end-to-end encrypted, and they generally cannot be.**
> ⚠️ **Search, compliance retention, eDiscovery, DLP and admin export all require the
> provider to read content — and enterprise buyers demand exactly those features.**
> **⚠️ Assume your employer can read anything in them, because that is a contractual product
> feature, not a flaw.**

---

## §22. Push and Notifications

**⚠️ Mobile push exists because battery does not permit persistent connections per app** —
⚠️ **so one OS-level channel multiplexes for everything.**
**⚠️ APNs and FCM** are that channel, ⚠️ **which means Apple and Google see notification
metadata for essentially every app — ⚠️ and government requests for push notification
records have been documented, which is a §24 → `comms-encryption-metadata-interoperability-and-policy` problem hiding in an engineering decision.**
**⚠️ E2EE apps handle this** by sending a content-free wake-up push and fetching the
message, ⚠️ **so the notification service learns that a message arrived but not what it
says.**
**⚠️ Web push** uses VAPID and encrypted payloads.
**⚠️ The design problem** is notification fatigue — ⚠️ **and the honest observation is that
platforms optimizing for engagement have an incentive that runs directly against the user's
interest here.**

---

# PART V — CROSS-CUTTING
