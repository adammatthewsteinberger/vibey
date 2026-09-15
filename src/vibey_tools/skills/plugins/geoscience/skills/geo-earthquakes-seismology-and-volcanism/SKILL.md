---
name: geo-earthquakes-seismology-and-volcanism
description: "Use when working on seismic or volcanic problems: earthquake mechanics, seismic waves and how they are used to image the interior, the magnitude-versus-intensity distinction that is routinely conflated, the difference between earthquake prediction and forecasting and why one is not available; and volcanism including magma properties, eruption styles and the controls on explosivity."
---

# Geoscience: Earthquakes, Seismology, and Volcanism

> **Part 2 of 5** of the *Geoscience* reference (plugin `geoscience`), covering §5–§6. Sibling skills: `geo-earth-structure-tectonics-rocks-and-deep-time` (§0–§4), `geo-surface-processes-soils-and-hydrology` (§7–§10), `geo-oceans-cryosphere-cycles-hazards-and-observation` (§11–§16), `geo-reference` (§17–§22). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Tectonics, stratigraphy, hydraulics and seismological theory are settled; satellite-measured continental water storage and deep learning in seismology recently changed the science. See §17 → `geo-reference` for both.

> **Scope.** Complements a weather-science reference (the atmosphere) and a
> Newtonian-mechanics reference (the physics). ⚠️ **This is the solid Earth, the water,
> and the land surface.**
>
> **⚠️ GOTCHA** boxes mark genuine misconceptions and places where intuition fails badly.
>
> **The three ideas that organize the field:**
> 1. **⚠️ Deep time is the hardest thing to internalize and the most important.** Processes
>    imperceptible on human timescales — millimetres per year — build mountains and open
>    oceans given tens of millions of years. **Almost every geological misconception is a
>    failure of timescale intuition** (§3 → `geo-earth-structure-tectonics-rocks-and-deep-time`).
> 2. **⚠️ The Earth runs on two engines.** Internal heat (radiogenic decay plus primordial)
>    drives tectonics, building topography; solar energy drives the water cycle and
>    weathering, tearing it down. **Everything at the surface is the interaction** (§1 → `geo-earth-structure-tectonics-rocks-and-deep-time`, §7 → `geo-surface-processes-soils-and-hydrology`).
> 3. **⚠️ Rates and residence times explain more than mechanisms do.** Water in a river
>    resides for days, in groundwater for millennia. **Whether something is renewable
>    depends entirely on the ratio of extraction rate to renewal rate** — and it's why
>    §10 → `geo-surface-processes-soils-and-hydrology` is the most consequential section here (§10 → `geo-surface-processes-soils-and-hydrology`, §17.1 → `geo-reference`).

---

## §5. Earthquakes and Seismology

### 5.1 Mechanics
**⚠️ Elastic rebound**: stress accumulates on a locked fault, the rock deforms elastically,
and when friction is overcome it **ruptures and snaps back** — releasing stored strain
energy. **The rupture propagates along the fault at a few km/s; it is not a point event.**

**Focus/hypocentre** (at depth) vs **epicentre** (surface projection).
**Foreshocks, mainshock, aftershocks** — ⚠️ **aftershocks follow Omori's law, decaying
roughly as 1/t**, and **a foreshock is only identifiable as such retrospectively**, which
is a large part of why prediction fails.

### 5.2 Waves
```
P (primary)    ⚠️ compressional, FASTEST, travels through solid AND liquid
S (secondary)  shear, slower, ⚠️ SOLIDS ONLY — the shadow zone proves a liquid outer core
Love, Rayleigh surface waves — ⚠️ slowest, largest amplitude, and they do most of the damage
```
**⚠️ The S−P time difference gives distance from a single station** — three stations
triangulate. **This is how epicentre location works and it's genuinely simple.**

### 5.3 Magnitude and intensity — a distinction people conflate
**⚠️ Magnitude is a property of the earthquake; intensity is a property of a place.**
- **Moment magnitude `M_w`** — ⚠️ **the modern standard**, derived from **seismic moment
  `M₀ = μAD`** (shear modulus × rupture area × slip). **Doesn't saturate for large events,
  unlike the older Richter scale (`M_L`), which does above ~7.**
- ⚠️ **Logarithmic: +1 magnitude = ~32× the energy, +2 = ~1000×.**
- **Modified Mercalli intensity** — observed shaking and damage, varies with distance, site
  conditions and building stock.

**⚠️ Site effects matter enormously**: **soft sediment amplifies shaking**, and
**liquefaction** — saturated loose sand losing strength under cyclic loading — ⚠️ **causes
much of the damage in many earthquakes, and it's a soil property, not an earthquake
property.**

### 5.4 ⚠️ Prediction vs forecasting
> **⚠️ GOTCHA — short-term deterministic earthquake prediction does not work and there is
> no credible method.** ⚠️ **Claims of imminent prediction (animals, radon, clouds,
> planetary alignment) have never validated prospectively.**
> **What does work**: **probabilistic seismic hazard assessment** (long-term rates from
> Gutenberg-Richter statistics, fault slip rates and paleoseismology), **operational
> aftershock forecasting**, and **earthquake early warning** — ⚠️ **which is not prediction
> at all: it detects the fast P-wave and warns before the damaging S and surface waves
> arrive, buying seconds to tens of seconds. The physics is exploitation of wave speed
> difference, not foresight.**

---

## §6. Volcanism

**⚠️ Magma viscosity controls almost everything, and it's set by silica content and
dissolved volatiles:**
```
Basaltic     low silica, LOW viscosity  ⚠️ gas escapes easily → effusive lava flows
                                        Shield volcanoes (Hawaii, Iceland)
Andesitic    intermediate               Stratovolcanoes — the classic cone
Rhyolitic    high silica, HIGH viscosity ⚠️ gas cannot escape → EXPLOSIVE
                                        Calderas, ash flows, the largest eruptions
```
**⚠️ Explosivity is a gas-escape problem.** Viscous magma traps volatiles until pressure
overcomes strength — **the reason subduction-zone volcanoes are dangerous and Hawaiian ones
are tourist attractions.**

**Settings**: **divergent** (decompression melting), **subduction** (⚠️ **flux melting,
§2 → `geo-earth-structure-tectonics-rocks-and-deep-time` — and the source of most explosive volcanism**), **hotspots** (⚠️ **mantle plumes,
producing age-progressive island chains as the plate moves over a fixed source — Hawaii is
the type example, and plume theory is itself contested**).

**Hazards**: ⚠️ **pyroclastic density currents are the main killer — fast, hot, and
unsurvivable**; **lahars** (⚠️ **volcanic mudflows, which can occur years after an
eruption and travel far down valleys**); ash (⚠️ **an aviation hazard — it melts in jet
engines**); gas; and lava (⚠️ **rarely lethal, because it's slow**).
**VEI** is logarithmic by erupted volume.
