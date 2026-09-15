---
name: rocket-aerodynamics-structures-guidance-and-reentry
description: "Use when the vehicle itself is the problem: aerodynamic loads and the max-Q and angle-of-attack constraints, structural mechanics of thin-walled tanks including buckling, common bulkheads and pressure stabilization, guidance and control mathematics (steering laws, thrust vector control, slosh and flexible-body modes), reentry heating physics with the Fay-Riddell and Sutton-Graves relations and ablative versus radiative thermal protection, and combustion instabilities and the physics of characteristic failure modes."
---

# Rocket Science: Aerodynamics and Loads, Structures, Guidance and Control, Reentry, and Failure Physics

> **Part 4 of 5** of the *Rocket Science* reference (plugin `rocket-science`), covering §9–§13. Sibling skills: `rocket-equation-nozzles-and-combustion` (§0–§3), `rocket-turbomachinery-cooling-and-propellants` (§4–§6), `rocket-orbital-mechanics-and-ascent` (§7–§8), `rocket-reference` (§14–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §9. Aerodynamics and Loads

**Dynamic pressure** `q = ½ρv²` drives everything structural in the atmosphere.
**Aerodynamic normal force** `N = q·S·C_N·α`, and the resulting **bending moment**
`M ≈ q·α·(something)` — ⚠️ **the `q·α` product is the load metric launch vehicles are
actually flown to.** Guidance limits `q·α`, and **wind shear is dangerous precisely because
it creates α that the vehicle didn't command.**

**⚠️ Launch vehicles are aerodynamically unstable** — the centre of pressure is typically
ahead of the centre of mass, so any disturbance grows. **They are actively stabilized by
thrust vectoring**, which is why a control failure is immediately catastrophic rather than
gradually degrading. Fins (on some vehicles) move CP aft.

**Transonic** (M 0.8–1.2) brings shock formation, buffet, and a drag rise; **supersonic**
brings wave drag. **Base drag** behind the vehicle is significant and is one reason engine
plumes matter aerodynamically.

**Acoustic loads at liftoff: 160–180 dB OASPL.** ⚠️ **Water deluge isn't for cooling
primarily — it's acoustic suppression**, protecting the payload and vehicle from
reflected acoustic energy that could shake components apart.

---

## §10. Structures

**[DURABLE] The governing failure mode is buckling, not yielding.**

**Euler column buckling**: `P_cr = π²EI/(KL)²`.
**Thin-walled cylinder axial buckling** — the practically important case:
```
σ_cr = γ · E · t/(R·√(3(1−ν²)))
```
⚠️ **γ is a knockdown factor of 0.15–0.65** because real cylinders are exquisitely sensitive
to imperfections. **Classical theory over-predicts buckling strength by up to 5×** — this
is one of the few places in engineering where linear theory is dramatically wrong, and
NASA SP-8007 empirical knockdowns are still the working design basis.

**Pressure stabilization**: internal pressure adds a tensile stress that raises the
effective buckling threshold. ⚠️ **Atlas's balloon tanks took this to the limit — the
vehicle would collapse under its own weight if depressurized.** Structurally brilliant,
operationally demanding.

**Hoop and longitudinal stress** in a thin cylinder: `σ_h = pR/t`, `σ_l = pR/(2t)`.
⚠️ **Hoop is twice longitudinal** — which is why cylindrical tanks fail along a longitudinal
seam and why weld orientation matters.

**Stiffening**: **isogrid** (equilateral triangular pockets machined from plate — high
efficiency, expensive), **orthogrid**, **skin-stringer**, **sandwich**.

**Load cases that size the structure:**
```
Max-Q            bending + axial, mid-atmosphere
Max-g            late in burn — ⚠️ vehicle nearly empty, high acceleration
Liftoff release  transient twang
Landing (if reusable)  ⚠️ an entirely additional load path
```

**Common bulkhead** between tanks saves length and mass but ⚠️ **must handle a large ΔT
across it** (LOX at 90 K, RP-1 at ambient) and any pressure reversal.

**⚠️ POGO**: a closed-loop instability coupling structural longitudinal modes → feedline
pressure oscillation → thrust oscillation → structure. **Nearly destroyed Apollo 13's
S-II.** Suppressed with **gas-filled accumulators in the feedlines** that detune the
hydraulic resonance.

---

## §11. Guidance and Control

**Attitude dynamics** — Euler's equations for a rigid body:
```
I·ω̇ + ω × (I·ω) = M
```
⚠️ **The `ω × Iω` gyroscopic coupling term is why 3-axis control isn't three independent
problems.**

**TVC control authority**: a gimbal deflection δ produces moment `M = F·L·sin δ` where L is
the distance from gimbal to CoM. ⚠️ **Typical gimbal range is only ±5–8°** — control
authority is limited, and it decreases as propellant depletes and the CoM moves.

**Control challenges, and each is a real loss-of-vehicle mode:**
- **⚠️ Slosh**: propellant in a partly-full tank behaves like a pendulum with a natural
  frequency `ω_s ≈ √(1.84·g_eff/R)`. If it couples with the control loop, divergence.
  **Anti-slosh baffles** raise damping.
- **⚠️ Flexible body modes**: the vehicle bends. **The IMU measures local attitude including
  the bending mode.** If the controller has gain at that frequency, it drives the mode.
  **Notch filters at the bending frequencies** are mandatory — and the frequencies shift as
  propellant drains, so the filters must be scheduled.
- **Actuator lag and rate limits.**

**Guidance**:
- **Atmospheric phase**: ⚠️ **open-loop pitch program.** Closed-loop steering at high `q`
  risks commanding an α the structure can't survive — the guidance is deliberately dumb
  while it matters.
- **Vacuum phase**: **Powered Explicit Guidance (PEG)** / **iterative guidance mode** —
  solves the linear-tangent steering law that is the optimal-control solution for a flat,
  constant-gravity field, re-solved each cycle.
- **Optimal control formally**: minimize propellant subject to dynamics → Pontryagin's
  maximum principle gives **bang-bang thrust** and the **primer vector** determining
  optimal burn timing.
- **⚠️ Powered descent**: the landing problem is non-convex (thrust magnitude bounded below
  by a non-zero minimum). **Lossless convexification** (Açıkmeşe & Ploen) proves that a
  relaxed convex formulation has the same optimum — **making a real-time, guaranteed-
  convergence solution possible.** This is the genuinely important modern contribution to
  the field, and it's why autonomous propulsive landing became practical.

⚠️ **The "hoverslam"**: if minimum throttle produces T/W > 1, hovering is impossible. The
burn must be timed so velocity and altitude reach zero simultaneously — **a boundary-value
problem with no margin for a late start.**

**Navigation**: strapdown IMU integration accumulates error as roughly `t³` in position for
a bias error. Bounded by GNSS, star trackers, or radar altimetry, fused via Kalman filter.

---

## §12. Reentry Physics

**[DURABLE] The problem: dispose of ~30 MJ/kg (LEO) or ~60 MJ/kg (lunar return) without
depositing it in the vehicle.**

**Allen–Eggers blunt body theory (1958)** — the foundational insight:

> **⚠️ GOTCHA — reentry heating is overwhelmingly *compression*, not friction.**
> The bow shock compresses and heats the air; the vehicle is heated by that gas.
> **A blunt body pushes a detached bow shock ahead of itself, dumping most of the energy
> into the air rather than into the vehicle.** A slender, "aerodynamic" shape produces an
> attached shock and concentrates heating on the surface — **it would be destroyed.**
> This is why every reentry vehicle from Mercury to Orion to Dragon is bluff.

**Deceleration** (Allen–Eggers, exponential atmosphere `ρ = ρ₀e^(−h/H)`, H ≈ 7.2 km):
```
a_max = v_e² · sin γ / (2·e·H)          [independent of ballistic coefficient!]
```
⚠️ **Peak deceleration depends only on entry velocity and flight path angle** — not on
mass or drag area. β shifts *where* it happens, not how severe it is. **Apollo: ~6.5 g;
ballistic Soyuz abort: ~9 g; Galileo probe at Jupiter: ~230 g.**

**Stagnation-point heating — the Sutton–Graves relation:**
```
q_s = k · √(ρ/R_n) · v³
```
with k ≈ 1.7415×10⁻⁴ (SI) for air.

**⚠️ Two consequences that drive all TPS design:**
1. **`q ∝ v³`.** Lunar return at 11 km/s versus LEO at 7.8 km/s is `(11/7.8)³` ≈ **2.8×
   the heat flux.** Mars return is worse still.
2. **`q ∝ 1/√R_n`.** ⚠️ **A blunter nose (larger radius) *reduces* peak heating.** Another
   argument for bluff bodies, and why sharp leading edges (Shuttle wing, X-37) need the
   most exotic materials.

**Total heat load** `Q = ∫q dt` scales differently from peak flux — ⚠️ **a shallow entry
lowers peak flux but *raises* total load**, which is why the design point is a trade, not a
minimization. **Peak flux sizes the material; total load sizes the thickness.**

**Radiative heating** becomes significant above ~10 km/s, scaling as roughly `v^8` — ⚠️ **at
Jupiter or high-speed sample-return, radiation dominates convection entirely.**

**The entry corridor**: too steep → exceed heating and g-limits; too shallow → skip out.
⚠️ **For Apollo lunar return the corridor was about ±1° in flight path angle** — a
genuinely tight target from 400,000 km away.

**Lifting entry** with L/D 0.3 (Apollo) to ~1 (Shuttle) widens the corridor, permits
cross-range, and allows load management by **bank-angle modulation** — rolling the lift
vector to control descent rate, which is how Apollo and Orion actually fly entry.

**⚠️ Mars EDL is the hardest routine case**: the atmosphere is thick enough to require a
heat shield but too thin to slow you to parachute-safe speeds. ⚠️ **Supersonic parachute
deployment at Mach 1.5–2.2** followed by propulsive terminal descent, and this chain is why
landed mass has historically been capped around 1 tonne.

---

## §13. Instabilities and Failure Physics

**13.1 Combustion instability** — acoustic modes of the chamber coupling with the
combustion process. **Longitudinal (chug, ~100s Hz), tangential and radial (screech,
kHz).** ⚠️ **Tangential modes are the destructive ones — they can destroy an engine in
milliseconds.** Rayleigh's criterion: instability grows when heat release is in phase with
pressure oscillation. **Fixes: acoustic baffles, Helmholtz/quarter-wave cavities, injector
redesign.** ⚠️ **The F-1 required ~2,000 full-scale tests and years of injector iteration**;
it is still not a fully predictive discipline.

**13.2 POGO** — §10.

**13.3 Water hammer and priming shock** — filling a dry line with propellant produces
pressure spikes far above steady-state.

**13.4 Stage separation** — ⚠️ **brief, violent, essentially untestable at full scale on
the ground.** Recontact, plume impingement, and tip-off rates. **Hot staging** (igniting
the upper stage before separation) removes ullage-settling requirements but requires an
interstage that survives the plume.

**13.5 Reliability statistics** — ⚠️ **new vehicles historically succeed on first flight
roughly 50% of the time**; mature vehicles reach 95–98%. **Bayesian reliability growth
models** are the standard analytical treatment. **There is no launch vehicle approaching
aviation reliability, and the physics of §1 → `rocket-equation-nozzles-and-combustion` — thin margins, no redundancy in structure,
single-use hardware — is why.**

**13.6 The organizational failure mode** — ⚠️ **normalization of deviance**: an off-nominal
observation recurs without consequence and is reclassified as acceptable. **Challenger
(O-ring blow-by) and Columbia (foam shedding) both followed this pattern**, and both
accident boards concluded the organizational cause dominated the technical one.
