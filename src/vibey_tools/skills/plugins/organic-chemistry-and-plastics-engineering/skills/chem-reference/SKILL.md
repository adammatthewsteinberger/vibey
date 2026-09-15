---
name: chem-reference
description: "Use when correcting an organic chemistry or plastics misconception, looking up a Tg, melting point, modulus, density, pKa or processing-temperature figure, finding the books, or needing a quick-reference picker — plus the current state of the global plastics treaty and the EU PFAS restriction. Companion to the other organic chemistry and plastics skills."
---

# Organic Chemistry and Plastics: What's Live, Misconceptions, Numbers, and Books

> **Part 6 of 6** of the *Organic Chemistry and Plastics Engineering* reference (plugin `organic-chemistry-and-plastics-engineering`), covering §27–§32. Sibling skills: `chem-carbon-bonding-functional-groups-and-stereochemistry` (§0–§5), `chem-mechanisms-reactions-characterization-and-synthesis` (§6–§12), `chem-polymers-polymerization-molecular-weight-and-morphology` (§13–§17), `chem-commodity-engineering-plastics-additives-and-processing` (§18–§23), `chem-recycling-bioplastics-and-health-regulation` (§24–§26). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The chemistry is settled. Two regulatory areas are moving. See §27 for the global plastics treaty, and the EU PFAS restriction.

> **⚠️ Two disciplines joined at one hinge: organic chemistry explains what molecules DO,
> and polymer engineering explains what happens when you make them very long.** ⚠️ **Chain
> length changes almost everything — a C₂₀ hydrocarbon is a wax and a C₂₀₀,₀₀₀ one is a
> structural material, with identical chemistry.**
>
> **Complements a manufacturing reference (moulding and processing), a materials/textiles
> reference (fibres and finishing), and a thermodynamics reference (phase behaviour).**
>
> **⚠️ SCOPE NOTE: this is a conceptual map of mechanisms, materials and industrial
> practice. It is not a laboratory manual and contains no procedures.** ⚠️ **Practical
> synthetic work requires trained supervision, proper facilities and hazard assessment —
> organic chemistry involves flammables, toxics, corrosives and exotherms that hurt people
> who improvise.**
>
> **⚠️ GOTCHA** boxes mark where intuition fails and where products actually break.
>
> **The three ideas that organize this document:**
> 1. **⚠️ STRUCTURE DETERMINES PROPERTIES, through mechanism** (§3 → `chem-carbon-bonding-functional-groups-and-stereochemistry`, §6 → `chem-mechanisms-reactions-characterization-and-synthesis`). **Functional
>    groups are behaviour classes, and reaction "rules" are consequences of electron
>    density and sterics rather than facts to memorize.**
> 2. **⚠️ Tg AND MORPHOLOGY GOVERN PLASTIC BEHAVIOUR more than chemistry does** (§16 → `chem-polymers-polymerization-molecular-weight-and-morphology`).
>    **Whether a polymer is rigid, rubbery, tough or brittle at your service temperature
>    follows from where Tg sits and how much crystallinity there is.**
> 3. **⚠️ Most plastic FAILURES are environmental, not mechanical** (§23 → `chem-commodity-engineering-plastics-additives-and-processing`). **Environmental
>    stress cracking, UV, and additive migration destroy far more parts than overload
>    does — and the load that causes ESC is often well below the design stress.**

---

## §27. What's Live — checked August 2026

### 27.1 ⚠️ The global plastics treaty stalled, and is going backwards
**⚠️ Directly relevant to §24 → `chem-recycling-bioplastics-and-health-regulation` and §25 → `chem-recycling-bioplastics-and-health-regulation`, because a binding treaty would have set the frame
for everything downstream.**

- **⚠️ WHAT HAPPENED.** ⚠️ **INC-5 in Busan (November–December 2024) ended without a binding
  agreement, producing only a Chair's text.** ⚠️ **Talks resumed at INC-5.2 in Geneva,
  5–15 August 2025, and collapsed again — states could not agree on limiting plastic
  PRODUCTION, regulating toxic substances, or binding obligations.**
- ⚠️ **Two late drafts focused on voluntary measures were rejected by the ambitious camp,
  and many negotiators concluded "no deal was better than a weak one."**
  ⚠️ **Reporting describes up to 120 countries agreeing on core provisions — phasing out
  harmful products and chemicals, majority decision-making at future COPs — without
  reaching agreement overall.**
- **⚠️ THE STRUCTURAL DIVIDE**: ⚠️ **an "upstream and downstream" majority supporting
  full-lifecycle measures including production caps and chemical regulation, against
  petrostates and allies favouring a waste-management-only scope.**
- **⚠️ Then the process itself broke down.** ⚠️ **The chair resigned in October 2025; a
  one-day INC-5.3 in Geneva on 7 February 2026 did no substantive negotiation and existed
  solely to elect a new chair, Julio Cordano of Chile.**
- **⚠️ CURRENT STATE**: ⚠️ **informal and closed-door consultations through 2026, further
  closed meetings reported for Bangkok in late September 2026, and formal negotiations
  resuming at INC-5.4 reportedly in March 2027.** ⚠️ **A non-negotiated reference text has
  been released; reporting notes civil society was not granted access to the preceding
  talks, and that bridging proposals from countries were not included.**

> **⚠️ GOTCHA — a Nature Comment argues the failure is PROCEDURAL as much as political.**
> ⚠️ **The researchers' specific criticism is that separating negotiations on key issues —
> capping production versus financing waste management — "makes it easy to pit"
> constituencies against each other, and they call for urgent reform of INC procedures.**
> **⚠️ That is a more actionable diagnosis than "petrostates blocked it," and it is why the
> chair election mattered more than a procedural step normally would.**

**⚠️ Scale for context**: ⚠️ **OECD estimates cited put global plastic waste at over
1 billion tonnes in 2025 rising to 1.7 billion by 2060.** ⚠️ **One campaign group notes
ocean plastic pollution increased by 42 million tonnes during the four years of
negotiation.**
**⚠️ Sourcing note: much of the available commentary comes from environmental NGOs and
industry associations with opposed positions; I've anchored the procedural chronology on
IISD, CIEL and C&EN, which report the mechanics rather than advocating an outcome.**

### 27.2 ⚠️ The EU PFAS restriction and the fluoropolymer question
**⚠️ Directly consequential for §19 → `chem-commodity-engineering-plastics-additives-and-processing` and §20 → `chem-commodity-engineering-plastics-additives-and-processing`, and it is the most significant chemicals
regulation currently in progress anywhere.**

- **⚠️ SCOPE.** ⚠️ **A restriction proposal submitted to ECHA on 13 January 2023 by five
  member states — Denmark, Germany, Netherlands, Norway and Sweden — covering around
  14,000 substances across virtually every industrial sector.** ⚠️ **Described as the most
  comprehensive chemical restriction ever proposed under REACH, and the scope — all PFAS,
  all uses — is without precedent.**
- **⚠️ WHERE IT STANDS**: ⚠️ **the 2023 consultation drew over 5,600 scientific and
  technical comments; the proposal was substantially revised and republished in August
  2025, expanding to eight additional sectors.** ⚠️ **RAC adopted its FINAL opinion in
  early March 2026, concluding PFAS pose an EU-wide risk justifying restriction; SEAC
  published a DRAFT opinion and ECHA launched a 60-day consultation on 26 March 2026,
  closing 25 May.** ⚠️ **SEAC's final opinion is expected by end-2026, after which the
  Commission drafts an Annex XVII amendment for the REACH Committee to vote on.**
- **⚠️ THE DEROGATIONS TELL THE STORY.** ⚠️ **The revision increased proposed derogations
  from 26 to 74** — ⚠️ **and the reported durations show how the difficulty is distributed:
  6.5 years for medicine blister packs, 13.5 years for stoppers, syringes, inhalers,
  injection devices, implantable and invasive medical devices, and 23.5 years for plastic
  articles containing recovered material excluding food contact.**
  ⚠️ **A June 2026 consultation on the SEAC draft reportedly drew 3,511 comments from over
  3,200 organizations, with electronics and semiconductors generating the most.**

> **⚠️ GOTCHA — the fluoropolymer argument is the substantive scientific dispute inside
> this, and it matters for §19 → `chem-commodity-engineering-plastics-additives-and-processing`.** ⚠️ **Industry argues that fluoropolymers such as PTFE,
> FEP, PFA, PCTFE and ETFE differ STRUCTURALLY from the small, mobile, bioaccumulative
> PFAS that drive the health concern — they are high-molecular-weight polymers with low
> migration and low environmental release from the article itself.**
> ⚠️ **The counter-argument is lifecycle: RAC's focus reportedly included emissions
> estimation across the fluoropolymer LIFECYCLE, specifically at MANUFACTURE and at the
> WASTE stage — where non-polymeric PFAS processing aids and degradation products are the
> issue rather than the polymer in service.**
> **⚠️ Reported emission limits reflect this: roughly 0.0030% to air, 0.0006% to water and
> 0% to soil for non-polymeric PFAS residues from polymerization aid technology in
> fluoropolymer manufacturing from end-2030.**
> ⚠️ **The proposal reportedly includes a third regulatory option permitting continued
> fluoropolymer use under emission-minimizing conditions — which is the shape a compromise
> would take.**

**⚠️ The engineering reality that regulators are being asked to weigh**: ⚠️ **fluoropolymers
are functionally irreplaceable in many sealing, semiconductor, medical and chemical-handling
applications, and alternatives are frequently not commercially available.** ⚠️ **SEAC has
reportedly stressed that even where derogations are recommended they should be seen as
"necessary but not necessarily sufficient," with further exemptions possibly needed given
data gaps.** ⚠️ **The Commission's reported framing is critical uses permitted under strict
conditions until acceptable substitutes exist.**
**⚠️ Sourcing note: my sources here are predominantly law firms advising affected clients
and fluoropolymer industry bodies, both of which have positions.** ⚠️ **The procedural facts
(dates, committee steps, consultation counts) are consistent across all of them and traceable
to ECHA; the framing of the fluoropolymer carve-out is contested and I've given both sides
rather than adjudicating.**

---

## §28. Misconceptions

| Misconception | Correction |
|---|---|
| Isomers are basically the same compound | ⚠️ **Fuel, drug and poison can share a formula** (§1 → `chem-carbon-bonding-functional-groups-and-stereochemistry`) |
| Enantiomers are chemically identical | ⚠️ **Biology is chiral. Thalidomide** (§4 → `chem-carbon-bonding-functional-groups-and-stereochemistry`) |
| Selling the safe enantiomer solves it | ⚠️ **They interconverted in the body** (§4 → `chem-carbon-bonding-functional-groups-and-stereochemistry`) |
| Reaction rules must be memorized | ⚠️ **They follow from electron density and sterics** (§6 → `chem-mechanisms-reactions-characterization-and-synthesis`) |
| Markovnikov is an arbitrary rule | ⚠️ **A consequence of carbocation stability** (§7 → `chem-mechanisms-reactions-characterization-and-synthesis`) |
| Catalysts shift the equilibrium | ⚠️ **They change rate, both directions equally** (§9 → `chem-mechanisms-reactions-characterization-and-synthesis`) |
| Yield of 90% per step is good | ⚠️ **Ten steps gives ~35%. Go convergent** (§11 → `chem-mechanisms-reactions-characterization-and-synthesis`) |
| Amides are basic like amines | ⚠️ **The lone pair is delocalized. That's why nylon is stable** (§3 → `chem-carbon-bonding-functional-groups-and-stereochemistry`) |
| Tacticity is a detail | ⚠️ **Isotactic PP is a plastic; atactic PP is goo** (§13 → `chem-polymers-polymerization-molecular-weight-and-morphology`) |
| A polymer has a molecular weight | ⚠️ **It has a distribution** (§15 → `chem-polymers-polymerization-molecular-weight-and-morphology`) |
| Tg is a melting point | ⚠️ **It's a mobility transition. Amorphous polymers have no Tm** (§16 → `chem-polymers-polymerization-molecular-weight-and-morphology`) |
| Higher molecular weight is always better | ⚠️ **Melt viscosity rises ~MW³·⁴. There's an optimum** (§15 → `chem-polymers-polymerization-molecular-weight-and-morphology`) |
| A plastic's properties come from the resin | ⚠️ **Cooling rate changes crystallinity and everything with it** (§16 → `chem-polymers-polymerization-molecular-weight-and-morphology`) |
| Datasheet tensile strength is the design value | ⚠️ **Polymers creep. Use creep data** (§17 → `chem-polymers-polymerization-molecular-weight-and-morphology`) |
| Plastic parts fail from overload | ⚠️ **Usually ESC, UV or hydrolysis** (§23 → `chem-commodity-engineering-plastics-additives-and-processing`) |
| A harmless solvent is safe with any plastic | ⚠️ **ESC cracks under stress at low exposure** (§23 → `chem-commodity-engineering-plastics-additives-and-processing`) |
| Nylon parts are dimensionally stable | ⚠️ **They absorb water and move** (§19 → `chem-commodity-engineering-plastics-additives-and-processing`) |
| PET can be moulded as received | ⚠️ **Dry it or you hydrolyse the chain** (§18 → `chem-commodity-engineering-plastics-additives-and-processing`, §22 → `chem-commodity-engineering-plastics-additives-and-processing`) |
| The chasing arrows means recyclable | ⚠️ **It's an identification code** (§24 → `chem-recycling-bioplastics-and-health-regulation`) |
| Recycled plastic equals virgin plastic | ⚠️ **Each heat cycle cuts molecular weight** (§22 → `chem-commodity-engineering-plastics-additives-and-processing`, §24 → `chem-recycling-bioplastics-and-health-regulation`) |
| Chemical recycling solves plastic waste | ⚠️ **Ask what fraction becomes new POLYMER** (§24 → `chem-recycling-bioplastics-and-health-regulation`) |
| Bio-based means biodegradable | ⚠️ **Orthogonal. Bio-PE is neither-nor** (§25 → `chem-recycling-bioplastics-and-health-regulation`) |
| Compostable means it'll break down anywhere | ⚠️ **PLA needs industrial composting** (§25 → `chem-recycling-bioplastics-and-health-regulation`) |
| BPA-free means safe | ⚠️ **Some substitutes are close analogues with less data** (§26 → `chem-recycling-bioplastics-and-health-regulation`) |
| The plastics treaty was agreed | ⚠️ **Collapsed twice; formal talks reportedly resume 2027** (§27.1) |
| PFAS restriction is a done deal | ⚠️ **SEAC final opinion expected end-2026, then legislation** (§27.2) |
| Fluoropolymers are obviously the same as other PFAS | ⚠️ **Genuinely contested — the dispute is lifecycle emissions** (§27.2) |

---

## §29. Numbers

```
⚠️ sp³ ~109.5° · sp² ~120° · sp 180°
⚠️ Ten steps at 90% yield  ⚠️ ≈35% overall
⚠️ Step-growth  ⚠️ needs >99% conversion for useful MW (Carothers)
⚠️ Melt viscosity  ⚠️ ~MW³·⁴ above entanglement threshold
⚠️ Dispersity Mw/Mn  ⚠️ ~1.0 anionic/controlled · ~2 step-growth
⚠️ PS Tg  ~100 °C (glassy at room temperature — hence brittle)
⚠️ PP Tg  ⚠️ near or above 0 °C — embrittles in cold
⚠️ PFAS restriction scope  ⚠️ ~14,000 substances, all sectors
⚠️ PFAS derogations  ⚠️ 26 → 74 in the 2025 revision
⚠️ PFAS consultations  ⚠️ 5,600+ comments (2023) · 3,511 (2026)
⚠️ Fluoropolymer manufacturing emission limits (reported, from end-2030)
   ⚠️ 0.0030% air · 0.0006% water · 0% soil (non-polymeric residues)
⚠️ PFAS timeline  ⚠️ RAC final Mar 2026 · SEAC final expected end-2026
⚠️ Plastics treaty  ⚠️ INC-5.2 collapsed Aug 2025 · INC-5.3 Feb 2026
                    (chair election only) · ⚠️ INC-5.4 reported Mar 2027
⚠️ Global plastic waste  ⚠️ >1 bn tonnes (2025) → 1.7 bn (2060), OECD
```

---

## §30. Books

| Author | Work | Why |
|---|---|---|
| **Clayden, Greeves & Warren** | ***Organic Chemistry*** | ⚠️ **The best organic textbook written. Mechanism-first** |
| **Warren & Wyatt** | *Organic Synthesis: The Disconnection Approach* | ⚠️ **§11 → `chem-mechanisms-reactions-characterization-and-synthesis`, retrosynthesis taught properly** |
| **Anslyn & Dougherty** | *Modern Physical Organic Chemistry* | The theory underneath §6 → `chem-mechanisms-reactions-characterization-and-synthesis` |
| **Young & Lovell** | ***Introduction to Polymers*** | ⚠️ **The standard polymer text** |
| **Painter & Coleman** | *Fundamentals of Polymer Science* | Readable and rigorous |
| **Osswald & Menges** | *Materials Science of Polymers for Engineers* | ⚠️ **§16–§17 → `chem-polymers-polymerization-molecular-weight-and-morphology`, engineering-oriented** |
| **Ezrin** | ***Plastics Failure Guide*** | ⚠️ **§23 → `chem-commodity-engineering-plastics-additives-and-processing`. Case-based and genuinely useful** |
| **Rosato** | *Injection Molding Handbook* | §22 → `chem-commodity-engineering-plastics-additives-and-processing` |
| **Anastas & Warner** | *Green Chemistry* | §12 → `chem-mechanisms-reactions-characterization-and-synthesis` |
| **ECHA / REACH documentation** | — | ⚠️ **§27.2, primary** |
| **IISD Earth Negotiations Bulletin** | — | ⚠️ **§27.1 — reports mechanics, not advocacy** |

---

## §31. Quick Reference

### 31.1 Picker
| Question | Where |
|---|---|
| Why does this reaction go that way? | ⚠️ **Track electron density and sterics** (§6 → `chem-mechanisms-reactions-characterization-and-synthesis`) |
| Which proton comes off? | ⚠️ **pKa, via conjugate base stability** (§5 → `chem-carbon-bonding-functional-groups-and-stereochemistry`) |
| Does stereochemistry matter here? | ⚠️ **If biology touches it, yes** (§4 → `chem-carbon-bonding-functional-groups-and-stereochemistry`) |
| Why is my part brittle in winter? | ⚠️ **You crossed Tg** (§16 → `chem-polymers-polymerization-molecular-weight-and-morphology`) |
| Part cracked with no obvious load | ⚠️ **ESC — check fluid contact and residual stress** (§23 → `chem-commodity-engineering-plastics-additives-and-processing`) |
| Part is weak with no visible defect | ⚠️ **Was the resin dried?** (§22 → `chem-commodity-engineering-plastics-additives-and-processing`) |
| Same resin, different parts, different behaviour | ⚠️ **Cooling rate changed crystallinity** (§16 → `chem-polymers-polymerization-molecular-weight-and-morphology`) |
| Nylon part changed dimensions | ⚠️ **Moisture absorption** (§19 → `chem-commodity-engineering-plastics-additives-and-processing`) |
| Snap-fit lost its grip | ⚠️ **Stress relaxation** (§17 → `chem-polymers-polymerization-molecular-weight-and-morphology`) |
| Old vinyl went stiff | ⚠️ **Plasticizer migrated out** (§20 → `chem-commodity-engineering-plastics-additives-and-processing`) |
| Can we use recycled content? | ⚠️ **Depends on stream, MW loss and food contact** (§24 → `chem-recycling-bioplastics-and-health-regulation`) |
| Is compostable plastic better? | ⚠️ **Only if the facility exists and accepts it** (§25 → `chem-recycling-bioplastics-and-health-regulation`) |
| Can we keep using PTFE? | ⚠️ **Watch §27.2 — derogation-dependent** |

### 31.2 Plastic part design checks
- [ ] ⚠️ **Tg relative to the LOWEST and HIGHEST service temperature** (§16 → `chem-polymers-polymerization-molecular-weight-and-morphology`)
- [ ] ⚠️ **Creep data at service temperature and duration, not tensile strength** (§17 → `chem-polymers-polymerization-molecular-weight-and-morphology`)
- [ ] ⚠️ **Every fluid the part will contact, checked for ESC** (§23 → `chem-commodity-engineering-plastics-additives-and-processing`)
- [ ] UV exposure and stabilization (§20 → `chem-commodity-engineering-plastics-additives-and-processing`, §23 → `chem-commodity-engineering-plastics-additives-and-processing`)
- [ ] ⚠️ **Moisture absorption and dimensional consequences** (§19 → `chem-commodity-engineering-plastics-additives-and-processing`)
- [ ] Residual stress minimized — gate, cooling, annealing (§22 → `chem-commodity-engineering-plastics-additives-and-processing`, §23 → `chem-commodity-engineering-plastics-additives-and-processing`)
- [ ] ⚠️ **Anisotropy from fibre orientation and flow direction accounted for** (§20 → `chem-commodity-engineering-plastics-additives-and-processing`)
- [ ] ⚠️ **Drying specified for hygroscopic resins** (§22 → `chem-commodity-engineering-plastics-additives-and-processing`)
- [ ] Additive migration acceptable for the contact application (§20 → `chem-commodity-engineering-plastics-additives-and-processing`, §26 → `chem-recycling-bioplastics-and-health-regulation`)
- [ ] ⚠️ **Single-polymer construction where end-of-life matters** (§24 → `chem-recycling-bioplastics-and-health-regulation`)
- [ ] ⚠️ **Regulatory exposure over product life — PFAS, food contact** (§26 → `chem-recycling-bioplastics-and-health-regulation`, §27.2)

---

## §32. Method

**§1–§26 → `chem-carbon-bonding-functional-groups-and-stereochemistry`, `chem-mechanisms-reactions-characterization-and-synthesis`, `chem-polymers-polymerization-molecular-weight-and-morphology`, `chem-commodity-engineering-plastics-additives-and-processing`, `chem-recycling-bioplastics-and-health-regulation` rests on settled chemistry and long-established polymer engineering** — **bonding
and mechanism, stereochemistry, the polymerization families, Tg and morphology,
viscoelasticity, and the degradation mechanisms.** ⚠️ **None of it needed verification;
Carothers' equation and the glass transition are not new.**

**Two searches were run in August 2026**, on **the global plastics treaty** and **the EU
PFAS restriction** — ⚠️ **both chosen because they are the regulatory questions that will
determine what materials engineers are allowed to specify, and both moved substantially in
the last year.**

**Confidence.** **High** in §16 → `chem-polymers-polymerization-molecular-weight-and-morphology` and §23 → `chem-commodity-engineering-plastics-additives-and-processing`, which are the sections I'd most want read.
⚠️ **Tg and crystallinity explain more about how a plastic part will behave than its
chemical identity does — including the fact that the same resin gives different properties
depending on how it was cooled.** ⚠️ **§23 → `chem-commodity-engineering-plastics-additives-and-processing`'s environmental stress cracking is the single
most under-appreciated failure mode in plastics engineering: a part under residual stress
from moulding cracks in contact with a fluid that would be harmless alone, at stresses far
below its rated strength.** **§4 → `chem-carbon-bonding-functional-groups-and-stereochemistry` is the close third, and the thalidomide detail that the
enantiomers interconverted is the part usually omitted from the moral.**

**High** on §27.1's chronology, which is consistent across IISD, CIEL, C&EN and multiple
outlets: ⚠️ **Busan without agreement, INC-5.2's collapse in August 2025, the chair's
resignation in October, and INC-5.3 on 7 February 2026 as a one-day chair election won by
Julio Cordano.** ⚠️ **The Bangkok meeting and the March 2027 INC-5.4 date come from a single
recent report and are marked as reported.** ⚠️ **I've flagged that most commentary here is
from parties with positions and anchored on the process-reporting sources.**

**High** on §27.2's procedural facts, which trace to ECHA and are reported identically by
many law firms: ⚠️ **the January 2023 submission by five member states, ~14,000 substances,
5,600+ comments, the August 2025 revision, RAC's final opinion in March 2026, the SEAC
consultation from 26 March to 25 May, and a final opinion expected end-2026.**
⚠️ **The derogation durations, emission limits and the 26→74 count come from law-firm and
industry summaries rather than the ECHA documents directly, and I've marked them reported.**
**⚠️ The fluoropolymer question is the one place I deliberately declined to adjudicate: the
structural argument (high-MW polymers with low migration) and the lifecycle counter-argument
(manufacturing and waste-stage emissions of non-polymeric species) are both substantive, my
sources on each side are interested parties, and the regulators themselves have not
finished.**
