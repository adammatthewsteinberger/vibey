---
name: hvacr-load-calculation-air-humidity-and-heat-pumps
description: "Use for HVAC design and troubleshooting: load calculation and why rule-of-thumb sizing fails, air distribution, duct sizing and static pressure, humidity control and the sensible versus latent split, ventilation and indoor air quality, heat pumps including cold-climate performance and defrost, controls and staging, and the building envelope that sets the load in the first place."
---

# Refrigeration and Climate Control: Load Calculation, Air Distribution, Humidity Control, Ventilation, Heat Pumps, Controls, and the Building Envelope

> **Part 2 of 5** of the *Refrigeration, AC, Climate Control and Food/Water Storage* reference (plugin `refrigeration-ac-climate-control-food-water`), covering §7–§13. Sibling skills: `hvacr-cycle-components-refrigerants-and-diagnosis` (§0–§6), `hvacr-cold-chain-temperature-limits-and-validation` (§14–§21), `hvacr-preservation-water-storage-and-treatment` (§22–§24), `hvacr-reference` (§25–§30). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 1. **⚠️ SUPERHEAT and SUBCOOLING are how you see inside a sealed system** (§5 → `hvacr-cycle-components-refrigerants-and-diagnosis`).
>    **Everything else in diagnosis is guessing.**
> 2. **⚠️ The cold chain is only as good as its worst link, and the worst link is almost
>    always a HANDOFF** (§15 → `hvacr-cold-chain-temperature-limits-and-validation`, §20 → `hvacr-cold-chain-temperature-limits-and-validation`). **Not the warehouse and not the truck — the dock, the
>    delay, the unmonitored gap.**
> 3. **⚠️ Preservation is about denying microbes ONE of their requirements** (§22 → `hvacr-preservation-water-storage-and-treatment`).
>    **Temperature is only one option; water activity, pH, oxygen and competition are the
>    others, and the durable methods stack several.**

---

## §7. Load Calculation

**⚠️ Sizing by rule of thumb is the most common and most damaging HVAC error.**
```
⚠️ SENSIBLE LOAD  temperature — conduction through envelope, solar gain,
   infiltration, internal gains (people, lighting, equipment)
⚠️ LATENT LOAD    moisture — occupants, infiltration, cooking, process
⚠️ SHR (sensible heat ratio) = sensible / total. ⚠️ THE number that
   determines whether equipment will control humidity (§9)
⚠️ DESIGN CONDITIONS  chosen percentile, not the record extreme —
   deliberately, because sizing for the worst hour ruins the other 8,759
⚠️ METHOD  ACCA Manual J (residential) / ASHRAE methods; ⚠️ Manual S for
   equipment selection and Manual D for ducts
```
> **⚠️ GOTCHA — an OVERSIZED air conditioner performs worse, not better, and this is
> counterintuitive to almost every homeowner.** ⚠️ **It satisfies the thermostat quickly and
> short-cycles, which means it never runs long enough to dehumidify** (§9) — **producing a
> cold, clammy building.** **⚠️ It also wears the compressor with frequent starts and
> delivers worse efficiency than its rating.** **⚠️ "Bigger to be safe" is exactly backwards.**

---

## §8. Air Distribution

**⚠️ Duct design**: **friction rate, equal friction and static regain methods, ⚠️ and the
fact that flexible duct has dramatically higher resistance than smooth metal — and
compressed or kinked flex is a common, invisible capacity killer.**
**⚠️ External static pressure is the vital sign of an air system** — ⚠️ **measure it; high
ESP means the blower is fighting the ductwork and airflow is below design, which shows up
as §5 → `hvacr-cycle-components-refrigerants-and-diagnosis`'s iced evaporator.**
**⚠️ Duct leakage in unconditioned space is a large and common loss**; **⚠️ sealing and
insulating ducts frequently beats equipment upgrades on cost-effectiveness.**
**⚠️ Return path matters as much as supply**: ⚠️ **a closed bedroom door with no return path
pressurizes the room, and the air finds its way out through the envelope.**
**Air changes per hour, throw and diffuser selection, balancing dampers, and ⚠️ VAV vs
constant volume.**

---

## §9. ⚠️ Humidity Control

**⚠️ The half of comfort that equipment sizing routinely ignores.**
```
⚠️ Cooling coils dehumidify by condensing moisture — which requires the
   coil surface to be BELOW the DEW POINT and requires RUN TIME
⚠️ SHORT CYCLING = NO DEHUMIDIFICATION (§7). This is the mechanism
⚠️ VARIABLE-SPEED equipment dehumidifies far better because it runs
   longer at lower capacity
⚠️ LOWER airflow across the coil = colder coil = MORE latent removal
   and less sensible capacity — the standard trade
⚠️ REHEAT  overcool to dehumidify, then reheat. Effective and energy-hungry
⚠️ DEDICATED DEHUMIDIFIER or DESICCANT for high latent loads
```
**⚠️ Target range roughly 40–60% RH**: ⚠️ **below ~30% causes static, respiratory
discomfort and wood shrinkage; above ~60% supports mould, dust mites and condensation.**
**⚠️ Condensation control is a building-physics problem**: ⚠️ **surfaces below the dew point
will wet, so the failure appears at thermal bridges, uninsulated pipes and window
frames** — **and the fix is usually insulation or ventilation, not a bigger AC.**
**⚠️ Condensate management**: ⚠️ **blocked drains and clogged traps cause a large share of
water-damage callbacks; float switches are cheap insurance.**

---

## §10. Ventilation and Indoor Air Quality

**⚠️ Ventilation dilutes; filtration removes; source control beats both.**
**Rates per ASHRAE 62.1/62.2; ⚠️ CO₂ as a PROXY for ventilation adequacy (⚠️ it's a
tracer for occupant-generated pollutants, not itself the hazard at typical indoor
levels), demand-controlled ventilation.**
**⚠️ Filtration**: **MERV and the equivalences to ISO/EN ratings; ⚠️ HEPA; and ⚠️ the
critical caveat that fitting a high-MERV filter to a system not designed for its pressure
drop reduces airflow and can cause §5 → `hvacr-cycle-components-refrigerants-and-diagnosis`'s problems.** **Check ESP after any filter upgrade.**
**⚠️ Energy recovery**: **HRV (sensible only) vs ERV (⚠️ sensible AND latent — usually the
right choice in humid climates).**
**⚠️ Legionella is the serious IAQ hazard in this domain**: ⚠️ **it grows in warm stagnant
water — cooling towers, hot water systems held between roughly 20–45°C, and dead legs in
plumbing.** **⚠️ Control is temperature (hot stored hot, cold kept cold), circulation, and
elimination of stagnation; ASHRAE 188 covers water management plans.**

---

## §11. Heat Pumps

**⚠️ A refrigeration cycle with a reversing valve — and the single most important point is
that COP above 1 is normal and does not violate anything** (see a thermo reference):
**you're moving heat, not making it.**
```
⚠️ COP falls as the temperature LIFT rises — which is why air-source
   performance degrades in cold weather
⚠️ COLD-CLIMATE models use vapour injection, variable speed and better
   controls; ⚠️ modern units maintain useful capacity well below 0°C,
   which is a genuine change from older equipment
⚠️ DEFROST  outdoor coil frosts below freezing; the unit periodically
   REVERSES to melt it. ⚠️ The steam and the temporary cold air are
   normal and are constantly misdiagnosed as faults
⚠️ BALANCE POINT  where capacity meets load; below it, supplementary heat
   ⚠️ RESISTANCE BACKUP has COP 1 — every hour it runs erases the savings.
   Controls that call it unnecessarily are the main cause of
   disappointing heat-pump bills
GROUND-SOURCE  ⚠️ much smaller lift, higher COP, high capital cost
```
**⚠️ The efficiency metrics** (SEER2, HSPF2, EER, COP) ⚠️ **are seasonal averages under
test conditions, and real performance depends heavily on installation quality, charge
(§5 → `hvacr-cycle-components-refrigerants-and-diagnosis`), airflow (§8) and controls.**

---

## §12. Controls

**⚠️ Thermostats and setpoints, deadband and hysteresis (⚠️ to prevent short cycling),
staging, setback (⚠️ genuinely effective for furnaces and AC; ⚠️ more nuanced for heat
pumps, where a deep setback triggers resistance backup on recovery and can cost more than
it saves).**
**⚠️ Building automation**: **BACnet and Modbus; sequences of operation; economizer control
(⚠️ "free cooling" when outdoor air is suitable — and a stuck economizer is one of the most
common and most expensive commercial faults, because it fails silently).**
**⚠️ Commissioning is the step that's skipped and shouldn't be** — ⚠️ **a correctly designed
system installed and left uncommissioned routinely underperforms its specification by a
wide margin.**

---

## §13. Building Envelope

**⚠️ The cheapest HVAC is the load you never have.**
**Insulation (R-value, ⚠️ and thermal bridging which defeats it locally), air sealing
(⚠️ usually more cost-effective per pound than added insulation), windows (U-factor,
SHGC — ⚠️ and SHGC matters more than U-factor in cooling-dominated climates), shading,
and thermal mass.**
**⚠️ Vapour control is climate-dependent and getting it wrong causes rot**: ⚠️ **the vapour
retarder goes on the WARM-IN-WINTER side in heating climates, and the logic inverts in
hot-humid climates — which is why a detail copied from the wrong climate zone traps
moisture inside the assembly.**

---

# PART III — THE COLD CHAIN
