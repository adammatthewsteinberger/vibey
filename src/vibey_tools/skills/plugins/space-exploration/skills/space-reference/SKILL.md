---
name: space-reference
description: "Use when correcting a common spaceflight misconception, weighing a contested mission-architecture question, asking what is genuinely open, finding the books, or needing the numbers, a subsystem picker, and a design checklist. Companion to the other space-exploration skills."
---

# Space Exploration: Misconceptions, Contested Questions, and the Open Frontier

> **Part 5 of 5** of the *Space Exploration* reference (plugin `space-exploration`), covering §15–§20. Sibling skills: `space-mission-architecture-and-trajectory` (§0–§2), `space-power-thermal-comms-and-navigation` (§3–§6), `space-attitude-propulsion-and-edl` (§7–§8), `space-human-factors-life-support-and-reliability` (§9–§14). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The physics and subsystem engineering are stable; radiation dose limits and ISRU and life-support performance have real recent data. See §17 below for what is genuinely open.

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
>    beyond the Moon, forcing autonomy (§6 → `space-power-thermal-comms-and-navigation`); inverse-square makes both sunlight and
>    signal scarce (§3 → `space-power-thermal-comms-and-navigation`, §5 → `space-power-thermal-comms-and-navigation`).
> 3. **⚠️ For crewed deep space, the binding constraint is not propulsion — it's human
>    physiology.** Radiation dose and microgravity deconditioning bound mission duration
>    more tightly than Δv does (§9 → `space-human-factors-life-support-and-reliability`).

---

## §15. Misconceptions

| Claim | Reality |
|---|---|
| "Astronauts float because there's no gravity" | ⚠️ **~89% of surface gravity at ISS. They're in free fall** |
| "Space is cold, so things freeze fast" | ⚠️ **Vacuum has no conduction or convection. Overheating is usually the bigger problem** (§4 → `space-power-thermal-comms-and-navigation`) |
| "Just add shielding for radiation" | ⚠️ **Dense shielding can increase dose via secondaries** (§11 → `space-human-factors-life-support-and-reliability`) |
| "We've done a year on ISS, so Mars is fine" | ⚠️ **SANS is cumulative and dose-dependent; ISS is inside the magnetosphere** (§9 → `space-human-factors-life-support-and-reliability`) |
| "The hard part of Mars is getting there" | ⚠️ **EDL and physiology are harder than the Δv** (§8 → `space-attitude-propulsion-and-edl`, §9 → `space-human-factors-life-support-and-reliability`) |
| "Rovers are driven in real time" | ⚠️ **3–22 minutes one-way. They're autonomous** (§5.3 → `space-power-thermal-comms-and-navigation`, §6.2 → `space-power-thermal-comms-and-navigation`) |
| "Solar power works anywhere" | ⚠️ **0.07% of Earth's flux at Pluto** (§3 → `space-power-thermal-comms-and-navigation`) |
| "RTGs are nuclear reactors" | Passive decay heat plus thermocouples, ~6–7% efficient (§3 → `space-power-thermal-comms-and-navigation`) |
| "ISRU is speculative" | ⚠️ **MOXIE made 12 g/hr of ≥98% oxygen on Mars, 16 times** (§10.2 → `space-human-factors-life-support-and-reliability`) |
| "MOXIE proves Mars propellant is solved" | ⚠️ **30–70 kWh per kg of O₂. Tens of tonnes needed. That's a power plant** (§10.2 → `space-human-factors-life-support-and-reliability`) |
| "ISS recycles everything" | ⚠️ **~93% water; the oxygen loop is roughly half-closed** (§10.1 → `space-human-factors-life-support-and-reliability`) |
| "Aerocapture is routine" | ⚠️ **Never flown. Aerobraking has been; they're different** (§2 → `space-mission-architecture-and-trajectory`) |
| "Planetary protection is bureaucratic overhead" | It protects the science from self-contamination (§13 → `space-human-factors-life-support-and-reliability`) |
| "Bigger dish always means more data" | Also power, thermal, mass, and pointing (§5.1 → `space-power-thermal-comms-and-navigation`) |
| "Deep space missions are limited by instruments" | ⚠️ **Frequently limited by downlink volume instead** (§5.2 → `space-power-thermal-comms-and-navigation`) |

---

## §16. Contested

**16.1 Crewed versus robotic.** *Robotic*: vastly cheaper, no life support, no return
requirement, tolerates decades and lethal environments. ⚠️ **Perseverance costs a fraction
of a crewed mission and has operated for years.** *Crewed*: a human geologist's
field judgement per sol dwarfs a rover's — **Apollo 17's Schmitt did more field geology in
three days than rovers have in decades** — plus dexterity, repair, and the political and
inspirational case. **[CONTESTED, and the honest framing is that it's a values question
about what exploration is for, not a purely technical comparison.]**

**16.2 Moon first, or direct to Mars?** *Moon*: proving ground, three days from home,
ISRU practice, ⚠️ **and abort options that Mars simply doesn't have.** *Mars direct*:
the Moon is a different environment (no atmosphere, different regolith, different dust)
and lunar infrastructure may not transfer. **⚠️ The strongest argument for the Moon is not
technical transfer — it's that you can fail and recover.**

**16.3 Are planetary protection requirements proportionate?** §13 → `space-human-factors-life-support-and-reliability`.

**16.4 Sample return versus in-situ analysis.** *Return*: terrestrial labs are
unboundedly better and can be revisited as techniques improve — ⚠️ **Apollo samples are
still yielding results 50+ years on.** *In situ*: far cheaper, no backward-contamination
problem, and instruments have improved enormously. **Mars Sample Return's cost growth has
made this a live argument rather than an academic one.**

**16.5 Nuclear propulsion.** §3 → `space-power-thermal-comms-and-navigation` and a rocket-science reference §16.2. ⚠️ **The physics
works; programme durability across a decade never has.**

**16.6 How autonomous should spacecraft be?** More autonomy means more capability at
distance and less ground cost, ⚠️ **and a harder verification problem plus fault-protection
that can itself cause failures** (§6.2 → `space-power-thermal-comms-and-navigation`). **Learned components make this sharper** — see a
robotics-software reference §8.3.

---

## §17. What's Actually Open

**[DURABLE] The physics is settled; these are unsolved engineering and unknown biology.**

- **⚠️ Human deep-space radiation risk.** §9.1 → `space-human-factors-life-support-and-reliability`. **Not just shielding — the biology.**
  HZE-ion effects on the CNS and on cancer risk are extrapolated from poor analogues, and
  ⚠️ **the uncertainty in the risk model is itself a major part of why limits are set where
  they are.**
- **⚠️ SANS aetiology.** §9.2 → `space-human-factors-life-support-and-reliability`. **Unknown mechanism, no countermeasure, dose-dependent, and
  it gates multi-year missions.** Arguably the single most important open question for
  crewed Mars.
- **Long-duration closed-loop life support.** §10.1 → `space-human-factors-life-support-and-reliability`. ⚠️ **Nothing has run closed at high
  ratio for Mars-mission durations without resupply.** Reliability over 1,000 days is the
  unproven part, not the chemistry.
- **⚠️ ISRU at scale.** §10.2 → `space-human-factors-life-support-and-reliability`. Energy cost, dust tolerance, autonomous operation for years
  before crew arrive, and **cryogenic storage of the product over a synodic period**.
- **Mars EDL beyond ~1 tonne.** §8 → `space-attitude-propulsion-and-edl`. **Supersonic retropropulsion, inflatable decelerators,
  or something else. Unproven at Mars.**
- **Zero-g cryogenic propellant transfer and long-duration storage.** ⚠️ **Understood
  physics, undemonstrated at scale**, and load-bearing for multiple architectures.
- **Dust mitigation.** ⚠️ **Lunar dust is abrasive, electrostatically clingy, and defeated
  Apollo-era seals in days.** Not solved.
- **Partial-gravity physiology.** ⚠️ **We have data at 1 g and at ~0 g. We have essentially
  none at 0.16 g or 0.38 g**, and no way to get it without building a centrifuge or going.
- **Planetary protection for crewed missions.** §13 → `space-human-factors-life-support-and-reliability`. Unresolved in policy and in practice.
- **Autonomous fault management** that is both capable and verifiable (§6.2 → `space-power-thermal-comms-and-navigation`).

---

## §18. Books

| Author | Work | Why |
|---|---|---|
| **Wertz & Larson** | ***Space Mission Analysis and Design*** (SMAD) | ⚠️ **The bible. If you own one book on this, it's this** |
| **Wertz, Everett & Puschell** | *Space Mission Engineering: The New SMAD* | The updated successor |
| **Fortescue, Swinerd & Stark** | *Spacecraft Systems Engineering* | Excellent, and more readable than SMAD |
| **Brown** | *Elements of Spacecraft Design* | Subsystem sizing with worked numbers |
| **Gilmore (ed.)** | *Spacecraft Thermal Control Handbook* | §4 → `space-power-thermal-comms-and-navigation` definitively |
| **Vallado** | *Fundamentals of Astrodynamics and Applications* | §2 → `space-mission-architecture-and-trajectory`'s mathematics |
| **Wiesel** | *Spaceflight Dynamics* | Approachable astrodynamics |
| **Eckart** | *Spaceflight Life Support and Biospherics* | §10 → `space-human-factors-life-support-and-reliability` |
| **Larson & Pranke** | *Human Spaceflight: Mission Analysis and Design* | The crewed counterpart to SMAD |
| **Braeunig / Curtis** | *Orbital Mechanics for Engineering Students* | Cross-reference for §2 → `space-mission-architecture-and-trajectory` |
| **NASA SP-2016-6105** | *NASA Systems Engineering Handbook* | ⚠️ **Free, and the actual process document** |
| **Squyres** | *Roving Mars* | ⚠️ **The best account of what building and operating a planetary mission is actually like** |
| **Mindell** | *Digital Apollo* | Human-machine autonomy, historically grounded |

**Primary sources**: **NASA NTRS** (⚠️ **the technical reports server — decades of design
documents, free**), **NASA Human Research Roadmap** (§9 → `space-human-factors-life-support-and-reliability`'s risk register, explicitly
maintained), **COSPAR planetary protection policy**, **JPL Horizons** for ephemerides,
**the Planetary Society** for programme context, **NASA/ESA mission pages** for instrument
specifications.

---

## §19. Quick Reference

### 19.1 Numbers
```
Solar constant 1,361 W/m² at 1 AU; ∝ 1/r²
Mars 590 W/m² · Jupiter 50 · Saturn 15 · Pluto 0.9

Light time: Moon 1.3 s · Mars 3–22 min · Jupiter 33–53 min · Saturn 68–84 min
Mars synodic period 25.6 months           ⚠️ the scheduling quantum

Solar arrays ~50–150 W/kg · RTG ~2–5 W/kg, ~6–7% efficient, ~1.6%/yr decay
MMRTG ≈ 110 W_e from ~2,000 W_th
Batteries 100–250 Wh/kg

Consumables ~5 kg/person/day open loop
ISS water recovery up to ~93%; Sabatier closes ~50% of the O₂ loop
MOXIE: 12 g O₂/hr peak, ≥98% purity, 15 kg, ~300 W, 800 °C, 16 runs
ISRU energy: Mars SOXE 30–70 kWh/kg O₂ · lunar MRE 3–5 kW/kg · H₂ reduction 2–3 kW/kg

NASA career radiation limit 600 mSv · ESA/Roscosmos 1 Sv
⚠️ Mars mission estimate ~1,000 mSv — exceeds NASA's limit
Bone loss ~1–1.5%/month · SANS in ~70% of >6-month crews

Mars atmosphere ~1% of Earth's, ~95% CO₂
Mars landed mass ceiling historically ~1 tonne
Parachute deploy Mach 1.5–2.2
Lunar night 14 Earth days
```

### 19.2 Picker
| Need | Approach |
|---|---|
| Power inside ~Jupiter | Solar (§3 → `space-power-thermal-comms-and-navigation`) |
| Power beyond Jupiter, or through lunar night | RTG or fission (§3 → `space-power-thermal-comms-and-navigation`) |
| Reject heat | Radiator area, and tune `α/ε` (§4 → `space-power-thermal-comms-and-navigation`) |
| High data volume from a surface | ⚠️ **Relay orbiter, not direct-to-Earth** (§5.4 → `space-power-thermal-comms-and-navigation`) |
| Data rate at extreme range | Ka-band or optical + LDPC coding (§5.2 → `space-power-thermal-comms-and-navigation`) |
| Precise interplanetary navigation | Doppler + ranging + **Delta-DOR** (§6.1 → `space-power-thermal-comms-and-navigation`) |
| Landing in hazardous terrain | **Terrain-relative navigation** (§6.1 → `space-power-thermal-comms-and-navigation`) |
| Large Δv, plenty of time | Electric propulsion (§7 → `space-attitude-propulsion-and-edl`) |
| Orbit insertion, fast | Bipropellant (§7 → `space-attitude-propulsion-and-edl`) |
| ~1 tonne to the Martian surface | Sky crane (§8 → `space-attitude-propulsion-and-edl`) |
| Return propellant from Mars | ⚠️ **ISRU — and size the power plant first** (§10.2 → `space-human-factors-life-support-and-reliability`) |
| GCR shielding | ⚠️ **Hydrogen-rich mass, not aluminium** (§11 → `space-human-factors-life-support-and-reliability`) |
| Landing near a special region | ⚠️ **Category IV sterilization** (§13 → `space-human-factors-life-support-and-reliability`) |

### 19.3 Design checklist
- [ ] Mass, power, data, Δv margins per §14.1 → `space-human-factors-life-support-and-reliability` — and are they still intact?
- [ ] Link budget closed at maximum range, worst geometry (§5.1 → `space-power-thermal-comms-and-navigation`)
- [ ] Data volume, not just data rate, closes against the science plan (§5.2 → `space-power-thermal-comms-and-navigation`)
- [ ] Thermal closes at both hot and cold extremes, BOL and EOL (§4 → `space-power-thermal-comms-and-navigation`)
- [ ] Power closes at EOL, worst eclipse, worst dust (§3 → `space-power-thermal-comms-and-navigation`)
- [ ] Every deployment identified as a single-point failure (§14.2 → `space-human-factors-life-support-and-reliability`)
- [ ] Safe mode is survivable indefinitely and Earth-pointed (§6.2 → `space-power-thermal-comms-and-navigation`)
- [ ] Fault protection cannot fire during a critical event (§6.2 → `space-power-thermal-comms-and-navigation`)
- [ ] Autonomy sufficient for the light-time (§5.3 → `space-power-thermal-comms-and-navigation`)
- [ ] Radiation total-dose budget closes for the environment (§11 → `space-human-factors-life-support-and-reliability`)
- [ ] Planetary protection category identified and costed (§13 → `space-human-factors-life-support-and-reliability`)
- [ ] Units checked at every interface ⚠️ (§14.2 → `space-human-factors-life-support-and-reliability`)

---

## §20. Method

**This is engineering, not reporting.** §1–§8 → `space-mission-architecture-and-trajectory`, `space-power-thermal-comms-and-navigation`, `space-attitude-propulsion-and-edl`, §11–§14 → `space-human-factors-life-support-and-reliability` rest on the standard systems
literature — **SMAD, Fortescue, Brown, the Gilmore thermal handbook, and the NASA Systems
Engineering Handbook** — plus physics established elsewhere; none of it has a currency
dependency and none of it was web-verified. **Deliberately scoped to complement rather than
duplicate**: launch, staging, orbital mechanics and reentry heating are in a rocket-science
reference; flight software practice is in a robotics-software reference.

**Two searches were run in August 2026**, confined to the two areas where hard numbers have
landed and where the constraint is genuinely binding: **human radiation limits and SANS**
(§9 → `space-human-factors-life-support-and-reliability`), and **ISRU and life-support performance** (§10 → `space-human-factors-life-support-and-reliability`).

**Primary and near-primary sources for those sections**: **NASA's own MOXIE mission-completion
reporting** and the **Science Advances** MOXIE paper (Hoffman, Hecht et al.) for the
12 g/hr, ≥98% purity, 16-run figures and the instrument parameters; the **PDS MOXIE
instrument page** for the warm-up/production duty cycle and the ~650 W·h allocation; a
2026 **ScienceDirect ECLSS review** for the comparative ISRU energy costs; **NASA's ECLSS
page** and a 2026 **Water Resources Research** review for the ~93% water recovery figure;
**NASA's Human Research Roadmap** and peer-reviewed SANS literature (Lee et al. and
successors) for §9.2 → `space-human-factors-life-support-and-reliability`; and multiple peer-reviewed sources plus the **NASA 2022 standard**
for the 600 mSv career limit and the ~1,000 mSv Mars estimate.

**Confidence.** **High** in §1–§8 → `space-mission-architecture-and-trajectory`, `space-power-thermal-comms-and-navigation`, `space-attitude-propulsion-and-edl` and §11–§14 → `space-human-factors-life-support-and-reliability` — settled subsystem engineering with
numbers that are representative sizing values rather than specifications; treat the ranges
as design guidance. **High** in §10.2 → `space-human-factors-life-support-and-reliability`'s MOXIE figures, which come from NASA and the
instrument team directly. **High** in §9.1 → `space-human-factors-life-support-and-reliability`'s dose limit and the statement that a Mars
mission exceeds it — ⚠️ **this is consistently reported across independent peer-reviewed
sources, and the ~1,000 mSv estimate is an estimate with real uncertainty, resting on
Curiosity RAD measurements extrapolated to a mission profile that hasn't been flown.**

⚠️ **Moderate confidence on the SANS incidence figure (~70% of >6-month crews)**: it comes
from clinical review literature rather than a single definitive study, **the astronaut
sample is small enough that percentages should be treated as indicative**, and the
underlying aetiology being unknown means the risk model itself may shift. **§16 is
engineering and values judgement, not physics** — particularly §16.1, where the crewed
versus robotic question is not settled by any technical argument and I have not pretended
otherwise. **§17's list is my assessment** of where the open problems sit; specialists in
life support or EDL would weight them differently.
