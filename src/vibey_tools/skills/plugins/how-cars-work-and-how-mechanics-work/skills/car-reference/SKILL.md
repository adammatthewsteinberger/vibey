---
name: car-reference
description: "Use when correcting a car or repair misconception, looking up a torque, pressure, voltage, interval or cost figure, finding the resources, or needing a diagnostic quick reference — plus the current state of right to repair, data access and the technician skills gap. Companion to the other cars and mechanics skills."
---

# Cars and Mechanics: What's Live, Misconceptions, Numbers, and Books

> **Part 5 of 5** of the *How Cars Work — and How Mechanics Do Their Jobs* reference (plugin `how-cars-work-and-how-mechanics-work`), covering §30–§35. Sibling skills: `car-engine-cycle-fuel-ignition-management-and-emissions` (§0–§9), `car-transmissions-driveline-suspension-steering-brakes-and-tyres` (§10–§15), `car-electrical-networks-adas-ev-and-high-voltage-safety` (§16–§24), `car-diagnostic-method-obd-tools-and-shop-economics` (§25–§29). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The mechanical fundamentals are a century settled. Two areas moved. See §30 for right to repair and data access, and the technician skills gap.

> **⚠️ Two documents in one, deliberately.** **The machine (§1–§24 → `car-engine-cycle-fuel-ignition-management-and-emissions`, `car-transmissions-driveline-suspension-steering-brakes-and-tyres`, `car-electrical-networks-adas-ev-and-high-voltage-safety`) and the JOB (§25–§29 → `car-diagnostic-method-obd-tools-and-shop-economics`).**
> ⚠️ **The second half is the one most explanations skip, and it's where the actual
> expertise lives — a good technician is a diagnostician, and parts-swapping is what
> happens when diagnosis fails.**
>
> **Complements a thermodynamics reference (the cycle theory), a refrigeration reference
> (A/C, which is a vapour-compression system), and an industrial engineering reference
> (§28 → `car-diagnostic-method-obd-tools-and-shop-economics`'s shop flow).**
>
> **⚠️ Safety, stated once:** ⚠️ **hybrid and EV systems carry 400–800 V DC, which is
> lethal and does not let go; work on them requires specific training, insulated tools and
> proven de-energization** (§22 → `car-electrical-networks-adas-ev-and-high-voltage-safety`). **⚠️ Springs and struts store enormous energy. Fuel
> systems hold pressure long after shutdown. Airbag modules are explosive devices.
> Jack stands, not jacks. And a hot cooling system is pressurized above 100°C.**
>
> **The three ideas that organize this document:**
> 1. **⚠️ A DTC names a CIRCUIT or a CONDITION, not a broken part** (§26 → `car-diagnostic-method-obd-tools-and-shop-economics`). **P0171 does not
>    mean "replace the O2 sensor" — it means the ECU is compensating for a lean condition,
>    and the sensor is the WITNESS, not the suspect.**
> 2. **⚠️ Almost every engine fault is air, fuel, spark, compression, or timing** (§25 → `car-diagnostic-method-obd-tools-and-shop-economics`).
>    **Five things. Test which one is missing before touching anything.**
> 3. **⚠️ The trade's constraint is no longer mechanical skill — it's ACCESS and TRAINING**
>    (§29 → `car-diagnostic-method-obd-tools-and-shop-economics`). **Diagnostic data, software, and calibration capability now decide what a shop
>    can and cannot fix.**

---

## §30. What's Live — verified August 2026

### 30.1 ⚠️ Right to repair: the fight is over DATA, not spanners
**⚠️ This determines what an independent shop is physically able to fix.**

- **⚠️ Massachusetts remains the test case.** **Voters approved Question 1 in November 2020
  by a reported ~75%, requiring manufacturers of model year 2022+ vehicles to provide a
  standardized open-access telematics platform.** ⚠️ **The Alliance for Automotive
  Innovation sued before it took effect, and as of 2026 the litigation continues** —
  **so shops in Massachusetts still do not have the access the law was meant to
  guarantee.** ⚠️ **Maine passed a similar measure in November 2023 by a reported 84%.**
- **⚠️ The litigation shifted materially in 2026.** ⚠️ **At oral argument before the First
  Circuit on 3 February 2026, Auto Innovators conceded that its members COULD safely
  comply with the law as the district court interpreted it — abandoning its central
  argument that compliance was impossible.** ⚠️ **The Massachusetts AG declined mediation
  on 25 February 2026, noting some manufacturers had used the pending case as a reason to
  delay compliance.**
- **⚠️ Federally, the picture is contested and the details matter.** **The REPAIR Act
  (H.R. 1566 / S. 1379) advanced from a House subcommittee, ⚠️ but the full Energy and
  Commerce Committee passed a SUBSTITUTE within the Motor Vehicle Modernization Act of
  2026 (H.R. 7389) by 48–1.** ⚠️ **That version codifies the 2014 industry MOU rather than
  the REPAIR Act's broader provisions** — **and SEMA, notably, is NEUTRAL on it.**
  ⚠️ **It is attached to a surface transportation reauthorization with a 30 September 2026
  deadline.**
- **⚠️ Competing proposal**: **the SAFE Repair Act, backed by collision and automaker
  groups, building on a 2023 voluntary agreement — reported as not yet introduced.**

> **⚠️ GOTCHA — the modern fight is not about access to a wiring diagram, and framing it
> that way misses the point.** ⚠️ **It is about TELEMATICS DATA, SOFTWARE LOCKS and PARTS
> PAIRING** — **the practices where a replacement part is inert until authorized, or a
> repair requires a manufacturer-controlled software transaction** (§17 → `car-electrical-networks-adas-ev-and-high-voltage-safety`'s secure gateway).
> ⚠️ **Proposed federal language would prohibit parts pairing and software locking and
> cover diagnostics, repair, calibration and RECALIBRATION** (§18 → `car-electrical-networks-adas-ev-and-high-voltage-safety`).
> **⚠️ Note the genuine counter-arguments rather than dismissing them: OEMs cite
> cybersecurity and IP, and NHTSA raised safety concerns about the Massachusetts telematics
> mandate in 2023.** ⚠️ **The dealer association has also opposed the REPAIR Act, arguing
> it is substantially about permitting real-time vehicle data to be sold onward with owner
> consent — which is a privacy question as much as a repair one.**

### 30.2 ⚠️ The skills gap has replaced the tool gap
**⚠️ The binding constraint on the trade is now people and training, not equipment.**

- **⚠️ Scale**: ⚠️ **industry estimates place the US technician shortage between roughly
  75,000 and 100,000, with reported need to fill 75,000+ positions annually just to meet
  demand.** **⚠️ The cause is demographic — an aging workforce retiring faster than
  replacement — compounded by a persistent perception of the trade as low-skill, which is
  now simply false.**
- **⚠️ The training gap is unevenly distributed, and this is the finding that matters most
  for independents.** ⚠️ **In the 2026 ATMC Training Benchmarks Survey (2,685 responses,
  up from 1,725 in 2025), 55% of aftermarket and independent shop respondents said they
  have access to the training they need, versus 72% at OEM dealerships.** ⚠️ **And the
  leading obstacle reported was CONTENT GAPS, not cost.**
- **⚠️ What technicians say they need**: ⚠️ **ADAS ranked among the most-requested topics,
  alongside hybrid/EV systems, paint and refinish, and structural repair.**
- **⚠️ UK figures, reported and worth flagging as such**: ⚠️ **IMI TechSafe data reportedly
  showed technicians gaining EV qualifications DROPPED 13% between Q1 and Q3 of 2025,
  against a projected shortfall of 44,000 EV-trained mechanics by 2035**, **and a reported
  figure of just 3% of UK technicians currently ADAS-qualified.**
- **⚠️ Retention is as much the problem as recruitment.** ⚠️ **The 2026 WrenchWay/ASE Voice
  of Technician report is reported as finding 77% say higher pay is the biggest issue, 79%
  do not believe the industry is improving, and 23% say they will probably leave the
  industry within five years for reasons other than retirement.**

> **⚠️ GOTCHA — the ADAS calibration gap is a safety problem hiding inside a business
> problem.** ⚠️ **One 2026 source reports that 88% of vehicles requiring ADAS
> recalibration after collision repair do not get it.** **⚠️ Treat that specific figure
> cautiously — it comes from a diagnostic tool vendor's marketing content — but the
> direction is corroborated: most vehicles since around 2016 require calibration, shops
> lack space and process, and independents have measurably worse training access.**
> ⚠️ **The liability exposure is real and growing: incorrect calibration of automatic
> emergency braking is a foreseeable-harm scenario, and shops need documentation to
> protect themselves.**

**⚠️ The strategic point one trainer makes, which cuts against the usual framing**:
⚠️ **"the knowledge gap is the shop owner, not the technician"** — **technicians who attend
training are ready to learn; the barrier is the decision-maker choosing whether to invest
in tooling and training at all.** **⚠️ And the honest option set is: invest, or sublet EV
and ADAS work to good partners — but telling customers "we don't work on those" quietly
loses the whole household's business.**
**⚠️ Note the countervailing point on EVs and employment**: ⚠️ **EVs remove oil changes and
timing belts but still need brakes, suspension, tyres, HVAC, steering and electronics —
and they ADD high-voltage service, thermal management and software diagnostics.** **It is a
shift in required skills rather than a reduction in work.**

---

## §31. Misconceptions

| Misconception | Correction |
|---|---|
| The code tells you which part is bad | ⚠️ **It names a circuit or condition. Test** (§26 → `car-diagnostic-method-obd-tools-and-shop-economics`) |
| P0171 means replace the O2 sensor | ⚠️ **Vacuum leak, MAF or fuel delivery. It's the witness** (§26 → `car-diagnostic-method-obd-tools-and-shop-economics`) |
| P0420 means the catalyst is dead | ⚠️ **Often an exhaust leak or upstream cause** (§26 → `car-diagnostic-method-obd-tools-and-shop-economics`, §28 → `car-diagnostic-method-obd-tools-and-shop-economics`) |
| Premium fuel gives more power | ⚠️ **Octane is knock resistance, not energy** (§4 → `car-engine-cycle-fuel-ignition-management-and-emissions`, §5 → `car-engine-cycle-fuel-ignition-management-and-emissions`) |
| Black used oil means bad oil | ⚠️ **Detergents holding soot. That's the oil working** (§7 → `car-engine-cycle-fuel-ignition-management-and-emissions`) |
| Oil is oil | ⚠️ **Specs exist for aftertreatment and LSPI now** (§5 → `car-engine-cycle-fuel-ignition-management-and-emissions`, §7 → `car-engine-cycle-fuel-ignition-management-and-emissions`) |
| Rotors warp | ⚠️ **Usually pad transfer and thickness variation** (§14 → `car-transmissions-driveline-suspension-steering-brakes-and-tyres`) |
| Brake fluid lasts forever | ⚠️ **Hygroscopic. Time-based interval** (§14 → `car-transmissions-driveline-suspension-steering-brakes-and-tyres`) |
| Use the pressure on the tyre sidewall | ⚠️ **That's the tyre's MAX. Use the door jamb** (§15 → `car-transmissions-driveline-suspension-steering-brakes-and-tyres`) |
| Tyres are fine until the tread is low | ⚠️ **Rubber ages. Check the DOT date** (§15 → `car-transmissions-driveline-suspension-steering-brakes-and-tyres`) |
| Lifetime fluid means lifetime | ⚠️ **It means the warranty period** (§29 → `car-diagnostic-method-obd-tools-and-shop-economics`) |
| My driving is "normal service" | ⚠️ **Short trips and idling are SEVERE by the manual** (§29 → `car-diagnostic-method-obd-tools-and-shop-economics`) |
| DPF failed | ⚠️ **Usually the duty cycle never allowed regeneration** (§8 → `car-engine-cycle-fuel-ignition-management-and-emissions`) |
| A diesel can have an ignition misfire | ⚠️ **No spark. It's fuel or compression** (§9 → `car-engine-cycle-fuel-ignition-management-and-emissions`) |
| Turbos just wear out | ⚠️ **Most turbo failures are oil failures** (§3 → `car-engine-cycle-fuel-ignition-management-and-emissions`) |
| EVs need no maintenance | ⚠️ **Tyres, brakes, suspension, HVAC, coolant, 12V** (§20 → `car-electrical-networks-adas-ev-and-high-voltage-safety`) |
| EV won't start — must be the big battery | ⚠️ **Usually the 12V battery** (§20 → `car-electrical-networks-adas-ev-and-high-voltage-safety`) |
| Charge an EV to 100% every night | ⚠️ **20–80% for NMC; LFP differs** (§21 → `car-electrical-networks-adas-ev-and-high-voltage-safety`) |
| Regen means brakes never wear out | ⚠️ **They seize from disuse instead** (§14 → `car-transmissions-driveline-suspension-steering-brakes-and-tyres`, §23 → `car-electrical-networks-adas-ev-and-high-voltage-safety`) |
| A windscreen swap is just glass | ⚠️ **The forward camera needs calibration** (§18 → `car-electrical-networks-adas-ev-and-high-voltage-safety`) |
| ADAS calibration is optional | ⚠️ **Safety-critical, and a liability exposure** (§18 → `car-electrical-networks-adas-ev-and-high-voltage-safety`, §30.2) |
| Free code reading is a diagnosis | ⚠️ **It's a parts store selling parts** (§26 → `car-diagnostic-method-obd-tools-and-shop-economics`) |
| Right to repair is about wiring diagrams | ⚠️ **It's telematics, software locks, parts pairing** (§30.1) |
| Independents can't fix modern cars | ⚠️ **Access and training are the constraint, not skill** (§30) |

---

## §32. Numbers

```
⚠️ Stoichiometric AFR (petrol)   ~14.7:1  (⚠️ catalyst works only near it)
⚠️ Cam speed                     ⚠️ HALF crank speed
⚠️ CAN termination               ⚠️ ~120Ω each end; ~60Ω across the pair
⚠️ EV traction voltage           400 V or 800 V DC
⚠️ Fuel trim reading             ⚠️ positive = adding fuel = sees LEAN
⚠️ Tyre sidewall 225/45R17 94V   width/aspect/radial/rim/load/speed
⚠️ Tyre age guidance             reported 6–10 years regardless of tread
⚠️ ADAS calibration kit          reported $4,000 mobile – $16,000 integrated
⚠️ ADAS tech training investment reported $3,000–$10,000 per technician
⚠️ US technician shortage        reported ~75,000–100,000
⚠️ Training access               ⚠️ 55% independents vs 72% dealership
⚠️ ATMC survey 2026              2,685 responses (1,725 in 2025)
⚠️ Techs likely to leave <5 yrs  reported 23% (non-retirement)
⚠️ MA Question 1 (2020)          reported ~75% in favour · Maine 2023 ~84%
⚠️ H.R. 7389 committee vote      48–1 · reauthorization deadline 30 Sep 2026
```

---

## §33. Books and Resources

| Source | Why |
|---|---|
| **Halderman** | *Automotive Technology* | ⚠️ **The standard textbook, and genuinely good** |
| **Bosch Automotive Handbook** | — | ⚠️ **Dense reference for how systems actually work** |
| **ASE study guides / certification** | — | ⚠️ **The structured path through the trade** |
| **ALLDATA / Mitchell1 / Identifix** | — | ⚠️ **§27 → `car-diagnostic-method-obd-tools-and-shop-economics`'s service information. The real cost of entry** |
| **OEM service portals** | — | ⚠️ **Where the authoritative procedure lives** (§30.1) |
| **SAE J1979 / J1962 (OBD-II)** | — | The standard behind §26 → `car-diagnostic-method-obd-tools-and-shop-economics` |
| **ScannerDanner (Paul Danner)** | *Engine Performance Diagnostics* | ⚠️ **The best teaching on scope-based §25 → `car-diagnostic-method-obd-tools-and-shop-economics` diagnosis** |
| **Wells / Autel / Snap-on training** | — | Tool-specific but substantive |
| **IMI TechSafe / ASE xEV certifications** | — | ⚠️ **§22 → `car-electrical-networks-adas-ev-and-high-voltage-safety`'s HV credential** |
| **I-CAR** | — | ⚠️ **Collision and ADAS procedure — §18 → `car-electrical-networks-adas-ev-and-high-voltage-safety`, §24 → `car-electrical-networks-adas-ev-and-high-voltage-safety`** |
| **TSBs and recall databases (NHTSA)** | — | ⚠️ **§25 → `car-diagnostic-method-obd-tools-and-shop-economics` step 2. Free and constantly ignored** |

---

## §34. Quick Reference

### 34.1 Diagnostic picker
| Symptom | Where |
|---|---|
| Any running fault | ⚠️ **Air, fuel, spark, compression, timing** (§25 → `car-diagnostic-method-obd-tools-and-shop-economics`) |
| Lean or rich code | ⚠️ **Read FUEL TRIMS at idle AND load** (§6 → `car-engine-cycle-fuel-ignition-management-and-emissions`, §26 → `car-diagnostic-method-obd-tools-and-shop-economics`) |
| Lean at idle only | ⚠️ **Vacuum leak — smoke test** (§6 → `car-engine-cycle-fuel-ignition-management-and-emissions`, §27 → `car-diagnostic-method-obd-tools-and-shop-economics`) |
| Lean at load only | ⚠️ **Fuel delivery or MAF** (§6 → `car-engine-cycle-fuel-ignition-management-and-emissions`) |
| Misfire | ⚠️ **Isolate cylinder, then ignition vs fuel vs compression** (§25 → `car-diagnostic-method-obd-tools-and-shop-economics`) |
| Overheats at idle, fine moving | ⚠️ **Cooling fan** (§7 → `car-engine-cycle-fuel-ignition-management-and-emissions`) |
| Overheats always, no leak | ⚠️ **Thermostat, pump, or head gasket — block test** (§7 → `car-engine-cycle-fuel-ignition-management-and-emissions`) |
| Many unrelated faults at once | ⚠️ **Ground or CAN** (§16 → `car-electrical-networks-adas-ev-and-high-voltage-safety`, §17 → `car-electrical-networks-adas-ev-and-high-voltage-safety`) |
| Battery dies overnight | ⚠️ **Parasitic draw, after modules sleep** (§16 → `car-electrical-networks-adas-ev-and-high-voltage-safety`) |
| Judder under braking | ⚠️ **DTV/pad transfer, not "warped"** (§14 → `car-transmissions-driveline-suspension-steering-brakes-and-tyres`) |
| Shudder at steady cruise | ⚠️ **Torque converter lock-up** (§10 → `car-transmissions-driveline-suspension-steering-brakes-and-tyres`) |
| Pull to one side | ⚠️ **Swap front tyres first — free test** (§13 → `car-transmissions-driveline-suspension-steering-brakes-and-tyres`) |
| Tyre wearing on one edge | ⚠️ **Camber. Feathered → toe. Cupped → dampers** (§15 → `car-transmissions-driveline-suspension-steering-brakes-and-tyres`) |
| Clicking on turns | ⚠️ **Outer CV joint** (§11 → `car-transmissions-driveline-suspension-steering-brakes-and-tyres`) |
| Safety system light after bodywork | ⚠️ **Calibration** (§18 → `car-electrical-networks-adas-ev-and-high-voltage-safety`) |
| EV completely dead | ⚠️ **12V battery** (§20 → `car-electrical-networks-adas-ev-and-high-voltage-safety`) |
| Diesel warning light, short trips | ⚠️ **DPF regeneration never completing** (§8 → `car-engine-cycle-fuel-ignition-management-and-emissions`) |

### 34.2 Before you replace anything
- [ ] ⚠️ **Complaint verified and reproduced** (§25 → `car-diagnostic-method-obd-tools-and-shop-economics`)
- [ ] ⚠️ **TSBs and recalls checked** (§25 → `car-diagnostic-method-obd-tools-and-shop-economics`)
- [ ] Freeze frame captured before clearing anything (§26 → `car-diagnostic-method-obd-tools-and-shop-economics`)
- [ ] ⚠️ **Visual inspection done — wiring, connectors, leaks** (§25 → `car-diagnostic-method-obd-tools-and-shop-economics`)
- [ ] ⚠️ **A TEST performed that distinguishes this cause from the alternatives**
- [ ] ⚠️ **Root cause identified, not just the failed component** (§26 → `car-diagnostic-method-obd-tools-and-shop-economics`)
- [ ] Relearn/calibration requirements known before starting (§6 → `car-engine-cycle-fuel-ignition-management-and-emissions`, §18 → `car-electrical-networks-adas-ev-and-high-voltage-safety`)
- [ ] ⚠️ **Fix verified under the original failing conditions** (§25 → `car-diagnostic-method-obd-tools-and-shop-economics`)

---

## §35. Method

**§1–§29 → `car-engine-cycle-fuel-ignition-management-and-emissions`, `car-transmissions-driveline-suspension-steering-brakes-and-tyres`, `car-electrical-networks-adas-ev-and-high-voltage-safety`, `car-diagnostic-method-obd-tools-and-shop-economics` rests on settled automotive engineering and standard trade practice** — **the
four-stroke cycle, closed-loop fuel control, hydraulic braking, alignment geometry, OBD-II
as specified in SAE standards, and diagnostic method as taught in ASE-track training.**
⚠️ **None of it needed verification.**

**Two searches were run in August 2026**, on **right to repair** and **the technician
skills gap** — ⚠️ **both chosen because they bear directly on the SECOND half of the title:
they determine what a mechanic is actually able to do.**

**Confidence.** **High** in §25 → `car-diagnostic-method-obd-tools-and-shop-economics`, §26 → `car-diagnostic-method-obd-tools-and-shop-economics` and §6 → `car-engine-cycle-fuel-ignition-management-and-emissions`, which are the load-bearing sections and the
ones I'd most want read. ⚠️ **"The code names a circuit or condition, not a failed part" is
the correction that would prevent the largest share of wasted money in this domain, and
§6 → `car-engine-cycle-fuel-ignition-management-and-emissions`'s fuel-trim reading is the highest-yield single diagnostic skill — positive trim means
the ECU is adding fuel, and where the trim goes wrong (idle vs load, one bank vs both)
narrows the cause immediately.** **§28 → `car-diagnostic-method-obd-tools-and-shop-economics`'s misdiagnosis list is the same point in worked form,
and the pattern across all of them is that the replaced part was the one REPORTING the
problem rather than causing it.**

**High** in §22 → `car-electrical-networks-adas-ev-and-high-voltage-safety`'s high-voltage procedure, which is safety-critical and standard across
training bodies.

**High** on §30.1's legislative and litigation facts, which come from law firm briefings,
SEMA, the Auto Care Association and trade press that corroborate each other on the
specifics: ⚠️ **the February 2026 First Circuit concession, the AG's refusal of mediation,
the 48–1 committee vote on H.R. 7389, and the substitution of MOU codification for the
REPAIR Act's broader language.** ⚠️ **Sourcing caution: the Auto Care Association and SEMA
are advocacy organizations for the independent aftermarket, so I've included the
counter-arguments — OEM cybersecurity and IP claims, NHTSA's 2023 safety concern, and the
dealer association's data-sale objection — because they are substantive rather than
pretextual.**

**Moderate** on §30.2's specific figures. ⚠️ **The ATMC survey numbers (2,685 responses,
55% vs 72% training access, content gaps over cost) are the most solid, coming from ASE's
Training Managers Council.** ⚠️ **The 75,000–100,000 shortage range is an industry estimate
band rather than a single measurement, and the UK IMI figures and the WrenchWay/ASE
retention percentages come from secondary reporting.** ⚠️ **The 88% ADAS non-calibration
figure I have deliberately flagged in-line as coming from a diagnostic tool vendor's
marketing — the direction is corroborated by independent trade coverage of process and
training gaps, but I would not cite that specific number without a primary source.**
