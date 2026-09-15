---
name: car-electrical-networks-adas-ev-and-high-voltage-safety
description: "Use for the electrical and electrified side of a modern car: the 12V system and parasitic draw, vehicle networks including CAN, LIN and automotive Ethernet with gateways, ADAS sensing and the calibration requirement, air conditioning, EV architecture and charging, battery chemistry and degradation, high-voltage safety practice and why it is non-negotiable, hybrid architectures, and body construction and corrosion."
---

# Cars and Mechanics: The 12V System, Vehicle Networks, ADAS, Air Conditioning, EV Architecture, Batteries, High-Voltage Safety, Hybrids, and Corrosion

> **Part 3 of 5** of the *How Cars Work — and How Mechanics Do Their Jobs* reference (plugin `how-cars-work-and-how-mechanics-work`), covering §16–§24. Sibling skills: `car-engine-cycle-fuel-ignition-management-and-emissions` (§0–§9), `car-transmissions-driveline-suspension-steering-brakes-and-tyres` (§10–§15), `car-diagnostic-method-obd-tools-and-shop-economics` (§25–§29), `car-reference` (§30–§35). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The mechanical fundamentals are a century settled. Two areas moved. See §30 → `car-reference` for right to repair and data access, and the technician skills gap.

> **⚠️ Two documents in one, deliberately.** **The machine (§1–§24 → `car-engine-cycle-fuel-ignition-management-and-emissions`, `car-transmissions-driveline-suspension-steering-brakes-and-tyres`) and the JOB (§25–§29 → `car-diagnostic-method-obd-tools-and-shop-economics`).**
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
> proven de-energization** (§22). **⚠️ Springs and struts store enormous energy. Fuel
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

## §16. The 12V System

**⚠️ Battery, starter, alternator, and the fact that ⚠️ the ALTERNATOR runs the car once
started; the battery starts it and buffers.**
```
⚠️ VOLTAGE DROP TESTING is the skill that separates real electrical
   diagnosis from guessing. ⚠️ A circuit can show correct voltage with
   no load and collapse under load — you must test WITH THE CIRCUIT
   WORKING, measuring the drop ACROSS the suspect connection
⚠️ GROUNDS cause an enormous share of weird electrical faults.
   ⚠️ A corroded ground produces symptoms in unrelated systems,
   because current finds an unintended return path
⚠️ PARASITIC DRAW  a module not sleeping. ⚠️ Requires the vehicle to
   actually go to sleep before measuring — a common testing error
⚠️ AGM and EFB batteries need REGISTRATION on many cars with smart
   charging; fitting an unregistered battery shortens its life
```
**⚠️ Jump starting modern cars** ⚠️ **has real risks to electronics; follow the
manufacturer's designated points, which often are NOT the battery terminals.**

---

## §17. ⚠️ Vehicle Networks

**⚠️ A modern car is a distributed computer network on wheels, with dozens of ECUs.**
```
⚠️ CAN  differential pair (CAN-H / CAN-L), ⚠️ noise-immune, message-based
   with priority arbitration. ⚠️ ~120Ω terminating resistors at each
   end — measuring ~60Ω across the pair is the classic quick check
LIN  cheap single-wire subnet for slow things (mirrors, seats)
FlexRay · MOST · ⚠️ AUTOMOTIVE ETHERNET for cameras and high bandwidth
⚠️ GATEWAY MODULE  segregates networks — and in newer vehicles
   ⚠️ SECURE GATEWAY authentication is required for a scan tool to
   perform WRITE operations. ⚠️ This is precisely the §30.1 fight
```
**⚠️ Network fault symptoms are distinctive**: ⚠️ **a shorted CAN line takes out MANY
unrelated systems at once and produces a storm of communication codes** — **so when
everything fails simultaneously, suspect the network or a ground (§16), not each system.**
**⚠️ Module programming and coding**: ⚠️ **many replacement parts are inert until programmed
to the vehicle, and some are VIN-locked** — **which is the parts-pairing issue in §30.1 → `car-reference`.**

---

## §18. ⚠️ ADAS

**⚠️ Cameras, radar, ultrasonic, lidar on some vehicles, feeding AEB, ACC, lane keep, blind
spot and parking systems.**
> **⚠️ GOTCHA — CALIBRATION is the part that gets missed, and it is a safety and liability
> issue, not a formality.** ⚠️ **A forward camera aimed a fraction of a degree off points
> its detection zone metres away at distance.** **⚠️ Calibration is required after
> windscreen replacement, alignment changes, suspension work, bumper or grille removal,
> and any collision repair — not only after "ADAS work."**
> **⚠️ STATIC calibration needs targets, precise distances, level floor and controlled
> lighting — which is why it needs SPACE most shops don't have.** **⚠️ DYNAMIC calibration
> requires a road drive under specified conditions.** **⚠️ Many vehicles need both.**
> **⚠️ A car returned uncalibrated may have AEB that brakes late or not at all, with no
> warning light** (§30.2 → `car-reference`).

---

## §19. Air Conditioning

**⚠️ A vapour-compression refrigeration system** (see a refrigeration reference for the
cycle): **compressor, condenser, expansion device, evaporator, receiver/drier or
accumulator.**
**⚠️ Refrigerants**: ⚠️ **R-134a is being displaced by R-1234yf, which is mildly flammable
and much more expensive — and the two are NOT interchangeable, with deliberately different
service fittings.**
**⚠️ Diagnosis**: **pressures on both sides tell the story; ⚠️ the system is sealed, so low
refrigerant means a LEAK — recharging without finding it is a temporary fix and, in most
jurisdictions, venting is illegal.**
**⚠️ The cabin filter is the most commonly forgotten maintenance item** and causes weak
airflow that gets misdiagnosed as a blower or A/C fault.

---

## §20. EV Architecture

```
⚠️ HIGH VOLTAGE BATTERY (400 V or 800 V) → inverter → motor
   ⚠️ 800 V architectures enable faster charging at lower current
⚠️ BMS  monitors cell voltages and temperatures, balances cells,
   enforces limits. ⚠️ Effectively the battery's ECU
⚠️ ON-BOARD CHARGER (AC) vs ⚠️ DC FAST CHARGING (bypasses it, feeds
   the pack directly)
⚠️ DC-DC CONVERTER  ⚠️ replaces the alternator, running the 12V system
   from the HV pack. ⚠️ EVs still have a 12V battery, and a dead 12V
   battery immobilizes an EV completely — a very common call-out
MOTORS  permanent magnet synchronous (efficient) · induction (no
   rare-earth magnets) · ⚠️ one-speed reduction gear, no gearbox
⚠️ THERMAL MANAGEMENT  liquid cooling/heating of the pack;
   ⚠️ heat pumps for cabin heat (resistance heating destroys winter range)
```
**⚠️ What EVs still need serviced**: ⚠️ **tyres (⚠️ heavier vehicles and instant torque wear
them faster), brakes (§14 → `car-transmissions-driveline-suspension-steering-brakes-and-tyres`'s seizing problem), suspension, steering, HVAC, coolant,
cabin filter, 12V battery and software.** **⚠️ What disappears: oil changes, spark plugs,
timing belts, exhaust and fuel systems.**

---

## §21. Batteries and Degradation

**⚠️ Chemistry**: **NMC (higher energy density) vs LFP (⚠️ longer cycle life, more tolerant
of full charging, less energy dense, weaker in cold).**
**⚠️ Degradation drivers, in rough order**: ⚠️ **heat, time (calendar ageing), high state of
charge dwelling, deep cycling, and frequent DC fast charging.** **⚠️ Which is why the
standard advice is 20–80% for daily use and full charges before long trips only** —
**⚠️ with LFP being the exception, where periodic full charges are recommended for BMS
calibration.**
**⚠️ State of Health vs State of Charge**: ⚠️ **SoH is capacity relative to new and is what
matters for a used EV purchase; ⚠️ and pack-level SoH readings vary by tool and method,
so treat single readings cautiously.**
**⚠️ Repairability is the live commercial question**: ⚠️ **module-level and cell-level repair
is technically feasible and often blocked by design, pack construction (structural packs,
glued cells) or data access** — **which is why relatively minor pack damage can total a
vehicle** (§30.1 → `car-reference`).

---

## §22. ⚠️ High-Voltage Safety

> **⚠️ Not negotiable. 400–800 V DC is lethal, and DC causes muscle contraction that
> prevents letting go.**
```
⚠️ ORANGE CABLES = HIGH VOLTAGE. Do not cut, pierce or probe them
⚠️ THE PROCEDURE  qualified training → remove the SERVICE DISCONNECT
   (or follow the OEM shutdown) → ⚠️ WAIT the specified time for
   capacitors to discharge → ⚠️ VERIFY zero volts with a
   CAT III/IV rated meter → verify your meter still works on a
   known live source
⚠️ INSULATED (1000 V) TOOLS and Class 0 rubber gloves, inspected
   and in date, with leather protectors
⚠️ ISOLATION FAULTS  the HV system is deliberately FLOATING relative
   to chassis; ⚠️ an isolation fault means that separation has failed
   and the vehicle should be treated as dangerous
⚠️ DAMAGED PACKS  thermal runaway risk, ⚠️ can reignite hours or days
   later, and requires specific quarantine and firefighting guidance
```
**⚠️ Even for non-HV work**: ⚠️ **an EV or hybrid can be silently "on" and move without
warning; follow the OEM's readiness-disable procedure before working near wheels.**

---

## §23. Hybrids

**⚠️ Series (engine only generates), parallel (both can drive the wheels), power-split
(⚠️ the Toyota planetary arrangement — no conventional transmission at all), and mild
hybrid (⚠️ 48 V, assists but cannot drive alone).**
**⚠️ PHEV** adds a larger pack and plug charging — ⚠️ **and PHEVs used without plugging in
are worse than a plain hybrid, because they carry the battery weight and gain nothing.**
**⚠️ Hybrid-specific service issues**: ⚠️ **the engine runs intermittently, so oil and fuel
age by TIME rather than distance; brakes seize from disuse (§14 → `car-transmissions-driveline-suspension-steering-brakes-and-tyres`); and ⚠️ the ICE in a
hybrid often uses the Atkinson cycle (§1 → `car-engine-cycle-fuel-ignition-management-and-emissions`).**

---

## §24. Body and Corrosion

**⚠️ Unibody versus body-on-frame; ⚠️ crumple zones and high-strength steels — and the
critical repair consequence that ⚠️ ultra-high-strength and boron steels often CANNOT be
heated or straightened and must be sectioned per OEM procedure**, **because heating
destroys the metallurgy the crash structure depends on.**
**⚠️ Corrosion** is galvanic and electrochemical; ⚠️ **it starts where water sits and where
drains block, and surface rust versus structural rust is the distinction that decides
whether a vehicle is economically repairable.**
**⚠️ Post-collision, the ADAS calibration requirement (§18) is now part of any structural
or bumper repair**, **and this is what §30.2 → `car-reference`'s 88% figure is about.**

---

# PART IV — THE MECHANIC'S JOB
