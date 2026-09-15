---
name: wireless-thread-matter-lora-cellular-uwb-and-choosing
description: "Use when selecting a radio technology: Thread, Zigbee and Matter and what Matter actually standardises, LoRa and LPWAN with their duty-cycle and payload constraints, cellular and cellular IoT including LTE-M and NB-IoT, UWB for ranging, the other technologies worth knowing, and a direct method for choosing a radio from range, rate, power and cost requirements."
---

# Wireless Technologies and RF: Thread, Zigbee and Matter, LoRa and LPWAN, Cellular and Cellular IoT, UWB, Other Technologies, and Choosing a Radio

> **Part 3 of 6** of the *Wireless Technologies: RF, Standards, Building and Programming* reference (plugin `wireless-technologies-and-rf-engineering`), covering §11–§16. Sibling skills: `wireless-propagation-link-budget-modulation-antennas-and-spectrum` (§0–§5), `wireless-wifi-bluetooth-ble-nfc-and-rfid` (§6–§10), `wireless-antenna-integration-certification-low-power-and-debugging` (§17–§21), `wireless-security-coexistence-and-positioning` (§22–§24), `wireless-reference` (§25–§30). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The physics is permanent and the mature standards are stable. Two areas are moving. See §25 → `wireless-reference` for Wi-Fi's next generation, and Bluetooth ranging.

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

## §11. Thread, Zigbee and Matter

**⚠️ 802.15.4** is the shared PHY/MAC underneath — ⚠️ **low rate, low power, mesh-capable,
2.4 GHz (and sub-GHz variants).**
**⚠️ Zigbee** adds its own network and application layers, ⚠️ **and its historical problem
was profile fragmentation between vendors.**
**⚠️ Thread** is IPv6-native (6LoWPAN), ⚠️ **self-healing mesh, no single point of failure,
with Border Routers connecting to the wider IP network — and being IP-native is the
architectural advantage over Zigbee.**
**⚠️ MATTER** is an APPLICATION layer running over Thread, Wi-Fi or Ethernet — ⚠️ **it is
explicitly NOT a radio standard, which is the single most common misunderstanding about
it.**
> **⚠️ GOTCHA — Matter's promise was "everything works with everything," and the honest
> assessment is that it has been slower and messier than promised.** ⚠️ **Feature coverage
> lags device categories, vendor implementations differ, and multi-admin sharing has been
> awkward.** **⚠️ It is real and improving; treat maturity claims by device category rather
> than as a blanket.**

**⚠️ Mesh routing realities**: ⚠️ **battery devices are usually END DEVICES that do not
route, so a mesh only heals if enough mains-powered routers exist — a mesh of battery
sensors is not a mesh.**

---

## §12. LoRa and LPWAN

**⚠️ LoRa is the modulation** (⚠️ **chirp spread spectrum — the reason it demodulates
signals BELOW the noise floor, which is genuinely remarkable**); ⚠️ **LoRaWAN is the network
protocol above it.**
**⚠️ The trade is explicit**: ⚠️ **kilometres of range and years of battery, in exchange for
tiny payloads, high latency and very low duty cycle.**
**⚠️ Spreading factor** trades range against airtime — ⚠️ **and higher SF means much longer
transmissions, which consumes duty-cycle allowance and capacity fast.**
**⚠️ Device classes**: ⚠️ **A (uplink-initiated, lowest power), B (scheduled receive slots),
C (continuous receive, mains power).**
**⚠️ Deployment models**: ⚠️ **private gateway versus public network versus roaming — and
the honest question for any LPWAN project is who owns and maintains the gateways.**
**⚠️ The alternatives**: ⚠️ **Sigfox, Wi-Fi HaLow (802.11ah), Amazon Sidewalk, and
cellular NB-IoT/LTE-M** (§13).

---

## §13. Cellular and Cellular IoT

**⚠️ The generations**: ⚠️ **and note 2G/3G SUNSET has stranded a great deal of deployed
telemetry — a live lesson about designing hardware around a network you don't control.**
**⚠️ 5G's three service classes** are the useful framing: ⚠️ **eMBB (bandwidth), URLLC
(latency and reliability), mMTC (device density) — and no deployment delivers all three at
once.**
**⚠️ mmWave versus sub-6 GHz** is §2 → `wireless-propagation-link-budget-modulation-antennas-and-spectrum`'s physics again: ⚠️ **enormous bandwidth, terrible
propagation and building penetration, which is why mmWave coverage is patchy and sub-6 does
the real work.**
**⚠️ For IoT specifically**: ⚠️ **NB-IoT (deep indoor penetration, tiny data) and LTE-M
(more bandwidth, mobility, VoLTE) — with PSM and eDRX as the power-saving mechanisms that
make multi-year battery life possible on a cellular radio.**
**⚠️ Practical concerns**: ⚠️ **eSIM/iSIM provisioning, roaming agreements and permanent
roaming restrictions, module certification against carrier requirements (⚠️ which is
separate from and additional to regulatory certification, §18 → `wireless-antenna-integration-certification-low-power-and-debugging`), and network sunset risk.**

---

## §14. UWB

**⚠️ Ultra-wideband** transmits extremely short pulses across very wide bandwidth at very
low power spectral density.
**⚠️ Why it is good at ranging**: ⚠️ **time-of-flight resolution scales with BANDWIDTH, and
UWB has a great deal of it — giving roughly 10 cm accuracy — plus the short pulse makes
multipath separable rather than confusing.**
**⚠️ The security property is the important one**: ⚠️ **cryptographically timed
DISTANCE BOUNDING resists relay attacks in a way RSSI-based proximity fundamentally cannot**
(§22 → `wireless-security-coexistence-and-positioning`, §24 → `wireless-security-coexistence-and-positioning`).
**⚠️ Standards**: ⚠️ **802.15.4z, with FiRa and CCC (Car Connectivity Consortium) driving
interoperability for digital car keys.**
**⚠️ The cost**: ⚠️ **dedicated hardware and meaningfully higher power than BLE — which is
exactly the pressure that produced Bluetooth Channel Sounding** (§25.2 → `wireless-reference`).

---

## §15. Other Technologies Worth Knowing

**⚠️ Wi-Fi HaLow (802.11ah)** — ⚠️ **sub-GHz Wi-Fi, kilometre range, IP-native, low rate;
technically attractive and adoption has been slow.**
**⚠️ 60 GHz (802.11ad/ay, WiGig)** — ⚠️ **multi-gigabit at room scale, blocked by a hand.**
**⚠️ Satellite**: ⚠️ **LEO constellations, and direct-to-device messaging now appearing in
phones — with latency and link budget both governed by §2 → `wireless-propagation-link-budget-modulation-antennas-and-spectrum`.**
**⚠️ Infrared** — ⚠️ **still ubiquitous in remotes, line-of-sight, no spectrum regulation.**
**⚠️ Wireless power (Qi)** — ⚠️ **inductive coupling like NFC (§10 → `wireless-wifi-bluetooth-ble-nfc-and-rfid`), with alignment and
foreign-object detection as the engineering problems.**
**⚠️ Wired alternatives worth remembering**: ⚠️ **Ethernet and PoE solve many "IoT"
problems better than any radio, and powerline and MoCA exist — the best wireless decision
is sometimes not to.**

---

# PART III — BUILDING WIRELESS PRODUCTS

## §16. Choosing a Radio

```
⚠️ THE DECISION ORDER — ⚠️ answer these before picking a chip
   ⚠️ 1. RANGE and environment · 2. DATA RATE and duty cycle ·
   ⚠️ 3. POWER SOURCE — battery life target is the harshest
      constraint and drives everything (§19)
   ⚠️ 4. Latency requirement · 5. Number of nodes and topology ·
   ⚠️ 6. What must it talk TO? (⚠️ if a phone must connect
      directly, that means BLE or Wi-Fi, full stop)
   ⚠️ 7. Infrastructure — does a gateway exist? · 8. Regions to sell
⚠️ MODULE vs CHIP-DOWN
   ⚠️ PRE-CERTIFIED MODULE  ⚠️ dramatically cheaper and faster for
      low and medium volume, because it carries modular
      certification (§18). ⚠️ Higher unit cost
   ⚠️ CHIP-DOWN  cheapest at volume, ⚠️ full certification burden
      and RF layout expertise required
   ⚠️ ⚠️ FOR MOST PROJECTS, USE A MODULE. The certification saving
      alone usually exceeds the unit-cost penalty
⚠️ ECOSYSTEM MATTERS AS MUCH AS SILICON  ⚠️ SDK quality,
   documentation, stack maturity, long-term availability, and
   whether you can get support
```
