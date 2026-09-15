---
name: space-attitude-propulsion-and-edl
description: "Use when working on pointing, orbit maintenance, or getting to a surface: attitude determination and control (sensors, reaction wheels, momentum management, thrusters) and in-space propulsion including electric propulsion trade-offs, and entry, descent and landing — the entry corridor, aeroshells and heating, parachutes and terminal descent, and surface operations."
---

# Space Exploration: Attitude Control, In-Space Propulsion, and Entry, Descent and Landing

> **Part 3 of 5** of the *Space Exploration* reference (plugin `space-exploration`), covering §7–§8. Sibling skills: `space-mission-architecture-and-trajectory` (§0–§2), `space-power-thermal-comms-and-navigation` (§3–§6), `space-human-factors-life-support-and-reliability` (§9–§14), `space-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    beyond the Moon, forcing autonomy (§6 → `space-power-thermal-comms-and-navigation`); inverse-square makes both sunlight and
>    signal scarce (§3 → `space-power-thermal-comms-and-navigation`, §5 → `space-power-thermal-comms-and-navigation`).
> 3. **⚠️ For crewed deep space, the binding constraint is not propulsion — it's human
>    physiology.** Radiation dose and microgravity deconditioning bound mission duration
>    more tightly than Δv does (§9 → `space-human-factors-life-support-and-reliability`).

---

## §7. Attitude Control and In-Space Propulsion

**Attitude sensing**: star trackers (best, arcsecond-class), sun sensors, horizon sensors,
magnetometers (LEO only), gyros.

**Actuation**: **reaction wheels** (⚠️ **precise, but they saturate and must be
desaturated — and wheel failure has crippled missions; Kepler and Hayabusa both lost
wheels**), **control moment gyros** (higher torque, used on ISS), **thrusters** (fast,
consume propellant), **magnetorquers** (LEO only), **spin stabilization** (⚠️ **simple and
robust, at the cost of pointing flexibility**), **gravity-gradient**, and
⚠️ **solar radiation pressure**, which Kepler used as a virtual third wheel after two
failed — a genuinely elegant recovery.

**In-space propulsion:**

| Type | Isp (s) | Use |
|---|---|---|
| **Cold gas** | 50–70 | Simple, small ΔV, contamination-free |
| **Monopropellant (hydrazine)** | 220–235 | ⚠️ **The RCS workhorse** |
| **Bipropellant (MMH/NTO)** | 300–330 | Orbit insertion, hypergolic and storable |
| **Solid** | 280–300 | Single-burn kick stages |
| **Hall thruster** | 1,500–2,500 | ⚠️ **Station-keeping and orbit raising, now standard** |
| **Gridded ion** | 3,000–4,000 | ⚠️ **Dawn visited two main-belt bodies — impossible chemically** |
| **Solar sail** | ∞ | No propellant; tiny thrust |

**⚠️ The electric propulsion trade, stated properly**: 10× the Isp means ~1/10 the
propellant for the same Δv, **but thrust is millinewtons, so burns last months and the
power system must be sized to feed it** — the mass moves from the propellant tank to the
solar arrays. **It wins when the mission has time and the Δv is large.**

**Station-keeping**: **GEO needs ~50 m/s/yr** (north-south dominates, against lunisolar
perturbations); **LEO drag makeup**; **halo orbits need small but continual maintenance**
because they're unstable.

---

## §8. EDL and Surface Operations

**[DURABLE] Entry heating physics is in a rocket-science reference §12. What matters here
is the sequence and why it's hard.**

**⚠️ Mars EDL is the canonical hard case, and the reason is a genuine physical squeeze:**
the atmosphere is **~1% of Earth's** — thick enough to demand a heat shield, **too thin to
slow you to safe landing speed with parachutes alone.** Venus and Titan are easier
(dense atmospheres); the Moon and asteroids are easier (no atmosphere, pure propulsive).

**The Mars sequence, roughly seven minutes:**
```
Entry interface (~125 km, ~5.5–7.5 km/s)
  → peak heating (~100 s), peak deceleration (~8–15 g)
    → supersonic parachute deploy (Mach 1.5–2.2, ~10 km)   ⚠️ narrow box
      → heat shield jettison → radar/TRN acquisition
        → backshell separation → powered descent
          → touchdown: legs, airbags, or sky crane
```
**⚠️ Everything is autonomous** (§5.3 → `space-power-thermal-comms-and-navigation`) — the vehicle has landed or crashed before the
first telemetry arrives.

**Landing methods and their regimes**: **airbags** (Pathfinder, MER — ⚠️ **mass-efficient
but caps landed mass around a few hundred kg and requires benign terrain**), **legs**
(Viking, Phoenix, InSight — ⚠️ **engine plume excavates regolith and can contaminate
samples**), **sky crane** (MSL, Perseverance — ⚠️ **bizarre-looking and the correct answer
for ~1-tonne rovers: it keeps the engines away from the surface and puts the wheels down
directly**).

**⚠️ The landed-mass ceiling**: Mars EDL has historically capped landed mass near
**~1 tonne**, because parachute area scales badly and supersonic retropropulsion was
unproven. **Scaling past it requires either much larger decelerators or supersonic
retropropulsion**, which is the central open EDL problem (§17 → `space-reference`).

**Surface operations**: **mobility** (rocker-bogie suspension — ⚠️ **passively keeps six
wheels loaded on rough terrain, no active control**), ⚠️ **wheel wear**, which was a real
mission-shaping problem for Curiosity, **dust** (⚠️ **abrasive, electrostatic, and
mission-ending for solar-powered landers**), **thermal cycling**, **sample acquisition**
(drilling in vacuum or low gravity is genuinely hard — ⚠️ **InSight's mole failed because
Martian regolith didn't provide expected friction**), and **traverse planning** under
light-time (§6.2 → `space-power-thermal-comms-and-navigation`).
