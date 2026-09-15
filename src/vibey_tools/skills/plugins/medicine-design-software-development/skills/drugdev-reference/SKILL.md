---
name: drugdev-reference
description: "Use when correcting a drug discovery software misconception, looking up an attrition rate, dataset size, accuracy or timeline figure, finding the tools and resources, or needing a quick-reference picker — plus the current state of AI drug discovery clinical evidence and the FDA and EMA regulatory framework for AI. Companion to the other drug discovery software skills."
---

# Drug Discovery Software: What's Live, Misconceptions, Numbers, and Tools

> **Part 6 of 6** of the *Medicine Design Software Development* reference (plugin `medicine-design-software-development`), covering §24–§29. Sibling skills: `drugdev-pipeline-targets-and-drug-likeness` (§0–§3), `drugdev-representation-cheminformatics-data-quality-and-leakage` (§4–§7), `drugdev-protein-structure-docking-and-molecular-dynamics` (§8–§12), `drugdev-qsar-admet-generative-models-and-validation` (§13–§18), `drugdev-pipeline-engineering-compute-and-regulated-software` (§19–§23). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The chemistry and physics are stable. Two areas moved. See §24 for the AI drug discovery clinical evidence, and the FDA and EMA regulatory framework for AI.

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
> 1. **⚠️ The bottleneck is BIOLOGY, not compute** (§1 → `drugdev-pipeline-targets-and-drug-likeness`, §24.1). **Roughly 90% of candidates
>    entering clinical trials fail, mostly for efficacy and toxicity reasons that appear
>    only in humans — and no amount of upstream modelling has yet moved that number.**
> 2. **⚠️ Random train/test splits are almost always WRONG here** (§7 → `drugdev-representation-cheminformatics-data-quality-and-leakage`). **Chemical data is
>    clustered into analogue series, so random splitting tests interpolation within a
>    series and reports it as generalization. This is the field's defining methodological
>    failure.**
> 3. **⚠️ Prediction is cheap; VALIDATION is the product** (§18 → `drugdev-qsar-admet-generative-models-and-validation`, §24.2). **In a regulated
>    context, an unvalidated model is not evidence — the FDA framework is explicitly about
>    credibility for a stated context of use, not about accuracy in the abstract.**

---

## §24. What's Live — verified August 2026

### 24.1 ⚠️ AI drug discovery meets clinical reality
**⚠️ 2026 is the year the evidence starts arriving, and the honest position is "promising
early, unproven where it counts."**

- **⚠️ The scale of the bet**: **reported ~$60B invested in the sector since 2019 (with
  broader life-science AI investment cited above $100B), ⚠️ around 173–175 AI-originated
  drug programmes have entered human trials, and ⚠️ NONE has yet received FDA approval.**
  ⚠️ **Industry estimates suggest 15–20 of those programmes could enter pivotal Phase III
  trials during 2026.**
- **⚠️ The encouraging number**: **published analyses report ⚠️ 80–90% Phase 1 success for
  AI-discovered molecules, against a historical industry average variously cited at
  ~40–65% or ~52%.** ⚠️ **Phase 2 success is reported around 40% — "based on a limited
  sample and broadly comparable to historical industry performance."**
- **⚠️ Timelines do appear compressed**: **reported candidates reaching human trials in
  under 18 months, versus a typical multi-year discovery phase.**

> **⚠️ GOTCHA — the selection-bias objection is strong and should be stated before the
> optimistic reading.** ⚠️ **The sample sizes are small and likely skewed, and early AI
> programmes may simply have selected EASIER TARGETS** — **a pattern one analysis notes
> is familiar from early monoclonal antibody development, "when initial success rates
> reflected careful target selection rather than technological superiority."**
> ⚠️ **The open question is whether the early-stage advantage COMPOUNDS or merely
> FRONT-LOADS the same attrition.** **⚠️ Phase 1 tests safety in healthy volunteers;
> good molecular design plausibly helps there. Phase 2 tests whether the biology was
> right, and design quality helps far less.**
> **⚠️ As one summary put it: biology does not care how cleverly you found your molecule.**

**⚠️ The current consensus position, stated carefully**: ⚠️ **"the evidence does not yet
show that AI materially changes the probability of surviving Phase 2 and Phase 3 testing."**
⚠️ **Clinical attrition remains around 90%, and Derek Lowe's observation is quoted across
sources — most failures still result from efficacy or safety issues that emerge only in
humans** (§1 → `drugdev-pipeline-targets-and-drug-likeness`). ⚠️ **A plausible outcome flagged by commentators is "accelerated timelines
without improved efficacy — commercially valuable but scientifically underwhelming."**
**⚠️ Sourcing caution: much of the enthusiastic coverage comes from vendors, consultancies
and AI-in-pharma trade outlets; the peer-reviewed narrative reviews are notably more
measured, and I've weighted toward those.**

### 24.2 ⚠️ The regulatory framework for AI arrived
**⚠️ This is the section that changes how you should BUILD, not just what you should
believe.**

- **⚠️ FDA published draft guidance on 6 January 2025** — ***Considerations for the Use of
  Artificial Intelligence To Support Regulatory Decision-Making for Drug and Biological
  Products*** — **establishing ⚠️ a risk-based CREDIBILITY ASSESSMENT FRAMEWORK.**
  ⚠️ **The comment period closed 7 April 2025 (reported extended), and final guidance is
  reported as expected in Q2 2026.**
- **⚠️ The central concept is CONTEXT OF USE (COU)**: ⚠️ **credibility is defined as
  "trust in the performance of an AI model for a particular context of use."** **⚠️ There
  is no such thing as a validated model in the abstract — only a model credible for a
  stated role in a stated decision.**
- **⚠️ The 7-step framework**, **as reported across sources:**
```
⚠️ 1. Define the QUESTION OF INTEREST — the specific regulatory question
⚠️ 2. Define the CONTEXT OF USE — the model's precise role and how its
      outputs influence decisions
⚠️ 3. Assess MODEL RISK — ⚠️ from MODEL INFLUENCE × DECISION CONSEQUENCE
      (a risk matrix; risk rises as either increases)
   4. Develop a CREDIBILITY ASSESSMENT PLAN proportionate to that risk
   5. Execute the plan
   6. Document results in a CREDIBILITY ASSESSMENT REPORT
⚠️ 7. Determine ADEQUACY for the context of use
```
- **⚠️ The critical scoping distinction for discovery teams**: ⚠️ **if AI is used to
  DISCOVER a drug but traditional validation confirms safety and efficacy, extensive AI
  documentation may not be required** — **the guidance targets AI that DIRECTLY SUPPORTS
  REGULATORY DECISION-MAKING.** **⚠️ So a generative model that proposed a molecule later
  validated conventionally is in a very different position from a model whose output
  substitutes for an experiment.**
- **⚠️ International alignment moved**: ⚠️ **on 14 January 2026 the FDA and EMA jointly
  published *Guiding Principles of Good Machine Learning Practice for Drug Development* —
  reported as ten high-level principles complementing the credibility framework.**
  **EMA's September 2024 Reflection Paper on AI in medicines runs in parallel.**
  ⚠️ **FDA also announced an AI-Enabled Optimization of Early-Phase Clinical Trials pilot,
  with an RFI published 29 April 2026.**

> **⚠️ GOTCHA — the engineering implications are concrete and they land on §19 → `drugdev-pipeline-engineering-compute-and-regulated-software`, §21 → `drugdev-pipeline-engineering-compute-and-regulated-software` and
> §22 → `drugdev-pipeline-engineering-compute-and-regulated-software`.** ⚠️ **A credibility assessment plan must describe model design, DATA STRATEGY,
> training methodology, performance metrics and evaluation methodology — and be
> submitted early, within a submission or on request during inspection.**
> **⚠️ That means: data provenance and versioning are regulatory artefacts, not
> engineering hygiene; ⚠️ the split strategy (§7 → `drugdev-representation-cheminformatics-data-quality-and-leakage`) is a documented decision you must
> defend; ⚠️ model versioning and the ability to reproduce a specific historical
> prediction are requirements; and ⚠️ "we retrained it and it's better now" is a change
> control event.**
> **⚠️ Sponsors are also expected to define a threshold or risk matrix for when a
> technology counts as AI under FDA's definition versus a complex decision tree —
> which is a governance question most teams have not answered.**

**⚠️ The honest caveat on all of this**: ⚠️ **the draft is a draft, a critical peer-reviewed
review of it exists in the literature, and the US policy environment around AI shifted
with the January 2025 executive order — so implementation detail is genuinely in motion.**
**⚠️ The DIRECTION, however, is stable and internationally converging: risk-proportionate,
context-of-use-anchored, documentation-heavy.** **⚠️ Build for that.**

---

## §25. Misconceptions

| Misconception | Correction |
|---|---|
| AI will collapse drug development timelines | ⚠️ **Early-stage yes; clinical attrition unchanged** (§1 → `drugdev-pipeline-targets-and-drug-likeness`, §24.1) |
| The bottleneck is compute | ⚠️ **It's biology and target validation** (§1 → `drugdev-pipeline-targets-and-drug-likeness`) |
| Random train/test split is standard practice | ⚠️ **It leaks badly here. Scaffold or time split** (§7 → `drugdev-representation-cheminformatics-data-quality-and-leakage`) |
| High test R² means the model works | ⚠️ **Check the split, then the noise floor** (§6 → `drugdev-representation-cheminformatics-data-quality-and-leakage`, §7 → `drugdev-representation-cheminformatics-data-quality-and-leakage`) |
| The same molecule has one SMILES | ⚠️ **Canonicalize, or you'll duplicate everything** (§4 → `drugdev-representation-cheminformatics-data-quality-and-leakage`) |
| Lipinski's rules define drug-likeness | ⚠️ **A retrospective observation, not a filter** (§3 → `drugdev-pipeline-targets-and-drug-likeness`) |
| Public bioactivity data is precise | ⚠️ **~1 order of magnitude between labs is common** (§6 → `drugdev-representation-cheminformatics-data-quality-and-leakage`) |
| AlphaFold solved structure for drug design | ⚠️ **Apo-like; docking into it underperforms** (§9 → `drugdev-protein-structure-docking-and-molecular-dynamics`) |
| pLDDT is an accuracy guarantee | ⚠️ **A confidence score; low regions may be disordered** (§9 → `drugdev-protein-structure-docking-and-molecular-dynamics`) |
| Docking scores predict affinity | ⚠️ **Poses reasonable, scoring poor. Triage only** (§10 → `drugdev-protein-structure-docking-and-molecular-dynamics`) |
| Better docking software fixes scoring | ⚠️ **Protein prep matters more than program choice** (§10 → `drugdev-protein-structure-docking-and-molecular-dynamics`) |
| MD tells you what the protein does | ⚠️ **Microseconds vs milliseconds of real biology** (§11 → `drugdev-protein-structure-docking-and-molecular-dynamics`) |
| MM/GBSA is a cheap FEP | ⚠️ **Much less reliable and widely over-trusted** (§12 → `drugdev-protein-structure-docking-and-molecular-dynamics`) |
| Deep learning beats classical QSAR | ⚠️ **RF on ECFP is often competitive. Run it** (§13 → `drugdev-qsar-admet-generative-models-and-validation`, §17 → `drugdev-qsar-admet-generative-models-and-validation`) |
| Similar structure means similar activity | ⚠️ **Activity cliffs, and they're the interesting cases** (§13 → `drugdev-qsar-admet-generative-models-and-validation`) |
| Generating novel molecules is the hard part | ⚠️ **Scoring is. Generators hack the objective** (§15 → `drugdev-qsar-admet-generative-models-and-validation`) |
| Novelty metrics show a generative model works | ⚠️ **Nearly meaningless. Synthesizability matters** (§15 → `drugdev-qsar-admet-generative-models-and-validation`) |
| Benchmark SOTA transfers to practice | ⚠️ **Documented leakage in the standard benchmarks** (§17 → `drugdev-qsar-admet-generative-models-and-validation`) |
| Test-set accuracy is the goal | ⚠️ **Fewer DMTA cycles is the goal** (§16 → `drugdev-qsar-admet-generative-models-and-validation`) |
| Uncertainty estimation is optional | ⚠️ **It's what drives compound selection** (§16 → `drugdev-qsar-admet-generative-models-and-validation`) |
| Validation means a good validation set | ⚠️ **In GxP it means documented qualification** (§22 → `drugdev-pipeline-engineering-compute-and-regulated-software`) |
| Research code can be made GxP later | ⚠️ **Retrofitting traceability is far more expensive** (§22 → `drugdev-pipeline-engineering-compute-and-regulated-software`) |
| A model is validated or not | ⚠️ **Credible for a CONTEXT OF USE, or not** (§24.2) |
| AI-discovered drugs have been approved | ⚠️ **~173 in trials, zero approvals as of 2026** (§24.1) |
| 90% Phase 1 success proves AI works | ⚠️ **Small, likely skewed sample; easier targets** (§24.1) |

---

## §26. Numbers

```
⚠️ Timeline / cost      reported 10–15 yrs · >$1–2B per approved drug
⚠️ Clinical attrition   ⚠️ ~90% of entrants never approved
⚠️ Failure causes       reported ~40–50% efficacy · ~30% toxicity
⚠️ Funnel               >10,000 screened → 20–100 in Phase I → ~1 approved
⚠️ Experimental noise   ⚠️ ~0.5 log units on pIC50; ~1 order of magnitude
                        between labs — ⚠️ this is your accuracy ceiling
⚠️ FEP accuracy         reported ~1 kcal/mol (⚠️ ≈ 5× in affinity)
⚠️ AlphaFold            pLDDT >90 for well-determined regions
⚠️ AI programmes in trials  ⚠️ ~173–175 · ⚠️ ZERO approvals
⚠️ AI Phase 1 success   reported 80–90% (vs ~40–65% historical)
⚠️ AI Phase 2 success   ⚠️ reported ~40% — comparable to historical
⚠️ Sector investment    reported ~$60B since 2019
⚠️ FDA draft guidance   6 Jan 2025 · comments closed 7 Apr 2025 ·
                        ⚠️ final expected Q2 2026
⚠️ FDA–EMA principles   14 Jan 2026, reported 10 principles
```

---

## §27. Tools and Resources

| Tool / Source | Why |
|---|---|
| **RDKit** | ⚠️ **The foundation. Learn it first** (§5 → `drugdev-representation-cheminformatics-data-quality-and-leakage`) |
| **ChEMBL / PubChem / BindingDB** | §6 → `drugdev-representation-cheminformatics-data-quality-and-leakage`'s data, with §6 → `drugdev-representation-cheminformatics-data-quality-and-leakage`'s caveats |
| **Therapeutics Data Commons (TDC)** | ⚠️ **Benchmarks — read §17 → `drugdev-qsar-admet-generative-models-and-validation` before trusting them** |
| **AutoDock Vina / Smina** | Free docking (§10 → `drugdev-protein-structure-docking-and-molecular-dynamics`) |
| **OpenMM** | ⚠️ **The most programmable MD engine** (§11 → `drugdev-protein-structure-docking-and-molecular-dynamics`) |
| **AlphaFold DB / ESMFold** | §9 → `drugdev-protein-structure-docking-and-molecular-dynamics` |
| **DeepChem / chemprop** | ⚠️ **chemprop is the strong GNN baseline** (§13 → `drugdev-qsar-admet-generative-models-and-validation`) |
| **scikit-learn + ECFP** | ⚠️ **THE baseline you must beat** (§17 → `drugdev-qsar-admet-generative-models-and-validation`) |
| **Nextflow / Snakemake** | §19 → `drugdev-pipeline-engineering-compute-and-regulated-software` |
| **Leach, *Molecular Modelling*** | The standard textbook |
| **Gasteiger & Engel, *Chemoinformatics*** | §4–§5 → `drugdev-representation-cheminformatics-data-quality-and-leakage` foundations |
| **Derek Lowe, *In the Pipeline*** | ⚠️ **The best sceptical running commentary on this field** |
| **Pat Walters, *Practical Cheminformatics*** | ⚠️ **Excellent on §7 → `drugdev-representation-cheminformatics-data-quality-and-leakage` and §17 → `drugdev-qsar-admet-generative-models-and-validation`'s methodology traps** |
| **FDA draft guidance (Jan 2025)** | ⚠️ **§24.2, primary source. Read it directly** |
| **GAMP 5 (2nd ed.) / FDA CSA guidance** | §22 → `drugdev-pipeline-engineering-compute-and-regulated-software` |
| **IEC 62304 / ISO 14971** | §23 → `drugdev-pipeline-engineering-compute-and-regulated-software` |

---

## §28. Quick Reference

### 28.1 Picker
| Question | Where |
|---|---|
| My model has great metrics — is it real? | ⚠️ **Check the split first** (§7 → `drugdev-representation-cheminformatics-data-quality-and-leakage`) |
| What baseline should I beat? | ⚠️ **Random forest on ECFP4** (§13 → `drugdev-qsar-admet-generative-models-and-validation`, §17 → `drugdev-qsar-admet-generative-models-and-validation`) |
| How accurate can this model possibly be? | ⚠️ **The experimental noise floor** (§6 → `drugdev-representation-cheminformatics-data-quality-and-leakage`) |
| Should I use docking scores to rank? | ⚠️ **No. Triage only** (§10 → `drugdev-protein-structure-docking-and-molecular-dynamics`) |
| I need affinity predictions for a series | ⚠️ **FEP, with a good structure** (§12 → `drugdev-protein-structure-docking-and-molecular-dynamics`) |
| Can I dock into an AlphaFold model? | ⚠️ **You can; expect worse performance** (§9 → `drugdev-protein-structure-docking-and-molecular-dynamics`) |
| Generative model outputs look great | ⚠️ **Check synthesizability and objective hacking** (§15 → `drugdev-qsar-admet-generative-models-and-validation`) |
| Which compounds should we make next? | ⚠️ **Active learning with uncertainty** (§16 → `drugdev-qsar-admet-generative-models-and-validation`) |
| How do I join two chemical datasets? | ⚠️ **Standardize, then InChIKey** (§4 → `drugdev-representation-cheminformatics-data-quality-and-leakage`) |
| Model works in-house, fails on new chemistry | ⚠️ **Applicability domain** (§7 → `drugdev-representation-cheminformatics-data-quality-and-leakage`) |
| Will this need to be validated? | ⚠️ **Ask now, not later** (§22 → `drugdev-pipeline-engineering-compute-and-regulated-software`) |
| Does the FDA guidance apply to us? | ⚠️ **Depends on context of use** (§24.2) |

### 28.2 Before you trust a model
- [ ] ⚠️ **Split is scaffold-based or time-based, and justified** (§7 → `drugdev-representation-cheminformatics-data-quality-and-leakage`)
- [ ] ⚠️ **Duplicates removed after canonicalization** (§4 → `drugdev-representation-cheminformatics-data-quality-and-leakage`)
- [ ] Standardization done AFTER splitting, or identically to both (§7 → `drugdev-representation-cheminformatics-data-quality-and-leakage`)
- [ ] ⚠️ **Simple fingerprint baseline run and reported** (§17 → `drugdev-qsar-admet-generative-models-and-validation`)
- [ ] Performance compared against the experimental noise floor (§6 → `drugdev-representation-cheminformatics-data-quality-and-leakage`)
- [ ] ⚠️ **Applicability domain defined and enforced at inference** (§7 → `drugdev-representation-cheminformatics-data-quality-and-leakage`)
- [ ] Uncertainty estimates present and calibrated (§16 → `drugdev-qsar-admet-generative-models-and-validation`)
- [ ] ⚠️ **Activity cliff performance reported separately if relevant** (§13 → `drugdev-qsar-admet-generative-models-and-validation`)
- [ ] ⚠️ **Prospective test planned, and failures will be recorded** (§18 → `drugdev-qsar-admet-generative-models-and-validation`)
- [ ] Model version, data version and environment pinned (§21 → `drugdev-pipeline-engineering-compute-and-regulated-software`)

---

## §29. Method

**§1–§23 → `drugdev-pipeline-targets-and-drug-likeness`, `drugdev-representation-cheminformatics-data-quality-and-leakage`, `drugdev-protein-structure-docking-and-molecular-dynamics`, `drugdev-qsar-admet-generative-models-and-validation`, `drugdev-pipeline-engineering-compute-and-regulated-software` rests on established cheminformatics, structural biology, computational chemistry
and regulated-software practice** — **molecular representation, force fields and free
energy theory, QSAR methodology, and the GxP/GAMP/21 CFR Part 11 framework.** ⚠️ **The
split-leakage problem and the docking scoring limitation have both been documented
consistently for many years and needed no verification.**

**Two searches were run in August 2026**, on **AI drug discovery clinical evidence** and
**the FDA regulatory framework** — ⚠️ **the first because the field's central empirical
claim is now being tested, the second because it changes how these systems must be built.**

**Confidence.** **High** in §7 → `drugdev-representation-cheminformatics-data-quality-and-leakage` and §17 → `drugdev-qsar-admet-generative-models-and-validation`, which are the sections I'd most want read.
⚠️ **Random splitting on clustered chemical data is the field's defining methodological
failure, and the repeated independent finding that a random forest on ECFP fingerprints
matches elaborate architectures once splits are fixed is the single most useful sanity
check available.** **§6 → `drugdev-representation-cheminformatics-data-quality-and-leakage`'s noise-floor point is the companion: a model reporting error below
the experimental measurement error is fitting something other than chemistry.**

**High** in §10 → `drugdev-protein-structure-docking-and-molecular-dynamics`'s docking assessment and §12 → `drugdev-protein-structure-docking-and-molecular-dynamics`'s FEP framing — ⚠️ **both are long-standing,
well-characterized limitations that vendors consistently understate.**

**Moderate-to-high** on §24.1. ⚠️ **The structural facts — roughly 173–175 AI-originated
programmes in trials, zero approvals, ~90% overall clinical attrition — are consistent
across every source including the peer-reviewed reviews.** ⚠️ **The 80–90% Phase 1 figure
appears widely but rests on a small sample (one source traces it to 24 molecules through
December 2023), and the comparison baseline varies between sources (~40–65% vs ~52%),
which alone should induce caution.** **⚠️ I've given the selection-bias objection prominence
because it is the strongest argument in the debate and comes from the more sceptical
sources, and because the enthusiastic coverage is dominated by vendors and trade outlets
with obvious interests.** **⚠️ My own read is that the Phase 1 advantage is plausible on
mechanism — molecular design quality should help with safety in healthy volunteers — and
that Phase 2 is where the claim actually gets tested.**

**High** on §24.2's framework, which traces to FDA's own published guidance and is
corroborated by multiple independent law-firm and industry analyses. ⚠️ **The seven steps,
the context-of-use concept, the model-influence × decision-consequence risk matrix, and
the credibility assessment plan and report are all from primary or near-primary sources.**
⚠️ **The Q2 2026 finalization date and the January 2026 FDA–EMA joint principles are
reported rather than confirmed by me against a primary document, and the guidance remains
a DRAFT — so I'd verify current status before relying on specifics.** **⚠️ The engineering
implications I've drawn in the gotcha box are my inference from the documentation
requirements, not language quoted from the guidance.**
