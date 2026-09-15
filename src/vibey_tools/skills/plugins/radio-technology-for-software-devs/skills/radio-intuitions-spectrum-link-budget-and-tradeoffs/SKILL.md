---
name: radio-intuitions-spectrum-link-budget-and-tradeoffs
description: "Use when starting on anything wireless: why wireless breaks the intuitions software engineers bring from wired networking, spectrum and the band characteristics that follow from physics, the link budget as the single calculation that explains most range questions, and the range, rate and power triangle you cannot escape. Includes the router for the whole radio-technology reference."
---

# Radio Technology: Why Wireless Breaks Software Intuitions, Spectrum, the Link Budget, and the Range/Rate/Power Triangle

> **Part 1 of 6** of the *Radio Technology for Software Developers* reference (plugin `radio-technology-for-software-devs`), covering §0–§4. Sibling skills: `radio-antennas-propagation-noise-and-modulation` (§5–§9), `radio-spread-spectrum-ofdm-access-and-sdr` (§10–§16), `radio-protocol-stacks-wifi-ble-lpwan-and-gnss` (§17–§22), `radio-regulatory-security-and-debugging` (§23–§26), `radio-reference` (§27–§32). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    medium where the same code works on your desk and fails in the field** (§1).
> 2. **⚠️ The link budget is the single most useful tool you can learn** (§3). **Most
>    wireless problems are budget problems, and most of them are diagnosable on paper
>    before you build anything.**
> 3. **⚠️ Choosing the radio is an architecture decision, not a component decision.**
>    **Range, data rate, power and cost trade against each other in ways physics fixes**
>    (§4, §19 → `radio-protocol-stacks-wifi-ble-lpwan-and-gnss`), **and you cannot fix a bad choice in firmware.**

---

## §0. Routing

| You want... | Go to |
|---|---|
| **⚠️ Why wireless breaks your assumptions** | **§1** |
| Spectrum and bands | §2 |
| **⚠️ Link budget and dB** | **§3** |
| **The range/rate/power triangle** | **§4** |
| Antennas | §5 → `radio-antennas-propagation-noise-and-modulation` |
| Propagation and fading | §6 → `radio-antennas-propagation-noise-and-modulation` |
| Noise and interference | §7 → `radio-antennas-propagation-noise-and-modulation` |
| Modulation | §8 → `radio-antennas-propagation-noise-and-modulation` |
| **Shannon's limit** | **§9 → `radio-antennas-propagation-noise-and-modulation`** |
| Spread spectrum | §10 → `radio-spread-spectrum-ofdm-access-and-sdr` |
| OFDM | §11 → `radio-spread-spectrum-ofdm-access-and-sdr` |
| Coding and retransmission | §12 → `radio-spread-spectrum-ofdm-access-and-sdr` |
| Multiple access | §13 → `radio-spread-spectrum-ofdm-access-and-sdr` |
| **⚠️ SDR and IQ** | **§14 → `radio-spread-spectrum-ofdm-access-and-sdr`** |
| Sampling and DSP | §15 → `radio-spread-spectrum-ofdm-access-and-sdr` |
| SDR toolchain | §16 → `radio-spread-spectrum-ofdm-access-and-sdr` |
| PHY/MAC and the stack | §17 → `radio-protocol-stacks-wifi-ble-lpwan-and-gnss` |
| Wi-Fi | §18 → `radio-protocol-stacks-wifi-ble-lpwan-and-gnss` |
| **Bluetooth / BLE** | **§19 → `radio-protocol-stacks-wifi-ble-lpwan-and-gnss`** |
| **LPWAN and cellular IoT** | **§20 → `radio-protocol-stacks-wifi-ble-lpwan-and-gnss`** |
| 802.15.4, Thread, Matter | §21 → `radio-protocol-stacks-wifi-ble-lpwan-and-gnss` |
| GNSS | §22 → `radio-protocol-stacks-wifi-ble-lpwan-and-gnss` |
| **Regulatory** | **§23 → `radio-regulatory-security-and-debugging`** |
| **What moved** | **§24 → `radio-regulatory-security-and-debugging`** |
| Security | §25 → `radio-regulatory-security-and-debugging` |
| **⚠️ Debugging RF** | **§26 → `radio-regulatory-security-and-debugging`** |
| Anti-patterns | §27 → `radio-reference` |
| Misconceptions | §28 → `radio-reference` |
| Numbers, books, quick ref | §29–§31 → `radio-reference` |

---

## §1. ⚠️ Why Wireless Breaks Software Intuitions

```
WIRED assumption              ⚠️ RF reality
─────────────────────────────────────────────────────────────────────
The link is up or down        ⚠️ Continuously variable quality. "Up" is a
                              threshold you chose
Bandwidth is provisioned      ⚠️ SHARED medium. Your neighbour's microwave
                              is on your network
Errors are rare              ⚠️ Errors are CONSTANT and being corrected
                              below you. Raw BER may be 1e-3
Latency is stable            ⚠️ Retries, backoff and contention make it
                              heavy-tailed. The p99 is nothing like the mean
It works here → works there   ⚠️ Move it 30 cm and it may not (§6 multipath)
Reproducible                  ⚠️ RF bugs are famously intermittent, weather-
                              dependent, orientation-dependent and
                              time-of-day dependent
Add capacity by adding nodes  ⚠️ More radios in a band = LESS total capacity
```
> **⚠️ GOTCHA — the single most common failure pattern: it works perfectly on the bench,
> then fails in deployment.** ⚠️ **The bench has short range, line of sight, no
> interference, and a fresh battery.** **The field has none of those.** **Almost every
> field failure traces to §3 (budget), §6 → `radio-antennas-propagation-noise-and-modulation` (multipath/fading), §7 → `radio-antennas-propagation-noise-and-modulation` (interference), or §23 → `radio-regulatory-security-and-debugging`
> (duty cycle limits you didn't know applied).**

**⚠️ The mental shift**: **stop thinking of the radio as a pipe and start thinking of it
as a statistical channel.** ⚠️ **Design for packet loss, design for variable latency,
design for the link disappearing entirely for seconds at a time — and make your protocol
idempotent, because you will retransmit.**

---

## §2. Spectrum and Bands

```
λ = c / f      ⚠️ c ≈ 3×10⁸ m/s.  At 2.4 GHz, λ ≈ 12.5 cm
```
⚠️ **Wavelength determines antenna size** — **an efficient antenna is a meaningful fraction
of a wavelength (¼λ is the classic), which is why low-frequency radios need big antennas
and why your 2.4 GHz chip antenna can be a few centimetres of PCB trace.**

```
BAND        TYPICAL USE                      ⚠️ CHARACTER
LF/MF/HF    AM radio, maritime, amateur      ⚠️ Long range, ground wave and
  <30 MHz                                    ionospheric skip, tiny bandwidth
VHF 30–300M FM, aviation, marine, ham        Good building penetration
UHF 300M–3G ⚠️ 433/868/915 ISM, LoRa, cell,  ⚠️ THE workhorse. Reasonable
            Wi-Fi 2.4, BLE, Zigbee           penetration and antenna size
SHF 3–30G   Wi-Fi 5/6E/7, radar, satellite,  ⚠️ Wide bandwidth, poor
            5G mmWave lower                  penetration, more directional
EHF >30G    ⚠️ mmWave 5G, automotive radar   Enormous bandwidth, blocked by
                                             a hand, absorbed by rain
```
**⚠️ The universal tradeoff, and it's physics, not engineering:**
⚠️ **Lower frequency → better penetration and diffraction, longer range for the same
power, less available bandwidth, bigger antennas.**
⚠️ **Higher frequency → more bandwidth, higher data rates, shorter range, blocked by
walls and bodies, smaller antennas.**
**⚠️ There is no band that is good at everything, and every protocol in §18–§22 → `radio-protocol-stacks-wifi-ble-lpwan-and-gnss` is a
different point on this curve.**

---

## §3. ⚠️ The Link Budget

**⚠️ This is the tool. Learn it and most wireless design becomes arithmetic.**

```
⚠️ Received power (dBm) = TX power (dBm)
                        + TX antenna gain (dBi)
                        − path loss (dB)
                        − cable/connector/body losses (dB)
                        + RX antenna gain (dBi)

⚠️ LINK MARGIN = received power − receiver sensitivity
   ⚠️ Want AT LEAST 10–20 dB margin for a real deployment. Zero margin
   means it works on a good day, in one orientation, and nowhere else
```

**⚠️ Decibels — get comfortable, because everything is in dB and it's all multiplication
turned into addition:**
```
⚠️ +3 dB  ≈ 2×  power      ⚠️ −3 dB  ≈ half power
⚠️ +10 dB = 10× power      ⚠️ +20 dB = 100×
dBm = dB relative to 1 milliwatt.  ⚠️ 0 dBm = 1 mW.  20 dBm = 100 mW
dBi = antenna gain vs an isotropic radiator
⚠️ Typical numbers: BLE TX 0–10 dBm · Wi-Fi 15–20 dBm · LoRa 14 dBm (EU)
⚠️ Receiver sensitivity: Wi-Fi ~−90 dBm · BLE ~−95 dBm · LoRa ~−137 dBm
```

**⚠️ Free-space path loss (Friis)** — **the optimistic case, and reality is always worse:**
```
FSPL(dB) = 20·log₁₀(d) + 20·log₁₀(f) + 32.44   (d in km, f in MHz)

⚠️ CONSEQUENCE 1: doubling distance costs 6 dB. Every time
⚠️ CONSEQUENCE 2: doubling FREQUENCY also costs 6 dB — which is why the
   same power gets you less range at 5 GHz than 2.4 GHz
⚠️ CONSEQUENCE 3: to DOUBLE your range you need 4× the power (+6 dB).
   To 10× your range you need 100× the power
```
> **⚠️ GOTCHA — "just turn up the transmit power" is almost always the wrong answer, and
> the arithmetic above is why.** ⚠️ **6 dB of extra TX power (4× the battery drain, and
> possibly illegal — §23 → `radio-regulatory-security-and-debugging`) buys you double the range in free space and much less
> indoors.** **Meanwhile 6 dB of antenna improvement is free at runtime, and moving the
> antenna away from a ground plane or a battery can be worth 10 dB.**
> **⚠️ Sensitivity, antenna and placement beat power almost every time.**

**⚠️ Real-world loss is far worse than free space**: **indoor path loss exponents run
roughly 3–5 rather than 2**; ⚠️ **a wall costs perhaps 3–15 dB, concrete or foil-backed
insulation far more, and a human body 3–10 dB and moving.**

---

## §4. The Range / Rate / Power Triangle

**⚠️ Pick two. This is the constraint that determines your protocol choice.**
```
⚠️ LONG RANGE + LOW POWER  → very low data rate    (LoRa, NB-IoT, Sigfox)
⚠️ HIGH RATE + LOW POWER   → short range           (BLE, Zigbee)
⚠️ HIGH RATE + LONG RANGE  → high power            (Wi-Fi, cellular)
```
**⚠️ Why, physically**: **for a fixed receiver, detecting a signal requires a minimum
energy PER BIT above the noise.** ⚠️ **Slowing the data rate means spending more time —
and therefore more energy — per bit, which raises effective sensitivity.** **LoRa's
−137 dBm sensitivity is bought entirely with time** (§10 → `radio-spread-spectrum-ofdm-access-and-sdr`).
**⚠️ And duty cycle is the real power lever, not TX power.** **A device transmitting for
20 ms once an hour at 14 dBm draws almost nothing on average.** ⚠️ **Battery life in LPWAN
designs is dominated by sleep current and message frequency, not by transmit power** —
**which is why a firmware bug that keeps the radio awake destroys a ten-year battery
budget in weeks.**
