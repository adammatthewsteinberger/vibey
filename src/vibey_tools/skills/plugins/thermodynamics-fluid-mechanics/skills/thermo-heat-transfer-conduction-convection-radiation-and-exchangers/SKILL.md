---
name: thermo-heat-transfer-conduction-convection-radiation-and-exchangers
description: "Use for heat transfer: conduction including thermal resistance networks, fins and transient response with the Biot and Fourier numbers, convection with the Nusselt correlations for free and forced flow, radiation with emissivity, view factors and why it dominates at high temperature, and heat exchangers using the log-mean temperature difference and effectiveness-NTU methods plus boiling and condensation."
---

# Thermodynamics and Fluid Mechanics: Conduction, Convection, Radiation, and Heat Exchangers and Phase Change

> **Part 5 of 6** of the *Thermodynamics and Fluid Mechanics* reference (plugin `thermodynamics-fluid-mechanics`), covering §25–§28. Sibling skills: `thermo-laws-entropy-property-relations-and-phase-behaviour` (§0–§7), `thermo-cycles-exergy-combustion-and-psychrometrics` (§8–§12), `thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes` (§13–§18), `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery` (§19–§24), `thermo-reference` (§29–§35). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The laws are permanent — Carnot 1824, Navier-Stokes 1845. Two areas of practice moved. See §29 → `thermo-reference` for CFD and turbulence modelling, and high-density thermal management.

> **⚠️ These are one subject, not two.** **Both are continuum theories built on the same
> conservation laws applied to a control volume; heat transfer is the third face of the
> same object.** **Complements a fundamental-physics reference (statistical mechanics
> underneath), an aerospace reference (external aerodynamics), and a power-engineering
> reference (cycles at plant scale).**
>
> **⚠️ Unusual epistemic status for this series: this content is as close to permanent as
> engineering knowledge gets.** ⚠️ **The Second Law has survived every attempt to violate
> it; Navier-Stokes dates to the 1840s.** **What changes is COMPUTATIONAL PRACTICE and
> APPLICATION — which is what §29 → `thermo-reference` covers.**
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

## §25. Conduction

```
⚠️ FOURIER'S LAW   q" = −k∇T
1D PLANE WALL      R = L/(kA)     CYLINDER  R = ln(r₂/r₁)/(2πkL)
⚠️ THERMAL RESISTANCE NETWORKS — series and parallel, exactly like circuits.
   ⚠️ The most useful practical tool in conduction
FINS               ⚠️ fin efficiency; adding area helps only if the fin
   conducts well relative to the convection removing heat from it
⚠️ TRANSIENT       lumped capacitance valid when Bi < 0.1 (§19);
   otherwise Heisler charts or the semi-infinite solution
⚠️ CONTACT RESISTANCE  real interfaces are not perfect. ⚠️ Frequently the
   dominant resistance in electronics cooling — hence thermal interface
   materials (§29.2)
```
**⚠️ Critical radius of insulation is the counterintuitive one**: ⚠️ **adding insulation to
a small-diameter pipe or wire can INCREASE heat loss**, **because the added outer surface
area can outweigh the added conductive resistance.** **Above the critical radius,
insulation behaves as expected.**

---

## §26. Convection

**⚠️ q = hA(T_s − T_∞) — and h is not a property.** ⚠️ **The heat transfer coefficient
depends on geometry, flow regime, fluid properties and velocity, and finding it is the
whole problem.**
```
FORCED     ⚠️ Nu = f(Re, Pr). Dittus-Boelter for turbulent pipe flow;
   many geometry-specific correlations
NATURAL    ⚠️ Nu = f(Ra, Pr). Buoyancy-driven, and much weaker than forced
MIXED      ⚠️ when Gr/Re² ~ 1, neither dominates
```
**⚠️ Typical magnitudes of h span orders of magnitude, and knowing the ranges is more
useful than any single correlation** (§32 → `thermo-reference`) — ⚠️ **natural convection in air is feeble;
boiling and condensation are enormous.** **⚠️ This ordering is exactly why §29.2 → `thermo-reference` happened.**
**⚠️ The Prandtl number tells you the relative thickness of the velocity and thermal
boundary layers**: ⚠️ **Pr ≪ 1 (liquid metals) means thermal layer much thicker; Pr ≫ 1
(oils) the reverse.**

---

## §27. Radiation

```
⚠️ STEFAN-BOLTZMANN  q" = εσT⁴   (σ = 5.67×10⁻⁸ W/m²K⁴)
   ⚠️ FOURTH POWER of ABSOLUTE temperature — which is why radiation is
   negligible at room temperature and dominant in furnaces and in space
EMISSIVITY ε · ABSORPTIVITY α · ⚠️ Kirchhoff: α = ε at the same wavelength
   and temperature
VIEW FACTOR F₁₂   ⚠️ geometry. Reciprocity: A₁F₁₂ = A₂F₂₁
WIEN'S LAW        λ_max·T ≈ 2898 μm·K — where the peak sits
```
**⚠️ Selective surfaces exploit the spectral difference**: ⚠️ **a solar absorber wants high
absorptivity in the visible (where the sun emits) and low emissivity in the infrared
(where it would re-radiate)** — **not a contradiction of Kirchhoff, because those are
different wavelengths.**
**⚠️ In space, radiation is the ONLY heat rejection mechanism** — **no convection, no
conduction to anything** — ⚠️ **which is why spacecraft thermal design is dominated by
radiator area and why "space is cold" is misleading: vacuum is a superb insulator, and
overheating is usually the harder problem.**

---

## §28. Heat Exchangers and Phase Change

```
⚠️ LMTD method     Q = UA·ΔT_lm·F     ⚠️ counterflow beats parallel flow
⚠️ ε-NTU method    for when outlet temperatures are unknown
FOULING            ⚠️ resistance grows in service; designers add a fouling
   factor, and fouling is the usual cause of degraded performance in practice
```
**⚠️ BOILING is the highest-flux mode available and it has a cliff:**
```
⚠️ THE BOILING CURVE — natural convection → NUCLEATE boiling (⚠️ excellent,
   where you want to operate) → CRITICAL HEAT FLUX → transition →
   FILM boiling
⚠️ CHF / BURNOUT   past the peak, a vapour blanket forms and the surface
   temperature JUMPS dramatically at the same heat flux. ⚠️ In a
   flux-controlled system this destroys the surface — the failure mode
   behind nuclear fuel cladding limits and power electronics burnout
```
**⚠️ The Leidenfrost effect is film boiling you can see** — **a droplet on a very hot plate
levitating on its own vapour, and taking LONGER to evaporate than on a cooler plate.**
**⚠️ Condensation**: **dropwise gives far higher coefficients than filmwise, and ⚠️ is hard
to sustain because surfaces revert to filmwise as they age.**
