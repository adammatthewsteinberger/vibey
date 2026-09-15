---
name: thermo-laws-entropy-property-relations-and-phase-behaviour
description: "Use when setting up a thermodynamic analysis: systems, properties and choosing the control volume, the zeroth law and temperature, the first law and energy accounting, the second law and entropy as direction and as energy quality, property relations and the Maxwell relations, equations of state from ideal gas through cubic equations and compressibility, and phase behaviour including saturation, quality and phase diagrams. Includes the router for the whole thermodynamics and fluid mechanics reference."
---

# Thermodynamics and Fluid Mechanics: Systems and Properties, the Zeroth and First Laws, the Second Law and Entropy, Property Relations, Equations of State, and Phase Behaviour

> **Part 1 of 6** of the *Thermodynamics and Fluid Mechanics* reference (plugin `thermodynamics-fluid-mechanics`), covering §0–§7. Sibling skills: `thermo-cycles-exergy-combustion-and-psychrometrics` (§8–§12), `thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes` (§13–§18), `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery` (§19–§24), `thermo-heat-transfer-conduction-convection-radiation-and-exchangers` (§25–§28), `thermo-reference` (§29–§35). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    (§2, §16 → `thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes`).
> 2. **⚠️ The Second Law is about DIRECTION and about QUALITY of energy** (§4). **The
>    First Law says you can't win; the Second says you can't break even — and the Second
>    is where all the engineering lives.**
> 3. **⚠️ Dimensionless groups are the most powerful tool in the subject** (§19 → `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery`). **They
>    tell you which physics dominates before you compute anything, and they let a model
>    predict a full-scale ship.**

---

## §0. Routing

| You want... | Go to |
|---|---|
| Systems, properties, state | §1–§2 |
| First Law | §3 |
| **⚠️ Second Law and entropy** | **§4** |
| Property relations | §5 |
| Equations of state | §6 |
| Phase behaviour | §7 |
| **Power cycles** | **§8 → `thermo-cycles-exergy-combustion-and-psychrometrics`** |
| Refrigeration and heat pumps | §9 → `thermo-cycles-exergy-combustion-and-psychrometrics` |
| **⚠️ Exergy** | **§10 → `thermo-cycles-exergy-combustion-and-psychrometrics`** |
| Combustion | §11 → `thermo-cycles-exergy-combustion-and-psychrometrics` |
| Psychrometrics | §12 → `thermo-cycles-exergy-combustion-and-psychrometrics` |
| Fluid properties and statics | §13–§14 → `thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes` |
| **⚠️ Control volume** | **§15 → `thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes`** |
| **⚠️ Bernoulli — and the myth** | **§16 → `thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes`** |
| Navier-Stokes | §17 → `thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes` |
| Boundary layers | §18 → `thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes` |
| **⚠️ Dimensional analysis** | **§19 → `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery`** |
| Internal flow | §20 → `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery` |
| External flow and drag | §21 → `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery` |
| **⚠️ Turbulence** | **§22 → `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery`** |
| Compressible flow | §23 → `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery` |
| Turbomachinery | §24 → `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery` |
| **Conduction** | **§25 → `thermo-heat-transfer-conduction-convection-radiation-and-exchangers`** |
| Convection | §26 → `thermo-heat-transfer-conduction-convection-radiation-and-exchangers` |
| Radiation | §27 → `thermo-heat-transfer-conduction-convection-radiation-and-exchangers` |
| Heat exchangers, boiling | §28 → `thermo-heat-transfer-conduction-convection-radiation-and-exchangers` |
| **What's live** | **§29 → `thermo-reference`** |
| Anti-patterns, misconceptions | §30–§31 → `thermo-reference` |
| Numbers, books, quick ref | §32–§34 → `thermo-reference` |

---

# PART I — THERMODYNAMICS

## §1. Systems and Properties

```
SYSTEM      ⚠️ what you draw the boundary around. CLOSED (no mass crossing),
            OPEN/control volume (mass crosses), ISOLATED (nothing crosses)
PROPERTY    ⚠️ INTENSIVE (independent of amount: T, P, ρ, v) vs
            EXTENSIVE (scales with amount: V, m, U, S)
STATE       ⚠️ fixed by a sufficient number of independent intensive
            properties. For a simple compressible substance, TWO
PROCESS     the path between states. ⚠️ Properties are path-independent;
            WORK AND HEAT ARE NOT
EQUILIBRIUM ⚠️ thermal, mechanical, chemical, phase — all required
```
> **⚠️ GOTCHA — heat and work are not properties, and this is the deepest bookkeeping point
> in the subject.** ⚠️ **A system does not "contain heat."** **It contains internal energy;
> heat and work are ENERGY IN TRANSIT across the boundary.** **⚠️ That's why we write
> δQ and δW (inexact differentials, path-dependent) but dU and dS (exact, state
> functions).** **Nearly every confused thermodynamics argument traces to treating heat as
> a stored quantity.**

**⚠️ Quasi-static vs real processes**: ⚠️ **the reversible idealization requires infinitely
slow change through equilibrium states — it never happens, and it's the benchmark
everything real is measured against** (§10 → `thermo-cycles-exergy-combustion-and-psychrometrics`).

---

## §2. The Zeroth Law and Temperature

**⚠️ If A is in thermal equilibrium with C, and B is with C, then A is with B.** ⚠️ **This
sounds trivial and is what makes TEMPERATURE a meaningful property and thermometry
possible** — **it was named "zeroth" because it was recognized as logically prior after
the first and second were already numbered.**
**⚠️ Temperature is not heat and not thermal energy.** ⚠️ **A spark at 1000°C carries far
less energy than a bathtub at 40°C.** **Temperature is intensive; thermal energy is
extensive.**

---

## §3. The First Law

```
CLOSED SYSTEM      ΔU = Q − W
⚠️ CONTROL VOLUME  (steady flow energy equation, SFEE)
   Q̇ − Ẇ = Σṁ_out(h + V²/2 + gz) − Σṁ_in(h + V²/2 + gz)
⚠️ ENTHALPY  h = u + Pv  — ⚠️ NOT a form of energy; a bookkeeping convenience
   that bundles internal energy with the FLOW WORK (Pv) needed to push
   mass across the boundary. It exists because open systems are common
```
**⚠️ Sign conventions vary between textbooks and cause endless errors** — ⚠️ **be explicit
about whether W is work done BY or ON the system.** **Most engineering texts take W as
work done by the system (so it's positive in a turbine).**
**Specific heats**: **c_v and c_p**; ⚠️ **c_p > c_v always, because constant-pressure
heating must also do expansion work.** **For ideal gases, c_p − c_v = R.**

---

## §4. ⚠️ The Second Law and Entropy

**⚠️ The conceptual core of the whole subject, and the most-mangled idea in popular
science.**
```
KELVIN-PLANCK  ⚠️ no cycle can convert heat entirely into work with a
   SINGLE reservoir. You always reject heat somewhere
CLAUSIUS       ⚠️ heat does not spontaneously flow cold → hot
ENTROPY        dS ≥ δQ/T, equality for reversible processes
⚠️ ENTROPY GENERATION  S_gen ≥ 0 for any real process. THE statement
```
> **⚠️ GOTCHA — "entropy is disorder" is a misleading pop-science gloss and it generates
> bad intuitions.** ⚠️ **Entropy is a measure of the number of microstates consistent
> with the macrostate (Boltzmann: S = k ln Ω) — it's about MULTIPLICITY, or equivalently
> about missing information.** **"Disorder" is a loose visual metaphor that fails on real
> cases: ⚠️ oil and water separating LOOKS more ordered while entropy increases; some
> crystallization and self-assembly processes increase total entropy while producing
> visibly ordered structures.**
> **⚠️ Better intuitions**: **entropy measures how much energy is unavailable for work at
> a given ambient temperature** (§10 → `thermo-cycles-exergy-combustion-and-psychrometrics`), **and it measures how many ways the microscopic
> configuration could be arranged without changing what you can measure.**

**⚠️ Carnot efficiency — the ceiling nothing beats:**
```
⚠️ η_Carnot = 1 − T_C/T_H     (⚠️ ABSOLUTE temperatures, always)
```
⚠️ **This is a limit set by the temperatures alone — not by materials, engineering skill
or budget.** **⚠️ Which is why raising T_H is the perennial goal in power generation and
why it's a materials problem more than a thermodynamics problem.**
**⚠️ The local-decrease point, since it recurs**: ⚠️ **entropy of a SYSTEM can decrease
(that's what a refrigerator does); the entropy of system plus surroundings cannot.**
**Life, crystals and engines are not violations — they export entropy.**

---

## §5. Property Relations

```
⚠️ Tds RELATIONS   Tds = du + Pdv     Tds = dh − vdP
⚠️ MAXWELL RELATIONS  from equality of mixed second partials of the
   thermodynamic potentials (U, H, A, G). ⚠️ They let you get
   HARD-TO-MEASURE quantities (entropy changes) from EASY ones (P, v, T)
POTENTIALS   ⚠️ U (internal), H (enthalpy), A (Helmholtz, useful at
   constant T and V), G (Gibbs, constant T and P — the one that governs
   phase equilibrium and chemical reaction)
```
**⚠️ Gibbs free energy is the practical criterion for spontaneity at constant T and P**:
**ΔG < 0.** ⚠️ **And ΔG = ΔH − TΔS shows the competition directly — enthalpy and entropy
pulling against each other, with temperature setting the exchange rate.**

---

## §6. Equations of State

```
IDEAL GAS      Pv = RT. ⚠️ Assumes point particles, no intermolecular forces.
   ⚠️ Good at LOW pressure and HIGH temperature relative to critical
COMPRESSIBILITY FACTOR  Z = Pv/RT. ⚠️ Z = 1 is ideal; the deviation tells
   you how wrong the ideal assumption is
VAN DER WAALS  ⚠️ adds molecular volume (b) and attraction (a). Qualitatively
   right, quantitatively mediocre — and historically important for
   predicting the critical point
CUBIC EOS      ⚠️ Redlich-Kwong, Soave-RK, Peng-Robinson. The practical
   workhorses in process engineering
⚠️ PRINCIPLE OF CORRESPONDING STATES  gases at the same REDUCED
   temperature and pressure (T/T_crit, P/P_crit) behave similarly.
   ⚠️ Remarkable, and the basis of generalized charts
```
**⚠️ For liquids and solids, use tabulated properties or incompressible approximations** —
⚠️ **the ideal gas law is not a general-purpose tool and applying it near saturation is a
classic error.**

---

## §7. Phase Behaviour

**⚠️ The P-v-T surface and its projections** (**P-T phase diagram, T-s and P-h diagrams —
⚠️ and P-h is the working diagram for refrigeration, T-s for power cycles**).
```
SATURATION       ⚠️ at a given pressure, boiling occurs at ONE temperature —
   and adding heat then changes QUALITY, not temperature
QUALITY x        mass fraction vapour in a two-phase mixture
CRITICAL POINT   ⚠️ above it, no distinction between liquid and vapour;
   supercritical fluids have liquid-like density and gas-like transport
TRIPLE POINT     all three phases coexist
⚠️ CLAUSIUS-CLAPEYRON  dP/dT = h_fg/(T·v_fg) — the slope of the phase
   boundary. ⚠️ Explains why water's solid-liquid line slopes BACKWARD
   (ice is less dense than water), which is nearly unique
LATENT HEAT      ⚠️ enormous compared to sensible heat — water's latent heat
   of vaporization is roughly 540× the energy to raise 1 g by 1°C.
   ⚠️ This is why phase change dominates thermal engineering (§28)
```
