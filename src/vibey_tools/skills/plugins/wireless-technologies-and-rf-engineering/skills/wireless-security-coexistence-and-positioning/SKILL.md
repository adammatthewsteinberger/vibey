---
name: wireless-security-coexistence-and-positioning
description: "Use for the cross-cutting problems: wireless security including pairing, key provisioning, the standard-specific weaknesses and what encryption does not protect, coexistence in shared bands and the interference between collocated radios, and positioning and sensing from RSSI and time-of-flight ranging to channel-state sensing."
---

# Wireless Technologies and RF: Wireless Security, Coexistence, and Positioning and Sensing

> **Part 5 of 6** of the *Wireless Technologies: RF, Standards, Building and Programming* reference (plugin `wireless-technologies-and-rf-engineering`), covering §22–§24. Sibling skills: `wireless-propagation-link-budget-modulation-antennas-and-spectrum` (§0–§5), `wireless-wifi-bluetooth-ble-nfc-and-rfid` (§6–§10), `wireless-thread-matter-lora-cellular-uwb-and-choosing` (§11–§16), `wireless-antenna-integration-certification-low-power-and-debugging` (§17–§21), `wireless-reference` (§25–§30). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 2. **⚠️ SPECTRUM IS A SHARED, CONTESTED, REGULATED RESOURCE** (§5 → `wireless-propagation-link-budget-modulation-antennas-and-spectrum`, §23). **You do not own
>    your channel. Unlicensed bands mean your neighbours, your own other radios, and
>    physically unrelated devices all degrade you — and coexistence design is not optional.**
> 3. **⚠️ THE ANTENNA IS THE MOST NEGLECTED COMPONENT AND THE MOST DECISIVE** (§4 → `wireless-propagation-link-budget-modulation-antennas-and-spectrum`, §17 → `wireless-antenna-integration-certification-low-power-and-debugging`).
>    **A superb radio with a badly integrated antenna performs worse than a mediocre radio
>    with a good one, and antenna problems are usually designed in months before anyone
>    measures them.**

---

## §22. ⚠️ Wireless Security

```
⚠️ ⚠️ THE STRUCTURAL FACT: THERE IS NO PHYSICAL BOUNDARY. ⚠️ An
   attacker need not touch anything. Encryption is not optional
⚠️ WI-FI  ⚠️ WEP broken · WPA2 (⚠️ KRACK, and offline dictionary
   attack on captured handshakes with weak PSKs) → ⚠️ WPA3 with
   SAE, which resists offline attack and gives forward secrecy ·
   ⚠️ OWE encrypts OPEN networks (huge for public Wi-Fi) ·
   ⚠️ 802.1X/EAP for enterprise — ⚠️ and CERTIFICATE VALIDATION
   ON THE CLIENT is the step most often skipped, enabling evil
   twin attacks
⚠️ BLUETOOTH  ⚠️ pairing methods matter: ⚠️ "Just Works" gives NO
   MITM protection · passkey and numeric comparison do ·
   ⚠️ LE Secure Connections (4.2+) uses ECDH — legacy pairing
   does not and is broken. ⚠️ Known attack families: BlueBorne,
   KNOB (key negotiation downgrade), BIAS, and repeated pairing
   flaws
⚠️ ⚠️ RELAY ATTACKS are the deep problem for proximity-implies-
   authorization systems (cars, access control). ⚠️ Signal
   strength CANNOT defend against a relay — only cryptographic
   DISTANCE BOUNDING can (§14, §24, §25.2)
⚠️ NFC/RFID  ⚠️ cloning of weak tags, relay, and skimming (§10)
⚠️ IoT-SPECIFIC FAILINGS  ⚠️ hardcoded and shared keys ·
   unauthenticated firmware update · no key rotation ·
   ⚠️ debug interfaces left enabled in production · secrets
   readable from flash
⚠️ TRAFFIC ANALYSIS AND PRIVACY  ⚠️ MAC randomization exists
   because MAC addresses enabled physical tracking; ⚠️ BLE
   resolvable private addresses do the same, ⚠️ and static
   identifiers in advertising payloads defeat both
```

---

## §23. ⚠️ Coexistence

> **⚠️ §1 → `wireless-propagation-link-budget-modulation-antennas-and-spectrum`'s second organizing idea. You share the band, and the interferers are often your
> own.**
```
⚠️ SAME-BAND NEIGHBOURS  ⚠️ 2.4 GHz holds Wi-Fi, Bluetooth,
   Zigbee, Thread, proprietary remotes, wireless mice, video
   senders — ⚠️ and MICROWAVE OVENS, which are genuinely
   disruptive and periodic
⚠️ ⚠️ IN-DEVICE COEXISTENCE IS THE HARDER PROBLEM  ⚠️ Wi-Fi and
   Bluetooth radios centimetres apart on the same board, often
   sharing an antenna. ⚠️ PTA (packet traffic arbitration) and
   time-division coexistence schemes exist for exactly this,
   and combo chips handle it internally
⚠️ ⚠️ USB 3 RADIATES BROADBAND NOISE AROUND 2.4 GHz. ⚠️ This is a
   documented, real effect that desensitizes nearby receivers —
   ⚠️ move the dongle or use a short extension cable. It is the
   most common "my wireless mouse is broken" cause
⚠️ OTHER SELF-INTERFERENCE  ⚠️ switching regulator harmonics ·
   display and camera clocks · unshielded high-speed buses
⚠️ MITIGATIONS  ⚠️ frequency planning · adaptive frequency
   hopping (⚠️ Bluetooth's AFH actively avoids busy channels) ·
   antenna separation and isolation · filtering · shielding ·
   time-division scheduling · ⚠️ and simply choosing a
   different band
⚠️ ⚠️ REGULATORY COEXISTENCE IS ALSO CONTESTED  ⚠️ 6 GHz
   allocation, and the interests of incumbent licensed users
   versus unlicensed expansion, are an active policy fight —
   which is worth knowing because it determines what spectrum
   your product may use in a few years
```

---

## §24. Positioning and Sensing

**⚠️ The techniques, in ascending order of accuracy and cost**:
⚠️ **RSSI trilateration (⚠️ crude — signal strength is a terrible distance proxy because
of multipath and obstruction, and this is why "proximity" beacons are so unreliable);
⚠️ FINGERPRINTING against a survey map; ⚠️ AoA/AoD requiring antenna arrays;
⚠️ TIME OF FLIGHT and TDoA, which is what UWB does well (§14 → `wireless-thread-matter-lora-cellular-uwb-and-choosing`) and now Bluetooth Channel
Sounding (§25.2 → `wireless-reference`); ⚠️ and GNSS outdoors, with RTK for centimetre accuracy.**
**⚠️ RF SENSING** is a rapidly growing use: ⚠️ **detecting presence, motion, breathing and
gestures from CHANNEL STATE INFORMATION perturbations — ⚠️ and Wi-Fi Sensing (802.11bf)
standardizes it.**
> **⚠️ GOTCHA — RF sensing is a privacy problem, not just a feature.** ⚠️ **A network that
> can detect breathing through walls is doing surveillance regardless of intent, and this
> is an area where the capability is arriving well ahead of the norms.**
