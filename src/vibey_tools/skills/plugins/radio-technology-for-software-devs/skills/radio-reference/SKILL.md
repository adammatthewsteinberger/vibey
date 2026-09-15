---
name: radio-reference
description: "Use when checking a wireless anti-pattern, correcting a radio misconception, looking up a power level, sensitivity, data rate or range figure, finding the books and resources, or needing a picker. Companion to the other radio-technology skills."
---

# Radio Technology: Anti-Patterns, Misconceptions, Numbers, and Resources

> **Part 6 of 6** of the *Radio Technology for Software Developers* reference (plugin `radio-technology-for-software-devs`), covering §27–§32. Sibling skills: `radio-intuitions-spectrum-link-budget-and-tradeoffs` (§0–§4), `radio-antennas-propagation-noise-and-modulation` (§5–§9), `radio-spread-spectrum-ofdm-access-and-sdr` (§10–§16), `radio-protocol-stacks-wifi-ble-lpwan-and-gnss` (§17–§22), `radio-regulatory-security-and-debugging` (§23–§26). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    (§4 → `radio-intuitions-spectrum-link-budget-and-tradeoffs`, §19 → `radio-protocol-stacks-wifi-ble-lpwan-and-gnss`), **and you cannot fix a bad choice in firmware.**

---

## §27. Anti-Patterns

```
⚠️ Cranking TX power instead of fixing the antenna or placement (§3, §5)
⚠️ Testing only at short range, line of sight, on the bench (§1)
⚠️ Designing the enclosure before the antenna (§5)
⚠️ Assuming datasheet range figures. They're free-space, ideal, and marketing
⚠️ Treating RSSI as SNR (§7)
⚠️ Ignoring duty-cycle limits until certification (§23)
⚠️ Using max LoRa spreading factor "for range" and killing network capacity (§10)
⚠️ No retry/idempotency at the application layer (§1)
⚠️ Trusting negotiated BLE connection parameters without reading them back (§19)
⚠️ Forgetting ATT MTU negotiation and wondering why BLE throughput is awful (§19)
⚠️ Designing a global product around one region's sub-GHz band (§23)
⚠️ Designing around 2G in 2026 (§24.2), or around 6 GHz 320 MHz channels
   without checking regional allocation (§24.1)
⚠️ Shipping a shared network-wide key (§25)
⚠️ Proximity security based on signal strength (§25)
⚠️ Downsampling without an anti-alias filter (§15)
⚠️ No production RF telemetry, then trying to debug from user reports (§26)
```

---

## §28. Misconceptions

| Misconception | Correction |
|---|---|
| More TX power fixes range | ⚠️ **4× power for 2× range; antenna/placement usually beat it** (§3 → `radio-intuitions-spectrum-link-budget-and-tradeoffs`) |
| Antenna gain amplifies | ⚠️ **It focuses. Gain in one direction is loss in another** (§5 → `radio-antennas-propagation-noise-and-modulation`) |
| Line of sight is enough | ⚠️ **You need ~60% of the Fresnel zone clear** (§6 → `radio-antennas-propagation-noise-and-modulation`) |
| RSSI tells you link quality | ⚠️ **It includes interference. Use SNR** (§7 → `radio-antennas-propagation-noise-and-modulation`) |
| dBm and dB are interchangeable | ⚠️ **dBm is absolute power; dB is a ratio** (§3 → `radio-intuitions-spectrum-link-budget-and-tradeoffs`) |
| Wider channel is always faster | ⚠️ **Wider = more noise and more overlap** (§7 → `radio-antennas-propagation-noise-and-modulation`, §18 → `radio-protocol-stacks-wifi-ble-lpwan-and-gnss`) |
| Advertised PHY rate ≈ throughput | ⚠️ **Roughly half or less, and shared** (§8 → `radio-antennas-propagation-noise-and-modulation`, §18 → `radio-protocol-stacks-wifi-ble-lpwan-and-gnss`) |
| CSMA/CD works on radio | ⚠️ **You can't hear a collision while transmitting** (§13 → `radio-spread-spectrum-ofdm-access-and-sdr`) |
| Carrier sense prevents collisions | ⚠️ **Hidden node problem** (§13 → `radio-spread-spectrum-ofdm-access-and-sdr`) |
| Bluetooth and BLE are the same protocol | ⚠️ **Different protocols, shared brand** (§19 → `radio-protocol-stacks-wifi-ble-lpwan-and-gnss`) |
| Matter is a radio protocol | ⚠️ **It's an application layer over Thread/Wi-Fi/Ethernet** (§21 → `radio-protocol-stacks-wifi-ble-lpwan-and-gnss`) |
| Mesh gives everyone long battery life | ⚠️ **Routers can't sleep. Only leaf nodes do** (§21 → `radio-protocol-stacks-wifi-ble-lpwan-and-gnss`) |
| Nyquist means 2× the highest frequency | ⚠️ **2× the BANDWIDTH; and 1× for complex IQ** (§15 → `radio-spread-spectrum-ofdm-access-and-sdr`) |
| The DC spike is a signal | ⚠️ **LO leakage artefact of direct conversion** (§14 → `radio-spread-spectrum-ofdm-access-and-sdr`) |
| GNSS works indoors | ⚠️ **Signal is below the noise floor; it needs sky view** (§22 → `radio-protocol-stacks-wifi-ble-lpwan-and-gnss`) |
| Encryption alone secures a radio link | ⚠️ **Without replay protection it doesn't** (§25 → `radio-regulatory-security-and-debugging`) |
| ISM bands are unregulated | ⚠️ **Unlicensed ≠ unregulated. Power and duty cycle bind** (§23 → `radio-regulatory-security-and-debugging`) |
| One design ships globally | ⚠️ **Sub-GHz and 6 GHz allocations differ by region** (§23 → `radio-regulatory-security-and-debugging`, §24.1 → `radio-regulatory-security-and-debugging`) |
| 5G RedCap is the IoT default now | ⚠️ **Few markets; LTE Cat-1/Cat-1 bis is the 2026 default** (§24.2 → `radio-regulatory-security-and-debugging`) |
| Wi-Fi 7 certified means full MLO | ⚠️ **Implementations vary; check the mode** (§24.1 → `radio-regulatory-security-and-debugging`) |
| Satellite IoT is a separate protocol | ⚠️ **NTN is NB-IoT/LTE-M over satellite** (§24.2 → `radio-regulatory-security-and-debugging`) |

---

## §29. Numbers

```
c ≈ 3×10⁸ m/s        λ = c/f      ⚠️ 2.4 GHz → λ ≈ 12.5 cm
⚠️ +3 dB = 2×  ·  +10 dB = 10×  ·  0 dBm = 1 mW  ·  20 dBm = 100 mW
⚠️ Thermal noise floor  −174 dBm/Hz  →  −114 dBm in 1 MHz
⚠️ FSPL: double the distance = −6 dB · double the frequency = −6 dB
⚠️ Link margin target   10–20 dB minimum for real deployments
Wall loss               ⚠️ ~3–15 dB; concrete/foil far more; human body 3–10 dB
Indoor path loss exponent  ⚠️ ~3–5 (free space is 2)
⚠️ Multipath null spacing  ~λ/2 → about 6 cm at 2.4 GHz
Sensitivity     Wi-Fi ~−90 dBm · BLE ~−95 dBm · ⚠️ LoRa ~−137 dBm
⚠️ Shannon      C = B·log₂(1+SNR) — linear in B, logarithmic in SNR
BLE connection interval   7.5 ms – 4 s      ⚠️ Default ATT MTU 23 bytes
⚠️ 802.15.4     250 kbps        Bluetooth hops  1600/s
⚠️ EU sub-GHz duty cycle   commonly ~1% per hour
Wi-Fi 2.4 GHz non-overlapping channels   ⚠️ 1, 6, 11
⚠️ 6 GHz adoption   97 countries, full or partial (§24.1)
GNSS satellites for a fix   ⚠️ 4 (3 position + 1 clock)
```

---

## §30. Books and Resources

| Author | Work | Why |
|---|---|---|
| **ARRL** | ***The ARRL Handbook*** | ⚠️ **The practical RF bible. Amateur radio, and unmatched** |
| **Lyons** | ***Understanding Digital Signal Processing*** | ⚠️ **The best DSP book for engineers. §15 → `radio-spread-spectrum-ofdm-access-and-sdr`** |
| **Collins et al.** | *Software-Defined Radio for Engineers* | ⚠️ **Free PDF from Analog Devices. §14–§16 → `radio-spread-spectrum-ofdm-access-and-sdr`** |
| **Rappaport** | *Wireless Communications: Principles and Practice* | ⚠️ **The standard propagation text. §3 → `radio-intuitions-spectrum-link-budget-and-tradeoffs`, §6 → `radio-antennas-propagation-noise-and-modulation`** |
| **Proakis** | *Digital Communications* | Rigorous; the reference for §8–§12 → `radio-antennas-propagation-noise-and-modulation`, `radio-spread-spectrum-ofdm-access-and-sdr` |
| **Gast** | *802.11 Wireless Networks: The Definitive Guide* | §18 → `radio-protocol-stacks-wifi-ble-lpwan-and-gnss` |
| **Townsend et al.** | *Getting Started with Bluetooth Low Energy* | §19 → `radio-protocol-stacks-wifi-ble-lpwan-and-gnss` |

**⚠️ Online**: **PySDR (Marc Lichtman) — a free, genuinely excellent SDR/DSP text with
Python examples, and the best starting point for a software developer**; **the GNU Radio
tutorials**; **your regulator's actual documents (FCC Part 15, ETSI EN 300 220 / EN 300
328) — dry and authoritative**; **and the radio chip vendor app notes, which are often the
best practical antenna and layout guidance available anywhere.**

---

## §31. Quick Reference

### 31.1 Picker
| Question | Answer |
|---|---|
| Will this link work? | ⚠️ **Compute the link budget. Want 10–20 dB margin** (§3 → `radio-intuitions-spectrum-link-budget-and-tradeoffs`) |
| Range is bad — what first? | ⚠️ **Antenna, placement, orientation. Not TX power** (§3 → `radio-intuitions-spectrum-link-budget-and-tradeoffs`, §5 → `radio-antennas-propagation-noise-and-modulation`) |
| Works on bench, fails in field | ⚠️ **§1 → `radio-intuitions-spectrum-link-budget-and-tradeoffs` checklist: budget, multipath, interference, duty cycle** |
| Intermittent, moves when I move | ⚠️ **Multipath fading. Try antenna diversity** (§6 → `radio-antennas-propagation-noise-and-modulation`) |
| Strong signal, bad throughput | ⚠️ **Interference. Check SNR, look at the spectrum** (§7 → `radio-antennas-propagation-noise-and-modulation`, §26 → `radio-regulatory-security-and-debugging`) |
| Battery life is terrible | ⚠️ **Duty cycle and connection interval, not TX power** (§4 → `radio-intuitions-spectrum-link-budget-and-tradeoffs`, §19 → `radio-protocol-stacks-wifi-ble-lpwan-and-gnss`) |
| Long range, tiny data, own the site | ⚠️ **LoRaWAN** (§20 → `radio-protocol-stacks-wifi-ble-lpwan-and-gnss`) |
| Long range, tiny data, devices roam | ⚠️ **LTE-M** (§20 → `radio-protocol-stacks-wifi-ble-lpwan-and-gnss`, §24.2 → `radio-regulatory-security-and-debugging`) |
| Deep indoors, stationary, 10-yr battery | ⚠️ **NB-IoT** (§20 → `radio-protocol-stacks-wifi-ble-lpwan-and-gnss`) |
| Global fleet, mixed markets, 2026 | ⚠️ **LTE Cat-1 / Cat-1 bis** (§24.2 → `radio-regulatory-security-and-debugging`) |
| Need reliable firmware updates | ⚠️ **LTE-M, or LTE-M as a fallback layer** (§24.2 → `radio-regulatory-security-and-debugging`) |
| Phone accessory | ⚠️ **BLE** (§19 → `radio-protocol-stacks-wifi-ble-lpwan-and-gnss`) |
| Home automation mesh | ⚠️ **Thread + Matter** (§21 → `radio-protocol-stacks-wifi-ble-lpwan-and-gnss`) |
| Want to see what's actually on the air | ⚠️ **RTL-SDR, $30** (§16 → `radio-spread-spectrum-ofdm-access-and-sdr`, §26 → `radio-regulatory-security-and-debugging`) |

### 31.2 Before design freeze
- [ ] ⚠️ **Link budget computed with realistic (not free-space) path loss** (§3 → `radio-intuitions-spectrum-link-budget-and-tradeoffs`)
- [ ] ⚠️ **10–20 dB margin at worst-case range and orientation** (§3 → `radio-intuitions-spectrum-link-budget-and-tradeoffs`)
- [ ] Antenna keep-out respected; tuned **in the final enclosure** (§5 → `radio-antennas-propagation-noise-and-modulation`)
- [ ] ⚠️ **Regional band allocations checked for every target market** (§23 → `radio-regulatory-security-and-debugging`, §24.1 → `radio-regulatory-security-and-debugging`)
- [ ] ⚠️ **Duty cycle budget computed against message rate** (§23 → `radio-regulatory-security-and-debugging`)
- [ ] Pre-certified module, or a certification budget and schedule (§23 → `radio-regulatory-security-and-debugging`)
- [ ] ⚠️ **Self-interference tested with all subsystems running** (§7 → `radio-antennas-propagation-noise-and-modulation`)
- [ ] Application-layer retry, idempotency, and backoff (§1 → `radio-intuitions-spectrum-link-budget-and-tradeoffs`)
- [ ] ⚠️ **Per-device keys; replay protection; signed firmware** (§25 → `radio-regulatory-security-and-debugging`)
- [ ] ⚠️ **RSSI/SNR/retry telemetry shipped to production** (§26 → `radio-regulatory-security-and-debugging`)
- [ ] Chosen radio still supported over the product's service life (§24.2 → `radio-regulatory-security-and-debugging`)

---

## §32. Method

**§1–§23 → `radio-intuitions-spectrum-link-budget-and-tradeoffs`, `radio-antennas-propagation-noise-and-modulation`, `radio-spread-spectrum-ofdm-access-and-sdr`, `radio-protocol-stacks-wifi-ble-lpwan-and-gnss`, `radio-regulatory-security-and-debugging` and §25–§27 → `radio-regulatory-security-and-debugging` rest on physics, information theory and mature protocol
specifications** — ⚠️ **Friis, Shannon, Nyquist and the dB arithmetic are not going to
change** — sourced from §30. **No verification needed.**

**Two searches were run in August 2026**, on **Wi-Fi 7/8 and 6 GHz status** and **the IoT
connectivity landscape** — ⚠️ **the two areas where a software developer's radio choice
turns on facts that changed recently and where a 2024 answer would produce a bad design.**

**Confidence.** **High** in §3 → `radio-intuitions-spectrum-link-budget-and-tradeoffs`, §4 → `radio-intuitions-spectrum-link-budget-and-tradeoffs` and §6 → `radio-antennas-propagation-noise-and-modulation`, which are the sections I'd most want read.
⚠️ **The link budget and the "double the range needs 4× the power" consequence are the
single highest-leverage things a software developer can learn here** — **they turn most
range arguments into arithmetic** — **and the λ/2 multipath null spacing (~6 cm at
2.4 GHz) explains more otherwise-inexplicable field bugs than anything else in the
document.**

**High** in §24.1 → `radio-regulatory-security-and-debugging`'s facts. ⚠️ **The 6 GHz fragmentation point is the one I'd emphasise:
97 countries with full or partial allocation is real progress AND means a design assuming
320 MHz channels may have nowhere to put them.** **The claim that harmonization has been
achieved is explicitly contested in the reporting, and I've said so rather than picking a
side.** **The Wi-Fi 8 timeline (~2028 ratification, pre-standard silicon sampling 2026) is
consistent across sources.** ⚠️ **The enterprise cost figures come from a single vendor
analysis and I've attributed them as such — the ratio (switch infrastructure costing
several times the APs) is the durable insight, not the specific dollar amounts.**

**High** in §24.2 → `radio-regulatory-security-and-debugging`'s direction. ⚠️ **The most decision-relevant and least expected finding
is that LTE Cat-1/Cat-1 bis has become the pragmatic default for international fleets
rather than the LPWAN technologies** — **operator guidance says this directly** — **and
that 5G RedCap is explicitly framed as "a future consideration rather than a universal
near-term replacement."** **The NTN-as-firmware-update point is the mechanism that explains
why satellite IoT moved so fast, and it's worth knowing.**

⚠️ **Sourcing caution, stated plainly**: **much of the IoT connectivity material online is
published by connectivity providers, eSIM platforms and module vendors, all of whom have a
position.** **The throughput figures and the decision-tree logic recur consistently across
independent sources including operator technical documentation, so I've reported those.**
⚠️ **The cost figures (£0.50/month NB-IoT, £1–3/month LTE-M) come from a single vendor and
should be treated as indicative only.** **Where a claim came from one interested source,
I've said so in the text rather than laundering it into the numbers table.**
