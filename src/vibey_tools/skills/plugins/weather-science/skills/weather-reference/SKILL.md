---
name: weather-reference
description: "Use when correcting a weather misconception, looking up a scale, rate or threshold value, finding the canon, or needing a picker and a method for reading a forecast critically. Companion to the other weather-science skills."
---

# Weather Science: Misconceptions, Numbers, and Canon

> **Part 5 of 5** of the *Weather Science* reference (plugin `weather-science`), covering §17–§21. Sibling skills: `weather-atmosphere-radiation-thermodynamics-and-moisture` (§0–§4), `weather-dynamics-circulation-and-synoptic` (§5–§7), `weather-severe-storms-cyclones-and-boundary-layer` (§8–§10), `weather-observation-nwp-verification-and-machine-learning` (§11–§16). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §17. Misconceptions

| Misconception | The correction |
|---|---|
| Air flows from high to low pressure | ⚠️ **Aloft it flows ALONG isobars — geostrophic balance** (§5.1 → `weather-dynamics-circulation-and-synoptic`) |
| Greenhouse gases "trap heat like a blanket" | ⚠️ **They raise the emission altitude; the lapse rate does the work** (§2 → `weather-atmosphere-radiation-thermodynamics-and-moisture`) |
| Stability is a property of an air parcel | ⚠️ **It's a comparison of parcel vs environment lapse rate** (§3 → `weather-atmosphere-radiation-thermodynamics-and-moisture`) |
| Relative humidity measures moisture content | ⚠️ **It's a ratio to saturation; changes with temperature alone** (§4 → `weather-atmosphere-radiation-thermodynamics-and-moisture`) |
| Rain forms by droplets simply growing | ⚠️ **Mid-latitude rain mostly starts as ice (Bergeron)** (§4 → `weather-atmosphere-radiation-thermodynamics-and-moisture`) |
| Wind shear helps all storms | ⚠️ **Organizes thunderstorms, DESTROYS hurricanes** (§8 → `weather-severe-storms-cyclones-and-boundary-layer`, §9 → `weather-severe-storms-cyclones-and-boundary-layer`) |
| The mesocyclone is the tornado | ⚠️ **Tornadogenesis needs near-ground vorticity too** (§8 → `weather-severe-storms-cyclones-and-boundary-layer`) |
| Hurricane category tells you the danger | ⚠️ **Saffir-Simpson is wind only. Surge and rain often dominate** (§9 → `weather-severe-storms-cyclones-and-boundary-layer`) |
| Coriolis determines bathtub drainage | ⚠️ **Orders of magnitude too small** (§5 → `weather-dynamics-circulation-and-synoptic`) |
| Better models will beat the two-week limit | ⚠️ **It's intrinsic to the atmosphere** (§14.1 → `weather-observation-nwp-verification-and-machine-learning`) |
| Chaos means climate projection is impossible | ⚠️ **Different problem: boundary-value, not initial-value** (§16 → `weather-observation-nwp-verification-and-machine-learning`) |
| Model resolution is the main limit on skill | ⚠️ **Parameterization and assimilation matter as much or more** (§12 → `weather-observation-nwp-verification-and-machine-learning`) |
| AI models have replaced NWP | ⚠️ **No agency has decommissioned one; they depend on NWP analyses** (§15.4 → `weather-observation-nwp-verification-and-machine-learning`) |
| AI models beat physics at everything | ⚠️ **Physics still wins on record-breaking extremes** (§15.2 → `weather-observation-nwp-verification-and-machine-learning`) |
| Lower RMSE means a better forecast | ⚠️ **RMSE rewards smoothing** (§13 → `weather-observation-nwp-verification-and-machine-learning`, §15.3 → `weather-observation-nwp-verification-and-machine-learning`) |
| "85% accurate" is a meaningful claim | ⚠️ **Skill requires a reference forecast** (§13 → `weather-observation-nwp-verification-and-machine-learning`) |

---

## §18. Numbers

```
STRUCTURE
Troposphere to ~11 km (8 polar / 17 tropical) · Scale height ~8 km
Standard sea level P 1013.25 hPa · ⚠️ pressure halves every ~5.5 km

RADIATION
Solar constant 1361 W/m² · ⚠️ ÷4 = ~340 W/m² global average
Albedo ~0.30 · Effective emitting temperature ~255 K · Surface mean ~288 K

LAPSE RATES ⚠️
Dry adiabatic 9.8 °C/km · Saturated ~4–7 °C/km · Standard average 6.5 °C/km

MOISTURE
⚠️ Clausius-Clapeyron ~7% more water vapour per °C
Homogeneous freezing ~−40 °C · supercooled water common above that

DYNAMICS
f = 2Ω sin φ · Ω = 7.292×10⁻⁵ rad/s · ⚠️ f = 0 at the equator
Jet stream cores 200–300 hPa, 30–60+ m/s (higher in winter)

SEVERE
CAPE: >1000 J/kg moderate · >2500 strong · >4000 extreme
⚠️ Supercells need strong deep-layer shear (~20 m/s over 0–6 km)
Tropical cyclone genesis: SST ≳26.5 °C, low shear, >~5° latitude

PREDICTABILITY ⚠️
Deterministic synoptic limit ~2 weeks (intrinsic) · ACC 0.6 ≈ useful skill limit
CFL: halving grid spacing costs ~8–16×
```

---

## §19. Books

| Author | Work | Why |
|---|---|---|
| **Wallace & Hobbs** | ***Atmospheric Science: An Introductory Survey*** | ⚠️ **The standard. Start here** |
| **Holton & Hakim** | ***An Introduction to Dynamic Meteorology*** | ⚠️ **§5 → `weather-dynamics-circulation-and-synoptic` and §7 → `weather-dynamics-circulation-and-synoptic` properly. The dynamics text** |
| **Markowski & Richardson** | ***Mesoscale Meteorology in Midlatitudes*** | ⚠️ **§8 → `weather-severe-storms-cyclones-and-boundary-layer`, definitively** |
| **Emanuel** | *Divine Wind* / *Atmospheric Convection* | §9 → `weather-severe-storms-cyclones-and-boundary-layer`, from the person who derived the intensity theory |
| **Bluestein** | *Synoptic-Dynamic Meteorology* | Deep synoptic |
| **Kalnay** | ***Atmospheric Modeling, Data Assimilation and Predictability*** | ⚠️ **§12 → `weather-observation-nwp-verification-and-machine-learning` and §14 → `weather-observation-nwp-verification-and-machine-learning`. The NWP reference** |
| **Lorenz** | *"Deterministic Nonperiodic Flow"* (1963) | ⚠️ **The paper. Short and readable** |
| **Rogers & Yau** | *A Short Course in Cloud Physics* | §4 → `weather-atmosphere-radiation-thermodynamics-and-moisture` |
| **Wilks** | *Statistical Methods in the Atmospheric Sciences* | ⚠️ **§13 → `weather-observation-nwp-verification-and-machine-learning` — verification done properly** |

**Practical**: **ECMWF newsletters and technical memoranda** (⚠️ **outstanding and free**),
**WeatherBench 2** (⚠️ **the ML benchmark — see the leaderboard before believing any skill
claim**), **AMS journals**, **NOAA/NWS training (COMET/MetEd)**, **university surface and
upper-air archives**, **ERA5 via Copernicus**, and **model output from open-meteo and
similar for hands-on work.**

---

## §20. Quick Reference

### 20.1 Picker
| Question | Look at |
|---|---|
| Will air rise? | ⚠️ **Compare ELR to DALR/SALR; check CAPE and CIN** (§3 → `weather-atmosphere-radiation-thermodynamics-and-moisture`) |
| Where's the wind aloft? | **Geostrophic — along the isobars** (§5.1 → `weather-dynamics-circulation-and-synoptic`) |
| Why is the jet there? | ⚠️ **Thermal wind — the temperature gradient** (§5.2 → `weather-dynamics-circulation-and-synoptic`) |
| Will a cyclone develop? | **Upper-level divergence ahead of a trough; PV thinking** (§5.3 → `weather-dynamics-circulation-and-synoptic`, §7.2 → `weather-dynamics-circulation-and-synoptic`) |
| Will storms organize? | ⚠️ **Deep-layer shear** (§8 → `weather-severe-storms-cyclones-and-boundary-layer`) |
| Will a hurricane intensify? | ⚠️ **SST, low shear, mid-level moisture** (§9 → `weather-severe-storms-cyclones-and-boundary-layer`) |
| How uncertain is this forecast? | ⚠️ **Ensemble spread — and check its calibration** (§12.3 → `weather-observation-nwp-verification-and-machine-learning`) |
| Is this forecast skillful? | ⚠️ **Against what reference, on what metric?** (§13 → `weather-observation-nwp-verification-and-machine-learning`) |
| Beyond ~2 weeks? | ⚠️ **Don't. Use statistics/teleconnections instead** (§14 → `weather-observation-nwp-verification-and-machine-learning`, §16 → `weather-observation-nwp-verification-and-machine-learning`) |
| Cheap global medium-range guidance | **ML models — with §15.2 → `weather-observation-nwp-verification-and-machine-learning`'s caveats** (§15 → `weather-observation-nwp-verification-and-machine-learning`) |
| A record-breaking extreme | ⚠️ **Trust physics-based HRES over current ML** (§15.2 → `weather-observation-nwp-verification-and-machine-learning`) |

### 20.2 Reading a forecast critically
- [ ] What's the lead time relative to the predictability limit? (§14 → `weather-observation-nwp-verification-and-machine-learning`)
- [ ] Deterministic or ensemble — and if ensemble, what's the spread? (§12.3 → `weather-observation-nwp-verification-and-machine-learning`)
- [ ] Is this a smoothed field that might be hiding an extreme? (§13 → `weather-observation-nwp-verification-and-machine-learning`, §15.3 → `weather-observation-nwp-verification-and-machine-learning`)
- [ ] Physics-based, ML, or blended — and does that matter for this event type? (§15 → `weather-observation-nwp-verification-and-machine-learning`)
- [ ] What's the reference forecast the skill claim is measured against? (§13 → `weather-observation-nwp-verification-and-machine-learning`)
- [ ] Is the hazard the headline variable, or something else (surge, rain)? (§9 → `weather-severe-storms-cyclones-and-boundary-layer`)

---

## §21. Method

**§1–§14 → `weather-atmosphere-radiation-thermodynamics-and-moisture`, `weather-dynamics-circulation-and-synoptic`, `weather-severe-storms-cyclones-and-boundary-layer`, `weather-observation-nwp-verification-and-machine-learning` and §16–§18 → `weather-observation-nwp-verification-and-machine-learning` rest on settled atmospheric physics** — hydrostatic and geostrophic
balance, thermodynamics, cloud microphysics, baroclinic instability, and **Lorenz
(1963)** — sourced from the references in §19, chiefly **Wallace & Hobbs**, **Holton &
Hakim**, **Markowski & Richardson**, and **Kalnay** for §12 → `weather-observation-nwp-verification-and-machine-learning` and §14 → `weather-observation-nwp-verification-and-machine-learning`. ⚠️ **None of that
needed verification; it has been stable for decades.**

**Two searches were run in August 2026**, both on §15 → `weather-observation-nwp-verification-and-machine-learning` — **the state of ML weather
prediction** and **its documented limitations.**

**Confidence.** **High** in §1–§14 → `weather-atmosphere-radiation-thermodynamics-and-moisture`, `weather-dynamics-circulation-and-synoptic`, `weather-severe-storms-cyclones-and-boundary-layer`, `weather-observation-nwp-verification-and-machine-learning` and §16–§18 → `weather-observation-nwp-verification-and-machine-learning`. **High** in §15 → `weather-observation-nwp-verification-and-machine-learning`'s factual claims, which
came out unusually well-sourced for a fast-moving area: **peer-reviewed primary literature**
(**Nature** for GenCast, **Science Advances** for the extremes result, **Geoscientific
Model Development** for AIFS, **npj Artificial Intelligence** for the assimilation review),
plus **ECMWF's own publications** and multiple **arXiv** evaluations.

⚠️ **What I want to flag is not uncertainty but a genuine disagreement in the field, and
I've deliberately given both sides rather than resolving it.** **The headline result — ML
ensembles surpassing ECMWF's ENS at a fraction of the cost — is real and comes from
peer-reviewed work.** **The counter-result — physics-based HRES still winning on
record-breaking extremes, with a proposed mechanism (an implicit ceiling from the training
distribution) — is also real and also peer-reviewed.** ⚠️ **One assessment I found put it
sharply: the accuracy headline contradicts the extremes evidence, and both camps know it.**

**⚠️ §15.3 → `weather-observation-nwp-verification-and-machine-learning` is my own synthesis of why they can both be right**, and I think it's the most
useful thing in the section: **RMSE structurally rewards smoothing (§13 → `weather-observation-nwp-verification-and-machine-learning`'s double-penalty
problem), so a model optimized against it can be genuinely better on average and
genuinely worse in the tail.** **That is not a contradiction; it's a consequence of the
objective function.** ⚠️ **The existence of work on fair extremes comparison — weighted
potential CRPS — is the field acknowledging the same thing.**

**One sourcing caution**: ⚠️ **claims like "AI outperforms on 90% of metrics" come from
vendor-adjacent and popular sources, and §15.3 → `weather-observation-nwp-verification-and-machine-learning` is the reason to distrust that framing.**
**The peer-reviewed claims are narrower and better specified, and I have used those.**
**The single most checkable fact in §15 → `weather-observation-nwp-verification-and-machine-learning`, and the one I'd anchor on: as of 2026 no major
meteorological agency has decommissioned its NWP system.**
