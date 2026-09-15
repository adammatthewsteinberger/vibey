---
name: chaos-logistic-map-lyapunov-and-attractors
description: "Use when quantifying or classifying chaotic behaviour: the logistic map as the canonical example, Feigenbaum universality and why the constant is universal, the precise content of 'period three implies chaos', Lyapunov exponents and how they are computed and misread, strange attractors and their structure, and the recognized routes to chaos."
---

# Chaos Theory: The Logistic Map, Lyapunov Exponents, Strange Attractors, and Routes to Chaos

> **Part 2 of 5** of the *Chaos Theory* reference (plugin `chaos-theory`), covering §5–§8. Sibling skills: `chaos-foundations-dynamical-systems-and-bifurcations` (§0–§4), `chaos-fractals-poincare-and-hamiltonian-chaos` (§9–§11), `chaos-detection-control-applications-and-computation` (§12–§15), `chaos-reference` (§16–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Settled mathematics — Poincare 1890, Lorenz 1963, Smale 1967, Ruelle-Takens 1971, Feigenbaum 1978, Takens 1981. Nothing here has changed.

> **Scope.** Complements a Newtonian-mechanics reference (§13 there introduces chaos from
> the physics side) and a weather-science reference (§14 there, predictability limits).
> ⚠️ **This is the mathematics itself.**
>
> **⚠️ GOTCHA** boxes mark the misconceptions — and chaos theory is **the most
> misappropriated area of mathematics in general discourse**, so there are many. §16 → `chaos-reference`
> consolidates them.
>
> **The three ideas that matter most:**
> 1. **⚠️ Chaos is deterministic.** No randomness anywhere. The equations are exact, the
>    trajectory is unique, and the behaviour is still unpredictable in practice. **That
>    combination is the entire subject** (§1 → `chaos-foundations-dynamical-systems-and-bifurcations`).
> 2. **⚠️ Nonlinearity is necessary but nowhere near sufficient.** Most nonlinear systems
>    are not chaotic. **Chaos needs stretching *and* folding** — divergence to separate
>    nearby states, confinement to keep them bounded (§1.3 → `chaos-foundations-dynamical-systems-and-bifurcations`, §7).
> 3. **⚠️ Chaos is generic, not exotic.** Poincaré found it in the three-body problem in
>    1890. **The integrable, solvable systems in textbooks are the rare special cases, and
>    they trained everyone's intuition wrong** (§11 → `chaos-fractals-poincare-and-hamiltonian-chaos`).

---

## §5. The Logistic Map

**⚠️ The most important toy model in mathematics**, and it earns the status:
```
x_{n+1} = r x_n (1 − x_n),     x ∈ [0,1],  r ∈ [0,4]
```
```
r < 1          → extinction (x → 0)
1 < r < 3      → stable fixed point at 1 − 1/r
r = 3          ⚠️ first period-doubling
r ≈ 3.449      period 4        r ≈ 3.544  period 8 ...
r∞ ≈ 3.5699    ⚠️ ACCUMULATION POINT — onset of chaos
r > r∞         chaos, ⚠️ interleaved with PERIODIC WINDOWS
r ≈ 3.828      ⚠️ the period-3 window (see Sharkovskii, below)
r = 4          fully chaotic, conjugate to the tent map
```

### 5.1 ⚠️ Feigenbaum universality — the deep result
**The period-doubling parameter intervals shrink at a constant ratio:**
```
δ = 4.669201609...    ⚠️ the ratio of successive parameter intervals
α = 2.502907875...    the scaling of the attractor's spatial structure
```
> **⚠️ GOTCHA — these constants are UNIVERSAL, and this is the genuinely astonishing part.**
> ⚠️ **Any one-dimensional map with a smooth quadratic maximum period-doubles with the
> same δ** — the logistic map, the sine map, a dripping tap, a driven oscillator, a
> convecting fluid. **The constants have been measured in physical experiments.**
> **Feigenbaum's insight (1978) was that this is a renormalization group phenomenon** —
> ⚠️ **the same mathematical machinery as universality in critical phase transitions.**
> **The microscopic details are irrelevant; only the order of the maximum matters.**

### 5.2 ⚠️ "Period three implies chaos"
**Li and Yorke (1975)** — for a continuous 1D map, **the existence of a period-3 orbit
implies orbits of every period, plus an uncountable set of aperiodic orbits.**
**⚠️ This is a special case of Sharkovskii's theorem (1964), which gives a complete
ordering of periods**: if a map has a periodic orbit of period `p`, it has orbits of every
period below `p` in the Sharkovskii ordering. **Period 3 sits at the top, so it implies
everything.** ⚠️ **And the paper's title gave the field its name.**

---

## §6. Lyapunov Exponents

**⚠️ The quantitative measure of sensitivity.** For an infinitesimal separation `δ₀`:
```
|δ(t)| ≈ |δ₀| e^(λt)
```
**⚠️ An n-dimensional system has n Lyapunov exponents (the Lyapunov spectrum).**
```
λ_max > 0   ⚠️ CHAOS — this is the operational definition
λ_max = 0   marginal / quasi-periodic (⚠️ a flow always has one zero exponent along
            the trajectory direction)
λ_max < 0   converging to a fixed point
Σλᵢ < 0     ⚠️ dissipative — phase space volume contracts
Σλᵢ = 0     ⚠️ conservative/Hamiltonian (Liouville) — §11
```
**⚠️ The signature of a strange attractor in 3D is (+, 0, −) with the sum negative**:
stretching in one direction, neutral along the flow, strong contraction — **volume
shrinks onto a fractal set while trajectories on it separate.** **That's stretch-and-fold
expressed in exponents.**

**⚠️ The Lyapunov time `1/λ_max` is the practically useful number**: the timescale on which
errors grow by `e`.
> **⚠️ GOTCHA — the predictability horizon scales LOGARITHMICALLY with initial accuracy.**
> ```
> t_horizon ≈ (1/λ) ln(tolerance/δ₀)
> ```
> ⚠️ **Improving your measurements by a factor of 1000 buys you only `ln(1000)/λ ≈ 6.9/λ`
> of extra prediction time.** **A few more Lyapunov times, not a thousand times longer.**
> **This is why better instruments cannot rescue long-range weather forecasting**, and it
> is the single most practically important consequence of chaos.

---

## §7. Strange Attractors

**Lorenz (1963)** — derived from a drastically truncated model of thermal convection:
```
ẋ = σ(y − x)        ẏ = x(ρ − z) − y        ż = xy − βz
σ = 10, ρ = 28, β = 8/3    ⚠️ the classic parameters
```
**⚠️ Two lobes, never repeating, never crossing.** The trajectory orbits one wing, switches
to the other unpredictably. **Fractal dimension ≈ 2.06** — ⚠️ **more than a surface, less
than a volume, which is what "strange" means geometrically.**
**⚠️ Lorenz found it by accident**: he restarted a simulation from printed output rounded
to three decimals instead of the stored six, and the run diverged completely. **The
practical lesson arrived before the theory.**

**Rössler** — simpler, single-scroll, designed to be the minimal example.
**Hénon map** — a 2D map, `x_{n+1} = 1 − ax_n² + y_n`, `y_{n+1} = bx_n`; ⚠️ **zoom in and
the Cantor-set cross-section is directly visible.**
**Also**: the double pendulum, Duffing and van der Pol oscillators, Chua's circuit
(⚠️ **chaos you can build on a breadboard**), the standard map (§11 → `chaos-fractals-poincare-and-hamiltonian-chaos`).

**⚠️ A strange attractor is strange geometrically (fractal) and chaotic dynamically
(λ > 0), and these are logically independent** — **strange nonchaotic attractors exist.**
**Most people use "strange" to mean both; be aware they're different claims.**

---

## §8. Routes to Chaos

**⚠️ Chaos does not arrive arbitrarily — there are a small number of characteristic
routes, and identifying which one you're on tells you what to expect.**
```
PERIOD-DOUBLING CASCADE   ⚠️ Feigenbaum. Infinite cascade in finite parameter range (§5)
QUASI-PERIODIC            ⚠️ Ruelle-Takens-Newhouse (1971): fixed point → limit cycle
                          → torus → chaos, after only a FEW bifurcations
                          ⚠️ This overturned Landau's picture of turbulence as an
                          infinite sequence of frequencies
INTERMITTENCY             ⚠️ long near-regular stretches interrupted by irregular bursts;
                          bursts become more frequent as the parameter increases
                          (Pomeau-Manneville types I, II, III)
CRISIS                    sudden expansion or destruction of an attractor
```
**⚠️ Intermittency is the one to recognize in real data** — **a system that looks periodic
most of the time with occasional bursts is not a periodic system with noise; it may be
chaotic, and the distinction has different implications for control.**
