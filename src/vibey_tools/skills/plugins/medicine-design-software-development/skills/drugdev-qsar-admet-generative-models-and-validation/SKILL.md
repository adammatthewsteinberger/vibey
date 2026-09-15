---
name: drugdev-qsar-admet-generative-models-and-validation
description: "Use for the machine learning layer: QSAR and property prediction, ADMET prediction and its applicability domain, generative models for molecule design and what they actually produce, active learning and the design-make-test-analyse loop, the benchmarks and why leaderboard performance transfers so poorly, and validation that means something — prospective tests, baselines and the checks that catch a leaking model."
---

# Drug Discovery Software: QSAR and Property Prediction, ADMET Prediction, Generative Models, Active Learning and the DMTA Loop, Benchmarks, and Validation That Means Something

> **Part 4 of 6** of the *Medicine Design Software Development* reference (plugin `medicine-design-software-development`), covering §13–§18. Sibling skills: `drugdev-pipeline-targets-and-drug-likeness` (§0–§3), `drugdev-representation-cheminformatics-data-quality-and-leakage` (§4–§7), `drugdev-protein-structure-docking-and-molecular-dynamics` (§8–§12), `drugdev-pipeline-engineering-compute-and-regulated-software` (§19–§23), `drugdev-reference` (§24–§29). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 3. **⚠️ Prediction is cheap; VALIDATION is the product** (§18, §24.2 → `drugdev-reference`). **In a regulated
>    context, an unvalidated model is not evidence — the FDA framework is explicitly about
>    credibility for a stated context of use, not about accuracy in the abstract.**

---

## §13. QSAR and Property Prediction

**⚠️ Predicting activity or a property from structure — the oldest ML application in the
field, dating to the 1960s.**
```
⚠️ CLASSICAL  descriptors/fingerprints + random forest, SVM or
   gradient boosting. ⚠️ STILL HIGHLY COMPETITIVE, and frequently
   beats deep learning on small datasets — which is most datasets here
⚠️ DEEP  GNNs (message passing on the molecular graph),
   transformers on SMILES, ⚠️ pretrained molecular foundation models
⚠️ MULTITASK  related endpoints trained together often help
```
> **⚠️ GOTCHA — ACTIVITY CLIFFS break the core assumption.** ⚠️ **QSAR assumes similar
> structures have similar activity; activity cliffs are pairs of near-identical molecules
> with order-of-magnitude activity differences, and they are exactly the cases medicinal
> chemists care about.** **⚠️ Models systematically fail on them, and aggregate metrics
> hide this because cliffs are a minority of pairs.**
> **⚠️ Report performance on cliff pairs separately if the model will be used for lead
> optimization.**

**⚠️ Honest expectations**: ⚠️ **on well-populated endpoints with good data, models are
useful triage tools.** **⚠️ They rarely replace an assay, and their value is in ORDERING
what to test next** (§16), **not in producing numbers to quote.**

---

## §14. ADMET Prediction

```
ABSORPTION  solubility, permeability (Caco-2, PAMPA), efflux (P-gp)
DISTRIBUTION  plasma protein binding, ⚠️ blood-brain barrier, volume
METABOLISM  ⚠️ CYP450 inhibition and substrate; metabolic stability;
   ⚠️ SITE OF METABOLISM prediction
EXCRETION  clearance, half-life
⚠️ TOXICITY  ⚠️ hERG (cardiac liability — the classic killer),
   hepatotoxicity, Ames mutagenicity, reactive metabolites
```
**⚠️ ADMET models are among the most USEFUL in practice** — ⚠️ **because the endpoints are
measured consistently in-house, the datasets are large, and early filtering has genuine
value.** **⚠️ hERG and CYP models in particular are standard.**
**⚠️ The caution**: ⚠️ **in vitro endpoints are proxies for in vivo behaviour, and in vivo
is a proxy for human.** **⚠️ Each step loses information, which is why physiologically-based
pharmacokinetic (PBPK) modelling exists to bridge them** — **and PBPK is itself an area
where regulators accept computational evidence** (§24.2 → `drugdev-reference`).

---

## §15. Generative Models

**⚠️ De novo design — proposing new molecules rather than filtering existing ones.**
```
APPROACHES  VAEs · GANs · autoregressive (SMILES/SELFIES) ·
   ⚠️ reinforcement learning against a scoring function ·
   ⚠️ diffusion models (increasingly, especially 3D structure-based)
⚠️ CONDITIONING  on a target pocket, on desired properties,
   scaffold-constrained, fragment growing/linking
```
> **⚠️ GOTCHA — generation is not the hard part; SCORING is.** ⚠️ **A generative model
> optimizes whatever objective you give it, and if that objective is a docking score
> (§10 → `drugdev-protein-structure-docking-and-molecular-dynamics`) or a QSAR model (§13), the generator will find that function's failure modes.**
> **⚠️ This is reward hacking with molecules — you get compounds that score brilliantly
> and are inactive, unstable or unmakeable.**
> **⚠️ Therefore: SYNTHESIZABILITY constraints (SA score, retrosynthesis-aware generation,
> or generating only from purchasable building blocks) are not a nicety.** ⚠️ **And
> "novelty" metrics are nearly meaningless — it is trivial to generate novel molecules and
> hard to generate novel USEFUL ones.**

**⚠️ Retrosynthesis prediction and computer-aided synthesis planning** (⚠️ **ASKCOS,
AiZynthFinder, commercial tools**) **close the loop, and ⚠️ they are the practical gate on
whether a designed molecule can actually be made.**

---

## §16. Active Learning and the DMTA Loop

**⚠️ The framing that makes ML in this domain make sense** (§1 → `drugdev-pipeline-targets-and-drug-likeness`): ⚠️ **you are not building a
model to be accurate; you are building a model to CHOOSE WHAT TO TEST NEXT.**
```
⚠️ The loop: model → select compounds → SYNTHESIZE AND ASSAY →
   retrain → repeat
⚠️ ACQUISITION  exploit (best predicted) vs explore (most uncertain) vs
   diverse batch selection. ⚠️ Batch selection matters because you make
   compounds in batches, not one at a time
⚠️ THEREFORE UNCERTAINTY QUANTIFICATION IS A FIRST-CLASS REQUIREMENT,
   not a nice-to-have. ⚠️ Ensembles, conformal prediction, Gaussian
   processes on fingerprints
⚠️ THE METRIC THAT MATTERS  ⚠️ how many DMTA cycles to reach the target
   profile — not test-set R²
```
**⚠️ Self-driving labs and closed-loop automation** connect this to robotic synthesis and
assay — ⚠️ **and the real bottleneck becomes assay throughput and reliability, not
prediction.**

---

## §17. ⚠️ Benchmarks

**⚠️ Common ones**: **MoleculeNet, Therapeutics Data Commons (TDC), DUD-E and LIT-PCBA
(virtual screening), CASF and PDBbind (scoring), GuacaMol and MOSES (generative), and
polaris-style curated benchmarks.**
> **⚠️ GOTCHA — most published benchmark improvements do not transfer, and there are
> documented structural reasons.** ⚠️ **MoleculeNet's random splits are known to inflate
> results (§7 → `drugdev-representation-cheminformatics-data-quality-and-leakage`); DUD-E's decoys are separable from actives by trivial properties, so models
> learn the decoy generation procedure; PDBbind has train-test protein overlap; and
> generative benchmarks reward distributional metrics that don't correspond to usefulness.**
> **⚠️ Independent reanalyses have repeatedly found that simple baselines — random forest
> on ECFP fingerprints — match or beat elaborate architectures once splits are fixed.**
> **⚠️ Always run that baseline. If your model doesn't beat it, you have learned something
> important.**

---

## §18. ⚠️ Validation That Means Something

```
⚠️ RETROSPECTIVE  time split (§7); ⚠️ external test set from a
   different lab; performance stratified by applicability domain
⚠️ PROSPECTIVE  ⚠️ THE ONLY REAL TEST — predict, then synthesize and
   assay, and report the outcome including failures
⚠️ THE COMPARISON THAT MATTERS  not "better than random" but
   ⚠️ "better than a medicinal chemist" or "better than the cheap baseline"
⚠️ CALIBRATION  are the confidence estimates honest? (§16)
⚠️ ERROR ANALYSIS  where does it fail, and is that a systematic class?
```
**⚠️ The publication asymmetry to be aware of**: ⚠️ **prospective validations that failed
are rarely published, so the visible literature overstates the field.** ⚠️ **This is the
same problem as §24.1 → `drugdev-reference` at a smaller scale.**

---

# PART V — ENGINEERING
