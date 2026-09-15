---
name: rocket-turbomachinery-cooling-and-propellants
description: "Use when working on the engine's feed, thermal, or chemical side: why pumps are needed and the pump thermodynamics, the engine cycles compared (gas generator, staged combustion, expander, electric pump) with their pressure and efficiency trade-offs, heat transfer and regenerative cooling including film and ablative cooling and the wall heat flux problem, and propellant chemistry — the common combinations, density versus specific impulse, cryogenics, hypergolics and storability."
---

# Rocket Science: Turbomachinery and Cycles, Heat Transfer and Cooling, and Propellants

> **Part 2 of 5** of the *Rocket Science* reference (plugin `rocket-science`), covering §4–§6. Sibling skills: `rocket-equation-nozzles-and-combustion` (§0–§3), `rocket-orbital-mechanics-and-ascent` (§7–§8), `rocket-aerodynamics-structures-guidance-and-reentry` (§9–§13), `rocket-reference` (§14–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The physics here is settled — Tsiolkovsky 1903, the isentropic relations older still — and nothing in §1-§12 has a currency dependency. See §17 → `rocket-reference` for what is genuinely open.

> **How to read this.** The physics, the derivations, and the numbers — not the industry.
> Where a result matters more than its derivation, the derivation is compressed to its
> load-bearing step.
>
> Two markers only, because this domain barely moves:
> - **[DURABLE]** — settled physics and engineering. Effectively everything below.
> - **[CONTESTED]** — genuinely open questions (§16 → `rocket-reference`, §17 → `rocket-reference`).
>
> **⚠️ GOTCHA** boxes mark where physical intuition actively misleads.
>
> **Notation**: `v_e` exhaust velocity, `Isp` specific impulse, `g₀` = 9.80665 m/s²,
> `ṁ` mass flow, `γ` ratio of specific heats, `R_u` = 8314 J/(kmol·K), `μ` gravitational
> parameter, `c*` characteristic velocity, `C_F` thrust coefficient.
>
> **The three facts that generate everything else:**
> 1. **Momentum conservation with variable mass gives a logarithm** — and that logarithm
>    is why rockets are 90% propellant and why staging exists (§1 → `rocket-equation-nozzles-and-combustion`).
> 2. **A converging-diverging nozzle converts thermal energy to directed kinetic energy**,
>    and its performance factorizes cleanly into `c*` (how good is your combustion) ×
>    `C_F` (how good is your nozzle) — ⚠️ **which is why those two can be measured and
>    optimized independently** (§2 → `rocket-equation-nozzles-and-combustion`).
> 3. **Orbits are energy states, not altitudes.** The vis-viva equation `v² = μ(2/r − 1/a)`
>    determines nearly everything in mission design from two numbers (§7 → `rocket-orbital-mechanics-and-ascent`).

---

## §4. Turbomachinery and Cycles

### 4.1 Why pumps

**[DURABLE]** Pressure-fed systems need tank pressure > chamber pressure. Tank mass scales
with `p·V`, so for a large stage at `p_c` = 10 MPa the tanks would be absurd.
**Turbopumps decouple tank pressure (~0.2–0.4 MPa, mostly for NPSH and structural
stability) from chamber pressure (7–30 MPa).**

**Pump power**: `P = ṁ · Δp / (ρ · η)`.
⚠️ **The numbers are startling** — the SSME's high-pressure fuel turbopump delivers about
**70 MW** from a unit you can lift. That power density is why turbopumps are the hardest
component in the engine.

**⚠️ Cavitation is the recurring failure**. Required **NPSH** (net positive suction head)
must be met or vapour bubbles form and collapse, destroying the impeller. **Inducers**
(axial pre-stages) are fitted specifically to raise suction performance and allow lower
tank pressures — which saves tank mass.

### 4.2 Cycle thermodynamics compared

| Cycle | Turbine drive gas | Turbine exhaust | Isp penalty | p_c ceiling |
|---|---|---|---|---|
| **Pressure-fed** | — | — | none | ⚠️ tank-limited, ~2–3 MPa |
| **Gas generator** | Separate preburner, fuel-rich | **Dumped overboard** | ⚠️ **1–3%** | ~10–12 MPa |
| **Expander** | Fuel heated in cooling jacket | To chamber | ~0 | ⚠️ **heat-transfer-limited** |
| **Expander bleed** | Same, partial flow | Dumped | small | higher than closed expander |
| **Staged combustion (ORSC/FRSC)** | Preburner, oxidizer- or fuel-rich | **Into chamber** | ~0 | 20–26 MPa |
| **Full-flow staged** | Two preburners, both flows | Both into chamber | ~0 | ⚠️ **30+ MPa** |

**⚠️ The expander cycle's fundamental limit is geometric**: available heat scales with
chamber *surface area* (∝ r²) while required power scales with *mass flow* (∝ r³ roughly).
**Beyond ~250 kN there isn't enough wall heat to drive the pump.** This is a hard physical
ceiling, not an engineering shortfall — hence RL10-class engines only.

**⚠️ Full-flow staged combustion's real advantage isn't just Isp**: both turbines run on
gas that has already passed through a preburner, so **turbine inlet temperatures are lower
for a given chamber pressure**, and **no fuel-oxidizer interpropellant seal is needed**
(each turbopump sees only its own propellant). **That seal is a classic failure point** —
eliminating it is a reliability argument as much as a performance one.

**Oxygen-rich staged combustion** is a **materials problem**: hot, high-pressure oxygen
will burn most metals. Soviet/Russian work on burn-resistant alloys and protective coatings
(ZhS6K, enamel coatings) is what made RD-170/RD-180 possible, and it was a genuine
decades-long capability advantage.

---

## §5. Heat Transfer and Cooling

**[DURABLE] Chamber wall heat flux is the highest sustained flux in routine engineering.**

**Typical: 10–160 MW/m² at the throat.** ⚠️ **For comparison, a domestic hob is ~0.05 MW/m².**
The throat is the peak because that's where velocity is highest and the boundary layer
thinnest.

**Gas-side heat transfer** via the **Bartz correlation**:
```
h_g = (0.026/D*^0.2) · (μ^0.2 c_p / Pr^0.6) · (p_c/c*)^0.8 · (D*/R_c)^0.1 · (A*/A)^0.9 · σ
```
where σ corrects for property variation across the boundary layer. ⚠️ **Note
`h_g ∝ p_c^0.8`** — **raising chamber pressure raises heat flux nearly proportionally**,
which is the real constraint on high-p_c engines, not structural strength.

**Cooling approaches:**
- **Regenerative** — propellant through milled channels or brazed tubes before injection.
  ⚠️ **The heat isn't lost — it's returned to the chamber**, so the penalty is pressure
  drop (pump work), not energy.
- **Film / curtain cooling** — a fuel-rich boundary layer at the wall. ⚠️ **Costs Isp
  directly** (that propellant burns poorly), typically 1–3%, but often unavoidable at the
  throat.
- **Ablative** — sacrificial charring liner. Simple, single-use-ish, mass-heavy.
- **Radiative** — for nozzle extensions where `q` is low: `q = εσT⁴`, needing niobium or
  carbon-carbon at 1,300–1,800 K.
- **Transpiration** — porous wall, ultimate performance, rarely used.

**⚠️ The channel design trade**: narrower channels raise coolant velocity and `h_c`,
improving cooling, but raise pressure drop as roughly `Δp ∝ v²`. **And the coolant-side
limit is nucleate-to-film boiling transition** — cross it and heat transfer *collapses* and
the wall burns through in milliseconds.

---

## §6. Propellants

**[DURABLE] The physics that determines choice** (see §2.1 → `rocket-equation-nozzles-and-combustion` — it's `√(T_c/M_w)` plus
density):

| Combination | Isp_vac (s) | ρ_bulk (kg/m³) | T_c (K) | O/F | Notes |
|---|---|---|---|---|---|
| LOX/LH₂ | 450–465 | ⚠️ **~360** | 3,200 | 5.5–6.0 | Best Isp, worst density |
| LOX/CH₄ | 360–380 | ~830 | 3,500 | 3.4–3.8 | Clean, ISRU-able |
| LOX/RP-1 | 340–360 | ~1,030 | 3,700 | 2.3–2.7 | Dense, cokes |
| N₂O₄/MMH | 320–340 | ~1,190 | 3,400 | 1.9–2.2 | Hypergolic, toxic |
| LOX/UDMH | 340–350 | ~1,000 | 3,400 | 1.9 | — |
| APCP (solid) | 250–290 | ~1,800 | 3,000 | — | No shutdown |
| H₂O₂/RP-1 | 300–320 | ~1,250 | 2,900 | 7–8 | Non-toxic monoprop option |

> **⚠️ GOTCHA — density impulse is the metric people omit.**
> `I_ρ = Isp × ρ_bulk`. It measures **impulse per unit tank volume**, and for a
> volume-constrained (rather than mass-constrained) stage it matters more than Isp.
>
> ```
> LOX/LH₂:  450 × 0.36 = 162    ⚠️ lowest
> LOX/CH₄:  370 × 0.83 = 307
> LOX/RP-1: 350 × 1.03 = 361    ⚠️ more than double hydrogen
> N₂O₄/MMH: 330 × 1.19 = 393
> ```
> **This is the quantitative reason hydrogen loses on first stages.** The tank volume —
> and therefore tank mass, insulation mass, and aerodynamic drag — swamps the Isp
> advantage low in the trajectory where mass ratio matters less. **Hydrogen wins where Δv
> is high and structure is a smaller fraction: upper stages and deep space.**

**Cryogenic realities**: LH₂ boils at **20.3 K**, LOX at **90.2 K**, LCH₄ at **111.7 K**.
⚠️ **Methane and oxygen being within ~20 K of each other permits common-bulkhead tanks and
shared insulation** — a real structural advantage that is part of why methane became
popular. **Hydrogen's 20 K requires vacuum-jacketed or foam insulation, and boil-off makes
long coast phases expensive.** **Hydrogen embrittlement** attacks many steels;
**LOX compatibility** rules out most organics and requires scrupulous cleanliness —
⚠️ **a fingerprint in a LOX line is an ignition source.**
