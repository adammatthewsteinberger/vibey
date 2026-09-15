---
name: wireless-reference
description: "Use when correcting a wireless misconception, looking up a range, throughput, power, sensitivity or duty-cycle figure, finding the sources, or needing a quick-reference picker — plus the current state of Wi-Fi's next generation and Bluetooth ranging. Companion to the other wireless technologies skills."
---

# Wireless Technologies and RF: What's Live, Misconceptions, Numbers, and Sources

> **Part 6 of 6** of the *Wireless Technologies: RF, Standards, Building and Programming* reference (plugin `wireless-technologies-and-rf-engineering`), covering §25–§30. Sibling skills: `wireless-propagation-link-budget-modulation-antennas-and-spectrum` (§0–§5), `wireless-wifi-bluetooth-ble-nfc-and-rfid` (§6–§10), `wireless-thread-matter-lora-cellular-uwb-and-choosing` (§11–§16), `wireless-antenna-integration-certification-low-power-and-debugging` (§17–§21), `wireless-security-coexistence-and-positioning` (§22–§24). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The physics is permanent and the mature standards are stable. Two areas are moving. See §25 for Wi-Fi's next generation, and Bluetooth ranging.

> **⚠️ The domain where physics imposes limits that no amount of software cleverness
> removes — and where nearly every practical problem turns out to be either a link budget
> problem, an antenna problem, or a coexistence problem.**
>
> **Builds on an electromagnetism reference (fields, propagation, transmission lines) and
> complements a peripherals reference (§5's wireless HID), a computer-hardware reference
> (§9 → `wireless-wifi-bluetooth-ble-nfc-and-rfid` networking), and a cryptography reference (WPA3, pairing, key exchange).**
>
> **⚠️ GOTCHA** boxes mark where spec-sheet numbers and field reality diverge — which in RF
> is nearly everywhere.
>
> **The three ideas that organize this document:**
> 1. **⚠️ THE LINK BUDGET IS THE WHOLE GAME** (§2 → `wireless-propagation-link-budget-modulation-antennas-and-spectrum`). **Transmit power, antenna gains, path
>    loss and receiver sensitivity determine whether a link works. Everything else is
>    optimization within that envelope, and "add more power" is almost never the available
>    lever because regulation caps it.**
> 2. **⚠️ SPECTRUM IS A SHARED, CONTESTED, REGULATED RESOURCE** (§5 → `wireless-propagation-link-budget-modulation-antennas-and-spectrum`, §23 → `wireless-security-coexistence-and-positioning`). **You do not own
>    your channel. Unlicensed bands mean your neighbours, your own other radios, and
>    physically unrelated devices all degrade you — and coexistence design is not optional.**
> 3. **⚠️ THE ANTENNA IS THE MOST NEGLECTED COMPONENT AND THE MOST DECISIVE** (§4 → `wireless-propagation-link-budget-modulation-antennas-and-spectrum`, §17 → `wireless-antenna-integration-certification-low-power-and-debugging`).
>    **A superb radio with a badly integrated antenna performs worse than a mediocre radio
>    with a good one, and antenna problems are usually designed in months before anyone
>    measures them.**

---

## §25. What's Live — checked August 2026

### 25.1 ⚠️ Wi-Fi 8: reliability instead of speed, and hardware ahead of the standard
**⚠️ §6 → `wireless-wifi-bluetooth-ble-nfc-and-rfid`'s next generation, and it represents a genuine change of philosophy.**

- **⚠️ THE SHIFT.** ⚠️ **IEEE 802.11bn, marketed as Wi-Fi 8 and named Ultra High Reliability
  (UHR), is the first generation NOT primarily chasing peak throughput.** ⚠️ **Samsung
  Research summarizes the trajectory bluntly: from 2 Mbps in legacy 802.11 to 36 Gbps in
  Wi-Fi 7 by adding bandwidth, higher modulation and spatial streams — and 802.11bn shifts
  focus beyond peak performance in ideal conditions to stable performance at coverage
  edges.**
- **⚠️ THE PAR TARGETS, which are the honest specification of ambition**: ⚠️ **at least 25%
  higher throughput in CHALLENGING signal conditions, 25% lower latency at the 95th
  PERCENTILE, and 25% fewer dropped packets — all relative to Wi-Fi 7.**
  ⚠️ **Note these are percentile and edge-case targets, not peak-rate targets. Peak
  bandwidth is reported as broadly unchanged.**
- **⚠️ THE NEW MECHANISMS** are mostly about APs cooperating rather than competing:
  ⚠️ **Multi-AP Coordination (MAPC), Coordinated Spatial Reuse (Co-SR — APs adjusting
  transmit power so they can share a channel simultaneously), Dynamic Sub-Channel Operation
  (splitting wide channels into narrower ones to serve more devices), Enhanced Long Range,
  and Distributed Resource Units.** ⚠️ **MediaTek trials are reported suggesting Co-SR could
  raise system throughput 15–25%.**
- **⚠️ It retains** 2.4/5/6 GHz, 320 MHz channels and Multi-Link Operation from Wi-Fi 7.

> **⚠️ GOTCHA — products are arriving YEARS before the standard, and this matters for buying
> decisions.** ⚠️ **IEEE final approval is targeted for 2028, with certification reported
> around January 2028; meanwhile draft-based hardware was shown at CES 2026 by multiple
> chipmakers and router brands, with retail products reported as possible from summer or
> late 2026.**
> ⚠️ **Draft progress through 2026 is publicly tracked and is genuinely incremental — Draft
> 1.3 approved in January, Draft 1.4 in March, and Draft 2.0 reported slipping from May to
> July 2026.**
> **⚠️ The consistent advice across sources, including ones with no product to sell, is that
> Wi-Fi 7 is the mature standard for this cycle and deferring a refresh to wait for Wi-Fi 8
> means waiting through a draft-hardware period into a 2028 certification window and then
> again for clients.**
> ⚠️ **The stated exceptions are exactly the environments UHR targets: very high AP density,
> heavy roaming, deterministic latency requirements, and large fleets of low-power uplink
> devices — those operators should track it and treat draft hardware as evaluation, not
> production.**

**⚠️ My reading**: ⚠️ **this is the most honest generational pitch Wi-Fi has made in years,
because §1 → `wireless-propagation-link-budget-modulation-antennas-and-spectrum`'s core complaint — that advertised rates never resemble real experience — is
finally what the standard is targeting.** ⚠️ **One source puts it well: Wi-Fi 8 will not
make every client faster, it is designed to make Wi-Fi less fragile.**

### 25.2 ⚠️ Bluetooth Channel Sounding: ranging without UWB hardware
**⚠️ §14 → `wireless-thread-matter-lora-cellular-uwb-and-choosing`'s capability arriving on the radio everything already has — and §22 → `wireless-security-coexistence-and-positioning`'s relay-attack
problem being addressed properly.**

- **⚠️ WHAT IT IS.** ⚠️ **Channel Sounding is the flagship feature of Bluetooth Core 6.0,
  adopted August 2024.** ⚠️ **The SIG describes it as enabling SECURE FINE RANGING between
  two devices, designed to meet the accuracy and security requirements of applications like
  digital keys and Find My networks.**
- **⚠️ HOW, and the two methods are complementary.** ⚠️ **Phase-Based Ranging and
  Round-Trip Timing, usable independently or together — RTT for coarse range, phase for
  precision.** ⚠️ **One technical description explains the mechanism as synthesizing a wide
  effective bandwidth from many narrow 1 MHz channels using super-resolution techniques,
  which is how a narrowband radio achieves fine ranging at all.**
- **⚠️ ACCURACY CLAIMS VARY BY SOURCE AND SHOULD BE READ CAREFULLY.** ⚠️ **Reported figures
  range from "tens of centimetre-level" to "±10 cm at 10 m" to "centimetre-level over
  distances up to roughly 150 metres."** ⚠️ **The conservative reading is sub-metre
  reliably, with centimetre-class accuracy under good conditions — and independent research
  on performance in complex indoor environments is active, which itself indicates the
  hard cases are not solved.**
- **⚠️ THE SECURITY PROPERTY IS THE POINT, and it is §22 → `wireless-security-coexistence-and-positioning`'s problem directly.** ⚠️ **RSSI
  proximity is an educated guess that relay attacks defeat trivially; Channel Sounding
  provides distance bounding described as relay-attack-resistant via cryptographic
  frequency hopping.** ⚠️ **Core 6.2 is reported to add anomaly detection against
  amplitude-based spoofing.**

> **⚠️ GOTCHA — the strategic significance is that this challenges UWB on UWB's home
> ground.** ⚠️ **One description states it plainly: centimetre-accurate measurement using
> the standard BLE 2.4 GHz radio, WITHOUT requiring UWB hardware.**
> ⚠️ **For product designers that changes the §14 → `wireless-thread-matter-lora-cellular-uwb-and-choosing` versus §8 → `wireless-wifi-bluetooth-ble-nfc-and-rfid` decision materially — if the
> radio you already fitted for connectivity can also do secure ranging, the case for a
> second dedicated radio narrows considerably.** **⚠️ I would not assume it fully matches
> UWB's accuracy or multipath resilience; the honest position is that it is good enough for
> a large set of applications that previously needed UWB.**

**⚠️ Deployment status**: ⚠️ **silicon vendors have shipped native Channel Sounding
hardware, with adoption reported reaching flagship and high-end smartphones; Nordic
Semiconductor expects expansion into commercial and industrial use in 2026 for sub-metre
asset tracking and worker-safety geofencing; Samsung anticipates digital key and precise
device discovery use cases.**
**⚠️ Note the SIG's cadence**: ⚠️ **Core 6.0 (Aug 2024), 6.1 (May 2025), 6.2 (late 2025),
6.3 (May 2026) — roughly twice yearly, refining rather than replacing.** ⚠️ **And §8 → `wireless-wifi-bluetooth-ble-nfc-and-rfid`'s
point recurs: features have decoupled from version numbers, which is why the SIG encourages
advertising "supports Auracast" rather than a core version.**
**⚠️ Sourcing note: the Bluetooth SIG is describing its own specification, and several
sources are silicon vendors and paywalled market-research summaries.** ⚠️ **The
specification facts and the mechanism are solid; the accuracy figures and adoption
percentages are vendor and analyst claims, and I have reported the range rather than
picking the most flattering number.**

---

## §26. Misconceptions

| Misconception | Correction |
|---|---|
| Advertised data rate is what you get | ⚠️ **Peak, shared, half-duplex, pre-overhead** (§1 → `wireless-propagation-link-budget-modulation-antennas-and-spectrum`) |
| More transmit power fixes range | ⚠️ **Regulated, and often makes the return path worse** (§5 → `wireless-propagation-link-budget-modulation-antennas-and-spectrum`, §7 → `wireless-wifi-bluetooth-ble-nfc-and-rfid`) |
| 5 GHz is better than 2.4 GHz | ⚠️ **More capacity, less range. Physics, not quality** (§2 → `wireless-propagation-link-budget-modulation-antennas-and-spectrum`) |
| Wider channels are always faster | ⚠️ **Higher noise floor, fewer channels. Often worse when dense** (§6 → `wireless-wifi-bluetooth-ble-nfc-and-rfid`) |
| Antenna gain amplifies | ⚠️ **It's directionality. Passive** (§4 → `wireless-propagation-link-budget-modulation-antennas-and-spectrum`) |
| Higher-gain omni is always better | ⚠️ **It squashes the pattern vertically** (§4 → `wireless-propagation-link-budget-modulation-antennas-and-spectrum`) |
| The antenna is a component you bolt on | ⚠️ **The ground plane and enclosure are part of it** (§4 → `wireless-propagation-link-budget-modulation-antennas-and-spectrum`, §17 → `wireless-antenna-integration-certification-low-power-and-debugging`) |
| Test the radio on a bare board | ⚠️ **The enclosure detunes it. Tune as-built** (§17 → `wireless-antenna-integration-certification-low-power-and-debugging`) |
| MIMO works best with clear line of sight | ⚠️ **Spatial multiplexing needs rich multipath** (§3 → `wireless-propagation-link-budget-modulation-antennas-and-spectrum`) |
| BLE is a newer Bluetooth version | ⚠️ **Different radio and stack, since 4.0 in 2010** (§8 → `wireless-wifi-bluetooth-ble-nfc-and-rfid`) |
| LE Audio means Bluetooth 5.2+ | ⚠️ **Features decoupled from version numbers** (§8 → `wireless-wifi-bluetooth-ble-nfc-and-rfid`) |
| Auracast works on any modern device | ⚠️ **Needs PAwR — 5.4 and later** (§8 → `wireless-wifi-bluetooth-ble-nfc-and-rfid`) |
| Poll a BLE characteristic for updates | ⚠️ **Subscribe. Notifications exist for this** (§9 → `wireless-wifi-bluetooth-ble-nfc-and-rfid`) |
| NFC is short-range because of low power | ⚠️ **Near-field inductive coupling. Physics** (§10 → `wireless-wifi-bluetooth-ble-nfc-and-rfid`) |
| Matter is a wireless protocol | ⚠️ **Application layer over Thread/Wi-Fi/Ethernet** (§11 → `wireless-thread-matter-lora-cellular-uwb-and-choosing`) |
| A mesh of battery sensors self-heals | ⚠️ **Battery devices usually don't route** (§11 → `wireless-thread-matter-lora-cellular-uwb-and-choosing`) |
| RSSI gives you distance | ⚠️ **Terrible proxy. Multipath and obstruction dominate** (§24 → `wireless-security-coexistence-and-positioning`) |
| Signal strength proves proximity | ⚠️ **Relay attacks defeat it. Needs distance bounding** (§22 → `wireless-security-coexistence-and-positioning`, §25.2) |
| Optimize transmit efficiency for battery life | ⚠️ **Sleep current usually dominates** (§19 → `wireless-antenna-integration-certification-low-power-and-debugging`) |
| A coin cell with enough capacity will work | ⚠️ **Peak current capability is separate** (§19 → `wireless-antenna-integration-certification-low-power-and-debugging`) |
| Certification is a final step | ⚠️ **Design for it, pre-test early** (§18 → `wireless-antenna-integration-certification-low-power-and-debugging`) |
| A module means no RF work | ⚠️ **Only if you follow the reference layout exactly** (§16 → `wireless-thread-matter-lora-cellular-uwb-and-choosing`, §17 → `wireless-antenna-integration-certification-low-power-and-debugging`) |
| My wireless mouse is faulty | ⚠️ **Often USB 3 noise desensitizing 2.4 GHz** (§23 → `wireless-security-coexistence-and-positioning`) |
| Interference comes from other people | ⚠️ **In-device coexistence is often the harder problem** (§23 → `wireless-security-coexistence-and-positioning`) |
| Wi-Fi 8 will be much faster | ⚠️ **Peak is broadly flat. It targets edge and percentile** (§25.1) |
| Wi-Fi 8 products mean the standard is done | ⚠️ **Draft hardware. IEEE approval targeted 2028** (§25.1) |
| Ranging requires UWB | ⚠️ **Channel Sounding does it on the BLE radio** (§25.2) |

---

## §27. Numbers

```
⚠️ dB  ⚠️ +3 dB = 2× power · +10 dB = 10× · 0 dBm = 1 mW
⚠️ Path loss  ⚠️ ∝ distance² AND frequency² · 2× distance = 6 dB
⚠️ 2.4 GHz non-overlapping 20 MHz channels  ⚠️ 3 (1, 6, 11)
⚠️ dBi vs dBd  ⚠️ 2.15 dB apart
⚠️ Bluetooth Classic  79 ch × 1 MHz · ⚠️ BLE 40 ch × 2 MHz
⚠️ Legacy BLE advertising payload  ⚠️ 31 bytes
⚠️ NFC  13.56 MHz · near field · centimetres
⚠️ RFID  LF 125 kHz · HF 13.56 MHz · UHF 860-960 MHz (regional)
⚠️ UWB ranging accuracy  ⚠️ ~10 cm
⚠️ Wi-Fi 7 peak (802.11be)  ⚠️ ~36 Gbps quoted (Samsung Research)
⚠️ Wi-Fi 8 PAR targets  ⚠️ +25% throughput in CHALLENGING conditions ·
   −25% latency at 95th percentile · −25% dropped packets
⚠️ Wi-Fi 8 IEEE approval target  ⚠️ 2028 (cert ~Jan 2028 reported)
⚠️ Wi-Fi 8 draft progress  ⚠️ D1.3 Jan 2026 · D1.4 Mar · D2.0 → Jul
⚠️ Co-SR trial gain  ⚠️ 15-25% system throughput (MediaTek, reported)
⚠️ Bluetooth Core 6.0  ⚠️ adopted August 2024
⚠️ Channel Sounding accuracy  ⚠️ reported from "tens of cm" to
   "±10 cm at 10 m" — ⚠️ treat sub-metre as the safe claim
⚠️ SIG cadence  ⚠️ 6.0 Aug 2024 · 6.1 May 2025 · 6.2 late 2025 ·
                 6.3 May 2026
```

---

## §28. Sources

| Source | Why |
|---|---|
| **Rappaport, *Wireless Communications: Principles and Practice*** | ⚠️ **§2–§3 → `wireless-propagation-link-budget-modulation-antennas-and-spectrum`, the standard** |
| **ARRL Antenna Book / Handbook** | ⚠️ **§4 → `wireless-propagation-link-budget-modulation-antennas-and-spectrum`, §17 → `wireless-antenna-integration-certification-low-power-and-debugging` — practical and unmatched** |
| **Bluetooth SIG core specification and feature overviews** | ⚠️ **§8–§9 → `wireless-wifi-bluetooth-ble-nfc-and-rfid`, primary and free** |
| **IEEE 802.11 working group documents** | ⚠️ **§6 → `wireless-wifi-bluetooth-ble-nfc-and-rfid`, §25.1 — the actual drafts** |
| **Wi-Fi Alliance certification programmes** | What "certified" actually means |
| **NFC Forum specifications** | §10 → `wireless-wifi-bluetooth-ble-nfc-and-rfid` |
| **Nordic, TI, Espressif and Silicon Labs app notes** | ⚠️ **§16–§19 → `wireless-thread-matter-lora-cellular-uwb-and-choosing`, `wireless-antenna-integration-certification-low-power-and-debugging` — vendor app notes are the real documentation in RF** |
| **Zephyr Project documentation** | ⚠️ **§9 → `wireless-wifi-bluetooth-ble-nfc-and-rfid`, §17 → `wireless-antenna-integration-certification-low-power-and-debugging` — portable and well written** |
| **Your regulator's equipment authorization guidance** | ⚠️ **§18 → `wireless-antenna-integration-certification-low-power-and-debugging` — read before designing** |
| **Ekahau / wireless survey vendor material** | §7 → `wireless-wifi-bluetooth-ble-nfc-and-rfid`, practical deployment |
| **RTL-SDR community resources** | ⚠️ **§21 → `wireless-antenna-integration-certification-low-power-and-debugging`, the cheapest way to actually see RF** |

---

## §29. Quick Reference

### 29.1 Picker
| Question | Where |
|---|---|
| Will this link work? | ⚠️ **Do the link budget first** (§2 → `wireless-propagation-link-budget-modulation-antennas-and-spectrum`) |
| Range is poor — what now? | ⚠️ **Antenna and placement before power** (§1 → `wireless-propagation-link-budget-modulation-antennas-and-spectrum`, §17 → `wireless-antenna-integration-certification-low-power-and-debugging`) |
| Which radio for my product? | ⚠️ **Answer power and "talk to what" first** (§16 → `wireless-thread-matter-lora-cellular-uwb-and-choosing`) |
| Module or chip-down? | ⚠️ **Module, unless high volume** (§16 → `wireless-thread-matter-lora-cellular-uwb-and-choosing`, §18 → `wireless-antenna-integration-certification-low-power-and-debugging`) |
| Why is battery life bad? | ⚠️ **Measure SLEEP current on the real board** (§19 → `wireless-antenna-integration-certification-low-power-and-debugging`) |
| BLE throughput too low | ⚠️ **Connection interval, MTU, PHY — not the "2 Mbps"** (§9 → `wireless-wifi-bluetooth-ble-nfc-and-rfid`) |
| Wi-Fi slow in a crowded office | ⚠️ **Narrower channels, lower power, more APs** (§7 → `wireless-wifi-bluetooth-ble-nfc-and-rfid`) |
| Client won't roam | ⚠️ **The client decides, not the AP** (§6 → `wireless-wifi-bluetooth-ble-nfc-and-rfid`) |
| Tag won't read on metal | ⚠️ **Needs on-metal design with a spacer** (§10 → `wireless-wifi-bluetooth-ble-nfc-and-rfid`) |
| Is proximity secure enough? | ⚠️ **No. Relay attacks. Need distance bounding** (§22 → `wireless-security-coexistence-and-positioning`, §25.2) |
| Mouse drops out near the PC | ⚠️ **USB 3 noise. Move the dongle** (§23 → `wireless-security-coexistence-and-positioning`) |
| Should I wait for Wi-Fi 8? | ⚠️ **No, unless you're a dense-deployment operator** (§25.1) |
| Do I need UWB for ranging? | ⚠️ **Maybe not now** (§14 → `wireless-thread-matter-lora-cellular-uwb-and-choosing`, §25.2) |

### 29.2 Wireless product checklist
- [ ] ⚠️ **Link budget computed with realistic path loss, not free space** (§2 → `wireless-propagation-link-budget-modulation-antennas-and-spectrum`)
- [ ] ⚠️ **Regions of sale confirmed — band availability and duty cycle** (§5 → `wireless-propagation-link-budget-modulation-antennas-and-spectrum`)
- [ ] Radio chosen against power budget and connectivity requirement (§16 → `wireless-thread-matter-lora-cellular-uwb-and-choosing`)
- [ ] ⚠️ **Module reference layout followed EXACTLY, keepout respected** (§17 → `wireless-antenna-integration-certification-low-power-and-debugging`)
- [ ] ⚠️ **Antenna tuned with the final enclosure, battery and display fitted** (§17 → `wireless-antenna-integration-certification-low-power-and-debugging`)
- [ ] ⚠️ **Tested on-body if worn** (§17 → `wireless-antenna-integration-certification-low-power-and-debugging`)
- [ ] Sleep current measured, not calculated (§19 → `wireless-antenna-integration-certification-low-power-and-debugging`)
- [ ] Peak current capability of the battery verified (§19 → `wireless-antenna-integration-certification-low-power-and-debugging`)
- [ ] ⚠️ **In-device coexistence considered — every radio and switcher** (§23 → `wireless-security-coexistence-and-positioning`)
- [ ] ⚠️ **Pre-compliance scan before booking a chamber** (§18 → `wireless-antenna-integration-certification-low-power-and-debugging`)
- [ ] ⚠️ **Modular certification conditions not invalidated** (§18 → `wireless-antenna-integration-certification-low-power-and-debugging`)
- [ ] Industry certification budgeted (SIG, Wi-Fi Alliance, carrier) (§18 → `wireless-antenna-integration-certification-low-power-and-debugging`)
- [ ] ⚠️ **Pairing method gives MITM protection — not "Just Works"** (§22 → `wireless-security-coexistence-and-positioning`)
- [ ] ⚠️ **Provisioning window closes; device authenticates too** (§20 → `wireless-antenna-integration-certification-low-power-and-debugging`, §22 → `wireless-security-coexistence-and-positioning`)
- [ ] ⚠️ **Signed firmware update path; debug interfaces disabled** (§22 → `wireless-security-coexistence-and-positioning`)
- [ ] ⚠️ **Tested at range, in the real environment, against golden units** (§21 → `wireless-antenna-integration-certification-low-power-and-debugging`)

---

## §30. Method

**§1–§24 → `wireless-propagation-link-budget-modulation-antennas-and-spectrum`, `wireless-wifi-bluetooth-ble-nfc-and-rfid`, `wireless-thread-matter-lora-cellular-uwb-and-choosing`, `wireless-antenna-integration-certification-low-power-and-debugging`, `wireless-security-coexistence-and-positioning` rests on settled physics and mature standards** — **the link budget, free-space
path loss, OFDM, CSMA/CA, the GATT model, near-field coupling in NFC, and the
certification regime.** ⚠️ **None needed verification; Friis published the transmission
equation in 1946 and the Chu-Harrington limit on small antennas is not going to move.**

**Two searches were run in August 2026**, on **Wi-Fi 8** and **Bluetooth Channel Sounding**
— ⚠️ **the first because 802.11bn represents a genuine change in what a Wi-Fi generation is
FOR, the second because it puts secure ranging on the radio that is already in everything,
which changes a real design decision.**

**Confidence.** **High** in §2 → `wireless-propagation-link-budget-modulation-antennas-and-spectrum` and §4 → `wireless-propagation-link-budget-modulation-antennas-and-spectrum`, which are the sections I'd most want read.
⚠️ **The link budget predicts more than any amount of protocol knowledge, and the dB
intuition — 3 dB doubles, doubling distance costs 6 dB — is what lets you sanity-check a
claim in your head.** ⚠️ **§4 → `wireless-propagation-link-budget-modulation-antennas-and-spectrum`'s "gain is directionality, not amplification" and "the ground
plane is part of the antenna" are the two corrections that most often prevent a product
from being designed wrong months before anyone measures it.** **§19 → `wireless-antenna-integration-certification-low-power-and-debugging`'s point that sleep
current usually dominates battery life is the one that most often saves a project.**

**High** on §25.1's targets, which come from the IEEE 802.11bn PAR as reported by Samsung
Research: ⚠️ **at least 25% higher throughput in challenging conditions, 25% lower 95th-
percentile latency, 25% fewer dropped packets.** ⚠️ **Those are percentile and edge-case
figures rather than peak-rate ones, and reading them correctly is the whole point of the
section.**
⚠️ **The timeline is the practically important part and it is consistent across sources
including ones with nothing to sell: IEEE approval targeted 2028, draft hardware shown at
CES 2026, and the sensible advice being that Wi-Fi 7 is the standard for this cycle.**
**⚠️ Vendor trial figures (Co-SR at 15–25%) are marked as reported.**

**Moderate-to-high** on §25.2. ⚠️ **The specification facts are solid and come from the
Bluetooth SIG directly: Channel Sounding in Core 6.0 from August 2024, combining
phase-based ranging and round-trip timing, designed for digital keys and Find My
networks.**
⚠️ **The ACCURACY CLAIMS are where I'd hold back — sources give "tens of centimetres",
"±10 cm at 10 m" and "centimetre-level up to 150 metres", which cannot all describe the
same thing, and active research on complex indoor environments suggests the hard cases are
unsolved.** **⚠️ I have reported the range and named sub-metre as the safe claim rather
than repeating the most flattering figure.**
⚠️ **The security framing is the durable content: distance bounding defeats relay attacks
in a way signal strength fundamentally cannot, and that is a §22 → `wireless-security-coexistence-and-positioning` problem that has needed a
real answer for years.**
