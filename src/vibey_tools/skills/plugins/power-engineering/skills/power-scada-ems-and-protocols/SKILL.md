---
name: power-scada-ems-and-protocols
description: "Use when integrating with grid control systems: SCADA, energy management systems and distribution management systems and what each actually does, and the protocols including DNP3, IEC 61850, IEC 60870-5 and Modbus with their data models, timing and security characteristics."
---

# Power Engineering: SCADA, EMS and DMS, and the Protocols

> **Part 3 of 5** of the *Power Engineering* reference (plugin `power-engineering`), covering §6–§7. Sibling skills: `power-ac-fundamentals-generation-and-grid` (§0–§3), `power-system-analysis-and-protection` (§4–§5), `power-inverters-storage-markets-and-datacenters` (§8–§12), `power-reference` (§13–§18). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Circuit theory and power system analysis are settled; the inverter-dominated grid and datacenter load growth moved fast. See §15 → `power-reference` for both, dated.

> **Scope.** Complements an electrical-engineering reference, which is circuit-level —
> components, op-amps, PCB layout, signal integrity. ⚠️ **This is grid scale: kilovolts
> and megawatts, and the software that runs it.**
>
> **⚠️ GOTCHA** boxes mark what kills people, destroys equipment, or causes blackouts.
>
> **The three ideas that organize the whole field:**
> 1. **⚠️ Generation must equal load, continuously, everywhere.** The grid stores almost
>    nothing. **Frequency IS the balance signal** — it falls when load exceeds generation
>    and rises when it doesn't, in real time, across a continent (§1.4 → `power-ac-fundamentals-generation-and-grid`).
> 2. **⚠️ Reactive power is not "wasted" power — it's a separate commodity that must also
>    balance, and it's local.** Real power flows across a system; reactive power doesn't
>    travel well, so voltage is a local problem and frequency is a global one (§1.2 → `power-ac-fundamentals-generation-and-grid`).
> 3. **⚠️ Protection is the fastest software in the system and it acts on trust.** A relay
>    decides in milliseconds to disconnect equipment, and it must be right — a false trip
>    causes an outage, a missed trip destroys equipment or kills someone (§5 → `power-system-analysis-and-protection`).

---

## §6. SCADA, EMS, and DMS

```
Field:  sensors, CTs/VTs, IEDs, relays, RTUs
   ↓ (§7 protocols)
SCADA:  acquisition, alarms, supervisory control, historian
   ↓
EMS (transmission):  state estimation, contingency analysis, OPF, AGC, dispatch
DMS (distribution):  fault location/isolation/restoration (FLISR), volt/VAr,
                     outage management, DERMS
   ↓
Markets (§10), planning, asset management
```
**⚠️ Contingency analysis is the control room's core loop**: continuously simulate
**"what if this element fails?"** across a large list, and confirm the system stays within
limits. **The `N−1` criterion means operating so that any single failure is survivable** —
⚠️ **so the grid is deliberately run below its physical capability, always.**

**⚠️ The operator is the user, and the design constraints are unusual**: alarm floods
during a real event are a documented contributor to blackout escalation; the system must
degrade legibly; and ⚠️ **the software's job during a crisis is to reduce the number of
things a human must decide, not to present more information.**

---

## §7. Protocols

| Protocol | Domain | ⚠️ Notes |
|---|---|---|
| **Modbus** | Ubiquitous, simple | ⚠️ **No security whatsoever. Assume it's plaintext and trusted-by-position** |
| **DNP3** | ⚠️ **North American SCADA standard** | Event-driven with timestamps and quality flags; **Secure Authentication exists — use it** |
| **IEC 60870-5-101/104** | European SCADA equivalent | 104 is the TCP/IP variant |
| **IEC 61850** | ⚠️ **Substation automation, and the modern one** | Object model + SCL config; **GOOSE** and **Sampled Values** |
| **IEC 61970/61968 CIM** | ⚠️ **Network model exchange** | The semantic model behind EMS/DMS interoperability |
| **IEEE C37.118 / IEEE 2664** | Synchrophasors | PMU streaming (§4.2 → `power-system-analysis-and-protection`) |
| **OpenADR, IEEE 2030.5** | Demand response, DER | Utility-to-customer |
| **OPC UA** | Industrial | Increasingly a bridge layer |

**⚠️ IEC 61850 GOOSE deserves specific attention**: it's a **multicast layer-2 publish/
subscribe message for protection signalling with a ~4 ms delivery requirement.** ⚠️ **It
retransmits with decreasing intervals to survive loss, and it bypasses the IP stack
entirely — so ordinary network engineering intuitions do not apply.** **Sampled Values
(SV)** streams digitized CT/VT waveforms at high rate, ⚠️ **which turns substation
protection into a hard-real-time networking problem and makes PTP time synchronization
safety-relevant.**

> **⚠️ GOTCHA — nearly all of these protocols were designed for physically isolated
> networks and have no meaningful authentication by default.** **Security in this domain
> is overwhelmingly perimeter- and segmentation-based** (§11.2 → `power-inverters-storage-markets-and-datacenters`). ⚠️ **Never assume a
> protocol validates who sent a command.**
