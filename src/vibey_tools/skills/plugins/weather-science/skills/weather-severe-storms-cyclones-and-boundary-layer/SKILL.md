---
name: weather-severe-storms-cyclones-and-boundary-layer
description: "Use when working on high-impact or local-scale weather: thunderstorms and severe weather including supercells, tornadoes, hail and the ingredients-based forecasting approach, tropical cyclones and their structure, intensification and forecast challenges, and the boundary layer and local effects such as sea breezes, terrain flows and urban heat."
---

# Weather Science: Thunderstorms and Severe Weather, Tropical Cyclones, and the Boundary Layer

> **Part 3 of 5** of the *Weather Science* reference (plugin `weather-science`), covering §8–§10. Sibling skills: `weather-atmosphere-radiation-thermodynamics-and-moisture` (§0–§4), `weather-dynamics-circulation-and-synoptic` (§5–§7), `weather-observation-nwp-verification-and-machine-learning` (§11–§16), `weather-reference` (§17–§21). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    weather is the atmosphere and ocean moving that surplus poleward** (§2.3 → `weather-atmosphere-radiation-thermodynamics-and-moisture`).
> 2. **⚠️ Rotation changes everything.** On a non-rotating planet air would flow directly
>    from high to low pressure. **The Coriolis effect makes it flow *along* isobars
>    instead**, and that single fact produces jet streams, cyclones, and the entire
>    structure of mid-latitude weather (§5 → `weather-dynamics-circulation-and-synoptic`).
> 3. **⚠️ The atmosphere is chaotic, and this is a mathematical property, not a
>    measurement problem.** Lorenz (1963) showed the predictability limit is intrinsic.
>    **No observing system and no model — physics-based or learned — removes it** (§14.1 → `weather-observation-nwp-verification-and-machine-learning`).

---

## §8. Thunderstorms and Severe Weather

**The three ingredients**: **moisture**, **instability** (CAPE, §3 → `weather-atmosphere-radiation-thermodynamics-and-moisture`), and **lift** (a
trigger). ⚠️ **Add the fourth — vertical wind shear — and you get organized, long-lived,
severe storms rather than brief single cells.**

```
Single cell     ⚠️ weak shear. The downdraft kills the updraft. ~30–60 min
Multicell       moderate shear. New cells form on the gust front
Supercell       ⚠️ STRONG shear. Rotating updraft (a mesocyclone). Long-lived,
                and responsible for most violent tornadoes and giant hail
MCS / squall line / bow echo / derecho    organized linear systems
```
**⚠️ Why shear matters, and it's the key insight**: in weak shear the storm's own cold
downdraft undercuts its updraft and it dies. **Shear tilts the updraft so precipitation
falls out away from the inflow, letting the storm sustain itself indefinitely.**

**⚠️ Supercell rotation comes from tilting horizontal vorticity into the vertical.**
Ambient wind shear creates horizontal spin; the updraft tilts it upright. **The
mesocyclone is not the tornado** — ⚠️ **tornadogenesis additionally requires vorticity
concentration near the ground, and the details remain incompletely understood despite
decades of field campaigns.**

**Hail** grows by accretion in the updraft; ⚠️ **size is limited by how long the stone can
be suspended, so updraft strength sets maximum hail size.**
**Downbursts and microbursts** — ⚠️ **an aviation hazard, and the cause of several fatal
accidents that drove the deployment of low-level wind shear detection.**
**Lightning** — charge separation via graupel-ice collisions in the mixed-phase region.

---

## §9. Tropical Cyclones

**⚠️ A fundamentally different machine from an extratropical cyclone**: a warm-core system
powered by **latent heat from a warm ocean**, not by baroclinic instability.

**Formation requirements**:
```
SST ≳ 26.5 °C through a deep layer   ⚠️ the fuel
Low vertical wind shear              ⚠️ shear TEARS THEM APART — opposite to §8
Sufficient Coriolis (⚠️ >~5° latitude — they cannot form on the equator)
Pre-existing disturbance
Mid-level moisture
```
**⚠️ Shear organizes thunderstorms and destroys hurricanes.** **The reason is structural:
a hurricane needs its warm core stacked vertically, and shear displaces it.**

**Structure**: eye (⚠️ **subsidence, calm, warm**), eyewall (⚠️ **the strongest winds and
the maximum latent heat release**), spiral rainbands, and outflow aloft.
**⚠️ Intensity is limited by thermodynamics** — the maximum potential intensity is
essentially a Carnot efficiency argument on the ocean-to-outflow temperature difference.
**Eyewall replacement cycles** cause intensity fluctuations.
**Rapid intensification** remains ⚠️ **the hardest operational forecast problem, and the
one with the worst consequences when missed.**

**⚠️ Storm surge kills more people than wind** in most landfalling cyclones, and it depends
on bathymetry, track angle and tide as much as on category. **The Saffir-Simpson scale
rates wind only** — ⚠️ **which is a genuine communication failure, because it says nothing
about surge or rainfall, and rainfall flooding is often the dominant hazard.**

---

## §10. Boundary Layer and Local Effects

**⚠️ The boundary layer is where friction, surface heating, and turbulence matter, and it
has a strong diurnal cycle**: a convective mixed layer by day (⚠️ **often capped by an
inversion**), a shallow stable layer at night with a decoupled residual layer above.

**Local circulations, all driven by differential heating**: sea/land breeze (⚠️ **water's
high heat capacity means land heats and cools faster**), mountain/valley winds, **urban
heat island.**

**Orographic effects**: forced ascent → windward precipitation; **rain shadow** and
⚠️ **föhn/chinook warming on the lee side — air descends dry-adiabatically after losing
moisture, so it arrives warmer than it started.** **Mountain waves and rotor turbulence
are aviation hazards.**

**⚠️ Radiation fog vs advection fog** — the first forms from nocturnal cooling under clear
calm skies, the second when warm moist air moves over a cold surface. **Different forecast
problems entirely.**
