---
name: linux-kernel-shell-reference
description: "Use when reviewing kernel or shell work for known anti-patterns, weighing contested questions (Rust in the kernel, the CVE flood, systemd, io_uring's performance vs attack surface, monolithic vs microkernel, a stable in-kernel ABI, bcachefs's removal, which shell, set -e), checking whether a kernel-version or tooling claim is still current (snapshot verified August 2026), finding the primary sources, books, people, and channels, or needing the kernel numbers, diagnostic first moves, kernel patch checklist, and shell script checklist. Companion to the other os-development-kernel-shell skills."
---

# Linux Kernel & Shell: Anti-Patterns, Contested Questions, Currency, and Canon

> **Part 5 of 5** of the *OS Development — Linux Kernel and Shell* reference (plugin `os-development-kernel-shell`), covering §15–§20. Sibling skills: `linux-kernel-architecture-and-code` (§0–§3), `linux-syscalls-ebpf-boot-and-init` (§4–§7), `linux-shell-scripting-and-userland` (§8–§11), `linux-kernel-debugging-process-and-hardening` (§12–§14). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 below for the currency snapshot and what goes stale first.

> **How to read this.** Reference, not tutorial. Sections are independent. Three markers:
> - **[DURABLE]** — architecture, algorithms, or semantics that have been stable for
>   decades and will outlive this document.
> - **[VERSIONED]** — depends on a kernel version, a shell version, or a distro. Check
>   `Documentation/`, the man page, or the source for your version.
> - **[CONTESTED]** — the kernel community itself disagrees, publicly and at length.
>   Both cases given.
>
> **⚠️ GOTCHA** boxes mark the mistakes that produce kernel oopses, data loss, silent
> corruption, or a patch rejected on the mailing list.
>
> **The framing that matters most:** the kernel is not "a big program." It is a
> **hostile-input state machine running with no memory protection, no exceptions, a
> hard limit on stack depth, and a promise never to break userspace**. Almost every
> kernel-specific rule below descends from one of those five facts.

---

## §15. Anti-Patterns

### 15.1 Kernel

| Anti-pattern | Why | Instead |
|---|---|---|
| `GFP_KERNEL` in atomic context | Sleeping under a spinlock/IRQ → deadlock | `GFP_ATOMIC`, or restructure |
| Large stack arrays / recursion | 16 KB stack, no guard in older configs | `kmalloc`, iteration |
| `volatile` for concurrency | Provides neither atomicity nor ordering | `READ_ONCE`/`WRITE_ONCE` + locks/barriers |
| `atomic_t` for reference counts | No overflow/UAF detection | **`refcount_t`** |
| Manual `kfree` in a driver probe path | Leaks on every error branch | **`devm_*`** |
| Inconsistent lock ordering | Deadlock, found in production | Document + lockdep |
| Floating point in kernel | FPU state not saved | Fixed point; or `kernel_fpu_begin/end` if you truly must |
| Dereferencing `__user` pointers | Bug and security hole | `copy_from_user` + Sparse (`make C=1`) |
| Reading a userspace value twice | TOCTOU → privesc | Copy once, validate the copy |
| `copy_to_user` of an unzeroed struct | Info leak via padding | `memset` first |
| Ignoring `-EPROBE_DEFER` | Spinning or failing on a not-yet-ready dependency | Return it |
| Busy-waiting in a driver | Burns a CPU | `wait_event`, completions, threaded IRQ |
| New `/proc` file for arbitrary data | Wrong interface, becomes ABI | sysfs (stable) or debugfs (unstable) |
| Changing a `uapi` struct | Breaks userspace forever | New syscall/flag; size-and-flags pattern |
| Out-of-tree module as a long-term plan | No stable ABI; DKMS forever | Upstream it |
| Shipping on a non-LTS kernel | EOL in ~10 weeks | Anchor to LTS |

### 15.2 Shell

| Anti-pattern | Why | Instead |
|---|---|---|
| Unquoted `$var` | Word splitting + globbing → wrong files | `"$var"` |
| Parsing `ls` | Breaks on spaces, newlines, glob chars | Globs, `find -print0` |
| `rm -rf $DIR/` | Empty/typo'd var → catastrophe | `set -u` + `"${DIR:?}"` |
| Relying on `set -e` alone | Full of exceptions (§8.2 → `linux-shell-scripting-and-userland`) | Check returns that matter |
| `cd dir; do_thing` | `cd` can fail | `cd dir \|\| exit 1` |
| Predictable `/tmp/file.$$` | Symlink attack | `mktemp` |
| `cmd \| while read` expecting side effects | Subshell in bash | `while read … done < <(cmd)` |
| Bash-isms in `#!/bin/sh` | `/bin/sh` is dash/ash on many systems | `#!/usr/bin/env bash`, or write POSIX |
| Cleanup code at the end of the script | Skipped on error/signal | `trap cleanup EXIT` |
| Missing `local` in functions | Global by default; corrupts caller | `local` everything |
| `echo` for arbitrary data | Interprets escapes inconsistently across shells | `printf '%s\n'` |
| Data on stdout mixed with logs | Breaks composition | Logs to stderr |
| A 900-line bash script | Unmaintainable, untestable | Python at ~200 lines |
| No `shellcheck` | Every quoting bug is mechanically detectable | Run it in CI |
| `sudo` inside a script without checking | Prompts mid-run, or runs unexpectedly as root | Check `EUID`, fail fast |

---

## §16. Contested Questions

**16.1 Rust in the kernel.** §2.6 → `linux-kernel-architecture-and-code`. Settled as policy, unsettled as social reality.

**16.2 The CVE flood.** §13.3 → `linux-kernel-debugging-process-and-hardening`. Honest-but-unusable vs. dishonest-but-triageable.

**16.3 systemd.** §7.1 → `linux-syscalls-ebpf-boot-and-init`.

**16.4 io_uring: performance vs. attack surface.** §4.3 → `linux-syscalls-ebpf-boot-and-init`. The unusual feature of this
argument is that both sides cite the same evidence — it *is* fast and it *has* produced a
disproportionate share of exploitable bugs.

**16.5 Monolithic vs. microkernel.** The oldest argument in the field (Tanenbaum–Torvalds,
1992). Linux won commercially and decisively; the microkernel case (fault isolation,
formal verifiability — seL4 has a machine-checked proof) remains technically strong and is
where safety-critical systems actually go. Note the irony that Linux has been steadily
absorbing microkernel-ish ideas: FUSE, uio/vfio userspace drivers, and eBPF are all "run
this in a constrained context instead of ring 0."

**16.6 Stable in-kernel ABI.** *For:* out-of-tree drivers wouldn't need constant
rebuilding; vendors could ship binaries. *Against (the kernel's position, in
`Documentation/process/stable-api-nonsense.rst`):* a stable internal ABI freezes bad
designs forever, prevents whole-tree refactoring, and the correct answer is to upstream
your driver — at which point someone else fixes it for you when the interface changes.
This is settled in the kernel and permanently contested by hardware vendors.

**16.7 bcachefs's removal.** §17. A dispute about development process, not about the
filesystem's technical merit — which is generally acknowledged.

**16.8 Which shell.** §9.3 → `linux-shell-scripting-and-userland`. Genuinely low-stakes for interactive use, genuinely
high-stakes for scripts, and people persistently conflate the two.

**16.9 `set -e`.** Some argue it's essential defensive practice; others (the BashFAQ 105
position) that its exception list makes it actively misleading and that explicit error
checking is the only honest approach. Both camps write correct scripts; neither writes
them by relying on `set -e` alone.

---

## §17. Currency Snapshot — verified August 2026

| Thing | Status as of Aug 2026 | Decay risk |
|---|---|---|
| **Kernel mainline** | **7.1.9** (19 Aug 2026); 7.2-rc in flight. **7.0 released 12 April 2026** after 6.19; major number carries no semantic meaning. **7.0 already EOL (27 June 2026)** | **High** |
| **Kernel LTS** | 5.10, 5.15, 6.1, 6.6, 6.12, **6.18**. GKH **extended 6.6/6.12/6.18 in Feb 2026**; 6.18 → at least **Dec 2028**. ⚠️ **5.10 and 5.15 EOL 31 Dec 2026** | Medium |
| **Rust for Linux** | **Experimental label removed in 7.0.** First-class language; coexistence policy formalized at the 2025 Tokyo Maintainers Summit (Rust for new code, C stays, no forced migration). Stable-Rust-only builds, min ~1.93. Kernel Rust API covers PCI enumeration, IRQ, DMA mapping, platform device registration. **Graphics subsystem to accept only Rust for new drivers** (GKH, OSS India, July 2026) | Medium |
| **PREEMPT_RT** | **Mainlined in 6.12** (Sept 2024): x86, arm64, RISC-V | Low |
| **sched_ext** | Merged **6.12**. `scx` schedulers (`scx_rusty`, `scx_lavd`, `scx_bpfland`, `scx_layered`) in production at Meta. SCX-enabled kernels default on Fedora/Arch/CachyOS/NixOS/openSUSE TW; Ubuntu 26.04 HWE only; Debian stable needs backports | Medium |
| **EEVDF** | Fair-class scheduler since 6.6 (replaced CFS) | Low |
| **bcachefs** | ⚠️ Marked "externally maintained" **Aug 2025**; **removed from the tree entirely in 6.18** ("It's now a DKMS module, making the in-kernel code stale"). Ships as DKMS; tools v1.38.6 (June 2026) dropped the "experimental" label. Root-fs use requires an initramfs that loads the module | Medium |
| **Kernel CVEs** | kernel.org is a CNA since Feb 2024; ~50 CVEs/week, **no severity scores**; **432 published in <48h in July 2026**. Largest CVE issuer in existence | **High** |
| **EU CRA** | Vulnerability/incident **reporting obligations start 11 Sept 2026**; full application 11 Dec 2027. The kernel is a component in your SBOM | **Imminent** |
| **io_uring** | ~60% of Google VRP kernel exploit submissions; ~$1M paid in io_uring bounties. Disabled in ChromeOS, restricted on Android, blocked by containerd's default seccomp profile. Published io_uring-only rootkit evades syscall monitoring. `kernel.io_uring_disabled=2` to disable | Medium |
| **systemd** | **v261** current; **v258** removed cgroup v1 and SysV runlevels; **v259** deprecated SysV scripts, made journald persistent by default, dropped iptables NAT for nftables; **v260 (March 2026) removed SysV generators entirely**; v260 raises minimums (kernel 5.10, glibc 2.34, OpenSSL 3.0, Python 3.9) | Medium |
| **bash** | **5.3** (3 July 2025) — first release in 3 years. `${ cmd; }` / `${\| cmd; }` non-forking command substitution, `GLOBSORT`, `source -p`, no fork for `&&`/`\|\|` RHS, C23 conformance. Readline 8.3. ⚠️ **macOS still ships 3.2** | Low |
| **zsh** | **5.9.1** (31 May 2026). macOS default since Catalina | Low |
| **fish** | **4.7** (May 2026); Rust rewrite since 4.0 (Feb 2025). Non-POSIX by design | Medium |
| **nushell** | Past **0.111**, still pre-1.0. Structured-data pipelines | High |
| **POSIX** | **POSIX.1-2024 / Base Specifications Issue 8 / SUSv5**, published 14 June 2024. Aligned with C17. ⚠️ **`test -a`/`-o` removed**; `gettimeofday()` removed; new "intrinsic utilities" category. First technical corrigendum in progress | Low |
| **Shell usage** | Bash/shell scripting at **49% of developers** (SO 2025 survey), 5th overall, ahead of TypeScript. Fish ~7% among developers | Annual |
| **Distro userland** | Ubuntu shipping **uutils** (Rust coreutils) — behavioural differences from GNU are a new source of portability surprises | Medium |

**Goes stale fastest:** kernel version numbers and LTS EOL dates; CVE volume; Rust
subsystem policy; nushell. **Essentially never stale:** §1 → `linux-kernel-architecture-and-code` (architecture), §3 → `linux-kernel-architecture-and-code`
(concurrency), §4.1 → `linux-syscalls-ebpf-boot-and-init` (the ABI contract), §8 → `linux-shell-scripting-and-userland` (shell semantics), §10 → `linux-shell-scripting-and-userland` (defensive scripting),
§15 (anti-patterns).

---

## §18. The Canon

### 18.1 Primary sources — prefer these over everything else

- **`Documentation/` in the kernel tree** and **docs.kernel.org**. Specifically:
  `process/submitting-patches.rst`, `process/coding-style.rst`,
  `process/stable-api-nonsense.rst`, `process/volatile-considered-harmful.rst`,
  **`memory-barriers.txt`**, `RCU/`, `scheduler/sched-ext.rst`, `bpf/`, `process/cve.rst`.
- **The source itself.** `git log -p <file>` and `git blame` answer questions no
  documentation will. **Bootlin's Elixir** (`elixir.bootlin.com`) is the best
  cross-referenced browser.
- **LWN.net** — the single most valuable ongoing source on kernel development. The weekly
  Kernel Page, the merge-window summaries, and Jonathan Corbet's architecture articles are
  effectively the kernel's journal of record. **Subscribe.**
- **`man7.org`** (Michael Kerrisk) — the definitive Linux man pages, especially section 2
  and 7.
- **The Open Group Base Specifications Issue 8** (`pubs.opengroup.org`) — POSIX itself,
  free online. The shell grammar chapter is the answer to every "why does the shell do
  that" question.
- **GNU Bash Reference Manual** and **`bash-hackers`-style references**; **BashFAQ** and
  **BashPitfalls** on `mywiki.wooledge.org` — the latter is the best shell-bug catalogue
  in existence.
- **kernelnewbies.org**, the **KernelNewbies mailing list**, and the **KVM/Plumbers/LSFMM
  conference materials**.
- **ebpf.io** / **docs.ebpf.io**, and **Brendan Gregg's** site.

### 18.2 Books

| Author | Work | Why |
|---|---|---|
| **Robert Love** | *Linux Kernel Development* (3e) | Still the best readable introduction to kernel concepts, even though the code has moved on |
| **Bovet & Cesati** | *Understanding the Linux Kernel* | Deep, structural, dated (2.6) but conceptually intact |
| **Corbet, Rubini & Kroah-Hartman** | *Linux Device Drivers* (3e) | The classic driver text. **Very** dated in API, still correct in model |
| **Kerrisk** | ***The Linux Programming Interface*** | **The single best book on the Linux userspace API.** If you buy one book, this one |
| **Stevens & Rago** | *Advanced Programming in the UNIX Environment* | The other one |
| **Stevens** | *UNIX Network Programming*, *TCP/IP Illustrated* | Sockets and the wire |
| **Brendan Gregg** | ***Systems Performance***, ***BPF Performance Tools*** | The performance and observability canon. USE method, flame graphs, the whole toolkit |
| **Kaiwan Billimoria** | *Linux Kernel Programming* / *…Part 2* | The most current practical kernel-programming books |
| **Bhattacharjee & Lustig** | *Architectural and OS Support for Virtual Memory* | Memory management depth |
| **Cooper & many** | *Advanced Bash-Scripting Guide* | Comprehensive, uneven — cross-check against BashFAQ |
| **Robbins & Beebe** | *Classic Shell Scripting* | The disciplined, portable approach |
| **Newham** | *Learning the bash Shell* | The O'Reilly standard |
| **Silberschatz et al.** | *Operating System Concepts* | The academic foundation, if you want theory |
| **Arpaci-Dusseau** | ***Operating Systems: Three Easy Pieces*** | **Free online**, and the best modern OS textbook |

### 18.3 People and channels
Jonathan Corbet (LWN), Greg Kroah-Hartman (stable, CVEs — `kroah.com/log`), Linus
Torvalds (the LKML archives are a genuine education in engineering judgment, and
occasionally in what not to do), Michael Kerrisk (man-pages), Brendan Gregg
(performance), Miguel Ojeda (Rust for Linux), Tejun Heo (cgroups, sched_ext), Jens Axboe
(block, io_uring), Chet Ramey (bash, since 1990), Phoronix (news and benchmarks — treat
benchmarks with normal caution), `lore.kernel.org` for every mailing list ever.

---

## §19. Quick Reference

### 19.1 Kernel numbers
- x86-64 kernel stack: **16 KB** (`THREAD_SIZE`), shared with IRQ frames on some configs.
- Page size: **4 KiB** typical; 2 MiB / 1 GiB huge pages; arm64 supports 4/16/64 KiB.
- `kmalloc` max: order-limited, a few MB — use `vmalloc` above that.
- Default `HZ`: 250 or 1000 (`CONFIG_HZ`); tickless (`NO_HZ_FULL`) for RT.
- `sched_rt_runtime_us`: **950000** of 1000000 µs — the RT throttle.
- Kernel release cadence: **~9–10 weeks**; merge window **2 weeks**; ~7 `rc`s.
- New LTS projected EOL: **~2 years**, extended on industry demand.

### 19.2 Diagnostic first moves
| Symptom | First command |
|---|---|
| System slow | `top` / `htop`, then `cat /proc/pressure/*` (PSI) |
| High iowait / D-state processes | `iostat -xz 1`, `biolatency`, `cat /proc/PID/stack` |
| Which syscalls | `strace -f -c -p PID` (dev only) or `bpftrace` |
| Where is CPU going | `perf top`, then `perf record -g` → flame graph |
| Kernel oops | `dmesg -T`, `journalctl -k -b -1`, `faddr2line` |
| Out of memory | `dmesg \| grep -i oom`, `/sys/fs/cgroup/*/memory.events` |
| Network | `ss -tanp`, `ip -s link`, `tcpdump`, `bpftrace` on tcp tracepoints |
| Disk full but `du` disagrees | `lsof +L1` (deleted-but-open files) |
| Module won't load | `dmesg`, `modinfo`, check signature + taint + kernel version |

### 19.3 Kernel patch checklist
- [ ] Builds clean with `W=1` and no new warnings
- [ ] `checkpatch.pl --strict` clean (or deviations justified)
- [ ] `make C=1` (Sparse) clean — especially `__user`/`__iomem` annotations
- [ ] Tested with KASAN + lockdep enabled
- [ ] Locking documented; no sleeping in atomic context
- [ ] All error paths unwind correctly (test them with fault injection)
- [ ] No `uapi` changes, or an explicitly compatible extension
- [ ] `Fixes:` tag if it's a fix; `Cc: stable@` if it should be backported
- [ ] Commit message explains **why**
- [ ] Sent as plain text to the right list per `get_maintainer.pl`

### 19.4 Shell script checklist
- [ ] `set -Eeuo pipefail` and `IFS=$'\n\t'`
- [ ] `shellcheck` clean
- [ ] Every expansion quoted; `"$@"` not `$@`
- [ ] `local` in every function
- [ ] `trap cleanup EXIT`; `mktemp` for temp files
- [ ] Required inputs validated with `${VAR:?}`
- [ ] Dependencies checked with `command -v`
- [ ] Logs to stderr, data to stdout, meaningful exit codes
- [ ] Idempotent, or documented as not
- [ ] Correct shebang for the features used; tested on the target's `/bin/sh` if POSIX

---

## §20. Sources and Method

**Method.** Narrative (not systematic) review. Durable material — §1 → `linux-kernel-architecture-and-code` (architecture),
§3 → `linux-kernel-architecture-and-code` (concurrency), §4.1 → `linux-syscalls-ebpf-boot-and-init` (the ABI contract), §8 → `linux-shell-scripting-and-userland` (shell semantics), §10 → `linux-shell-scripting-and-userland` (defensive
scripting), §12 → `linux-kernel-debugging-process-and-hardening` (debugging technique), §15 (anti-patterns) — is synthesized from the
kernel's own documentation, the POSIX specification, and the canonical texts in §18.
Every **time-sensitive** claim (versions, EOL dates, feature status, policy changes) was
verified against a primary or near-primary source in **August 2026** and is flagged in
§17 with a decay-risk rating. Where the kernel community itself disagrees, §16 presents
both cases rather than adjudicating.

**Search log** (August 2026): Linux kernel current version and LTS support timelines ·
Rust for Linux status after 7.0 · bash/zsh/fish/nushell versions and adoption · bash 5.3
features · eBPF and sched_ext status · Linux kernel CNA and CVE volume · bcachefs removal
· POSIX.1-2024 / Issue 8 · systemd v258–v261 changes · io_uring security posture.

**Primary and near-primary sources consulted (selected):**
- kernel.org releases and **docs.kernel.org** — `scheduler/sched-ext.rst`, `bpf/verifier`,
  `process/cve.rst`
- **LWN.net** — bcachefs removal; systemd v258/v259 highlights; kernel CVE assignment
  process; bash-5.3 release
- **Greg Kroah-Hartman** — `kroah.com/log` on the Linux CVE assignment process; LTS
  extension announcements; Open Source Summit India keynote coverage (July 2026)
- **Rust for Linux** project site and kernel Rust policy documentation
- **Phoronix** — Linux 7.0 driver core / Rust; bcachefs "externally maintained"; systemd
  259; Google restricting io_uring
- **The Open Group** — Base Specifications Issue 8 (POSIX.1-2024); IEEE 1003.1-2024
- **GNU** — bash release announcement and `NEWS`/`CHANGES` (Chet Ramey), bash home page
- **systemd** GitHub release notes v258 / v259
- **Google Security Blog** coverage of kCTF VRP io_uring findings (via Phoronix and
  contemporaneous reporting); ARMO io_uring rootkit disclosure
- **The Register** — "Linux kernel team publishes 432 CVEs in two days" (July 2026)
- European Commission — Cyber Resilience Act reporting obligations

**Confidence statement.** **High confidence** in §1–§8 → `linux-kernel-architecture-and-code`, `linux-shell-scripting-and-userland`, §10–§15 → `linux-shell-scripting-and-userland`, §18–§19 — these rest on
kernel documentation, the POSIX standard, and long-established practice. **High
confidence** in §17's verified items as of the stated date. **Moderate confidence** in the
2026 Rust-policy specifics (§2.6 → `linux-kernel-architecture-and-code`) and the sched_ext distro-status details (§5.2 → `linux-syscalls-ebpf-boot-and-init`) — these
rest partly on conference reporting and practitioner blogs rather than primary project
documentation, and subsystem-level policy in particular is being decided maintainer by
maintainer rather than by a single announcement. Where a figure comes from a vendor's own
program (Google's VRP payout percentages in §4.3 → `linux-syscalls-ebpf-boot-and-init`), it is attributed as such; the direction
of that evidence is much more reliable than its precision.
