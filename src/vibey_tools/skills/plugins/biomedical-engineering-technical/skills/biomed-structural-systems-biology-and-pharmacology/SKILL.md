---
name: biomed-structural-systems-biology-and-pharmacology
description: "Use when modelling biological structure or dynamics: structural biology including protein structure determination and prediction, systems biology and network modelling, pharmacokinetics and pharmacodynamics including compartment models, clearance and dose-response, and physiological models of the cardiovascular, respiratory and metabolic systems."
---

# Biomedical Engineering: Structural Biology, Systems Biology, PK/PD, and Physiological Models

> **Part 3 of 5** of the *Biomedical Engineering* reference (plugin `biomedical-engineering-technical`), covering §6–§9. Sibling skills: `biomed-signals-and-medical-imaging` (§0–§2), `biomed-clinical-data-ml-and-bioinformatics` (§3–§5), `biomed-biomechanics-devices-and-biostatistics` (§10–§15), `biomed-reference` (§16–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The physics, physiology and mathematics are stable; tool and pipeline recommendations shift slowly.

> **Scope note.** This is the engineering and science. **Regulatory pathways, quality
> systems, and lifecycle process are deliberately excluded** — they're a separate subject
> and they'd swamp the technical content.
>
> **⚠️ GOTCHA** boxes mark where a silent wrong answer is produced — which in this domain
> is the dangerous failure mode, not a crash.
>
> **The three technical facts that recur everywhere below:**
> 1. **⚠️ Biological signals are non-stationary, and most DSP assumes stationarity.** Every
>    windowing choice is an assumption about how long the physiology holds still (§1 → `biomed-signals-and-medical-imaging`).
> 2. **⚠️ Prevalence governs predictive value.** Sensitivity and specificity are properties
>    of a test; PPV is a property of a test *in a population*. Confusing them is the single
>    most common quantitative error in the field (§4.1 → `biomed-clinical-data-ml-and-bioinformatics`).
> 3. **⚠️ Biological variability is the signal's competitor.** Between-subject variance
>    usually exceeds the effect you're measuring, which is why normalization,
>    within-subject designs, and mixed-effects models dominate (§15 → `biomed-biomechanics-devices-and-biostatistics`).

---

## §6. Structural Biology

**Protein structure**: primary (sequence) → secondary (α-helix, β-sheet, from backbone
φ/ψ angles — ⚠️ **Ramachandran plot shows the allowed regions**) → tertiary → quaternary.

**Determination**: **X-ray crystallography** (⚠️ **resolution in Å; requires crystals, and
the phase problem**), **cryo-EM** (⚠️ **the resolution revolution — now routinely
sub-3 Å, no crystals needed**), **NMR** (solution state, size-limited).

**Prediction**: **AlphaFold2/3** changed the field — ⚠️ **read the confidence metrics
properly. pLDDT is per-residue confidence (>90 very high, <50 likely disordered); PAE is
the predicted aligned error between residue pairs and is what tells you whether relative
domain positions are trustworthy.** **A high-pLDDT structure with high inter-domain PAE
means good domains, unreliable arrangement.**

**⚠️ And the standing caveats**: predicted structures are **single static conformations**;
they do not give you the conformational ensemble, ligand-bound states, or the effects of
point mutations reliably.

**Molecular dynamics**: integrate Newton's equations with a **force field** (AMBER,
CHARMM, OPLS) at **~2 fs timesteps** — ⚠️ **which is the fundamental problem: biologically
interesting events take microseconds to milliseconds, i.e. 10⁹–10¹² steps.** Enhanced
sampling (replica exchange, metadynamics, umbrella sampling) exists to bridge it.
**Docking** (AutoDock Vina, Glide) for binding pose; ⚠️ **scoring functions predict pose
much better than they predict affinity.**

---

## §7. Systems Biology

**Mass-action kinetics**: `d[X]/dt = Σ (production) − Σ (consumption)`.
**Michaelis–Menten**: `v = V_max[S]/(K_m + [S])` — ⚠️ **valid under the quasi-steady-state
assumption ([S] ≫ [E]), which is violated inside cells more often than people assume.**
**Hill equation**: `θ = [L]^n/(K_d + [L]^n)` — cooperativity, and `n` is the steepness of
the switch.

**Network motifs** that recur and what they do: **negative feedback** (homeostasis, noise
reduction), **positive feedback** (⚠️ **bistability — a switch**), **coherent feedforward
loop** (⚠️ **persistence detection: filters transient inputs**), **incoherent feedforward
loop** (pulse generation, fold-change detection), **oscillators** (negative feedback plus
delay — circadian clocks, p53).

**Flux balance analysis** for metabolism: `S·v = 0` at steady state, then maximize an
objective (usually growth) by linear programming subject to flux bounds. ⚠️ **No kinetic
parameters needed, which is why it scales to genome-scale models — and why it can't
predict dynamics.**

**Stochastic simulation** — **Gillespie's algorithm** for exact trajectories when molecule
counts are low. ⚠️ **Necessary because transcription factors can number in the tens per
cell, where the deterministic ODE is simply wrong.**

---

## §8. PK/PD

**[DURABLE] The quantitative core of dosing.**

**One-compartment IV bolus**: `C(t) = (D/V)·e^(−kt)`, with **half-life** `t½ = ln2/k` and
**clearance** `CL = k·V`.
**⚠️ Clearance is the physiologically meaningful parameter** — volume of plasma cleared per
unit time. **Half-life is derived from CL and V, not fundamental.**

**Steady state on repeated dosing**:
```
C_ss,avg = (F · D) / (CL · τ)
Accumulation ratio = 1/(1 − e^(−kτ))
⚠️ Steady state is reached at ~4–5 half-lives, regardless of dose or interval
```
**Loading dose** `= C_target × V / F` — ⚠️ **because reaching steady state otherwise takes
4–5 half-lives, which for amiodarone (t½ ≈ 58 days) is months.**

**Absorption**: bioavailability `F`, **first-pass metabolism**, `T_max`, `C_max`.
**Distribution**: `V_d` — ⚠️ **an apparent volume, not physical; it can exceed total body
water enormously for tissue-bound drugs.**
**Elimination**: usually first-order; ⚠️ **but saturable (Michaelis–Menten) elimination
makes concentration rise disproportionately with dose — phenytoin and ethanol are the
classic examples, and this is where dosing errors become toxic.**

**PD**: `E = E_max·C^n/(EC₅₀^n + C^n)`. **Direct-effect, effect-compartment (for
hysteresis), and indirect-response models.**

**Population PK (NONMEM/nlmixr/Monolix)** — **nonlinear mixed effects**: fixed effects
(typical values), **random effects** (between-subject variability, usually log-normal:
`P_i = P_typ · e^(η_i)`), and residual error. ⚠️ **Covariates (weight, renal function,
age) explain part of the between-subject variance — allometric scaling `CL ∝ WT^0.75` is
the standard starting point.**

**PBPK** — physiologically-based models with actual organ compartments, blood flows, and
partition coefficients. ⚠️ **Used for extrapolation where you have no data: paediatrics,
organ impairment, drug-drug interactions.**

---

## §9. Physiological Models

**⚠️ Hodgkin–Huxley (1952)** — still the foundation of computational neuroscience:
```
C_m dV/dt = I_ext − ḡ_Na m³h (V−E_Na) − ḡ_K n⁴ (V−E_K) − ḡ_L(V−E_L)
dx/dt = α_x(V)(1−x) − β_x(V)x        for x ∈ {m, h, n}
```
**⚠️ The gating variables are the insight**: `m³h` and `n⁴` — activation raised to a power
(multiple independent gates) times inactivation. **Four coupled nonlinear ODEs producing an
action potential from first principles.**

**Reduced models**: **FitzHugh–Nagumo** (2D, captures excitability and the phase-plane
geometry), **integrate-and-fire** and **Izhikevich** (⚠️ **computationally cheap enough for
large networks, and reproduces most observed spiking patterns with four parameters**).

**Nernst and GHK**:
```
E_ion = (RT/zF)·ln([ion]_out/[ion]_in)      ⚠️ ~61.5/z · log₁₀(ratio) mV at 37 °C
```

**Cardiac electrophysiology**: ionic models (Luo-Rudy, ten Tusscher, O'Hara-Rudy) coupled
by the **monodomain or bidomain** reaction-diffusion equation for tissue propagation.
⚠️ **Reentry and spiral waves are the mechanism of many arrhythmias, and they emerge from
the tissue equations, not the cell model.**

**Hemodynamics**: **Windkessel** — the 2-element model is `C dP/dt + P/R = Q(t)`, a
capacitor-resistor analogue of arterial compliance and peripheral resistance.
**Poiseuille**: `Q = πΔP r⁴/(8µL)` — ⚠️ **the `r⁴` is why a small stenosis has enormous
consequence; halving radius cuts flow 16-fold.**
**Reynolds number** `Re = ρvD/µ` — ⚠️ **blood flow is mostly laminar (Re < 2000); turbulence
appears at stenoses and valves and is what a bruit or murmur is.**
**⚠️ Blood is non-Newtonian** — shear-thinning, with the Fåhræus–Lindqvist effect reducing
apparent viscosity in small vessels.

**Respiratory**: compliance `C = ΔV/ΔP`, resistance, the **equation of motion**
`P = V/C + R·V̇ + PEEP`, and dead space via the Bohr equation.
