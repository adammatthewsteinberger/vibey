---
name: car-engine-cycle-fuel-ignition-management-and-emissions
description: "Use for anything engine-side: the four-stroke cycle, engine anatomy, the air path with throttle and turbocharging, fuel and injection including port versus direct, ignition and knock and why timing gets retarded, engine management and closed-loop fuel control with lambda sensors and fuel trims, cooling and lubrication, emissions aftertreatment with catalysts, EGR, DPF and SCR, and diesel specifics. Includes the router for the whole cars and mechanics reference."
---

# Cars and Mechanics: The Four-Stroke Cycle, Engine Anatomy, Air, Fuel, Ignition and Knock, Engine Management, Cooling, Emissions, and Diesel

> **Part 1 of 5** of the *How Cars Work — and How Mechanics Do Their Jobs* reference (plugin `how-cars-work-and-how-mechanics-work`), covering §0–§9. Sibling skills: `car-transmissions-driveline-suspension-steering-brakes-and-tyres` (§10–§15), `car-electrical-networks-adas-ev-and-high-voltage-safety` (§16–§24), `car-diagnostic-method-obd-tools-and-shop-economics` (§25–§29), `car-reference` (§30–§35). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The mechanical fundamentals are a century settled. Two areas moved. See §30 → `car-reference` for right to repair and data access, and the technician skills gap.

> **⚠️ Two documents in one, deliberately.** **The machine (§1–§24 → `car-transmissions-driveline-suspension-steering-brakes-and-tyres`, `car-electrical-networks-adas-ev-and-high-voltage-safety`) and the JOB (§25–§29 → `car-diagnostic-method-obd-tools-and-shop-economics`).**
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

## §0. Routing

| You want... | Go to |
|---|---|
| Engine basics | §1–§2 |
| Air path and boost | §3 |
| Fuel and injection | §4 |
| **⚠️ Ignition and knock** | **§5** |
| **⚠️ Engine management** | **§6** |
| Cooling and lubrication | §7 |
| **⚠️ Emissions aftertreatment** | **§8** |
| Diesel specifics | §9 |
| **Transmissions** | **§10 → `car-transmissions-driveline-suspension-steering-brakes-and-tyres`** |
| Driveline and differentials | §11 → `car-transmissions-driveline-suspension-steering-brakes-and-tyres` |
| Suspension | §12 → `car-transmissions-driveline-suspension-steering-brakes-and-tyres` |
| Steering and alignment | §13 → `car-transmissions-driveline-suspension-steering-brakes-and-tyres` |
| **Brakes** | **§14 → `car-transmissions-driveline-suspension-steering-brakes-and-tyres`** |
| **⚠️ Tyres** | **§15 → `car-transmissions-driveline-suspension-steering-brakes-and-tyres`** |
| **12V system** | **§16 → `car-electrical-networks-adas-ev-and-high-voltage-safety`** |
| **⚠️ CAN and networks** | **§17 → `car-electrical-networks-adas-ev-and-high-voltage-safety`** |
| **⚠️ ADAS** | **§18 → `car-electrical-networks-adas-ev-and-high-voltage-safety`** |
| A/C | §19 → `car-electrical-networks-adas-ev-and-high-voltage-safety` |
| **⚠️ EV architecture and HV safety** | **§20–§22 → `car-electrical-networks-adas-ev-and-high-voltage-safety`** |
| Hybrids | §23 → `car-electrical-networks-adas-ev-and-high-voltage-safety` |
| Body and corrosion | §24 → `car-electrical-networks-adas-ev-and-high-voltage-safety` |
| **⚠️ DIAGNOSTIC METHOD** | **§25 → `car-diagnostic-method-obd-tools-and-shop-economics`** |
| **⚠️ OBD-II and scan data** | **§26 → `car-diagnostic-method-obd-tools-and-shop-economics`** |
| Tools | §27 → `car-diagnostic-method-obd-tools-and-shop-economics` |
| **⚠️ Common misdiagnoses** | **§28 → `car-diagnostic-method-obd-tools-and-shop-economics`** |
| Maintenance and shop economics | §29 → `car-diagnostic-method-obd-tools-and-shop-economics` |
| **What's live** | **§30 → `car-reference`** |
| Misconceptions, numbers | §31–§32 → `car-reference` |
| Books, quick ref, method | §33–§35 → `car-reference` |

---

# PART I — POWERTRAIN

## §1. The Four-Stroke Cycle

**⚠️ Intake → compression → power → exhaust, over two crankshaft revolutions.**
```
⚠️ The camshaft turns at HALF crankshaft speed — because each valve
   opens once per two revolutions. ⚠️ This is why timing belt/chain
   ratios are 2:1 and why "one tooth out" is a large error
⚠️ COMPRESSION RATIO  higher = more efficiency, ⚠️ limited by KNOCK (§5)
⚠️ VOLUMETRIC EFFICIENCY  how completely the cylinder fills.
   ⚠️ THE thing intake design, valve timing and forced induction all
   exist to improve
⚠️ ATKINSON/MILLER CYCLE  ⚠️ effective compression < expansion, via
   late intake valve closing. More efficient, less power dense —
   which is why it's standard in hybrids (§23)
```
**⚠️ Firing order and balance**: ⚠️ **inline-6 and flat-6 are inherently balanced; inline-4
has a secondary imbalance (hence balance shafts); V6 needs offset crank pins or a balance
shaft.** **⚠️ This is why engine layout is a NVH decision as much as a packaging one.**

---

## §2. Engine Anatomy

**Block, head, gasket (⚠️ the head gasket seals combustion, coolant AND oil passages
simultaneously — which is why its failure produces such varied symptoms), crankshaft,
connecting rods, pistons and rings (⚠️ compression rings seal, the oil control ring
scrapes — worn oil rings cause oil consumption without compression loss), bearings,
valvetrain.**
**⚠️ Valvetrain types**: **OHV/pushrod, SOHC, DOHC; ⚠️ variable valve timing (cam phasing)
and variable lift (VTEC-type) exist to broaden the useful VE curve.**
**⚠️ Timing belt vs chain**: ⚠️ **belts are a SERVICE ITEM with a replacement interval;
chains are meant to last but stretch and their tensioners and guides fail.** ⚠️ **On an
INTERFERENCE engine, a failed belt or jumped chain means valves meet pistons and the
engine is destroyed** — **which is why belt intervals are not advisory.**

---

## §3. The Air Path

**⚠️ Filter → throttle → manifold → valves.** **⚠️ MAF vs MAP sensing (§6); IAT; and
⚠️ the fact that an intake leak downstream of the MAF is unmetered air, which is the
classic cause of a lean code** (§28 → `car-diagnostic-method-obd-tools-and-shop-economics`).
**⚠️ Forced induction**: **⚠️ turbochargers are driven by exhaust energy (efficient, with
lag); superchargers are crank-driven (instant, parasitic).** **⚠️ Intercooling raises
density; wastegate and blow-off/diverter valves manage pressure; ⚠️ variable geometry
turbines reduce lag.**
**⚠️ The turbo failure people misattribute**: ⚠️ **most turbo failures are OIL failures —
coked oil in the bearing feed from a hot shutdown, extended intervals or the wrong grade.**
**⚠️ EGR** recirculates inert exhaust to lower peak combustion temperature and cut NOx
(§8) — ⚠️ **and it is a notorious carbon-fouling point, especially on diesel.**

---

## §4. Fuel and Injection

```
⚠️ PORT INJECTION (PFI)  injects onto the back of the intake valve —
   ⚠️ which incidentally WASHES it clean
⚠️ DIRECT INJECTION (GDI)  injects into the cylinder. Higher pressure,
   better efficiency and power, enables stratified charge
   ⚠️ THE TRADE-OFF: no fuel washes the intake valves, so carbon
   deposits build up. ⚠️ Walnut blasting is a real service item on
   GDI engines and surprises owners
DUAL INJECTION  ⚠️ some manufacturers fit BOTH to get around exactly that
⚠️ FUEL TRIM  short-term and long-term (§6, §26) — the single most
   informative live data on a running engine
```
**⚠️ Fuel pressure and delivery**: **lift pump, high-pressure pump on GDI, regulator,
returnless systems.** ⚠️ **A weak pump often shows only under load, which is why static
pressure tests miss it.**
**⚠️ Octane** is knock RESISTANCE, not energy content (§5) — ⚠️ **premium fuel in an engine
that doesn't require it buys nothing.**

---

## §5. ⚠️ Ignition and Knock

**Coil-on-plug, spark plug heat range and gap, dwell.**
> **⚠️ GOTCHA — KNOCK is not "pinging because the engine is old."** ⚠️ **It's
> uncontrolled AUTO-IGNITION of the end gas ahead of the flame front, producing a pressure
> spike that hammers pistons and bearings.** **⚠️ The knock sensor is a microphone-like
> accelerometer; when it detects knock the ECU RETARDS timing, which protects the engine
> and costs power and economy.**
> ⚠️ **So a car that "feels gutless" may be pulling timing for knock caused by carbon
> deposits, bad fuel, overheating or a lean condition — and it may set no code at all.**
> **⚠️ LSPI (low-speed pre-ignition) in turbo GDI engines is a related and destructive
> phenomenon, and it's why modern turbo engines specify particular oil formulations
> (API SP / dexos) — the oil chemistry itself is a knock-control measure.**

---

## §6. ⚠️ Engine Management and Closed-Loop Control

**⚠️ Understand this and most driveability diagnosis becomes readable.**
```
⚠️ THE ECU'S JOB  maintain the air-fuel ratio near STOICHIOMETRIC
   (~14.7:1 for petrol) because ⚠️ THE CATALYST ONLY WORKS THERE (§8)
⚠️ THE FEEDBACK LOOP
   ⚠️ Upstream O2 / wideband sensor reads exhaust oxygen
   → ECU adjusts injector pulse width
   → ⚠️ SHORT TERM FUEL TRIM (STFT) swings moment to moment
   → ⚠️ LONG TERM FUEL TRIM (LTFT) learns the persistent correction
⚠️ READING TRIMS IS THE CORE SKILL
   ⚠️ POSITIVE trim = ECU ADDING fuel = it sees LEAN
   ⚠️ NEGATIVE trim = ECU REMOVING fuel = it sees RICH
   ⚠️ Lean at IDLE but fine at load → vacuum leak (leak is a fixed
      volume, proportionally huge at idle)
   ⚠️ Lean at LOAD but fine at idle → fuel delivery or a MAF reading low
   ⚠️ Lean on ONE BANK only → that bank's O2, injectors, or a
      bank-specific leak — NOT the fuel pump
```
**⚠️ Open loop vs closed loop**: ⚠️ **cold start, wide-open throttle and some failure modes
run OPEN loop from a table, ignoring the O2 sensor** — **which is why some faults only
appear once the engine warms and closes the loop.**
**⚠️ Adaptations and relearns**: ⚠️ **the ECU learns; after a repair, learned corrections
may need clearing, and throttle bodies, transmissions and steering angle sensors often
require explicit relearn procedures** (§27 → `car-diagnostic-method-obd-tools-and-shop-economics`).

---

## §7. Cooling and Lubrication

**⚠️ Cooling**: ⚠️ **the system is PRESSURIZED to raise the coolant's boiling point** —
**which is why removing a hot cap causes flash boiling and serious burns.** **⚠️ Thermostat
(stuck open = never warms = poor economy and heater; stuck closed = overheat), water pump,
radiator, fan (⚠️ electric fan or clutch failure shows as overheating at idle but not at
speed — the road speed provides airflow), and the heater core, which is a small radiator
inside the cabin.**
**⚠️ Combustion gases in the coolant** (⚠️ **detectable with a block tester**) **indicate a
head gasket or crack, and the classic sign is a persistently pressurized system or
overflow with no external leak.**
**⚠️ Lubrication**: ⚠️ **oil does five jobs — lubricate, cool, clean (detergents and
dispersants hold soot in suspension, which is why used oil is black and that is NORMAL),
seal the rings, and protect against corrosion.** **⚠️ Viscosity grades (5W-30: the W number
is cold behaviour), and ⚠️ modern specifications exist for aftertreatment and LSPI
compatibility (§5, §8), so "oil is oil" is genuinely false now.**

---

## §8. ⚠️ Emissions Aftertreatment

```
⚠️ THREE-WAY CATALYST  oxidizes CO and HC, reduces NOx.
   ⚠️ ONLY works in a narrow window around stoichiometric — which is
   the entire reason for the closed-loop control in §6
⚠️ DOWNSTREAM O2 SENSOR  ⚠️ its job is to MONITOR THE CATALYST, not to
   control fuel. A "lazy" downstream sensor mirroring the upstream one
   sets a catalyst efficiency code
⚠️ EVAP  captures fuel vapour. ⚠️ A loose fuel cap genuinely does set
   a code (P0455/P0457) — the system pressure/vacuum tests itself
⚠️ DIESEL (§9)
   ⚠️ DOC → DPF (traps soot, ⚠️ REGENERATES by burning it off) →
   ⚠️ SCR with DEF/AdBlue (urea converts NOx to N₂ and water)
⚠️ GPF  particulate filters now on many direct-injection PETROL engines
```
> **⚠️ GOTCHA — DPF problems are usually USE-PATTERN problems, and this is the single most
> common diesel misunderstanding.** ⚠️ **Regeneration requires sustained high exhaust
> temperature, which requires sustained driving.** **⚠️ A diesel used only for short cold
> trips cannot complete regenerations, the filter loads up, and eventually it needs forced
> regeneration or replacement.** **The vehicle was mismatched to the duty cycle; the part
> did not fail.**

---

## §9. Diesel Specifics

**⚠️ Compression ignition — no spark, ⚠️ so a diesel "misfire" is a fuelling or compression
problem, never an ignition one.**
**⚠️ Very high compression ratios; glow plugs for cold starting; ⚠️ common rail injection at
extremely high pressure with piezo or solenoid injectors; and ⚠️ injector coding — modern
injectors carry calibration data that must be entered when replaced.**
**⚠️ Diesels run LEAN overall**, ⚠️ **which is why a three-way catalyst can't work and why
SCR exists** (§8).
**⚠️ Fuel contamination is the expensive failure**: ⚠️ **water or petrol in diesel destroys
the high-pressure pump, and the debris then contaminates the entire fuel system — often
making it a full-system replacement rather than a pump job.**
