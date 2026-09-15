---
name: weather-atmosphere-radiation-thermodynamics-and-moisture
description: "Use when reasoning about the physical state of the atmosphere: its vertical structure, radiation and the energy budget including the imbalance that actually drives weather, thermodynamics and stability with lapse rates, parcel theory and CAPE, and moisture and clouds including humidity measures, condensation and precipitation formation. Includes the router for the whole weather-science reference."
---

# Weather Science: The Atmosphere, Radiation and the Energy Budget, Thermodynamics, and Moisture

> **Part 1 of 5** of the *Weather Science* reference (plugin `weather-science`), covering §0–§4. Sibling skills: `weather-dynamics-circulation-and-synoptic` (§5–§7), `weather-severe-storms-cyclones-and-boundary-layer` (§8–§10), `weather-observation-nwp-verification-and-machine-learning` (§11–§16), `weather-reference` (§17–§21). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Atmospheric physics is settled — hydrostatic balance, geostrophy, Lorenz's 1963 chaos work. One area moved dramatically. See §15 → `weather-observation-nwp-verification-and-machine-learning` for machine-learning weather prediction and the live scientific dispute around it.

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
>    weather is the atmosphere and ocean moving that surplus poleward** (§2.3).
> 2. **⚠️ Rotation changes everything.** On a non-rotating planet air would flow directly
>    from high to low pressure. **The Coriolis effect makes it flow *along* isobars
>    instead**, and that single fact produces jet streams, cyclones, and the entire
>    structure of mid-latitude weather (§5 → `weather-dynamics-circulation-and-synoptic`).
> 3. **⚠️ The atmosphere is chaotic, and this is a mathematical property, not a
>    measurement problem.** Lorenz (1963) showed the predictability limit is intrinsic.
>    **No observing system and no model — physics-based or learned — removes it** (§14.1 → `weather-observation-nwp-verification-and-machine-learning`).

---

## §0. Routing

| You want... | Go to |
|---|---|
| Atmospheric structure | §1 |
| **Radiation and the energy budget** | **§2** |
| **Thermodynamics and stability** | **§3** |
| Moisture and clouds | §4 |
| **Dynamics — the balances** | **§5 → `weather-dynamics-circulation-and-synoptic`** |
| General circulation | §6 → `weather-dynamics-circulation-and-synoptic` |
| **Synoptic systems and fronts** | **§7 → `weather-dynamics-circulation-and-synoptic`** |
| Thunderstorms and tornadoes | §8 → `weather-severe-storms-cyclones-and-boundary-layer` |
| Tropical cyclones | §9 → `weather-severe-storms-cyclones-and-boundary-layer` |
| Boundary layer and local effects | §10 → `weather-severe-storms-cyclones-and-boundary-layer` |
| Observation | §11 → `weather-observation-nwp-verification-and-machine-learning` |
| **Numerical weather prediction** | **§12 → `weather-observation-nwp-verification-and-machine-learning`** |
| Forecast verification | §13 → `weather-observation-nwp-verification-and-machine-learning` |
| **Predictability and chaos** | **§14 → `weather-observation-nwp-verification-and-machine-learning`** |
| **ML weather prediction** | **§15 → `weather-observation-nwp-verification-and-machine-learning`** |
| Weather vs climate | §16 → `weather-observation-nwp-verification-and-machine-learning` |
| Misconceptions | §17 → `weather-reference` |
| Numbers | §18 → `weather-reference` |
| Books | §19 → `weather-reference` |
| Quick reference | §20 → `weather-reference` |

---

## §1. Structure of the Atmosphere

```
Troposphere    surface–~11 km  ⚠️ ALL weather. Temperature DECREASES with height
Tropopause     ⚠️ the lid — ~8 km polar, ~17 km tropical
Stratosphere   ~11–50 km  temperature INCREASES (ozone absorbs UV) ⚠️ → very stable
Mesosphere     ~50–85 km  decreases again
Thermosphere   >85 km     increases; extremely thin
```
**⚠️ The tropopause is a lid because the stratosphere's temperature inversion makes it
strongly stable** — rising air becomes colder than its surroundings and stops.
**This is why thunderstorm anvils spread horizontally**, and why weather is confined to the
lowest ~10 km.

**Composition**: N₂ 78%, O₂ 21%, Ar 0.93%, CO₂ ~0.04% and rising, **water vapour 0–4% and
highly variable** — ⚠️ **water vapour is the variable one, and its variability is most of
what makes weather.**

**Hydrostatic balance** — ⚠️ **the single most important approximation in meteorology:**
```
dP/dz = −ρg
```
**The upward pressure-gradient force balances gravity.** ⚠️ **Excellent to within a
fraction of a percent for large-scale flow, and it fails only in deep convection** — which
is exactly why convection-resolving models must be **non-hydrostatic** (§12.1 → `weather-observation-nwp-verification-and-machine-learning`).
**Scale height** ≈ 8 km — pressure falls roughly exponentially, halving about every 5.5 km.

---

## §2. Radiation and the Energy Budget

**Solar constant** ≈ **1361 W/m²** at the top of the atmosphere. ⚠️ **Averaged over the
rotating sphere, that's ÷4 ≈ 340 W/m²** — the geometric factor that surprises people.

**Shortwave in, longwave out**: the Sun (~5800 K) emits in the visible; Earth (~255 K
effective) emits in the infrared. ⚠️ **Greenhouse gases are largely transparent to
shortwave and absorbing in longwave, which is the entire mechanism.**

**Albedo** ≈ 0.30 globally. **Clouds both cool (reflecting shortwave) and warm (trapping
longwave)** — ⚠️ **the net depends on cloud height and thickness: low thick clouds cool, high
thin cirrus warm. Cloud feedback remains the largest uncertainty in climate sensitivity.**

**⚠️ The greenhouse mechanism, stated correctly**: greenhouse gases don't "trap heat" like
a blanket. **They absorb outgoing longwave and re-emit in all directions, including
downward — which raises the altitude from which radiation finally escapes to space.**
⚠️ **Because temperature falls with height, emitting from higher up means emitting at a
colder temperature and therefore less efficiently — so the surface must warm to restore
balance.** **The lapse rate is essential to the argument, and explanations that omit it
are incomplete.**

### 2.3 ⚠️ The energy imbalance that drives weather
**The tropics absorb more energy than they emit; the poles emit more than they absorb.**
⚠️ **Weather is the transport mechanism that closes that gap** — roughly split between
the atmosphere (sensible heat, latent heat, and eddies) and the ocean. **Every storm system
in §7 → `weather-dynamics-circulation-and-synoptic` is part of this transport.**

---

## §3. Thermodynamics and Stability

**Adiabatic processes** — no heat exchange, so rising air expands and cools by doing work
on its surroundings.
```
Dry adiabatic lapse rate (DALR)     ⚠️ 9.8 °C/km — a constant, from physics
Saturated adiabatic lapse rate      ⚠️ ~4–7 °C/km — LESS, because condensation
                                    releases latent heat that partly offsets cooling
Environmental lapse rate (ELR)      ⚠️ whatever the actual sounding says — measured
Standard atmosphere average         6.5 °C/km
```
> **⚠️ GOTCHA — stability is a COMPARISON between the parcel's lapse rate and the
> environment's, not a property of either alone.**
> ```
> ELR < SALR           absolutely stable    ⚠️ parcel always colder → sinks back
> SALR < ELR < DALR    conditionally unstable ⚠️ stable if dry, unstable if saturated
>                      — and this is the common atmospheric state
> ELR > DALR           absolutely unstable  ⚠️ rare and short-lived; convection
>                      destroys it immediately
> ```
> **⚠️ "Conditionally unstable" is the key state: the atmosphere is often stable to dry
> displacement and unstable once a parcel saturates.** **That's why you need a trigger to
> get a thunderstorm even when the environment is primed** (§8 → `weather-severe-storms-cyclones-and-boundary-layer`).

**Potential temperature `θ`** — the temperature a parcel would have if brought
adiabatically to 1000 hPa. ⚠️ **Conserved under dry adiabatic motion, which makes it the
natural vertical coordinate for tracking air masses.** **`θ_e` (equivalent potential
temperature)** is conserved including moisture, and is the workhorse variable.

**CAPE / CIN** — ⚠️ **CAPE (Convective Available Potential Energy) is the integrated
buoyancy available to a rising parcel, in J/kg — it's the fuel.** **CIN (Convective
Inhibition) is the energy barrier that must be overcome first — it's the lid.**
⚠️ **High CAPE with strong CIN means nothing happens until something breaks the cap — and
then everything happens at once.** **This is why the most violent storms often form in
capped environments.**

---

## §4. Moisture and Clouds

**Measures**: **mixing ratio** and **specific humidity** (⚠️ **conserved under
temperature change — use these for tracking**), **relative humidity** (⚠️ **a ratio to
saturation, so it changes when temperature changes even with constant moisture — which
is why RH is a poor moisture variable**), **dewpoint** (⚠️ **the good intuitive one**), and
**wet-bulb temperature.**

**⚠️ Clausius-Clapeyron**: saturation vapour pressure rises roughly exponentially with
temperature — **about 7% per °C.** ⚠️ **This is one of the most consequential numbers in
atmospheric science**: warmer air holds substantially more water, which sets the scaling
for extreme precipitation intensity.

**⚠️ Cloud formation requires condensation nuclei.** Homogeneous nucleation needs
supersaturation of several hundred percent; **with CCN present, clouds form at just over
100%.** ⚠️ **Aerosol therefore controls cloud droplet number and size, which controls
albedo and precipitation efficiency — the aerosol-cloud interaction, and the largest
uncertainty in radiative forcing.**

**Precipitation formation**, two pathways:
- **Collision-coalescence** — warm clouds, droplets growing by collision. ⚠️ **Slow;
  needs a deep warm cloud.**
- **Bergeron-Findeisen (ice process)** — ⚠️ **the dominant mechanism in mid-latitudes.**
  **Saturation vapour pressure over ice is lower than over supercooled water, so ice
  crystals grow at the expense of surrounding droplets.** **Most rain in temperate regions
  starts as snow.**
- **⚠️ Supercooled water is common** down to about −40 °C, below which homogeneous freezing
  finally occurs. **This is the aircraft icing hazard.**

**Cloud classification** by altitude and form: cirro- (high), alto- (mid), strato-
(layered), cumulo- (heaped), nimbo- (precipitating). ⚠️ **Cumulonimbus is the only cloud
that produces lightning, hail and tornadoes.**
