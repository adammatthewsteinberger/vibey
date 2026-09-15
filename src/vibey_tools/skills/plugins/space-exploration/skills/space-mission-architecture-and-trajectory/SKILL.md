---
name: space-mission-architecture-and-trajectory
description: "Use when shaping a mission at the top level: the design cascade from science requirements down to subsystems, the architecture trades, why everything reduces to mass, and trajectory and mission design including launch windows, transfer options, delta-v budgets and gravity assists. Includes the router for the whole space-exploration reference."
---

# Space Exploration: Mission Architecture and Trajectory Design

> **Part 1 of 5** of the *Space Exploration* reference (plugin `space-exploration`), covering §0–§2. Sibling skills: `space-power-thermal-comms-and-navigation` (§3–§6), `space-attitude-propulsion-and-edl` (§7–§8), `space-human-factors-life-support-and-reliability` (§9–§14), `space-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    **You are always spending the same budget** (§1.3).
> 2. **Distance imposes latency and darkness.** Light-time makes teleoperation impossible
>    beyond the Moon, forcing autonomy (§6 → `space-power-thermal-comms-and-navigation`); inverse-square makes both sunlight and
>    signal scarce (§3 → `space-power-thermal-comms-and-navigation`, §5 → `space-power-thermal-comms-and-navigation`).
> 3. **⚠️ For crewed deep space, the binding constraint is not propulsion — it's human
>    physiology.** Radiation dose and microgravity deconditioning bound mission duration
>    more tightly than Δv does (§9 → `space-human-factors-life-support-and-reliability`).

---

## §0. Routing

| You want... | Go to |
|---|---|
| **Mission architecture and trade space** | **§1** |
| Trajectory design and mission types | §2 |
| Power systems | §3 → `space-power-thermal-comms-and-navigation` |
| Thermal control | §4 → `space-power-thermal-comms-and-navigation` |
| **Communications and link budgets** | **§5 → `space-power-thermal-comms-and-navigation`** |
| Navigation, autonomy, and timing | §6 → `space-power-thermal-comms-and-navigation` |
| Attitude control and propulsion | §7 → `space-attitude-propulsion-and-edl` |
| EDL and surface operations | §8 → `space-attitude-propulsion-and-edl` |
| **Human physiology — the hard limits** | **§9 → `space-human-factors-life-support-and-reliability`** |
| **Life support and ISRU** | **§10 → `space-human-factors-life-support-and-reliability`** |
| Radiation environments and shielding | §11 → `space-human-factors-life-support-and-reliability` |
| Scientific instrumentation | §12 → `space-human-factors-life-support-and-reliability` |
| Planetary protection and contamination | §13 → `space-human-factors-life-support-and-reliability` |
| Reliability, margins, failure modes | §14 → `space-human-factors-life-support-and-reliability` |
| Misconceptions | §15 → `space-reference` |
| Contested | §16 → `space-reference` |
| What's actually open | §17 → `space-reference` |
| Books | §18 → `space-reference` |
| Quick reference | §19 → `space-reference` |

---

## §1. Mission Architecture

### 1.1 The design cascade

**[DURABLE] Requirements flow downward and mass flows upward, and the loop closes only by
iteration:**
```
Science/mission objectives
  → measurement requirements → instrument selection
    → pointing, power, data volume, thermal requirements
      → bus sizing → power system → thermal system
        → mass and volume → launch vehicle and trajectory
          → ⚠️ which constrains everything above. Iterate.
```
**⚠️ The characteristic mistake is treating this as a waterfall.** It converges only if
you carry margins (§14.1 → `space-human-factors-life-support-and-reliability`) and re-run the loop when any element grows.

### 1.2 The architecture trades

| Trade | Poles |
|---|---|
| **Flyby / orbiter / lander / rover / sample return** | Cost and risk rise steeply; ⚠️ **so does science return per target** |
| **Single large vs. distributed small** | One capable spacecraft vs. constellations; ⚠️ **the latter buys simultaneity and graceful degradation** |
| **Solar vs. radioisotope** | §3 → `space-power-thermal-comms-and-navigation` — ⚠️ **decided largely by heliocentric distance and duty cycle** |
| **Chemical vs. electric propulsion** | §7 → `space-attitude-propulsion-and-edl` — time versus propellant mass |
| **Direct vs. gravity assist** | Δv versus flight time and window rigidity |
| **Crewed vs. robotic** | §16.1 → `space-reference` |
| **Store-and-forward vs. direct-to-Earth** | Relay orbiters transform surface data return (§5.4 → `space-power-thermal-comms-and-navigation`) |

### 1.3 ⚠️ Everything is mass

**[DURABLE] The conversion factors that make this concrete:**
- **Power**: solar arrays run **~50–150 W/kg** at 1 AU (BOL, including structure);
  **RTGs ~2–5 W/kg**. Batteries **~100–250 Wh/kg**.
- **Data rate**: gain scales as `D²`, so doubling downlink means a bigger dish or more
  transmit power — **and transmit power means more array and more radiator** (§5 → `space-power-thermal-comms-and-navigation`).
- **Redundancy**: full block redundancy roughly **doubles** the subsystem mass.
- **Consumables**: **~5 kg/person/day** of food, water and oxygen open-loop —
  ⚠️ **which is why closure ratio dominates crewed mission mass** (§10.2 → `space-human-factors-life-support-and-reliability`).

**⚠️ And propellant mass is exponential in Δv** (see a rocket-science reference §1), so a
kilogram added to a Mars lander costs several kilograms in Earth departure stage.

---

## §2. Trajectory and Mission Design

**[DURABLE] Orbital mechanics proper is in a rocket-science reference §7. What matters
here is the mission-level consequence.**

**Launch windows** are set by planetary geometry. **Mars synodic period ≈ 25.6 months** —
⚠️ **miss the window and you wait over two years**, which is the single hardest scheduling
constraint in planetary exploration and the reason Mars programmes slip in two-year
quanta.

**Porkchop plots** — contours of C₃ (launch energy) and arrival `v_∞` over departure and
arrival dates. ⚠️ **The working tool of mission design**: they show simultaneously what the
launch vehicle must deliver and what the arrival must absorb.

**Gravity assists** buy Δv at the cost of rigidity and flight time. **Cassini's
VVEJGA** (Venus-Venus-Earth-Jupiter) took ~7 years to Saturn; **direct would have needed a
launch vehicle that didn't exist.** ⚠️ **Assists don't just save propellant — they enable
missions outright**, and they make the launch window nearly immovable.

**Low-energy transfers** via weak-stability boundaries cost less Δv and much more time.

**Orbit selection at the target**: **circular vs. elliptical** (⚠️ **elliptical is far
cheaper to enter and gives varied altitude coverage; circular gives uniform resolution**),
**polar vs. equatorial** (coverage vs. Δv), **frozen orbits** for stability,
**sun-synchronous** for consistent lighting, and **halo orbits at L1/L2** (⚠️ **thermally
stable, continuous sky access, and the reason JWST is at Sun-Earth L2** — with the cost
that it's unreachable for servicing).

**⚠️ Aerocapture** — using a single atmospheric pass to enter orbit — offers enormous Δv
savings and **has never been flown.** Aerobraking (many shallow passes over months) has
been, repeatedly, at Mars and Venus. **The difference is that aerobraking is
incrementally correctable and aerocapture is one shot.**
