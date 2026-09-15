---
name: drugdev-pipeline-engineering-compute-and-regulated-software
description: "Use for the engineering and compliance layer: pipeline engineering and workflow orchestration for computational chemistry, compute including GPU and cluster economics, reproducibility with environment and data versioning, and the regulated context — GxP, computer system validation, the FDA credibility framework and what counts as software as a medical device."
---

# Drug Discovery Software: Pipeline Engineering, Compute, Reproducibility, GxP and Validation, and Software as a Medical Device

> **Part 5 of 6** of the *Medicine Design Software Development* reference (plugin `medicine-design-software-development`), covering §19–§23. Sibling skills: `drugdev-pipeline-targets-and-drug-likeness` (§0–§3), `drugdev-representation-cheminformatics-data-quality-and-leakage` (§4–§7), `drugdev-protein-structure-docking-and-molecular-dynamics` (§8–§12), `drugdev-qsar-admet-generative-models-and-validation` (§13–§18), `drugdev-reference` (§24–§29). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §19. Pipeline Engineering

**⚠️ Workflow orchestration**: **Nextflow and Snakemake (⚠️ the bioinformatics standards,
container-friendly and resumable), Airflow/Prefect/Dagster (⚠️ general-purpose, better for
scheduled production work), and ⚠️ the practical requirement that long-running scientific
jobs must be RESUMABLE — a 200-hour simulation that fails at hour 190 must not restart.**
**⚠️ Data engineering specifics**: **⚠️ chemical databases need structure search (RDKit's
PostgreSQL cartridge, or a dedicated chemical database), ⚠️ InChIKey as the join key
(§4 → `drugdev-representation-cheminformatics-data-quality-and-leakage`), and provenance tracking on every derived value.**
**⚠️ The architectural pattern that works**: ⚠️ **separate the SCIENCE (a pure function
from molecule to prediction) from the ORCHESTRATION and the STORAGE** — **because the
science changes fast, the models get retrained constantly, and mixing them makes both
untestable.**
**⚠️ Model registry and versioning is not optional** ⚠️ **when a number may end up in a
regulatory submission** (§22): **you must be able to say which model version, trained on
which data, produced a given prediction on a given date.**

---

## §20. Compute

**⚠️ The workloads are heterogeneous and sizing them wrong is expensive:**
```
⚠️ EMBARRASSINGLY PARALLEL  docking, descriptor calculation, virtual
   screening. ⚠️ Scale horizontally; cheap; spot instances are ideal
⚠️ GPU-BOUND  MD, deep learning, ⚠️ free energy (§12)
⚠️ LONG-RUNNING  MD trajectories — ⚠️ checkpointing is mandatory
⚠️ MEMORY-BOUND  large structure and trajectory analysis
```
**⚠️ Storage is the underestimated cost**: ⚠️ **MD trajectories are enormous, and the
policy question — what to keep, at what frame rate, for how long — should be decided
before you generate terabytes.**
**⚠️ Licensing** is a real architectural constraint in this field: ⚠️ **several key
commercial tools are node- or token-licensed, which limits how you can scale.**

---

## §21. Reproducibility

**⚠️ Higher stakes than usual, because results may support regulatory decisions** (§22).
**⚠️ The specific hazards here**: ⚠️ **RDKit version changes altering descriptors (§5 → `drugdev-representation-cheminformatics-data-quality-and-leakage`);
force field version differences (§11 → `drugdev-protein-structure-docking-and-molecular-dynamics`); MD being non-deterministic by nature (⚠️ so
reproducibility means the ENSEMBLE and the seed and the exact configuration, not identical
trajectories); GPU non-determinism in deep learning; and ⚠️ random seeds in splitting,
which is where §7 → `drugdev-representation-cheminformatics-data-quality-and-leakage`'s leakage often hides.**
**⚠️ The practices**: **containers with pinned versions, environment lock files, ⚠️ data
versioning (DVC or equivalent), experiment tracking, and ⚠️ recording the exact input
structures and standardization pipeline used** — **not just "from ChEMBL."**

---

## §22. ⚠️ GxP, Validation and the Regulated Context

> **⚠️ The mindset shift that catches software engineers: in a GxP environment, if it
> isn't documented, it didn't happen.**
```
⚠️ GxP  GLP (lab), GCP (clinical), GMP (manufacturing).
   ⚠️ Discovery research is usually NOT GxP; ⚠️ the moment output
   supports a regulatory submission, everything changes
⚠️ CSV / CSA  Computer System Validation — ⚠️ and FDA's Computer
   Software Assurance guidance deliberately shifts effort from
   exhaustive documentation toward RISK-BASED critical thinking
   and more actual testing
⚠️ GAMP 5 (2nd ed.)  the industry framework; ⚠️ software categories
   by risk; ⚠️ explicitly accommodates Agile and supplier leverage
⚠️ 21 CFR PART 11  electronic records and signatures. ⚠️ In practice:
   AUDIT TRAILS (who changed what, when, why — and they must not be
   disableable), access control, ⚠️ DATA INTEGRITY
⚠️ ALCOA+  Attributable, Legible, Contemporaneous, Original, Accurate
   (+ Complete, Consistent, Enduring, Available). ⚠️ The data
   integrity standard, and a genuinely good checklist for ANY
   scientific data system
```
**⚠️ What this means for how you build**: ⚠️ **requirements traceability from user
requirement through design to test; ⚠️ change control; ⚠️ IQ/OQ/PQ qualification;
periodic review; and supplier assessment for anything you didn't write.**
**⚠️ The honest engineering advice**: ⚠️ **decide EARLY whether a system will ever be GxP,
because retrofitting audit trails and traceability onto a research codebase is far more
expensive than building them in.** **⚠️ And keep the GxP boundary as small as you can —
validate the system that produces the submitted number, not the entire research
platform.**

---

## §23. Software as a Medical Device

**⚠️ A different regime from drug development software, and worth distinguishing.**
⚠️ **SaMD is software with a medical purpose that is itself a device — diagnostic
algorithms, clinical decision support above a threshold.** **⚠️ IEC 62304 governs the
software lifecycle; ISO 14971 governs risk management; the EU MDR/IVDR applies in
Europe.**
**⚠️ The adaptive AI problem**: ⚠️ **a model that keeps learning after clearance breaks
the traditional "locked device" assumption** — **which is why Predetermined Change Control
Plans exist, specifying in advance what changes are permitted without a new submission.**
**⚠️ Note this is a separate track from §24.2 → `drugdev-reference`'s drug-development framework**, ⚠️ **though
the credibility concepts are explicitly borrowed from the medical device computational
modelling guidance.**
