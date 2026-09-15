---
name: drugdev-protein-structure-docking-and-molecular-dynamics
description: "Use for structure-based work: protein structure and what a crystal structure does and does not tell you, structure prediction and how to read a confidence score, docking and the gap between pose prediction and affinity ranking, molecular dynamics with force fields and sampling limits, and free energy methods including FEP and where the accuracy actually is."
---

# Drug Discovery Software: Protein Structure, Structure Prediction, Docking, Molecular Dynamics, and Free Energy Methods

> **Part 3 of 6** of the *Medicine Design Software Development* reference (plugin `medicine-design-software-development`), covering §8–§12. Sibling skills: `drugdev-pipeline-targets-and-drug-likeness` (§0–§3), `drugdev-representation-cheminformatics-data-quality-and-leakage` (§4–§7), `drugdev-qsar-admet-generative-models-and-validation` (§13–§18), `drugdev-pipeline-engineering-compute-and-regulated-software` (§19–§23), `drugdev-reference` (§24–§29). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 1. **⚠️ The bottleneck is BIOLOGY, not compute** (§1 → `drugdev-pipeline-targets-and-drug-likeness`, §24.1 → `drugdev-reference`). **Roughly 90% of candidates
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

## §8. Protein Structure

**⚠️ Primary → secondary → tertiary → quaternary; ⚠️ the PDB as the experimental
repository (X-ray, cryo-EM, NMR).**
**⚠️ What a crystallographer knows and a software engineer often doesn't:**
⚠️ **RESOLUTION and B-factors indicate reliability — a 3.5 Å structure does not pin down
side chain positions; ⚠️ crystal structures are one conformational snapshot under
non-physiological conditions; ⚠️ hydrogens are usually absent; ⚠️ and missing loops are
common and are often the flexible functionally-important regions.**
**⚠️ Binding sites**: **orthosteric vs allosteric; ⚠️ cryptic pockets that only open in
certain conformations and are invisible in the apo structure; and ⚠️ INDUCED FIT — the
protein moves when the ligand binds, which most docking ignores** (§10).
**⚠️ Water is not a nuisance**: ⚠️ **structured waters mediate binding, and displacing a
water has a real free energy cost or gain.**

---

## §9. ⚠️ Structure Prediction

**⚠️ AlphaFold2 and successors were a genuine breakthrough** — ⚠️ **reported pLDDT above 90
for well-determined regions, and the AlphaFold DB made predicted structures available at
proteome scale.** **⚠️ AlphaFold3 and equivalents extend to complexes including
protein-ligand.**
> **⚠️ GOTCHA — "we solved protein structure" overstates it in ways that matter for drug
> design specifically.** ⚠️ **Predicted structures are typically APO-like and represent one
> conformation; docking into AlphaFold models has repeatedly been shown to perform WORSE
> than docking into experimental holo structures** — **because side chains in the pocket
> are not in their ligand-bound arrangement.**
> **⚠️ pLDDT is a CONFIDENCE score, not an accuracy guarantee, and low-pLDDT regions are
> frequently intrinsically disordered rather than merely uncertain.**
> **⚠️ Structure prediction did not solve binding affinity, conformational ensembles, or
> the effect of mutations on function.**

---

## §10. ⚠️ Docking

**⚠️ Predicts a binding POSE and scores it. Understand what each half can do.**
```
⚠️ POSE PREDICTION  ⚠️ reasonably good — often gets a near-native pose
   in the top ranks for well-behaved systems
⚠️ SCORING / AFFINITY RANKING  ⚠️ POOR. ⚠️ Docking scores correlate
   weakly with measured affinity, and this has been true for decades
   despite continuous effort
⚠️ THEREFORE  use docking to ENRICH and TRIAGE, never to rank a
   final series or to claim a predicted potency
```
**⚠️ Programs**: **AutoDock Vina (free, widely used), Glide, GOLD, rDock, DiffDock and
other ML pose predictors** (⚠️ **and note ML docking methods have been criticized for
benchmark leakage — the same protein appearing in train and test** — §7 → `drugdev-representation-cheminformatics-data-quality-and-leakage`).
**⚠️ Practical determinants of whether docking is useful at all**: ⚠️ **protein preparation
(protonation, tautomers, missing atoms) matters more than the choice of program; ⚠️ the
ligand's protonation state at pH 7.4; ⚠️ receptor flexibility (ensemble docking as a
partial answer); and ⚠️ a well-chosen box.**
**⚠️ Virtual screening realities**: ⚠️ **enrichment factors matter more than hit rate;
decoy selection biases benchmarks badly (DUD-E has known artefacts that let models learn
decoy properties rather than binding); and ⚠️ ultra-large library screening of billions of
compounds is now feasible and shifts the bottleneck to synthesis and assay throughput.**

---

## §11. Molecular Dynamics

**⚠️ Simulating atomic motion under a force field — the tool for questions docking can't
answer.**
**Force fields** (**AMBER, CHARMM, OPLS, and ⚠️ increasingly ML potentials**), **and
⚠️ the ligand parameterization problem: proteins are well-parameterized, arbitrary small
molecules are not, and bad ligand parameters invalidate the whole simulation.**
**⚠️ Engines**: **GROMACS, AMBER, OpenMM (⚠️ the most programmable), NAMD, Desmond.**
**⚠️ The timescale problem is the honest limitation**: ⚠️ **routine simulations reach
microseconds; many biologically relevant motions take milliseconds to seconds.**
**⚠️ Enhanced sampling (metadynamics, replica exchange, umbrella sampling) exists to
attack exactly this gap.**
**⚠️ What MD is genuinely good for**: **binding site flexibility and cryptic pockets,
water networks, stability of a docked pose, and generating ensembles for §10.**

---

## §12. Free Energy Methods

**⚠️ The most accurate physics-based affinity predictions available, and the most
expensive.**
```
⚠️ FEP / TI  alchemical transformation between two ligands.
   ⚠️ RELATIVE binding free energy is the practical workhorse —
   reported accuracy often around 1 kcal/mol for congeneric series
⚠️ ABFE  absolute binding free energy — harder, less reliable
MM/PBSA · MM/GBSA  ⚠️ cheaper, much less reliable, and widely
   over-trusted in the literature
```
**⚠️ Where FEP fits in practice**: ⚠️ **lead optimization within a congeneric series where
you already have a good structure** — **prioritizing which of 50 analogues to synthesize.**
**⚠️ It is not a screening tool and it does not rescue a wrong binding mode.**
**⚠️ 1 kcal/mol ≈ a factor of ~5 in affinity at room temperature** — ⚠️ **useful context for
what "accurate to 1 kcal/mol" actually buys you.**

---

# PART IV — MACHINE LEARNING
