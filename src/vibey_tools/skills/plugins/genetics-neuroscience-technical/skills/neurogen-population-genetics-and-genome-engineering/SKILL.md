---
name: neurogen-population-genetics-and-genome-engineering
description: "Use when working at population scale or editing genomes: heritability and why it is the most misused number in biology, evolutionary forces, GWAS and polygenic scores and what they do and do not support, the CRISPR toolbox and its mechanisms, classic and adjacent editing tools, and delivery as the actual bottleneck along with genetic screens and synthetic biology."
---

# Genetics and Neuroscience: Population Genetics, Genome Engineering, and Synthetic Biology

> **Part 2 of 5** of the *Genetics and Neuroscience* reference (plugin `genetics-neuroscience-technical`), covering §4–§6. Sibling skills: `neurogen-molecular-genetics-and-regulation` (§0–§3), `neurogen-neuron-biophysics-plasticity-and-coding` (§7–§9), `neurogen-circuits-neuromodulation-and-neural-engineering` (§10–§14), `neurogen-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    trait.** Almost every public misuse of the word stems from missing this (§4.1).
> 3. **⚠️ The brain's computational unit is the circuit, not the neuron.** Single-cell
>    biophysics is well understood; how populations implement computation is not (§9 → `neurogen-neuron-biophysics-plasticity-and-coding`, §17 → `neurogen-reference`).

---

## §4. Population and Quantitative Genetics

### 4.1 ⚠️ Heritability — the most misused number in biology

**Hardy–Weinberg**: `p² + 2pq + q² = 1` under random mating, no selection/drift/migration/
mutation. ⚠️ **Deviation is usually a genotyping artifact, and HWE testing is a standard
QC filter before it is ever a biological finding.**

**Variance decomposition**: `V_P = V_G + V_E + V_GxE`, with `V_G = V_A + V_D + V_I`.
```
Broad-sense  H² = V_G / V_P
Narrow-sense h² = V_A / V_P     ⚠️ additive only — this is what responds to selection
```

> **⚠️ GOTCHA — what heritability does NOT mean.**
> - **It is a property of a population in an environment**, not of a trait or a person.
>   ⚠️ **"h² = 0.8" says nothing about any individual.**
> - **It says nothing about malleability.** ⚠️ **Height is highly heritable and rose
>   dramatically with nutrition. Phenylketonuria is fully genetic and fully treated by
>   diet.**
> - **⚠️ High h² requires low environmental variance.** In a uniform environment,
>   heritability rises mechanically — because the denominator shrank, not because genes
>   matter more.
> - **⚠️ It says nothing about between-group differences.** Within-group heritability is
>   mathematically compatible with a purely environmental between-group gap — Lewontin's
>   seed-lot argument.

### 4.2 Evolutionary forces
**Selection**: `Δp ≈ spq/w̄` for weak selection. **Drift**: variance `pq/2N_e`, and
⚠️ **fixation probability of a new neutral allele is 1/2N — small populations lose
variation fast.** **Effective population size N_e** is usually much smaller than census
size. **Mutation-selection balance**: `q̂ ≈ √(µ/s)` for recessives, `q̂ ≈ µ/s` for
dominants.

**Linkage disequilibrium**: `D = p_AB − p_A p_B`, normalized as `D′` and `r²`.
⚠️ **LD decays with recombination and time: `D_t = D_0(1−c)^t`.** **This is the entire
basis of GWAS** — you genotype a tag SNP and detect an association driven by an
ungenotyped causal variant in LD with it, ⚠️ **which is why the lead SNP is usually not
causal.**

### 4.3 GWAS and polygenic scores

**Model**: `y = Xβ + ε` per variant, with **genome-wide significance at p < 5 × 10⁻⁸**
(⚠️ **Bonferroni for ~1 million independent tests**).

**⚠️ The technical requirements that make or break a GWAS:**
- **Population stratification** — ancestry correlates with both genotype and phenotype,
  producing spurious associations. **Correct with principal components or linear mixed
  models.** ⚠️ **Uncorrected stratification is the classic GWAS failure.**
- **Fine-mapping** — the lead SNP is in LD with dozens of others (§4.2).
  **Credible sets, not single variants.**
- **⚠️ Variant-to-gene assignment is genuinely hard.** Most hits are non-coding and
  regulatory; **the nearest gene is often wrong** (§2.1 → `neurogen-molecular-genetics-and-regulation`). Use eQTL colocalization,
  chromatin contact data, or functional follow-up.

**Polygenic scores**: `PRS_i = Σ_j β_j · G_ij`.
> **⚠️ GOTCHA — PRS portability across ancestries is poor, and the reason is structural.**
> Predictive accuracy **drops substantially in populations distant from the discovery
> cohort**, because LD patterns, allele frequencies, and effect sizes all differ. **Since
> discovery cohorts have been overwhelmingly European-ancestry, PRS work worst where they
> are most needed.** This is a property of the method plus the sampling, not a fixable
> analysis choice.

**Missing heritability** — GWAS-explained variance long fell short of twin-study `h²`.
⚠️ **Largely resolved by**: many variants of tiny effect below significance thresholds
(SNP-heritability from GREML/LDSC captures much more), rare variants not on arrays, and
⚠️ **upward bias in twin-study estimates from shared-environment and assortative-mating
assumptions.**

---

## §5. Genome Engineering

### 5.1 The CRISPR toolbox — mechanisms

**Cas9 (Type II)**: guide RNA (~20 nt spacer) + **PAM** (⚠️ **SpCas9 requires 5′-NGG-3′
immediately 3′ of the protospacer — the PAM is the targeting constraint, and it is why not
every site is editable**) → **blunt double-strand break ~3 bp upstream of PAM.**

**Repair determines outcome** — ⚠️ **this is the crux:**
```
NHEJ    error-prone, indels → ⚠️ frameshift KNOCKOUT. Active in all cell-cycle phases
MMEJ    microhomology-mediated, predictable deletions
HDR     precise KNOCK-IN — ⚠️ requires a donor template AND S/G2 phase,
        so it is inefficient and nearly absent in post-mitotic cells (neurons, muscle)
```
**⚠️ "CRISPR can rewrite any gene" collides with this**: knockout is easy, precise
correction by HDR is hard, and in non-dividing tissue it barely works.

**Cas12a (Cpf1)**: T-rich PAM, **staggered cut**, ⚠️ **processes its own crRNA array —
convenient for multiplexing.** **Cas13**: RNA-targeting, ⚠️ **edits the transcript, so the
effect is transient and the genome is untouched.**

**Base editing (Komor/Gaudelli)** — ⚠️ **no double-strand break:**
```
CBE:  cytosine deaminase + nCas9  → C•G → T•A
ABE:  evolved adenine deaminase + nCas9 → A•T → G•C
```
**⚠️ Editing window is ~4–8 nt within the protospacer**, which creates **bystander
edits** — other identical bases in the window are also changed. **Together CBE and ABE
cover the four transition mutations, but not transversions.**

**Prime editing (Anzalone)**: **nCas9 fused to reverse transcriptase**, guided by a
**pegRNA** that carries both the target and the desired edit as an RT template.
⚠️ **Can install all 12 base substitutions plus small insertions and deletions, without a
double-strand break or a donor template.** **The trade: lower efficiency and a much more
complex reagent to design.**

**CRISPRi/CRISPRa**: **catalytically dead dCas9** fused to KRAB (repress) or VP64/VPR
(activate). ⚠️ **No sequence change at all — a reversible, tunable perturbation, which
makes it the right tool for screens** (§6.2).

**⚠️ Specificity and safety concerns that are real:**
- **Off-target editing** at sites with mismatches. **Mitigate**: high-fidelity variants
  (eSpCas9, HiFi Cas9), truncated guides, RNP delivery (⚠️ **transient exposure — protein
  degrades, unlike plasmid**). **Measure**: GUIDE-seq, CIRCLE-seq, DISCOVER-seq.
- **⚠️ On-target structural consequences are the underrated risk**: large deletions,
  **chromothripsis**, and **loss of heterozygosity** following a double-strand break.
  **This is a major argument for base and prime editing.**
- **p53 activation** — cells with functional p53 respond to DSBs; ⚠️ **selecting for
  successfully edited cells can enrich for p53-deficient ones.**
- **Mosaicism** in embryo editing, and **pre-existing immunity** to Cas9 from
  *S. pyogenes* / *S. aureus* exposure.

### 5.2 Classic and adjacent tools
Restriction enzymes and cloning, **PCR** (⚠️ `2ⁿ` amplification; qPCR `C_t`), **Gibson
assembly**, **Golden Gate**, **ZFNs and TALENs** (⚠️ **protein-DNA recognition — harder to
retarget than CRISPR's RNA guide, which is the entire reason CRISPR won**),
**recombinases** (Cre-lox, Flp-FRT — ⚠️ **the basis of conditional knockouts**),
**RNAi** (transient knockdown, ⚠️ **off-target seed effects are pervasive**),
**transposons** (Sleeping Beauty, PiggyBac).

---

## §6. Delivery, Screens, Synthetic Biology

### 6.1 ⚠️ Delivery is the actual bottleneck

| Vector | Capacity | Notes |
|---|---|---|
| **AAV** | ⚠️ **~4.7 kb** | Non-integrating (mostly), long expression, serotype-dependent tropism. ⚠️ **SpCas9 alone is ~4.2 kb — barely fits, hence dual-vector and compact orthologs** |
| **Lentivirus** | ~8–10 kb | ⚠️ **Integrates — durable but insertional mutagenesis risk** |
| **Adenovirus** | ~30 kb | High immunogenicity |
| **LNP** | large | ⚠️ **Transient, re-dosable, liver-tropic by default. The workhorse for in vivo editing** |
| **Electroporation / RNP** | — | ⚠️ **Ex vivo standard — transient and highly specific** |

**⚠️ Tropism is the constraint that shapes the whole field**: LNPs go to liver
(ApoE-mediated LDLR uptake) unless engineered otherwise. **This is why liver diseases
dominated the in vivo editing pipeline** — not because they were most important, but
because they were reachable. **CNS, muscle and lung remain hard.**

**Immunogenicity**: pre-existing AAV neutralizing antibodies exclude a large fraction of
patients; ⚠️ **and AAV re-dosing is generally not possible.**

### 6.2 Screens
**Pooled CRISPR screens**: library of guides → select or sort → sequence guide abundance →
enrichment/depletion. **Readouts**: viability, reporter, FACS.
**⚠️ Perturb-seq / CROP-seq** couples perturbation with **single-cell transcriptomic
readout**, giving a rich phenotype per perturbation rather than a single number.
**⚠️ Design essentials**: 4–10 guides per gene, non-targeting and safe-harbour controls,
adequate library representation (⚠️ **≥500–1000× coverage; under-representation produces
noise that looks like hits**), and **MAGeCK or similar for analysis.**

### 6.3 Synthetic biology
**Parts** (promoters, RBS, terminators, CDS), **devices**, **systems**. **Standards**:
BioBricks, SBOL. **Circuits**: toggle switch (⚠️ **mutual repression → bistability**),
repressilator (⚠️ **three-node ring → oscillation**), logic gates, **feedback controllers**.
**⚠️ The recurring practical problems**: **burden** (circuits compete with host metabolism),
**evolutionary instability** (⚠️ **a costly circuit is selected against and breaks within
tens of generations**), **context dependence** (a part behaves differently in a new
construct), and **retroactivity** (downstream load changes upstream behaviour).
**Gene drives**: super-Mendelian inheritance via homing; ⚠️ **resistance alleles arise
readily through NHEJ repair at the cut site, which is the central technical obstacle.**
