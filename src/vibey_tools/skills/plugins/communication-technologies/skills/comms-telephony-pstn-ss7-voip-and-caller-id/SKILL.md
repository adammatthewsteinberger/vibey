---
name: comms-telephony-pstn-ss7-voip-and-caller-id
description: "Use for voice: the PSTN and circuit switching, SS7 and the signalling trust model that makes location tracking and SMS interception possible, VoIP and SIP with NAT traversal and codecs, VoLTE and VoNR carrying voice over IP in mobile networks, and caller ID, spoofing, robocalls and the STIR/SHAKEN attestation scheme with its real limits."
---

# Communication Technologies: The PSTN, SS7 and Its Security Problem, VoIP and SIP, VoLTE and VoNR, and Caller ID, Spoofing and Robocalls

> **Part 2 of 6** of the *Communication Technologies* reference (plugin `communication-technologies`), covering §8–§12. Sibling skills: `comms-email-smtp-authentication-and-deliverability` (§0–§7), `comms-sms-rcs-signal-protocol-and-messaging-apps` (§13–§18), `comms-webrtc-video-conferencing-team-platforms-and-push` (§19–§22), `comms-encryption-metadata-interoperability-and-policy` (§23–§27), `comms-reference` (§28–§33). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §8. The PSTN

**⚠️ Circuit switching** dedicated a path for the call's duration — ⚠️ **which guaranteed
quality and wasted capacity, and is the opposite of packet switching's trade.**
**⚠️ The hierarchy**: ⚠️ **local loop, central office/exchange, tandem and toll switches,
with E.164 numbering as the global address space.**
**⚠️ Digital voice**: ⚠️ **8 kHz sampling, 8-bit companded (μ-law/A-law) = 64 kbit/s, which
is the DS0 that the whole T1/E1 hierarchy is built from.** ⚠️ **This is why traditional
phone audio sounds the way it does — 300–3400 Hz, a deliberate 1930s bandwidth choice.**
**⚠️ Signalling**: ⚠️ **in-band originally (⚠️ which is what phone phreaking exploited),
then out-of-band via SS7** (§9).
**⚠️ The PSTN is being switched off** — ⚠️ **copper retirement and all-IP migration are
underway in most developed markets, with real consequences for alarms, lifts, medical
pendants and payment terminals that assumed a powered analogue line.**

---

## §9. ⚠️ SS7 and Its Security Problem

```
⚠️ WHAT IT IS  ⚠️ the out-of-band signalling network that sets up
   calls, routes SMS, handles roaming and queries subscriber
   location. ⚠️ Designed in the 1970s-80s
⚠️ ⚠️ THE DESIGN ASSUMPTION WAS A CLOSED CLUB OF TRUSTED STATE
   MONOPOLY CARRIERS. ⚠️ There is essentially NO AUTHENTICATION
   between network elements
⚠️ ⚠️ WHEN DEREGULATION AND ROAMING OPENED IT UP, that
   assumption failed — ⚠️ and access can be obtained through
   small carriers, leased connections or compromised equipment
⚠️ ⚠️ WHAT SS7 ACCESS PERMITS  ⚠️ locating a subscriber ·
   ⚠️ INTERCEPTING SMS (⚠️ which defeats SMS-based two-factor
   authentication, §13) · intercepting or redirecting calls ·
   denial of service
⚠️ ⚠️ THIS IS NOT THEORETICAL. ⚠️ It has been demonstrated
   publicly, documented by regulators, and used in the wild
⚠️ DIAMETER  ⚠️ the LTE-era successor, with better authentication
   in principle and ⚠️ comparable classes of vulnerability in
   practice, partly because interworking with SS7 is required
⚠️ MITIGATIONS  ⚠️ SS7 firewalls, home routing, filtering — but
   ⚠️ THE STRUCTURAL PROBLEM PERSISTS because the network must
   interoperate globally with participants of varying integrity
   (§1's federated trade, in its most consequential form)
```

---

## §10. VoIP and SIP

**⚠️ The separation that defines it**: ⚠️ **SIP handles signalling — establishing, modifying
and terminating sessions — while RTP carries the actual media, on different ports and often
a different path.**
**⚠️ SDP** negotiates codecs and addresses; ⚠️ **SRTP encrypts media; SIP over TLS protects
signalling.**
**⚠️ Codecs**: ⚠️ **G.711 (uncompressed PSTN quality), G.722 and Opus for wideband —
⚠️ and Opus is the modern default because it adapts across a huge bitrate range and handles
loss gracefully.**
**⚠️ NAT traversal is the perennial engineering pain**: ⚠️ **STUN discovers your public
address, TURN relays when direct connection fails, and ICE tries candidates in order**
(§19 → `comms-webrtc-video-conferencing-team-platforms-and-push`).
**⚠️ Quality metrics**: ⚠️ **latency (⚠️ interactivity degrades noticeably above roughly
150 ms one-way), JITTER (⚠️ absorbed by a jitter buffer, which trades latency for
smoothness), and packet loss — ⚠️ and concealment algorithms mask modest loss surprisingly
well.**
**⚠️ SIP trunking** replaced ISDN for business telephony, ⚠️ **and toll fraud on
misconfigured PBXs remains a live and expensive problem.**

---

## §11. VoLTE and VoNR

**⚠️ Voice over LTE** carries voice as IP packets over the data network with QoS bearers,
⚠️ **rather than falling back to a circuit-switched network.**
**⚠️ The IMS core** is the architecture underneath, ⚠️ **and it is what makes voice a
service on the data network rather than a separate system.**
**⚠️ The user-visible benefits**: ⚠️ **HD voice via wideband codecs (AMR-WB and EVS),
much faster call setup, and simultaneous voice and data.**
**⚠️ 2G and 3G shutdown** makes VoLTE mandatory rather than optional — ⚠️ **and this has
stranded older handsets and, importantly, a great deal of embedded telemetry** (see a
wireless reference §13).
**⚠️ VoWiFi** uses the same IMS core over any internet connection, ⚠️ **which is why calls
work over hotel Wi-Fi with no coverage, and why emergency location becomes harder** (§27 → `comms-encryption-metadata-interoperability-and-policy`).

---

## §12. ⚠️ Caller ID, Spoofing and Robocalls

**⚠️ Caller ID was never authenticated** — ⚠️ **the calling number is asserted by the
originating network and, with SIP trunking, is trivially set by the caller.**
**⚠️ NEIGHBOUR SPOOFING** — ⚠️ **forging a number matching the recipient's prefix — exploits
this, and it is why answer rates for unknown numbers collapsed.**
**⚠️ STIR/SHAKEN** is the response: ⚠️ **the originating carrier cryptographically signs the
calling number with an attestation level (A: we know the caller and their right to the
number; B: we know the customer but not the number; C: we just passed it on), and the
terminating carrier verifies** (see a cryptography reference on certificate chains).
> **⚠️ GOTCHA — STIR/SHAKEN authenticates the CARRIER'S ASSERTION, not the caller's
> honesty.** ⚠️ **An A-level attestation means a carrier vouched for the number, not that the
> call is legitimate.** **⚠️ It also only works on IP-connected legs, so calls transiting
> older segments lose the signature — which is exactly §1 → `comms-email-smtp-authentication-and-deliverability`'s weakest-participant problem.**

**⚠️ It has helped and not solved**: ⚠️ **enforcement, traceback and gateway-provider
obligations do more of the work than the cryptography does.**
**⚠️ Branded calling** and RCS-verified sender identity (§15 → `comms-sms-rcs-signal-protocol-and-messaging-apps`) are the commercial responses to
the trust collapse.

---

# PART III — MESSAGING
