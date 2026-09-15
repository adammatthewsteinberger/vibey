---
name: periph-compliance-accessibility-and-security
description: "Use before shipping a peripheral or assessing one: compliance and certification including USB-IF, CE, FCC and the logo programmes, accessibility and the design decisions that include or exclude users, and peripheral security — malicious devices, BadUSB-class attacks, DMA exposure and firmware update integrity."
---

# Computer Peripherals: Compliance and Certification, Accessibility, and Peripheral Security

> **Part 5 of 6** of the *Computer Peripherals: Design, Building, Standards and Programming* reference (plugin `computer-peripherals-design-and-standards`), covering §22–§24. Sibling skills: `periph-stack-usb-thunderbolt-and-wireless` (§0–§5), `periph-buses-pcie-hid-keyboards-mice-and-displays` (§6–§11), `periph-audio-printers-storage-controllers-and-haptics` (§12–§15), `periph-designing-firmware-pcb-and-debugging` (§16–§21), `periph-reference` (§25–§30). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §22. Compliance and Certification

**⚠️ Nothing ships without this, and first-time designers routinely underestimate it.**
⚠️ **EMC — emissions and immunity — with FCC Part 15 in the US and CE/UKCA marking in
Europe requiring an EMC directive assessment;** ⚠️ **safety (IEC 62368-1 having replaced
60950 for IT equipment);** ⚠️ **RED for anything with a radio, plus regional radio
approvals.**
**⚠️ Materials and environmental**: ⚠️ **RoHS, REACH, WEEE, and battery regulations.**
**⚠️ Logo programmes**: ⚠️ **USB-IF certification requires membership and testing, and
gives you the right to use the logos and a database listing** (§25.1 → `periph-reference`); ⚠️ **Bluetooth SIG
qualification; DisplayPort and HDMI certification** (§25.2 → `periph-reference`).
**⚠️ Pre-compliance testing** with a cheap near-field probe and spectrum analyser
⚠️ **catches most problems before an expensive chamber booking, and is the single
best-value practice for small teams.**

---

## §23. Accessibility

**⚠️ Peripherals are where accessibility is won or lost**, ⚠️ **because the input device is
the interface for anyone who cannot use a standard keyboard and mouse.**
⚠️ **Switch access and scanning interfaces; ⚠️ modular and adaptive controllers with 3.5 mm
switch jacks; ⚠️ eye tracking; ⚠️ head pointers; ⚠️ alternative keyboards — split,
ortholinear, chorded, one-handed; ⚠️ and braille displays.**
**⚠️ Design practices that cost nothing**: ⚠️ **don't rely on colour alone for status,
support OS accessibility features rather than fighting them, allow full remapping,
make actuation force and travel adjustable where possible, and ⚠️ ensure the device works
without vendor software.**
**⚠️ The mechanical keyboard community's customization work has genuine accessibility
value** — ⚠️ **adjustable actuation, layer systems and macro support serve disability
needs as much as enthusiast ones.**

---

## §24. ⚠️ Peripheral Security

```
⚠️ ⚠️ BADUSB  ⚠️ a device can CLAIM TO BE ANYTHING. ⚠️ A USB stick
   whose firmware declares itself a keyboard can type commands
   at machine speed. ⚠️ THE TRUST MODEL IS THE FLAW: USB has no
   device authentication, and the host believes the descriptor
⚠️ ⚠️ DMA ATTACKS  ⚠️ Thunderbolt and PCIe devices can read host
   memory directly (§7). ⚠️ IOMMU/VT-d and "Thunderbolt security
   levels" exist for this; ⚠️ pre-boot and sleep states have
   been the weak points
⚠️ MALICIOUS CHARGERS AND CABLES  ⚠️ cables with embedded
   implants are commercially available. ⚠️ USB data blockers
   ("USB condoms") and charge-only cables are the mitigation
⚠️ WIRELESS  ⚠️ unencrypted 2.4 GHz keyboard traffic has been
   sniffable and INJECTABLE in documented cases; ⚠️ Bluetooth
   pairing weaknesses recur
⚠️ FIRMWARE  ⚠️ unsigned firmware update paths on peripherals are
   a persistent supply-chain exposure
⚠️ MITIGATIONS  ⚠️ USB device authorization / port control policy ·
   ⚠️ USBGuard on Linux · disable unused ports in firmware ·
   IOMMU enabled · signed firmware · ⚠️ and the plain advice not
   to plug in unknown devices, which remains effective
⚠️ ⚠️ USB4 and USB-C do NOT fix the trust model. ⚠️ They add
   capability, not authentication
```
