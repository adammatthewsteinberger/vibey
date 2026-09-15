---
name: thermo-reference
description: "Use when checking a thermodynamics or fluids anti-pattern or misconception, looking up a property, dimensionless group, friction factor or heat transfer coefficient figure, finding the books, or needing a quick-reference picker — plus the current state of CFD and turbulence modelling and high-density thermal management. Companion to the other thermodynamics and fluid mechanics skills."
---

# Thermodynamics and Fluid Mechanics: What's Live, Anti-Patterns, Misconceptions, Numbers, and Books

> **Part 6 of 6** of the *Thermodynamics and Fluid Mechanics* reference (plugin `thermodynamics-fluid-mechanics`), covering §29–§35. Sibling skills: `thermo-laws-entropy-property-relations-and-phase-behaviour` (§0–§7), `thermo-cycles-exergy-combustion-and-psychrometrics` (§8–§12), `thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes` (§13–§18), `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery` (§19–§24), `thermo-heat-transfer-conduction-convection-radiation-and-exchangers` (§25–§28). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The laws are permanent — Carnot 1824, Navier-Stokes 1845. Two areas of practice moved. See §29 for CFD and turbulence modelling, and high-density thermal management.

> **⚠️ These are one subject, not two.** **Both are continuum theories built on the same
> conservation laws applied to a control volume; heat transfer is the third face of the
> same object.** **Complements a fundamental-physics reference (statistical mechanics
> underneath), an aerospace reference (external aerodynamics), and a power-engineering
> reference (cycles at plant scale).**
>
> **⚠️ Unusual epistemic status for this series: this content is as close to permanent as
> engineering knowledge gets.** ⚠️ **The Second Law has survived every attempt to violate
> it; Navier-Stokes dates to the 1840s.** **What changes is COMPUTATIONAL PRACTICE and
> APPLICATION — which is what §29 covers.**
>
> **⚠️ GOTCHA** boxes mark the classic misconceptions, and the places where a correct
> formula applied outside its assumptions gives confidently wrong answers.
>
> **The three ideas that organize this document:**
> 1. **⚠️ Define the control volume first.** **Most thermo and fluids errors are
>    bookkeeping errors — the wrong boundary, or a term crossing it unaccounted**
>    (§2 → `thermo-laws-entropy-property-relations-and-phase-behaviour`, §16 → `thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes`).
> 2. **⚠️ The Second Law is about DIRECTION and about QUALITY of energy** (§4 → `thermo-laws-entropy-property-relations-and-phase-behaviour`). **The
>    First Law says you can't win; the Second says you can't break even — and the Second
>    is where all the engineering lives.**
> 3. **⚠️ Dimensionless groups are the most powerful tool in the subject** (§19 → `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery`). **They
>    tell you which physics dominates before you compute anything, and they let a model
>    predict a full-scale ship.**

---

## §29. What's Live — verified August 2026

### 29.1 ⚠️ CFD: GPUs moved the boundary, ML has not replaced the models
**⚠️ The physics didn't change; what you can afford to compute did.**

- **⚠️ RANS remains dominant in industry, and the sources are blunt about why.**
  ⚠️ **Scale-resolving methods remain "computationally infeasible for most industrial CFD
  practitioners," and RANS is projected to stay the most common approach for the near
  future.** **The reason is §22 → `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery`'s Re³ scaling — DNS at industrial Reynolds numbers is
  described as out of reach "for decades."**
- **⚠️ GPU acceleration is the real, deployed change.** **OpenFOAM with GPU backends,
  Ansys Fluent GPU acceleration and GPU-native solvers are reported achieving
  10–100× speedups over CPU-only runs**, ⚠️ **progressively making LES accessible for a
  broader range of industrial problems.** **A NASA seminar description put it as GPU
  hardware having "initiated a transition from classical RANS-based methods to
  Scale-Resolving Simulation approaches" in external aerodynamics.**
- **⚠️ ML in turbulence modelling is genuinely promising and genuinely not there yet.**
  ⚠️ **One 2026 assessment: hybrid physics-ML turbulence models are "still largely in the
  research phase" and likely to enter mainstream industrial tools "within the next 5–10
  years," with the most promising near-term application being data-driven RANS correction
  for separated flows — where classical RANS is known to be systematically wrong.**
- **⚠️ The theoretical obstacle is real, not just engineering lag.** **Research reports
  non-unique ML mappings in data-driven RANS models, difficulty achieving robust
  generalization, and accumulated industrial evidence suggesting "a universal, simple, and
  local turbulence model may be difficult to achieve."**

> **⚠️ GOTCHA — read "1000× faster" claims carefully, and note what they're measuring.**
> ⚠️ **Headline speedups typically describe SURROGATE MODELS trained on prior CFD results,
> not solvers.** **A surrogate interpolates within its training distribution; it does not
> solve Navier-Stokes, and it has no reliable error bound outside that distribution.**
> **⚠️ That's genuinely useful for design-space exploration and dangerous as a
> verification tool.** ⚠️ **Also note where the credible deployment actually is —
> astronomy adaptive optics and long-range imaging, per one 2026 survey — rather than in
> certified aerodynamic design.**

**⚠️ The practitioner summary**: ⚠️ **use RANS for design iteration, know its failure modes
(separation, strong curvature, rotation — §22 → `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery`'s Boussinesq problem), reach for
scale-resolving methods where those failures matter and GPUs make it affordable, and treat
ML surrogates as fast interpolators rather than as solvers.** **⚠️ Validation against
experiment did not become less necessary.**

### 29.2 ⚠️ High-density thermal management: air hit a wall
**⚠️ The most consequential applied heat-transfer problem right now, and it is §26 → `thermo-heat-transfer-conduction-convection-radiation-and-exchangers`'s
h-magnitude table becoming a business constraint.**

- **⚠️ The physical driver: liquid's volumetric heat transfer capacity is roughly
  3,000–4,000× that of air.** ⚠️ **Air cooling reaches physical limits reported around
  25–50 kW per rack depending on layout** — **and modern accelerator racks blow past it.**
  **An NVIDIA GB200 NVL72 is reported drawing roughly 120 kW, with GB300 configurations
  pushing 135–200 kW.** ⚠️ **Chip TDPs exceeding 1,000 W today are projected toward
  4,000 W by 2029.**
- **⚠️ The threshold framework that recurs across sources**: **below ~20–30 kW/rack air
  with rear-door heat exchangers remains defensible; ⚠️ 20–50 kW is the direct-to-chip
  zone (ASHRAE TC 9.9 recommends DLC above 20 kW, and one source notes this is "grounded
  in heat flux physics, not vendor preference"); above ~50 kW liquid is mandatory; above
  ~100 kW immersion enters.**
- **⚠️ Direct-to-chip cold plates dominate** — **reported at roughly 65% of the liquid
  cooling market in 2026, and expected to remain dominant through at least 2028 because
  they are mature, retrofittable, and what the hardware vendors specify.**
  ⚠️ **Immersion achieves the best PUE (reported 1.02–1.05) and carries real
  compatibility problems: elastomer seals degrading, thermal interface materials
  dissolving, conformal coatings reacting.**

> **⚠️ GOTCHA — the most thermodynamically interesting development is the warm-water
> move, and it's a §4 → `thermo-laws-entropy-property-relations-and-phase-behaviour` argument.** ⚠️ **NVIDIA's Vera Rubin is specified for single-phase
> direct liquid cooling at a 45°C supply temperature** — **high enough that data centres
> can reject heat through DRY COOLERS using ambient air rather than mechanical chillers.**
> **⚠️ Chillers are among the largest energy draws in a liquid-cooled facility, so raising
> the coolant temperature eliminates an entire refrigeration cycle.** ⚠️ **This is
> exactly §10 → `thermo-cycles-exergy-combustion-and-psychrometrics`'s exergy lesson in practice: don't spend work moving heat down a temperature
> gradient you didn't need to create.**

**⚠️ Adoption figures vary widely by source and should be treated as directional** —
**one puts liquid cooling in new builds at ~22% in 2026, another projects ~37% penetration
against ~3% in 2021.** ⚠️ **Average rack density was reported jumping 69% year-over-year to
about 27 kW, with AI training racks as the outliers pulling the average up.**
**⚠️ And the honest closing note from one industry source, which is a systems point rather
than a chip point**: ⚠️ **"The chip-level thermal problem is solved. The building-level and
community-level thermal problems are just getting started"** — **heat rejection capacity,
water availability and permitting are the actual bottlenecks.** **⚠️ Two-phase immersion
additionally faces fluid-availability and PFAS regulatory risk.**

---

## §30. Anti-Patterns

```
⚠️ Applying Bernoulli through a pump, across streamlines, or in separated
   or viscous-dominated flow (§16)
⚠️ Using gauge pressure in an absolute-pressure formula (§14)
⚠️ Ideal gas law near saturation or at high pressure (§6)
⚠️ Celsius in Carnot efficiency or Stefan-Boltzmann (§4, §27)
⚠️ Confusing Darcy and Fanning friction factors — a factor of 4 (§20)
⚠️ Confusing HHV and LHV when comparing efficiencies (§11)
⚠️ Lumped capacitance without checking Bi < 0.1 (§25)
⚠️ Ignoring minor losses in short piping runs (§20)
⚠️ Ignoring contact resistance in electronics cooling (§25)
⚠️ Sizing a cooling system on sensible load only in a humid climate (§12)
⚠️ Treating h as a fluid property (§26)
⚠️ Running a pump without checking NPSH available (§24)
⚠️ Trusting a RANS separation prediction without validation (§22, §29.1)
⚠️ Treating an ML surrogate as a solver (§29.1)
⚠️ First Law efficiency as the sole metric — it hides exergy destruction (§10)
⚠️ Not drawing the control volume (§15)
```

---

## §31. Misconceptions

| Misconception | Correction |
|---|---|
| A hot system "contains heat" | ⚠️ **It contains internal energy. Heat is energy in transit** (§1 → `thermo-laws-entropy-property-relations-and-phase-behaviour`) |
| Temperature measures thermal energy | ⚠️ **Intensive vs extensive. A spark vs a bathtub** (§2 → `thermo-laws-entropy-property-relations-and-phase-behaviour`) |
| Entropy is disorder | ⚠️ **Multiplicity / missing information. Disorder fails on cases** (§4 → `thermo-laws-entropy-property-relations-and-phase-behaviour`) |
| Entropy can never decrease | ⚠️ **Locally yes — that's a fridge. Total can't** (§4 → `thermo-laws-entropy-property-relations-and-phase-behaviour`) |
| Better engineering can beat Carnot | ⚠️ **It's set by temperatures alone** (§4 → `thermo-laws-entropy-property-relations-and-phase-behaviour`) |
| COP > 1 violates energy conservation | ⚠️ **You're moving heat, not creating it** (§9 → `thermo-cycles-exergy-combustion-and-psychrometrics`) |
| Efficiency over 100% is impossible | ⚠️ **Condensing boilers, quoted on LHV** (§11 → `thermo-cycles-exergy-combustion-and-psychrometrics`) |
| Enthalpy is a form of energy | ⚠️ **A bookkeeping bundle: u + Pv** (§3 → `thermo-laws-entropy-property-relations-and-phase-behaviour`) |
| Air moves faster over a wing because it must rejoin | ⚠️ **Equal transit time is FALSE** (§16 → `thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes`) |
| Bernoulli explains lift, Newton is the rival | ⚠️ **Both describe the same flow turning** (§16 → `thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes`) |
| Bernoulli applies generally | ⚠️ **Steady, inviscid, incompressible, along a streamline** (§16 → `thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes`) |
| Smooth surfaces always have less drag | ⚠️ **Dimples delay separation; drag crisis** (§18 → `thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes`, §21 → `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery`) |
| Turbulent boundary layers are bad | ⚠️ **They resist separation better** (§18 → `thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes`) |
| Suction pulls fluid | ⚠️ **Ambient pressure pushes. Nothing pulls** (§14 → `thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes`) |
| Insulation always reduces heat loss | ⚠️ **Below critical radius it can increase it** (§25 → `thermo-heat-transfer-conduction-convection-radiation-and-exchangers`) |
| Space is cold, so spacecraft need heating | ⚠️ **Vacuum insulates; rejecting heat is the problem** (§27 → `thermo-heat-transfer-conduction-convection-radiation-and-exchangers`) |
| h is a property of the fluid | ⚠️ **It depends on geometry and flow. That's the problem** (§26 → `thermo-heat-transfer-conduction-convection-radiation-and-exchangers`) |
| More heat flux always means more boiling | ⚠️ **Past CHF the surface burns out** (§28 → `thermo-heat-transfer-conduction-convection-radiation-and-exchangers`) |
| A droplet evaporates fastest on the hottest plate | ⚠️ **Leidenfrost — film boiling insulates** (§28 → `thermo-heat-transfer-conduction-convection-radiation-and-exchangers`) |
| Tacoma Narrows was resonance from vortex shedding | ⚠️ **Better explained as aeroelastic flutter** (§21 → `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery`) |
| Navier-Stokes is solved, we just need computers | ⚠️ **Existence/smoothness is an open problem** (§17 → `thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes`) |
| DNS will replace turbulence models soon | ⚠️ **Work scales ~Re³. Decades away** (§22 → `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery`, §29.1) |
| ML has replaced turbulence modelling | ⚠️ **Still research-phase; 5–10 years to mainstream** (§29.1) |
| "1000× faster CFD" means faster solvers | ⚠️ **Usually surrogates, valid only in-distribution** (§29.1) |

---

## §32. Numbers

```
⚠️ σ (Stefan-Boltzmann)  5.67×10⁻⁸ W/m²K⁴     ⚠️ R_universal  8.314 J/mol·K
⚠️ Water: c_p ≈ 4.18 kJ/kg·K · h_fg ≈ 2257 kJ/kg at 100°C (⚠️ ~540× c_p·1K)
Air: c_p ≈ 1.005 kJ/kg·K · γ = 1.4 · ν ≈ 1.5×10⁻⁵ m²/s at 20°C
⚠️ Speed of sound in air at 20°C  ~343 m/s
TRANSITION  ⚠️ pipe Re ≈ 2300–4000 · flat plate Re_x ≈ 5×10⁵
⚠️ Drag crisis (sphere)  Re ≈ 3×10⁵      ⚠️ Strouhal (cylinder)  ≈ 0.2
⚠️ Bi < 0.1 for lumped capacitance      ⚠️ Ma > 0.3 compressibility matters
⚠️ Kolmogorov energy spectrum  E(k) ∝ k^(−5/3)
⚠️ DNS cost  grid ~Re^(9/4), work ~Re³
h (W/m²K)  ⚠️ natural convection air 2–25 · forced air 25–250 ·
   forced water 50–20,000 · ⚠️ boiling/condensation 2,500–100,000
⚠️ Liquid vs air volumetric heat capacity  ~3,000–4,000×
⚠️ Air cooling rack limit  ~25–50 kW      ⚠️ GB200 NVL72  ~120 kW
⚠️ Vera Rubin coolant supply  45°C (enables chiller-free dry coolers)
⚠️ Immersion PUE  reported 1.02–1.05
```

---

## §33. Books

| Author | Work | Why |
|---|---|---|
| **Çengel & Boles** | ***Thermodynamics: An Engineering Approach*** | ⚠️ **The standard, and readable** |
| **Moran & Shapiro** | *Fundamentals of Engineering Thermodynamics* | The other standard; stronger on exergy |
| **White** | ***Fluid Mechanics*** | ⚠️ **The standard fluids text** |
| **Munson et al.** | *Fundamentals of Fluid Mechanics* | Good problem sets |
| **Incropera & DeWitt** | ***Fundamentals of Heat and Mass Transfer*** | ⚠️ **THE heat transfer reference** |
| **Anderson** | *Modern Compressible Flow* / *Fundamentals of Aerodynamics* | ⚠️ **§23 → `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery`, and historically rich** |
| **Pope** | ***Turbulent Flows*** | ⚠️ **§22 → `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery`. The serious treatment** |
| **Batchelor** | *An Introduction to Fluid Dynamics* | Rigorous, classic |
| **Tennekes & Lumley** | *A First Course in Turbulence* | ⚠️ **Short and deep** |
| **Bejan** | *Advanced Engineering Thermodynamics* | ⚠️ **§10 → `thermo-cycles-exergy-combustion-and-psychrometrics`. Exergy done properly** |
| **Ferziger & Perić** | *Computational Methods for Fluid Dynamics* | §29.1 |
| **Vincenti & Kruger** | *Introduction to Physical Gas Dynamics* | The statistical bridge |

**⚠️ Also**: **NIST REFPROP and the NIST Chemistry WebBook for real property data
(⚠️ do not use ideal-gas approximations where real property data exists); the NASA
Turbulence Modeling Resource for verification cases; ⚠️ the Moody chart and steam tables,
which you should be able to read fluently.**

---

## §34. Quick Reference

### 34.1 Picker
| Question | Where |
|---|---|
| Where do I start any problem? | ⚠️ **Draw the control volume** (§15 → `thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes`) |
| Does viscosity matter here? | ⚠️ **Reynolds number** (§19 → `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery`) |
| Does compressibility matter? | ⚠️ **Ma > 0.3** (§19 → `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery`, §23 → `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery`) |
| Can I use lumped capacitance? | ⚠️ **Bi < 0.1** (§19 → `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery`, §25 → `thermo-heat-transfer-conduction-convection-radiation-and-exchangers`) |
| Can I use Bernoulli? | ⚠️ **Steady, inviscid, incompressible, one streamline** (§16 → `thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes`) |
| Best possible cycle efficiency? | ⚠️ **1 − T_C/T_H, absolute temperatures** (§4 → `thermo-laws-entropy-property-relations-and-phase-behaviour`) |
| Where are my real losses? | ⚠️ **Exergy analysis, not First Law efficiency** (§10 → `thermo-cycles-exergy-combustion-and-psychrometrics`) |
| Why is my heat exchanger underperforming? | ⚠️ **Fouling; check flow arrangement** (§28 → `thermo-heat-transfer-conduction-convection-radiation-and-exchangers`) |
| Pump is noisy and eroding | ⚠️ **Cavitation. Check NPSH available** (§24 → `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery`) |
| Flow separates / stalls | ⚠️ **Adverse pressure gradient; consider tripping it turbulent** (§18 → `thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes`) |
| Heat won't leave a small hot chip | ⚠️ **Contact resistance, then h magnitude** (§25 → `thermo-heat-transfer-conduction-convection-radiation-and-exchangers`, §26 → `thermo-heat-transfer-conduction-convection-radiation-and-exchangers`) |
| Air cooling isn't enough | ⚠️ **§29.2's thresholds** |
| Which turbulence model? | ⚠️ **RANS to iterate; scale-resolving where it separates** (§22 → `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery`, §29.1) |
| Evaporative cooling not working | ⚠️ **Wet-bulb is the floor** (§12 → `thermo-cycles-exergy-combustion-and-psychrometrics`) |

### 34.2 Before trusting a result
- [ ] ⚠️ **Control volume drawn; every crossing accounted** (§15 → `thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes`)
- [ ] ⚠️ **Absolute temperatures and pressures where required** (§4 → `thermo-laws-entropy-property-relations-and-phase-behaviour`, §14 → `thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes`)
- [ ] Assumptions of every formula checked against the actual regime (§16 → `thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes`)
- [ ] ⚠️ **Dimensionless groups computed BEFORE the detailed calculation** (§19 → `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery`)
- [ ] Units consistent; Darcy vs Fanning, HHV vs LHV resolved (§20 → `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery`, §11 → `thermo-cycles-exergy-combustion-and-psychrometrics`)
- [ ] ⚠️ **Second Law sanity check — is entropy generation ≥ 0?** (§4 → `thermo-laws-entropy-property-relations-and-phase-behaviour`)
- [ ] ⚠️ **Order-of-magnitude estimate agrees with the computed answer**
- [ ] ⚠️ **CFD validated against experiment, not just converged** (§29.1)

---

## §35. Method

**§1–§28 → `thermo-laws-entropy-property-relations-and-phase-behaviour`, `thermo-cycles-exergy-combustion-and-psychrometrics`, `thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes`, `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery`, `thermo-heat-transfer-conduction-convection-radiation-and-exchangers` is settled science and engineering** — **the laws, property relations, cycles,
Navier-Stokes, boundary layer theory, the dimensionless groups, and the three modes of
heat transfer** — sourced from §33. ⚠️ **This is the most stable content in this series;
Carnot published in 1824 and none of it needed verification.**

**Two searches were run in August 2026**, on **CFD and turbulence modelling practice** and
**high-density thermal management** — ⚠️ **deliberately targeting PRACTICE rather than
theory, because the theory doesn't move and the practice genuinely has.**

**Confidence.** **High** throughout §1–§28 → `thermo-laws-entropy-property-relations-and-phase-behaviour`, `thermo-cycles-exergy-combustion-and-psychrometrics`, `thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes`, `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery`, `thermo-heat-transfer-conduction-convection-radiation-and-exchangers`. ⚠️ **The sections I'd most want read are §4 → `thermo-laws-entropy-property-relations-and-phase-behaviour`,
§10 → `thermo-cycles-exergy-combustion-and-psychrometrics`, §16 → `thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes` and §19 → `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery`.** **§10 → `thermo-cycles-exergy-combustion-and-psychrometrics` (exergy) because it is under-taught and it changes where you look
for losses; §16 → `thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes` because the equal-transit-time lift myth is still in circulation and in
some textbooks; §19 → `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery` because dimensional analysis tells you which physics dominates before
you compute anything, which is most of engineering judgement.**

**High** in §29.1's characterization. ⚠️ **The claim I'd emphasise is the sceptical one:
RANS remains dominant, ML turbulence models are explicitly described in 2026 sources as
"still largely in the research phase" with a 5–10 year horizon to mainstream tools, and
the obstacles include documented non-uniqueness in ML mappings and doubt that a universal
local model exists.** ⚠️ **The "1000× faster" framing in vendor and aggregator material
almost always refers to surrogates rather than solvers, and I've flagged that distinction
explicitly because it's the difference between a design-exploration tool and a
verification tool.** **The GPU speedup figures (10–100×) come from vendor and consultancy
sources and I've reported them as reported.**

**High** in §29.2's physics and threshold logic, moderate in the specific market numbers.
⚠️ **The 3,000–4,000× volumetric heat capacity ratio, the ~1,000 W+ chip TDPs, the
GB200 NVL72 at ~120 kW, and the 45°C Vera Rubin coolant specification are consistent
across sources and traceable to vendor specifications.** ⚠️ **The adoption percentages vary
substantially between sources (22% vs 37% for 2026) and I've presented them as
directional rather than picking one.** **⚠️ Sourcing caution: a significant share of the
liquid-cooling material comes from vendors, buying guides and consultancies with obvious
interests** — **I anchored the threshold logic on the ASHRAE TC 9.9 recommendation and on
the physics (which is checkable from §26 → `thermo-heat-transfer-conduction-convection-radiation-and-exchangers`'s h-magnitude table) rather than on any vendor's
recommended product.**

⚠️ **One judgement stated plainly**: **the warm-water cooling development in §29.2 is
presented as an exergy story (§10 → `thermo-cycles-exergy-combustion-and-psychrometrics`) rather than merely a product feature, and that framing
is mine.** **I think it's the right reading — eliminating a refrigeration cycle by raising
the acceptable coolant temperature is precisely "don't create a temperature gradient you
then have to spend work climbing" — but the connection is my analysis, not a citation.**
