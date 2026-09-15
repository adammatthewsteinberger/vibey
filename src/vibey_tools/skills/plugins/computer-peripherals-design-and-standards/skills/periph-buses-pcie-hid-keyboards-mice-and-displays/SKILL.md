---
name: periph-buses-pcie-hid-keyboards-mice-and-displays
description: "Use for the bus and device layer: embedded buses including I2C, SPI and UART, PCIe peripherals, the HID class and report descriptors that make devices work without drivers, keyboards including matrix scanning, debounce, rollover and switch behaviour, mice and pointing devices with sensors and polling rates, and displays and their interfaces."
---

# Computer Peripherals: Embedded Buses, PCIe Peripherals, HID, Keyboards, Mice and Pointing Devices, and Displays

> **Part 2 of 6** of the *Computer Peripherals: Design, Building, Standards and Programming* reference (plugin `computer-peripherals-design-and-standards`), covering §6–§11. Sibling skills: `periph-stack-usb-thunderbolt-and-wireless` (§0–§5), `periph-audio-printers-storage-controllers-and-haptics` (§12–§15), `periph-designing-firmware-pcb-and-debugging` (§16–§21), `periph-compliance-accessibility-and-security` (§22–§24), `periph-reference` (§25–§30). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 2. **⚠️ DESCRIPTORS ARE THE INTERFACE** (§8, §19 → `periph-designing-firmware-pcb-and-debugging`). **A USB device declares what it is by
>    handing over a data structure at enumeration. Almost all "device not recognized"
>    problems are descriptor problems, and once you can read descriptors you can debug
>    nearly anything.**
> 3. **⚠️ LATENCY IS A CHAIN, AND PEOPLE OPTIMIZE THE WRONG LINK** (§9, §21 → `periph-designing-firmware-pcb-and-debugging`). **Polling
>    rate, debounce, USB scheduling, OS input stack, render queue and display scanout all
>    add up. Buying an 8 kHz mouse while running a 60 Hz display optimizes a link that
>    wasn't the problem.**

---

## §6. Embedded Buses

**⚠️ For building peripherals rather than connecting them.**
```
⚠️ I²C  ⚠️ two wires, addressed, multi-drop, open-drain with
   pull-ups. ⚠️ Slow (100k/400k/1M), and ⚠️ ADDRESS COLLISIONS
   between chips are a classic design trap
⚠️ SPI  ⚠️ four wires, fast, full duplex, ⚠️ no addressing — one
   chip-select line PER DEVICE. Displays, sensors, flash
⚠️ UART / serial  ⚠️ no clock, both ends must agree on baud rate.
   ⚠️ Still the universal debug interface
⚠️ 1-Wire, CAN (automotive/industrial), RS-485 (long runs,
   differential, multi-drop)
⚠️ ⚠️ PS/2 IS INTERRUPT-DRIVEN, not polled — ⚠️ which is why it had
   genuinely lower latency than early USB and why it persists in
   niche uses
⚠️ GPIO, ADC, PWM, and interrupt handling are the primitives
   everything else is built from
```

---

## §7. PCIe Peripherals

**⚠️ Where bandwidth or latency demands exceed USB**: ⚠️ **GPUs, capture cards, NICs,
NVMe, professional audio interfaces.**
**⚠️ The architecture**: ⚠️ **BARs (base address registers) map device memory into the
host address space, MSI/MSI-X for interrupts, DMA for bulk movement, and configuration
space for enumeration.**
**⚠️ Option ROMs and UEFI drivers** allow a device to participate in boot.
**⚠️ The advantage over USB is DMA** — ⚠️ **the device writes directly to host memory
rather than being polled — which is also exactly why PCIe devices are a security concern
and why the IOMMU exists** (§24 → `periph-compliance-accessibility-and-security`).

---

# PART II — DEVICE CLASSES

## §8. ⚠️ HID

> **⚠️ The protocol that makes input devices interoperable, and the one worth understanding
> in detail because it is where custom peripherals live.**
```
⚠️ THE MODEL  ⚠️ a device describes its own data format using a
   REPORT DESCRIPTOR — a binary structure of usage pages, usages,
   logical minimums and maximums, report sizes and counts
   ⚠️ THE HOST PARSES IT AND ADAPTS. ⚠️ This is why a device with
   an unusual control set works without a driver
⚠️ USAGE TABLES  standardized numbers for "X axis", "left button",
   "volume up". ⚠️ Getting the usage right is what makes the OS
   treat your device as the correct KIND of device
⚠️ REPORTS  ⚠️ INPUT (device→host) · OUTPUT (host→device, e.g.
   LEDs) · FEATURE (bidirectional configuration)
   ⚠️ Report IDs multiplex several report types on one endpoint
⚠️ BOOT PROTOCOL  ⚠️ a fixed simplified format for keyboards and
   mice so the BIOS can use them before any HID parser exists.
   ⚠️ THIS IS WHY 6KRO EXISTS — the boot keyboard report has six
   key slots (§9)
⚠️ ⚠️ THE POWER OF THE MODEL: you can invent a device the OS has
   never seen, and if your descriptor is correct it works
   everywhere with no driver. ⚠️ You can also write a
   syntactically valid descriptor that describes something
   nonsensical, and the failure is silent (§19)
⚠️ HID OVER I²C and HID OVER GATT extend the same model to
   internal and Bluetooth devices
```

---

## §9. ⚠️ Keyboards

```
⚠️ SWITCH TYPES  ⚠️ mechanical (linear / tactile / clicky) ·
   membrane / rubber dome · scissor · ⚠️ optical and Hall-effect
   (⚠️ contactless, enabling ADJUSTABLE ACTUATION POINT and
   rapid trigger)
⚠️ THE MATRIX  ⚠️ rows and columns scanned to reduce pin count
⚠️ ⚠️ GHOSTING AND BLOCKING  ⚠️ without isolation diodes, three
   keys in a rectangle make a phantom fourth appear.
   ⚠️ A DIODE PER SWITCH gives full NKRO. ⚠️ "Anti-ghosting" in
   marketing usually means BLOCKING (refusing the ambiguous
   input) rather than true NKRO
⚠️ ⚠️ 6KRO vs NKRO  ⚠️ 6KRO is not a hardware limit — it's the HID
   BOOT PROTOCOL report format (§8). ⚠️ NKRO requires a custom
   descriptor, which is why some NKRO keyboards fail in BIOS
   and offer a toggle
⚠️ DEBOUNCE  ⚠️ mechanical contacts bounce for milliseconds.
   ⚠️ Debounce algorithm and window are a REAL latency
   contributor and a real design trade — too short gives double
   presses, too long adds delay
⚠️ SCAN RATE and USB POLLING are separate: ⚠️ a fast matrix scan
   gains nothing if the endpoint is polled at 125 Hz (§21)
⚠️ LAYOUT and PROFILE  ⚠️ ANSI/ISO/JIS · Cherry, OEM, SA, DSA
   keycap profiles · ⚠️ MX vs Topre vs low-profile stems
⚠️ PCB, PLATE, MOUNTING  ⚠️ gasket, top, tray, integrated —
   these determine acoustics and flex, which is most of what
   enthusiasts actually care about
```

---

## §10. Mice and Pointing Devices

**⚠️ Sensors**: ⚠️ **optical (LED or laser) taking thousands of surface images per second
and correlating them; ⚠️ the specs that matter are max tracking speed, max acceleration,
and lift-off distance.**
> **⚠️ GOTCHA — DPI IS A MARKETING NUMBER PAST A POINT.** ⚠️ **Very high DPI settings are
> frequently interpolated rather than native, and no one uses 30,000 DPI.** **⚠️ What
> matters is sensor accuracy — absence of smoothing, acceleration and angle snapping —
> which cheap sensors add to hide their deficiencies.**

**⚠️ Polling rate**: ⚠️ **125/500/1000 Hz and now 4/8 kHz; ⚠️ the returns diminish sharply
and high rates cost CPU and battery** (§21 → `periph-designing-firmware-pcb-and-debugging`).
**⚠️ Switches** are the wear item — ⚠️ **DOUBLE-CLICKING from switch degradation is the
characteristic failure mode of otherwise-good mice, and is repairable.**
**⚠️ Other pointing devices**: ⚠️ **trackballs, trackpads (⚠️ capacitive multitouch with
substantial gesture processing in firmware or driver), graphics tablets (⚠️ EMR — the
pen is passive and powered by the tablet's field), and touchscreens.**

---

## §11. Displays

```
⚠️ PANEL TECHNOLOGIES  ⚠️ TN (fast, poor angles) · IPS (colour,
   angles) · VA (contrast, slower transitions) · ⚠️ OLED /
   QD-OLED (per-pixel emission, true blacks, ⚠️ burn-in risk) ·
   miniLED backlights with local dimming
⚠️ THE SPECS THAT ARE ROUTINELY MISREPRESENTED
   ⚠️ RESPONSE TIME  ⚠️ quoted as best-case GtG with overdrive
      that causes INVERSE GHOSTING. Independent measurement is
      the only reliable source
   ⚠️ CONTRAST  ⚠️ "dynamic" figures are meaningless; native
      contrast is the real number
   ⚠️ HDR  ⚠️ the lower certification tiers are near-meaningless
      on a display without local dimming
   ⚠️ REFRESH RATE  ⚠️ a panel's rate and the INTERFACE bandwidth
      needed to feed it are different problems (§25.2)
⚠️ VARIABLE REFRESH  ⚠️ adaptive sync — the display refreshes when
   the frame is ready rather than on a fixed clock. ⚠️ The
   REFRESH RANGE and whether LFC (low framerate compensation)
   exists matter more than the badge
⚠️ ⚠️ DSC (Display Stream Compression)  ⚠️ visually lossless,
   hardware, ~3:1, microsecond latency — ⚠️ NOT streaming-style
   compression. ⚠️ It is how high modes fit in limited pipes,
   and it is genuinely fine, with the caveats in §25.2
⚠️ COLOUR  gamut (sRGB/DCI-P3/Rec.2020) · bit depth and ⚠️ FRC
   dithering ("10-bit" often means 8-bit+FRC) · calibration
   and ICC profiles · EDID/DisplayID as the display's descriptor
```
