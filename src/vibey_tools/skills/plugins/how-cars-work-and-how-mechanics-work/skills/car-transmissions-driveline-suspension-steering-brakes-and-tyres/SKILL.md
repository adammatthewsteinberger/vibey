---
name: car-transmissions-driveline-suspension-steering-brakes-and-tyres
description: "Use for the drivetrain and chassis: manual, torque-converter automatic, dual-clutch and CVT transmissions and how each fails, driveline and differentials including limited-slip and all-wheel drive, suspension geometry and damping, steering and alignment with camber, caster and toe, brakes including hydraulics, ABS and the real causes of judder and fade, and tyres — construction, compounds, ratings, pressure, and wear patterns read as a diagnostic."
---

# Cars and Mechanics: Transmissions, Driveline and Differentials, Suspension, Steering and Alignment, Brakes, and Tyres

> **Part 2 of 5** of the *How Cars Work — and How Mechanics Do Their Jobs* reference (plugin `how-cars-work-and-how-mechanics-work`), covering §10–§15. Sibling skills: `car-engine-cycle-fuel-ignition-management-and-emissions` (§0–§9), `car-electrical-networks-adas-ev-and-high-voltage-safety` (§16–§24), `car-diagnostic-method-obd-tools-and-shop-economics` (§25–§29), `car-reference` (§30–§35). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The mechanical fundamentals are a century settled. Two areas moved. See §30 → `car-reference` for right to repair and data access, and the technician skills gap.

> **⚠️ Two documents in one, deliberately.** **The machine (§1–§24 → `car-engine-cycle-fuel-ignition-management-and-emissions`, `car-electrical-networks-adas-ev-and-high-voltage-safety`) and the JOB (§25–§29 → `car-diagnostic-method-obd-tools-and-shop-economics`).**
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

## §10. Transmissions

```
⚠️ MANUAL  clutch (⚠️ friction disc, pressure plate, release bearing —
   and the flywheel, often dual-mass and a wear item itself), synchros
⚠️ TORQUE-CONVERTER AUTOMATIC  ⚠️ the converter is a FLUID coupling that
   also MULTIPLIES torque at stall; ⚠️ the lock-up clutch eliminates
   slip at cruise, and a shuddering lock-up clutch is often
   misdiagnosed as an engine misfire (§28)
⚠️ CVT  belt/chain and variable pulleys. ⚠️ Fluid-specific and
   intolerant of the wrong fluid; the "rubber band" feel is inherent
⚠️ DCT  two clutches, pre-selected gears. ⚠️ Fast, and low-speed
   creep behaviour is a common complaint rather than a fault
⚠️ FLUID  ⚠️ transmission fluid is a HYDRAULIC and FRICTION-MODIFYING
   fluid, not just a lubricant. ⚠️ The wrong spec causes shift
   problems that look mechanical
```
**⚠️ The "sealed for life" claim**: ⚠️ **fluid degrades regardless of the label, and many
transmission failures trace to never-changed fluid.** **⚠️ The genuine caveat: changing very
old, badly degraded fluid in a high-mileage unit can precipitate failure — not because the
new fluid is harmful but because the worn clutches were relying on the degraded fluid's
friction characteristics.**

---

## §11. Driveline and Differentials

**Driveshafts, CV joints (⚠️ a clicking on turns is the classic outer CV symptom, and a
torn boot is the cause — grease out, dirt in), U-joints, ⚠️ and the differential, which
exists because the outside wheel travels further in a corner.**
**⚠️ Open vs limited-slip vs locking; ⚠️ AWD versus 4WD (part-time 4WD has NO centre
differential and must not be used on high-traction surfaces — driveline windup), and
transfer cases.**
**⚠️ Tyre size matching matters on AWD**: ⚠️ **mismatched circumferences force continuous
differential action and can destroy a transfer case or coupling** — **which is why AWD cars
often require replacing tyres in fours** (§15).

---

# PART II — CHASSIS

## §12. Suspension

**⚠️ Its job: keep the tyre in contact with the road while isolating the body.**
```
SPRINGS  carry the load and set ride height
⚠️ DAMPERS (shocks/struts)  ⚠️ control OSCILLATION, not ride height.
   ⚠️ Worn dampers cause float, nose dive, and — importantly —
   longer braking distances and tyre cupping
⚠️ BUSHINGS  ⚠️ the most commonly overlooked wear item. Worn bushings
   cause clunks, alignment drift and vague handling
ANTI-ROLL BAR + links (⚠️ end links are a very common rattle source)
TYPES  MacPherson strut · double wishbone · multi-link · live axle ·
   air suspension (⚠️ compressor and bag failures are expensive)
```
**⚠️ Diagnosis by noise is genuinely informative**: ⚠️ **clunk over bumps → links, bushings
or ball joints; knock on turning → CV or strut mount; squeak → bushings; and a repeated
"cupping" wear pattern on the tyre points at dampers** (§15).

---

## §13. Steering and Alignment

**Rack and pinion; ⚠️ hydraulic, electro-hydraulic and now electric power steering (EPS),
⚠️ which is what makes lane-keep assist possible** (§18 → `car-electrical-networks-adas-ev-and-high-voltage-safety`).
```
⚠️ ALIGNMENT ANGLES
   ⚠️ TOE   the biggest cause of rapid tyre wear. ⚠️ Also the easiest
      to knock out and the cheapest to fix
   ⚠️ CAMBER  wear on one edge; affects cornering grip
   ⚠️ CASTER  straight-line stability and self-centring; ⚠️ uneven
      caster causes pull
   ⚠️ THRUST ANGLE  rear axle direction — ⚠️ causes "dog tracking"
      and a crooked steering wheel that a front-only alignment
      will never fix
```
**⚠️ A pull is not automatically an alignment fault**: ⚠️ **tyre conicity, uneven pressures,
a dragging brake, or a worn bushing all pull.** **⚠️ Swapping the front tyres side to side
is a free test that isolates tyre-caused pull.**

---

## §14. Brakes

**⚠️ Hydraulic force multiplication: master cylinder → lines → calipers; ⚠️ the vacuum or
electric booster provides assist, so a hard pedal often means a booster or vacuum supply
problem, not a brake problem.**
```
⚠️ BRAKE FLUID IS HYGROSCOPIC — it absorbs water from the air, which
   lowers its boiling point. ⚠️ Under heavy braking the water boils,
   the vapour compresses, and THE PEDAL GOES TO THE FLOOR.
   ⚠️ THIS is why brake fluid has a time-based service interval
   regardless of mileage, and why it is so often skipped
⚠️ FADE  pad fade (friction falls with temperature) vs the fluid
   boiling above. Different causes, similar feel
⚠️ WARPED ROTORS  ⚠️ usually NOT warped. Almost always uneven pad
   material TRANSFER or thickness variation. Judder from DTV
⚠️ ABS  prevents lock-up by modulating; ⚠️ the wheel speed sensors it
   uses also feed traction control, stability control and ADAS (§18)
⚠️ EPB  electric park brakes must be put in SERVICE MODE with a tool
   before pad replacement — force the piston back mechanically and
   you destroy the actuator
```
**⚠️ Regenerative braking on hybrids and EVs** (§23 → `car-electrical-networks-adas-ev-and-high-voltage-safety`) ⚠️ **means friction brakes are used
little and can SEIZE from corrosion** — **a genuinely different failure mode.**

---

## §15. ⚠️ Tyres

**⚠️ Everything the car does — accelerate, brake, corner — happens through four contact
patches roughly the size of a hand. ⚠️ Tyres are the highest-leverage component on the
vehicle and the most neglected.**
```
⚠️ SIDEWALL  225/45R17 94V → width mm / aspect % / radial / rim inch /
   load index / ⚠️ SPEED RATING
⚠️ DOT DATE CODE  last four digits = week and year. ⚠️ Rubber AGES;
   many manufacturers advise replacement at 6–10 years regardless of tread
⚠️ PRESSURE  ⚠️ use the DOOR JAMB placard, NOT the number on the tyre
   sidewall (that is the tyre's MAXIMUM, not the vehicle's spec).
   ⚠️ This is one of the most common consumer errors
⚠️ WEAR PATTERNS DIAGNOSE THE CAR
   Both edges → underinflation · Centre → overinflation
   ⚠️ One edge → camber · ⚠️ Feathering/sawtooth → TOE
   ⚠️ Cupping/scalloping → worn dampers (§12)
TPMS  ⚠️ direct sensors need relearn/registration after replacement
```
**⚠️ Tread depth and wet grip**: ⚠️ **tread exists to evacuate water; a legal-but-low tread
has dramatically longer wet stopping distances than new.** **Aquaplaning risk rises sharply
as depth falls.**

---

# PART III — ELECTRICAL AND ELECTRONIC
