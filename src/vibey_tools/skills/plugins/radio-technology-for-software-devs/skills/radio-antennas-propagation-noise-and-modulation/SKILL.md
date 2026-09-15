---
name: radio-antennas-propagation-noise-and-modulation
description: "Use when the physical layer is the problem: antennas including gain, polarization, radiation patterns and matching, propagation and fading including multipath and the fading models, noise and interference and the noise floor, modulation schemes and their spectral efficiency versus robustness trade-off, and Shannon's limit as the hard ceiling on what any scheme can achieve."
---

# Radio Technology: Antennas, Propagation and Fading, Noise and Interference, Modulation, and Shannon's Limit

> **Part 2 of 6** of the *Radio Technology for Software Developers* reference (plugin `radio-technology-for-software-devs`), covering §5–§9. Sibling skills: `radio-intuitions-spectrum-link-budget-and-tradeoffs` (§0–§4), `radio-spread-spectrum-ofdm-access-and-sdr` (§10–§16), `radio-protocol-stacks-wifi-ble-lpwan-and-gnss` (§17–§22), `radio-regulatory-security-and-debugging` (§23–§26), `radio-reference` (§27–§32). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §5. Antennas

**⚠️ The most under-appreciated component in the whole system, and usually the cheapest
place to gain 10 dB.**
```
GAIN (dBi)     ⚠️ NOT amplification — it's focusing. A high-gain antenna is
               directional; it robs from one direction to give to another
RADIATION PATTERN  ⚠️ where the energy actually goes. A dipole has a NULL
               along its own axis — point it at the receiver and you get nothing
POLARIZATION   ⚠️ linear (V/H) or circular. CROSS-POLARIZED antennas can cost
               you 20+ dB. This is why an orientation change kills a link
IMPEDANCE / VSWR  ⚠️ mismatch reflects power back. Aim for VSWR < 2:1
GROUND PLANE   ⚠️ many antennas need one and are part of it. Changing the
               PCB changes the antenna
```
> **⚠️ GOTCHA — the enclosure, the PCB, the battery and the human holding it are all part
> of your antenna.** ⚠️ **An antenna tuned on the bench, on a bare board, will detune when
> you put it in a plastic case near a LiPo cell.** **Metal enclosures are close to fatal
> for internal antennas.** **This is why "it worked on the dev board" is such a common and
> expensive surprise** — **and why RF designs get re-tuned after mechanical design
> freezes, not before.**

**Practical rules**: ⚠️ **keep antennas away from ground planes, metal and batteries;
respect the manufacturer's keep-out area exactly; height matters enormously outdoors;
and for a fixed link, aiming a directional antenna is the cheapest dB you will ever buy.**

---

## §6. Propagation and Fading

```
FREE SPACE      the §3 baseline. ⚠️ You will not get it
REFLECTION      off ground, walls, metal
⚠️ MULTIPATH    copies arrive at different times and phases and INTERFERE.
                Can add or CANCEL
DIFFRACTION     ⚠️ bending around edges — why you get signal around corners.
                Better at low frequencies
SCATTERING      off rough surfaces, rain, foliage
⚠️ FRESNEL ZONE the ellipsoid around the line of sight that must be ~60%
                clear. ⚠️ Visual line of sight is NOT enough for a long link
ABSORPTION      ⚠️ water absorbs strongly. Foliage, rain and people are
                lossy — and 2.4 GHz is near a water absorption feature
```
**⚠️ Fading is the thing that makes RF bugs irreproducible:**
- **⚠️ FAST fading (Rayleigh/Rician)** — **multipath nulls occur on the scale of HALF A
  WAVELENGTH.** ⚠️ **At 2.4 GHz that's about 6 cm.** **Move the device a few centimetres
  and the link can go from fine to dead. This is not a defect.**
- **SLOW fading (shadowing)** — **obstacles, log-normal distributed.**
- **⚠️ Doppler** — **movement shifts frequency and changes the channel over time.**

**⚠️ The mitigations, and all of them are just diversity in some dimension:**
**spatial (multiple antennas — MIMO), frequency (hop or spread — §10 → `radio-spread-spectrum-ofdm-access-and-sdr`, §11 → `radio-spread-spectrum-ofdm-access-and-sdr`), time
(interleave and retransmit — §12 → `radio-spread-spectrum-ofdm-access-and-sdr`), and polarization.** ⚠️ **Antenna diversity — two
antennas a few centimetres apart — is often the single highest-value fix for an
intermittent indoor link, precisely because the nulls are that small.**

---

## §7. Noise and Interference

```
⚠️ THERMAL NOISE FLOOR = −174 dBm/Hz at room temperature
   ⚠️ In 1 MHz of bandwidth: −174 + 10·log₁₀(10⁶) = −114 dBm
   ⚠️ WIDER BANDWIDTH = MORE NOISE. This is why narrowband radios are
   more sensitive than wideband ones
NOISE FIGURE (NF)  how much your receiver adds. 2–10 dB typical
SNR                signal-to-noise. ⚠️ What actually determines whether you
                   can demodulate
SINR               ⚠️ includes interference — the realistic metric
```
**⚠️ Interference sources that actually bite in the field**: **microwave ovens (2.4 GHz,
and they pulse at the mains frequency); other Wi-Fi and BLE; USB 3.0 and its cables,
which radiate broadband noise right at 2.4 GHz; switching power supplies; LED drivers;
poorly shielded cheap electronics; and your own device's digital sections.**
> **⚠️ GOTCHA — self-interference is the one people miss.** ⚠️ **A switching regulator,
> a high-speed digital bus, or a display ribbon cable on the same board can raise your
> receiver's effective noise floor by tens of dB.** **Symptom: sensitivity is far worse
> than the datasheet and only in the finished product.** **Diagnosis: turn subsystems off
> one at a time and watch the noise floor.**

**⚠️ RSSI is not SNR, and confusing them causes bad decisions.** **RSSI measures total
received power INCLUDING interference.** ⚠️ **A strong RSSI in a noisy band can mean a
worse link than a weak RSSI in a quiet one.** **Use SNR/LQI where the radio provides it.**

---

## §8. Modulation

```
ANALOG      AM (amplitude) · FM (frequency) · PM (phase)
DIGITAL
  ASK/OOK   ⚠️ on-off keying. Trivially simple, poor noise performance.
            Very common in cheap 433 MHz remotes
  FSK/GFSK  ⚠️ frequency shifts. Robust, constant envelope (efficient
            amplifiers). BLE, many sub-GHz radios
  PSK       BPSK, QPSK — phase shifts. Better spectral efficiency
  ⚠️ QAM    amplitude AND phase. 16/64/256/1024/4096-QAM.
            ⚠️ Each step up packs more bits per symbol and needs MORE SNR
```
**⚠️ The constellation diagram is the mental model**: **each symbol is a point in
IQ space** (§14 → `radio-spread-spectrum-ofdm-access-and-sdr`); ⚠️ **noise scatters the received points into clouds, and higher-order
QAM packs the points closer together, so the clouds overlap at lower noise.** **This is
exactly why high data rates need short range: 4096-QAM needs a very clean signal.**
**⚠️ Adaptive modulation and coding (AMC) is why real links have variable rates** —
**the radio drops to a more robust scheme as SNR falls.** ⚠️ **Your "150 Mbps" Wi-Fi link
is a peak PHY rate under ideal conditions and shared with everything else in the band.**

---

## §9. Shannon's Limit

```
⚠️ C = B · log₂(1 + SNR)

C = capacity (bits/s) · B = bandwidth (Hz) · SNR = linear (not dB)
```
**⚠️ This is a hard physical bound, not an engineering target.** **No modulation, coding
or clever protocol beats it.**
**⚠️ What it tells you practically:**
- **⚠️ Bandwidth is worth more than power.** **Capacity is LINEAR in bandwidth and only
  LOGARITHMIC in SNR.** **Doubling bandwidth doubles capacity; doubling SNR adds a
  fraction of a bit per symbol.** ⚠️ **This is why every generation of everything chases
  wider channels — 320 MHz in Wi-Fi 7, mmWave in 5G.**
- **⚠️ At high SNR you're in diminishing returns.** **Going from 30 to 40 dB SNR buys
  little.**
- **⚠️ You can trade SNR for bandwidth**, **which is exactly what spread spectrum does
  (§10 → `radio-spread-spectrum-ofdm-access-and-sdr`) — LoRa transmits BELOW the noise floor by using far more bandwidth than the data
  needs.**
