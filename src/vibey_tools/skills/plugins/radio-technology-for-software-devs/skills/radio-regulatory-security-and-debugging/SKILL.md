---
name: radio-regulatory-security-and-debugging
description: "Use when shipping a radio product or diagnosing a field problem: the regulatory layer including power limits, duty cycles, certification and why the rules differ by region, what moved in Wi-Fi and the 6 GHz status and in IoT connectivity after the 2G and 3G sunset, wireless security including the attack surface specific to radio, and how to debug an RF problem from the software side when you cannot see the spectrum."
---

# Radio Technology: The Regulatory Layer, What Moved, Security, and Debugging RF From Software

> **Part 5 of 6** of the *Radio Technology for Software Developers* reference (plugin `radio-technology-for-software-devs`), covering §23–§26. Sibling skills: `radio-intuitions-spectrum-link-budget-and-tradeoffs` (§0–§4), `radio-antennas-propagation-noise-and-modulation` (§5–§9), `radio-spread-spectrum-ofdm-access-and-sdr` (§10–§16), `radio-protocol-stacks-wifi-ble-lpwan-and-gnss` (§17–§22), `radio-reference` (§27–§32). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** RF physics and DSP are permanent. Two areas moved. See §24 below for Wi-Fi 7 and 8 and the 6 GHz regulatory status, and the IoT connectivity landscape after the 2G and 3G sunset.

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
>    (§4 → `radio-intuitions-spectrum-link-budget-and-tradeoffs`, §19 → `radio-protocol-stacks-wifi-ble-lpwan-and-gnss`), **and you cannot fix a bad choice in firmware.**

---

## §23. ⚠️ Regulatory

> **⚠️ GOTCHA — this is where software people get their companies in real trouble.**
> ⚠️ **Transmitting is REGULATED. Power limits, duty cycle, band edges and spurious
> emissions are legal requirements, not guidelines** — **and a product that fails
> certification is a product you cannot sell.**

```
ISM BANDS   ⚠️ 433/868 MHz (EU), 915 MHz (US), 2.4 GHz (global), 5 GHz, 6 GHz
   ⚠️ Sub-GHz allocations DIFFER BY REGION — 868 EU vs 915 US is why LoRa
   modules are region-specific and why a design doesn't ship globally unchanged
⚠️ DUTY CYCLE  EU sub-GHz typically limits you to ~1% airtime per hour in
   many sub-bands. ⚠️ This is a HARD design constraint that determines how
   often you can send and interacts brutally with high LoRa spreading factors
POWER LIMITS   ⚠️ EIRP/ERP caps, and antenna gain counts toward them
LISTEN BEFORE TALK · DFS (⚠️ 5 GHz radar avoidance — the AP must vacate a
   channel, which looks like a random outage to your application)
CERTIFICATION  ⚠️ FCC (US) · CE/RED (EU) · UKCA · plus per-country. Pre-certified
   modules transfer most of this burden and are usually the right call
```
**⚠️ Practical advice**: **use a pre-certified module unless you have RF engineers and
volume to justify otherwise**; **plan for regional SKUs from day one if you're using
sub-GHz**; ⚠️ **never ship firmware that lets a user set arbitrary TX power or frequency**;
and **budget for pre-compliance testing before design freeze, not after.**

---

## §24. What Moved — verified August 2026

### 24.1 ⚠️ Wi-Fi 7, 6 GHz, and the Wi-Fi 8 question
**⚠️ Wi-Fi 7 is real and shipping; the interesting facts are about regulation and about
whether it's worth deploying.**

- **⚠️ Wi-Fi Alliance certification began January 2024; as of 2026 enterprise APs are
  widely available and consumer routers start under $100.**
- **⚠️ MLO (Multi-Link Operation) is the genuinely new capability** — **a client uses
  multiple bands SIMULTANEOUSLY for one connection, giving aggregation and, more
  importantly, failover when one band is congested or interfered.** ⚠️ **Implementations
  vary substantially: most clients implement EMLSR or MLMR-STR, and the more complex modes
  are not adopted.** **"Wi-Fi 7 certified" does not tell you which MLO mode you get.**
- **⚠️ Wi-Fi 7 mandates WPA3 and Protected Management Frames** for devices to use 11be
  rates and MLO — **so it forces a security upgrade whether you planned one or not.**
- **Preamble puncturing is mandatory for certification** — ⚠️ **the AP carves an
  interfered portion out of a wide channel and uses the rest, which is a real robustness
  improvement in messy spectrum.**

> **⚠️ GOTCHA — 6 GHz availability is NOT global, and this breaks product plans.**
> ⚠️ **The Wi-Fi Alliance reports 97 countries have adopted the full 6 GHz band or a
> portion of it** — **up from 62 in a prior count** — **but allocations differ: some
> countries have the full 1200 MHz, others only a lower slice.** ⚠️ **Claims that 6 GHz
> harmonization has been achieved are contested, and disparities remain.**
> **⚠️ A device designed around 320 MHz channels in 6 GHz may have nowhere to put them in
> a given market.** **Also note standard-power outdoor 6 GHz requires AFC (Automated
> Frequency Coordination) with GNSS position reporting — an operational dependency that
> did not previously exist in Wi-Fi.**

**⚠️ The honest deployment answer for 2026**: **one analysis puts the AP refresh at
$30,000–50,000 per 100 units while the switch infrastructure to support 802.3bt PoE and
multi-gig uplinks runs $150,000–300,000** — ⚠️ **the APs are the cheap part** — **and
concludes that for most enterprises the ROI isn't there yet in 2026, strengthening in
2027–28 as clients refresh. **Design guidance that recurs: 6 GHz becomes the capacity
layer, 5 GHz becomes the compatibility layer, and 2.4 GHz is for IoT and range.**

**⚠️ Wi-Fi 8 (802.11bn, "Ultra High Reliability")**: **pre-standard silicon sampling from
2026 and prototypes shown at CES 2026**, ⚠️ **but ratification is expected around 2028
and consumer devices toward the end of the decade.** **The notable shift is in the goal:
⚠️ Wi-Fi 8 targets reliability, latency consistency and multi-AP coordination rather than
peak throughput** — **an acknowledgement that the binding constraint is now density and
determinism, not headline speed.** ⚠️ **Do not delay projects for it.**

### 24.2 ⚠️ The IoT connectivity landscape after the 2G/3G sunset
**⚠️ If you are choosing a cellular radio in 2026, the ground has shifted and several
common defaults are now wrong.**

- **⚠️ The 2G/3G sunset is the forcing function.** **Reporting indicates roughly 37
  operators phasing out 2G and 39 retiring 3G across 2025–26**, **stranding millions of
  legacy modules.** ⚠️ **Any new design built around 2G will face forced migration well
  inside its intended service life.**
- **⚠️ The surprise default is LTE Cat-1 / Cat-1 bis, not the LPWAN technologies.**
  **Guidance from operators is that Cat-1 and Cat-1 bis have become strong default choices
  for international fleets** — ⚠️ **because availability and roaming maturity beat
  theoretical efficiency when your devices cross borders.** **Cat-1 bis needs only a
  single antenna, which removes much of the hardware penalty.**
- **⚠️ 5G RedCap is real but not yet the answer.** ⚠️ **It is commercially available in
  only a few markets, module costs remain higher, and operator guidance frames it as "a
  future consideration rather than a universal near-term replacement."** **Plan an upgrade
  path; don't design around it today unless your market has it.**
- **⚠️ Satellite NTN crossed into practicality, and the mechanism matters**: **NTN is
  NB-IoT and LTE-M run over satellite rather than a tower.** ⚠️ **In some cases an
  existing module can gain satellite capability via FIRMWARE UPDATE rather than a hardware
  swap** — **which is why this moved fast.** **Treat it as a complementary resilience
  layer for remote assets, not a primary path** — **and note it needs clear line of sight
  to the satellite, so it does not solve indoor coverage.**
- **⚠️ eSIM/eUICC (SGP.32) is now a mainstream part of the design**, **allowing remote
  operator switching and multi-IMSI — which matters because permanent roaming is
  restricted in a growing number of countries.**

**⚠️ Rough capability bands, reported for 2026 — theoretical maxima, treat as ordering
rather than as achievable throughput:**
```
NB-IoT      ⚠️ ~26 kbps down / ~17 kbps up. Best deep-indoor penetration
            (operators typically allocate it good spectrum). ⚠️ Poor mobility
LoRaWAN     ⚠️ roughly comparable to NB-IoT in data terms; unlicensed, self-run
LTE-M       ⚠️ ~1 Mbps both directions. Mobility, roaming, viable FOTA
LTE Cat-1   ⚠️ ~10 Mbps down / 5 Mbps up. Enough for video
RedCap      higher again; §24.2 caveats apply
```
**⚠️ Indicative connectivity costs cited for 2026**: **LoRaWAN cheapest at scale (no
recurring network fee if you run the gateways), NB-IoT SIM plans from roughly £0.50/month,
LTE-M typically £1–3/month.** ⚠️ **Verify against current quotes; these vary hugely by
volume and region.**
**⚠️ And a design pattern worth stealing**: **combining technologies — NB-IoT for routine
telemetry with LTE-M fallback specifically for firmware updates — is a reported real-world
approach that resolves the NB-IoT FOTA problem without paying LTE-M rates for every
message.**

---

## §25. Security

**⚠️ Radio is broadcast. Assume everything is being received by someone else.**
```
⚠️ EAVESDROPPING   passive, undetectable, and cheap with an RTL-SDR
⚠️ REPLAY          capture and retransmit. ⚠️ Defeats any system without a
   rolling code, nonce or timestamp — this is how many garage doors,
   car fobs and cheap sensors fall
JAMMING            trivial and hard to defend against; spread spectrum helps
SPOOFING           especially GNSS (§22)
⚠️ SIDE CHANNELS   RF emissions leak information (TEMPEST); ⚠️ and RSSI-based
   proximity is trivially defeated by an amplifier — relay attacks against
   keyless entry are the standard example
```
**⚠️ Practical requirements**: **encrypt at the application layer and do not trust link
encryption alone**; ⚠️ **use authenticated encryption with nonces or counters — encryption
without replay protection is not enough**; **provision unique per-device keys, never a
shared global key**; **sign firmware updates**; ⚠️ **and for proximity claims use a
protocol with cryptographic distance bounding (UWB) rather than signal strength.**
**⚠️ BLE pairing modes matter**: **Just Works provides no MITM protection.** **Use
passkey or numeric comparison where the threat model warrants it.**

---

## §26. ⚠️ Debugging RF From Software

**⚠️ An ordered procedure, because guessing is expensive here:**
```
1. ⚠️ IS IT A LINK BUDGET PROBLEM? Compute it (§3). Compare predicted RSSI
   to measured. A 20 dB discrepancy points at the antenna or the enclosure
2. ⚠️ LOOK AT THE SPECTRUM. An RTL-SDR and a waterfall display will show you
   interference in thirty seconds that you'd never find in logs
3. ⚠️ MOVE IT. If moving the device 10 cm changes everything, it's
   multipath fading (§6), not your code
4. ⚠️ CHECK RSSI **AND** SNR/LQI. Strong RSSI with bad SNR = interference (§7)
5. ⚠️ TURN OFF YOUR OWN SUBSYSTEMS one at a time. Self-interference (§7)
6. ⚠️ SNIFF THE PROTOCOL. A cheap BLE/802.15.4 sniffer shows retries and
   which side is failing
7. ⚠️ TEST WITH A CABLE and attenuators. Removing the air removes variables
8. ⚠️ CHECK ORIENTATION AND POLARIZATION (§5)
9. ⚠️ CHECK REGULATORY BEHAVIOUR — DFS events and duty-cycle blocking look
   exactly like random unexplained outages (§23)
10. ⚠️ LOG RSSI/SNR/retry counts CONTINUOUSLY IN PRODUCTION. RF problems are
    statistical and you cannot debug them from a single incident report
```
**⚠️ The instrumentation that pays for itself**: **an RTL-SDR ($30) for spectrum
visibility, a protocol sniffer for your radio family, a set of RF attenuators for
bench-testing range without walking around a car park, and — if you can — a few hours with
a spectrum analyzer at the deployment site.**
