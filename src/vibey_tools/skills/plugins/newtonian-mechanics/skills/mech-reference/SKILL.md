---
name: mech-reference
description: "Use when correcting a mechanics misconception from the consolidated list, looking up a constant, formula or magnitude, finding the textbook canon, or needing a problem-solving picker and the sanity checks worth running on any mechanics answer. Companion to the other newtonian-mechanics skills."
---

# Newtonian Mechanics: Misconceptions, Numbers, Formulas, and Canon

> **Part 5 of 5** of the *Newtonian Mechanics* reference (plugin `newtonian-mechanics`), covering §15–§19. Sibling skills: `mech-kinematics-newtons-laws-and-forces` (§0–§3), `mech-energy-momentum-and-collisions` (§4–§5), `mech-rotation-rigid-bodies-and-oscillations` (§6–§8), `mech-orbits-frames-analytical-mechanics-and-simulation` (§9–§14). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Settled since 1687 — Newton's Principia, Euler's rigid-body work in the 1750s, Lagrange 1788, Hamilton 1833. Nothing here has changed or will.

> **Scope.** Complements a fundamental-physics reference, which covers relativity, quantum
> mechanics and where classical mechanics breaks down. ⚠️ **This is the classical theory
> done properly**, including §14 → `mech-orbits-frames-analytical-mechanics-and-simulation` on numerical integration — the part that matters if
> you're simulating any of it.
>
> **⚠️ GOTCHA** boxes mark genuine misconceptions, including several that survive a
> physics degree.
>
> **The three ideas that reorganize everything once you see them:**
> 1. **⚠️ Force causes acceleration, not velocity.** This one sentence is the entire
>    content of the Aristotle-to-Newton revolution, and **the misconception it replaced is
>    the single most robust error in physics education** (§2.2 → `mech-kinematics-newtons-laws-and-forces`).
> 2. **⚠️ The conservation laws are not consequences of `F = ma` — they're deeper than
>    it.** Momentum conservation follows from spatial translation symmetry, energy from
>    time-translation symmetry, angular momentum from rotational symmetry (Noether, 1918).
>    **They survive into relativity and quantum mechanics; `F = ma` does not** (§4.5 → `mech-energy-momentum-and-collisions`).
> 3. **⚠️ Newtonian mechanics is deterministic but not predictable.** Determinism is a
>    property of the equations; predictability is a property of your knowledge. **Chaos
>    separates them, and the separation is not a defect of your instruments** (§13 → `mech-orbits-frames-analytical-mechanics-and-simulation`).

---

## §15. Misconceptions — the consolidated list

| Misconception | The correction |
|---|---|
| Motion requires a force | ⚠️ **Constant velocity requires ZERO net force** (§2.2 → `mech-kinematics-newtons-laws-and-forces`) |
| A thrown object carries a forward force | ⚠️ **It carries momentum. Only gravity and drag act** (§2.2 → `mech-kinematics-newtons-laws-and-forces`) |
| Third-law pairs cancel | ⚠️ **Different bodies. Nothing would ever accelerate** (§2.2 → `mech-kinematics-newtons-laws-and-forces`) |
| Heavier objects fall faster | Not in vacuum; in air it's the mass/drag ratio (§2.2 → `mech-kinematics-newtons-laws-and-forces`) |
| Centrifugal force pushes you outward | ⚠️ **Only exists in the rotating frame** (§2.2 → `mech-kinematics-newtons-laws-and-forces`, §10 → `mech-orbits-frames-analytical-mechanics-and-simulation`) |
| N = mg always | ⚠️ **Only in one special case** (§3.2 → `mech-kinematics-newtons-laws-and-forces`) |
| Static friction = μ_s N | ⚠️ **It's an inequality. Compute from equilibrium** (§3.3 → `mech-kinematics-newtons-laws-and-forces`) |
| Friction depends on contact area | Not in the Coulomb model, for good reason (§3.3 → `mech-kinematics-newtons-laws-and-forces`) |
| Constant-acceleration equations always apply | ⚠️ **Only for constant acceleration** (§1 → `mech-kinematics-newtons-laws-and-forces`) |
| Zero velocity means zero acceleration | Top of the arc (§1 → `mech-kinematics-newtons-laws-and-forces`) |
| Energy is "lost" to friction | ⚠️ **It becomes thermal energy. Never lost** (§4 → `mech-energy-momentum-and-collisions`) |
| Moment of inertia is a property of the object | ⚠️ **Of the object AND the axis** (§6 → `mech-rotation-rigid-bodies-and-oscillations`) |
| L and ω are parallel | ⚠️ **Only about principal axes** (§7 → `mech-rotation-rigid-bodies-and-oscillations`) |
| Pendulum period is amplitude-independent | ⚠️ **Only in the small-angle approximation** (§8 → `mech-rotation-rigid-bodies-and-oscillations`) |
| Tacoma Narrows was resonance | ⚠️ **Aeroelastic flutter — a self-excited instability** (§8 → `mech-rotation-rigid-bodies-and-oscillations`) |
| Coriolis determines bathtub drains | ⚠️ **Orders of magnitude too small** (§10 → `mech-orbits-frames-analytical-mechanics-and-simulation`) |
| Bernoulli explains lift via equal transit time | ⚠️ **Wrong, and universally repeated** (§12 → `mech-orbits-frames-analytical-mechanics-and-simulation`) |
| Deterministic means predictable | ⚠️ **Chaos separates them** (§13 → `mech-orbits-frames-analytical-mechanics-and-simulation`) |
| RK4 is best because it's fourth order | ⚠️ **Not for long integrations. Symplectic wins** (§14.2 → `mech-orbits-frames-analytical-mechanics-and-simulation`) |
| Euler integration is fine for orbits | ⚠️ **It spirals. Reorder two lines** (§14.1 → `mech-orbits-frames-analytical-mechanics-and-simulation`) |
| F = ma works for rockets | ⚠️ **Variable mass needs F = dp/dt done properly** (§2.1 → `mech-kinematics-newtons-laws-and-forces`) |

---

## §16. Numbers and Formulas

```
CONSTANTS
g = 9.80665 m/s² (standard) · G = 6.674×10⁻¹¹ N·m²/kg²
Earth: M = 5.972×10²⁴ kg · R = 6371 km · escape 11.2 km/s · LEO orbital ~7.8 km/s
⚠️ g at ISS altitude ≈ 90% of surface value

KINEMATICS (constant a only)
v = v₀ + at · x = x₀ + v₀t + ½at² · v² = v₀² + 2aΔx
a_c = v²/r = ω²r · projectile range v₀²sin(2θ)/g

DYNAMICS
F = dp/dt (⚠️ = ma only for constant m) · J = ∫F dt = Δp
f_s ≤ μ_s N · f_k = μ_k N · F_drag = ½ρC_dAv² · v_t = √(2mg/ρC_dA)

ENERGY
KE = ½mv² · KE_rot = ½Iω² · PE = mgh = −GMm/r · PE_spring = ½kx²
W = ∫F·dr · P = F·v

MOMENT OF INERTIA (about centre of mass)
Hoop MR² · Disc/cylinder ½MR² · Solid sphere ⅖MR² · Spherical shell ⅔MR²
Rod (centre) ML²/12 · Rod (end) ML²/3 · ⚠️ Parallel axis: I = I_cm + Md²

ROTATION
τ = r×F = Iα · L = Iω = r×p · rolling: v = ωR

OSCILLATION
ω = √(k/m) · pendulum ω = √(g/L) (⚠️ small angle) · Q ≈ ω₀/Δω

ORBITS
T² ∝ a³ · E = −GMm/2a · v_esc = √(2GM/r) = √2 × v_circ

NON-INERTIAL
F_cent = mω²r · F_Cor = −2m(ω×v)

FLUIDS
P = ρgh · A₁v₁ = A₂v₂ · P + ½ρv² + ρgh = const (⚠️ along a streamline)
Re = ρvL/μ
```

---

## §17. Books

| Author | Work | Why |
|---|---|---|
| **Kleppner & Kolenkow** | ***An Introduction to Mechanics*** | ⚠️ **The best rigorous first course. Hard, and worth it** |
| **Morin** | ***Introduction to Classical Mechanics*** | ⚠️ **Superb problems with full solutions. The one to work through** |
| **Taylor** | ***Classical Mechanics*** | ⚠️ **The clearest bridge into Lagrangian/Hamiltonian (§11 → `mech-orbits-frames-analytical-mechanics-and-simulation`)** |
| **Goldstein, Poole & Safko** | ***Classical Mechanics*** | The graduate standard |
| **Landau & Lifshitz** | *Mechanics* (Vol. 1) | ⚠️ **Extraordinarily terse and elegant; starts from least action** |
| **Feynman** | ***The Feynman Lectures*, Vol. I** | ⚠️ **Free online. Unmatched for physical intuition** |
| **Strogatz** | ***Nonlinear Dynamics and Chaos*** | ⚠️ **§13 → `mech-orbits-frames-analytical-mechanics-and-simulation`, and the best-written maths textbook in circulation** |
| **Hairer, Lubich & Wanner** | *Geometric Numerical Integration* | ⚠️ **§14 → `mech-orbits-frames-analytical-mechanics-and-simulation` rigorously — why symplectic works** |
| **Hestenes et al.** | *Force Concept Inventory* (1992) | ⚠️ **The research documenting §15** |
| **Sussman & Wisdom** | *Structure and Interpretation of Classical Mechanics* | ⚠️ **Mechanics in executable Scheme. Idiosyncratic and clarifying for programmers** |

---

## §18. Quick Reference

### 18.1 Problem-solving picker
| Situation | Approach |
|---|---|
| Forces known, want motion | **Free-body diagram + `ΣF = ma`** (§2.3 → `mech-kinematics-newtons-laws-and-forces`) |
| Don't care about time, know positions | ⚠️ **Energy conservation — far less algebra** (§4 → `mech-energy-momentum-and-collisions`) |
| Collision or explosion | ⚠️ **Momentum conservation; check if KE is conserved too** (§5 → `mech-energy-momentum-and-collisions`) |
| Short, violent interaction | **Impulse-momentum** (§5 → `mech-energy-momentum-and-collisions`) |
| Constraints everywhere (pendulums, linkages) | ⚠️ **Lagrangian — constraint forces vanish** (§11 → `mech-orbits-frames-analytical-mechanics-and-simulation`) |
| Want a conserved quantity | ⚠️ **Find the symmetry (Noether)** (§4.5 → `mech-energy-momentum-and-collisions`) |
| Rotating or accelerating frame | **Add fictitious forces** (§10 → `mech-orbits-frames-analytical-mechanics-and-simulation`) |
| Small oscillation about equilibrium | ⚠️ **Expand the potential — you'll get SHM** (§8 → `mech-rotation-rigid-bodies-and-oscillations`) |
| Central force | ⚠️ **Angular momentum conserved, motion is planar** (§9 → `mech-orbits-frames-analytical-mechanics-and-simulation`) |
| Simulating it | ⚠️ **Symplectic integrator, and monitor energy** (§14 → `mech-orbits-frames-analytical-mechanics-and-simulation`) |
| Long-duration orbital simulation | ⚠️ **Verlet, not RK4** (§14.2 → `mech-orbits-frames-analytical-mechanics-and-simulation`) |
| Stiff system | Implicit method (§14.3 → `mech-orbits-frames-analytical-mechanics-and-simulation`) |

### 18.2 Sanity checks
- [ ] **Dimensional analysis** — do the units work? ⚠️ **Catches most algebra errors free**
- [ ] **Limiting cases** — what happens as `m→0`, `θ→0`, `t→∞`? Does it match intuition?
- [ ] **Signs** — is the force in the direction physics says it should be?
- [ ] **Order of magnitude** — is the answer physically plausible?
- [ ] **Conserved quantities** — is energy/momentum conserved when it should be?
- [ ] **Free-body diagram**: can I name the object exerting every force I drew? (§2.3 → `mech-kinematics-newtons-laws-and-forces`)
- [ ] **Simulation**: is the conserved quantity drifting? (§14.3 → `mech-orbits-frames-analytical-mechanics-and-simulation`)

---

## §19. Method

**No searches were run, and none could have been useful.** ⚠️ **This is settled physics
and has been for centuries**: Newton's *Principia* (1687), Euler's rigid-body work
(1750s), Lagrange's *Mécanique analytique* (1788), Hamilton (1833), Noether (1918),
Poincaré on the three-body problem (1890). **Nothing in §1–§13 → `mech-kinematics-newtons-laws-and-forces`, `mech-energy-momentum-and-collisions`, `mech-rotation-rigid-bodies-and-oscillations`, `mech-orbits-frames-analytical-mechanics-and-simulation` has changed or will
change.**

**Sources** are the standard texts in §17 — chiefly **Kleppner & Kolenkow** and **Morin**
for the core, **Taylor** and **Landau & Lifshitz** for §11 → `mech-orbits-frames-analytical-mechanics-and-simulation`, **Strogatz** for §13 → `mech-orbits-frames-analytical-mechanics-and-simulation`, and
**Hairer/Lubich/Wanner** for §14 → `mech-orbits-frames-analytical-mechanics-and-simulation`'s geometric integration results.

**Scoped to complement**: relativity, quantum mechanics, and the boundaries where
classical mechanics fails belong in a fundamental-physics reference; ⚠️ **this document
stays inside the classical domain deliberately and says where the edges are (§9 → `mech-orbits-frames-analytical-mechanics-and-simulation`'s
perihelion precession, §12 → `mech-orbits-frames-analytical-mechanics-and-simulation`'s turbulence) rather than crossing them.** Rocket propulsion and
the variable-mass derivation gestured at in §2.1 → `mech-kinematics-newtons-laws-and-forces` sit in a rocket-science reference.

**Confidence: high throughout**, with one distinction worth drawing.

**§1–§13 → `mech-kinematics-newtons-laws-and-forces`, `mech-energy-momentum-and-collisions`, `mech-rotation-rigid-bodies-and-oscillations`, `mech-orbits-frames-analytical-mechanics-and-simulation` are textbook results stated with their validity conditions** — ⚠️ **and the
conditions are the valuable part, because essentially every error in classical mechanics
is a correct formula applied outside its assumptions.** Constant-acceleration kinematics
with non-constant acceleration, `N = mg` on an incline, small-angle pendulum period at
large amplitude, Bernoulli off a streamline: **the formula is right and the application is
wrong.** §15 collects these.

**§15's misconception list is grounded in physics-education research**, principally the
**Force Concept Inventory** literature — ⚠️ **these are documented, measured, and
resistant to instruction, not anecdotes about students.**

⚠️ **Two specific corrections I've made deliberately against widespread belief, both of
which you will find stated the other way in reputable places.** **The Tacoma Narrows
collapse is attributed in the modern engineering literature to aeroelastic flutter — a
self-excited feedback instability — not to simple resonance**, and it remains the standard
textbook resonance example anyway. **And the Coriolis-bathtub claim is off by orders of
magnitude** while being one of the most-repeated pieces of physics folklore.

**§14 → `mech-orbits-frames-analytical-mechanics-and-simulation` is the section I'd most encourage reading if you write simulations**, and ⚠️ **its
central claim is counterintuitive enough to state plainly: for long integrations, a
second-order symplectic method beats fourth-order RK4.** **Order of accuracy is the wrong
figure of merit when what you care about is qualitative long-run behaviour rather than
per-step error.**
