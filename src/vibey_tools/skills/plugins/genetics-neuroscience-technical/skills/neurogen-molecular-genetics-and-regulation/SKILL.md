---
name: neurogen-molecular-genetics-and-regulation
description: "Use when working with genes and their expression: the central dogma stated accurately, transcription and splicing, translation and protein fate, cis-regulation, chromatin and epigenetic marks, non-coding RNA, and mutation, variant classes and their consequences together with the inheritance patterns. Includes the router for the whole genetics-neuroscience reference."
---

# Genetics and Neuroscience: Molecular Genetics, Gene Regulation, and Inheritance

> **Part 1 of 5** of the *Genetics and Neuroscience* reference (plugin `genetics-neuroscience-technical`), covering §0–§3. Sibling skills: `neurogen-population-genetics-and-genome-engineering` (§4–§6), `neurogen-neuron-biophysics-plasticity-and-coding` (§7–§9), `neurogen-circuits-neuromodulation-and-neural-engineering` (§10–§14), `neurogen-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    genes are expressed (§2).
> 2. **⚠️ Heritability is a population statistic, not a property of an individual or a
>    trait.** Almost every public misuse of the word stems from missing this (§4.1 → `neurogen-population-genetics-and-genome-engineering`).
> 3. **⚠️ The brain's computational unit is the circuit, not the neuron.** Single-cell
>    biophysics is well understood; how populations implement computation is not (§9 → `neurogen-neuron-biophysics-plasticity-and-coding`, §17 → `neurogen-reference`).

---

## §0. Routing

| You want... | Go to |
|---|---|
| **Central dogma and molecular mechanism** | **§1** |
| Gene regulation and epigenetics | §2 |
| Mutation, variation, inheritance | §3 |
| **Population and quantitative genetics** | **§4 → `neurogen-population-genetics-and-genome-engineering`** |
| **Genome engineering (CRISPR et al.)** | **§5 → `neurogen-population-genetics-and-genome-engineering`** |
| Delivery, screens, synthetic biology | §6 → `neurogen-population-genetics-and-genome-engineering` |
| Neuron biophysics and synapses | §7 → `neurogen-neuron-biophysics-plasticity-and-coding` |
| **Plasticity rules** | **§8 → `neurogen-neuron-biophysics-plasticity-and-coding`** |
| Neural coding | §9 → `neurogen-neuron-biophysics-plasticity-and-coding` |
| Circuit architectures | §10 → `neurogen-circuits-neuromodulation-and-neural-engineering` |
| Neuromodulation | §11 → `neurogen-circuits-neuromodulation-and-neural-engineering` |
| Development and glia | §12 → `neurogen-circuits-neuromodulation-and-neural-engineering` |
| **Neural engineering methods** | **§13 → `neurogen-circuits-neuromodulation-and-neural-engineering`** |
| Stimulation and intervention | §14 → `neurogen-circuits-neuromodulation-and-neural-engineering` |
| Misconceptions | §15 → `neurogen-reference` |
| Numbers | §16 → `neurogen-reference` |
| **Frontier: what actually moved** | **§17 → `neurogen-reference`** |
| Books | §18 → `neurogen-reference` |
| Quick reference | §19 → `neurogen-reference` |

---

## §1. Molecular Genetics

### 1.1 The central dogma, stated accurately

```
DNA --replication--> DNA
DNA --transcription--> RNA --translation--> protein
RNA --reverse transcription--> DNA        (retroviruses, retrotransposons, telomerase)
```
**⚠️ Crick's actual claim was narrower than the cartoon**: once information passes *into*
protein, it cannot get back out. **Reverse transcription doesn't violate it; prions are the
genuinely awkward case** — conformational information propagating without nucleic acid.

**Genetic code**: 64 codons → 20 amino acids + stop. **Degenerate** (⚠️ **mostly in the
third position — "wobble" — which is why many third-position substitutions are
synonymous**), non-overlapping, near-universal (⚠️ **mitochondria and some ciliates
differ**).

**⚠️ Synonymous ≠ silent.** Codon usage affects translation *speed*, which affects
co-translational folding; it also affects mRNA structure, stability, and splicing
enhancers. **"Silent mutation" is a misnomer that has misled variant interpretation.**

### 1.2 Transcription and splicing

**Transcription**: promoter → RNA Pol II (⚠️ **plus general TFs and Mediator**) →
elongation → termination. **Pol I** for rRNA, **Pol III** for tRNA and 5S.

**⚠️ Splicing is where most of the complexity lives.** Spliceosome recognizes **GT…AG**
(the GU-AG rule), branch point, and polypyrimidine tract. **Alternative splicing**
(exon skipping, intron retention, alternative 5′/3′ sites, mutually exclusive exons)
means **~20,000 genes produce well over 100,000 proteins.**

**⚠️ Splice-site mutations are a large and underappreciated share of pathogenic variants** —
and a variant deep in an intron, or a synonymous variant that creates a cryptic splice
site, can be fully causal. **This is why "coding-only" exome sequencing misses disease.**

**Post-transcriptional**: 5′ cap, poly(A) tail, **nonsense-mediated decay** (⚠️ **degrades
transcripts with a premature stop codon more than ~50 nt upstream of the last exon-exon
junction — which is why some nonsense mutations produce no protein at all rather than a
truncated one, and why the position of the stop matters clinically**).

### 1.3 Translation and protein fate
Ribosome (⚠️ **a ribozyme — the peptidyl transferase centre is RNA**), tRNA charging,
initiation/elongation/termination. Then folding (chaperones), post-translational
modification (phosphorylation, glycosylation, ubiquitination), trafficking, and degradation
via **ubiquitin-proteasome** or autophagy.

---

## §2. Gene Regulation and Epigenetics

### 2.1 Cis-regulation

**Promoters** (proximal), **enhancers** (⚠️ **can act over hundreds of kilobases, in either
orientation, and are frequently not the nearest gene — which is why assigning a GWAS hit
to a gene by proximity is unreliable**), silencers, insulators.

**⚠️ 3D genome organization is the missing piece in most explanations**: **TADs**
(topologically associating domains) bounded by **CTCF/cohesin** loops constrain which
enhancers can reach which promoters. **Disrupting a TAD boundary can cause disease by
letting an enhancer contact the wrong gene** — demonstrated in limb malformations. **The
mechanism is loop extrusion: cohesin extrudes DNA until blocked by convergently-oriented
CTCF sites.**

**Transcription factors** bind short degenerate motifs (~6–12 bp), which occur far too
often by chance — ⚠️ **so specificity comes from combinatorial binding, cooperativity, and
chromatin accessibility, not from the motif alone.**

### 2.2 Chromatin and epigenetic marks

| Mark | Effect |
|---|---|
| **DNA methylation (5mC at CpG)** | ⚠️ **Promoter CpG island methylation → silencing. Gene-body methylation correlates with *expression*** |
| **H3K4me3** | Active promoters |
| **H3K27ac** | ⚠️ **Active enhancers — the standard enhancer mark** |
| **H3K4me1** | Primed/poised enhancers |
| **H3K27me3** | Polycomb repression, ⚠️ **facultative heterochromatin — reversible** |
| **H3K9me3** | Constitutive heterochromatin |
| **H3K36me3** | Gene bodies, transcription elongation |

**⚠️ "Bivalent" domains** (H3K4me3 + H3K27me3) mark developmentally poised genes in stem
cells.

**Imprinting** — parent-of-origin monoallelic expression at ~100–200 loci, via
differentially methylated regions. ⚠️ **Prader-Willi and Angelman syndromes arise from the
same 15q11-13 region depending on parental origin** — the cleanest demonstration that
sequence alone doesn't determine phenotype.

**X-inactivation** via *XIST* lncRNA — ⚠️ **random in humans, producing mosaic females, and
~15% of X genes escape it.**

**⚠️ Transgenerational epigenetic inheritance in mammals is contested.** Most marks are
erased in two reprogramming waves (gametogenesis and post-fertilization). **Claims of
inherited environmental effects are much stronger in plants and *C. elegans* than in
mammals**, and mammalian claims frequently have unexcluded confounds (in-utero exposure
affects three generations at once: mother, fetus, and fetal germline).

### 2.3 Non-coding RNA
**miRNA** (~22 nt, seed match to 3′UTR, translational repression/destabilization —
⚠️ **one miRNA regulates hundreds of targets**), **siRNA**, **piRNA** (transposon defence
in germline), **lncRNA** (⚠️ **thousands annotated, function demonstrated for a small
minority — treat "lncRNA X regulates Y" claims with care**), **circRNA**, **snoRNA**.

---

## §3. Mutation, Variation, Inheritance

### 3.1 Variant classes and consequences
**By type**: SNV, indel, CNV, inversion, translocation, repeat expansion (⚠️ **anticipation
in Huntington's, fragile X — expansions grow across generations and severity tracks repeat
number**), aneuploidy.
**By coding consequence**: synonymous (⚠️ **§1.1 — not necessarily silent**), missense,
nonsense (⚠️ **§1.2 — NMD position-dependent**), frameshift, splice-site, regulatory.

**⚠️ Loss-of-function vs gain-of-function is the distinction that determines therapy.**
LoF → replace or upregulate. GoF/dominant-negative → ⚠️ **you must silence the mutant
allele, and allele-specific silencing is much harder than adding a gene.**

**Mutation rate**: ~1.1 × 10⁻⁸ per base per generation → **~70 de novo mutations per
individual.** ⚠️ **Strongly paternal-age dependent (~2 additional per paternal year)**,
because spermatogonia keep dividing.

### 3.2 Inheritance patterns
Autosomal dominant, autosomal recessive, X-linked (recessive/dominant), mitochondrial
(⚠️ **maternal, with heteroplasmy and a threshold effect — the proportion of mutant mtDNA
determines whether phenotype appears**), and non-Mendelian: imprinting, mosaicism,
digenic, polygenic.

**⚠️ Penetrance and expressivity are separate concepts and both get flattened.**
**Penetrance** = the proportion of carriers showing *any* phenotype. **Expressivity** =
how *severely*. ⚠️ **Penetrance estimated from affected families is systematically
overestimated** — ascertainment bias — and population-biobank estimates are frequently far
lower.

**Variant interpretation** (ACMG/AMP): pathogenic → likely pathogenic → **VUS** → likely
benign → benign. ⚠️ **VUS is the operational problem — most rare missense variants land
there, and reclassification happens as evidence accrues.** Evidence lines: population
frequency (gnomAD), segregation, de novo status, functional assays, computational
prediction (⚠️ **which is supporting evidence only, never sufficient**).
