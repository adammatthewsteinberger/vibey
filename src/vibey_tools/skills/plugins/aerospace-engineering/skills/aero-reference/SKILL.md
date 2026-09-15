---
name: aero-reference
description: "Use when correcting an aerodynamics or flight misconception, checking what moved in BVLOS drone regulation and eVTOL certification (verified August 2026), looking up a speed, load factor, coefficient or performance number, finding the canon, or needing a picker and a design review checklist. Companion to the other aerospace-engineering skills."
---

# Aerospace Engineering: Misconceptions, What Moved, Numbers, and Canon

> **Part 5 of 5** of the *Aerospace Engineering* reference (plugin `aerospace-engineering`), covering §15–§20. Sibling skills: `aero-aerodynamics-airfoils-and-compressible-flow` (§0–§4), `aero-performance-stability-and-propulsion` (§5–§7), `aero-structures-aeroelasticity-and-avionics` (§8–§10), `aero-drones-launch-vehicles-flight-test-and-design` (§11–§14). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Aerodynamics, structures and flight mechanics are settled — Lanchester-Prandtl circulation theory, the Breguet range equation, von Karman. Two regulatory areas moved. See §16 below for BVLOS drone rules and eVTOL certification.

> **Scope.** Complements a rocket-science reference (propulsion physics, orbital
> mechanics, reentry), a flight-software reference (avionics and DO-178C), and a
> space-exploration reference. ⚠️ **This is vehicle engineering: how air vehicles and
> launchers are actually designed.**
>
> **⚠️ GOTCHA** boxes mark misconceptions and killers — and aerospace has both in
> quantity.
>
> **The three ideas that organize the field:**
> 1. **⚠️ Lift comes from turning the flow, and the popular explanation is wrong.**
>    Newton's third law and circulation both describe it correctly; "equal transit time"
>    does not, and it's what most people were taught (§1.2 → `aero-aerodynamics-airfoils-and-compressible-flow`).
> 2. **⚠️ Aircraft design is a convergence loop, not a sequence.** Weight drives lift
>    drives wing area drives weight. **You iterate to a fixed point, and everything is
>    coupled to everything** (§14 → `aero-drones-launch-vehicles-flight-test-and-design`).
> 3. **⚠️ Margins in aerospace are small and the consequences are absolute.** Structural
>    factor of safety is typically **1.5**, against 3–5 in civil engineering. **Every
>    kilogram is fought for, which is why aerospace failures are rarely about ignorance
>    and usually about a margin that was correct on paper** (§8 → `aero-structures-aeroelasticity-and-avionics`, §13 → `aero-drones-launch-vehicles-flight-test-and-design`).

---

## §15. Misconceptions

| Misconception | Correction |
|---|---|
| Lift comes from equal transit time over a longer upper surface | ⚠️ **False. Parcels don't meet; symmetric airfoils and inverted flight disprove it** (§1.2 → `aero-aerodynamics-airfoils-and-compressible-flow`) |
| Bernoulli explains lift | ⚠️ **Bernoulli relates pressure to velocity correctly; it doesn't explain WHY velocities differ** (§1.2 → `aero-aerodynamics-airfoils-and-compressible-flow`) |
| Newton and circulation are competing theories | ⚠️ **Same physics, different bookkeeping** (§1.2 → `aero-aerodynamics-airfoils-and-compressible-flow`) |
| Stall happens at a specific airspeed | ⚠️ **Stall is angle of attack. `V_stall ∝ √n`** (§2 → `aero-aerodynamics-airfoils-and-compressible-flow`) |
| Slower flight always means less drag | ⚠️ **Below best-glide speed, induced drag rises** (§3 → `aero-aerodynamics-airfoils-and-compressible-flow`) |
| A 60° bank is a mild manoeuvre | ⚠️ **2g, and stall speed up 41%** (§5 → `aero-performance-stability-and-propulsion`) |
| Doubling fuel doubles range | ⚠️ **Breguet is logarithmic in weight fraction** (§5 → `aero-performance-stability-and-propulsion`) |
| Static stability is always desirable | ⚠️ **Relaxed stability buys performance — with a flight computer** (§6 → `aero-performance-stability-and-propulsion`) |
| Sweep is for looks or speed directly | ⚠️ **It reduces the normal velocity component, raising critical Mach** (§4 → `aero-aerodynamics-airfoils-and-compressible-flow`) |
| Jets are always more efficient than props | ⚠️ **Propulsive efficiency favours props below ~M 0.6** (§7 → `aero-performance-stability-and-propulsion`) |
| High bypass is about noise | ⚠️ **It's propulsive efficiency; noise is a bonus** (§7 → `aero-performance-stability-and-propulsion`) |
| Aircraft structures are designed for static strength | ⚠️ **Fatigue dominates in transports — see Comet** (§8 → `aero-structures-aeroelasticity-and-avionics`) |
| Composites are simply better | ⚠️ **Barely-visible impact damage makes inspection harder** (§8 → `aero-structures-aeroelasticity-and-avionics`) |
| Flutter gives warning | ⚠️ **Sharp boundary, exponential growth, seconds** (§9 → `aero-structures-aeroelasticity-and-avionics`) |
| Adding mass to a control surface is harmless | ⚠️ **Mass balance is a flutter parameter** (§9 → `aero-structures-aeroelasticity-and-avionics`) |
| Fly-by-wire is mainly a weight saving | ⚠️ **It enables envelope protection and relaxed stability** (§10 → `aero-structures-aeroelasticity-and-avionics`) |
| A quadrotor yaws by tilting | ⚠️ **Differential torque — which is why yaw is the weak axis** (§11.1 → `aero-drones-launch-vehicles-flight-test-and-design`) |
| Multirotor designs scale up well | ⚠️ **Thrust scales with area, mass with volume** (§11.1 → `aero-drones-launch-vehicles-flight-test-and-design`) |
| Drone endurance is a battery-brand problem | ⚠️ **Specific energy is ~50× below kerosene. It's physics** (§11.1 → `aero-drones-launch-vehicles-flight-test-and-design`) |
| Add power to escape vortex ring state | ⚠️ **Move laterally. Power makes it worse** (§11.2 → `aero-drones-launch-vehicles-flight-test-and-design`) |
| A type certificate means you can fly passengers | ⚠️ **Air carrier certificate is separate** (§13 → `aero-drones-launch-vehicles-flight-test-and-design`, §16.2) |
| Erratic GPS drift on a drone is a GPS problem | ⚠️ **Usually magnetometer interference** (§11.1 → `aero-drones-launch-vehicles-flight-test-and-design`) |

---

## §16. What Moved — verified August 2026

### 16.1 ⚠️ BVLOS drone regulation — FAA Part 108
**The regulatory change that would unlock routine commercial drone operations at scale.**

**The record**: **Executive Order 14307 (June 6, 2025)** directed the FAA to publish a
BVLOS NPRM within 30 days and finalize within 240. **The NPRM was published August 7,
2025** (90 FR 38212, Docket FAA-2025-1908). ⚠️ **The comment period drew roughly
3,000–3,100 responses, with more than half addressing the proposed right-of-way rules.**
**The FAA reopened comments in January 2026 on right-of-way and electronic conspicuity —
the most contested provisions — and a further extension request was denied.**

**What Part 108 would change:**
- ⚠️ **Replaces the case-by-case Part 107 waiver system with a standing, performance-based
  rule** — **waivers have reportedly cost some operators up to $125,000.**
- **Covers operations up to 1,320 pounds**; ⚠️ **Part 107 remains for VLOS. Part 108 is a
  separate regulation, not a replacement.**
- ⚠️ **Shifts responsibility from the individual remote pilot to the ORGANIZATION** — the
  operator is the accountable entity. **The FAA's own preamble acknowledges that with
  increasing autonomy the role of the pilot has decreased and will continue to.**
- **⚠️ Airworthiness acceptance rather than FAA type certification** — manufacturers
  demonstrate airworthiness against consensus standards.
- **Remote ID (Part 89) required**; **a framework for third-party services including UTM
  (proposed Part 146)**; **detect-and-avoid expectations.**

> **⚠️ GOTCHA — sources conflict on whether this rule is final, and several state
> confidently that it is.** ⚠️ **The best-dated sources I found, checking the public
> rulemaking record in July 2026, say the rule remained at NPRM stage with no final rule
> issued, and that operators must continue using existing waiver paths.** **Other sources —
> including some written earlier in 2026 — assert it "will become law in 2026" or predict
> finalization in spring 2026.** ⚠️ **The deadline slipped: the original executive-order
> date of February 1, 2026 was extended by a 43-day government shutdown to roughly March
> 16, 2026, and passed.**
>
> ⚠️ **Verify current status directly against the Federal Register or faa.gov before
> relying on this.** **The direction is not in doubt; the effective date is.**

**⚠️ A contested provision worth knowing about**: **airworthiness acceptance eligibility as
drafted is tied to US production or countries with specific bilateral UAS agreements** —
and ⚠️ **DJI has publicly noted the US currently has no such agreements, which would
exclude foreign manufacturers entirely.** **That is an industrial-policy question wearing
a technical-standard costume.**

### 16.2 eVTOL certification
**⚠️ The regulatory framework is now complete; the aircraft are not certified.**

**Where things stand:**
- **⚠️ The framework exists**: **the powered-lift SFAR (late 2024)**, an **advisory circular
  (July 2025)**, and **Part 194 as the dedicated operating rule** — ⚠️ **which one source
  describes as removing the last regulatory blocker to US revenue eVTOL flights once an
  airframe is type-certificated.**
- **Joby** — ⚠️ **completed Stage 4 of the FAA's five-stage process, confirmed late March
  2026; first FAA-conforming aircraft flew March 11, 2026 and entered TIA flight testing.**
  **Reported as ~85% through certification.**
- **Archer** — ⚠️ **100% of its 797 means of compliance accepted; closed Phase 3 (of four)
  in April/May 2026.** **Final airworthiness criteria issued under Special Class
  21.17(b).**
- **⚠️ Globally, only three eVTOL type certificates have been issued, all in China**:
  **EHang's EH216-S (CAAC, October 2023, followed by production certificate and AOC)** and
  **AutoFlight's Prosperity I (2024).** ⚠️ **EASA has issued none.**
- **The FAA selected 8 eIPP demonstration projects in March 2026**, covering **26 states**,
  with pre-certification demonstration flights from summer 2026 — ⚠️ **and Joby flew
  point-to-point eIPP flights in New York in April 2026.**

> **⚠️ GOTCHA — the timeline claims here diverge sharply, and one source is explicitly
> written to rebut the others.** ⚠️ **Optimistic sources describe air taxi service
> beginning summer 2026 and type certification by year-end 2026 or early 2027.** **A
> March 2026 analysis states flatly that no US eVTOL will hold a type certificate in 2026,
> putting Joby's mid-2027 probability at 20–30% and Archer at 2028 or later, and citing
> independent analysts projecting entry into service in mid-to-late 2027.**
>
> ⚠️ **Note also that "demonstration flights" and "commercial service" are being conflated
> in coverage.** **The eIPP flights are pre-certification demonstrations, not revenue
> passenger service** — and **§13 → `aero-drones-launch-vehicles-flight-test-and-design`'s point applies: a type certificate, a production
> certificate, and an air carrier certificate are three separate approvals.**
>
> **⚠️ The sector's history supports caution**: **Lilium filed for insolvency in November
> 2024 after certification delays, and Eve moved its commercial target from 2026 to 2028.**
> **Typical eVTOL type certification is cited at 5–8 years from application.**

---

## §17. Numbers

```
ATMOSPHERE (ISA)
Sea level: ρ = 1.225 kg/m³, p = 101,325 Pa, T = 288.15 K, a = 340.3 m/s
⚠️ Lapse rate 6.5 K/km to 11 km; tropopause 11 km, −56.5 °C
Density halves at ~6.5 km

AERODYNAMICS
q = ½ρV² · L = qSC_L · C_Di = C_L²/(πARe) · e ≈ 0.7–0.9
⚠️ Incompressible below M 0.3 · transonic 0.8–1.2 · hypersonic M > 5
Typical cruise: airliner M 0.78–0.85 at 35,000 ft

L/D ⚠️
Sailplane 40–70 · Airliner 17–20 · Light aircraft 10–15 · Shuttle on approach 4–6

PERFORMANCE
⚠️ Breguet: R = (V/c)(L/D)ln(W_i/W_f)
Load factor n = 1/cos φ · ⚠️ 60° bank = 2g · V_stall ∝ √n
Airliner wing loading 500–750 kg/m² · GA 50–100 kg/m²

STRUCTURES ⚠️
Ultimate = 1.5 × limit  (vs 3–5 in civil engineering)
Airliner OEW ~50–55% MTOW · fuel to ~40% MTOW

PROPULSION
⚠️ η_p ≈ 2/(1 + V_e/V_∞) · high-bypass BPR 8–12+
Turbine inlet temp ⚠️ above the alloy melting point, film-cooled

UAS ⚠️
Multirotor endurance 20–40 min · Li-ion 250–300 Wh/kg (⚠️ ~50× below kerosene)
Thrust ∝ ω² · Part 107 VLOS · Part 108 proposed to 1,320 lb (§16.1)

LAUNCH
⚠️ Max-Q ~11–14 km · structural mass fraction is the design driver
```

---

## §18. Books

| Author | Work | Why |
|---|---|---|
| **Anderson** | ***Fundamentals of Aerodynamics*** | ⚠️ **The standard. §1–§4 → `aero-aerodynamics-airfoils-and-compressible-flow`, and unusually well written** |
| **Anderson** | *Introduction to Flight* | ⚠️ **The broad first book, with genuine history** |
| **Raymer** | ***Aircraft Design: A Conceptual Approach*** | ⚠️ **§14 → `aero-drones-launch-vehicles-flight-test-and-design`. The design book — practical and complete** |
| **Torenbeek** | *Synthesis of Subsonic Airplane Design* | The European counterpart |
| **Nelson** | *Flight Stability and Automatic Control* | §6 → `aero-performance-stability-and-propulsion` |
| **Etkin & Reid** | *Dynamics of Flight* | §6 → `aero-performance-stability-and-propulsion`, rigorous |
| **Niu** | ***Airframe Structural Design*** | ⚠️ **§8 → `aero-structures-aeroelasticity-and-avionics`, and genuinely practical** |
| **Hodges & Pierce** | *Introduction to Structural Dynamics and Aeroelasticity* | §9 → `aero-structures-aeroelasticity-and-avionics` |
| **Mattingly** | *Elements of Propulsion* | §7 → `aero-performance-stability-and-propulsion` |
| **Beard & McLain** | ***Small Unmanned Aircraft: Theory and Practice*** | ⚠️ **§11 → `aero-drones-launch-vehicles-flight-test-and-design`, the UAS reference, with working code** |
| **Sutton & Biblarz** | *Rocket Propulsion Elements* | §12 → `aero-drones-launch-vehicles-flight-test-and-design` |
| **Vincenti** | *What Engineers Know and How They Know It* | ⚠️ **How aerospace knowledge is actually produced. Unusual and excellent** |

**⚠️ Also**: **NASA Technical Reports Server (NTRS)** — ⚠️ **decades of free primary
literature, and one of the great engineering archives**; **NACA/NASA reports**; **FAA and
EASA regulations and advisory circulars** (⚠️ **the actual requirements, free**);
**XFOIL/XFLR5** and **OpenVSP** for conceptual design; **ArduPilot** and **PX4** for UAS
autopilots; **AIAA papers**; **NTSB and AAIB accident reports** (⚠️ **the most instructive
engineering documents in the field**).

---

## §19. Quick Reference

### 19.1 Picker
| Need | Approach |
|---|---|
| Estimate lift | `L = ½ρV²S·C_L` (§1 → `aero-aerodynamics-airfoils-and-compressible-flow`) |
| Reduce induced drag | ⚠️ **Higher aspect ratio; elliptical loading** (§2 → `aero-aerodynamics-airfoils-and-compressible-flow`, §3 → `aero-aerodynamics-airfoils-and-compressible-flow`) |
| Fly efficiently in transonic cruise | ⚠️ **Sweep, supercritical airfoil, area ruling** (§4 → `aero-aerodynamics-airfoils-and-compressible-flow`) |
| Maximize range | ⚠️ **Breguet — L/D, SFC, weight fraction** (§5 → `aero-performance-stability-and-propulsion`) |
| Maximum glide distance | Best `L/D` speed — ⚠️ **not slowest** (§3 → `aero-aerodynamics-airfoils-and-compressible-flow`, §5 → `aero-performance-stability-and-propulsion`) |
| Improve manoeuvrability | ⚠️ **Relaxed static stability + FBW** (§6 → `aero-performance-stability-and-propulsion`, §10 → `aero-structures-aeroelasticity-and-avionics`) |
| Efficient subsonic thrust | ⚠️ **High bypass — accelerate more air, less** (§7 → `aero-performance-stability-and-propulsion`) |
| Reduce structural weight safely | ⚠️ **Damage tolerance, not just higher allowables** (§8 → `aero-structures-aeroelasticity-and-avionics`) |
| Prevent flutter | ⚠️ **Mass balance, stiffness, incremental envelope expansion** (§9 → `aero-structures-aeroelasticity-and-avionics`) |
| Tune a multirotor | ⚠️ **Rate loop first, then attitude, then position** (§11.1 → `aero-drones-launch-vehicles-flight-test-and-design`) |
| Long drone endurance | ⚠️ **Fixed-wing or VTOL hybrid — not a better battery** (§11.1 → `aero-drones-launch-vehicles-flight-test-and-design`) |
| Fly a drone BVLOS today | ⚠️ **Part 107 waiver — Part 108 not final** (§16.1) |
| Size a new aircraft | ⚠️ **Sizing loop + constraint diagram** (§14 → `aero-drones-launch-vehicles-flight-test-and-design`) |

### 19.2 Design review checklist
- [ ] Has the sizing loop actually converged, with weight margin? (§14 → `aero-drones-launch-vehicles-flight-test-and-design`)
- [ ] Does the design point satisfy every constraint line? (§14 → `aero-drones-launch-vehicles-flight-test-and-design`)
- [ ] CG range within limits at all loadings, all fuel states? (§6 → `aero-performance-stability-and-propulsion`)
- [ ] Static margin acceptable — or is FBW assumed and specified? (§6 → `aero-performance-stability-and-propulsion`, §10 → `aero-structures-aeroelasticity-and-avionics`)
- [ ] Flutter cleared across the envelope, control surfaces mass balanced? (§9 → `aero-structures-aeroelasticity-and-avionics`)
- [ ] Fatigue spectrum defined and inspection intervals set? (§8 → `aero-structures-aeroelasticity-and-avionics`)
- [ ] Ultimate = 1.5 × limit demonstrated by test, not analysis alone? (§8 → `aero-structures-aeroelasticity-and-avionics`, §13 → `aero-drones-launch-vehicles-flight-test-and-design`)
- [ ] Stall characteristics benign — does the root stall first? (§2 → `aero-aerodynamics-airfoils-and-compressible-flow`)
- [ ] Single sensor failures handled without hazardous control response? (§10 → `aero-structures-aeroelasticity-and-avionics`)
- [ ] Certification basis agreed and means of compliance accepted? (§13 → `aero-drones-launch-vehicles-flight-test-and-design`)
- [ ] For UAS: airspace class, Remote ID, DAA, and current rule status? (§11.3 → `aero-drones-launch-vehicles-flight-test-and-design`, §16.1)

---

## §20. Method

**§1–§15 → `aero-aerodynamics-airfoils-and-compressible-flow`, `aero-performance-stability-and-propulsion`, `aero-structures-aeroelasticity-and-avionics`, `aero-drones-launch-vehicles-flight-test-and-design` and §17 rest on settled engineering** — **Lanchester and Prandtl's circulation
and lifting-line theory (1900s–1918), the Kutta condition, Breguet's range equation, von
Kármán's work on transonic flow, and Whitcomb's area rule (1952)** — sourced from the
texts in §18, chiefly **Anderson**, **Raymer**, **Nelson**, **Niu** and **Beard &
McLain**. ⚠️ **None of it needed verification.**

**Scoped to complement**: propulsion physics, the rocket equation and reentry sit in a
rocket-science reference; DO-178C, redundancy and avionics software in a flight-software
reference. ⚠️ **§12 → `aero-drones-launch-vehicles-flight-test-and-design` deliberately covers only the vehicle-engineering aspects of launchers
and points elsewhere for the physics.**

**Two searches were run in August 2026**, both on **regulation** rather than engineering —
because ⚠️ **that is what actually moved, and in both cases it is what gates whether the
engineering can be deployed.**

**Confidence.** **High** in §1–§15 → `aero-aerodynamics-airfoils-and-compressible-flow`, `aero-performance-stability-and-propulsion`, `aero-structures-aeroelasticity-and-avionics`, `aero-drones-launch-vehicles-flight-test-and-design` and §17. ⚠️ **§1.2 → `aero-aerodynamics-airfoils-and-compressible-flow` and §2 → `aero-aerodynamics-airfoils-and-compressible-flow`'s stall gotcha are the two
corrections I'd most want carried away — the equal-transit-time explanation is
comprehensively wrong and near-universally taught, and "stall is angle of attack, not
airspeed" has direct safety consequences.**

⚠️ **§16 is where I want to be explicit, because both subsections have sources in direct
contradiction and I have not resolved either.**

**On Part 108**: ⚠️ **multiple sources assert the rule is final or imminent; the
best-dated sources checking the actual rulemaking record in July 2026 say it remained at
NPRM stage.** **I have reported the documented record — EO, NPRM publication date, docket
number, comment volumes, reopening, denied extension — and flagged the contradiction
rather than picking a side.** ⚠️ **The original deadline demonstrably slipped, extended by
a government shutdown and then passed, which is itself evidence for the more cautious
reading.** **Check the Federal Register directly.**

**On eVTOL**: ⚠️ **the divergence is starker, and one source is explicitly written to
rebut the optimistic consensus** — asserting no US type certificate in 2026 and putting
Joby at 20–30% for mid-2027. **I have reported the verifiable milestones (Stage 4
completion confirmed late March 2026, conforming aircraft flying, Archer's means-of-
compliance acceptance, the three Chinese type certificates, the eIPP selections) and
presented the timeline claims as contested.** ⚠️ **Note that much of the optimistic
coverage comes from outlets adjacent to the industry, and that "demonstration flights,"
"type certificate" and "commercial service" are being used interchangeably when §13 → `aero-drones-launch-vehicles-flight-test-and-design` shows
they are three distinct things.** **The Lilium insolvency and Eve's slip are the relevant
base rate.**
