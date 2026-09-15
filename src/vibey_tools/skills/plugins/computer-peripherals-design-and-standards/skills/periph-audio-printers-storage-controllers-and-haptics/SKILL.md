---
name: periph-audio-printers-storage-controllers-and-haptics
description: "Use for the remaining device classes: audio interfaces including latency, buffer sizes and the class-compliant path, printers and scanners with their page description languages, storage, capture and the miscellaneous device classes, and game controllers and haptics including force feedback and rumble."
---

# Computer Peripherals: Audio Interfaces, Printers and Scanners, Storage, Capture and Everything Else, and Controllers and Haptics

> **Part 3 of 6** of the *Computer Peripherals: Design, Building, Standards and Programming* reference (plugin `computer-peripherals-design-and-standards`), covering §12–§15. Sibling skills: `periph-stack-usb-thunderbolt-and-wireless` (§0–§5), `periph-buses-pcie-hid-keyboards-mice-and-displays` (§6–§11), `periph-designing-firmware-pcb-and-debugging` (§16–§21), `periph-compliance-accessibility-and-security` (§22–§24), `periph-reference` (§25–§30). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 2. **⚠️ DESCRIPTORS ARE THE INTERFACE** (§8 → `periph-buses-pcie-hid-keyboards-mice-and-displays`, §19 → `periph-designing-firmware-pcb-and-debugging`). **A USB device declares what it is by
>    handing over a data structure at enumeration. Almost all "device not recognized"
>    problems are descriptor problems, and once you can read descriptors you can debug
>    nearly anything.**
> 3. **⚠️ LATENCY IS A CHAIN, AND PEOPLE OPTIMIZE THE WRONG LINK** (§9 → `periph-buses-pcie-hid-keyboards-mice-and-displays`, §21 → `periph-designing-firmware-pcb-and-debugging`). **Polling
>    rate, debounce, USB scheduling, OS input stack, render queue and display scanout all
>    add up. Buying an 8 kHz mouse while running a 60 Hz display optimizes a link that
>    wasn't the problem.**

---

## §12. Audio Interfaces

**⚠️ The signal chain**: ⚠️ **transducer → preamp → ADC → digital → DAC → amplifier →
transducer, and the weakest link governs.**
**⚠️ Sample rate and bit depth**: ⚠️ **bit depth sets DYNAMIC RANGE, sample rate sets
BANDWIDTH via Nyquist; ⚠️ and higher-than-necessary rates mainly buy filter headroom, not
audible quality — the honest case for high rates is in production, not playback.**
**⚠️ Latency** is the peripheral-specific problem: ⚠️ **buffer size trades latency against
dropouts, and driver model matters enormously — ASIO, WASAPI exclusive, CoreAudio and
JACK exist because the general OS mixer path is too slow for monitoring.**
**⚠️ USB Audio Class 2** gives driver-free high-rate multichannel audio; ⚠️ **UAC1 is
limited but works on hosts lacking UAC2 support.**
**⚠️ Impedance matching** for headphones, ⚠️ **phantom power for condenser microphones, and
balanced versus unbalanced connections for noise rejection over distance.**

---

## §13. Printers and Scanners

**⚠️ Technologies**: ⚠️ **inkjet (thermal or piezo), laser (electrophotography — charge,
expose, develop, transfer, fuse), thermal, and 3D printers, which are peripherals with an
unusually deep firmware stack.**
**⚠️ Page description languages**: ⚠️ **PostScript, PCL, PDF — versus HOST-BASED "GDI"
printers that push rendering onto the computer to cut hardware cost, which is why some
cheap printers have terrible cross-platform support.**
**⚠️ Standards that actually help**: ⚠️ **IPP and driverless printing (AirPrint, Mopria),
and SANE/TWAIN/WIA on the scanning side.**
**⚠️ The business model is the design constraint** — ⚠️ **cartridge authentication chips,
firmware updates that reject third-party supplies, and region locking are engineering
decisions made for commercial reasons, and they are a live consumer-rights issue.**

---

## §14. Storage, Capture and Everything Else

**⚠️ USB Mass Storage versus UASP** — ⚠️ **UASP allows command queuing and is substantially
faster.**
**⚠️ Bridge chips** are the usual culprit in enclosure problems, ⚠️ **including TRIM
passthrough and SMART data being hidden from the host.**
**⚠️ Webcams and capture**: ⚠️ **UVC gives driver-free operation; ⚠️ the bandwidth question
is whether the device does onboard compression (MJPEG, H.264) or sends uncompressed, which
determines what resolutions fit.**
**⚠️ Card readers, docks and hubs** — ⚠️ **and note that a hub SHARES upstream bandwidth,
which is the source of many "my drive got slow when I plugged in the webcam" reports.**

---

## §15. Controllers and Haptics

**⚠️ Gamepads**: ⚠️ **analog sticks (potentiometers, and now Hall-effect to eliminate
DRIFT — which is caused by potentiometer wear and contamination), triggers, rumble.**
**⚠️ Standards fragmentation is the practical problem**: ⚠️ **XInput versus DirectInput
versus HID gamepad, with Steam Input and SDL acting as translation layers because no
single standard won.**
**⚠️ Haptics**: ⚠️ **ERM (eccentric rotating mass — cheap, slow to spin up) versus LRA
(linear resonant actuator — fast, precise, narrow frequency) versus piezo; ⚠️ and the
quality difference is mostly in the DRIVE WAVEFORM, not the motor.**
**⚠️ Force feedback** in wheels and flight controls, ⚠️ **and accessibility controllers**
(§23 → `periph-compliance-accessibility-and-security`).

---

# PART III — BUILDING ONE
