---
name: thermo-dimensional-analysis-flows-turbulence-and-turbomachinery
description: "Use for flow analysis and scaling: dimensional analysis and the Buckingham Pi theorem with the dimensionless groups that tell you which physics dominates before you compute anything, internal flow with friction factors, the Moody chart and minor losses, external flow, drag and lift coefficients, turbulence and why it remains the hard problem, compressible flow including choking, shocks and nozzles, and turbomachinery with pumps, fans, compressors and their curves."
---

# Thermodynamics and Fluid Mechanics: Dimensional Analysis, Internal Flow, External Flow and Drag, Turbulence, Compressible Flow, and Turbomachinery

> **Part 4 of 6** of the *Thermodynamics and Fluid Mechanics* reference (plugin `thermodynamics-fluid-mechanics`), covering §19–§24. Sibling skills: `thermo-laws-entropy-property-relations-and-phase-behaviour` (§0–§7), `thermo-cycles-exergy-combustion-and-psychrometrics` (§8–§12), `thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes` (§13–§18), `thermo-heat-transfer-conduction-convection-radiation-and-exchangers` (§25–§28), `thermo-reference` (§29–§35). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 3. **⚠️ Dimensionless groups are the most powerful tool in the subject** (§19). **They
>    tell you which physics dominates before you compute anything, and they let a model
>    predict a full-scale ship.**

---

## §19. ⚠️ Dimensional Analysis

**⚠️ The highest-leverage tool in the subject. Buckingham Pi: a relation among n variables
with k independent dimensions reduces to n−k dimensionless groups.**
```
⚠️ REYNOLDS   Re = ρVL/μ   inertia/viscous. ⚠️ THE master parameter
⚠️ MACH       Ma = V/c     compressibility. ⚠️ >0.3 matters, >1 changes everything
⚠️ FROUDE     Fr = V/√(gL) inertia/gravity — free surface, ships, open channel
⚠️ PRANDTL    Pr = ν/α     momentum vs thermal diffusivity (§26)
⚠️ NUSSELT    Nu = hL/k    convective vs conductive heat transfer — the OUTPUT
⚠️ BIOT       Bi = hL/k_s  ⚠️ note k is the SOLID's here, unlike Nusselt.
              Bi < 0.1 justifies lumped capacitance (§25)
⚠️ RAYLEIGH   Ra = Gr·Pr   natural convection driver
⚠️ WEBER      We = ρV²L/σ  inertia/surface tension — droplets, atomization
⚠️ STROUHAL   St = fL/V    vortex shedding frequency
⚠️ FOURIER    Fo = αt/L²   dimensionless time in transient conduction
```
**⚠️ Dynamic similarity is what makes model testing possible**: ⚠️ **match the relevant
dimensionless groups and the model predicts the prototype.** **⚠️ The practical difficulty
is that you often cannot match all of them at once — matching Reynolds and Froude
simultaneously in ship testing requires an impossible fluid, which is why hull resistance
is decomposed into components scaled separately.**
**⚠️ Use them before computing anything**: ⚠️ **Re tells you whether viscosity matters, Ma
whether compressibility does, Bi whether internal gradients do.** **Knowing which terms
are negligible is most of engineering judgement.**

---

## §20. Internal Flow

```
ENTRANCE LENGTH → fully developed
⚠️ TRANSITION in pipes  Re ≈ 2300 (laminar) to ~4000 (turbulent)
LAMINAR       ⚠️ Hagen-Poiseuille: Q ∝ ΔP·D⁴  — the FOURTH power of diameter.
   ⚠️ Halving the diameter cuts flow 16× at fixed pressure. This dominates
   biological and microfluidic design
⚠️ DARCY-WEISBACH  h_f = f(L/D)(V²/2g)
   ⚠️ f = 64/Re laminar; from Colebrook/Moody for turbulent
MOODY CHART   ⚠️ f vs Re and relative roughness ε/D.
   ⚠️ In fully rough turbulent flow, f becomes INDEPENDENT of Re
MINOR LOSSES  ⚠️ fittings, bends, valves, entries — often NOT minor, and
   frequently dominant in short piping runs
```
**⚠️ Note the friction-factor confusion**: ⚠️ **the Darcy friction factor is 4× the Fanning
friction factor**, **and mixing them up is a classic and expensive unit error.**

---

## §21. External Flow and Drag

```
⚠️ F_D = ½ρV²·C_D·A
⚠️ FORM (pressure) DRAG   from separation and wake — dominates bluff bodies
⚠️ SKIN FRICTION DRAG     from shear — dominates streamlined bodies
INDUCED DRAG              ⚠️ the price of lift, from trailing vortices; ∝ 1/V²
WAVE DRAG                 ⚠️ transonic and supersonic (§23)
```
**⚠️ The drag crisis is the classic demonstration of §18 → `thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes`**: ⚠️ **C_D for a sphere drops
sharply around Re ≈ 3×10⁵ as the boundary layer transitions to turbulent and separation is
delayed.** **A rougher ball can have LESS drag than a smooth one in that regime.**
**⚠️ Vortex shedding and the von Kármán street** — **St ≈ 0.2 for a cylinder over a wide Re
range** — ⚠️ **and lock-in with a structure's natural frequency causes vortex-induced
vibration, which is a real failure mode for chimneys, cables and risers.** **⚠️ Note the
Tacoma Narrows collapse is commonly and incorrectly attributed to simple vortex shedding
resonance; it is better explained as aeroelastic flutter.**

---

## §22. ⚠️ Turbulence

**⚠️ "The last great unsolved problem of classical physics," and the honest framing is
that we have statistics rather than solutions.**
```
⚠️ CHARACTERISTICS  irregular, diffusive, rotational, dissipative, 3D,
   ⚠️ and a continuous range of scales
⚠️ ENERGY CASCADE   energy enters at large scales, transfers to smaller
   eddies, dissipates at the KOLMOGOROV SCALE η = (ν³/ε)^¼
⚠️ K41 SCALING      E(k) ∝ ε^(2/3)k^(−5/3) in the inertial subrange.
   ⚠️ Remarkably robust experimentally, with known intermittency corrections
⚠️ THE COST OF DNS  resolving all scales needs grid points ~Re^(9/4) and
   total work ~Re³. ⚠️ THIS is why DNS is infeasible for industrial
   Reynolds numbers and will remain so for decades (§29.1)
⚠️ CLOSURE PROBLEM  averaging Navier-Stokes creates the Reynolds stress
   term, which introduces more unknowns than equations. ⚠️ Every RANS
   model is a guess at closing it — and none is universal
```
**⚠️ Reynolds decomposition, the Boussinesq eddy-viscosity hypothesis** (⚠️ **which assumes
Reynolds stress aligns with mean strain rate — demonstrably false in flows with strong
curvature, rotation or separation, and it's the root of RANS's known failure modes**),
**and the model hierarchy: mixing length → k-ε → k-ω → SST → Reynolds stress models.**

---

## §23. Compressible Flow

```
⚠️ c = √(γRT)     Ma = V/c
STAGNATION PROPERTIES  T₀/T = 1 + ((γ−1)/2)Ma²
⚠️ ISENTROPIC NOZZLE  subsonic: area DOWN → velocity UP.
   ⚠️ SUPERSONIC: area UP → velocity UP. The reversal is why rocket and
   supersonic nozzles are converging-DIVERGING
⚠️ CHOKING        at the throat Ma = 1; mass flow becomes INDEPENDENT of
   downstream pressure. ⚠️ You cannot pull more through by lowering it
NORMAL SHOCK      ⚠️ discontinuous, irreversible, always supersonic→subsonic.
   ⚠️ Entropy INCREASES across it; stagnation pressure drops
OBLIQUE SHOCK / PRANDTL-MEYER EXPANSION  ⚠️ shocks compress abruptly;
   expansions are gradual and isentropic
FANNO (friction) and RAYLEIGH (heat addition) flow
```
**⚠️ Wave drag and the transonic regime**: ⚠️ **local supersonic pockets form on a wing
below Ma = 1, terminated by shocks — which is the drag rise, and the reason for swept
wings and supercritical aerofoils.**

---

## §24. Turbomachinery

**⚠️ The Euler turbomachine equation relates torque to the change in angular momentum** —
⚠️ **which is §15 → `thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes`'s angular momentum control volume applied directly.**
**Pumps and compressors add energy; turbines extract it.** ⚠️ **Axial vs centrifugal:
centrifugal gives high head per stage, axial gives high flow.**
**⚠️ Specific speed selects machine type** — **a dimensionless group (§19) that tells you
whether the duty calls for radial, mixed or axial flow before any detailed design.**
**⚠️ Cavitation is the characteristic pump failure**: ⚠️ **local pressure falls below the
vapour pressure, bubbles form and collapse violently, eroding the impeller.**
**⚠️ NPSH available must exceed NPSH required** — **and this is a suction-side problem, so
raising discharge pressure doesn't fix it.**
**System curve vs pump curve; ⚠️ affinity laws (Q ∝ N, H ∝ N², P ∝ N³)** — ⚠️ **the cubic
on power is why variable-speed drives on pumps and fans save so much energy.**

---

# PART III — HEAT TRANSFER
