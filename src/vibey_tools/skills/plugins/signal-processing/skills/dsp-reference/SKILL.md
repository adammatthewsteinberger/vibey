---
name: dsp-reference
description: "Use when checking a DSP anti-pattern, weighing a contested question, confirming whether a claim about the classical-versus-learned audio convergence is still current (snapshot verified August 2026), finding the books, primary sources and people, or needing the numbers, a method picker, and the when-it-sounds-or-looks-wrong list. Companion to the other signal-processing skills."
---

# Signal Processing: Anti-Patterns, Contested Questions, Currency, and Canon

> **Part 5 of 5** of the *Signal Processing* reference (plugin `signal-processing`), covering §15–§20. Sibling skills: `dsp-sampling-frequency-domain-and-filters` (§0–§3), `dsp-convolution-multirate-and-spectral-analysis` (§4–§7), `dsp-audio-rf-and-images` (§8–§10), `dsp-implementation-tools-and-testing` (§11–§14). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 below for the currency snapshot and what goes stale first.

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
>    the parameters you can't hand-tune** (§8 → `dsp-audio-rf-and-images`, §16.1).

---

## §15. Anti-Patterns

| Anti-pattern | Why |
|---|---|
| **Sampling without an analogue anti-aliasing filter** | ⚠️ **Irreversible. Nothing downstream fixes it** (§1.1 → `dsp-sampling-frequency-domain-and-filters`) |
| Downsampling without low-pass filtering first | ⚠️ **Self-inflicted aliasing** (§5 → `dsp-convolution-multirate-and-spectral-analysis`) |
| Sampling exactly at 2×B | Nyquist is a strict inequality (§1.1 → `dsp-sampling-frequency-domain-and-filters`) |
| Ignoring sample-clock jitter | Timing uncertainty becomes amplitude noise (§1.1 → `dsp-sampling-frequency-domain-and-filters`) |
| Quantizing without dither on quiet signals | Error correlates with signal → audible distortion (§1.2 → `dsp-sampling-frequency-domain-and-filters`) |
| No headroom | Clipping generates broadband harmonics (§1.2 → `dsp-sampling-frequency-domain-and-filters`) |
| Assuming zero-padding adds resolution | ⚠️ **It interpolates. Resolution = 1/T** (§2.2 → `dsp-sampling-frequency-domain-and-filters`) |
| Rectangular window on a non-periodic signal | Spectral leakage across all bins (§2.2 → `dsp-sampling-frequency-domain-and-filters`) |
| Comparing FFT magnitudes across libraries | Normalization conventions differ (§2.2 → `dsp-sampling-frequency-domain-and-filters`) |
| A single periodogram as a spectral estimate | ⚠️ **Variance doesn't shrink with data. Use Welch** (§7.1 → `dsp-convolution-multirate-and-spectral-analysis`) |
| High-order IIR in direct form | ⚠️ **Numerically fragile. Use cascaded biquads/SOS** (§3.2 → `dsp-sampling-frequency-domain-and-filters`) |
| Bilinear transform without pre-warping | Your cutoff lands in the wrong place (§3.2 → `dsp-sampling-frequency-domain-and-filters`) |
| `filtfilt` in a real-time path | Non-causal by construction (§3.3 → `dsp-sampling-frequency-domain-and-filters`) |
| Moving average as a serious low-pass | Sinc response, poor stopband (§3.3 → `dsp-sampling-frequency-domain-and-filters`) |
| Linear filter for impulsive noise | ⚠️ **It smears it. Use a median filter** (§3.3 → `dsp-sampling-frequency-domain-and-filters`) |
| FFT convolution without zero-padding to N+M-1 | ⚠️ **Circular wraparound corrupts the edges** (§4 → `dsp-convolution-multirate-and-spectral-analysis`) |
| Not carrying filter state across blocks | ⚠️ **A click at every block boundary** (§13 → `dsp-implementation-tools-and-testing`) |
| `scipy.signal.resample` for audio | Assumes periodicity; rings at the edges. Use `resample_poly` (§5 → `dsp-convolution-multirate-and-spectral-analysis`) |
| LMS step size chosen by guess | Diverges or never converges (§6 → `dsp-convolution-multirate-and-spectral-analysis`) |
| Echo cancellation without double-talk detection | ⚠️ **The filter destroys itself when both sides speak** (§6 → `dsp-convolution-multirate-and-spectral-analysis`, §8.3 → `dsp-audio-rf-and-images`) |
| Parametric spectral estimate with wrong model order | ⚠️ **Confident spurious peaks** (§7.3 → `dsp-convolution-multirate-and-spectral-analysis`) |
| Wigner-Ville cross-terms read as real components | Artifacts of the transform (§7.2 → `dsp-convolution-multirate-and-spectral-analysis`) |
| Allocation, locks, or logging in the audio callback | Hard real-time thread → dropouts (§11 → `dsp-implementation-tools-and-testing`) |
| Ignoring denormals in a decaying IIR | ⚠️ **CPU spikes when the signal goes quiet** (§11 → `dsp-implementation-tools-and-testing`) |
| Fixed-point port without simulating first | Coefficient quantization can destabilize IIR (§11 → `dsp-implementation-tools-and-testing`) |
| Wraparound instead of saturating arithmetic | A loud sound becomes a horrible one (§11 → `dsp-implementation-tools-and-testing`) |
| Trusting PESQ/STOI as ground truth | ⚠️ **They correlate imperfectly with human judgement** (§13 → `dsp-implementation-tools-and-testing`) |
| Never plotting the spectrogram | ⚠️ **Most DSP bugs are visible and only visible** (§13 → `dsp-implementation-tools-and-testing`) |
| Never listening to the audio | The ear catches what metrics miss (§13 → `dsp-implementation-tools-and-testing`) |
| Replacing a working DSP block with a neural net wholesale | ⚠️ **The evidence favours hybrids** (§8.3 → `dsp-audio-rf-and-images`, §16.1) |
| Assuming a neural enhancer is free | ⚠️ **DNNs significantly raise real-time compute** (§8.2 → `dsp-audio-rf-and-images`) |

---

## §16. Contested Questions

**16.1 Classical DSP or deep learning?** ⚠️ **The live question, and the evidence is more
interesting than either camp's slogan.** *For learning*: it removes the fine hand-tuning of
estimator parameters that classical enhancement depends on, and it wins clearly on source
separation and on non-stationary noise. *For classical*: interpretability, guarantees,
tiny compute, and no training data required — **and much state-of-the-art echo cancellation
remains classical or hybrid, with DNNs replacing only the nonlinear residual stage.**
**[The synthesis the field has actually converged on — RNNoise, DeepFilterNet, Opus 1.5/1.6
— is hybrid: keep the DSP structure you understand, learn the parameters you can't tune.]**

**16.2 Are neural codecs going to replace classical ones?** *For*: dramatically lower
bitrates, and codec tokens double as generative-model inputs. *Against*: compute, model
size (⚠️ **which Opus's own developers name as a main barrier to DNNs in codecs**),
determinism, and the fact that classical codecs are absorbing neural components
incrementally rather than being displaced. **⚠️ Note also that DRED's resynthesis discards
phase — fine for speech intelligibility, and a categorical change in what "reconstruction"
means.**

**16.3 Do objective quality metrics work?** PESQ, POLQA, STOI, SI-SDR are cheap and
repeatable; **they also disagree with listeners, especially on generative or heavily
processed audio where a metric can reward artifacts.** ⚠️ **Subjective MOS testing persists
because nothing has replaced it.**

**16.4 Is high-resolution audio (96/192 kHz) audible?** *For*: filter design headroom,
fewer intermodulation artifacts, and real benefit **during production**. *Against*: the
psychoacoustic evidence for playback benefit above 44.1/48 kHz is weak, and blind tests
mostly fail to show it. **[CONTESTED, and unusually heated relative to the stakes.]**

**16.5 FIR or IIR?** §3.1 → `dsp-sampling-frequency-domain-and-filters`. **Genuinely application-dependent** — and the phase requirement
usually settles it before compute does.

**16.6 Should DSP still be taught with the Z-transform and analogue prototypes?** *For*:
it's the language of the literature, and you cannot read filter design papers without it.
*Against*: most practitioners call a library function and never design a filter from poles
and zeros. **⚠️ The defensible middle: understand what the tool is doing well enough to
choose and debug it — §3.1 → `dsp-sampling-frequency-domain-and-filters`'s decision table matters more than deriving the bilinear
transform.**

---

## §17. Currency Snapshot — verified August 2026

**[DURABLE] Almost none of this document moves.** Nyquist 1928, Shannon 1949,
Cooley–Tukey 1965, Ephraim–Malah 1985. **§1–§7 → `dsp-sampling-frequency-domain-and-filters`, `dsp-convolution-multirate-and-spectral-analysis` and §9–§15 → `dsp-audio-rf-and-images`, `dsp-implementation-tools-and-testing` are stable.** Here is what
changed.

| Thing | Status as of Aug 2026 | Decay risk |
|---|---|---|
| **⚠️ Opus + ML** | **Opus 1.5 (March 2024, Xiph.Org) put machine learning inside the codec for the first time** — all **decoder-side**, so services can adopt playback-side alone. **Deep PLC** (neural reconstruction of lost packets, for occasional loss); **DRED** (for burst loss); **LACE/NoLACE** (DNN post-filter denoising). Opus is **mandatory in WebRTC** | Low (dated) |
| **DRED mechanics** | **Rate-distortion-optimized VAE** compressing acoustic parameters: **up to ~1 second of redundancy at ~12–32 kb/s overhead**, carried in packet padding; each 20 ms packet effectively transmitted many times over. **20 acoustic features — 18 Bark-frequency cepstral coefficients (bands matching CELT) plus pitch and voicing.** ⚠️ **No waveform or phase information, so recovered speech "will significantly deviate from the original waveform, despite sounding similar."** Trained against realistic burst-loss traces from Microsoft's Audio Deep PLC Challenge, plus a generative loss model **under 10,000 parameters** | Low |
| **⚠️ Opus 1.6** | **Released December 2025.** Adds **bandwidth extension (BWE)**, extending the FARGAN wideband vocoder used by deep PLC and DRED — ⚠️ **enabling DRED to reach fullband quality**, and **NoLACE + BWE giving good fullband speech as low as 9 kb/s.** Many DRED improvements over 1.5 | Medium |
| **⚠️ DRED standardization** | **IETF `draft-ietf-mlcodec-opus-dred`** — draft **-05 dated January 2026**, expiring July 2026. ⚠️ **As of 2026 the format is still being finalised: treat DRED as advanced rather than settled** | **High** |
| **The DNN-in-codec barrier** | ⚠️ **Opus's developers name model size — "even more than complexity" — as one of the main barriers to using DNNs in codecs.** Independent evaluation notes any AI/ML use "is bound to significantly increase the real-time computational requirements" | Medium |
| **Speech enhancement** | **RNNoise (Valin, 2018)** remains the landmark hybrid: a 4-hidden-layer network estimates **ideal critical-band gains** while **a traditional pitch filter attenuates noise between harmonics** — beating a classical MMSE spectral estimator at real-time 48 kHz on a low-power CPU. **DeepFilterNet** and successors **predict linear filters instead of estimating clean speech**, for edge deployability. ⚠️ **Current honest read: traditional methods are "fast but conservative"; deep learning is "more aggressive while preserving speech quality, at the cost of higher computational requirements"** | Medium |
| **Echo cancellation** | ⚠️ **Notably, most state-of-the-art AEC remains classical DSP or hybrid DSP-ML** — delay estimator and adaptive linear filter classical, **DNNs typically replacing only the nonlinear residual echo suppressor.** End-to-end neural AEC is an active research direction, not the default | Medium |
| **Hearing aids** | Real-time multichannel deep enhancement compared against adaptive differential microphones and binaural beamforming: ⚠️ **all approaches perform similarly in diffuse noise; the binaural deep approach wins in the presence of spatial interferers.** Deep models for hearing aids require **processing delay of only a few milliseconds** | Medium |

**Goes stale fastest:** the DRED standardization status and the neural-enhancement
frontier. **Essentially never stale:** §1–§7 → `dsp-sampling-frequency-domain-and-filters`, `dsp-convolution-multirate-and-spectral-analysis`, §9–§15 → `dsp-audio-rf-and-images`, `dsp-implementation-tools-and-testing`.

---

## §18. The Canon

### 18.1 Books

| Author | Work | Why |
|---|---|---|
| **Smith, Steven W.** | ***The Scientist and Engineer's Guide to DSP*** | ⚠️ **Free online, and the best possible starting point.** Intuition before formalism |
| **Oppenheim & Schafer** | ***Discrete-Time Signal Processing*** | The standard graduate text. Rigorous |
| **Lyons** | ***Understanding Digital Signal Processing*** | ⚠️ **The best bridge between intuition and rigour.** Superb on practical gotchas |
| **Proakis & Manolakis** | *Digital Signal Processing* | Comprehensive, communications-leaning |
| **Vaidyanathan** | *Multirate Systems and Filter Banks* | §5 → `dsp-convolution-multirate-and-spectral-analysis`, definitively |
| **Zölzer** | *DAFX: Digital Audio Effects* | ⚠️ **The audio-effects reference, and genuinely fun** |
| **Pirkle** | *Designing Audio Effect Plugins in C++* | Implementation-focused |
| **Kay** | *Fundamentals of Statistical Signal Processing* (2 vols) | §6 → `dsp-convolution-multirate-and-spectral-analysis`, §7.4 → `dsp-convolution-multirate-and-spectral-analysis` — estimation and detection |
| **Haykin** | *Adaptive Filter Theory* | §6 → `dsp-convolution-multirate-and-spectral-analysis` |
| **Zwicker & Fastl** | *Psychoacoustics* | §8.1 → `dsp-audio-rf-and-images`'s foundations |
| **Gonzalez & Woods** | *Digital Image Processing* | §10 → `dsp-audio-rf-and-images` |
| **Proakis & Salehi** | *Digital Communications* | §9 → `dsp-audio-rf-and-images` |
| **Bracewell** | *The Fourier Transform and Its Applications* | ⚠️ **The classic on §2 → `dsp-sampling-frequency-domain-and-filters`, and beautifully written** |

### 18.2 Primary sources and tooling
**`scipy.signal` documentation** (⚠️ **unusually good at explaining *which* method and
why**), **MATLAB's DSP documentation**, **the Opus codec site and its demo pages**
(⚠️ **Valin's write-ups on Opus 1.5 and 1.6 are outstanding technical communication and the
best free explanation of neural-in-codec design**), **IETF drafts** for DRED,
**GNU Radio tutorials**, **DSPRelated.com**, **musicdsp.org**, **KVR** and the JUCE forum
for audio implementation, **the ICASSP / Interspeech / DAFx / AES** proceedings.

### 18.3 People
**Jean-Marc Valin** (⚠️ **Opus, Speex, RNNoise — arguably the most consequential practical
audio DSP engineer working, and he publishes clearly**), **Richard Lyons** (the best
explainer in the field), **Julius O. Smith III** (⚠️ **Stanford CCRMA — his four free
online books on filters, spectral audio, and physical modelling are a remarkable
resource**), **Alan Oppenheim**, **Steven W. Smith**, **Ronald Bracewell**,
**Udo Zölzer**, **P. P. Vaidyanathan**, **Simon Haykin**, **Monty Montgomery**
(⚠️ **Xiph — his video demonstrations of sampling and dither are the clearest explanations
of §1 → `dsp-sampling-frequency-domain-and-filters` anywhere**), **Emmanuel Vincent** and **Antoine Liutkus** (source separation).

---

## §19. Quick Reference

### 19.1 Numbers
- **Nyquist: fs > 2B**, strictly
- **Frequency resolution Δf = fs/N = 1/T** — ⚠️ **set by duration, nothing else**
- **~6 dB SNR per bit**; 16-bit ≈ 96 dB
- **Hearing: 20 Hz – 20 kHz, ~120 dB**
- **Musician latency threshold ≈ 10 ms**; conversational ≈ 150–200 ms one-way
- **FFT convolution beats direct at roughly 50–100 taps**
- **Zero-pad convolution to ≥ N+M-1**
- **Shannon: C = B log₂(1 + SNR)** — a hard ceiling

### 19.2 Method picker
| Need | Use |
|---|---|
| Remove a specific frequency | Notch filter (§3.3 → `dsp-sampling-frequency-domain-and-filters`) |
| Smooth without distorting peaks | **Savitzky–Golay** (§3.3 → `dsp-sampling-frequency-domain-and-filters`) |
| Remove impulsive noise | **Median filter** — not linear (§3.3 → `dsp-sampling-frequency-domain-and-filters`) |
| Linear phase required | **FIR** (§3.1 → `dsp-sampling-frequency-domain-and-filters`) |
| Tight compute, phase irrelevant | **IIR biquads** (§3.1 → `dsp-sampling-frequency-domain-and-filters`) |
| Flat group delay | **Bessel** (§3.2 → `dsp-sampling-frequency-domain-and-filters`) |
| Sharpest transition for the order | **Elliptic** (§3.2 → `dsp-sampling-frequency-domain-and-filters`) |
| Offline, want zero phase | `filtfilt` (§3.3 → `dsp-sampling-frequency-domain-and-filters`) |
| Estimate a spectrum | **Welch**, or multitaper (§7.1 → `dsp-convolution-multirate-and-spectral-analysis`) |
| Resolve close tones with short data | **MUSIC/ESPRIT** — ⚠️ model-dependent (§7.3 → `dsp-convolution-multirate-and-spectral-analysis`) |
| Time-varying spectrum | STFT; **CQT for music** (§7.2 → `dsp-convolution-multirate-and-spectral-analysis`) |
| Change sample rate | **Polyphase resampler** (§5 → `dsp-convolution-multirate-and-spectral-analysis`) |
| Find a known signal in noise | **Matched filter** (§4 → `dsp-convolution-multirate-and-spectral-analysis`) |
| Estimate time delay between mics | **GCC-PHAT** (§4 → `dsp-convolution-multirate-and-spectral-analysis`) |
| Cancel echo | Adaptive filter + residual suppressor + **double-talk detector** (§8.3 → `dsp-audio-rf-and-images`) |
| Suppress noise, low compute | **RNNoise / DeepFilterNet** hybrid (§8.3 → `dsp-audio-rf-and-images`) |
| Multi-mic spatial filtering | **Beamforming** (MVDR/GSC) (§8.3 → `dsp-audio-rf-and-images`) |
| Separate music sources | Neural separator (Demucs) (§8.4 → `dsp-audio-rf-and-images`) |
| Voice over a lossy network | ⚠️ **Opus with Deep PLC / DRED** (§8.2 → `dsp-audio-rf-and-images`) |
| Track a state over time | **Kalman filter** (§6 → `dsp-convolution-multirate-and-spectral-analysis`) |

### 19.3 When it sounds/looks wrong
1. **Plot the spectrogram.** Then **listen** (§13 → `dsp-implementation-tools-and-testing`)
2. **Check for aliasing** — is anything above Nyquist? (§1.1 → `dsp-sampling-frequency-domain-and-filters`)
3. **Check scaling** — Parseval's theorem (§13 → `dsp-implementation-tools-and-testing`)
4. **Check window/overlap alignment** — off-by-one (§13 → `dsp-implementation-tools-and-testing`)
5. **Check filter state across blocks** — clicks at boundaries? (§13 → `dsp-implementation-tools-and-testing`)
6. **Check zero-padding** in FFT convolution (§4 → `dsp-convolution-multirate-and-spectral-analysis`)
7. **Check for clipping and DC offset** (§1.2 → `dsp-sampling-frequency-domain-and-filters`)
8. **Check denormals** if CPU spikes on silence (§11 → `dsp-implementation-tools-and-testing`)
9. **Test with an impulse and a sine** before real data (§13 → `dsp-implementation-tools-and-testing`)

---

## §20. Sources and Method

**Method.** Narrative review, written as practice guidance for engineers implementing DSP.
**The overwhelming majority — §1–§7 → `dsp-sampling-frequency-domain-and-filters`, `dsp-convolution-multirate-and-spectral-analysis`, §9–§15 → `dsp-audio-rf-and-images`, `dsp-implementation-tools-and-testing` — is classical signal processing**, resting on
the standard literature (Oppenheim & Schafer, Lyons, Smith, Vaidyanathan, Kay, Bracewell)
rather than on anything searched, and it does not move: **Nyquist is 1928, Shannon 1949,
Cooley–Tukey 1965, and Ephraim–Malah 1985.** §17 says so plainly rather than manufacturing
a currency layer. Two targeted searches were run in **August 2026** on the one part that
genuinely moved: the convergence of classical DSP with machine learning in audio.

**Search log** (August 2026): Opus 1.5/1.6, DRED, deep packet loss concealment, and neural
audio codecs · speech enhancement and noise suppression, classical versus deep, and
real-time constraints.

**Primary and near-primary sources consulted (selected):**
- **The Opus codec project's own demo pages for 1.5 and 1.6** and the **xiph/opus
  repository**, for the DRED, Deep PLC, LACE/NoLACE and BWE descriptions and the
  bitrate figures; **IETF `draft-ietf-mlcodec-opus-dred`** for the acoustic-feature
  specification and the standardization status; **arXiv 2212.04453** (Valin et al.,
  *DRED: Deep REDundancy Coding of Speech*) for the design rationale
- **arXiv 1709.08243** (Valin, *A Hybrid DSP/Deep Learning Approach to Real-Time Full-Band
  Speech Enhancement* — RNNoise), read for the architecture and the stated comparison
  against MMSE; DeepFilterNet and successor papers for the predict-filters-not-signal
  approach; **IEEE/ACM TASLP** work on real-time multichannel deep enhancement in hearing
  aids for the diffuse-versus-spatial-interferer comparison
- Independent evaluation write-ups (CouthIT) of Opus 1.5's Deep PLC and LACE, and a 2026
  practitioner guide to noise suppression, for the classical-versus-deep framing

**Confidence statement.** **Very high confidence** in §1–§7 → `dsp-sampling-frequency-domain-and-filters`, `dsp-convolution-multirate-and-spectral-analysis` and §9–§15 → `dsp-audio-rf-and-images`, `dsp-implementation-tools-and-testing` — this is textbook
signal processing, taught consistently for decades, and my confidence rests on that
literature rather than on web sources. **High confidence in the Opus material** in §8.2 → `dsp-audio-rf-and-images` and
§17: the mechanism descriptions, bitrates and feature counts come from the Opus project's
own documentation and the IETF draft, and Valin's technical writing is unusually precise.
⚠️ **The DRED standardization status is the item most likely to have moved** — the draft I
saw was dated January 2026 with a July 2026 expiry, so **check the IETF datatracker before
relying on it.**

⚠️ **Moderate confidence on §8.3 → `dsp-audio-rf-and-images`'s classical-versus-deep comparison.** The individual
findings are from peer-reviewed sources, but **"most state-of-the-art AEC is still
classical or hybrid" comes from a paper whose authors were motivating their own end-to-end
alternative**, and such framing is naturally selective; the hearing-aid comparison is one
study on two acoustic scenes. **The broad pattern — that hybrids are outperforming both
pure approaches in production audio — is well supported across multiple independent lines
of evidence, but the specific characterizations should not be read as settled consensus.**
§16 is opinion labelled as such, and §16.4 in particular is a debate where I have tried to
report the state of the evidence rather than adjudicate.
