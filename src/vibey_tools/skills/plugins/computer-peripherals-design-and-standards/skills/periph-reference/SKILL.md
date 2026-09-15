---
name: periph-reference
description: "Use when correcting a peripheral misconception, looking up a bandwidth, power, polling-rate or latency figure, finding the sources, or needing a quick-reference picker — plus the current state of USB bandwidth and labelling and display interface bandwidth tiers. Companion to the other peripherals skills."
---

# Computer Peripherals: What's Live, Misconceptions, Numbers, and Sources

> **Part 6 of 6** of the *Computer Peripherals: Design, Building, Standards and Programming* reference (plugin `computer-peripherals-design-and-standards`), covering §25–§30. Sibling skills: `periph-stack-usb-thunderbolt-and-wireless` (§0–§5), `periph-buses-pcie-hid-keyboards-mice-and-displays` (§6–§11), `periph-audio-printers-storage-controllers-and-haptics` (§12–§15), `periph-designing-firmware-pcb-and-debugging` (§16–§21), `periph-compliance-accessibility-and-security` (§22–§24). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The protocols are stable and long-lived. Two areas are moving. See §25 for USB bandwidth and labelling, and display interface bandwidth tiers.

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
> 1. **⚠️ THE CONNECTOR IS NOT THE PROTOCOL** (§2 → `periph-stack-usb-thunderbolt-and-wireless`, §3 → `periph-stack-usb-thunderbolt-and-wireless`, §25.1). **A USB-C port can be
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

## §25. What's Live — checked August 2026

### 25.1 ⚠️ USB bandwidth, and the labelling reform
**⚠️ §2 → `periph-stack-usb-thunderbolt-and-wireless`'s naming disaster finally being addressed — and §3 → `periph-stack-usb-thunderbolt-and-wireless`'s power ceiling now in shipping
products.**

- **⚠️ THE SPEC.** ⚠️ **USB4 Version 2.0 was published by the USB Promoter Group to enable
  80 Gbps over the existing USB-C cable and connector, based on a new physical layer
  architecture, doubling the previous maximum aggregate bandwidth.** ⚠️ **USB-IF's own
  announcement notes it can optionally run ASYMMETRICALLY — up to 120 Gbps in one direction
  while retaining 40 Gbps in the other — specifically for driving very high-performance
  displays.**
- **⚠️ WHAT ELSE THE VERSION 2.0 UPDATE CARRIES**: ⚠️ **PCIe tunnelling advancing to Gen4,
  doubling per-lane throughput for external SSDs and eGPU enclosures relative to Gen3
  tunnelling in USB4 v1; and DisplayPort tunnelling advancing to DisplayPort 2.1 with
  UHBR20 signaling** (§25.2). ⚠️ **Backward compatibility with USB4 v1, Thunderbolt 3 and
  Thunderbolt 4 is retained, with those devices falling back to older signaling.**
- **⚠️ THE LABELLING REFORM.** ⚠️ **The USB-IF has shifted from version-based branding to
  explicit capability identifiers: "USB 40Gbps", "USB 80Gbps" and "240W" markings on
  certified cables and packaging.** ⚠️ **The USB-IF states plainly that specification names
  and technical terminology are NOT intended for describing capabilities to end
  consumers.**
- **⚠️ POWER.** ⚠️ **Power Delivery can negotiate up to 240 W on capable ports under PD 3.1,
  using voltages up to 48 V.**

> **⚠️ GOTCHA — the cable is now a first-class variable, and length is the physical
> limit.** ⚠️ **Passive USB4 40 Gbps cables are commonly limited to around 0.8 m; reporting
> indicates many certified passive USB-C cables up to one metre support 80 Gbps, with
> anything longer typically requiring ACTIVE RETIMERS.**
> ⚠️ **Those active cables contain embedded signal processing and SOMETIMES OPERATE
> DIRECTIONALLY — which introduces real design considerations for hubs and monitors, and
> means an active cable is not simply a longer passive one.**
> **⚠️ The counterfeit problem is the practical hazard.** ⚠️ **Guidance is to look for
> laser-etched USB-IF logos, a scannable code linking to the certification database, and
> explicit text markings — and to treat "USB4-compatible" phrasing and printed-not-etched
> logos as red flags.**

**⚠️ My honest assessment of the reform**: ⚠️ **the shift to speed-and-wattage labels is the
right fix and directly addresses §2 → `periph-stack-usb-thunderbolt-and-wireless`'s problem, but as one outlet notes, adoption depends on
consistent enforcement by manufacturers and retailers — and the older Gen-x-by-y
terminology remains in circulation alongside it.** ⚠️ **Practical advice unchanged: check
the PORT spec, the CABLE spec and the DEVICE spec separately, because the slowest link
governs and a fast cable cannot upgrade a slow port.**

### 25.2 ⚠️ Display interfaces: the bandwidth tiers matter more than the version badge
**⚠️ §11 → `periph-buses-pcie-hid-keyboards-mice-and-displays`'s interface question, and the trap is buying on the version number.**

- **⚠️ DISPLAYPORT 2.1's TIERS.** ⚠️ **UHBR10, UHBR13.5 and UHBR20, with UHBR20 giving four
  lanes at 20 Gbps for 80 Gbps total link bandwidth.** ⚠️ **DisplayPort 2.1 uses 128b/132b
  encoding rather than the older 8b/10b, substantially reducing overhead so more of the raw
  rate is usable.**
- **⚠️ THE BADGE DOES NOT TELL YOU THE TIER — this is the central practical point.**
  ⚠️ **A device can carry a DisplayPort 2.1 badge while implementing only UHBR13.5.**
  ⚠️ **One guide's framing is right: the 2026 DP 2.1 ecosystem "rewards precise matching
  over blanket assumptions about the DP 2.1 badge."**
- **⚠️ CABLES ARE CERTIFIED SEPARATELY AND BY TIER.** ⚠️ **VESA-certified DP80 cables must
  support UHBR20 across four lanes for 80 Gbps; DP54 supports UHBR13.5 for 54 Gbps over a
  two-metre passive cable.** ⚠️ **Passive DP80 is reliable to roughly one metre — reporting
  notes in-box cables with UHBR20 monitors are often only 1 m — and VESA introduced
  DP80LL "low loss" ACTIVE cables to give up to three metres at UHBR20, roughly triple the
  passive length.**
- **⚠️ HDMI 2.2** was introduced at CES 2025 with an "Ultra96" certified cable programme and
  QR-code verification. ⚠️ **Note the adoption lag: reporting observes it took about two
  years from HDMI 2.1 to the first supported TVs and around four years to widespread
  adoption — so a new HDMI version number is a multi-year signal, not a this-year one.**

> **⚠️ GOTCHA — DSC is not the compromise people assume, and the honest comparison is
> narrower than the marketing.** ⚠️ **DSC is a hardware, visually lossless algorithm applying
> roughly 3:1 compression with latency in MICROSECONDS — categorically different from
> streaming video compression.**
> ⚠️ **UHBR20 is described as currently the only interface able to drive 4K 240 Hz 10-bit
> HDR uncompressed, while UHBR13.5 reaches 4K 240 Hz WITH DSC and handles roughly 187 Hz at
> 10-bit HDR uncompressed.** ⚠️ **The reported practical differences from going uncompressed
> are avoiding occasional alt-tab black screens and handshake quirks — not image quality.**
> **⚠️ And the ceiling still applies: even UHBR20 reportedly requires DSC for the most
> extreme modes.**
> ⚠️ **So the reasonable position is that DSC is fine for almost everyone, and UHBR20 is
> worth paying for only if you have confirmed the whole chain — GPU, monitor input AND
> certified cable — supports it and you specifically want an uncompressed path.**

**⚠️ Sourcing note: VESA and the USB-IF primary announcements anchor the specifications, and
TFTCentral is the most technically careful independent source on DisplayPort certification
in practice.** ⚠️ **Several other sources here are monitor and cable vendors, whose framing
favours buying the higher tier — I have marked the practical claims as reported and stated
the more conservative reading.**

---

## §26. Misconceptions

| Misconception | Correction |
|---|---|
| USB-C means fast | ⚠️ **It's a connector. Can be USB 2.0 only** (§3 → `periph-stack-usb-thunderbolt-and-wireless`) |
| All USB-C cables are equivalent | ⚠️ **Speed, power and video are separate capabilities** (§3 → `periph-stack-usb-thunderbolt-and-wireless`, §25.1) |
| A better cable speeds up a slow port | ⚠️ **The slowest link governs** (§25.1) |
| USB 3.0, 3.1 Gen 1 and 3.2 Gen 1x1 differ | ⚠️ **Same 5 Gbps, renamed twice** (§2 → `periph-stack-usb-thunderbolt-and-wireless`) |
| Cables are passive wire | ⚠️ **Above 3 A they carry an e-marker chip and negotiate** (§3 → `periph-stack-usb-thunderbolt-and-wireless`) |
| USB-C always carries 20 V | ⚠️ **5 V until negotiated. That's the safety property** (§3 → `periph-stack-usb-thunderbolt-and-wireless`) |
| USB4 and Thunderbolt 4 are the same | ⚠️ **USB4 makes PCIe and dual-display optional** (§4 → `periph-stack-usb-thunderbolt-and-wireless`) |
| 6KRO is a hardware limitation | ⚠️ **It's the HID boot protocol report format** (§8 → `periph-buses-pcie-hid-keyboards-mice-and-displays`, §9 → `periph-buses-pcie-hid-keyboards-mice-and-displays`) |
| "Anti-ghosting" means NKRO | ⚠️ **Usually blocking. True NKRO needs per-switch diodes** (§9 → `periph-buses-pcie-hid-keyboards-mice-and-displays`) |
| Higher DPI is better | ⚠️ **Interpolated past a point. Accuracy is the real spec** (§10 → `periph-buses-pcie-hid-keyboards-mice-and-displays`) |
| 8 kHz polling is a big upgrade | ⚠️ **Saves under 1 ms. The display is the bigger term** (§21 → `periph-designing-firmware-pcb-and-debugging`) |
| Wireless is inherently laggy | ⚠️ **Good implementations are competitive; variance is the issue** (§5 → `periph-stack-usb-thunderbolt-and-wireless`) |
| Dongle problems are the dongle's fault | ⚠️ **USB 3 ports radiate noise into 2.4 GHz** (§5 → `periph-stack-usb-thunderbolt-and-wireless`) |
| DSC is like streaming compression | ⚠️ **Hardware, visually lossless, microsecond latency** (§11 → `periph-buses-pcie-hid-keyboards-mice-and-displays`, §25.2) |
| Quoted response time is real | ⚠️ **Best-case GtG with overdrive artifacts** (§11 → `periph-buses-pcie-hid-keyboards-mice-and-displays`) |
| "10-bit" panel means 10-bit | ⚠️ **Often 8-bit + FRC dithering** (§11 → `periph-buses-pcie-hid-keyboards-mice-and-displays`) |
| A DisplayPort 2.1 badge means 80 Gbps | ⚠️ **It may be UHBR13.5. Check the tier** (§25.2) |
| Higher sample rates sound better | ⚠️ **Bit depth is dynamic range; rate is bandwidth** (§12 → `periph-audio-printers-storage-controllers-and-haptics`) |
| Device-not-recognized means broken hardware | ⚠️ **Usually a descriptor or power problem** (§19 → `periph-designing-firmware-pcb-and-debugging`) |
| A valid descriptor means a working device | ⚠️ **Malformed descriptors fail silently** (§8 → `periph-buses-pcie-hid-keyboards-mice-and-displays`, §19 → `periph-designing-firmware-pcb-and-debugging`) |
| Test on one OS is enough | ⚠️ **Each parses descriptors differently** (§19 → `periph-designing-firmware-pcb-and-debugging`) |
| You need a custom driver | ⚠️ **If HID fits, you get every OS free** (§8 → `periph-buses-pcie-hid-keyboards-mice-and-displays`, §16 → `periph-designing-firmware-pcb-and-debugging`) |
| Any VID/PID will do for a product | ⚠️ **VIDs are issued and cost money. Don't squat** (§16 → `periph-designing-firmware-pcb-and-debugging`) |
| Mouse double-click means replace it | ⚠️ **Switch wear. Repairable** (§10 → `periph-buses-pcie-hid-keyboards-mice-and-displays`) |
| Stick drift is unavoidable | ⚠️ **Potentiometer wear. Hall-effect eliminates it** (§15 → `periph-audio-printers-storage-controllers-and-haptics`) |
| USB is a trusted connection | ⚠️ **No device authentication. A stick can claim to be a keyboard** (§24 → `periph-compliance-accessibility-and-security`) |
| USB4 improved the security model | ⚠️ **Adds capability, not authentication** (§24 → `periph-compliance-accessibility-and-security`) |

---

## §27. Numbers

```
⚠️ USB topology  127 devices · 7 tiers · host-polled
⚠️ USB speeds  1.5 / 12 / 480 Mbps · 5 / 10 / 20 / 40 / 80 Gbps
⚠️ USB default current  500 mA (USB2) · 900 mA (USB3) pre-negotiation
⚠️ E-marker required  ⚠️ above 3 A
⚠️ PD 3.1 EPR  ⚠️ up to 240 W, voltages to 48 V
⚠️ USB4 v2  ⚠️ 80 Gbps symmetric · ⚠️ optional 120/40 asymmetric
⚠️ Passive USB-C at 80 Gbps  ⚠️ ~1 m; longer needs active retimers
⚠️ Passive USB4 40 Gbps cable  ⚠️ commonly ~0.8 m
⚠️ USB polling  ⚠️ 125 Hz = 8 ms · 1000 Hz = 1 ms · 8 kHz = 0.125 ms
⚠️ 60 Hz display scanout  ⚠️ ~8 ms average — the bigger latency term
⚠️ DP 2.1 tiers  UHBR10 · UHBR13.5 (54 Gbps) · UHBR20 (80 Gbps)
⚠️ DP encoding  ⚠️ 128b/132b (was 8b/10b)
⚠️ DP80 passive  ~1 m · ⚠️ DP80LL active up to 3 m
⚠️ DSC  ⚠️ ~3:1, hardware, microsecond latency
⚠️ UHBR20 uncompressed ceiling  ⚠️ 4K 240 Hz 10-bit HDR
⚠️ UHBR13.5 uncompressed  ⚠️ ~187 Hz at 4K 10-bit HDR (reported)
⚠️ HDMI 2.1 → first TVs  ⚠️ ~2 yr; widespread ~4 yr (reported)
⚠️ USB D+/D− impedance  ⚠️ 90 Ω differential
```

---

## §28. Sources

| Source | Why |
|---|---|
| **USB-IF specifications and product database** | ⚠️ **§2–§3 → `periph-stack-usb-thunderbolt-and-wireless`, primary and free** |
| **USB HID Usage Tables and HID spec** | ⚠️ **§8 → `periph-buses-pcie-hid-keyboards-mice-and-displays`. Read the usage tables directly** |
| **VESA DisplayPort resources** | ⚠️ **§11 → `periph-buses-pcie-hid-keyboards-mice-and-displays`, §25.2, primary** |
| **TFTCentral** | ⚠️ **§11 → `periph-buses-pcie-hid-keyboards-mice-and-displays`, §25.2 — the careful independent display source** |
| **QMK and ZMK documentation** | ⚠️ **§17 → `periph-designing-firmware-pcb-and-debugging`. Excellent, and free** |
| **TinyUSB** | ⚠️ **§17 → `periph-designing-firmware-pcb-and-debugging`, portable USB stack with readable source** |
| **Axelson, *USB Complete*** | The standard practical book |
| **Rtings** | ⚠️ **§11 → `periph-buses-pcie-hid-keyboards-mice-and-displays` — measured display data, not spec sheets** |
| **Chris Gammell, *Contextual Electronics*** | §18 → `periph-designing-firmware-pcb-and-debugging`, practical PCB work |
| **Blum, *Exploring Arduino* / Raspberry Pi Pico docs** | §16–§17 → `periph-designing-firmware-pcb-and-debugging` entry points |
| **Your national EMC guidance and IEC 62368-1** | ⚠️ **§22 → `periph-compliance-accessibility-and-security` — read before designing, not after** |

---

## §29. Quick Reference

### 29.1 Picker
| Question | Where |
|---|---|
| Will this cable do what I need? | ⚠️ **Check speed, power AND video separately** (§3 → `periph-stack-usb-thunderbolt-and-wireless`, §25.1) |
| Why won't my device enumerate? | ⚠️ **Read the descriptors first** (§19 → `periph-designing-firmware-pcb-and-debugging`) |
| Why does my keyboard fail in BIOS? | ⚠️ **NKRO vs boot protocol** (§8 → `periph-buses-pcie-hid-keyboards-mice-and-displays`, §9 → `periph-buses-pcie-hid-keyboards-mice-and-displays`) |
| Do I need a driver? | ⚠️ **If HID fits, no** (§8 → `periph-buses-pcie-hid-keyboards-mice-and-displays`, §16 → `periph-designing-firmware-pcb-and-debugging`) |
| Why is my input laggy? | ⚠️ **Measure the whole chain; suspect the display** (§21 → `periph-designing-firmware-pcb-and-debugging`) |
| Is 8 kHz polling worth it? | ⚠️ **Under 1 ms. Almost never the limit** (§21 → `periph-designing-firmware-pcb-and-debugging`) |
| Wireless or wired? | ⚠️ **Latency is close now; power and congestion decide** (§5 → `periph-stack-usb-thunderbolt-and-wireless`) |
| Do I need UHBR20? | ⚠️ **Only for confirmed uncompressed 4K 240 Hz+** (§25.2) |
| Is DSC bad? | ⚠️ **No. Visually lossless, microseconds** (§11 → `periph-buses-pcie-hid-keyboards-mice-and-displays`, §25.2) |
| Why did my drive slow down? | ⚠️ **Hub shares upstream bandwidth** (§14 → `periph-audio-printers-storage-controllers-and-haptics`) |
| Is this USB stick safe to plug in? | ⚠️ **It can claim to be a keyboard. Don't** (§24 → `periph-compliance-accessibility-and-security`) |
| What MCU for a custom HID device? | ⚠️ **Native USB peripheral; RP2040/STM32/nRF52** (§16 → `periph-designing-firmware-pcb-and-debugging`) |

### 29.2 Custom peripheral checklist
- [ ] ⚠️ **Device class chosen — HID if at all possible** (§8 → `periph-buses-pcie-hid-keyboards-mice-and-displays`, §16 → `periph-designing-firmware-pcb-and-debugging`)
- [ ] ⚠️ **Report descriptor validated, not just compiled** (§8 → `periph-buses-pcie-hid-keyboards-mice-and-displays`, §19 → `periph-designing-firmware-pcb-and-debugging`)
- [ ] ⚠️ **Correct usage page and usages for the device KIND** (§8 → `periph-buses-pcie-hid-keyboards-mice-and-displays`)
- [ ] Endpoint type matches the traffic pattern (§2 → `periph-stack-usb-thunderbolt-and-wireless`)
- [ ] ⚠️ **Current draw declared honestly and inrush handled** (§19 → `periph-designing-firmware-pcb-and-debugging`)
- [ ] ⚠️ **90 Ω differential pairs, matched, continuous ground plane** (§18 → `periph-designing-firmware-pcb-and-debugging`)
- [ ] ⚠️ **ESD protection on every exposed line** (§18 → `periph-designing-firmware-pcb-and-debugging`)
- [ ] Connector mechanically retained (§18 → `periph-designing-firmware-pcb-and-debugging`)
- [ ] ⚠️ **Legitimate VID/PID — not squatted** (§16 → `periph-designing-firmware-pcb-and-debugging`)
- [ ] ⚠️ **Bootloader with a hardware recovery path** (§17 → `periph-designing-firmware-pcb-and-debugging`)
- [ ] ⚠️ **Tested on Windows, macOS, Linux AND in BIOS** (§19 → `periph-designing-firmware-pcb-and-debugging`)
- [ ] ⚠️ **Onboard profile storage so it works without vendor software** (§20 → `periph-designing-firmware-pcb-and-debugging`)
- [ ] Remappable, and doesn't rely on colour alone (§23 → `periph-compliance-accessibility-and-security`)
- [ ] ⚠️ **Pre-compliance EMC scan before booking a chamber** (§22 → `periph-compliance-accessibility-and-security`)

---

## §30. Method

**§1–§24 → `periph-stack-usb-thunderbolt-and-wireless`, `periph-buses-pcie-hid-keyboards-mice-and-displays`, `periph-audio-printers-storage-controllers-and-haptics`, `periph-designing-firmware-pcb-and-debugging`, `periph-compliance-accessibility-and-security` rests on long-stable specifications and mature practice** — **USB's transfer
types and enumeration sequence, the HID descriptor model, matrix scanning and NKRO, panel
technologies, PCB signal integrity, and the BadUSB trust-model problem.** ⚠️ **None needed
verification; the HID class specification and USB's host-polled architecture have been
fixed for decades.**

**Two searches were run in August 2026**, on **USB bandwidth and labelling** and **display
interface tiers** — ⚠️ **both because they are exactly where §1 → `periph-stack-usb-thunderbolt-and-wireless`'s first organizing idea
bites: the connector and the version badge have both become detached from actual
capability, and buyers and designers get caught by it constantly.**

**Confidence.** **High** in §8 → `periph-buses-pcie-hid-keyboards-mice-and-displays` and §19 → `periph-designing-firmware-pcb-and-debugging`, which are the sections I'd most want read.
⚠️ **The descriptor model is the key that unlocks the whole domain — a device declares what
it is, the host adapts, and that is simultaneously why peripherals work driver-free and why
almost every development failure is a descriptor problem that fails silently.**
⚠️ **§21 → `periph-designing-firmware-pcb-and-debugging`'s latency arithmetic is the second, because it is where enthusiast spending most
reliably goes to the wrong link: 1000 Hz to 8000 Hz polling saves under a millisecond while
a 60 Hz display contributes around eight.** **§9 → `periph-buses-pcie-hid-keyboards-mice-and-displays`'s 6KRO explanation is the small correction
I most enjoy — it is not a hardware limit at all, it is the shape of the HID boot report.**

**High** on §25.1's specification claims, which come from USB-IF and USB Promoter Group
announcements directly: ⚠️ **USB4 Version 2.0 at 80 Gbps with optional 120/40 asymmetric
operation, PCIe Gen4 and DisplayPort 2.1 tunnelling, and the explicit statement that
specification names are not intended for consumer-facing description.**
⚠️ **The cable-length physics — roughly a metre passive at 80 Gbps, active retimers beyond,
and some active cables being DIRECTIONAL — is the part with real design consequences and is
consistently reported.** **⚠️ Counterfeit-detection guidance comes from a cable vendor and
is marked as such.**

**High** on §25.2's specifications, anchored on VESA's own announcements and TFTCentral:
⚠️ **DP80 certification requiring four-lane UHBR20 for 80 Gbps, DP54 for UHBR13.5, DP80LL
active cables tripling passive length to three metres, and 128b/132b encoding.**
⚠️ **The framing I'd defend is the conservative one: the version badge does not tell you the
tier, and DSC is genuinely fine for almost everyone — the uncompressed path buys freedom
from handshake quirks rather than image quality.** **⚠️ Several sources in that section are
monitor and cable vendors with an interest in selling the higher tier, and the HDMI 2.2
adoption-lag point is the useful corrective: a new version number is a multi-year signal,
not a this-year one.**
