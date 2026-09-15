---
name: nuclear-structure-decay-reactions-and-dose
description: "Use when working with nuclei and radiation at the physics level: nuclear structure and the binding energy curve that explains why both fission and fusion release energy, radioactive decay modes and kinetics, nuclear reactions and cross sections including resonances and the energy dependence that matters, and radiation and dose — the quantities, units and the biological effect they are meant to capture. Includes the router for the whole nuclear-physics reference."
---

# Nuclear Physics: Nuclear Structure, Radioactive Decay, Reactions and Cross Sections, and Dose

> **Part 1 of 5** of the *Nuclear Physics* reference (plugin `nuclear-physics`), covering §0–§4. Sibling skills: `nuclear-fission-reactor-physics-and-reactor-types` (§5–§7), `nuclear-fuel-cycle-waste-and-safety` (§8–§9), `nuclear-fusion-confinement-and-detection` (§10–§14), `nuclear-reference` (§15–§21). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Nuclear physics is settled — Rutherford 1911, Chadwick 1932, Hahn-Meitner-Frisch 1938, Lawson 1957, Bethe. Fusion milestones and the fission build picture moved. See §16 → `nuclear-reference` for both.

> **Scope.** ⚠️ **This covers nuclear physics and nuclear *energy* — reactor physics,
> fusion, radiation, and the fuel cycle.** **It does not cover weapon design, and §17 → `nuclear-reference`
> says why plainly.** The physics here is standard undergraduate and graduate curriculum
> material.
>
> **⚠️ GOTCHA** boxes mark misconceptions and places where intuition fails — and public
> understanding of this subject is unusually poor, so §15 → `nuclear-reference` is long.
>
> **The three ideas that organize everything:**
> 1. **⚠️ The binding energy curve explains fission and fusion in one picture.** Iron-56 is
>    the most tightly bound nucleus. **Anything heavier releases energy by splitting;
>    anything lighter releases energy by fusing.** Both run downhill toward iron (§1.2).
> 2. **⚠️ Nuclear energy densities are about a million times chemical.** Same Coulomb
>    barrier scaling that makes them hard to initiate makes them enormous once initiated.
>    **Every practical consequence — fuel volumes, waste volumes, accident severity —
>    follows from that factor** (§18 → `nuclear-reference`).
> 3. **⚠️ Reactor safety is dominated by decay heat, not by the chain reaction.** You can
>    stop fission in under a second. **You cannot stop the ~7% residual heat from fission
>    products, and every major accident is a failure to remove it** (§9 → `nuclear-fuel-cycle-waste-and-safety`).

---

## §0. Routing

| You want... | Go to |
|---|---|
| **Nuclear structure and binding energy** | **§1** |
| Radioactive decay | §2 |
| Reactions and cross sections | §3 |
| **Radiation and dose** | **§4** |
| **Fission physics** | **§5 → `nuclear-fission-reactor-physics-and-reactor-types`** |
| **Reactor physics** | **§6 → `nuclear-fission-reactor-physics-and-reactor-types`** |
| Reactor types | §7 → `nuclear-fission-reactor-physics-and-reactor-types` |
| Fuel cycle and waste | §8 → `nuclear-fuel-cycle-waste-and-safety` |
| **Reactor safety and accidents** | **§9 → `nuclear-fuel-cycle-waste-and-safety`** |
| **Fusion physics** | **§10 → `nuclear-fusion-confinement-and-detection`** |
| Magnetic confinement | §11 → `nuclear-fusion-confinement-and-detection` |
| Inertial confinement | §12 → `nuclear-fusion-confinement-and-detection` |
| **Why fusion is hard to engineer** | **§13 → `nuclear-fusion-confinement-and-detection`** |
| Detection and measurement | §14 → `nuclear-fusion-confinement-and-detection` |
| **Misconceptions** | **§15 → `nuclear-reference`** |
| **What moved** | **§16 → `nuclear-reference`** |
| Scope note | §17 → `nuclear-reference` |
| Numbers | §18 → `nuclear-reference` |
| Books | §19 → `nuclear-reference` |
| Quick reference | §20 → `nuclear-reference` |

---

## §1. Nuclear Structure

### 1.1 The basics
**Nucleus** = `Z` protons + `N` neutrons, `A = Z + N`. **Isotopes** share `Z`;
⚠️ **isotopes are chemically near-identical and nuclearly completely different — which is
the entire basis of enrichment and of why `²³⁸U` and `²³⁵U` behave so differently.**

**The four forces at nuclear scale**: **strong** (⚠️ **binds nucleons, range ~1 fm, and
its short range is why big nuclei become unstable — every proton repels every other, but
only neighbours attract**), **electromagnetic** (repels protons), **weak** (beta decay),
gravity (negligible).

**⚠️ The semi-empirical mass formula (liquid drop model)** captures most binding energy in
five terms:
```
volume − surface − Coulomb − asymmetry − pairing
```
⚠️ **It explains the shape of the binding curve, the valley of stability, and — with the
fissility parameter `Z²/A` — why fission becomes energetically favourable for heavy
nuclei.**
**Shell model** adds the quantum structure: ⚠️ **magic numbers 2, 8, 20, 28, 50, 82, 126
mark closed shells and unusual stability.** ⚠️ **Doubly-magic `²⁰⁸Pb` is why the decay
chains end where they do.**

### 1.2 ⚠️ The binding energy curve
**Binding energy per nucleon vs mass number.** ⚠️ **This one curve is the whole subject:**
```
Rises steeply from H to ~A=56       ⚠️ FUSION releases energy here
Peak at ⁵⁶Fe / ⁶²Ni  (~8.8 MeV/nucleon)
Declines slowly to U               ⚠️ FISSION releases energy here
```
**Mass defect**: the bound nucleus weighs less than its parts, and `E = mc²` gives the
difference. ⚠️ **Nuclear reactions convert a fraction of a percent of mass into energy;
chemical reactions convert ~10⁻¹⁰. That ratio is the million-fold factor.**

---

## §2. Radioactive Decay

```
Alpha (α)      ⚠️ emits ⁴He; heavy nuclei; quantum TUNNELLING through the Coulomb
               barrier — which is why half-lives span 30 orders of magnitude
Beta-minus     n → p + e⁻ + ν̄ₑ    ⚠️ neutron-rich nuclei
Beta-plus / EC p → n + e⁺ + νₑ    proton-rich
Gamma (γ)      ⚠️ NOT a change of nuclide — de-excitation of an excited state
Spontaneous fission · neutron emission (⚠️ delayed neutrons — see §6.3)
```
**Decay law**: `N(t) = N₀e^{−λt}`, `t½ = ln2/λ`, activity `A = λN` in becquerels.
**⚠️ Secular equilibrium**: when a long-lived parent feeds a short-lived daughter, the
daughter's activity rises to match the parent's. **This is why radon (3.8 d) persists in
uranium-bearing rock indefinitely.**

> **⚠️ GOTCHA — long half-life means LOW activity, and this inverts most people's
> intuition.** ⚠️ **Activity is `λN`, and `λ = ln2/t½`.** **`²³⁸U` (4.5 billion years) is
> barely radioactive — you can hold it. `¹³¹I` (8 days) is intensely radioactive and
> dangerous.** **"It stays radioactive for 10,000 years" and "it is dangerously
> radioactive" are close to opposites**, and the confusion drives a lot of bad reasoning
> about waste (§8 → `nuclear-fuel-cycle-waste-and-safety`).

---

## §3. Reactions and Cross Sections

**Notation** `X(a,b)Y`. **Q-value** positive = exothermic.
**⚠️ Cross section `σ`** in **barns** (10⁻²⁸ m²) — ⚠️ **an effective target area, and it is
a *probability*, not a geometric size. It can be far larger than the physical nucleus.**

**⚠️ Energy dependence is the crux of reactor design:**
- **1/v behaviour** at low energy — ⚠️ **slower neutrons spend longer near the nucleus, so
  absorption cross sections rise as `1/√E`.**
- **Resonances** at specific energies — ⚠️ **enormous, narrow peaks.** **The resonance
  region in `²³⁸U` is why moderation must be *fast* through it** (§6.2 → `nuclear-fission-reactor-physics-and-reactor-types`).
- **Thresholds** for endothermic reactions.

**⚠️ The number that drives reactor physics**: the fission cross section of `²³⁵U` is
**~585 barns for thermal neutrons and ~1–2 barns for fast neutrons.** ⚠️ **A factor of
several hundred.** **That is why thermal reactors can run on low-enriched fuel and fast
reactors cannot.**

---

## §4. Radiation and Dose

| Type | Range in matter | ⚠️ Hazard |
|---|---|---|
| **Alpha** | ⚠️ **cm of air; stopped by skin/paper** | ⚠️ **Negligible externally; severe INTERNALLY (inhaled/ingested)** |
| **Beta** | mm of plastic | Skin and eye dose; internal |
| **Gamma/X** | ⚠️ **attenuates exponentially — no definite range** | Whole-body penetrating |
| **Neutron** | Needs hydrogenous shielding | ⚠️ **Highly damaging; activates materials** |

**⚠️ Shielding logic follows the interaction mechanism**: **hydrogen-rich material
(water, polyethylene, concrete) to moderate neutrons, then a thermal absorber (boron);
high-Z material (lead) for gamma.** ⚠️ **High-Z alone is poor for neutrons, and moderating
material alone is poor for gamma. Layered shields are the norm.**

**Dose quantities — routinely muddled:**
```
Activity     becquerel (Bq)   ⚠️ decays/second — a property of the SOURCE
Absorbed     gray (Gy)        J/kg deposited
Equivalent   sievert (Sv)     ⚠️ Gy × radiation weighting (α ≈ 20, γ/β = 1)
Effective    sievert          ⚠️ × tissue weighting — whole-body risk proxy
```
**⚠️ Bq tells you nothing about hazard on its own.** **A large Bq number from a weak
alpha emitter safely contained is harmless; a small number inhaled is not.** **Reporting
becquerels without geometry, isotope and pathway is uninformative.**

**⚠️ Deterministic vs stochastic effects — the distinction that governs everything:**
- **Deterministic** — ⚠️ **have a threshold, severity rises with dose.** Radiation
  sickness, burns, cataracts. **Below threshold, they do not occur.**
- **Stochastic** — ⚠️ **cancer risk; probability rises with dose, severity does not.**
  **Assumed by regulation to have no threshold (LNT), which is a conservative policy
  choice and is scientifically contested at low doses** (§15 → `nuclear-reference`).

**ALARA**: **time, distance** (⚠️ **inverse square — the cheapest control by far**),
**shielding**.
