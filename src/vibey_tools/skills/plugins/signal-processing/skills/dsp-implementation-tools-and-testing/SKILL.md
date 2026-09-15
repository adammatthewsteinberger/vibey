---
name: dsp-implementation-tools-and-testing
description: "Use when getting DSP to run correctly on real hardware: implementation (fixed-point arithmetic and Q formats, overflow and saturation, real-time constraints, block processing), the tool landscape (NumPy and SciPy, MATLAB, GNU Radio, JUCE, CMSIS-DSP), testing and debugging DSP against known signals and reference implementations, and sensors and physical signals including calibration and drift."
---

# Signal Processing: Implementation, Tools, Testing, and Physical Sensors

> **Part 4 of 5** of the *Signal Processing* reference (plugin `signal-processing`), covering §11–§14. Sibling skills: `dsp-sampling-frequency-domain-and-filters` (§0–§3), `dsp-convolution-multirate-and-spectral-analysis` (§4–§7), `dsp-audio-rf-and-images` (§8–§10), `dsp-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §11. Implementation

**[DURABLE] Where DSP theory meets the hardware budget.**

**Fixed point** — ⚠️ **still standard on MCUs, DSP chips, and in FPGA/ASIC.**
**Q notation** (Q15, Q31) describes where the binary point sits. **The failure modes**:
**overflow** (⚠️ **use saturating arithmetic — wraparound turns a loud sound into a
horrible one**), **underflow and loss of precision** in cascades, and ⚠️ **coefficient
quantization changing your filter's response — and in IIR, potentially its stability**
(§3.2 → `dsp-sampling-frequency-domain-and-filters`). **Always simulate in fixed point before committing to hardware.**

**⚠️ Denormals**: on some CPUs, arithmetic on denormal floats runs **orders of magnitude
slower**. In a decaying IIR filter this manifests as **CPU spikes when the signal goes
quiet** — a genuinely confusing symptom. **Enable flush-to-zero, or inject tiny dither.**

**Real-time constraints**: fixed block size, **⚠️ no allocation, no locks, and no
unbounded operations in the audio callback** — this is a hard-real-time thread, and a
`malloc` or a mutex in it produces dropouts. **Lock-free ring buffers** to communicate with
other threads. **Latency = block size + algorithmic delay + hardware buffering.**

**Hardware**: **SIMD** (⚠️ **DSP vectorizes exceptionally well — this is often a 4–8×
win**), **DSP cores** (TI C6000, ADI SHARC), **ARM CMSIS-DSP** on Cortex-M (⚠️ **and the
M4F/M7 DSP extensions make surprisingly capable audio possible on a microcontroller**),
**FPGA** for extreme throughput or determinism, and **GPU** for large batch or image work
(⚠️ **but usually the wrong answer for low-latency streaming audio because of transfer
overhead**).

---

## §12. Tools

**Python**: **`scipy.signal`** (⚠️ **the practical default — and remember `output='sos'`
and `resample_poly`**), **NumPy**, **`librosa`** (music/audio analysis),
**`python-soundfile`**, **`pyFFTW`**, **`torchaudio`**.
**MATLAB**: the **Signal Processing** and **DSP System** toolboxes are genuinely excellent
and remain an industry standard, with a real Simulink-to-hardware path.
**C/C++**: **FFTW** (⚠️ **the reference FFT; note the GPL/commercial licensing**),
**KissFFT** (permissive, simple), **CMSIS-DSP**, **JUCE** (audio applications),
**liquid-dsp** (SDR), **Eigen**.
**Julia**: `DSP.jl`, `FFTW.jl`. **GNU Radio** for SDR flowgraphs (§9 → `dsp-audio-rf-and-images`).
**Analysis**: **Audacity**, **Sonic Visualiser**, **REW**, **Inspectrum**, and
⚠️ **a spectrum analyzer plugin of some kind is the single most useful debugging tool in
audio work** (§13).

---

## §13. Testing and Debugging DSP

**[DURABLE] The discipline, and it's underdeveloped in most codebases.**

**⚠️ Test with known signals first, always**: an impulse (gives you the impulse response
directly), a step, a pure sine at a known frequency and amplitude, white noise (⚠️ **which
should give you a flat spectrum — if it doesn't, your analysis is wrong before your
algorithm is**), and a **chirp/sweep** to get the frequency response in one shot.

**Verify the properties you can check cheaply**: **Parseval's theorem** (⚠️ **energy in
time equals energy in frequency — a superb catch-all for scaling and normalization bugs**),
**linearity and time-invariance** where they should hold, **DC gain**, **group delay**, and
**round-trip identity** (analyze then synthesize should reconstruct).

**⚠️ Look at the signal.** Plot the waveform, the spectrum, and the spectrogram. **Most DSP
bugs are instantly visible and invisible in numbers** — and for audio, **listen to it**.
The ear detects artifacts that no metric flags.

**⚠️ The specific bugs to check for first**: **off-by-one in window alignment or overlap**;
**scaling factors** from FFT normalization; **edge effects** at buffer boundaries
(⚠️ **the classic: filter state not carried between blocks, giving a click at every block
boundary**); **circular convolution wraparound** (§4 → `dsp-convolution-multirate-and-spectral-analysis`); **complex conjugate and sign
conventions**; **and phase unwrapping**.

**Metrics**: SNR, THD, THD+N, SINAD, ENOB for converters; **PESQ, POLQA, STOI, SI-SDR**
for speech quality — ⚠️ **and the honest caveat that these correlate imperfectly with human
judgement, which is why subjective MOS testing persists.**

---

## §14. Sensors and Physical Signals

**⚠️ The physical layer determines what's possible, and it's often mishandled in
software-first teams.** **Transducer characteristics** — sensitivity, frequency response,
nonlinearity, drift — **bound your entire system**; no filter fixes a bad sensor.
**Calibration** matters and drifts with temperature and time. **Grounding, shielding, and
mains hum** at 50/60 Hz and harmonics are the most common contaminants in instrumentation.
**Anti-aliasing before the ADC** (§1.1 → `dsp-sampling-frequency-domain-and-filters`). **Common-mode rejection** in differential
measurements. **Noise types**: thermal/Johnson (white), shot, **1/f flicker**
(⚠️ **dominant at low frequencies and the reason DC measurements are hard**), and
quantization (§1.2 → `dsp-sampling-frequency-domain-and-filters`).

**Domain notes**: **biomedical** — ECG (baseline wander, mains, muscle artifact), EEG
(⚠️ **microvolt-level, and eye-blink artifacts dominate**), PPG (motion artifact);
**vibration and machinery** — envelope analysis for bearing faults, order tracking;
**seismic and geophysical** — deconvolution; **radar/lidar** — matched filtering and
pulse compression.
