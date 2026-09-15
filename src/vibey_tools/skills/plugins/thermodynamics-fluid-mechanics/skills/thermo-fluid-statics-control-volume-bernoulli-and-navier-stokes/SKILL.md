---
name: thermo-fluid-statics-control-volume-bernoulli-and-navier-stokes
description: "Use when starting a fluids problem: fluid properties and viscosity, fluid statics and buoyancy, the control volume and the conservation of mass, momentum and energy, Bernoulli's equation with the assumptions it depends on and the equal-transit-time lift myth it gets blamed for, the Navier-Stokes equations and what each term means, and boundary layers including transition and separation."
---

# Thermodynamics and Fluid Mechanics: Fluid Properties, Statics, the Control Volume, Bernoulli and the Lift Myth, Navier-Stokes, and Boundary Layers

> **Part 3 of 6** of the *Thermodynamics and Fluid Mechanics* reference (plugin `thermodynamics-fluid-mechanics`), covering §13–§18. Sibling skills: `thermo-laws-entropy-property-relations-and-phase-behaviour` (§0–§7), `thermo-cycles-exergy-combustion-and-psychrometrics` (§8–§12), `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery` (§19–§24), `thermo-heat-transfer-conduction-convection-radiation-and-exchangers` (§25–§28), `thermo-reference` (§29–§35). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    (§2 → `thermo-laws-entropy-property-relations-and-phase-behaviour`, §16).
> 2. **⚠️ The Second Law is about DIRECTION and about QUALITY of energy** (§4 → `thermo-laws-entropy-property-relations-and-phase-behaviour`). **The
>    First Law says you can't win; the Second says you can't break even — and the Second
>    is where all the engineering lives.**
> 3. **⚠️ Dimensionless groups are the most powerful tool in the subject** (§19 → `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery`). **They
>    tell you which physics dominates before you compute anything, and they let a model
>    predict a full-scale ship.**

---

## §13. Fluid Properties

```
⚠️ CONTINUUM ASSUMPTION  valid when the Knudsen number Kn = λ/L ≪ 1.
   ⚠️ Breaks down in rarefied gas (high altitude, vacuum) and
   microfluidics — where you need slip models or DSMC
VISCOSITY μ    ⚠️ resistance to shear. Newtonian: τ = μ(du/dy)
   ⚠️ Gas viscosity RISES with temperature; liquid viscosity FALLS.
   Different mechanisms — momentum exchange vs intermolecular forces
KINEMATIC ν = μ/ρ    "momentum diffusivity"
SURFACE TENSION  ⚠️ dominates at small scale; Δp = 2σ/R for a droplet
COMPRESSIBILITY  ⚠️ bulk modulus; a liquid is nearly incompressible
VAPOUR PRESSURE  ⚠️ the cavitation criterion (§24)
```
**⚠️ Non-Newtonian fluids are the norm outside textbooks**: **shear-thinning
(paint, blood, polymer solutions), shear-thickening (cornstarch suspension),
Bingham plastic (toothpaste, drilling mud — ⚠️ requires a yield stress before it flows at
all), and viscoelastic.**

---

## §14. Statics

**⚠️ dp/dz = −ρg**, **hence p = ρgh for constant density.** **Manometry; ⚠️ absolute vs
gauge pressure — mixing them is a classic error.**
**⚠️ Forces on submerged surfaces**: **magnitude and the CENTRE OF PRESSURE** (⚠️ **which
is below the centroid, because pressure increases with depth**).
**⚠️ Buoyancy (Archimedes)**: **the buoyant force equals the weight of displaced fluid, and
acts at the centroid of the displaced volume.** **⚠️ Stability requires the METACENTRE
above the centre of gravity** — **which is why a ship with liquid cargo free to slosh (free
surface effect) can capsize despite adequate static stability.**

---

## §15. ⚠️ The Control Volume

**⚠️ The single most important analytical tool in fluid mechanics.**
**⚠️ The Reynolds Transport Theorem converts system (Lagrangian) statements of the
conservation laws into control-volume (Eulerian) form** — **which is what you can actually
measure.**
```
⚠️ MASS       ṁ_in = ṁ_out for steady flow.  ρAV = constant (incompressible)
⚠️ MOMENTUM   ΣF = Σṁ_out·V_out − Σṁ_in·V_in  ⚠️ VECTOR equation — the
   most-botched one. Momentum flux carries direction; pressure forces
   act on ALL boundary surfaces including where flow enters and leaves
⚠️ ENERGY     the SFEE (§3)
ANGULAR MOMENTUM  ⚠️ the basis of turbomachinery analysis (Euler equation, §24)
```
**⚠️ The discipline that prevents most errors**: ⚠️ **draw the control volume explicitly,
mark every place mass or force crosses it, and choose the boundary where you actually
know the conditions.** **Most "hard" problems become easy with a better choice of control
volume.**

---

## §16. ⚠️ Bernoulli — and the Lift Myth

```
⚠️ p + ½ρV² + ρgz = constant
⚠️ VALID ONLY: steady, incompressible, inviscid, ALONG A STREAMLINE,
   no shaft work, no heat transfer
```
> **⚠️ GOTCHA — Bernoulli is the most misapplied equation in engineering, and it is
> misapplied by textbooks.** ⚠️ **It does NOT apply across streamlines in general, through
> a pump or turbine, in viscous-dominated regions, or in separated flow.** **⚠️ Applying
> it where viscosity matters gives a confidently wrong answer that looks reasonable.**

> **⚠️ GOTCHA — the "equal transit time" explanation of aerodynamic lift is FALSE, and it
> is still in circulation and in some textbooks.** ⚠️ **The claim that air parting at the
> leading edge must rejoin at the trailing edge — and therefore travels faster over the
> longer upper surface — has no physical basis.** **⚠️ Measured flow shows upper-surface
> air arrives WELL AHEAD of the lower-surface air, not simultaneously.**
> **⚠️ It also cannot explain symmetric aerofoils, flat plates, or inverted flight, all of
> which generate lift perfectly well.**
> **⚠️ The correct account**: **the aerofoil turns the flow downward (circulation, with the
> Kutta condition setting the circulation), and by Newton's third law the reaction is
> lift.** ⚠️ **Bernoulli and the momentum picture are two consistent descriptions of the
> same thing — the error is not "using Bernoulli," it's the equal-transit-time premise.**

**⚠️ Where Bernoulli IS the right tool**: **Pitot-static measurement, venturi and orifice
metering, nozzle exit velocity, Torricelli.** ⚠️ **The extended form with head losses
(§20 → `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery`) is the practical engineering version.**

---

## §17. Navier-Stokes

```
⚠️ ρ(∂V/∂t + V·∇V) = −∇p + μ∇²V + ρg
   unsteady + convective  =  pressure + viscous + body force
```
**⚠️ The convective term V·∇V is nonlinear, and that nonlinearity is the source of
essentially all the difficulty** — **turbulence, chaos, and the fact that existence and
smoothness in 3D remains a Millennium Prize problem.**
**⚠️ Exact solutions exist only for a handful of highly restricted cases** — **Couette,
Poiseuille, Stokes flow** — **which is why the subject is dominated by dimensional
analysis (§19 → `thermo-dimensional-analysis-flows-turbulence-and-turbomachinery`), empirical correlation, and computation (§29.1 → `thermo-reference`).**
**⚠️ Useful limits**: ⚠️ **Stokes flow (Re ≪ 1) drops the convective term entirely — linear,
reversible, and the regime of microorganisms and sedimentation; potential flow (inviscid,
irrotational) is analytically tractable and ⚠️ produces d'Alembert's paradox — zero drag —
which is precisely how we learned viscosity is never negligible near a wall** (§18).

---

## §18. Boundary Layers

**⚠️ Prandtl's 1904 insight is the one that made modern fluid mechanics possible**:
⚠️ **viscous effects are confined to a thin layer near the surface; outside it, inviscid
theory works.** **This reconciled d'Alembert's paradox with reality and split an
intractable problem into two tractable ones.**
```
⚠️ NO-SLIP CONDITION  fluid velocity at a solid wall equals the wall's
   velocity. ⚠️ The boundary condition that makes viscosity matter at all
δ (thickness), δ* (displacement), θ (momentum thickness)
⚠️ TRANSITION  laminar → turbulent, around Re_x ~ 5×10⁵ on a flat plate
   (⚠️ highly sensitive to roughness, freestream turbulence, pressure gradient)
⚠️ SEPARATION  an ADVERSE pressure gradient (dp/dx > 0) decelerates the
   near-wall fluid until it reverses. ⚠️ Separation causes pressure drag,
   stall and most of the hard problems in aerodynamics
```
**⚠️ The counterintuitive result worth knowing**: ⚠️ **a TURBULENT boundary layer resists
separation better than a laminar one, because turbulent mixing brings high-momentum fluid
toward the wall.** **⚠️ This is why golf balls have dimples — tripping the boundary layer
turbulent increases skin friction slightly but delays separation dramatically, shrinking
the wake and cutting total drag.** **Same reason for turbulator strips and vortex
generators.**
