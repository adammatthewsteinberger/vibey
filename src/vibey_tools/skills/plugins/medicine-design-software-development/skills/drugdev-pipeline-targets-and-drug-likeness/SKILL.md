---
name: drugdev-pipeline-targets-and-drug-likeness
description: "Use when orienting on a drug discovery project: the pipeline stage by stage with its attrition and where computation actually helps rather than where it is claimed to, targets and modalities from small molecules to biologics and their different constraints, and what makes a molecule a drug — potency, selectivity, exposure and the property filters worth taking seriously. Includes the router for the whole drug discovery software reference."
---

# Drug Discovery Software: The Pipeline and Where Software Helps, Targets and Modalities, and What Makes a Molecule a Drug

> **Part 1 of 6** of the *Medicine Design Software Development* reference (plugin `medicine-design-software-development`), covering §0–§3. Sibling skills: `drugdev-representation-cheminformatics-data-quality-and-leakage` (§4–§7), `drugdev-protein-structure-docking-and-molecular-dynamics` (§8–§12), `drugdev-qsar-admet-generative-models-and-validation` (§13–§18), `drugdev-pipeline-engineering-compute-and-regulated-software` (§19–§23), `drugdev-reference` (§24–§29). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The chemistry and physics are stable. Two areas moved. See §24 → `drugdev-reference` for the AI drug discovery clinical evidence, and the FDA and EMA regulatory framework for AI.

> **⚠️ Written for software engineers entering computational drug discovery — a domain
> where the code is easy and the EVALUATION is brutally hard.** ⚠️ **You can build a
> molecular property predictor in an afternoon and get a beautiful R². It will very
> probably be measuring leakage, not chemistry** (§7 → `drugdev-representation-cheminformatics-data-quality-and-leakage`).
>
> **Complements an AI/ML reference (model architectures), a healthcare/clinical reference
> (the trial end), and a scientific-computing reference (HPC and reproducibility).**
>
> **⚠️ GOTCHA** boxes mark the evaluation traps and the places where a correct-looking
> result is meaningless.
>
> **The three ideas that organize this document:**
> 1. **⚠️ The bottleneck is BIOLOGY, not compute** (§1, §24.1 → `drugdev-reference`). **Roughly 90% of candidates
>    entering clinical trials fail, mostly for efficacy and toxicity reasons that appear
>    only in humans — and no amount of upstream modelling has yet moved that number.**
> 2. **⚠️ Random train/test splits are almost always WRONG here** (§7 → `drugdev-representation-cheminformatics-data-quality-and-leakage`). **Chemical data is
>    clustered into analogue series, so random splitting tests interpolation within a
>    series and reports it as generalization. This is the field's defining methodological
>    failure.**
> 3. **⚠️ Prediction is cheap; VALIDATION is the product** (§18 → `drugdev-qsar-admet-generative-models-and-validation`, §24.2 → `drugdev-reference`). **In a regulated
>    context, an unvalidated model is not evidence — the FDA framework is explicitly about
>    credibility for a stated context of use, not about accuracy in the abstract.**

---

## §0. Routing

| You want... | Go to |
|---|---|
| **⚠️ The pipeline and the attrition** | **§1** |
| Targets and modalities | §2 |
| **⚠️ What makes a molecule a drug** | **§3** |
| **Molecular representation** | **§4 → `drugdev-representation-cheminformatics-data-quality-and-leakage`** |
| Cheminformatics toolkits | §5 → `drugdev-representation-cheminformatics-data-quality-and-leakage` |
| **⚠️ Data sources and quality** | **§6 → `drugdev-representation-cheminformatics-data-quality-and-leakage`** |
| **⚠️ Splitting and leakage** | **§7 → `drugdev-representation-cheminformatics-data-quality-and-leakage`** |
| Protein structure | §8 → `drugdev-protein-structure-docking-and-molecular-dynamics` |
| **⚠️ Structure prediction** | **§9 → `drugdev-protein-structure-docking-and-molecular-dynamics`** |
| **⚠️ Docking** | **§10 → `drugdev-protein-structure-docking-and-molecular-dynamics`** |
| Molecular dynamics | §11 → `drugdev-protein-structure-docking-and-molecular-dynamics` |
| Free energy methods | §12 → `drugdev-protein-structure-docking-and-molecular-dynamics` |
| QSAR and property prediction | §13 → `drugdev-qsar-admet-generative-models-and-validation` |
| ADMET | §14 → `drugdev-qsar-admet-generative-models-and-validation` |
| **Generative models** | **§15 → `drugdev-qsar-admet-generative-models-and-validation`** |
| Active learning and the DMTA loop | §16 → `drugdev-qsar-admet-generative-models-and-validation` |
| **⚠️ Benchmarks** | **§17 → `drugdev-qsar-admet-generative-models-and-validation`** |
| **⚠️ Validation that means something** | **§18 → `drugdev-qsar-admet-generative-models-and-validation`** |
| Pipeline engineering | §19 → `drugdev-pipeline-engineering-compute-and-regulated-software` |
| Compute | §20 → `drugdev-pipeline-engineering-compute-and-regulated-software` |
| Reproducibility | §21 → `drugdev-pipeline-engineering-compute-and-regulated-software` |
| **⚠️ GxP and validation** | **§22 → `drugdev-pipeline-engineering-compute-and-regulated-software`** |
| Software as a medical device | §23 → `drugdev-pipeline-engineering-compute-and-regulated-software` |
| **What's live** | **§24 → `drugdev-reference`** |
| Misconceptions, numbers | §25–§26 → `drugdev-reference` |
| Tools, quick ref, method | §27–§29 → `drugdev-reference` |

---

## §1. ⚠️ The Pipeline and Where Software Helps

```
TARGET ID → HIT FINDING → HIT-TO-LEAD → LEAD OPTIMIZATION →
PRECLINICAL → PHASE I → PHASE II → PHASE III → FILING
⚠️ Reported: 10–15 years and >$1–2B per approved drug
⚠️ Reported attrition: >10,000 compounds screened → ~1 approved
⚠️ ~90% of candidates entering clinical trials never gain approval
```
> **⚠️ GOTCHA — understand WHERE the failures happen or you will optimize the wrong
> thing.** ⚠️ **The dominant clinical failure modes are lack of EFFICACY (reported around
> 40–50%) and TOXICITY (reported around 30%)** — **and both are properties of the BIOLOGY
> and the human system, not of the molecule's binding affinity.**
> **⚠️ Computation is genuinely good at hit finding, property optimization and reducing
> cycle time in lead optimization. ⚠️ It is much weaker at predicting whether the TARGET
> was the right one — which is where most money is lost.**
> **⚠️ So a platform claim of the form "we designed a molecule 10× faster" is compatible
> with no improvement in the outcome that matters** (§24.1 → `drugdev-reference`).

**⚠️ The DMTA cycle** (**Design–Make–Test–Analyse**) **is the operating loop of lead
optimization, and ⚠️ the real objective of most discovery software is REDUCING THE NUMBER
OF CYCLES**, **not maximizing predictive accuracy in isolation** (§16 → `drugdev-qsar-admet-generative-models-and-validation`).

---

## §2. Targets and Modalities

**⚠️ Targets**: **enzymes (kinases, proteases), GPCRs, ion channels, nuclear receptors,
protein-protein interfaces (⚠️ historically "undruggable" — flat, large surfaces with no
pocket).**
**⚠️ Target validation is the highest-value and least computational step**: ⚠️ **genetic
evidence that modulating the target changes the disease is the strongest predictor of
clinical success, and human genetics-supported targets have a substantially better track
record.**
**⚠️ Modalities and their very different computational problems:**
```
SMALL MOLECULES  ⚠️ the classic cheminformatics domain (most of this doc)
BIOLOGICS  ⚠️ antibodies — sequence and structure problems, not SMILES
PROTACs / molecular glues  ⚠️ TERNARY complexes; conventional
   affinity-driven design does not apply
PEPTIDES · OLIGONUCLEOTIDES (ASO, siRNA) · ⚠️ mRNA and vaccines ·
CELL AND GENE THERAPY
```
**⚠️ Do not assume small-molecule tooling transfers** — ⚠️ **RDKit and docking are largely
irrelevant to antibody engineering, which is a sequence/structure problem with its own
stack.**

---

## §3. ⚠️ What Makes a Molecule a Drug

**⚠️ Potency is the easy part. Almost everything hard is about what the body does to the
molecule.**
```
⚠️ POTENCY  IC50, Ki, Kd, EC50 — ⚠️ note these are assay-dependent and
   NOT directly comparable across labs or formats (§6)
⚠️ SELECTIVITY  ⚠️ hitting the target and NOT the 500 similar proteins
⚠️ ADME  Absorption, Distribution, Metabolism, Excretion
⚠️ TOXICITY  ⚠️ hERG (cardiac), hepatotoxicity, genotoxicity, reactive
   metabolites
⚠️ DEVELOPABILITY  solubility, stability, synthesizability, cost,
   crystallinity, formulation
⚠️ LIGAND EFFICIENCY  LE = ΔG/heavy atoms; LLE = pIC50 − logP
   ⚠️ These exist because raw potency can be bought with lipophilicity,
   which then wrecks everything else
```
> **⚠️ GOTCHA — Lipinski's Rule of Five is widely misused as a filter, and Lipinski said
> otherwise.** ⚠️ **It was a retrospective ORAL BIOAVAILABILITY observation, explicitly not
> a design rule, and it does not apply to natural products, actively transported
> compounds, antibiotics, or beyond-Rule-of-5 space where important drugs live.**
> **⚠️ Hard-filtering a virtual library on Ro5 discards real chemistry.** **⚠️ Use it as a
> soft flag; the related PAINS filters deserve the same caution — they flag frequent
> hitters, and treating them as a validated exclusion list has been criticized in the
> literature.**

---

# PART II — REPRESENTATION AND DATA
