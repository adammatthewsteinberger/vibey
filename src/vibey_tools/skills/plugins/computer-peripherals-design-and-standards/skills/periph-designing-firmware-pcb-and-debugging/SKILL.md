---
name: periph-designing-firmware-pcb-and-debugging
description: "Use when building your own peripheral: designing a custom peripheral from requirements to bill of materials, firmware including the USB stack choices, PCB and mechanical design, enumeration and debugging when a device will not appear or misbehaves, drivers and OS integration across Windows, macOS and Linux, and measuring latency properly rather than trusting a spec sheet."
---

# Computer Peripherals: Designing a Custom Peripheral, Firmware, PCB and Mechanical Design, Enumeration and Debugging, Drivers and OS Integration, and Measuring Latency

> **Part 4 of 6** of the *Computer Peripherals: Design, Building, Standards and Programming* reference (plugin `computer-peripherals-design-and-standards`), covering §16–§21. Sibling skills: `periph-stack-usb-thunderbolt-and-wireless` (§0–§5), `periph-buses-pcie-hid-keyboards-mice-and-displays` (§6–§11), `periph-audio-printers-storage-controllers-and-haptics` (§12–§15), `periph-compliance-accessibility-and-security` (§22–§24), `periph-reference` (§25–§30). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The protocols are stable and long-lived. Two areas are moving. See §25 → `periph-reference` for USB bandwidth and labelling, and display interface bandwidth tiers.

> **⚠️ The layer where a computer meets the physical world — and the one where standards
> politics, signal integrity, human factors and firmware all collide at once.**
>
> **Complements a computer-hardware reference (the host side), an electromagnetism
> reference (signal integrity, differential pairs, EMC), and a semiconductor reference
> (the microcontrollers involved).**
>
> **⚠️ GOTCHA** boxes mark where the marketing name and the actual capability diverge —
> and this domain has the worst naming in computing.
>
> **The three ideas that organize this document:**
> 1. **⚠️ THE CONNECTOR IS NOT THE PROTOCOL** (§2 → `periph-stack-usb-thunderbolt-and-wireless`, §3 → `periph-stack-usb-thunderbolt-and-wireless`, §25.1 → `periph-reference`). **A USB-C port can be
>    anything from 480 Mbps and 5 W to 80 Gbps and 240 W with video and PCIe tunnelling.
>    Identical-looking ports and cables behave completely differently, and this single
>    confusion causes more peripheral problems than any technical failure.**
> 2. **⚠️ DESCRIPTORS ARE THE INTERFACE** (§8 → `periph-buses-pcie-hid-keyboards-mice-and-displays`, §19). **A USB device declares what it is by
>    handing over a data structure at enumeration. Almost all "device not recognized"
>    problems are descriptor problems, and once you can read descriptors you can debug
>    nearly anything.**
> 3. **⚠️ LATENCY IS A CHAIN, AND PEOPLE OPTIMIZE THE WRONG LINK** (§9 → `periph-buses-pcie-hid-keyboards-mice-and-displays`, §21). **Polling
>    rate, debounce, USB scheduling, OS input stack, render queue and display scanout all
>    add up. Buying an 8 kHz mouse while running a 60 Hz display optimizes a link that
>    wasn't the problem.**

---

## §16. Designing a Custom Peripheral

```
⚠️ THE DECISION ORDER
   ⚠️ 1. What DEVICE CLASS is it? (§8) ⚠️ If HID fits, you get
      cross-platform support free. ⚠️ Vendor-specific means
      writing and maintaining drivers forever — avoid unless
      genuinely necessary
   ⚠️ 2. Wired or wireless? (§5)
   ⚠️ 3. Power budget and source
   ⚠️ 4. Microcontroller selection — ⚠️ NATIVE USB peripheral vs
      bit-banged vs a USB bridge chip
   ⚠️ 5. Enclosure and manufacturing method
⚠️ COMMON MCU CHOICES  ⚠️ RP2040/RP2350 (cheap, native USB, PIO) ·
   STM32 · ATmega32U4 (the classic HID choice) · nRF52 (BLE) ·
   ESP32 (Wi-Fi/BLE)
⚠️ ⚠️ VID/PID  ⚠️ USB Vendor IDs are ISSUED BY THE USB-IF AND COST
   MONEY. ⚠️ For hobby projects, use a PID sublicensed from a
   chip vendor's range or a community allocation — ⚠️ do NOT
   ship products with a squatted VID, which is common and wrong
⚠️ PROTOTYPE PATH  breadboard → dev board → custom PCB →
   ⚠️ and expect at least two board revisions
```

---

## §17. Firmware

**⚠️ The mature open ecosystems save enormous effort**: ⚠️ **QMK and ZMK for keyboards
(⚠️ ZMK being BLE-first), CircuitPython and Arduino for rapid work, TinyUSB as the
portable USB stack, and vendor HALs underneath.**
**⚠️ What the firmware actually does**: ⚠️ **matrix scanning and debounce (§9 → `periph-buses-pcie-hid-keyboards-mice-and-displays`), layer and
macro handling, descriptor generation, endpoint management, and persistent configuration.**
**⚠️ The real-time discipline**: ⚠️ **interrupt latency, avoiding blocking in the main loop,
and keeping the USB polling deadline no matter what else is happening.**
**⚠️ Power management for battery devices** is usually where naive firmware fails —
⚠️ **sleep states, wake sources, and connection interval negotiation dominate battery life
far more than the radio's rated current.**
**⚠️ DFU and bootloaders** — ⚠️ **and always leave a hardware recovery path, because
bricking a device with no bootloader entry is the classic first-project disaster.**

---

## §18. PCB and Mechanical Design

**⚠️ For USB specifically** (see an electromagnetism reference): ⚠️ **90 Ω differential
impedance for D+/D−, length matching within the pair, avoiding stubs and layer changes on
high-speed pairs, and a continuous ground reference plane under the pair — a split plane
under a differential pair is the classic EMC failure.**
**⚠️ ESD protection on every externally exposed line** — ⚠️ **TVS diodes at the connector,
and this is not optional on a product.**
**⚠️ Power integrity**: ⚠️ **decoupling capacitors close to pins, bulk capacitance,
and a clean supply for analog sections.**
**⚠️ Mechanical**: ⚠️ **connector retention (⚠️ through-hole or reinforced SMD, because a
ripped-off USB connector is the most common physical failure), tolerance stack-up, and
the enclosure process choice — 3D print, injection mould, CNC or sheet metal** (see a
manufacturing reference).
**⚠️ Design for assembly and test** — ⚠️ **test points, and a way to program the board
after assembly.**

---

## §19. ⚠️ Enumeration and Debugging

> **⚠️ Where most peripheral development time actually goes.**
```
⚠️ THE ENUMERATION SEQUENCE  ⚠️ attach and speed detection via
   pull-ups → reset → address assignment → ⚠️ DEVICE DESCRIPTOR
   read → configuration, interface, endpoint descriptors →
   ⚠️ HID REPORT DESCRIPTOR → configuration selected → operational
⚠️ ⚠️ ALMOST EVERY "DEVICE NOT RECOGNIZED" IS A DESCRIPTOR OR
   POWER PROBLEM. ⚠️ A malformed report descriptor typically
   fails SILENTLY — the device enumerates and then does nothing,
   or does something bizarre
⚠️ THE TOOLS, in order of usefulness
   ⚠️ lsusb -v / USBView / USB Prober — ⚠️ read the actual
      descriptors first, always
   ⚠️ HID descriptor validators and parsers
   ⚠️ Wireshark with usbmon (Linux) — ⚠️ free protocol capture
   ⚠️ Hardware protocol analysers — expensive and decisive
   ⚠️ OSCILLOSCOPE for physical-layer problems, ⚠️ and eye
      diagrams for signal integrity
⚠️ THE COMMON FAULTS  ⚠️ descriptor length mismatches · wrong
   usage page · endpoint size vs report size disagreement ·
   ⚠️ requesting more current than declared · missing or wrong
   pull-ups · ⚠️ bus-powered device browning out on inrush ·
   host controller quirks that differ across OSes
⚠️ ⚠️ TEST ON ALL TARGET PLATFORMS. ⚠️ Windows, macOS, Linux, BIOS
   and phones parse descriptors differently and tolerate
   different sloppiness
```

---

## §20. Drivers and OS Integration

**⚠️ Prefer the class driver** (§1 → `periph-stack-usb-thunderbolt-and-wireless`, §8 → `periph-buses-pcie-hid-keyboards-mice-and-displays`) — ⚠️ **a custom driver is a permanent maintenance
liability across OS versions.**
**⚠️ Userspace access** is the middle path: ⚠️ **libusb, HIDAPI, WebUSB and WebHID —
⚠️ and WebHID in particular means a configuration tool can be a web page rather than an
installed application, which is a genuine improvement in the peripheral world.**
**⚠️ When a kernel driver is genuinely required**: ⚠️ **Windows WDF/UMDF and driver signing;
Linux kernel modules; macOS DriverKit having replaced kexts.**
**⚠️ Permissions**: ⚠️ **udev rules on Linux, and the mistake of instructing users to run
things as root rather than shipping a rules file.**
**⚠️ The honest observation about vendor software**: ⚠️ **much peripheral configuration
software is heavy, runs at startup, and exists partly for telemetry — which is why
ONBOARD PROFILE STORAGE is a real feature, letting the device keep its configuration
without resident software.**

---

## §21. ⚠️ Measuring Latency

> **⚠️ §1 → `periph-stack-usb-thunderbolt-and-wireless`'s third organizing idea, made concrete.**
```
⚠️ THE FULL CHAIN, and every link adds
   ⚠️ Physical actuation and switch travel
   ⚠️ DEBOUNCE window (§9)
   ⚠️ Matrix scan interval
   ⚠️ ⚠️ USB POLLING INTERVAL — ⚠️ 1000 Hz = 1 ms, 125 Hz = 8 ms
   ⚠️ OS input stack and application
   ⚠️ Render and present queue
   ⚠️ ⚠️ DISPLAY SCANOUT AND PIXEL RESPONSE — ⚠️ at 60 Hz this
      alone averages ~8 ms of the total
⚠️ ⚠️ THE ARITHMETIC PEOPLE SKIP: going from 1000 Hz to 8000 Hz
   polling saves at most ~0.9 ms. ⚠️ Going from a 60 Hz to a
   240 Hz display saves several times that. ⚠️ Optimize the
   largest term
⚠️ HOW TO ACTUALLY MEASURE  ⚠️ high-speed camera on the input and
   the screen together (the ground truth) · ⚠️ instrumented
   hardware that shorts a switch and watches the display ·
   ⚠️ latency test tools in-OS. ⚠️ Software timestamps alone
   cannot see the ends of the chain
⚠️ VARIANCE MATTERS MORE THAN MEAN  ⚠️ consistent 5 ms feels
   better than 2 ms averaging with occasional 20 ms spikes
```

---

# PART IV — CROSS-CUTTING
