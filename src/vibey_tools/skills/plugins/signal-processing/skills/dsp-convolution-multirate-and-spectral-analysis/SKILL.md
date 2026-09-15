---
name: dsp-convolution-multirate-and-spectral-analysis
description: "Use when processing or analyzing a sampled signal: convolution and correlation including fast convolution via the FFT and overlap-add and overlap-save, multirate processing (decimation, interpolation, polyphase, resampling), adaptive filtering and estimation (LMS, RLS, Kalman, Wiener), and spectral analysis and time-frequency methods including Welch's method and wavelets."
---

# Signal Processing: Convolution, Multirate, Adaptive Filtering, and Spectral Analysis

> **Part 2 of 5** of the *Signal Processing* reference (plugin `signal-processing`), covering §4–§7. Sibling skills: `dsp-sampling-frequency-domain-and-filters` (§0–§3), `dsp-audio-rf-and-images` (§8–§10), `dsp-implementation-tools-and-testing` (§11–§14), `dsp-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    escapes that** (§2.4 → `dsp-sampling-frequency-domain-and-filters`). Most DSP design is choosing where on that curve to sit.
> 2. **⚠️ Aliasing is irreversible.** Once you've sampled too slowly, the information is
>    gone — no filter, no algorithm, and no neural network recovers it. **This is the one
>    mistake in this document that cannot be fixed downstream** (§1 → `dsp-sampling-frequency-domain-and-filters`).
> 3. **The field is mid-convergence with machine learning, and the interesting result is
>    that hybrids are winning** — not pure DSP, and not pure end-to-end learning.
>    ⚠️ **The pattern that keeps recurring: use DSP for the structure you know, and learn
>    the parameters you can't hand-tune** (§8 → `dsp-audio-rf-and-images`, §16.1 → `dsp-reference`).

---

## §4. Convolution and Correlation

**[DURABLE] Convolution is what a linear time-invariant system *does*.** Output = input
convolved with impulse response. ⚠️ **Everything in §3 → `dsp-sampling-frequency-domain-and-filters` is convolution.**

**The convolution theorem**: convolution in time is multiplication in frequency.
**Practically: for long filters, FFT-based convolution beats direct convolution** —
crossover typically around 50–100 taps depending on implementation.
**⚠️ Overlap-add and overlap-save** are how you apply FFT convolution to a continuous
stream without processing the whole signal at once. **Partitioned convolution** gives you
low latency with long impulse responses — ⚠️ **which is how real-time convolution reverb
with a multi-second impulse response is possible at all.**

**⚠️ Circular vs. linear convolution is the classic FFT bug**: the FFT gives you circular
convolution, which wraps around. **Zero-pad both inputs to at least N+M-1** or your output
is corrupted at the edges in a way that looks like a subtle artifact rather than an error.

**Correlation** is convolution with one input reversed. **Cross-correlation for time
delay estimation and template matching** (⚠️ **and GCC-PHAT is the standard for acoustic
time-difference-of-arrival**), **autocorrelation for periodicity and pitch**, and
**matched filtering** — ⚠️ **provably optimal for detecting a known signal in white noise,
and the basis of radar, sonar, and GPS.**

---

## §5. Multirate

**[DURABLE] Changing sample rate correctly, which people routinely get wrong.**

**Decimation (downsampling by M)**: ⚠️ **low-pass filter FIRST, then discard samples.**
Skipping the filter aliases (§1.1 → `dsp-sampling-frequency-domain-and-filters`). **Interpolation (upsampling by L)**: insert zeros, then
low-pass to remove the spectral images. **Rational resampling by L/M**: upsample, filter
once, downsample — ⚠️ **and the single filter does both jobs; don't do it in two stages.**

**Polyphase decomposition** restructures this so you never compute samples you're about to
discard — ⚠️ **an M-fold efficiency win, and it's what every real resampler does.**

**⚠️ Arbitrary-ratio resampling** (44.1 → 48 kHz, the classic) needs fractional-delay
interpolation — **Farrow structures, or windowed-sinc interpolation.** ⚠️ **Quality varies
enormously between implementations; a cheap resampler is an audible one.** Libraries:
**libsamplerate/SoX/r8brain** for audio, `scipy.signal.resample_poly` (⚠️ **use
`resample_poly`, not `resample` — the latter assumes periodicity and rings at the edges**).

**Related structures**: **CIC filters** (⚠️ **multiplier-free, the standard front end in
sigma-delta and SDR hardware**), **half-band filters** (half the taps are zero),
**filter banks and the STFT** as a multirate system (§7).

---

## §6. Adaptive Filtering and Estimation

**[DURABLE] When the filter must learn its own coefficients.**

**LMS** — gradient descent on the error. ⚠️ **Simple, cheap, robust, and the workhorse.
Its convergence depends on the step size and on the input's eigenvalue spread**; NLMS
normalizes for input power and is what you should actually use. **RLS** — much faster
convergence, O(n²) per sample, ⚠️ **and numerically fragile.** **Frequency-domain adaptive
filters** for long responses.

**Applications, and the pattern is the same in all of them**: **echo cancellation**
(⚠️ **model the echo path, subtract the prediction** — §8.3 → `dsp-audio-rf-and-images`), **noise cancellation** with a
reference mic, **channel equalization** (§9 → `dsp-audio-rf-and-images`), **system identification**, and
**line enhancement**.

**Kalman filtering** is the optimal recursive estimator for linear-Gaussian systems —
⚠️ **and the crossover point where signal processing becomes state estimation.** EKF, UKF,
and particle filters for nonlinear cases. **Wiener filtering** is the optimal
*non-adaptive* linear filter given known spectra, and it remains the theoretical baseline
that §8 → `dsp-audio-rf-and-images`'s learned enhancers are measured against.

**⚠️ The recurring practical failures**: **step size too large diverges, too small never
converges**; **double-talk** in echo cancellation (⚠️ **when both ends speak, adaptation
must freeze or the filter destroys itself** — a double-talk detector is mandatory);
**insufficient excitation** means the filter can't identify what it can't hear; and
**non-stationarity** breaks the assumptions everything rests on.

---

## §7. Spectral Analysis and Time-Frequency

**7.1 Estimating a spectrum properly.** ⚠️ **A single FFT magnitude is a terrible spectral
estimator** — its variance doesn't decrease with more data. **Welch's method** (average
periodograms over overlapping windows) trades resolution for variance reduction and is the
correct default. **Bartlett** is the non-overlapping version; **multitaper** (Thomson)
uses orthogonal windows and is the best general-purpose estimator when you can afford it.

**7.2 Time-frequency.** **STFT/spectrogram** — ⚠️ **fixed resolution at every frequency,
which is its central limitation.** **Wavelets** and **constant-Q transforms** give
finer time resolution at high frequencies and finer frequency resolution at low —
⚠️ **which matches both human hearing and most physical signals, and is why CQT is
preferred for music.** **Wigner-Ville** has excellent resolution and ⚠️ **cross-term
artifacts that look like real components.** **Mel spectrograms** warp frequency
perceptually and are the standard input representation for speech ML (§8 → `dsp-audio-rf-and-images`).

**7.3 Parametric methods** — ⚠️ **these beat the fs/N resolution limit by assuming a
model.** **MUSIC** and **ESPRIT** for sinusoids in noise (the basis of direction-of-arrival
estimation), **AR/Burg** modelling, **matrix pencil**. ⚠️ **The catch: if the model order
is wrong or the model doesn't fit, they produce confident nonsense** — spurious peaks that
look exactly like real ones.

**7.4 Detection and estimation.** **Matched filtering** (§4), **CFAR detectors** for radar,
**ROC curves** for the detection/false-alarm trade, and **the Cramér–Rao bound** —
⚠️ **which tells you the best variance any unbiased estimator can achieve, so you know when
to stop trying to improve your estimator.**
