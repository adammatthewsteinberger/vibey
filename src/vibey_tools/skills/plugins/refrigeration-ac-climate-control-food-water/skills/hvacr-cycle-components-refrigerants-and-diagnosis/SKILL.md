---
name: hvacr-cycle-components-refrigerants-and-diagnosis
description: "Use when working on a refrigeration system: the vapour-compression cycle as it actually behaves, compressors, condensers, evaporators and metering devices, refrigerant properties, safety classification and flammability, charge, evacuation and leak detection, diagnosis by superheat and subcooling and what each measurement tells you, and the alternative cooling approaches including absorption, thermoelectric and evaporative. Includes the router for the whole refrigeration and climate control reference."
---

# Refrigeration and Climate Control: The Cycle in Practice, Components, Refrigerants, Charge and Leaks, Superheat and Subcooling Diagnosis, and Other Cooling Approaches

> **Part 1 of 5** of the *Refrigeration, AC, Climate Control and Food/Water Storage* reference (plugin `refrigeration-ac-climate-control-food-water`), covering §0–§6. Sibling skills: `hvacr-load-calculation-air-humidity-and-heat-pumps` (§7–§13), `hvacr-cold-chain-temperature-limits-and-validation` (§14–§21), `hvacr-preservation-water-storage-and-treatment` (§22–§24), `hvacr-reference` (§25–§30). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The thermodynamics is permanent. Two areas moved. See §25 → `hvacr-reference` for the refrigerant transition, and cold chain capacity and food loss.

> **⚠️ Everything here is one idea in different clothes: MOVING HEAT from where you don't
> want it to where you don't care, and doing it reliably enough that the thing being
> cooled stays safe.** **Complements a thermodynamics reference (the cycle theory and
> psychrometrics) and a cooking/cleaning reference (food safety at the point of use).**
>
> **⚠️ GOTCHA** boxes mark the diagnoses people get backwards, and the safety limits that
> aren't negotiable.
>
> **⚠️ Safety, stated once and up front:** ⚠️ **refrigerant systems hold high pressure and
> can cause frostbite and asphyxiation; A2L refrigerants are mildly flammable and require
> specific tooling and training (§25.1 → `hvacr-reference`); ammonia is toxic; and the food temperature limits
> in §16 → `hvacr-cold-chain-temperature-limits-and-validation` are not guidance, they are the reason people don't die.** **⚠️ Refrigerant handling
> is a certified activity in most jurisdictions — venting is illegal and recovery is
> mandatory.**
>
> **The three ideas that organize this document:**
> 1. **⚠️ SUPERHEAT and SUBCOOLING are how you see inside a sealed system** (§5).
>    **Everything else in diagnosis is guessing.**
> 2. **⚠️ The cold chain is only as good as its worst link, and the worst link is almost
>    always a HANDOFF** (§15 → `hvacr-cold-chain-temperature-limits-and-validation`, §20 → `hvacr-cold-chain-temperature-limits-and-validation`). **Not the warehouse and not the truck — the dock, the
>    delay, the unmonitored gap.**
> 3. **⚠️ Preservation is about denying microbes ONE of their requirements** (§22 → `hvacr-preservation-water-storage-and-treatment`).
>    **Temperature is only one option; water activity, pH, oxygen and competition are the
>    others, and the durable methods stack several.**

---

## §0. Routing

| You want... | Go to |
|---|---|
| The cycle in practice | §1 |
| **Components** | **§2** |
| **⚠️ Refrigerants** | **§3–§4** |
| **⚠️ Diagnosis** | **§5** |
| Other cooling cycles | §6 |
| Load calculation | §7 → `hvacr-load-calculation-air-humidity-and-heat-pumps` |
| Air distribution | §8 → `hvacr-load-calculation-air-humidity-and-heat-pumps` |
| **⚠️ Humidity control** | **§9 → `hvacr-load-calculation-air-humidity-and-heat-pumps`** |
| Ventilation and IAQ | §10 → `hvacr-load-calculation-air-humidity-and-heat-pumps` |
| **Heat pumps** | **§11 → `hvacr-load-calculation-air-humidity-and-heat-pumps`** |
| Controls | §12 → `hvacr-load-calculation-air-humidity-and-heat-pumps` |
| Envelope | §13 → `hvacr-load-calculation-air-humidity-and-heat-pumps` |
| **⚠️ Spoilage mechanisms** | **§14–§15 → `hvacr-cold-chain-temperature-limits-and-validation`** |
| **⚠️ Temperature limits** | **§16 → `hvacr-cold-chain-temperature-limits-and-validation`** |
| Chilling and freezing | §17 → `hvacr-cold-chain-temperature-limits-and-validation` |
| Controlled atmosphere | §18 → `hvacr-cold-chain-temperature-limits-and-validation` |
| Transport refrigeration | §19 → `hvacr-cold-chain-temperature-limits-and-validation` |
| **Monitoring and validation** | **§20 → `hvacr-cold-chain-temperature-limits-and-validation`** |
| Pharmaceutical cold chain | §21 → `hvacr-cold-chain-temperature-limits-and-validation` |
| **⚠️ Preservation without cold** | **§22 → `hvacr-preservation-water-storage-and-treatment`** |
| Water storage and treatment | §23–§24 → `hvacr-preservation-water-storage-and-treatment` |
| **What's live** | **§25 → `hvacr-reference`** |
| Misconceptions, numbers | §26–§27 → `hvacr-reference` |
| Books, quick ref, method | §28–§30 → `hvacr-reference` |

---

# PART I — REFRIGERATION

## §1. The Cycle in Practice

```
⚠️ COMPRESSOR   low-pressure vapour → high-pressure, high-temperature vapour
⚠️ CONDENSER    rejects heat; vapour → liquid (⚠️ and SUBCOOLS below
                saturation before leaving)
⚠️ METERING     expansion valve or capillary — pressure drops, some liquid
                flashes to vapour and the mixture gets COLD
⚠️ EVAPORATOR   absorbs heat; liquid → vapour (⚠️ and SUPERHEATS above
                saturation before returning)
```
**⚠️ The idea most people miss**: ⚠️ **the cold does not come from the compressor.** **It
comes from LATENT HEAT of vaporization in the evaporator — the refrigerant boils, and
boiling absorbs enormous energy at constant temperature.** ⚠️ **The compressor's job is to
raise the pressure so the vapour can be condensed at ambient temperature; it's a pump for
the cycle, not a cold generator.**
**⚠️ Why the expansion device is deliberately wasteful**: ⚠️ **throttling is isenthalpic and
irreversible — a turbine could recover work but isn't worth the complexity at small
scale.** **This is one of the largest single sources of inefficiency in the cycle and it's
accepted on cost grounds.**

---

## §2. Components

```
COMPRESSORS
  ⚠️ RECIPROCATING  robust, serviceable, ⚠️ liquid slugging destroys it
  SCROLL            ⚠️ the residential/light commercial default; quiet, efficient
  SCREW / CENTRIFUGAL  large commercial and industrial chillers
  ⚠️ HERMETIC (sealed) vs SEMI-HERMETIC (serviceable) vs OPEN-DRIVE
  ⚠️ INVERTER/VARIABLE SPEED  ⚠️ the biggest efficiency gain available —
     a fixed-speed compressor cycles on and off; a modulating one runs
     longer at lower capacity, which also dehumidifies far better (§9)
CONDENSERS   air-cooled · water-cooled (⚠️ with a cooling tower —
   ⚠️ Legionella risk, see §10) · evaporative
EVAPORATORS  ⚠️ DX (direct expansion) vs flooded · finned coil
METERING     ⚠️ TXV (thermostatic — mechanically maintains superheat) ·
   ⚠️ EEV (electronic — better control, needed for modulating systems) ·
   capillary tube (⚠️ fixed orifice; critically charge-sensitive) · orifice
ACCESSORIES  filter-drier (⚠️ moisture is the enemy — it forms acid with
   refrigerant and oil), receiver, accumulator (⚠️ protects the compressor
   from liquid return), sight glass, service valves
```
**⚠️ Oil management is the under-appreciated failure mode**: ⚠️ **compressor oil circulates
with the refrigerant and must return.** **Poor line sizing, wrong slope, or missing traps
on vertical risers strand the oil in the evaporator and the compressor eventually seizes.**

---

## §3. ⚠️ Refrigerants — Properties and Classification

```
⚠️ NAMING  R-<number>. ⚠️ 400-series = ZEOTROPIC blends (components boil at
   different temperatures → GLIDE); 500-series = azeotropic;
   ⚠️ 600-series = organics (R-600a isobutane); 700-series = inorganic
   (R-717 ammonia, R-718 water, R-744 CO₂); ⚠️ R-1234xx = HFOs
⚠️ ASHRAE 34 SAFETY CLASSES
   TOXICITY  A (lower) · B (higher — ⚠️ ammonia is B)
   FLAMMABILITY  1 (none) · 2L (⚠️ MILDLY flammable, burning velocity
      <10 cm/s) · 2 (flammable) · 3 (⚠️ higher flammability — propane)
   ⚠️ So: R-410A = A1 · R-32 and R-454B = A2L · R-290 propane = A3 ·
      R-717 ammonia = B2L
⚠️ ODP  ozone depletion — CFCs and HCFCs, addressed by Montreal Protocol
⚠️ GWP  global warming potential — HFCs, addressed by Kigali/AIM/F-Gas (§25.1)
⚠️ GLIDE  ⚠️ zeotropic blends change temperature as they evaporate, which
   means you MUST charge them as LIQUID and cannot top up after a leak
   without risking fractionation
```
> **⚠️ GOTCHA — you cannot "drop in" a different refrigerant.** ⚠️ **Pressure-temperature
> relationships, oil compatibility (mineral oil for CFC/HCFC, POE for HFC/HFO), material
> compatibility, metering device sizing and system safety design all differ.** **⚠️ Putting
> an A2L into a system not designed and certified for it is unsafe and generally illegal
> — the equipment needs leak detection, specific electrical design, and charge limits per
> UL 60335-2-40** (§25.1 → `hvacr-reference`).

**⚠️ Natural refrigerants have real advantages and real constraints**: ⚠️ **CO₂ (R-744) is
non-toxic and non-flammable with negligible GWP but runs at very high pressure and goes
TRANSCRITICAL above ~31°C, which hurts efficiency in hot climates; ammonia (R-717) is the
most thermodynamically efficient common refrigerant and is toxic, so it's confined to
industrial plant with trained operators; propane (R-290) is excellent and flammable, so
it's limited to small sealed charges.**

---

## §4. Charge, Evacuation and Leaks

**⚠️ The three things that determine whether a system lasts**: ⚠️ **correct charge, a
properly evacuated system, and no moisture.**
**⚠️ Evacuation**: ⚠️ **pull to a deep vacuum (commonly targeted around 500 microns) and
perform a DECAY TEST with the pump isolated** — **a rising vacuum means either a leak or
remaining moisture boiling off.** **⚠️ Skipping evacuation leaves non-condensables and
water, which produces high head pressure and acid formation.**
**⚠️ Leak detection**: **electronic detectors, bubble solution, UV dye, nitrogen pressure
test (⚠️ NEVER pressure-test with oxygen — it reacts explosively with compressor oil;
never with the refrigerant itself, which is both illegal venting and expensive).**
**⚠️ Recovery is mandatory** — ⚠️ **venting refrigerant is illegal in most jurisdictions,
and larger systems face leak inspection and repair requirements** (§25.1 → `hvacr-reference`).

---

## §5. ⚠️ Diagnosis: Superheat and Subcooling

> **⚠️ These two measurements are how you see inside a sealed system, and everything else
> is guessing.**
```
⚠️ SUPERHEAT = actual suction line temp − saturation temp at suction pressure
   ⚠️ Tells you about the EVAPORATOR and the charge/metering
   ⚠️ LOW superheat  → too much refrigerant reaching the evaporator →
      RISK OF LIQUID RETURN TO THE COMPRESSOR (the destructive failure)
   ⚠️ HIGH superheat → refrigerant boiling off too early → undercharge,
      restriction, or a starved evaporator

⚠️ SUBCOOLING = saturation temp at liquid pressure − actual liquid line temp
   ⚠️ Tells you about the CONDENSER and the charge
   ⚠️ LOW subcooling  → undercharge, or condenser not condensing fully
   ⚠️ HIGH subcooling → overcharge, or liquid backing up (restriction)

⚠️ WHICH ONE TO CHARGE BY
   ⚠️ FIXED ORIFICE / CAPILLARY → charge by SUPERHEAT
   ⚠️ TXV / EEV → charge by SUBCOOLING (⚠️ the valve controls superheat,
      so superheat tells you about the VALVE, not the charge)
```
**⚠️ Common patterns:**
```
⚠️ High superheat + low subcooling      → UNDERCHARGE or leak
⚠️ Low superheat + high subcooling      → OVERCHARGE
⚠️ High superheat + high subcooling     → RESTRICTION (metering device, drier)
⚠️ Low superheat + low subcooling       → metering device overfeeding, or
                                          weak compressor
⚠️ High head pressure                   → dirty condenser, overcharge,
                                          non-condensables, high ambient
⚠️ Iced evaporator                      → low airflow (⚠️ FIRST suspect —
   dirty filter or coil), low charge, or low ambient operation
```
> **⚠️ GOTCHA — most "low on refrigerant" calls are airflow problems.** ⚠️ **A refrigerant
> system is SEALED; it does not consume refrigerant.** **If it's low, there is a LEAK, and
> topping it up without finding the leak is both a temporary fix and, for larger systems,
> a compliance failure.** **⚠️ Before adding refrigerant: check the filter, the coil, the
> blower and the ductwork.**

---

## §6. Other Cooling Approaches

```
⚠️ ABSORPTION  heat-driven rather than work-driven. LiBr/water (⚠️ chilled
   water only, above freezing) or ammonia/water. ⚠️ Poor COP but runs on
   WASTE HEAT or gas — economic where electricity is dear or heat is free
⚠️ EVAPORATIVE  ⚠️ limited by WET-BULB temperature (see a thermo reference's
   psychrometrics). Excellent in dry climates, useless in humid ones.
   ⚠️ Direct adds moisture; INDIRECT cools without adding it
⚠️ THERMOELECTRIC (Peltier)  ⚠️ no moving parts, no refrigerant, poor COP
   and limited capacity. Small coolers and precise spot cooling only
⚠️ DESICCANT  removes moisture chemically, then cool sensibly. ⚠️ Pairs well
   with evaporative and solves the humid-climate latent load problem (§9)
RADIATIVE / NIGHT-SKY · magnetocaloric and elastocaloric (⚠️ research stage)
⚠️ CRYOGENIC  liquid nitrogen and CO₂ for rapid freezing (§17) and for
   transport where mechanical refrigeration is impractical
```

---

# PART II — HVAC AND CLIMATE CONTROL
