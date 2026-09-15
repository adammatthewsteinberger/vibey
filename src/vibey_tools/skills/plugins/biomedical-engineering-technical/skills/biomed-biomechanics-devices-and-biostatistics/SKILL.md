---
name: biomed-biomechanics-devices-and-biostatistics
description: "Use when working on the physical or experimental side: biomechanics of tissue and gait, biomaterials and biocompatibility, tissue engineering and scaffolds, neural interfaces and prosthetics (recording, the signal chain, prosthetic control), lab automation and instrumentation, and the biostatistics that determine whether a result holds up — study design, multiple comparisons, survival analysis and effect sizes."
---

# Biomedical Engineering: Biomechanics, Biomaterials, Devices, Lab Automation, and Biostatistics

> **Part 4 of 5** of the *Biomedical Engineering* reference (plugin `biomedical-engineering-technical`), covering §10–§15. Sibling skills: `biomed-signals-and-medical-imaging` (§0–§2), `biomed-clinical-data-ml-and-bioinformatics` (§3–§5), `biomed-structural-systems-biology-and-pharmacology` (§6–§9), `biomed-reference` (§16–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    windowing choice is an assumption about how long the physiology holds still (§1 → `biomed-signals-and-medical-imaging`).
> 2. **⚠️ Prevalence governs predictive value.** Sensitivity and specificity are properties
>    of a test; PPV is a property of a test *in a population*. Confusing them is the single
>    most common quantitative error in the field (§4.1 → `biomed-clinical-data-ml-and-bioinformatics`).
> 3. **⚠️ Biological variability is the signal's competitor.** Between-subject variance
>    usually exceeds the effect you're measuring, which is why normalization,
>    within-subject designs, and mixed-effects models dominate (§15).

---

## §10. Biomechanics

**Tissue mechanics**: ⚠️ **biological tissue is viscoelastic, anisotropic, and nonlinear** —
it exhibits **creep**, **stress relaxation**, and **hysteresis**. Models: Maxwell,
Kelvin-Voigt, standard linear solid; **hyperelastic** strain-energy formulations
(Mooney-Rivlin, Ogden, **Fung** for soft tissue) for large deformation.

**⚠️ The J-shaped stress-strain curve** of collagenous tissue: compliant at low strain
(crimped fibres straightening), stiffening sharply as fibres engage. **A linear modulus is
meaningless without specifying the strain.**

| Material | Young's modulus |
|---|---|
| Cortical bone | 15–20 GPa |
| Trabecular bone | 0.1–2 GPa |
| Tendon | 1–2 GPa |
| Cartilage | 0.5–10 MPa |
| Arterial wall | 0.1–1 MPa |
| ⚠️ **Brain tissue** | **1–10 kPa** |

**⚠️ That range spans seven orders of magnitude** — which is why implant stiffness matching
matters so much (§11).

**Gait analysis**: motion capture + force plates → **inverse dynamics** to get joint moments
from kinematics and ground reaction forces. **Gait cycle**: stance ~60%, swing ~40%.
**⚠️ Soft tissue artifact** — markers move relative to bone — is the dominant error source.

**Wolff's law**: bone remodels along loading. ⚠️ **Which is why stress shielding by a stiff
implant causes bone resorption around it** — a mechanical cause of implant loosening.

---

## §11. Biomaterials

**Classes and their trade-offs:**

| Material | Modulus | ⚠️ Note |
|---|---|---|
| **316L stainless** | 200 GPa | Cheap; ⚠️ **stress shielding, nickel release** |
| **Ti-6Al-4V** | ⚠️ **110 GPa** | **Closest to bone of the metals; excellent osseointegration** |
| **CoCr** | 210 GPa | Wear-resistant bearing surfaces |
| **UHMWPE** | 1 GPa | ⚠️ **Bearing surface; wear particles drive osteolysis** |
| **PEEK** | 3–4 GPa | ⚠️ **Radiolucent, bone-like modulus; bioinert (doesn't bond)** |
| **PLA/PGA/PLGA** | 1–4 GPa | ⚠️ **Resorbable; degradation rate tunable by copolymer ratio** |
| **Hydroxyapatite** | 80–110 GPa | Bioactive, brittle; a coating more than a bulk material |
| **Bioglass 45S5** | 35 GPa | ⚠️ **Bonds chemically to bone** |
| **Hydrogels (PEG, alginate)** | ⚠️ **kPa** | Soft tissue and cell encapsulation |

**⚠️ Stress shielding is the recurring failure mechanism**: a 200 GPa implant next to
20 GPa bone carries the load, the bone unloads, and Wolff's law resorbs it (§10).
**Modulus matching is a first-order design requirement, not a refinement.**

**Biocompatibility** is graded: **bioinert** (fibrous encapsulation), **bioactive**
(chemical bonding — bioglass, HA), **bioresorbable** (replaced by tissue).
**⚠️ The foreign body response is the default outcome**: protein adsorption within seconds
→ acute inflammation → macrophage/foreign body giant cells → **fibrous capsule**.
**That capsule is why implanted sensors drift and fail** (§13).

**Degradation**: PLGA hydrolyses; ⚠️ **the acidic degradation products can cause local
inflammation, and bulk erosion can produce a sudden mechanical failure rather than a
gradual one.**

---

## §12. Tissue Engineering

**The triad: cells + scaffold + signals.**

**Scaffold requirements**: **porosity >90%** with **interconnected pores 100–500 µm** for
bone (⚠️ **too small and cells can't infiltrate; too large and you lose mechanical
integrity and surface area**), degradation matched to tissue formation rate, and
appropriate modulus.

> **⚠️ GOTCHA — the oxygen diffusion limit is the field's hard ceiling.** Cells more than
> **~150–200 µm from a capillary** become hypoxic and die. **This is why thick, solid
> engineered tissue fails**, and why the successes to date are thin (skin, cartilage,
> cornea, bladder) or hollow (trachea, vessels). **Vascularization is the unsolved
> problem**, and everything else in the field is downstream of it.

**Fabrication**: electrospinning (nanofibres, ECM-like), **3D bioprinting** (extrusion,
inkjet, laser-assisted — ⚠️ **the trade is resolution against cell viability under shear**),
decellularization (⚠️ **keeps native ECM architecture and vasculature — arguably the most
promising route to complex organs**), and **organ-on-chip** microfluidics.

**Cells**: autologous (no rejection, slow to expand), allogeneic, **iPSCs** (⚠️ **patient-
specific and pluripotent, but differentiation efficiency and residual undifferentiated
cells creating teratoma risk are real**), and **organoids** — self-organizing 3D cultures
that recapitulate architecture, ⚠️ **and which are far better models than 2D culture while
still lacking vasculature and immune components.**

---

## §13. Neural Interfaces and Prosthetics

### 13.1 Recording

| Modality | Bandwidth | Invasiveness | Longevity |
|---|---|---|---|
| **EEG (scalp)** | ⚠️ **low; spatially blurred by skull** | none | indefinite |
| **ECoG** | good | subdural | years |
| **Intracortical (Utah array)** | ⚠️ **single-unit** | penetrating | ⚠️ **months–years, degrading** |
| **Peripheral nerve cuff** | moderate | surgical | — |
| **EMG (surface / implanted)** | good for prosthetics | low | — |

**⚠️ The chronic-recording failure mode is the foreign body response** (§11): glial
scarring encapsulates the electrode, impedance rises, and **signal amplitude decays over
months.** **This — not the electronics — is the limiting factor on intracortical BCI
longevity**, and flexible/soft electrodes exist specifically to reduce the mechanical
mismatch driving it.

### 13.2 Signal chain
```
Spike detection (threshold on 300–6000 Hz band, typically −4 to −5×RMS noise)
  → spike sorting (PCA/template matching, ⚠️ or "threshold crossings" used directly,
    since much BCI decoding works fine without sorting)
    → binned firing rates (⚠️ typically 20–50 ms bins)
      → decoder
```
**Decoders**: **population vector**, **Wiener filter**, **Kalman filter** (⚠️ **the
workhorse for cursor and reach decoding — smooth, causal, and it handles the latent-state
structure naturally**), and recurrent networks.
**⚠️ Non-stationarity is the operational problem**: units appear and disappear day to day.
**Recalibration, or decoders designed to be robust to unit turnover, are required.**

**EEG BCI paradigms**: **P300** (⚠️ **~300 ms positive deflection to an oddball —
requires averaging over repetitions, so it's slow**), **SSVEP** (⚠️ **frequency-tagged
flicker; high information rate and needs no training**), and **motor imagery**
(⚠️ **event-related desynchronization in µ/β bands; the CSP + LDA pipeline is the classic
baseline, and a substantial fraction of users cannot drive it — "BCI illiteracy"**).

### 13.3 Prosthetic control
**Direct EMG** — amplitude envelope drives velocity. **Pattern recognition** over EMG
features (⚠️ **time-domain features — MAV, zero crossings, waveform length, slope sign
changes — plus LDA remains a very strong baseline**). **Targeted muscle reinnervation**
surgically redirects amputated nerves to spare muscle, creating intuitive control sites.

**⚠️ The sensory problem is as important as the motor one**: without proprioception and
touch, users must watch the limb constantly, and rejection rates for advanced prostheses
are high. **Sensory feedback via nerve stimulation is where the field's leverage is.**

**Control latency budget: ⚠️ under ~100–125 ms end-to-end**, or the coupling feels wrong
and performance degrades.

---

## §14. Lab Automation and Instrumentation

**Liquid handling** — ⚠️ **the practical constraints are viscosity, surface tension,
evaporation from edge wells, and carryover.** Acoustic dispensing (Echo) avoids tips
entirely and reaches nanolitre volumes.

**Plate formats**: 96 / 384 / 1536, and ⚠️ **edge effects are real — evaporation makes
perimeter wells systematically different. Randomize plate layout, or exclude edges.**

**Detection**: absorbance (Beer–Lambert `A = εcl`), fluorescence (⚠️ **sensitive but
subject to photobleaching and inner-filter effects**), luminescence, flow cytometry
(⚠️ **compensation for spectral overlap is mandatory and routinely done badly**),
mass spectrometry, and **qPCR** (`C_t` values; efficiency-corrected ΔΔC_t).

**Sequencing chemistries**: **Illumina** (sequencing-by-synthesis, short, ⚠️ **very high
accuracy Q30+**), **Oxford Nanopore** (⚠️ **long reads, real-time, higher raw error but
excellent for structural variants and assembly**), **PacBio HiFi** (long *and* accurate via
circular consensus).

**Assay quality metrics**: **Z' factor** `= 1 − 3(σ_p + σ_n)/|µ_p − µ_n|` — ⚠️ **>0.5 is a
usable screening assay; this single number is how high-throughput screens are validated.**
**CV**, **LOD/LOQ**, and dynamic range.

**⚠️ Standards worth using**: **SiLA 2** and **OPC-UA** for instrument integration,
**AnIML/ADF** for data. **The recurring practical problem is vendor-proprietary formats
and drivers**, which is why lab data integration is disproportionately painful.

---

## §15. Biostatistics

**⚠️ Study designs and what they can support**: RCT (causal), cohort, case-control
(⚠️ **efficient for rare outcomes; cannot estimate incidence**), cross-sectional,
crossover (⚠️ **within-subject, so it removes between-subject variance — powerful when
carryover can be excluded**).

**Survival analysis** — because **censoring** makes ordinary regression invalid:
**Kaplan–Meier** estimator, **log-rank test**, **Cox proportional hazards**
`h(t|X) = h₀(t)·exp(βᵀX)`. ⚠️ **Test the proportional hazards assumption (Schoenfeld
residuals) — it is routinely assumed and rarely checked, and crossing survival curves
invalidate it.**

**Mixed-effects models** — ⚠️ **the correct default for repeated measures and clustered
data**, which describes most biomedical data. `y = Xβ + Zu + ε`. **Treating repeated
measures as independent inflates the effective N and manufactures significance.**

**Multiple comparisons**: Bonferroni (conservative), ⚠️ **Benjamini–Hochberg FDR — the
standard in genomics, where you test 20,000 genes and controlling FWER would leave you
nothing.**

**⚠️ Effect size over p-values.** Report confidence intervals, and distinguish
**statistical from clinical significance** — with large N, trivial differences are
significant. **MCID (minimal clinically important difference)** is the relevant benchmark.

**Diagnostic accuracy**: sensitivity, specificity, **likelihood ratios**
(⚠️ **LR+ = Sens/(1−Spec); prevalence-independent and directly usable in Bayesian updating
of pre-test odds**), ROC and AUC, **and §4.1 → `biomed-clinical-data-ml-and-bioinformatics`'s prevalence dependence for PPV/NPV.**

**⚠️ Agreement is not correlation.** For method comparison use **Bland–Altman**
(difference vs mean, with limits of agreement), not `r` — ⚠️ **two methods can correlate at
r = 0.99 while one reads systematically double the other.** For categorical raters, use
**Cohen's/Fleiss' κ**; for continuous, **ICC**.
