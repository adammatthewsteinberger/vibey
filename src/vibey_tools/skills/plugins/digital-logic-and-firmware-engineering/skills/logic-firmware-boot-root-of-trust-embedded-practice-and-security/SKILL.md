---
name: logic-firmware-boot-root-of-trust-embedded-practice-and-security
description: "Use for firmware: the firmware landscape from UEFI to embedded RTOS and bare metal, the boot sequence stage by stage, root of trust and verified boot with the chain of signatures, ACPI and the platform interfaces that hand control to the OS, embedded firmware practice including interrupts, DMA and update strategy, and firmware security — the attack surface, persistence and why firmware compromise is so hard to detect."
---

# Digital Logic and Firmware: The Firmware Landscape, the Boot Sequence, Root of Trust and Verified Boot, ACPI and Platform Interfaces, Embedded Firmware Practice, and Firmware Security

> **Part 4 of 5** of the *CMOS, Logic Gates and Firmware Engineering* reference (plugin `digital-logic-and-firmware-engineering`), covering §20–§25. Sibling skills: `logic-devices-transistors-cmos-gates-and-power` (§0–§8), `logic-standard-cells-boolean-minimization-and-arithmetic` (§9–§13), `logic-sequential-timing-metastability-cdc-and-hdl` (§14–§19), `logic-reference` (§26–§31). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Boolean algebra and CMOS circuit design do not change. Two things are moving. See §26 → `logic-reference` for the Secure Boot certificate expiry, and open-source firmware and silicon roots of trust.

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
> 3. **⚠️ TRUST IS A CHAIN THAT STARTS BEFORE ANY SOFTWARE RUNS** (§22, §25, §26 → `logic-reference`). **Every
>    security property the OS provides rests on firmware that executed first. Firmware is
>    the most privileged and least examined code in the machine.**

---

## §20. The Firmware Landscape

```
⚠️ WHAT COUNTS AS FIRMWARE  ⚠️ far more than "the BIOS" —
   ⚠️ platform firmware (UEFI/BIOS) · embedded controller ·
   ⚠️ management engine / PSP (⚠️ a separate processor with
   higher privilege than the CPU, running code you cannot
   inspect) · ⚠️ BMC/service processor · storage controller
   firmware · GPU VBIOS · network card firmware · ⚠️ MICROCODE ·
   peripheral firmware
⚠️ ⚠️ THE UNCOMFORTABLE TRUTH: a modern machine runs a great deal
   of privileged code before and beneath the OS, most of it
   proprietary and unexamined (§25, §26.2)
⚠️ THE SPECTRUM  ⚠️ bare metal → RTOS → embedded Linux
⚠️ WHAT MAKES FIRMWARE DIFFERENT FROM SOFTWARE  ⚠️ it may be the
   only thing running · ⚠️ failure can be unrecoverable (bricking)
   · updates are risky and sometimes one-way · ⚠️ hardware
   constraints are absolute · debugging is hard · ⚠️ lifetimes
   measured in decades
```

---

## §21. ⚠️ The Boot Sequence

> **⚠️ The chain that gets a machine from applied power to an operating system, and knowing
> its stages is what makes boot failures diagnosable.**
```
⚠️ THE STAGES, in order
   ⚠️ 1. POWER SEQUENCING and RESET  ⚠️ rails come up in a
      required order; reset released when stable
   ⚠️ 2. ⚠️ THE FIRST INSTRUCTION comes from a fixed RESET VECTOR
      in ROM — ⚠️ and at this point there is NO RAM initialized
   ⚠️ 3. ⚠️ EARLY INIT  ⚠️ often running out of CACHE-AS-RAM,
      because DRAM does not work until it is trained
   ⚠️ 4. ⚠️ MEMORY TRAINING  ⚠️ the memory controller calibrates
      timings against the actual DIMMs. ⚠️ This is why first
      boot after a RAM change is slow, and why results are
      cached
   ⚠️ 5. Chipset and silicon init · 6. device enumeration
   ⚠️ 7. Boot device selection · 8. bootloader · 9. kernel
⚠️ ⚠️ UEFI vs LEGACY BIOS
   ⚠️ Legacy: 16-bit real mode, MBR, 512-byte boot sector,
      interrupt-based services. ⚠️ Effectively gone
   ⚠️ UEFI: ⚠️ a small OS in its own right — 64-bit, GPT
      partitions, ⚠️ an EFI SYSTEM PARTITION holding actual
      executable files, driver model, protocols, boot manager
      with variables, ⚠️ and a shell
⚠️ THE UEFI PHASES  ⚠️ SEC → PEI (pre-EFI init, memory) →
   ⚠️ DXE (driver execution — where most functionality lives) →
   BDS (boot device select) → TSL → RUNTIME
⚠️ ⚠️ RUNTIME SERVICES PERSIST AFTER THE OS BOOTS — ⚠️ variable
   access and firmware update paths remain callable, which is
   both useful and an attack surface (§25)
⚠️ EMBEDDED EQUIVALENTS  ⚠️ ROM bootloader → first-stage (SPL,
   often size-constrained) → U-Boot or similar → kernel
```

---

## §22. ⚠️ Root of Trust and Verified Boot

```
⚠️ ⚠️ THE CORE IDEA: TRUST MUST START SOMEWHERE IMMUTABLE. ⚠️ A
   hardware root of trust — mask ROM or fused keys that cannot
   be modified — verifies the next stage, which verifies the
   next, and so on
⚠️ ⚠️ TWO DIFFERENT THINGS OFTEN CONFLATED
   ⚠️ SECURE / VERIFIED BOOT  ⚠️ ENFORCES — refuses to run
      unsigned code
   ⚠️ MEASURED BOOT  ⚠️ RECORDS — hashes each stage into TPM PCRs
      and lets a remote party ATTEST what ran. ⚠️ It does not
      block anything
   ⚠️ They are complementary, not alternatives
⚠️ THE TPM  ⚠️ PCRs (⚠️ extend-only, so history cannot be
   rewritten) · sealing (⚠️ releasing a key only if PCRs match,
   which is how BitLocker binds to platform state) ·
   attestation · endorsement key
⚠️ ⚠️ UEFI SECURE BOOT's KEY HIERARCHY (§26.1)
   ⚠️ PK (Platform Key — the OEM's root, one key)
   ⚠️ KEK (Key Exchange Key — authorizes updates to the lists)
   ⚠️ DB (allowed signatures) and ⚠️ DBX (revoked)
⚠️ SHIM  ⚠️ how Linux boots under Secure Boot — a small
   Microsoft-signed loader that then validates the distribution's
   own key, with MOK for user-enrolled keys
⚠️ ROLLBACK PROTECTION  ⚠️ signature validity is not enough —
   ⚠️ an attacker can install a genuinely signed OLD version
   with a known vulnerability. ⚠️ Monotonic counters or fuses
   are the defence, and this is frequently omitted
⚠️ ⚠️ THE HONEST LIMIT: verified boot proves what LOADED, not
   that it is CORRECT. ⚠️ A signed vulnerable bootloader passes
   verification perfectly (§26.1's BlackLotus)
```

---

## §23. ACPI and Platform Interfaces

**⚠️ ACPI is how firmware describes the platform to the OS** — ⚠️ **tables (DSDT, SSDT,
MADT, FADT and many more) plus AML, a bytecode the OS interprets.**
**⚠️ Power states** are the visible part: ⚠️ **S-states (system sleep), C-states (CPU idle),
P-states (performance/frequency), D-states (device) — and getting these right is most of
what "sleep doesn't work" bugs are about.**
**⚠️ Device tree** is the alternative model used on ARM and RISC-V embedded systems —
⚠️ **a static description passed to the kernel rather than an interpreted bytecode, and
much easier to reason about.**
**⚠️ SMBIOS/DMI** for inventory data, ⚠️ **and SMM (System Management Mode) as the
x86 mechanism that is both genuinely useful and a serious security concern** (§25).
**⚠️ The practical point**: ⚠️ **an enormous share of "Linux doesn't support this laptop"
problems are ACPI table bugs that Windows tolerates because the vendor tested against
Windows only.**

---

## §24. Embedded Firmware Practice

**⚠️ The startup sequence before `main()`**: ⚠️ **vector table, stack pointer, copying
initialized data from flash to RAM, zeroing BSS, calling constructors — ⚠️ and knowing this
is what lets you debug a device that never reaches `main`.**
**⚠️ The linker script and memory map** are first-class design artifacts, not boilerplate.
**⚠️ Interrupts**: ⚠️ **keep ISRs short, understand priority and nesting, ⚠️ and volatile
plus atomic access for anything shared with an ISR — ⚠️ noting that `volatile` is NOT a
synchronization primitive** (see a microarchitecture reference §8).
**⚠️ Bare metal versus RTOS**: ⚠️ **superloop with a state machine is often the right answer;
an RTOS buys preemption and structure at the cost of stack-per-task and a scheduler to
reason about.**
**⚠️ Watchdogs** — ⚠️ **and the discipline that a watchdog must be fed from a place that
proves the system is actually working, not from a timer interrupt that runs regardless.**
**⚠️ Field update is the hardest requirement**: ⚠️ **A/B partitions, atomic switchover,
power-fail safety, rollback, and a recovery path that cannot itself be bricked** (see a
peripherals reference §17).

---

## §25. ⚠️ Firmware Security

```
⚠️ ⚠️ WHY IT MATTERS DISPROPORTIONATELY  ⚠️ firmware runs before
   and beneath the OS, persists across reinstalls and disk
   replacement, and is largely invisible to antivirus
⚠️ THE ATTACK CLASSES
   ⚠️ BOOTKITS  ⚠️ persist in the boot chain (§26.1)
   ⚠️ SMM attacks  ⚠️ SMM is more privileged than the kernel
      and hypervisor
   ⚠️ ⚠️ DMA attacks  ⚠️ a peripheral reading host memory
      directly — IOMMU is the mitigation (see a peripherals
      reference §24)
   ⚠️ SPI flash modification — ⚠️ physical or logical, if write
      protection is misconfigured
   ⚠️ ⚠️ SUPPLY CHAIN  implanted or modified firmware before
      delivery
   ⚠️ Unsigned or weakly-signed update paths
   ⚠️ ⚠️ CONFIGURATION IMAGE PARSING — ⚠️ the LogoFAIL class
      showed that image parsers in firmware, processing an
      attacker-supplied boot logo, were exploitable. ⚠️ Firmware
      contains far more attack surface than people assume
⚠️ THE DEFENCES  ⚠️ hardware root of trust (§22) · signed
   updates with ROLLBACK PROTECTION · ⚠️ SPI write protection ·
   reduced attack surface · memory-safe languages in firmware ·
   ⚠️ measured boot and attestation · runtime firmware
   integrity monitoring
⚠️ ⚠️ THE STRUCTURAL PROBLEM  ⚠️ firmware is written by
   organizations that do not maintain it for the device's life,
   patched slowly or never, and the user usually cannot tell
   what version they run or whether it is vulnerable
```
