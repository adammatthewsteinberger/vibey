---
name: biomed-signals-and-medical-imaging
description: "Use when working with physiological signals or medical images: the signals and their frequency bands (ECG, EEG, EMG, PPG), the filtering constraints specific to this domain, detection and feature extraction; and medical imaging — modality physics for CT, MRI, ultrasound, PET and X-ray, the DICOM internals that produce silent errors, reconstruction, and registration and segmentation. Includes the router for the whole biomedical-engineering reference."
---

# Biomedical Engineering: Physiological Signal Processing and Medical Imaging

> **Part 1 of 5** of the *Biomedical Engineering* reference (plugin `biomedical-engineering-technical`), covering §0–§2. Sibling skills: `biomed-clinical-data-ml-and-bioinformatics` (§3–§5), `biomed-structural-systems-biology-and-pharmacology` (§6–§9), `biomed-biomechanics-devices-and-biostatistics` (§10–§15), `biomed-reference` (§16–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The physics, physiology and mathematics are stable; tool and pipeline recommendations shift slowly.

> **Scope note.** This is the engineering and science. **Regulatory pathways, quality
> systems, and lifecycle process are deliberately excluded** — they're a separate subject
> and they'd swamp the technical content.
>
> **⚠️ GOTCHA** boxes mark where a silent wrong answer is produced — which in this domain
> is the dangerous failure mode, not a crash.
>
> **The three technical facts that recur everywhere below:**
> 1. **⚠️ Biological signals are non-stationary, and most DSP assumes stationarity.** Every
>    windowing choice is an assumption about how long the physiology holds still (§1).
> 2. **⚠️ Prevalence governs predictive value.** Sensitivity and specificity are properties
>    of a test; PPV is a property of a test *in a population*. Confusing them is the single
>    most common quantitative error in the field (§4.1 → `biomed-clinical-data-ml-and-bioinformatics`).
> 3. **⚠️ Biological variability is the signal's competitor.** Between-subject variance
>    usually exceeds the effect you're measuring, which is why normalization,
>    within-subject designs, and mixed-effects models dominate (§15 → `biomed-biomechanics-devices-and-biostatistics`).

---

## §0. Routing

| You want... | Go to |
|---|---|
| **Physiological signal processing** | **§1** |
| Medical imaging physics and DICOM | §2 |
| Registration and segmentation | §2.4 |
| Clinical data structures | §3 → `biomed-clinical-data-ml-and-bioinformatics` |
| **Clinical ML technicals** | **§4 → `biomed-clinical-data-ml-and-bioinformatics`** |
| Bioinformatics: sequences and variants | §5 → `biomed-clinical-data-ml-and-bioinformatics` |
| Structural biology | §6 → `biomed-structural-systems-biology-and-pharmacology` |
| Systems biology and network models | §7 → `biomed-structural-systems-biology-and-pharmacology` |
| **PK/PD modeling** | **§8 → `biomed-structural-systems-biology-and-pharmacology`** |
| Physiological models | §9 → `biomed-structural-systems-biology-and-pharmacology` |
| Biomechanics | §10 → `biomed-biomechanics-devices-and-biostatistics` |
| Biomaterials | §11 → `biomed-biomechanics-devices-and-biostatistics` |
| Tissue engineering | §12 → `biomed-biomechanics-devices-and-biostatistics` |
| **Neural interfaces and prosthetics** | **§13 → `biomed-biomechanics-devices-and-biostatistics`** |
| Lab automation and instrumentation | §14 → `biomed-biomechanics-devices-and-biostatistics` |
| Biostatistics | §15 → `biomed-biomechanics-devices-and-biostatistics` |
| Misconceptions | §16 → `biomed-reference` |
| Numbers | §17 → `biomed-reference` |
| Books | §18 → `biomed-reference` |
| Quick reference | §19 → `biomed-reference` |

---

## §1. Physiological Signal Processing

### 1.1 The signals and their bands

| Signal | Band | Amplitude | Sampling |
|---|---|---|---|
| **ECG** | 0.05–150 Hz (diagnostic) | 0.1–5 mV | ≥500 Hz diagnostic, 250 monitoring |
| **EEG** | 0.5–100 Hz | ⚠️ **10–100 µV** | 250–1000 Hz |
| **EMG** | 20–500 Hz | 50 µV–5 mV | ≥1000 Hz |
| **PPG** | 0.5–8 Hz | — (AC/DC ratio) | 25–500 Hz |
| **Respiration** | 0.1–2 Hz | — | 25–50 Hz |
| **EOG** | 0.1–30 Hz | 10–100 µV | 250 Hz |
| **Intracortical spikes** | ⚠️ **300–6000 Hz** | 50–500 µV | ⚠️ **≥20–30 kHz** |
| **LFP** | 1–300 Hz | 0.1–1 mV | 1–2 kHz |

**EEG rhythms**: δ 0.5–4, θ 4–8, α 8–13, β 13–30, γ 30–100 Hz.

### 1.2 ⚠️ The filtering constraints that are specific to this domain

**⚠️ Powerline interference (50/60 Hz) sits inside the ECG diagnostic band.** A notch
filter at 60 Hz removes real QRS spectral content — the QRS complex has energy up to
~100 Hz. **A narrow notch rings; a wide notch distorts.** Prefer **adaptive filtering
against a reference sinusoid**, or a very narrow IIR notch applied with zero phase.

**⚠️ Phase distortion changes measured intervals, and intervals are diagnoses.**
A causal high-pass at 0.5 Hz shifts and distorts the **ST segment** — and ST elevation is
myocardial infarction. **The standard fix: zero-phase forward-backward filtering
(`filtfilt`), or a high-pass at 0.05 Hz for diagnostic ECG.**
```
⚠️ Monitoring ECG:  0.5–40 Hz  — acceptable, suppresses wander, NOT diagnostic
⚠️ Diagnostic ECG:  0.05–150 Hz — required for ST analysis
```
**Confusing the two produces plausible, wrong ST measurements.**

**Baseline wander** (respiration, electrode motion, ~0.15–0.3 Hz) — high-pass or
**cubic-spline fitting through the PQ segments**, which avoids filter distortion entirely.

**Motion artifact** overlaps the signal band and cannot be filtered out spectrally.
⚠️ **Use an accelerometer as a reference channel and adaptive-cancel** — this is what
wearable PPG does.

### 1.3 Detection and feature extraction

**Pan–Tompkins QRS detection** — the durable algorithm, and the structure is worth
knowing because it generalizes:
```
bandpass 5–15 Hz  →  differentiate (emphasize slope)  →  square (rectify, emphasize
large)  →  moving-window integrate (~150 ms)  →  adaptive dual thresholds
   + ⚠️ 200 ms refractory (physiologically impossible to have two QRS closer)
   + ⚠️ searchback: if no beat in 1.66× the running RR average, re-search at low threshold
```
**⚠️ The refractory period and searchback are the parts that make it robust** — they encode
physiology as constraints, which is the general lesson.

**HRV** from the RR interval series: **time domain** (SDNN, **RMSSD** — ⚠️ **the
parasympathetic index**, pNN50), **frequency domain** (LF 0.04–0.15 Hz, HF 0.15–0.4 Hz,
LF/HF ratio — ⚠️ **whose interpretation as "sympathovagal balance" is contested**), and
**nonlinear** (Poincaré SD1/SD2, sample entropy, DFA).
**⚠️ RR series are irregularly sampled** — interpolate to a uniform grid before FFT, or use
Lomb–Scargle.

**EEG artifact removal**: **ICA** is the workhorse — ⚠️ **eye blinks and cardiac artifact
separate into identifiable components** with characteristic scalp topographies.
**Regression against EOG channels** for blinks. **ASR (Artifact Subspace
Reconstruction)** for motion.
**⚠️ Reference choice changes everything**: average reference, linked mastoids, or
**Laplacian** — and results are not comparable across reference schemes.

**Time-frequency**, because the signals are non-stationary: **STFT** (⚠️ **fixed
resolution trade — Heisenberg**), **wavelets** (⚠️ **Morlet for EEG oscillations; better
time resolution at high frequency**), **Hilbert–Huang/EMD**, and **multitaper** for
noisy spectral estimates.

---

## §2. Medical Imaging

### 2.1 Modality physics

| Modality | Physics | Resolution | ⚠️ Constraint |
|---|---|---|---|
| **CT** | X-ray attenuation, filtered backprojection or iterative recon | 0.5–1 mm | ⚠️ **Ionizing dose; ALARA** |
| **MRI** | Nuclear magnetic resonance, T1/T2 relaxation | 1 mm | Long acquisition; ⚠️ **field is a physical hazard** |
| **Ultrasound** | Acoustic reflection, ~1–15 MHz | 0.3–2 mm | ⚠️ **Operator-dependent; acoustic shadowing** |
| **PET** | Positron annihilation, 511 keV coincidence | 4–5 mm | ⚠️ **Functional, not anatomical; needs CT for attenuation correction** |
| **SPECT** | Single-photon gamma | 8–10 mm | Lower resolution than PET |
| **OCT** | Low-coherence interferometry | ⚠️ **1–15 µm** | Penetration only ~1–2 mm |
| **Digital pathology** | Whole-slide scanning | 0.25 µm/px | ⚠️ **Gigapixel — pyramidal tiling mandatory** |

**CT numbers** are in **Hounsfield units**: `HU = 1000 × (µ − µ_water)/µ_water`.
⚠️ **Water = 0, air = −1000, dense bone ≈ +1000 to +3000.** Fixed and physical, which is
why CT is quantitative and MRI intensity is not.

**MRI contrast** comes from **TR and TE**: T1-weighted (short TR/TE — fat bright, fluid
dark), T2-weighted (long TR/TE — ⚠️ **fluid bright, which is why pathology shows**), FLAIR
(T2 with CSF suppressed), DWI/ADC (diffusion — ⚠️ **restricted diffusion in acute stroke
within minutes**), and functional/BOLD.

> **⚠️ GOTCHA — MRI intensity has no absolute meaning.** Unlike CT's Hounsfield units, MRI
> signal depends on scanner, coil, sequence, and shim. **Intensity values are not
> comparable across scans without normalization** (histogram matching, z-scoring within a
> tissue mask, or N4 bias-field correction first). **Training an ML model on raw MRI
> intensities across sites is a well-known way to learn the scanner instead of the
> disease.**

### 2.2 ⚠️ DICOM internals that produce silent errors

**Hierarchy**: Patient → Study → Series → Instance, identified by **UIDs**.
⚠️ **UIDs must be globally unique; generating them incorrectly corrupts archives
irreversibly.** Use a registered root plus a unique suffix.

**The specific traps:**
- **⚠️ Rescale.** `HU = pixel_value × RescaleSlope + RescaleIntercept`. **Stored pixels are
  not HU.** Skipping this is the most common CT bug and produces confidently wrong
  measurements.
- **⚠️ Photometric interpretation.** `MONOCHROME1` = minimum is white; `MONOCHROME2` =
  minimum is black. **Getting it wrong inverts the image** and a radiologist will notice
  but a model won't.
- **⚠️ Orientation.** `ImageOrientationPatient` (two direction cosine vectors) and
  `ImagePositionPatient` define anatomical space. **Left/right confusion means the wrong
  side, and wrong-side surgery is a real event class.** Always derive laterality from the
  geometry, never from the display convention.
- **Slice spacing ≠ slice thickness.** `SliceThickness` is the acquisition; spacing must be
  computed from consecutive `ImagePositionPatient` values. ⚠️ **They disagree with gaps or
  overlap**, and using the wrong one distorts volumes.
- **Window/level** (`WindowCenter`, `WindowWidth`) is display only — ⚠️ **never bake it
  into stored data you intend to analyse.**
- **Multi-frame and enhanced DICOM** put per-frame attributes in functional group
  sequences, not at the top level.

**⚠️ De-identification is harder than stripping tags.** PHI hides in **private tags**,
**burned-in pixel annotation**, `StudyDescription` free text, and ⚠️ **the face itself —
facial reconstruction from head CT/MRI is demonstrated, so "defacing" is a genuine
requirement for shared neuroimaging.**

### 2.3 Reconstruction
**Filtered backprojection** — the Radon transform inverted, with a **ramp filter** in
frequency (⚠️ **the ramp amplifies high-frequency noise; apodize with Shepp-Logan or
Hann**). **Iterative reconstruction** (ART, SART, MBIR) is slower and permits substantially
lower dose. **⚠️ Undersampling produces streak artifacts**; compressed sensing exploits
sparsity to recover from fewer projections, which is what makes fast MRI possible.

### 2.4 Registration and segmentation

**Registration** = find the transform aligning two images:
```
T* = argmin_T  S(I_fixed, T(I_moving)) + λR(T)
```
**Transform models**: rigid (6 DOF) → affine (12) → **deformable** (B-spline free-form,
diffeomorphic/LDDMM, Demons).
**Similarity metrics**: SSD (⚠️ **same modality only**), normalized cross-correlation, and
⚠️ **mutual information — the standard for multimodal (CT↔MRI), because it makes no
assumption about intensity relationship, only statistical dependence.**
```
MI(A,B) = H(A) + H(B) − H(A,B)
```
**⚠️ Practical requirements**: multi-resolution pyramids (avoids local minima), and
**regularization to keep the deformation invertible** — an unregularized deformable
registration will happily fold tissue through itself.

**Segmentation**: thresholding → region growing → **level sets / active contours** →
**atlas-based** → **deep learning**.
⚠️ **nnU-Net remains the strong baseline that beats most novel architectures on medical
segmentation** — its contribution is automated configuration of preprocessing, patch size,
and augmentation, which matters more than architecture.
**Metrics**: **Dice** `2|A∩B|/(|A|+|B|)`, **IoU**, **Hausdorff distance** (⚠️ **worst-case
boundary error — the one that matters clinically, because Dice is insensitive to a small
but catastrophic boundary error**), and **surface Dice**.

**⚠️ Class imbalance is severe** — a lesion may be 0.1% of voxels. **Dice loss or
Tversky loss rather than cross-entropy**, and patch sampling biased toward foreground.

**Toolkits**: ITK/SimpleITK, ANTs (registration), 3D Slicer, MONAI, nnU-Net, FSL and
FreeSurfer (neuro), pydicom, dcm4che, OHIF, OpenSlide (pathology).
