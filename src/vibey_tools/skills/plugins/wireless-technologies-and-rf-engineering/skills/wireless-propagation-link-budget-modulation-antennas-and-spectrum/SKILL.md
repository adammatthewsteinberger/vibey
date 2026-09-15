---
name: wireless-propagation-link-budget-modulation-antennas-and-spectrum
description: "Use for the physics and rules that constrain every wireless design: why wireless breaks the assumptions wired systems allow, propagation and the link budget as the calculation that answers most range questions, modulation and multiple access, antennas including gain, pattern and matching, and spectrum and the regulatory limits on power and duty cycle. Includes the router for the whole wireless technologies reference."
---

# Wireless Technologies and RF: Why Wireless Is Hard, Propagation and the Link Budget, Modulation and Multiple Access, Antennas, and Spectrum and Regulation

> **Part 1 of 6** of the *Wireless Technologies: RF, Standards, Building and Programming* reference (plugin `wireless-technologies-and-rf-engineering`), covering §0–§5. Sibling skills: `wireless-wifi-bluetooth-ble-nfc-and-rfid` (§6–§10), `wireless-thread-matter-lora-cellular-uwb-and-choosing` (§11–§16), `wireless-antenna-integration-certification-low-power-and-debugging` (§17–§21), `wireless-security-coexistence-and-positioning` (§22–§24), `wireless-reference` (§25–§30). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 1. **⚠️ THE LINK BUDGET IS THE WHOLE GAME** (§2). **Transmit power, antenna gains, path
>    loss and receiver sensitivity determine whether a link works. Everything else is
>    optimization within that envelope, and "add more power" is almost never the available
>    lever because regulation caps it.**
> 2. **⚠️ SPECTRUM IS A SHARED, CONTESTED, REGULATED RESOURCE** (§5, §23 → `wireless-security-coexistence-and-positioning`). **You do not own
>    your channel. Unlicensed bands mean your neighbours, your own other radios, and
>    physically unrelated devices all degrade you — and coexistence design is not optional.**
> 3. **⚠️ THE ANTENNA IS THE MOST NEGLECTED COMPONENT AND THE MOST DECISIVE** (§4, §17 → `wireless-antenna-integration-certification-low-power-and-debugging`).
>    **A superb radio with a badly integrated antenna performs worse than a mediocre radio
>    with a good one, and antenna problems are usually designed in months before anyone
>    measures them.**

---

## §0. Routing

| You want... | Go to |
|---|---|
| Why wireless is hard | §1 |
| **⚠️ Propagation and link budget** | **§2** |
| Modulation and access | §3 |
| **⚠️ Antennas** | **§4** |
| **⚠️ Spectrum and regulation** | **§5** |
| **Wi-Fi standards** | **§6 → `wireless-wifi-bluetooth-ble-nfc-and-rfid`** |
| Wi-Fi deployment | §7 → `wireless-wifi-bluetooth-ble-nfc-and-rfid` |
| **⚠️ Bluetooth** | **§8 → `wireless-wifi-bluetooth-ble-nfc-and-rfid`** |
| **⚠️ BLE programming** | **§9 → `wireless-wifi-bluetooth-ble-nfc-and-rfid`** |
| **⚠️ NFC and RFID** | **§10 → `wireless-wifi-bluetooth-ble-nfc-and-rfid`** |
| Thread, Zigbee, Matter | §11 → `wireless-thread-matter-lora-cellular-uwb-and-choosing` |
| LoRa and LPWAN | §12 → `wireless-thread-matter-lora-cellular-uwb-and-choosing` |
| Cellular and IoT | §13 → `wireless-thread-matter-lora-cellular-uwb-and-choosing` |
| UWB | §14 → `wireless-thread-matter-lora-cellular-uwb-and-choosing` |
| Other technologies | §15 → `wireless-thread-matter-lora-cellular-uwb-and-choosing` |
| **Choosing a radio** | **§16 → `wireless-thread-matter-lora-cellular-uwb-and-choosing`** |
| **⚠️ Antenna integration** | **§17 → `wireless-antenna-integration-certification-low-power-and-debugging`** |
| **⚠️ Certification** | **§18 → `wireless-antenna-integration-certification-low-power-and-debugging`** |
| Low-power design | §19 → `wireless-antenna-integration-certification-low-power-and-debugging` |
| Provisioning | §20 → `wireless-antenna-integration-certification-low-power-and-debugging` |
| **⚠️ RF debugging** | **§21 → `wireless-antenna-integration-certification-low-power-and-debugging`** |
| **⚠️ Security** | **§22 → `wireless-security-coexistence-and-positioning`** |
| **⚠️ Coexistence** | **§23 → `wireless-security-coexistence-and-positioning`** |
| Positioning and sensing | §24 → `wireless-security-coexistence-and-positioning` |
| **What's live** | **§25 → `wireless-reference`** |
| Misconceptions, numbers | §26–§27 → `wireless-reference` |
| Sources, quick ref, method | §28–§30 → `wireless-reference` |

---

## §1. Why Wireless Is Hard

```
⚠️ WHAT YOU GIVE UP versus a wire
   ⚠️ A SHARED medium — ⚠️ half duplex in practice for most
      technologies, with contention and collisions
   ⚠️ UNPREDICTABLE and TIME-VARYING channel
   ⚠️ NO physical security boundary (§22)
   ⚠️ REGULATED transmit power (§5)
   ⚠️ Interference from things you don't control (§23)
⚠️ WHAT YOU GAIN  mobility, no cabling cost, deployment speed,
   and reach into places wires cannot go
⚠️ ⚠️ THE PERSISTENT ILLUSION: that advertised data rates describe
   what you will get. ⚠️ Wi-Fi's PHY rate is a peak, shared,
   half-duplex, before overhead, at the best modulation — real
   throughput is commonly a third to a half of it, and far less
   under load or at range
⚠️ THE HIERARCHY OF FIXES, in order of effectiveness
   ⚠️ 1. MOVE THE ANTENNA (§4, §17) · 2. reduce the distance or
   obstruction · 3. change frequency or channel (§23) ·
   ⚠️ 4. change modulation/data rate · 5. only then, more power
```

---

# PART I — RF FUNDAMENTALS

## §2. ⚠️ Propagation and the Link Budget

> **⚠️ If you learn one thing here, learn this. It predicts more than any amount of
> protocol knowledge.**
```
⚠️ THE BUDGET  ⚠️ Received power (dBm) = TX power + TX antenna gain
   − path loss − losses + RX antenna gain
   ⚠️ LINK MARGIN = received power − receiver sensitivity.
   ⚠️ You want meaningful margin, not a bare pass
⚠️ ⚠️ dB THINKING  ⚠️ +3 dB doubles power · +10 dB is 10× ·
   ⚠️ −3 dB halves it. ⚠️ dBm is absolute (0 dBm = 1 mW), dB and
   dBi are ratios. ⚠️ Confusing them is the classic beginner error
⚠️ FREE SPACE PATH LOSS  ⚠️ rises with the SQUARE of distance AND
   the SQUARE of frequency. ⚠️ Doubling distance costs 6 dB
   ⚠️ THIS IS WHY 2.4 GHz REACHES FURTHER THAN 5 GHz, which
   reaches further than 6 GHz — ⚠️ pure physics, not
   implementation quality
⚠️ REAL ENVIRONMENTS ARE WORSE  ⚠️ path loss exponent in buildings
   is well above the free-space value
   ⚠️ ABSORPTION  ⚠️ WATER absorbs 2.4 GHz strongly — which is why
      human bodies, aquariums and foliage are real obstacles, and
      why body-worn devices behave differently on-body
   ⚠️ REFLECTION and MULTIPATH  ⚠️ copies arriving at different
      times cause FADING — and multipath can be destructive
      enough that moving 20 cm fixes a "broken" link
   ⚠️ DIFFRACTION and the Fresnel zone · penetration losses
      (⚠️ concrete, metal, low-E glass and foil insulation are
      severe; ⚠️ modern energy-efficient windows can be near
      RF-opaque, which surprises people)
⚠️ FADING  ⚠️ slow (shadowing) vs FAST (multipath) · Rayleigh vs
   Rician. ⚠️ Diversity and MIMO exist to exploit this rather
   than fight it
⚠️ NOISE FLOOR and SNR  ⚠️ sensitivity improves as data rate falls
   — ⚠️ which is why every technology has a rate-versus-range
   curve and drops rate automatically at the edge
```

---

## §3. Modulation and Multiple Access

```
⚠️ MODULATION  ⚠️ ASK/FSK/PSK → QAM. ⚠️ Higher-order QAM packs
   more bits per symbol and DEMANDS higher SNR — ⚠️ this is the
   rate/range trade, made concrete
⚠️ SPREAD SPECTRUM  ⚠️ FHSS (⚠️ Bluetooth — hop away from
   interference) · DSSS · ⚠️ CSS (LoRa's chirp spread spectrum,
   which is why it decodes BELOW the noise floor, §12)
⚠️ ⚠️ OFDM  ⚠️ split the channel into many narrow orthogonal
   subcarriers. ⚠️ A narrow subcarrier sees a FLAT channel, which
   makes equalization tractable and multipath survivable —
   ⚠️ this is the enabling idea behind modern Wi-Fi, LTE and
   5G alike
⚠️ ⚠️ OFDMA  ⚠️ allocate DIFFERENT subcarriers to different users
   in the same transmission. ⚠️ The key Wi-Fi 6 change, and it
   helps DENSITY and small packets rather than peak speed
⚠️ MULTIPLE ACCESS  ⚠️ CSMA/CA with backoff (Wi-Fi — ⚠️ note it
   CANNOT detect collisions like Ethernet, only avoid them,
   hence RTS/CTS and the HIDDEN NODE problem) · TDMA · FDMA ·
   CDMA · polling
⚠️ MIMO  ⚠️ spatial multiplexing (⚠️ independent streams, needs
   RICH MULTIPATH to work — ⚠️ counter-intuitively, a clean
   line-of-sight channel gives WORSE MIMO gain) · beamforming ·
   diversity · MU-MIMO
⚠️ ERROR CONTROL  FEC, interleaving, ARQ and hybrid ARQ
```

---

## §4. ⚠️ Antennas

**⚠️ See an electromagnetism reference for the field theory. Here, what matters in
practice.**
```
⚠️ THE KEY PARAMETERS
   ⚠️ GAIN is NOT amplification — ⚠️ it is DIRECTIONALITY. An
      antenna is passive; gain in one direction is loss in
      another. ⚠️ dBi vs dBd (2.15 dB apart)
   ⚠️ RADIATION PATTERN  ⚠️ and a high-gain omni antenna gets its
      gain by SQUASHING the pattern vertically — which is why it
      can perform WORSE for a device above or below it
   ⚠️ POLARIZATION  ⚠️ cross-polarization loss is severe. ⚠️ A
      vertical and a horizontal antenna couple poorly, which is
      part of why phone orientation changes signal
   ⚠️ IMPEDANCE MATCH, VSWR, RETURN LOSS  ⚠️ a mismatched antenna
      reflects power back rather than radiating it
   ⚠️ BANDWIDTH and EFFICIENCY
⚠️ TYPES  ⚠️ monopole/whip · dipole · ⚠️ PCB TRACE (cheap, and
   utterly dependent on ground plane and clearance, §17) ·
   ⚠️ CHIP antennas (small, low efficiency, need a matching
   network) · patch · Yagi · parabolic · slot
⚠️ ⚠️ THE GROUND PLANE IS PART OF THE ANTENNA. ⚠️ A quarter-wave
   monopole needs a ground plane to work at all — and on a small
   product, the PCB ground plane IS the other half of the
   antenna. ⚠️ Shrinking the board changes the antenna
⚠️ THE FUNDAMENTAL LIMIT  ⚠️ small antennas are inherently
   narrowband and inefficient (Chu-Harrington). ⚠️ You cannot
   design your way out of this — physics caps it
```

---

## §5. ⚠️ Spectrum and Regulation

```
⚠️ WHO DECIDES  ⚠️ ITU allocates regionally · national regulators
   (FCC, Ofcom, ETSI/CEPT in Europe, and equivalents) set the
   rules you must actually meet
⚠️ ⚠️ LICENSED vs UNLICENSED IS THE DEFINING SPLIT
   ⚠️ LICENSED (cellular)  exclusive use, protected from
      interference, expensive, auctioned
   ⚠️ UNLICENSED / ISM  ⚠️ free to use, NO protection from
      interference, ⚠️ and you must ACCEPT interference from
      others. This asymmetry is the whole of §23
⚠️ THE BANDS THAT MATTER
   ⚠️ 2.4 GHz  ⚠️ global, crowded, better propagation
   ⚠️ 5 GHz  more spectrum, ⚠️ DFS requirements (radar detection —
      ⚠️ and a false radar detection kicks everyone off a channel)
   ⚠️ 6 GHz  ⚠️ newest and largest, ⚠️ AVAILABILITY VARIES BY
      COUNTRY, with power limits (LPI, VLP, standard power/AFC)
   ⚠️ Sub-GHz (868/915 MHz)  ⚠️ REGION-SPECIFIC — a 915 MHz
      device is illegal in Europe. ⚠️ This catches product
      designers constantly
   ⚠️ 60 GHz, UWB (6.5-8 GHz), NFC (13.56 MHz)
⚠️ THE LIMITS YOU DESIGN AGAINST  ⚠️ EIRP caps · duty cycle limits
   (⚠️ severe in EU sub-GHz — 1% duty cycle is common and
   constrains protocol design) · listen-before-talk · channel
   dwell time · spurious emission masks
⚠️ ⚠️ SAR limits for body-worn and handheld devices
```

---

# PART II — THE STANDARDS
