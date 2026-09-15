---
name: wireless-wifi-bluetooth-ble-nfc-and-rfid
description: "Use for the short-range standards: Wi-Fi and its generations, Wi-Fi in practice including channel planning, roaming and the throughput you actually get, Bluetooth and its profiles, BLE programming with GATT, advertising, connection intervals and the throughput reality, and NFC and RFID across their frequency bands and use cases."
---

# Wireless Technologies and RF: Wi-Fi, Wi-Fi in Practice, Bluetooth, BLE Programming, and NFC and RFID

> **Part 2 of 6** of the *Wireless Technologies: RF, Standards, Building and Programming* reference (plugin `wireless-technologies-and-rf-engineering`), covering §6–§10. Sibling skills: `wireless-propagation-link-budget-modulation-antennas-and-spectrum` (§0–§5), `wireless-thread-matter-lora-cellular-uwb-and-choosing` (§11–§16), `wireless-antenna-integration-certification-low-power-and-debugging` (§17–§21), `wireless-security-coexistence-and-positioning` (§22–§24), `wireless-reference` (§25–§30). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The physics is permanent and the mature standards are stable. Two areas are moving. See §25 → `wireless-reference` for Wi-Fi's next generation, and Bluetooth ranging.

> **⚠️ The domain where physics imposes limits that no amount of software cleverness
> removes — and where nearly every practical problem turns out to be either a link budget
> problem, an antenna problem, or a coexistence problem.**
>
> **Builds on an electromagnetism reference (fields, propagation, transmission lines) and
> complements a peripherals reference (§5's wireless HID), a computer-hardware reference
> (§9 networking), and a cryptography reference (WPA3, pairing, key exchange).**
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

## §6. Wi-Fi

```
⚠️ THE GENERATIONS  ⚠️ and note the naming was retrofitted —
   802.11n became "Wi-Fi 4" years later
   ⚠️ 802.11n / Wi-Fi 4  MIMO, 2.4 and 5 GHz
   ⚠️ 802.11ac / Wi-Fi 5  5 GHz only, wider channels, MU-MIMO down
   ⚠️ 802.11ax / Wi-Fi 6  ⚠️ OFDMA, TWT (target wake time — real
      battery benefit for IoT), BSS colouring, 1024-QAM.
      ⚠️ 6E adds the 6 GHz band
   ⚠️ 802.11be / Wi-Fi 7  ⚠️ 320 MHz channels, 4096-QAM, and
      ⚠️ MULTI-LINK OPERATION — a device using 2.4, 5 and 6 GHz
      SIMULTANEOUSLY, which is the genuinely new idea
   ⚠️ 802.11bn / Wi-Fi 8  §25.1
⚠️ ⚠️ WIDER CHANNELS ARE NOT FREE  ⚠️ a 320 MHz channel has a
   HIGHER NOISE FLOOR than a 20 MHz one and fewer non-overlapping
   channels exist. ⚠️ In dense environments NARROWER channels
   frequently outperform wider ones — the opposite of the
   marketing
⚠️ THE MAC  CSMA/CA, DCF, airtime fairness (⚠️ or its absence —
   a slow legacy client can consume airtime disproportionately)
⚠️ ⚠️ 2.4 GHz HAS ONLY THREE NON-OVERLAPPING 20 MHz CHANNELS
   (1, 6, 11 in most regions). ⚠️ Using anything else makes
   things worse for everyone, including you
⚠️ ROAMING  802.11k/v/r — ⚠️ and note the CLIENT decides when to
   roam, not the AP, which is why "sticky client" problems are
   hard to fix from the infrastructure side
⚠️ SECURITY  WPA2 → ⚠️ WPA3 (SAE replacing PSK, forward secrecy,
   ⚠️ and OWE for open networks) · 802.1X/EAP for enterprise (§22)
```

---

## §7. Wi-Fi in Practice

**⚠️ Design for the WORST client, not the best** — ⚠️ **a network engineered around a
laptop's radio will fail for a battery-powered sensor with a chip antenna.**
**⚠️ Site survey**: ⚠️ **predictive modelling, then passive and active survey, then
post-deployment validation — ⚠️ and validate with the actual client devices, because
different radios see different coverage.**
**⚠️ Coverage versus CAPACITY** is the design distinction people miss: ⚠️ **in dense
deployments you deliberately LOWER AP power and use narrower channels to create smaller
cells, because more APs at lower power beats fewer at high power.**
**⚠️ The recurring real-world faults**: ⚠️ **co-channel interference from too much power,
hidden nodes, sticky clients, DFS radar events dropping a channel, 2.4 GHz congestion, and
mounting APs above ceiling tiles or in metal enclosures.**
> **⚠️ GOTCHA — "more signal" is usually the wrong fix.** ⚠️ **A client that hears the AP
> fine but whose weak transmitter cannot be heard back has an ASYMMETRIC link, and turning
> AP power up makes it worse by extending the cell without extending the return path.**

---

## §8. ⚠️ Bluetooth

```
⚠️ ⚠️ TWO DIFFERENT TECHNOLOGIES SHARING A NAME
   ⚠️ BR/EDR ("Classic")  ⚠️ connection-oriented, streaming,
      audio, higher power. ⚠️ 79 channels, 1 MHz, FHSS
   ⚠️ LE (Low Energy)  ⚠️ COMPLETELY DIFFERENT radio and protocol
      stack. ⚠️ 40 channels, 2 MHz, designed around short bursts
      and long sleep. ⚠️ Introduced in 4.0 (2010) — it is not new
⚠️ THE LE STACK  PHY → Link Layer → HCI → L2CAP → ⚠️ ATT → GATT
   → application (§9) · SMP for pairing (§22) · GAP for roles
⚠️ ROLES  ⚠️ advertiser/scanner, then central/peripheral —
   ⚠️ and these are independent of client/server at the GATT layer,
   which confuses newcomers constantly
⚠️ KEY LE FEATURES BY VERSION
   ⚠️ 4.2 privacy and longer packets · ⚠️ 5.0 2M PHY (double rate)
      and CODED PHY (⚠️ long range via FEC, at lower rate) ·
      5.1 direction finding (AoA/AoD) · ⚠️ 5.2 LE AUDIO and the
      LC3 codec · ⚠️ 5.4 PAwR — ⚠️ the protocol that enables
      Auracast · ⚠️ 6.0 Channel Sounding (§25.2)
⚠️ ⚠️ LE AUDIO IS NOT A VERSION NUMBER. ⚠️ The SIG now encourages
   advertising "supports LE Audio" or "supports Auracast" rather
   than a core version, because features and versions decoupled
⚠️ AURACAST  ⚠️ broadcast audio — one source to unlimited
   receivers. ⚠️ Genuinely transformative for hearing aids and
   public venues, and REQUIRES PAwR, so 5.3 and earlier cannot
   participate
⚠️ THE PRACTICAL PARAMETERS  ⚠️ CONNECTION INTERVAL and slave
   latency dominate both latency AND battery life (§19); MTU
   size dominates throughput
```

---

## §9. ⚠️ BLE Programming

> **⚠️ The most commonly built wireless application, and the model repays understanding.**
```
⚠️ ⚠️ GATT IS A DATABASE  ⚠️ the peripheral exposes SERVICES,
   each containing CHARACTERISTICS, each with a VALUE and
   DESCRIPTORS. ⚠️ The central reads, writes, or subscribes
⚠️ UUIDs  ⚠️ 16-bit for SIG-adopted services, 128-bit for custom.
   ⚠️ Use adopted services where one exists — heart rate, battery,
   device information — because generic apps will understand them
⚠️ THE OPERATIONS  ⚠️ read · write · WRITE WITHOUT RESPONSE
   (faster, unacknowledged) · ⚠️ NOTIFY (unacknowledged push) ·
   ⚠️ INDICATE (acknowledged push, slower)
   ⚠️ Polling by repeated read is the classic beginner mistake —
   SUBSCRIBE instead
⚠️ ADVERTISING  ⚠️ 31 bytes in a legacy advertising packet, plus
   a scan response. ⚠️ That tight budget shapes beacon design ·
   extended advertising lifts it substantially
⚠️ ⚠️ THROUGHPUT IS GOVERNED BY connection interval, packets per
   interval, MTU and PHY — ⚠️ NOT by the advertised "2 Mbps",
   which is a raw PHY rate. ⚠️ Real application throughput is a
   fraction of it
⚠️ THE STACKS  ⚠️ Zephyr · Nordic nRF Connect SDK · ESP-IDF ·
   Arduino/CircuitPython for prototyping · BlueZ on Linux ·
   ⚠️ Web Bluetooth for browser-based tools
⚠️ DEBUGGING  ⚠️ nRF Connect mobile app for inspecting a GATT
   server · ⚠️ SNIFFERS (nRF Sniffer, Ubertooth) — and a sniffer
   is close to essential for connection-level problems
```

---

## §10. ⚠️ NFC and RFID

```
⚠️ ⚠️ NFC IS NOT RADIO IN THE USUAL SENSE. ⚠️ At 13.56 MHz over
   centimetres you are in the NEAR FIELD — this is INDUCTIVE
   COUPLING, essentially a loosely coupled transformer, not
   propagating waves. ⚠️ Field strength falls off far faster than
   1/r², which is precisely what makes it short-range BY PHYSICS
   rather than by power limit
⚠️ ⚠️ PASSIVE TAGS HAVE NO BATTERY — ⚠️ the reader's field powers
   them, and the tag replies by LOAD MODULATION (changing its
   own impedance so the reader sees the change). Elegant, and
   the reason tags cost cents
⚠️ THE STANDARDS  ⚠️ ISO 14443 (A/B — the payment and access
   card standard) · ISO 15693 (vicinity, longer range) ·
   FeliCa · ⚠️ NFC Forum tag types 1-5 and NDEF as the data format
⚠️ NFC MODES  ⚠️ reader/writer · card emulation (⚠️ HCE — how
   phone payments work) · peer-to-peer (largely deprecated)
⚠️ RFID BY FREQUENCY  ⚠️ LF 125 kHz (short, penetrates water and
   tissue — animal tags) · HF 13.56 MHz · ⚠️ UHF 860-960 MHz
   (⚠️ FAR FIELD backscatter, metres of range, bulk inventory
   reading — and REGION-SPECIFIC frequencies, §5)
⚠️ ⚠️ THE PRACTICAL FAILURE MODES  ⚠️ METAL DETUNES AND SHIELDS —
   a tag on metal needs an on-metal design with a spacer ·
   ⚠️ multiple cards in a wallet collide · antenna size sets range
   more than power does
⚠️ SECURITY  ⚠️ MIFARE Classic's Crypto1 is thoroughly broken and
   still widely deployed · ⚠️ relay attacks are the structural
   weakness of proximity-implies-presence (§22, §24)
```
