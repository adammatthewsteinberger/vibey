---
name: med-evidence-trials-safety-screening-and-ethics
description: "Use for the system layer and for judging medical evidence: evidence-based medicine and the hierarchy and its limits, trial methodology and its pathologies including surrogate endpoints, composite outcomes, publication bias and industry funding effects, drug development and regulation, patient safety and systems thinking about error, screening with lead-time bias and overdiagnosis, the difference between public health and clinical reasoning, and clinical ethics."
---

# Medicine and Pharmacology: Evidence-Based Medicine, Trial Methodology and Its Pathologies, Drug Development and Regulation, Patient Safety, Screening, Public Health Versus Clinical Medicine, and Ethics

> **Part 5 of 6** of the *Fundamentals of Medicine and Pharmacology* reference (plugin `medicine-and-pharmacology-fundamentals`), covering §20–§26. Sibling skills: `med-reading-the-field-physiology-and-clinical-reasoning` (§0–§6), `med-pharmacokinetics-pharmacodynamics-and-interactions` (§7–§12), `med-drug-classes-cardiovascular-anti-infective-and-analgesia` (§13–§15), `med-drug-classes-neuro-endocrine-immunology-and-oncology` (§16–§19), `med-reference` (§27–§32). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> (§20's evidence-quality reasoning is the same skill).**
>
> **⚠️ GOTCHA** boxes mark where clinical intuition — including clinicians' intuition — is
> reliably wrong.
>
> **The three ideas that organize this document:**
> 1. **⚠️ A TEST RESULT IS NOT A DIAGNOSIS** (§6 → `med-reading-the-field-physiology-and-clinical-reasoning`). **The probability that a positive test
>    means disease depends on how likely disease was beforehand. This single Bayesian fact
>    is the most useful thing in clinical medicine and the most consistently misunderstood
>    by patients and clinicians alike.**
> 2. **⚠️ EVERY DRUG IS A POISON AT SOME DOSE, AND EVERY EFFECT HAS A COST** (§9 → `med-pharmacokinetics-pharmacodynamics-and-interactions`, §12 → `med-pharmacokinetics-pharmacodynamics-and-interactions`).
>    **There are no side effects — only effects, some of which you wanted. The therapeutic
>    question is always a ratio, never an absolute.**
> 3. **⚠️ MOST OF WHAT DETERMINES HEALTH HAPPENS OUTSIDE CLINICAL MEDICINE** (§25).
>    **Sanitation, nutrition, income, housing and vaccination did more for life expectancy
>    than the entire therapeutic pharmacopoeia, and clinical medicine's share of health
>    outcomes is smaller than its share of spending.**

---

## §20. ⚠️ Evidence-Based Medicine

```
⚠️ ⚠️ WHAT IT ACTUALLY IS  ⚠️ integrating the best available
   evidence with clinical expertise AND patient values.
   ⚠️ It is NOT "follow the guideline" — the caricature has
   done real damage to the idea
⚠️ THE EVIDENCE HIERARCHY, and its qualifications
   ⚠️ Systematic reviews and meta-analyses → RCTs → cohort →
      case-control → case series → expert opinion
   ⚠️ ⚠️ A BAD META-ANALYSIS OF BAD TRIALS IS NOT BETTER THAN A
      GOOD COHORT STUDY. ⚠️ GRADE assesses evidence QUALITY
      rather than just study design, which is the improvement
⚠️ ⚠️ ABSOLUTE vs RELATIVE RISK — the most consequential
   presentational choice in medicine
   ⚠️ "Reduces risk by 50%" could mean 2% → 1% or 40% → 20%
   ⚠️ ⚠️ RELATIVE risk reduction is stable across baseline risk
      and SOUNDS bigger; ABSOLUTE reduction is what the patient
      actually gets
   ⚠️ ⚠️ NUMBER NEEDED TO TREAT = 1 ÷ absolute risk reduction —
      the most honest single number available, and the one
      least often reported
   ⚠️ NUMBER NEEDED TO HARM is its counterpart and is reported
      even less
⚠️ ⚠️ SURROGATE vs PATIENT-IMPORTANT OUTCOMES  ⚠️ a drug that
   improves a lab value has not been shown to help anyone.
   ⚠️ CAST (§13) is the reference case: the surrogate improved
   and mortality rose
⚠️ ⚠️ THE LIMITS OF EBM, stated fairly  ⚠️ trial populations
   differ from real patients (§21) · averages conceal
   heterogeneity · absence of evidence is not evidence of
   absence · ⚠️ and guidelines aggregate single-disease
   evidence for multimorbid patients (§4)
```

---

## §21. ⚠️ Trial Methodology and Its Pathologies

```
⚠️ WHY RANDOMIZATION WORKS  ⚠️ it balances KNOWN and UNKNOWN
   confounders in expectation. ⚠️ No observational method does
   this, which is the entire argument for the RCT
⚠️ BLINDING prevents differential treatment and assessment ·
   ⚠️ ALLOCATION CONCEALMENT is distinct from blinding and is
   the more commonly failed one
⚠️ ⚠️ INTENTION-TO-TREAT vs PER-PROTOCOL  ⚠️ ITT analyses people
   as randomized regardless of what they took. ⚠️ It preserves
   randomization and gives the more conservative, more honest
   answer — ⚠️ per-protocol analyses reintroduce selection
⚠️ ⚠️ THE PATHOLOGIES, all documented and all common
   ⚠️ PUBLICATION BIAS  ⚠️ positive results are more likely to
      be published, which biases every meta-analysis built on
      the literature. ⚠️ TRIAL REGISTRATION was introduced to
      fix this and compliance remains imperfect
   ⚠️ ⚠️ OUTCOME SWITCHING  ⚠️ changing the primary endpoint
      after seeing results. ⚠️ Comparing registered to published
      protocols repeatedly finds this
   ⚠️ p-HACKING and multiple comparisons · ⚠️ SUBGROUP ANALYSIS
      (⚠️ the astrological-sign subgroup in ISIS-2 is the famous
      demonstration that subgroups find spurious effects)
   ⚠️ ⚠️ COMPOSITE ENDPOINTS  ⚠️ where a difference in the least
      serious component drives an apparently impressive result
   ⚠️ Non-inferiority margins chosen generously · ⚠️ industry
      sponsorship associated with more favourable conclusions ·
      ⚠️ ghostwriting and selective reporting
   ⚠️ ⚠️ EXTERNAL VALIDITY  ⚠️ trial populations are younger,
      healthier and less multimorbid than real patients —
      ⚠️ and pregnant people, children and older adults are
      systematically underrepresented
⚠️ ⚠️ REGRESSION TO THE MEAN AND NATURAL HISTORY explain much
   apparent treatment effect — ⚠️ people seek care when at
   their worst and improve regardless, which is why
   uncontrolled before-after comparison is nearly worthless
   and why placebo controls exist
```

---

## §22. Drug Development and Regulation

**⚠️ The pipeline**: ⚠️ **target identification → hit and lead → preclinical → Phase I
(safety, healthy volunteers usually) → Phase II (efficacy signal, dose) → Phase III
(confirmatory, powered for outcomes) → regulatory review → Phase IV surveillance**
(§12 → `med-pharmacokinetics-pharmacodynamics-and-interactions`).
**⚠️ Attrition is brutal**: ⚠️ **the great majority of compounds entering clinical
development fail, most commonly for lack of efficacy — and the cost of successes therefore
includes the cost of failures, which is the honest part of the pricing argument.**
**⚠️ The regulators**: ⚠️ **FDA, EMA and national agencies, with accelerated and conditional
pathways trading evidentiary certainty for speed.** ⚠️ **The trade is real: faster access
versus more post-approval uncertainty, and confirmatory trials required under accelerated
approval have historically been slow to complete.**
**⚠️ Patents, exclusivity, generics and biosimilars** (§18 → `med-drug-classes-neuro-endocrine-immunology-and-oncology`) — ⚠️ **and the practices around
extending exclusivity are a live policy dispute.**
**⚠️ Pricing** is genuinely contested: ⚠️ **the R&D-cost justification, the counter-argument
about marketing spend and publicly funded basic research, and value-based versus
cost-based frameworks are all serious positions** (see an investment reference for the
market side).

---

## §23. ⚠️ Patient Safety

**⚠️ The founding insight** (*To Err Is Human*): ⚠️ **most harm comes from SYSTEM failures,
not from individual incompetence — and the response should be system redesign rather than
blame.**
**⚠️ The Swiss cheese model** and defence in depth: ⚠️ **harm requires multiple barriers to
fail simultaneously, which is exactly the pattern in a civil engineering reference and a
digital-logic reference.**
**⚠️ Where harm concentrates**: ⚠️ **medication errors, healthcare-associated infection,
diagnostic error (§5 → `med-reading-the-field-physiology-and-clinical-reasoning`), surgical error, handoffs and transitions of care, and
communication failure.**
**⚠️ Interventions with evidence**: ⚠️ **checklists, structured handoff protocols, barcode
medication administration, computerized order entry with decision support (⚠️ which
introduces its own errors, including alert fatigue), and standardization.**
**⚠️ JUST CULTURE** is the governing concept — ⚠️ **distinguishing human error from at-risk
behaviour from recklessness, because a punitive response to honest error destroys the
reporting that safety improvement depends on.**
**⚠️ The honest note**: ⚠️ **frequently cited estimates of deaths from medical error vary
enormously by methodology and the highest figures are contested; the direction — that
preventable harm is substantial — is not.**

---

## §24. ⚠️ Screening

> **⚠️ Where good intentions and bad reasoning most often meet, and §6 → `med-reading-the-field-physiology-and-clinical-reasoning`'s mathematics
> becomes policy.**
```
⚠️ ⚠️ SCREENING IS TESTING PEOPLE WITHOUT SYMPTOMS, so
   pre-test probability is LOW BY DEFINITION — ⚠️ which means
   §6's base rate problem applies maximally
⚠️ THE WILSON-JUNGNER CRITERIA (WHO, and still the standard)
   ⚠️ important health problem · recognizable latent stage ·
   suitable acceptable test · ⚠️ AN ACCEPTED TREATMENT THAT
   WORKS BETTER WHEN STARTED EARLY · facilities available ·
   agreed policy on whom to treat · cost-effective ·
   continuing process
   ⚠️ ⚠️ THE TREATMENT CRITERION IS THE ONE MOST OFTEN IGNORED —
   early detection is only valuable if earlier treatment
   changes the outcome
⚠️ ⚠️ OVERDIAGNOSIS IS THE CENTRAL HARM AND IT IS
   COUNTERINTUITIVE  ⚠️ detecting real disease that would
   never have caused symptoms or death in that person's
   lifetime. ⚠️ The diagnosis is CORRECT; the detection is
   harmful — because it delivers treatment, anxiety and
   sick-role status with no possible benefit
   ⚠️ Thyroid cancer screening in South Korea is the
   most-cited demonstration: incidence rose enormously while
   mortality was unchanged
⚠️ ⚠️ LEAD TIME AND LENGTH BIAS (§19) MAKE SCREENING LOOK
   EFFECTIVE EVEN WHEN IT IS NOT. ⚠️ Only a MORTALITY
   comparison in a randomized trial answers the question
⚠️ ⚠️ THE ASYMMETRY THAT MAKES THIS POLITICALLY HARD  ⚠️ the
   people helped by screening are identifiable and grateful;
   ⚠️ the people harmed by overdiagnosis believe they were
   saved. ⚠️ There is no constituency for stopping a screening
   programme
```

---

## §25. ⚠️ Public Health versus Clinical Medicine

**⚠️ §1 → `med-reading-the-field-physiology-and-clinical-reasoning`'s third organizing idea.** ⚠️ **The great improvements in life expectancy came
predominantly from clean water, sanitation, nutrition, housing, occupational safety and
vaccination — largely before, and independently of, most therapeutic medicine.**
**⚠️ McKeown's thesis** made this argument in a strong form and has been substantially
criticized on detail; ⚠️ **the qualified version — that social and environmental
determinants dominate, with clinical medicine contributing meaningfully but later and less
than assumed — is broadly accepted.**
**⚠️ The prevention paradox** (Rose): ⚠️ **a preventive measure bringing large benefit to a
population often offers little to each participating individual — which explains why
population-level interventions feel unrewarding and why individual advice underperforms
structural change.**
**⚠️ Rose's other insight**: ⚠️ **shifting the whole population distribution slightly
prevents more disease than targeting the high-risk tail, because most cases arise from the
large group at modest risk.**
**⚠️ The social determinants** — ⚠️ **income, education, housing, food security and social
connection — predict health outcomes more strongly than healthcare access does in most
developed settings.**
**⚠️ And the resource observation**: ⚠️ **healthcare spending is concentrated in the final
period of life and in high-technology intervention, while the interventions with the
largest population effect are cheap and unglamorous.**

---

## §26. Ethics

**⚠️ The four principles** (Beauchamp and Childress): ⚠️ **autonomy, beneficence,
non-maleficence, justice — useful as a checklist and criticized for offering no method of
resolution when they conflict, which is exactly when you need one.**
**⚠️ INFORMED CONSENT** requires capacity, disclosure, understanding and voluntariness —
⚠️ **and capacity is decision-specific and can fluctuate, so it is not a global property of
a person.**
**⚠️ Confidentiality** and its limits (⚠️ **harm to others, mandatory reporting, public
health**).
**⚠️ Resource allocation** — ⚠️ **QALYs and their critiques, particularly disability
discrimination concerns; the rule of rescue; and the tension between identified and
statistical lives.**
**⚠️ End-of-life care**: ⚠️ **the distinction between withdrawing treatment and actively
ending life, the doctrine of double effect, advance directives, and palliative care as
active treatment rather than as giving up.**
**⚠️ Research ethics**: ⚠️ **Nuremberg, Helsinki and Belmont exist because of documented
atrocities — Tuskegee, Willowbrook and others — and the resulting mistrust in affected
communities is a real and persisting consequence.**
