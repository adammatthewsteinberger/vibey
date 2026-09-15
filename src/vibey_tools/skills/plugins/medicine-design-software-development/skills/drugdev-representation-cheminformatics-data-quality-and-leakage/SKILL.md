---
name: drugdev-representation-cheminformatics-data-quality-and-leakage
description: "Use when building the data layer: molecular representation including SMILES, InChI, fingerprints and graphs and where each loses information, the cheminformatics toolkits, the public and commercial data sources and the quality problems they carry, and splitting and leakage — scaffold splits, temporal splits and the analogue-series leakage that inflates almost every reported benchmark result."
---

# Drug Discovery Software: Molecular Representation, Cheminformatics Toolkits, Data Sources and Their Quality, and Splitting and Leakage

> **Part 2 of 6** of the *Medicine Design Software Development* reference (plugin `medicine-design-software-development`), covering §4–§7. Sibling skills: `drugdev-pipeline-targets-and-drug-likeness` (§0–§3), `drugdev-protein-structure-docking-and-molecular-dynamics` (§8–§12), `drugdev-qsar-admet-generative-models-and-validation` (§13–§18), `drugdev-pipeline-engineering-compute-and-regulated-software` (§19–§23), `drugdev-reference` (§24–§29). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The chemistry and physics are stable. Two areas moved. See §24 → `drugdev-reference` for the AI drug discovery clinical evidence, and the FDA and EMA regulatory framework for AI.

> **⚠️ Written for software engineers entering computational drug discovery — a domain
> where the code is easy and the EVALUATION is brutally hard.** ⚠️ **You can build a
> molecular property predictor in an afternoon and get a beautiful R². It will very
> probably be measuring leakage, not chemistry** (§7).
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
> 2. **⚠️ Random train/test splits are almost always WRONG here** (§7). **Chemical data is
>    clustered into analogue series, so random splitting tests interpolation within a
>    series and reports it as generalization. This is the field's defining methodological
>    failure.**
> 3. **⚠️ Prediction is cheap; VALIDATION is the product** (§18 → `drugdev-qsar-admet-generative-models-and-validation`, §24.2 → `drugdev-reference`). **In a regulated
>    context, an unvalidated model is not evidence — the FDA framework is explicitly about
>    credibility for a stated context of use, not about accuracy in the abstract.**

---

## §4. Molecular Representation

```
⚠️ SMILES  text. ⚠️ NON-CANONICAL by default — the same molecule has many
   valid strings, so ALWAYS canonicalize before deduplicating or joining
⚠️ InChI / InChIKey  ⚠️ canonical by construction; the right key for
   database joins. ⚠️ Note tautomer and stereochemistry layer subtleties
SELFIES  ⚠️ every string is a VALID molecule — useful for generative
   models because it removes invalid-output failure modes (§15)
⚠️ MOLECULAR GRAPHS  atoms as nodes, bonds as edges. ⚠️ The natural
   representation, and what GNNs consume
FINGERPRINTS  ⚠️ ECFP/Morgan (circular, the workhorse), MACCS,
   RDKit, Avalon. ⚠️ Fast, interpretable-ish, and still competitive
   with deep learning on many tasks (§13)
DESCRIPTORS  computed physicochemical properties (logP, TPSA, etc.)
3D CONFORMERS  ⚠️ molecules are FLEXIBLE — a single 3D structure is a
   choice, and conformer generation is its own problem
```
> **⚠️ GOTCHA — the representation problems that silently corrupt datasets:**
> ⚠️ **TAUTOMERS (the same compound written in different protomeric forms will not match),
> STEREOCHEMISTRY (frequently missing or wrong in public data, and enantiomers can differ
> by orders of magnitude in activity), SALTS AND SOLVATES (strip counterions), and
> PROTONATION STATE at physiological pH (which is often not what's in the file).**
> **⚠️ A standardization pipeline is not optional infrastructure — it is the first thing
> you build.**

---

## §5. Cheminformatics Toolkits

**⚠️ RDKit is the default and effectively the field's standard library** — **open source,
Python and C++, covering parsing, standardization, descriptors, fingerprints, substructure
search, conformer generation, reaction handling and visualization.**
**⚠️ Others**: **OpenBabel (format conversion), CDK (Java), ChemAxon and OpenEye
(commercial, strong in specific areas), Datamol (RDKit ergonomics).**
**⚠️ Substructure and similarity search**: ⚠️ **SMARTS for pattern matching; Tanimoto
similarity on fingerprints; ⚠️ and the crucial caveat that "similar" by Tanimoto does not
mean similar in activity** (§13 → `drugdev-qsar-admet-generative-models-and-validation`'s activity cliffs).
**⚠️ Practical engineering notes**: ⚠️ **RDKit is not thread-safe in all operations, mol
objects don't pickle trivially across versions, and ⚠️ RDKit version changes can alter
descriptor values — so pin the version and record it** (§21 → `drugdev-pipeline-engineering-compute-and-regulated-software`).

---

## §6. ⚠️ Data Sources and Their Quality

```
⚠️ ChEMBL   curated bioactivity from literature. ⚠️ THE main public
   resource, and ⚠️ its heterogeneity is the problem: assays differ
PubChem     enormous, ⚠️ much less curated
BindingDB   binding affinities · ⚠️ PDB / PDBbind for structures
DrugBank · ZINC / Enamine REAL (⚠️ purchasable and enumerated —
   billions of compounds) · ⚠️ Open Reaction Database · TDC benchmarks
⚠️ PROPRIETARY  internal pharma data is usually better-controlled and
   is why in-house models can outperform published ones
```
> **⚠️ GOTCHA — public bioactivity data is far noisier than its precision suggests.**
> ⚠️ **The same compound-target pair measured in different labs commonly differs by
> around an order of magnitude, and published experimental error on pIC50 is often
> estimated near 0.5 log units.** **⚠️ That sets a CEILING on achievable model accuracy
> that no architecture can exceed** — **a model reporting RMSE well below the
> experimental noise floor is fitting the noise, the assay, or the split** (§7).
> **⚠️ Also beware: activity data is heavily biased toward what was measured, censored
> values ("> 10 μM") are frequently mishandled, and ⚠️ inactives are massively
> under-reported because negative results aren't published.**

---

## §7. ⚠️ Splitting and Leakage

> **⚠️ THE defining methodological failure of ML in this field, and the reason so many
> published models don't work in practice.**
```
⚠️ THE PROBLEM  chemical datasets are ANALOGUE SERIES — dozens of close
   variants around a scaffold, from one medicinal chemistry campaign.
   ⚠️ A RANDOM SPLIT puts near-identical molecules in train AND test,
   so you measure interpolation within a series and call it generalization
⚠️ BETTER SPLITS
   ⚠️ SCAFFOLD SPLIT (Bemis-Murcko) — separates by core structure
   ⚠️ TIME SPLIT — train on what was known before date X, test after.
      ⚠️ The most realistic, because it mirrors actual prospective use
   ⚠️ CLUSTER SPLIT — cluster by similarity, hold out whole clusters
   ⚠️ For targets: hold out whole PROTEIN FAMILIES, not random pairs
⚠️ OTHER LEAKAGE ROUTES
   ⚠️ Duplicate compounds under different SMILES (§4)
   ⚠️ Standardizing or normalizing BEFORE splitting
   ⚠️ Test-set information in feature selection or hyperparameter choice
   ⚠️ Structure-based: the same PROTEIN in train and test with a
      different ligand
```
**⚠️ APPLICABILITY DOMAIN is the corollary and it belongs in the API**: ⚠️ **a model should
report whether a query is within the chemical space it was trained on**, **and a
confident prediction on an out-of-domain molecule is worse than no prediction.**
**⚠️ The honest test**: ⚠️ **can the model predict compounds made AFTER the training data
was assembled?** **Everything else is a proxy.**

---

# PART III — STRUCTURE-BASED METHODS
