---
name: neurogen-reference
description: "Use when correcting a common genetics or neuroscience misconception, checking a magnitude or physiological value, asking what actually moved at the frontier (therapeutic genome editing and connectomics), finding the textbook canon, or needing the core equations, a method picker, and an interpretation checklist. Companion to the other genetics-neuroscience skills."
---

# Genetics and Neuroscience: Misconceptions, Numbers, and the Frontier

> **Part 5 of 5** of the *Genetics and Neuroscience* reference (plugin `genetics-neuroscience-technical`), covering §15–§20. Sibling skills: `neurogen-molecular-genetics-and-regulation` (§0–§3), `neurogen-population-genetics-and-genome-engineering` (§4–§6), `neurogen-neuron-biophysics-plasticity-and-coding` (§7–§9), `neurogen-circuits-neuromodulation-and-neural-engineering` (§10–§14). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Molecular mechanism, population genetics and cellular neuroscience are settled; therapeutic genome editing and connectomics moved materially. See §17 below for the frontier.

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
>    biophysics is well understood; how populations implement computation is not (§9 → `neurogen-neuron-biophysics-plasticity-and-coding`, §17).

---

## §15. Misconceptions

| Claim | Reality |
|---|---|
| "Synonymous mutations are silent" | ⚠️ **They affect translation speed, folding, mRNA stability, splicing** (§1.1 → `neurogen-molecular-genetics-and-regulation`) |
| "Nonsense mutation → truncated protein" | ⚠️ **NMD often destroys the transcript entirely — position-dependent** (§1.2 → `neurogen-molecular-genetics-and-regulation`) |
| "The nearest gene to a GWAS hit is the causal gene" | ⚠️ **Enhancers act over hundreds of kb, past nearer genes** (§2.1 → `neurogen-molecular-genetics-and-regulation`, §4.3 → `neurogen-population-genetics-and-genome-engineering`) |
| "Heritability tells you how genetic a person's trait is" | ⚠️ **It's a population variance ratio, not an individual property** (§4.1 → `neurogen-population-genetics-and-genome-engineering`) |
| "High heritability means not modifiable" | ⚠️ **Height, PKU** (§4.1 → `neurogen-population-genetics-and-genome-engineering`) |
| "Within-group heritability implies between-group genetics" | ⚠️ **Mathematically it does not** (§4.1 → `neurogen-population-genetics-and-genome-engineering`) |
| "The lead GWAS SNP is the causal variant" | ⚠️ **Usually just in LD with it** (§4.2 → `neurogen-population-genetics-and-genome-engineering`) |
| "Polygenic scores work across populations" | ⚠️ **Accuracy drops substantially outside the discovery ancestry** (§4.3 → `neurogen-population-genetics-and-genome-engineering`) |
| "Missing heritability means the studies were wrong" | Largely resolved: polygenicity, rare variants, twin-estimate bias (§4.3 → `neurogen-population-genetics-and-genome-engineering`) |
| "CRISPR rewrites any gene" | ⚠️ **Knockout is easy; HDR knock-in is inefficient and near-absent in post-mitotic cells** (§5.1 → `neurogen-population-genetics-and-genome-engineering`) |
| "Off-target editing is the main safety risk" | ⚠️ **On-target large deletions, chromothripsis and LOH are arguably bigger** (§5.1 → `neurogen-population-genetics-and-genome-engineering`) |
| "Base editing can make any change" | ⚠️ **Transitions only, with bystander edits in the window** (§5.1 → `neurogen-population-genetics-and-genome-engineering`) |
| "The hard part of gene therapy is the editor" | ⚠️ **Delivery and tropism are the bottleneck** (§6.1 → `neurogen-population-genetics-and-genome-engineering`) |
| "We use 10% of our brains" | Nonsense; metabolically and evolutionarily impossible |
| "GABA is the inhibitory neurotransmitter" | ⚠️ **Depends on E_Cl — depolarizing in immature neurons and after injury** (§7 → `neurogen-neuron-biophysics-plasticity-and-coding`) |
| "Dopamine is the pleasure chemical" | ⚠️ **Reward prediction error and wanting, not liking** (§11 → `neurogen-circuits-neuromodulation-and-neural-engineering`) |
| "Neurons are the computational unit" | ⚠️ **Dendritic branches are subunits; populations are the unit** (§7 → `neurogen-neuron-biophysics-plasticity-and-coding`, §9 → `neurogen-neuron-biophysics-plasticity-and-coding`) |
| "Left-brain/right-brain personality types" | Lateralization is real for specific functions; the personality claim is not |
| "Adult brains don't change" | ⚠️ **Plasticity persists; even critical periods can be reopened** (§12 → `neurogen-circuits-neuromodulation-and-neural-engineering`) |
| "Glia are support cells" | ⚠️ **Pruning, myelination, blood flow, synaptic modulation** (§12 → `neurogen-circuits-neuromodulation-and-neural-engineering`) |
| "Calcium imaging shows spikes" | ⚠️ **A slow proxy — 100–500 ms decay, cannot resolve fast trains** (§13 → `neurogen-circuits-neuromodulation-and-neural-engineering`) |
| "Optogenetics shows what the circuit normally does" | ⚠️ **Non-physiological synchrony; a gain-of-function caveat** (§13 → `neurogen-circuits-neuromodulation-and-neural-engineering`) |
| "DBS works by shutting the target off" | ⚠️ **Mechanism genuinely unsettled** (§14 → `neurogen-circuits-neuromodulation-and-neural-engineering`) |
| "We've mapped the brain" | ⚠️ **One fly brain and one cubic millimetre of mouse cortex** (§17.2) |

---

## §16. Numbers

```
GENETICS
Human genome 3.1 Gb, 46 chromosomes · ~20,000 protein-coding genes
⚠️ Coding ~1–2% of genome · >100,000 protein isoforms via splicing
Mutation rate 1.1×10⁻⁸/base/generation → ~70 de novo per individual
⚠️ +~2 de novo per year of paternal age
Genome-wide significance p < 5×10⁻⁸ · Human genetic diversity ~0.1% between individuals
Genes with imprinting ~100–200 · X-inactivation escape ~15%
Cas9 PAM: 5′-NGG-3′ (SpCas9) · guide 20 nt · base editing window ~4–8 nt
AAV capacity ~4.7 kb · SpCas9 CDS ~4.2 kb ⚠️

NEUROSCIENCE
~86 billion neurons · ~85 billion glia
⚠️ Cerebellum holds ~69 billion (mostly granule cells) — over half of all neurons
Cortex ~16 billion neurons · Synapses ~10¹⁴–10¹⁵
Cortical neuron ~7,000 synapses · E:I ratio ~80:20
Resting −70 mV · Threshold ~−55 mV · AP peak +30 mV · AP duration ~1 ms
Refractory ~1–2 ms · τ_m 10–20 ms · λ 0.1–1 mm
Conduction 0.5–120 m/s (⚠️ ~6× diameter in µm, myelinated)
Firing rates 0.1–200 Hz · Synaptic delay 0.5–2 ms
⚠️ STDP window ±20–50 ms
Brain 2% of body mass, ⚠️ ~20% of resting metabolic rate
Two-photon depth ~500–800 µm · GCaMP decay 100–500 ms
```

---

## §17. Frontier — What Actually Moved

**[Everything above is settled. These two areas changed materially and are worth dating.]**

### 17.1 Therapeutic genome editing

**⚠️ Casgevy (exagamglogene autotemcel) is the landmark**: the first approved
CRISPR-Cas9 therapy, for sickle cell disease and transfusion-dependent β-thalassemia,
approved 2023. **Ex vivo** — cells edited outside the body and reinfused. ⚠️ **Reported
~$2.2M price, which has become a structural test of whether gene editing works as a
healthcare intervention rather than only as science.**

**In vivo editing has now been demonstrated repeatedly:**
- **NTLA-2001** (transthyretin amyloidosis, LNP to liver) — **~87% TTR protein reduction at
  12 months**, competitive with approved siRNA therapies, with Phase 3 studies listed.
- **⚠️ The KJ case (reported NEJM, May 2025) is the one to know**: a **personalized in vivo
  CRISPR therapy for an infant with CPS1 deficiency, developed, FDA-approved and delivered
  in six months**, via LNP by IV infusion. Dosed three times, symptoms and medication
  dependence reduced, no serious side effects reported. **It sets precedent for a
  regulatory pathway for rapid approval of platform therapies** — arguably more significant
  than the editing itself.
- **Prime editing reached patients**: **PM359** for chronic granulomatous disease showed
  **restored NADPH oxidase activity in 58% of neutrophils by Day 15 and 66% by Day 30** in
  the first dosed patient — above the anticipated clinical threshold.
- **Base editing** in trials for AATD and hypercholesterolemia; **over 50 CRISPR trials
  actively recruiting globally as of mid-2026.**

> **⚠️ GOTCHA — a source conflict I could not resolve, so treat with caution.** One 2026
> source lists **EDIT-101 (Leber congenital amaurosis) as FDA-approved alongside Casgevy.**
> ⚠️ **Multiple other sources from the same period describe Casgevy as the only approved
> CRISPR therapy.** I have not been able to reconcile these. **Verify against FDA directly
> before relying on it.** The safe statement: **Casgevy is unambiguously approved; treat
> any second approval as unconfirmed.**

**⚠️ The honest summary**: the technology works, and the remaining problems are
**delivery beyond liver, manufacturing, and cost** — not editing chemistry.

### 17.2 Connectomics

**⚠️ *Nature Methods* named EM-based connectomics its Method of the Year for 2025**, on the
strength of two results:

**FlyWire (2024)** — **the complete connectome of an adult *Drosophila* brain**:
**139,255 neurons and ~5 × 10⁷ chemical synapses**, with annotations for cell types,
classes, nerves, hemilineages and predicted neurotransmitters. ⚠️ **The first adult
connectome completed since *C. elegans***, and it required years of distributed human
proofreading on top of automated segmentation.

**MICrONS (2025)** — **one cubic millimetre of mouse visual cortex**: EM reconstruction of
**>200,000 cells and ~0.5 billion synapses**, ⚠️ **co-registered with calcium imaging of
~75,000 neurons in the same animal viewing natural and synthetic stimuli.** **That
co-registration is the point** — structure and function in the same tissue.

> **⚠️ GOTCHA — scale honestly.** One cubic millimetre is roughly **0.2% of mouse cortex.**
> A **full mouse connectome is estimated to require on the order of 500 petabytes**, with
> **imaging alone costing $200–300M**, and human proofreading for a human brain would be
> vastly harder still. ⚠️ **"We've mapped the brain" is wrong by several orders of
> magnitude**, and ⚠️ **the "fly brain upload" framing is a misreading**: simulations built
> on the connectome still require training on top of it to produce behaviour. **What the
> connectome gives you is the wiring — not the synaptic weights, the neuromodulatory state,
> or the dynamics.**

**⚠️ And the deeper limitation**: a connectome is a static, single-individual snapshot. It
does not contain plasticity (§8 → `neurogen-neuron-biophysics-plasticity-and-coding`), neuromodulation (§11 → `neurogen-circuits-neuromodulation-and-neural-engineering`), or short-term synaptic dynamics
(§7 → `neurogen-neuron-biophysics-plasticity-and-coding`) — **all of which are load-bearing for computation.**

---

## §18. Books

| Author | Work | Why |
|---|---|---|
| **Alberts et al.** | ***Molecular Biology of the Cell*** | ⚠️ **The foundation. If you own one, this** |
| **Watson et al.** | *Molecular Biology of the Gene* | The genetics-focused companion |
| **Strachan & Read** | *Human Molecular Genetics* | Clinical and human-specific |
| **Hartl & Clark** | *Principles of Population Genetics* | §4 → `neurogen-population-genetics-and-genome-engineering`, standard |
| **Falconer & Mackay** | ***Introduction to Quantitative Genetics*** | ⚠️ **The heritability mathematics, done properly** |
| **Lynch & Walsh** | *Genetics and Analysis of Quantitative Traits* | The deep reference |
| **Doudna & Sternberg** | *A Crack in Creation* | CRISPR from a discoverer; accessible |
| **Kandel et al.** | ***Principles of Neural Science*** | ⚠️ **The neuroscience reference. Comprehensive and readable** |
| **Purves et al.** | *Neuroscience* | The friendlier undergraduate text |
| **Dayan & Abbott** | ***Theoretical Neuroscience*** | ⚠️ **§8 → `neurogen-neuron-biophysics-plasticity-and-coding`, §9 → `neurogen-neuron-biophysics-plasticity-and-coding`'s mathematics** |
| **Gerstner et al.** | *Neuronal Dynamics* | ⚠️ **Free online; the best modern computational treatment** |
| **Koch** | *Biophysics of Computation* | Dendrites and single-neuron computation |
| **Rieke et al.** | *Spikes: Exploring the Neural Code* | §9 → `neurogen-neuron-biophysics-plasticity-and-coding`, foundational |
| **Sterling & Laughlin** | *Principles of Neural Design* | ⚠️ **Why brains are built the way they are — energy and information** |
| **Luo** | *Principles of Neurobiology* | Modern, circuit-focused |
| **Sanes, Reh & Harris** | *Development of the Nervous System* | §12 → `neurogen-circuits-neuromodulation-and-neural-engineering` |
| **Buzsáki** | *Rhythms of the Brain* | §10 → `neurogen-circuits-neuromodulation-and-neural-engineering`'s oscillations, from the authority |

**Primary and data**: **gnomAD** (⚠️ **population allele frequencies — check every variant
here first**), **ClinVar**, **OMIM**, **Ensembl/UCSC**, **GWAS Catalog**, **GTEx**
(eQTLs), **ENCODE** (regulatory elements), **Allen Brain Atlas**, **FlyWire** and
**MICrONS** (§17.2), **NeuroMorpho**, **DANDI**, **Addgene** (⚠️ **plasmids, and the
protocols with them**), **bioRxiv**.

---

## §19. Quick Reference

### 19.1 Equations
```
p² + 2pq + q² = 1                       Hardy-Weinberg
h² = V_A/V_P · H² = V_G/V_P             ⚠️ narrow vs broad sense §4.1
D = p_AB − p_A·p_B · D_t = D_0(1−c)^t   linkage disequilibrium decay
q̂ ≈ √(µ/s) recessive · µ/s dominant     mutation-selection balance
PRS_i = Σ_j β_j·G_ij                    polygenic score
λ = √(r_m/r_i) · τ_m = r_m·c_m          cable constants
Δw = η·x·y                              Hebb (⚠️ unstable)
δ = r + γV(s′) − V(s)                   ⚠️ dopamine RPE = TD error §11
I(S;R) = H(R) − H(R|S)                  mutual information
v̂ = Σ r_i·c_i                           population vector
```

### 19.2 Picker
| Need | Tool |
|---|---|
| Knock out a gene | **Cas9 + NHEJ** frameshift (§5.1 → `neurogen-population-genetics-and-genome-engineering`) |
| Precise single-base change | ⚠️ **Base editor (transitions) or prime editor (any)** (§5.1 → `neurogen-population-genetics-and-genome-engineering`) |
| Change expression without editing DNA | **CRISPRi/a (dCas9)** (§5.1 → `neurogen-population-genetics-and-genome-engineering`) |
| Transient knockdown | RNAi or Cas13 (§5.1 → `neurogen-population-genetics-and-genome-engineering`) |
| Edit in post-mitotic tissue | ⚠️ **Base/prime editing — HDR won't work** (§5.1 → `neurogen-population-genetics-and-genome-engineering`) |
| In vivo liver delivery | **LNP** (§6.1 → `neurogen-population-genetics-and-genome-engineering`) |
| Long-term expression, small cargo | **AAV** ⚠️ (4.7 kb) (§6.1 → `neurogen-population-genetics-and-genome-engineering`) |
| Ex vivo cell editing | ⚠️ **RNP electroporation** (§6.1 → `neurogen-population-genetics-and-genome-engineering`) |
| Genome-wide functional screen | Pooled CRISPR; ⚠️ **Perturb-seq for rich readout** (§6.2 → `neurogen-population-genetics-and-genome-engineering`) |
| Millisecond causal circuit test | **Optogenetics** (§13 → `neurogen-circuits-neuromodulation-and-neural-engineering`) |
| Hours-long circuit manipulation | **DREADDs** ⚠️ (CNO caveat) (§13 → `neurogen-circuits-neuromodulation-and-neural-engineering`) |
| Population activity, many neurons | **GCaMP two-photon** or **Neuropixels** (§13 → `neurogen-circuits-neuromodulation-and-neural-engineering`) |
| Single-cell biophysics | **Patch clamp** (§13 → `neurogen-circuits-neuromodulation-and-neural-engineering`) |
| Cell types with spatial position | **MERFISH / spatial transcriptomics** (§13 → `neurogen-circuits-neuromodulation-and-neural-engineering`) |
| Monosynaptic input mapping | **Rabies tracing** (§13 → `neurogen-circuits-neuromodulation-and-neural-engineering`) |
| Check a variant's frequency | ⚠️ **gnomAD, always first** (§18) |

### 19.3 Interpretation checklist
- [ ] Is this "silent" variant actually affecting splicing or translation? (§1.1 → `neurogen-molecular-genetics-and-regulation`)
- [ ] Where is the premature stop relative to the last junction? (NMD) (§1.2 → `neurogen-molecular-genetics-and-regulation`)
- [ ] Assigned the GWAS hit by proximity, or by functional evidence? (§2.1 → `neurogen-molecular-genetics-and-regulation`, §4.3 → `neurogen-population-genetics-and-genome-engineering`)
- [ ] Is penetrance from families (biased) or population data? (§3.2 → `neurogen-molecular-genetics-and-regulation`)
- [ ] Corrected for population stratification? (§4.3 → `neurogen-population-genetics-and-genome-engineering`)
- [ ] Is the PRS being applied outside its discovery ancestry? (§4.3 → `neurogen-population-genetics-and-genome-engineering`)
- [ ] Is heritability being read as an individual property? (§4.1 → `neurogen-population-genetics-and-genome-engineering`)
- [ ] LoF or GoF — does the therapy strategy match? (§3.1 → `neurogen-molecular-genetics-and-regulation`)
- [ ] Is HDR being assumed in post-mitotic tissue? (§5.1 → `neurogen-population-genetics-and-genome-engineering`)
- [ ] Checked on-target structural outcomes, not just off-targets? (§5.1 → `neurogen-population-genetics-and-genome-engineering`)
- [ ] Bystander edits inside the base-editing window? (§5.1 → `neurogen-population-genetics-and-genome-engineering`)
- [ ] Screen library coverage ≥500–1000×? (§6.2 → `neurogen-population-genetics-and-genome-engineering`)
- [ ] Is the optogenetic manipulation physiologically plausible? (§13 → `neurogen-circuits-neuromodulation-and-neural-engineering`)
- [ ] DREADD experiment run with a DREADD-free CNO control? (§13 → `neurogen-circuits-neuromodulation-and-neural-engineering`)
- [ ] Are calcium transients being read as spike counts? (§13 → `neurogen-circuits-neuromodulation-and-neural-engineering`)

---

## §20. Method

**§1–§16 → `neurogen-molecular-genetics-and-regulation`, `neurogen-population-genetics-and-genome-engineering`, `neurogen-neuron-biophysics-plasticity-and-coding`, `neurogen-circuits-neuromodulation-and-neural-engineering` and §19 are settled science**, resting on the standard texts in §18 — **Alberts,
Kandel, Falconer & Mackay, Hartl & Clark, Dayan & Abbott, Gerstner** — and on foundational
primary results (**Hodgkin & Huxley 1952, Hardy & Weinberg 1908, Bliss & Lømo 1973,
Schultz 1997, Jinek/Doudna & Charpentier 2012, Komor 2016, Anzalone 2019**). **None of it
was web-verified; the textbooks are the authority and the mechanisms have been stable for
years to decades.**

**Scoped to complement** a biomedical-engineering reference, which holds bioinformatics
pipelines, structural biology, physiological modelling, and neural-interface hardware.

**Two searches were run in August 2026**, confined to §17 — therapeutic genome editing and
connectomics — where capability genuinely changed.

**Sources for §17**: the **Innovative Genomics Institute's** 2025 and 2026 clinical trial
updates and the **NEJM**-reported KJ case for in vivo CRISPR; **CRISPR Medicine News** for
the PM359 prime editing data; trial trackers for NTLA-2001 and pipeline breadth;
**Nature Methods'** Method of the Year 2025 editorial, the **Nature** FlyWire and MICrONS
papers, and Princeton/MIT institutional reporting for §17.2's figures.

**Confidence.** **High** throughout §1–§16 → `neurogen-molecular-genetics-and-regulation`, `neurogen-population-genetics-and-genome-engineering`, `neurogen-neuron-biophysics-plasticity-and-coding`, `neurogen-circuits-neuromodulation-and-neural-engineering` — established mechanism, with numbers stated as
representative ranges rather than constants. **High** on §17.2's connectomics figures,
which come from the primary *Nature* papers and are consistent across sources.

⚠️ **Two explicit cautions.** **§17.1 contains an unresolved source conflict**, flagged in
place: one source lists EDIT-101 as approved alongside Casgevy while others describe
Casgevy as the sole approval. **I have not resolved it and have said so rather than
picking.** And ⚠️ **clinical trial results in §17.1 are single-arm early-phase data,
frequently from company announcements rather than peer-reviewed publication** — the PM359
figures in particular are from one patient. **Early-phase results routinely fail to
replicate at scale; read them as demonstrations of mechanism, not efficacy.**

**§15's contested entries** — predictive coding, serotonin function, DBS mechanism,
transgenerational epigenetic inheritance in mammals — **are areas where competent
researchers disagree**, and I have marked them rather than adjudicating.
