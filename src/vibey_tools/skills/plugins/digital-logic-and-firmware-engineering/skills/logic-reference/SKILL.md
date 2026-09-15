---
name: logic-reference
description: "Use when correcting a digital logic or firmware misconception, looking up a delay, voltage, power, setup-time or fault-coverage figure, finding the sources, or needing a quick-reference picker — plus the current state of the Secure Boot certificate expiry and open-source firmware and silicon roots of trust. Companion to the other digital logic and firmware skills."
---

# Digital Logic and Firmware: What's Live, Misconceptions, Numbers, and Sources

> **Part 5 of 5** of the *CMOS, Logic Gates and Firmware Engineering* reference (plugin `digital-logic-and-firmware-engineering`), covering §26–§31. Sibling skills: `logic-devices-transistors-cmos-gates-and-power` (§0–§8), `logic-standard-cells-boolean-minimization-and-arithmetic` (§9–§13), `logic-sequential-timing-metastability-cdc-and-hdl` (§14–§19), `logic-firmware-boot-root-of-trust-embedded-practice-and-security` (§20–§25). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Boolean algebra and CMOS circuit design do not change. Two things are moving. See §26 for the Secure Boot certificate expiry, and open-source firmware and silicon roots of trust.

> **⚠️ SCOPE, because this sits between existing neighbours.** ⚠️ **A semiconductor
> reference covers device physics and fabrication; a microarchitecture reference covers how
> gates become processors. Neither covers the two layers here: HOW TRANSISTORS BECOME
> BOOLEAN LOGIC, and HOW A MACHINE GETS FROM POWER-ON TO AN OPERATING SYSTEM.**
>
> **⚠️ These are the two ends of the stack where the abstractions are built, and where they
> most often leak.**
>
> **⚠️ GOTCHA** boxes mark where the textbook idealization and the real circuit diverge.
>
> **The three ideas that organize this document:**
> 1. **⚠️ CMOS COMPUTES BY CONNECTING, NOT BY AMPLIFYING** (§5 → `logic-devices-transistors-cmos-gates-and-power`). **A static CMOS gate is two
>    complementary switch networks, one connecting the output to power and one to ground,
>    never both. Once you see this, gate construction becomes mechanical and the power
>    behaviour becomes obvious.**
> 2. **⚠️ TIMING IS THE REAL CONSTRAINT, NOT LOGIC** (§15 → `logic-sequential-timing-metastability-cdc-and-hdl`, §17 → `logic-sequential-timing-metastability-cdc-and-hdl`). **Getting the Boolean
>    function right is the easy part. Setup and hold violations, clock skew and metastability
>    are what actually make digital systems fail, and they fail intermittently.**
> 3. **⚠️ TRUST IS A CHAIN THAT STARTS BEFORE ANY SOFTWARE RUNS** (§22 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security`, §25 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security`, §26). **Every
>    security property the OS provides rests on firmware that executed first. Firmware is
>    the most privileged and least examined code in the machine.**

---

## §26. What's Live — checked August 2026

### 26.1 ⚠️ The Secure Boot certificates expire — a fifteen-year clock running out
**⚠️ §22 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security`'s key hierarchy meeting a hard date, and it affects essentially every PC sold since
around 2012.**

- **⚠️ THE DATES, and these are specific.** ⚠️ **Microsoft's original 2011 Secure Boot
  certificates have 15-year validity and expire on a staggered schedule: Microsoft
  Corporation KEK CA 2011 on 24 June 2026; Microsoft Corporation UEFI CA 2011 (which signs
  third-party bootloaders including the Linux shim) on 27 June 2026; and Microsoft Windows
  Production PCA 2011 (which signs the Windows bootloader) on 19 October 2026.**
  ⚠️ **The replacements are the 2023 family — Windows UEFI CA 2023 and Microsoft Corporation
  KEK 2K CA 2023.**
- **⚠️ WHAT ACTUALLY BREAKS — and the answer is narrower than the alarm suggests.**
  ⚠️ **Red Hat states it plainly: systems with the 2011 certificate already enrolled will
  continue to boot after 27 June 2026, because the expiration affects the ability to SIGN
  NEW BINARIES, not to boot existing ones.** ⚠️ **Microsoft's framing is that devices will
  still boot but will lose the ability to install Secure Boot security updates — entering
  what one analysis calls a degraded security state.**
- **⚠️ WHY THE KEK MATTERS MOST.** ⚠️ **One security vendor makes the sharpest point: the
  KEK is the credential that authorizes Windows Update to push new entries to a device's
  allow list (DB) and deny list (DBX).** ⚠️ **Lose that and you lose the revocation
  mechanism — meaning newly discovered malicious bootloaders can no longer be blocked.**
- **⚠️ THE THREAT THIS PROTECTS AGAINST IS REAL AND CURRENT.** ⚠️ **Microsoft cites the
  BlackLotus UEFI bootkit (CVE-2023-24932) as an example of the unsecured boot path being
  used as an attack vector today, noting bootkit malware can be difficult or impossible to
  detect with standard antivirus.**

> **⚠️ GOTCHA — the operational problem is VISIBILITY, not the update itself.** ⚠️ **One
> vendor's assessment is that most enterprises cannot answer the basic question of which
> devices in their fleet still have the 2011 KEK — and that gap is the core of the
> problem.**
> ⚠️ **Most consumer devices receive the update automatically via Windows Update, but older
> systems may require an OEM FIRMWARE update, which is a different and much less reliable
> distribution channel.**
> **⚠️ It is not only Windows.** ⚠️ **Red Hat has released shim signed with BOTH the 2011 and
> 2023 certificates so it boots on machines with either enrolled; fwupd is being used to
> distribute updated certificates on Linux, noting that at least one major OEM will not ship
> the expired key on new hardware — so existing install media may not boot on some new
> machines.** ⚠️ **Google documents the same requirement for Compute Engine Shielded VMs,
> flagging it as critical for instances using full-disk encryption or secrets sealed to
> vTPM PCRs** (§22 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security`'s sealing).

**⚠️ Two forward-looking notes.** ⚠️ **The 2023 certificates are reported valid until 2038 —
so this recurs.** ⚠️ **And a post-quantum transition for the boot chain is reported as
separately underway, which is the same migration problem a cryptography reference describes
arriving in the least updateable code in the machine.**
**⚠️ Sourcing note: dates and mechanics come from Microsoft, Red Hat and Google
documentation directly, which agree.** ⚠️ **The most alarming framings come from a firmware
security vendor selling fleet visibility — the underlying KEK/revocation point is
nonetheless correct and worth taking seriously.**

### 26.2 ⚠️ Open-source firmware and open silicon roots of trust
**⚠️ §20 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security`'s uncomfortable truth being addressed from two directions at once.**

- **⚠️ CALIPTRA is the notable one, because it is open-source SILICON, not just firmware.**
  ⚠️ **Announced at OCP 2022 by Microsoft, Google and AMD, with NVIDIA joining, it is a
  reusable silicon-level root-of-trust IP block for datacentre-class SoCs — CPUs, GPUs,
  DPUs, TPUs, NICs and SSDs — and it is open source down to the RTL, along with the ROM and
  firmware.** ⚠️ **It now lives in the CHIPS Alliance.**
- **⚠️ THE SCOPE IS DELIBERATELY NARROW, which is why it may succeed.** ⚠️ **The project
  states the minimalist scope explicitly: define core RoT capabilities — identity, measured
  boot, attestation — and nothing else, to maximize composability, reuse across cloud
  providers and vendors, and the feasibility of open-sourcing at all.** ⚠️ **Caliptra 2.0
  defines a Root of Trust for Measurement baseline; the SoC must measure the code and
  configuration it boots into Caliptra.**
- **⚠️ CONCRETE NUMBERS from Caliptra 2.1**: ⚠️ **the complete subsystem totals 1,640,145
  gates, with approximately 62% dedicated to cryptographic accelerators, the key vault and
  key mover logic, and the remainder RISC-V cores and interface logic.** ⚠️ **That is a
  useful sanity check on what a hardware root of trust actually costs in area.**
- **⚠️ ADOPTION.** ⚠️ **AMD stated strategic plans to integrate Caliptra into its 2026+
  product lineup.** ⚠️ **One analysis reports that Microsoft and Google intend to make a
  Caliptra-based root of trust a REQUIREMENT for compute, networking and storage controller
  chips supplied to their datacentres — and that in new deployments Caliptra owns boot I/O,
  firmware layout, SoC sequencing, resets and DMA islands, with proprietary forked firmware
  not permitted.**
- **⚠️ ON THE PLATFORM FIRMWARE SIDE**: ⚠️ **AMD's openSIL abstracts silicon initialization
  so alternative bootloaders — coreboot, oreboot, LinuxBoot — can accept hand-off, replacing
  the assumption baked into AGESA and Intel FSP that UEFI comes next.** ⚠️ **AMD is explicit
  that openSIL is not intended to replace UEFI, but to enable alternatives.**
  ⚠️ **Concretely, Dasharo v0.9.0 is reported as the first officially released open-source
  firmware for a consumer AMD AM5 platform, combining coreboot with openSIL on an MSI
  PRO B850-P.**

> **⚠️ GOTCHA — "open source" here means auditable, not user-controlled, and the distinction
> matters.** ⚠️ **A Caliptra root of trust still enforces signatures against keys the SoC
> vendor or cloud operator controls; making the RTL public means the DESIGN can be
> inspected, not that you can run your own firmware on it.**
> ⚠️ **One analyst note is worth keeping in view: vendors with existing proprietary roots of
> trust — NVIDIA is named — are founding members while also keeping their own solutions, and
> "not every implementation may use Caliptra exclusively."** **⚠️ Expect coexistence rather
> than replacement.**
> **⚠️ And the consumer picture is far behind the datacentre one.** ⚠️ **A single
> motherboard being the FIRST consumer AM5 board with open-source firmware, in 2026, is the
> honest measure of how niche this remains outside hyperscale.**

**⚠️ Sourcing note: Caliptra material comes from the project's own repository and
specifications plus vendor blogs — all interested parties, though the gate counts and
architectural scope are checkable in the public RTL.** ⚠️ **The claim about hyperscaler
procurement requirements is from a paid analysis newsletter reporting conversations at OCP
and is marked accordingly.**

---

## §27. Misconceptions

| Misconception | Correction |
|---|---|
| AND and OR are the basic gates | ⚠️ **NAND and NOR are natural in CMOS; AND costs more** (§5 → `logic-devices-transistors-cmos-gates-and-power`) |
| A gate amplifies its input | ⚠️ **It connects the output to a rail. Two switch networks** (§5 → `logic-devices-transistors-cmos-gates-and-power`) |
| NOR and NAND are equivalent in cost | ⚠️ **NOR stacks weak pMOS in series. NAND preferred** (§5 → `logic-devices-transistors-cmos-gates-and-power`, §6 → `logic-devices-transistors-cmos-gates-and-power`) |
| nMOS and pMOS are mirror images | ⚠️ **Mobility differs 2-3×; pMOS must be wider** (§6 → `logic-devices-transistors-cmos-gates-and-power`) |
| A pass transistor passes the signal | ⚠️ **nMOS loses a threshold on a high. Use a transmission gate** (§3 → `logic-devices-transistors-cmos-gates-and-power`, §7 → `logic-devices-transistors-cmos-gates-and-power`) |
| CMOS uses no static power | ⚠️ **Was true. Leakage is now major** (§8 → `logic-devices-transistors-cmos-gates-and-power`) |
| Minimal gate count is the goal | ⚠️ **Synthesis optimizes timing, area and power together** (§11 → `logic-standard-cells-boolean-minimization-and-arithmetic`) |
| Hand-minimize before synthesis | ⚠️ **Usually makes results worse** (§11 → `logic-standard-cells-boolean-minimization-and-arithmetic`) |
| Redundant terms are always waste | ⚠️ **They eliminate hazards** (§11 → `logic-standard-cells-boolean-minimization-and-arithmetic`) |
| Latch and flip-flop are synonyms | ⚠️ **Level-sensitive vs edge-triggered. Different things** (§14 → `logic-sequential-timing-metastability-cdc-and-hdl`) |
| An incomplete if is harmless | ⚠️ **It infers a latch. Heed the warning** (§14 → `logic-sequential-timing-metastability-cdc-and-hdl`) |
| Slowing the clock fixes timing | ⚠️ **Setup yes. HOLD violations are broken at any speed** (§15 → `logic-sequential-timing-metastability-cdc-and-hdl`) |
| Metastability can be designed out | ⚠️ **Only made arbitrarily unlikely. No circuit eliminates it** (§15 → `logic-sequential-timing-metastability-cdc-and-hdl`) |
| Two flops synchronize any signal | ⚠️ **Single-bit level only. Multi-bit needs Gray/handshake/FIFO** (§17 → `logic-sequential-timing-metastability-cdc-and-hdl`) |
| It works on the bench, so CDC is fine | ⚠️ **CDC bugs are probabilistic. Run static CDC analysis** (§17 → `logic-sequential-timing-metastability-cdc-and-hdl`) |
| HDL is a programming language | ⚠️ **It describes hardware. Concurrent by default** (§18 → `logic-sequential-timing-metastability-cdc-and-hdl`) |
| Simulation passing means it works | ⚠️ **Blocking/non-blocking mismatch is silent** (§18 → `logic-sequential-timing-metastability-cdc-and-hdl`) |
| Verification and test are the same | ⚠️ **Is the design right vs was this die made right** (§19 → `logic-sequential-timing-metastability-cdc-and-hdl`) |
| Ripple carry is fine | ⚠️ **Linear delay. The carry chain is the problem** (§13 → `logic-standard-cells-boolean-minimization-and-arithmetic`) |
| Two's complement is a convention | ⚠️ **It lets one adder handle signed and unsigned** (§13 → `logic-standard-cells-boolean-minimization-and-arithmetic`) |
| BIOS is a small program | ⚠️ **UEFI is effectively an OS with drivers and a shell** (§21 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security`) |
| Firmware stops once the OS loads | ⚠️ **Runtime services persist and are callable** (§21 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security`) |
| Secure boot and measured boot are one thing | ⚠️ **One enforces, one records** (§22 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security`) |
| A valid signature means safe code | ⚠️ **Signed vulnerable bootloaders pass. Hence rollback protection** (§22 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security`) |
| Reinstalling the OS clears an infection | ⚠️ **Not a firmware one** (§25 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security`) |
| Firmware has little attack surface | ⚠️ **LogoFAIL: image parsers in firmware were exploitable** (§25 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security`) |
| Secure Boot certs expiring stops boot | ⚠️ **Existing systems keep booting. You lose signing and revocation** (§26.1) |
| Only Windows is affected | ⚠️ **The UEFI CA 2011 signs the Linux shim too** (§26.1) |
| Open-source RoT means you control it | ⚠️ **Auditable design, vendor-controlled keys** (§26.2) |

---

## §28. Numbers

```
⚠️ Silicon diode drop  ~0.7 V · ⚠️ Schottky ~0.3 V
⚠️ Hole vs electron mobility  ⚠️ ~2-3× lower → pMOS wider
⚠️ CMOS stack height  ⚠️ practically 3-4 series devices
⚠️ Logical effort optimum  ⚠️ fanout ≈ 4 per stage
⚠️ Dynamic power  ⚠️ P = α·C·V²·f
⚠️ Functional completeness  ⚠️ NAND alone, or NOR alone
⚠️ Metastability  ⚠️ MTBF improves EXPONENTIALLY with settling time
⚠️ Ripple carry delay  ⚠️ linear in width · lookahead logarithmic
⚠️ ⚠️ SECURE BOOT EXPIRY DATES
   ⚠️ Microsoft Corporation KEK CA 2011  ⚠️ 24 June 2026
   ⚠️ Microsoft Corporation UEFI CA 2011  ⚠️ 27 June 2026
      (signs third-party bootloaders incl. Linux shim)
   ⚠️ Microsoft Windows Production PCA 2011  ⚠️ 19 October 2026
   ⚠️ Replacements: 2023 family, reported valid to 2038
   ⚠️ Original validity  ⚠️ 15 years (issued 2011)
⚠️ Caliptra 2.1 subsystem  ⚠️ 1,640,145 gates
   ⚠️ ~62% crypto accelerators, key vault, key mover
⚠️ Dasharo v0.9.0  ⚠️ first open-source firmware for consumer AM5
```

---

## §29. Sources

| Source | Why |
|---|---|
| **Weste & Harris, *CMOS VLSI Design*** | ⚠️ **§5–§9 → `logic-devices-transistors-cmos-gates-and-power`, `logic-standard-cells-boolean-minimization-and-arithmetic`. Logical effort is Harris's** |
| **Rabaey, *Digital Integrated Circuits*** | The other standard for circuit-level CMOS |
| **Harris & Harris, *Digital Design and Computer Architecture*** | ⚠️ **§10–§18 → `logic-standard-cells-boolean-minimization-and-arithmetic`, `logic-sequential-timing-metastability-cdc-and-hdl`, and the best entry point** |
| **Wakerly, *Digital Design: Principles and Practices*** | §10–§16 → `logic-standard-cells-boolean-minimization-and-arithmetic`, `logic-sequential-timing-metastability-cdc-and-hdl`, thorough |
| **Cummings' CDC and Verilog papers (SNUG)** | ⚠️ **§17–§18 → `logic-sequential-timing-metastability-cdc-and-hdl` — free, and the definitive practitioner writing** |
| **Horowitz & Hill, *The Art of Electronics*** | ⚠️ **§2–§3 → `logic-devices-transistors-cmos-gates-and-power`, §7 → `logic-devices-transistors-cmos-gates-and-power` interfacing. Unmatched** |
| **UEFI Specification (uefi.org)** | ⚠️ **§21–§23 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security`, primary and free** |
| **TCG TPM specifications** | ⚠️ **§22 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security`** |
| **coreboot, U-Boot and Zephyr documentation** | ⚠️ **§21 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security`, §24 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security` — real firmware you can read** |
| **Caliptra repository and OCP specifications** | ⚠️ **§26.2, primary** |
| **Microsoft, Red Hat and Google Secure Boot guidance** | ⚠️ **§26.1 — go to these, not to summaries** |

---

## §30. Quick Reference

### 30.1 Picker
| Question | Where |
|---|---|
| How do I build gate X in CMOS? | ⚠️ **PDN from the expression, PUN is its dual** (§5 → `logic-devices-transistors-cmos-gates-and-power`) |
| Why is my path slow? | ⚠️ **Load capacitance and drive. Logical effort** (§6 → `logic-devices-transistors-cmos-gates-and-power`) |
| Where is the power going? | ⚠️ **Clock network, then leakage, then glitches** (§8 → `logic-devices-transistors-cmos-gates-and-power`) |
| Design won't meet timing | ⚠️ **Setup: pipeline or resize. Hold: add delay** (§15 → `logic-sequential-timing-metastability-cdc-and-hdl`) |
| Intermittent failure in the field | ⚠️ **Suspect CDC and metastability first** (§15 → `logic-sequential-timing-metastability-cdc-and-hdl`, §17 → `logic-sequential-timing-metastability-cdc-and-hdl`) |
| Synthesis inferred a latch | ⚠️ **Incomplete if/case in combinational logic** (§14 → `logic-sequential-timing-metastability-cdc-and-hdl`) |
| Simulation passes, hardware fails | ⚠️ **Blocking vs non-blocking, or CDC** (§17 → `logic-sequential-timing-metastability-cdc-and-hdl`, §18 → `logic-sequential-timing-metastability-cdc-and-hdl`) |
| Board is dead at power-on | ⚠️ **Rails, reset, then the boot stages in order** (§21 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security`) |
| Never reaches main() | ⚠️ **Vector table, stack, BSS/data init** (§24 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security`) |
| Sleep or wake broken | ⚠️ **ACPI tables and D/C/S states** (§23 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security`) |
| Is my machine's boot chain trusted? | ⚠️ **PK/KEK/DB/DBX state, and TPM PCRs** (§22 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security`) |
| Do I need to act before June 2026? | ⚠️ **Check KEK/DB for 2023 certs. Enterprise: audit the fleet** (§26.1) |

### 30.2 Design checks
- [ ] ⚠️ **Every combinational block fully specified — no inferred latches** (§14 → `logic-sequential-timing-metastability-cdc-and-hdl`)
- [ ] ⚠️ **All CDC paths identified and correctly synchronized by TYPE** (§17 → `logic-sequential-timing-metastability-cdc-and-hdl`)
- [ ] ⚠️ **Static CDC analysis run, not just simulation** (§17 → `logic-sequential-timing-metastability-cdc-and-hdl`)
- [ ] Reset strategy defined; async de-assertion synchronized (§14 → `logic-sequential-timing-metastability-cdc-and-hdl`)
- [ ] ⚠️ **Timing closed at all PVT corners, setup AND hold** (§4 → `logic-devices-transistors-cmos-gates-and-power`, §15 → `logic-sequential-timing-metastability-cdc-and-hdl`)
- [ ] Clock gating applied; activity factors considered (§8 → `logic-devices-transistors-cmos-gates-and-power`)
- [ ] FSMs have a safe default for illegal states (§16 → `logic-sequential-timing-metastability-cdc-and-hdl`)
- [ ] ⚠️ **DFT inserted and coverage measured** (§19 → `logic-sequential-timing-metastability-cdc-and-hdl`)
- [ ] **Firmware side:**
- [ ] ⚠️ **Root of trust is genuinely immutable** (§22 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security`)
- [ ] ⚠️ **Rollback protection present — signatures alone are insufficient** (§22 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security`)
- [ ] ⚠️ **Update is atomic, power-fail safe, with a recovery path** (§24 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security`)
- [ ] ⚠️ **SPI write protection configured** (§25 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security`)
- [ ] Watchdog fed from proof of correct operation, not a bare timer (§24 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security`)
- [ ] ⚠️ **Secure Boot certificate state audited ahead of June 2026** (§26.1)

---

## §31. Method

**§1–§25 → `logic-devices-transistors-cmos-gates-and-power`, `logic-standard-cells-boolean-minimization-and-arithmetic`, `logic-sequential-timing-metastability-cdc-and-hdl`, `logic-firmware-boot-root-of-trust-embedded-practice-and-security` rests on settled material** — **Boolean algebra, static CMOS construction, the
setup/hold constraint, metastability, the CDC techniques, the UEFI phase model and the
verified-boot key hierarchy.** ⚠️ **None needed verification; De Morgan published in 1847
and the complementary-network construction has been the basis of digital design since the
1960s.**

**⚠️ On scope: I deliberately did not re-derive device physics or fabrication (a
semiconductor reference), nor how gates compose into processors (a microarchitecture
reference).** ⚠️ **What is here is the gate level and the boot level — the two layers those
files assume rather than explain.**

**Two searches were run in August 2026**, on **the Secure Boot certificate expiry** and
**open-source firmware and roots of trust** — ⚠️ **the first because it is a hard-dated
event affecting essentially every PC sold since 2012 and the consequences are widely
misreported, the second because §20 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security`'s uncomfortable truth about unexaminable privileged
code is finally being addressed.**

**Confidence.** **High** in §5 → `logic-devices-transistors-cmos-gates-and-power` and §15 → `logic-sequential-timing-metastability-cdc-and-hdl`, which are the sections I'd most want read.
⚠️ **The complementary-network construction is the most useful single idea here: once you
see that a gate is two mutually exclusive switch networks and that the PUN is the dual of
the PDN, you can draw any gate mechanically — and it immediately explains why NAND and NOR
are the natural primitives and why AND costs more than NAND, which is backwards from how
Boolean algebra is taught.**
⚠️ **§15 → `logic-sequential-timing-metastability-cdc-and-hdl`'s setup-versus-hold asymmetry is the second and it has real consequences: a setup
violation is fixed by slowing the clock, a hold violation is a broken chip at ANY frequency.
Knowing which you have determines whether you have a tuning problem or a respin.**
**⚠️ §17 → `logic-sequential-timing-metastability-cdc-and-hdl`'s warning that a two-flop synchronizer is for single-bit level signals ONLY is the
correction that prevents the worst class of intermittent field failure.**

**High** on §26.1, which is unusually well-sourced because Microsoft, Red Hat and Google all
publish on it and agree on the dates and mechanics. ⚠️ **The correction I'd most want
carried is Red Hat's: systems keep booting — what expires is the ability to SIGN new
binaries and, via the KEK, to UPDATE the allow and deny lists.** ⚠️ **That is a serious loss,
because it removes the revocation path that blocks newly discovered bootkits, but it is not
the "your PC won't start" framing that circulates.** **⚠️ The most urgent-sounding analysis
comes from a firmware-security vendor selling fleet visibility; the KEK point it makes is
correct regardless.**

**Moderate-to-high** on §26.2. ⚠️ **Caliptra's architecture, minimalist scope and gate
counts come from the project's own specifications and repository, which are public and
checkable.** ⚠️ **AMD's stated 2026+ integration plan is from AMD directly.** **⚠️ The claim
that hyperscalers will REQUIRE Caliptra of their chip suppliers is from a paid analyst
newsletter reporting OCP conversations, and I have marked it as reported rather than
treating it as established.** ⚠️ **The framing I'd defend is the gotcha: open RTL means the
design is auditable, not that you control the keys — and one motherboard being the first
consumer AM5 board with open firmware in 2026 is the honest measure of how far this is from
mainstream.**
