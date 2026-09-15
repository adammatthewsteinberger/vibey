---
name: maker-boards-and-platforms
description: "Use when choosing a board or getting oriented in the maker hardware ecosystem: the board decision tree, the Raspberry Pi lineup with its gotchas and alternatives, the Qualcomm acquisition of Arduino and what it changed, the Arduino boards, ESP32 as the workhorse, and the rest of the microcontroller field including the RP2040 and Pico. Includes the router for the whole diy-kit-dev reference."
---

# DIY Kit Dev: Choosing a Board, Raspberry Pi, Arduino, and the Microcontroller Field

> **Part 1 of 5** of the *DIY Kit Dev* reference (plugin `diy-kit-dev`), covering §0–§3. Sibling skills: `maker-power-electronics-and-io` (§4–§7), `maker-software-build-and-debug` (§8–§10), `maker-networking-enclosures-and-productization` (§11–§14), `maker-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    never corrupts an SD card is the right answer far more often than a Pi is** (§1).
> 2. **⚠️ It's the power supply.** When something works on the bench and fails in the
>    field, when a board reboots randomly, when Wi-Fi drops under load, when readings
>    drift — **check power first, second, and third** (§4 → `maker-power-electronics-and-io`). This one heuristic will save
>    you more time than everything else in this document.
> 3. **The last 10% is 90% of the work.** A breadboard demo is a weekend. **Something that
>    survives a year in a garage, on a windowsill, or outdoors is a different project** —
>    enclosure, power, moisture, thermal, watchdog, recovery, and update (§13 → `maker-networking-enclosures-and-productization`). Know which
>    one you're signing up for.

---

## §0. Routing

| Asked about... | Go to |
|---|---|
| **Which board should I use?** | **§1** |
| Raspberry Pi lineup | §2 |
| Arduino — and what Qualcomm changed | §3 |
| ESP32 family | §3.3 |
| **Power — read this** | **§4 → `maker-power-electronics-and-io`** |
| Electronics you must know | §5 → `maker-power-electronics-and-io` |
| Sensors and inputs | §6 → `maker-power-electronics-and-io` |
| Motors, actuators, outputs | §7 → `maker-power-electronics-and-io` |
| Software: Arduino / MicroPython / ESP-IDF | §8 → `maker-software-build-and-debug` |
| Prototyping, soldering, physical build | §9 → `maker-software-build-and-debug` |
| **Debugging hardware** | §10 → `maker-software-build-and-debug` |
| Networking and home automation | §11 → `maker-networking-enclosures-and-productization` |
| Enclosures, 3D printing, fabrication | §12 → `maker-networking-enclosures-and-productization` |
| Prototype → product | §13 → `maker-networking-enclosures-and-productization` |
| Buying, suppliers, and counterfeits | §14 → `maker-networking-enclosures-and-productization` |
| "Don't do this" | §15 → `maker-reference` |
| "Which is better?" | §16 → `maker-reference` |
| "Is this still current?" | §17 → `maker-reference` |
| Books, channels, communities | §18 → `maker-reference` |

---

## §1. Choosing a Board

**[DURABLE] The single decision that determines everything else.** The mistake in both
directions: reaching for a Pi because Linux is familiar, or forcing a microcontroller to
do something that genuinely needs an OS.

### 1.1 The decision tree

```
Does it need a filesystem, a display server, a camera pipeline,
containers, or arbitrary Linux software?
├─ YES → Single-board computer (Raspberry Pi 5 / Zero 2 W / alternatives)  §2
└─ NO  → Does it need to be battery-powered for weeks/months?
         ├─ YES → Microcontroller, and low-power design matters       §4.4
         └─ NO  → Does it need Wi-Fi/BLE?
                  ├─ YES → ESP32 family (usually ESP32-S3 or C6)      §3.3
                  └─ NO  → Pico / Arduino / any cheap MCU             §2.3, §3
```

**[DURABLE] The questions that actually decide it:**

| Question | Why it matters |
|---|---|
| **Real-time timing?** | ⚠️ **Linux is not real-time.** Precise pulse timing, motor control, and protocol bit-banging want an MCU |
| **Boot time** | MCU: instant. Pi: 20–30 seconds, and it must shut down cleanly |
| **Power budget** | MCU: µA–mA in sleep. Pi: hundreds of mA minimum, always |
| **⚠️ Will it lose power unexpectedly?** | **An SD-card Pi hates this.** MCUs don't care |
| **Analog inputs?** | ⚠️ **Raspberry Pi has no ADC.** MCUs do. This surprises people constantly |
| **Networking** | Pi: full stack. ESP32: excellent Wi-Fi/BLE. Pico W: good. AVR Arduino: needs a shield |
| **Heavy compute / vision / ML** | Pi 5, or an MCU with an accelerator for small models |
| **Unit cost at volume** | §13 → `maker-networking-enclosures-and-productization` |

**[DURABLE] The hybrid answer is often the right one and under-used**: a **Pico or ESP32
handling real-time I/O, talking to a Pi over UART/I²C/USB** that handles networking,
storage, and logic. You get deterministic timing *and* Linux.

---

## §2. Raspberry Pi

**[VERSIONED] The families**: **Model B** (the main boards), **Zero** (small, cheap,
low-power), **400/500** (a computer inside a keyboard), **Compute Module** (for embedding
in your own product), and **Pico** — ⚠️ **which is a microcontroller, not a Linux
computer**, and is conceptually closer to an Arduino or ESP32 than to a Pi.

### 2.1 The current lineup (mid-2026)

| Board | Notes |
|---|---|
| **Pi 5** | The current flagship. BCM2712, PCIe for NVMe. ⚠️ **Wants active cooling and a proper 5V/5A USB-C supply** |
| **Pi 4B** | Still widely deployed and a fine budget entry. Firmware-boosted to 1.8 GHz |
| **Pi Zero 2 W** | ⚠️ **The value pick.** Outperforms a Pi 3B on most tasks at lower power and cost |
| **Pi 500 / 500+** | Pi 5 in a keyboard. 500 is 8 GB; **500+ (Sept 2025, ~$200) adds 16 GB RAM, a 256 GB NVMe SSD, and a mechanical keyboard** |
| **CM5** | Compute Module 5 — BCM2712 as a module for your own carrier board. §13 → `maker-networking-enclosures-and-productization` |
| **Pico 2 / Pico 2 W** | **RP2350: dual Cortex-M33 @ 150 MHz**, floating point and DSP. From **$5**. W adds Wi-Fi and **Bluetooth 5.2** |

**⚠️ Pi 1/2/3 are not worth buying new** — a Zero 2 W beats a 3B for less money and less
power.

**[VERSIONED] The RP2350 chip is separately purchasable** for your own designs:
**RP2350A (7×7 QFN60) ~$1.10** and **RP2350B (10×10 QFN80) ~$1.20** singly, dropping to
**~$0.80–0.90 on reels** — with **RP2354** variants adding 2 MB stacked flash.
**⚠️ This matters more than it looks**: it's a credible, well-documented, cheaply available
MCU for a custom board, backed by unusually good documentation.

### 2.2 The Pi gotchas

> **⚠️ GOTCHA — the recurring Raspberry Pi failure modes, in order of how often they bite:**
> - **⚠️ SD card corruption is the #1 Pi reliability problem.** Cheap or counterfeit cards,
>   sudden power loss, and write-heavy workloads kill them. **Fixes: a good A2-rated card,
>   move logs to tmpfs, consider read-only root, or boot from USB/NVMe on a Pi 5.**
> - **Under-voltage.** ⚠️ **The lightning-bolt icon and `vcgencmd get_throttled` are your
>   friends.** A phone charger is not a Pi supply. The Pi 5 in particular wants 5V/5A.
> - **Thermal throttling.** The Pi 5 needs active cooling under sustained load.
> - **No ADC.** Add an MCP3008 or use an MCU.
> - **⚠️ GPIO is 3.3V and not 5V-tolerant.** 5V on a GPIO pin will destroy the chip.
>   **Level-shift.**
> - **Not real-time.** Don't bit-bang timing-critical protocols from Linux userspace.
> - **Unclean shutdown** corrupts filesystems. Add a UPS HAT or design for it.

### 2.3 The alternatives
**Orange Pi, Radxa Rock, Banana Pi, Libre Computer, Odroid** — frequently better specs per
dollar. **⚠️ The trade-off is real and consistently underweighted: software support and
community size.** Raspberry Pi's advantage was never the hardware — it's that every
tutorial, library, and forum answer assumes it. **For a first project, that's worth more
than the extra RAM.**
**Jetson Orin Nano / Super** for genuinely GPU-heavy vision and ML.
**BeagleBone** for its PRUs (real-time cores alongside Linux) — a genuinely distinctive
answer to §1's timing problem.

---

## §3. Arduino, ESP32, and the Microcontroller Field

### 3.1 ⚠️ The Qualcomm acquisition — the ecosystem event of the period

**[VERSIONED] On 7 October 2025, Qualcomm announced it was acquiring Arduino.** It was a
genuine surprise — **Arduino wasn't known to be courting a buyer and nothing leaked
beforehand**, which is rare. Financial terms weren't disclosed.

**What was announced alongside it**: the **Arduino UNO Q**, a **"dual-brain" board** pairing
a **Qualcomm Dragonwing QRB2210** running Debian Linux (with AI and graphics acceleration,
quad-core, camera/audio/display support) with an **STMicro microcontroller for real-time
work**. ⚠️ **It is the first UNO-family board that is a standalone-capable single-board
computer rather than a microcontroller dev board** — which puts it in Raspberry Pi's
territory, not Arduino's traditional one. It ships alongside **Arduino App Lab**, and
**Edge Impulse** (also Qualcomm-owned) provides the edge-AI layer.

**The stated commitments**: Arduino remains an **independent brand**, continues supporting
**microcontrollers and microprocessors from multiple semiconductor providers**, and
Qualcomm said it would make the Dragonwing SoC available beyond Arduino boards. Qualcomm
framed it alongside its acquisitions of **Edge Impulse** and **Foundries.io**.

> **⚠️ GOTCHA — the community reaction is the part worth knowing, and it's mixed.**
> Coverage was openly skeptical: IEEE Spectrum's headline was **"Qualcomm Buys Arduino,
> and the Open-Source Community Is Skeptical."** Adafruit's write-up noted that
> **Arduino and Qualcomm did not respond to inquiries over several months**, and read the
> emphasis on "community trust" and "heritage" as **defensive framing anticipating
> backlash**.
>
> **The concrete flashpoint was a terms-and-conditions change** that the community read as
> an attempt to lock down previously-open software and hardware. **Arduino says that
> reading was incorrect**, and held a public AMA — with Qualcomm, Edge Impulse and
> STMicro — **reiterating a "100% commitment" to open source software and open hardware**
> and continued work with non-Qualcomm partners.
>
> **[CONTESTED] Where this actually lands is not yet knowable**, and anyone telling you
> otherwise is guessing. **The practical position: nothing has broken for existing users.
> The AVR boards, the IDE, and the libraries all still work. But if you are starting a
> long-lived project, the ESP32 and RP2350 ecosystems are not owned by a company whose
> incentives just changed** — and that's a legitimate input to a platform decision now in
> a way it wasn't in 2024.

### 3.2 The Arduino boards

| Board | Use |
|---|---|
| **Uno R3** (ATmega328P) | ⚠️ **Ancient and still the best first board.** 16 MHz, 2 KB RAM. Every tutorial targets it, it's 5V-tolerant, and it's hard to destroy |
| **Uno R4 Minima / WiFi** | Renesas RA4M1, 32-bit, much more capable. WiFi adds an ESP32-S3 for connectivity |
| **Nano / Nano Every** | Uno-class in a breadboard-friendly footprint |
| **Nano ESP32** | ESP32-S3 in Arduino form factor |
| **Mega 2560** | When you need a lot of pins |
| **Uno Q** | §3.1 — a different class of thing |

**[DURABLE] The Arduino ecosystem's real product was never the hardware — it's the IDE, the
library ecosystem, and the fact that a beginner can blink an LED in five minutes.** That's
why "Arduino" survived being technically outclassed for a decade.

### 3.3 ESP32 — the workhorse

**[VERSIONED] For most connected hobby projects in 2026, an ESP32 is the default answer**:
Wi-Fi and Bluetooth built in, cheap, mature tooling, enormous library support.

**The family has grown to roughly a dozen variants.** The ones that matter:

| Chip | Notes |
|---|---|
| **ESP32-S3** | ⚠️ **The best all-rounder for hobbyists** — Xtensa dual-core 240 MHz, **128-bit SIMD for wake-word and image work**, USB, camera and LCD interfaces, Wi-Fi + BLE. **Start here unless you have a reason not to** |
| **ESP32-C3** | RISC-V, cheap, Wi-Fi + BLE. The economical modern choice |
| **ESP32-C6** | ⚠️ **RISC-V with Wi-Fi 6, BLE, and 802.15.4 — the path to Thread, Zigbee, and Matter.** The pick for a net-new battery sensor design, and aligned with where Espressif is heading |
| **ESP32-H2** | 802.15.4 only — low-power Matter-over-Thread end devices |
| **ESP32-P4** | ⚠️ **Dual-core RISC-V 400 MHz, MIPI camera/display, hardware H.264 (1080p30), up to 32 MB PSRAM — and no wireless at all.** Needs a companion C6/C5. For smart displays, video doorbells, HMI panels |
| **Original ESP32** | Still fine for cheap Wi-Fi projects, MQTT sensors, relays, and teaching |

**⚠️ Newer ≠ better supported.** One 2026 selection guide is blunt about the trade-off: the
established parts have **"modules in abundant stock, lowest price, most stable supply
chain, richest community resources"**, while the newest silicon may be **pre-production,
without official modules, and not yet supported in Arduino-ESP32 or MicroPython**.
**Check toolchain support before committing to a new chip.** Espressif announced further
parts through 2026 (the S31, C61, H21 and others) — **treat anything announced within the
last few months as not yet hobby-ready.**

**[DURABLE] SoC vs. module matters for anything you might build more than one of**: a
**module** (ESP32-WROOM and friends) integrates the chip with flash, a PCB antenna, and RF
shielding — **which is what makes regulatory certification tractable** (§13 → `maker-networking-enclosures-and-productization`).

### 3.4 The rest of the field
**STM32** (huge range, steep learning curve, professional standard), **Nordic nRF52/nRF53**
(⚠️ **the best BLE silicon**, and what most commercial BLE products use), **Teensy** (Paul
Stoffregen's boards — ⚠️ **exceptional for audio and precise timing**, and superbly
supported), **Adafruit Feather / QT Py / ItsyBitsy** (a coherent ecosystem with STEMMA QT
connectors that eliminate soldering for I²C), **Seeed XIAO** (tiny, cheap, many variants),
**Micro:bit** (the best board for teaching children).
