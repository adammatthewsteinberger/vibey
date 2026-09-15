---
name: geo-reference
description: "Use when checking what observation recently changed in the field (satellite gravimetry and continental drying, and deep learning in seismology, verified August 2026), correcting a geoscience misconception, looking up a rate, depth or magnitude, finding the canon, or needing a picker and the sanity checks for a geoscience claim. Companion to the other geoscience skills."
---

# Geoscience: What Observation Recently Changed, Misconceptions, Numbers, and Canon

> **Part 5 of 5** of the *Geoscience* reference (plugin `geoscience`), covering §17–§22. Sibling skills: `geo-earth-structure-tectonics-rocks-and-deep-time` (§0–§4), `geo-earthquakes-seismology-and-volcanism` (§5–§6), `geo-surface-processes-soils-and-hydrology` (§7–§10), `geo-oceans-cryosphere-cycles-hazards-and-observation` (§11–§16). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Tectonics, stratigraphy, hydraulics and seismological theory are settled; satellite-measured continental water storage and deep learning in seismology recently changed the science. See §17 below for both.

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
>    §10 → `geo-surface-processes-soils-and-hydrology` is the most consequential section here (§10 → `geo-surface-processes-soils-and-hydrology`, §17.1).

---

## §17. What Observation Recently Changed — verified August 2026

### 17.1 ⚠️ Satellite gravimetry and continental drying
**GRACE and GRACE-FO measure the mass of water by its gravitational signal** — ⚠️ **a
genuinely new observational capability that lets us weigh continental water storage
directly rather than infer it.**

**The findings, from peer-reviewed work:**
- **⚠️ A Science Advances study reports unprecedented terrestrial water storage loss since
  2002**, with **areas experiencing drying increasing by twice the size of California
  annually** (~831,600 km²/yr), forming **"mega-drying" regions across the Northern
  Hemisphere.**
- **⚠️ Groundwater depletion accounts for 68% of terrestrial water storage loss over
  non-glaciated continental regions.**
- **⚠️ Dry areas are now drying faster than wet areas are wetting** — which is not what a
  simple "wet gets wetter" framing predicts.
- **⚠️ The continents now contribute more freshwater to sea level rise than the ice
  sheets**, and drying regions contribute more than glaciers and ice caps. **That
  reframes the sea level budget.**
- **75% of the population lives in 101 countries that have been losing freshwater.**
- **A separate GRACE/GRACE-FO analysis over 21.5 years** finds **groundwater depletion
  dominating freshwater decline at continental scales, most prominently in Asia at
  −55 km³/yr**, ⚠️ **while ice mass loss remains the largest single global contributor by
  component** — **and it identifies emerging groundwater *gains* in some regions
  alongside widespread decline.**
- **NASA reports 21 of Earth's 37 largest aquifers have exceeded sustainability tipping
  points, 13 of them significantly distressed.**

> **⚠️ GOTCHA — GRACE is powerful and it has real uncertainties, and the literature is
> explicit about this.** ⚠️ **Groundwater storage is not measured directly — it's derived
> by subtracting modelled soil moisture, snow, surface water and glacier contributions
> from total water storage, so model error propagates in.** **A published re-analysis
> found earlier GRACE-based depletion rates for the Northwest India Aquifer were likely
> overestimates**, with constrained forward modelling giving **~14 km³/yr against a
> published ~18 km³/yr** — and the corrected figure matched well-monitoring data.
> ⚠️ **Where GRACE has been compared against dense well networks it generally agrees
> (correlations ~0.52–0.95 across major US aquifers), which is the reassuring part — but
> treat single-basin headline numbers with more caution than continental-scale trends.**

**⚠️ Why this belongs in a geoscience document rather than a news summary**: it is a
**measurement capability change**, not a policy story. **We can now weigh the continents'
water, and the answer differed from what models assumed.**

### 17.2 ⚠️ Deep learning in seismology
**A quieter revolution, and it changed what the observational record contains.**

**The problem it solved**: ⚠️ **STA/LTA detection had been the backbone of real-time
seismic processing since the earliest digital acquisition, and manual picking by skilled
analysts had become impossible to scale as channel counts grew.**

**The models**: **PhaseNet** (⚠️ **Zhu & Beroza 2019 — a U-Net that reformulates phase
picking as image segmentation**), **EQTransformer** (⚠️ **Mousavi et al. 2020 — CNN +
LSTM + self-attention doing joint detection and picking, and notably compact at ~379k
parameters**), **GPD**, and association methods like **GaMMA**.

**⚠️ The consequence for the science, which is the important part**: **these models detect
earthquakes missed by standard methods**, and the resulting catalogues have
⚠️ **contributed to uncovering fault-structure complexity and earthquake swarm dynamics,
giving new insight into aseismic crustal processes.** **One 2026 study applying a DL
workflow to a single day containing a major mainshock obtained 5,315 earthquakes — reduced
to 3,839 after location-quality filtering — against 1,086 in the manually reviewed
catalogue.** ⚠️ **The record got several times denser, and denser catalogues change what
questions you can ask.**

**⚠️ DAS is the amplifier.** **PhaseNet-DAS** applies this to fibre-optic distributed
acoustic sensing, ⚠️ **turning existing telecom cable into an ultra-dense seismic array.**
The scale is different in kind: **applied to ~9,839 catalogued earthquakes near one array,
it produced ~36 million P-picks and ~53 million S-picks.** **Submarine and ocean-bottom
variants (DeepSubDAS, PickBlue, OBSTransformer) extend it to marine environments** —
⚠️ **which matters because seismometers are scarce at sea and most plate boundaries are
underwater.**

**⚠️ The honest caveats, and the literature is candid**: models trained on regional surface
stations at 100 Hz ⚠️ **transfer poorly to high-frequency borehole data (2000 Hz) and to
DAS without retraining**; there is documented **prediction inconsistency and parameter
dependence** in neural pickers, with active work on mitigation; and ⚠️ **catalogue
performance is variable enough that a 2026 paper is titled, in effect, "which is better:
deep learning or manual picking?"** — **it is not a settled rout.**

---

## §18. Misconceptions

| Misconception | Correction |
|---|---|
| Plates float on molten rock | ⚠️ **The asthenosphere is solid and ductile. S-waves prove it** (§1.1 → `geo-earth-structure-tectonics-rocks-and-deep-time`) |
| Convection currents drag plates | ⚠️ **Slab pull dominates; plates are the top of the system** (§1.2 → `geo-earth-structure-tectonics-rocks-and-deep-time`) |
| Continental crust subducts | ⚠️ **Too buoyant — it collides and thickens** (§1.2 → `geo-earth-structure-tectonics-rocks-and-deep-time`) |
| ¹⁴C dates rocks and dinosaurs | ⚠️ **Organic only, ~50 ka limit** (§3 → `geo-earth-structure-tectonics-rocks-and-deep-time`) |
| You date a sedimentary rock directly | ⚠️ **The grains predate the deposit. Bracket it** (§3 → `geo-earth-structure-tectonics-rocks-and-deep-time`) |
| The rock record is continuous | ⚠️ **It's mostly gaps** (§3 → `geo-earth-structure-tectonics-rocks-and-deep-time`) |
| Richter is the modern magnitude scale | ⚠️ **M_w is; Richter saturates above ~7** (§5.3 → `geo-earthquakes-seismology-and-volcanism`) |
| Magnitude describes shaking at a place | ⚠️ **That's intensity. Magnitude is the source** (§5.3 → `geo-earthquakes-seismology-and-volcanism`) |
| Earthquakes are predictable short-term | ⚠️ **They are not. Early warning ≠ prediction** (§5.4 → `geo-earthquakes-seismology-and-volcanism`) |
| Lava is the main volcanic killer | ⚠️ **Pyroclastic flows and lahars are** (§6 → `geo-earthquakes-seismology-and-volcanism`) |
| All volcanoes erupt similarly | ⚠️ **Viscosity and gas escape decide everything** (§6 → `geo-earthquakes-seismology-and-volcanism`) |
| Fine sediment erodes most easily | ⚠️ **Cohesion — see the Hjulström curve** (§7 → `geo-surface-processes-soils-and-hydrology`) |
| Porosity and permeability are the same | ⚠️ **Clay: high porosity, no permeability** (§10 → `geo-surface-processes-soils-and-hydrology`) |
| Groundwater flows downhill | ⚠️ **It follows hydraulic head, and can flow up** (§10 → `geo-surface-processes-soils-and-hydrology`) |
| Aquifers refill if you stop pumping | ⚠️ **Compaction is often permanent** (§10 → `geo-surface-processes-soils-and-hydrology`, §17.1) |
| "Fossil water" is renewable | ⚠️ **Millennial residence times. It's mining** (§10 → `geo-surface-processes-soils-and-hydrology`) |
| A 100-year flood happens once a century | ⚠️ **1% annual probability. ~26% chance in 30 years** (§9 → `geo-surface-processes-soils-and-hydrology`) |
| Levees eliminate flood risk | ⚠️ **They transfer it and encourage exposure** (§9 → `geo-surface-processes-soils-and-hydrology`) |
| Melting sea ice raises sea level | ⚠️ **It's floating. Land ice is the one that matters** (§12 → `geo-oceans-cryosphere-cycles-hazards-and-observation`) |
| Soil is renewable on human timescales | ⚠️ **0.01–0.1 mm/yr** (§8 → `geo-surface-processes-soils-and-hydrology`) |
| Rare earths are geologically rare | ⚠️ **Processing and supply concentration are the constraint** (§14 → `geo-oceans-cryosphere-cycles-hazards-and-observation`) |
| Reserves = how much exists | ⚠️ **Reserves are economic; resources are geological** (§14 → `geo-oceans-cryosphere-cycles-hazards-and-observation`) |
| Silicate weathering will fix CO₂ | ⚠️ **It's the thermostat, and it's ~10⁵–10⁶ years too slow** (§13 → `geo-oceans-cryosphere-cycles-hazards-and-observation`) |
| Disaster losses rise because hazards rise | ⚠️ **Exposure and vulnerability dominate** (§15 → `geo-oceans-cryosphere-cycles-hazards-and-observation`) |
| A geophysical inversion gives the answer | ⚠️ **Non-unique. Needs constraints and uncertainty** (§16 → `geo-oceans-cryosphere-cycles-hazards-and-observation`) |

---

## §19. Numbers

```
EARTH
Radius 6371 km · Age 4.54 Ga · Crust 0–35 km (oceanic ~7 km)
Lithosphere ~100 km · Mantle to 2890 km · Core to 6371 km
⚠️ Deepest borehole ~12 km · Plate motion 10–100 mm/yr
⚠️ Oldest ocean floor ~200 Ma · Oldest continental crust ~4 Ga

TIME
4.54 Ga formation · 2.4 Ga Great Oxidation · 541 Ma Cambrian
252 Ma Permian-Triassic (~90% marine species) · 66 Ma K-Pg · 11.7 ka Holocene
¹⁴C half-life 5730 yr, ⚠️ useful to ~50 ka

EARTHQUAKES
⚠️ +1 magnitude = ~32× energy · +2 = ~1000×
P ~6 km/s crust, S ~3.5 km/s · ⚠️ brittle-ductile transition ~10–15 km
M₀ = μAD

WATER
Ocean 96.5% of Earth's water · ice caps ~1.7% · ⚠️ groundwater ~1.7%
Rivers and lakes ~0.01% · Ocean salinity ~35 psu
Thermohaline overturning ~1000 yr
⚠️ Groundwater residence: days to millions of years
Darcy: Q = −KA(dh/dl)

RATES
⚠️ Soil formation 0.01–0.1 mm/yr
Continental drying expansion ~831,600 km²/yr (§17.1)
⚠️ Groundwater = 68% of non-glaciated continental TWS loss (§17.1)
Asia groundwater trend ~−55 km³/yr (§17.1)
```

---

## §20. Books

| Author | Work | Why |
|---|---|---|
| **Marshak** | ***Earth: Portrait of a Planet*** | ⚠️ **The best broad introduction** |
| **Press, Siever et al.** | *Understanding Earth* | Classic survey |
| **Stein & Wysession** | ***An Introduction to Seismology, Earthquakes, and Earth Structure*** | ⚠️ **§5 → `geo-earthquakes-seismology-and-volcanism` and §16 → `geo-oceans-cryosphere-cycles-hazards-and-observation`, definitively** |
| **Fetter** | ***Applied Hydrogeology*** | ⚠️ **§10 → `geo-surface-processes-soils-and-hydrology`, the standard** |
| **Freeze & Cherry** | ***Groundwater*** | ⚠️ **The classic, and now free online** |
| **Anderson, Woessner & Hunt** | *Applied Groundwater Modeling* | §10 → `geo-surface-processes-soils-and-hydrology` quantitatively |
| **Dingman** | *Physical Hydrology* | §9 → `geo-surface-processes-soils-and-hydrology` |
| **Bierman & Montgomery** | ***Key Concepts in Geomorphology*** | §7 → `geo-surface-processes-soils-and-hydrology` |
| **Montgomery** | ***Dirt: The Erosion of Civilizations*** | ⚠️ **§8 → `geo-surface-processes-soils-and-hydrology`'s stakes, superbly written** |
| **McPhee** | ***Annals of the Former World*** | ⚠️ **The best writing about geology, full stop. Read it for deep time (§3 → `geo-earth-structure-tectonics-rocks-and-deep-time`)** |
| **Talley et al.** | *Descriptive Physical Oceanography* | §11 → `geo-oceans-cryosphere-cycles-hazards-and-observation` |
| **Cuffey & Paterson** | *The Physics of Glaciers* | §12 → `geo-oceans-cryosphere-cycles-hazards-and-observation` |

**Practical**: **USGS publications and data** (⚠️ **enormous, free, authoritative**),
**national geological survey maps**, **IRIS/EarthScope** for seismic data, **GRACE/
GRACE-FO at JPL** (§17.1), **Copernicus/Sentinel** and **Landsat** archives, **ObsPy** and
**SeisBench** for seismological work in Python, **MODFLOW** for groundwater modelling,
and **QGIS**.

---

## §21. Quick Reference

### 21.1 Picker
| Question | Approach |
|---|---|
| How old is this rock? | ⚠️ **U-Pb zircon; bracket sediments with ash or intrusions** (§3 → `geo-earth-structure-tectonics-rocks-and-deep-time`) |
| How old is this organic material (<50 ka)? | **¹⁴C** (§3 → `geo-earth-structure-tectonics-rocks-and-deep-time`) |
| Where was the earthquake? | ⚠️ **S−P times from ≥3 stations** (§5.2 → `geo-earthquakes-seismology-and-volcanism`) |
| How big was it? | **M_w from seismic moment** (§5.3 → `geo-earthquakes-seismology-and-volcanism`) |
| How much will it shake *here*? | ⚠️ **Site conditions — soft sediment amplifies** (§5.3 → `geo-earthquakes-seismology-and-volcanism`) |
| Will this slope fail? | ⚠️ **Factor of safety; pore pressure after rain** (§7 → `geo-surface-processes-soils-and-hydrology`) |
| How much water will this well yield? | **Darcy, aquifer tests, cone of depression** (§10 → `geo-surface-processes-soils-and-hydrology`) |
| Is this water source sustainable? | ⚠️ **Compare extraction to recharge, and check residence time** (§10 → `geo-surface-processes-soils-and-hydrology`) |
| Is the ground subsiding? | ⚠️ **InSAR** (§16 → `geo-oceans-cryosphere-cycles-hazards-and-observation`) |
| Is the aquifer losing storage regionally? | ⚠️ **GRACE, with §17.1's caveats** (§17.1) |
| Are there earthquakes we're missing? | ⚠️ **DL phase picking; DAS if fibre is available** (§17.2) |
| What's the flood risk here? | ⚠️ **Return period ≠ schedule; check non-stationarity** (§9 → `geo-surface-processes-soils-and-hydrology`) |
| Map faults under forest | **LiDAR bare-earth** (§16 → `geo-oceans-cryosphere-cycles-hazards-and-observation`) |

### 21.2 Sanity checks
- [ ] What timescale is this process on, and does my intuition match it? (§3 → `geo-earth-structure-tectonics-rocks-and-deep-time`)
- [ ] Am I confusing rate with total, or magnitude with intensity? (§5.3 → `geo-earthquakes-seismology-and-volcanism`)
- [ ] Is this a probability or a schedule? (§9 → `geo-surface-processes-soils-and-hydrology`)
- [ ] Is this resource renewable *at the rate I'm using it*? (§10 → `geo-surface-processes-soils-and-hydrology`, §14 → `geo-oceans-cryosphere-cycles-hazards-and-observation`)
- [ ] Is this measurement direct, or derived by subtracting models? (§17.1)
- [ ] Is this inversion unique, and where's the uncertainty? (§16 → `geo-oceans-cryosphere-cycles-hazards-and-observation`)
- [ ] Is the trend hazard, or exposure and vulnerability? (§15 → `geo-oceans-cryosphere-cycles-hazards-and-observation`)

---

## §22. Method

**§1–§16 → `geo-earth-structure-tectonics-rocks-and-deep-time`, `geo-earthquakes-seismology-and-volcanism`, `geo-surface-processes-soils-and-hydrology`, `geo-oceans-cryosphere-cycles-hazards-and-observation` and §18–§19 rest on settled science** — plate tectonics (confirmed 1960s),
stratigraphic principles (Steno, Hutton, Lyell), radiometric dating, Darcy's law (1856),
elastic rebound (Reid, 1910), and seismological wave theory — sourced from the references
in §20, chiefly **Marshak**, **Stein & Wysession**, **Fetter**, **Freeze & Cherry**, and
**Bierman & Montgomery**. ⚠️ **None of that needed verification.**

**Scoped to complement**: the atmosphere sits in a weather-science reference, and the
mechanics in a Newtonian-mechanics reference. ⚠️ **§9 → `geo-surface-processes-soils-and-hydrology`'s floods and §12 → `geo-oceans-cryosphere-cycles-hazards-and-observation`'s cryosphere touch
both deliberately.**

**Two searches were run in August 2026**, and ⚠️ **both were about measurement capability
rather than events** — which is why §17 is framed as "what observation changed" rather than
as news. **The science moved because we can now measure things we couldn't.**

**Confidence.** **High** in §1–§16 → `geo-earth-structure-tectonics-rocks-and-deep-time`, `geo-earthquakes-seismology-and-volcanism`, `geo-surface-processes-soils-and-hydrology`, `geo-oceans-cryosphere-cycles-hazards-and-observation`. **High** in §17's factual content, which came from
**peer-reviewed primary literature** — **Science Advances** and **EGUsphere/Copernicus**
for §17.1, **NASA/JPL** mission pages, and **Nature Communications, Geophysical Journal
International, Geophysical Journal International (2026), and Scientific Reports** for
§17.2.

⚠️ **The §17.1 caveat is the one I'd want carried forward, and I've given it a gotcha box
rather than a footnote.** **GRACE does not measure groundwater — it measures total mass
change, and groundwater is what's left after subtracting modelled soil moisture, snow,
surface water and glaciers.** ⚠️ **Model error propagates directly into the headline
number.** **The published re-analysis finding earlier Northwest India depletion rates were
likely overestimated is exactly the kind of correction that gets far less attention than
the original alarming figure** — and **the validation against ~23,000 monitoring wells
across US aquifers (correlations 0.52–0.95) is the reason to trust continental-scale
trends more than single-basin headlines.**

⚠️ **§17.2 I have deliberately not overstated.** **Deep learning genuinely transformed
seismic catalogue density — several-fold more events in the case I cited — and the
limitations are documented in the same literature**: poor transfer to high-frequency
borehole and DAS data without retraining, prediction inconsistency requiring mitigation,
and **an active 2026 paper still asking whether deep learning or manual picking is
better.** **A denser catalogue is not automatically a better one, and the field knows
it.**
