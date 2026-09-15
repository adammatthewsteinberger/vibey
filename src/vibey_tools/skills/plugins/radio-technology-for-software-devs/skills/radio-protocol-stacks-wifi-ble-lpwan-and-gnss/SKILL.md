---
name: radio-protocol-stacks-wifi-ble-lpwan-and-gnss
description: "Use when choosing or debugging a specific radio technology: the protocol stack and where each layer's problems show up, Wi-Fi and the 802.11 generations, Bluetooth and BLE including connection parameters and throughput reality, LPWAN and cellular IoT options, 802.15.4 with Zigbee, Thread and Matter, and GNSS including time to first fix and accuracy in real conditions."
---

# Radio Technology: The Stack, Wi-Fi, Bluetooth and BLE, LPWAN and Cellular IoT, Thread and Matter, and GNSS

> **Part 4 of 6** of the *Radio Technology for Software Developers* reference (plugin `radio-technology-for-software-devs`), covering §17–§22. Sibling skills: `radio-intuitions-spectrum-link-budget-and-tradeoffs` (§0–§4), `radio-antennas-propagation-noise-and-modulation` (§5–§9), `radio-spread-spectrum-ofdm-access-and-sdr` (§10–§16), `radio-regulatory-security-and-debugging` (§23–§26), `radio-reference` (§27–§32). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** RF physics and DSP are permanent. Two areas moved. See §24 → `radio-regulatory-security-and-debugging` for Wi-Fi 7 and 8 and the 6 GHz regulatory status, and the IoT connectivity landscape after the 2G and 3G sunset.

> **⚠️ Scope.** Written for people who write software and now have to make a radio work.
> Complements an embedded/IoT reference (the devices), an electrical engineering
> reference (the circuits), and a networking reference (layer 3 and up). **This is layers
> 0–2 and the physics underneath them.**
>
> **⚠️ GOTCHA** boxes mark things that cause intermittent, unreproducible field failures —
> the expensive kind.
>
> **The three ideas that organize this document:**
> 1. **⚠️ RF is where software abstractions leak worst.** **Every layer above assumes a
>    link that mostly works; RF is a shared, non-deterministic, physically-constrained
>    medium where the same code works on your desk and fails in the field** (§1 → `radio-intuitions-spectrum-link-budget-and-tradeoffs`).
> 2. **⚠️ The link budget is the single most useful tool you can learn** (§3 → `radio-intuitions-spectrum-link-budget-and-tradeoffs`). **Most
>    wireless problems are budget problems, and most of them are diagnosable on paper
>    before you build anything.**
> 3. **⚠️ Choosing the radio is an architecture decision, not a component decision.**
>    **Range, data rate, power and cost trade against each other in ways physics fixes**
>    (§4 → `radio-intuitions-spectrum-link-budget-and-tradeoffs`, §19), **and you cannot fix a bad choice in firmware.**

---

## §17. The Stack

**⚠️ Know which layer your problem is at, because the tools are completely different.**
```
PHY   ⚠️ modulation, coding, symbol timing. Tools: SDR, spectrum analyzer
MAC   ⚠️ channel access, addressing, ACK/retry. Tools: sniffer, protocol analyzer
NET+  routing, transport, application. Tools: normal software debugging
```
⚠️ **The most common mistake is trying to debug a PHY problem with application-layer
tools.** **If your packet loss is caused by a fading null (§6 → `radio-antennas-propagation-noise-and-modulation`), no amount of Wireshark
will show you why.**

---

## §18. Wi-Fi (802.11)

```
GEN      STD      BANDS          KEY FEATURE
Wi-Fi 4  11n      2.4/5          MIMO
Wi-Fi 5  11ac     5              MU-MIMO, 256-QAM, 160 MHz
Wi-Fi 6  11ax     2.4/5          ⚠️ OFDMA, TWT (big for IoT battery life)
Wi-Fi 6E 11ax     ⚠️ + 6 GHz     clean spectrum, no legacy devices
Wi-Fi 7  11be     2.4/5/6        ⚠️ MLO, 320 MHz, 4096-QAM, puncturing (§24.1)
Wi-Fi 8  11bn     ⚠️ ~2028       reliability, not speed (§24.1)
```
**⚠️ Things software people get wrong about Wi-Fi:**
- **⚠️ Advertised rates are aggregate PHY peaks.** **Real throughput is roughly half or
  less after MAC overhead, and shared.**
- **⚠️ 2.4 GHz has only three non-overlapping 20 MHz channels (1, 6, 11) in most
  regulatory domains.** **Using anything else creates partial overlap, which is worse than
  full overlap — partial overlap means carrier sense fails AND you interfere.**
- **⚠️ Wider channels are not automatically better.** **A 160 MHz channel has a higher peak
  rate and a proportionally higher noise floor (§7 → `radio-antennas-propagation-noise-and-modulation`) and more chance of overlapping
  someone.** **In dense environments narrower channels often outperform.**
- **⚠️ Wi-Fi power-saves badly compared to BLE or 802.15.4** — ⚠️ **TWT (Wi-Fi 6) improves
  this substantially and is the reason Wi-Fi became viable for battery IoT at all.**
- **⚠️ Roaming between APs is client-driven and historically terrible.** **802.11k/v/r
  help; client implementations vary enormously.**

---

## §19. Bluetooth and BLE

**⚠️ Classic Bluetooth and BLE are different protocols that share a brand.**
```
BLE       ⚠️ 2.4 GHz, 40 channels × 2 MHz, GFSK, adaptive frequency hopping
   ⚠️ 3 ADVERTISING channels (37/38/39) deliberately placed to dodge the
   most-used Wi-Fi channels
ROLES     Peripheral/Central; Broadcaster/Observer
⚠️ GATT   the data model — Services → Characteristics → Descriptors, each
   with a UUID. ⚠️ This is where most BLE application bugs live
CONNECTION INTERVAL  ⚠️ 7.5 ms–4 s. THE dominant power/latency knob
5.x       ⚠️ 2 Mbps PHY (faster, shorter range) · CODED PHY (LE Long Range,
   ~4× range via FEC) · extended advertising · ⚠️ LE Audio and Auracast ·
   direction finding (AoA/AoD)
```
> **⚠️ GOTCHA — connection interval and slave latency dominate both battery life and
> responsiveness, and they're negotiated, not commanded.** ⚠️ **The central proposes; the
> peripheral requests; and some platforms silently override what you ask for.**
> **iOS in particular enforces its own constraints regardless of your request**, **which
> is why a peripheral behaves differently on Android and iOS with identical firmware.**
> **⚠️ Always read back the ACTUAL negotiated parameters rather than assuming.**

**⚠️ MTU negotiation is the other perennial**: **the default ATT MTU is tiny (23 bytes,
20 usable), and failing to negotiate a larger one silently fragments your data and
destroys throughput.**

---

## §20. LPWAN and Cellular IoT

```
LoRaWAN   ⚠️ unlicensed sub-GHz, CSS (§10), ~km range, YOU run the gateway.
   ⚠️ No recurring network cost; duty-cycle limited (§23); Class A devices
   only listen briefly after transmitting, so downlink is very constrained
Sigfox    ultra-narrowband, tiny payloads, operator network (⚠️ commercially
   troubled; check viability before designing it in)
NB-IoT    ⚠️ licensed, in-band LTE. Best deep-indoor penetration, lowest
   power, ⚠️ poor mobility, slow FOTA
LTE-M     ⚠️ licensed. Handles MOBILITY, better roaming, enough bandwidth
   for reliable firmware updates, voice capable
LTE Cat-1 / Cat-1 bis  ⚠️ higher rate, very broad availability (§24.2)
5G RedCap ⚠️ "reduced capability" 5G — the mid-tier (§24.2)
NTN       ⚠️ satellite running NB-IoT/LTE-M (§24.2)
```
**⚠️ The decision tree that actually matters** (elaborated in §24.2 → `radio-regulatory-security-and-debugging`):
```
Does it MOVE?              → ⚠️ LTE-M. NB-IoT and LoRaWAN handle mobility poorly
Do you control the site?   → ⚠️ LoRaWAN (no recurring cost) is viable
Data per day?              ⚠️ <1 KB: NB-IoT/LoRaWAN · 1 KB–1 MB: NB-IoT/LTE-M
                             >1 MB: LTE-M or LTE Cat-1
Need reliable OTA updates? → ⚠️ LTE-M. NB-IoT FOTA is slow and painful
No coverage at all?        → NTN/satellite, or LoRaWAN with your own gateway
```

---

## §21. 802.15.4, Zigbee, Thread, Matter

**⚠️ Keep the layers straight, because the marketing does not:**
```
802.15.4  ⚠️ the PHY/MAC. 2.4 GHz (and sub-GHz), DSSS, 250 kbps
Zigbee    full stack on top of 802.15.4. ⚠️ Older; vendor profile fragmentation
Thread    ⚠️ IPv6 (6LoWPAN) MESH on 802.15.4. Self-healing, no single
          coordinator, border router bridges to your LAN
Matter    ⚠️ APPLICATION layer. Runs over Thread, Wi-Fi, or Ethernet.
          ⚠️ NOT a radio — this is the single most common confusion
```
**⚠️ Mesh networking is genuinely useful and genuinely costly**: **self-healing and
extended coverage, at the price of routing overhead, latency that grows with hop count,
and routers that cannot sleep.** ⚠️ **In a mesh, only leaf/end devices get long battery
life.**

---

## §22. GNSS

**⚠️ GPS, GLONASS, Galileo, BeiDou.** **Trilateration from satellite timing; you need
4 satellites — three for position and one to solve for the receiver's clock error.**
```
⚠️ Signal arrives BELOW the noise floor (~−130 dBm); DSSS processing gain
   recovers it (§10). This is why GNSS fails indoors
TTFF   ⚠️ cold start can be 30 s+; A-GNSS supplies ephemeris over the network
   to cut this dramatically
ACCURACY  ⚠️ ~3–5 m typical consumer; RTK/PPP reach centimetres with
   correction data; multipath in urban canyons is the dominant error
⚠️ SPOOFING and JAMMING are real, cheap, and increasingly common
```
**⚠️ For software**: **NMEA sentences are the lingua franca; use HDOP/fix-quality rather
than trusting any fix; and expect to filter — raw consumer GNSS positions jump around,
and naive distance-accumulation over noisy fixes massively overestimates travel.**
