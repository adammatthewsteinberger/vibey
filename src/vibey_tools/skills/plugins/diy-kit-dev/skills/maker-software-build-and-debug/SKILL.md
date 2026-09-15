---
name: maker-software-build-and-debug
description: "Use when writing the firmware, physically building, or debugging a hardware project: the software layer (Arduino, MicroPython, CircuitPython, ESP-IDF, PlatformIO) and how to choose, the prototyping ladder from breadboard through perfboard to PCB, soldering and wiring practice, and debugging hardware with a multimeter, a logic analyzer and an oscilloscope."
---

# DIY Kit Dev: The Software Layer, Building It Physically, and Debugging Hardware

> **Part 3 of 5** of the *DIY Kit Dev* reference (plugin `diy-kit-dev`), covering §8–§10. Sibling skills: `maker-boards-and-platforms` (§0–§3), `maker-power-electronics-and-io` (§4–§7), `maker-networking-enclosures-and-productization` (§11–§14), `maker-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    enclosure, power, moisture, thermal, watchdog, recovery, and update (§13 → `maker-networking-enclosures-and-productization`). Know which
>    one you're signing up for.

---

## §8. The Software Layer

| Option | Best for | ⚠️ Trade-off |
|---|---|---|
| **Arduino C++ (IDE / CLI / PlatformIO)** | Widest library support; the default for MCUs | Hides real hardware behind abstractions; the IDE is weak (⚠️ **use PlatformIO or the CLI once you're past the first week**) |
| **MicroPython** | ⚠️ **Fast iteration, REPL on the device, excellent for learning and prototyping** | Slower, more RAM, less real-time. **v1.27.0 released December 2025** |
| **CircuitPython** (Adafruit) | Beginner-friendliest — ⚠️ **the board appears as a USB drive; save the file and it runs** | Adafruit-ecosystem-centric; a fork of MicroPython |
| **ESP-IDF** | Production ESP32 — full control, FreeRTOS, OTA, security, low power | Steeper. ⚠️ **But it's where you end up for anything serious on ESP32** |
| **Zephyr / RTOS** | Professional multi-platform embedded | Real learning curve |
| **Rust (embassy, esp-rs)** | Memory safety, async, growing fast | ⚠️ Smaller ecosystem; more friction per project |
| **ESPHome** | ⚠️ **YAML instead of code, for home automation.** Genuinely excellent | Constrained to what it supports — but that's a lot |
| **Tasmota / WLED** | Flash-and-configure firmware for smart plugs and LED strips | ⚠️ **WLED is so good it's usually the right answer for LED projects** |

**[DURABLE] The pragmatic progression**: start in **CircuitPython or the Arduino IDE** to
get something blinking; move to **PlatformIO or MicroPython** as projects grow; drop to
**ESP-IDF or C** when you need power management, OTA, or timing you can't get otherwise.
**⚠️ Skipping straight to ESP-IDF is a common way to quit.**

**Rules of thumb that hold across all of them**: **non-blocking code** (⚠️ **`delay()`
blocks everything — use millis()-style timing or async**), **watchdog timers** (§13 → `maker-networking-enclosures-and-productization`),
**serial logging** with levels, **store config in NVS/EEPROM/a file rather than
recompiling**, and **version your firmware and print the version at boot** — you will
otherwise not know what's running on a device in a cupboard.

---

## §9. Building It Physically

### 9.1 The prototyping ladder
```
Breadboard        → fast, reusable, ⚠️ unreliable connections; NOT for anything permanent
                    or anything above ~1A, and hopeless at high frequency
Perfboard/stripboard → soldered, permanent, cheap, ugly. Fine for one-offs
Protoboard/shield → purpose-made boards for Arduino/Pi form factors
Custom PCB        → §13. Cheaper than people think
```
**⚠️ A large share of "intermittent" bugs are breadboard contact problems**, especially
after the board has been used a few times. **If a circuit works when you press on it,
that's your answer.**

### 9.2 Soldering
**[DURABLE] It's a learnable skill and worth two hours of deliberate practice.**
**Temperature-controlled iron** (~350°C for leaded, ~370°C for lead-free), **flux is not
optional** (⚠️ **most soldering problems are flux problems**), **heat the joint and feed
solder to the joint — not to the iron**, **tin the tip and keep it clean**, and
**⚠️ ventilate — the fumes are flux, and you shouldn't breathe them.**

**Leaded solder is easier to work with and is a lead exposure risk**; lead-free needs more
heat. Either way: **wash your hands, don't eat at the bench.**

**Also useful**: heat-shrink over every splice (⚠️ **never leave bare twisted wire**),
**JST/Dupont/screw terminals** for connections you'll want to undo, **strain relief** on
anything that moves, and **ferrules** on stranded wire going into screw terminals.

### 9.3 Wiring practice
**⚠️ Colour-code consistently** (red = V+, black = ground, and stick to it).
**Label everything.** **Keep signal wires away from motor wires** — motor noise couples
into signal lines and produces exactly the kind of intermittent fault you'll blame on
software. **Twist power pairs.** **Document the pinout as you go** — ⚠️ **you will not
remember which GPIO the relay is on in six months, and tracing it is worse than writing it
down.**

---

## §10. Debugging Hardware

**[DURABLE] The discipline is different from software debugging: you can't trust that the
hardware is doing what the code says.**

**The order to check, which is empirically the right order:**
```
1. POWER            §4. Voltage at the actual pin, under load, with a meter
2. GROUND           Common ground between everything?
3. CONNECTIONS      Continuity test. Breadboard contacts. Cold solder joints
4. ORIENTATION      Polarity, pin 1, TX/RX crossed
5. LEVELS           3.3V vs 5V mismatch
6. THE PART         Is it counterfeit, dead, or the wrong variant? (§14)
7. ONLY THEN        Your code
```

**Techniques**: **binary-search by disconnection** (remove half the circuit); **the blink
test** (⚠️ **an LED on a GPIO is the world's cheapest debugger**); **serial print
everything**; **a logic analyzer for any bus problem** (⚠️ **I²C and SPI issues are
essentially unguessable and completely obvious on a trace**); **`i2cdetect`** to confirm a
device is even present and at the address you think; **swap a known-good part**; and
**test subsystems in isolation before integrating.**

**⚠️ The magic-smoke rules**: unplug before rewiring; **double-check polarity before
applying power** (reversed polarity kills most things instantly); use a **current-limited
bench supply** for first power-up of anything new; and **don't hot-plug** — connecting a
sensor to a powered board can put voltage on a pin before ground connects.
