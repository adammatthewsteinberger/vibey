---
name: maker-networking-enclosures-and-productization
description: "Use when connecting a project to a network or home automation, packaging it, or turning it into a product: WiFi, BLE and LoRa, MQTT, Home Assistant and ESPHome, enclosures, 3D printing and fabrication, the honest prototype-to-product path including certification and manufacturing, and buying and sourcing parts including clones and counterfeits."
---

# DIY Kit Dev: Networking, Enclosures, Prototype to Product, and Sourcing

> **Part 4 of 5** of the *DIY Kit Dev* reference (plugin `diy-kit-dev`), covering §11–§14. Sibling skills: `maker-boards-and-platforms` (§0–§3), `maker-power-electronics-and-io` (§4–§7), `maker-software-build-and-debug` (§8–§10), `maker-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 → `maker-reference` for the currency snapshot and what goes stale first.

> **How to read this.** Reference for making things, aimed at software engineers who want
> to build hardware. Deliberately complementary to a professional embedded/IoT reference —
> **that** covers industrial-grade firmware, RTOS, certification, and fleet management;
> **this** covers getting a thing working on your desk, and what it takes to make it
> reliable enough to leave running.
>
> Three markers:
> - **[DURABLE]** — physics, electronics, and build craft. Doesn't expire.
> - **[VERSIONED]** — boards, chips, prices, ecosystem. Verify.
> - **[CONTESTED]** — genuine disagreement.
>
> **⚠️ GOTCHA** boxes mark the things that destroy hardware, waste weekends, or cause the
> intermittent fault you'll chase for a month.
>
> **The three framings that organize everything below:**
> 1. **Pick the smallest board that does the job.** The instinct is to reach for a Linux
>    SBC because it's familiar. **A microcontroller that boots in 50ms, draws 20mA, and
>    never corrupts an SD card is the right answer far more often than a Pi is** (§1 → `maker-boards-and-platforms`).
> 2. **⚠️ It's the power supply.** When something works on the bench and fails in the
>    field, when a board reboots randomly, when Wi-Fi drops under load, when readings
>    drift — **check power first, second, and third** (§4 → `maker-power-electronics-and-io`). This one heuristic will save
>    you more time than everything else in this document.
> 3. **The last 10% is 90% of the work.** A breadboard demo is a weekend. **Something that
>    survives a year in a garage, on a windowsill, or outdoors is a different project** —
>    enclosure, power, moisture, thermal, watchdog, recovery, and update (§13). Know which
>    one you're signing up for.

---

## §11. Networking and Home Automation

**Protocols**: **Wi-Fi** (easy, power-hungry), **BLE** (low power, short range),
**Zigbee** and **Thread** (mesh, low power, ⚠️ **need a coordinator/border router**),
**Matter** (⚠️ **the cross-vendor standard — an ESP32-C6 or H2 is the hobbyist path in**),
**LoRa / LoRaWAN** (⚠️ **kilometres of range at very low data rates — the right answer for
remote sensors**), **ESP-NOW** (⚠️ **Espressif's connectionless peer-to-peer protocol —
fast, no router needed, excellent for sensor→hub links**), **MQTT** (the default
application protocol for this world).

**[DURABLE] Home Assistant is the centre of gravity for hobbyist home automation**, and
**ESPHome** integrates with it so tightly that a sensor node becomes a YAML file. **If
you're building anything sensor-and-automation shaped, look there before writing code.**
**Node-RED** for flow-based logic; **InfluxDB + Grafana** for time-series and dashboards;
**Zigbee2MQTT** for bringing commercial Zigbee devices under your own control.

> **⚠️ GOTCHA — security, briefly but seriously.** Hobby IoT devices are notoriously bad,
> and yours will be too unless you decide otherwise. **The minimum: put them on a separate
> VLAN or guest network; don't port-forward anything to the internet (use a VPN or
> Tailscale); change default credentials; don't hardcode Wi-Fi passwords into code you'll
> push to GitHub** (⚠️ **this happens constantly — use a secrets file and gitignore it**);
> **prefer local control over cloud dependency**; and **have an update path** (§13).

---

## §12. Enclosures and Fabrication

**3D printing** — **PLA** (easy, ⚠️ **deforms in a hot car or direct sun**), **PETG**
(⚠️ **the right default for enclosures** — tougher, more heat-resistant, still easy),
**ABS/ASA** (outdoor and heat, needs an enclosed printer), **TPU** (flexible).
**Design for printing**: avoid overhangs beyond ~45°, add clearance for fit
(⚠️ **0.2–0.4mm for parts that must slide together — printers are not precise**), use
**heat-set inserts** rather than tapping plastic for anything that comes apart repeatedly.

**Also**: **laser cutting** (fast, flat, excellent for panels), **CNC**, and
**off-the-shelf project boxes** — ⚠️ **which are underrated; a $5 ABS box and a step drill
beats three failed print iterations.**

**⚠️ For anything outdoors**: **IP-rated enclosure**, **cable glands** (not holes),
**drainage** (⚠️ **condensation forms inside sealed boxes — a weep hole at the bottom is
standard practice**), **UV-resistant material**, and **desiccant packs**. **Weatherproofing
is the thing that most often turns a working project into a dead one after three months.**

---

## §13. Prototype → Product

**[DURABLE] Be honest about which you're doing**, because the gap is enormous and mostly
invisible from the prototype side.

**The reliability layer a permanent installation needs:**
- **⚠️ Watchdog timer.** The device must recover from a hang without you visiting it.
- **Recovery from power loss** — resume state, don't require a button press.
- **Brownout detection** and sane behaviour on marginal power.
- **OTA updates.** ⚠️ **Firmware you can't update is firmware you'll have to physically
  retrieve.**
- **Failsafes** — what happens when Wi-Fi is down, the sensor is disconnected, or the
  server is unreachable? **Default to safe, not to last-known.**
- **Observability** — heartbeat, uptime, error counters, firmware version.
- **Thermal margin** and **conformal coating** for damp environments.

**Custom PCBs** — **KiCad** (free, excellent, now the default) or EasyEDA; **JLCPCB,
PCBWay, OSH Park, Aisler** for fabrication. ⚠️ **Five boards for ~$5 plus shipping is
genuinely accessible**, and **assembly services (JLCPCB's) will place parts for you**,
which changes what's feasible for a small run. **Expect two or three revisions** — order
the cheap prototypes early.

**Going to volume** — the things that surprise software people: **certification** (FCC/CE
for anything with a radio — ⚠️ **using a pre-certified module rather than a bare chip is
the single biggest cost saver**, §3.3 → `maker-boards-and-platforms`), **safety certification** for mains,
**RoHS/REACH/WEEE**, **⚠️ the EU Cyber Resilience Act** which now imposes security
obligations on connected products, **component lifecycle and second sources**,
**manufacturing test fixtures**, **support and returns**, and **the CM4/CM5 or a
module-based design** as the route to a Pi-based product.

**⚠️ And the honest warning: hardware margins are thin, iteration is slow and expensive,
and inventory is real money sitting in a box.** A great prototype is not a business.

---

## §14. Buying and Sourcing

**Suppliers**: **Adafruit** and **SparkFun** (⚠️ **more expensive, and the documentation
and tutorials are the actual product — worth it while learning**), **Pimoroni** (UK),
**Mouser / Digi-Key / RS / Farnell** (components proper, genuine parts, real datasheets),
**AliExpress / LCSC** (⚠️ **cheap, slow, variable — fine for passives and modules, risky
for critical ICs**), **Seeed**, **Waveshare**, **Core Electronics**, **The Pi Hut**.

> **⚠️ GOTCHA — counterfeits and fakes are endemic at the cheap end**, and they cost more
> time than money. The recurring ones: **fake FTDI and CH340 USB-serial chips** (drivers
> may refuse them), **relabelled or lower-grade ICs**, **SD cards reporting far more
> capacity than they have** (⚠️ **test any cheap card with `f3` or H2testw before trusting
> data to it**), **18650 cells with impossible capacity claims** (§4.3 → `maker-power-electronics-and-io`), and **power
> supplies that don't deliver rated current** or lack real isolation.
>
> **The rule: buy passives and generic modules cheaply, buy anything critical — ICs,
> power supplies, lithium cells, SD cards — from a reputable distributor.**

**[DURABLE] Buy a starter kit for your first project.** A decent Arduino or Pi kit with
assorted resistors, LEDs, jumpers, sensors, and a breadboard removes the friction of
discovering mid-project that you don't own a 220Ω resistor. **Then buy an assortment box
of resistors, capacitors, and headers** — you'll use them forever.
