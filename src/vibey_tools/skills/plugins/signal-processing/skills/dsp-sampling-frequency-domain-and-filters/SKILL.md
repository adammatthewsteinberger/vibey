---
name: dsp-sampling-frequency-domain-and-filters
description: "Use when starting on anything that samples the physical world: sampling and the Nyquist–Shannon theorem, aliasing, quantization and dither, the frequency domain and its transforms (DFT, FFT, STFT), the DFT facts that bite — windowing, spectral leakage, frequency resolution and the time-frequency uncertainty trade — and filter design including the FIR versus IIR decision. Includes the router for the whole signal-processing reference."
---

# Signal Processing: Sampling and Quantization, the Frequency Domain, and Filters

> **Part 1 of 5** of the *Signal Processing* reference (plugin `signal-processing`), covering §0–§3. Sibling skills: `dsp-convolution-multirate-and-spectral-analysis` (§4–§7), `dsp-audio-rf-and-images` (§8–§10), `dsp-implementation-tools-and-testing` (§11–§14), `dsp-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 → `dsp-reference` for the currency snapshot and what goes stale first.

> **How to read this.** Reference for engineers who need DSP working, not a course. Three
> markers:
> - **[DURABLE]** — sampling theory, transforms, filters, estimation. **Nyquist is 1928;
>   Shannon 1949; the Cooley–Tukey FFT 1965. This material does not expire.**
> - **[VERSIONED]** — codecs, libraries, hardware, the ML layer.
> - **[CONTESTED]** — genuine disagreement.
>
> **⚠️ GOTCHA** boxes mark where the code runs, the plot looks fine, and the answer is
> wrong.
>
> **The three framings that organize everything below:**
> 1. **Everything is a trade between time and frequency resolution, and you cannot cheat
>    it.** The uncertainty principle is not a metaphor here — **a short window gives you
>    good time resolution and poor frequency resolution, and no amount of cleverness
>    escapes that** (§2.4). Most DSP design is choosing where on that curve to sit.
> 2. **⚠️ Aliasing is irreversible.** Once you've sampled too slowly, the information is
>    gone — no filter, no algorithm, and no neural network recovers it. **This is the one
>    mistake in this document that cannot be fixed downstream** (§1).
> 3. **The field is mid-convergence with machine learning, and the interesting result is
>    that hybrids are winning** — not pure DSP, and not pure end-to-end learning.
>    ⚠️ **The pattern that keeps recurring: use DSP for the structure you know, and learn
>    the parameters you can't hand-tune** (§8 → `dsp-audio-rf-and-images`, §16.1 → `dsp-reference`).

---

## §0. Routing

| Asked about... | Go to |
|---|---|
| **Sampling, aliasing, quantization** | **§1** |
| The frequency domain, FFT, windowing | §2 |
| Filters — design and choice | §3 |
| Convolution and correlation | §4 → `dsp-convolution-multirate-and-spectral-analysis` |
| Multirate: resampling, decimation | §5 → `dsp-convolution-multirate-and-spectral-analysis` |
| Adaptive filtering and estimation | §6 → `dsp-convolution-multirate-and-spectral-analysis` |
| Spectral analysis and time-frequency | §7 → `dsp-convolution-multirate-and-spectral-analysis` |
| **Audio and speech** | **§8 → `dsp-audio-rf-and-images`** |
| RF and communications | §9 → `dsp-audio-rf-and-images` |
| Images and video | §10 → `dsp-audio-rf-and-images` |
| Implementation: fixed point, real-time | §11 → `dsp-implementation-tools-and-testing` |
| Tools and libraries | §12 → `dsp-implementation-tools-and-testing` |
| Testing and debugging DSP | §13 → `dsp-implementation-tools-and-testing` |
| Sensors and physical signals | §14 → `dsp-implementation-tools-and-testing` |
| "Don't do this" | §15 → `dsp-reference` |
| "Which side is right?" | §16 → `dsp-reference` |
| "Is this still current?" | §17 → `dsp-reference` |
| Books and people | §18 → `dsp-reference` |

---

## §1. Sampling and Quantization

**[DURABLE] The foundation, and the source of the most expensive mistakes.**

### 1.1 Nyquist–Shannon

**A signal band-limited to B Hz is perfectly reconstructable from samples taken at
> 2B Hz.** ⚠️ **Note the strictness: strictly greater than, and strictly band-limited.**

> **⚠️ GOTCHA — aliasing, and why it's the worst bug in this document.** Frequency
> components above Nyquist **do not disappear — they fold back and appear as lower
> frequencies that are indistinguishable from real signal.** A 30 kHz tone sampled at
> 44.1 kHz appears at 14.1 kHz. **It looks like data. It is not.**
>
> **⚠️ The fix must happen in the analog domain, before the ADC.** An **anti-aliasing
> filter** is a hardware component. **Once aliased, always aliased** — there is no
> software repair, and this is the single most important operational fact in DSP.
>
> **The same applies when you downsample in software** (§5 → `dsp-convolution-multirate-and-spectral-analysis`): ⚠️ **decimating without
> low-pass filtering first is aliasing you inflicted on yourself.**

**⚠️ And the corollaries people miss**: sampling a signal that isn't band-limited
(virtually everything real) aliases the noise floor too; **sampling exactly at 2B is not
enough** (a sine sampled at its zero crossings gives you nothing); and **jitter in the
sample clock is itself a noise source** — timing uncertainty translates directly into
amplitude error, and it dominates at high frequencies.

**Oversampling** deliberately samples well above Nyquist to relax the analog filter
requirements and spread quantization noise over a wider band. **Sigma-delta converters**
push this to an extreme with noise shaping — ⚠️ **which is why a 1-bit converter at very
high rate can outperform a 16-bit converter at Nyquist.**

### 1.2 Quantization

**[DURABLE] Amplitude discretization.** The rule of thumb: **~6 dB of SNR per bit.**
16-bit ≈ 96 dB, 24-bit ≈ 144 dB (⚠️ **in theory — real converters are limited by analog
noise well before that**).

**⚠️ Quantization error is only noise-like if the signal is busy enough.** For quiet or
slowly-varying signals it becomes **correlated with the signal and audible as distortion**.
**Dither** — adding a small amount of noise before quantizing — **decorrelates the error
and trades distortion for a slightly raised noise floor.** ⚠️ **It sounds absurd and it is
correct: adding noise makes it sound better.** **Noise shaping** pushes that noise into
frequency bands where it matters less perceptually.

**Also**: **clipping** is a hard nonlinearity that generates broadband harmonics —
⚠️ **leave headroom**; **DC offset** eats dynamic range and breaks many algorithms
(high-pass it out); and **float vs. fixed** is §11 → `dsp-implementation-tools-and-testing`.

---

## §2. The Frequency Domain

### 2.1 The transforms

**[DURABLE]** **Fourier series** (periodic), **Fourier transform** (continuous, infinite),
**DTFT** (discrete-time, continuous frequency), **DFT** (discrete both — ⚠️ **what you can
actually compute**), and the **FFT**, which is an algorithm for the DFT, not a different
transform. **O(n log n) versus O(n²)** — and that reduction is arguably the single most
consequential algorithm in engineering.

**Related transforms**: **DCT** (real-valued, energy-compacting — ⚠️ **the basis of JPEG
and MP3/AAC**), **MDCT** (overlapping, critically sampled — ⚠️ **what modern audio codecs
actually use**), **Hilbert** (analytic signal, envelope, instantaneous phase),
**wavelets** (multi-resolution — §7 → `dsp-convolution-multirate-and-spectral-analysis`), and the **Z-transform** (the discrete analogue of
Laplace, and the language of filter design — §3).

### 2.2 ⚠️ The DFT facts that bite

> **⚠️ GOTCHA — every one of these produces a wrong plot that looks plausible:**
> - **⚠️ The DFT assumes your signal is periodic with period N.** It isn't. The
>   discontinuity between the last sample and the first creates **spectral leakage** —
>   energy smeared across all bins.
> - **Windowing is the mitigation, and it has a cost.** Multiplying by a taper (Hann,
>   Hamming, Blackman–Harris, Kaiser) reduces leakage **and widens the main lobe**, so you
>   trade frequency resolution for dynamic range. ⚠️ **Rectangular (no window) has the
>   narrowest main lobe and the worst sidelobes — it's the right choice only when your
>   signal is genuinely periodic in the window.**
> - **Bin spacing is fs/N.** ⚠️ **A frequency between bins spreads across neighbours —
>   "scalloping loss."** This is why a pure tone rarely shows as a single clean spike.
> - **⚠️ Zero-padding does not add resolution.** It interpolates the spectrum — smoother
>   plot, same underlying resolution. **The resolution is set by the observation duration,
>   full stop.**
> - **Normalization conventions differ between libraries** — where the 1/N goes.
>   ⚠️ **Check before comparing magnitudes across tools.**
> - **Real input → conjugate-symmetric spectrum.** Use `rfft` and halve your work.
> - **⚠️ The FFT is fastest for highly composite N** (powers of two ideally). A prime N
>   falls back to a slower path — in older or naive implementations, dramatically slower.

### 2.3 Frequency resolution
**Δf = fs/N = 1/T**, where **T is the observation duration.** ⚠️ **This is the whole story:
to resolve two tones 1 Hz apart you need at least one second of data.** No window, no
zero-padding, and no algorithm changes it — though **parametric methods (§7.3 → `dsp-convolution-multirate-and-spectral-analysis`) can beat it
by assuming a model.**

### 2.4 The uncertainty trade
**[DURABLE] Δt · Δf ≥ constant.** Short windows localize events in time and blur them in
frequency; long windows do the reverse. ⚠️ **Every spectrogram you have ever looked at is a
choice on this curve**, and picking the window length is the main design decision in
time-frequency analysis (§7 → `dsp-convolution-multirate-and-spectral-analysis`).

---

## §3. Filters

**[DURABLE] The core tool. Choose the class first, then the design method.**

### 3.1 FIR vs. IIR — the decision that matters

| | **FIR** | **IIR** |
|---|---|---|
| Feedback | None | Yes |
| **Stability** | ⚠️ **Always stable** | ⚠️ **Can be unstable; must check poles** |
| **Phase** | ⚠️ **Exactly linear phase available** (symmetric taps) | Nonlinear phase; group delay varies |
| Order for a given sharpness | ⚠️ **Much higher** | Much lower — often 10× fewer coefficients |
| Fixed-point behaviour | Well-behaved | ⚠️ **Coefficient quantization can destabilize** |
| Analogue equivalent | None | Butterworth, Chebyshev, Elliptic, Bessel |

**⚠️ The decision rule**: **linear phase required (audio, images, anything where waveform
shape matters)? FIR.** **Tight compute budget and phase doesn't matter (control loops,
simple smoothing)? IIR.**

### 3.2 Design

**FIR methods**: **windowed sinc** (simple, adequate), **Parks–McClellan / Remez**
(⚠️ **optimal equiripple for a given order — the professional default**), **least
squares**, **frequency sampling**.

**IIR methods**: design in the analogue domain and transform — **bilinear transform**
(⚠️ **warps frequency; pre-warp your critical frequencies or your cutoff lands in the wrong
place**), or **impulse invariance**. The classical families: **Butterworth** (maximally
flat passband), **Chebyshev I/II** (ripple traded for steeper rolloff), **Elliptic**
(steepest, ripple everywhere), **Bessel** (⚠️ **maximally flat *group delay* — the one to
use when waveform shape matters more than magnitude**).

**⚠️ Always implement high-order IIR as cascaded second-order sections (biquads / SOS).**
A direct-form high-order IIR is numerically fragile and can be unstable purely from
coefficient quantization. ⚠️ **`scipy.signal` defaults to transfer-function output for
historical reasons — ask for `output='sos'`.**

### 3.3 The specifics worth knowing
**Group delay** is the derivative of phase — ⚠️ **it's what actually smears your waveform,
and it's frequency-dependent for IIR.** **Filtfilt / zero-phase filtering** runs the filter
forwards and backwards to cancel phase — ⚠️ **excellent offline, impossible in real time,
and it squares the magnitude response** (so your -3 dB point moves). **Transient response**
at startup matters for short signals. And the everyday filters: **moving average**
(⚠️ **the crudest low-pass; its frequency response is a sinc with poor stopband**),
**exponential/one-pole** (cheap, adequate), **median** (nonlinear; ⚠️ **excellent for
impulsive noise where linear filters smear it**), **Savitzky–Golay** (⚠️ **smooths while
preserving peak shape — the right choice for spectroscopy and chromatography**),
**notch** for mains hum, **DC blocker**, **all-pass** for phase shaping.
