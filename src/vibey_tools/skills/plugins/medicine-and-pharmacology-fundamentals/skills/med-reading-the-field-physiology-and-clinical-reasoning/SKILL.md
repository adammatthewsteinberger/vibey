---
name: med-reading-the-field-physiology-and-clinical-reasoning
description: "Use for the foundations and the single most misunderstood piece of medicine: how to read claims in this field, homeostasis and physiological organization, drug targets, pathophysiology, clinical reasoning including heuristics and diagnostic error, and diagnostic testing with sensitivity, specificity, predictive values and the Bayesian logic that makes a positive result mean far less than people assume at low prevalence. A technical reference, not medical advice. Includes the router for the whole medicine and pharmacology reference."
---

# Medicine and Pharmacology: How to Read This Field, Homeostasis and Physiological Organization, Drug Targets, Pathophysiology, Clinical Reasoning, and Diagnostic Testing

> **Part 1 of 6** of the *Fundamentals of Medicine and Pharmacology* reference (plugin `medicine-and-pharmacology-fundamentals`), covering §0–§6. Sibling skills: `med-pharmacokinetics-pharmacodynamics-and-interactions` (§7–§12), `med-drug-classes-cardiovascular-anti-infective-and-analgesia` (§13–§15), `med-drug-classes-neuro-endocrine-immunology-and-oncology` (§16–§19), `med-evidence-trials-safety-screening-and-ethics` (§20–§26), `med-reference` (§27–§32). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 1. **⚠️ A TEST RESULT IS NOT A DIAGNOSIS** (§6). **The probability that a positive test
>    means disease depends on how likely disease was beforehand. This single Bayesian fact
>    is the most useful thing in clinical medicine and the most consistently misunderstood
>    by patients and clinicians alike.**
> 2. **⚠️ EVERY DRUG IS A POISON AT SOME DOSE, AND EVERY EFFECT HAS A COST** (§9 → `med-pharmacokinetics-pharmacodynamics-and-interactions`, §12 → `med-pharmacokinetics-pharmacodynamics-and-interactions`).
>    **There are no side effects — only effects, some of which you wanted. The therapeutic
>    question is always a ratio, never an absolute.**
> 3. **⚠️ MOST OF WHAT DETERMINES HEALTH HAPPENS OUTSIDE CLINICAL MEDICINE** (§25 → `med-evidence-trials-safety-screening-and-ethics`).
>    **Sanitation, nutrition, income, housing and vaccination did more for life expectancy
>    than the entire therapeutic pharmacopoeia, and clinical medicine's share of health
>    outcomes is smaller than its share of spending.**

---

## §0. Routing

| You want... | Go to |
|---|---|
| How to read this field | §1 |
| Physiology's organizing ideas | §2 |
| Drug targets | §3 |
| Pathophysiology | §4 |
| **⚠️ Clinical reasoning** | **§5** |
| **⚠️ Diagnostic testing** | **§6** |
| **⚠️ Pharmacokinetics** | **§7 → `med-pharmacokinetics-pharmacodynamics-and-interactions`** |
| **⚠️ Pharmacodynamics** | **§8 → `med-pharmacokinetics-pharmacodynamics-and-interactions`** |
| **⚠️ Dose-response** | **§9 → `med-pharmacokinetics-pharmacodynamics-and-interactions`** |
| **⚠️ Interactions** | **§10 → `med-pharmacokinetics-pharmacodynamics-and-interactions`** |
| Variability between people | §11 → `med-pharmacokinetics-pharmacodynamics-and-interactions` |
| Adverse effects | §12 → `med-pharmacokinetics-pharmacodynamics-and-interactions` |
| Cardiovascular drugs | §13 → `med-drug-classes-cardiovascular-anti-infective-and-analgesia` |
| **⚠️ Anti-infectives** | **§14 → `med-drug-classes-cardiovascular-anti-infective-and-analgesia`** |
| **⚠️ Analgesia** | **§15 → `med-drug-classes-cardiovascular-anti-infective-and-analgesia`** |
| Neuro and psychiatric | §16 → `med-drug-classes-neuro-endocrine-immunology-and-oncology` |
| Endocrine and metabolic | §17 → `med-drug-classes-neuro-endocrine-immunology-and-oncology` |
| Immunology and biologics | §18 → `med-drug-classes-neuro-endocrine-immunology-and-oncology` |
| Oncology | §19 → `med-drug-classes-neuro-endocrine-immunology-and-oncology` |
| **⚠️ Evidence-based medicine** | **§20 → `med-evidence-trials-safety-screening-and-ethics`** |
| **⚠️ Trial pathologies** | **§21 → `med-evidence-trials-safety-screening-and-ethics`** |
| Drug development | §22 → `med-evidence-trials-safety-screening-and-ethics` |
| **⚠️ Patient safety** | **§23 → `med-evidence-trials-safety-screening-and-ethics`** |
| **⚠️ Screening** | **§24 → `med-evidence-trials-safety-screening-and-ethics`** |
| **⚠️ Public health** | **§25 → `med-evidence-trials-safety-screening-and-ethics`** |
| Ethics | §26 → `med-evidence-trials-safety-screening-and-ethics` |
| **What's live** | **§27 → `med-reference`** |
| Misconceptions, numbers | §28–§29 → `med-reference` |
| Sources, quick ref, method | §30–§32 → `med-reference` |

---

## §1. How to Read This Field

```
⚠️ ⚠️ MEDICINE IS A PRACTICE UNDER UNCERTAINTY, not an applied
   science with deterministic answers. ⚠️ The same treatment
   helps some patients, harms others, and does nothing for
   most — and you usually cannot know in advance which
⚠️ ⚠️ THE NUMBER NEEDED TO TREAT makes this concrete: ⚠️ for
   many effective, guideline-recommended treatments, dozens of
   people take the drug for one to benefit. ⚠️ That is not a
   failure of the drug; it is what "effective" means at
   population level (§20)
⚠️ THE HIERARCHY OF WHAT IS KNOWN  ⚠️ mechanism (why it should
   work) is WEAKER evidence than outcome data (whether it did).
   ⚠️ The graveyard of plausible mechanisms that failed in
   trials is very large (§21)
⚠️ ⚠️ CLINICAL EQUIPOISE  ⚠️ genuine uncertainty about which of
   two options is better is the ETHICAL PRECONDITION for a
   trial — and it is more common than confident practice
   suggests
⚠️ WHAT THIS FILE IS FOR  ⚠️ understanding what medicine is
   doing and how to evaluate claims about it — ⚠️ NOT
   self-diagnosis or self-treatment, which are genuinely
   dangerous and for which this is not adequate
```

---

# PART I — FOUNDATIONS

## §2. Homeostasis and Physiological Organization

**⚠️ HOMEOSTASIS is the organizing concept**: ⚠️ **the body maintains internal variables —
temperature, pH, glucose, osmolality, blood pressure — within narrow ranges through negative
feedback loops with sensors, controllers and effectors.**
**⚠️ Most disease is a failure of regulation** rather than of a part — ⚠️ **which is why
understanding the control loop usually explains the illness better than knowing the organ.**
**⚠️ Feedback matters clinically**: ⚠️ **negative feedback stabilizes, POSITIVE feedback runs
away (clotting cascades, labour, and pathologically in septic shock).**
**⚠️ RESERVE CAPACITY** explains why disease presents late: ⚠️ **kidneys, liver and lungs
have large functional reserve, so substantial damage accumulates before symptoms appear —
which is the physiological argument for screening (§24 → `med-evidence-trials-safety-screening-and-ethics`) and the reason "I felt fine" is not
evidence of health.**
**⚠️ Compensation confounds interpretation**: ⚠️ **a normal-looking value may be normal
because a compensatory mechanism is working hard, and its failure is then abrupt.**
**⚠️ The systems**: ⚠️ **cardiovascular, respiratory, renal, gastrointestinal, endocrine,
nervous, immune, musculoskeletal, reproductive — and the integrative fact that they are
coupled, so single-system thinking misses most of the interesting pathology.**

---

## §3. Drug Targets

```
⚠️ ⚠️ ALMOST ALL DRUGS WORK BY BINDING A PROTEIN. ⚠️ The target
   landscape is therefore a protein landscape
⚠️ THE MAJOR TARGET CLASSES
   ⚠️ RECEPTORS  ⚠️ GPCRs (the largest single drug target family
      by a wide margin), ion channels, nuclear receptors,
      enzyme-linked receptors
   ⚠️ ENZYMES  ⚠️ inhibited far more often than activated,
      because breaking a catalytic site is easier than
      improving one
   ⚠️ TRANSPORTERS  ⚠️ reuptake inhibitors, pumps
   ⚠️ ION CHANNELS · structural proteins · nucleic acids
⚠️ ⚠️ THE DRUGGABILITY PROBLEM  ⚠️ most proteins are NOT
   druggable by small molecules — they lack a suitable binding
   pocket. ⚠️ This is why so much disease biology is understood
   and untreated, and why biologics (§18) and newer modalities
   matter
⚠️ SELECTIVITY vs SPECIFICITY  ⚠️ no drug is perfectly specific;
   ⚠️ OFF-TARGET binding is where most adverse effects come from
   (§12)
⚠️ NEWER MODALITIES  ⚠️ monoclonal antibodies · antisense and
   siRNA · mRNA · gene therapy · cell therapy · PROTACs
   (targeted protein degradation) — ⚠️ several of which reach
   targets small molecules cannot
```

---

## §4. Pathophysiology

**⚠️ The general mechanisms of disease** — ⚠️ **and most named diseases are a combination:**
⚠️ **INFLAMMATION (acute and chronic — a defence mechanism that causes much of the damage
attributed to the pathogen); ⚠️ ISCHAEMIA and hypoxia; ⚠️ NEOPLASIA (§19 → `med-drug-classes-neuro-endocrine-immunology-and-oncology`); ⚠️ degeneration;
⚠️ AUTOIMMUNITY (loss of self-tolerance); ⚠️ metabolic derangement; ⚠️ genetic defects;
⚠️ and INFECTION** (§14 → `med-drug-classes-cardiovascular-anti-infective-and-analgesia`).
**⚠️ Cell injury and death**: ⚠️ **reversible injury, necrosis (uncontrolled, inflammatory)
versus apoptosis (programmed, quiet) — and the distinction matters therapeutically.**
**⚠️ Repair and its costs**: ⚠️ **regeneration versus FIBROSIS — scar tissue restores
integrity and not function, which is why fibrosis is the final common pathway of chronic
disease in liver, lung, kidney and heart alike.**
**⚠️ Risk factor versus cause**: ⚠️ **most chronic disease is multifactorial with no single
cause, and the Bradford Hill considerations are the standard framework for reasoning from
association toward causation.**
**⚠️ Multimorbidity is the actual clinical reality** — ⚠️ **most older patients have several
conditions interacting, and single-disease guidelines applied additively produce
polypharmacy** (§10 → `med-pharmacokinetics-pharmacodynamics-and-interactions`).

---

## §5. ⚠️ Clinical Reasoning

```
⚠️ THE TWO MODES  ⚠️ PATTERN RECOGNITION (fast, usually right,
   fails on atypical presentations) and ⚠️ ANALYTICAL reasoning
   (slow, effortful, needed when the pattern does not fit)
   ⚠️ Expertise is largely a larger pattern library PLUS knowing
   when the pattern does not apply
⚠️ ⚠️ THE DIFFERENTIAL DIAGNOSIS is the core discipline —
   ⚠️ and it is ordered by two axes at once: what is LIKELY and
   what is DANGEROUS. ⚠️ "Must not miss" diagnoses stay on the
   list even at low probability, which is a decision-theoretic
   move rather than a probabilistic one
⚠️ ⚠️ THE HISTORY DOES MOST OF THE WORK. ⚠️ Studies repeatedly
   find the majority of diagnoses are established from history
   alone, with examination and investigation confirming rather
   than discovering. ⚠️ This is the opposite of how medicine is
   portrayed
⚠️ ⚠️ THE COGNITIVE BIASES, which are documented in clinicians
   ⚠️ ANCHORING on the first hypothesis · ⚠️ PREMATURE CLOSURE
      (the single most common diagnostic error) · availability
      bias · confirmation bias · ⚠️ DIAGNOSIS MOMENTUM (a label
      acquired early is carried forward unexamined) ·
      ⚠️ SEARCH SATISFICING (finding one abnormality and
      stopping) · attribution bias toward the patient
⚠️ DEBIASING that works  ⚠️ explicit differentials, diagnostic
   time-outs, "what else could this be?", second opinions,
   and structural rather than exhortative fixes (§23)
⚠️ ⚠️ ILLNESS vs DISEASE  ⚠️ disease is the pathological process;
   ILLNESS is the person's experience of it. ⚠️ They can occur
   independently, and treating only the former explains much
   patient dissatisfaction
```

---

## §6. ⚠️ Diagnostic Testing

> **⚠️ §1's first organizing idea and the highest-value section in this file. If you learn
> one thing here, learn this.**
```
⚠️ THE FOUR NUMBERS, and two are properties of the TEST while
   two are properties of the SITUATION
   ⚠️ SENSITIVITY  ⚠️ of people WITH disease, the fraction who
      test positive. ⚠️ A property of the test
   ⚠️ SPECIFICITY  ⚠️ of people WITHOUT disease, the fraction who
      test negative. ⚠️ A property of the test
   ⚠️ ⚠️ POSITIVE PREDICTIVE VALUE  ⚠️ of people who test
      positive, the fraction who HAVE the disease.
      ⚠️ DEPENDS ON PREVALENCE
   ⚠️ ⚠️ NEGATIVE PREDICTIVE VALUE — likewise
⚠️ ⚠️ THE CENTRAL FACT: PPV DEPENDS ON PRE-TEST PROBABILITY.
   ⚠️ THE SAME TEST, WITH THE SAME SENSITIVITY AND SPECIFICITY,
   MEANS COMPLETELY DIFFERENT THINGS IN DIFFERENT POPULATIONS
⚠️ ⚠️ THE WORKED INTUITION THAT MAKES IT CONCRETE
   ⚠️ Take a test with 99% sensitivity and 99% specificity —
   which is a very good test. ⚠️ Apply it where the disease
   affects 1 in 10,000
   ⚠️ Out of 1,000,000 people: 100 have it, and ~99 test
   positive. ⚠️ 999,900 do not have it, and ~9,999 test
   POSITIVE ANYWAY
   ⚠️ ⚠️ SO ~10,098 POSITIVES, OF WHOM ~99 ARE REAL — UNDER 1%.
   ⚠️ A positive result on an excellent test still means the
   person probably does not have the disease
   ⚠️ ⚠️ THIS IS THE BASE RATE FALLACY, and it is the single
   most consequential reasoning error in medicine
⚠️ LIKELIHOOD RATIOS  ⚠️ the cleanest way to use tests — LR+
   and LR− multiply the pre-test ODDS to give post-test odds.
   ⚠️ An LR near 1 means the test changed nothing
⚠️ ⚠️ THE THRESHOLD IS A CHOICE, NOT A FACT  ⚠️ moving the cutoff
   trades sensitivity against specificity (the ROC curve).
   ⚠️ Where you set it depends on the relative cost of missing
   disease versus falsely labelling health
⚠️ ⚠️ THEREFORE: DO NOT ORDER A TEST WHOSE RESULT WILL NOT
   CHANGE WHAT YOU DO. ⚠️ Low-pre-test-probability testing
   generates false positives, cascades of further testing,
   incidental findings and harm (§24)
```

---

# PART II — PHARMACOLOGY
