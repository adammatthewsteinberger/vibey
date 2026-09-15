---
name: periph-stack-usb-thunderbolt-and-wireless
description: "Use when working out how a peripheral actually connects: the peripheral stack from physical layer to application, USB architecture with descriptors, endpoints and transfer types, USB-C and Power Delivery including the cable and role negotiation mess, Thunderbolt and alternate modes, and wireless peripherals and their latency and pairing trade-offs. Includes the router for the whole peripherals reference."
---

# Computer Peripherals: The Peripheral Stack, USB Architecture, USB-C and Power Delivery, Thunderbolt and Alternate Modes, and Wireless Peripherals

> **Part 1 of 6** of the *Computer Peripherals: Design, Building, Standards and Programming* reference (plugin `computer-peripherals-design-and-standards`), covering §0–§5. Sibling skills: `periph-buses-pcie-hid-keyboards-mice-and-displays` (§6–§11), `periph-audio-printers-storage-controllers-and-haptics` (§12–§15), `periph-designing-firmware-pcb-and-debugging` (§16–§21), `periph-compliance-accessibility-and-security` (§22–§24), `periph-reference` (§25–§30). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 1. **⚠️ THE CONNECTOR IS NOT THE PROTOCOL** (§2, §3, §25.1 → `periph-reference`). **A USB-C port can be
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

## §0. Routing

| You want... | Go to |
|---|---|
| The peripheral stack | §1 |
| **⚠️ USB architecture** | **§2** |
| **⚠️ USB-C and Power Delivery** | **§3** |
| Thunderbolt and alt modes | §4 |
| Wireless | §5 |
| Embedded buses | §6 → `periph-buses-pcie-hid-keyboards-mice-and-displays` |
| PCIe peripherals | §7 → `periph-buses-pcie-hid-keyboards-mice-and-displays` |
| **⚠️ HID protocol** | **§8 → `periph-buses-pcie-hid-keyboards-mice-and-displays`** |
| **⚠️ Keyboards** | **§9 → `periph-buses-pcie-hid-keyboards-mice-and-displays`** |
| Mice and pointing | §10 → `periph-buses-pcie-hid-keyboards-mice-and-displays` |
| **Displays** | **§11 → `periph-buses-pcie-hid-keyboards-mice-and-displays`** |
| Audio | §12 → `periph-audio-printers-storage-controllers-and-haptics` |
| Printers and scanners | §13 → `periph-audio-printers-storage-controllers-and-haptics` |
| Storage and capture | §14 → `periph-audio-printers-storage-controllers-and-haptics` |
| Controllers and haptics | §15 → `periph-audio-printers-storage-controllers-and-haptics` |
| **Building a custom peripheral** | **§16 → `periph-designing-firmware-pcb-and-debugging`** |
| Firmware | §17 → `periph-designing-firmware-pcb-and-debugging` |
| PCB and mechanical | §18 → `periph-designing-firmware-pcb-and-debugging` |
| **⚠️ Enumeration debugging** | **§19 → `periph-designing-firmware-pcb-and-debugging`** |
| Drivers and OS integration | §20 → `periph-designing-firmware-pcb-and-debugging` |
| **⚠️ Latency measurement** | **§21 → `periph-designing-firmware-pcb-and-debugging`** |
| Compliance and EMC | §22 → `periph-compliance-accessibility-and-security` |
| Accessibility | §23 → `periph-compliance-accessibility-and-security` |
| **⚠️ Security** | **§24 → `periph-compliance-accessibility-and-security`** |
| **What's live** | **§25 → `periph-reference`** |
| Misconceptions, numbers | §26–§27 → `periph-reference` |
| Sources, quick ref, method | §28–§30 → `periph-reference` |

---

## §1. The Peripheral Stack

```
⚠️ THE LAYERS, and problems can live at any of them
   ⚠️ PHYSICAL  connector, cable, differential signalling, power
   ⚠️ LINK  encoding, framing, error handling
   ⚠️ PROTOCOL  transfers, endpoints, enumeration
   ⚠️ DEVICE CLASS  ⚠️ HID, audio, storage, video — the shared
      contract that means you don't need a driver per product
   ⚠️ DRIVER  OS integration
   ⚠️ APPLICATION
⚠️ ⚠️ CLASS DRIVERS ARE WHY PERIPHERALS "JUST WORK". ⚠️ A keyboard
   from any vendor works on any OS because both implement the HID
   class (§8). ⚠️ Vendor-specific drivers exist only where the
   class model is insufficient — or where the vendor wants
   lock-in and telemetry
⚠️ HOST-CENTRIC vs PEER  ⚠️ USB is strictly host-controlled: devices
   NEVER initiate transfers, they are polled. ⚠️ This shapes
   everything about latency (§21) and power
```

---

# PART I — BUSES AND PROTOCOLS

## §2. ⚠️ USB Architecture

```
⚠️ THE TOPOLOGY  a tiered star; ⚠️ one host controller, hubs,
   devices. ⚠️ Max 127 devices, 7 tiers
⚠️ ⚠️ THE HOST POLLS. Devices cannot speak unbidden — which is why
   an interrupt endpoint's POLLING INTERVAL sets input latency
⚠️ ENDPOINTS AND TRANSFER TYPES — ⚠️ the distinction that matters
   ⚠️ CONTROL  enumeration and configuration; guaranteed
   ⚠️ INTERRUPT  ⚠️ small, periodic, BOUNDED LATENCY, guaranteed
      bandwidth. ⚠️ Keyboards and mice (§8)
   ⚠️ BULK  ⚠️ large, reliable, NO timing guarantee — uses whatever
      bandwidth is left. Storage and printers
   ⚠️ ISOCHRONOUS  ⚠️ guaranteed BANDWIDTH and timing, NO error
      correction. ⚠️ Audio and video, where a late packet is
      worse than a lost one
⚠️ SPEEDS  Low 1.5 Mbps · Full 12 · High 480 · SuperSpeed 5 ·
   10 · 20 · ⚠️ USB4 40 and 80 (§25.1)
⚠️ ⚠️ THE NAMING DISASTER  ⚠️ USB 3.0 → 3.1 Gen 1 → 3.2 Gen 1x1
   all describe THE SAME 5 Gbps. ⚠️ The USB-IF renamed the same
   thing twice, and the current fix is to abandon version
   numbers for SPEED LABELS (§25.1)
⚠️ POWER  ⚠️ default 500 mA (USB 2) / 900 mA (USB 3) until
   negotiated. ⚠️ Everything above that requires PD (§3)
```

---

## §3. ⚠️ USB-C and Power Delivery

> **⚠️ The connector that solved the plug-orientation problem and created a capability-
> discovery problem.**
```
⚠️ THE CONNECTOR  24 pins, reversible, ⚠️ with the CC (Configuration
   Channel) pins doing orientation detection, role detection and
   PD communication
⚠️ ⚠️ USB-C IS A CONNECTOR, NOT A CAPABILITY. ⚠️ A USB-C port may
   carry USB 2.0 only. This is legal and common on cheap devices
⚠️ POWER DELIVERY  ⚠️ negotiated over CC using BMC-encoded
   messaging. ⚠️ Source advertises PDOs (power data objects),
   sink requests one
   ⚠️ FIXED PDOs at 5/9/15/20 V · ⚠️ PPS (programmable power
   supply) for fine-grained voltage — ⚠️ which is what enables
   efficient direct battery charging
   ⚠️ PD 3.1 EPR extends to 28/36/48 V for up to 240 W
⚠️ ⚠️ E-MARKER CHIPS  ⚠️ cables above 3 A contain a chip declaring
   their rating. ⚠️ A cable without one is limited to 3 A
   regardless of construction — the cable is an ACTIVE
   PARTICIPANT in the negotiation
⚠️ ⚠️ Vbus is 5 V UNTIL NEGOTIATED. ⚠️ This is the safety property
   that makes 48 V over a consumer connector acceptable
⚠️ DATA ROLE vs POWER ROLE are INDEPENDENT and swappable (DRP,
   DRD) — a laptop can charge from a monitor while sending video
⚠️ ⚠️ THE COUNTERFEIT PROBLEM  ⚠️ non-compliant cables and chargers
   have destroyed hardware. ⚠️ Certification and the USB-IF
   product database are the only real defence (§25.1)
```

---

## §4. Thunderbolt and Alternate Modes

**⚠️ ALT MODE** reconfigures USB-C's high-speed pins to carry a different protocol
entirely — ⚠️ **most importantly DisplayPort, which is how USB-C carries video** (§11 → `periph-buses-pcie-hid-keyboards-mice-and-displays`).
**⚠️ Thunderbolt** tunnels PCIe and DisplayPort over the same connector.
⚠️ **Thunderbolt 3 was contributed to USB4, which is why USB4 and Thunderbolt look so
similar; ⚠️ Thunderbolt 4 aligns closely with USB4 while MANDATING a feature set that USB4
leaves optional, and Thunderbolt 5 reaches 80 Gbps.**
> **⚠️ GOTCHA — the crucial difference is MANDATORY versus OPTIONAL.** ⚠️ **USB4 allows
> manufacturers to omit PCIe tunnelling and dual-display support to cut cost; Thunderbolt
> requires them.** **⚠️ So "USB4" tells you less about what a port can do than "Thunderbolt
> 4" does — a rare case where the proprietary standard is the clearer promise.**

**⚠️ PCIe tunnelling** is what makes eGPUs and external NVMe enclosures work, ⚠️ **and it
also creates a DMA security exposure that IOMMU protection exists to contain** (§24 → `periph-compliance-accessibility-and-security`).
**⚠️ Compatibility rules of thumb**: ⚠️ **Thunderbolt 4 and 5 hosts handle USB4 devices;
USB4 hosts support Thunderbolt 3 and 4 devices; Thunderbolt 3 hosts typically handle USB
devices only up to 10 Gbps.**

---

## §5. Wireless Peripherals

**⚠️ Bluetooth**: ⚠️ **Classic versus LE; ⚠️ HID over GATT for LE devices; ⚠️ and the
CONNECTION INTERVAL is the latency parameter that matters, negotiated between devices and
often conservative by default.**
**⚠️ Proprietary 2.4 GHz dongles** exist because ⚠️ **they can use shorter intervals,
frequency hopping tuned for latency rather than coexistence, and skip Bluetooth's
pairing and stack overhead — which is why competitive gaming peripherals ship dongles
rather than relying on Bluetooth.**
**⚠️ The real-world problems**: ⚠️ **2.4 GHz congestion (Wi-Fi, microwaves), USB 3 port
RADIATED NOISE desensitizing 2.4 GHz receivers (⚠️ a genuine and well-documented effect —
move the dongle away from USB 3 ports), latency variance rather than mean, and battery
management.**
**⚠️ Wireless is now competitive with wired for latency in good implementations** —
⚠️ **the remaining honest arguments for wired are power, reliability under congestion, and
not having a battery.**
