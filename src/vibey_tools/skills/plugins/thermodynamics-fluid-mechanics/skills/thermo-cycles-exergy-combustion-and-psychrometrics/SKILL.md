---
name: thermo-cycles-exergy-combustion-and-psychrometrics
description: "Use for applied cycle analysis: power cycles including Rankine, Brayton, Otto and Diesel with their efficiency limits and real irreversibilities, refrigeration and heat pump cycles and coefficient of performance, exergy and second-law efficiency and where work potential is actually destroyed, combustion with stoichiometry, adiabatic flame temperature and heating values, and psychrometrics including wet-bulb, dew point and the sensible-latent split."
---

# Thermodynamics and Fluid Mechanics: Power Cycles, Refrigeration and Heat Pumps, Exergy, Combustion, and Psychrometrics

> **Part 2 of 6** of the *Thermodynamics and Fluid Mechanics* reference (plugin `thermodynamics-fluid-mechanics`), covering §8–§12. Sibling skills: `thermo-laws-entropy-property-relations-and-phase-behaviour` (§0–§7), `thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes` (§13–§18), `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery` (§19–§24), `thermo-heat-transfer-conduction-convection-radiation-and-exchangers` (§25–§28), `thermo-reference` (§29–§35). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §8. Power Cycles

```
⚠️ CARNOT     two isothermal + two isentropic. ⚠️ The efficiency ceiling,
   and impractical — the isothermal heat exchange requires infinite time
⚠️ RANKINE    steam. Pump → boiler → turbine → condenser.
   ⚠️ Improvements: superheat, reheat, regeneration (feedwater heating),
   supercritical operation. ⚠️ Condensing at low pressure is what
   makes it efficient — the vacuum matters as much as the boiler
⚠️ BRAYTON    gas turbine. Compress → burn → expand.
   ⚠️ Improvements: intercooling, reheat, regeneration.
   ⚠️ COMBINED CYCLE — Brayton exhaust feeds a Rankine bottoming cycle,
   reaching the highest efficiencies of any heat engine in service
OTTO          spark ignition. η = 1 − 1/r^(γ−1) — ⚠️ efficiency depends on
   COMPRESSION RATIO alone in the ideal case, and knock limits r
DIESEL        compression ignition; higher r, cutoff ratio penalty
STIRLING      ⚠️ external heat, regenerator, theoretically Carnot-efficient;
   practically limited by heat transfer and sealing
```
**⚠️ The universal cycle lesson**: ⚠️ **every improvement listed above is a way of moving
heat addition to a HIGHER average temperature or heat rejection to a LOWER one** —
**because §4 → `thermo-laws-entropy-property-relations-and-phase-behaviour` says that's the only lever.** **Regeneration, reheat and combined cycles are
all that one idea in different clothes.**
**⚠️ Isentropic efficiency** — **real turbines and compressors deviate from isentropic, and
⚠️ compressor irreversibility hurts more than turbine irreversibility in gas turbines
because the compressor consumes a large fraction of turbine output (the back-work ratio).**

---

## §9. Refrigeration and Heat Pumps

**⚠️ A heat engine run backwards: work in, heat moved from cold to hot.**
```
⚠️ COP_refrigeration = Q_C/W        ⚠️ COP_heat pump = Q_H/W = COP_R + 1
⚠️ Carnot limits: COP_R = T_C/(T_H−T_C)    COP_HP = T_H/(T_H−T_C)
```
**⚠️ COP exceeds 1 routinely, and this confuses people** — ⚠️ **it is not an efficiency and
does not violate anything.** **You're MOVING heat, not creating it, so getting 3–4 units of
heat delivered per unit of work is ordinary.** ⚠️ **This is the entire thermodynamic case
for heat pumps over resistance heating.**
**⚠️ The vapour-compression cycle**: **evaporator → compressor → condenser → expansion
valve.** ⚠️ **The expansion valve is deliberately irreversible (throttling, isenthalpic) —
a turbine would recover work but isn't worth the cost and complexity at small scale.**
**⚠️ COP collapses as the temperature lift grows** — **which is why air-source heat pumps
degrade in extreme cold and why ground-source performs better.**
**⚠️ Absorption refrigeration** — **driven by heat rather than work; useful where waste
heat is free.**

---

## §10. ⚠️ Exergy

**⚠️ The concept that makes the Second Law quantitative and actionable, and it is
under-taught.**
⚠️ **Exergy (availability) is the maximum useful work obtainable as a system comes to
equilibrium with a specified DEAD STATE (the ambient environment).**
```
⚠️ Energy is CONSERVED. Exergy is DESTROYED — in proportion to entropy
   generated:   ⚠️ X_destroyed = T₀ · S_gen   (Gouy-Stodola)
```
**⚠️ Why it matters practically**: ⚠️ **a First Law analysis says a furnace burning fuel at
2000 K to heat a room to 293 K is ~90% "efficient."** **A Second Law analysis says you have
destroyed most of the fuel's capacity to do work.** ⚠️ **Exergy analysis locates WHERE in a
plant the real losses occur — and it's usually the combustion chamber and the heat
exchangers with large temperature differences, not the components engineers instinctively
target.**
**⚠️ This is the rigorous version of "don't use a high-temperature source for a
low-temperature job."**

---

## §11. Combustion

**Stoichiometry, air-fuel ratio, equivalence ratio φ** (⚠️ **φ > 1 rich, φ < 1 lean**),
**excess air.**
**⚠️ Heating values**: ⚠️ **HHV includes the latent heat of the water vapour formed; LHV
does not.** **Quoted efficiencies differ by which is used, and cross-comparisons are
frequently apples-to-oranges** — ⚠️ **condensing boilers achieving ">100% efficiency" are
quoted on LHV and are recovering that latent heat.**
**Adiabatic flame temperature; dissociation at high temperature; ⚠️ equilibrium vs
kinetics — NOx formation is kinetically limited and strongly temperature-dependent, which
is why lowering peak flame temperature is the primary NOx control.**
**⚠️ Flame types**: **premixed vs diffusion; laminar flame speed; ⚠️ flashback and blowoff
as the stability limits.**

---

## §12. Psychrometrics

**⚠️ The thermodynamics of moist air — HVAC's core tool and worth knowing because the
intuitions are counterintuitive.**
```
⚠️ Absolute vs RELATIVE humidity (⚠️ RH is relative to saturation AT THAT
   TEMPERATURE — which is why heating air lowers RH with no moisture change)
DEW POINT      ⚠️ the actual measure of moisture content, temperature-independent
WET BULB       evaporative cooling limit
⚠️ ENTHALPY of moist air; the psychrometric chart
```
**⚠️ Why evaporative cooling fails in humid climates**: ⚠️ **the wet-bulb temperature is the
floor, and it approaches dry-bulb as RH approaches 100%.** **This is the same physics that
limits human thermoregulation** (see an exercise physiology reference §7) — **and wet-bulb
temperature is the meaningful heat-stress metric for exactly this reason.**
**⚠️ Sensible vs latent load**: ⚠️ **dehumidification often dominates cooling energy in
humid climates, and a system sized only on sensible load will fail to control humidity.**

---

# PART II — FLUID MECHANICS
