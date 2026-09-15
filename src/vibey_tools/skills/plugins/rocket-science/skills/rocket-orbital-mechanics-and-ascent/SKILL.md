---
name: rocket-orbital-mechanics-and-ascent
description: "Use when working the trajectory: the two-body problem, orbital elements, the vis-viva equation, manoeuvres (Hohmann transfers, plane changes, bi-elliptic), patched conics and interplanetary transfers including gravity assists and porkchop plots, orbital perturbations (J2, drag, third-body, solar radiation pressure), and ascent trajectory design — gravity turn, max-Q, gravity and drag losses, and throttle and staging scheduling."
---

# Rocket Science: Orbital Mechanics and the Ascent Trajectory

> **Part 3 of 5** of the *Rocket Science* reference (plugin `rocket-science`), covering §7–§8. Sibling skills: `rocket-equation-nozzles-and-combustion` (§0–§3), `rocket-turbomachinery-cooling-and-propellants` (§4–§6), `rocket-aerodynamics-structures-guidance-and-reentry` (§9–§13), `rocket-reference` (§14–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    determines nearly everything in mission design from two numbers (§7).

---

## §7. Orbital Mechanics

### 7.1 The two-body problem

**[DURABLE]** From Newton, the relative motion of two point masses:
```
r̈ = −μ · r̂ / r²,        μ = G(M+m) ≈ GM
```
Solutions are conic sections. The **orbit equation**:
```
r = h²/μ · 1/(1 + e·cos θ)
```
with specific angular momentum `h = r × v` and eccentricity vector
`e = (v×h)/μ − r̂`.

**Specific orbital energy**: `ε = v²/2 − μ/r = −μ/(2a)`
⚠️ **Energy depends only on semi-major axis.** Two wildly different-looking orbits with the
same `a` have the same energy and the same period.

**Rearranged, this gives the vis-viva equation — the single most useful formula in
mission design:**
```
v² = μ · (2/r − 1/a)
```
**Circular**: `v = √(μ/r)`. **Escape**: `v = √(2μ/r) = √2 · v_circ`.
⚠️ **Escape velocity is only 41% more than circular velocity** — a surprisingly small
margin, and the reason interplanetary departure is cheaper than intuition suggests.

**Period**: `T = 2π√(a³/μ)` (Kepler's third).

**Kepler's equation** for position in time: `M = E − e·sin E`, with `M = n(t − t_p)`.
⚠️ **Transcendental — no closed-form solution for E.** Newton-Raphson converges in a few
iterations; this is the standard numerical kernel in every propagator.

### 7.2 Manoeuvres

**Hohmann transfer** (two burns, minimum energy for coplanar circular-to-circular):
```
Δv₁ = √(μ/r₁) · [√(2r₂/(r₁+r₂)) − 1]
Δv₂ = √(μ/r₂) · [1 − √(2r₁/(r₁+r₂))]
```
**Worked — LEO (6,678 km) to GEO (42,164 km), μ_E = 398,600 km³/s²:**
```
v₁ = √(398600/6678) = 7.726 km/s
a_t = (6678+42164)/2 = 24,421 km
v_p,t = √(398600·(2/6678 − 1/24421)) = 10.239 km/s → Δv₁ = 2.513 km/s
v_a,t = √(398600·(2/42164 − 1/24421)) = 1.622 km/s
v₂ = √(398600/42164) = 3.075 km/s        → Δv₂ = 1.453 km/s
Total = 3.966 km/s   (⚠️ plus ~1.8 km/s if changing 28.5° inclination at GEO)
```

**⚠️ Bi-elliptic beats Hohmann when `r₂/r₁ > 11.94`** — a three-burn transfer via a very
high apoapsis. Counterintuitive, and genuinely used for some high-energy transfers.

**Plane change**: `Δv = 2v·sin(Δi/2)`.
⚠️ **At LEO velocity, a 28.5° plane change costs 3.8 km/s — more than reaching GEO.**
This is why you **launch into your target inclination**, why launch-site latitude is a
hard mission constraint, and why plane changes are done at apoapsis where `v` is smallest.

**Combined manoeuvre**: doing the plane change during the GEO circularization burn uses
vector addition rather than sequential burns:
`Δv = √(v₁² + v₂² − 2v₁v₂·cos Δi)` — ⚠️ **saves several hundred m/s and is standard
practice.**

**The Oberth effect**: for a burn `Δv` at speed `v`, energy change is
`Δε = v·Δv + Δv²/2`. ⚠️ **The `v·Δv` term means the same propellant buys more energy when
you're moving faster** — hence departure burns at periapsis, and the value of dropping deep
into a gravity well before burning.

### 7.3 Patched conics and interplanetary

**[DURABLE]** Divide the trajectory into segments where a single body dominates. The
**sphere of influence** radius:
```
r_SOI = a_planet · (m_planet/M_sun)^(2/5)
```
Earth: ~924,000 km. ⚠️ **A useful fiction, not physics — the transition is smooth in
reality, but the approximation is good to a fraction of a percent for preliminary design.**

**Hyperbolic excess velocity** `v_∞` is the speed relative to the planet at SOI exit, with
`C₃ = v_∞²` the **characteristic energy** — the number launch vehicle performance charts
are plotted against. Departure burn from a parking orbit:
```
v_p = √(v_∞² + 2μ/r_p)
```
⚠️ **Note the Oberth benefit is embedded here**: the `2μ/r_p` term means you need far less
than `v_∞` added to your orbital speed.

**Gravity assists**: in the planet's frame, `|v_∞|` is unchanged — only its **direction**
rotates by `2·arcsin(1/e)`. In the heliocentric frame, that rotation changes the heliocentric
speed. ⚠️ **Free Δv, paid for in launch-window rigidity and flight time**, and the reason
outer-planet missions have such constrained launch periods.

**Lambert's problem** — given two position vectors and a transfer time, find the orbit.
⚠️ **The computational core of all trajectory design**; solved by Gauss, Battin, or
universal-variable formulations, and what a porkchop plot is a visualization of.

### 7.4 Perturbations

Real orbits aren't Keplerian. The dominant terms, in order:

**J₂ (Earth oblateness, J₂ = 1.0826×10⁻³)** — by far the largest. Causes secular drift:
```
Ω̇ = −(3/2)·J₂·(R_E/p)²·n·cos i          [nodal regression]
ω̇ = (3/4)·J₂·(R_E/p)²·n·(5cos²i − 1)    [apsidal precession]
```
**⚠️ Two elegant exploitations:**
- **Sun-synchronous orbit**: choose `i` so `Ω̇` = 0.9856°/day (Earth's mean motion about the
  Sun). At 800 km this gives **i ≈ 98.6°** — retrograde. **The orbit precesses to keep
  local solar time constant**, which is why imaging satellites always see the same
  lighting.
- **Molniya orbit**: set `5cos²i − 1 = 0` → **i = 63.4°**, freezing apsidal precession so
  apogee stays over the northern hemisphere. Highly eccentric, 12-hour period, long
  northern dwell.

**Drag** — dominant below ~600 km: `a_drag = −(1/2)·ρ·(C_D·A/m)·v²·v̂`.
⚠️ **`ρ` varies by more than an order of magnitude with solar activity**, making reentry
prediction genuinely uncertain. Ballistic coefficient `β = m/(C_D·A)` determines lifetime.

**Third-body** (Moon, Sun), **solar radiation pressure** (~4.5 μN/m² at 1 AU; dominant for
high area-to-mass), and **higher geopotential terms** — ⚠️ **the J₂₂ tesseral term drives
GEO satellites toward two stable longitudes, requiring east-west station-keeping.**

---

## §8. Ascent Trajectory

**[DURABLE] The Δv budget in full:**
```
Δv_required = Δv_orbital + Δv_gravity + Δv_drag + Δv_steering − Δv_rotation
```

**Gravity loss**: `∫ g·sin γ dt` where γ is flight path angle.
⚠️ **This is the big one — 1.2–1.7 km/s for a typical launch.** Minimized by pitching over
early and by high initial thrust-to-weight. **At T/W = 1.0 you hover and lose 9.8 m/s per
second of hovering**; practical liftoff T/W is **1.2–1.4**, and higher isn't automatically
better because it raises max-Q and structural loads (§9 → `rocket-aerodynamics-structures-guidance-and-reentry`).

**Drag loss**: `∫ (D/m) dt` — typically **only 100–150 m/s**, ⚠️ **much smaller than people
expect**, because the vehicle is through the dense atmosphere quickly. This is why
aerodynamic optimization matters far less for rockets than for aircraft.

**Steering loss**: `∫ a·(1 − cos α) dt` — thrust not aligned with velocity.

**Earth rotation credit**: `465·cos(latitude)` m/s eastward.
Kourou (5.2°N): 463 m/s. Cape Canaveral (28.5°N): 409 m/s. Baikonur (45.6°N): 325 m/s.
⚠️ **Which is why equatorial sites are valuable and why polar/retrograde launches forfeit
this entirely** (and pay double to cancel it).

**The gravity turn**: after a vertical rise, pitch slightly, then let gravity rotate the
velocity vector with **zero angle of attack**. ⚠️ **Zero-α is not an efficiency choice —
it's a structural one.** Aerodynamic side loads on a long thin cylinder at angle of attack
generate bending moments that the structure can't take (§9 → `rocket-aerodynamics-structures-guidance-and-reentry`, §10 → `rocket-aerodynamics-structures-guidance-and-reentry`).

**Max-Q** occurs where `q = ½ρv²` peaks — ⚠️ **typically 30–90 s, at 10–15 km, at
20–40 kPa.** Density is falling while velocity rises; the product peaks. **Engines throttle
down through it** to limit loads.
