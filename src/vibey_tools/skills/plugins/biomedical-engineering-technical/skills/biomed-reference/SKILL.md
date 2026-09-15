---
name: biomed-reference
description: "Use when correcting a common biomedical misconception, checking a physiological or instrument value, finding the textbook canon, or needing the core equations, a method picker, and a debugging checklist for a pipeline producing implausible output. Companion to the other biomedical-engineering skills."
---

# Biomedical Engineering: Misconceptions, Numbers, and Canon

> **Part 5 of 5** of the *Biomedical Engineering* reference (plugin `biomedical-engineering-technical`), covering §16–§20. Sibling skills: `biomed-signals-and-medical-imaging` (§0–§2), `biomed-clinical-data-ml-and-bioinformatics` (§3–§5), `biomed-structural-systems-biology-and-pharmacology` (§6–§9), `biomed-biomechanics-devices-and-biostatistics` (§10–§15). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    within-subject designs, and mixed-effects models dominate (§15 → `biomed-biomechanics-devices-and-biostatistics`).

---

## §16. Misconceptions

| Claim | Reality |
|---|---|
| "95% sensitivity and specificity means a positive is probably real" | ⚠️ **At 1% prevalence, PPV is 16%** (§4.1 → `biomed-clinical-data-ml-and-bioinformatics`) |
| "High AUROC means the model is clinically useful" | ⚠️ **AUROC is prevalence-independent and says nothing about calibration or net benefit** (§4.2 → `biomed-clinical-data-ml-and-bioinformatics`) |
| "Accuracy is a reasonable metric" | ⚠️ **99% by always predicting the majority class** (§4.1 → `biomed-clinical-data-ml-and-bioinformatics`) |
| "The model generalizes — we cross-validated" | ⚠️ **Internal CV is rung one of five** (§4.4 → `biomed-clinical-data-ml-and-bioinformatics`) |
| "We split randomly, so it's fair" | ⚠️ **Split by patient. Slices from one patient leak** (§4.4 → `biomed-clinical-data-ml-and-bioinformatics`) |
| "MRI intensities are comparable across scans" | ⚠️ **They have no absolute meaning. CT's Hounsfield units do** (§2.1 → `biomed-signals-and-medical-imaging`) |
| "The pixel values are Hounsfield units" | ⚠️ **Not until you apply RescaleSlope/Intercept** (§2.2 → `biomed-signals-and-medical-imaging`) |
| "Dice 0.9 means the segmentation is good" | ⚠️ **Dice is insensitive to small catastrophic boundary errors. Check Hausdorff** (§2.4 → `biomed-signals-and-medical-imaging`) |
| "UMAP shows the cell types are far apart" | ⚠️ **UMAP distances and cluster sizes are artifacts** (§5.3 → `biomed-clinical-data-ml-and-bioinformatics`) |
| "AlphaFold solved protein structure" | ⚠️ **Single static conformations. Check pLDDT *and* PAE** (§6 → `biomed-structural-systems-biology-and-pharmacology`) |
| "Half-life determines dosing" | ⚠️ **Clearance is the physiological parameter; t½ is derived** (§8 → `biomed-structural-systems-biology-and-pharmacology`) |
| "Double the dose, double the concentration" | ⚠️ **Not with saturable elimination — phenytoin, ethanol** (§8 → `biomed-structural-systems-biology-and-pharmacology`) |
| "Volume of distribution is a real volume" | ⚠️ **Apparent; can exceed total body water** (§8 → `biomed-structural-systems-biology-and-pharmacology`) |
| "A notch filter cleans up the ECG" | ⚠️ **60 Hz is inside the diagnostic band; it distorts the QRS** (§1.2 → `biomed-signals-and-medical-imaging`) |
| "Any ECG filter setting is fine" | ⚠️ **0.5–40 Hz monitoring settings invalidate ST analysis** (§1.2 → `biomed-signals-and-medical-imaging`) |
| "Missing lab values should be imputed" | ⚠️ **Missingness is a clinical decision and is informative** (§4.3 → `biomed-clinical-data-ml-and-bioinformatics`) |
| "The implant should be as strong as possible" | ⚠️ **Stiffness mismatch causes stress shielding and resorption** (§10 → `biomed-biomechanics-devices-and-biostatistics`, §11 → `biomed-biomechanics-devices-and-biostatistics`) |
| "We can grow a solid organ" | ⚠️ **~150–200 µm oxygen diffusion limit. Vascularization is unsolved** (§12 → `biomed-biomechanics-devices-and-biostatistics`) |
| "Spike sorting is required for BCI" | ⚠️ **Threshold crossings work well for many decoders** (§13.2 → `biomed-biomechanics-devices-and-biostatistics`) |
| "The BCI electrode will last" | ⚠️ **Glial encapsulation degrades signal over months** (§13.1 → `biomed-biomechanics-devices-and-biostatistics`) |
| "r = 0.99 means the two methods agree" | ⚠️ **Use Bland–Altman. One can read double the other** (§15 → `biomed-biomechanics-devices-and-biostatistics`) |
| "Repeated measures can be pooled" | ⚠️ **Inflates N and manufactures significance. Mixed models** (§15 → `biomed-biomechanics-devices-and-biostatistics`) |
| "Blood is a Newtonian fluid" | Shear-thinning; Fåhræus–Lindqvist in small vessels (§9 → `biomed-structural-systems-biology-and-pharmacology`) |
| "TPM lets me compare samples" | ⚠️ **Within-sample only. Use median-of-ratios or TMM across** (§5.3 → `biomed-clinical-data-ml-and-bioinformatics`) |

---

## §17. Numbers

```
PHYSIOLOGY
Resting HR 60–100 bpm · BP 120/80 mmHg · RR 12–20/min · Temp 37 °C
Cardiac output ~5 L/min · Blood volume ~5 L · Stroke volume ~70 mL
Ejection fraction 55–70% · Mean arterial pressure ≈ DBP + ⅓(SBP−DBP)
SpO₂ 95–100% · Tidal volume ~500 mL · pH 7.35–7.45
Nernst at 37 °C: E ≈ (61.5/z)·log₁₀([out]/[in]) mV
Resting membrane potential ≈ −70 mV · AP peak ≈ +30 mV
Neuron firing 1–200 Hz · Cortical neurons ~16 billion

SIGNALS
ECG 0.1–5 mV, 0.05–150 Hz diagnostic · EEG 10–100 µV, 0.5–100 Hz
EMG 50 µV–5 mV, 20–500 Hz · Spikes 300–6000 Hz, sample ≥20 kHz
⚠️ QRS 80–120 ms · PR 120–200 ms · QT 350–450 ms (rate-corrected)

IMAGING
HU: air −1000, fat −100, water 0, muscle +40, bone +1000…+3000
CT 0.5–1 mm · MRI ~1 mm · PET 4–5 mm · OCT 1–15 µm · WSI 0.25 µm/px

MOLECULAR
Human genome 3.1 Gb, ~20,000 protein-coding genes
Exome ~1% of genome · ~4–5 million variants per genome vs reference
⚠️ Germline WGS ~30× · Somatic 100–1000×
Q30 = 1 error in 1000 · Cell ~10 µm · Protein 1–10 nm
Typical cell ~10⁴–10⁵ mRNA molecules

MECHANICS
Cortical bone 15–20 GPa · Tendon 1–2 GPa · Cartilage 0.5–10 MPa
Artery 0.1–1 MPa · ⚠️ Brain 1–10 kPa
Gait: stance 60%, swing 40%

ENGINEERING LIMITS
⚠️ Oxygen diffusion limit ~150–200 µm
Scaffold pores 100–500 µm (bone), porosity >90%
⚠️ Prosthetic control latency budget <100–125 ms
Z' factor >0.5 for a usable screening assay
Steady state at 4–5 half-lives
```

---

## §18. Books

| Author | Work | Why |
|---|---|---|
| **Guyton & Hall** | ***Textbook of Medical Physiology*** | ⚠️ **The physiology reference. Everything downstream depends on it** |
| **Rangayyan** | *Biomedical Signal Analysis* | §1 → `biomed-signals-and-medical-imaging`, thorough and practical |
| **Sörnmo & Laguna** | *Bioelectrical Signal Processing in Cardiac and Neurological Applications* | ⚠️ **The best treatment of ECG/EEG processing** |
| **Prince & Links** | *Medical Imaging Signals and Systems* | §2 → `biomed-signals-and-medical-imaging` physics, properly derived |
| **Bushberg et al.** | *The Essential Physics of Medical Imaging* | The comprehensive imaging physics reference |
| **Fitzpatrick & Sonka** | *Handbook of Medical Imaging* | Registration and segmentation depth |
| **Durbin, Eddy, Krogh, Mitchison** | ***Biological Sequence Analysis*** | ⚠️ **The HMM/alignment mathematics. Still unmatched** |
| **Compeau & Pevzner** | *Bioinformatics Algorithms* | Algorithmic, teachable |
| **Alon** | ***An Introduction to Systems Biology*** | ⚠️ **Network motifs (§7 → `biomed-structural-systems-biology-and-pharmacology`), and beautifully written** |
| **Rowland & Tozer** | *Clinical Pharmacokinetics and Pharmacodynamics* | §8 → `biomed-structural-systems-biology-and-pharmacology`, the standard |
| **Gabrielsson & Weiner** | *PK/PD Data Analysis* | Practical modelling with worked datasets |
| **Keener & Sneyd** | *Mathematical Physiology* | ⚠️ **§9 → `biomed-structural-systems-biology-and-pharmacology`'s models, rigorously. Two volumes** |
| **Dayan & Abbott** | *Theoretical Neuroscience* | Computational neuroscience foundations |
| **Fung** | *Biomechanics: Mechanical Properties of Living Tissues* | ⚠️ **The founding text of §10 → `biomed-biomechanics-devices-and-biostatistics`** |
| **Ratner et al.** | *Biomaterials Science* | §11 → `biomed-biomechanics-devices-and-biostatistics`, comprehensive |
| **Lanza, Langer & Vacanti** | *Principles of Tissue Engineering* | §12 → `biomed-biomechanics-devices-and-biostatistics` |
| **Enderle & Bronzino** | *Introduction to Biomedical Engineering* | The broad survey |
| **Bronzino & Peterson** | *The Biomedical Engineering Handbook* | Reference, multi-volume |
| **Vittinghoff et al.** | *Regression Methods in Biostatistics* | §15 → `biomed-biomechanics-devices-and-biostatistics`, applied and clear |
| **Harrell** | *Regression Modeling Strategies* | ⚠️ **On validation, calibration and overfitting — the antidote to §4 → `biomed-clinical-data-ml-and-bioinformatics`'s failures** |

**Primary and practical**: **PubMed/PMC**, **bioRxiv/medRxiv**, **PhysioNet**
(⚠️ **open physiological datasets — MIMIC, PTB-XL, and the reference implementations that
go with them**), **The Cancer Imaging Archive**, **UK Biobank**, **Ensembl/UCSC/NCBI**,
**PDB**, **GATK Best Practices**, **Bioconductor**, **MONAI**, **nnU-Net**, **scanpy /
Seurat**, **OpenSim** (§10 → `biomed-biomechanics-devices-and-biostatistics`), **NEURON / Brian2** (§9 → `biomed-structural-systems-biology-and-pharmacology`).

---

## §19. Quick Reference

### 19.1 Equations
```
PPV = (Sens·Prev)/(Sens·Prev + (1−Spec)(1−Prev))     ⚠️ §4.1
Brier = (1/N)Σ(p_i − y_i)²                            calibration
Dice = 2|A∩B|/(|A|+|B|)                               segmentation
MI(A,B) = H(A)+H(B)−H(A,B)                            multimodal registration
HU = pixel·RescaleSlope + RescaleIntercept            ⚠️ §2.2
E_ion = (RT/zF)ln([out]/[in])                         Nernst
C_m dV/dt = I − ḡ_Na m³h(V−E_Na) − ḡ_K n⁴(V−E_K) − ḡ_L(V−E_L)   Hodgkin-Huxley
v = V_max[S]/(K_m+[S])                                Michaelis-Menten
θ = [L]ⁿ/(K_d+[L]ⁿ)                                   Hill
C(t) = (D/V)e^(−kt) · t½ = ln2/k · CL = kV            PK
C_ss,avg = FD/(CL·τ) · loading = C_target·V/F         PK steady state
E = E_max·Cⁿ/(EC₅₀ⁿ+Cⁿ)                               PD
Q = πΔP r⁴/(8µL)                                      Poiseuille ⚠️ r⁴
Re = ρvD/µ                                            turbulence onset
C dP/dt + P/R = Q(t)                                  2-element Windkessel
A = εcl                                               Beer-Lambert
Z' = 1 − 3(σ_p+σ_n)/|µ_p−µ_n|                        assay quality
h(t|X) = h₀(t)exp(βᵀX)                                Cox
Q = −10 log₁₀ P(error)                                Phred
```

### 19.2 Picker
| Need | Use |
|---|---|
| QRS detection | **Pan–Tompkins** + refractory + searchback (§1.3 → `biomed-signals-and-medical-imaging`) |
| Diagnostic ECG filtering | ⚠️ **0.05–150 Hz, zero-phase** (§1.2 → `biomed-signals-and-medical-imaging`) |
| Remove EEG blinks | **ICA**, or EOG regression (§1.3 → `biomed-signals-and-medical-imaging`) |
| Non-stationary spectral analysis | **Wavelets** (Morlet) or multitaper (§1.3 → `biomed-signals-and-medical-imaging`) |
| Multimodal image registration | ⚠️ **Mutual information + multi-resolution** (§2.4 → `biomed-signals-and-medical-imaging`) |
| Medical segmentation baseline | **nnU-Net** (§2.4 → `biomed-signals-and-medical-imaging`) |
| Segmentation metric that catches bad boundaries | ⚠️ **Hausdorff, not just Dice** (§2.4 → `biomed-signals-and-medical-imaging`) |
| Imbalanced classification metric | **AUPRC**, and calibration (§4.1 → `biomed-clinical-data-ml-and-bioinformatics`–4.2) |
| Fix overconfident network | **Temperature scaling** (§4.2 → `biomed-clinical-data-ml-and-bioinformatics`) |
| Is the model clinically useful | ⚠️ **Decision curve analysis** (§4.2 → `biomed-clinical-data-ml-and-bioinformatics`) |
| Read alignment, short | **BWA-MEM** / Bowtie2 (§5.1 → `biomed-clinical-data-ml-and-bioinformatics`) |
| Read alignment, long | **minimap2** (§5.1 → `biomed-clinical-data-ml-and-bioinformatics`) |
| Germline variants | **GATK HaplotypeCaller** or DeepVariant (§5.2 → `biomed-clinical-data-ml-and-bioinformatics`) |
| Differential expression | ⚠️ **DESeq2/edgeR — negative binomial** (§5.3 → `biomed-clinical-data-ml-and-bioinformatics`) |
| Single-cell clustering | Graph + **Leiden**; ⚠️ UMAP for pictures only (§5.3 → `biomed-clinical-data-ml-and-bioinformatics`) |
| Genome-scale metabolism | **FBA** (§7 → `biomed-structural-systems-biology-and-pharmacology`) |
| Low molecule counts | ⚠️ **Gillespie, not ODEs** (§7 → `biomed-structural-systems-biology-and-pharmacology`) |
| Population PK | **Nonlinear mixed effects**; allometric CL ∝ WT^0.75 (§8 → `biomed-structural-systems-biology-and-pharmacology`) |
| Extrapolate to new population | **PBPK** (§8 → `biomed-structural-systems-biology-and-pharmacology`) |
| Large spiking networks | **Izhikevich** or integrate-and-fire (§9 → `biomed-structural-systems-biology-and-pharmacology`) |
| Repeated measures | ⚠️ **Mixed-effects models** (§15 → `biomed-biomechanics-devices-and-biostatistics`) |
| Many hypotheses | **Benjamini–Hochberg FDR** (§15 → `biomed-biomechanics-devices-and-biostatistics`) |
| Method comparison | ⚠️ **Bland–Altman, not correlation** (§15 → `biomed-biomechanics-devices-and-biostatistics`) |
| Time-to-event with censoring | **Kaplan–Meier + Cox** (§15 → `biomed-biomechanics-devices-and-biostatistics`) |

### 19.3 Debugging checklist
- [ ] Did you apply RescaleSlope/Intercept before treating pixels as HU? (§2.2 → `biomed-signals-and-medical-imaging`)
- [ ] Is laterality derived from ImageOrientationPatient, not display? (§2.2 → `biomed-signals-and-medical-imaging`)
- [ ] Slice spacing computed from positions, not SliceThickness? (§2.2 → `biomed-signals-and-medical-imaging`)
- [ ] MRI intensities normalized before cross-site modelling? (§2.1 → `biomed-signals-and-medical-imaging`)
- [ ] ECG filter band appropriate to the claim (diagnostic vs monitoring)? (§1.2 → `biomed-signals-and-medical-imaging`)
- [ ] Zero-phase filtering where intervals are measured? (§1.2 → `biomed-signals-and-medical-imaging`)
- [ ] Split by patient, not by sample? (§4.4 → `biomed-clinical-data-ml-and-bioinformatics`)
- [ ] Any feature downstream of clinical suspicion? (§4.3 → `biomed-clinical-data-ml-and-bioinformatics`)
- [ ] Missingness modelled rather than naively imputed? (§4.3 → `biomed-clinical-data-ml-and-bioinformatics`)
- [ ] PPV computed at the *deployment* prevalence? (§4.1 → `biomed-clinical-data-ml-and-bioinformatics`)
- [ ] Calibration checked, not just discrimination? (§4.2 → `biomed-clinical-data-ml-and-bioinformatics`)
- [ ] Units stored with values; UCUM? (§3 → `biomed-clinical-data-ml-and-bioinformatics`)
- [ ] Negation handled in any text processing? (§3 → `biomed-clinical-data-ml-and-bioinformatics`)
- [ ] Read depth adequate for germline vs somatic? (§5.2 → `biomed-clinical-data-ml-and-bioinformatics`)
- [ ] Normalization method valid for across-sample comparison? (§5.3 → `biomed-clinical-data-ml-and-bioinformatics`)
- [ ] Both pLDDT and PAE checked on predicted structures? (§6 → `biomed-structural-systems-biology-and-pharmacology`)
- [ ] Proportional hazards assumption tested? (§15 → `biomed-biomechanics-devices-and-biostatistics`)
- [ ] Clustering/repeated measures accounted for in the model? (§15 → `biomed-biomechanics-devices-and-biostatistics`)

---

## §20. Method

**This is the technical layer only.** Regulatory pathways, quality management, and software
lifecycle process were deliberately excluded on request — they are a large separate subject
and would have displaced the engineering content.

**Sources.** §1–§15 → `biomed-signals-and-medical-imaging`, `biomed-clinical-data-ml-and-bioinformatics`, `biomed-structural-systems-biology-and-pharmacology`, `biomed-biomechanics-devices-and-biostatistics` rest on the standard textbook and primary literature listed in §18 —
**Guyton & Hall, Sörnmo & Laguna, Prince & Links, Durbin et al., Alon, Rowland & Tozer,
Keener & Sneyd, Fung, Ratner, Harrell** — plus foundational primary results
(**Hodgkin & Huxley 1952, Pan & Tompkins 1985, Michaelis & Menten 1913, Bland & Altman
1986, Cox 1972**). **None of this has a currency dependency and none was web-verified**;
the physics, physiology and mathematics are settled and the textbooks are the authority.

**Confidence.** **High** throughout §1–§15 → `biomed-signals-and-medical-imaging`, `biomed-clinical-data-ml-and-bioinformatics`, `biomed-structural-systems-biology-and-pharmacology`, `biomed-biomechanics-devices-and-biostatistics`. The equations are standard and stated with
their assumptions; the numerical ranges in §17 are **representative physiological and
engineering values, not specifications** — normal ranges vary by lab, population and
method, and should be taken as orientation rather than reference intervals.

⚠️ **Two areas carry real caveats.** **Tool recommendations in §19.2** (nnU-Net, BWA-MEM,
DESeq2, minimap2) reflect what has been the durable default for several years, but
**bioinformatics tooling turns over faster than the rest of this document** — verify
against current best-practice guides before committing a pipeline. And **§4.3 → `biomed-clinical-data-ml-and-bioinformatics`'s documented
failure cases** (shortcut features, the spending-as-need proxy) are drawn from the
published literature on model failure; **I have described the mechanisms, which generalize,
rather than adjudicating any specific system's current behaviour.**

**⚠️ Nothing here is clinical guidance.** The dosing, interval and physiological figures
are engineering orientation for people building systems, not a basis for patient care.
