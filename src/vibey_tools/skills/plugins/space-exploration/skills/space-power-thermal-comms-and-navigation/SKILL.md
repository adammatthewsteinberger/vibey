---
name: space-power-thermal-comms-and-navigation
description: "Use when sizing or debugging a spacecraft bus subsystem: power (solar arrays, radioisotope sources, batteries, and the eclipse and degradation budgets), thermal control (radiators, louvres, multilayer insulation, heaters and the thermal balance), communications including the link budget, what it means in practice, light-time and its consequences, and relay architecture, and deep space navigation and onboard autonomy."
---

# Space Exploration: Power, Thermal Control, Communications, and Navigation

> **Part 2 of 5** of the *Space Exploration* reference (plugin `space-exploration`), covering §3–§6. Sibling skills: `space-mission-architecture-and-trajectory` (§0–§2), `space-attitude-propulsion-and-edl` (§7–§8), `space-human-factors-life-support-and-reliability` (§9–§14), `space-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The physics and subsystem engineering are stable; radiation dose limits and ISRU and life-support performance have real recent data. See §17 → `space-reference` for what is genuinely open.

> **How to read this.** The engineering of getting somewhere and doing something once
> you're there. **Launch, staging, orbital mechanics and reentry heating physics are
> covered in a rocket-science reference** — this document assumes them and points there
> rather than duplicating. **Flight software practice** sits in a robotics-software
> reference (§14 there).
>
> Two markers:
> - **[DURABLE]** — physics, subsystem engineering, and design constraints. Most of this.
> - **[CONTESTED]** — genuine disagreement about approach.
>
> **⚠️ GOTCHA** boxes mark where a mission has died, or where the constraint is harder
> than it looks.
>
> **The three constraints that generate every mission design:**
> 1. **⚠️ Mass is the currency and everything converts to it.** Power converts to mass
>    (arrays, radioisotopes, radiators). Data rate converts to mass (antenna, power).
>    Reliability converts to mass (redundancy). Crew time converts to mass (consumables).
>    **You are always spending the same budget** (§1.3 → `space-mission-architecture-and-trajectory`).
> 2. **Distance imposes latency and darkness.** Light-time makes teleoperation impossible
>    beyond the Moon, forcing autonomy (§6); inverse-square makes both sunlight and
>    signal scarce (§3, §5).
> 3. **⚠️ For crewed deep space, the binding constraint is not propulsion — it's human
>    physiology.** Radiation dose and microgravity deconditioning bound mission duration
>    more tightly than Δv does (§9 → `space-human-factors-life-support-and-reliability`).

---

## §3. Power

**[DURABLE] Solar flux scales as `1/r²`, and this single fact partitions the solar
system:**
```
Venus   0.72 AU   2,600 W/m²
Earth   1.00 AU   1,361 W/m²    (the solar constant)
Mars    1.52 AU     590 W/m²    ⚠️ 43% of Earth
Jupiter 5.20 AU      50 W/m²
Saturn  9.54 AU      15 W/m²
Pluto  39.5 AU        0.9 W/m²  ⚠️ 0.07% of Earth
```
**⚠️ Solar becomes impractical roughly beyond Jupiter** — Juno flies enormous arrays at
Jupiter and is the outer limit of the approach. **Beyond that, radioisotope power is not a
preference; it's the only option.**

**Solar arrays**: triple-junction GaAs at **~30–32% efficiency**, degrading with radiation
(⚠️ **severe in Jupiter's belts and in GEO**), temperature, and dust (⚠️ **the Mars dust
accumulation that ended Opportunity and InSight**). **Always quote BOL and EOL** — the
difference can be 15–30% over a long mission.

**RTGs**: ²³⁸Pu, **87.7-year half-life**, thermoelectric conversion at only **~6–7%**
efficiency. **MMRTG ≈ 110 W electrical at BOL from ~2,000 W thermal**, decaying **~1.6%/yr**
(⚠️ **combining fuel decay and thermocouple degradation**). **⚠️ The binding constraint is
plutonium supply, not engineering** — US production restarted in 2013 at kilograms per
year, and it gates outer-planet missions.

**⚠️ The waste heat is a feature**: RTG thermal output keeps spacecraft warm in the outer
solar system, which is why RTG missions often need less dedicated survival heating.

**Batteries** (Li-ion, ~100–250 Wh/kg) size to **eclipse duration and peak load**, with
**depth-of-discharge traded against cycle life** — ⚠️ **a LEO spacecraft sees ~16
eclipses/day, so ~90,000 cycles over 15 years**, which forces shallow DoD.

**Fuel cells** for short crewed missions (⚠️ **Apollo's produced drinking water as a
by-product**), **fission** (Kilopower/KRUSTY demonstrated 1–10 kW class) for surface power
where solar duty cycle fails — ⚠️ **a lunar night is 14 Earth days, which no practical
battery bridges.**

---

## §4. Thermal Control

**[DURABLE] In vacuum there is no convection.** Heat moves by conduction and radiation
only, and radiation is the only path off the vehicle:
```
Q_rad = εσA(T⁴ − T_sink⁴)
```
**⚠️ The `T⁴` is brutal**: rejecting heat from a cold radiator requires enormous area.
A radiator at 300 K rejects ~460 W/m² at best; at 200 K, ~91 W/m².

**Equilibrium temperature** from absorbed sunlight:
```
T_eq = [ (α/ε) · S · A_proj / (σ A_rad) ]^(1/4)
```
⚠️ **The `α/ε` ratio — solar absorptivity over infrared emissivity — is the primary
design knob**, and it's why thermal control is largely a coatings problem. White paint
(`α/ε ≈ 0.2`) runs cold; polished metal runs hot; **second-surface mirrors and OSRs**
give very low `α/ε` for radiators.

**Passive**: **MLI blankets** (⚠️ **10–30 layers of aluminized Mylar; effective emissivity
~0.01–0.03 — the single most effective thermal component on most spacecraft**), coatings,
thermal isolators, **heat pipes** (⚠️ **capillary two-phase transport, no moving parts,
very high effective conductivity**), thermal mass.

**Active**: electric heaters (⚠️ **often the largest steady power draw on an outer-planet
spacecraft**), louvres, pumped fluid loops, **cryocoolers** for IR detectors.

**⚠️ The extremes are what break designs**: **JWST** needs its instruments below ~40 K,
achieved with a tennis-court-sized sunshield giving ~300 K of gradient across five layers;
**Parker Solar Probe** survives ~1,400 °C on a carbon-composite shield while the bus stays
near room temperature; **lunar surface** swings ~120 °C to −170 °C, and ⚠️ **permanently
shadowed craters sit near 25–40 K**, which is colder than Pluto's surface and a genuine
materials problem.

---

## §5. Communications

### 5.1 The link budget

**[DURABLE] The equation that governs every deep space mission:**
```
P_r = P_t + G_t + G_r − L_fs − L_other
L_fs = 20 log₁₀(4πd/λ)          free-space path loss
G = η (πD/λ)²                    dish gain
```
**⚠️ Path loss scales as `d²`, so data rate falls as `1/d²`** for fixed everything else.
**Mars at opposition vs. conjunction varies by ~7× in distance — about 17 dB.**

**The `C/N₀` and achievable rate**:
```
C/N₀ = EIRP + G/T − L_fs − k       (k = −228.6 dBW/K/Hz)
R_max ≈ (C/N₀) / (E_b/N₀ required)
```
**⚠️ `G/T` — receive gain over system noise temperature — is the single figure of merit for
a ground station**, and it's why cryogenically-cooled LNAs matter.

### 5.2 What that means in practice

**Coding buys enormous margin.** ⚠️ **Turbo and LDPC codes operate within ~1 dB of the
Shannon limit**, versus the ~9 dB gap of uncoded BPSK — **an order of magnitude in
effective data rate for free, and the reason deep space missions return anything at all.**
Concatenated Reed–Solomon + convolutional was the older standard (Voyager).

**Bands**: **S** (2 GHz, robust, low rate), **X** (8 GHz, the workhorse), **Ka** (32 GHz,
⚠️ **~4× the gain of X for the same dish, but rain-attenuated and pointing-critical**),
**optical** (⚠️ **1550 nm; orders of magnitude more gain from the tiny wavelength, at the
cost of needing near-arcsecond pointing and cloud-free ground sites**).

**⚠️ The numbers that show the problem**: Voyager 1 at ~24 billion km returns **~160 bit/s**
on a 3.7 m dish with 23 W. New Horizons at Pluto returned **~1–2 kbit/s** and took
**16 months** to downlink the encounter data. **Data volume, not instrument capability, is
frequently the limiting factor for outer-planet science.**

### 5.3 Light-time and its consequences

```
Moon        1.3 s one-way       ⚠️ teleoperation marginal but possible
Mars        3–22 min            ⚠️ teleoperation impossible
Jupiter     33–53 min
Saturn      68–84 min
Voyager 1   ~23 hours
```
**⚠️ Round-trip light time to Mars exceeds 40 minutes at conjunction.** **This is the
single reason surface robots must be autonomous** (§6.2) and why EDL must be entirely
self-contained — the spacecraft has landed or crashed before Earth knows it entered.

### 5.4 Relay architecture
**⚠️ Mars surface missions overwhelmingly return data via orbiters** (MRO, MAVEN, TGO)
rather than direct-to-Earth: an orbiter passes overhead at ~400 km instead of 200 million,
and the `1/d²` advantage is astronomical. **Surface assets carry small UHF radios; the
orbiter carries the big X/Ka link.** **The Deep Space Network** (Goldstone, Madrid,
Canberra — 120° apart for continuous coverage) is the ground segment, ⚠️ **and it is
oversubscribed, which is a real and under-appreciated constraint on mission planning.**

---

## §6. Navigation and Autonomy

### 6.1 Deep space navigation

**[DURABLE] Three measurement types, and they're complementary:**
- **Doppler** — line-of-sight velocity from carrier frequency shift. ⚠️ **Precise to
  ~0.1 mm/s**, and the workhorse.
- **Ranging** — round-trip time of a modulated code. Metres at planetary distance.
- **⚠️ Delta-DOR** (Delta Differential One-way Ranging) — two stations observe the
  spacecraft and a quasar alternately; **differencing removes common errors and gives
  plane-of-sky position to nanoradians.** This is what makes precision arrival possible.

**Optical navigation** — imaging the target against background stars, essential for
approach and for small bodies where the ephemeris is poor.

**⚠️ Onboard**: star trackers (arcsecond attitude), sun sensors, IMUs (⚠️ **drift, always**),
and for landing, **terrain-relative navigation** — matching descent imagery against
orbital maps in real time. **Perseverance's TRN is what allowed landing in Jezero's
hazardous terrain**, which earlier missions would have had to avoid.

### 6.2 Autonomy

**[DURABLE] Autonomy is not a nicety at distance; it's forced by §5.3.**

**The levels in practice**: **sequenced execution** (a time-tagged command load — the
historical default), **event-driven sequencing**, **onboard planning** (⚠️ **the Remote
Agent experiment on Deep Space 1 in 1999 was the first onboard planner in control of a
spacecraft**), **autonomous science** (AEGIS on the Mars rovers selects and targets
spectroscopy without ground involvement), and **fully autonomous EDL** (§8 → `space-attitude-propulsion-and-edl`).

**⚠️ Fault protection is the hardest part, and it's what actually keeps spacecraft alive**:
- **Safe mode** — power-positive, thermally stable, Earth-pointed, awaiting instructions.
  ⚠️ **Every deep space mission enters safe mode. The design question is whether it can
  survive there indefinitely.**
- **Watchdogs and command loss timers** — ⚠️ **if no command is received for N days, assume
  a fault and reconfigure.** This has saved missions whose primary receivers failed.
- **Redundancy management** and autonomous swap to the B-side string.
- **⚠️ Fault protection that misfires is itself a hazard** — a spurious safe-mode entry
  during a critical event (an orbit insertion burn) can lose the mission.
