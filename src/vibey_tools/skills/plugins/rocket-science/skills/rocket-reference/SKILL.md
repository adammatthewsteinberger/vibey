---
name: rocket-reference
description: "Use when checking a number that constrains a real vehicle, correcting a common misconception about how rockets work, weighing a contested engineering question, or asking what is genuinely open in the field: the textbook canon, the equations that carry the load, and a diagnostic table for reasoning about a vehicle or an anomaly. Companion to the other rocket-science skills."
---

# Rocket Science: Numbers, Misconceptions, Contested Questions, and the Open Frontier

> **Part 5 of 5** of the *Rocket Science* reference (plugin `rocket-science`), covering §14–§20. Sibling skills: `rocket-equation-nozzles-and-combustion` (§0–§3), `rocket-turbomachinery-cooling-and-propellants` (§4–§6), `rocket-orbital-mechanics-and-ascent` (§7–§8), `rocket-aerodynamics-structures-guidance-and-reentry` (§9–§13). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The physics here is settled — Tsiolkovsky 1903, the isentropic relations older still — and nothing in §1-§12 has a currency dependency. See §17 below for what is genuinely open.

> **How to read this.** The physics, the derivations, and the numbers — not the industry.
> Where a result matters more than its derivation, the derivation is compressed to its
> load-bearing step.
>
> Two markers only, because this domain barely moves:
> - **[DURABLE]** — settled physics and engineering. Effectively everything below.
> - **[CONTESTED]** — genuinely open questions (§16, §17).
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

## §14. Numbers

```
g₀ = 9.80665 m/s²                    R_u = 8314.46 J/(kmol·K)
μ_Earth = 398,600 km³/s²             R_Earth = 6,378 km
μ_Sun = 1.327×10¹¹ km³/s²            μ_Moon = 4,903 km³/s²
μ_Mars = 42,828 km³/s²               1 AU = 1.496×10⁸ km

LEO circular (200 km):  7.784 km/s     Period 88.5 min
GEO:                    3.075 km/s     r = 42,164 km, period 23h56m
Earth escape (surface): 11.18 km/s
Earth rotation at equator: 465 m/s

Scale height H ≈ 7.2 km (troposphere-ish)
Karman line: 100 km    ⚠️ conventional, not physical
Max-Q: 20–40 kPa at 10–15 km
Liftoff T/W: 1.2–1.4
Structural coefficient ε: 0.06–0.10
Payload fraction to LEO: 2–4%
Chamber pressure: 5–30 MPa
Throat heat flux: 10–160 MW/m²
c*: 1,800 (kerolox) – 2,350 m/s (hydrolox)
C_F: 1.5–1.9
Reentry energy: ~30 MJ/kg from LEO
```

---

## §15. Misconceptions

| Claim | Reality |
|---|---|
| "Rockets push against the air" | ⚠️ **Momentum conservation; they work better in vacuum** (§1.1 → `rocket-equation-nozzles-and-combustion`) |
| "Space starts at 100 km" | Conventional boundary. ⚠️ **Orbit is about 7.8 km/s, not altitude** (§7.1 → `rocket-orbital-mechanics-and-ascent`) |
| "Suborbital ≈ orbital" | ⚠️ **~40× the energy** (§7.1 → `rocket-orbital-mechanics-and-ascent`) |
| "Reentry heat is friction" | ⚠️ **Compression in the shock layer** (§12 → `rocket-aerodynamics-structures-guidance-and-reentry`) |
| "Sharper = better for reentry" | ⚠️ **Blunter reduces peak flux (`q ∝ 1/√R_n`)** (§12 → `rocket-aerodynamics-structures-guidance-and-reentry`) |
| "Hydrogen is always the best fuel" | ⚠️ **Worst density impulse; loses on first stages** (§6 → `rocket-turbomachinery-cooling-and-propellants`) |
| "Burn stoichiometric for max Isp" | ⚠️ **Fuel-rich wins — `v_e ∝ √(T_c/M_w)`** (§2.1 → `rocket-equation-nozzles-and-combustion`) |
| "Bigger nozzle is always better" | ⚠️ **Flow separation and side loads at sea level** (§2.3 → `rocket-equation-nozzles-and-combustion`) |
| "Astronauts float because there's no gravity" | Gravity at ISS is ~89% of surface. **They're in free fall** |
| "Speed up to catch a target ahead" | ⚠️ **Raises your orbit and slows you down. Slow down to catch up** (§7.2 → `rocket-orbital-mechanics-and-ascent`) |
| "Plane changes are cheap" | ⚠️ **28.5° at LEO ≈ 3.8 km/s** (§7.2 → `rocket-orbital-mechanics-and-ascent`) |
| "Peak reentry g depends on the vehicle" | ⚠️ **Allen–Eggers: independent of ballistic coefficient** (§12 → `rocket-aerodynamics-structures-guidance-and-reentry`) |
| "Higher T/W at liftoff is always better" | Raises max-Q and structural loads (§8 → `rocket-orbital-mechanics-and-ascent`, §9 → `rocket-aerodynamics-structures-guidance-and-reentry`) |
| "SSTO just needs better engines" | ⚠️ **Marginal on mass fraction, not Isp** (§16.1) |
| "Classical buckling theory sizes the tank" | ⚠️ **Over-predicts by up to 5×; knockdowns are empirical** (§10 → `rocket-aerodynamics-structures-guidance-and-reentry`) |
| "Aerospikes are obviously better" | ⚠️ **Never flown operationally; base heating, cooling, mass** (§16.3) |

---

## §16. Contested

**16.1 Is SSTO viable?** The physics permits it — with `Isp` = 450 s and `ε` = 0.08,
`Δv` = 9.4 km/s gives a payload fraction of about 1%. ⚠️ **The dispute is whether ~1% is a
vehicle or a stunt.** Any mass growth eats the entire payload, and the thing that kills SSTO
proposals is always structural mass, not propulsion. **Two-stage-to-orbit with a reusable
first stage is the position the industry converged on**, and the argument that it was
always the right answer is strong.

**16.2 Nuclear thermal propulsion.** ~900 s Isp at high thrust is genuinely transformative
for Mars. ⚠️ **The counterarguments are non-technical as much as technical**: ground testing
a nuclear engine, launch-abort scenarios, and political durability across the decade it
takes. **The physics has been demonstrated (NERVA, 1960s); the programme durability never
has.**

**16.3 Altitude-compensating nozzles.** ~5–8% mission-averaged Isp gain in principle.
⚠️ **Against: base heating on a truncated aerospike, cooling a large surface, mass, and
the fact that a simple bell has decades of reliability data.** No operational flight. **The
theoretical advantage has been known since the 1960s and has never survived a trade study.**

**16.4 How much does Isp actually matter versus cost?** ⚠️ **A genuine strategic split.**
The performance-maximizing tradition treats Isp as near-sacred; the manufacturing-cost
tradition accepts lower Isp for cheaper, faster-built, higher-cadence hardware.
**Gas-generator kerolox at 311 s outcompeted staged-combustion hydrolox at 450 s
commercially** — which is an argument that the rocket equation is not the only equation.

---

## §17. What's Actually Open

**[DURABLE] Unusually for a technical field, the fundamentals are closed.** Newtonian
mechanics, thermodynamics, and the conservation laws are not in dispute, and no result in
§1–§12 → `rocket-equation-nozzles-and-combustion`, `rocket-turbomachinery-cooling-and-propellants`, `rocket-orbital-mechanics-and-ascent`, `rocket-aerodynamics-structures-guidance-and-reentry` is going to be revised. **What remains genuinely unsolved is engineering, not
physics:**

- **⚠️ Combustion instability prediction.** Still substantially empirical after 70 years.
  CFD has improved dramatically and it is still not the case that you can confidently
  design a stable injector without testing.
- **⚠️ Turbulence and boundary-layer transition.** The closure problem is unsolved;
  transition location on a reentry vehicle is a genuine uncertainty that drives TPS margin.
- **Long-duration cryogenic storage and zero-g propellant transfer.** ⚠️ **The physics is
  understood; the engineering is not demonstrated at scale.** Settling, thermal management,
  and gauging in microgravity are open practical problems.
- **Buckling knockdown factors.** ⚠️ **Still empirical (NASA SP-8007, 1968).** Modern
  probabilistic approaches exist but conservative empiricism remains the design basis.
- **Reusable TPS life prediction.** Inspection and certification of ceramic systems for
  repeated flight remains unsolved economically.
- **Ablation modelling** — pyrolysis, char, and surface recession coupling.

**Everything else in this document you can take to the bank.**

---

## §18. Textbooks

| Author | Work | Why |
|---|---|---|
| **Sutton & Biblarz** | ***Rocket Propulsion Elements*** (9th ed.) | ⚠️ **The standard. If you own one propulsion book, this is it** |
| **Huzel & Huang** | *Modern Engineering for Design of Liquid-Propellant Rocket Engines* | ⚠️ **NASA SP-125 — the actual engine design manual, and free** |
| **Curtis** | ***Orbital Mechanics for Engineering Students*** | The best entry point to §7 → `rocket-orbital-mechanics-and-ascent`; worked and readable |
| **Vallado** | ***Fundamentals of Astrodynamics and Applications*** | ⚠️ **The professional reference. Exhaustive, with algorithms** |
| **Bate, Mueller & White** | *Fundamentals of Astrodynamics* | ⚠️ **The 1971 USAF Academy text. Cheap, superb, still unmatched on intuition** |
| **Battin** | *An Introduction to the Mathematics and Methods of Astrodynamics* | The deep end. Lambert's problem definitively |
| **Anderson** | *Hypersonic and High-Temperature Gas Dynamics* | §12 → `rocket-aerodynamics-structures-guidance-and-reentry`, rigorously |
| **Anderson** | *Modern Compressible Flow* | §2 → `rocket-equation-nozzles-and-combustion`'s isentropic relations, properly derived |
| **Hill & Peterson** | *Mechanics and Thermodynamics of Propulsion* | Cycles and turbomachinery (§4 → `rocket-turbomachinery-cooling-and-propellants`) |
| **Humble, Henry & Larson** | *Space Propulsion Analysis and Design* | Systems-level integration |
| **Wertz & Larson** | *Space Mission Analysis and Design* (SMAD) | The systems-engineering bible |
| **Regan & Anandakrishnan** | *Dynamics of Atmospheric Re-Entry* | §12 → `rocket-aerodynamics-structures-guidance-and-reentry` in depth |
| **Griffin & French** | *Space Vehicle Design* | Vehicle-level |
| **NASA SP-8007** | *Buckling of Thin-Walled Circular Cylinders* | ⚠️ **Still the design basis for §10 → `rocket-aerodynamics-structures-guidance-and-reentry`** |

**Tools**: **NASA CEA** (Chemical Equilibrium with Applications — ⚠️ **the standard for
computing `c*`, `T_c`, and equilibrium composition; free, and every propulsion engineer
uses it**), **GMAT** (NASA's mission analysis tool, open source), **Poliastro/Orekit**
(astrodynamics libraries), **RPA** (rocket propulsion analysis), **JPL Horizons** for
ephemerides, **STK** commercially.

---

## §19. Quick Reference

### 19.1 The equations that carry the load
```
Δv = Isp·g₀·ln(m₀/m_f)                        rocket equation
F = ṁ·v_e + (p_e−p_a)·A_e                     thrust
Isp·g₀ = c* · C_F                             performance factorization
v_e = √( (2γ/(γ−1))·(R_u T_c/M_w)·[1−(p_e/p_c)^((γ−1)/γ)] )
v² = μ(2/r − 1/a)                             vis-viva
ε = −μ/(2a)                                   specific energy
T = 2π√(a³/μ)                                 period
Δv_plane = 2v·sin(Δi/2)                       plane change
q_s = k·√(ρ/R_n)·v³                           Sutton–Graves stagnation heating
a_max = v_e²·sin γ/(2eH)                      Allen–Eggers peak deceleration
σ_h = pR/t                                    hoop stress
I_ρ = Isp × ρ_bulk                            density impulse
```

### 19.2 Diagnostic table
| Symptom | Physics |
|---|---|
| Low measured Isp, `c*` nominal | Nozzle: separation, contour, or expansion ratio (§2.3 → `rocket-equation-nozzles-and-combustion`) |
| Low `c*` | Injector mixing / incomplete combustion (§3 → `rocket-equation-nozzles-and-combustion`) |
| High-frequency chamber oscillation | ⚠️ Tangential acoustic mode (§13.1 → `rocket-aerodynamics-structures-guidance-and-reentry`) |
| Longitudinal vehicle oscillation | ⚠️ POGO — feedline/structure coupling (§10 → `rocket-aerodynamics-structures-guidance-and-reentry`) |
| Wall burn-through at throat | Coolant boiling crisis or channel blockage (§5 → `rocket-turbomachinery-cooling-and-propellants`) |
| Turbopump destroyed on start | ⚠️ Cavitation / insufficient NPSH (§4.1 → `rocket-turbomachinery-cooling-and-propellants`) |
| Control divergence late in burn | Slosh, or bending mode as CoM shifts (§11 → `rocket-aerodynamics-structures-guidance-and-reentry`) |
| Payload short of target orbit | Check gravity loss and staging velocity (§8 → `rocket-orbital-mechanics-and-ascent`) |
| Buckled tank at max-g | ⚠️ Empty tank, high axial load — knockdown factor (§10 → `rocket-aerodynamics-structures-guidance-and-reentry`) |
| TPS recession above prediction | Radiative heating or transition location (§12 → `rocket-aerodynamics-structures-guidance-and-reentry`, §17) |

---

## §20. Method

**This document is physics, not reporting.** §1–§14 → `rocket-equation-nozzles-and-combustion`, `rocket-turbomachinery-cooling-and-propellants`, `rocket-orbital-mechanics-and-ascent`, `rocket-aerodynamics-structures-guidance-and-reentry` rest on Sutton & Biblarz,
Huzel & Huang (NASA SP-125), Vallado, Curtis, Bate/Mueller/White, Anderson, and the
primary results they compile — **Tsiolkovsky (1903), Allen & Eggers (NACA, 1958),
Sutton & Graves (1971), Bartz (1957), NASA SP-8007 (1968)**. None of it has a currency
dependency and none of it was web-verified, because the standard texts are the authority
and they are stable.

**Confidence**: **very high** throughout §1–§14 → `rocket-equation-nozzles-and-combustion`, `rocket-turbomachinery-cooling-and-propellants`, `rocket-orbital-mechanics-and-ascent`, `rocket-aerodynamics-structures-guidance-and-reentry` — these are closed results, cross-checked
against the standard references, with derivations included so you can verify rather than
trust. **The worked numbers in §1.3 → `rocket-equation-nozzles-and-combustion` and §7.2 → `rocket-orbital-mechanics-and-ascent` I computed here**; they're arithmetic on
stated assumptions, so check the assumptions rather than the arithmetic. **Order-of-magnitude
figures** (heat flux ranges, `c*` values, structural coefficients) are representative
engineering values that vary by design — treat them as sizing guidance, not specifications.

⚠️ **§16 is engineering judgement, not physics**, and reasonable specialists disagree —
particularly on SSTO and on the Isp-versus-cost question, where the disagreement is really
about economics and programme risk wearing a technical costume. **§17's list of open
problems is my assessment** of where prediction still fails; a combustion specialist might
draw the boundary differently.
