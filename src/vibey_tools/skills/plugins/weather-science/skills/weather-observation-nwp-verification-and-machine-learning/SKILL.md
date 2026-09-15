---
name: weather-observation-nwp-verification-and-machine-learning
description: "Use when working on forecasting systems: the observation network, numerical weather prediction including the governing system, data assimilation as the underrated half, and ensembles, forecast verification and the scoring rules, predictability and the intrinsic chaos limit, machine-learning weather prediction with its limits, the live scientific dispute and the metrics problem underneath it, and the weather-versus-climate distinction."
---

# Weather Science: Observation, Numerical Weather Prediction, Verification, Predictability, and Machine Learning

> **Part 4 of 5** of the *Weather Science* reference (plugin `weather-science`), covering §11–§16. Sibling skills: `weather-atmosphere-radiation-thermodynamics-and-moisture` (§0–§4), `weather-dynamics-circulation-and-synoptic` (§5–§7), `weather-severe-storms-cyclones-and-boundary-layer` (§8–§10), `weather-reference` (§17–§21). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Atmospheric physics is settled — hydrostatic balance, geostrophy, Lorenz's 1963 chaos work. One area moved dramatically. See §15 below for machine-learning weather prediction and the live scientific dispute around it.

> **Scope.** Complements a Newtonian-mechanics reference (§10 there covers Coriolis and
> rotating frames properly) and a fundamental-physics reference (radiation, thermodynamics).
> ⚠️ **This is the atmosphere specifically.**
>
> **⚠️ GOTCHA** boxes mark genuine misconceptions and the places where intuition
> systematically misleads.
>
> **The three ideas that organize the whole field:**
> 1. **⚠️ Weather is a heat engine driven by differential solar heating.** The tropics
>    receive more energy than they radiate, the poles the reverse, and **essentially all
>    weather is the atmosphere and ocean moving that surplus poleward** (§2.3 → `weather-atmosphere-radiation-thermodynamics-and-moisture`).
> 2. **⚠️ Rotation changes everything.** On a non-rotating planet air would flow directly
>    from high to low pressure. **The Coriolis effect makes it flow *along* isobars
>    instead**, and that single fact produces jet streams, cyclones, and the entire
>    structure of mid-latitude weather (§5 → `weather-dynamics-circulation-and-synoptic`).
> 3. **⚠️ The atmosphere is chaotic, and this is a mathematical property, not a
>    measurement problem.** Lorenz (1963) showed the predictability limit is intrinsic.
>    **No observing system and no model — physics-based or learned — removes it** (§14.1).

---

## §11. Observation

| System | Provides | ⚠️ Notes |
|---|---|---|
| **Surface stations / METAR** | T, Td, P, wind, visibility | Sparse and land-biased |
| **Radiosonde** | ⚠️ **The vertical profile** | ~2×/day, ~800 sites; **the backbone of upper-air truth** |
| **Weather radar** | Precipitation, ⚠️ **Doppler velocity** | **Dual-pol** distinguishes hydrometeor type |
| **Satellite — geostationary** | Continuous imagery | ⚠️ **Poor at high latitudes** |
| **Satellite — polar orbiting** | Sounding, global coverage | ⚠️ **The dominant data volume in assimilation** |
| **Aircraft (AMDAR)** | Upper-air en route | ⚠️ **Dropped sharply during COVID and measurably degraded forecasts** |
| **GNSS radio occultation** | ⚠️ **Bias-free temperature/humidity profiles** | High-value, growing |
| **Buoys, ships, profilers, lightning networks** | | |

**⚠️ Radar caveats worth knowing**: the beam rises with distance so distant echoes sample
higher altitudes; **ground clutter, anomalous propagation, bright band at the melting
level, and beam blockage** all produce artifacts. ⚠️ **Doppler measures only the radial
component of velocity** — motion across the beam is invisible.

---

## §12. Numerical Weather Prediction

### 12.1 The governing system
**The primitive equations**: momentum (Navier-Stokes on a rotating sphere), continuity,
thermodynamic energy, the ideal gas law, and moisture conservation.
⚠️ **A coupled nonlinear PDE system with no analytic solution — so you discretize.**

**Discretization**: spectral (⚠️ **spherical harmonics — historically dominant for global
models**) or grid-point (finite difference/volume, icosahedral and cubed-sphere grids).
**Vertical coordinates**: sigma, pressure, hybrid, isentropic.
**⚠️ CFL condition constrains the timestep given grid spacing and wave speed** — **which is
why resolution is expensive: halving grid spacing roughly costs 8–16×.**
**Hydrostatic** for coarse global models; ⚠️ **non-hydrostatic required below ~10 km grid
spacing, where convection begins to be resolved** (§1 → `weather-atmosphere-radiation-thermodynamics-and-moisture`).

**⚠️ Parameterization is where the physics that can't be resolved lives**: convection,
cloud microphysics, radiation, boundary layer turbulence, gravity wave drag, land surface.
⚠️ **This is the largest source of model error and the hardest part of NWP.** **The
"grey zone" — grid spacings around 1–10 km where convection is partly resolved and partly
parameterized — is genuinely awkward.**

### 12.2 ⚠️ Data assimilation — the underrated half
**The forecast is only as good as its initial conditions, and observations are sparse,
irregular and noisy.** **DA combines a short-range forecast (the "background") with
observations, weighted by their respective error statistics**, to produce an **analysis**.

**Methods**: 3D-Var, **4D-Var** (⚠️ **assimilates over a time window, using the model
itself as a constraint — ECMWF's long-standing strength**), **EnKF** (flow-dependent
error covariances from an ensemble), and **hybrid** approaches which now dominate.

> **⚠️ GOTCHA — data assimilation is arguably a larger contributor to modern forecast
> skill than model improvements, and it's almost invisible outside the field.**
> ⚠️ **It's also the reason §15's ML models are not yet a full replacement: they mostly
> consume an analysis produced by conventional physics-based assimilation.**

**Reanalysis** — ⚠️ **rerunning a fixed modern DA system over the historical record to
produce a physically consistent gridded dataset.** **ERA5 is the standard**, and it is
**the training data for essentially every ML weather model** (§15).

### 12.3 Ensembles
**⚠️ Since initial conditions and the model are both uncertain, run many forecasts.**
Perturb initial conditions (singular vectors, bred modes, EDA) and represent model
uncertainty (stochastic physics, multi-model, multi-physics).
**⚠️ Ensemble prediction arrived operationally in 1992 and was the previous methodological
break in forecasting** — before §15. **The ensemble mean is more skillful than any member;
the spread is the uncertainty estimate.**
⚠️ **A well-calibrated ensemble's spread should match its error. Under-dispersion is the
common failure and it makes forecasts overconfident.**

---

## §13. Forecast Verification

**⚠️ "Was the forecast good?" is a harder question than it looks, and the metric you choose
determines the answer** (§15.3).
```
RMSE / MAE                deterministic error  ⚠️ REWARDS SMOOTHING — see §15.3
ACC (anomaly correlation) ⚠️ the standard synoptic skill score; 0.6 conventionally
                          taken as the limit of useful deterministic skill
Brier score               probabilistic, binary events
CRPS                      ⚠️ probabilistic, continuous — the standard ensemble metric
Reliability diagram       ⚠️ do 30% forecasts verify 30% of the time?
POD / FAR / CSI           categorical events
```
**⚠️ The double penalty problem**: a sharp forecast of a feature in slightly the wrong place
is penalized twice — **once for predicting it where it wasn't, once for missing it where it
was.** ⚠️ **A blurry forecast scores better on RMSE while being less useful.** **This is
not a technicality; it distorts model development toward smoothness** (§15.3).

**⚠️ Skill must beat a reference** — persistence, climatology, or a previous model.
**"85% accurate" means nothing without one.**

---

## §14. Predictability and Chaos

### 14.1 The intrinsic limit
**Lorenz (1963)** — ⚠️ **deterministic nonlinear systems exhibit sensitive dependence on
initial conditions.** Errors grow, and **small-scale errors propagate upscale.**
> **⚠️ GOTCHA — the predictability limit is a property of the atmosphere, not of our
> instruments or models.** ⚠️ **Roughly two weeks for synoptic-scale deterministic
> forecasting is a mathematical bound, not an engineering target.** **Perfect observations
> and a perfect model would not remove it** — see a Newtonian-mechanics reference §13 for
> why better data buys only logarithmic improvement.
>
> **⚠️ And predictability is flow-dependent.** Some regimes are far more predictable than
> others, which is exactly what the ensemble spread is telling you (§12.3).

**Scale matters**: convective cells minutes to hours; mesoscale systems hours; synoptic
systems days; **planetary waves and teleconnections longer.** ⚠️ **Seasonal forecasting
works not by predicting weather but by predicting boundary-condition-driven shifts in the
distribution** — chiefly ENSO (§6 → `weather-dynamics-circulation-and-synoptic`).

---

## §15. Machine Learning Weather Prediction

**⚠️ This is the section that moved, and it moved fast enough that most general knowledge
about it is out of date.** **Verified August 2026.**

### 15.1 What happened
**⚠️ One assessment frames it as the biggest methodological break in forecasting since
ensemble prediction arrived in 1992** — and that seems right. **Between November 2023 and
mid-2026, data-driven models trained on reanalysis went from research curiosities to
operational systems running alongside the physics engines they were built to challenge.**

**The models**: **FourCastNet** (NVIDIA, Fourier neural operator; later SFNO),
**Pangu-Weather** (Huawei, 3D Earth-Specific Transformer), **GraphCast** (Google DeepMind,
GNN on a multi-scale icosahedral mesh), **GenCast** (⚠️ **DeepMind, a conditional diffusion
model producing ensembles**), **AIFS** (ECMWF, GNN-transformer hybrid), **Aurora**
(Microsoft), **NeuralGCM** (hybrid), **FuXi / FengWu**, **NVIDIA Atlas**, **FGN**.

**⚠️ Operational status is the important part:**
- **ECMWF's AIFS Single has run operationally since 25 February 2025** — ⚠️ **the first
  operational ML weather system**, with a **51-member probabilistic version (AIFS-CRPS)
  following.**
- **NOAA/NWS made AI/ML models available in mid-December 2025**, including **AIGFS** and
  **HyGEFS**.
- **Google's WeatherNext** family operationalized GenCast (as WeatherNext Gen).

**⚠️ The skill claims, and they're substantiated:** GraphCast **matches or exceeds IFS HRES
on global benchmarks**; **GenCast was the first probabilistic MLWP model to significantly
outperform ECMWF's ENS at high resolution** (Nature, 2024); and by 2026 ⚠️ **ensemble
systems including GenCast and FGN have surpassed the skill of the ECMWF ensemble — the
gold standard in operational meteorology — at a small fraction of the computational
cost.**

**⚠️ The computational asymmetry is the genuinely disruptive part**: training is expensive
and one-off; **inference is seconds on a single GPU versus hours on a supercomputer.**

### 15.2 ⚠️ The limits — and there is a live scientific dispute here
> **⚠️ GOTCHA — the headline "AI beats physics" and the extremes evidence genuinely
> conflict, and you should know both sides.**
>
> **A Science Advances paper (2026, Zhang et al.) found that for record-breaking weather
> extremes, ECMWF's HRES still consistently outperforms GraphCast, Pangu-Weather and FuXi**
> — ⚠️ **with AI errors larger for record-breaking heat, cold and wind across nearly all
> lead times, systematic underestimation of both frequency and intensity of records, and
> growing bias the further the record is exceeded.** ⚠️ **The performance gap was widest
> at SHORT lead times.**
>
> **The proposed mechanism is important**: ⚠️ **models trained on 1979–2017 tend to be
> limited to extreme values already observed, "as if they had an implicit ceiling," while
> physics-based models are not so constrained and can in principle represent unprecedented
> situations.**

**Other documented limitations:**
- **⚠️ Smoothing.** Models trained to minimize average error produce **overly smooth
  fields, blurring small-scale structure and systematically underrepresenting extremes,
  worsening with lead time.** ⚠️ **This is §13's double-penalty problem expressed as a
  training objective.** **Diffusion-based ensembles (GenCast) substantially address it** —
  which is a large part of why they work.
- **⚠️ Dependence on physics-based assimilation.** **Every current ML model relies on a
  conventional analysis for initial conditions** (§12.2). ⚠️ **The replacement narrative is
  oversold and the dependency is underreported** — and **GraphCast initialized on GFS
  rather than ERA5 produces systematic inconsistencies.** **ML-based data assimilation is
  the live frontier that would close this.**
- **Physical consistency** — ⚠️ **outputs can violate known physical laws or expected
  statistical consistency**, and one assessment concluded AI models **do not properly
  reproduce sub-synoptic and mesoscale phenomena.**
- **Precipitation** — ⚠️ **persistent difficulty with light precipitation across GraphCast,
  Pangu, FuXi and CREDIT, with a positive frequency bias in the drizzle regime**, attributed
  to symmetric regression losses on a non-negative intermittent variable.
- **Temporal resolution** — ⚠️ **AIFS and AIGFS step every 6 hours where GFS gives hourly
  output; that matters for hurricanes and sharp fronts.**
- **Tropical cyclones** — track prediction is good; ⚠️ **intensity is uneven, with earlier
  models underestimating peak intensity and both tested models overestimating inner-core
  size. And a subtle trap: ERA5 itself underestimates peak intensity, so agreement with
  reanalysis does not imply accuracy.**
- **Climate shift** — ⚠️ **behaviour in novel climate states not represented in training
  is an open question.**
- **⚠️ Nowcasting (0–12 h) is still behind high-resolution NWP.**

**⚠️ The counterargument deserves stating fairly too**: one 2026 review argues it is
**"certainly an over-statement to say that they can only predict what has been seen locally
in their training dataset,"** notes that ML models have **overcome long-standing physics
model biases** such as slow tropical cyclone track bias, and points to **next-generation
models incorporating observations directly** — potentially removing the reanalysis
dependency entirely.

### 15.3 ⚠️ The metrics problem underneath the dispute
**Part of why the two camps disagree is that they're measuring different things.**
⚠️ **RMSE rewards smoothing (§13), so a model that hedges scores well on the headline
metric while underrepresenting exactly the extremes that matter operationally.** **Work on
fair comparison for extremes — weighted potential CRPS and similar — exists precisely
because the standard scores flatter the smoothing problem.**
**⚠️ When you read "AI outperforms on 90% of metrics," ask which metrics, and on what
distribution of events.**

### 15.4 The state of play
**⚠️ As of 2026, no major meteorological agency has decommissioned its NWP system.**
**ECMWF, NOAA and the Met Office all run AI models *alongside* traditional ones, not
instead of them**, with AI as one guidance product among several.
**⚠️ That is the correct read**: this is an additional, extraordinarily cheap, often more
skillful source of guidance — **not a replacement for a physics-based system that still
provides the analysis, the extremes, the physical consistency, and the fallback.**

---

## §16. Weather vs Climate

**⚠️ "Weather is what you get, climate is what you expect."** More usefully: **weather is
an initial-value problem; climate is a boundary-value problem.**
⚠️ **This is why a two-week predictability limit (§14) does not imply climate projection is
impossible** — you are not predicting the trajectory, you are predicting the statistics of
the attractor under changed forcing. **These are different mathematical problems.**

**Attribution** — ⚠️ **modern extreme event attribution asks how much a specific event's
probability or intensity changed, not whether climate change "caused" it.** The
either/or framing is the wrong question.
**Climate sensitivity** — ⚠️ **cloud feedback remains the dominant uncertainty** (§2 → `weather-atmosphere-radiation-thermodynamics-and-moisture`).
