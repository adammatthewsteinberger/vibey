---
name: maker-power-electronics-and-io
description: "Use when wiring, powering, or interfacing hardware — the part that stops you destroying things: the power rules and common voltages, batteries and low-power design, the electronics you actually need (Ohm's law, pull-up and pull-down resistors, decoupling, level shifting, current limits), sensors and inputs over I2C, SPI and analog including debouncing, and outputs, motors and actuators with their drivers and back-EMF."
---

# DIY Kit Dev: Power, Electronics, Sensors, and Actuators

> **Part 2 of 5** of the *DIY Kit Dev* reference (plugin `diy-kit-dev`), covering §4–§7. Sibling skills: `maker-boards-and-platforms` (§0–§3), `maker-software-build-and-debug` (§8–§10), `maker-networking-enclosures-and-productization` (§11–§14), `maker-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    drift — **check power first, second, and third** (§4). This one heuristic will save
>    you more time than everything else in this document.
> 3. **The last 10% is 90% of the work.** A breadboard demo is a weekend. **Something that
>    survives a year in a garage, on a windowsill, or outdoors is a different project** —
>    enclosure, power, moisture, thermal, watchdog, recovery, and update (§13 → `maker-networking-enclosures-and-productization`). Know which
>    one you're signing up for.

---

## §4. Power — Read This Section

**[DURABLE] More project failures trace to power than to anything else, and it's rarely
the first thing people check.**

### 4.1 The rules

- **⚠️ Amps are pulled, not pushed.** A 5V/3A supply doesn't force 3A into your circuit;
  the circuit draws what it needs up to that limit. **Undersizing means brownouts, not a
  clean failure.**
- **⚠️ Budget for peak, not average.** A Wi-Fi transmit burst, a motor stall, or a servo
  starting can be **many times** the idle draw — and lasts milliseconds, which is exactly
  long enough to reset your board and short enough to be invisible on a multimeter.
- **⚠️ Never power motors or servos from a board's regulator.** This is the single most
  common beginner destruction. **Separate supply, common ground.**
- **Decoupling capacitors.** 0.1 µF ceramic next to every IC's power pin, plus bulk
  electrolytic (100–1000 µF) near motors and LED strips. **⚠️ This fixes a startling
  proportion of "random reboot" and "flaky sensor" problems.**
- **Common ground, always.** Separate supplies must share a ground reference or nothing
  works and signals float.
- **⚠️ Wire gauge and voltage drop are real.** Long thin wires to an LED strip cause dim
  ends and brownouts. Inject power at both ends of a long run.
- **USB cables are not equal.** ⚠️ **A charge-only or thin cable causes under-voltage that
  presents as software flakiness.** Suspect the cable early.

### 4.2 Common voltages
**5V** (USB, most Arduinos, LED strips), **3.3V** (ESP32, Pi GPIO, most modern sensors,
most SD cards), **12V** (motors, LED strips, automotive), **LiPo 3.7V nominal** (⚠️ **3.0–4.2V
across its range — plan for both ends**).

**⚠️ Level shifting is not optional.** Connecting a 5V output to a 3.3V input destroys the
3.3V part. A **bidirectional level shifter** or even a resistor divider for one-way
signals costs pennies. **A 3.3V output into a 5V input often works** (many 5V parts read
3.3V as high) — **but check the datasheet rather than assuming.**

### 4.3 Batteries
**LiPo/Li-ion** — best energy density, needs **protection circuitry and a proper charge
IC (TP4056 and better)**. **⚠️ Lithium cells are genuinely dangerous when mistreated: never
charge unattended on a flammable surface, never puncture, never over-discharge, and never
use a cell that has swollen.** This is the one place in hobby electronics where the failure
mode is fire.
**18650 cells** — cheap, replaceable, ⚠️ **and the counterfeit rate is enormous** (a
"9900mAh" 18650 does not exist; real cells top out around 3500mAh).
**LiFePO4** — safer chemistry, lower density, longer life.
**Alkaline/NiMH** — fine for low-drain, no fire risk.
**Solar** — needs a charge controller sized for a rainy week, not an average day.

### 4.4 Low-power design
**[DURABLE] The order of magnitude that matters**: an ESP32 running Wi-Fi continuously
lasts hours on a small battery; the **same ESP32 in deep sleep, waking briefly to
transmit, lasts months.**
**The techniques**: deep sleep between readings (⚠️ **the dominant lever by far**),
duty-cycling the radio, powering sensors from a GPIO so they're fully off, cutting
regulator quiescent current, and **⚠️ measuring actual consumption** — a USB power meter or
a current-sense module tells you in minutes what guessing won't tell you in a week.

---

## §5. The Electronics You Actually Need

**[DURABLE] You don't need an EE degree. You do need these.**

**Ohm's law** (V = IR) and **power** (P = VI). ⚠️ **The one calculation you will use
constantly: the LED series resistor.** R = (V_supply − V_forward) / I_desired. A red LED
at ~2V forward, 20mA, on 5V → (5−2)/0.02 = 150Ω.

**⚠️ LEDs without a current-limiting resistor burn out.** Every time. This is the most
common first mistake.

**Pull-up and pull-down resistors** — ⚠️ **a floating input is not "low," it's random.**
Buttons need a pull-up or pull-down (most MCUs have internal ones — `INPUT_PULLUP`).
**I²C requires pull-ups on SDA and SCL** — usually 4.7kΩ, and often already on breakout
boards (⚠️ **which is why chaining many breakouts can over-pull the bus**).

**Transistors and MOSFETs as switches** — when a GPIO pin can't supply enough current
(⚠️ **which is most of the time — a pin sources tens of milliamps at best**). Use a
**logic-level MOSFET** for DC loads and a **relay or solid-state relay** for AC.

**⚠️ Flyback diodes.** Any inductive load — motor, relay coil, solenoid — generates a
large reverse voltage spike when switched off that **will destroy your driver
transistor**. A diode across the coil is non-negotiable.

**Capacitors** — decoupling (§4.1), smoothing, timing. **Voltage regulators** — linear
(LM7805, AMS1117: simple, ⚠️ **wastes the difference as heat**) vs. switching/buck
(efficient, slightly noisier).

**The protocols you'll meet**:

| Protocol | Wires | Notes |
|---|---|---|
| **GPIO** | 1 | On/off |
| **PWM** | 1 | Dimming, servos, motor speed |
| **ADC** | 1 | Analog in. ⚠️ **Not on Raspberry Pi** |
| **I²C** | 2 + gnd | Addressed bus, many devices. ⚠️ **Address conflicts are the classic failure** |
| **SPI** | 4+ | Faster, one chip-select per device |
| **UART** | 2 + gnd | Serial. ⚠️ **TX→RX, RX→TX — crossed, not straight** |
| **1-Wire** | 1 + gnd | DS18B20 temperature sensors |
| **CAN** | 2 | Automotive and robust industrial |

**Tools worth owning**, in order of value: a **multimeter** (⚠️ **non-negotiable, and £20
is enough**), a decent **soldering iron** with temperature control, **helping hands**,
**wire strippers**, **flush cutters**, a **USB power meter**, and eventually a
**logic analyzer** (⚠️ **£10 clones of the Saleae work with the free Sigrok/PulseView
software and will save you days**) and a **bench power supply with current limiting**.

---

## §6. Sensors and Inputs

**[DURABLE] The categories, with the ones actually worth using:**

| Measuring | Common parts | ⚠️ Notes |
|---|---|---|
| **Temp / humidity** | **BME280/BME680** (I²C, also pressure/gas), DS18B20 (1-Wire, waterproof versions), SHT4x | ⚠️ **Avoid DHT11 — it's cheap and bad.** DHT22 is tolerable; BME280 is better for pennies more |
| **Motion** | PIR (HC-SR501), mmWave radar (LD2410) | ⚠️ **mmWave detects presence, not just motion** — it sees a stationary person. Big upgrade for room occupancy |
| **Distance** | HC-SR04 (ultrasonic, cheap, crude), VL53L0X/L1X (laser ToF, precise), LiDAR | Ultrasonic is confused by soft surfaces and angles |
| **Light** | LDR (crude), BH1750/TSL2591 (calibrated lux) | |
| **Motion/orientation** | MPU6050 (⚠️ ubiquitous and ageing), BNO085 (⚠️ **on-board sensor fusion — worth the money**), ICM-20948 | Raw IMU data needs fusion; a chip that does it for you saves enormous effort |
| **Current** | INA219/INA226 (I²C), ACS712 (hall) | For measuring your own power draw (§4.4) |
| **Air quality** | SGP30/SGP41 (VOC), SCD40/41 (⚠️ **true NDIR CO₂ — accept no "eCO₂" substitute**), PMS5003 (particulates) | ⚠️ **"eCO₂" from a VOC sensor is an estimate, not a CO₂ measurement** |
| **Soil moisture** | Capacitive | ⚠️ **Never resistive — it corrodes away in weeks** |
| **Camera** | Pi Camera Module 3, ESP32-CAM, USB webcam | ESP32-CAM is cheap and fiddly |
| **RFID/NFC** | RC522, PN532 | |
| **Input** | Buttons (⚠️ **debounce them**), rotary encoders, capacitive touch, joysticks | Debounce in hardware (RC) or software |

**[DURABLE] The practices that separate working from flaky:**
- **⚠️ Debounce every mechanical switch.** A button press is electrically several presses.
- **Filter noisy analog readings** — moving average or an exponential filter. **Raw ADC
  readings jitter.**
- **Calibrate.** ⚠️ **Cheap sensors are frequently accurate in relative terms and wrong in
  absolute ones.** Compare against a known reference before trusting a number.
- **Read the datasheet for the settling and warm-up time.** Many sensors need seconds to
  minutes before their first reading means anything — **gas sensors especially.**
- **Handle the failure case.** ⚠️ **A disconnected sensor often reads a plausible value
  (0, or full-scale), not an error.** Sanity-check ranges.

---

## §7. Outputs, Motors and Actuators

| Actuator | Notes |
|---|---|
| **Servo** | Position control via PWM, 0–180°. ⚠️ **Cheap servos jitter and stall — and a stalling servo draws a lot** (§4.1) |
| **Continuous-rotation servo** | Speed, not position. Convenient for small robots |
| **DC motor** | Needs an **H-bridge driver** (L298N is common and inefficient; DRV8833 or TB6612FNG are better). ⚠️ **Never drive from a GPIO** |
| **Stepper** | Precise positioning. A28YBJ-48 + ULN2003 to learn; **NEMA 17 + A4988/TMC2209** for real work (⚠️ **TMC drivers are near-silent — worth it**) |
| **Solenoid / relay** | ⚠️ **Flyback diode** (§5). For mains, use a proper relay module or SSR |
| **LED strips** | **WS2812B/NeoPixel** (one data wire, ⚠️ **timing-critical — an ESP32/Pico handles this better than a busy Linux box**), **SK6812** (adds white), **APA102/DotStar** (clocked, easier timing). ⚠️ **Power budget: ~60mA per pixel at full white** — a 300-LED strip can pull 18A |
| **Displays** | SSD1306 OLED (tiny, cheap, I²C), ST7789/ILI9341 TFT (SPI, colour), e-paper (⚠️ **beautiful for low-refresh status displays and zero power when static**), HD44780 character LCD |
| **Audio** | DFPlayer Mini (MP3 from SD), I²S DACs, piezo buzzers |

> **⚠️ GOTCHA — mains voltage.** If your project switches 120/230V AC, that is a different
> category of risk from everything else here. **Use a properly enclosed, certified relay
> module or a commercial smart plug you control over the network** rather than wiring mains
> onto a breadboard. **If you're not confident, don't** — and in many jurisdictions
> permanent mains wiring is legally restricted to qualified electricians regardless of your
> confidence.
