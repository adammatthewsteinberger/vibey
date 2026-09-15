---
name: radio-spread-spectrum-ofdm-access-and-sdr
description: "Use when working with modern waveforms or an SDR: spread spectrum and processing gain, OFDM and why it dominates, coding and retransmission strategies, multiple access schemes, SDR and IQ sampling and what complex baseband actually represents, the sampling and DSP essentials needed to work with it, and the SDR toolchain."
---

# Radio Technology: Spread Spectrum, OFDM, Coding, Multiple Access, and Software-Defined Radio

> **Part 3 of 6** of the *Radio Technology for Software Developers* reference (plugin `radio-technology-for-software-devs`), covering §10–§16. Sibling skills: `radio-intuitions-spectrum-link-budget-and-tradeoffs` (§0–§4), `radio-antennas-propagation-noise-and-modulation` (§5–§9), `radio-protocol-stacks-wifi-ble-lpwan-and-gnss` (§17–§22), `radio-regulatory-security-and-debugging` (§23–§26), `radio-reference` (§27–§32). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §10. Spread Spectrum

**⚠️ Deliberately using much more bandwidth than the data requires, in exchange for
robustness.**
```
DSSS   ⚠️ multiply data by a fast pseudo-random code. Spreads energy;
       the receiver correlates to recover it, gaining PROCESSING GAIN.
       Interference and multipath are suppressed. 802.15.4, GPS, older Wi-Fi
FHSS   ⚠️ hop the carrier around a channel set. If one channel is jammed
       you lose one hop, not the link. ⚠️ Bluetooth — 1600 hops/second
CSS    ⚠️ chirp spread spectrum — LoRa. Frequency sweeps across the band
CDMA   multiple users, different codes, same band and time
```
**⚠️ LoRa's spreading factor is the clearest illustration of §4 → `radio-intuitions-spectrum-link-budget-and-tradeoffs` in a single knob:**
⚠️ **SF7 → SF12 roughly doubles airtime per step, adds a few dB of sensitivity per step,
and cuts the data rate.** **SF12 reaches furthest and can occupy the channel for seconds
per message** — ⚠️ **which collides directly with duty-cycle regulation (§23 → `radio-regulatory-security-and-debugging`) and destroys
network capacity if used carelessly.** **Adaptive Data Rate exists to push devices to the
lowest SF that works.**

---

## §11. OFDM

**⚠️ Why nearly everything modern — Wi-Fi, LTE, 5G, DVB — uses it.**
**⚠️ The problem it solves**: **at high data rates, symbols become shorter than the
multipath delay spread, so echoes of one symbol smear into the next — inter-symbol
interference — and equalizing that in a single wideband carrier is brutally hard.**
**⚠️ The solution**: **split the channel into many narrow, orthogonal subcarriers, each
carrying a low-rate stream.** ⚠️ **Each subcarrier's symbol is now long compared to the
delay spread, and a CYCLIC PREFIX (guard interval) absorbs the remaining echo.**
**⚠️ And it's cheap because it's an FFT.** **Modulation and demodulation are IFFT/FFT
operations, which is precisely why OFDM became practical when DSP got fast enough.**
**⚠️ The costs**: **high peak-to-average power ratio (PAPR), demanding linear amplifiers
and hurting efficiency** — ⚠️ **which is why uplinks sometimes use SC-FDMA instead** —
**and sensitivity to frequency offset and phase noise.**
**OFDMA** (Wi-Fi 6+, LTE) — ⚠️ **allocates subsets of subcarriers to different users,
so several small devices share one transmission instead of each taking a full turn.**
**This is a capacity/efficiency feature, not a speed feature.**

---

## §12. Coding and Retransmission

**⚠️ Every real radio link is running errors and correcting them beneath you.**
```
FEC    ⚠️ forward error correction — add redundancy so errors are fixed
       without retransmission. Convolutional/Viterbi, Reed-Solomon,
       ⚠️ Turbo and LDPC (near-Shannon; LDPC in Wi-Fi, 5G), Polar (5G control)
CRC    ⚠️ DETECTS errors; does not correct them
INTERLEAVING  ⚠️ scatter bits in time so a BURST error becomes many
       single-bit errors that FEC can handle. Essential against fading (§6)
ARQ    retransmission. ⚠️ HARQ combines retransmissions with the failed
       copy rather than discarding it — used throughout LTE/5G
```
**⚠️ Coding gain is real and large**: **a good FEC can buy 5–10 dB, which by §3 → `radio-intuitions-spectrum-link-budget-and-tradeoffs` is
several times the range.** ⚠️ **It costs data rate and latency, which is why low-latency
modes use weaker coding.**

---

## §13. Multiple Access

```
FDMA / TDMA / CDMA / OFDMA / SDMA   ⚠️ divide by frequency, time, code,
   subcarrier, or space (beamforming/MIMO)
⚠️ CSMA/CA   listen before transmit, random backoff — Wi-Fi. ⚠️ Note
   CSMA/CD (collision DETECTION, from Ethernet) is IMPOSSIBLE on radio:
   you cannot hear a collision while transmitting
ALOHA        ⚠️ just transmit and hope. LoRaWAN. Simple; capacity collapses
   under load — classic ALOHA tops out around 18% channel utilization
```
> **⚠️ GOTCHA — the hidden node problem is the classic wireless-only failure and it has
> no wired analogue.** ⚠️ **A and C can both hear B but not each other, so both sense the
> channel as clear and both transmit, colliding at B.** **Carrier sensing cannot fix
> this** — **RTS/CTS can, at a cost in overhead.** **Symptom: throughput collapses when a
> particular pair of nodes is active, and each node's local view looks fine.**

---

# PART II — SOFTWARE-DEFINED RADIO

---

## §14. ⚠️ SDR and IQ Sampling

**⚠️ The concept that makes radio tractable for software people, and the one most
tutorials explain badly.**

```
        ┌─────────┐   ┌──────┐   ┌─────┐   ┌──────────────┐
RF ────►│ LNA/Mix │──►│ Filt │──►│ ADC │──►│ YOUR SOFTWARE│
        └─────────┘   └──────┘   └─────┘   └──────────────┘
        ⚠️ hardware shrinks; software grows
```
**⚠️ IQ (complex baseband) is the key idea.** **The radio mixes the signal down so the
carrier is at 0 Hz, producing two streams: I (in-phase) and Q (quadrature, 90° shifted).**
⚠️ **Together they form a COMPLEX number per sample.**
**⚠️ Why complex, concretely:**
- ⚠️ **A real-valued signal cannot distinguish +10 kHz from −10 kHz relative to the
  carrier.** **The complex representation can, so you get the full spectrum around your
  tuned frequency rather than a folded-over version.**
- ⚠️ **Amplitude = |I + jQ|; phase = atan2(Q, I).** **Every modulation in §8 → `radio-antennas-propagation-noise-and-modulation` becomes
  arithmetic on complex numbers.**
- **A constellation diagram is literally a scatter plot of your IQ samples.**
- ⚠️ **Sample rate = the bandwidth you can see.** **A 2 Msps complex stream gives you
  2 MHz of spectrum, centred on your tuning frequency.**

**⚠️ Practical gotchas that will confuse you first time:**
- **⚠️ DC spike at centre frequency** — **an artefact of direct-conversion receivers (LO
  leakage), not a real signal.** **Tune slightly off-target to avoid burying your signal
  under it.**
- **⚠️ IQ imbalance produces mirror images of real signals** reflected about the centre.
- **⚠️ Automatic gain control will lie to you about absolute power.**
- **⚠️ Overflow/dropped samples**: **if your processing can't keep up, samples are simply
  lost, and the symptom is corrupt demodulation rather than an error message.**

---

## §15. Sampling and DSP Essentials

```
⚠️ NYQUIST      sample rate must exceed 2× the signal BANDWIDTH.
   ⚠️ For complex/IQ sampling, sample rate = bandwidth (not 2×) —
   the complex representation already carries the sign of frequency
ALIASING        ⚠️ under-sampled content folds back and is indistinguishable
   from real signal. Anti-alias filtering is mandatory, not optional
DECIMATION      ⚠️ filter THEN downsample. Downsampling without filtering
   first aliases — the single most common beginner DSP bug
INTERPOLATION   upsample and filter
FFT             ⚠️ time → frequency. Bin width = sample rate / FFT size.
   ⚠️ WINDOWING (Hann, Blackman) reduces spectral leakage from the implicit
   rectangular window; without it a strong tone smears across bins
FILTERS         FIR (⚠️ linear phase, stable, more taps) vs IIR (efficient,
   phase distortion). ⚠️ For radio, linear phase usually matters
```
**⚠️ The receive chain in software, in order**: **tune → sample (IQ) → filter to the
signal's bandwidth → decimate → correct frequency offset → time-synchronize → equalize →
demodulate to symbols → decode (FEC) → deframe → CRC.**
⚠️ **Synchronization is where most of the difficulty lives.** **Your oscillator and theirs
disagree — carrier frequency offset, sample timing offset, and phase — and estimating and
tracking those is the bulk of a real demodulator.**

---

## §16. SDR Toolchain

```
⚠️ RTL-SDR       ~$30, RX only, ~24–1766 MHz, 8-bit, ~2.4 MHz BW.
   ⚠️ Start here. A repurposed TV tuner and genuinely capable for learning
HackRF One       ~$300, TX+RX (half duplex), 1 MHz–6 GHz, 8-bit, 20 MHz
LimeSDR / PlutoSDR  mid-range, full duplex, better ADCs
USRP (Ettus)     ⚠️ research/production grade, expensive, excellent
BladeRF          mid-high

SOFTWARE
⚠️ GNU Radio     flowgraph-based DSP framework. The standard. Python/C++ blocks
SoapySDR         ⚠️ hardware abstraction — write once, swap radios
GQRX / SDR++ / SDRangel   general-purpose receivers and spectrum viewing
Inspectrum       ⚠️ excellent for visually reverse-engineering a capture
Universal Radio Hacker  ⚠️ purpose-built for protocol reverse engineering
liquid-dsp / NumPy+SciPy   ⚠️ roll your own; NumPy is fine for offline work
srsRAN / OpenAirInterface  open-source LTE/5G stacks
```
**⚠️ A learning path that actually works**: **receive FM broadcast (proves the chain) →
decode ADS-B aircraft transponders at 1090 MHz (real digital demodulation, instant visible
results) → decode a 433 MHz sensor around your home (OOK, simple, and it teaches framing)
→ then attempt transmit — carefully, and see §23 → `radio-regulatory-security-and-debugging` first.**

---

# PART III — PROTOCOLS
