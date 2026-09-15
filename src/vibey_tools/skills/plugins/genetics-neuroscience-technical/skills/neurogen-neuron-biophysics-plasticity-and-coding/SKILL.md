---
name: neurogen-neuron-biophysics-plasticity-and-coding
description: "Use when reasoning about how neurons compute: neuron biophysics including membrane potentials, the Hodgkin-Huxley treatment, cable theory and synaptic transmission; plasticity including long-term potentiation and depression, spike-timing-dependent plasticity and homeostatic mechanisms; and neural coding — rate versus temporal codes, population coding, and decoding methods."
---

# Genetics and Neuroscience: Neuron Biophysics, Plasticity, and Neural Coding

> **Part 3 of 5** of the *Genetics and Neuroscience* reference (plugin `genetics-neuroscience-technical`), covering §7–§9. Sibling skills: `neurogen-molecular-genetics-and-regulation` (§0–§3), `neurogen-population-genetics-and-genome-engineering` (§4–§6), `neurogen-circuits-neuromodulation-and-neural-engineering` (§10–§14), `neurogen-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Molecular mechanism, population genetics and cellular neuroscience are settled; therapeutic genome editing and connectomics moved materially. See §17 → `neurogen-reference` for the frontier.

> **Scope.** Complements a biomedical-engineering reference, which covered bioinformatics
> *pipelines* (alignment, variant calling), structural biology, and neural interfaces at
> the *hardware* level. **This document is the underlying biology and its mathematics.**
> Cross-references point there rather than repeating.
>
> **⚠️ GOTCHA** boxes mark where the standard summary is wrong or where a number is
> routinely misinterpreted.
>
> **The three facts that recur throughout:**
> 1. **⚠️ Regulation, not gene content, explains most biological difference.** Humans and
>    chimps share nearly all protein-coding sequence; the difference is when and where
>    genes are expressed (§2 → `neurogen-molecular-genetics-and-regulation`).
> 2. **⚠️ Heritability is a population statistic, not a property of an individual or a
>    trait.** Almost every public misuse of the word stems from missing this (§4.1 → `neurogen-population-genetics-and-genome-engineering`).
> 3. **⚠️ The brain's computational unit is the circuit, not the neuron.** Single-cell
>    biophysics is well understood; how populations implement computation is not (§9, §17 → `neurogen-reference`).

---

## §7. Neuron Biophysics and Synapses

**[Hodgkin–Huxley, Nernst, and cable theory are derived in a biomedical-engineering
reference §9. Here: what they imply.]**

**Resting potential ≈ −70 mV**, set by K⁺ permeability and the Na⁺/K⁺-ATPase
(⚠️ **3 Na⁺ out : 2 K⁺ in — electrogenic, and it consumes a large share of the brain's
ATP**). **Action potential**: threshold ~−55 mV → Na⁺ influx (regenerative) → K⁺ efflux →
afterhyperpolarization. **Refractory period** enforces directionality and caps firing rate.

**Cable equation** for dendritic propagation:
```
λ = √(r_m/r_i)          ⚠️ length constant — how far a signal decays passively (0.1–1 mm)
τ_m = r_m·c_m           membrane time constant (~10–20 ms)
```
**⚠️ Passive decay is why dendrites need active conductances**; dendritic Na⁺ and Ca²⁺
channels support local spikes, making **the dendrite a computational unit, not a passive
cable** — individual branches can act as independent nonlinear subunits.

**Myelination and saltatory conduction**: ⚠️ **conduction velocity scales roughly linearly
with diameter in myelinated axons (~6 × diameter in µm m/s) but only as √diameter
unmyelinated** — which is why myelin is such an efficient solution.

**Synaptic transmission**: AP → **Ca²⁺ influx through voltage-gated channels** →
⚠️ **vesicle fusion is steeply Ca²⁺-dependent (roughly 4th power), which makes release
probabilistic and highly modulable** → neurotransmitter → receptor.

| Receptor | Type | Effect |
|---|---|---|
| **AMPA** | ionotropic glutamate | Fast excitatory, Na⁺/K⁺ |
| **NMDA** | ionotropic glutamate | ⚠️ **Mg²⁺ block relieved by depolarization + needs glutamate → a COINCIDENCE DETECTOR. Ca²⁺-permeable. This is the molecular basis of §8** |
| **Kainate** | ionotropic glutamate | Modulatory |
| **mGluR** | metabotropic | Slow modulation |
| **GABA_A** | ionotropic | ⚠️ **Fast inhibition via Cl⁻ — and the benzodiazepine/barbiturate target** |
| **GABA_B** | metabotropic | Slow inhibition, K⁺ |
| **Glycine** | ionotropic | Inhibition, spinal cord and brainstem |
| **nACh / mACh** | ionotropic / metabotropic | §11 → `neurogen-circuits-neuromodulation-and-neural-engineering` |

**⚠️ GABA is not always inhibitory.** Its effect depends on the **chloride reversal
potential**, which is set by the KCC2/NKCC1 transporter ratio. **In immature neurons GABA
is depolarizing**, and KCC2 downregulation in injury or epilepsy can make it depolarizing
again in adults — a real mechanism, not a curiosity.

**Short-term plasticity**: **facilitation** (residual Ca²⁺) and **depression** (vesicle
depletion). ⚠️ **A synapse is a dynamic filter — depressing synapses act as high-pass /
change detectors, facilitating ones as low-pass integrators.**

---

## §8. Plasticity

**Hebb**: cells that fire together wire together. Formalized:
```
Δw_ij = η · x_i · y_j          ⚠️ unstable — weights grow without bound
```
**Stabilizations**: **Oja's rule** (normalization, and ⚠️ **it converges to the first
principal component — Hebbian learning is PCA**), **BCM** (⚠️ **sliding threshold θ_M
that adapts to recent activity, giving both LTP and LTD**), **synaptic scaling**
(homeostatic, multiplicative, ⚠️ **preserves relative weights while stabilizing total
drive**).

**LTP/LTD mechanism**: **NMDA receptor coincidence detection** (§7) → Ca²⁺ influx →
⚠️ **high Ca²⁺ → CaMKII → AMPA receptor insertion → LTP; modest Ca²⁺ → calcineurin/PP1 →
AMPA removal → LTD.** **The amplitude of the calcium transient is the sign of the
plasticity** — one mechanism, two directions.

**⚠️ STDP** — the timing rule:
```
pre before post (~+10 ms)   → potentiation
post before pre (~−10 ms)   → depression
Window ~±20–50 ms, asymmetric and exponentially decaying
```
**⚠️ STDP is a real phenomenon, not a universal law**: the window shape varies by synapse
type, brain region, and dendritic location, and **it depends strongly on firing rate and
on neuromodulatory state** — which is the bridge to §11 → `neurogen-circuits-neuromodulation-and-neural-engineering`.

**Three-factor rules** — ⚠️ **pre × post × neuromodulator.** This is how a global reward or
novelty signal gates which coincidences get consolidated, and it is the most plausible
biological answer to the credit-assignment problem.

**Structural plasticity**: spine formation and elimination, ⚠️ **and consolidation requires
protein synthesis — which is why late-LTP is blocked by translation inhibitors and early
LTP isn't.** **Synaptic tagging and capture** explains how weakly-stimulated synapses can
capture plasticity-related proteins made elsewhere.

---

## §9. Neural Coding

**Rate coding** — information in firing frequency. Simple, robust, ⚠️ **and slow: estimating
a rate takes time.**
**Temporal coding** — spike timing carries information. ⚠️ **Demonstrated in auditory
localization (microsecond interaural timing) and in olfaction; contested elsewhere.**
**Population coding** — ⚠️ **the modern default**. Information is distributed; individual
neurons are noisy and ambiguous.

**Tuning curves and the population vector**: `v̂ = Σ_i r_i · c_i` — the classic result from
motor cortex, and the basis of early BCI decoders (see a biomedical-engineering
reference §13).

**⚠️ Noise correlations matter and are counterintuitive**: correlated variability between
neurons can either help or hurt population coding depending on whether the correlation
aligns with the signal direction. **Averaging over more neurons does not reduce noise if
the noise is shared.**

**Information theory**: `I(S;R) = H(R) − H(R|S)`. ⚠️ **Estimating mutual information from
limited spike data is severely biased upward; bias-correction is mandatory.**

**Efficient coding** (Barlow) — sensory systems decorrelate and match their dynamic range
to input statistics. ⚠️ **Predicts centre-surround receptive fields and adaptation from
first principles**, and it works.
**Predictive coding** — cortex propagates prediction *error*, not raw signal.
⚠️ **Influential and genuinely contested; the anatomical evidence for the required
error-unit populations is debated.**
**Sparse coding** — few active units, overcomplete basis; ⚠️ **learning sparse codes on
natural images reproduces V1 simple-cell receptive fields.**

**⚠️ Dimensionality**: population activity typically occupies a **low-dimensional manifold**
far smaller than the number of neurons. **Neural trajectories, fixed points and line
attractors are the current working vocabulary for cortical computation.**
