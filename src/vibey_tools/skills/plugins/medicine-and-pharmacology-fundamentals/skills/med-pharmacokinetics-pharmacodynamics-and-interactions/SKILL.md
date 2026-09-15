---
name: med-pharmacokinetics-pharmacodynamics-and-interactions
description: "Use for how drugs actually behave in a body: pharmacokinetics with absorption, distribution, metabolism, excretion, half-life and clearance, pharmacodynamics with receptors, agonism, antagonism and efficacy, dose-response and the therapeutic window, drug interactions including the cytochrome P450 pathways, variability between people from genetics, age, organ function and pregnancy, and adverse effects and how they are classified and detected. Technical orientation, not medical advice."
---

# Medicine and Pharmacology: Pharmacokinetics, Pharmacodynamics, Dose-Response and the Therapeutic Window, Drug Interactions, Variability Between People, and Adverse Effects

> **Part 2 of 6** of the *Fundamentals of Medicine and Pharmacology* reference (plugin `medicine-and-pharmacology-fundamentals`), covering §7–§12. Sibling skills: `med-reading-the-field-physiology-and-clinical-reasoning` (§0–§6), `med-drug-classes-cardiovascular-anti-infective-and-analgesia` (§13–§15), `med-drug-classes-neuro-endocrine-immunology-and-oncology` (§16–§19), `med-evidence-trials-safety-screening-and-ethics` (§20–§26), `med-reference` (§27–§32). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The physiology and pharmacology are stable. Two areas are moving fast. See §27 → `med-reference` for incretin therapeutics, and antimicrobial resistance.

> **⚠️ NOT MEDICAL ADVICE, and this matters more here than in any other file in this
> series.** ⚠️ **Nothing here is a diagnosis, a treatment recommendation, or dosing
> guidance. Individual clinical decisions require a licensed clinician who knows your
> history, and no general reference substitutes for that.**
>
> **⚠️ This is pitched where a preclinical survey or an informed-patient reference sits:
> the concepts that let you understand what medicine is doing and evaluate claims about
> it.** ⚠️ **It deliberately contains no dosing tables, no specific regimens, and no
> operational detail.**
>
> **Complements an organic-chemistry reference (drug molecules and metabolism), a
> statistics-adjacent reference (trial methodology), and a speaking-and-influence reference
> (§20 → `med-evidence-trials-safety-screening-and-ethics`'s evidence-quality reasoning is the same skill).**
>
> **⚠️ GOTCHA** boxes mark where clinical intuition — including clinicians' intuition — is
> reliably wrong.
>
> **The three ideas that organize this document:**
> 1. **⚠️ A TEST RESULT IS NOT A DIAGNOSIS** (§6 → `med-reading-the-field-physiology-and-clinical-reasoning`). **The probability that a positive test
>    means disease depends on how likely disease was beforehand. This single Bayesian fact
>    is the most useful thing in clinical medicine and the most consistently misunderstood
>    by patients and clinicians alike.**
> 2. **⚠️ EVERY DRUG IS A POISON AT SOME DOSE, AND EVERY EFFECT HAS A COST** (§9, §12).
>    **There are no side effects — only effects, some of which you wanted. The therapeutic
>    question is always a ratio, never an absolute.**
> 3. **⚠️ MOST OF WHAT DETERMINES HEALTH HAPPENS OUTSIDE CLINICAL MEDICINE** (§25 → `med-evidence-trials-safety-screening-and-ethics`).
>    **Sanitation, nutrition, income, housing and vaccination did more for life expectancy
>    than the entire therapeutic pharmacopoeia, and clinical medicine's share of health
>    outcomes is smaller than its share of spending.**

---

## §7. ⚠️ Pharmacokinetics

> **⚠️ What the body does to the drug. ADME.**
```
⚠️ ⚠️ ABSORPTION  ⚠️ BIOAVAILABILITY is the fraction of an
   administered dose reaching systemic circulation unchanged.
   ⚠️ IV is 100% by definition
   ⚠️ ⚠️ FIRST-PASS METABOLISM  ⚠️ oral drugs traverse the gut
      wall and LIVER before reaching circulation, and some are
      largely destroyed there. ⚠️ This is why some drugs cannot
      be given orally at all, and why oral and IV doses of the
      same drug differ so much
   ⚠️ Routes: oral, IV, IM, SC, transdermal, inhaled,
      sublingual (⚠️ which bypasses first pass), rectal, topical
⚠️ ⚠️ DISTRIBUTION  ⚠️ VOLUME OF DISTRIBUTION is a
   pharmacokinetic abstraction, not a real volume — a drug
   concentrated in tissue has a Vd far exceeding body volume
   ⚠️ ⚠️ PROTEIN BINDING  ⚠️ only the FREE fraction is active.
      ⚠️ Displacement interactions and low albumin change free
      concentration without changing the total measured level
   ⚠️ Barriers: blood-brain, placenta
⚠️ ⚠️ METABOLISM  ⚠️ PHASE I (oxidation, reduction, hydrolysis —
   mostly CYP450) and PHASE II (conjugation — making it
   water-soluble for excretion)
   ⚠️ ⚠️ THE CYP450 SYSTEM IS WHERE MOST INTERACTIONS LIVE (§10)
   ⚠️ PRODRUGS require metabolism to become active — ⚠️ so a
      poor metabolizer gets NO effect, which is the reverse of
      the usual intuition (§11)
⚠️ ELIMINATION  renal (⚠️ and renal impairment is the single
   most common reason doses must change) and hepatic/biliary
⚠️ ⚠️ HALF-LIFE  ⚠️ time for concentration to halve.
   ⚠️ STEADY STATE takes about 4-5 half-lives — ⚠️ and so does
   washout. ⚠️ This is why some drugs take weeks to show full
   effect and weeks to leave
⚠️ ⚠️ FIRST-ORDER vs ZERO-ORDER  ⚠️ most drugs clear a constant
   FRACTION per unit time. ⚠️ A few saturate their metabolism
   and clear a constant AMOUNT — ⚠️ so concentration rises
   disproportionately with dose. ⚠️ Ethanol and phenytoin are
   the classic examples, and this is why such drugs are
   dangerous near the top of their range
```

---

## §8. ⚠️ Pharmacodynamics

> **⚠️ What the drug does to the body.**
```
⚠️ ⚠️ AFFINITY vs EFFICACY — the distinction that makes the rest
   comprehensible
   ⚠️ AFFINITY  how tightly it binds
   ⚠️ EFFICACY  what happens once bound
⚠️ THE LIGAND CLASSES
   ⚠️ FULL AGONIST  binds and produces maximal response
   ⚠️ PARTIAL AGONIST  ⚠️ produces a submaximal response — ⚠️ and
      therefore acts as an ANTAGONIST in the presence of a full
      agonist, by occupying the receptor and doing less.
      ⚠️ Clinically important and counterintuitive
   ⚠️ ANTAGONIST  binds, no effect, blocks
      ⚠️ COMPETITIVE (surmountable by more agonist) vs
      NON-COMPETITIVE/irreversible (not surmountable)
   ⚠️ INVERSE AGONIST  ⚠️ reduces CONSTITUTIVE activity below
      baseline — genuinely different from an antagonist
   ⚠️ ALLOSTERIC MODULATORS  bind elsewhere and change the
      response to the natural ligand
⚠️ ⚠️ RECEPTOR REGULATION explains tolerance and rebound
   ⚠️ Chronic agonist → DOWNREGULATION and desensitization →
      tolerance
   ⚠️ ⚠️ Chronic antagonist → UPREGULATION → ⚠️ REBOUND OR
      WITHDRAWAL PHENOMENA WHEN STOPPED ABRUPTLY. ⚠️ This is
      why several drug classes must be tapered rather than
      stopped
⚠️ SPARE RECEPTORS  ⚠️ maximal response may occur with only a
   fraction occupied, which decouples occupancy from effect
```

---

## §9. ⚠️ Dose-Response and the Therapeutic Window

```
⚠️ ⚠️ "THE DOSE MAKES THE POISON" (Paracelsus) is the
   foundational statement of pharmacology and toxicology alike
⚠️ THE CURVES  ⚠️ graded dose-response (magnitude in an
   individual) vs QUANTAL (fraction of a population responding)
   ⚠️ EC50 / ED50 — potency · ⚠️ Emax — EFFICACY
   ⚠️ ⚠️ POTENCY AND EFFICACY ARE DIFFERENT AND THE CONFUSION IS
   COMMERCIALLY USEFUL. ⚠️ A more potent drug works at a lower
   DOSE; that says nothing about how much effect it can
   achieve. ⚠️ Milligram comparisons between drugs are
   meaningless
⚠️ ⚠️ THERAPEUTIC INDEX  ⚠️ the ratio between the toxic dose and
   the effective dose. ⚠️ NARROW THERAPEUTIC INDEX drugs — where
   the effective and dangerous ranges nearly overlap — are the
   ones requiring monitoring, and they are a disproportionate
   share of serious medication harm
⚠️ ⚠️ THERAPEUTIC DRUG MONITORING exists for exactly those, and
   the reason is §11's variability: the same dose produces
   different concentrations in different people
⚠️ HORMESIS  ⚠️ some agents have opposite effects at low and
   high doses — which complicates linear extrapolation from
   high-dose toxicology
⚠️ ⚠️ AND THE POPULATION VERSION  ⚠️ a drug that helps on average
   may harm a subgroup; average effect and individual effect
   are different quantities (§20)
```

---

## §10. ⚠️ Drug Interactions

**⚠️ PHARMACOKINETIC interactions** change the concentration: ⚠️ **CYP INDUCTION (more
enzyme, lower levels, loss of effect — and a prodrug's effect INCREASES) versus CYP
INHIBITION (less enzyme, higher levels, toxicity).**
**⚠️ Also**: ⚠️ **absorption interference (chelation, pH change), protein-binding
displacement, transporter effects (P-glycoprotein), and competition for renal excretion.**
**⚠️ PHARMACODYNAMIC interactions** change the effect at constant concentration:
⚠️ **additive, synergistic, or antagonistic — and the additive sedative or bleeding effects
of several drugs each individually acceptable is a very common real-world harm.**
> **⚠️ GOTCHA — food, supplements and herbal products interact, and patients frequently do
> not report them because they do not consider them drugs.** ⚠️ **Grapefruit juice inhibits
> intestinal CYP3A4; ⚠️ St John's wort is a potent enzyme INDUCER that has caused
> transplant rejection and contraceptive failure.** **⚠️ "Natural" carries no pharmacological
> meaning whatsoever.**

**⚠️ POLYPHARMACY** is the systemic version — ⚠️ **interaction risk rises faster than
linearly with the number of medications, and DEPRESCRIBING is a legitimate and underused
clinical activity** (§4 → `med-reading-the-field-physiology-and-clinical-reasoning`'s multimorbidity).
**⚠️ The prescribing cascade** is the pattern worth naming: ⚠️ **a drug's adverse effect is
mistaken for a new condition and treated with another drug.**

---

## §11. Variability Between People

**⚠️ The same dose does not produce the same result**, ⚠️ **and the sources are systematic
enough to be anticipated.**
**⚠️ PHARMACOGENOMICS**: ⚠️ **CYP2D6 poor, intermediate, extensive and ULTRARAPID
metabolizer phenotypes; CYP2C19; TPMT; HLA alleles predicting severe hypersensitivity —
⚠️ and testing is standard practice for a growing but still small set of drugs.**
**⚠️ Organ function**: ⚠️ **renal and hepatic impairment are the dominant practical
modifiers.**
**⚠️ Age**: ⚠️ **neonates and children are not small adults — organ systems and metabolism
differ qualitatively; ⚠️ older adults have altered body composition, reduced renal function
and greater sensitivity, which is why deprescribing frameworks exist.**
**⚠️ Pregnancy and lactation** — ⚠️ **altered physiology plus fetal exposure, and an evidence
base that is thin precisely because trials exclude pregnant people, which is itself an
equity problem** (§21 → `med-evidence-trials-safety-screening-and-ethics`).
**⚠️ Sex differences** in pharmacokinetics and adverse-effect profiles are real and
historically under-studied.
**⚠️ Adherence** is the largest single source of variability in practice, ⚠️ **and it is
consistently overestimated by prescribers.**

---

## §12. Adverse Effects

```
⚠️ ⚠️ THERE ARE NO "SIDE EFFECTS" — ONLY EFFECTS, some of which
   you wanted (§1's second organizing idea)
⚠️ THE CLASSIFICATION
   ⚠️ TYPE A (augmented)  ⚠️ predictable, dose-related, an
      extension of the drug's pharmacology. ⚠️ Most adverse
      effects, and manageable by dose
   ⚠️ ⚠️ TYPE B (bizarre)  ⚠️ unpredictable, NOT dose-related —
      allergy, idiosyncratic reactions. ⚠️ Rare, and
      disproportionately the cause of serious harm
   ⚠️ Plus chronic, delayed (⚠️ including carcinogenesis and
      teratogenesis, which may appear decades later) and
      end-of-use effects
⚠️ ⚠️ ALLERGY vs INTOLERANCE  ⚠️ a genuinely important
   distinction. ⚠️ Nausea from an antibiotic is not an allergy,
   and mislabelling it as one removes a useful drug class from
   a patient for life — ⚠️ penicillin allergy delabelling is an
   established quality-improvement activity for this reason
⚠️ ⚠️ PHARMACOVIGILANCE AND ITS LIMIT  ⚠️ trials enroll
   thousands; RARE adverse effects appear only in post-marketing
   surveillance, in millions of people, sometimes years later.
   ⚠️ THEREFORE A NEWLY APPROVED DRUG'S SAFETY PROFILE IS
   ALWAYS INCOMPLETE — this is structural, not negligence
   ⚠️ Spontaneous reporting systems are known to be
   substantially under-reported and cannot give incidence
⚠️ ⚠️ NOCEBO  ⚠️ adverse effects arising from EXPECTATION are
   real and measurable — ⚠️ blinded trials find substantial
   adverse-effect rates in placebo arms, which matters for
   interpreting real-world complaint rates
```

---

# PART III — DRUG CLASSES
