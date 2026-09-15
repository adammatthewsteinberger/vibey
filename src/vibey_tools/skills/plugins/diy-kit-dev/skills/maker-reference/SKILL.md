---
name: maker-reference
description: "Use when checking a maker hardware anti-pattern, weighing a contested question, confirming whether a board lineup or ecosystem claim is still current (snapshot verified August 2026), finding the books, sites and channels, or needing the board picker, the numbers worth remembering, and the what-to-check list for when it doesn't work. Companion to the other diy-kit-dev skills."
---

# DIY Kit Dev: Anti-Patterns, Contested Questions, Currency, and Canon

> **Part 5 of 5** of the *DIY Kit Dev* reference (plugin `diy-kit-dev`), covering §15–§20. Sibling skills: `maker-boards-and-platforms` (§0–§3), `maker-power-electronics-and-io` (§4–§7), `maker-software-build-and-debug` (§8–§10), `maker-networking-enclosures-and-productization` (§11–§14). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 below for the currency snapshot and what goes stale first.

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
>    enclosure, power, moisture, thermal, watchdog, recovery, and update (§13 → `maker-networking-enclosures-and-productization`). Know which
>    one you're signing up for.

---

## §15. Anti-Patterns

| Anti-pattern | Why |
|---|---|
| Reaching for a Pi when an MCU would do | Boot time, power, SD corruption, no real-time (§1 → `maker-boards-and-platforms`) |
| Reaching for an MCU when you need Linux | Fighting the platform (§1 → `maker-boards-and-platforms`) |
| **Not checking power first** | ⚠️ **The most common root cause of everything** (§4 → `maker-power-electronics-and-io`) |
| Powering motors or servos from the board regulator | ⚠️ **The classic destruction** (§4.1 → `maker-power-electronics-and-io`) |
| Sizing the supply for average, not peak | Brownouts that look like software bugs (§4.1 → `maker-power-electronics-and-io`) |
| No decoupling capacitors | "Random reboots" and flaky sensors (§4.1 → `maker-power-electronics-and-io`) |
| Separate supplies without common ground | Nothing works, signals float (§4.1 → `maker-power-electronics-and-io`) |
| Assuming the USB cable is fine | ⚠️ Charge-only and thin cables cause under-voltage (§4.1 → `maker-power-electronics-and-io`) |
| 5V signal into a 3.3V pin | Destroys the part. Level-shift (§4.2 → `maker-power-electronics-and-io`) |
| LED without a current-limiting resistor | Burns out. Every time (§5 → `maker-power-electronics-and-io`) |
| Floating input instead of a pull-up/pull-down | ⚠️ **Not "low" — random** (§5 → `maker-power-electronics-and-io`) |
| No flyback diode on a motor/relay/solenoid | ⚠️ Kills the driver transistor (§5 → `maker-power-electronics-and-io`) |
| Not debouncing a mechanical switch | One press reads as several (§6 → `maker-power-electronics-and-io`) |
| Trusting a cheap sensor's absolute reading | Accurate relatively, wrong absolutely (§6 → `maker-power-electronics-and-io`) |
| Treating a disconnected sensor's 0 as real | ⚠️ **Failures read as plausible values** (§6 → `maker-power-electronics-and-io`) |
| Resistive soil moisture sensors | Corrode away in weeks (§6 → `maker-power-electronics-and-io`) |
| Believing "eCO₂" is CO₂ | It's a VOC-based estimate (§6 → `maker-power-electronics-and-io`) |
| Undersizing LED strip power | ~60mA/pixel at white; 300 LEDs ≈ 18A (§7 → `maker-power-electronics-and-io`) |
| **Breadboarding mains voltage** | ⚠️ **Different category of risk** (§7 → `maker-power-electronics-and-io`) |
| Charging LiPo unattended on a flammable surface | ⚠️ **The one fire risk here** (§4.3 → `maker-power-electronics-and-io`) |
| `delay()` in anything that must stay responsive | Blocks everything (§8 → `maker-software-build-and-debug`) |
| Wi-Fi credentials committed to GitHub | ⚠️ Happens constantly (§11 → `maker-networking-enclosures-and-productization`) |
| No watchdog on a permanent installation | You'll be visiting it (§13 → `maker-networking-enclosures-and-productization`) |
| No OTA update path | You'll be physically retrieving it (§13 → `maker-networking-enclosures-and-productization`) |
| Assuming a working prototype is nearly a product | ⚠️ **The last 10% is 90%** (§13 → `maker-networking-enclosures-and-productization`) |
| Permanent project left on a breadboard | Intermittent contact faults forever (§9.1 → `maker-software-build-and-debug`) |
| Not documenting the pinout as you build | You won't remember in six months (§9.3 → `maker-software-build-and-debug`) |
| Signal wires bundled with motor wires | Coupled noise you'll blame on software (§9.3 → `maker-software-build-and-debug`) |
| Sealed outdoor enclosure with no drainage | ⚠️ **Condensation forms inside** (§12 → `maker-networking-enclosures-and-productization`) |
| PLA enclosure in direct sun or a car | Deforms. Use PETG (§12 → `maker-networking-enclosures-and-productization`) |
| Trusting an untested cheap SD card | ⚠️ Test with `f3`/H2testw first (§14 → `maker-networking-enclosures-and-productization`) |
| Buying critical ICs or power supplies from the cheapest source | Counterfeits (§14 → `maker-networking-enclosures-and-productization`) |
| Adopting a brand-new chip before toolchain support lands | ⚠️ **Pre-production silicon isn't hobby-ready** (§3.3 → `maker-boards-and-platforms`) |
| Debugging code before verifying power, ground and connections | Wrong order (§10 → `maker-software-build-and-debug`) |
| Hot-plugging sensors onto a powered board | Voltage on a pin before ground connects (§10 → `maker-software-build-and-debug`) |

---

## §16. Contested Questions

**16.1 Arduino or ESP32 for a beginner?** *Arduino Uno*: 5V-tolerant and hard to destroy,
every tutorial targets it, no Wi-Fi to complicate things. *ESP32*: vastly more capable for
the same money, Wi-Fi built in, and you won't outgrow it in a month. **[CONTESTED. The
defensible split: Uno if you're learning electronics; ESP32 if you're a software engineer
who wants a connected thing working this weekend.]**

**16.2 Does the Qualcomm acquisition matter?** §3.1 → `maker-boards-and-platforms`. **Genuinely unresolved.** Nothing has
broken; the commitments are stated; the community is skeptical and the skepticism isn't
unreasonable given the T&C episode. **The practical hedge is platform diversity, not
panic.**

**16.3 MicroPython or C/C++?** *Python*: faster iteration, REPL, lower barrier, and
adequate for most sensor-and-network work. *C/C++*: performance, memory, real-time, full
library access, and where production ends up. **Most projects never need C. Some can't
work without it.**

**16.4 Raspberry Pi or the alternatives?** §2.3 → `maker-boards-and-platforms`. Better specs per dollar elsewhere;
**Pi's advantage is ecosystem, documentation, and long-term availability**, and for
beginners that dominates.

**16.5 Should hobbyists design PCBs?** *For*: cheap, reliable, compact, and KiCad is free
and good. *Against*: real learning curve, and three revisions of shipping delay.
**⚠️ Worth it once you're building more than one of something, or once wiring reliability
is the limiting factor.**

**16.6 Is the maker movement in decline?** ⚠️ **Genuinely contested.** *For decline*: the
2010s peak has passed, Maker Media's difficulties, cheap finished products undercutting
DIY. *Against*: 3D printing is far cheaper and better, board capability has exploded,
Home Assistant and ESPHome created a huge new practical use case, and the barrier to a
custom PCB has collapsed. **The character changed more than the size.**

---

## §17. Currency Snapshot — verified August 2026

**[DURABLE] The electronics fundamentals (§4 → `maker-power-electronics-and-io`, §5 → `maker-power-electronics-and-io`, §9 → `maker-software-build-and-debug`, §10 → `maker-software-build-and-debug`) have not changed in decades
and won't.** What follows is the part that moves.

| Thing | Status as of Aug 2026 | Decay risk |
|---|---|---|
| **⚠️ Qualcomm–Arduino** | **Announced 7 October 2025**, subject to regulatory approval; terms undisclosed. Arduino to remain an **independent brand supporting multiple silicon vendors**. Launched alongside the **UNO Q** — **"dual brain": Qualcomm Dragonwing QRB2210 running Debian Linux + an STMicro MCU**, with **Edge Impulse** for edge AI and **Arduino App Lab**. ⚠️ **First UNO-family board that is a standalone SBC rather than an MCU dev board.** Builds on Qualcomm's Edge Impulse and Foundries.io acquisitions. Arduino cited **33M active users** | Low (event) |
| **⚠️ Community reaction** | **Openly skeptical** — IEEE Spectrum: *"Qualcomm Buys Arduino, and the Open-Source Community Is Skeptical."* Adafruit noted **Arduino and Qualcomm did not respond to inquiries over several months** and read the "community trust"/"heritage" language as **defensive framing**. **Flashpoint: a T&C change read as locking down previously-open software/hardware** — **Arduino says that reading was incorrect** and held an AMA (with Qualcomm, Edge Impulse, STMicro) reasserting **"100% commitment"** to open source and continued non-Qualcomm partnerships. ⚠️ **Where it lands is not yet knowable** | Medium |
| **Raspberry Pi lineup** | **Pi 5** flagship (BCM2712, PCIe/NVMe, wants 5V/5A + active cooling). **Pi 4B** still current-ish. **Zero 2 W** the value pick — beats a 3B for less. **Pi 500** (Pi 5 in a keyboard, 8 GB); **Pi 500+ (Sept 2025, ~$200): 16 GB RAM, 256 GB NVMe, mechanical keyboard**. **CM5** for embedding. **Pi 1/2/3 not worth buying new** | Medium |
| **Pico / RP2350** | **Pico 2 / 2 W: RP2350, dual Cortex-M33 @ 150 MHz with FP and DSP, from $5**; W adds Wi-Fi + **BT 5.2**. **Chips sold separately: RP2350A ~$1.10, RP2350B ~$1.20 singly; ~$0.80–0.90 on reels.** **RP2354** variants add 2 MB stacked flash | Medium |
| **ESP32 family** | ⚠️ **Roughly a dozen variants now.** **S3** = best hobbyist all-rounder (Xtensa dual 240 MHz, 128-bit SIMD for wake-word/vision, USB, camera/LCD). **C3** = cheap RISC-V. **C6** = Wi-Fi 6 + BLE + 802.15.4 → **Thread/Zigbee/Matter; the pick for net-new battery sensors**. **H2** = 802.15.4-only Matter-over-Thread. **P4** = dual RISC-V 400 MHz, MIPI CSI/DSI, **H.264 1080p30, up to 32 MB PSRAM, ⚠️ no wireless — needs a C5/C6 companion** | **High** |
| **⚠️ New-silicon caution** | Newer parts (S31, C61, H21 and others announced through 2026) may be **pre-production, without official modules, and unsupported in Arduino-ESP32 or MicroPython**, while established parts have **abundant module stock, lowest price, most stable supply, richest community support.** **Check toolchain support first** | **High** |
| **Toolchains** | **ESP32 Arduino Core 3.1.x** (Jan 2026) covers ESP32/S3/C6 with full BLE 5 + Wi-Fi 6 on newer chips; the popular libraries "just work." **Pico W Arduino core (Philhower) stable**, though with fewer complex libraries. **MicroPython 1.27.0 (Dec 2025)**, with ESP32-P4 builds including C5/C6-coprocessor variants. **CircuitPython** actively developed; Matter/Thread support constrained by needing C SDK linkage | Medium |
| **Supply chain** | Reported as **stable in 2026**, having recovered from 2024 disruptions around newly-introduced parts (ESP32-P4, Pico 2 W). ESP32 modules in mass production; Pico W stock steady | Medium |

**Goes stale fastest:** §3.3 → `maker-boards-and-platforms`'s ESP32 variant table and §2.1 → `maker-boards-and-platforms`'s lineup. **Essentially never
stale:** §4 → `maker-power-electronics-and-io`, §5 → `maker-power-electronics-and-io`, §6 → `maker-power-electronics-and-io`'s practices, §9 → `maker-software-build-and-debug`, §10 → `maker-software-build-and-debug`, §15.

---

## §18. The Canon

### 18.1 Books

| Author | Work | Why |
|---|---|---|
| **Platt** | ***Make: Electronics*** (3rd ed.) | ⚠️ **The best beginner electronics book, by a distance.** Learn-by-destroying-things |
| **Platt** | *Encyclopedia of Electronic Components* (3 vols) | "What is this part and how do I use it?" |
| **Scherz & Monk** | *Practical Electronics for Inventors* | The step up. Comprehensive |
| **Horowitz & Hill** | ***The Art of Electronics*** (3rd ed.) | The bible. ⚠️ Not a beginner book, and worth owning anyway |
| **Monk** | *Programming Arduino*; *Raspberry Pi Cookbook* | Practical and reliable |
| **Blum** | *Exploring Arduino* | Good bridge from blinking to building |
| **Williams** | *Make: AVR Programming* | When you want to know what Arduino is hiding |
| **Nussey** | *Arduino For Dummies* | Genuinely fine, despite the title |

### 18.2 Sites and documentation
**Adafruit Learn** (⚠️ **the best free tutorial library in this space, and the reason
Adafruit's premium is worth paying while learning**), **SparkFun tutorials**,
**Raspberry Pi documentation** (⚠️ **the RP2040/RP2350 datasheets and the Pico SDK book
are unusually good technical writing**), **Espressif ESP-IDF docs**, **Arduino Docs and
Language Reference**, **Hackaday** (news and inspiration), **Hackster.io** (project
sharing), **Instructables** (⚠️ variable quality — verify before following),
**Home Assistant** and **ESPHome** docs, **Everything ESP32** and **RandomNerdTutorials**
(⚠️ **the most reliable ESP32 tutorial source**), **/r/arduino**, **/r/raspberry_pi**,
**/r/esp32**, **/r/AskElectronics** (⚠️ **read the rules; it's a good resource that
punishes low-effort questions**), **EEVblog forum**.

### 18.3 People and channels
**Dave Jones** (**EEVblog** — ⚠️ **the best electronics teardown and test-gear education
anywhere, and refreshingly willing to call out bad design**), **Bill Hammack**
(**engineerguy** — beautiful explanations of how things work), **Andreas Spiess**
(⚠️ **"the guy with the Swiss accent" — rigorous, measurement-driven ESP32 and IoT
content; unusually honest about what doesn't work**), **DroneBot Workshop** (thorough,
patient, excellent selection guides), **Great Scott**, **bigclivedotcom** (⚠️ **teardowns
of cheap and dangerous mains devices — genuinely educational about what not to buy**),
**Ben Eater** (⚠️ **breadboard computers from first principles — the best digital-logic
education on the internet**), **Limor "Ladyada" Fried** and **Phillip Torrone**
(Adafruit), **Naomi Wu**, **Jeff Geerling** (⚠️ **the most rigorous Raspberry Pi
benchmarking and testing available**), **Paul Stoffregen** (Teensy), **Rui Santos**
(RandomNerdTutorials), **Michael Klements**, **Marco Reps** and **Zach Freedman**
(fabrication and design).

---

## §19. Quick Reference

### 19.1 Board picker
| Need | Board |
|---|---|
| Learning electronics, first project | **Arduino Uno R3** — 5V-tolerant, hard to break |
| Connected sensor / anything with Wi-Fi | **ESP32-S3** (or C6 for Matter/Thread) |
| Cheapest capable MCU | **Pico 2 / RP2350**, $5 |
| Battery sensor, months of life | **ESP32-C6** with deep sleep, or a Pico + LoRa |
| Linux, general purpose | **Pi 5** (or **Zero 2 W** for value) |
| Desktop replacement | **Pi 500 / 500+** |
| Camera, vision, ML | **Pi 5**, or **ESP32-S3**/**P4** for on-device |
| Video/display HMI panel | **ESP32-P4** + C6 companion |
| Real-time timing + Linux | **Pi + Pico over UART**, or BeagleBone PRU |
| Precise audio / timing | **Teensy** |
| BLE product | **Nordic nRF52/nRF53** |
| Teaching a child | **Micro:bit** |
| Embedding in your own product | **CM5**, or an **ESP32 module** (pre-certified) |

### 19.2 Numbers worth remembering
- **GPIO: 3.3V on Pi and ESP32, 5V on classic Arduino. ⚠️ Pi GPIO is not 5V-tolerant.**
- **A GPIO pin sources tens of mA at most.** Anything more needs a transistor.
- **LED resistor: R = (V_supply − V_forward) / I.** ~150–220Ω for a red LED on 5V.
- **I²C pull-ups: ~4.7kΩ** (often already on breakouts).
- **WS2812B: ~60mA per pixel at full white.**
- **Decoupling: 0.1µF at every IC power pin.**
- **LiPo: 3.0–4.2V**, nominal 3.7V.
- **Soldering: ~350°C leaded, ~370°C lead-free.**
- **PETG over PLA for enclosures.**

### 19.3 When it doesn't work
1. **Power** — measure at the pin, under load (§4 → `maker-power-electronics-and-io`)
2. **Ground** — common? (§4.1 → `maker-power-electronics-and-io`)
3. **Connections** — continuity, breadboard contacts, solder joints (§9.1 → `maker-software-build-and-debug`)
4. **Orientation** — polarity, pin 1, TX/RX crossed (§5 → `maker-power-electronics-and-io`)
5. **Voltage levels** — 3.3V vs 5V (§4.2 → `maker-power-electronics-and-io`)
6. **The part** — dead, wrong variant, or counterfeit? (§14 → `maker-networking-enclosures-and-productization`)
7. **Then the code** (§10 → `maker-software-build-and-debug`)

---

## §20. Sources and Method

**Method.** Narrative review, written as **build guidance for software engineers entering
hardware**, and deliberately complementary to a professional embedded/IoT reference —
this document stops where certification, RTOS internals, and fleet management begin, and
points at them in §13 → `maker-networking-enclosures-and-productization`. **The electronics fundamentals, build craft, and debugging
discipline (§4 → `maker-power-electronics-and-io`, §5 → `maker-power-electronics-and-io`, §6 → `maker-power-electronics-and-io`'s practices, §9 → `maker-software-build-and-debug`, §10 → `maker-software-build-and-debug`, §15) are decades stable** and rest on the
standard hobbyist literature (Platt, Scherz & Monk, Horowitz & Hill) plus consistently
reported practitioner experience — they were not web-verified because they do not need to
be. Four targeted searches were run in **August 2026** on the parts that move: the Arduino
ownership change, the Raspberry Pi lineup, the ESP32 family, and the Python toolchains.

**Search log** (August 2026): Qualcomm's acquisition of Arduino and the community reaction ·
Raspberry Pi 2026 lineup including Pico 2/RP2350, CM5 and Pi 500 · ESP32 variant comparison
and selection · MicroPython/CircuitPython current state.

**Primary and near-primary sources consulted (selected):**
- **Arduino's own announcement blog post** and **Qualcomm's press release** for the
  acquisition terms and UNO Q specification; **IEEE Spectrum**, **Adafruit's blog**, and
  **Hackster.io** for the community reaction, the terms-and-conditions episode, and the
  follow-up AMA. ⚠️ **I have represented both the company statements and the skepticism
  because the disagreement is the story**
- **Raspberry Pi's own product pages and microcontroller documentation** for the lineup and
  RP2040/RP2350 positioning; **Phoronix** for RP2350 chip pricing; multiple 2026 buying
  guides for the Pi 500+ specification and the model-by-model recommendations
- **ESP32 selection guides** from DroneBot Workshop, Elecrow, esp32.co.uk, espboards.dev
  and WizzDev for the variant comparison, the S3/C6/P4 positioning, and the
  new-silicon-maturity caution; **MicroPython download pages** for P4 coprocessor variants
  and **the MicroPython release record** for v1.27.0

**Confidence statement.** **High confidence** in §4 → `maker-power-electronics-and-io`, §5 → `maker-power-electronics-and-io`, §6 → `maker-power-electronics-and-io`'s practices, §7 → `maker-power-electronics-and-io`, §9 → `maker-software-build-and-debug`, §10 → `maker-software-build-and-debug`, §12 → `maker-networking-enclosures-and-productization`,
§14 → `maker-networking-enclosures-and-productization`'s cautions and §15 — these are physics and long-settled craft, and my confidence rests
on the standard literature rather than any single source. **High confidence in the Arduino
acquisition facts** (§3.1 → `maker-boards-and-platforms`): the date, the UNO Q architecture, and the stated commitments
come from Arduino's and Qualcomm's own announcements, and the skeptical reaction is
consistently reported across independent outlets including IEEE Spectrum and Adafruit.
⚠️ **I have deliberately not predicted the outcome** — §16.2 leaves it open because it is
genuinely open. **Moderate confidence in §2.1 → `maker-boards-and-platforms` and §3.3 → `maker-boards-and-platforms`'s specific specifications and
prices**: board lineups, chip pricing, and variant availability change frequently, several
figures come from retailer and enthusiast guides rather than manufacturer datasheets, and
**anything price-related should be checked at point of purchase**. **The ESP32 variant
landscape is the fastest-moving material here** — Espressif announces parts faster than
toolchains support them, which is itself the §3.3 → `maker-boards-and-platforms` warning. Sensor and part recommendations
in §6 → `maker-power-electronics-and-io` and §7 → `maker-power-electronics-and-io` reflect widely-held practitioner consensus rather than measured comparison,
and reasonable builders disagree about some of them.
